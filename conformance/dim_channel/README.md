# Conformance Dimension — Channel (TLS-only / mTLS)

> **Task 5.5 deliverable.** Implements the RFC 9266 TLS Exporter
> Channel Binding contract from
> [Requirement 9.2.3](../../docs/en/specification/2025-10-25/README.md)
> and [design.md §9.3](../../docs/en/specification/2025-10-25/README.md).

## What this dimension covers

| Dimension axis | Values |
| --- | --- |
| `channel` | `tls-only`, `mtls` |
| `message-type` (per task 5.5 内容) | BOOTSTRAP, DELEGATE, REVOKE |
| `binding-shape` (per task 5.5 验收) | present-correct, present-tampered, absent |

The cartesian product is `2 × 3 × 3 = 18` scenarios. Every scenario is
executed against an RP-side validator that follows the §9.3 truth table:

| `mode`     | binding present  | matches exporter | result                 |
| ---------- | ---------------- | ---------------- | ---------------------- |
| `tls-only` | absent           | n/a              | accept (not required)  |
| `tls-only` | present          | matches          | reject `E_PROTOCOL`    |
| `tls-only` | present          | mismatches       | reject `E_PROTOCOL`    |
| `mtls`     | absent           | n/a              | reject `E_ATTESTATION_INVALID` |
| `mtls`     | present          | matches          | accept                 |
| `mtls`     | present          | mismatches       | reject `E_ATTESTATION_INVALID` |

The two task-5.5 verbatim acceptance gates are encoded as their own tests
in [`test_dim_channel.py`](./test_dim_channel.py):

* `test_acceptance_gate_mtls_missing_binding_rejected` — mTLS 缺 Channel
  Binding 时被拒（错误码 1007 `E_ATTESTATION_INVALID`）.
* `test_acceptance_gate_tls_only_without_binding_accepted` — TLS-only 不
  要求 Channel Binding 仍可通过.

## Files

| File | Purpose |
| --- | --- |
| [`tls_context.py`](./tls_context.py) | Synthetic TLS context with deterministic RFC 9266 exporter (HKDF-SHA256). Stdlib-only. |
| [`rp_validator.py`](./rp_validator.py) | RP-side `validate_channel_binding(envelope, ctx)` implementing the §9.3 truth table. |
| [`scenarios.py`](./scenarios.py) | Builds the `(message_type × tls_mode × binding_shape)` matrix on top of the task 3.x BOOTSTRAP / DELEGATE / REVOKE vectors. |
| [`driver.py`](./driver.py) | CLI entry point. `python -m conformance.dim_channel.driver`. |
| [`test_dim_channel.py`](./test_dim_channel.py) | Pytest suite. The actual conformance gate. |

## Running

From the repository root:

```bash
# CLI report (text)
python -m conformance.dim_channel.driver

# CLI report (JSON, for CI)
python -m conformance.dim_channel.driver --format json

# Pytest gate
pytest conformance/dim_channel/
```

The driver exits `0` only when every scenario matches its expected
`(accepted, error_code)` tuple; pytest mirrors the same gate via the
parametrised `test_scenario_matches_expectation`.

## Design notes

* **No real TLS handshake.** The exporter is derived deterministically from
  HKDF-SHA256 keyed by `connection_id || mode`. This keeps the conformance
  gate hermetic (no network, no certificates) while preserving the two
  properties RFC 9266 actually requires of an exporter: collision
  resistance across distinct connections, and stability across the same
  connection. Full network-level mTLS is the responsibility of `task 6.2
  conformance/attacks/test_hijack.py`.
* **Anchor vectors.** Each message type re-uses one canonical positive
  vector from `vectors/`:
  * BOOTSTRAP → `vectors/bootstrap/pos-cbor-ed25519`
  * DELEGATE  → `vectors/delegate/pos-depth-1`
  * REVOKE    → `vectors/revoke/reason-human-initiated`
  We overlay the `channel_binding` field per the scenario's binding shape.
  Updating these anchors only requires changing the `_ANCHOR_VECTORS`
  table in `scenarios.py`.
* **Field name.** The wire location of the binding is `channel_binding`,
  carried at envelope top-level *or* inside `claims`; both are accepted by
  the validator. The CDDL schema (`schemas/fap-1.0.cddl`) treats this
  field as transport-layer metadata and does not reify it; this matches
  design.md §9.3 which describes channel binding as an additional input
  to the signature, not a new envelope field.
* **Stdlib-only.** This dimension does not import `cbor2` or
  `cryptography`, so it runs in any Python ≥ 3.10 environment without
  bootstrapping `pbt/`.
