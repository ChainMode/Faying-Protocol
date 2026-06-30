/**
 * =============================================================================
 *  Faying Protocol/1.0 — Reference TypeScript Types (Human-Readable View)
 * =============================================================================
 *
 *  ⚠️  Non-normative human-readable view; the CDDL in fap-1.0.cddl is
 *      authoritative.
 *
 *  This file is the TypeScript reflection of the data models defined in
 *  `design.md §4.1 (核心类型 / TypeScript 视图)` and the envelope structure
 *  in `design.md §5.2 (信封结构)`. It is provided as a developer-friendly
 *  reference for SDK authors, reviewers, and conformance test writers.
 *
 *  Authoritative wire-format schema:
 *      schemas/fap-1.0.cddl  (Normative)
 *
 *  Whenever this file disagrees with the CDDL, the CDDL wins. This module
 *  intentionally omits any runtime validation logic so that consumers can
 *  treat it as pure type metadata.
 *
 *  ---------------------------------------------------------------------------
 *  Field Naming Convention — snake_case (CBOR/CDDL) ↔ camelCase (TypeScript)
 *  ---------------------------------------------------------------------------
 *  The CDDL wire format uses kebab/snake-case for keys (e.g. `mandate-id`,
 *  `not-after`, `endorsed-scope`). The TypeScript reference view in
 *  design.md §4.1 mostly uses snake_case to stay visually close to the wire
 *  representation; we preserve that style here verbatim so reviewers can
 *  compare line-for-line.
 *
 *  When an SDK serialises one of these objects to canonical CBOR/JSON, it
 *  MUST map the property names exactly as shown below to the CDDL keys:
 *
 *      TypeScript (this file)            CDDL key (fap-1.0.cddl)
 *      ─────────────────────────         ───────────────────────
 *      mandate_id                  ↔     mandate-id
 *      issued_at                   ↔     issued-at
 *      not_before                  ↔     not-before
 *      not_after                   ↔     not-after
 *      ms_id                       ↔     ms-id
 *      presence_req                ↔     presence-req
 *      signal_types                ↔     signal-types
 *      max_staleness_ms            ↔     max-staleness-ms
 *      on_loss                     ↔     on-loss
 *      produced_at                 ↔     produced-at
 *      device_id                   ↔     device-id
 *      device_attestation          ↔     device-attestation
 *      time_window                 ↔     time-window
 *      max_invocations             ↔     max-invocations
 *      max_cost_units              ↔     max-cost-units
 *      endorsed_scope              ↔     endorsed-scope
 *      endorsed_grade              ↔     endorsed-grade
 *      endorsed_lifetime_ms        ↔     endorsed-lifetime-ms
 *      offline_revocation_policy   ↔     offline-revocation-policy
 *      msg_type                    ↔     msg-type
 *      msg_id                      ↔     msg-id
 *      target_grade                ↔     target-grade
 *      human_witness               ↔     human-witness
 *      parent_mandate              ↔     parent-mandate
 *      child_subject               ↔     child-subject
 *      child_scope                 ↔     child-scope
 *      child_grade                 ↔     child-grade
 *      effective_at                ↔     effective-at
 *      faying_request_ref          ↔     faying-request-ref
 *      proposed_scope              ↔     proposed-scope
 *      proposed_grade              ↔     proposed-grade
 *      proposed_endorsement        ↔     proposed-endorsement
 *      expected_lifetime_ms        ↔     expected-lifetime-ms
 *      reason_code                 ↔     reason-code
 *      target_human                ↔     target-human
 *      request_msg_id              ↔     request-msg-id
 *      bootstrap_ref               ↔     bootstrap-ref
 *      reject_reason               ↔     reject-reason
 *      scope_used                  ↔     scope-used
 *      risk_level                  ↔     risk-level
 *      affected_resources          ↔     affected-resources
 *      uncertainty_flags           ↔     uncertainty-flags
 *      free_text                   ↔     free-text
 *      endorsement_id              ↔     endorsement-id
 *      device_health               ↔     device-health
 *      secure_element              ↔     secure-element
 *      last_boot_at                ↔     last-boot-at
 *
 *  Some legacy SDKs may prefer idiomatic camelCase (e.g. `mandateId`).
 *  This is permitted *internally* but the on-the-wire representation MUST
 *  use the CDDL key form.
 *
 *  ---------------------------------------------------------------------------
 *  Sources
 *  ---------------------------------------------------------------------------
 *      design.md §4.1   Core types (TypeScript view)
 *      design.md §4.2   CDDL (authoritative)
 *      design.md §5.2   Envelope structure
 *      design.md §5.3   Message claims (BOOTSTRAP / PRESENCE / GRADE_SWITCH /
 *                                       DELEGATE / REVOKE / FAYING_REQUEST /
 *                                       FAYING_REQUEST_RESP / DISCLOSURE)
 *      design.md §5.4   Error codes
 *      design.md §6     Cryptography (signature bundle)
 *
 *  This file MUST compile cleanly under `tsc --strict --noEmit`.
 *  See `tsconfig.json` next to this file for the verification config.
 *
 *  Requirements traceability: 4.1 / 5.1 / 7.1 / 10.1.
 * =============================================================================
 */

