> **Reference Implementation, Not Normative — for conformance testing only.**
>
> This package exists solely to exercise the Faying Protocol/1.0 互操作合规
> 测试套件 (`conformance/`) and the cross-implementation matrix (task 5.6).
> It is **not** the protocol itself, **not** a production library, and carries
> no normative weight. The authoritative wire-format definition is
> [`schemas/fap-1.0.cddl`](../../schemas/fap-1.0.cddl); the protocol正本 is
> [`docs/zh-CN/specification/2025-10-25/README.md`](../../docs/zh-CN/specification/2025-10-25/README.md).

# Faying Protocol/1.0 — TypeScript Reference Implementation

A Node.js reference codec for the Faying Protocol/1.0 持续性授权协议. It parses
and encodes protocol messages (BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE /
REVOKE / FAYING_REQUEST / DISCLOSURE …), computes the §6.3 signing input,
verifies and produces signatures across the full algorithm suite, and emits
interop bundles consumable by the Rust reference implementation.

It uses WebAuthn concepts for the human-witness model and a deterministic CBOR
codec for byte-exact interoperability with the official `vectors/` corpus.

## Why "Not Normative"

Two independent reference implementations (this one + the Rust one in
[`../rust`](../rust)) exist purely to demonstrate that the protocol is
implementable, unambiguous, and interoperable across languages. If this code
and `schemas/fap-1.0.cddl` ever disagree, **the CDDL wins** and this code is
the bug.

## Requirements

- **Node.js ≥ 22.6.0** — the source is authored in TypeScript and run directly
  via Node's native type-stripping (`node src/cli.ts …`), so **no build step**
  is required. Node 24 (used to author this) works out of the box.
- Dependencies (installed via `npm install`):
  - [`cbor-x`](https://www.npmjs.com/package/cbor-x) — an independent
    third-party CBOR decoder used to cross-check that the bytes we emit are
    well-formed CBOR. (The canonical signing-input encoder is hand-rolled in
    [`src/detcbor.ts`](src/detcbor.ts) because mainstream encoders do not
    implement RFC 8949 §4.2.1 key ordering the way the corpus requires.)
  - [`@noble/hashes`](https://www.npmjs.com/package/@noble/hashes) — pure-JS
    BLAKE3 for the hash dimension. SHA-256 / Ed25519 / ECDSA-P256 come from
    Node's built-in `node:crypto`.

## Install

```bash
cd reference-impls/typescript
npm install
```

## Run

```bash
# Run the full data-plane dimension matrix (tasks 5.2–5.5) over vectors/
node src/cli.ts dims          # or: npm run matrix

# Produce an interop bundle (each message in BOTH CBOR and JSON)
node src/cli.ts produce <outDir>

# Verify an interop bundle (e.g. one produced by the Rust impl)
node src/cli.ts verify <inDir>

# Unit tests
node --test                   # or: npm test

# Optional: strict type-check (requires devDependencies installed)
npm run typecheck
```

`node src/cli.ts dims` exits non-zero if any dimension fails, so it can gate CI.

## What each dimension checks (mirrors `conformance/dim_*/`)

| Dimension | Source task | Checks |
| --- | --- | --- |
| `encoding` | 5.2 | CBOR and JSON of each message collapse to a byte-identical Det-CBOR signing input; the SHA-256 matches `expected.json`; the CBOR envelope signature verifies. |
| `signing` | 5.3 | Every corpus envelope re-signs + verifies under Ed25519 / ES256 / ML-DSA-65; the signing input is invariant across algorithms; suite negotiation picks the strongest mutual algorithm and rejects disjoint sets with `E_PROTOCOL`. |
| `hash` | 5.4 | SHA-256 and BLAKE3 both produce 32-byte digests over the §6.3 signing input; SHA-256 matches any reference digest advertised by the vector. |
| `channel` | 5.5 | RFC 9266 channel-binding accept/reject matrix: mTLS requires a correct binding (else `E_ATTESTATION_INVALID`); TLS-only must not carry one. |

## Signing-input contract (the crux of interop)

Per [design.md §6.3](../../docs/en/specification/2025-10-25/README.md):

```
signing_input_bytes = Deterministic-CBOR( Envelope_without_signature )   # RFC 8949 §4.2.1
signing_input_hash  = SHA-256( signing_input_bytes )                     # cross-encoding identity
```

The Ed25519 / ECDSA-P256 signature is computed over `signing_input_bytes`
directly (each algorithm applies its own internal hash). The
`signing_input_hash` is the value the official vectors record in
`expected.json` and the value the cross-impl manifest carries so both
implementations can confirm they agree byte-for-byte. This matches the
behaviour of `vectors/encoding-equivalence/generate.py` and the Python
conformance drivers.

## Layout

```
reference-impls/typescript/
├── package.json
├── src/
│   ├── detcbor.ts      Deterministic CBOR codec (RFC 8949 §4.2.1)
│   ├── json_wire.ts    JSON fallback wire form ⟷ value model
│   ├── crypto.ts       Ed25519 / ES256 / ML-DSA-65 (placeholder) sign/verify
│   ├── hash.ts         SHA-256 / BLAKE3 over the signing input
│   ├── negotiation.ts  Algorithm-suite negotiation (Requirement 8.1 / 8.2)
│   ├── protocol.ts     Envelope model + §6.3 signing input + builders
│   ├── vectors.ts      Loads the official vectors/ corpus
│   ├── dimensions.ts   Runs the 5.2–5.5 dimension matrix
│   ├── interop.ts      Produce / verify cross-impl interop bundles
│   └── cli.ts          Command-line entry point
└── test/
    └── codec.test.ts   Unit tests (node --test)
```

## ML-DSA-65 note

A vetted pure-JS ML-DSA-65 (FIPS 204) implementation is not bundled. As with
the official vector toolchain and the Python conformance drivers, the
ML-DSA-65 path here uses a **deterministic placeholder** signature so the
algorithm-agility and negotiation logic is exercised end-to-end. The
placeholder is format-checked only and **must not** be mistaken for
cryptography.
