# GRADE_SWITCH Test Vectors — Faying Protocol/1.0

This directory holds the official `GRADE_SWITCH` test vectors for
Faying Protocol/1.0. They exercise the message and authorization-grade
sections of the specification:

- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §5.3.3 — GRADE_SWITCH wire shape (`mandate_id`, `target_grade`, `reason`, optional `human_witness`)
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §7.2 — 触发条件矩阵 (per-event outcome by current grade)
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §7.4 — 等级切换报文要求差异 (`human_witness` MUST on upgrade and on G0 Override; MAY on downgrade)
- [`design.md`](../../.kiro/specs/faying-auth-protocol/design.md) §EH.1 — error-code table (`1010 E_HUMAN_WITNESS_REQUIRED` for the negative cases)

The schema-of-record is [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl);
the inner `Mandate` carried in `GRADE_SWITCH_RESP.claims` validates
against the same `mandate` rule that the BOOTSTRAP vectors use.

## Vector matrix (11)

### Upgrades — `human_witness` MUST (§7.4 row 1)

| Vector            | `current_grade` | `target_grade` | §7.2 outcome | Witness |
| ----------------- | --------------: | -------------: | ------------ | :-----: |
| `up-g3-to-g2`     |              G3 |             G2 | Active(G2)   |   ✅   |
| `up-g2-to-g1`     |              G2 |             G1 | Active(G1)   |   ✅   |
| `up-g4-to-g3`     |              G4 |             G3 | Active(G3)   |   ✅   |

### Downgrades — `human_witness` MAY (§7.4 row 2)

The canonical downgrade form omits `human_witness` so verifiers learn
to accept the bare HP-signed envelope.

| Vector            | `current_grade` | `target_grade` | §7.2 outcome | Witness |
| ----------------- | --------------: | -------------: | ------------ | :-----: |
| `down-g1-to-g2`   |              G1 |             G2 | Active(G2)   |   ⚪   |
| `down-g2-to-g3`   |              G2 |             G3 | Active(G3)   |   ⚪   |
| `down-g3-to-g4`   |              G3 |             G4 | Active(G4)   |   ⚪   |

### G0 Emergency Override — `human_witness` MUST (§7.4 row 3, §7.1)

`G0` is *orthogonal* to G1–G4: it suspends the target Mandate without
moving it along the grade continuum.

| Vector                  | `current_grade` | `target_grade` | §7.2 outcome | Witness |
| ----------------------- | --------------: | -------------: | ------------ | :-----: |
| `override-g0-from-g1`   |              G1 |             G0 | Suspended    |   ✅   |
| `override-g0-from-g2`   |              G2 |             G0 | Suspended    |   ✅   |
| `override-g0-from-g4`   |              G4 |             G0 | Suspended    |   ✅   |

### Negative — upgrade missing `human_witness` → 1010

| Vector                          | `current_grade` | `target_grade` | Error                          |
| ------------------------------- | --------------: | -------------: | ------------------------------ |
| `neg-up-g3-to-g2-no-witness`    |              G3 |             G2 | `1010 E_HUMAN_WITNESS_REQUIRED` |
| `neg-up-g2-to-g1-no-witness`    |              G2 |             G1 | `1010 E_HUMAN_WITNESS_REQUIRED` |

## Per-vector layout

Each vector lives in its own directory and contains:

| File              | Purpose                                                                                                                 |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------- |
| `request.cbor`    | Canonical CBOR (RFC 8949 §4.2.1) encoding of the `GRADE_SWITCH` envelope, signed by HP.                                 |
| `request.json`    | Equivalent JSON encoding (`Content-Type: application/faying-protocol+json`) using the `$bytes` / `$tag` markers.        |
| `response.cbor`   | `GRADE_SWITCH_RESP` envelope carrying the updated Mandate (positive) or `ERROR` envelope (negative). Always signed by MS. |
| `response.json`   | JSON encoding of the same response envelope.                                                                            |
| `expected.json`   | Final state, witness expectation, §7.2 trigger-matrix outcome, error code if any, requirements traceability, on-disk digests. |
| `debug.json`      | Human-readable mirror of both `request_view` and `response_view`. Not normative.                                        |

`request.cbor` and `request.json` materialise to the same canonical
CBOR signing input, and likewise for the response. The verifier
asserts both round-trips on every vector.

## Encoding & signing rules

Every vector follows design.md §5.1 / §6.3:

1. **CBOR is canonical** (RFC 8949 §4.2.1). Both CBOR and JSON
   encodings produce the *same* canonical CBOR signing input for the
   outer envelope, so the same HP / MS Ed25519 signature appears in
   both wire forms.
2. **Detached signatures**. The outer `signature` block sits next to
   the signed object — never inside the signed input — so audit
   tooling can re-sign without rebuilding the payload.
3. **Inner Mandate signature**. Positive responses carry a Mandate
   inside `GRADE_SWITCH_RESP.claims` whose `signature` field is itself
   computed over `Deterministic-CBOR(Mandate − signature)`. This is
   what downstream property tests (P13 audit chain) verify.
4. **JSON byte-string convention**. JSON cannot carry raw bytes
   natively, so every CBOR `bstr` is encoded as
   `{"$bytes": "<base64url(no padding)>"}` and CBOR tag-0 timestamps
   as `{"$tag": 0, "$value": "<RFC 3339>"}`. This keeps the JSON tree
   shape isomorphic to the CBOR tree.

## §7.4 message-requirement matrix in code

The generator and verifier each rederive §7.2 / §7.4 independently.
The generator stamps `expected.trigger_matrix` and
`expected.request_must_carry_human_witness` on every vector;
`_tools/verify.py` rederives the matrix from a literal table inside
the verifier and confirms agreement. A drift in either side will
fail verification.