// -----------------------------------------------------------------------------
// 1. Primitive aliases
// -----------------------------------------------------------------------------

/** `fay:01HX...Z` — ULID-like identifier of an iFay instance. */
export type FayID = string;

/** `hp:...` — Human Prime identifier; may anchor to a WebAuthn credentialId. */
export type HumanPrimeID = string;

/** ULID-form Mandate identifier. */
export type MandateID = string;

/** RFC 3339 / ISO 8601 timestamp string (CBOR tag 0 on the wire). */
export type IsoTime = string;

/** 16-byte cryptographic nonce. */
export type Nonce = Uint8Array;

/**
 * Canonical name of an action exposed through `Scope.actions`.
 *
 * Per design.md §9.10.3 (T2 Atomic_Action) the protocol forbids wildcards or
 * prefix matching — every action MUST be a fully-qualified, single-purpose
 * verb such as `control:drone:takeoff` or `read:user-profile`.
 */
export type AtomicAction = string;

// -----------------------------------------------------------------------------
// 2. Authorization grade & scope
// -----------------------------------------------------------------------------

/**
 * Authorization grade.
 *
 * Numerically lower values are MORE strict (less autonomous). G0 is the
 * Emergency Override sentinel; G1..G4 form the regular continuum.
 */
export enum Grade {
  /** G0 — Emergency Override (suspends Mandate). */
  EmergencyOverride = 0,
  /** G1 — Strict. */
  Strict = 1,
  /** G2 — Moderate. */
  Moderate = 2,
  /** G3 — Loose. */
  Loose = 3,
  /** G4 — Autonomous. */
  Autonomous = 4,
}

/**
 * Recognised presence-signal channel types.
 *
 * Mirrors the CDDL `presence-signal-type` enumeration in §4.2.
 */
export type PresenceSignalType =
  | "webauthn-uv-fresh"
  | "face-continuous"
  | "fingerprint-tap"
  | "presence-heartbeat-only"
  | "intent-ticket";

/**
 * Policy describing what to do when the bound presence signal goes stale.
 *
 * Free-form string of one of:
 *   - `"downgrade-to:Gx"` where x ∈ {1..4}
 *   - `"suspend"`
 *   - `"emergency-override"`
 *
 * Parsing is performed by the receiver; this view is intentionally a string
 * to mirror the CDDL.
 */
export type OnLossPolicy =
  | `downgrade-to:G${1 | 2 | 3 | 4}`
  | "suspend"
  | "emergency-override";

/** Authorization scope (least-privilege). */
export interface Scope {
  /** Allowed resource domains (URL pattern / SPIFFE-ID-like). */
  domains: string[];
  /** Allowed atomic actions; wildcards are forbidden (§9.10.3 T2). */
  actions: AtomicAction[];
  /** Permitted terminal set (Phase 2 derivation use). */
  terminals?: string[];
  /** Optional resource budget. */
  budget?: ResourceBudget;
}

/** Quantitative budget bound to a Scope. */
export interface ResourceBudget {
  /** [start, end] window during which the scope may be exercised. */
  time_window: [IsoTime, IsoTime];
  /** Maximum number of accepted invocations within the window. */
  max_invocations?: number;
  /** Abstract resource units (currency, inference quota, traffic, …). */
  max_cost_units?: number;
}

// -----------------------------------------------------------------------------
// 3. Presence requirement & signal
// -----------------------------------------------------------------------------

