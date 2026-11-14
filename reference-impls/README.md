# Faying Protocol/1.0 — Reference Implementations

> **Reference Implementation, Not Normative — for conformance testing only.**
>
> The implementations under this directory exist solely to drive the
> [互操作合规测试套件 (`conformance/`)](../conformance/README.md) defined by
> Requirement 10.3 / design.md §TS.4. They are **not part of the protocol
> specification** and **MUST NOT** be cited as authoritative. The authoritative
> grammar is [`schemas/fap-1.0.cddl`](../schemas/fap-1.0.cddl); the
> authoritative wire format is described in the protocol正本
> [`docs/zh-CN/specification/draft/Faying-Protocol-1.0.md`](../docs/zh-CN/specification/draft/Faying-Protocol-1.0.md)
> §5 / §6.

## Layout

| Path                                | Language   | Crypto stack                         | Purpose                           |
| ----------------------------------- | ---------- | ------------------------------------ | --------------------------------- |
| [`typescript/`](./typescript/README.md) | TypeScript / Node.js | `node:crypto` Ed25519 + ECDSA-P256, custom canonical-CBOR | Conformance smoke driver, vector verifier |
| [`rust/`](./rust/README.md)         | Rust       | `ed25519-dalek` + `p256` + `ciborium` | Same role; second independent stack |

Both implementations consume the same on-disk artefacts:

- `vectors/` — task 3.x official test vectors (the neutral wire format
  produced by the Python generator in `_tools/generate.py`).
- `schemas/fap-1.0.cddl` — the normative CDDL grammar (Section §4.2 of the
  protocol正本).

Cross-implementation interop is exercised against those neutral vectors:
each implementation independently decodes, re-derives the canonical-CBOR
signing input, and verifies the Ed25519 / ECDSA-P256 signature. Results are
recorded in [`conformance/cross-impl/results.md`](../conformance/cross-impl/results.md).

## Why "Not Normative"

design.md §6 explicitly anchors normativity at the CDDL + the prose. Anything
shipped here is illustrative only:

- An interop bug between TS and Rust is **not** a protocol bug unless it can
  be traced back to ambiguity in the CDDL, the timestamp tag-0 rule, the
  canonical-CBOR rule (RFC 8949 §4.2.1), or the §6.3 signing-input
  definition.
- If an interop bug **does** map back to a spec ambiguity, it MUST be filed
  as an Issue against the protocol committee per the §11 Open Questions
  workflow, not patched silently in either reference impl.

## Banner requirement

Every source file in `typescript/` and `rust/`, and every `README.md`,
carries the banner

> Reference Implementation, Not Normative — for conformance testing only.

so reviewers can distinguish reference code from any future
production-quality SDK (which would have its own normative gates).
