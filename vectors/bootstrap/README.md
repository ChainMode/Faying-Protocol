# BOOTSTRAP Test Vectors — Faying Protocol/1.0

This directory holds the official BOOTSTRAP test vectors for Faying
Protocol/1.0. They are produced from `_tools/generate.py` and verified
by `_tools/verify.py`; the inner Mandates also validate against the
authoritative CDDL grammar (`schemas/fap-1.0.cddl`) via
`_tools/validate-with-cddl.sh`.

The vectors are referenced from:

- `index.json` — machine-readable catalogue of every vector.
- The PBT suite under `pbt/` (task 4.x) consumes them as fixtures.
- The conformance suite under `conformance/` (task 5.x) uses them to
  drive interoperability tests across reference implementations.

Each vector lives in its own folder and contains:

| File              | Purpose                                          |
| ----------------- | ------------------------------------------------ |
| `request.<enc>`   | Encoded BOOTSTRAP envelope (CBOR or JSON).       |
| `response.<enc>`  | Encoded Mandate (positive) or ERROR (negative).  |
| `expected.json`   | Expected outcome (mandate id, error code, …).    |
| `debug.json`      | JSON-friendly mirror of both wire payloads, with raw bytes encoded as `{"$bytes": "<base64url>"}` and CBOR tag-0 timestamps as `{"$tag": 0, "$value": "<RFC 3339>"}`. Provided for human review; not part of the wire format. |

`<enc>` is `cbor` for the canonical Faying Protocol wire format and
`json` for the debug fallback (`Content-Type: application/faying-protocol+json`).

## Vector catalogue

### Positive vectors (6)

Six encoding × algorithm combinations. Every positive vector issues a
Mandate at `grade = 2` (Moderate) bound to `https://api.example.com/v1/calendar`.

| Vector                  | Encoding | Algorithm   | Notes                                     |
| ----------------------- | -------- | ----------- | ----------------------------------------- |
| `pos-cbor-ed25519`      | CBOR     | Ed25519     | Real signature.                           |
| `pos-cbor-es256`        | CBOR     | ECDSA-P256  | Real signature.                           |
| `pos-cbor-ml-dsa-65`    | CBOR     | ML-DSA-65   | Placeholder signature (see below).        |
| `pos-json-ed25519`      | JSON     | Ed25519     | Real signature; signing input is canonical CBOR. |
| `pos-json-es256`        | JSON     | ECDSA-P256  | Real signature; signing input is canonical CBOR. |
| `pos-json-ml-dsa-65`    | JSON     | ML-DSA-65   | Placeholder signature (see below).        |

### Negative vectors (4)

| Vector                    | Trigger                           | Error                          |
| ------------------------- | --------------------------------- | ------------------------------ |
| `neg-no-witness`          | Missing `human_witness`.          | `1010 E_HUMAN_WITNESS_REQUIRED` |
| `neg-not-after-infinity`  | `not_after = "infinity"` sentinel | `1099 E_PROTOCOL`              |
| `neg-not-after-before`    | `not_after < not_before`          | `1099 E_PROTOCOL`              |
| `neg-unsupported-alg`     | `signature_bundle.alg = "RSA-PKCS1-v1_5-SHA1"` | `1099 E_PROTOCOL`              |

The ERROR response in every negative vector is itself signed by the
Mandate Service so the rejection is auditable on the Attestation Chain
(design.md §3.3, Requirement 3.1).

## Encoding & signing rules

Every vector adheres to the rules in design.md §5.1 / §6.3:

1. **CBOR is canonical (RFC 8949 §4.2.1).** Both CBOR vectors and JSON
   vectors use the canonical CBOR encoding of the unsigned envelope as
   the signing input. This guarantees that the same Faying message has
   the same digest regardless of wire encoding.
2. **JSON is sorted-key, comma-separated, UTF-8.** It exists as a
   debugging fallback; the spec recommends `Content-Type:
   application/faying-protocol+json`.
3. **Detached signatures.** The outer envelope `signature` block sits
   alongside the signed object — never inside the signed-input — so
   the audit trail can re-sign without reconstructing the payload.
4. **Inner Mandate signature.** The Mandate carried in
   `BOOTSTRAP_RESP.claims` has its own signature (signed by the MS
   key) computed over `Deterministic-CBOR(Mandate − signature)`. This
   matches the CDDL `mandate.signature` rule and is what downstream
   property tests (P13 audit chain, P16.1 endorsement signature
   inclusion) verify.

### JSON byte-string convention

JSON cannot carry raw bytes natively, so we encode every CBOR `bstr`
as a tagged object:

```json
{ "$bytes": "<base64url(no padding)>" }
```

Likewise CBOR tag-0 timestamps are mirrored as:

```json
{ "$tag": 0, "$value": "2026-01-01T00:00:00Z" }
```

This keeps the JSON tree shape isomorphic to the CBOR tree, so the
canonical-CBOR signing input recovers the same bytes whether you
start from JSON or CBOR (`_tools/verify.py` does this round-trip).

## Signature policy — why ML-DSA-65 is a placeholder

ML-DSA-65 (FIPS 204) is the post-quantum signature algorithm Faying
Protocol/1.0 MUST be able to negotiate (design.md §6.1, §8.2). At the
time these vectors were authored, no vetted ML-DSA-65 implementation
ships in the standard Python toolchain (`cryptography` does not yet
expose ML-DSA; `liboqs-python` ships its own dependencies and is not
universally available in CI).

