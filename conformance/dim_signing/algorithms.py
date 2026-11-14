"""Algorithm-agility primitives for the signing-dimension conformance suite.

The protocol's normative algorithm enum (CDDL ``signature-bundle.alg``) is::

    "Ed25519" / "ES256" / "ML-DSA-65"

This module provides a single uniform API (``sign`` / ``verify`` /
``generate_keypair``) keyed by the wire-format algorithm string, so the
dim_signing conformance driver can iterate over the three values without
branching on each call site.

* ``Ed25519`` — RFC 8032 EdDSA over Curve25519, deterministic by design.
* ``ES256``   — NIST P-256 ECDSA with SHA-256, signatures emitted as
  IEEE-P1363 fixed-length ``r || s`` (64 bytes); this is the layout the
  ``vectors/bootstrap/_tools/generate.py`` toolchain uses, so vectors and
  conformance signatures are byte-compatible.
* ``ML-DSA-65`` — FIPS 204 module-lattice-based DSA. A vetted pure-Python
  implementation is not available at vector-authoring time, so this
  module produces a *deterministic placeholder* whose format matches the
  one in ``vectors/bootstrap/_tools/generate.py``. The placeholder is
  sufficient to exercise the algorithm-suite negotiation logic (which is
  the actual subject of Requirement 8.1 and acceptance criterion of
  task 5.3); it is **NOT** a cryptographic primitive and MUST NOT be
  shipped in a reference implementation. See ``README.md`` for the
  rationale.

The module is intentionally tolerant of the alternate spelling
``ECDSA-P256`` (which the task description uses) by aliasing it to
``ES256``. The ``signature-bundle.alg`` enum on the wire remains
``ES256``.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from typing import Any, Optional, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

# ---------------------------------------------------------------------------
# Algorithm identifiers (wire-format strings, case-sensitive).
# ---------------------------------------------------------------------------
ALG_ED25519 = "Ed25519"
ALG_ES256 = "ES256"
ALG_ML_DSA_65 = "ML-DSA-65"

# Stable iteration order; also accepted by negotiation.NEGOTIATION_ORDER.
SUPPORTED_ALGORITHMS: Tuple[str, ...] = (ALG_ED25519, ALG_ES256, ALG_ML_DSA_65)

# Aliases the task spec uses informally.
_ALIASES = {
    "ECDSA-P256": ALG_ES256,
    "ecdsa-p256": ALG_ES256,
    "es256": ALG_ES256,
    "ed25519": ALG_ED25519,
    "ml-dsa-65": ALG_ML_DSA_65,
}


def normalize_alg(alg: str) -> str:
    """Map informal names (``ECDSA-P256``, lowercase) to the wire enum."""

    if alg in SUPPORTED_ALGORITHMS:
        return alg
    if alg in _ALIASES:
        return _ALIASES[alg]
    raise ValueError(
        f"unsupported signing algorithm {alg!r}; expected one of "
        f"{SUPPORTED_ALGORITHMS} (aliases: {sorted(_ALIASES)})"
    )


# ---------------------------------------------------------------------------
# Key handle.
# ---------------------------------------------------------------------------
@dataclass
class KeyPair:
    """Algorithm-agnostic key handle.

    Attributes:
        alg: One of :data:`SUPPORTED_ALGORITHMS`.
        private: Library-specific private key handle. ``None`` for
            ML-DSA-65 (placeholder).
        public_bytes: Algorithm-specific public key bytes (raw 32 bytes
            for Ed25519; uncompressed SEC1 ``0x04 || X || Y`` for ES256;
            deterministic placeholder for ML-DSA-65).
        private_seed: Seed bytes used to derive the keypair (for
            reproducibility / placeholder verification).
    """

    alg: str
    private: Any
    public_bytes: bytes
    private_seed: bytes

    def public_key_bytes(self) -> bytes:
        return self.public_bytes


# ---------------------------------------------------------------------------
# Deterministic seed expansion (mirrors vectors/bootstrap/_tools/generate.py).
# ---------------------------------------------------------------------------
def _expand_seed(seed: bytes, label: str, length: int) -> bytes:
    out = b""
    counter = 0
    while len(out) < length:
        h = hashlib.sha256()
        h.update(seed)
        h.update(label.encode("utf-8"))
        h.update(counter.to_bytes(4, "big"))
        out += h.digest()
        counter += 1
    return out[:length]


# ---------------------------------------------------------------------------
# Key generation.
# ---------------------------------------------------------------------------
# NIST P-256 group order n.
_P256_ORDER = (
    0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
)


def _make_ed25519(seed: bytes) -> KeyPair:
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return KeyPair(alg=ALG_ED25519, private=sk, public_bytes=pk, private_seed=seed)


def _make_p256(seed: bytes) -> KeyPair:
    scalar = (int.from_bytes(seed, "big") % (_P256_ORDER - 1)) + 1
    sk = ec.derive_private_key(scalar, ec.SECP256R1())
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return KeyPair(alg=ALG_ES256, private=sk, public_bytes=pk, private_seed=seed)


def _make_ml_dsa_65(seed: bytes) -> KeyPair:
    # Deterministic placeholder: see module docstring for the rationale.
    public = b"test-only-ml-dsa-65-pubkey-" + _expand_seed(seed, "pubkey", 32)
    return KeyPair(
        alg=ALG_ML_DSA_65, private=None, public_bytes=public, private_seed=seed
    )


def generate_keypair(alg: str, *, seed: Optional[bytes] = None) -> KeyPair:
    """Deterministically generate a keypair for the given algorithm.

    Args:
        alg: One of :data:`SUPPORTED_ALGORITHMS` (or alias).
        seed: 32-byte seed material; if omitted, ``secrets.token_bytes(32)``
            is used so the call is non-deterministic by default.
    """

    alg = normalize_alg(alg)
    if seed is None:
        seed = secrets.token_bytes(32)
    if len(seed) != 32:
        raise ValueError("seed must be exactly 32 bytes")

    if alg == ALG_ED25519:
        return _make_ed25519(_expand_seed(seed, f"{alg}:sk", 32))
    if alg == ALG_ES256:
        return _make_p256(_expand_seed(seed, f"{alg}:sk", 32))
    if alg == ALG_ML_DSA_65:
        return _make_ml_dsa_65(_expand_seed(seed, f"{alg}:sk", 32))
    raise AssertionError(f"unhandled alg {alg!r}")


# ---------------------------------------------------------------------------
# Signing / verification.
# ---------------------------------------------------------------------------
def sign(kp: KeyPair, message: bytes, *, label: str = "conformance") -> bytes:
    """Produce a signature over ``message`` using ``kp``.

    The ``label`` argument only affects the ML-DSA-65 placeholder format
    (where it ends up embedded so the signatures are deterministic per
    label); it is ignored for Ed25519 and ES256.
    """

    alg = normalize_alg(kp.alg)
    if alg == ALG_ED25519:
        return kp.private.sign(message)
    if alg == ALG_ES256:
        der = kp.private.sign(message, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")
    if alg == ALG_ML_DSA_65:
        digest = hashlib.sha256(message).digest()
        prefix = b"test-only-ml-dsa-65-sig-"
        # Use the first 8 bytes of the label so the format matches the
        # vector generator exactly.
        label_bytes = label.encode("utf-8")[:8].ljust(8, b"\x00")
        return prefix + label_bytes + digest
    raise AssertionError(f"unhandled alg {alg!r}")


def verify(kp: KeyPair, message: bytes, signature: bytes) -> bool:
    """Verify a signature produced by :func:`sign`.

    Returns ``True`` on success, ``False`` on cryptographic failure or
    a structural mismatch. Does **not** raise on mismatch, mirroring the
    conformance driver's branch-free style.
    """

    alg = normalize_alg(kp.alg)
    if alg == ALG_ED25519:
        try:
            kp.private.public_key().verify(signature, message)
            return True
        except InvalidSignature:
            return False
    if alg == ALG_ES256:
        if len(signature) != 64:
            return False
        r = int.from_bytes(signature[:32], "big")
        s = int.from_bytes(signature[32:], "big")
        if r == 0 or s == 0 or r >= _P256_ORDER or s >= _P256_ORDER:
            return False
        try:
            der = encode_dss_signature(r, s)
            # cryptography's EC verify signature is
            # ``verify(signature, data, signature_algorithm)`` — note the
            # message comes second.
            kp.private.public_key().verify(
                der, message, ec.ECDSA(hashes.SHA256())
            )
            return True
        except InvalidSignature:
            return False
    if alg == ALG_ML_DSA_65:
        # Placeholder format check (see module docstring).
        prefix = b"test-only-ml-dsa-65-sig-"
        if not signature.startswith(prefix):
            return False
        if len(signature) != len(prefix) + 8 + 32:
            return False
        embedded_digest = signature[-32:]
        return embedded_digest == hashlib.sha256(message).digest()
    raise AssertionError(f"unhandled alg {alg!r}")
