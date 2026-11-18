# `conformance/dim_encoding/` — Encoding-Dimension Conformance Driver (task 5.2)

> **Normative anchors** — Requirement [10.1](../../docs/en/specification/2025-10-25/README.md) / [10.2](../../docs/en/specification/2025-10-25/README.md) / [10.3](../../docs/en/specification/2025-10-25/README.md); design.md §5.1, §6.3 S2; tasks.md §5.2.

This package is the **encoding axis** (`{cbor, json}`) of the §TS.4 互操作测试矩阵 mandated by Requirement 10.3. It exercises every CBOR/JSON pair shipped by task 3.x and proves the encoding-equivalence claims of design.md §5.1 / §6.3 against the on-disk vector corpus.

## 1. Invariants

For every pair the driver enforces seven invariants. Each is a direct lift of one EARS clause (codes appear in the driver's per-finding `code` field):

| Code | Invariant | EARS clause |
| --- | --- | --- |
| `E1.*` | CBOR + JSON both decode (or one of them, with INFO) | R10.1.1 / R10.1.3 |
| `E2.semantic` | Field semantics agree after lifting JSON binary / tag-0 markers | R10.1.3 |
| `E3.sig_input.diff` | `Det-CBOR(envelope − signature)` is bit-for-bit identical across encodings | R10.2.1, R10.2.4 |
| `E4.hash.expected` | `SHA-256(signature_input)` matches `expected.json` | R10.2.4 |
| `E5.verify.diverge` | Ed25519 verification yields the same outcome on both encodings | R10.1.3 |
| `E6.content_type` | JSON Content-Type ∈ accepted set | R10.1.2 |
| `E7.cbor.noncanonical` | CBOR file canonicality (advisory) | R10.2.1 |

Codes in the `INFO` level (`E0.one_sided`, `E5.skipped`, `E5.invalid`, `E6.content_type.legacy`, `E7.*`) surface advisory observations that do not gate the run.

## 2. Content-Type policy

design.md §5.1 and Requirement 10.1.2 define the **normative** JSON media type:

```
application/faying-protocol+json
```

The conformance driver also recognises the **legacy alias** `application/fap+json` because tasks 3.7 / 5.2 and several `vectors/*/index.json` files still emit it for backward compatibility. The protocol body itself retired the `fap` short form — see [`docs/zh-CN/specification/2025-10-25/01-概述.md` §1.1](../../docs/zh-CN/specification/2025-10-25/01-概述.md).

```python
ACCEPTED_JSON_CONTENT_TYPES = (
    "application/faying-protocol+json",
    "application/fap+json",   # legacy alias
)
NORMATIVE_JSON_CONTENT_TYPE = "application/faying-protocol+json"
```

A pair that declares the legacy alias passes I-E-6 but yields an `INFO E6.content_type.legacy` finding so the corpus drift is loud.

## 3. JSON wire conventions

The corpus uses four conventions for binary / timestamp fields, all valid per design.md §5.1. The driver's [`normalize.py`](./normalize.py) collapses them to a single CBOR-native shape:

| Convention | Used by | Example |
| --- | --- | --- |
| `{"$bytes": "<base64url>"}` | bootstrap, delegate, grade-switch, revoke, presence, encoding-equivalence (in `binary_field_paths`-keyed mode) | `{"$bytes": "AAECAwQF…"}` |
| `{"$bytes": "<hex>"}` | endorsement | `{"$bytes": "776562617574686e…"}` |
| `{"$b64": "<std-b64>"}` | faying-request | `{"$b64": "bYP4drcJ24aq…"}` |
| `{"$b64u": "<base64url>"}` | disclosure | `{"$b64u": "AAAAAAAAAAAA…"}` |
| `{"$tag": 0, "$value": "<rfc3339>"}` | bootstrap, delegate, grade-switch, revoke, presence | tag-0 timestamp |
| `{"$tag": 0, "value": "<rfc3339>"}` | endorsement | tag-0 timestamp variant |
| Bare RFC 3339 string | encoding-equivalence, disclosure, faying-request, errors | `"2025-12-17T12:00:00Z"` |
| Bare hex string in `*_hex` keys | errors | `"pubkey_hex": "11…11"` |

The `$bytes` convention's hex-vs-b64u ambiguity is resolved by character-set sniffing inside the marker decoder — see [`normalize._decode_bytes_marker`](./normalize.py).

## 4. Sub-second timestamp handling

cbor2 unconditionally maps tag 0 to `datetime`, which round-trips with full microsecond precision. A vector that carries `"…11:59:57.500Z"` decodes to `datetime(microsecond=500000)` and re-encodes as `"…11:59:57.500000Z"`, breaking byte-level canonicality. The driver works around this in [`driver._datetimes_to_tag0`](./driver.py): every decoded `datetime` is converted back into `CBORTag(0, str)` whose string format mirrors what the in-tree generators emit:

* whole seconds → `…HH:MM:SSZ`
* millisecond precision → `…HH:MM:SS.fffZ`
* microsecond precision → `…HH:MM:SS.ffffffZ`

The signature-input comparison (I-E-3) is performed on the normalized form, so canonicality holds regardless of sub-second precision.

## 5. Running

```bash
# Run via the conformance super-driver (recommended):
python conformance/runner.py --run --dim encoding

# Or run the dimension driver directly:
python -m conformance.dim_encoding.driver --format text -v
python -m conformance.dim_encoding.driver --format json

# Or as pytest tests:
python -m pytest conformance/dim_encoding/tests -q
```

Exit codes:

* `0` — every pair passed I-E-1 .. I-E-6 (I-E-7 is advisory).
* `1` — at least one pair surfaced a `FAIL` finding.
* `2` — CLI mis-use (mutually exclusive flags, unknown `--dim`).
* `4` — unable to import a wired dimension driver.

## 6. Reference / Not Normative

This package ships under [`conformance/`](../README.md), which the spec body declares **non-normative**: the authoritative artefacts are [`vectors/`](../../vectors/) and [`schemas/`](../../schemas/). `dim_encoding/` consumes those artefacts; it does not redefine protocol semantics.
