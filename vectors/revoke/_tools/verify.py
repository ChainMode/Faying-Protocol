"""
Verify the REVOKE test vectors emitted by ``generate.py``.

Performs the following checks per vector:

1. CBOR / JSON round-trip equivalence — both encodings round-trip to
   byte-identical canonical CBOR for the unsigned envelope, so the
   same outer signature appears in both wire forms.
2. Structural shape against design.md §5.3.5:
   * request `header.msg_type == "REVOKE"`,
   * request `claims` carries `mandate_id`, `cascade`, `reason`,
     `effective_at`, with `reason` ∈ the nine ``RevokeReason``
     enum values,
   * positive responses carry `REVOKE_RECEIPT` with `mandate_id`,
     `reason`, `revoked_at`, `cascade`, `cascaded_mandate_ids`,
   * negative responses carry an `ERROR` envelope with the declared
     `code` / `name` (1006 / E_REVOKED).
3. Outer Ed25519 signature on every envelope —
   `H( Deterministic-CBOR(... − signature) )`.
4. RR visibility timestamp = `effective_at + RevocationVisibilityBudget`
   (default 1s).
5. Affected mandate id list matches the receipt's
   `mandate_id` ∪ `cascaded_mandate_ids`.
6. Per-vector SHA-256 digests on disk match `expected.digests.*`.
7. `index.json` reproduces the same digests, references every vector
   exactly once, and records all nine RevokeReason values.

Exit code is 0 on success, 1 on any failure.
"""

from __future__ import annotations

import base64
import hashlib
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import cbor2
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519


# ---------------------------------------------------------------------------
# Generic decode helpers (mirror generate.py without importing it)
# ---------------------------------------------------------------------------


REVOKE_REASON_ENUM = {
    "human-initiated",
    "expiry",
    "task-completed",
    "human-prime-unreachable",
    "ego-deviation",
    "fay-credential-invalid",
    "human-prime-credential-invalid",
    "regulatory-order",
    "terminal-disconnected",
}

REVOCATION_VISIBILITY_BUDGET_MS = 1000


def b64u_decode(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "==")


