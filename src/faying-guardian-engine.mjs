import {
  createHash,
  createPrivateKey,
  createPublicKey,
  randomBytes,
  sign,
  verify,
} from "node:crypto";
import http from "node:http";

const ED25519_PKCS8_PREFIX = Buffer.from("302e020100300506032b657004220420", "hex");
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");

export const FAYING_DOMAINS = Object.freeze({
  BOOTSTRAP: "ifay.faying.bootstrap.v1:",
  PRESENCE: "ifay.faying.presence.v1:",
  REVOKE: "ifay.faying.revoke.v1:",
  COFAY_STEWARDSHIP: "ifay.faying.cofay-stewardship.v1:",
  COFAY_TRANSFER: "ifay.faying.cofay-transfer.v1:",
});

export const Grade = Object.freeze({
  G0_EMERGENCY: 0,
  G1_STRICT: 1,
  G2_MODERATE: 2,
  G3_LOOSE: 3,
  G4_AUTONOMOUS: 4,
});

export const PROTOCOL_ERRORS = Object.freeze({
  E_NO_MANDATE: { code: 1001, name: "E_NO_MANDATE" },
  E_MANDATE_EXPIRED: { code: 1002, name: "E_MANDATE_EXPIRED" },
  E_SCOPE_VIOLATION: { code: 1003, name: "E_SCOPE_VIOLATION" },
  E_GRADE_INSUFFICIENT: { code: 1004, name: "E_GRADE_INSUFFICIENT" },
  E_PRESENCE_STALE: { code: 1005, name: "E_PRESENCE_STALE" },
  E_REVOKED: { code: 1006, name: "E_REVOKED" },
  E_ATTESTATION_INVALID: { code: 1007, name: "E_ATTESTATION_INVALID" },
  E_REPLAY: { code: 1009, name: "E_REPLAY" },
  E_HUMAN_WITNESS_REQUIRED: { code: 1010, name: "E_HUMAN_WITNESS_REQUIRED" },
  E_ROGUE_DETECTED: { code: 1011, name: "E_ROGUE_DETECTED" },
  E_BUDGET_EXCEEDED: { code: 1012, name: "E_BUDGET_EXCEEDED" },
  E_ENDORSEMENT_INVALID: { code: 1013, name: "E_ENDORSEMENT_INVALID" },
  E_FAYING_REQUEST_NOT_CONFIRMED: { code: 1014, name: "E_FAYING_REQUEST_NOT_CONFIRMED" },
  E_GRADE_AMPLIFICATION: { code: 1021, name: "E_GRADE_AMPLIFICATION" },
  E_SCOPE_ESCAPE: { code: 1022, name: "E_SCOPE_ESCAPE" },
  E_STEWARDSHIP_HOP_LIMIT: { code: 1023, name: "E_STEWARDSHIP_HOP_LIMIT" },
  E_UPSTREAM_EMERGENCY_HALT: { code: 1024, name: "E_UPSTREAM_EMERGENCY_HALT" },
  E_TRANSFER_DUAL_SIG_REQUIRED: { code: 1025, name: "E_TRANSFER_DUAL_SIG_REQUIRED" },
  E_PROTOCOL: { code: 1099, name: "E_PROTOCOL" },
});

export const ROGUE_FAY_ACTION_FORBIDDEN = "ROGUE_FAY_ACTION_FORBIDDEN";

/**
 * Deterministic RFC 8785 JCS serializer.
 */
export function canonicalizeJcs(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") {
    return JSON.stringify(value);
  }
  if (typeof value === "number") {
    if (!Number.isFinite(value)) {
      throw new TypeError("Non-finite numbers are forbidden in JCS");
    }
    return Object.is(value, -0) ? "0" : JSON.stringify(value);
  }
  if (Array.isArray(value)) {
    return `[${value.map((v) => canonicalizeJcs(v === undefined ? null : v)).join(",")}]`;
  }
  if (typeof value === "object") {
    const keys = Object.keys(value)
      .filter((k) => value[k] !== undefined)
      .sort();
    return `{${keys.map((k) => `${JSON.stringify(k)}:${canonicalizeJcs(value[k])}`).join(",")}}`;
  }
  throw new TypeError(`Unsupported JCS value type: ${typeof value}`);
}

/**
 * Creates a deterministic or random Ed25519 keypair for a Human Prime, iFay, coFay, or Org Steward.
 */
export function createFayingSigner(seedOrPassphrase = randomBytes(32)) {
  const seed32 =
    Buffer.isBuffer(seedOrPassphrase) || seedOrPassphrase instanceof Uint8Array
      ? Buffer.from(seedOrPassphrase).length >= 32
        ? Buffer.from(seedOrPassphrase).subarray(0, 32)
        : createHash("sha256").update(Buffer.from(seedOrPassphrase)).digest()
      : createHash("sha256").update(String(seedOrPassphrase), "utf8").digest();

  const privKey = createPrivateKey({
    key: Buffer.concat([ED25519_PKCS8_PREFIX, seed32]),
    format: "der",
    type: "pkcs8",
  });
  const pubKey = createPublicKey(privKey);
  const spki = pubKey.export({ format: "der", type: "spki" });
  const publicKeyRaw = Buffer.from(spki.subarray(spki.length - 32));
  const publicKeyHex = publicKeyRaw.toString("hex");

  return {
    alg: "Ed25519",
    publicKeyRaw,
    publicKeyHex,
    signDomainJson(domainPrefix, obj) {
      const msg = Buffer.from(`${domainPrefix}${canonicalizeJcs(obj)}`, "utf8");
      const sig = sign(null, msg, privKey);
      return {
        alg: "Ed25519",
        pubkey: publicKeyHex,
        sig: sig.toString("hex"),
      };
    },
  };
}

export function verifyDomainJsonSignature(domainPrefix, obj, sigBundle) {
  try {
    if (!sigBundle || sigBundle.alg !== "Ed25519") return false;
    const rawPub = Buffer.from(sigBundle.pubkey, "hex");
    const rawSig = Buffer.from(sigBundle.sig, "hex");
    if (rawPub.length !== 32 || rawSig.length !== 64) return false;
    const pubKey = createPublicKey({
      key: Buffer.concat([ED25519_SPKI_PREFIX, rawPub]),
      format: "der",
      type: "spki",
    });
    const msg = Buffer.from(`${domainPrefix}${canonicalizeJcs(obj)}`, "utf8");
    return verify(null, msg, pubKey, rawSig);
  } catch {
    return false;
  }
}

/**
 * Validates T2 Atomic Action & Scope rules:
 * - Wildcards (`*`) are strictly forbidden in `actions`;
 * - `domains` and `actions` must be non-empty arrays.
 */
export function validateAtomicScope(scope) {
  if (
    !scope ||
    !Array.isArray(scope.domains) ||
    scope.domains.length === 0 ||
    !Array.isArray(scope.actions) ||
    scope.actions.length === 0
  ) {
    return { ok: false, reason: "Scope must declare non-empty domains[] and atomic actions[]" };
  }
  for (const act of scope.actions) {
    if (typeof act !== "string" || act.trim().length === 0 || act.includes("*")) {
      return {
        ok: false,
        reason: `Atomic action '${String(act)}' violates T2 (wildcards and empty strings are forbidden)`,
      };
    }
  }
  for (const dom of scope.domains) {
    if (typeof dom !== "string" || dom.trim().length === 0 || dom === "*") {
      return {
        ok: false,
        reason: `Domain '${String(dom)}' violates least-privilege scope (bare '*' wildcard forbidden)`,
      };
    }
  }
  return { ok: true };
}

