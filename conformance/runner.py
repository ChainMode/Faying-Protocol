#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Faying Protocol/1.0 — Conformance Test Suite Runner (skeleton).

This runner is the entry point of the互操作合规测试套件 mandated by
Requirement 10.3 (design.md §TS.4). Task 5.1 ships only the skeleton:

  * It loads the 5-dimensional matrix from ``conformance/matrix.yaml``.
  * It enumerates the cartesian product
    ``encoding × signing-alg × hash × channel × impl-language``.
  * In ``--dry-run`` mode it prints every combination and exits 0 if the
    combination count meets the Requirement 10.3 minimum (≥ 24).

Dimensional execution (per-combination CBOR/JSON re-parse, signature re-verify,
channel-binding probes, etc.) belongs to tasks 5.2 – 5.6 and is intentionally
*not* implemented here. ``--run`` is reserved as a placeholder so callers can
fail fast until the dimensional drivers land.

The runner is **stdlib-only** so it can be invoked in any contributor's
environment without first bootstrapping ``pbt/``'s virtualenv. It deliberately
references ``vectors/`` and ``schemas/`` (per the task spec) but does not yet
read them; the dimensional task drivers will plug in here.

Usage::

    python conformance/runner.py --dry-run
    python conformance/runner.py --dry-run --format json
    python conformance/runner.py --matrix conformance/matrix.yaml --dry-run
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import sys
from typing import Any, Dict, List, Tuple

# ---------------------------------------------------------------------------
# Repository layout anchors (Requirement 10.3 references these explicitly).
# ---------------------------------------------------------------------------
HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.abspath(os.path.join(HERE, os.pardir))
DEFAULT_MATRIX = os.path.join(HERE, "matrix.yaml")
VECTORS_DIR = os.path.join(REPO_ROOT, "vectors")
SCHEMAS_DIR = os.path.join(REPO_ROOT, "schemas")

# Order is **normative** for combination identifiers below. Keep it stable so
# downstream artifacts (CI logs, audit chains) can hash combination IDs.
DIMENSION_ORDER: Tuple[str, ...] = (
    "encoding",
    "signing-alg",
    "hash",
    "channel",
    "impl-language",
)


# ---------------------------------------------------------------------------
# Minimal YAML loader.
# ---------------------------------------------------------------------------
# We avoid PyYAML here so the conformance runner is dependency-free. The
# parser only handles the very specific shape declared by ``matrix.yaml``:
#
#   * top-level ``key: scalar`` lines
#   * top-level ``key:`` introducing a 2-space-indented sub-mapping
#   * in a sub-mapping, ``key:`` introduces a 4-space-indented scalar list
#     of ``- value`` items
#   * ``#`` comments, blank lines
#
# Anything more elaborate (anchors, flow style, multi-line strings, deeply
# nested mappings) is rejected with an explicit error so authors do not
# silently introduce shapes the runner cannot interpret.
def _scalar(value: str) -> Any:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if lowered in ("null", "~", ""):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value


def _strip_comment(raw: str) -> str:
    # We do not support `#` inside string literals in matrix.yaml; the format
    # is intentionally restricted. If a `#` shows up it always starts a
    # comment.
    return raw.split("#", 1)[0].rstrip()


def parse_matrix_yaml(path: str) -> Dict[str, Any]:
    """Parse ``matrix.yaml`` into a plain dict.

    Raises ``ValueError`` with a precise location if a line falls outside the
    accepted subset. This is more useful than PyYAML's silent type coercion
    for a small, controlled file.
    """
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()

    result: Dict[str, Any] = {}
    current_top: str | None = None
    current_sub: str | None = None

    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = _strip_comment(raw)
        if not line.strip():
            continue

        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)

        if indent == 0:
            key, sep, value = stripped.partition(":")
            if not sep:
                raise ValueError(
                    f"matrix.yaml line {lineno}: expected 'key: ...': {raw!r}"
                )
            key = key.strip()
            value = value.strip()
            if value:
                result[key] = _scalar(value)
                current_top = None
            else:
                result[key] = {}
                current_top = key
            current_sub = None
        elif indent == 2:
            if current_top is None:
                raise ValueError(
                    f"matrix.yaml line {lineno}: indented line has no parent: {raw!r}"
                )
            key, sep, value = stripped.partition(":")
            if not sep:
                raise ValueError(
                    f"matrix.yaml line {lineno}: expected 'key: ...': {raw!r}"
                )
            key = key.strip()
            value = value.strip()
            if value:
                result[current_top][key] = _scalar(value)
                current_sub = None
            else:
                result[current_top][key] = []
                current_sub = key
        elif indent == 4:
            if current_sub is None:
                raise ValueError(
                    f"matrix.yaml line {lineno}: list item without parent key: {raw!r}"
                )
            if not stripped.startswith("- "):
                raise ValueError(
                    f"matrix.yaml line {lineno}: expected '- value': {raw!r}"
                )
            result[current_top][current_sub].append(_scalar(stripped[2:].strip()))
        else:
            raise ValueError(
                f"matrix.yaml line {lineno}: unsupported indent {indent}: {raw!r}"
            )

    return result


