# REVOKE Test Vectors — Faying Protocol/1.0

This directory holds the official `REVOKE` test vectors for
Faying Protocol/1.0. They exercise the symmetric-revocation path
that closes the Faying lifecycle: every Mandate that BOOTSTRAP can
issue must be reachable by an equally-authenticated REVOKE, must
become visible on the Revocation Registry within
`RevocationVisibilityBudget`, and must remain Revoked forever.

- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §5.3.5 — `REVOKE` wire shape (`mandate_id`, `cascade`, `reason ∈ RevokeReason`, `effective_at`) and `REVOKE_RECEIPT` post-revocation state.
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §3.4 / §9.6 — Revocation Registry visibility within `RevocationVisibilityBudget` (default 1s).
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §4.3 / §8.1 — Mandate state machine: `Revoked` is a terminal state, no `Revoked → Active` transition exists.
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §7.5 / §9.7 — cascade revocation across the derivation subtree.
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §EH.1 / §EH.3 — `1006 E_REVOKED` routes to audit-log and HP view channel (critical bucket).
- Blueprint chapter 13 — the nine `RevokeReason` values exhaustively cover the nine decoupling triggers.

The schema-of-record is [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl); the
`mandate` rule is the same one referenced by every other vector
batch, and `signature-bundle` is reused verbatim.

## Vector matrix (14)

### Positive — one vector per `RevokeReason` (9 vectors)

Every entry covers a single decoupling trigger from blueprint
chapter 13. The directly-revoked Mandate is `cascade=true` by
default, but the descendant set is empty (these vectors revoke a
leaf Mandate; the cascade-tree behaviour is exercised separately
below).

| Vector                                       | `RevokeReason`                     | Trigger / decoupling category                                                  |
| -------------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------ |
| `reason-human-initiated`                     | `human-initiated`                  | HP explicitly initiates REVOKE (Requirement 4.1.3 symmetric path).             |
| `reason-expiry`                              | `expiry`                           | Mandate `not_after` elapses; MS auto-revokes.                                  |
| `reason-task-completed`                      | `task-completed`                   | iFay reports task completion via DISCLOSURE; HP confirms via REVOKE.           |
| `reason-human-prime-unreachable`             | `human-prime-unreachable`          | HP cannot be reached past `HumanReachabilityBudget` (Requirement 9.4.4).       |
| `reason-ego-deviation`                       | `ego-deviation`                    | iFay behaviour outside Ego boundary (Requirement 9.4.5 / §9.10.4 T3).          |
| `reason-fay-credential-invalid`              | `fay-credential-invalid`           | iFay's session key, device attestation, or signature chain failed.             |
| `reason-human-prime-credential-invalid`      | `human-prime-credential-invalid`   | HP's root credential compromised or rotated out.                               |
| `reason-regulatory-order`                    | `regulatory-order`                 | Authoritative regulator order; still made visible through HP's view channel.   |
| `reason-terminal-disconnected`               | `terminal-disconnected`            | Bound terminal disconnected past Reconciliation timeout (§4.3 Disconnected → Revoked). |

### Cascade behaviour (2 vectors)

| Vector                | `cascade` | Tree depth | Receipt `cascaded_mandate_ids`            |
| --------------------- | --------- | ---------: | ----------------------------------------- |
| `cascade-depth-2`     | `true`    |          2 | `[child_id, grandchild_id]` (topological) |
| `cascade-disabled`    | `false`   |          2 | `[]` — descendants stay Active            |

`cascade-depth-2` revokes the parent of a depth-2 derivation tree
(parent G3 → child G2 → grandchild G1) and validates Requirement
7.2 in full:

- 7.2.1 — every descendant is marked Revoked in the same atomic
  transaction;
- 7.2.2 — no NEW DELEGATE referencing the Revoked parent may
  succeed (`E_REVOKED`);
- 7.2.3 — RR pushes REVOKE notifications to every affected RP
  within `RevocationVisibilityBudget`.

`cascade-disabled` documents the explicit override of the §5.3.5
cascade default (`true`). Children remain Active until they
expire on their own `not_after` or are explicitly revoked. The
parent's Revoked state is still terminal.

### Irreversibility documentation (3 vectors)

These three vectors materialise Requirement 4.3 — once a Mandate
is `Revoked`, no implementation may transition it back.

| Vector                                | What it documents                                                                                     |
| ------------------------------------- | ----------------------------------------------------------------------------------------------------- |
| `irreversibility-double-revoke`       | Second REVOKE on a Revoked Mandate is idempotent: the receipt advertises the *original* `revoked_at`. |
| `irreversibility-rebootstrap-new-id`  | Recovery after REVOKE requires a fresh BOOTSTRAP that issues a Mandate with a *different* `mandate_id`, even when (subject, scope) match. |
| `neg-use-after-revoke`                | RP-side use of a Revoked Mandate yields an `ERROR { code:1006, name:"E_REVOKED" }` response and a critical-bucket push to HP's view channel. |

