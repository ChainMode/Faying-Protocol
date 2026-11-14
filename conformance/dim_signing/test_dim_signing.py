"""Conformance tests for the signing-algorithm dimension (task 5.3).

This file is the acceptance harness for task 5.3 of
``docs/en/specification/2025-10-25/README.md``. It validates two related
but distinct claims:

  A. **Re-sign coverage** — every vector under ``vectors/`` can be
     re-signed and verified under each of ``Ed25519`` / ``ES256`` /
     ``ML-DSA-65`` (3/3 algorithms跑通).

  B. **Algorithm-suite negotiation** — the negotiation rule from
     Requirement 8.1 (clauses 1–4) plus Requirement 8.2 clause 3
     (PQC OPTIONAL) holds for every advertised support set in the
     conformance matrix.

Run the suite with::

    pytest conformance/dim_signing/

The tests are stdlib-only at the test level, with ``cbor2`` and
``cryptography`` pulled in transitively via the dim_signing package.
They do NOT require the ``pbt/`` virtualenv.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import List

import pytest

from conformance.dim_signing.algorithms import (
    ALG_ED25519,
    ALG_ES256,
    ALG_ML_DSA_65,
    SUPPORTED_ALGORITHMS,
)
from conformance.dim_signing.negotiation import (
    MANDATORY_BASELINE,
    NEGOTIATION_ORDER,
    NegotiationError,
    negotiate,
)
from conformance.dim_signing.resign import (
    iter_vector_dirs,
    resign_and_verify,
    resign_vector_across_algorithms,
    load_envelope,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VECTORS_ROOT = REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Vector discovery (collected once at import time so pytest -k filters work).
# ---------------------------------------------------------------------------
def _discover_vectors() -> List[Path]:
    if not VECTORS_ROOT.exists():
        pytest.skip(f"vectors directory missing: {VECTORS_ROOT}", allow_module_level=True)
    vectors = iter_vector_dirs(VECTORS_ROOT)
    if not vectors:
        pytest.skip("no vectors discovered", allow_module_level=True)
    return vectors


VECTOR_DIRS: List[Path] = _discover_vectors()
VECTOR_IDS: List[str] = [
    f"{vd.parent.name}/{vd.name}" for vd in VECTOR_DIRS
]


# ---------------------------------------------------------------------------
# A. Re-sign coverage.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("vector_dir", "algorithm"),
    [
        (vd, alg)
        for vd in VECTOR_DIRS
        for alg in SUPPORTED_ALGORITHMS
    ],
    ids=[
        f"{vd.parent.name}/{vd.name}::{alg}"
        for vd in VECTOR_DIRS
        for alg in SUPPORTED_ALGORITHMS
    ],
)
def test_resign_each_vector_under_each_algorithm(
    vector_dir: Path, algorithm: str
) -> None:
    """Every vector re-signs and verifies cleanly under each algorithm.

    Validates: Requirements 8.1, 10.3 (acceptance criterion of task 5.3,
    "3/3 算法跑通").
    """

    envelope, _encoding = load_envelope(vector_dir)
    result = resign_and_verify(
        envelope,
        vector_name=vector_dir.name,
        algorithm=algorithm,
        seed=b"\x00" * 32,  # deterministic for reproducibility
    )

    assert result.signature_alg == algorithm, (
        f"signature.alg field must equal the requested algorithm, "
        f"got {result.signature_alg!r} for {algorithm!r}"
    )
    assert result.verify_ok, (
        f"verification failed for {vector_dir.name} under {algorithm}: "
        f"{result.notes}"
    )
    assert result.signature_length > 0
    assert result.public_key_length > 0


def test_three_of_three_algorithms_succeed_on_every_vector() -> None:
    """All three algorithms succeed on every vector (acceptance bullet 1).

    This is the aggregate version of the per-(vector, alg) test; it
    fails fast if any single combination does not pass. The accompanying
    parametrized test gives finer-grained diagnostics.

    Validates: Requirements 8.1, 10.3
    """

    failures: List[str] = []
    for vd in VECTOR_DIRS:
        results = resign_vector_across_algorithms(vd, seed=b"\x00" * 32)
        succeeded = {alg for alg, r in results.items() if r.passed()}
        if succeeded != set(SUPPORTED_ALGORITHMS):
            missing = sorted(set(SUPPORTED_ALGORITHMS) - succeeded)
            failures.append(f"{vd.parent.name}/{vd.name}: missing {missing}")
    assert not failures, "; ".join(failures)


# ---------------------------------------------------------------------------
# Property test (small Cartesian property): stable signing-input hash.
# ---------------------------------------------------------------------------
def test_signing_input_invariant_across_algorithms() -> None:
    """Signing input ``H(Det-CBOR(Envelope_without_signature))`` is
    independent of which algorithm signs it.

    This is the conformance-level cousin of property P16.1: the signing
    input must depend only on the envelope payload, not on the signing
    algorithm. If this invariant breaks, any cross-algorithm vector
    interchange would silently lose verifiability.

    Validates: Requirements 8.1, 10.2
    """

    for vd in VECTOR_DIRS:
        results = resign_vector_across_algorithms(vd, seed=b"\x11" * 32)
        digests = {r.signing_input_sha256 for r in results.values()}
        assert len(digests) == 1, (
            f"{vd.parent.name}/{vd.name}: signing input differs across "
            f"algorithms (must be invariant): {digests}"
        )


# ---------------------------------------------------------------------------
# B. Algorithm-suite negotiation.
# ---------------------------------------------------------------------------
def test_mandatory_baseline_is_classical_pair() -> None:
    """Requirement 8.1 clause 3: implementations MUST support
    ``{Ed25519, ECDSA-P256}``.
    """

    assert MANDATORY_BASELINE == frozenset({ALG_ED25519, ALG_ES256})


def test_negotiation_picks_strongest_mutually_supported() -> None:
    """Requirement 8.1 clause 2: pick the strongest mutual algorithm.

    Iterate every non-empty pair of advertised support sets drawn from
    ``SUPPORTED_ALGORITHMS`` and assert that ``negotiate(a, b)`` is the
    head of :data:`NEGOTIATION_ORDER` that is in ``a ∩ b``.
    """

    universe = list(SUPPORTED_ALGORITHMS)
    pairs_tested = 0
    for r1 in range(1, len(universe) + 1):
        for client in itertools.combinations(universe, r1):
            for r2 in range(1, len(universe) + 1):
                for server in itertools.combinations(universe, r2):
                    pairs_tested += 1
                    intersection = set(client) & set(server)
                    if not intersection:
                        with pytest.raises(NegotiationError):
                            negotiate(client, server)
                        continue
                    expected = next(
                        a for a in NEGOTIATION_ORDER if a in intersection
                    )
                    actual = negotiate(client, server)
                    assert actual == expected, (
                        f"client={client} server={server} "
                        f"expected {expected!r} got {actual!r}"
                    )
    assert pairs_tested >= 49, (
        f"expected ≥ 49 client/server combinations, got {pairs_tested}"
    )


def test_negotiation_rejects_disjoint_sets_with_e_protocol() -> None:
    """Requirement 8.1 clause 4: empty intersection → ``E_PROTOCOL``."""

    with pytest.raises(NegotiationError) as excinfo:
        negotiate([ALG_ED25519], ["RSA-PKCS1-v1_5-SHA1"])
    assert excinfo.value.error_name == "E_PROTOCOL"
    assert excinfo.value.error_code == 1099


def test_negotiation_aliases_ecdsa_p256() -> None:
    """The task description uses ``ECDSA-P256``; the wire enum is
    ``ES256``. The negotiator must accept both.
    """

    assert negotiate(["ECDSA-P256"], [ALG_ES256]) == ALG_ES256


def test_ml_dsa_65_is_optional_for_bootstrap() -> None:
    """Requirement 8.2 clause 3: an implementation that lacks ML-DSA-65
    must still be able to BOOTSTRAP whenever the classical baseline is
    mutually supported.

    Concretely:
      * client supports {Ed25519, ES256, ML-DSA-65}
      * server supports {Ed25519, ES256}            (no PQC)
      → negotiation succeeds and picks the strongest *classical*
        algorithm, i.e. ``Ed25519``.

    Validates: Requirement 8.2 (the acceptance bullet
    "ML-DSA-65 作为 OPTIONAL 实现存在").
    """

    chosen = negotiate(
        client_supports=[ALG_ED25519, ALG_ES256, ALG_ML_DSA_65],
        server_supports=[ALG_ED25519, ALG_ES256],
    )
    assert chosen == ALG_ED25519, (
        f"server without PQC support must still BOOTSTRAP via the "
        f"classical baseline; expected Ed25519, got {chosen!r}"
    )

    # Symmetric case: server has PQC, client does not. Still classical.
    chosen2 = negotiate(
        client_supports=[ALG_ED25519, ALG_ES256],
        server_supports=[ALG_ED25519, ALG_ES256, ALG_ML_DSA_65],
    )
    assert chosen2 == ALG_ED25519


def test_ml_dsa_65_chosen_when_both_sides_advertise_it() -> None:
    """When both sides advertise PQC, the strongest-rule selects it."""

    chosen = negotiate(
        client_supports=[ALG_ED25519, ALG_ML_DSA_65],
        server_supports=[ALG_ES256, ALG_ML_DSA_65],
    )
    assert chosen == ALG_ML_DSA_65


def test_negotiation_order_covers_every_supported_algorithm() -> None:
    """Sanity: every wire-format algorithm appears in NEGOTIATION_ORDER.

    A drift here would let a future PR add an algorithm to
    SUPPORTED_ALGORITHMS without giving it a strength rank, which would
    silently break the strongest-rule. Catch it at conformance time.
    """

    assert set(NEGOTIATION_ORDER) == set(SUPPORTED_ALGORITHMS)
