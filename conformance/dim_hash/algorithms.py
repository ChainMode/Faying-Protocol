"""Hash-agility primitives for the hash-dimension conformance suite.

The protocol's normative hash enum is declared in design.md §6.1 (the
algorithm-suite negotiation table). The wire format does **not** reify the
hash choice as an envelope field — design.md §6.3 fixes the signing input
as ``H( Deterministic-CBOR(Envelope_without_signature) )`` with ``H``
selected by the BOOTSTRAP-time negotiation (Requirement 8.1). The two
hash names task 5.4 covers are::

    "SHA-256" / "BLAKE3"

…with ``SHA3-256`` reserved as a PQC协商位 (design.md §6.1) but **not**
required by task 5.4.

This module provides a single uniform API (``compute_hash``) keyed by the
wire-format hash name, so the dim_hash conformance driver and tests can
iterate over the two values without branching on each call site.

* ``SHA-256`` — NIST FIPS 180-4. Provided by the standard library
  (``hashlib.sha256``); always available.

* ``BLAKE3`` — the BLAKE3 specification (Aumasson et al., 2020). Provided
  by the third-party ``blake3`` PyPI package, which wraps the official
  Rust reference implementation. The Python standard library does not
  ship a BLAKE3 implementation as of Python 3.13, so we depend on the
  ``blake3`` package (also used by the protocol's reference impls in
  task 5.6).

  If ``blake3`` is unavailable, :func:`compute_hash` raises an
  :class:`ImportError`-derived :class:`HashUnavailableError` with a
  clear remediation message. Task 5.4's acceptance criterion is
  "2/2 哈希跑通", so silent skip of the BLAKE3 path would violate the
  gate; we surface the missing dependency explicitly.

Both algorithms are used as drop-in replacements inside the §6.3
signing-input expression::

    signing-input(envelope, h) = h( Deterministic-CBOR(envelope_without_sig) )

Crucially, *only the wrapper changes*: the byte string fed to the
hash function is independent of which hash algorithm is in use. This
is the property the conformance driver verifies most carefully (see
:mod:`conformance.dim_hash.signing_input`).
"""

from __future__ import annotations

import hashlib
from typing import Callable, Dict, Tuple

# ---------------------------------------------------------------------------
# Algorithm identifiers (wire-format strings, case-sensitive).
# ---------------------------------------------------------------------------
HASH_SHA256 = "SHA-256"
HASH_BLAKE3 = "BLAKE3"

# Stable iteration order; also accepted by negotiation.NEGOTIATION_ORDER.
SUPPORTED_HASHES: Tuple[str, ...] = (HASH_SHA256, HASH_BLAKE3)

# Spec-mandated digest sizes, in bytes. Both algorithms emit 32-byte
# digests by default; a different size is a protocol violation.
HASH_DIGEST_SIZE_BYTES: Dict[str, int] = {
    HASH_SHA256: 32,  # NIST FIPS 180-4
    HASH_BLAKE3: 32,  # BLAKE3 default output length (the spec allows
                       # arbitrary-length output, but FAP/1.0 fixes it to 32).
}

# Aliases the task spec / RFCs sometimes use.
_ALIASES = {
    "sha-256": HASH_SHA256,
    "sha256": HASH_SHA256,
    "SHA256": HASH_SHA256,
    "blake3": HASH_BLAKE3,
    "Blake3": HASH_BLAKE3,
}


class HashUnavailableError(ImportError):
    """Raised when a supported hash algorithm has no implementation.

    The conformance gate of task 5.4 requires "2/2 哈希跑通". If a
    required hash cannot be computed (e.g. because the ``blake3``
    package is not installed), we raise this so the failure is loud
    rather than silently dropping the BLAKE3 column from the matrix.
    """


def normalize_hash(name: str) -> str:
    """Map informal names (lowercase, no hyphen) to the wire enum.

    Raises ``ValueError`` for any name outside the protocol's enum.
    """

    if name in SUPPORTED_HASHES:
        return name
    if name in _ALIASES:
        return _ALIASES[name]
    raise ValueError(
        f"unsupported hash algorithm {name!r}; expected one of "
        f"{SUPPORTED_HASHES} (aliases: {sorted(_ALIASES)})"
    )


# ---------------------------------------------------------------------------
# Lazy BLAKE3 import.
# ---------------------------------------------------------------------------
def _blake3_digest(data: bytes) -> bytes:
    try:
        import blake3 as _blake3  # noqa: WPS433 — lazy import is intentional
    except ImportError as exc:  # pragma: no cover - exercised only when
        # the optional dependency is missing.
        raise HashUnavailableError(
            "BLAKE3 is required by the FAP/1.0 hash-dimension conformance "
            "suite (task 5.4) but the 'blake3' PyPI package is not "
            "installed. Install it with `pip install blake3` (the package "
            "wraps the BLAKE3 team's official Rust implementation). "
            "Skipping BLAKE3 silently would violate task 5.4's '2/2 "
            "hashes' acceptance gate."
        ) from exc
    return _blake3.blake3(data).digest()


def _sha256_digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


# Dispatch table; each entry consumes the canonical signing-input bytes
# and returns the digest. The signature is identical across algorithms,
# which is the structural guarantee task 5.4 verifies at runtime.
_DISPATCH: Dict[str, Callable[[bytes], bytes]] = {
    HASH_SHA256: _sha256_digest,
    HASH_BLAKE3: _blake3_digest,
}


def compute_hash(algorithm: str, data: bytes) -> bytes:
    """Return the digest of ``data`` under ``algorithm``.

    Both supported algorithms emit 32-byte digests; the result is
    cross-checked against :data:`HASH_DIGEST_SIZE_BYTES` to catch
    misbehaving back-ends (a non-32-byte BLAKE3 output, for instance,
    would mean the optional package is producing an XOF-style output
    rather than the FAP/1.0-fixed 32-byte form).

    Raises:
        HashUnavailableError: if the algorithm has no implementation
            available in this environment.
        ValueError: if ``algorithm`` is not in
            :data:`SUPPORTED_HASHES`.
        AssertionError: if the back-end returns a non-conformant
            digest length (defensive invariant; should never fire on
            a conformant implementation).
    """

    alg = normalize_hash(algorithm)
    digest = _DISPATCH[alg](data)
    expected_len = HASH_DIGEST_SIZE_BYTES[alg]
    if len(digest) != expected_len:
        raise AssertionError(
            f"{alg} back-end returned {len(digest)}-byte digest; "
            f"FAP/1.0 fixes {alg} output to {expected_len} bytes "
            "(see design.md §6.1 algorithm-suite table)"
        )
    return digest
