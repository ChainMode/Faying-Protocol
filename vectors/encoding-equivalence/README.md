# Encoding Equivalence Vectors — `vectors/encoding-equivalence/`

> **Spec:** Faying Protocol/1.0
> **Task:** [`tasks.md` 3.7](../../.kiro/specs/faying-auth-protocol/tasks.md) — 跨编码 round-trip 向量（CBOR ↔ JSON 等价）
> **Requirements covered:** `R10.1.3`, `R10.1.4`, `R10.2.1`, `R10.2.4`
> **Normative references:** [`design.md` §5.1 编码规则](../../docs/zh-CN/specification/draft/Faying-Protocol-1.0.md), §5.2 信封结构, §6.3 签名格式（S2 / S4）；[RFC 8949](https://www.rfc-editor.org/rfc/rfc8949) §4.2.1 Core Deterministic Encoding；[RFC 8259](https://www.rfc-editor.org/rfc/rfc8259) JSON；[RFC 4648](https://www.rfc-editor.org/rfc/rfc4648) §5 base64url

---

## What this vector set demonstrates

For each of the **five business message types** below, this directory ships
**one representative vector** in **both** CBOR and JSON encodings, plus the
shared signature input and an `expected.json` recording the equivalence
assertions:

| # | Folder | `msg_type` | Scenario |
| - | - | - | - |
| 1 | [`01-bootstrap/`](./01-bootstrap/)         | `BOOTSTRAP`     | HP issues a fresh G2 Mandate to an iFay (single-action read scope, WebAuthn UV witness). |
| 2 | [`02-presence/`](./02-presence/)           | `PRESENCE`      | iFay heartbeats a fresh `webauthn-uv-fresh` signal to refresh `PresenceState.last_freshness`. |
| 3 | [`03-grade-switch/`](./03-grade-switch/)   | `GRADE_SWITCH`  | HP upgrades an active Mandate from G2 → G1 with a WebAuthn `human_witness`. |
| 4 | [`04-delegate/`](./04-delegate/)           | `DELEGATE`      | A child Mandate is derived to a new terminal — `child.scope ⊆ parent.scope`, `child.grade ≥ parent.grade`. |
| 5 | [`05-revoke/`](./05-revoke/)               | `REVOKE`        | HP revokes a Mandate with `cascade=true`, `reason="human-initiated"`. |

The headline acceptance criteria of task 3.7 are:

1. **CBOR & JSON deserialize to semantically equal objects.**
2. **The signature input hash is identical across both encodings.**
3. **Signature verification yields the same result from either encoding.**

All three are enforced by [`verify.py`](./verify.py) over the on-disk artefacts
on every run.

---

## Files per vector

Each `NN-<msg-type>/` directory contains:

| File | Content |
| --- | --- |
| `message.cbor`                    | RFC 8949 Deterministic CBOR encoding of the **signed** envelope. Wire `Content-Type: application/faying-protocol+cbor`. |
| `message.cbor.hex`                | Lower-case hex of `message.cbor` for diffability. |
| `message.json`                    | JSON encoding of the **same** signed envelope. Wire `Content-Type: application/faying-protocol+json`. Binary fields are base64url-encoded strings (see below). |
| `signature.input.det-cbor.hex`    | Hex of `Deterministic-CBOR( Envelope_without_signature )` — the byte string fed to the hash function. |
| `signature.input.hash.hex`        | Hex of `SHA-256(signature.input.det-cbor)` — the per-design.md §6.3 S2 signature input. |
| `expected.json`                   | Equivalence assertions, traceability, signature artefacts, and the binary-field mapping needed to round-trip JSON ↔ CBOR. |

Plus the two top-level files:

| File | Content |
| --- | --- |
| [`index.json`](./index.json) | Machine-readable manifest: list of vectors, fixed seed, conventions, traceability. |
| [`generate.py`](./generate.py) | Reproducible generator. Re-running it overwrites the vectors byte-for-byte. |
| [`verify.py`](./verify.py)     | Independent verifier — re-runs all equivalence assertions against the on-disk artefacts. |

---

## Conventions

### Key naming

Wire keys use **kebab-case** to match the authoritative [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl) (e.g. `msg-type`, `not-after`, `signal-types`). The TypeScript human-readable view in [`schemas/types.ts`](../../schemas/types.ts) uses `snake_case` and documents the 1:1 mapping; both are non-normative views of the same wire-level keys.

### Binary fields in JSON

JSON has no native bytes type. CBOR `bstr` fields are encoded in JSON as **base64url with stripped padding** (RFC 4648 §5, no `=` padding). The exact list of binary paths for every vector is recorded in `expected.json → binary_field_paths`, expressed as dotted paths (e.g. `header.nonce`, `attestation.signature.sig`). Receivers re-hydrate bytes by base64url-decoding those paths before comparing to the CBOR shape.

### Deterministic CBOR

All signature inputs are produced by **RFC 8949 §4.2.1 Core Deterministic Encoding** (length-first lexicographic key order, shortest integer encoding, no indefinite-length items, etc.), implemented by `cbor2.dumps(obj, canonical=True)`. This is what makes the signature input independent of any JSON serialisation ambiguity — both encodings flow through the same deterministic CBOR before the hash.

### Cryptography

| Primitive | Choice | Rationale |
| --- | --- | --- |
| Hash | SHA-256 | Default per `design.md §6.1`. |
| Signature | Ed25519 | Default per `design.md §6.1`; deterministic, fast to verify. |
| Seed | `00112233…22 1100` (32 bytes, see `index.json`) | Fixed for reproducibility; **NEVER use this seed for production**. |

The same Ed25519 keypair is reused across all five vectors so that reviewers can verify any subset independently with a single public key.

> ⚠️ **Test-only material.** The `attestation.signature.sig` and inner `presence-signal.signature.sig` bytes are deterministic placeholders. This vector set tests **wire-format equivalence**, not the inner attestation chain (those properties are exercised by the per-message vector sets in tasks 3.1–3.6).

---

## Acceptance check (the equivalence proof)

For every vector the verifier (and the generator's self-check) asserts:

```
let cbor_obj   = cbor2.loads( message.cbor )
let json_raw   = json.loads( message.json )
let json_obj   = decode_binary_paths( json_raw, expected.binary_field_paths )

assert cbor_obj == json_obj                                   ── (1) semantic equality

let det_cbor_from_cbor = canonical_cbor( cbor_obj − signature )
let det_cbor_from_json = canonical_cbor( json_obj − signature )

assert det_cbor_from_cbor == det_cbor_from_json
       == bytes.fromhex( signature.input.det-cbor.hex )       ── (2) identical Det-CBOR
assert sha256( det_cbor_from_cbor ).hex()
       == signature.input.hash.hex
       == expected.signature_input.hash_hex                   ── (3) identical hash

assert ed25519.verify( pub, sig, det_cbor_from_cbor ) == OK
assert ed25519.verify( pub, sig, det_cbor_from_json ) == OK   ── (4) identical verify result
```

Run it locally:

```bash
python3 vectors/encoding-equivalence/verify.py
```

Expected output:

```
Verifying 5 vector(s) in encoding-equivalence/ ...
  [PASS] 01-bootstrap  (BOOTSTRAP)
  [PASS] 02-presence  (PRESENCE)
  [PASS] 03-grade-switch  (GRADE_SWITCH)
  [PASS] 04-delegate  (DELEGATE)
  [PASS] 05-revoke  (REVOKE)

All equivalence assertions hold:
  • CBOR & JSON decode to semantically equal objects
  • Det-CBOR(envelope_without_signature) is identical across encodings
  • SHA-256(signature_input) matches expected.json
  • Ed25519 verification yields the same outcome from both encodings
```

---

## Reproducing / regenerating

```bash
# Required Python deps
pip install cbor2 cryptography

# Regenerate all artefacts in place (deterministic; produces identical bytes)
python3 vectors/encoding-equivalence/generate.py

# Re-verify
python3 vectors/encoding-equivalence/verify.py
```

The generator is a single file with no hidden state. The fixed seed and the
canonical CBOR rule together guarantee bit-stable output across runs and
machines.

---

## Traceability

| Requirement | EARS clause | Where it shows up here |
| --- | --- | --- |
| 10.1 — CBOR primary / JSON fallback equivalence | `R10.1.3` | Each vector ships both encodings with proven semantic equality. |
| 10.1 — Det-CBOR before signing removes JSON ambiguity | `R10.1.4` | Both encodings collapse to one Det-CBOR byte string before signing. |
| 10.2 — Det-CBOR per RFC 8949 §4.2.1 | `R10.2.1` | `cbor2.dumps(obj, canonical=True)` ≡ Core Deterministic Encoding. |
| 10.2 — `signature_input = H( Det-CBOR( Envelope_without_signature ) )` | `R10.2.4` | Stored verbatim as `signature.input.det-cbor.hex` and `signature.input.hash.hex`. |

| Design section | Coverage in this vector set |
| --- | --- |
| §5.1 编码规则 | CBOR primary, JSON fallback, deterministic encoding, base64url for `bstr`. |
| §5.2 信封结构 | The full `FayingProtocolEnvelope` is exercised end-to-end in every vector. |
| §6.3 S2 签名输入 | `signature.input.det-cbor.hex` is the literal `Deterministic-CBOR(Envelope_without_signature)`. |
