# DELEGATE Test Vectors — Faying Protocol/1.0

This directory holds the official `DELEGATE` test vectors for
Faying Protocol/1.0. They exercise the cross-device / sub-agent
derivation path and the multi-sign attestation chain that anchors it:

- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §3.3 — Attestation Chain (root HP → MS-Cert → parent → child) and invariants `I-AC-1..3`.
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §5.3.4 — DELEGATE wire shape (`parent_mandate`, `child_subject`, `child_scope`, `child_grade`, optional `device_id`).
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §6.3 — multi-sign chain (the child Mandate's `signature_bundle.chain` carries the parent Mandate's outer signature).
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §9.7 — derivation convergence (`child.scope ⊆ parent.scope`, `child.grade.autonomy ≤ parent.grade.autonomy`).
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §EH.1 / §5.4 — error code `1099 E_PROTOCOL` for scope-expansion / grade-autonomy-increase rejections.

The schema-of-record is [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl);
the inner Mandate carried in `DELEGATE_RESP.claims` validates against
the same `mandate` rule that the BOOTSTRAP / GRADE_SWITCH vectors use,
with the additional `parent` field populated.

## Vector matrix (9)

### Positive — `child.scope ⊆ parent.scope`, `child.grade.autonomy ≤ parent.grade.autonomy`

| Vector                       | Depth | parent → child grade        | `device_id` claim | Chain length |
| ---------------------------- | ----: | --------------------------- | :---------------: | -----------: |
| `pos-depth-1`                |     1 | G3 → G2                     |        —          |          2   |
| `pos-depth-2`                |     2 | G3 → G2 → G1                |        —          |          3   |
| `pos-depth-3`                |     3 | G4 → G3 → G2 → G1           |        —          |          4   |
| `pos-cross-device-binding`   |     1 | G3 → G2 (bound to mobile-2) |        ✅         |          2   |
| `pos-chain-verify`           |     1 | G2 → G2 (equal autonomy)    |        —          |          2   |

`Chain length` is the size of the child Mandate's
`signature_bundle.chain` array. It equals `depth + 1` because the
chain always starts with the HP signature over the MS-Cert
(`hp-root:ms-cert`) and then accumulates one entry per derivation
hop (`parent-i:outer-sig` for `i = 0 .. depth-1`).

### Negative — every case rejected with `1099 E_PROTOCOL`

| Vector                            | Convergence axis violated | Expansion description                                                            |
| --------------------------------- | ------------------------- | -------------------------------------------------------------------------------- |
| `neg-scope-expansion-action`      | `scope.actions`           | Child requests `calendar:event:delete` not in parent's actions.                  |
| `neg-scope-expansion-domain`      | `scope.domains`           | Child requests `https://api.example.com/v1/files` not in parent's domains.       |
| `neg-scope-expansion-terminal`    | `scope.terminals`         | Child binds to `terminal:tablet:roaming-1` not in parent's terminals.            |
| `neg-grade-autonomy-up`           | `grade.autonomy`          | Parent G2 (Moderate) → child G4 (Autonomous) escalates autonomy.                 |

## Per-vector layout

Each vector lives in its own directory and contains:

| File              | Purpose                                                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `request.cbor`    | Canonical CBOR (RFC 8949 §4.2.1) encoding of the `DELEGATE` envelope, signed by MS.                                       |
| `request.json`    | Equivalent JSON encoding (`Content-Type: application/faying-protocol+json`) using the `$bytes` / `$tag` markers.         |
| `response.cbor`   | `DELEGATE_RESP` envelope carrying the new child Mandate (positive) or `ERROR` envelope (negative). Always signed by MS. |
| `response.json`   | JSON encoding of the same response envelope.                                                                             |
| `expected.json`   | `chain_depth`, `parent_mandate_id`, `child_mandate_id`, `signature_chain`, error code (if any), digests, requirements traceability. |
| `debug.json`      | Human-readable mirror of both `request_view` and `response_view`. Not normative.                                         |

`request.cbor` and `request.json` materialise to the same canonical
CBOR signing input, and likewise for the response. The verifier
asserts both round-trips on every vector.

