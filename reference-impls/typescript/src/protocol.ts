// Reference Implementation, Not Normative — for conformance testing only.
//
// Faying Protocol/1.0 envelope model + signing-input construction.
//
// This module is the heart of the reference codec: it turns the on-wire
// CBOR/JSON value model (see detcbor.ts / cbor.ts) into the protocol's
// logical concepts (envelope header / claims / signature-bundle) and
// computes the §6.3 signing input that every implementation must agree on:
//
//     signing_input_bytes = Deterministic-CBOR( Envelope_without_signature )
//     signing_input_hash  = SHA-256( signing_input_bytes )
//
// The bytes are what gets fed to Ed25519 / ES256 (which apply their own
// internal hash); the hash is the cross-encoding identity digest recorded
// in the official vectors' expected.json. Both are exposed here.

import crypto from "node:crypto";
import { encode as detEncode, decode as detDecode, Tag0, type CborValue } from "./detcbor.ts";
import { verify as cryptoVerify, sign as cryptoSign, type KeyPair } from "./crypto.ts";

export type Envelope = Map<string, CborValue>;

/** Message types per design.md §5.2. */
export const MSG_TYPES = [
  "BOOTSTRAP",
  "BOOTSTRAP_RESP",
  "PRESENCE",
  "PRESENCE_ACK",
  "GRADE_SWITCH",
  "GRADE_SWITCH_RESP",
  "DELEGATE",
  "DELEGATE_RESP",
  "REVOKE",
  "REVOKE_RECEIPT",
  "FAYING_REQUEST",
  "FAYING_REQUEST_RESP",
  "DISCLOSURE",
  "ERROR",
] as const;

/** Decode CBOR wire bytes into an envelope value model. */
export function decodeCbor(buf: Uint8Array): CborValue {
  return detDecode(buf);
}

/** Encode an envelope value model into deterministic CBOR wire bytes. */
export function encodeCbor(value: CborValue): Uint8Array {
  return detEncode(value);
}

/** Strip the top-level `signature` field from an envelope (or mandate). */
export function stripSignature(value: CborValue): CborValue {
  if (value instanceof Map && value.has("signature")) {
    const out = new Map(value);
    out.delete("signature");
    return out;
  }
  return value;
}

/**
 * Compute the §6.3 signing input bytes: Det-CBOR(value without signature).
 * Works on any signed object (envelope, inner mandate, attestation).
 */
export function signingInput(value: CborValue): Uint8Array {
  return detEncode(stripSignature(value));
}

/** SHA-256 of the signing input — the cross-encoding identity digest. */
export function signingInputHash(value: CborValue): string {
  return crypto.createHash("sha256").update(signingInput(value)).digest("hex");
}

/** Read the outer signature-bundle of an envelope, if present. */
export function readSignatureBundle(value: CborValue): {
  alg: string;
  pubkey: Uint8Array;
  sig: Uint8Array;
} | null {
  if (!(value instanceof Map)) return null;
  const bundle = value.get("signature");
  if (!(bundle instanceof Map)) return null;
  const alg = bundle.get("alg");
  const pubkey = bundle.get("pubkey");
  const sig = bundle.get("sig");
  if (typeof alg !== "string" || !(pubkey instanceof Uint8Array) || !(sig instanceof Uint8Array)) {
    return null;
  }
  return { alg, pubkey, sig };
}

/**
 * Verify the outer signature of an envelope against its §6.3 signing input.
 * Returns true/false; false also covers "no signature recoverable".
 */
export function verifyEnvelope(value: CborValue): boolean {
  const bundle = readSignatureBundle(value);
  if (bundle === null) return false;
  return cryptoVerify(bundle.alg, bundle.pubkey, signingInput(value), bundle.sig);
}

/** Attach a freshly computed signature bundle to an envelope using `kp`. */
export function signEnvelope(envelopeNoSig: Envelope, kp: KeyPair, label = "ref"): Envelope {
  const sig = cryptoSign(kp, signingInput(envelopeNoSig), label);
  const bundle = new Map<string, CborValue>([
    ["alg", kp.alg],
    ["pubkey", kp.publicKey],
    ["sig", sig],
  ]);
  const out = new Map(envelopeNoSig);
  out.set("signature", bundle);
  return out;
}

// ---------------------------------------------------------------------------
// Envelope construction helpers (builders for produced interop messages).
// ---------------------------------------------------------------------------

export interface HeaderInput {
  msgType: string;
  msgId: string;
  issuedAt: string;
  expiry: string;
  nonce: Uint8Array;
  grade: number;
  issuer: string;
  subject: string;
}

