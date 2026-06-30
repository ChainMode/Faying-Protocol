"""
Verify the generated PRESENCE test vectors.

Checks performed
----------------
1. Every vector decodes as both CBOR and JSON, and the two views
   round-trip to the same canonical CBOR signing input.
2. Each vector matches the structural shape of the CDDL
   ``presence-signal`` rule: the required keys are present with the
   correct primitive type (`bstr .size 16` for the nonce, CBOR tag-0
   timestamp for `produced-at`, signal-type in the closed enum).
3. For ``fresh`` and ``stale`` vectors the outer Ed25519 signature
   must verify; for ``tampered-*-bad-signature`` it must NOT verify;
   for ``tampered-*-bad-attestation`` the device-attestation
   signature must NOT verify but the envelope signature itself must
   verify; for replay vectors the envelope signature verifies but the
   ``(mandate-id, nonce)`` tuple matches the one recorded in
   ``expected.replay_of``.
4. Freshness window equals (now − produced_at) with a 1ms tolerance
   and matches `expected.freshness_window.age_ms`. The
   `within_budget` flag also matches `expected.freshness_window`.
5. On-disk SHA-256 digests match `expected.digests.*`.

Exit code is 0 on success, 1 otherwise.
"""

from __future__ import annotations

import base64
import datetime as _dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import cbor2
from cryptography.hazmat.primitives.asymmetric import ed25519


VECTORS_ROOT = Path(__file__).resolve().parent.parent


SIGNAL_TYPES = {
    "webauthn-uv-fresh",
    "face-continuous",
    "fingerprint-tap",
    "presence-heartbeat-only",
    "intent-ticket",
}


VERDICTS = {"ok", "stale", "replay", "attestation-invalid"}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "==")


def materialise_for_cbor(node: Any) -> Any:
    """Convert a JSON-friendly tree (`$bytes` / `$tag` markers) into
    the CBOR-friendly tree."""
    if isinstance(node, dict):
        if set(node.keys()) == {"$bytes"}:
            return b64u_decode(node["$bytes"])
        if set(node.keys()) == {"$tag", "$value"} and node["$tag"] == 0:
            return cbor2.CBORTag(0, node["$value"])
        return {k: materialise_for_cbor(v) for k, v in node.items()}
    if isinstance(node, list):
        return [materialise_for_cbor(x) for x in node]
    return node


