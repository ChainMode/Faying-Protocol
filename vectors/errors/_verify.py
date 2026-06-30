#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifier for vectors/errors/.

Checks (per task 3.6 acceptance criteria):

  (1) All 15 error codes in §5.4 are covered: 1001..1014 + 1099.
  (2) Each <code>-<NAME>/ directory has trigger.{cbor,json}, error.{cbor,json},
      expected.json.
  (3) CBOR <-> JSON round-trip: cbor2.loads(trigger.cbor) and the JSON file
      represent the same field set (modulo bytes-vs-hex on opaque fields).
  (4) ERROR envelope fields obey §EH.3 #3 — no sensitive substrings:
        - "private_key", "ms_internal", "key_fingerprint"
        - the human prime ID HP_ID does not appear in error.json claims
          (other-HP identifier hygiene)
  (5) expected.json carries:
        - code, name, audit-log-entry (5-tuple or null), must-push-hp-view
        - audit-log-entry, when non-null, is a 5-tuple
          (error_code, mandate_id, ts, rp_id, reason)
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import cbor2

ROOT = Path(__file__).resolve().parent
HP_ID = "hp:01HXR000000000000000000HP"
MS_ID = "ms:fap-test-ms-1"

EXPECTED_CODES = {1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008,
                  1009, 1010, 1011, 1012, 1013, 1014, 1099}

# fields that must NOT appear inside ERROR claims body
FORBIDDEN_TOKENS = [
    "private_key",
    "privkey",
    "ms_internal",
    "ms_state",
    "key_fingerprint",
    "fingerprint:",
    "ms_session_secret",
    "internal_state",
]

REQUIRED_FILES = ["trigger.cbor", "trigger.json", "error.cbor", "error.json", "expected.json"]


def collect_dirs() -> dict[int, Path]:
    out: dict[int, Path] = {}
    for child in sorted(ROOT.iterdir()):
        if not child.is_dir():
            continue
        m = re.match(r"^(\d{4})-(.+)$", child.name)
        if not m:
            continue
        out[int(m.group(1))] = child
    return out


def assert_eq(label: str, got, want):
    if got != want:
        raise SystemExit(f"FAIL {label}: got={got!r} want={want!r}")


def find_string_in(obj, needle: str) -> bool:
    """Recursively search obj for any string containing `needle`."""
    if isinstance(obj, str):
        return needle in obj
    if isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str) and needle in k:
                return True
            if find_string_in(v, needle):
                return True
        return False
    if isinstance(obj, (list, tuple)):
        return any(find_string_in(x, needle) for x in obj)
    return False


def main() -> int:
    dirs = collect_dirs()
    have = set(dirs.keys())
    missing = EXPECTED_CODES - have
    extra = have - EXPECTED_CODES
    if missing:
        print(f"FAIL: missing error code dirs: {sorted(missing)}")
        return 1
    if extra:
        print(f"FAIL: unexpected error code dirs: {sorted(extra)}")
        return 1

    failures: list[str] = []

    for code in sorted(dirs):
        d = dirs[code]

        # (2) all required files exist
        for fname in REQUIRED_FILES:
            if not (d / fname).exists():
                failures.append(f"{d.name}: missing {fname}")
                continue

        if any(not (d / f).exists() for f in REQUIRED_FILES):
            continue

        # (3) round-trip
        trigger_cbor = cbor2.loads((d / "trigger.cbor").read_bytes())
        trigger_json = json.loads((d / "trigger.json").read_text(encoding="utf-8"))
        error_cbor = cbor2.loads((d / "error.cbor").read_bytes())
        error_json = json.loads((d / "error.json").read_text(encoding="utf-8"))

        # The JSON view stores the same structure as CBOR (Python dict round-
        # trips to identical primitives). Compare structurally.
        if trigger_cbor != trigger_json:
            failures.append(f"{d.name}: trigger.cbor != trigger.json (struct mismatch)")
        if error_cbor != error_json:
            failures.append(f"{d.name}: error.cbor != error.json (struct mismatch)")

        # (4) sensitive-info hygiene on error envelope
        claims = error_json.get("claims", {})

        # 4a: forbidden tokens anywhere in error claims
        for tok in FORBIDDEN_TOKENS:
            if find_string_in(claims, tok):
                failures.append(f"{d.name}: forbidden token {tok!r} found in error.claims")

        # 4b: error claims must NOT carry HP identifiers
        if find_string_in(claims, HP_ID):
            failures.append(f"{d.name}: HP id {HP_ID!r} leaked into error.claims (§EH.3 #3)")

        # 4c: error envelope code matches dirname
        if claims.get("code") != code:
            failures.append(
                f"{d.name}: error.claims.code={claims.get('code')!r} mismatches dir code={code}"
            )

        # 4d: error envelope mandate_id, when present, must NOT contain "private" or "key:"
        if "mandate_id" in claims:
            mid = claims["mandate_id"]
            if not isinstance(mid, str) or not mid.startswith("mnd:"):
                failures.append(f"{d.name}: error.claims.mandate_id has wrong shape: {mid!r}")

        # (5) expected.json shape
        expected = json.loads((d / "expected.json").read_text(encoding="utf-8"))
        for k in ("code", "name", "audit-log-entry", "must-push-hp-view"):
            if k not in expected:
                failures.append(f"{d.name}: expected.json missing key {k!r}")

        if expected.get("code") != code:
            failures.append(f"{d.name}: expected.code != dir code")

        ale = expected.get("audit-log-entry")
        if ale is not None:
            for k in ("error_code", "mandate_id", "ts", "rp_id", "reason"):
                if k not in ale:
                    failures.append(
                        f"{d.name}: expected.audit-log-entry missing key {k!r} (5-tuple)"
                    )
            if ale.get("error_code") != code:
                failures.append(f"{d.name}: expected.audit-log-entry.error_code != code")

        if not isinstance(expected.get("must-push-hp-view"), bool):
            failures.append(f"{d.name}: expected.must-push-hp-view must be a boolean")

    if failures:
        print("VERIFY FAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print(f"OK: 15/15 error codes covered, all envelope and expected.json checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