| Direction | `human_witness` | `RR notification` | `AC chain entry` |
| --------- | :-------------: | :--------------: | :--------------: |
| Upgrade   | MUST            | MUST             | MUST             |
| Downgrade | MAY             | MUST             | MUST             |
| G0 Override | MUST          | MUST (highest priority) | MUST    |

## Trigger-matrix (§7.2) coverage

This batch covers the upgrade, downgrade, and G0 Override rows of the
matrix in design.md §7.2:

- `human-upgrade`: G2 → G1, G3 → G2, G4 → G3 (one vector each).
- `human-downgrade`: G1 → G2, G2 → G3, G3 → G4 (one vector each).
- `g0-override`: G1, G2, G4 → Suspended (three diversity samples).

The remaining rows (`在场新鲜度过期`, `检测到 Ego 偏离`,
`撤销注册不可达`) are exercised by the `vectors/presence/` and
`vectors/errors/` batches, not duplicated here.

The negative case `升级缺见证 → E_HUMAN_WITNESS_REQUIRED` is
echoed as a row in design.md §EH.1; the generator emits `mandate_id`
inside the `ERROR.claims` so audit consumers can correlate the
rejection back to the mutated Mandate.

## WebAuthn `human_witness` placeholder

The accepted vectors carry a synthetic WebAuthn assertion under
`claims.human_witness`:

```jsonc
{
  "credential_id":      "<base64url 16 bytes>",
  "authenticator_data": { "$bytes": "<base64url 37 bytes>" },
  "client_data_json":   { "$bytes": "<base64url UTF-8 JSON>" },
  "signature":          { "$bytes": "<base64url 64 bytes>" },
  "user_present":       true,
  "user_verified":      true
}
```

These bytes are **deterministic placeholders** — they parse against
the structural shape but do not validate against a real WebAuthn
authenticator. The surrounding Ed25519 envelope signature *is* real
and is the cryptographic anchor verifiers should rely on. When a
production WebAuthn fixture lands (tracked alongside §3.3 / the
BOOTSTRAP and PRESENCE batches), `_tools/generate.py` should swap
out `make_webauthn_assertion` for a builder that emits real
attestations and the on-disk digests will change accordingly.

The negative vectors **omit** `claims.human_witness` entirely so the
`E_HUMAN_WITNESS_REQUIRED` rejection becomes observable.

## Determinism

All vectors are reproducible. `_tools/generate.py` derives every key,
nonce, message-id, mandate-id, and synthetic payload byte from the
fixed master seed `FAYING_VECTOR_SEED` (the same 32-byte seed shared
with the BOOTSTRAP and PRESENCE batches) and a per-batch domain
separator (`b"grade-switch|"`). `index.json` records the SHA-256 of
that seed under `deterministic_seed_sha256`, and per-vector
`digests.{request,response}_{cbor,json}_sha256` are recorded in both
`expected.json` and `index.json` so reviewers can detect accidental
edits.

## Verifying the vectors

```bash
python3 vectors/grade-switch/_tools/generate.py    # regenerate
python3 vectors/grade-switch/_tools/verify.py      # validate
```

`verify.py` performs the following checks per vector:

1. CBOR / JSON round-trip equivalence (canonical CBOR is byte-identical
   regardless of which encoding you decode first).
2. Structural shape against §5.3.3:
   - request `header.msg_type == "GRADE_SWITCH"`,
   - claims contain `mandate_id`, `target_grade ∈ {0..4}`, `reason`,
   - `human_witness` is present iff the direction declares it MUST.
3. Response shape:
   - accepted vectors → `GRADE_SWITCH_RESP` with a signed inner
     Mandate (CDDL `mandate.signature` rule),
   - negative vectors → `ERROR` carrying the declared `code` / `name`.
4. Outer Ed25519 signature on every envelope (`H( Deterministic-CBOR
   (Envelope_without_signature) )`).
5. Per-vector SHA-256 digests on disk match `expected.digests.*`.
6. `expected.trigger_matrix` matches a literal §7.2 table baked into
   the verifier.

Exit code is `0` on success, `1` on any failure.

## Requirements traceability

These vectors validate the following acceptance criteria
(see [`requirements.md`](../../.kiro/specs/faying-auth-protocol/requirements.md)):

| Requirement | Acceptance criterion verified                                                                                                |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------- |
| 6.1         | Every upgrade and override vector carries a verifiable WebAuthn `human_witness`; the two negative vectors omit it and surface `1010 E_HUMAN_WITNESS_REQUIRED`. |
| 6.2         | The three `override-g0-from-*` vectors confirm G0 Emergency Override drops the target Mandate to `Suspended` regardless of the current grade. |
| 6.3         | Every accepted vector's response carries a Mandate whose `presence-req.max-staleness-ms` matches §7.1 for the new grade; downgrades widen the budget, upgrades tighten it. |
| 10.1        | Each vector ships matching CBOR (primary) and JSON (debug fallback) encodings; both materialise to the same canonical CBOR. |
| 10.3        | The catalogue covers the §7.2 upgrade / downgrade / G0 Override rows and is shaped for cross-implementation conformance.    |

## Stability promise

`index.json` is the canonical machine-readable manifest of this
directory. Once a Faying Protocol/1.0 release is cut, the `digests`
fields and per-vector `name`s become normative for that release.
Subsequent edits MUST either:

- bump the protocol version (`schemas/fap-1.0.cddl` and
  `index.json.spec_version` together), or
- be additive (new vectors only, no edits to existing payloads).

Until then, the vectors are draft and may be regenerated;
reviewers should diff `index.json` to spot any change.