/** Presence requirement bound to a Mandate's grade. */
export interface PresenceRequirement {
  /** Acceptable signal channels; first entry is the preferred channel. */
  signal_types: PresenceSignalType[];
  /** Hard staleness ceiling in milliseconds. */
  max_staleness_ms: number;
  /** Action to take once the signal exceeds `max_staleness_ms`. */
  on_loss: OnLossPolicy;
}

/** A single presence assertion produced by a presence device. */
export interface PresenceSignal {
  mandate_id: MandateID;
  signal_type: PresenceSignalType;
  produced_at: IsoTime;
  /** 16 random bytes; replay-protected by the receiver's seen-set. */
  nonce: Nonce;
  device_id: string;
  device_attestation: Attestation;
  signature: SignatureBundle;
}

// -----------------------------------------------------------------------------
// 4. Attestation & signature bundle
// -----------------------------------------------------------------------------

/** Recognised cryptographic algorithms (default + alternates + PQC). */
export type SignatureAlgorithm = "Ed25519" | "ES256" | "ML-DSA-65";

/**
 * Detached signature with optional cert/parent chain for multi-sign cases
 * (DELEGATE chains, MS counter-signatures, etc.).
 */
export interface SignatureBundle {
  alg: SignatureAlgorithm;
  /** Raw public key bytes; encoded format is alg-specific. */
  pubkey: Uint8Array;
  /** Detached signature bytes over `H(Deterministic-CBOR(payload))`. */
  sig: Uint8Array;
  /** Optional certificate / parent-Mandate chain. */
  chain?: Uint8Array[];
}

/** Pluggable verifiable assertion carrier. */
export interface Attestation {
  format: "webauthn" | "tpm-quote" | "platform-keystore" | "self-signed";
  /** Format-self-describing payload bytes. */
  payload: Uint8Array;
  /** Public-key identifier of the signer. */
  signer: string;
  signature: SignatureBundle;
}

/**
 * Opaque WebAuthn assertion blob carried in BOOTSTRAP / GRADE_SWITCH /
 * FAYING_REQUEST flows. Verification is delegated to a WebAuthn library;
 * the protocol layer only inspects the outcome and `userVerified`/
 * `userPresent` flags.
 */
export interface WebAuthnAssertion {
  /** Base64url-encoded credential ID. */
  credential_id: string;
  /** Raw `authenticatorData` bytes. */
  authenticator_data: Uint8Array;
  /** UTF-8 bytes of the JSON `clientDataJSON` blob. */
  client_data_json: Uint8Array;
  /** Raw `signature` bytes returned by the authenticator. */
  signature: Uint8Array;
  /** Optional `userHandle` (rpId-scoped). */
  user_handle?: Uint8Array;
}

// -----------------------------------------------------------------------------
// 5. Mandate & Endorsement
// -----------------------------------------------------------------------------

/**
 * Endorsed Mandate addendum — pre-committed offline autonomy.
 *
 * Only when `enabled = true` and `(endorsed_scope ⊆ scope ∧
 * endorsed_grade.autonomy ≤ grade.autonomy ∧ endorsed_lifetime_ms ≤
 * not_after − not_before)` may the iFay continue to act on the D-dimension
 * during a perceived disconnection. Accountability never shifts away from
 * `Mandate.issuer` (§4.1, §11.x).
 */
export interface Endorsement {
  enabled: boolean;
  /** MUST be ⊆ Mandate.scope (§11.2 P16.3). */
  endorsed_scope: Scope;
  /** MUST satisfy `endorsed_grade.autonomy ≤ Mandate.grade.autonomy`. */
  endorsed_grade: Grade;
  /** Hard ceiling in ms; MUST be ≤ (Mandate.not_after − Mandate.not_before). */
  endorsed_lifetime_ms: number;
  /** Behaviour to apply if HP REVOKEs while the iFay is still disconnected. */
  offline_revocation_policy:
    | "stop-and-audit"
    | "stop-only"
    | "graceful-stop";
}

/**
 * Mandate — token-replacing core record.
 *
 * Every accepted call MUST resolve to exactly one Mandate whose status is
 * `Active` (or `Disconnected` for `endorsed.enabled = true` paths) at the
 * time of the call.
 */