export function buildHeader(h: HeaderInput): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["version", "Faying Protocol/1.0"],
    ["msg_type", h.msgType],
    ["msg_id", h.msgId],
    ["issued_at", new Tag0(h.issuedAt)],
    ["expiry", new Tag0(h.expiry)],
    ["nonce", h.nonce],
    ["grade", h.grade],
    ["issuer", h.issuer],
    ["subject", h.subject],
  ]);
}

export function buildScope(opts: {
  domains: string[];
  actions: string[];
  terminals?: string[];
}): Map<string, CborValue> {
  const m = new Map<string, CborValue>([
    ["domains", opts.domains as CborValue[]],
    ["actions", opts.actions as CborValue[]],
  ]);
  if (opts.terminals) m.set("terminals", opts.terminals as CborValue[]);
  return m;
}

export function buildPresenceReq(opts: {
  signalTypes: string[];
  maxStalenessMs: number;
  onLoss: string;
}): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["signal-types", opts.signalTypes as CborValue[]],
    ["max-staleness-ms", opts.maxStalenessMs],
    ["on-loss", opts.onLoss],
  ]);
}

export function buildAttestation(kp: KeyPair, label: string): Map<string, CborValue> {
  const payload = new TextEncoder().encode(`faying-attestation-payload:${label}`);
  const sig = cryptoSign(kp, payload, `att-${label}`);
  return new Map<string, CborValue>([
    ["format", "self-signed"],
    ["payload", payload],
    ["signer", `hp:ref-${label}`],
    [
      "signature",
      new Map<string, CborValue>([
        ["alg", kp.alg],
        ["pubkey", kp.publicKey],
        ["sig", sig],
      ]),
    ],
  ]);
}

/** Build an unsigned envelope skeleton (header + claims + attestation). */
export function buildEnvelope(opts: {
  header: HeaderInput;
  claims: Map<string, CborValue>;
  attestation: Map<string, CborValue>;
}): Envelope {
  return new Map<string, CborValue>([
    ["header", buildHeader(opts.header)],
    ["claims", opts.claims],
    ["attestation", opts.attestation],
  ]);
}

// ---------------------------------------------------------------------------
// Endorsement convergence (design.md §11 / §7.5) — used by interop checks.
// ---------------------------------------------------------------------------

const OFFLINE_REVOCATION_POLICIES = ["stop-and-audit", "stop-only", "graceful-stop"];

/** Check that an endorsement converges within a Mandate's scope/grade/lifetime. */
export function endorsementConverges(mandate: Map<string, CborValue>): {
  ok: boolean;
  reason?: string;
} {
  const endorsement = mandate.get("endorsement");
  if (!(endorsement instanceof Map)) return { ok: true };
  const enabled = endorsement.get("enabled");
  if (enabled !== true) return { ok: true };

  const scope = mandate.get("scope");
  const endorsedScope = endorsement.get("endorsed-scope");
  if (scope instanceof Map && endorsedScope instanceof Map) {
    const parentActions = new Set((scope.get("actions") as CborValue[]) ?? []);
    const childActions = (endorsedScope.get("actions") as CborValue[]) ?? [];
    for (const a of childActions) {
      if (!parentActions.has(a)) {
        return { ok: false, reason: `endorsed_scope.actions ⊄ scope.actions (${String(a)})` };
      }
    }
    const parentDomains = new Set((scope.get("domains") as CborValue[]) ?? []);
    const childDomains = (endorsedScope.get("domains") as CborValue[]) ?? [];
    for (const d of childDomains) {
      if (!parentDomains.has(d)) {
        return { ok: false, reason: `endorsed_scope.domains ⊄ scope.domains (${String(d)})` };
      }
    }
  }

  const grade = mandate.get("grade");
  const endorsedGrade = endorsement.get("endorsed-grade");
  if (typeof grade === "number" && typeof endorsedGrade === "number") {
    // autonomy ranking: higher grade number = MORE autonomy.
    // endorsed_grade.autonomy must be <= grade.autonomy (i.e. number <=).
    if (endorsedGrade > grade) {
      return { ok: false, reason: `endorsed_grade.autonomy > grade.autonomy (${endorsedGrade} > ${grade})` };
    }
  }

  const lifetime = endorsement.get("endorsed-lifetime-ms");
  if (typeof lifetime !== "number" || lifetime <= 0) {
    return { ok: false, reason: "endorsed_lifetime_ms missing/non-finite/non-positive" };
  }

  const policy = endorsement.get("offline-revocation-policy");
  if (typeof policy !== "string" || !OFFLINE_REVOCATION_POLICIES.includes(policy)) {
    return { ok: false, reason: `offline_revocation_policy invalid: ${String(policy)}` };
  }
  return { ok: true };
}