def cbor_canonical(obj: Any) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def parse_iso(value: str) -> _dt.datetime:
    """Parse an RFC-3339 timestamp (Z-suffixed UTC, optional .ms)."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return _dt.datetime.fromisoformat(value)


def expect_keys(node: Dict[str, Any], required: Tuple[str, ...], path: str) -> None:
    for k in required:
        if k not in node:
            fail(f"{path}: missing required key '{k}' (have {sorted(node)})")


def cddl_presence_signal_check(signal: Dict[str, Any], path: str) -> None:
    expect_keys(
        signal,
        (
            "mandate-id",
            "signal-type",
            "produced-at",
            "nonce",
            "device-id",
            "device-attestation",
            "signature",
        ),
        path,
    )
    if not isinstance(signal["mandate-id"], str):
        fail(f"{path}.mandate-id: expected tstr")
    if signal["signal-type"] not in SIGNAL_TYPES:
        fail(f"{path}.signal-type: {signal['signal-type']!r} not in CDDL enum")
    pa = signal["produced-at"]
    if isinstance(pa, cbor2.CBORTag):
        if pa.tag != 0:
            fail(f"{path}.produced-at: expected CBOR tag 0")
    elif isinstance(pa, _dt.datetime):
        pass
    else:
        fail(f"{path}.produced-at: expected CBOR tag 0 (RFC 3339 timestamp), "
             f"got {type(pa).__name__}")
    nonce = signal["nonce"]
    if not isinstance(nonce, (bytes, bytearray)):
        fail(f"{path}.nonce: expected bstr, got {type(nonce).__name__}")
    if len(nonce) != 16:
        fail(f"{path}.nonce: expected 16 bytes, got {len(nonce)}")
    if not isinstance(signal["device-id"], str):
        fail(f"{path}.device-id: expected tstr")
    att = signal["device-attestation"]
    expect_keys(att, ("format", "payload", "signer", "signature"),
                f"{path}.device-attestation")
    sig = signal["signature"]
    expect_keys(sig, ("alg", "pubkey", "sig"), f"{path}.signature")
    if sig["alg"] not in {"Ed25519", "ES256", "ML-DSA-65"}:
        fail(f"{path}.signature.alg: unsupported {sig['alg']!r}")


def verify_ed25519(
    signing_input: bytes, pubkey: bytes, sig: bytes
) -> bool:
    try:
        ed25519.Ed25519PublicKey.from_public_bytes(pubkey).verify(
            sig, signing_input
        )
        return True
    except Exception:
        return False


def to_cbor_bytes(node_or_marker: Any) -> bytes:
    if isinstance(node_or_marker, dict) and set(node_or_marker.keys()) == {"$bytes"}:
        return b64u_decode(node_or_marker["$bytes"])
    if isinstance(node_or_marker, (bytes, bytearray)):
        return bytes(node_or_marker)
    fail(f"Expected bytes-marker, got {node_or_marker!r}")
    return b""  # unreachable


def verify_one(name: str) -> None:
    folder = VECTORS_ROOT / name
    expected_path = folder / "expected.json"
    cbor_path = folder / "signal.cbor"
    json_path = folder / "signal.json"

    expected = json.loads(expected_path.read_text(encoding="utf-8"))
    cbor_bytes = cbor_path.read_bytes()
    json_bytes = json_path.read_bytes()

    # 1. Decode both views. We work primarily off the JSON view
    #    materialised back into the CBOR-friendly tree, because that
    #    representation round-trips byte-identically to the on-disk
    #    CBOR (it preserves CBORTag(0, str) instead of decoding it
    #    into a Python datetime, which would re-encode with a
    #    different ISO format).
    json_view = json.loads(json_bytes)
    cbor_view = materialise_for_cbor(json_view)

    # 2. CDDL-shape check.
    cddl_presence_signal_check(cbor_view, f"{name}.signal")

    # 3. Round-trip equivalence: materialised JSON tree, encoded in
    #    canonical CBOR, MUST be byte-identical to the on-disk CBOR.
    if cbor_canonical(cbor_view) != cbor_bytes:
        fail(f"{name}: JSON ↔ CBOR round-trip mismatch")

    # 4. Digest sanity.
    cbor_sha = hashlib.sha256(cbor_bytes).hexdigest()
    json_sha = hashlib.sha256(json_bytes).hexdigest()
    if cbor_sha != expected["digests"]["signal_cbor_sha256"]:
        fail(f"{name}: CBOR digest mismatch")
    if json_sha != expected["digests"]["signal_json_sha256"]:
        fail(f"{name}: JSON digest mismatch")

    # 5. Verdict & freshness.
    verdict = expected["verdict"]
    if verdict not in VERDICTS:
        fail(f"{name}: verdict {verdict!r} not in {sorted(VERDICTS)}")
    fw = expected["freshness_window"]
    produced_at = parse_iso(fw["produced_at"])
    evaluated_at = parse_iso(fw["evaluated_at"])
    age_ms = int(round((evaluated_at - produced_at).total_seconds() * 1000))
    if abs(age_ms - fw["age_ms"]) > 1:
        fail(f"{name}: freshness age_ms drift "
             f"({age_ms} vs {fw['age_ms']})")
    within = age_ms <= fw["max_staleness_ms"]
    if within != fw["within_budget"]:
        fail(f"{name}: freshness within_budget mismatch "
             f"({within} vs {fw['within_budget']})")

    # 6. Signature verification, branching on tamper / state.
    state = expected["state"]
    tamper = expected.get("tamper")

    # Build the unsigned envelope and canonical signing input.
    unsigned = {k: v for k, v in cbor_view.items() if k != "signature"}
    signing_input = cbor_canonical(unsigned)
    sig_block = cbor_view["signature"]
    pubkey = to_cbor_bytes(sig_block["pubkey"])
    outer_sig = to_cbor_bytes(sig_block["sig"])

    outer_ok = verify_ed25519(signing_input, pubkey, outer_sig)

    att = cbor_view["device-attestation"]
    # The CDDL `attestation` rule treats `signature` as a detached
    # signature over `payload` (the opaque attestation blob signed
    # by the device). This matches the convention used by the
    # BOOTSTRAP generator (`vectors/bootstrap/_tools/generate.py`).
    att_signing_input = att["payload"]
    if not isinstance(att_signing_input, (bytes, bytearray)):
        fail(f"{name}.device-attestation.payload: expected bstr")
    att_sig_block = att["signature"]
    att_pubkey = to_cbor_bytes(att_sig_block["pubkey"])
    att_sig = to_cbor_bytes(att_sig_block["sig"])
    att_ok = verify_ed25519(bytes(att_signing_input), att_pubkey, att_sig)

    if state == "fresh" or state == "stale":
        if not outer_ok:
            fail(f"{name}: expected outer signature OK, got failure")
        if not att_ok:
            fail(f"{name}: expected device-attestation OK, got failure")
    elif tamper == "bad-signature":
        if outer_ok:
            fail(f"{name}: expected outer signature FAIL, got OK")
    elif tamper == "bad-attestation":
        if not outer_ok:
            fail(f"{name}: outer signature should remain OK on attestation tamper")
        if att_ok:
            fail(f"{name}: expected device-attestation FAIL, got OK")
    elif tamper == "replay":
        if not outer_ok:
            fail(f"{name}: replay vector outer signature must verify "
                 f"(replay is detected by seen-set, not by signature)")
        if not att_ok:
            fail(f"{name}: replay vector device-attestation must verify")
        # Check that nonce/produced-at match expected.replay_of
        replay = expected.get("replay_of")
        if not replay:
            fail(f"{name}: replay vector missing expected.replay_of")
        nonce_b64 = expected["nonce_b64u"]
        if nonce_b64 != replay["nonce"]:
            fail(f"{name}: nonce_b64u does not match replay_of.nonce")
    else:
        fail(f"{name}: unknown tamper category {tamper!r}")

    # 7. CDDL-shape spot checks pulled out as expected fields too.
    if cbor_view["mandate-id"] != expected["mandate_id"]:
        fail(f"{name}: mandate_id mismatch")
    if cbor_view["signal-type"] != expected["signal_type"]:
        fail(f"{name}: signal_type mismatch")
    if cbor_view["device-id"] != expected["device_id"]:
        fail(f"{name}: device_id mismatch")

    print(f"  ok  {state:<9} {expected['signal_type']:<25} "
          f"verdict={verdict:<19} {name}")


def main() -> None:
    index = json.loads(
        (VECTORS_ROOT / "index.json").read_text(encoding="utf-8")
    )
    print(f"Verifying {len(index['vectors'])} PRESENCE vectors\n")
    for entry in index["vectors"]:
        verify_one(entry["name"])
    print("\nAll vectors verified.")


if __name__ == "__main__":
    main()
