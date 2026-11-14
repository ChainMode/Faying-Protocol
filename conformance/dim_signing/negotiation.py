"""Algorithm-suite negotiation rule for Faying Protocol/1.0.

This module is the executable encoding of Requirement 8.1
(``docs/en/specification/2025-10-25/README.md``):

    1. THE Faying_Protocol_System SHALL 在 BOOTSTRAP 时让客户端与服务端
       各自声明所支持的签名 ... 算法套件。
    2. THE Faying_Protocol_System SHALL 选择双方共同支持的最强算法作为
       `SignatureBundle.alg` ... 的最终值。
    3. THE Faying_Protocol_System SHALL 至少同时支持签名算法集合
       `{Ed25519, ECDSA-P256}`。
    4. IF 双方在 BOOTSTRAP 时不存在任一共同支持的签名算法或哈希算法，
       THEN THE Mandate_Service SHALL 以 `E_PROTOCOL` 拒绝该次 BOOTSTRAP。

…in combination with Requirement 8.2 clause 3:

    WHILE PQC 套件被协议委员会标记为 `MUST` 之前，THE Faying_Protocol_System
    SHALL 将 PQC 套件实现为 `OPTIONAL`，且不得因对端不支持 PQC 而拒绝 BOOTSTRAP.

Strength ordering
-----------------
The "strongest" rule (clause 2) is interpreted per design.md §6.1:

    PQC > classical curve > none

The protocol's enum has only one PQC entry (``ML-DSA-65``) and two
classical entries (``Ed25519``, ``ES256``). design.md §6.1 marks
``Ed25519`` as the *default* and ``ES256`` as the *fallback*, which in
the negotiation order makes Ed25519 stronger than ES256 (it is more
resistant to nonce-reuse failures and has smaller signatures). The
resulting strict descending strength order is therefore::

    NEGOTIATION_ORDER = ("ML-DSA-65", "Ed25519", "ES256")

and :func:`negotiate` returns the first element of this tuple that
appears in both ``client_supports`` and ``server_supports``.
"""

from __future__ import annotations

from typing import Iterable, Tuple

from .algorithms import ALG_ED25519, ALG_ES256, ALG_ML_DSA_65, normalize_alg

# Strict descending strength order. Authoritative tie-breaker for clause 2.
NEGOTIATION_ORDER: Tuple[str, ...] = (ALG_ML_DSA_65, ALG_ED25519, ALG_ES256)

# Classical baseline mandated by clause 3 of Requirement 8.1.
MANDATORY_BASELINE: frozenset = frozenset({ALG_ED25519, ALG_ES256})


class NegotiationError(Exception):
    """Raised when no mutually-supported algorithm exists.

    This maps to error code 1099 (``E_PROTOCOL``) on the wire (see
    design.md §5.4 / §EH.1).
    """

    error_name: str = "E_PROTOCOL"
    error_code: int = 1099


def _normalize_set(algs: Iterable[str]) -> frozenset:
    """Normalise an advertised support set to wire-format names.

    Unknown / non-protocol algorithm names are *dropped silently* rather
    than raising. The negotiation protocol receives algorithm strings
    over the wire from the peer; an unrecognised string MUST be treated
    as "the peer does not support any algorithm this side recognises"
    so that the empty-intersection branch (Requirement 8.1 clause 4)
    fires uniformly with ``E_PROTOCOL``. Raising here would conflate
    "peer misbehaviour" with "implementation bug".
    """

    out: set = set()
    for alg in algs:
        try:
            out.add(normalize_alg(alg))
        except ValueError:
            # Unrecognised algorithm: peer advertises something outside
            # the Faying/1.0 enum. It cannot be in any intersection.
            continue
    return frozenset(out)


def negotiate(client_supports: Iterable[str], server_supports: Iterable[str]) -> str:
    """Return the strongest algorithm in ``client ∩ server``.

    Raises:
        NegotiationError: if the intersection is empty (Requirement 8.1
            clause 4 → ``E_PROTOCOL``).
    """

    client = _normalize_set(client_supports)
    server = _normalize_set(server_supports)
    intersection = client & server
    if not intersection:
        raise NegotiationError(
            f"E_PROTOCOL: no common signing algorithm between client "
            f"{sorted(client)} and server {sorted(server)}"
        )
    for alg in NEGOTIATION_ORDER:
        if alg in intersection:
            return alg
    # Defensive: NEGOTIATION_ORDER must list every supported algorithm.
    raise NegotiationError(
        f"E_PROTOCOL: intersection {sorted(intersection)} contains "
        f"algorithms outside NEGOTIATION_ORDER {NEGOTIATION_ORDER}"
    )
