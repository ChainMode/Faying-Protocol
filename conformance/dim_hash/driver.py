"""CLI driver for the hash-dimension conformance suite (task 5.4).

Usage::

    python -m conformance.dim_hash.driver
    python -m conformance.dim_hash.driver --format json
    python -m conformance.dim_hash.driver --filter blake3

Exit codes:

* ``0`` — every (vector, hash) pair passed (acceptance gate met).
* ``1`` — at least one pair failed.
* ``2`` — invalid CLI arguments.

The driver is meant to be invokable from the same ``runner.py``
skeleton ``--run`` mode that task 5.1 reserved.
"""

from __future__ import annotations

import argparse
import dataclasses as _dc
import json
import sys
from pathlib import Path
from typing import Iterable, List, Optional

from .algorithms import HASH_BLAKE3, HASH_SHA256, SUPPORTED_HASHES
from .signing_input import (
    HashCheckResult,
    hash_vector_across_algorithms,
    iter_vector_dirs,
)


_REPO_ROOT = Path(__file__).resolve().parents[2]
_VECTORS_ROOT = _REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Aggregation.
# ---------------------------------------------------------------------------
@_dc.dataclass
class HashSuiteSummary:
    """Aggregate result of running ``run_all``.

    Attributes:
        total_pairs: ``len(vectors) × len(SUPPORTED_HASHES)``.
        passed_pairs: count of pairs whose :class:`HashCheckResult`
            passed.
        failed_pairs: count of pairs that failed.
        per_algorithm: ``{algorithm -> (passed, total)}`` for at-a-
            glance per-column reporting.
        results: flat list of every per-(vector, algorithm) result.
    """

    total_pairs: int
    passed_pairs: int
    failed_pairs: int
    per_algorithm: dict
    results: List[HashCheckResult]
    cross_check_count: int = 0
    cross_check_failures: int = 0

    @property
    def ok(self) -> bool:
        return self.failed_pairs == 0


def run_all(
    *,
    vectors_root: Path = _VECTORS_ROOT,
    filter_substr: Optional[str] = None,
) -> HashSuiteSummary:
    """Run the dim_hash suite across every discovered vector."""

    vector_dirs: Iterable[Path] = iter_vector_dirs(vectors_root)
    if filter_substr:
        needle = filter_substr.lower()
        vector_dirs = [
            vd for vd in vector_dirs if needle in vd.name.lower()
        ]

    flat: List[HashCheckResult] = []
    per_alg: dict = {alg: [0, 0] for alg in SUPPORTED_HASHES}
    cross_check_total = 0
    cross_check_fail = 0
    for vd in vector_dirs:
        per_vector = hash_vector_across_algorithms(vd)
        for alg in SUPPORTED_HASHES:
            r = per_vector[alg]
            flat.append(r)
            per_alg[alg][1] += 1
            if r.passed():
                per_alg[alg][0] += 1
            if r.reference_digest_matched is not None:
                cross_check_total += 1
                if not r.reference_digest_matched:
                    cross_check_fail += 1

    passed = sum(1 for r in flat if r.passed())
    return HashSuiteSummary(
        total_pairs=len(flat),
        passed_pairs=passed,
        failed_pairs=len(flat) - passed,
        per_algorithm={
            alg: tuple(counts) for alg, counts in per_alg.items()
        },
        results=flat,
        cross_check_count=cross_check_total,
        cross_check_failures=cross_check_fail,
    )


# ---------------------------------------------------------------------------
# Output formatters.
# ---------------------------------------------------------------------------
def _format_text(summary: HashSuiteSummary, *, verbose: bool = False) -> str:
    lines: List[str] = []
    lines.append(
        "Faying Protocol/1.0 — Conformance dim_hash (task 5.4)"
    )
    lines.append(f"  supported hashes        : {list(SUPPORTED_HASHES)}")
    lines.append(
        f"  signing-input expression: H(Det-CBOR(envelope_without_signature))"
    )
    lines.append(f"  total (vector, hash)    : {summary.total_pairs}")
    lines.append(f"  passed                  : {summary.passed_pairs}")
    lines.append(f"  failed                  : {summary.failed_pairs}")
    for alg in SUPPORTED_HASHES:
        ok, tot = summary.per_algorithm[alg]
        lines.append(
            f"    {alg:<10} : {ok}/{tot} pass"
        )
    lines.append(
        f"  reference SHA-256 cross-checks: {summary.cross_check_count} "
        f"({summary.cross_check_failures} failures)"
    )
    # Acceptance gate: 2/2 hashes succeed on every vector.
    pass_per_alg = all(
        ok == tot for ok, tot in summary.per_algorithm.values()
    )
    lines.append(
        f"  Acceptance (task 5.4, 2/2 hashes): "
        f"{'MET' if pass_per_alg else 'NOT MET'}"
    )
    lines.append("")

    if verbose or not summary.ok:
        for r in summary.results:
            status = "PASS" if r.passed() else "FAIL"
            note = f"  {r.notes}" if r.notes else ""
            lines.append(
                f"  [{status}] {r.vector_name:40s}  "
                f"{r.hash_algorithm:<8} "
                f"input={r.signing_input_length:>5}B "
                f"digest={r.digest_hex}{note}"
            )
    return "\n".join(lines)


def _format_json(summary: HashSuiteSummary) -> str:
    payload = {
        "dimension": "hash",
        "supported_hashes": list(SUPPORTED_HASHES),
        "signing_input_expression": (
            "H(Det-CBOR(envelope_without_signature))  per design.md §6.3"
        ),
        "total_pairs": summary.total_pairs,
        "passed_pairs": summary.passed_pairs,
        "failed_pairs": summary.failed_pairs,
        "per_algorithm": {
            alg: {"passed": ok, "total": tot}
            for alg, (ok, tot) in summary.per_algorithm.items()
        },
        "reference_cross_checks": {
            "total": summary.cross_check_count,
            "failures": summary.cross_check_failures,
        },
        "results": [
            {
                "vector_name": r.vector_name,
                "hash_algorithm": r.hash_algorithm,
                "signing_input_length": r.signing_input_length,
                "digest_hex": r.digest_hex,
                "digest_length": r.digest_length,
                "reference_digest_matched": r.reference_digest_matched,
                "notes": r.notes,
                "passed": r.passed(),
            }
            for r in summary.results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="conformance.dim_hash.driver",
        description=(
            "Hash-dimension conformance driver. Implements the SHA-256 / "
            "BLAKE3 coverage and §6.3 signing-input identity gates of "
            "task 5.4."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: %(default)s)",
    )
    parser.add_argument(
        "--filter",
        default=None,
        help=(
            "Substring filter on vector directory name "
            "(e.g. 'pos-cbor', 'bootstrap')."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show every (vector, hash) result, not just failures.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    summary = run_all(filter_substr=args.filter)
    out = (
        _format_json(summary)
        if args.format == "json"
        else _format_text(summary, verbose=args.verbose)
    )
    print(out)
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