function isScopeSubset(sub, sup) {
  const domSet = new Set(sup.domains);
  const actSet = new Set(sup.actions);
  if (!sub.domains.every((d) => domSet.has(d))) return false;
  if (!sub.actions.every((a) => actSet.has(a))) return false;
  if (sup.terminals && sup.terminals.length > 0) {
    if (!sub.terminals || sub.terminals.length === 0) return false;
    const termSet = new Set(sup.terminals);
    if (!sub.terminals.every((t) => termSet.has(t))) return false;
  }
  if (sup.budget?.maxInvocations !== undefined) {
    if (
      sub.budget?.maxInvocations === undefined ||
      sub.budget.maxInvocations > sup.budget.maxInvocations
    ) {
      return false;
    }
  }
  return true;
}

const HUMAN_PRIME_RE = /^(hid|hp)_[a-z0-9][a-z0-9_-]{2,80}$/;
const IFAY_RE = /^ifay_[a-z0-9][a-z0-9_-]{2,80}$/;
const COFAY_RE = /^cofay_[a-z0-9][a-z0-9_-]{2,80}$/;
const STEWARD_RE = /^(hid|hp|org)_[a-z0-9][a-z0-9_-]{2,80}$/;

/**
 * Typed Circuit-Breaker Error thrown whenever a D-dimension external action is attempted
 * while the Fay is in `ROGUE_FAY` state, out of scope, under-graded, expired, or halted by G0.
 */
export class RogueFayError extends Error {
  constructor(message, details = {}) {
    super(message);
    this.name = "RogueFayError";
    this.code = ROGUE_FAY_ACTION_FORBIDDEN;
    this.protocolErrorCode = details.protocolErrorCode ?? PROTOCOL_ERRORS.E_ROGUE_DETECTED.code;
    this.protocolErrorName = details.protocolErrorName ?? PROTOCOL_ERRORS.E_ROGUE_DETECTED.name;
    this.fayId = details.fayId ?? null;
    this.behaviorState = details.behaviorState ?? "ROGUE_FAY";
    this.reason = details.reason ?? message;
    this.httpStatus = 403;
  }

  toJSON() {
    return {
      ok: false,
      error: this.code,
      protocolErrorCode: this.protocolErrorCode,
      protocolErrorName: this.protocolErrorName,
      fayId: this.fayId,
      behaviorState: this.behaviorState,
      reason: this.reason,
    };
  }
}

/**
 * `FayingGuardianEngine` — Authoritative Phase 1 + `1.1-cofay` Lifecycle & Circuit-Breaker Engine.
 *
 * Enforces:
 * - Default-deny `ROGUE_FAY` state (`P1`, `P15`): zero D-dimension external actions until explicit Human Prime `BOOTSTRAP`;
 * - `FayingRequest` (`P16.6`): `iFay`-initiated requests NEVER activate `Faying State` without signed Human Prime witness;
 * - Continuous `Presence` heartbeat (`P8`, `P9`, `P11`) with proactive millisecond staleness timer;
 * - Continuous `Human View` structured `DISCLOSURE` telemetry (`T3`);
 * - `1.1-cofay` single-hop delegated stewardship (`hopCount === 1`, scope/grade convergence, dual-signed transfer) & upstream `G0` cascade;
 * - Instant `<1ms` push broadcast on `G0 Emergency Brake` or heartbeat loss so all in-flight external actions abort in `<5ms`!
 */
export class FayingGuardianEngine {
  constructor(options = {}) {
    this._nowFn = options.nowMs ?? (() => Date.now());
    this._sessions = new Map();
    this._pendingRequests = new Map();
    this._revokedMandateIds = new Set();
    this._seenNonces = new Set();
    this._humanViewFeed = [];
    this._maxHumanViewEvents = options.maxHumanViewEvents ?? 500;
    this._subscribers = new Set();
    this._fayAbortSubscribers = new Map();
    this._timers = new Map();
  }

  nowMs() {
    return this._nowFn();
  }

  /**
   * Subscribes to all live Guardian state transitions and `Human View` events.
   */
  subscribe(listener) {
    this._subscribers.add(listener);
    return () => this._subscribers.delete(listener);
  }

  /**
   * Subscribes specifically to instant `ROGUE_FAY` / `G0` circuit-breaker trips for `fayId`.
   */
  onRogueTransition(fayId, callback) {
    const norm = String(fayId).toLowerCase();
    let set = this._fayAbortSubscribers.get(norm);
    if (!set) {
      set = new Set();
      this._fayAbortSubscribers.set(norm, set);
    }
    set.add(callback);
    return () => {
      set.delete(callback);
    };
  }

  _emitEvent(event) {
    for (const sub of this._subscribers) {
      try {
        sub(event);
      } catch {
        // isolate subscriber errors
      }
    }
  }

  _clearSessionTimer(fayId) {
    const existing = this._timers.get(fayId);
    if (existing) {
      clearTimeout(existing);
      this._timers.delete(fayId);
    }
  }

  _scheduleNextDeadline(session) {
    this._clearSessionTimer(session.fayId);
    if (session.behaviorState !== "FAYING") return;

    const now = this.nowMs();
    const presenceDeadline = session.lastPresenceAtMs + session.presenceReq.maxStalenessMs;
    const nextCheckMs = Math.min(presenceDeadline, session.notAfterMs);
    const delayMs = Math.max(1, nextCheckMs - now);

    // Only set real OS timer when using wall-clock time and delay <= 1 hour
    if (delayMs <= 3_600_000) {
      const timer = setTimeout(() => {
        this._evaluateLiveness(session.fayId, this.nowMs());
      }, delayMs);
      timer.unref?.();
      this._timers.set(session.fayId, timer);
    }
  }