To keep the vectors **deterministic and reproducible** without taking
on an optional dependency, ML-DSA-65 vectors carry a *placeholder
signature*:

```
sig := b"test-only-ml-dsa-65-sig-" || <8-byte label tag> || sha256(signing_input)
pubkey := b"test-only-ml-dsa-65-pubkey-" || <32 deterministic bytes>
```

`expected.json` for every ML-DSA-65 vector documents this with:

```json
"signature_verification": {
  "request_envelope": false,
  "response_envelope": false,
  "mandate_inner": false,
  "note": "Placeholder ML-DSA-65 signature; format-only check. ..."
}
```

When a real ML-DSA-65 backend lands (tracked under the §6.1 PQC
negotiation work item):

1. Replace the body of `make_ml_dsa_65` and `sign_bytes`/`verify_signature`
   in `_tools/generate.py` with calls into the real implementation.
2. Re-run `_tools/generate.py`. `index.json` digests will change; that
   change is the migration signal.
3. Flip `signature_verification.*: false` to `true` in the affected
   `expected.json` files.

The CDDL grammar already accepts `"ML-DSA-65"` in the
`signature-bundle.alg` enum, so no schema change is needed.

## Determinism

All vectors are reproducible. `_tools/generate.py` derives every key,
nonce, and synthetic payload byte from a fixed master seed
(`FAYING_VECTOR_SEED`). `index.json` records the SHA-256 of that seed
under `deterministic_seed_sha256` so reviewers can detect accidental
master-seed drift. The per-vector `digests.request_sha256` and
`digests.response_sha256` are also recorded in `expected.json` and
checked by `_tools/verify.py`.

To regenerate after any deliberate change:

```bash
python3 vectors/bootstrap/_tools/generate.py
python3 vectors/bootstrap/_tools/verify.py
bash    vectors/bootstrap/_tools/validate-with-cddl.sh
```

The first command rewrites the vectors; the second confirms structural
shape and signatures; the third runs the authoritative CDDL validator
against every positive Mandate.

## CDDL conformance

`_tools/validate-with-cddl.sh` extracts the inner Mandate from each
positive `BOOTSTRAP_RESP.claims` and validates it against
`schemas/fap-1.0.cddl` using the official `cddl` Ruby gem
(<https://rubygems.org/gems/cddl>, ≥ 0.12.0). The validator is invoked
through `_tools/mandate-only.cddl`, a verbatim copy of the schema with
the `mandate` rule reordered to the top so it is the entry rule.

Negative vectors deliberately violate one of:

- the `BootstrapClaims` envelope contract (missing `human_witness`),
- the `mandate.not-after` finiteness rule (Requirement 2.2),
- the `signature-bundle.alg` enum (Requirement 8.1).

They are therefore **not** expected to pass `mandate-only.cddl`
validation; the contract for negative vectors is that the response
body is a signed `ERROR` envelope carrying the documented error code.

## Attestation chain consistency

For positive vectors the chain instantiated by these fixtures is the
minimal HP → MS → IF triple from design.md §3.3:

```
HP key ──signs──▶ Attestation (BOOTSTRAP request envelope)
HP key ──signs──▶ BOOTSTRAP envelope (outer signature)
MS key ──signs──▶ Mandate (inner signature)
MS key ──signs──▶ BOOTSTRAP_RESP envelope (outer signature)
```

The HP and MS keys per vector are deterministically derived from the
seed (`derive("hp:<vector-name>", 32)` and `derive("ms:<vector-name>", 32)`
respectively) so the chain can be rebuilt independently from the
generator. Property tests under `pbt/tests/test_p13_audit_chain.py`
re-walk this chain and confirm each node verifies; conformance tests
under `conformance/` cross-check it across reference implementations.

Negative vectors keep the same key derivation but stop the chain at
the rejection point — only the ERROR response is countersigned by MS.

## Requirements traceability

These vectors validate the following requirements (see
`requirements.md`):

| Requirement | Acceptance criterion verified                                                                      |
| ----------- | ------------------------------------------------------------------------------------------------- |
| 2.2         | Every positive Mandate has a finite `not_after`; negatives `neg-not-after-infinity` and `neg-not-after-before` exercise the failure path. |
| 6.1         | `neg-no-witness` confirms missing `human_witness` is rejected with `E_HUMAN_WITNESS_REQUIRED`.    |
| 8.1         | `neg-unsupported-alg` exercises the algorithm-suite check; positive vectors cover the full {Ed25519, ES256, ML-DSA-65} matrix. |
| 10.1        | CBOR is the primary on-the-wire format; JSON variants prove the equivalence under the same CDDL grammar. |
| 10.2        | The signing input is canonical CBOR for both encodings (verified by `_tools/verify.py`).          |
| 10.3        | The cross-encoding × cross-algorithm matrix matches design.md §TS.4.                             |

## Stability promise

`index.json` is the canonical machine-readable manifest of this
directory. Once a Faying Protocol/1.0 release is cut, the `digests`
and `vector_name` fields in `index.json` and each `expected.json`
become normative for that release. Subsequent edits MUST either:

- bump the protocol version (`schemas/fap-1.0.cddl` and
  `index.json.spec_version` together), or
- be additive (new vectors only, no edits to existing payloads).

Until Faying Protocol/1.0 is cut, the vectors are draft and may be
regenerated; reviewers should diff `index.json` to spot any change.
