# PRESENCE Test Vectors — Faying Protocol/1.0

This directory holds the official PRESENCE test vectors for Faying
Protocol/1.0. They exercise the `presence-signal` rule of
`schemas/fap-1.0.cddl` and the verdict matrix derived from
[`design.md`](../../.kiro/specs/faying-auth-protocol/design.md):

- §3.2 Presence Channel — signal-type strength table and on-loss policy
- §5.3.2 PRESENCE message — wire shape carried inside the envelope
- §7.1 Authorization Grades — `max-staleness` budget per grade

The vectors are produced by `_tools/generate.py` and verified by
`_tools/verify.py`. They are referenced from:

- `index.json` — machine-readable catalogue of every vector.
- The PBT suite under `pbt/` (task 4.x) consumes them as fixtures for
  P8 (presence freshness) and P18.1 (presence challenge-response).
- The conformance suite under `conformance/` (task 5.x) drives them
  across reference implementations.

## Vector matrix (5 × 3 = 15)

| Signal type                 | Bound grade (§7.1) | `max-staleness-ms` | fresh                                    | stale                                   | tampered                                              |
| --------------------------- | ------------------ | -----------------: | ---------------------------------------- | --------------------------------------- | ----------------------------------------------------- |
| `webauthn-uv-fresh`         | G1 Strict          |              5 000 | `fresh-webauthn-uv` (1.5 s)              | `stale-webauthn-uv` (11 s)              | `tampered-webauthn-uv-bad-signature`                  |
| `face-continuous`           | G1 Strict          |              5 000 | `fresh-face-continuous` (2.5 s)          | `stale-face-continuous` (8 s)           | `tampered-face-continuous-bad-attestation`            |
| `fingerprint-tap`           | G2 Moderate        |             60 000 | `fresh-fingerprint-tap` (20 s)           | `stale-fingerprint-tap` (90 s)          | `tampered-fingerprint-tap-replay`                     |
| `presence-heartbeat-only`   | G4 Autonomous      |          1 800 000 | `fresh-presence-heartbeat-only` (10 min) | `stale-presence-heartbeat-only` (35 min)| `tampered-presence-heartbeat-only-bad-signature`      |
| `intent-ticket`             | G3 Loose           |            300 000 | `fresh-intent-ticket` (90 s)             | `stale-intent-ticket` (6 min)           | `tampered-intent-ticket-replay`                       |

The freshness budgets are taken verbatim from `design.md` §7.1:
G1 = 5 s, G2 = 60 s, G3 = 5 min, G4 = 30 min. `index.json` records
the same table under `freshness_table`.

### Verdict mapping

Each `expected.json` declares `verdict ∈ {ok, stale, replay,
attestation-invalid}` together with the §EH.1 error code that a
conformant verifier must emit:

| Verdict               | Error code (`§EH.1`) | When it applies                                                                                                         |
| --------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| `ok`                  | none                 | Signature verifies, attestation verifies, `(now − produced_at) ≤ max_staleness_ms`, nonce not in seen-set.               |
| `stale`               | `1005 E_PRESENCE_STALE` | Signature & attestation verify, but `(now − produced_at) > max_staleness_ms`.                                            |
| `replay`              | `1009 E_REPLAY`      | Signature & attestation verify, but `(mandate-id, nonce)` already consumed (see `expected.replay_of`).                   |
| `attestation-invalid` | `1007 E_ATTESTATION_INVALID` | Outer envelope signature fails, OR device-attestation signature fails.                                                  |

## Per-vector layout

Each vector lives in its own folder and contains:

| File             | Purpose                                                                                              |
| ---------------- | ---------------------------------------------------------------------------------------------------- |
| `signal.cbor`    | Canonical CBOR (RFC 8949 §4.2.1) encoding of the `presence-signal` envelope.                         |
| `signal.json`    | Equivalent JSON encoding (`Content-Type: application/faying-protocol+json`) using the bytes / tag-0 markers. |
| `expected.json`  | Verdict, error code, freshness window, mandate-id, signal-type, device-id, nonce, tamper category, requirements traceability, on-disk digests. |
| `debug.json`     | Human-readable mirror of `signal.json`. Not normative.                                               |

Both `signal.cbor` and `signal.json` decode to the same logical tree
(`signal.cbor == canonicalCBOR(materialise(signal.json))`,
byte-identical) — the verifier asserts this round-trip on every
vector.

## Verifying the vectors

```bash
python3 vectors/presence/_tools/generate.py    # regenerate
python3 vectors/presence/_tools/verify.py      # validate
```

`verify.py` performs the following checks per vector:

1. CDDL-shape check on the decoded `presence-signal` (mandate-id
   tstr, signal-type in the closed enum, produced-at as CBOR tag-0,
   nonce as 16-byte `bstr`, signature bundle complete).
2. JSON ↔ CBOR round-trip equivalence (byte-identical canonical
   CBOR after materialising the JSON markers).
