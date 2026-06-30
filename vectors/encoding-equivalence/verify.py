#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faying Protocol/1.0 — Encoding Equivalence Verifier
====================================================

Independent re-verifier for the vectors in this directory. Reads the on-disk
artefacts (no regeneration) and re-asserts every claim in `expected.json`
plus the headline acceptance criteria of task 3.7:

  1. CBOR & JSON deserialize to semantically equal objects.
  2. The Deterministic-CBOR signature input is bit-for-bit identical when
     derived from either encoding.
  3. The signature-input SHA-256 hash matches `expected.json`.
  4. Ed25519 signature verification on the Det-CBOR input succeeds.

Exits 0 on full success; non-zero with a printed summary on failure.

Run:
    python3 vectors/encoding-equivalence/verify.py
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.exceptions import InvalidSignature

ROOT = Path(__file__).resolve().parent


def b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def from_json_shape(obj: Any, path: tuple[str, ...], binary_paths: set[tuple[str, ...]]) -> Any:
    if isinstance(obj, dict):
        return {k: from_json_shape(v, path + (k,), binary_paths) for k, v in obj.items()}
    if isinstance(obj, list):
        return [from_json_shape(v, path, binary_paths) for v in obj]
    if path in binary_paths and isinstance(obj, str):
        return b64u_decode(obj)
    return obj


def verify_one(vector_dir: Path) -> list[str]:
    """Return list of failure messages (empty list = all pass)."""
    failures: list[str] = []
    expected = json.loads((vector_dir / "expected.json").read_text())

    # Reconstruct binary path set
    binary_paths: set[tuple[str, ...]] = {
        tuple(p.split(".")) for p in expected["binary_field_paths"]
    }

    # Load both encodings
    cbor_bytes = (vector_dir / "message.cbor").read_bytes()
    cbor_obj = cbor2.loads(cbor_bytes)

    json_text = (vector_dir / "message.json").read_text()
    json_obj_raw = json.loads(json_text)
    json_obj = from_json_shape(json_obj_raw, (), binary_paths)

    # 1. Semantic equality
    if cbor_obj != json_obj:
        failures.append(f"[{vector_dir.name}] CBOR ≠ JSON (semantic)")

    # 2. Strip signature, re-canonicalize, compare to stored Det-CBOR input
    cbor_no_sig = {k: v for k, v in cbor_obj.items() if k != "signature"}
    json_no_sig = {k: v for k, v in json_obj.items() if k != "signature"}

    sig_in_cbor = cbor2.dumps(cbor_no_sig, canonical=True)
    sig_in_json = cbor2.dumps(json_no_sig, canonical=True)

    stored_det_cbor_hex = (vector_dir / "signature.input.det-cbor.hex").read_text().strip()
    stored_det_cbor = bytes.fromhex(stored_det_cbor_hex)

    if sig_in_cbor != stored_det_cbor:
        failures.append(f"[{vector_dir.name}] Det-CBOR(envelope_no_sig) from CBOR ≠ stored")
    if sig_in_json != stored_det_cbor:
        failures.append(f"[{vector_dir.name}] Det-CBOR(envelope_no_sig) from JSON ≠ stored")
    if sig_in_cbor != sig_in_json:
        failures.append(f"[{vector_dir.name}] Det-CBOR mismatch CBOR vs JSON paths")

    # 3. Hash check
    expected_hash = expected["signature_input"]["hash_hex"]
    actual_hash = hashlib.sha256(stored_det_cbor).hexdigest()
    stored_hash_file = (vector_dir / "signature.input.hash.hex").read_text().strip()
    if actual_hash != expected_hash:
        failures.append(
            f"[{vector_dir.name}] SHA-256(det-cbor) {actual_hash} ≠ expected {expected_hash}"
        )
    if stored_hash_file != expected_hash:
        failures.append(
            f"[{vector_dir.name}] hash file {stored_hash_file} ≠ expected.json {expected_hash}"
        )

    # 4. Ed25519 signature verification — must succeed identically when
    #    presented with the Det-CBOR input derived from either encoding.
    pubkey_hex = expected["signature"]["pubkey_hex"]
    sig_hex = expected["signature"]["sig_hex"]
    pub = Ed25519PublicKey.from_public_bytes(bytes.fromhex(pubkey_hex))
    sig_bytes = bytes.fromhex(sig_hex)

    cbor_verify_ok = True
    json_verify_ok = True
    try:
        pub.verify(sig_bytes, sig_in_cbor)
    except InvalidSignature:
        cbor_verify_ok = False
    try:
        pub.verify(sig_bytes, sig_in_json)
    except InvalidSignature:
        json_verify_ok = False
    if not cbor_verify_ok:
        failures.append(f"[{vector_dir.name}] Ed25519 verify FAILED for CBOR-derived input")
    if not json_verify_ok:
        failures.append(f"[{vector_dir.name}] Ed25519 verify FAILED for JSON-derived input")
    if cbor_verify_ok != json_verify_ok:
        failures.append(
            f"[{vector_dir.name}] verification result differs across encodings"
        )

    return failures


def main() -> int:
    index = json.loads((ROOT / "index.json").read_text())
    vectors = index["vectors"]
    print(f"Verifying {len(vectors)} vector(s) in {ROOT.name}/ ...")

    all_failures: list[str] = []
    for entry in vectors:
        vd = ROOT / entry["id"]
        fails = verify_one(vd)
        status = "PASS" if not fails else "FAIL"
        print(f"  [{status}] {entry['id']}  ({entry['msg_type']})")
        all_failures.extend(fails)

    if all_failures:
        print("\nFailures:")
        for f in all_failures:
            print(f"  - {f}")
        return 1
    print("\nAll equivalence assertions hold:")
    print("  • CBOR & JSON decode to semantically equal objects")
    print("  • Det-CBOR(envelope_without_signature) is identical across encodings")
    print("  • SHA-256(signature_input) matches expected.json")
    print("  • Ed25519 verification yields the same outcome from both encodings")
    return 0


if __name__ == "__main__":
    sys.exit(main())
