// Reference Implementation, Not Normative — for conformance testing only.
//
// Faying Protocol/1.1 coFay Delegated Stewardship Profile & Atomic Dual-Signed
// Stewardship Transfer verifier. Implements the backward-compatible 1.1
// profile defined in `schemas/fap-1.1-cofay.cddl` and `schemas/fap-1.1-cofay.json`,
// plus §1.7.3 MAJOR.MINOR protocol version negotiation.

import { sign, verify, type Alg, type KeyPair } from "./crypto.ts";

export const STEWARDSHIP_SIGNING_DOMAIN = "ifay.faying.cofay-stewardship.v1:";
export const TRANSFER_SIGNING_DOMAIN = "ifay.faying.cofay-transfer.v1:";

export type UpstreamState = "Active" | "Degraded" | "G0" | "Revoked";

export interface ResourceBudget {
  max_invocations?: number;
  max_cost_units?: number;
}

export interface StewardshipScope {
  domains: string[];
  actions: string[];
  terminals?: string[];
  budget?: ResourceBudget;
}

export interface HexSignatureBundle {
  alg: Alg;
  pubkey: string;
  sig: string;
}

export interface CofayStewardshipMandate {
  version: string;
  profile: string;
  id: string;
  issued_at: string;
  not_before: string;
  not_after: string;
  steward_entity: string;
  accountable_human_prime: string;
  parent_mandate_id: string;
  manager_fay_id: string;
  manager_grade: number;
  manager_not_before: string;
  manager_not_after: string;
  manager_scope: StewardshipScope;
  subject_cofay_id: string;
  charter_id: string;
  charter_scope: StewardshipScope;
  scope: StewardshipScope;
  grade: number;
  hop_count: number;
  max_stewardship_hops: number;
  on_upstream_g0: string;
  manager_signature: HexSignatureBundle;
}

export interface CofayTransferAuthorization {
  version: string;
  profile: string;
  transfer_id: string;
  cofay_id: string;
  charter_id: string;
  previous_mandate_id: string;
  from_steward: string;
  from_human_prime: string;
  to_steward: string;
  to_human_prime: string;
  next_manager_fay_id: string;
  issued_at: string;
  expires_at: string;
  nonce: string;
  from_steward_signature: HexSignatureBundle;
  to_steward_signature: HexSignatureBundle;
}

export type StewardshipOutcome =
  | {
      valid: true;
      runtime_state: "active";
      accountable_human_prime: string;
      effective_grade: number;
    }
  | {
      valid: false;
      runtime_state: "rejected" | "safe-state-halt";
      error_code: number;
      error_name: string;
      reason: string;
    };

export type TransferOutcome =
  | {
      valid: true;
      active_steward: string;
      accountable_human_prime: string;
      next_manager_fay_id: string;
    }
  | {
      valid: false;
      error_code: number;
      error_name: string;
      reason: string;
    };

const HP_RE = /^hp_[a-z0-9][a-z0-9_-]{2,63}$/;
const STEWARD_RE = /^(hp|org)_[a-z0-9][a-z0-9_-]{2,63}$/;
const IFAY_RE = /^ifay_[a-z0-9][a-z0-9_-]{2,63}$/;
const COFAY_RE = /^cofay_[a-z0-9][a-z0-9_-]{2,63}$/;

