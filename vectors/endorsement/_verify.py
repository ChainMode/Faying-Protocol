#!/usr/bin/env python3
# =============================================================================
#  Self-check: verify every emitted vector against its stated outcome.
#
#  Loads `mandate.cbor` and `expected.json` from each vector directory, then:
#    - recomputes Deterministic-CBOR(Mandate_without_signature) and SHA-256
#    - asserts the recomputed hash hex equals expected.signature_input.hash_hex
#    - asserts the recomputed Det-CBOR hex equals expected.signature_input.det_cbor_hex
#    - if outcome == "accepted": signature MUST verify (Ed25519)
#    - if vector category starts with "(e)": signature MUST fail to verify
#      (post-signing tampering invariant for P16.1)
#    - asserts endorsement_field_hash_hex == SHA-256(Det-CBOR(endorsement)) when
#      `endorsement_in_signature` is true
#
#  Run from repo root: python3 vectors/endorsement/_verify.py
# =============================================================================

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

ROOT = Path(__file__).resolve().parent


def det_cbor(obj: Any) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(vector_dir: Path) -> Dict[str, Any]:
    expected = json.loads((vector_dir / "expected.json").read_text())
    mandate_cbor = (vector_dir / "mandate.cbor").read_bytes()
    mandate = cbor2.loads(mandate_cbor)

    # Top-level invariants
    assert "signature" in mandate, "top-level signature missing"

    body = {k: v for k, v in mandate.items() if k != "signature"}
    det = det_cbor(body)
    body_hash_hex = sha256(det)

    # The on-disk det-CBOR / hash MUST match `wire_*` fields. The
    # `signature_input.{det_cbor_hex,hash_hex}` fields document what the
    # signature was actually computed over. For non-tampered vectors the
    # two coincide; for (e) post-sign tamper they diverge — that gap is the
    # P16.1 invariant violation we are exercising.
    assert det.hex() == expected["signature_input"]["wire_det_cbor_hex"], (
        f"wire_det_cbor_hex mismatch in {vector_dir.name}"
    )
    assert body_hash_hex == expected["signature_input"]["wire_hash_hex"], (
        f"wire_hash_hex mismatch in {vector_dir.name}"
    )
    if expected["signature_input"]["wire_matches_signature_input"]:
        assert det.hex() == expected["signature_input"]["det_cbor_hex"]
        assert body_hash_hex == expected["signature_input"]["hash_hex"]
    else:
        # (e) tamper case: wire MUST diverge from signed input.
        assert det.hex() != expected["signature_input"]["det_cbor_hex"]
        assert body_hash_hex != expected["signature_input"]["hash_hex"]

    # Endorsement-field-hash invariant (P16.1) — computed over the
    # *signature-input* endorsement subtree, which for non-tampered vectors
    # equals the wire endorsement subtree.
    if expected["signature_input"]["endorsement_in_signature"]:
        assert "endorsement" in body, "endorsement_in_signature claimed but absent"
        wire_endorsement_hash = sha256(det_cbor(body["endorsement"]))
        if expected["signature_input"]["wire_matches_signature_input"]:
            assert (
                wire_endorsement_hash
                == expected["signature_input"]["endorsement_field_hash_hex"]
            ), f"endorsement_field_hash mismatch in {vector_dir.name}"
        else:
            # (e) tamper case: the on-wire endorsement hash necessarily
            # differs from the signed-input endorsement hash, since the
            # tampered field lives inside endorsement. The expected
            # endorsement_field_hash_hex documents the *signed* (legitimate)
            # subtree.
            assert (
                wire_endorsement_hash
                != expected["signature_input"]["endorsement_field_hash_hex"]
            ), (
                f"{vector_dir.name}: tampered vector should have wire "
                "endorsement hash differ from signed-input endorsement hash"
            )

    # Signature verification semantics
    sig_bundle = mandate["signature"]
    pubkey = ed25519.Ed25519PublicKey.from_public_bytes(sig_bundle["pubkey"])
    digest = hashlib.sha256(det).digest()

    sig_ok: bool
    try:
        pubkey.verify(sig_bundle["sig"], digest)
        sig_ok = True
    except InvalidSignature:
        sig_ok = False

    category = expected["category"]
    outcome = expected["outcome"]
    error_code = expected.get("error_code")

    if outcome == "accepted":
        assert sig_ok, (
            f"{vector_dir.name}: outcome=accepted but signature verification "
            "failed"
        )
        assert error_code is None
    else:
        # rejected — diagnose by category
        if category.startswith("(e)"):
            # post-sign tamper → signature MUST fail; error_code MUST be 1007
            assert not sig_ok, (
                f"{vector_dir.name}: category (e) post-sign tamper, "
                "expected signature to fail, but it verified"
            )
            assert error_code == 1007
        else:
            # MS-level structural rejections — signature itself MAY still
            # verify; but error_code MUST be 1013
            assert error_code == 1013

    return {
        "vector_id": expected["vector_id"],
        "category": category,
        "outcome": outcome,
        "error_code": error_code,
        "sig_verified": sig_ok,
        "det_cbor_len": len(det),
    }


def main() -> int:
    rc = 0
    rows = []
    for child in sorted(ROOT.iterdir()):
        if child.is_dir() and (child / "expected.json").exists():
            try:
                rows.append(verify(child))
            except AssertionError as exc:
                rows.append({"vector_id": child.name, "error": str(exc)})
                rc = 1

    width = max(len(r.get("vector_id", "")) for r in rows)
    for r in rows:
        if "error" in r:
            print(f"  ✗ {r['vector_id']:<{width}}  {r['error']}")
        else:
            tag = "✓"
            cat = r["category"][:3]
            sig = "sig=ok" if r["sig_verified"] else "sig=FAIL"
            ec = r["error_code"] or "-"
            print(
                f"  {tag} {r['vector_id']:<{width}}  cat={cat}  "
                f"outcome={r['outcome']:<8}  ec={ec!s:<5}  {sig}  "
                f"det_cbor={r['det_cbor_len']}B"
            )

    print(f"\n{len(rows)} vectors checked.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