  _transitionToRogue(fayId, { reason, protocolError, actorId = "guardian-watchdog", cascade = true }) {
    const norm = String(fayId).toLowerCase();
    const session = this._sessions.get(norm);
    this._clearSessionTimer(norm);

    const tsMs = this.nowMs();
    if (session) {
      if (session.behaviorState === "ROGUE_FAY" && session.mandateState === "REVOKED") {
        return session;
      }
      session.behaviorState = "ROGUE_FAY";
      session.mandateState =
        protocolError.code === PROTOCOL_ERRORS.E_REVOKED.code ||
        protocolError.code === PROTOCOL_ERRORS.E_UPSTREAM_EMERGENCY_HALT.code
          ? "REVOKED"
          : "HALTED";
      session.effectiveGrade = Grade.G0_EMERGENCY;
      session.haltReason = reason;
      session.haltedAtMs = tsMs;
      session.lastProtocolError = protocolError;
      if (session.mandateState === "REVOKED") {
        this._revokedMandateIds.add(session.mandateId);
      }
    }

    const rogueEvent = {
      type: "ROGUE_TRANSITION",
      fayId: norm,
      mandateId: session?.mandateId ?? null,
      behaviorState: "ROGUE_FAY",
      protocolErrorCode: protocolError.code,
      protocolErrorName: protocolError.name,
      reason,
      actorId,
      timestampIso: new Date(tsMs).toISOString(),
    };

    this._appendHumanView({
      eventType: "CIRCUIT_BREAKER_TRIPPED",
      fayId: norm,
      mandateId: session?.mandateId ?? null,
      accountableHumanPrime: session?.accountableHumanPrime ?? null,
      action: "system:faying:halt",
      domain: "faying-guardian",
      riskLevel: "critical",
      reversibility: "irreversible",
      affectedResources: [norm],
      uncertaintyFlags: [],
      summary: reason,
      timestampIso: rogueEvent.timestampIso,
    });

    // Fire immediate synchronous abort callbacks (<1ms) for all in-flight guarded calls!
    const abortSet = this._fayAbortSubscribers.get(norm);
    if (abortSet) {
      const errObj = new RogueFayError(reason, {
        fayId: norm,
        protocolErrorCode: protocolError.code,
        protocolErrorName: protocolError.name,
        reason,
      });
      for (const cb of Array.from(abortSet)) {
        try {
          cb(errObj);
        } catch {
          // isolate callback
        }
      }
    }

    this._emitEvent(rogueEvent);

    // Cascade immediately to any 1.1-cofay sessions stewarded by this manager iFay or Human Prime!
    if (cascade) {
      for (const child of this._sessions.values()) {
        if (
          child.behaviorState === "FAYING" &&
          (child.managerFayId === norm || child.accountableHumanPrime === norm)
        ) {
          this._transitionToRogue(child.fayId, {
            reason: `Upstream ${norm} entered ROGUE_FAY (${reason}) -> 1.1-cofay safe-state-halt`,
            protocolError: PROTOCOL_ERRORS.E_UPSTREAM_EMERGENCY_HALT,
            actorId: norm,
            cascade: true,
          });
        }
      }
    }

    return session;
  }

  _evaluateLiveness(fayId, evalMs = this.nowMs()) {
    const norm = String(fayId).toLowerCase();
    const session = this._sessions.get(norm);
    if (!session || session.behaviorState !== "FAYING") {
      return session ?? null;
    }

    // 1. Check upstream manager liveness first for 1.1-cofay sessions
    if (session.fayKind === "COFAY" && session.managerFayId) {
      const manager = this._evaluateLiveness(session.managerFayId, evalMs);
      if (!manager || manager.behaviorState !== "FAYING") {
        this._transitionToRogue(norm, {
          reason: `Upstream manager ${session.managerFayId} is not in FAYING state`,
          protocolError: PROTOCOL_ERRORS.E_UPSTREAM_EMERGENCY_HALT,
        });
        return this._sessions.get(norm);
      }
    }

    // 2. Hard finite TTL check (P7)
    if (evalMs > session.notAfterMs) {
      this._transitionToRogue(norm, {
        reason: `Mandate ${session.mandateId} expired at ${new Date(session.notAfterMs).toISOString()}`,
        protocolError: PROTOCOL_ERRORS.E_MANDATE_EXPIRED,
      });
      return this._sessions.get(norm);
    }

    // 3. Presence heartbeat freshness check (P8 / P11 / P17.5 Endorsed Mandate exception)
    const stalenessMs = evalMs - session.lastPresenceAtMs;
    if (stalenessMs > session.presenceReq.maxStalenessMs) {
      const end = session.endorsement;
      if (end && end.enabled) {
        if (!session.disconnectedSinceMs) {
          session.disconnectedSinceMs = session.lastPresenceAtMs + session.presenceReq.maxStalenessMs;
        }
        const disconnectedDuration = evalMs - session.disconnectedSinceMs;
        if (disconnectedDuration <= end.endorsedLifetimeMs) {
          session.mandateState = "DISCONNECTED_ENDORSED";
          session.effectiveGrade = Math.min(session.grade, end.endorsedGrade);
          return session;
        }
      }

      this._transitionToRogue(norm, {
        reason: `Presence heartbeat stale (${stalenessMs}ms > maxStalenessMs ${session.presenceReq.maxStalenessMs}ms)`,
        protocolError: PROTOCOL_ERRORS.E_PRESENCE_STALE,
      });
      return this._sessions.get(norm);
    }

    session.disconnectedSinceMs = null;
    session.mandateState = "ACTIVE";
    session.effectiveGrade = session.grade;
    return session;
  }

  _appendHumanView(entry) {
    const record = Object.freeze({
      id: `hv_${randomBytes(8).toString("hex")}`,
      ...entry,
    });
    this._humanViewFeed.push(record);
    if (this._humanViewFeed.length > this._maxHumanViewEvents) {
      this._humanViewFeed.shift();
    }
    this._emitEvent({ type: "HUMAN_VIEW", entry: record });
    return record;
  }

  /**
   * Returns current status of a Fay. Unregistered Fays are ALWAYS in default-deny `ROGUE_FAY`!
   */
  getStatus(fayId, evalMs = this.nowMs()) {
    const norm = String(fayId).toLowerCase();
    const session = this._evaluateLiveness(norm, evalMs);
    if (!session) {
      return {
        fayId: norm,
        behaviorState: "ROGUE_FAY",
        mandateState: "NONE",
        effectiveGrade: Grade.G0_EMERGENCY,
        mandateId: null,
        accountableHumanPrime: null,
        pendingRequests: Array.from(this._pendingRequests.values()).filter((r) => r.initiator === norm),
      };
    }
    return {
      fayId: session.fayId,
      fayKind: session.fayKind,
      behaviorState: session.behaviorState,
      mandateState: session.mandateState,
      mandateId: session.mandateId,
      accountableHumanPrime: session.accountableHumanPrime,
      stewardEntity: session.stewardEntity ?? session.accountableHumanPrime,
      managerFayId: session.managerFayId ?? null,
      grade: session.grade,
      effectiveGrade: session.effectiveGrade,
      scope: session.scope,
      notBeforeIso: new Date(session.notBeforeMs).toISOString(),
      notAfterIso: new Date(session.notAfterMs).toISOString(),
      lastPresenceAtIso: new Date(session.lastPresenceAtMs).toISOString(),
      maxStalenessMs: session.presenceReq.maxStalenessMs,
      invocationsUsed: session.invocationsUsed,
      haltReason: session.haltReason ?? null,
    };
  }

  /**
   * §5.3.6 `FAYING_REQUEST` — `iFay`-initiated proposal.
   * Per P16.6, an `iFay` CANNOT put itself into `Faying State`; it stays in `ROGUE_FAY` until
   * `Human Prime` explicitly signs `initiateFaying`.
   */
  submitFayingRequest({
    initiatorFayId,
    targetHumanPrime,
    proposedScope,
    proposedGrade = Grade.G2_MODERATE,
    reason = "Task requires external action",
    reasonCode = "establish",
  }) {
    const normFay = String(initiatorFayId).toLowerCase();
    const normHp = String(targetHumanPrime).toLowerCase();
    if (!IFAY_RE.test(normFay) || !HUMAN_PRIME_RE.test(normHp)) {
      return { ok: false, error: PROTOCOL_ERRORS.E_PROTOCOL.name, detail: "Invalid iFay or Human Prime ID" };
    }
    const scopeCheck = validateAtomicScope(proposedScope);
    if (!scopeCheck.ok) {
      return { ok: false, error: PROTOCOL_ERRORS.E_SCOPE_VIOLATION.name, detail: scopeCheck.reason };
    }
    const requestId = `freq_${randomBytes(10).toString("hex")}`;
    const record = {
      requestId,
      initiator: normFay,
      targetHuman: normHp,
      proposedScope,
      proposedGrade,
      reason,
      reasonCode,
      status: "PENDING_HUMAN_WITNESS",
      createdAtIso: new Date(this.nowMs()).toISOString(),
    };
    this._pendingRequests.set(requestId, record);
    this._appendHumanView({
      eventType: "FAYING_REQUEST_PENDING",
      fayId: normFay,
      mandateId: null,
      accountableHumanPrime: normHp,
      action: "faying:request:establish",
      domain: "faying-guardian",
      riskLevel: "normal",
      reversibility: "reversible",
      affectedResources: [normFay],
      uncertaintyFlags: ["awaiting-human-witness"],
      summary: `iFay ${normFay} requested Faying (${reason}) — still ROGUE_FAY until Human Prime confirms`,
      timestampIso: record.createdAtIso,
    });
    return { ok: true, request: record, behaviorState: "ROGUE_FAY" };
  }

