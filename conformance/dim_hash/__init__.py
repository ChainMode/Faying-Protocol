"""Faying Protocol/1.0 — Conformance: hash-algorithm dimension.

Implements task 5.4 of ``docs/en/specification/2025-10-25/README.md``:
exercise the two protocol-supported hash algorithms (``SHA-256`` and
``BLAKE3``) inside the signing-input expression mandated by
design.md §6.3:

    signing-input = H( Deterministic-CBOR(Envelope_without_signature) )

The acceptance criteria of task 5.4 are:

  * **2/2 哈希跑通**: every vector under ``vectors/`` can be re-hashed
    with each of the two algorithms; the digest length and content are
    consistent with the algorithm's specification (NIST FIPS 180-4 for
    SHA-256, the BLAKE3 specification for BLAKE3).

  * **签名输入构造与 §6.3 完全一致**: the *bytes that go into the hash*
    — i.e. ``Deterministic-CBOR(envelope_without_signature)`` — are
    identical regardless of which hash algorithm wraps them. The hash
    function is therefore a pure post-processor; the *signing input*
    is hash-algorithm-agnostic. This is the executable form of
    Property P16.1 (signature inclusion of envelope fields) and of the
    "identical signing input across encodings" claim in
    Requirement 10.2.

This package is **stdlib + ``cbor2`` + the optional ``blake3`` PyPI
package** only and does not depend on the ``pbt/`` virtualenv. If
``blake3`` is missing the conformance suite raises with a clear
remediation message rather than silently skipping the BLAKE3 path —
"2/2 hashes" is a hard acceptance gate.

Validates: Requirements 8.1, 10.2, 10.3 (task 5.4 acceptance).
"""

from .algorithms import (
    HASH_SHA256,
    HASH_BLAKE3,
    SUPPORTED_HASHES,
    HASH_DIGEST_SIZE_BYTES,
    compute_hash,
    normalize_hash,
)
from .negotiation import (
    MANDATORY_HASH_BASELINE,
    NEGOTIATION_ORDER,
    HashNegotiationError,
    negotiate_hash,
)
from .signing_input import (
    HashCheckResult,
    iter_vector_dirs,
    load_envelope,
    compute_signing_input,
    hash_vector_across_algorithms,
)

__all__ = [
    "HASH_SHA256",
    "HASH_BLAKE3",
    "SUPPORTED_HASHES",
    "HASH_DIGEST_SIZE_BYTES",
    "compute_hash",
    "normalize_hash",
    "MANDATORY_HASH_BASELINE",
    "NEGOTIATION_ORDER",
    "HashNegotiationError",
    "negotiate_hash",
    "HashCheckResult",
    "iter_vector_dirs",
    "load_envelope",
    "compute_signing_input",
    "hash_vector_across_algorithms",
]