# ---------------------------------------------------------------------------
# Matrix expansion.
# ---------------------------------------------------------------------------
def expand_matrix(spec: Dict[str, Any]) -> List[Dict[str, str]]:
    dimensions = spec.get("dimensions")
    if not isinstance(dimensions, dict):
        raise ValueError("matrix.yaml: 'dimensions' must be a mapping")

    missing = [d for d in DIMENSION_ORDER if d not in dimensions]
    if missing:
        raise ValueError(
            f"matrix.yaml: missing required dimensions {missing}; "
            f"Requirement 10.3 mandates {list(DIMENSION_ORDER)}"
        )

    axes: List[List[str]] = []
    for name in DIMENSION_ORDER:
        values = dimensions[name]
        if not isinstance(values, list) or not values:
            raise ValueError(
                f"matrix.yaml: dimension '{name}' must be a non-empty list"
            )
        # Cast each value to str (int/bool would be nonsensical here).
        axes.append([str(v) for v in values])

    combos: List[Dict[str, str]] = []
    for tup in itertools.product(*axes):
        combo = dict(zip(DIMENSION_ORDER, tup))
        combos.append(combo)
    return combos


def _combo_id(idx: int, combo: Dict[str, str]) -> str:
    parts = [combo[name] for name in DIMENSION_ORDER]
    return f"#{idx:03d} " + "/".join(parts)


# ---------------------------------------------------------------------------
# Output formatters.
# ---------------------------------------------------------------------------
def render_text(spec: Dict[str, Any], combos: List[Dict[str, str]]) -> str:
    lines: List[str] = []
    lines.append("Faying Protocol Conformance Matrix — dry run")
    lines.append(
        f"  spec_version : {spec.get('spec_version', '?')}"
    )
    lines.append(
        f"  requirement  : {spec.get('requirement', '?')}"
    )
    lines.append(
        f"  design_anchor: {spec.get('design_anchor', '?')}"
    )
    lines.append(
        f"  dimensions   : {' × '.join(DIMENSION_ORDER)}"
    )
    lines.append(
        f"  vectors_dir  : {os.path.relpath(VECTORS_DIR, REPO_ROOT)}"
    )
    lines.append(
        f"  schemas_dir  : {os.path.relpath(SCHEMAS_DIR, REPO_ROOT)}"
    )
    lines.append("")
    # Column widths so the table reads cleanly even as new values are added.
    widths = {
        name: max(len(name), max(len(c[name]) for c in combos))
        for name in DIMENSION_ORDER
    }
    header = "  ".join(name.ljust(widths[name]) for name in DIMENSION_ORDER)
    lines.append("  idx  " + header)
    lines.append("  " + "-" * (5 + len(header)))
    for idx, combo in enumerate(combos, start=1):
        row = "  ".join(combo[name].ljust(widths[name]) for name in DIMENSION_ORDER)
        lines.append(f"  {idx:03d}  {row}")
    lines.append("")
    lines.append(f"Total combinations: {len(combos)}")
    threshold = spec.get("acceptance_min_combinations", 24)
    if isinstance(threshold, int) and len(combos) >= threshold:
        lines.append(
            f"Acceptance (Requirement 10.3, ≥ {threshold}): MET"
        )
    else:
        lines.append(
            f"Acceptance (Requirement 10.3, ≥ {threshold}): NOT MET"
        )
    return "\n".join(lines)