export interface Mandate {
  version: "Faying Protocol/1.0";
  id: MandateID;
  issued_at: IsoTime;
  not_before: IsoTime;
  /** MUST be finite — open-ended Faying is an anti-pattern (P7). */
  not_after: IsoTime;
  /** Human Prime that bears accountability (or its delegated MS). */
  issuer: HumanPrimeID;
  /** Identifier of the actually-signing Mandate Service. */
  ms_id: string;
  /** Subject — the iFay being authorised. */
  subject: FayID;
  scope: Scope;
  grade: Grade;
  presence_req: PresenceRequirement;
  /** Set when this Mandate was derived from another via DELEGATE. */
  parent?: MandateID;
  /** Set when this is an Endorsed Mandate (offline autonomy enabled). */
  endorsement?: Endorsement;
  attestation: Attestation;
  /** Detached signature; signs `Deterministic-CBOR(this − signature)`. */
  signature: SignatureBundle;
}

// -----------------------------------------------------------------------------
// 6. Protocol envelope (§5.2)
// -----------------------------------------------------------------------------

/**
 * Discriminator for every Faying Protocol message that crosses a boundary.
 *
 * Mirrors design.md §5.2; the wire format encodes this as a tstr.
 */
export type FayingProtocolMsgType =
  | "BOOTSTRAP"
  | "BOOTSTRAP_RESP"
  | "PRESENCE"
  | "PRESENCE_ACK"
  | "GRADE_SWITCH"
  | "GRADE_SWITCH_RESP"
  | "DELEGATE"
  | "DELEGATE_RESP"
  | "REVOKE"
  | "REVOKE_RECEIPT"
  | "FAYING_REQUEST"
  | "FAYING_REQUEST_RESP"
  | "DISCLOSURE"
  | "ERROR";

/**
 * Generic envelope wrapping every protocol message.
 *
 * The detached signature in `signature` covers the `Deterministic-CBOR`
 * encoding of the envelope with `signature` removed (see §6.3).
 */
export interface FayingProtocolEnvelope<TPayload> {
  header: {
    version: "Faying Protocol/1.0";
    msg_type: FayingProtocolMsgType;
    /** ULID. */
    msg_id: string;
    issued_at: IsoTime;
    expiry: IsoTime;
    nonce: Nonce;
    /** Current session grade — used by RPs to fast-reject under-graded calls. */
    grade: Grade;
    /** Originating party (HP or service principal). */
    issuer: HumanPrimeID | string;
    subject: FayID;
  };
  claims: TPayload;
  attestation: Attestation;
  signature: SignatureBundle;
}

// -----------------------------------------------------------------------------
// 7. Message claim payloads (§5.3)
// -----------------------------------------------------------------------------

/** §5.3.1 — BOOTSTRAP. */
export interface BootstrapClaims {
  human_prime: HumanPrimeID;
  fay: FayID;
  scope: Scope;
  grade: Grade;
  presence_req: PresenceRequirement;
  /** MUST be finite. */
  not_after: IsoTime;
  /** WebAuthn assertion with `userVerification = true`. */
  human_witness: WebAuthnAssertion;
  /** Optional — present iff this BOOTSTRAP issues an Endorsed Mandate. */
  endorsement?: Endorsement;
  /** Set when responding to an IF-initiated FAYING_REQUEST. */
  faying_request_ref?: string;
}

/** §5.3.2 — PRESENCE. */
export interface PresenceClaims {
  mandate_id: MandateID;
  signal: PresenceSignal;
  device_health: {
    secure_element: boolean;
    tampered: boolean;
    last_boot_at: IsoTime;
  };
}

/** §5.3.3 — GRADE_SWITCH. */
export interface GradeSwitchClaims {
  mandate_id: MandateID;
  target_grade: Grade;
  reason: "human-initiated" | "presence-loss" | "policy-trigger";
  /** REQUIRED when target_grade increases autonomy; optional on downgrade. */
  human_witness?: WebAuthnAssertion;
}

/** §5.3.4 — DELEGATE. */
export interface DelegateClaims {
  parent_mandate: MandateID;
  child_subject: FayID;
  /** MUST be ⊆ parent.scope. */
  child_scope: Scope;
  /** MUST satisfy autonomy(child_grade) ≤ autonomy(parent.grade). */
  child_grade: Grade;
  /** Bound terminal id when this is a cross-device derivation. */
  device_id?: string;
}

