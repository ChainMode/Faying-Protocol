"""Faying Protocol/1.0 — Conformance: signing-algorithm dimension.

Implements task 5.3 of ``docs/en/specification/2025-10-25/README.md``:
re-sign every vector with each of the three protocol-supported algorithms
(``Ed25519`` / ``ECDSA-P256`` / ``ML-DSA-65``) and verify that the
algorithm-suite negotiation rule (Requirement 8.1) holds:

  * Both parties declare the algorithms they support.
  * The strongest mutually-supported algorithm is chosen.
  * If the intersection is empty → ``E_PROTOCOL``.
  * ``ML-DSA-65`` is OPTIONAL (Requirement 8.2): an implementation that
    does not advertise it MUST still succeed at BOOTSTRAP whenever the
    classical pair ``{Ed25519, ECDSA-P256}`` is mutually supported.

This package is **stdlib + ``cbor2`` + ``cryptography``** only and does
not depend on the ``pbt/`` virtualenv. Real ML-DSA-65 (FIPS 204) is not
available in pure-Python toolchains at vector-authoring time, so the
ML-DSA-65 path uses the same deterministic placeholder format as
``vectors/bootstrap/_tools/generate.py``; this is documented in
``README.md`` and is only used to exercise the *negotiation* logic, not
to claim cryptographic strength.
"""

from .algorithms import (
    ALG_ED25519,
    ALG_ES256,
    ALG_ML_DSA_65,
    SUPPORTED_ALGORITHMS,
    KeyPair,
    generate_keypair,
    sign,
    verify,
)
from .negotiation import (
    NEGOTIATION_ORDER,
    NegotiationError,
    negotiate,
)

__all__ = [
    "ALG_ED25519",
    "ALG_ES256",
    "ALG_ML_DSA_65",
    "SUPPORTED_ALGORITHMS",
    "KeyPair",
    "NEGOTIATION_ORDER",
    "NegotiationError",
    "generate_keypair",
    "negotiate",
    "sign",
    "verify",
]
