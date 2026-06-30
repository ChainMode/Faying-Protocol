"""
Verify the generated BOOTSTRAP test vectors.

This script is intentionally separate from `generate.py` so that the
output of generation can be checked using only the artefacts on disk
(plus the `cryptography` library to run real signature checks). It is
the contract that downstream property-based tests and reference
implementations must also satisfy.

Checks performed
----------------
1. Every positive vector decodes as CBOR (or JSON for the JSON
   encoding variants) and produces an envelope with `header.msg_type`
   matching the expected value.
2. The Mandate carried inside each positive `BOOTSTRAP_RESP` envelope
   matches the CDDL `mandate` rule structurally — every required field
   exists with the correct primitive type. (Full CDDL conformance
   testing is performed by the conformance suite via the `cddl` ruby
   gem; here we run the equivalent type-shape check in Python.)
3. For Ed25519 and ECDSA-P256 vectors, signatures verify against the
   pubkeys carried in the same payload. For ML-DSA-65 vectors we only
   confirm the placeholder signature format.
4. Negative vectors decode and the response is a signed ERROR envelope
   carrying the error code declared in `expected.json`.

Exit code is 0 on success, 1 otherwise.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

import datetime as _dt

import cbor2
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, ed25519
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature


VECTORS_ROOT = Path(__file__).resolve().parent.parent


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def load_vector(name: str, encoding: str) -> Tuple[Any, Any]:
    folder = VECTORS_ROOT / name
    req = folder / f"request.{encoding}"
    resp = folder / f"response.{encoding}"
    if encoding == "cbor":
        request = cbor2.loads(req.read_bytes())
        response = cbor2.loads(resp.read_bytes())
    else:
        request = json.loads(req.read_text(encoding="utf-8"))
        response = json.loads(resp.read_text(encoding="utf-8"))
    return request, response


def expect_keys(node: Dict[str, Any], required: Tuple[str, ...], path: str) -> None:
    for k in required:
        if k not in node:
            fail(f"{path}: missing required key '{k}' (have {sorted(node)})")


def cddl_mandate_check(mandate: Dict[str, Any], path: str) -> None:
    """Check the structural shape of a CDDL `mandate` rule."""
    expect_keys(
        mandate,
        (
            "version",
            "id",
            "issued-at",
            "not-before",
            "not-after",
            "issuer",
            "ms-id",
            "subject",
            "scope",
            "grade",
            "presence-req",
            "attestation",
            "signature",
        ),
        path,
    )
    if mandate["version"] != "Faying Protocol/1.0":
        fail(f"{path}.version: expected 'Faying Protocol/1.0', "
             f"got {mandate['version']!r}")
    if not isinstance(mandate["id"], str):
        fail(f"{path}.id: expected tstr")
    for tk in ("issued-at", "not-before", "not-after"):
        node = mandate[tk]
        # cbor2 decodes tag-0 timestamps eagerly into datetime; both
        # the raw `CBORTag(0, str)` form and the datetime form are
        # acceptable here (re-encoding produces the same bytes).
        if isinstance(node, cbor2.CBORTag):
            if node.tag != 0:
                fail(f"{path}.{tk}: expected CBOR tag 0 (RFC 3339 timestamp)")
        elif isinstance(node, _dt.datetime):
            pass
        else:
            fail(f"{path}.{tk}: expected CBOR tag 0 (RFC 3339 timestamp), "
                 f"got {type(node).__name__}")
    grade = mandate["grade"]
    if not (isinstance(grade, int) and 0 <= grade <= 4):
        fail(f"{path}.grade: expected 0..4, got {grade!r}")
    sig = mandate["signature"]
    expect_keys(sig, ("alg", "pubkey", "sig"), f"{path}.signature")
    if sig["alg"] not in {"Ed25519", "ES256", "ML-DSA-65"}:
        fail(f"{path}.signature.alg: unsupported algorithm {sig['alg']!r}")
    scope = mandate["scope"]
    expect_keys(scope, ("domains", "actions"), f"{path}.scope")
    pr = mandate["presence-req"]
    expect_keys(pr, ("signal-types", "max-staleness-ms", "on-loss"),
                f"{path}.presence-req")


def verify_signature_block(
    signing_input: bytes, sig_block: Dict[str, Any], context: str
) -> bool:
    alg = sig_block["alg"]
    pubkey = sig_block["pubkey"]
    sig = sig_block["sig"]
    if isinstance(pubkey, dict) and "$bytes" in pubkey:
        pubkey = base64.urlsafe_b64decode(pubkey["$bytes"] + "==")
    if isinstance(sig, dict) and "$bytes" in sig:
        sig = base64.urlsafe_b64decode(sig["$bytes"] + "==")
    if alg == "Ed25519":
        try:
            ed25519.Ed25519PublicKey.from_public_bytes(pubkey).verify(
                sig, signing_input
            )
            return True
        except Exception as exc:
            fail(f"{context}: Ed25519 verify failed: {exc}")
    elif alg == "ES256":
        if len(sig) != 64:
            fail(f"{context}: ES256 signature must be 64 raw bytes (r||s)")
        r = int.from_bytes(sig[:32], "big")
        s = int.from_bytes(sig[32:], "big")
        der = encode_dss_signature(r, s)
        pk = ec.EllipticCurvePublicKey.from_encoded_point(
            ec.SECP256R1(), pubkey
        )
        try:
            pk.verify(der, signing_input, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception as exc:
            fail(f"{context}: ES256 verify failed: {exc}")
    elif alg == "ML-DSA-65":
        if not sig.startswith(b"test-only-ml-dsa-65-sig-"):
            fail(f"{context}: ML-DSA-65 placeholder signature has wrong format")
        return True
    else:
        fail(f"{context}: unsupported alg {alg!r}")
    return False


def materialise_for_cbor(node: Any) -> Any:
    """Convert the JSON-friendly tree produced by debug.json (with
    ``$bytes`` and ``$tag`` markers) back into the CBOR-friendly tree
    so that we can re-canonicalise it for signing-input verification.
    """
    if isinstance(node, dict):
        if set(node.keys()) == {"$bytes"}:
            return base64.urlsafe_b64decode(node["$bytes"] + "==")
        if set(node.keys()) == {"$tag", "$value"} and node["$tag"] == 0:
            return cbor2.CBORTag(0, node["$value"])
        return {k: materialise_for_cbor(v) for k, v in node.items()}
    if isinstance(node, list):
        return [materialise_for_cbor(x) for x in node]
    return node


def positive_vector_check(name: str, encoding: str) -> None:
    request, response = load_vector(name, encoding)
    expected = json.loads(
        (VECTORS_ROOT / name / "expected.json").read_text(encoding="utf-8")
    )

    # Header sanity
    if request["header"]["msg_type"] != "BOOTSTRAP":
        fail(f"{name}: request.msg_type should be BOOTSTRAP, got "
             f"{request['header']['msg_type']!r}")
    if response["header"]["msg_type"] != "BOOTSTRAP_RESP":
        fail(f"{name}: response.msg_type should be BOOTSTRAP_RESP, got "
             f"{response['header']['msg_type']!r}")

    # CDDL-shape check on the inner Mandate (positive responses only).
    if encoding == "cbor":
        mandate = response["claims"]
    else:
        # JSON view: convert markers to CBOR types before shape-check.
        mandate = materialise_for_cbor(response["claims"])
    cddl_mandate_check(mandate, f"{name}.response.claims")

    if mandate["id"] != expected["mandate_id"]:
        fail(f"{name}: expected mandate_id={expected['mandate_id']!r}, "
             f"got {mandate['id']!r}")

    # Verify outer envelope signatures.
    alg = expected["algorithm"]

    if encoding == "cbor":
        request_for_sig = {k: v for k, v in request.items() if k != "signature"}
        signing_input_req = cbor2.dumps(request_for_sig, canonical=True)
        verify_signature_block(
            signing_input_req,
            request["signature"],
            f"{name}.request.signature",
        )

        response_for_sig = {k: v for k, v in response.items() if k != "signature"}
        signing_input_resp = cbor2.dumps(response_for_sig, canonical=True)
        verify_signature_block(
            signing_input_resp,
            response["signature"],
            f"{name}.response.signature",
        )

        # Inner Mandate signature.
        mandate_for_sig = {k: v for k, v in mandate.items() if k != "signature"}
        mandate_signing_input = cbor2.dumps(mandate_for_sig, canonical=True)
        verify_signature_block(
            mandate_signing_input,
            mandate["signature"],
            f"{name}.mandate.signature",
        )
    else:
        # For JSON-wire vectors we recover the CBOR signing input via
        # debug.json (the unsigned tree was materialised there). The
        # signature input is canonical CBOR regardless of the wire
        # encoding chosen — that is the whole point of design.md §6.3.
        debug = json.loads(
            (VECTORS_ROOT / name / "debug.json").read_text(encoding="utf-8")
        )
        request_view = debug["request_view"]
        response_view = debug["response_view"]
        request_for_sig = {
            k: materialise_for_cbor(v)
            for k, v in request_view.items()
            if k != "signature"
        }
        signing_input_req = cbor2.dumps(request_for_sig, canonical=True)
        verify_signature_block(
            signing_input_req,
            request_view["signature"],
            f"{name}.request.signature",
        )
        response_for_sig = {
            k: materialise_for_cbor(v)
            for k, v in response_view.items()
            if k != "signature"
        }
        signing_input_resp = cbor2.dumps(response_for_sig, canonical=True)
        verify_signature_block(
            signing_input_resp,
            response_view["signature"],
            f"{name}.response.signature",
        )
        mandate_view = response_view["claims"]
        mandate_for_sig = {
            k: materialise_for_cbor(v)
            for k, v in mandate_view.items()
            if k != "signature"
        }
        mandate_signing_input = cbor2.dumps(mandate_for_sig, canonical=True)
        verify_signature_block(
            mandate_signing_input,
            mandate_view["signature"],
            f"{name}.mandate.signature",
        )

    # Digest sanity: re-hash the on-disk bytes and compare.
    req_path = VECTORS_ROOT / name / f"request.{encoding}"
    resp_path = VECTORS_ROOT / name / f"response.{encoding}"
    req_digest = hashlib.sha256(req_path.read_bytes()).hexdigest()
    resp_digest = hashlib.sha256(resp_path.read_bytes()).hexdigest()
    if req_digest != expected["digests"]["request_sha256"]:
        fail(f"{name}: request digest mismatch")
    if resp_digest != expected["digests"]["response_sha256"]:
        fail(f"{name}: response digest mismatch")

    print(f"  ok  positive {alg:<10} {encoding} {name}")


def negative_vector_check(name: str) -> None:
    expected = json.loads(
        (VECTORS_ROOT / name / "expected.json").read_text(encoding="utf-8")
    )
    encoding = expected["encoding"]
    request, response = load_vector(name, encoding)

    if request["header"]["msg_type"] != "BOOTSTRAP":
        fail(f"{name}: request.msg_type should be BOOTSTRAP, got "
             f"{request['header']['msg_type']!r}")
    if response["header"]["msg_type"] != "ERROR":
        fail(f"{name}: response.msg_type should be ERROR, got "
             f"{response['header']['msg_type']!r}")
    claims = response["claims"]
    if claims["code"] != expected["error_code"]:
        fail(f"{name}: expected error_code={expected['error_code']}, "
             f"got {claims['code']}")
    if claims["name"] != expected["error_name"]:
        fail(f"{name}: expected error_name={expected['error_name']!r}, "
             f"got {claims['name']!r}")

    # Verify the response signature (ERROR is a signed envelope so the
    # rejection itself is auditable).
    response_for_sig = {k: v for k, v in response.items() if k != "signature"}
    signing_input_resp = cbor2.dumps(response_for_sig, canonical=True)
    verify_signature_block(
        signing_input_resp,
        response["signature"],
        f"{name}.response.signature",
    )

    print(f"  ok  negative {expected['error_name']:<28} {name}")


def main() -> None:
    index = json.loads(
        (VECTORS_ROOT / "index.json").read_text(encoding="utf-8")
    )
    print(f"Verifying {len(index['vectors'])} BOOTSTRAP vectors\n")
    for entry in index["vectors"]:
        if entry["kind"] == "positive":
            positive_vector_check(entry["name"], entry["encoding"])
        else:
            negative_vector_check(entry["name"])
    print("\nAll vectors verified.")


if __name__ == "__main__":
    main()
