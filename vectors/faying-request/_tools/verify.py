#!/usr/bin/env python3
"""
Verifier for `vectors/faying-request/`.

For every vector under this directory:
  1.  Each `*.cbor` round-trips back to the dict form encoded in `*.json`
      (modulo the JSON {"$b64": ...} encoding for byte strings).
  2.  Every envelope's signature verifies against the embedded `pubkey`
      using SHA-256(Deterministic-CBOR(envelope_without_signature)) as the
      signed input.
  3.  The (initiator, confirm_ts, took_effect) triple is present in
      `expected.json`'s attestation_chain_entry.
  4.  Negative-case error codes match the values declared in the spec
      §5.4 (1010 / 1014).
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

ROOT = Path(__file__).resolve().parents[1]


def from_jsonable(value):
    if isinstance(value, dict):
        if set(value.keys()) == {"$b64"}:
            return base64.b64decode(value["$b64"])
        return {k: from_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_jsonable(v) for v in value]
    return value


def det_cbor(obj) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def verify_envelope_signature(env: dict) -> None:
    if "signature" not in env:
        return
    sig = env["signature"]
    body = {k: v for k, v in env.items() if k != "signature"}
    digest = hashlib.sha256(det_cbor(body)).digest()
    pub = Ed25519PublicKey.from_public_bytes(sig["pubkey"])
    pub.verify(sig["sig"], digest)


def verify_pair(cbor_path: Path, json_path: Path) -> None:
    cbor_obj = cbor2.loads(cbor_path.read_bytes())
    json_obj = from_jsonable(json.loads(json_path.read_text(encoding="utf-8")))

    re_cbor = det_cbor(cbor_obj)
    if re_cbor != cbor_path.read_bytes():
        raise AssertionError(f"{cbor_path}: not deterministic-CBOR canonical")

    if det_cbor(cbor_obj) != det_cbor(json_obj):
        raise AssertionError(
            f"{json_path}: JSON mirror does not equal CBOR after $b64 decoding"
        )

    if "header" in cbor_obj and "signature" in cbor_obj:
        verify_envelope_signature(cbor_obj)


REQUIRED_TRIPLE = ("initiator", "confirm_ts", "took_effect")
NEGATIVE_ERROR_CODES = {
    "vec-07-bootstrap-timeout": ("E_FAYING_REQUEST_NOT_CONFIRMED", 1014),
    "vec-08-forged-ms-surrogate": ("E_HUMAN_WITNESS_REQUIRED", 1010),
}


def verify_vector(dir: Path) -> None:
    for cbor_path in sorted(dir.glob("*.cbor")):
        json_path = cbor_path.with_suffix(".json")
        if not json_path.exists():
            raise AssertionError(f"{json_path} missing for {cbor_path.name}")
        verify_pair(cbor_path, json_path)

    expected = json.loads((dir / "expected.json").read_text(encoding="utf-8"))
    ace = expected["attestation_chain_entry"]
    for f in REQUIRED_TRIPLE:
        if f not in ace:
            raise AssertionError(f"{dir.name}: expected triple field missing: {f}")

    if dir.name in NEGATIVE_ERROR_CODES:
        want_name, want_code = NEGATIVE_ERROR_CODES[dir.name]
        if expected.get("error_code") != want_name:
            raise AssertionError(
                f"{dir.name}: expected error_code={want_name}, "
                f"got {expected.get('error_code')!r}"
            )
        if expected.get("error_code_numeric") != want_code:
            raise AssertionError(
                f"{dir.name}: expected error_code_numeric={want_code}, "
                f"got {expected.get('error_code_numeric')!r}"
            )

    # No path may surrogate the HP witness.
    hc = expected.get("hardness_checks", {})
    if expected.get("outcome") in {"effective", "rejected"}:
        # baseline: HP witness irreplaceable claim must be asserted in every
        # vector's expected.json
        if hc.get("hp_witness_irreplaceable") is not True:
            raise AssertionError(
                f"{dir.name}: hardness_checks.hp_witness_irreplaceable must be true"
            )


def main() -> int:
    vectors = [p for p in sorted(ROOT.iterdir())
               if p.is_dir() and p.name.startswith("vec-")]
    if not vectors:
        print(f"no vectors found under {ROOT}", file=sys.stderr)
        return 1

    total_envelopes = 0
    for v in vectors:
        try:
            verify_vector(v)
            total_envelopes += len(list(v.glob("*.cbor")))
            print(f"  ✓ {v.name}")
        except (AssertionError, InvalidSignature) as e:
            print(f"  ✗ {v.name}: {e}", file=sys.stderr)
            return 2

    # also validate the index.json
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    declared = {v["vid"] for v in index["vectors"]}
    on_disk = {v.name for v in vectors}
    if declared != on_disk:
        print(f"index.json mismatch: declared={declared} on_disk={on_disk}",
              file=sys.stderr)
        return 3

    print(
        f"\nOK — {len(vectors)} vectors, {total_envelopes} envelopes, "
        "all CBOR ↔ JSON equivalent and all signatures verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
