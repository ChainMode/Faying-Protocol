"""Hash-suite negotiation rule for Faying Protocol/1.0.

This module is the executable encoding of the *hash* half of
Requirement 8.1 (``docs/en/specification/2025-10-25/README.md``):

    1. THE Faying_Protocol_System SHALL 在 BOOTSTRAP 时让客户端与服务端
       各自声明所支持的签名、哈希、KDF、对称、信道层算法套件。
    2. THE Faying_Protocol_System SHALL 选择双方共同支持的最强算法作为
       `SignatureBundle.alg`、`hash`、... 的最终值。
    4. IF 双方在 BOOTSTRAP 时不存在任一共同支持的签名算法或哈希算法，
       THEN THE Mandate_Service SHALL 以 `E_PROTOCOL` 拒绝该次 BOOTSTRAP。

Strength ordering
-----------------
The "strongest" rule (clause 2) for hashes is interpreted per
design.md §6.1:

    PQC > BLAKE3 > SHA-256

…but task 5.4 only covers ``SHA-256`` and ``BLAKE3`` (PQC ``SHA3-256``
is reserved as a 协商位 only). Within that two-element set BLAKE3 is
ranked stronger because:

  * It uses a Merkle-tree internal structure resistant to length-
    extension attacks SHA-256 is vulnerable to.
  * Its 256-bit security level is at least equal to SHA-256's against
    second-preimage / collision (both are 128-bit collision security
    in practice).
  * design.md §6.1 lists it under "备选" against SHA-256's "默认", a
    convention the protocol body uses in the *signing-alg* table to
    mean "alternative with at least the same security properties";
    we apply the same convention here.

The resulting strict descending strength order is therefore::

    NEGOTIATION_ORDER = ("BLAKE3", "SHA-256")

and :func:`negotiate_hash` returns the first element of this tuple
that appears in both ``client_supports`` and ``server_supports``.

Mandatory baseline
------------------
Per Requirement 8.1 clause 3, every conformant implementation MUST
support at least the classical signing-algorithm baseline
``{Ed25519, ECDSA-P256}``. The clause does *not* explicitly mandate a
hash baseline, but design.md §6.1 marks ``SHA-256`` as the default and
the encoding-equivalence vectors (task 3.7) all hash with SHA-256, so
the conformance suite treats ``{SHA-256}`` as the de-facto mandatory
hash baseline. BLAKE3 remains REQUIRED for protocol-level conformance
(it is in the ``hash`` enum and task 5.4 demands 2/2 coverage), but a
pair where one side advertises only SHA-256 must still BOOTSTRAP.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from .algorithms import HASH_BLAKE3, HASH_SHA256, normalize_hash

# Strict descending strength order. Authoritative tie-breaker for
# Requirement 8.1 clause 2.
NEGOTIATION_ORDER: Tuple[str, ...] = (HASH_BLAKE3, HASH_SHA256)

# De-facto mandatory hash baseline (see module docstring for the
# rationale). All conformant implementations must accept SHA-256 even
# if they prefer BLAKE3.
MANDATORY_HASH_BASELINE: frozenset = frozenset({HASH_SHA256})


class HashNegotiationError(Exception):
    """Raised when no mutually-supported hash algorithm exists.

    Per Requirement 8.1 clause 4 this maps to error code 1099
    (``E_PROTOCOL``) on the wire (see design.md §5.4 / §EH.1).
    """

    error_name: str = "E_PROTOCOL"
    error_code: int = 1099


def _normalize_set(names: Iterable[str]) -> frozenset:
    """Normalise an advertised hash support set to wire-format names.

    Unknown / non-protocol hash names are dropped silently. Receiving
    an unrecognised algorithm string from the peer is *peer behaviour*,
    not an implementation bug, so it must funnel into the empty-
    intersection branch of :func:`negotiate_hash` rather than raise.
    This mirrors :mod:`conformance.dim_signing.negotiation` so the
    two negotiation flows behave consistently.
    """

    out: set = set()
    for name in names:
        try:
            out.add(normalize_hash(name))
        except ValueError:
            continue
    return frozenset(out)


def negotiate_hash(
    client_supports: Iterable[str], server_supports: Iterable[str]
) -> str:
    """Return the strongest hash algorithm in ``client ∩ server``.

    Raises:
        HashNegotiationError: if the intersection is empty
            (Requirement 8.1 clause 4 → ``E_PROTOCOL``).
    """

    client = _normalize_set(client_supports)
    server = _normalize_set(server_supports)
    intersection = client & server
    if not intersection:
        raise HashNegotiationError(
            f"E_PROTOCOL: no common hash algorithm between client "
            f"{sorted(client)} and server {sorted(server)}"
        )
    for alg in NEGOTIATION_ORDER:
        if alg in intersection:
            return alg
    # Defensive: NEGOTIATION_ORDER must list every supported algorithm.
    raise HashNegotiationError(  # pragma: no cover - guarded by the test
        # ``test_negotiation_order_covers_every_supported_hash``.
        f"E_PROTOCOL: intersection {sorted(intersection)} contains "
        f"hashes outside NEGOTIATION_ORDER {NEGOTIATION_ORDER}"
    )
