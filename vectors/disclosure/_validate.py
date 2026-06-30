#!/usr/bin/env python3
# ======================================================================
#  vectors/disclosure/_validate.py
#  ----------------------------------------------------------------------
#  Suite-level validator for the DISCLOSURE test-vector set.
#
#  Checks per task 3.10 acceptance criteria:
#    1. Every vector contains expected.outcome ∈ {accepted, E_PROTOCOL,
#       ego-deviation-revoke}.
#    2. Each Disconnected-period DISCLOSURE that should be `accepted`
#       carries a non-empty endorsement_id, and that endorsement_id is
#       independently verifiable against context.endorsement_id.
#    3. CBOR <-> JSON structural equivalence (after b64u-decoding bytes).
#    4. CBOR is canonical (round-trips byte-for-byte).
#    5. Suite covers cases a-f and has ≥10 vectors.
# ======================================================================

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import cbor2

ROOT = Path(__file__).resolve().parent

ALLOWED_OUTCOMES = {"accepted", "E_PROTOCOL", "ego-deviation-revoke"}


def _b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _bytes_back(value: Any) -> Any:
    """Inverse of to_json_safe in _gen.py."""
    if isinstance(value, dict):
        if set(value.keys()) == {"$b64u"}:
            return _b64u_decode(value["$b64u"])
        return {k: _bytes_back(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_bytes_back(v) for v in value]
    return value


def _normalise_for_compare(value: Any) -> Any:
    """Normalise CBOR-decoded structures for comparison.

    cbor2 decodes a tag-0 string back into a datetime; we'd rather keep
    everything as plain JSON-serialisable scalars when comparing, so we
    stringify datetimes here.
    """
    import datetime

    if isinstance(value, datetime.datetime):
        # cbor2 attaches tzinfo for tag 0; emit RFC 3339 with Z suffix.
        return value.strftime("%Y-%m-%dT%H:%M:%SZ")
    if isinstance(value, dict):
        return {k: _normalise_for_compare(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalise_for_compare(v) for v in value]
    return value


def load_vector(folder: Path) -> Dict[str, Any]:
    return {
        "id": folder.name,
        "cbor": (folder / "disclosure.cbor").read_bytes(),
        "json": json.loads((folder / "disclosure.json").read_text(encoding="utf-8")),
        "context": json.loads(
            (folder / "context.json").read_text(encoding="utf-8")
        ),
        "expected": json.loads(
            (folder / "expected.json").read_text(encoding="utf-8")
        ),
    }


def check_outcome(v: Dict[str, Any]) -> Tuple[bool, str]:
    outcome = v["expected"].get("outcome")
    if outcome not in ALLOWED_OUTCOMES:
        return False, f"outcome={outcome!r} not in {sorted(ALLOWED_OUTCOMES)}"
    return True, "outcome ok"


def check_cbor_canonical(v: Dict[str, Any]) -> Tuple[bool, str]:
    decoded = cbor2.loads(v["cbor"])
    re_encoded = cbor2.dumps(decoded, canonical=True)
    if re_encoded != v["cbor"]:
        return False, "non-canonical CBOR (re-encode mismatch)"
    return True, "cbor canonical"


def check_cbor_json_equiv(v: Dict[str, Any]) -> Tuple[bool, str]:
    cbor_decoded = _normalise_for_compare(cbor2.loads(v["cbor"]))
    json_decoded = _normalise_for_compare(_bytes_back(v["json"]))
    if cbor_decoded != json_decoded:
        return False, "CBOR/JSON structural mismatch"
    return True, "cbor/json equivalent"


def check_disconnected_endorsement_id(v: Dict[str, Any]) -> Tuple[bool, str]:
    """Acceptance: Disconnected-period DISCLOSURE has endorsement_id and
    that id is independently verifiable against the context."""
    ctx = v["context"]["context"]
    if not ctx.get("is_disconnected"):
        return True, "n/a (not disconnected)"

    cbor = cbor2.loads(v["cbor"])
    claims = cbor["claims"]
    msg_endorsement_id = claims.get("endorsement-id")
    expected_outcome = v["expected"]["outcome"]

    if expected_outcome == "accepted":
        if not msg_endorsement_id:
            return False, "Disconnected+accepted but missing endorsement-id"
        ctx_endorsement_id = ctx.get("endorsement_id")
        if msg_endorsement_id != ctx_endorsement_id:
            return False, (
                f"endorsement-id mismatch: msg={msg_endorsement_id!r} "
                f"ctx={ctx_endorsement_id!r}"
            )
        return True, f"endorsement-id verifiable: {msg_endorsement_id}"

    # Negative-disconnected vectors: outcome must explain the rejection.
    if expected_outcome == "E_PROTOCOL":
        # Either missing entirely, or refers to a non-existent endorsement.
        if msg_endorsement_id is None:
            return True, "Disconnected+E_PROTOCOL: endorsement-id missing as expected"
        if msg_endorsement_id != ctx.get("endorsement_id"):
            return True, (
                "Disconnected+E_PROTOCOL: endorsement-id present but does not "
                "resolve against context (independently detectable)"
            )
    return True, "disconnected vector ok"


def check_case_coverage(vectors: List[Dict[str, Any]]) -> Tuple[bool, str]:
    cases = {v["expected"]["case"] for v in vectors}
    required = {"a", "b", "c", "d", "e", "f"}
    missing = required - cases
    if missing:
        return False, f"missing cases: {sorted(missing)}"
    return True, f"case coverage: {sorted(cases)}"


def check_min_count(vectors: List[Dict[str, Any]]) -> Tuple[bool, str]:
    if len(vectors) < 10:
        return False, f"only {len(vectors)} vectors (<10)"
    return True, f"{len(vectors)} vectors"


def check_index_alignment(vectors: List[Dict[str, Any]]) -> Tuple[bool, str]:
    idx = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    idx_ids = {e["id"] for e in idx["vectors"]}
    folder_ids = {v["id"] for v in vectors}
    if idx_ids != folder_ids:
        return False, (
            f"index.json out of sync: only-in-index={idx_ids - folder_ids}, "
            f"only-on-disk={folder_ids - idx_ids}"
        )
    return True, "index.json aligned"


def main() -> int:
    folders = sorted(p for p in ROOT.iterdir() if p.is_dir())
    vectors = [load_vector(f) for f in folders]
    if not vectors:
        print("no vectors found", file=sys.stderr)
        return 1

    failures = 0

    suite_checks = [
        ("case-coverage", lambda: check_case_coverage(vectors)),
        ("min-count", lambda: check_min_count(vectors)),
        ("index-alignment", lambda: check_index_alignment(vectors)),
    ]

    print("== suite-level checks ==")
    for name, fn in suite_checks:
        ok, msg = fn()
        marker = "✓" if ok else "✗"
        print(f"  [{marker}] {name}: {msg}")
        failures += 0 if ok else 1

    per_vector_checks = [
        ("outcome", check_outcome),
        ("cbor-canonical", check_cbor_canonical),
        ("cbor-json-equiv", check_cbor_json_equiv),
        ("disconnected-endorsement", check_disconnected_endorsement_id),
    ]

    print("\n== per-vector checks ==")
    for v in vectors:
        all_ok = True
        details = []
        for name, fn in per_vector_checks:
            ok, msg = fn(v)
            details.append((name, ok, msg))
            if not ok:
                all_ok = False
                failures += 1
        marker = "✓" if all_ok else "✗"
        print(f"  [{marker}] {v['id']}")
        for name, ok, msg in details:
            sub = "✓" if ok else "✗"
            print(f"        [{sub}] {name}: {msg}")

    print()
    if failures == 0:
        print(f"OK: all checks passed across {len(vectors)} vectors")
        return 0
    print(f"FAIL: {failures} check(s) failed", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