/** RFC 8785 JCS deterministic serializer for JSON objects/arrays/primitives. */
export function canonicalizeJcs(value: unknown): string {
  if (value === null || typeof value === "boolean" || typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new Error("RFC 8785 JCS forbids non-finite numbers");
    }
    return Object.is(value, -0) ? "0" : JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => canonicalizeJcs(v)).join(",")}]`;
  }
  if (typeof value === "object") {
    const entries = Object.entries(value as Record<string, unknown>)
      .filter(([, v]) => v !== undefined)
      .sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
    const parts = entries.map(([k, v]) => `${JSON.stringify(k)}:${canonicalizeJcs(v)}`);
    return `{${parts.join(",")}}`;
  }
  throw new Error(`Unsupported JCS type: ${typeof value}`);
}

function fromHex(hex: string): Uint8Array | null {
  if (!/^[0-9a-f]+$/.test(hex) || hex.length % 2 !== 0) return null;
  return new Uint8Array(Buffer.from(hex, "hex"));
}

function toHex(bytes: Uint8Array): string {
  return Buffer.from(bytes).toString("hex");
}

function parseIsoMs(iso: string): number | null {
  const ms = Date.parse(iso);
  return Number.isNaN(ms) ? null : ms;
}

function isSubset(sub: string[], sup: string[]): boolean {
  if (sub.length === 0) return false;
  const supSet = new Set(sup);
  return sub.every((item) => supSet.has(item));
}

function isScopeWithin(target: StewardshipScope, bound: StewardshipScope): boolean {
  if (!isSubset(target.domains, bound.domains)) return false;
  if (!isSubset(target.actions, bound.actions)) return false;
  if (bound.terminals && bound.terminals.length > 0) {
    if (!target.terminals || target.terminals.length === 0) return false;
    if (!isSubset(target.terminals, bound.terminals)) return false;
  }
  if (bound.budget?.max_invocations !== undefined) {
    if (
      target.budget?.max_invocations === undefined ||
      target.budget.max_invocations > bound.budget.max_invocations ||
      target.budget.max_invocations < 1
    ) {
      return false;
    }
  }
  if (bound.budget?.max_cost_units !== undefined) {
    if (
      target.budget?.max_cost_units === undefined ||
      target.budget.max_cost_units > bound.budget.max_cost_units ||
      target.budget.max_cost_units < 1
    ) {
      return false;
    }
  }
  return true;
}

export function stewardshipSigningInput(
  mandate: Omit<CofayStewardshipMandate, "manager_signature">,
): Uint8Array {
  const jcs = canonicalizeJcs(mandate);
  return new Uint8Array(Buffer.from(`${STEWARDSHIP_SIGNING_DOMAIN}${jcs}`, "utf8"));
}

export function signStewardshipMandate(
  unsignedMandate: Omit<CofayStewardshipMandate, "manager_signature">,
  managerKey: KeyPair,
): CofayStewardshipMandate {
  const msg = stewardshipSigningInput(unsignedMandate);
  const sig = sign(managerKey, msg, "steward");
  return {
    ...unsignedMandate,
    manager_signature: {
      alg: managerKey.alg,
      pubkey: toHex(managerKey.publicKey),
      sig: toHex(sig),
    },
  };
}

export function verifyStewardshipMandate(
  mandate: CofayStewardshipMandate,
  evaluatedAtIso: string,
  upstreamState: UpstreamState = "Active",
): StewardshipOutcome {
  if (mandate.version !== "Faying Protocol/1.1" || mandate.profile !== "cofay-stewardship") {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1099,
      error_name: "E_PROTOCOL",
      reason: "unsupported stewardship version or profile",
    };
  }

  // Upstream G0 / Revoked immediately triggers safe-state-halt cascade.
  if (upstreamState === "G0" || upstreamState === "Revoked") {
    return {
      valid: false,
      runtime_state: "safe-state-halt",
      error_code: 1024,
      error_name: "E_UPSTREAM_EMERGENCY_HALT",
      reason: `upstream manager state ${upstreamState} forces immediate safe-state-halt`,
    };
  }

  // Human Prime ultimate accountability check (personal hp_* or org_* anchored to hp_*).
  if (
    !STEWARD_RE.test(mandate.steward_entity) ||
    !HP_RE.test(mandate.accountable_human_prime) ||
    (mandate.steward_entity.startsWith("hp_") &&
      mandate.steward_entity !== mandate.accountable_human_prime)
  ) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1010,
      error_name: "E_HUMAN_WITNESS_REQUIRED",
      reason: "stewardship chain lacks a valid accountable Human Prime anchor",
    };
  }

  // Single-hop ceiling: coFay MUST NOT sub-delegate stewardship, hop_count MUST be 1.
  if (
    mandate.hop_count !== 1 ||
    mandate.max_stewardship_hops !== 1 ||
    !IFAY_RE.test(mandate.manager_fay_id) ||
    !COFAY_RE.test(mandate.subject_cofay_id)
  ) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1023,
      error_name: "E_STEWARDSHIP_HOP_LIMIT",
      reason: "coFay stewardship requires hop_count == 1 issued by an ifay_* manager to a cofay_* subject",
    };
  }

  if (mandate.on_upstream_g0 !== "safe-state-halt") {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1099,
      error_name: "E_PROTOCOL",
      reason: "on_upstream_g0 MUST be safe-state-halt",
    };
  }

  // Grade non-amplification: 0..4 and grade <= manager_grade.
  if (
    !Number.isInteger(mandate.grade) ||
    !Number.isInteger(mandate.manager_grade) ||
    mandate.grade < 0 ||
    mandate.grade > 4 ||
    mandate.manager_grade < 0 ||
    mandate.manager_grade > 4 ||
    mandate.grade > mandate.manager_grade
  ) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1021,
      error_name: "E_GRADE_AMPLIFICATION",
      reason: `stewardship grade ${mandate.grade} exceeds manager_grade ${mandate.manager_grade}`,
    };
  }

  // Scope & time-window convergence: scope <= charter_scope INTERSECT manager_scope.
  const nb = parseIsoMs(mandate.not_before);
  const na = parseIsoMs(mandate.not_after);
  const mnb = parseIsoMs(mandate.manager_not_before);
  const mna = parseIsoMs(mandate.manager_not_after);
  const evalMs = parseIsoMs(evaluatedAtIso);
  if (
    nb === null ||
    na === null ||
    mnb === null ||
    mna === null ||
    evalMs === null ||
    nb >= na ||
    nb < mnb ||
    na > mna ||
    evalMs < nb ||
    evalMs > na ||
    !isScopeWithin(mandate.scope, mandate.charter_scope) ||
    !isScopeWithin(mandate.scope, mandate.manager_scope)
  ) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1022,
      error_name: "E_SCOPE_ESCAPE",
      reason: "stewardship scope or validity window escapes charter_scope ∩ manager_scope",
    };
  }

  // Verify manager cryptographic signature over domain-separated JCS payload.
  const pubBytes = fromHex(mandate.manager_signature.pubkey);
  const sigBytes = fromHex(mandate.manager_signature.sig);
  if (!pubBytes || !sigBytes) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1003,
      error_name: "E_SIGNATURE_INVALID",
      reason: "malformed hex in manager_signature",
    };
  }
  const { manager_signature: _sig, ...unsigned } = mandate;
  const msg = stewardshipSigningInput(unsigned);
  if (!verify(mandate.manager_signature.alg, pubBytes, msg, sigBytes)) {
    return {
      valid: false,
      runtime_state: "rejected",
      error_code: 1003,
      error_name: "E_SIGNATURE_INVALID",
      reason: "manager_signature verification failed",
    };
  }

  return {
    valid: true,
    runtime_state: "active",
    accountable_human_prime: mandate.accountable_human_prime,
    effective_grade: mandate.grade,
  };
}

export function transferSigningInput(
  transfer: Omit<
    CofayTransferAuthorization,
    "from_steward_signature" | "to_steward_signature"
  >,
): Uint8Array {
  const jcs = canonicalizeJcs(transfer);
  return new Uint8Array(Buffer.from(`${TRANSFER_SIGNING_DOMAIN}${jcs}`, "utf8"));
}

export function signTransferAuthorization(
  unsignedTransfer: Omit<
    CofayTransferAuthorization,
    "from_steward_signature" | "to_steward_signature"
  >,
  fromKey: KeyPair,
  toKey: KeyPair,
): CofayTransferAuthorization {
  const msg = transferSigningInput(unsignedTransfer);
  const fromSig = sign(fromKey, msg, "from");
  const toSig = sign(toKey, msg, "to");
  return {
    ...unsignedTransfer,
    from_steward_signature: {
      alg: fromKey.alg,
      pubkey: toHex(fromKey.publicKey),
      sig: toHex(fromSig),
    },
    to_steward_signature: {
      alg: toKey.alg,
      pubkey: toHex(toKey.publicKey),
      sig: toHex(toSig),
    },
  };
}

export function verifyTransferAuthorization(
  transfer: CofayTransferAuthorization,
  evaluatedAtIso: string,
): TransferOutcome {
  if (transfer.version !== "Faying Protocol/1.1" || transfer.profile !== "cofay-transfer") {
    return {
      valid: false,
      error_code: 1099,
      error_name: "E_PROTOCOL",
      reason: "unsupported transfer version or profile",
    };
  }

  const issuedMs = parseIsoMs(transfer.issued_at);
  const expiresMs = parseIsoMs(transfer.expires_at);
  const evalMs = parseIsoMs(evaluatedAtIso);
  if (
    !COFAY_RE.test(transfer.cofay_id) ||
    !STEWARD_RE.test(transfer.from_steward) ||
    !STEWARD_RE.test(transfer.to_steward) ||
    !HP_RE.test(transfer.from_human_prime) ||
    !HP_RE.test(transfer.to_human_prime) ||
    !IFAY_RE.test(transfer.next_manager_fay_id) ||
    transfer.from_steward === transfer.to_steward ||
    transfer.nonce.length < 8 ||
    issuedMs === null ||
    expiresMs === null ||
    evalMs === null ||
    issuedMs >= expiresMs ||
    evalMs < issuedMs ||
    evalMs > expiresMs
  ) {
    return {
      valid: false,
      error_code: 1026,
      error_name: "E_TRANSFER_WINDOW_OR_PARTY_INVALID",
      reason: "invalid transfer party identifiers, self-transfer, or expired transfer window",
    };
  }

  const fromPub = fromHex(transfer.from_steward_signature.pubkey);
  const fromSig = fromHex(transfer.from_steward_signature.sig);
  const toPub = fromHex(transfer.to_steward_signature.pubkey);
  const toSig = fromHex(transfer.to_steward_signature.sig);
  if (!fromPub || !fromSig || !toPub || !toSig) {
    return {
      valid: false,
      error_code: 1025,
      error_name: "E_TRANSFER_DUAL_SIG_REQUIRED",
      reason: "malformed hex in dual signatures",
    };
  }

  const {
    from_steward_signature: _f,
    to_steward_signature: _t,
    ...unsigned
  } = transfer;
  const msg = transferSigningInput(unsigned);
  const okFrom = verify(transfer.from_steward_signature.alg, fromPub, msg, fromSig);
  const okTo = verify(transfer.to_steward_signature.alg, toPub, msg, toSig);
  if (!okFrom || !okTo) {
    return {
      valid: false,
      error_code: 1025,
      error_name: "E_TRANSFER_DUAL_SIG_REQUIRED",
      reason: "atomic transfer requires valid cryptographic signatures from both from_steward and to_steward",
    };
  }

  return {
    valid: true,
    active_steward: transfer.to_steward,
    accountable_human_prime: transfer.to_human_prime,
    next_manager_fay_id: transfer.next_manager_fay_id,
  };
}

/**
 * §1.7.3 MAJOR.MINOR protocol version negotiation:
 *   - Same MAJOR -> choose highest mutually supported MINOR.
 *   - No common MAJOR -> reject with E_PROTOCOL (1099).
 */
export function negotiateProtocolVersion(
  clientSupported: Iterable<string>,
  serverSupported: Iterable<string>,
): string {
  const parseVer = (raw: string): { major: number; minor: number; canonical: string } | null => {
    const trimmed = raw.replace(/^Faying Protocol\//, "");
    const m = /^(\d+)\.(\d+)$/.exec(trimmed);
    if (!m) return null;
    const major = Number(m[1]);
    const minor = Number(m[2]);
    return { major, minor, canonical: `Faying Protocol/${major}.${minor}` };
  };

  const cMap = new Map<string, { major: number; minor: number; canonical: string }>();
  for (const raw of clientSupported) {
    const p = parseVer(raw);
    if (p) cMap.set(p.canonical, p);
  }
  const common: { major: number; minor: number; canonical: string }[] = [];
  for (const raw of serverSupported) {
    const p = parseVer(raw);
    if (p && cMap.has(p.canonical)) common.push(p);
  }
  if (common.length === 0) {
    const err = new Error("E_PROTOCOL: no mutually supported Faying Protocol MAJOR.MINOR version");
    (err as Error & { errorCode?: number }).errorCode = 1099;
    throw err;
  }
  common.sort((a, b) => (a.major !== b.major ? b.major - a.major : b.minor - a.minor));
  return common[0]!.canonical;
}
