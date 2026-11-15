# Security Policy — Faying Protocol

## Supported Protocol & Artifact Versions

Security advisories and normative errata are maintained for the following released protocol baselines and their companion schemas, conformance vectors, and reference verifiers:

| Protocol Version | Normative Artifacts | Security Support |
| --- | --- | --- |
| `1.1-cofay` (`Faying Protocol/1.1`) | `schemas/fap-1.1-cofay.cddl`, `schemas/fap-1.1-cofay.json`, `vectors/cofay-stewardship-v1.1.json`, `docs/*/specification/1.1-cofay/` | Supported |
| `1.0` (`Faying Protocol/1.0`) | `schemas/fap-1.0.cddl`, `vectors/*/`, `docs/*/specification/2025-10-25/` | Supported |
| `< 1.0` (historical pre-release drafts) | Superseded snapshots | Unsupported |

> **Note on Reference Implementations & Conformance Vectors**: Code under `reference-impls/` and `conformance/` is provided for conformance verification and cross-language interoperability testing. Cryptographic seeds and keys stored under `vectors/` are deterministic public test fixtures and MUST NOT be used as production secrets.

## Security Scope

Reports are especially welcomed for vulnerabilities or specification ambiguities affecting:

1. **Cryptographic Mandate Binding**: Signature verification bypasses, canonical CBOR (RFC 8949) or RFC 8785 JCS signing-input malleability, domain-separation collisions, or algorithm downgrade flaws across `Ed25519`, `ECDSA-P256`, and the `ML-DSA-65` post-quantum agility slot.
2. **Graded Authority (`G0–G4`) & Presence Calibration**: Unauthorized elevation across `G0`–`G4` authorization grades, failure to downgrade or fail-closed (`Default-Deny`) when **Human Prime** presence signals expire, or scope boundary escapes.
3. **Symmetric Emergency Revocation & Disconnection Fail-Safe**: Delays, replay vulnerabilities, or bypasses in `REVOKE` handling, channel binding (TLS / mTLS RFC 9266), or disconnection safe-halt transitions.
4. **`1.1-cofay` Delegated Stewardship Chain**: Violations of the three-tier accountability chain (**Human Prime** / Organization Steward -> `iFay` Manager -> `coFay`), bypasses of the single-hop non-amplification ceiling (`hop_count == 1`, `grade <= manager_grade`, `scope` subset convergence), failure to cascade upstream `G0` halts (`E_UPSTREAM_EMERGENCY_HALT`), or dual-signature atomic stewardship transfer (`cofay-transfer-authorization`) forgery/replay.

## Reporting a Vulnerability Privately

**Please do NOT report undisclosed security vulnerabilities through public GitHub Issues, Discussions, or Pull Requests.**

### 1. Primary Channel — GitHub Private Vulnerability Reporting

Submit a confidential report directly via **GitHub Security Advisories**:

- **Report URL**: https://github.com/ChainMode/Faying-Protocol/security/advisories/new

### 2. Fallback Channel — Security Email

If GitHub Private Vulnerability Reporting is unavailable to you, send your report via email to:

- **Email**: **jah.g@ifay.ai**
- Include `[SECURITY][Faying-Protocol]` in the subject line along with affected schema/specification sections or reference verifier files, minimal reproduction steps or proof-of-concept test vectors, and impact assessment.

## Response & Coordinated Disclosure Timeline

- **Initial Acknowledgment**: Within **72 hours** of report receipt.
- **Triage & Severity Assessment**: Within **7 calendar days**, confirming reproducibility, affected versions (`1.0` / `1.1-cofay`), and remediation plan.
- **Coordinated Disclosure Window**: Up to **90 days** from receipt to allow downstream implementers to apply specification errata, conformance vectors, and verifier patches before public advisory publication. Credit will be attributed to the reporter unless anonymity is requested.
