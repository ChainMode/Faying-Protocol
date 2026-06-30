# Endorsed Mandate Test Vectors

Task **3.8** — Faying Protocol/1.0, spec [`.kiro/specs/faying-auth-protocol/`](../../.kiro/specs/faying-auth-protocol/).

Covers requirements **11.1 / 11.2 / 11.3 / 11.4** and properties **P16.1 / P16.3**.
Authoritative wire-format schema: [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl).

> These vectors are **normative inputs** to the conformance test suite (tasks 5.x). The Python tooling alongside them (`_generate.py`, `_verify.py`) is **non-normative** scaffolding and exists only to make the vectors reproducible.

## Layout

```
vectors/endorsement/
├── README.md                ← this file
├── index.json               ← machine-readable registry of all vectors
├── _generate.py             ← reproducible generator (non-normative)
├── _verify.py               ← self-check; asserts each vector matches its expected.json
└── <vector-id>/
    ├── mandate.cbor         ← Deterministic-CBOR encoding (RFC 8949 §4.2.1)
    ├── mandate.json         ← non-normative JSON view (kebab-case keys, hex bstr)
    └── expected.json        ← outcome contract (see schema below)
```

`mandate.cbor` is the on-wire form an implementation will see. `mandate.json` is provided for review convenience only — the CBOR file always wins where the two diverge.

## Expected outcome contract (`expected.json`)

```jsonc
{
  "vector_id":     "<dir-name>",
  "title":         "<human-readable title>",
  "category":      "(a) | (b) | (c) | (d) | (e) | (f)",
  "requirements":  ["11.1", ...],
  "properties":    ["P16.1" | "P16.3"],
  "outcome":       "accepted" | "rejected",
  "error_code":    null | 1007 | 1013,
  "error_name":    null | "E_ATTESTATION_INVALID" | "E_ENDORSEMENT_INVALID",
  "triggers":      ["revoke", ...],

  "signature_input": {
    "definition":                    "H( Deterministic-CBOR(Mandate_without_signature) )",
    "hash_alg":                       "SHA-256",
    "det_cbor_hex":                   "...",  // det-CBOR over which the signature was computed
    "hash_hex":                       "...",  // SHA-256 of det_cbor_hex
    "endorsement_field_hash_hex":     "...",  // SHA-256( Det-CBOR(endorsement) ) at sign time
    "endorsement_in_signature":        true,
    "wire_det_cbor_hex":              "...",  // det-CBOR of the on-disk mandate.cbor (minus signature)
    "wire_hash_hex":                  "...",  // SHA-256 of wire_det_cbor_hex
    "wire_matches_signature_input":    true   // false ⇒ post-sign tamper (category (e))
  },

  "violations":   [ "...", ... ],
  "notes":        "...",

  // Only present for category (e):
  "post_sign_tamper": {
    "$comment":         "...",
    "tampered_paths":   ["endorsement.endorsed-grade", ...]
  }
}
```

### How `signature_input` proves P16.1 inclusion

Per design.md §6.3:

```
signature input = H( Deterministic-CBOR(Mandate_without_signature) )
```

with the explicit anchor that the `endorsement` subtree (all five subfields:
`enabled` / `endorsed_scope` / `endorsed_grade` / `endorsed_lifetime_ms` /
`offline_revocation_policy`) is part of `Mandate_without_signature`. Each
`expected.json` records:

1. `det_cbor_hex` — the exact bytes the signer hashed.
2. `hash_hex` — SHA-256 of those bytes.
3. `endorsement_field_hash_hex` — SHA-256 of the `endorsement` subtree alone.

A conformance implementation can independently:

- Recompute Deterministic-CBOR over `mandate − signature` from `mandate.cbor`
  and check it equals `wire_det_cbor_hex`.
- Recompute Deterministic-CBOR over the `endorsement` subtree from
  `mandate.cbor` and check it equals `endorsement_field_hash_hex` for non-tamper
  vectors (i.e. when `wire_matches_signature_input == true`).
- Verify the `signature.sig` field against `signature.pubkey` over the SHA-256
  digest of `wire_det_cbor_hex` for non-tamper vectors.

For category-(e) vectors, the signature was computed over `det_cbor_hex` but the
on-disk body deterministically encodes to `wire_det_cbor_hex`, with the two
differing inside the `endorsement` subtree. Verification therefore fails with
`E_ATTESTATION_INVALID` (1007), exactly as P16.1 demands.

## Vector inventory

> Total: **11** vectors (≥10 required by task 3.8). All vectors share the same
> fixed Ed25519 keypair so artefacts are byte-stable across CI runs.

