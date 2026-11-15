# Contributing to Faying Protocol

Thank you for contributing to **Faying Protocol**! This guide covers repository setup, conformance verification, schema discipline, commit sign-off, terminology standards, and dual-track licensing.

## Code of Conduct & Security

- All participants are expected to uphold our [Code of Conduct](./CODE_OF_CONDUCT.md) (contact: **jah.g@ifay.ai**).
- Never report undisclosed vulnerabilities in public issues or pull requests; follow [SECURITY.md](./SECURITY.md) instead.

## Contribution Workflow

1. Fork `https://github.com/ChainMode/Faying-Protocol` on GitHub.
2. Clone your fork and configure `upstream`:
   ```bash
   git clone https://github.com/<your-username>/Faying-Protocol.git
   cd Faying-Protocol
   git remote add upstream https://github.com/ChainMode/Faying-Protocol.git
   ```
3. Create a focused topic branch from `main` (for example `feat/mandate-vector`, `fix/rust-cbor`, `docs/spec-clarification`).
4. Run the verification suites below before opening a Pull Request against `main`.

## Build, Conformance & Vector Verification

Faying Protocol ships cross-language reference verifiers (`reference-impls/`) and a five-dimensional conformance matrix (`conformance/`) backed by deterministic vectors (`vectors/`):

```bash
# 1. TypeScript reference verifier (Node.js >= 22.6)
cd reference-impls/typescript
npm test
npm run typecheck
cd ../..

# 2. Rust reference verifier (Cargo / Rust 2021)
cd reference-impls/rust
cargo test
cd ../..

# 3. Python conformance matrix & adversarial vector suite
python3 conformance/runner.py --dry-run
python3 -m pytest conformance
```

## Schema, Specification & Conformance Vector Discipline

- **Frozen `1.0` Baseline**: `schemas/fap-1.0.cddl`, `docs/{lang}/specification/2025-10-25/`, and published `1.0` vector families under `vectors/` are normative and **frozen**. Do not introduce breaking wire changes or mutate released `1.0` schemas in place.
- **Additive Minor Evolution**: Backward-compatible minor capabilities MUST be introduced via new versioned files (such as `schemas/fap-1.1-cofay.cddl`, `schemas/fap-1.1-cofay.json`, `vectors/cofay-stewardship-v1.1.json`, and `docs/{lang}/specification/1.1-cofay/`) verified across both TypeScript and Rust reference verifiers.
- **Multilingual Alignment**: `zh-CN` under `docs/zh-CN/` is the canonical source for narrative blueprints and specifications; translations in `zh-TW`, `en`, `ja`, `ko`, `de`, `es`, `fr`, and `ru` must preserve normative RFC 2119 / RFC 8174 keywords and structural parity.

## Ecosystem Terminology Rules

All specifications, schemas, comments, and documentation MUST use canonical positive iFay terminology:

- **`Human Prime`** (`人类原型`): Exclusively denotes the natural person mapped and served by an `iFay` (or the accountable natural-person witness behind an organizational steward).
- **`Host`** (`宿主`): Strictly denotes a runtime terminal hardware device, actuator peripheral, or client software application.
- **`Fay`** (`iFay` + `coFay`): Denotes an accountable digital avatar bound to a verifiable legal responsibility entity.
- **`GMChain`** (`公誉链`) & **`MeriToken`** (`美誉值` / `Merit Unit`): Denotes the ecosystem's strictly non-monetary social contribution reputation metric.

## Commit Convention & DCO 1.1 Sign-Off

Use [Conventional Commits](https://www.conventionalcommits.org/) (`feat`, `fix`, `docs`, `schema`, `refactor`, `test`, `chore`).

Every commit MUST include a **Developer Certificate of Origin v1.1 (DCO 1.1)** `Signed-off-by` trailer (`git commit -s`), certifying that you have the right to submit the contribution under this repository's licenses (full text at https://developercertificate.org/):

```text
feat(vectors): add stewardship expiry boundary case

Signed-off-by: Your Legal Name <you@example.com>
```

No separate CLA is required.

## Dual-Track Inbound = Outbound Licensing

By submitting a contribution (`Inbound = Outbound`), you agree that your contribution is licensed under the repository's dual-track model (`Copyright (c) 2025-2026 ChainMode contributors`):

- **MIT License** ([`LICENSE`](./LICENSE)) for reference implementations (`reference-impls/`, `conformance/`), machine-readable schemas (`schemas/`), and conformance test vectors (`vectors/`).
- **Creative Commons Attribution 4.0 International (`CC BY 4.0`)** ([`LICENSE-DOCS`](./LICENSE-DOCS)) for protocol specifications and architectural blueprint documents under `docs/`.