`irreversibility-rebootstrap-new-id` carries the new Mandate's
metadata in `expected.json` (not on the wire) so verifiers can
assert id-disjointness without an extra round trip. The new
`mandate_id` differs from the Revoked one even when the (subject,
scope) pair is identical — Requirement 4.3.3 forbids id reuse.

## Per-vector layout

Each vector lives in its own directory and contains:

| File              | Purpose                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `request.cbor`    | Canonical CBOR (RFC 8949 §4.2.1) encoding of the `REVOKE` envelope, signed by the HP root key (or HP-equivalent for auto-revoke reasons). |
| `request.json`    | Equivalent JSON encoding (`Content-Type: application/faying-protocol+json`) using the `$bytes` / `$tag` markers.         |
| `response.cbor`   | `REVOKE_RECEIPT` envelope (positive) or `ERROR` envelope (negative). Always signed by MS.                                 |
| `response.json`   | JSON encoding of the same response envelope.                                                                             |
| `expected.json`   | `target_mandate_id`, `cascade`, `revoke_reason`, `affected_mandate_ids`, `cascaded_mandate_ids`, `rr_visibility { effective_at, visibility_budget_ms, rr_visible_by, broadcast_channels }`, `audit_event` five-tuple, `post_state.no_revoked_to_active_path`, digests, requirements traceability. |
| `debug.json`      | Human-readable mirror of both `request_view` and `response_view`. Not normative.                                         |

`request.cbor` and `request.json` materialise to the same
canonical CBOR signing input, and likewise for the response. The
verifier asserts both round-trips on every vector.

## Encoding & signing rules

Every vector follows design.md §5.1 / §6.3:

1. **CBOR is canonical** (RFC 8949 §4.2.1). Both CBOR and JSON
   encodings produce the *same* canonical CBOR signing input for
   the outer envelope, so the same Ed25519 signature appears in
   both wire forms.
2. **REVOKE is HP-signed**. The REVOKE envelope's outer signature
   is computed with the HP root key (Requirement 4.1.3: REVOKE
   authentication strength MUST NOT be weaker than BOOTSTRAP).
   The receipt and any ERROR response are MS-signed.
3. **Detached signatures**. The outer `signature` block sits next
   to the signed object — never inside the signed input — so audit
   tooling can re-sign without rebuilding the payload.
4. **JSON byte-string convention**. JSON cannot carry raw bytes
   natively, so every CBOR `bstr` is encoded as
   `{"$bytes": "<base64url(no padding)>"}` and CBOR tag-0 timestamps
   as `{"$tag": 0, "$value": "<RFC 3339>"}`. This keeps the JSON
   tree shape isomorphic to the CBOR tree.

## RR visibility timestamp

Every vector's `expected.rr_visibility` block records:

- `effective_at` — the request's `claims.effective_at` (or, for
  `irreversibility-double-revoke`, the *original* revocation
  timestamp; the duplicate request does not move the budget).
- `visibility_budget_ms` — `1000` (default per design.md §3.4 / §9.6
  / Appendix B).
- `rr_visible_by` — `effective_at + visibility_budget_ms`. The
  Revocation Registry MUST advertise `revoked` status to all
  subsequent queries by this timestamp.
- `broadcast_channels` — `["pull-ocsp-like", "push-websocket-sse-mqtt"]`
  enumerating the two delivery modes Requirement 4.2.2 mandates.

Cascade vectors additionally record
`pushed_to_descendants_rps` to capture Requirement 7.2.3.

## Audit event five-tuple

Every vector's `expected.audit_event` matches the §9.6 audit-log
shape:

```text
(error_code, mandate_id, ts, rp_id, reason)
```

`error_code` is `null` on the success path (REVOKE → REVOKE_RECEIPT)
and `1006` on `neg-use-after-revoke`. Implementations SHOULD use
this five-tuple as the unit of audit-log indexing so the chain
remains diff-able across versions.

## Irreversibility invariant

Every `expected.json` carries
`post_state.no_revoked_to_active_path = true`. The verifier
refuses any vector whose `post_state` does not encode this claim,
so an accidental edit that introduces a recovery transition would
be caught immediately.

The exhaustive recovery path is illustrated by
`irreversibility-rebootstrap-new-id`: the only legal way to
restore authorisation over the same `(subject, scope)` is a fresh
BOOTSTRAP that issues a Mandate with a *different* `mandate_id`
(Requirement 4.3.3).

## Determinism

