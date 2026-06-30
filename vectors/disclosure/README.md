# DISCLOSURE Test Vectors

> **Spec refs**: Faying Protocol/1.0 §5.3.7 (DISCLOSURE 报文) · §9.10.4 T3 (避重就轻 / Selective Disclosure)
> **Requirement**: 13.3 (T3 结构化 Disclosure_Report 强约束)
> **Property**: P18.3 (`Disclosure_Mandatory_Fields`)
> **Task**: `tasks.md` 3.10

This suite exercises **schema-level enforcement** of the structured DISCLOSURE
report defined in §5.3.7. It does not attempt to verify cryptographic
signatures end-to-end (those are covered by `vectors/encoding-equivalence/`
and `conformance/dim_signing/`); instead it pins down the protocol-layer
behaviour of `mandatory_fields`, the high-sensitivity pre-disclosure rule,
the `ego-deviation` revoke trigger, and the Disconnected-period
`endorsement_id` linkage.

## Layout

```
vectors/disclosure/
├── README.md                ← this file
├── index.json               ← machine-readable suite manifest
├── _gen.py                  ← deterministic generator (re-run to rebuild)
├── _validate.py             ← suite-level invariants checker
└── <NN-slug>/
    ├── disclosure.cbor      ← Deterministic-CBOR (RFC 8949 §4.2.1) envelope
    ├── disclosure.json      ← application/fap+json equivalent (kebab-case)
    ├── context.json         ← surrounding context (mandate state, audit window)
    └── expected.json        ← outcome + audit notes
```

`disclosure.cbor` encodes the full `FayingProtocolEnvelope<DisclosureClaims>`
exactly as it appears on the wire (kebab-case keys, CBOR tag 0 for ISO times).
`disclosure.json` is the JSON fall-back encoding (`application/fap+json`,
§5.1); byte fields are wrapped as `{"$b64u": "<base64url-no-pad>"}` so the
two encodings round-trip losslessly.

## Case coverage

The 15 vectors realise every case (a)–(f) in task 3.10.

| Case | Description | Vectors |
| --- | --- | --- |
| **a** | All `mandatory_fields` legal (`action / scope_used / risk_level / reversibility / affected_resources / uncertainty_flags`) | 01, 02 |
| **b** | Each `mandatory_field` individually missing → `E_PROTOCOL` (1099) | 03–08 (one per field) |
| **c** | Field unparseable (enum out-of-range) → `E_PROTOCOL` (1099) | 09 (`risk_level="extreme"`), 10 (`reversibility="maybe"`) |
| **d** | High-sensitivity action (`risk_level ∈ {high, critical}`) executed without prior DISCLOSURE → reject | 11 |
| **e** | DISCLOSURE inconsistent with the actual action recorded in the audit log → `RevokeReason="ego-deviation"` | 12 |
| **f** | Disconnected-period DISCLOSURE: must carry `endorsement_id`, and that id must be independently verifiable | 13 (✓ valid id), 14 (missing), 15 (bogus / unresolvable id) |

`expected.outcome` is constrained to `{accepted, E_PROTOCOL, ego-deviation-revoke}` per task acceptance.

## Acceptance criteria

Both criteria from `tasks.md` 3.10 are mechanically verified by `_validate.py`:

1. **Each vector contains `expected.outcome`** — checked against the allowed
   set `{accepted, E_PROTOCOL, ego-deviation-revoke}`.
2. **Disconnected-period DISCLOSURE has `endorsement_id` independently
   verifiable** — for every vector whose `context.is_disconnected = true`:
   - if `expected.outcome = accepted`, the in-message `endorsement-id` MUST
     equal the `endorsement_id` recorded in `context.endorsement_id`
     (independently verifiable via the context bundle, without trusting the
     message itself);
   - if `expected.outcome = E_PROTOCOL`, the rejection path MUST be
     independently observable (id missing, or id present but unresolvable
     against the context).