## Encoding & signing rules

Every vector follows design.md §5.1 / §6.3:

1. **CBOR is canonical** (RFC 8949 §4.2.1). Both CBOR and JSON
   encodings produce the *same* canonical CBOR signing input for the
   outer envelope, so the same MS Ed25519 signature appears in both
   wire forms.
2. **Detached signatures**. The outer `signature` block sits next to
   the signed object — never inside the signed input — so audit
   tooling can re-sign without rebuilding the payload.
3. **Inner Mandate signature**. Positive responses carry a child
   Mandate inside `DELEGATE_RESP.claims` whose `signature` field is
   itself computed over `Deterministic-CBOR(Mandate − signature)`.
4. **Multi-sign chain (§6.3)**. The child Mandate's
   `signature.chain` array carries the *outer* signature bytes of
   every ancestor, in order from chain root to immediate parent:

   ```text
   chain[0] = HP signature over MS-Cert
   chain[1] = parent[0]'s outer signature
   chain[2] = parent[1]'s outer signature
   ...
   chain[k] = immediate parent's outer signature
   ```

   An independent verifier walks
   `HP-pubkey → MS-Cert → parent → ... → child` using only this
   array plus the protocol's well-known HP root key.
5. **JSON byte-string convention**. JSON cannot carry raw bytes
   natively, so every CBOR `bstr` is encoded as
   `{"$bytes": "<base64url(no padding)>"}` and CBOR tag-0 timestamps
   as `{"$tag": 0, "$value": "<RFC 3339>"}`. This keeps the JSON tree
   shape isomorphic to the CBOR tree.

## Authorization-grade autonomy direction

The protocol's grade integer runs **parallel** to autonomy:

| Grade | Label             | Autonomy |
| ----- | ----------------- | -------- |
| `G1`  | Strict            | lowest   |
| `G2`  | Moderate          | low      |
| `G3`  | Loose             | high     |
| `G4`  | Autonomous        | highest  |

So `child.grade.autonomy ≤ parent.grade.autonomy` from
[`requirements.md`](../../.kiro/specs/faying-auth-protocol/requirements.md) §7.1.2 is equivalent to
`child.grade_number ≤ parent.grade_number` on the wire. Every
positive vector in this batch picks a child grade with
`grade_number ≤` its parent's; equality is exercised by
`pos-chain-verify`. The negative vector `neg-grade-autonomy-up`
violates this with `parent_grade=2`, `requested_child_grade=4`.

## Cross-device `device_id` binding (§9.7)

`pos-cross-device-binding` populates `claims.device_id` so the new
child Mandate is bound to a *different* terminal than the parent
(`terminal:phone:mobile-2` vs. the parent's primary
`terminal:laptop:fixed-1`). The terminal must already appear in
`parent.scope.terminals`; pushing a brand-new terminal is what
`neg-scope-expansion-terminal` rejects. This is the operational
reason DELEGATE exists at all — design.md §9.3 mandates that each
Mandate be bound to its issuing device's `device_id` and
`device_attestation`, and Requirement 9.2 acceptance items 1–2
require cross-device reuse to take the DELEGATE path so a fresh
device-bound child Mandate is issued.

## Trigger-matrix (§9.7) coverage

This batch covers all four convergence axes that §9.7 normatively
constrains:

- `scope.actions` — positive (subset) + negative (`neg-scope-expansion-action`).
- `scope.domains` — positive (subset) + negative (`neg-scope-expansion-domain`).
- `scope.terminals` — positive subset (legal cross-device) + negative (`neg-scope-expansion-terminal`).
- `grade.autonomy` — positive descent (depths 1, 2, 3) + equal-autonomy edge case (`pos-chain-verify`) + negative escalation (`neg-grade-autonomy-up`).

The remaining DELEGATE rule — endorsement-convergence between
parent and child Endorsed_Mandate — is exercised by
`vectors/endorsement/f-delegate-child-not-converging/`, not
duplicated here.

## Determinism

