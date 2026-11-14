"""Faying Protocol/1.0 — Conformance encoding-dimension driver (task 5.2).

This package implements the encoding axis of the §TS.4 互操作测试矩阵:

    encoding ∈ {cbor, json}

For every test vector under ``vectors/`` that ships in **both** CBOR and JSON
wire form (per task 3.x), we re-prove the four claims of Requirement 10.1 /
10.2 / 10.3:

  1. The two encodings deserialize to **semantically equal** logical objects
     once the JSON-side binary markers (``$bytes`` / ``$b64`` / ``$b64u`` /
     ``$tag``) are lifted to native CBOR types (bytes / ``CBORTag``).
  2. ``Deterministic-CBOR(envelope_without_signature)`` is **bit-for-bit
     identical** whether derived from the CBOR file or from the JSON file
     (after lift-to-CBOR-shape).
  3. ``SHA-256(signature_input)`` is identical across encodings — Requirement
     10.2.4.
  4. Signature verification (where the vector ships a real Ed25519 signature)
     yields the **same outcome** on both encodings — Requirement 10.1.3.

The driver also asserts that the JSON wire form's HTTP ``Content-Type`` is
one of the accepted forms (the modern ``application/faying-protocol+json``
defined in design.md §5.1, and the legacy ``application/fap+json`` referenced
by tasks 3.7 / 5.2 which we still accept for compatibility — the protocol body
explicitly retired the ``fap`` short form but the conformance suite must
recognise it as a valid alias because existing vector metadata still emits
it).

Reference / Not Normative — `vectors/` and `schemas/` remain authoritative.
"""

from .normalize import (
    json_to_cbor_shape,
    canonical_cbor,
    strip_signature,
    detect_binary_marker,
)
from .vectors_index import (
    EncodingPair,
    discover_pairs,
)
from .driver import (
    EncodingCheckResult,
    run_pair,
    run_all,
    ACCEPTED_JSON_CONTENT_TYPES,
)

__all__ = [
    "json_to_cbor_shape",
    "canonical_cbor",
    "strip_signature",
    "detect_binary_marker",
    "EncodingPair",
    "discover_pairs",
    "EncodingCheckResult",
    "run_pair",
    "run_all",
    "ACCEPTED_JSON_CONTENT_TYPES",
]