All vectors are reproducible. `_tools/generate.py` derives every
key, nonce, message-id, mandate-id, and synthetic payload byte
from the fixed master seed `FAYING_VECTOR_SEED` (the same 32-byte
seed shared with the BOOTSTRAP / PRESENCE / GRADE_SWITCH /
DELEGATE batches) and a per-batch domain separator (`b"revoke|"`).
`index.json` records the SHA-256 of that seed under
`deterministic_seed_sha256`, and per-vector
`digests.{request,response}_{cbor,json}_sha256` are recorded in
both `expected.json` and `index.json` so reviewers can detect
accidental edits.

## Verifying the vectors

```bash
python3 vectors/revoke/_tools/generate.py    # regenerate
python3 vectors/revoke/_tools/verify.py      # validate
```

`verify.py` performs the following checks per vector:

1. CBOR / JSON round-trip equivalence (canonical CBOR is
   byte-identical regardless of which encoding you decode first).
2. Structural shape against §5.3.5:
   - request `header.msg_type == "REVOKE"`,
   - claims contain `mandate_id`, `cascade`, `reason ∈ RevokeReason`,
     `effective_at`,
   - positive responses → `REVOKE_RECEIPT` carrying `mandate_id`,
     `reason`, `revoked_at`, `cascade`, `cascaded_mandate_ids`,
   - negative responses → `ERROR` carrying `1006 / E_REVOKED`.
3. Outer Ed25519 signature on every envelope (`H( Deterministic-CBOR
   (Envelope_without_signature) )`).
4. `rr_visible_by - effective_at == visibility_budget_ms`.
5. `affected_mandate_ids == [target_mandate_id, *cascaded_mandate_ids]`.
6. `post_state.no_revoked_to_active_path is True` (Requirement 4.3.2).
7. Per-vector SHA-256 digests on disk match `expected.digests.*`.
8. `index.json` records every vector exactly once, all nine
   `RevokeReason` enum values are represented, and at least one
   vector has `cascade=true` with `tree_depth >= 2` and a non-empty
   `cascaded_mandate_ids`.

Exit code is `0` on success, `1` on any failure.

## Requirements traceability

These vectors validate the following acceptance criteria
(see [`requirements.md`](../../.kiro/specs/faying-auth-protocol/requirements.md)):

| Requirement | Acceptance criterion verified                                                                                                          |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 4.1         | Every positive vector encodes the symmetric-revocation contract: REVOKE is HP-signed; the audit-log five-tuple records the path; iFay-initiated paths (`reason-task-completed`) are mediated by HP confirmation. |
| 4.2         | `expected.rr_visibility` materialises the visibility budget and broadcast-channel list (`pull-ocsp-like`, `push-websocket-sse-mqtt`).  |
| 4.3         | Every vector encodes `post_state.no_revoked_to_active_path = true`. The three irreversibility vectors document idempotent double-revoke, fresh-id-on-rebootstrap, and 1006-on-use-after-revoke. |
| 7.2         | `cascade-depth-2` and `cascade-disabled` together exercise atomic cascade, no-cascade override, and the no-new-DELEGATE-off-Revoked-parent rule. |
| 9.4         | All nine `RevokeReason` values are covered (decoupling-state recognition triggers); `neg-use-after-revoke` records the HP-view-channel critical-bucket push for `E_REVOKED`. |
| 10.1        | Every vector ships matching CBOR (primary) and JSON (debug fallback) encodings; both materialise to the same canonical CBOR signing input and outer signature. |
| 10.3        | The catalogue covers every `RevokeReason`, both cascade modes, and three irreversibility shapes — shaped for cross-implementation conformance. |

## Design-anchor coverage

| design.md anchor                                              | Where exercised                                                                                |
| ------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| §5.3.5 (REVOKE wire shape; `RevokeReason` enum; cascade default) | All 14 vectors. The nine `reason-*` positives cover every enum value.                         |
| §3.4 / §9.6 (`RevocationVisibilityBudget`)                    | Every vector's `rr_visibility.rr_visible_by = effective_at + 1000ms`.                          |
| §4.3 / §8.1 (state machine — Revoked is terminal)             | Every vector's `post_state.no_revoked_to_active_path = true`; `irreversibility-double-revoke` and `irreversibility-rebootstrap-new-id` document the only legal recovery path. |
| §7.5 / §9.7 (cascade)                                         | `cascade-depth-2` (cascade=true, depth 2) and `cascade-disabled` (cascade=false).              |
| §EH.1 / §EH.3 (`E_REVOKED` audit + HP view channel)           | `neg-use-after-revoke` carries `error_code = 1006`, audit five-tuple, and critical-bucket flag. |

## Stability promise

`index.json` is the canonical machine-readable manifest of this
directory. Once a Faying Protocol/1.0 release is cut, the
`digests` fields and per-vector `name`s become normative for that
release. Subsequent edits MUST either:

- bump the protocol version (`schemas/fap-1.0.cddl` and
  `index.json.spec_version` together), or
- be additive (new vectors only, no edits to existing payloads).

Until then, the vectors are draft and may be regenerated;
reviewers should diff `index.json` to spot any change.