/** §5.3.5 — REVOKE. */
export interface RevokeClaims {
  mandate_id: MandateID;
  /** When true, cascades to the entire derivation subtree (default true). */
  cascade: boolean;
  reason: RevokeReason;
  /** Defaults to "now"; future timestamps allow scheduled revocation. */
  effective_at: IsoTime;
}

/** Enumerated RevokeReason matched to the nine triggers in blueprint ch.13. */
export type RevokeReason =
  | "human-initiated"
  | "expiry"
  | "task-completed"
  | "human-prime-unreachable"
  | "ego-deviation"
  | "fay-credential-invalid"
  | "human-prime-credential-invalid"
  | "regulatory-order"
  | "terminal-disconnected";

/** §5.3.6 — FAYING_REQUEST (IF-initiated bidirectional Faying request). */
export interface FayingRequestClaims {
  /** The iFay sending the request. */
  initiator: FayID;
  /** The Human Prime whose acknowledgement is required to take effect. */
  target_human: HumanPrimeID;
  proposed_scope: Scope;
  proposed_grade: Grade;
  /** Free-form rationale (display to HP). */
  reason: string;
  reason_code:
    | "establish"
    | "adjust-scope"
    | "adjust-grade"
    | "renew"
    | "endorsement-request";
  /** Desired Mandate lifetime; the issued Mandate may have a shorter one. */
  expected_lifetime_ms?: number;
  /** Set when the request also seeks an Endorsed Mandate. */
  proposed_endorsement?: Endorsement;
}

/** §5.3.6 — FAYING_REQUEST_RESP. */
export interface FayingRequestRespClaims {
  /** Echoes the originating FAYING_REQUEST.msg_id. */
  request_msg_id: string;
  status: "accepted" | "rejected" | "timeout";
  /** Set when status="accepted"; references the BOOTSTRAP that took effect. */
  bootstrap_ref?: string;
  reject_reason?: string;
}

/** §5.3.7 — DISCLOSURE (structured disclosure report). */
export interface DisclosureClaims {
  mandate_id: MandateID;
  // ----- mandatory fields (§9.10.4 T3) -----
  action: AtomicAction;
  scope_used: Scope;
  risk_level: "low" | "normal" | "high" | "critical";
  reversibility: "reversible" | "partially-reversible" | "irreversible";
  affected_resources: string[];
  uncertainty_flags: string[];
  // ----- optional supplements -----
  free_text?: string;
  intent?: "report" | "request-confirmation";
  /** Set when the action occurred during a Disconnected window. */
  endorsement_id?: string;
}

/** §5.3 — ERROR (response carrier for §5.4 error codes). */
export interface ErrorClaims {
  /** Numeric error code from §5.4 (1001..1099). */
  code: ErrorCode;
  /** Stable mnemonic name (e.g. "E_NO_MANDATE"). */
  name: ErrorName;
  /** Optional human-readable detail; MUST NOT leak sensitive material. */
  detail?: string;
}

// -----------------------------------------------------------------------------
// 8. Error codes (§5.4)
// -----------------------------------------------------------------------------

/** Numeric error code domain. */
export type ErrorCode =
  | 1001
  | 1002
  | 1003
  | 1004
  | 1005
  | 1006
  | 1007
  | 1008
  | 1009
  | 1010
  | 1011
  | 1012
  | 1013
  | 1014
  | 1099;

/** Stable mnemonic name aligned 1:1 with `ErrorCode`. */
export type ErrorName =
  | "E_NO_MANDATE"
  | "E_MANDATE_EXPIRED"
  | "E_SCOPE_VIOLATION"
  | "E_GRADE_INSUFFICIENT"
  | "E_PRESENCE_STALE"
  | "E_REVOKED"
  | "E_ATTESTATION_INVALID"
  | "E_RR_UNAVAILABLE"
  | "E_REPLAY"
  | "E_HUMAN_WITNESS_REQUIRED"
  | "E_ROGUE_DETECTED"
  | "E_BUDGET_EXCEEDED"
  | "E_ENDORSEMENT_INVALID"
  | "E_FAYING_REQUEST_NOT_CONFIRMED"
  | "E_PROTOCOL";