def render_json(spec: Dict[str, Any], combos: List[Dict[str, str]]) -> str:
    payload = {
        "spec_version": spec.get("spec_version"),
        "requirement": spec.get("requirement"),
        "design_anchor": spec.get("design_anchor"),
        "dimensions_order": list(DIMENSION_ORDER),
        "vectors_dir": os.path.relpath(VECTORS_DIR, REPO_ROOT),
        "schemas_dir": os.path.relpath(SCHEMAS_DIR, REPO_ROOT),
        "combinations": [
            {"idx": idx, **combo}
            for idx, combo in enumerate(combos, start=1)
        ],
        "total_combinations": len(combos),
        "acceptance_min_combinations": spec.get("acceptance_min_combinations", 24),
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# CLI.
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="conformance/runner.py",
        description=(
            "Faying Protocol/1.0 conformance test suite runner. "
            "Implements the Requirement 10.3 mandatory matrix "
            "(design.md §TS.4)."
        ),
    )
    parser.add_argument(
        "--matrix",
        default=DEFAULT_MATRIX,
        help="Path to matrix.yaml (default: %(default)s)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Enumerate the cartesian product of dimensions without invoking "
            "any per-combination test driver. Required for task 5.1 "
            "acceptance."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Output format (default: %(default)s)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help=(
            "Run the per-dimension drivers. Currently wires up the "
            "encoding axis (task 5.2); other dimensions follow in tasks "
            "5.3–5.6."
        ),
    )
    parser.add_argument(
        "--dim",
        action="append",
        choices=("encoding", "hash"),
        help=(
            "Restrict --run to one or more dimensions. Repeatable. Defaults "
            "to all wired dimensions when omitted."
        ),
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="When passed with --run, show all per-pair findings.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.run and args.dry_run:
        print(
            "error: --run and --dry-run are mutually exclusive", file=sys.stderr
        )
        return 2
    if not args.run and not args.dry_run:
        print(
            "error: pass --dry-run (per task 5.1) or --run (tasks 5.2–5.6).",
            file=sys.stderr,
        )
        return 2

    try:
        spec = parse_matrix_yaml(args.matrix)
        combos = expand_matrix(spec)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.run:
        # ``--run`` invokes the per-dimension drivers in turn. Currently
        # only the encoding axis (task 5.2) is wired up; tasks 5.3–5.6
        # will plug additional drivers in here keyed on their --dim name.
        # The driver modules live at ``conformance/dim_*/``; we make them
        # importable whether the runner is invoked as a script or as a
        # module by adding ``conformance/`` to ``sys.path``.
        if HERE not in sys.path:
            sys.path.insert(0, HERE)

        wired_dims: dict[str, Any] = {}
        try:
            from dim_encoding.driver import (
                run_all as _run_encoding,
                _format_text as _fmt_encoding_text,
                _format_json as _fmt_encoding_json,
            )
        except ImportError as exc:
            print(
                f"error: failed to import encoding driver: {exc}",
                file=sys.stderr,
            )
            return 4

        def _drive_encoding() -> int:
            summary = _run_encoding()
            if args.format == "json":
                print(_fmt_encoding_json(summary))
            else:
                print(_fmt_encoding_text(summary, verbose=args.verbose))
            return 0 if summary.ok else 1

        wired_dims["encoding"] = _drive_encoding

        try:
            from dim_hash.driver import (
                run_all as _run_hash,
                _format_text as _fmt_hash_text,
                _format_json as _fmt_hash_json,
            )
        except ImportError as exc:
            print(
                f"error: failed to import hash driver: {exc}",
                file=sys.stderr,
            )
            return 4

        def _drive_hash() -> int:
            summary = _run_hash()
            if args.format == "json":
                print(_fmt_hash_json(summary))
            else:
                print(_fmt_hash_text(summary, verbose=args.verbose))
            return 0 if summary.ok else 1

        wired_dims["hash"] = _drive_hash

        selected = args.dim or list(wired_dims.keys())
        unknown = [d for d in selected if d not in wired_dims]
        if unknown:
            print(
                f"error: unknown / not-yet-wired dimension(s): {unknown}; "
                f"available: {list(wired_dims.keys())}",
                file=sys.stderr,
            )
            return 2

        rc = 0
        for dim in selected:
            print(f"\n=== dimension: {dim} ===")
            rc = max(rc, wired_dims[dim]())
        return rc

    out = (
        render_json(spec, combos)
        if args.format == "json"
        else render_text(spec, combos)
    )
    print(out)

    threshold = spec.get("acceptance_min_combinations", 24)
    if isinstance(threshold, int) and len(combos) < threshold:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