| ID | Category | Outcome | Error | Hits |
| --- | --- | --- | --- | --- |
| `a-legal-policy-stop-and-audit` | (a) Legal Endorsed Mandate | accepted | — | 11.1, 11.2, 11.3, 11.4 / P16.1 + P16.3 |
| `a-legal-policy-stop-only`      | (a) Legal Endorsed Mandate | accepted | — | 11.1, 11.2, 11.3, 11.4 / P16.1 + P16.3 |
| `a-legal-policy-graceful-stop`  | (a) Legal Endorsed Mandate | accepted | — | 11.1, 11.2, 11.3, 11.4 / P16.1 + P16.3 |
| `b-scope-violation`             | (b) `endorsed_scope ⊄ scope`           | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |
| `c-grade-violation`             | (c) `endorsed_grade.autonomy > grade.autonomy` | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |
| `d1-lifetime-missing`           | (d) lifetime missing                   | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |
| `d2-lifetime-infinite`          | (d) lifetime ∞ (uint64 max)            | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |
| `d3-lifetime-exceeds-main`      | (d) lifetime > main mandate            | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |
| `e1-signature-tamper-endorsed-grade` | (e) tamper `endorsed_grade`       | rejected | 1007 `E_ATTESTATION_INVALID` (+ Revoke) | 11.1 / P16.1 |
| `e2-signature-tamper-endorsed-scope` | (e) tamper `endorsed_scope`       | rejected | 1007 `E_ATTESTATION_INVALID` (+ Revoke) | 11.1 / P16.1 |
| `f-delegate-child-not-converging` | (f) DELEGATE child ⊄ parent endorsement | rejected | 1013 `E_ENDORSEMENT_INVALID` | 11.2 / P16.3 |

### Note on the four-vs-three policies

Task 3.8 says *"each of 4 `offline_revocation_policy` values"* with
`stop-and-audit / stop-only / graceful-stop` listed parenthetically. design.md
§7.5 and the authoritative CDDL in `schemas/fap-1.0.cddl` enumerate exactly
**three** policy values, and the `Endorsement.offline-revocation-policy` field
is declared as `"stop-and-audit" / "stop-only" / "graceful-stop"`. The vector
set therefore covers all three, and the parenthetical "4" in tasks.md is
treated as an editorial typo. If protocol committee adds a fourth policy in a
future revision, regenerate by adding the new value to `_generate.py` (a) loop.

## Acceptance check (task 3.8 verbatim)

> *"Negative cases return error code matching spec doc §5.4 (1013 / 1007)"*

- All `(b) (c) (d) (f)` vectors: `error_code == 1013`.
- All `(e)` vectors: `error_code == 1007` and `triggers` includes `"revoke"`
  (per §5.4 row 1007: *"拒绝 + 触发 Revoke"*) plus a secondary
  `"ms_secondary_E_ENDORSEMENT_INVALID"` annotation reflecting the dual
  rejection path described in design.md §6.3 anchor text.

> *"Signature input includes endorsement field hash, consistent with P16.1"*

- Every legal/positive vector has `signature_input.endorsement_field_hash_hex`
  populated and `endorsement_in_signature == true`.
- The endorsement-subtree det-CBOR is part of the input that was hashed; this
  is independently recomputable from `mandate.cbor` (see "How
  `signature_input` proves P16.1 inclusion" above).
- The category-(e) vectors operationalise the inclusion: any post-sign mutation
  of `endorsement.*` necessarily changes `wire_det_cbor_hex`, breaking the
  signature.

## Reproducibility

```bash
# From the repo root:
python3 vectors/endorsement/_generate.py   # rewrites every vector + index.json
python3 vectors/endorsement/_verify.py     # asserts every vector matches its expected.json

# Dependencies (already on Python stdlib + PyPI common stack):
#   cbor2          (Deterministic CBOR)
#   cryptography   (Ed25519)
```

`_verify.py` returns exit code `0` iff **all** vectors pass.

## Cross-references

- [design.md §4.1 / §4.2](../../.kiro/specs/faying-auth-protocol/design.md) — `endorsement` field, CDDL
- [design.md §5.4](../../.kiro/specs/faying-auth-protocol/design.md) — error codes 1007 / 1013
- [design.md §6.3](../../.kiro/specs/faying-auth-protocol/design.md) — signature input + Endorsed_Mandate inclusion anchor
- [design.md §7.5](../../.kiro/specs/faying-auth-protocol/design.md) — Endorsement Grades sub-grade hard constraints
- [design.md §9.7](../../.kiro/specs/faying-auth-protocol/design.md) — DELEGATE endorsement convergence
- [design.md §11 / §12](../../.kiro/specs/faying-auth-protocol/design.md) — P16.1 / P16.3 narratives
- [requirements.md Requirement 11](../../.kiro/specs/faying-auth-protocol/requirements.md) — 11.1 / 11.2 / 11.3 / 11.4 EARS clauses
- [schemas/fap-1.0.cddl](../../schemas/fap-1.0.cddl) — authoritative wire-format schema
- [schemas/types.ts](../../schemas/types.ts) — non-normative TypeScript view (snake_case ↔ kebab-case mapping in file header)