/**
 * Convenience map from `ErrorCode` to `ErrorName`. SDKs MAY use this for
 * pretty-printing; the wire format only carries the numeric code plus the
 * mnemonic string in `ErrorClaims`.
 */
export const ERROR_NAME_BY_CODE: Readonly<Record<ErrorCode, ErrorName>> = {
  1001: "E_NO_MANDATE",
  1002: "E_MANDATE_EXPIRED",
  1003: "E_SCOPE_VIOLATION",
  1004: "E_GRADE_INSUFFICIENT",
  1005: "E_PRESENCE_STALE",
  1006: "E_REVOKED",
  1007: "E_ATTESTATION_INVALID",
  1008: "E_RR_UNAVAILABLE",
  1009: "E_REPLAY",
  1010: "E_HUMAN_WITNESS_REQUIRED",
  1011: "E_ROGUE_DETECTED",
  1012: "E_BUDGET_EXCEEDED",
  1013: "E_ENDORSEMENT_INVALID",
  1014: "E_FAYING_REQUEST_NOT_CONFIRMED",
  1099: "E_PROTOCOL",
};

// -----------------------------------------------------------------------------
// 9. Concrete envelope aliases (one per msg_type)
// -----------------------------------------------------------------------------

export type BootstrapEnvelope = FayingProtocolEnvelope<BootstrapClaims>;
export type BootstrapRespEnvelope = FayingProtocolEnvelope<Mandate>;
export type PresenceEnvelope = FayingProtocolEnvelope<PresenceClaims>;
export type PresenceAckEnvelope = FayingProtocolEnvelope<{ mandate_id: MandateID }>;
export type GradeSwitchEnvelope = FayingProtocolEnvelope<GradeSwitchClaims>;
export type GradeSwitchRespEnvelope = FayingProtocolEnvelope<{
  mandate_id: MandateID;
  effective_grade: Grade;
}>;
export type DelegateEnvelope = FayingProtocolEnvelope<DelegateClaims>;
export type DelegateRespEnvelope = FayingProtocolEnvelope<Mandate>;
export type RevokeEnvelope = FayingProtocolEnvelope<RevokeClaims>;
export type RevokeReceiptEnvelope = FayingProtocolEnvelope<{
  mandate_id: MandateID;
  effective_at: IsoTime;
}>;
export type FayingRequestEnvelope = FayingProtocolEnvelope<FayingRequestClaims>;
export type FayingRequestRespEnvelope =
  FayingProtocolEnvelope<FayingRequestRespClaims>;
export type DisclosureEnvelope = FayingProtocolEnvelope<DisclosureClaims>;
export type ErrorEnvelope = FayingProtocolEnvelope<ErrorClaims>;

/**
 * Discriminated union over every well-formed Faying Protocol message.
 *
 * Receivers should switch on `header.msg_type` to narrow the union; this
 * tagging mirrors the CDDL `msg-type` field exactly.
 */
export type FayingProtocolMessage =
  | BootstrapEnvelope
  | BootstrapRespEnvelope
  | PresenceEnvelope
  | PresenceAckEnvelope
  | GradeSwitchEnvelope
  | GradeSwitchRespEnvelope
  | DelegateEnvelope
  | DelegateRespEnvelope
  | RevokeEnvelope
  | RevokeReceiptEnvelope
  | FayingRequestEnvelope
  | FayingRequestRespEnvelope
  | DisclosureEnvelope
  | ErrorEnvelope;

// -----------------------------------------------------------------------------
// 10. Backwards-compatible legacy aliases
// -----------------------------------------------------------------------------
//
// design.md §1.1 deprecates the historical "FAP" / "Faying Auth Protocol"
// nomenclature in favour of "Faying Protocol/1.0". The aliases below are
// provided strictly so that early SDK consumers can migrate without a
// breaking rename — they MUST NOT appear in new code, on the wire, or in
// public APIs.
//
// They are intentionally `type` aliases (zero runtime impact).
// -----------------------------------------------------------------------------

/** @deprecated Use `FayingProtocolEnvelope<T>` instead. */
export type FapEnvelope<TPayload> = FayingProtocolEnvelope<TPayload>;

/** @deprecated Use `FayingProtocolMsgType` instead. */
export type FapMsgType = FayingProtocolMsgType;

/** @deprecated Use `Grade` instead. */
export type FapGrade = Grade;
