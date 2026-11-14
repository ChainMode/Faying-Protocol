"""CLI driver for the channel-binding conformance dimension (task 5.5).

Usage::

    python -m conformance.dim_channel.driver
    python -m conformance.dim_channel.driver --format json
    python -m conformance.dim_channel.driver --filter mtls

Exit codes:

* ``0`` — all scenarios passed (acceptance gate met).
* ``1`` — at least one scenario produced an unexpected outcome.
* ``2`` — invalid CLI arguments.

The driver is stdlib-only and is meant to be invokable from the same
``runner.py`` skeleton ``--run`` mode that task 5.1 reserved.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import List

from .scenarios import ScenarioResult, run_all


def _filter_results(
    results: List[ScenarioResult], needle: str | None
) -> List[ScenarioResult]:
    if not needle:
        return results
    n = needle.lower()
    return [r for r in results if n in r.scenario.scenario_id.lower()]


def _render_text(results: List[ScenarioResult]) -> str:
    lines: List[str] = []
    lines.append("Faying Protocol — dim_channel conformance results")
    lines.append("  Requirement: 9.2.3 / 10.3 (design.md §9.3 / §TS.4)")
    lines.append("  Channel binding: RFC 9266 TLS Exporter")
    lines.append("")
    if not results:
        lines.append("  (no scenarios matched the filter)")
        return "\n".join(lines)

    widths = {
        "scenario_id": max(20, max(len(r.scenario.scenario_id) for r in results)),
        "expect": 20,
        "actual": 28,
        "verdict": 7,
    }
    header = (
        "  "
        f"{'scenario_id'.ljust(widths['scenario_id'])}  "
        f"{'expected'.ljust(widths['expect'])}  "
        f"{'actual'.ljust(widths['actual'])}  "
        f"{'verdict'.ljust(widths['verdict'])}"
    )
    lines.append(header)
    lines.append("  " + "-" * (len(header) - 2))
    for r in results:
        expected = (
            "accept"
            if r.scenario.expected_accepted
            else f"reject {r.scenario.expected_error_code}"
        )
        if r.actual.accepted:
            actual = "accept"
        else:
            actual = (
                f"reject {r.actual.error_code} "
                f"({r.actual.error_name or '?'})"
            )
        verdict = "PASS" if r.passed else "FAIL"
        lines.append(
            "  "
            f"{r.scenario.scenario_id.ljust(widths['scenario_id'])}  "
            f"{expected.ljust(widths['expect'])}  "
            f"{actual.ljust(widths['actual'])}  "
            f"{verdict.ljust(widths['verdict'])}"
        )

    total = len(results)
    passed = sum(1 for r in results if r.passed)
    lines.append("")
    lines.append(f"Total: {total}  Passed: {passed}  Failed: {total - passed}")

    # Acceptance probes from task 5.5 verbatim.
    mtls_no_binding = [
        r
        for r in results
        if r.scenario.tls_mode == "mtls"
        and r.scenario.binding_shape == "absent"
    ]
    tls_no_binding = [
        r
        for r in results
        if r.scenario.tls_mode == "tls-only"
        and r.scenario.binding_shape == "absent"
    ]
    if mtls_no_binding:
        all_rejected = all(
            (not r.actual.accepted) and r.actual.error_code == 1007
            for r in mtls_no_binding
        )
        lines.append(
            "  Acceptance probe — mTLS missing channel binding rejected: "
            f"{'MET' if all_rejected else 'NOT MET'}"
        )
    if tls_no_binding:
        all_accepted = all(r.actual.accepted for r in tls_no_binding)
        lines.append(
            "  Acceptance probe — TLS-only without binding accepted:    "
            f"{'MET' if all_accepted else 'NOT MET'}"
        )
    return "\n".join(lines)


def _render_json(results: List[ScenarioResult]) -> str:
    payload = {
        "dimension": "channel",
        "requirement": "9.2.3",
        "design_anchor": "design.md §9.3",
        "binding_type": "tls-exporter (RFC 9266)",
        "results": [r.to_dict() for r in results],
        "summary": {
            "total": len(results),
            "passed": sum(1 for r in results if r.passed),
            "failed": sum(1 for r in results if not r.passed),
        },
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="conformance.dim_channel.driver",
        description=(
            "Channel-dimension conformance driver. Implements the RFC 9266 "
            "TLS Exporter check mandated by Requirement 9.2.3."
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
            "Substring filter on scenario_id "
            "(e.g. 'mtls', 'bootstrap__tls-only')."
        ),
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    results = _filter_results(run_all(), args.filter)
    out = (
        _render_json(results)
        if args.format == "json"
        else _render_text(results)
    )
    print(out)
    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
