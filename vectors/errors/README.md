# `vectors/errors/` — Error-Code Test Vectors

> **Spec authority**: [`docs/zh-CN/specification/draft/Faying-Protocol-1.0.md`](../../docs/zh-CN/specification/draft/Faying-Protocol-1.0.md) §5.4 (error code table) and §10 / §EH.1 / §EH.3 / §EH.4 (Error Handling).
>
> **Task**: `tasks.md` 3.6 — *错误码 test vectors（覆盖 12 项错误码）*. The task heading says "12"; design.md §5.4 (and the spec doc §5.4 / §EH.1) actually defines **15 codes** (`1001`–`1014` + `1099`). This vector set covers all 15.

## What this directory provides

For every error code listed in §5.4, this directory ships **at least one trigger vector** plus the expected `ERROR` envelope and the audit / HP-view contract:

| Layout | Purpose |
| --- | --- |
| `<code>-<NAME>/trigger.cbor` | The request that triggers the error, encoded with RFC 8949 §4.2.1 deterministic CBOR. |
| `<code>-<NAME>/trigger.json` | Same payload as JSON (non-normative debug fallback per §5.1). |
| `<code>-<NAME>/error.cbor` | The expected `ERROR` envelope per §5.2 / §5.4 (CBOR, deterministic). |
| `<code>-<NAME>/error.json` | Same envelope as JSON. |
| `<code>-<NAME>/expected.json` | Machine-readable expectations: `code`, `name`, `audit-log-entry` (5-tuple), `must-push-hp-view` boolean, plus EARS trace and spec anchors. |
| `index.json` | Directory index: every covered error code with file paths and SHA-256 of the CBOR artifacts. |
| `_generator.py` | Deterministic generator. Run with `python3 _generator.py` to regenerate the vectors verbatim. |
| `_verify.py` | Acceptance checker. Run with `python3 _verify.py`; exits 0 when all 15 vectors round-trip and obey §EH.3 sensitive-info hygiene. |

## Coverage matrix

The 15 covered codes — exactly the union of §5.4 rows:

| Code | Name | Trigger msg_type | Audit | HP view |
| ---: | --- | --- | :---: | :---: |
| 1001 | `E_NO_MANDATE` | `BUSINESS_CALL` | ✗ | ✗ |
| 1002 | `E_MANDATE_EXPIRED` | `BUSINESS_CALL` | ✓ | ✗ |
| 1003 | `E_SCOPE_VIOLATION` | `BUSINESS_CALL` | ✓ | ✗ |
| 1004 | `E_GRADE_INSUFFICIENT` | `BUSINESS_CALL` | ✓ | ✗ |
| 1005 | `E_PRESENCE_STALE` | `BUSINESS_CALL` | ✓ | ✗ |
| 1006 | `E_REVOKED` | `BUSINESS_CALL` | ✓ | ✓ |
| 1007 | `E_ATTESTATION_INVALID` | `BUSINESS_CALL` | ✓ | ✓ |
| 1008 | `E_RR_UNAVAILABLE` | `BUSINESS_CALL` | ✓ | ✗ |
| 1009 | `E_REPLAY` | `PRESENCE` | ✓ | ✓ |
| 1010 | `E_HUMAN_WITNESS_REQUIRED` | `GRADE_SWITCH` | ✓ | ✗ |
| 1011 | `E_ROGUE_DETECTED` | `DISCLOSURE` | ✓ | ✓ |
| 1012 | `E_BUDGET_EXCEEDED` | `BUSINESS_CALL` | ✓ | ✗ |
| 1013 | `E_ENDORSEMENT_INVALID` | `BOOTSTRAP` | ✓ | ✓ |
| 1014 | `E_FAYING_REQUEST_NOT_CONFIRMED` | `FAYING_REQUEST` | ✓ | ✗ |
| 1099 | `E_PROTOCOL` (DISCLOSURE-path) | `DISCLOSURE` | ✓ | ✓ * |

`*` Per §5.4 footnote, `E_PROTOCOL` defaults to audit-only **except** when triggered from the §5.3.7 DISCLOSURE `mandatory_fields` path, in which case it is also pushed to the HP view. The 1099 vector exercises that DISCLOSURE-path semantics, so its `must-push-hp-view = true`.

## Trigger semantics, per code

The triggers are **schema-level minimal counter-examples** designed to make the field-level cause obvious to a reader:

- **1001** A `BUSINESS_CALL` envelope whose `claims.mandate` is `null` — no Mandate accompanying the call.
- **1002** A Mandate with `not_after = 2024-12-18` against a deterministic `now = 2025-12-17`; trivially expired.
- **1003** Scope `actions = ["read:profile"]` while the call invokes `write:profile`.
- **1004** Mandate `grade = 3` (Loose) while the RP demands `grade = 1` (Strict) for the action.
- **1005** `presence_state.last_freshness` is 600 s old vs `max_staleness_ms = 60_000`.
- **1006** Mandate `mnd:…REVOKED` whose RR query returns `status = revoked, reason = human-initiated`.
- **1007** A Mandate carrying an `endorsement` whose fields were widened *after* signing — signature input no longer matches; per §6.3 S5 the verification step fails.
- **1008** RR query elapsed `6 000 ms`, exceeding the default `StaleBudget = 5 000 ms`.
- **1009** A `PRESENCE` envelope whose nonce is already in the seen-set with `ttl_ms_remaining = 540 000`.
- **1010** A `GRADE_SWITCH` from `current_grade = 3` to `target_grade = 1` (upgrade) lacking the `human_witness` field.
- **1011** A `DISCLOSURE` claiming `action = transfer:funds` while `scope_used.actions` only contains `read:profile`; RP observes the executed action and fires `ego-deviation` → `E_ROGUE_DETECTED`.
- **1012** A Mandate with `scope.budget.max_invocations = 10` and a budget state showing `current_invocations = 11`.
- **1013** A `BOOTSTRAP` whose `endorsement.endorsed_scope` widens beyond `Mandate.scope` (convergence violation).
- **1014** A `FAYING_REQUEST` whose `confirmation_deadline = now − 60 s` and `hp_witness_received = false`.
- **1099** A `DISCLOSURE` missing the `risk_level` mandatory field (§5.3.7).