3. Outer Ed25519 signature verification, branching on the tamper
   category:
   - `fresh` / `stale` → outer signature **must** verify;
     attestation **must** verify.
   - `bad-signature`   → outer signature **must not** verify.
   - `bad-attestation` → outer signature **must** verify (it is
     re-signed after the attestation tamper); attestation **must
     not** verify.
   - `replay`          → outer signature **must** verify; nonce
     matches `expected.replay_of.nonce`.
4. Freshness window: re-derives `(now − produced_at)` and compares it
   to `expected.freshness_window.age_ms` (1 ms tolerance) plus the
   `within_budget` boolean against the §7.1 max-staleness budget.
5. SHA-256 digests of `signal.{cbor,json}` against
   `expected.digests.*`.

## Encoding & signing rules

Every vector adheres to design.md §5.1 / §6.3:

- The signing input for the outer signature is the canonical CBOR
  encoding of the unsigned envelope (`canonicalCBOR(presence-signal
  − signature)`). This is identical regardless of the wire encoding
  chosen, so JSON and CBOR vectors carry the same outer signature.
- The signing input for the device-attestation block is its `payload`
  byte string (matching the convention used by the BOOTSTRAP vectors
  under `vectors/bootstrap/_tools/generate.py`).
- All bytes are 16-byte nonces, derived deterministically from the
  master seed `FAYING_VECTOR_SEED`; replay vectors set the nonce
  equal to the value recorded in `expected.replay_of.nonce` so the
  seen-set hit is reproducible.

## device_attestation is a stub

design.md §3.3 specifies the full Attestation Chain (HP → MS → IF →
derived IF) using TPM quote / WebAuthn AAGUID / platform keystore
formats. **For PRESENCE vectors we emit a self-signed Ed25519
attestation stub** so the wire form decodes against the CDDL
`attestation` rule but no real device-root-of-trust is required:

```jsonc
{
  "format":  "self-signed",
  "payload": "<presence-device-attestation:<vector-name>>",
  "signer":  "presence-device:<vector-name>",
  "signature": { "alg": "Ed25519", "pubkey": …, "sig": … }
}
```

This is **not** representative of a production attestation. When the
full chain lands (tracked alongside §3.3 / `vectors/bootstrap/`):

1. Replace `make_device_attestation_stub` in `_tools/generate.py`
   with a builder that emits real TPM-quote / WebAuthn formats.
2. Re-run `_tools/generate.py`. Digests in `index.json` will change;
   that change is the migration signal.

The CDDL grammar already accepts the four `attestation.format`
values (`"webauthn"`, `"tpm-quote"`, `"platform-keystore"`,
`"self-signed"`), so no schema change is needed.

## Determinism

All vectors are reproducible. `_tools/generate.py` derives every
key, nonce and synthetic payload byte from a fixed master seed
(`FAYING_VECTOR_SEED`). `index.json` records the SHA-256 of that
seed under `deterministic_seed_sha256` so reviewers can detect
accidental seed drift. The per-vector `digests.signal_cbor_sha256`
and `digests.signal_json_sha256` are also recorded in
`expected.json` and checked by `_tools/verify.py`.

A common evaluation anchor `evaluated_at = 2026-03-15T12:00:00Z` is
shared across every vector; freshness windows are computed against
this instant so reviewers can verify `(now − produced_at) ≤
max_staleness_ms` by inspection.

## Replay vectors — using `expected.replay_of`

Replay vectors are byte-different from any other vector in this
directory (each has its own envelope), but their `(mandate-id,
nonce)` tuple equals the value recorded in `expected.replay_of`. To
simulate a replay reject:

1. Seed the verifier's seen-set with the recorded
   `(mandate-id, nonce)` tuple at `produced_at = expected.replay_of.produced_at`.
2. Submit the replay vector. The verifier MUST emit
   `verdict = replay` / `1009 E_REPLAY` even though the signature
   and freshness window are otherwise valid.

`expected.nonce_b64u` always equals `expected.replay_of.nonce` for
replay vectors so the equality is checkable without decoding the
envelope.

## Requirements traceability

These vectors validate the following acceptance criteria (see
[`requirements.md`](../../.kiro/specs/faying-auth-protocol/requirements.md)):

| Requirement | Acceptance criterion verified                                                                          |
| ----------- | ------------------------------------------------------------------------------------------------------ |
| 5.1         | All 15 vectors carry `produced_at`, 16-byte nonce, signed envelope and device-attestation; stale vectors confirm `produced_at + freshness_window < now ⇒ E_PRESENCE_STALE`. |
| 5.2         | Stale vectors at G1/G2/G4 expose the on-loss tightening path (`face-continuous → degrade`, heartbeat → suspend). |
| 9.1         | Replay vectors reuse a 16-byte random nonce → `1009 E_REPLAY`; bad-signature / bad-attestation vectors trigger `1007 E_ATTESTATION_INVALID`. |
| 10.1        | Each vector ships matching CBOR (primary) and JSON (debug fallback) encodings, byte-equivalent under canonical CBOR. |
| 10.3        | The 5 × 3 matrix covers the §3.2 signal-strength table and §7.1 grade-staleness budgets, and is shaped for cross-implementation conformance. |

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