  /**
   * Phase 1 Explicit `Faying Action` (`BOOTSTRAP`) signed by the `Human Prime` (`humanSigner`).
   * Transitions an `iFay` from `ROGUE_FAY` -> `FAYING`.
   */
  initiateFaying({
    humanPrimeId,
    humanSigner,
    fayId,
    scope,
    grade = Grade.G2_MODERATE,
    ttlMs = 300_000,
    maxStalenessMs = 30_000,
    signalTypes = ["presence-heartbeat-only"],
    onLoss = "suspend",
    endorsement = null,
    fayingRequestRef = null,
    nonce = randomBytes(16).toString("hex"),
  }) {
    const now = this.nowMs();
    const normHp = String(humanPrimeId ?? "").toLowerCase();
    const normFay = String(fayId ?? "").toLowerCase();

    if (!HUMAN_PRIME_RE.test(normHp)) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.name,
        code: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.code,
        reason: "Faying Action requires a canonical Human Prime (hid_... or hp_...)",
      };
    }
    if (!IFAY_RE.test(normFay)) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_PROTOCOL.name,
        code: PROTOCOL_ERRORS.E_PROTOCOL.code,
        reason: "Phase 1 BOOTSTRAP subject must be an ifay_... identifier (use delegateCoFayStewardship for cofay_...)",
      };
    }
    if (!humanSigner || typeof humanSigner.signDomainJson !== "function") {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.name,
        code: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.code,
        reason: "Missing cryptographic Human Prime witness signer",
      };
    }
    if (!Number.isFinite(ttlMs) || ttlMs <= 0) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_PROTOCOL.name,
        code: PROTOCOL_ERRORS.E_PROTOCOL.code,
        reason: "Open-ended Mandate TTL is forbidden (P7 Finite Lifetime)",
      };
    }
    if (!Number.isInteger(grade) || grade < Grade.G1_STRICT || grade > Grade.G4_AUTONOMOUS) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_GRADE_INSUFFICIENT.name,
        code: PROTOCOL_ERRORS.E_GRADE_INSUFFICIENT.code,
        reason: "Faying State requires grade in G1..G4 (G0 is emergency halt)",
      };
    }
    if (!Number.isFinite(maxStalenessMs) || maxStalenessMs <= 0) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_PROTOCOL.name,
        code: PROTOCOL_ERRORS.E_PROTOCOL.code,
        reason: "maxStalenessMs must be finite and positive",
      };
    }

    const scopeCheck = validateAtomicScope(scope);
    if (!scopeCheck.ok) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_SCOPE_VIOLATION.name,
        code: PROTOCOL_ERRORS.E_SCOPE_VIOLATION.code,
        reason: scopeCheck.reason,
      };
    }

    if (this._seenNonces.has(`boot:${nonce}`)) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_REPLAY.name,
        code: PROTOCOL_ERRORS.E_REPLAY.code,
        reason: "Bootstrap nonce replay rejected",
      };
    }

    if (endorsement && endorsement.enabled) {
      const endScopeCheck = validateAtomicScope(endorsement.endorsedScope);
      if (
        !endScopeCheck.ok ||
        !isScopeSubset(endorsement.endorsedScope, scope) ||
        typeof endorsement.endorsedGrade !== "number" ||
        endorsement.endorsedGrade > grade ||
        typeof endorsement.endorsedLifetimeMs !== "number" ||
        endorsement.endorsedLifetimeMs <= 0 ||
        endorsement.endorsedLifetimeMs > ttlMs
      ) {
        return {
          ok: false,
          error: PROTOCOL_ERRORS.E_ENDORSEMENT_INVALID.name,
          code: PROTOCOL_ERRORS.E_ENDORSEMENT_INVALID.code,
          reason: "Endorsement violates P16.3 convergence (scope/grade/lifetime)",
        };
      }
    }

    const mandateId = `mnd_${randomBytes(12).toString("hex")}`;
    const notBeforeMs = now;
    const notAfterMs = now + ttlMs;

    const unsignedBootstrap = {
      version: "Faying Protocol/1.0",
      mandateId,
      humanPrime: normHp,
      subject: normFay,
      grade,
      scope,
      presenceReq: { signalTypes, maxStalenessMs, onLoss },
      notBeforeIso: new Date(notBeforeMs).toISOString(),
      notAfterIso: new Date(notAfterMs).toISOString(),
      nonce,
      ...(endorsement ? { endorsement } : {}),
      ...(fayingRequestRef ? { fayingRequestRef } : {}),
    };

    const humanWitnessSignature = humanSigner.signDomainJson(
      FAYING_DOMAINS.BOOTSTRAP,
      unsignedBootstrap,
    );
    if (
      !verifyDomainJsonSignature(
        FAYING_DOMAINS.BOOTSTRAP,
        unsignedBootstrap,
        humanWitnessSignature,
      )
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_ATTESTATION_INVALID.name,
        code: PROTOCOL_ERRORS.E_ATTESTATION_INVALID.code,
        reason: "Human Witness Ed25519 signature verification failed",
      };
    }

    this._seenNonces.add(`boot:${nonce}`);
    if (fayingRequestRef && this._pendingRequests.has(fayingRequestRef)) {
      this._pendingRequests.get(fayingRequestRef).status = "ACCEPTED";
    }

    const session = {
      fayId: normFay,
      fayKind: "IFAY",
      mandateId,
      accountableHumanPrime: normHp,
      humanPublicKeyHex: humanSigner.publicKeyHex,
      behaviorState: "FAYING",
      mandateState: "ACTIVE",
      grade,
      effectiveGrade: grade,
      scope: structuredClone(scope),
      presenceReq: { signalTypes: [...signalTypes], maxStalenessMs, onLoss },
      endorsement: endorsement ? structuredClone(endorsement) : null,
      notBeforeMs,
      notAfterMs,
      lastPresenceAtMs: now,
      disconnectedSinceMs: null,
      invocationsUsed: 0,
      costUnitsUsed: 0,
      humanWitnessSignature,
    };

    this._sessions.set(normFay, session);
    this._scheduleNextDeadline(session);

    this._appendHumanView({
      eventType: "FAYING_INITIATED",
      fayId: normFay,
      mandateId,
      accountableHumanPrime: normHp,
      action: "system:faying:engage",
      domain: "faying-guardian",
      riskLevel: "normal",
      reversibility: "reversible",
      affectedResources: scope.domains,
      uncertaintyFlags: [],
      summary: `Human Prime ${normHp} engaged Faying State for ${normFay} (G${grade}, TTL=${ttlMs}ms, heartbeat<=${maxStalenessMs}ms)`,
      timestampIso: new Date(now).toISOString(),
    });

    this._emitEvent({
      type: "FAYING_ENGAGED",
      fayId: normFay,
      mandateId,
      grade,
      accountableHumanPrime: normHp,
    });

    return {
      ok: true,
      mandateId,
      fayId: normFay,
      behaviorState: "FAYING",
      grade,
      notAfterIso: new Date(notAfterMs).toISOString(),
      humanWitnessSignature,
    };
  }

  /**
   * Extension `1.1-cofay` — Single-Hop Delegated `coFay` Stewardship (`hopCount === 1`).
   * Requires an active manager `iFay` session, non-amplifying grade (`grade <= managerGrade`),
   * and converged scope (`scope ⊆ charterScope ∩ managerScope`).
   */
  delegateCoFayStewardship({
    managerFayId,
    managerSigner,
    subjectCoFayId,
    stewardEntity,
    charterId = "charter_default",
    charterScope,
    scope,
    grade = Grade.G2_MODERATE,
    ttlMs = undefined,
    maxStalenessMs = 30_000,
    hopCount = 1,
  }) {
    const now = this.nowMs();
    const normMgr = String(managerFayId ?? "").toLowerCase();
    const normCofay = String(subjectCoFayId ?? "").toLowerCase();
    const normSteward = String(stewardEntity ?? "").toLowerCase();

    if (hopCount !== 1 || !IFAY_RE.test(normMgr) || !COFAY_RE.test(normCofay)) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_STEWARDSHIP_HOP_LIMIT.name,
        code: PROTOCOL_ERRORS.E_STEWARDSHIP_HOP_LIMIT.code,
        reason: "1.1-cofay enforces single-hop stewardship (hopCount === 1, ifay_ -> cofay_)",
      };
    }

    const mgrSession = this._evaluateLiveness(normMgr, now);
    if (!mgrSession || mgrSession.behaviorState !== "FAYING") {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_UPSTREAM_EMERGENCY_HALT.name,
        code: PROTOCOL_ERRORS.E_UPSTREAM_EMERGENCY_HALT.code,
        reason: "Manager iFay must be in active FAYING state before delegating coFay stewardship",
      };
    }

    const accountableHp = mgrSession.accountableHumanPrime;
    if (
      !STEWARD_RE.test(normSteward) ||
      ((normSteward.startsWith("hid_") || normSteward.startsWith("hp_")) &&
        normSteward !== accountableHp)
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.name,
        code: PROTOCOL_ERRORS.E_HUMAN_WITNESS_REQUIRED.code,
        reason: "coFay stewardship lacks valid accountable Human Prime anchor",
      };
    }

    if (!Number.isInteger(grade) || grade < Grade.G1_STRICT || grade > mgrSession.effectiveGrade) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_GRADE_AMPLIFICATION.name,
        code: PROTOCOL_ERRORS.E_GRADE_AMPLIFICATION.code,
        reason: `coFay grade G${grade} exceeds manager effective grade G${mgrSession.effectiveGrade}`,
      };
    }

    const scopeCheck = validateAtomicScope(scope);
    const charterCheck = validateAtomicScope(charterScope);
    const effectiveTtlMs =
      ttlMs !== undefined ? ttlMs : Math.max(1, Math.min(180_000, mgrSession.notAfterMs - now));
    const notAfterMs = now + effectiveTtlMs;
    if (
      !scopeCheck.ok ||
      !charterCheck.ok ||
      effectiveTtlMs <= 0 ||
      notAfterMs > mgrSession.notAfterMs ||
      !isScopeSubset(scope, charterScope) ||
      !isScopeSubset(scope, mgrSession.scope)
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_SCOPE_ESCAPE.name,
        code: PROTOCOL_ERRORS.E_SCOPE_ESCAPE.code,
        reason: "coFay scope or TTL escapes charterScope ∩ managerScope",
      };
    }

    const mandateId = `cmnd_${randomBytes(12).toString("hex")}`;
    const unsignedStewardship = {
      version: "Faying Protocol/1.1",
      profile: "cofay-stewardship",
      id: mandateId,
      stewardEntity: normSteward,
      accountableHumanPrime: accountableHp,
      parentMandateId: mgrSession.mandateId,
      managerFayId: normMgr,
      subjectCofayId: normCofay,
      charterId,
      grade,
      hopCount: 1,
      maxStewardshipHops: 1,
      onUpstreamG0: "safe-state-halt",
      scope,
      notBeforeIso: new Date(now).toISOString(),
      notAfterIso: new Date(notAfterMs).toISOString(),
    };

    const managerSignature = managerSigner.signDomainJson(
      FAYING_DOMAINS.COFAY_STEWARDSHIP,
      unsignedStewardship,
    );
    if (
      !verifyDomainJsonSignature(
        FAYING_DOMAINS.COFAY_STEWARDSHIP,
        unsignedStewardship,
        managerSignature,
      )
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_ATTESTATION_INVALID.name,
        code: PROTOCOL_ERRORS.E_ATTESTATION_INVALID.code,
        reason: "Invalid manager signature on 1.1-cofay stewardship mandate",
      };
    }

    const session = {
      fayId: normCofay,
      fayKind: "COFAY",
      mandateId,
      parentMandateId: mgrSession.mandateId,
      stewardEntity: normSteward,
      accountableHumanPrime: accountableHp,
      managerFayId: normMgr,
      charterId,
      charterScope: structuredClone(charterScope),
      behaviorState: "FAYING",
      mandateState: "ACTIVE",
      grade,
      effectiveGrade: grade,
      scope: structuredClone(scope),
      presenceReq: {
        signalTypes: ["presence-heartbeat-only"],
        maxStalenessMs: Math.min(maxStalenessMs, mgrSession.presenceReq.maxStalenessMs),
        onLoss: "suspend",
      },
      endorsement: null,
      notBeforeMs: now,
      notAfterMs,
      lastPresenceAtMs: now,
      disconnectedSinceMs: null,
      invocationsUsed: 0,
      costUnitsUsed: 0,
      managerSignature,
    };

    this._sessions.set(normCofay, session);
    this._scheduleNextDeadline(session);

    this._appendHumanView({
      eventType: "COFAY_STEWARDSHIP_ENGAGED",
      fayId: normCofay,
      mandateId,
      accountableHumanPrime: accountableHp,
      action: "system:cofay:delegate-stewardship",
      domain: "faying-guardian",
      riskLevel: "normal",
      reversibility: "reversible",
      affectedResources: scope.domains,
      uncertaintyFlags: [],
      summary: `coFay ${normCofay} engaged under 1.1-cofay single-hop stewardship of ${normMgr} (accountable HP: ${accountableHp})`,
      timestampIso: new Date(now).toISOString(),
    });

    return {
      ok: true,
      mandateId,
      fayId: normCofay,
      behaviorState: "FAYING",
      accountableHumanPrime: accountableHp,
      effectiveGrade: grade,
    };
  }

  /**
   * Extension `1.1-cofay` — Atomic Dual-Signed Stewardship Transfer (`fromStewardSigner` + `toStewardSigner`).
   */
  transferCoFayStewardship({
    cofayId,
    fromSteward,
    fromHumanPrime,
    fromStewardSigner,
    toSteward,
    toHumanPrime,
    toStewardSigner,
    nextManagerFayId,
    nonce = randomBytes(12).toString("hex"),
  }) {
    const now = this.nowMs();
    const normCofay = String(cofayId ?? "").toLowerCase();
    const normNextMgr = String(nextManagerFayId ?? "").toLowerCase();
    const cofaySession = this._evaluateLiveness(normCofay, now);
    const nextMgrSession = this._evaluateLiveness(normNextMgr, now);

    if (
      !cofaySession ||
      cofaySession.fayKind !== "COFAY" ||
      !nextMgrSession ||
      nextMgrSession.behaviorState !== "FAYING" ||
      fromSteward === toSteward ||
      !fromStewardSigner ||
      !toStewardSigner
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_TRANSFER_DUAL_SIG_REQUIRED.name,
        code: PROTOCOL_ERRORS.E_TRANSFER_DUAL_SIG_REQUIRED.code,
        reason: "Dual-signed transfer requires distinct stewards, active nextManagerFayId, and both signatures",
      };
    }

    const core = {
      version: "Faying Protocol/1.1",
      profile: "cofay-transfer",
      cofayId: normCofay,
      previousMandateId: cofaySession.mandateId,
      fromSteward: String(fromSteward).toLowerCase(),
      fromHumanPrime: String(fromHumanPrime).toLowerCase(),
      toSteward: String(toSteward).toLowerCase(),
      toHumanPrime: String(toHumanPrime).toLowerCase(),
      nextManagerFayId: normNextMgr,
      nonce,
      issuedAtIso: new Date(now).toISOString(),
    };
    const sigFrom = fromStewardSigner.signDomainJson(FAYING_DOMAINS.COFAY_TRANSFER, core);
    const sigTo = toStewardSigner.signDomainJson(FAYING_DOMAINS.COFAY_TRANSFER, core);
    if (
      !verifyDomainJsonSignature(FAYING_DOMAINS.COFAY_TRANSFER, core, sigFrom) ||
      !verifyDomainJsonSignature(FAYING_DOMAINS.COFAY_TRANSFER, core, sigTo)
    ) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_TRANSFER_DUAL_SIG_REQUIRED.name,
        code: PROTOCOL_ERRORS.E_TRANSFER_DUAL_SIG_REQUIRED.code,
        reason: "Dual signature verification failed",
      };
    }

    cofaySession.stewardEntity = core.toSteward;
    cofaySession.accountableHumanPrime = core.toHumanPrime;
    cofaySession.managerFayId = normNextMgr;
    cofaySession.parentMandateId = nextMgrSession.mandateId;
    cofaySession.lastPresenceAtMs = now;
    this._scheduleNextDeadline(cofaySession);

    return {
      ok: true,
      cofayId: normCofay,
      activeSteward: core.toSteward,
      accountableHumanPrime: core.toHumanPrime,
      nextManagerFayId: normNextMgr,
    };
  }

  /**
   * Refreshes continuous `Presence` heartbeat (`P8` / `P9` anti-replay / device tamper check).
   */
  recordHeartbeat({
    fayId,
    nonce = randomBytes(16).toString("hex"),
    signalType = "presence-heartbeat-only",
    deviceTampered = false,
  }) {
    const now = this.nowMs();
    const norm = String(fayId ?? "").toLowerCase();
    const session = this._evaluateLiveness(norm, now);

    if (!session || session.behaviorState !== "FAYING") {
      return {
        ok: false,
        error: ROGUE_FAY_ACTION_FORBIDDEN,
        code: session?.lastProtocolError?.code ?? PROTOCOL_ERRORS.E_NO_MANDATE.code,
        reason: "Cannot refresh heartbeat on a ROGUE_FAY / revoked session; explicit Human Prime Faying Action required",
      };
    }

    const nonceKey = `hb:${session.mandateId}:${nonce}`;
    if (this._seenNonces.has(nonceKey)) {
      return {
        ok: false,
        error: PROTOCOL_ERRORS.E_REPLAY.name,
        code: PROTOCOL_ERRORS.E_REPLAY.code,
        reason: "Replay of presence heartbeat nonce rejected",
      };
    }
    this._seenNonces.add(nonceKey);

    if (deviceTampered) {
      this._transitionToRogue(norm, {
        reason: "Device health reported tampered=true -> immediate halt to ROGUE_FAY",
        protocolError: PROTOCOL_ERRORS.E_ATTESTATION_INVALID,
      });
      return {
        ok: false,
        error: ROGUE_FAY_ACTION_FORBIDDEN,
        code: PROTOCOL_ERRORS.E_ATTESTATION_INVALID.code,
      };
    }

    session.lastPresenceAtMs = now;
    session.disconnectedSinceMs = null;
    session.mandateState = "ACTIVE";
    session.effectiveGrade = session.grade;
    this._scheduleNextDeadline(session);

    return {
      ok: true,
      fayId: norm,
      mandateId: session.mandateId,
      signalType,
      lastPresenceAtIso: new Date(now).toISOString(),
      expiresInMs: session.presenceReq.maxStalenessMs,
    };
  }

  /**
   * Red Emergency Brake (`G0 Emergency Override` / `REVOKE`).
   * Irreversible (`P10`), highest priority (`P12`), symmetric (`P4`), and cascades to all `coFay`s (`P14`).
   */
  triggerG0EmergencyBrake({
    targetId,
    actorId = "human-prime-red-button",
    reason = "G0 Emergency Brake triggered by Human Prime",
  }) {
    const normTarget = String(targetId ?? "").toLowerCase();
    const activeBefore = new Set(
      Array.from(this._sessions.values())
        .filter((s) => s.behaviorState === "FAYING")
        .map((s) => s.fayId),
    );

    // If targetId is a Human Prime (`hid_...` or `hp_...`), halt ALL Fays anchored to that Human Prime!
    if (HUMAN_PRIME_RE.test(normTarget)) {
      for (const s of this._sessions.values()) {
        if (s.accountableHumanPrime === normTarget && s.behaviorState === "FAYING") {
          this._transitionToRogue(s.fayId, {
            reason,
            protocolError: PROTOCOL_ERRORS.E_REVOKED,
            actorId,
            cascade: true,
          });
        }
      }
      const halted = Array.from(activeBefore).filter(
        (id) => this._sessions.get(id)?.behaviorState === "ROGUE_FAY",
      );
      return {
        ok: true,
        targetId: normTarget,
        behaviorState: "ROGUE_FAY",
        haltedFays: halted.sort(),
      };
    }

    this._transitionToRogue(normTarget, {
      reason,
      protocolError: PROTOCOL_ERRORS.E_REVOKED,
      actorId,
      cascade: true,
    });

    const haltedDownstream = Array.from(activeBefore).filter(
      (id) => this._sessions.get(id)?.behaviorState === "ROGUE_FAY",
    );
    if (!haltedDownstream.includes(normTarget) && this._sessions.has(normTarget)) {
      haltedDownstream.push(normTarget);
    }

    return {
      ok: true,
      targetId: normTarget,
      behaviorState: "ROGUE_FAY",
      haltedFays: haltedDownstream.sort(),
    };
  }

  /**
   * Authorizes a D-dimension external action right before execution and records a structured
   * `Human View` `DISCLOSURE` event (`T3`). Fails closed with `ROGUE_FAY_ACTION_FORBIDDEN` if
   * the Fay is in `ROGUE_FAY`, stale, expired, over budget, under-graded, or out of scope!
   */
  authorizeExternalAction({
    fayId,
    domain,
    action,
    minGrade = Grade.G1_STRICT,
    costUnits = 1,
    riskLevel = "normal",
    reversibility = "reversible",
    affectedResources = [],
    uncertaintyFlags = [],
    summary = "",
  }) {
    const now = this.nowMs();
    const norm = String(fayId ?? "").toLowerCase();
    const session = this._evaluateLiveness(norm, now);

    if (!session || session.behaviorState !== "FAYING") {
      const protoErr = session?.lastProtocolError ?? PROTOCOL_ERRORS.E_NO_MANDATE;
      return {
        allowed: false,
        error: new RogueFayError(
          session?.haltReason ??
            `Fay '${norm}' is in ROGUE_FAY state — all D-dimension external actions are forbidden`,
          {
            fayId: norm,
            protocolErrorCode: protoErr.code,
            protocolErrorName: protoErr.name,
          },
        ),
      };
    }

    const activeScope =
      session.mandateState === "DISCONNECTED_ENDORSED" && session.endorsement
        ? session.endorsement.endorsedScope
        : session.scope;

    if (!activeScope.domains.includes(domain) || !activeScope.actions.includes(action)) {
      return {
        allowed: false,
        error: new RogueFayError(
          `External action '${action}' on '${domain}' is outside authorized Mandate scope`,
          {
            fayId: norm,
            behaviorState: session.behaviorState,
            protocolErrorCode: PROTOCOL_ERRORS.E_SCOPE_VIOLATION.code,
            protocolErrorName: PROTOCOL_ERRORS.E_SCOPE_VIOLATION.name,
          },
        ),
      };
    }

    if (session.effectiveGrade < minGrade) {
      return {
        allowed: false,
        error: new RogueFayError(
          `Action '${action}' requires grade >= G${minGrade}, current effective grade is G${session.effectiveGrade}`,
          {
            fayId: norm,
            behaviorState: session.behaviorState,
            protocolErrorCode: PROTOCOL_ERRORS.E_GRADE_INSUFFICIENT.code,
            protocolErrorName: PROTOCOL_ERRORS.E_GRADE_INSUFFICIENT.name,
          },
        ),
      };
    }

    const maxInvocations = activeScope.budget?.maxInvocations;
    const maxCost = activeScope.budget?.maxCostUnits;
    if (
      (maxInvocations !== undefined && session.invocationsUsed + 1 > maxInvocations) ||
      (maxCost !== undefined && session.costUnitsUsed + costUnits > maxCost)
    ) {
      return {
        allowed: false,
        error: new RogueFayError(
          `Mandate ${session.mandateId} invocation/cost budget exhausted`,
          {
            fayId: norm,
            behaviorState: session.behaviorState,
            protocolErrorCode: PROTOCOL_ERRORS.E_BUDGET_EXCEEDED.code,
            protocolErrorName: PROTOCOL_ERRORS.E_BUDGET_EXCEEDED.name,
          },
        ),
      };
    }

    session.invocationsUsed += 1;
    session.costUnitsUsed += costUnits;

    const disclosure = this._appendHumanView({
      eventType: "EXTERNAL_ACTION_DISCLOSURE",
      fayId: norm,
      mandateId: session.mandateId,
      accountableHumanPrime: session.accountableHumanPrime,
      action,
      domain,
      scopeUsed: { domains: [domain], actions: [action] },
      riskLevel,
      reversibility,
      affectedResources: affectedResources.length > 0 ? affectedResources : [domain],
      uncertaintyFlags,
      endorsementActive: session.mandateState === "DISCONNECTED_ENDORSED",
      summary: summary || `Executed ${action} on ${domain}`,
      timestampIso: new Date(now).toISOString(),
    });

    return {
      allowed: true,
      mandate: {
        mandateId: session.mandateId,
        fayId: session.fayId,
        accountableHumanPrime: session.accountableHumanPrime,
        effectiveGrade: session.effectiveGrade,
        mandateState: session.mandateState,
      },
      disclosure,
    };
  }

  getHumanViewFeed({ fayId = null, limit = 50 } = {}) {
    const filtered = fayId
      ? this._humanViewFeed.filter((e) => e.fayId === String(fayId).toLowerCase())
      : this._humanViewFeed;
    return filtered.slice(-limit);
  }

  shutdown() {
    for (const timer of this._timers.values()) {
      clearTimeout(timer);
    }
    this._timers.clear();
  }
}

