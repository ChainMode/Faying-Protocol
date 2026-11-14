"""Pytest entry points for the encoding-dimension conformance driver.

These tests are *thin* — the actual invariants live in
``conformance.dim_encoding.driver`` (so they can also be invoked directly
through the CLI and the ``conformance/runner.py`` super-driver). Each test
locks in one acceptance criterion of task 5.2:

  * test_every_pair_passes               → I-E-1 .. I-E-7 hold on every
                                            two-sided pair shipped by task
                                            3.x (Requirements 10.1.3,
                                            10.2.1, 10.2.4, 10.3.3).
  * test_at_least_one_pair_per_msg_type   → the §TS.4 message-type coverage
                                            (BOOTSTRAP / PRESENCE / GRADE_
                                            SWITCH / DELEGATE / REVOKE)
                                            actually appears in the corpus.
  * test_content_type_assertion_explicit  → at least one pair declares the
                                            normative ``application/
                                            faying-protocol+json`` (or its
                                            recognised alias).
  * test_signature_input_hash_recorded   → every two-sided pair surfaces a
                                            SHA-256 digest, so downstream
                                            audits have a single anchor per
                                            vector.
  * test_normalize_round_trip            → the JSON-side normalisation is
                                            idempotent — repeated lifting
                                            does not mutate the tree.

Run with::

    python -m pytest conformance/dim_encoding/tests -q

or, equivalently, via the runner::

    python conformance/runner.py --run --dim encoding
"""

from __future__ import annotations

import pytest

from conformance.dim_encoding import (
    ACCEPTED_JSON_CONTENT_TYPES,
    discover_pairs,
    run_all,
    run_pair,
)
from conformance.dim_encoding.normalize import (
    json_to_cbor_shape,
)


@pytest.fixture(scope="session")
def summary():
    """Run the full encoding axis once per session."""
    return run_all()


def test_at_least_one_pair_discovered(summary):
    """The driver must find vectors to exercise; an empty corpus would
    silently green-light the suite."""
    assert summary.total > 0, "no CBOR/JSON pairs discovered under vectors/"


def test_every_pair_passes(summary):
    """Every discovered pair must satisfy the encoding-axis invariants.

    Validates: Requirements 10.1, 10.2, 10.3 (cross-encoding equivalence,
    Deterministic-CBOR signature input identity, signature-verification
    parity).
    """
    failures = [
        (r.pair.vector_id, [f"{f.code}: {f.message}" for f in r.findings if f.level == "FAIL"])
        for r in summary.results
        if not r.passed
    ]
    assert not failures, (
        "Encoding-dimension invariants violated:\n"
        + "\n".join(
            f"  - {vid}\n    " + "\n    ".join(msgs) for vid, msgs in failures
        )
    )


def test_at_least_one_pair_per_msg_type(summary):
    """The §TS.4 / Requirement 10.3.2 corpus mandates BOOTSTRAP, PRESENCE,
    GRADE_SWITCH, DELEGATE, and REVOKE message coverage.

    Two-sided coverage for each message type comes from the
    ``encoding-equivalence`` group (which ships exactly one of each, by
    design — see ``vectors/encoding-equivalence/index.json``). We assert
    each of those msg_types appears in at least one two-sided pair so the
    encoding-axis assertion is actually exercised against each.
    """
    import json
    from pathlib import Path

    eq_index_path = (
        Path(__file__).resolve().parents[3]
        / "vectors"
        / "encoding-equivalence"
        / "index.json"
    )
    eq_index = json.loads(eq_index_path.read_text("utf-8"))
    eq_msg_types = {v["msg_type"] for v in eq_index["vectors"]}
    required = {"BOOTSTRAP", "PRESENCE", "GRADE_SWITCH", "DELEGATE", "REVOKE"}
    missing = required - eq_msg_types
    assert not missing, (
        f"encoding-equivalence corpus is missing required §TS.4 msg_types: "
        f"{sorted(missing)}"
    )

    # And the driver actually exercised at least one two-sided pair from
    # the encoding-equivalence group.
    eq_pairs = [
        r for r in summary.results
        if r.pair.group == "encoding-equivalence" and r.pair.is_two_sided
    ]
    assert eq_pairs, (
        "encoding-equivalence vectors did not produce any two-sided pairs"
    )
    # Plus broader corpus coverage at the *group* level (one-sided OK).
    seen_groups = {r.pair.group for r in summary.results}
    for required_group in ("bootstrap", "presence", "grade-switch", "delegate", "revoke"):
        assert required_group in seen_groups, (
            f"vector group {required_group!r} not exercised at all"
        )


def test_content_type_assertion_explicit(summary):
    """At least one pair must explicitly declare its JSON Content-Type and
    have it accepted — Requirement 10.1.2.

    The Content-Type appears in vector ``expected.json`` files emitted by
    task 3.7 (``vectors/encoding-equivalence/*/expected.json``). If no
    pair surfaced the field, the assertion is vacuous and we surface that
    as a failure here so the corpus drift is loud.
    """
    pairs_with_ct = [r for r in summary.results if r.json_content_type]
    assert pairs_with_ct, (
        "no vector declared a JSON content_type in expected.json; "
        "Requirement 10.1.2 cannot be exercised"
    )
    for r in pairs_with_ct:
        assert r.json_content_type in ACCEPTED_JSON_CONTENT_TYPES, (
            f"vector {r.pair.vector_id} declares Content-Type "
            f"{r.json_content_type!r}, not in {list(ACCEPTED_JSON_CONTENT_TYPES)}"
        )


def test_signature_input_hash_recorded(summary):
    """Every two-sided pair should expose a SHA-256 digest of its
    Deterministic-CBOR signature input — Requirement 10.2.4."""
    missing = [
        r.pair.vector_id
        for r in summary.results
        if r.pair.is_two_sided and not r.signature_input_hash_hex
    ]
    assert not missing, (
        "two-sided pairs without a recorded signature_input hash:\n"
        + "\n".join(f"  - {x}" for x in missing)
    )


def test_normalize_round_trip():
    """``json_to_cbor_shape`` is idempotent on already-normalized trees:
    re-running it on the output never changes the result. This locks in
    the marker-detection logic against accidental greedy matching of
    binary fields that just happen to look like markers."""
    sample = {
        "header": {
            "version": "Faying Protocol/1.0",
            "issued-at": {"$tag": 0, "$value": "2026-01-01T00:00:00Z"},
            "nonce": {"$bytes": "AAECAwQFBgcICRAREhMUFQ"},
        },
        "claims": {
            "data": {"$b64": "aGVsbG8="},
            "alt": {"$b64u": "aGVsbG8"},
        },
    }
    once = json_to_cbor_shape(sample)
    twice = json_to_cbor_shape(once)
    assert once == twice


def test_run_pair_returns_finding_codes_with_dot_prefix():
    """Sanity: every Finding code uses the documented ``E<N>.<sub>``
    namespace so reports stay greppable."""
    pairs = discover_pairs()
    assert pairs, "discover_pairs returned empty"
    sample = run_pair(pairs[0])
    for f in sample.findings:
        head = f.code.split(".")[0]
        assert head.startswith("E") and head[1:].isalnum(), (
            f"unexpected finding code namespace: {f.code!r}"
        )
