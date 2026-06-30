"""
Verify the generated GRADE_SWITCH test vectors.

Checks performed
----------------
1. Every vector decodes as CBOR and as JSON, and the two views
   round-trip to the same canonical CBOR signing input
   (request and response, separately).
2. The decoded request envelope matches the structural shape
   expected by design.md §5.3.3:
   - ``header.msg_type == "GRADE_SWITCH"``
   - claims contain ``mandate_id`` (tstr) and ``target_grade``
     (0..4)
   - ``human_witness`` is present iff ``expected.request_must_carry_human_witness``
3. The decoded response envelope matches:
   - ``msg_type == "GRADE_SWITCH_RESP"`` for accepted vectors;
     ``msg_type == "ERROR"`` for negative vectors carrying the
     declared ``expected.error_code``.
4. Every outer envelope signature verifies (Ed25519 over canonical
   CBOR of the unsigned envelope). For accepted vectors the inner
   Mandate signature also verifies.
5. Per-vector SHA-256 digests on disk match ``expected.digests.*``.
6. The transition outcome encoded in ``expected.trigger_matrix``
   matches the §7.2 matrix that the generator derived from
   design.md.

Exit code: 0 on success, 1 otherwise.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import cbor2
from cryptography.hazmat.primitives.asymmetric import ed25519


VECTORS_ROOT = Path(__file__).resolve().parent.parent


# Mirrors the §7.2 outcome table the generator uses; the verifier
# rederives this independently so a drift in the generator is caught.
TRIGGER_MATRIX: Dict[Tuple[int, str], str] = {
    (3, "human-upgrade"):   "G2",
    (2, "human-upgrade"):   "G1",
    (4, "human-upgrade"):   "G3",
    (1, "human-downgrade"): "G2",
    (2, "human-downgrade"): "G3",
    (3, "human-downgrade"): "G4",
    (1, "g0-override"):     "Suspended",
    (2, "g0-override"):     "Suspended",
    (3, "g0-override"):     "Suspended",
    (4, "g0-override"):     "Suspended",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}", file=sys.stderr)
    raise SystemExit(1)


def b64u_decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "==")


def materialise_for_cbor(node: Any) -> Any:
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


def expect_keys(node: Dict[str, Any], required: Tuple[str, ...], path: str) -> None:
    for k in required:
        if k not in node:
            fail(f"{path}: missing required key '{k}' (have {sorted(node)})")


def verify_envelope_signature(envelope: Dict[str, Any], path: str) -> None:
    """Verify the outer Ed25519 signature over canonical CBOR of the
    unsigned envelope tree. Works on the JSON-mirror tree (with
    ``$bytes`` markers). Raises on failure."""
    expect_keys(envelope, ("header", "claims", "attestation", "signature"), path)
    sig_block = envelope["signature"]
    expect_keys(sig_block, ("alg", "pubkey", "sig"), f"{path}.signature")
    if sig_block["alg"] != "Ed25519":
        fail(f"{path}.signature.alg must be Ed25519, got {sig_block['alg']!r}")

    unsigned = {k: v for k, v in envelope.items() if k != "signature"}
    signing_input = cbor_canonical(materialise_for_cbor(unsigned))

    pub = b64u_decode(sig_block["pubkey"]["$bytes"])
    sig = b64u_decode(sig_block["sig"]["$bytes"])

    pk = ed25519.Ed25519PublicKey.from_public_bytes(pub)
    try:
        pk.verify(sig, signing_input)
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"{path}: envelope signature did not verify: {exc!r}")


def verify_mandate_signature(mandate: Dict[str, Any], path: str) -> None:
    """Verify the inner Mandate signature (CDDL `mandate.signature`)."""
    expect_keys(mandate, ("id", "issuer", "subject", "scope", "grade",
                          "presence-req", "attestation", "signature"), path)
    sig_block = mandate["signature"]
    expect_keys(sig_block, ("alg", "pubkey", "sig"), f"{path}.signature")
    if sig_block["alg"] != "Ed25519":
        fail(f"{path}.signature.alg must be Ed25519, got {sig_block['alg']!r}")

    unsigned = {k: v for k, v in mandate.items() if k != "signature"}
    signing_input = cbor_canonical(materialise_for_cbor(unsigned))

    pub = b64u_decode(sig_block["pubkey"]["$bytes"])
    sig = b64u_decode(sig_block["sig"]["$bytes"])
    pk = ed25519.Ed25519PublicKey.from_public_bytes(pub)
    try:
        pk.verify(sig, signing_input)
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"{path}: inner Mandate signature did not verify: {exc!r}")


def cbor_decode(payload: bytes) -> Any:
    return cbor2.loads(payload)


def cbor_to_json_view(obj: Any) -> Any:
    """Convert a CBOR-decoded tree back into the JSON-mirror shape
    using the ``$bytes`` and ``$tag`` markers."""
    if isinstance(obj, bytes):
        return {"$bytes": base64.urlsafe_b64encode(obj).rstrip(b"=").decode()}
    if isinstance(obj, cbor2.CBORTag) and obj.tag == 0:
        return {"$tag": 0, "$value": obj.value}
    if isinstance(obj, dict):
        return {k: cbor_to_json_view(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [cbor_to_json_view(x) for x in obj]
    return obj


def check_round_trip(
    vector_dir: Path, kind: str, expected_digests: Dict[str, str]
) -> Dict[str, Any]:
    """Decode `kind`.cbor and `kind`.json and confirm both materialise
    to the same canonical CBOR. Returns the decoded JSON-mirror tree
    (which is what verify_envelope_signature consumes)."""
    cbor_bytes = (vector_dir / f"{kind}.cbor").read_bytes()
    json_bytes = (vector_dir / f"{kind}.json").read_bytes()

    actual_cbor_sha = hashlib.sha256(cbor_bytes).hexdigest()
    actual_json_sha = hashlib.sha256(json_bytes).hexdigest()
    if expected_digests[f"{kind}_cbor_sha256"] != actual_cbor_sha:
        fail(
            f"{vector_dir.name}/{kind}.cbor sha256 mismatch: "
            f"on-disk={actual_cbor_sha} "
            f"expected={expected_digests[f'{kind}_cbor_sha256']}"
        )
    if expected_digests[f"{kind}_json_sha256"] != actual_json_sha:
        fail(
            f"{vector_dir.name}/{kind}.json sha256 mismatch: "
            f"on-disk={actual_json_sha} "
            f"expected={expected_digests[f'{kind}_json_sha256']}"
        )

    decoded_cbor = cbor_decode(cbor_bytes)
    decoded_json = json.loads(json_bytes.decode("utf-8"))

    cbor_canon = cbor_canonical(decoded_cbor)
    json_canon = cbor_canonical(materialise_for_cbor(decoded_json))
    if cbor_canon != json_canon:
        fail(
            f"{vector_dir.name}/{kind}: CBOR and JSON encodings did "
            f"not round-trip to the same canonical CBOR "
            f"(cbor_sha={hashlib.sha256(cbor_canon).hexdigest()}, "
            f"json_sha={hashlib.sha256(json_canon).hexdigest()})"
        )
    return decoded_json


def verify_vector(vector_dir: Path) -> None:
    expected_path = vector_dir / "expected.json"
    if not expected_path.exists():
        fail(f"{vector_dir}: missing expected.json")

    expected = json.loads(expected_path.read_text("utf-8"))
    digests = expected["digests"]

    request = check_round_trip(vector_dir, "request", digests)
    response = check_round_trip(vector_dir, "response", digests)

    # ----- Request structure (§5.3.3) -----
    if request["header"]["msg_type"] != "GRADE_SWITCH":
        fail(f"{vector_dir.name}: header.msg_type must be GRADE_SWITCH")
    claims = request["claims"]
    expect_keys(claims, ("mandate_id", "target_grade", "reason"),
                f"{vector_dir.name}.request.claims")
    if not isinstance(claims["target_grade"], int):
        fail(f"{vector_dir.name}: target_grade must be an integer")
    if claims["target_grade"] not in {0, 1, 2, 3, 4}:
        fail(f"{vector_dir.name}: target_grade outside {{0..4}}")
    direction = expected["direction"]
    if direction in ("upgrade", "override"):
        # Witness is MANDATORY per §7.4 → request MUST carry it.
        if "human_witness" not in claims:
            fail(f"{vector_dir.name}: human_witness expected but missing")
    elif direction == "downgrade":
        # §7.4 marks witness as MAY for downgrade; the canonical
        # generator deliberately omits it so verifiers learn to
        # accept the absent path.
        if "human_witness" in claims:
            fail(
                f"{vector_dir.name}: human_witness unexpectedly present "
                f"on a downgrade vector (the canonical downgrade form "
                f"omits it to exercise the §7.4 MAY branch)"
            )
    elif direction == "negative":
        # Whole point of the negative vector: missing witness.
        if "human_witness" in claims:
            fail(
                f"{vector_dir.name}: negative vector must omit "
                f"human_witness (got one present)"
            )
    else:  # pragma: no cover - defensive
        fail(f"{vector_dir.name}: unknown direction {direction!r}")

    # ----- Response structure -----
    expected_resp_type = (
        "ERROR" if expected["error_code"] is not None
        else "GRADE_SWITCH_RESP"
    )
    if response["header"]["msg_type"] != expected_resp_type:
        fail(
            f"{vector_dir.name}: response.msg_type must be "
            f"{expected_resp_type}, got {response['header']['msg_type']!r}"
        )
    if expected["error_code"] is not None:
        if response["claims"].get("code") != expected["error_code"]:
            fail(
                f"{vector_dir.name}: ERROR.code must be "
                f"{expected['error_code']}, got "
                f"{response['claims'].get('code')!r}"
            )
        if response["claims"].get("name") != expected["error_name"]:
            fail(
                f"{vector_dir.name}: ERROR.name must be "
                f"{expected['error_name']!r}"
            )

    # ----- Signatures -----
    verify_envelope_signature(request, f"{vector_dir.name}.request")
    verify_envelope_signature(response, f"{vector_dir.name}.response")
    if expected["error_code"] is None:
        # The accepted vectors carry a Mandate inside the response
        # envelope's claims; verify its inner signature too.
        verify_mandate_signature(
            response["claims"], f"{vector_dir.name}.response.mandate"
        )

    # ----- Trigger matrix consistency -----
    matrix = expected.get("trigger_matrix")
    if matrix is None:
        fail(f"{vector_dir.name}: expected.trigger_matrix missing")
    cur_grade = int(matrix["current_grade"][1:])
    event = matrix["event"]
    if event in {"human-upgrade", "human-downgrade", "g0-override"}:
        derived = TRIGGER_MATRIX.get((cur_grade, event))
        if derived != matrix["expected_outcome"]:
            fail(
                f"{vector_dir.name}: trigger_matrix mismatch — "
                f"({cur_grade}, {event}) → derived {derived}, "
                f"expected {matrix['expected_outcome']}"
            )


def main() -> int:
    index_path = VECTORS_ROOT / "index.json"
    if not index_path.exists():
        fail(f"{index_path}: not found; run generate.py first")

    index = json.loads(index_path.read_text("utf-8"))
    if index["category"] != "GRADE_SWITCH":
        fail(f"index.json category must be GRADE_SWITCH")

    if not index["vectors"]:
        fail("index.json contains no vectors")

    for entry in index["vectors"]:
        vector_dir = VECTORS_ROOT / entry["name"]
        if not vector_dir.is_dir():
            fail(f"{entry['name']}: directory missing")
        verify_vector(vector_dir)

    print(f"OK: verified {len(index['vectors'])} GRADE_SWITCH vectors")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