## What the `ERROR` envelope MUST and MUST NOT contain

Per §5.4 + §EH.3 #3, every `error.{cbor,json}` in this directory:

- Uses `header.msg_type = "ERROR"` and the `claims` body shape `{ code, message, mandate_id?, recovery_hint? }`.
- Carries the public-semantics `message` and (optionally) `recovery_hint` only.
- **Never** includes:
  - MS-internal state (state-machine variables, session secrets, internal counters);
  - private-key material or fingerprints;
  - identifiers belonging to **other** Human Primes than the one already implied by `header.subject`;
  - IF internal state-machine variables.

`_verify.py` enforces this constraint with a recursive substring scan plus an HP-id leak check.

## What `expected.json` declares

For each vector:

```jsonc
{
  "code": <int>,
  "name": "<E_*>",
  "summary": "<§5.4 summary>",
  "audit-log-entry": {                        // null only for 1001 (no Mandate context)
    "error_code": <int>,
    "mandate_id": "<mnd:…>" | null,           // null for 1013 / 1014: no Mandate exists yet
    "ts": "<RFC 3339>",
    "rp_id": "<rp:…>",
    "reason": "<§5.4 summary>"
  },
  "must-push-hp-view": <bool>,                // §EH.3 #2
  "trace": ["R<n>.<m>.<k>", …],               // EARS trace per requirements.md
  "spec_anchors": ["§5.4", "§EH.1", "§EH.3"]
}
```

## Determinism & regeneration

All artifacts are byte-stable:

- CBOR uses `cbor2.dumps(obj, canonical=True)` (RFC 8949 §4.2.1, sorted keys, shortest int forms).
- JSON uses `json.dumps(..., sort_keys=True, indent=2, ensure_ascii=False)`.
- A frozen `T_NOW = "2025-12-17T12:00:00Z"` removes wall-clock drift.

To regenerate:

```bash
python3 vectors/errors/_generator.py
python3 vectors/errors/_verify.py
```

Both scripts are dependency-light: only `cbor2` (already in the PBT environment per `pbt/pyproject.toml`).

## Acceptance check (task 3.6)

- `15/15` error codes covered (the task heading says 12; the spec doc §5.4 / §EH.1 actually has 15, all are emitted).
- ERROR envelopes carry no MS internal state, no private-key fingerprints, and no other-HP identifiers — verified mechanically by `_verify.py`.
- Each vector ships `(trigger.{cbor|json}, error.{cbor|json}, expected.json)` plus the directory-level `index.json`.

## Mapping to spec requirements

| Requirement | Where it lands in this vector set |
| --- | --- |
| `R2.1.*` (default-deny) | 1001 / 1003 / 1008 (no-Mandate / scope / RR-unavailable) |
| `R2.2.4` (mandate finite lifetime) | 1002 |
| `R3.2.*` (audit / HP-view) | every `expected.json` `audit-log-entry` + `must-push-hp-view` |
| `R3.3.*` (HP-view essentials) | 1006 / 1007 / 1009 / 1011 / 1013 vectors set `must-push-hp-view = true` |
| `R4.3.*` (revocation irreversibility) | 1006 (`recovery_hint` mandates *new* `mandate_id`) |
| `R5.1.2` (presence freshness) | 1005 |
| `R9.1.2` (anti-replay) | 1009 |
| `R10.3` (cross-encoding interop) | every vector ships paired `*.cbor` + `*.json` round-trip-equivalent files |
| `R11.1.4` / `R11.2.4` (endorsement integrity / convergence) | 1007 / 1013 |
| `R13.3.1` (DISCLOSURE mandatory fields) | 1099 |
| `R1.3.3` (FAYING_REQUEST timeout) | 1014 |
| `R6.1.2` (witness-required upgrade) | 1010 |

## Out of scope

These vectors deliberately do **not** validate cryptographic signatures end-to-end — `signature` and `attestation` are stubbed with constants of the correct shape. Real crypto verification belongs to:

- `vectors/bootstrap/` (BOOTSTRAP signature chains across Ed25519 / P-256 / ML-DSA-65) — task 3.1;
- `vectors/presence/` (PresenceSignal device attestation freshness) — task 3.2;
- `vectors/encoding-equivalence/` (Deterministic CBOR ↔ JSON signature-input equivalence) — task 3.7.

The error-code corpus exercises the **field-level error trigger conditions** and the **`ERROR` envelope shape** that protocol implementations MUST agree on, irrespective of which crypto stack they bind.
