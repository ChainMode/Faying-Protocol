"""Conformance tests for the hash-algorithm dimension (task 5.4).

This file is the acceptance harness for task 5.4 of
``docs/en/specification/2025-10-25/README.md``. It validates two related
but distinct claims:

  A. **Hash coverage** — every vector under ``vectors/`` can be hashed
     under each of ``SHA-256`` and ``BLAKE3`` (2/2 哈希跑通).

  B. **Signing-input construction (§6.3)** — the bytes fed to the hash
     function are identical regardless of which hash algorithm wraps
     them, and where a vector ships a SHA-256 reference digest of its
     signing input the conformance computation matches it exactly.

  C. **Hash-suite negotiation** — the negotiation rule from
     Requirement 8.1 (clauses 1–4) holds for every advertised hash
     support set.

Run the suite with::

    pytest conformance/dim_hash/

The tests are stdlib-only at the test level, with ``cbor2`` and
``blake3`` pulled in transitively via the dim_hash package. They do
NOT require the ``pbt/`` virtualenv.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import List

import pytest

from conformance.dim_hash.algorithms import (
    HASH_BLAKE3,
    HASH_DIGEST_SIZE_BYTES,
    HASH_SHA256,
    SUPPORTED_HASHES,
    compute_hash,
    normalize_hash,
)
from conformance.dim_hash.negotiation import (
    MANDATORY_HASH_BASELINE,
    NEGOTIATION_ORDER,
    HashNegotiationError,
    negotiate_hash,
)
from conformance.dim_hash.signing_input import (
    compute_signing_input,
    hash_vector_across_algorithms,
    iter_vector_dirs,
    load_envelope,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
VECTORS_ROOT = REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Vector discovery (collected once at import time so pytest -k filters work).
# ---------------------------------------------------------------------------
def _discover_vectors() -> List[Path]:
    if not VECTORS_ROOT.exists():
        pytest.skip(
            f"vectors directory missing: {VECTORS_ROOT}",
            allow_module_level=True,
        )
    vectors = iter_vector_dirs(VECTORS_ROOT)
    if not vectors:
        pytest.skip("no vectors discovered", allow_module_level=True)
    return vectors


VECTOR_DIRS: List[Path] = _discover_vectors()
VECTOR_IDS: List[str] = [
    f"{vd.parent.name}/{vd.name}" for vd in VECTOR_DIRS
]


# ---------------------------------------------------------------------------
# A. Hash coverage (2/2 哈希跑通).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("vector_dir", "algorithm"),
    [(vd, alg) for vd in VECTOR_DIRS for alg in SUPPORTED_HASHES],
    ids=[
        f"{vd.parent.name}/{vd.name}::{alg}"
        for vd in VECTOR_DIRS
        for alg in SUPPORTED_HASHES
    ],
)
def test_hash_each_vector_under_each_algorithm(
    vector_dir: Path, algorithm: str
) -> None:
    """Every vector hashes cleanly under each supported algorithm.

    Validates: Requirements 8.1, 10.2, 10.3 (acceptance criterion of
    task 5.4, "2/2 哈希跑通").
    """

    envelope, _encoding = load_envelope(vector_dir)
    signing_input = compute_signing_input(envelope)
    digest = compute_hash(algorithm, signing_input)

    expected_len = HASH_DIGEST_SIZE_BYTES[algorithm]
    assert len(digest) == expected_len, (
        f"{vector_dir.name}: {algorithm} digest is {len(digest)} bytes, "
        f"expected {expected_len} (FAP/1.0 fixes the output length)"
    )
    # Sanity: the all-zero digest would indicate a back-end that is
    # silently no-op'ing. SHA-256 / BLAKE3 of any non-empty input never
    # produces an all-zero digest.
    assert digest != b"\x00" * expected_len
    assert len(signing_input) > 0


def test_two_of_two_hashes_succeed_on_every_vector() -> None:
    """Both hash algorithms succeed on every vector (acceptance bullet 1).

    This is the aggregate version of the per-(vector, hash) test; it
    fails fast if any single combination does not pass. The
    accompanying parametrized test gives finer-grained diagnostics.

    Validates: Requirements 8.1, 10.2, 10.3
    """

    failures: List[str] = []
    for vd in VECTOR_DIRS:
        results = hash_vector_across_algorithms(vd)
        succeeded = {alg for alg, r in results.items() if r.passed()}
        if succeeded != set(SUPPORTED_HASHES):
            missing = sorted(set(SUPPORTED_HASHES) - succeeded)
            failures.append(f"{vd.parent.name}/{vd.name}: missing {missing}")
    assert not failures, "; ".join(failures)


# ---------------------------------------------------------------------------
# B. Signing-input construction matches §6.3.
# ---------------------------------------------------------------------------
def test_signing_input_invariant_across_hash_algorithms() -> None:
    """The signing-input bytes ``Det-CBOR(envelope_without_signature)``
    are independent of which hash algorithm wraps them.

    This is the conformance-level cousin of property P16.1 for the
    *hash* axis: the bytes that go into ``H(...)`` depend only on the
    envelope payload, not on which hash function is used. If this
    invariant breaks, swapping SHA-256 for BLAKE3 would silently
    change what the hash is computed over.

    Validates: Requirements 10.2, 10.3 (task 5.4 "签名输入构造与
    §6.3 完全一致")
    """

    for vd in VECTOR_DIRS:
        results = hash_vector_across_algorithms(vd)
        # Compare the captured signing-input bytes across algorithms.
        signing_inputs = {r.signing_input_bytes for r in results.values()}
        assert len(signing_inputs) == 1, (
            f"{vd.parent.name}/{vd.name}: signing-input bytes differ "
            f"across hash algorithms (must be invariant): "
            f"{sorted(len(b) for b in signing_inputs)}"
        )


def test_sha256_matches_reference_digests_in_vectors() -> None:
    """Where a vector ships a SHA-256 reference digest of the signing
    input (e.g. ``vectors/encoding-equivalence/01-bootstrap/expected.json
    .signature_input.hash_hex``), our computation matches it exactly.

    A mismatch would mean our signing-input construction diverges from
    the one in §6.3, which is a direct failure of task 5.4's
    acceptance gate "签名输入构造与 §6.3 完全一致".

    Validates: Requirements 10.2, 10.3
    """

    checked = 0
    failures: List[str] = []
    for vd in VECTOR_DIRS:
        results = hash_vector_across_algorithms(vd)
        sha = results[HASH_SHA256]
        if sha.reference_digest_matched is None:
            continue
        checked += 1
        if not sha.reference_digest_matched:
            failures.append(
                f"{vd.parent.name}/{vd.name}: {sha.notes}"
            )
    assert not failures, "; ".join(failures)
    # Sanity: at least the encoding-equivalence vectors ship reference
    # digests, so we should have cross-checked at least one.
    assert checked > 0, (
        "no vectors carried a SHA-256 reference digest of the signing "
        "input; the §6.3 cross-check was vacuous (expected at least "
        "vectors/encoding-equivalence/* to advertise hash_hex)"
    )


def test_digests_differ_between_sha256_and_blake3() -> None:
    """SHA-256 and BLAKE3 are different functions, so their digests of
    the same input must (overwhelmingly) differ.

    A coincident digest would mean one of the two back-ends is
    misconfigured (or, astronomically improbably, a real collision —
    we leave that to the universe).

    Validates: Requirements 8.1, 10.3 (algorithm distinctness)
    """

    for vd in VECTOR_DIRS:
        results = hash_vector_across_algorithms(vd)
        sha_hex = results[HASH_SHA256].digest_hex
        blake_hex = results[HASH_BLAKE3].digest_hex
        assert sha_hex != blake_hex, (
            f"{vd.parent.name}/{vd.name}: SHA-256 and BLAKE3 produced "
            f"identical digests {sha_hex!r}; one of the back-ends is "
            "misconfigured"
        )


# ---------------------------------------------------------------------------
# C. Hash-suite negotiation.
# ---------------------------------------------------------------------------
def test_mandatory_baseline_includes_sha256() -> None:
    """SHA-256 is the de-facto mandatory hash baseline (design.md §6.1
    marks it as the default and every existing vector hashes with it).
    """

    assert HASH_SHA256 in MANDATORY_HASH_BASELINE


def test_negotiation_picks_strongest_mutually_supported() -> None:
    """Requirement 8.1 clause 2: pick the strongest mutual hash.

    Iterate every non-empty pair of advertised support sets drawn from
    ``SUPPORTED_HASHES`` and assert that ``negotiate_hash(a, b)`` is
    the head of :data:`NEGOTIATION_ORDER` that is in ``a ∩ b``.
    """

    universe = list(SUPPORTED_HASHES)
    pairs_tested = 0
    for r1 in range(1, len(universe) + 1):
        for client in itertools.combinations(universe, r1):
            for r2 in range(1, len(universe) + 1):
                for server in itertools.combinations(universe, r2):
                    pairs_tested += 1
                    intersection = set(client) & set(server)
                    if not intersection:
                        with pytest.raises(HashNegotiationError):
                            negotiate_hash(client, server)
                        continue
                    expected = next(
                        a for a in NEGOTIATION_ORDER if a in intersection
                    )
                    actual = negotiate_hash(client, server)
                    assert actual == expected, (
                        f"client={client} server={server} "
                        f"expected {expected!r} got {actual!r}"
                    )
    # 2 algorithms → 3 non-empty subsets → 3 × 3 = 9 client/server
    # combinations.
    assert pairs_tested >= 9


def test_negotiation_rejects_disjoint_sets_with_e_protocol() -> None:
    """Requirement 8.1 clause 4: empty intersection → ``E_PROTOCOL``."""

    with pytest.raises(HashNegotiationError) as excinfo:
        negotiate_hash([HASH_SHA256], ["MD5"])
    assert excinfo.value.error_name == "E_PROTOCOL"
    assert excinfo.value.error_code == 1099


def test_negotiation_aliases_lowercase_names() -> None:
    """Hash names are case-insensitive on input but normalised to the
    wire-format on output."""

    assert negotiate_hash(["sha256"], ["SHA-256"]) == HASH_SHA256
    assert negotiate_hash(["blake3"], [HASH_BLAKE3]) == HASH_BLAKE3


def test_strongest_when_both_sides_advertise_blake3() -> None:
    """When both sides advertise BLAKE3 (which is ranked stronger than
    SHA-256 per :data:`NEGOTIATION_ORDER`), the strongest-rule selects
    it.
    """

    chosen = negotiate_hash(
        client_supports=[HASH_SHA256, HASH_BLAKE3],
        server_supports=[HASH_SHA256, HASH_BLAKE3],
    )
    assert chosen == HASH_BLAKE3


def test_falls_back_to_sha256_when_only_one_side_has_blake3() -> None:
    """A peer that only advertises SHA-256 must still BOOTSTRAP; the
    intersection is ``{SHA-256}`` and that is what gets chosen."""

    chosen = negotiate_hash(
        client_supports=[HASH_SHA256, HASH_BLAKE3],
        server_supports=[HASH_SHA256],
    )
    assert chosen == HASH_SHA256


def test_negotiation_order_covers_every_supported_hash() -> None:
    """Sanity: every wire-format hash appears in NEGOTIATION_ORDER.

    A drift here would let a future PR add a hash to SUPPORTED_HASHES
    without giving it a strength rank, which would silently break the
    strongest-rule. Catch it at conformance time.
    """

    assert set(NEGOTIATION_ORDER) == set(SUPPORTED_HASHES)


# ---------------------------------------------------------------------------
# Direct algorithm-API self-tests (NIST KAT-style spot checks).
# ---------------------------------------------------------------------------
def test_sha256_known_answer() -> None:
    """SHA-256 of the empty string matches the FIPS 180-4 known answer.

    This guards against a silently broken hashlib (e.g. an OpenSSL
    fallback that has been monkey-patched).
    """

    digest = compute_hash(HASH_SHA256, b"")
    expected = bytes.fromhex(
        "e3b0c44298fc1c149afbf4c8996fb924"
        "27ae41e4649b934ca495991b7852b855"
    )
    assert digest == expected


def test_blake3_known_answer() -> None:
    """BLAKE3 of the empty string matches the spec's known answer.

    This guards against a silently broken ``blake3`` package (e.g.
    one returning XOF-style output instead of the 32-byte default).
    """

    digest = compute_hash(HASH_BLAKE3, b"")
    expected = bytes.fromhex(
        "af1349b9f5f9a1a6a0404dea36dcc949"
        "9bcb25c9adc112b7cc9a93cae41f3262"
    )
    assert digest == expected


def test_normalize_rejects_unknown_hash() -> None:
    """``normalize_hash`` fails closed on names outside the protocol enum.

    Validates: Requirement 8.1 clause 4 (algorithms outside the enum
    cannot enter negotiation).
    """

    with pytest.raises(ValueError):
        normalize_hash("MD5")
    with pytest.raises(ValueError):
        normalize_hash("SHA3-256")  # PQC reserved but not in task 5.4
