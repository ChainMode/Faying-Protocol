> **Reference Implementation, Not Normative — for conformance testing only.**
>
> This crate exists solely to exercise the Faying Protocol/1.0 互操作合规测试
> 套件 (`conformance/`) and the cross-implementation matrix (task 5.6). It is
> **not** the protocol itself, **not** a production library, and carries no
> normative weight. The authoritative wire-format definition is
> [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl); the protocol正本 is
> [`docs/zh-CN/specification/2025-10-25/README.md`](../../docs/zh-CN/specification/2025-10-25/README.md).

# Faying Protocol/1.0 — Rust Reference Implementation

A Rust reference codec for the Faying Protocol/1.0 持续性授权协议, built on
[`ed25519-dalek`](https://crates.io/crates/ed25519-dalek) +
[`p256`](https://crates.io/crates/p256) +
[`ciborium`](https://crates.io/crates/ciborium). It parses and encodes protocol
messages (BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE / REVOKE /
FAYING_REQUEST / DISCLOSURE …), computes the §6.3 signing input, verifies and
produces signatures across the full algorithm suite, and exchanges interop
bundles byte-for-byte with the [TypeScript reference impl](../typescript).

## Why "Not Normative"

Two independent reference implementations (this one + the TypeScript one in
[`../typescript`](../typescript)) exist purely to demonstrate that the protocol
is implementable, unambiguous, and interoperable across languages. If this code
and `schemas/fap-1.0.cddl` ever disagree, **the CDDL wins** and this code is the
bug.

## Requirements

- A Rust toolchain (`cargo`), edition 2021. Authored against Rust 1.95.
- Dependencies (fetched by `cargo` from crates.io):
  - `ed25519-dalek` — Ed25519 signing/verification.
  - `p256` (feature `ecdsa`) — NIST P-256 ECDSA, fixed-length IEEE-P1363 r‖s.
  - `ciborium` — an independent third-party CBOR decoder used to cross-check
    well-formedness. (The canonical signing-input encoder is hand-rolled in
    [`src/detcbor.rs`](src/detcbor.rs) because `ciborium` preserves map
    insertion order rather than applying RFC 8949 §4.2.1 key sorting, which
    the corpus requires.)
  - `sha2`, `blake3` — the two hash-dimension algorithms.
  - `serde_json`, `hex`, `base64` — JSON wire form + encoding helpers.

## Build & Run

```bash
cd reference-impls/rust

cargo build
cargo test                          # unit + integration tests

# Run the full data-plane dimension matrix (tasks 5.2–5.5) over vectors/
cargo run -- dims                   # or: cargo run -- matrix

# Produce an interop bundle (each message in BOTH CBOR and JSON)
cargo run -- produce <outDir>

# Verify an interop bundle (e.g. one produced by the TS impl)
cargo run -- verify <inDir>
```

`cargo run -- dims` exits non-zero if any dimension fails, so it can gate CI.

## What each dimension checks (mirrors `conformance/dim_*/` and the TS impl)

| Dimension | Source task | Checks |
| --- | --- | --- |
| `encoding` | 5.2 | CBOR and JSON of each message collapse to a byte-identical Det-CBOR signing input; the SHA-256 matches `expected.json`; the CBOR envelope signature verifies. |
| `signing` | 5.3 | Every corpus envelope re-signs + verifies under Ed25519 / ES256 / ML-DSA-65; the signing input is invariant across algorithms; suite negotiation picks the strongest mutual algorithm and rejects disjoint sets with `E_PROTOCOL`. |
| `hash` | 5.4 | SHA-256 and BLAKE3 both produce 32-byte digests over the §6.3 signing input; SHA-256 matches any reference digest advertised by the vector. |
| `channel` | 5.5 | RFC 9266 channel-binding accept/reject matrix: mTLS requires a correct binding (else `E_ATTESTATION_INVALID`); TLS-only must not carry one. |

## Signing-input contract (the crux of interop)

Per [design.md §6.3](../../docs/en/specification/2025-10-25/README.md):

```
signing_input_bytes = Deterministic-CBOR( Envelope_without_signature )   // RFC 8949 §4.2.1
signing_input_hash  = SHA-256( signing_input_bytes )                     // cross-encoding identity
```

The Ed25519 / ECDSA-P256 signature is computed over `signing_input_bytes`
directly (each algorithm applies its own internal hash). The `signing_input_hash`
is the value the official vectors record in `expected.json` and the value the
cross-impl manifest carries so both implementations can confirm they agree
byte-for-byte. This matches `vectors/encoding-equivalence/generate.py`, the
Python conformance drivers, and the TypeScript reference impl.

The integration test `round_trips_encoding_equivalence_corpus_byte_for_byte`
proves this crate's deterministic CBOR encoder reproduces the on-disk canonical
bytes of the Python-generated vectors exactly, so cross-language interop rests
on a verified foundation rather than coincidence.

## Layout

```
reference-impls/rust/
├── Cargo.toml
├── src/
│   ├── detcbor.rs      Deterministic CBOR codec (RFC 8949 §4.2.1)
│   ├── json_wire.rs    JSON fallback wire form ⟷ value model
│   ├── crypto.rs       Ed25519 / ES256 / ML-DSA-65 (placeholder) sign/verify
│   ├── hash.rs         SHA-256 / BLAKE3 over the signing input
│   ├── negotiation.rs  Algorithm-suite negotiation (Requirement 8.1 / 8.2)
│   ├── protocol.rs     Envelope model + §6.3 signing input + builders
│   ├── vectors.rs      Loads the official vectors/ corpus
│   ├── dimensions.rs   Runs the 5.2–5.5 dimension matrix
│   ├── interop.rs      Produce / verify cross-impl interop bundles
│   ├── lib.rs          Library root
│   └── main.rs         CLI entry point
└── tests/
    └── codec.rs        Unit + integration tests (cargo test)
```

## ML-DSA-65 note

A vetted pure-Rust ML-DSA-65 (FIPS 204) implementation is not bundled. As with
the official vector toolchain, the Python conformance drivers, and the TS
reference impl, the ML-DSA-65 path here uses a **deterministic placeholder**
signature so the algorithm-agility and negotiation logic is exercised
end-to-end. The placeholder is format-checked only and **must not** be mistaken
for cryptography.