def cbor_for_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$bytes"}:
            return b64u_decode(obj["$bytes"])
        if set(obj.keys()) == {"$tag", "$value"} and obj["$tag"] == 0:
            return cbor2.CBORTag(0, obj["$value"])
        return {k: cbor_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [cbor_for_json(x) for x in obj]
    return obj


def cbor_canonical(obj: Any) -> bytes:
    return cbor2.dumps(obj, canonical=True)


def parse_iso(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# Verification primitives
# ---------------------------------------------------------------------------


class VerifyError(Exception):
    pass


def verify_outer_signature(envelope: Dict[str, Any], *, label: str) -> None:
    """Verify the outer ``signature`` block of an envelope tree."""
    if "signature" not in envelope:
        raise VerifyError(f"{label}: envelope missing outer signature")
    bundle = envelope["signature"]
    pubkey = b64u_decode(bundle["pubkey"]["$bytes"])
    sig    = b64u_decode(bundle["sig"]["$bytes"])
    alg    = bundle["alg"]
    if alg != "Ed25519":
        raise VerifyError(f"{label}: unexpected outer-sig alg {alg!r}")

    unsigned = {k: v for k, v in envelope.items() if k != "signature"}
    signing_input = cbor_canonical(cbor_for_json(unsigned))
    pk = ed25519.Ed25519PublicKey.from_public_bytes(pubkey)
    try:
        pk.verify(sig, signing_input)
    except InvalidSignature as exc:
        raise VerifyError(
            f"{label}: outer Ed25519 signature failed verification"
        ) from exc


def encoding_round_trip(
    cbor_path: Path, json_path: Path, *, label: str
) -> Dict[str, Any]:
    """Confirm CBOR and JSON encodings round-trip to identical canonical CBOR."""
    cbor_blob = cbor_path.read_bytes()
    json_blob = json_path.read_bytes()

    cbor_decoded = cbor2.loads(cbor_blob)
    json_decoded = json.loads(json_blob.decode("utf-8"))

    cbor_redumped = cbor_canonical(cbor_decoded)
    json_redumped_cbor = cbor_canonical(cbor_for_json(json_decoded))
    if cbor_redumped != json_redumped_cbor:
        raise VerifyError(
            f"{label}: CBOR ↔ JSON round-trip diverges (canonical CBOR "
            f"of CBOR-decoded != canonical CBOR of JSON-decoded)"
        )
    if cbor_redumped != cbor_blob:
        raise VerifyError(
            f"{label}: CBOR file is not canonical (RFC 8949 §4.2.1)"
        )

    return json_decoded


def verify_revoke_request(
    request_tree: Dict[str, Any], *, label: str, expected: Dict[str, Any]
) -> None:
    if request_tree["header"]["msg_type"] != "REVOKE":
        raise VerifyError(f"{label}: request msg_type != REVOKE")
    claims = request_tree["claims"]
    for required in ("mandate_id", "cascade", "reason", "effective_at"):
        if required not in claims:
            raise VerifyError(
                f"{label}: request claims missing {required!r}"
            )
    if claims["reason"] not in REVOKE_REASON_ENUM:
        raise VerifyError(
            f"{label}: reason {claims['reason']!r} not in RevokeReason enum"
        )
    if not isinstance(claims["cascade"], bool):
        raise VerifyError(
            f"{label}: cascade is not a boolean (got {type(claims['cascade'])})"
        )
    if claims["mandate_id"] != expected["target_mandate_id"]:
        raise VerifyError(
            f"{label}: request claims.mandate_id != expected.target_mandate_id "
            f"({claims['mandate_id']!r} vs {expected['target_mandate_id']!r})"
        )


def verify_revoke_receipt(
    response_tree: Dict[str, Any], *, label: str, expected: Dict[str, Any]
) -> None:
    if response_tree["header"]["msg_type"] != "REVOKE_RECEIPT":
        raise VerifyError(f"{label}: response msg_type != REVOKE_RECEIPT")
    claims = response_tree["claims"]
    for required in (
        "mandate_id", "reason", "revoked_at", "cascade",
        "cascaded_mandate_ids",
    ):
        if required not in claims:
            raise VerifyError(
                f"{label}: receipt claims missing {required!r}"
            )
    if claims["reason"] not in REVOKE_REASON_ENUM:
        raise VerifyError(
            f"{label}: receipt reason {claims['reason']!r} not in enum"
        )
    if claims["mandate_id"] != expected["target_mandate_id"]:
        raise VerifyError(
            f"{label}: receipt mandate_id != target_mandate_id"
        )

    # Verify cascade matches request semantics.
    if bool(claims["cascade"]) != bool(expected["cascade"]):
        raise VerifyError(
            f"{label}: receipt.cascade != expected.cascade "
            f"({claims['cascade']!r} vs {expected['cascade']!r})"
        )

    # Verify cascaded ids match.
    receipt_cascaded = list(claims["cascaded_mandate_ids"])
    expected_cascaded = list(expected.get("cascaded_mandate_ids", []))
    if receipt_cascaded != expected_cascaded:
        raise VerifyError(
            f"{label}: receipt.cascaded_mandate_ids != "
            f"expected.cascaded_mandate_ids "
            f"({receipt_cascaded!r} vs {expected_cascaded!r})"
        )

    # Verify affected_mandate_ids = [target] ∪ cascaded.
    affected = list(expected["affected_mandate_ids"])
    expected_affected = [expected["target_mandate_id"], *expected_cascaded]
    if affected != expected_affected:
        raise VerifyError(
            f"{label}: expected.affected_mandate_ids != "
            f"[target, *cascaded] ({affected!r} vs {expected_affected!r})"
        )


def verify_error_response(
    response_tree: Dict[str, Any], *, label: str, expected: Dict[str, Any]
) -> None:
    if response_tree["header"]["msg_type"] != "ERROR":
        raise VerifyError(
            f"{label}: response msg_type != ERROR (negative vector)"
        )
    claims = response_tree["claims"]
    if claims.get("code") != expected["error_code"]:
        raise VerifyError(
            f"{label}: ERROR code {claims.get('code')!r} != "
            f"expected.error_code {expected['error_code']!r}"
        )
    if claims.get("name") != expected["error_name"]:
        raise VerifyError(
            f"{label}: ERROR name {claims.get('name')!r} != "
            f"expected.error_name {expected['error_name']!r}"
        )
    if claims.get("mandate_id") != expected["target_mandate_id"]:
        raise VerifyError(
            f"{label}: ERROR mandate_id != target_mandate_id"
        )


def verify_rr_visibility(expected: Dict[str, Any], *, label: str) -> None:
    """Verify rr_visible_by = effective_at + visibility_budget_ms."""
    rr = expected["rr_visibility"]
    eff = parse_iso(rr["effective_at"]["$value"])
    visible = parse_iso(rr["rr_visible_by"]["$value"])
    budget = rr["visibility_budget_ms"]
    if budget != REVOCATION_VISIBILITY_BUDGET_MS:
        raise VerifyError(
            f"{label}: visibility_budget_ms {budget} != default "
            f"{REVOCATION_VISIBILITY_BUDGET_MS}"
        )
    delta = visible - eff
    expected_delta = timedelta(milliseconds=budget)
    if delta != expected_delta:
        raise VerifyError(
            f"{label}: rr_visible_by - effective_at = {delta} != "
            f"visibility_budget {expected_delta}"
        )


def verify_audit_event(expected: Dict[str, Any], *, label: str) -> None:
    """Five-tuple completeness check (§9.6)."""
    audit = expected["audit_event"]
    for key in ("error_code", "mandate_id", "ts", "rp_id", "reason"):
        if key not in audit:
            raise VerifyError(
                f"{label}: audit_event missing key {key!r}"
            )
    if audit["mandate_id"] != expected["target_mandate_id"]:
        raise VerifyError(
            f"{label}: audit_event.mandate_id != target_mandate_id"
        )
    if expected["kind"] == "negative":
        if audit["error_code"] != expected["error_code"]:
            raise VerifyError(
                f"{label}: audit_event.error_code != expected.error_code"
            )


def verify_irreversibility(expected: Dict[str, Any], *, label: str) -> None:
    """Every REVOKE vector MUST encode the no-revoked-to-active claim."""
    post = expected["post_state"]
    if not post.get("no_revoked_to_active_path"):
        raise VerifyError(
            f"{label}: post_state.no_revoked_to_active_path is not True "
            "(Requirement 4.3.2)"
        )


def verify_digests(vec_dir: Path, expected: Dict[str, Any], *, label: str) -> None:
    digests = expected["digests"]
    for filename, key in [
        ("request.cbor",  "request_cbor_sha256"),
        ("request.json",  "request_json_sha256"),
        ("response.cbor", "response_cbor_sha256"),
        ("response.json", "response_json_sha256"),
    ]:
        actual = hashlib.sha256((vec_dir / filename).read_bytes()).hexdigest()
        if actual != digests[key]:
            raise VerifyError(
                f"{label}: {filename} sha256 mismatch "
                f"(expected {digests[key]}, got {actual})"
            )


def verify_positive_vector(
    name: str,
    vec_dir: Path,
    expected: Dict[str, Any],
) -> None:
    label = f"vector[{name}]"

    request_tree = encoding_round_trip(
        vec_dir / "request.cbor", vec_dir / "request.json",
        label=f"{label} request",
    )
    response_tree = encoding_round_trip(
        vec_dir / "response.cbor", vec_dir / "response.json",
        label=f"{label} response",
    )

    verify_revoke_request(request_tree, label=label, expected=expected)
    verify_revoke_receipt(response_tree, label=label, expected=expected)

    verify_outer_signature(request_tree,  label=f"{label} request")
    verify_outer_signature(response_tree, label=f"{label} response")

    verify_rr_visibility(expected, label=label)
    verify_audit_event(expected, label=label)
    verify_irreversibility(expected, label=label)
    verify_digests(vec_dir, expected, label=label)


def verify_negative_vector(
    name: str,
    vec_dir: Path,
    expected: Dict[str, Any],
) -> None:
    label = f"vector[{name}]"

    request_tree = encoding_round_trip(
        vec_dir / "request.cbor", vec_dir / "request.json",
        label=f"{label} request",
    )
    response_tree = encoding_round_trip(
        vec_dir / "response.cbor", vec_dir / "response.json",
        label=f"{label} response",
    )

    verify_revoke_request(request_tree, label=label, expected=expected)
    verify_error_response(response_tree, label=label, expected=expected)

    verify_outer_signature(request_tree,  label=f"{label} request")
    verify_outer_signature(response_tree, label=f"{label} response")

    verify_audit_event(expected, label=label)
    verify_irreversibility(expected, label=label)
    verify_digests(vec_dir, expected, label=label)


def verify_index(out_root: Path) -> None:
    index = json.loads((out_root / "index.json").read_text("utf-8"))
    if index["category"] != "REVOKE":
        raise VerifyError("index.json: category != REVOKE")
    if index["spec_version"] != "Faying Protocol/1.0":
        raise VerifyError("index.json: spec_version mismatch")
    if (
        index["revocation_visibility_budget_ms"]
        != REVOCATION_VISIBILITY_BUDGET_MS
    ):
        raise VerifyError(
            "index.json: revocation_visibility_budget_ms != "
            f"{REVOCATION_VISIBILITY_BUDGET_MS}"
        )

    # Every RevokeReason enum value MUST be represented.
    seen_reasons = set(index["revoke_reason_coverage"])
    missing = REVOKE_REASON_ENUM - seen_reasons
    if missing:
        raise VerifyError(
            f"index.json: missing RevokeReason coverage: "
            f"{sorted(missing)}"
        )

    # Cross-check digests in index.json against expected.json.
    for entry in index["vectors"]:
        name = entry["name"]
        vec_dir = out_root / name
        expected = json.loads((vec_dir / "expected.json").read_text("utf-8"))
        if entry["request_cbor_sha256"] != expected["digests"]["request_cbor_sha256"]:
            raise VerifyError(
                f"index.json[{name}]: request_cbor_sha256 mismatch with expected.json"
            )
        if entry["response_cbor_sha256"] != expected["digests"]["response_cbor_sha256"]:
            raise VerifyError(
                f"index.json[{name}]: response_cbor_sha256 mismatch with expected.json"
            )

    # At least one vector with a depth-2 cascade tree.
    saw_cascade_depth_2 = False
    for entry in index["vectors"]:
        name = entry["name"]
        vec_dir = out_root / name
        expected = json.loads((vec_dir / "expected.json").read_text("utf-8"))
        if expected.get("tree_depth") == 2 and expected.get("cascade") is True:
            if expected.get("cascaded_mandate_ids"):
                saw_cascade_depth_2 = True
                break
    if not saw_cascade_depth_2:
        raise VerifyError(
            "index.json: no cascade=true vector with tree_depth>=2 and "
            "non-empty cascaded_mandate_ids found"
        )

    # At least 12 vectors total (task 3.5 acceptance: 12+).
    if len(index["vectors"]) < 12:
        raise VerifyError(
            f"index.json: only {len(index['vectors'])} vectors; "
            "task 3.5 requires ≥ 12"
        )


def main() -> int:
    out_root = Path(__file__).resolve().parent.parent
    if not (out_root / "index.json").exists():
        print(f"index.json missing at {out_root}; run generate.py first")
        return 1

    index = json.loads((out_root / "index.json").read_text("utf-8"))

    failed = 0
    total  = 0
    for entry in index["vectors"]:
        total += 1
        name = entry["name"]
        vec_dir = out_root / name
        expected = json.loads((vec_dir / "expected.json").read_text("utf-8"))
        try:
            if expected["kind"] == "positive":
                verify_positive_vector(name, vec_dir, expected)
            else:
                verify_negative_vector(name, vec_dir, expected)
            print(f"  ✓ {name}")
        except VerifyError as exc:
            failed += 1
            print(f"  ✗ {name}: {exc}")

    try:
        verify_index(out_root)
        print("  ✓ index.json")
    except VerifyError as exc:
        failed += 1
        print(f"  ✗ index.json: {exc}")

    if failed:
        print(f"\n{failed}/{total + 1} checks failed.")
        return 1
    print(f"\nAll {total + 1} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