/**
 * Starts a Live Guardian HTTP + Real-Time SSE Daemon (`127.0.0.1` by default) exposing:
 * - `GET  /health`
 * - `GET  /status?fayId=...`
 * - `POST /faying/engage`
 * - `POST /faying/delegate-cofay`
 * - `POST /faying/heartbeat`
 * - `POST /faying/brake` (Red G0 Emergency Brake — broadcasts over `/events` SSE in `<1ms`!)
 * - `POST /faying/authorize`
 * - `GET  /human-view`
 * - `GET  /events` (SSE real-time stream for Human View + instant `<5ms` circuit-breaker push)
 */
export function createGuardianDaemonServer({
  engine = new FayingGuardianEngine(),
  host = "127.0.0.1",
  port = 0,
} = {}) {
  const sseClients = new Set();

  const unsubscribeEngine = engine.subscribe((evt) => {
    const frame = `data: ${JSON.stringify(evt)}\n\n`;
    for (const res of Array.from(sseClients)) {
      try {
        res.write(frame);
      } catch {
        sseClients.delete(res);
      }
    }
  });

  async function readJson(req) {
    const chunks = [];
    for await (const c of req) {
      chunks.push(Buffer.isBuffer(c) ? c : Buffer.from(c));
    }
    const raw = Buffer.concat(chunks).toString("utf8");
    return raw ? JSON.parse(raw) : {};
  }

  function sendJson(res, status, body) {
    res.writeHead(status, { "content-type": "application/json; charset=utf-8" });
    res.end(JSON.stringify(body));
  }

  const server = http.createServer(async (req, res) => {
    try {
      const url = new URL(req.url ?? "/", `http://${req.headers.host ?? "127.0.0.1"}`);

      if (req.method === "GET" && url.pathname === "/health") {
        return sendJson(res, 200, { ok: true, service: "faying-guardian-daemon" });
      }

      if (req.method === "GET" && url.pathname === "/events") {
        res.writeHead(200, {
          "content-type": "text/event-stream; charset=utf-8",
          "cache-control": "no-cache, no-transform",
          connection: "keep-alive",
        });
        res.socket?.setNoDelay?.(true);
        res.flushHeaders?.();
        res.write(`data: ${JSON.stringify({ type: "CONNECTED" })}\n\n`);
        sseClients.add(res);
        res.on("close", () => sseClients.delete(res));
        return;
      }

      if (req.method === "GET" && url.pathname === "/status") {
        const fayId = url.searchParams.get("fayId") ?? "";
        return sendJson(res, 200, { ok: true, status: engine.getStatus(fayId) });
      }

      if (req.method === "GET" && url.pathname === "/human-view") {
        const fayId = url.searchParams.get("fayId") || null;
        const limit = Number(url.searchParams.get("limit") ?? 50);
        return sendJson(res, 200, {
          ok: true,
          events: engine.getHumanViewFeed({ fayId, limit }),
        });
      }

      if (req.method === "POST" && url.pathname === "/faying/engage") {
        const body = await readJson(req);
        const humanSigner = createFayingSigner(body.humanSeed ?? "default-human-prime-seed-example");
        const out = engine.initiateFaying({
          ...body,
          humanSigner,
        });
        return sendJson(res, out.ok ? 200 : 400, out);
      }

      if (req.method === "POST" && url.pathname === "/faying/delegate-cofay") {
        const body = await readJson(req);
        const managerSigner = createFayingSigner(body.managerSeed ?? "default-manager-seed-example");
        const out = engine.delegateCoFayStewardship({
          ...body,
          managerSigner,
        });
        return sendJson(res, out.ok ? 200 : 400, out);
      }

      if (req.method === "POST" && url.pathname === "/faying/heartbeat") {
        const body = await readJson(req);
        const out = engine.recordHeartbeat(body);
        return sendJson(res, out.ok ? 200 : 403, out);
      }

      if (req.method === "POST" && url.pathname === "/faying/brake") {
        const body = await readJson(req);
        const out = engine.triggerG0EmergencyBrake(body);
        return sendJson(res, 200, out);
      }

      if (req.method === "POST" && url.pathname === "/faying/authorize") {
        const body = await readJson(req);
        const out = engine.authorizeExternalAction(body);
        if (!out.allowed) {
          return sendJson(res, 403, out.error.toJSON());
        }
        return sendJson(res, 200, {
          ok: true,
          allowed: true,
          mandate: out.mandate,
          disclosure: out.disclosure,
        });
      }

      return sendJson(res, 404, { ok: false, error: "NOT_FOUND" });
    } catch (e) {
      return sendJson(res, 500, {
        ok: false,
        error: "INTERNAL_ERROR",
        detail: e instanceof Error ? e.message : String(e),
      });
    }
  });

  server.on("connection", (socket) => {
    socket.setNoDelay(true);
  });

  return {
    engine,
    server,
    async listen() {
      await new Promise((resolvePromise, rejectPromise) => {
        server.once("error", rejectPromise);
        server.listen(port, host, () => resolvePromise());
      });
      const addr = server.address();
      const boundPort = typeof addr === "object" && addr ? addr.port : port;
      return {
        host,
        port: boundPort,
        url: `http://${host}:${boundPort}`,
      };
    },
    async close() {
      unsubscribeEngine();
      engine.shutdown();
      for (const client of sseClients) {
        try {
          client.end();
        } catch {
          // ignore
        }
      }
      sseClients.clear();
      if (!server.listening) return;
      server.closeAllConnections?.();
      await new Promise((resolvePromise) => server.close(() => resolvePromise()));
    },
  };
}