All vectors are reproducible. `_tools/generate.py` derives every key,
nonce, message-id, mandate-id, and synthetic payload byte from the
fixed master seed `FAYING_VECTOR_SEED` (the same 32-byte seed shared
with the BOOTSTRAP / PRESENCE / GRADE_SWITCH batches) and a per-batch
domain separator (`b"delegate|"`). `index.json` records the SHA-256
of that seed under `deterministic_seed_sha256`, and per-vector
`digests.{request,response}_{cbor,json}_sha256` are recorded in both
`expected.json` and `index.json` so reviewers can detect accidental
edits.

## Verifying the vectors

```bash
python3 vectors/delegate/_tools/generate.py    # regenerate
python3 vectors/delegate/_tools/verify.py      # validate
```

`verify.py` performs the following checks per vector:

1. CBOR / JSON round-trip equivalence (canonical CBOR is byte-identical
   regardless of which encoding you decode first).
2. Structural shape against §5.3.4:
   - request `header.msg_type == "DELEGATE"`,
   - claims contain `parent_mandate`, `child_subject`, `child_scope`,
     `child_grade`,
   - positive responses → `DELEGATE_RESP` with a signed inner child
     Mandate (CDDL `mandate` rule), `signature.chain` length =
     `chain_depth + 1`,
   - negative responses → `ERROR` carrying `1099 / E_PROTOCOL`.
3. Outer Ed25519 signature on every envelope (`H( Deterministic-CBOR
   (Envelope_without_signature) )`).
4. Inner Ed25519 signature on every accepted child Mandate.
5. Per-vector SHA-256 digests on disk match `expected.digests.*`.
6. `index.json` records every vector exactly once and represents
   depths 1, 2, and 3.

Exit code is `0` on success, `1` on any failure.

## Requirements traceability

These vectors validate the following acceptance criteria
(see [`requirements.md`](../../.kiro/specs/faying-auth-protocol/requirements.md)):

| Requirement | Acceptance criterion verified                                                                                                          |
| ----------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| 7.1         | `pos-depth-{1,2,3}` and `pos-chain-verify` confirm `child.scope ⊆ parent.scope` and `child.grade.autonomy ≤ parent.grade.autonomy`; the four `neg-*` vectors confirm rejection with `1099 E_PROTOCOL` along the four convergence axes. The `signature_bundle.chain` field carries the parent-chain co-signatures so RPs can independently walk root → MS → parent → child. |
| 9.2         | `pos-cross-device-binding` populates `claims.device_id` so the child Mandate is freshly device-bound; `neg-scope-expansion-terminal` confirms terminals outside `parent.scope.terminals` are rejected. |
| 10.1        | Every vector ships matching CBOR (primary) and JSON (debug fallback) encodings; both materialise to the same canonical CBOR.          |
| 10.3        | The catalogue covers depths 1–3, four convergence axes, and the cross-device binding row, shaped for cross-implementation conformance. |

## Design-anchor coverage

| design.md anchor                         | Where exercised                                                                                |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------- |
| §3.3 (AC chain root → MS → parent → child) | Every accepted vector's `child.signature.chain` walks root → MS-Cert → ancestors → immediate parent. |
| §5.3.4 (DELEGATE wire shape)             | All nine vectors exercise the `DELEGATE` envelope and `DelegateClaims` fields.                 |
| §6.3 (multi-sign chain)                  | `pos-chain-verify` records the SHA-256 of every `chain[i]` plus the HP root pubkey for property tests. |
| §9.7 (派生 scope/grade 收敛)             | Four convergence axes covered (positive + negative on each).                                   |
| §EH.1 / §5.4 (1099 E_PROTOCOL)           | Four negative vectors all materialise `1099 E_PROTOCOL`.                                       |

## Stability promise

`index.json` is the canonical machine-readable manifest of this
directory. Once a Faying Protocol/1.0 release is cut, the `digests`
fields and per-vector `name`s become normative for that release.
Subsequent edits MUST either:

- bump the protocol version (`schemas/fap-1.0.cddl` and
  `index.json.spec_version` together), or
- be additive (new vectors only, no edits to existing payloads).

Until then, the vectors are draft and may be regenerated; reviewers
should diff `index.json` to spot any change.