`_validate.py` also asserts the auxiliary invariants:

- 6/6 cases (a–f) covered, ≥10 vectors total;
- `index.json` enumerates exactly the on-disk vectors;
- every `disclosure.cbor` is byte-stable canonical CBOR (round-trip equal);
- `disclosure.cbor` and `disclosure.json` decode to the same logical
  structure (after `$b64u` is unwrapped).

## Field map (`mandatory_fields`)

The six mandatory fields of `DisclosureClaims` (§5.3.7):

| TS / JSON key            | CBOR key                | Type                                               | Notes                                  |
| ------------------------ | ----------------------- | -------------------------------------------------- | -------------------------------------- |
| `action`                 | `action`                | `tstr` (Atomic_Action)                             | Exactly one — wildcards forbidden (P18.2) |
| `scope_used`             | `scope-used`            | `scope`                                            | Subset of `Mandate.scope` actually used |
| `risk_level`             | `risk-level`            | enum `low / normal / high / critical`              | High/critical → pre-disclosure required |
| `reversibility`          | `reversibility`         | enum `reversible / partially-reversible / irreversible` |                                       |
| `affected_resources`     | `affected-resources`    | `[* tstr]` (array, may be `[]`)                   | Empty list allowed; absence ≠ allowed   |
| `uncertainty_flags`      | `uncertainty-flags`     | `[* tstr]` (array, may be `[]`)                   | Empty list allowed; absence ≠ allowed   |

Optional supplements: `free_text`, `intent ∈ {report, request-confirmation}`,
`endorsement_id` (REQUIRED for Disconnected-period actions per §5.3.7 final
bullet).

## Encoding

- **CBOR (primary, normative)**: RFC 8949 Deterministic Encoding (§4.2.1).
  Decoders MUST treat `disclosure.cbor` as the on-wire reference; signature
  inputs in upstream specs are computed over the same canonical encoding
  with the `signature` field stripped (§6.3).
- **JSON (fallback, normative)**: `application/fap+json`. Bytes (`nonce`,
  `pubkey`, `sig`, `payload`) are encoded as `{"$b64u": "<base64url-no-pad>"}`
  per §5.1's JSON fall-back rules. ISO timestamps are plain strings (CBOR
  tag 0 is dropped on the JSON side).

## Reproducing

```bash
# Regenerate from the vector definitions in _gen.py.
python3 vectors/disclosure/_gen.py

# Validate the suite against the task 3.10 acceptance criteria.
python3 vectors/disclosure/_validate.py
```

Both scripts have a single dependency: the `cbor2` Python package.

## Stub-signature disclaimer

`signature` and `attestation` blocks in these vectors are deterministic stubs
(sentinel byte strings `STUB-SIG…`, `STUB-PUBKEY…`, `STUB-ATTESTATION…`).
This suite focuses on **schema-level** behaviour for Requirement 13.3; full
end-to-end signature verification across algorithm × encoding combinations
is the responsibility of:

- `vectors/encoding-equivalence/` (task 3.7) — Deterministic-CBOR ↔ JSON
  signature-input equivalence;
- `conformance/dim_signing/` (task 5.3) — Ed25519 / ECDSA-P256 / ML-DSA-65
  algorithm matrix.

Conformance runners that load these vectors should treat the `signature`
bundle as an opaque structural placeholder; do not attempt to verify it
cryptographically.

## Cross-references

- `docs/zh-CN/specification/draft/Faying-Protocol-1.0.md` §5.3.7, §5.4 (1099
  `E_PROTOCOL` DISCLOSURE-path note `*`), §9.10.4 T3, §EH.1
- `.kiro/specs/faying-auth-protocol/requirements.md` Requirement 13.3
- `.kiro/specs/faying-auth-protocol/design.md` §5.3.7, §9.10.4, §12 P18.3
- `schemas/fap-1.0.cddl` — authoritative wire schema
- `schemas/types.ts` `DisclosureClaims` — non-normative TS reflection