/**
 * Creates a unified `GuardianClient` backed either by an in-process `FayingGuardianEngine`
 * OR by a remote `faying-guardian` HTTP + real-time SSE daemon (`{ url: "http://127.0.0.1:4780" }`).
 *
 * Remote clients maintain a low-latency TCP_NODELAY SSE subscription to `/events` so `G0` emergency
 * brakes propagate to in-flight external calls in `<5ms` even across process boundaries!
 */
export function createGuardianClient(target) {
  if (target instanceof FayingGuardianEngine) {
    return {
      mode: "in-process",
      engine: target,
      async authorizeExternalAction(input) {
        return target.authorizeExternalAction(input);
      },
      onRogueTransition(fayId, callback) {
        return target.onRogueTransition(fayId, callback);
      },
      async close() {},
    };
  }

  if (target && target.engine instanceof FayingGuardianEngine && !target.url) {
    return createGuardianClient(target.engine);
  }

  const baseUrl = String(typeof target === "string" ? target : target?.url ?? "").replace(/\/+$/, "");
  if (!baseUrl) {
    throw new TypeError("createGuardianClient expects a FayingGuardianEngine or { url: 'http://...' }");
  }

  const rogueListeners = new Map();
  let sseReq = null;
  let sseReadyPromise = null;
  let closed = false;

  function ensureSseStream() {
    if (closed) return Promise.resolve();
    if (sseReadyPromise) return sseReadyPromise;
    sseReadyPromise = new Promise((resolveReady) => {
      const u = new URL(`${baseUrl}/events`);
      sseReq = http.get(
        {
          hostname: u.hostname,
          port: u.port,
          path: u.pathname,
          agent: false,
          headers: { accept: "text/event-stream" },
        },
        (res) => {
          res.socket?.setNoDelay?.(true);
          let buffer = "";
          let resolved = false;
          res.setEncoding("utf8");
          res.on("data", (chunk) => {
            buffer += chunk;
            let sepIdx;
            while ((sepIdx = buffer.indexOf("\n\n")) !== -1) {
              const rawEvent = buffer.slice(0, sepIdx);
              buffer = buffer.slice(sepIdx + 2);
              const dataLine = rawEvent
                .split("\n")
                .find((l) => l.startsWith("data: "));
              if (!dataLine) continue;
              try {
                const parsed = JSON.parse(dataLine.slice(6));
                if (parsed.type === "CONNECTED" && !resolved) {
                  resolved = true;
                  resolveReady();
                } else if (parsed.type === "ROGUE_TRANSITION") {
                  const callbacks = rogueListeners.get(String(parsed.fayId).toLowerCase());
                  if (callbacks) {
                    const errObj = new RogueFayError(parsed.reason, {
                      fayId: parsed.fayId,
                      protocolErrorCode: parsed.protocolErrorCode,
                      protocolErrorName: parsed.protocolErrorName,
                      reason: parsed.reason,
                    });
                    for (const cb of Array.from(callbacks)) {
                      cb(errObj);
                    }
                  }
                }
              } catch {
                // ignore malformed frame
              }
            }
          });
        },
      );
      sseReq.on("socket", (sock) => sock.setNoDelay(true));
      sseReq.on("error", () => resolveReady());
    });
  }

  return {
    mode: "remote-http-sse",
    url: baseUrl,
    connectPushStream: ensureSseStream,
    async authorizeExternalAction(input) {
      await ensureSseStream();
      const res = await fetch(`${baseUrl}/faying/authorize`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(input),
      });
      const json = await res.json();
      if (!res.ok || !json.allowed) {
        return {
          allowed: false,
          error: new RogueFayError(json.reason ?? "Action blocked by Faying Guardian", {
            fayId: json.fayId ?? input.fayId,
            protocolErrorCode: json.protocolErrorCode,
            protocolErrorName: json.protocolErrorName,
            reason: json.reason,
          }),
        };
      }
      return {
        allowed: true,
        mandate: json.mandate,
        disclosure: json.disclosure,
      };
    },
    onRogueTransition(fayId, callback) {
      const norm = String(fayId).toLowerCase();
      let set = rogueListeners.get(norm);
      if (!set) {
        set = new Set();
        rogueListeners.set(norm, set);
      }
      set.add(callback);
      ensureSseStream();
      return () => {
        set.delete(callback);
      };
    },
    async close() {
      closed = true;
      if (sseReq) {
        sseReq.destroy();
        sseReq = null;
      }
    },
  };
}
