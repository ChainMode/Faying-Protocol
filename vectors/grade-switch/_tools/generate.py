"""
Generate GRADE_SWITCH test vectors for Faying Protocol/1.0.

Output layout (relative to the parent directory of this file)::

    up-g3-to-g2/                request.{cbor,json}  response.{cbor,json}  expected.json
    up-g2-to-g1/                request.{cbor,json}  response.{cbor,json}  expected.json
    up-g4-to-g3/                request.{cbor,json}  response.{cbor,json}  expected.json
    down-g1-to-g2/              request.{cbor,json}  response.{cbor,json}  expected.json
    down-g2-to-g3/              request.{cbor,json}  response.{cbor,json}  expected.json
    down-g3-to-g4/              request.{cbor,json}  response.{cbor,json}  expected.json
    override-g0-from-g1/        request.{cbor,json}  response.{cbor,json}  expected.json
    override-g0-from-g2/        request.{cbor,json}  response.{cbor,json}  expected.json
    override-g0-from-g4/        request.{cbor,json}  response.{cbor,json}  expected.json
    neg-up-g3-to-g2-no-witness/ request.{cbor,json}  response.{cbor,json}  expected.json
    neg-up-g2-to-g1-no-witness/ request.{cbor,json}  response.{cbor,json}  expected.json
    index.json
    README.md

These vectors exercise:

* design.md §5.3.3 (GRADE_SWITCH message shape)
* design.md §7.2 (触发条件矩阵 — upgrade/downgrade outcomes per current grade)
* design.md §7.4 (等级切换报文要求差异: human_witness MUST on upgrade
  and on G0 Emergency Override; MAY on downgrade)
* §5.4 error code 1010 ``E_HUMAN_WITNESS_REQUIRED`` for the negative
  cases that omit ``human_witness`` on an upgrade.

Determinism contract
--------------------
* All Ed25519 keypairs, nonces, mandate / message ids, and synthetic
  payload bytes are derived from a fixed master seed
  (``FAYING_VECTOR_SEED``). The seed is intentionally identical to the
  one used by ``vectors/bootstrap/_tools/generate.py`` and
  ``vectors/presence/_tools/generate.py`` so that the three batches
  share a reproducibility anchor.
* Every key derivation goes through a per-batch domain separator
  (``b"grade-switch|"``) so vectors here do not collide with the
  BOOTSTRAP / PRESENCE batches.
* CBOR is encoded with ``cbor2.dumps(canonical=True)`` (RFC 8949
  §4.2.1). The signing input for every envelope is the canonical CBOR
  encoding of the unsigned envelope, regardless of wire encoding;
  JSON vectors mirror the CBOR shape via the
  ``{"$bytes": "<base64url>"}`` and ``{"$tag": 0, "$value": ...}``
  conventions established by the BOOTSTRAP / PRESENCE batches.
* The WebAuthn ``human_witness`` blobs are *placeholder* assertions
  whose bytes are deterministically derived from the seed, but the
  surrounding signature scheme (Ed25519 over canonical CBOR) is real
  and verifiable. README.md documents the placeholder boundary.

Acceptance (task 3.3)
---------------------
* Each upgrade vector carries a verifiable WebAuthn assertion (bytes
  are placeholders; structure and the surrounding Ed25519 envelope
  signature are real). The negative cases drop the assertion so the
  ``E_HUMAN_WITNESS_REQUIRED`` rejection is observable.
* The state-transition outcome on every vector matches §7.2 (e.g.
  G2 + ``HP 主动升级`` → G1; G3 + ``HP 主动降级`` → G4; G0 Override →
  Suspended).
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


# ---------------------------------------------------------------------------
# Deterministic source of randomness
# ---------------------------------------------------------------------------

# 32-byte fixed seed; identical to the BOOTSTRAP / PRESENCE batches so
# the three are anchored on one reproducibility seed. The per-batch
# domain separator below ensures no key / nonce collision between
# batches.
FAYING_VECTOR_SEED = bytes.fromhex(
    "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    "0001020304050607080910111213a414"
)


def derive(label: str, length: int = 32) -> bytes:
    """Deterministically expand the master seed into label-tagged bytes."""
    out = b""
    counter = 0
    while len(out) < length:
        h = hashlib.sha256()
        h.update(FAYING_VECTOR_SEED)
        h.update(b"grade-switch|")  # batch domain separator
        h.update(label.encode("utf-8"))
        h.update(counter.to_bytes(4, "big"))
        out += h.digest()
        counter += 1
    return out[:length]


# ---------------------------------------------------------------------------
# Key generation (deterministic Ed25519)
# ---------------------------------------------------------------------------


@dataclass
class Ed25519KeyPair:
    privkey: ed25519.Ed25519PrivateKey
    pubkey_raw: bytes


def make_ed25519(seed_label: str) -> Ed25519KeyPair:
    seed = derive(seed_label, 32)
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return Ed25519KeyPair(privkey=sk, pubkey_raw=pk)


def sign(kp: Ed25519KeyPair, message: bytes) -> bytes:
    return kp.privkey.sign(message)


def verify(kp: Ed25519KeyPair, message: bytes, signature: bytes) -> bool:
    try:
        kp.privkey.public_key().verify(signature, message)
        return True
    except Exception:  # pragma: no cover - defensive
        return False


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------


def cbor_canonical(obj: Any) -> bytes:
    """Deterministic CBOR encoding (RFC 8949 §4.2.1)."""
    return cbor2.dumps(obj, canonical=True)


def cbor_for_json(obj: Any) -> Any:
    """Convert a JSON-friendly tree (with explicit byte / tag carriers)
    into the matching CBOR-friendly tree.

    Reverses the ``{"$bytes": ...}`` and ``{"$tag": 0, "$value": ...}``
    conventions used in the JSON wire form so that the same logical
    payload yields the same canonical CBOR bytes regardless of the
    wire encoding chosen.
    """
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$bytes"}:
            return base64.urlsafe_b64decode(obj["$bytes"] + "==")
        if set(obj.keys()) == {"$tag", "$value"} and obj["$tag"] == 0:
            return cbor2.CBORTag(0, obj["$value"])
        return {k: cbor_for_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [cbor_for_json(x) for x in obj]
    return obj


def json_canonical(obj: Any) -> bytes:
    """JSON serialisation with stable key order."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def b64u(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def bytes_marker(data: bytes) -> Dict[str, str]:
    return {"$bytes": b64u(data)}


def time_marker(iso: str) -> Dict[str, Any]:
    return {"$tag": 0, "$value": iso}


# ---------------------------------------------------------------------------
# Constants — §7.1 budgets and §7.4 message-requirement matrix
# ---------------------------------------------------------------------------


# Authorization grade max-staleness budgets (design.md §7.1).
# Used to populate the issued Mandate's `presence-req.max-staleness-ms`
# and to keep the response Mandate consistent with the new grade.
GRADE_MAX_STALENESS_MS: Dict[int, int] = {
    1:        5_000,    # G1 Strict
    2:       60_000,    # G2 Moderate
    3:      300_000,    # G3 Loose
    4:    1_800_000,    # G4 Autonomous
}

GRADE_PRIMARY_SIGNAL: Dict[int, List[str]] = {
    1: ["webauthn-uv-fresh", "face-continuous"],
    2: ["fingerprint-tap"],
    3: ["intent-ticket"],
    4: ["presence-heartbeat-only"],
}

# §7.2 触发条件矩阵 — outcome per (current_grade, event).
# Used purely to assert in expected.json that the vector matches the
# matrix; the verifier (and downstream PBT) consume this for cross
# checks. Only the rows we exercise are encoded here.
TRIGGER_MATRIX: Dict[Tuple[int, str], str] = {
    # event = "human-upgrade"
    (3, "human-upgrade"):   "G2",
    (2, "human-upgrade"):   "G1",
    (4, "human-upgrade"):   "G3",
    # event = "human-downgrade"
    (1, "human-downgrade"): "G2",
    (2, "human-downgrade"): "G3",
    (3, "human-downgrade"): "G4",
    # event = "g0-override"
    (1, "g0-override"):     "Suspended",
    (2, "g0-override"):     "Suspended",
    (3, "g0-override"):     "Suspended",
    (4, "g0-override"):     "Suspended",
}


# ---------------------------------------------------------------------------
# Builders aligned with CDDL (`mandate`, `scope`, `presence-requirement`,
# `attestation`, `signature-bundle`) and the §5.3.3 GRADE_SWITCH claims.
# ---------------------------------------------------------------------------


def make_scope() -> Dict[str, Any]:
    """A typical scope shared across the grade-switch vectors."""
    return {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": [
            "calendar:event:create",
            "calendar:event:read",
            "calendar:event:update",
        ],
        "terminals": ["terminal:laptop:fixed-1"],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 100,
        },
    }


def make_presence_req(grade: int) -> Dict[str, Any]:
    """Presence requirement consistent with §7.1 for the given grade."""
    if grade == 0:
        # G0 is an out-of-band override channel; Mandates are never
        # *issued* at G0. We still need *some* presence-req shape on
        # the override target Mandate, so we keep the most strict
        # window (G1 Strict). The override response carries the
        # *previous* presence-req (i.e. the Mandate that is being
        # suspended), so this branch is only hit when constructing a
        # G0 *request envelope header*.
        signals = GRADE_PRIMARY_SIGNAL[1]
        max_stale = GRADE_MAX_STALENESS_MS[1]
        on_loss = "suspend"
    else:
        signals = GRADE_PRIMARY_SIGNAL[grade]
        max_stale = GRADE_MAX_STALENESS_MS[grade]
        if grade == 4:
            on_loss = "suspend"
        else:
            on_loss = f"downgrade-to:G{min(grade + 1, 4)}"
    return {
        "signal-types": signals,
        "max-staleness-ms": max_stale,
        "on-loss": on_loss,
    }


def make_webauthn_assertion(label: str) -> Dict[str, Any]:
    """Synthetic WebAuthn `human_witness` blob keyed by `label`.

    Deterministic but *not* a real WebAuthn assertion — see README's
    "WebAuthn placeholder" note. The bytes shape (credential_id,
    authenticator_data, client_data_json, signature) matches what the
    BOOTSTRAP vectors emit so verifiers can share decoding logic.
    """
    cred_id = derive(f"webauthn:{label}:cred", 16)
    auth_data = derive(f"webauthn:{label}:auth", 37)
    client_data = (
        '{"type":"webauthn.get","challenge":"'
        + b64u(derive(f"webauthn:{label}:chal", 32))
        + '","origin":"https://faying.example",'
        '"crossOrigin":false}'
    ).encode("utf-8")
    sig = derive(f"webauthn:{label}:sig", 64)
    return {
        "credential_id": b64u(cred_id),
        "authenticator_data": bytes_marker(auth_data),
        "client_data_json": bytes_marker(client_data),
        "signature": bytes_marker(sig),
        "user_present": True,
        "user_verified": True,
    }


def make_attestation(kp: Ed25519KeyPair, label: str) -> Dict[str, Any]:
    """Build an `attestation` object signing a deterministic payload."""
    payload = b"faying-attestation-payload:" + label.encode("utf-8")
    sig = sign(kp, payload)
    return {
        "format": "self-signed",
        "payload": bytes_marker(payload),
        "signer": f"hp:vector-{label}",
        "signature": {
            "alg": "Ed25519",
            "pubkey": bytes_marker(kp.pubkey_raw),
            "sig": bytes_marker(sig),
        },
    }


def make_signature_bundle(
    kp: Ed25519KeyPair, signed_message: bytes
) -> Dict[str, Any]:
    return {
        "alg": "Ed25519",
        "pubkey": bytes_marker(kp.pubkey_raw),
        "sig": bytes_marker(sign(kp, signed_message)),
    }


def envelope_skeleton(
    *,
    msg_type: str,
    msg_id: str,
    issued_at: str,
    expiry: str,
    nonce: bytes,
    grade: int,
    issuer: str,
    subject: str,
    claims: Dict[str, Any],
    attestation: Dict[str, Any],
) -> Dict[str, Any]:
    """Build an envelope tree minus the outer signature.

    Mirrors the structure used by the BOOTSTRAP and PRESENCE
    generators so all three batches share the same canonical-CBOR
    signing-input convention.
    """
    return {
        "header": {
            "version": "Faying Protocol/1.0",
            "msg_type": msg_type,
            "msg_id": msg_id,
            "issued_at": time_marker(issued_at),
            "expiry": time_marker(expiry),
            "nonce": bytes_marker(nonce),
            "grade": grade,
            "issuer": issuer,
            "subject": subject,
        },
        "claims": claims,
        "attestation": attestation,
    }


def make_mandate(
    *,
    mandate_id: str,
    issuer: str,
    subject: str,
    grade: int,
    issued_at: str,
    not_before: str,
    not_after: str,
    ms_kp: Ed25519KeyPair,
    label: str,
) -> Dict[str, Any]:
    """Build and sign an inner Mandate (CDDL `mandate` rule)."""
    skeleton: Dict[str, Any] = {
        "version": "Faying Protocol/1.0",
        "id": mandate_id,
        "issued-at": time_marker(issued_at),
        "not-before": time_marker(not_before),
        "not-after": time_marker(not_after),
        "issuer": issuer,
        "ms-id": f"ms:vector-{label}",
        "subject": subject,
        "scope": make_scope(),
        "grade": grade,
        "presence-req": make_presence_req(grade),
        "attestation": make_attestation(ms_kp, f"ms-{label}"),
    }
    signing_input = cbor_canonical(cbor_for_json(skeleton))
    full = dict(skeleton)
    full["signature"] = make_signature_bundle(ms_kp, signing_input)
    return full


# ---------------------------------------------------------------------------
# Vector specification
# ---------------------------------------------------------------------------


@dataclass
class VectorSpec:
    name: str
    direction: str        # "upgrade" | "downgrade" | "override" | "negative"
    current_grade: int    # the Mandate's grade prior to the switch
    target_grade: int     # what the request asks for (0 for G0 override)
    final_state: str      # "Active(Gn)" | "Suspended"
    summary: str
    requirements: List[str]
    request_tree: Dict[str, Any]
    request_kp: Ed25519KeyPair       # HP signs the GRADE_SWITCH envelope
    response_tree: Dict[str, Any]
    response_kp: Ed25519KeyPair      # MS signs the response envelope
    mandate_id: str
    expected_extras: Dict[str, Any]
    notes: str
    error_code: Optional[int] = None
    error_name: Optional[str] = None



# ---------------------------------------------------------------------------
# Per-vector builders
# ---------------------------------------------------------------------------


def _common_window() -> Tuple[str, str, str, str]:
    """Issued-at / not-before / not-after / envelope expiry tuple
    shared by every vector for diff readability."""
    issued_at  = "2026-01-01T00:00:00Z"
    not_before = "2026-01-01T00:00:00Z"
    not_after  = "2026-01-01T23:59:59Z"
    expiry     = "2026-01-01T00:01:00Z"
    return issued_at, not_before, not_after, expiry


def _ids(name: str, current: int, target: int) -> Tuple[str, str, str, str, str]:
    """Stable id strings used in the envelope and Mandate."""
    suffix = name.upper().replace("-", "_")
    msg_id_req      = f"01HXMSG-GS-REQ-{suffix}"
    msg_id_resp     = f"01HXMSG-GS-RESP-{suffix}"
    mandate_id      = f"01HXMNDT-GS-{suffix}"
    issuer          = f"hp:01HXHP-{suffix}"
    subject         = f"fay:01HXFAY-{suffix}"
    return msg_id_req, msg_id_resp, mandate_id, issuer, subject


def _build_grade_switch_request(
    *,
    name: str,
    current_grade: int,
    target_grade: int,
    reason: str,
    issuer: str,
    subject: str,
    msg_id_req: str,
    mandate_id: str,
    hp_kp: Ed25519KeyPair,
    include_witness: bool,
) -> Dict[str, Any]:
    """Build a GRADE_SWITCH request envelope (without the outer
    signature). The header `grade` field carries the *current* grade
    so RPs and audit consumers know which Mandate is being mutated."""
    issued_at, _not_before, _not_after, expiry = _common_window()
    nonce = derive(f"req-nonce:{name}", 16)

    claims: Dict[str, Any] = {
        "mandate_id": mandate_id,
        "target_grade": target_grade,
        "reason": reason,
    }
    if include_witness:
        claims["human_witness"] = make_webauthn_assertion(
            f"witness:{name}"
        )

    return envelope_skeleton(
        msg_type="GRADE_SWITCH",
        msg_id=msg_id_req,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=current_grade if current_grade > 0 else 1,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(hp_kp, f"req-{name}"),
    )


def _build_grade_switch_response(
    *,
    name: str,
    target_grade: int,
    issuer: str,
    subject: str,
    msg_id_resp: str,
    mandate: Dict[str, Any],
    ms_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    """Build a GRADE_SWITCH_RESP envelope carrying the updated
    Mandate. The Mandate is already signed by `make_mandate`."""
    issued_at, _not_before, _not_after, expiry = _common_window()
    return envelope_skeleton(
        msg_type="GRADE_SWITCH_RESP",
        msg_id=msg_id_resp,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=target_grade if target_grade > 0 else 1,
        issuer=issuer,
        subject=subject,
        claims=mandate,
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


def _build_error_response(
    *,
    name: str,
    current_grade: int,
    issuer: str,
    subject: str,
    msg_id_resp: str,
    mandate_id: str,
    code: int,
    error_name: str,
    detail: str,
    ms_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    issued_at, _not_before, _not_after, expiry = _common_window()
    return envelope_skeleton(
        msg_type="ERROR",
        msg_id=msg_id_resp,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=current_grade if current_grade > 0 else 1,
        issuer=issuer,
        subject=subject,
        claims={
            "code": code,
            "name": error_name,
            "detail": detail,
            "mandate_id": mandate_id,
        },
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


def build_upgrade_spec(
    name: str, current_grade: int, target_grade: int, *, summary_extra: str = ""
) -> VectorSpec:
    assert target_grade < current_grade, "Upgrade lowers the grade number"
    msg_id_req, msg_id_resp, mandate_id, issuer, subject = _ids(
        name, current_grade, target_grade
    )
    issued_at, not_before, not_after, _expiry = _common_window()
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")

    request_tree = _build_grade_switch_request(
        name=name,
        current_grade=current_grade,
        target_grade=target_grade,
        reason="human-initiated",
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        mandate_id=mandate_id,
        hp_kp=hp_kp,
        include_witness=True,
    )

    new_mandate = make_mandate(
        mandate_id=mandate_id,
        issuer=issuer,
        subject=subject,
        grade=target_grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        ms_kp=ms_kp,
        label=name,
    )
    response_tree = _build_grade_switch_response(
        name=name,
        target_grade=target_grade,
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        mandate=new_mandate,
        ms_kp=ms_kp,
    )

    matrix_outcome = TRIGGER_MATRIX[(current_grade, "human-upgrade")]
    expected_extras = {
        "outcome": "accepted",
        "request_must_carry_human_witness": True,
        "trigger_matrix": {
            "current_grade": f"G{current_grade}",
            "event": "human-upgrade",
            "expected_outcome": matrix_outcome,
        },
        "post_state": {
            "mandate_status": "Active",
            "grade": f"G{target_grade}",
            "presence_req_max_staleness_ms":
                GRADE_MAX_STALENESS_MS[target_grade],
        },
        "presence_key_rotated": True,
    }

    return VectorSpec(
        name=name,
        direction="upgrade",
        current_grade=current_grade,
        target_grade=target_grade,
        final_state=f"Active(G{target_grade})",
        summary=(
            f"Upgrade G{current_grade} → G{target_grade} signed by HP with "
            f"a verifiable human_witness{summary_extra}; MS issues an "
            f"updated Mandate at G{target_grade} (max-staleness "
            f"{GRADE_MAX_STALENESS_MS[target_grade]} ms)."
        ),
        requirements=["6.1", "6.2", "6.3", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        mandate_id=mandate_id,
        expected_extras=expected_extras,
        notes=(
            "Upgrade direction (target.autonomy < current.autonomy in "
            "design.md numbering: smaller grade number = stricter / "
            "lower-autonomy). human_witness is MANDATORY per §7.4. The "
            "MS rotates the Presence-Bound Mandate Key and issues a "
            "new Mandate whose presence-req tightens to the new "
            "grade's max-staleness budget."
        ),
    )


def build_downgrade_spec(
    name: str, current_grade: int, target_grade: int
) -> VectorSpec:
    assert target_grade > current_grade, "Downgrade raises the grade number"
    msg_id_req, msg_id_resp, mandate_id, issuer, subject = _ids(
        name, current_grade, target_grade
    )
    issued_at, not_before, not_after, _expiry = _common_window()
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")

    request_tree = _build_grade_switch_request(
        name=name,
        current_grade=current_grade,
        target_grade=target_grade,
        reason="human-initiated",
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        mandate_id=mandate_id,
        hp_kp=hp_kp,
        include_witness=False,  # downgrade: human_witness is MAY, not MUST
    )

    new_mandate = make_mandate(
        mandate_id=mandate_id,
        issuer=issuer,
        subject=subject,
        grade=target_grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        ms_kp=ms_kp,
        label=name,
    )
    response_tree = _build_grade_switch_response(
        name=name,
        target_grade=target_grade,
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        mandate=new_mandate,
        ms_kp=ms_kp,
    )

    matrix_outcome = TRIGGER_MATRIX[(current_grade, "human-downgrade")]
    expected_extras = {
        "outcome": "accepted",
        "request_must_carry_human_witness": False,
        "trigger_matrix": {
            "current_grade": f"G{current_grade}",
            "event": "human-downgrade",
            "expected_outcome": matrix_outcome,
        },
        "post_state": {
            "mandate_status": "Active",
            "grade": f"G{target_grade}",
            "presence_req_max_staleness_ms":
                GRADE_MAX_STALENESS_MS[target_grade],
        },
        "presence_key_rotated": True,
    }

    return VectorSpec(
        name=name,
        direction="downgrade",
        current_grade=current_grade,
        target_grade=target_grade,
        final_state=f"Active(G{target_grade})",
        summary=(
            f"Downgrade G{current_grade} → G{target_grade} initiated by HP "
            f"without a human_witness (MAY per §7.4); MS issues an "
            f"updated Mandate at G{target_grade}."
        ),
        requirements=["6.1", "6.2", "6.3", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        mandate_id=mandate_id,
        expected_extras=expected_extras,
        notes=(
            "Downgrade direction (target.autonomy > current.autonomy = "
            "larger grade number). §7.4 marks human_witness as MAY for "
            "the downgrade direction, so this vector intentionally "
            "omits it; verifiers MUST still accept on the strength of "
            "the HP-signed envelope alone."
        ),
    )


def build_override_spec(name: str, current_grade: int) -> VectorSpec:
    """Build a G0 Emergency Override vector.

    G0 is *orthogonal* to G1–G4 (§7.1): it is the HP's unilateral
    channel to push the target Mandate into ``Suspended``. The
    response therefore returns a Mandate clone whose ``grade`` is the
    pre-override value but whose status is ``Suspended`` — captured in
    ``expected.post_state``.
    """
    target_grade = 0  # G0 channel
    msg_id_req, msg_id_resp, mandate_id, issuer, subject = _ids(
        name, current_grade, target_grade
    )
    issued_at, not_before, not_after, _expiry = _common_window()
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")

    request_tree = _build_grade_switch_request(
        name=name,
        current_grade=current_grade,
        target_grade=target_grade,
        reason="human-initiated",
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        mandate_id=mandate_id,
        hp_kp=hp_kp,
        include_witness=True,  # §7.4: G0 Override requires human_witness
    )

    # The override response carries the *current* Mandate snapshot
    # (grade unchanged) but the post_state declares the Mandate as
    # `Suspended`. Per design.md §7.1, G0 is not a destination grade
    # but an action that suspends.
    suspended_mandate = make_mandate(
        mandate_id=mandate_id,
        issuer=issuer,
        subject=subject,
        grade=current_grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        ms_kp=ms_kp,
        label=name,
    )
    response_tree = _build_grade_switch_response(
        name=name,
        target_grade=current_grade,  # snapshot; status is Suspended
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        mandate=suspended_mandate,
        ms_kp=ms_kp,
    )

    expected_extras = {
        "outcome": "accepted",
        "request_must_carry_human_witness": True,
        "trigger_matrix": {
            "current_grade": f"G{current_grade}",
            "event": "g0-override",
            "expected_outcome": "Suspended",
        },
        "post_state": {
            "mandate_status": "Suspended",
            "grade": f"G{current_grade}",
            "note": (
                "G0 is a unilateral override channel orthogonal to "
                "G1-G4; the Mandate.grade snapshot is unchanged but "
                "the Mandate's status is Suspended."
            ),
        },
        "ms_priority": "highest",
        "rr_notification": "highest",
    }

    return VectorSpec(
        name=name,
        direction="override",
        current_grade=current_grade,
        target_grade=0,
        final_state="Suspended",
        summary=(
            f"G0 Emergency Override from G{current_grade} → Suspended; HP "
            f"unilateral channel with mandatory human_witness."
        ),
        requirements=["6.1", "6.2", "6.3", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        mandate_id=mandate_id,
        expected_extras=expected_extras,
        notes=(
            "G0 Emergency Override is the only path on which a Mandate "
            "transitions to Suspended without an in-band degradation. "
            "human_witness MUST be present (§7.4 line 3); RR "
            "notification carries highest priority (§EH.3)."
        ),
    )


def build_negative_no_witness_spec(
    name: str, current_grade: int, target_grade: int
) -> VectorSpec:
    """Upgrade request that omits ``human_witness`` →
    ``E_HUMAN_WITNESS_REQUIRED`` (1010)."""
    assert target_grade < current_grade, "Upgrade lowers the grade number"
    msg_id_req, msg_id_resp, mandate_id, issuer, subject = _ids(
        name, current_grade, target_grade
    )
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")

    request_tree = _build_grade_switch_request(
        name=name,
        current_grade=current_grade,
        target_grade=target_grade,
        reason="human-initiated",
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        mandate_id=mandate_id,
        hp_kp=hp_kp,
        include_witness=False,
    )
    response_tree = _build_error_response(
        name=name,
        current_grade=current_grade,
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        mandate_id=mandate_id,
        code=1010,
        error_name="E_HUMAN_WITNESS_REQUIRED",
        detail=(
            f"GRADE_SWITCH from G{current_grade} to G{target_grade} is "
            f"an upgrade direction (target_grade.autonomy strictly "
            f"greater than current); human_witness is MUST per §7.4 "
            f"and §5.3.3."
        ),
        ms_kp=ms_kp,
    )

    expected_extras = {
        "outcome": "rejected",
        "request_must_carry_human_witness": True,
        "trigger_matrix": {
            "current_grade": f"G{current_grade}",
            "event": "human-upgrade",
            "expected_outcome":
                TRIGGER_MATRIX[(current_grade, "human-upgrade")],
            "expected_outcome_when_accepted_only": True,
        },
        "post_state": {
            "mandate_status": "Active",
            "grade": f"G{current_grade}",
            "note": (
                "Rejection does not mutate Mandate state; the Mandate "
                "remains at the pre-request grade. RP / IF wait for HP "
                "to re-issue with a valid human_witness (§EH.1 row "
                "'升级缺见证')."
            ),
        },
    }

    return VectorSpec(
        name=name,
        direction="negative",
        current_grade=current_grade,
        target_grade=target_grade,
        final_state=f"Active(G{current_grade})",
        summary=(
            f"Negative: upgrade G{current_grade} → G{target_grade} "
            f"without human_witness must be rejected with "
            f"E_HUMAN_WITNESS_REQUIRED (1010)."
        ),
        requirements=["6.1", "6.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        mandate_id=mandate_id,
        expected_extras=expected_extras,
        notes=(
            "Verifies §5.3.3 协议层不变式 and §7.4 row 1: any upgrade "
            "lacking a verifiable human_witness MUST be refused. The "
            "ERROR envelope itself is signed by MS so the rejection "
            "is auditable on the Attestation Chain (Requirement 3.1)."
        ),
        error_code=1010,
        error_name="E_HUMAN_WITNESS_REQUIRED",
    )


# ---------------------------------------------------------------------------
# Vector emission
# ---------------------------------------------------------------------------


def _render_pair(
    spec: VectorSpec, *, encoding: str
) -> Tuple[bytes, Dict[str, Any], bytes, Dict[str, Any], bytes]:
    """Sign and serialise one (request, response) encoding pair.

    Returns
    -------
    request_bytes, request_full_tree, response_bytes, response_full_tree,
    request_signing_input
    """
    # --- Request: HP signs canonical CBOR of unsigned envelope ---
    req_signing_input = cbor_canonical(cbor_for_json(spec.request_tree))
    req_bundle = make_signature_bundle(spec.request_kp, req_signing_input)
    req_full = dict(spec.request_tree)
    req_full["signature"] = req_bundle

    # --- Response: MS signs canonical CBOR of unsigned envelope ---
    resp_signing_input = cbor_canonical(cbor_for_json(spec.response_tree))
    resp_bundle = make_signature_bundle(spec.response_kp, resp_signing_input)
    resp_full = dict(spec.response_tree)
    resp_full["signature"] = resp_bundle

    if encoding == "cbor":
        req_bytes = cbor_canonical(cbor_for_json(req_full))
        resp_bytes = cbor_canonical(cbor_for_json(resp_full))
    elif encoding == "json":
        req_bytes = json_canonical(req_full)
        resp_bytes = json_canonical(resp_full)
    else:  # pragma: no cover - defensive
        raise ValueError(encoding)

    return req_bytes, req_full, resp_bytes, resp_full, req_signing_input


def write_vector(out_root: Path, spec: VectorSpec) -> Dict[str, Any]:
    out = out_root / spec.name
    out.mkdir(parents=True, exist_ok=True)

    # Both CBOR and JSON encodings live side by side in every vector
    # directory so reviewers can diff them without rerunning the
    # generator.
    cbor_req, req_full, cbor_resp, resp_full, req_signing_input = (
        _render_pair(spec, encoding="cbor")
    )
    json_req, _, json_resp, _, _ = _render_pair(spec, encoding="json")

    (out / "request.cbor").write_bytes(cbor_req)
    (out / "request.json").write_bytes(json_req)
    (out / "response.cbor").write_bytes(cbor_resp)
    (out / "response.json").write_bytes(json_resp)

    expected: Dict[str, Any] = {
        "vector_name":   spec.name,
        "direction":     spec.direction,
        "current_grade": f"G{spec.current_grade}",
        "target_grade": (
            "G0" if spec.target_grade == 0 else f"G{spec.target_grade}"
        ),
        "final_state":   spec.final_state,
        "mandate_id":    spec.mandate_id,
        "summary":       spec.summary,
        "notes":         spec.notes,
        "error_code":    spec.error_code,
        "error_name":    spec.error_name,
        "encodings":     ["cbor", "json"],
        "files": {
            "request_cbor":  "request.cbor",
            "request_json":  "request.json",
            "response_cbor": "response.cbor",
            "response_json": "response.json",
        },
        "signature_verification": {
            "request_envelope":  True,
            "response_envelope": True,
            "mandate_inner": (
                spec.error_code is None
            ),
            "note": (
                "Real Ed25519 signatures over canonical CBOR. WebAuthn "
                "human_witness blobs are deterministic placeholders "
                "(see README); verifiers MUST treat their bytes as "
                "opaque and only validate structural presence."
            ),
        },
        "digests": {
            "request_cbor_sha256":
                hashlib.sha256(cbor_req).hexdigest(),
            "request_json_sha256":
                hashlib.sha256(json_req).hexdigest(),
            "response_cbor_sha256":
                hashlib.sha256(cbor_resp).hexdigest(),
            "response_json_sha256":
                hashlib.sha256(json_resp).hexdigest(),
            "request_signing_input_sha256":
                hashlib.sha256(req_signing_input).hexdigest(),
        },
        "requirements_validated": spec.requirements,
    }
    expected.update(spec.expected_extras)

    # Human-readable mirrors of both wire payloads (not normative).
    debug = {
        "request_view":  req_full,
        "response_view": resp_full,
    }
    (out / "debug.json").write_text(
        json.dumps(debug, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (out / "expected.json").write_text(
        json.dumps(expected, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return {
        "name":          spec.name,
        "direction":     spec.direction,
        "current_grade": f"G{spec.current_grade}",
        "target_grade":  expected["target_grade"],
        "final_state":   spec.final_state,
        "summary":       spec.summary,
        "request_cbor":  f"{spec.name}/request.cbor",
        "request_json":  f"{spec.name}/request.json",
        "response_cbor": f"{spec.name}/response.cbor",
        "response_json": f"{spec.name}/response.json",
        "expected":      f"{spec.name}/expected.json",
        "request_cbor_sha256":
            expected["digests"]["request_cbor_sha256"],
        "response_cbor_sha256":
            expected["digests"]["response_cbor_sha256"],
        "error_code":    spec.error_code,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    out_root = Path(__file__).resolve().parent.parent
    out_root.mkdir(parents=True, exist_ok=True)

    specs: List[VectorSpec] = []

    # Upgrades (witness MUST) — three vectors covering the §7.2
    # "HP 主动升级" row.
    specs.append(build_upgrade_spec("up-g3-to-g2", 3, 2))
    specs.append(build_upgrade_spec("up-g2-to-g1", 2, 1))
    specs.append(build_upgrade_spec("up-g4-to-g3", 4, 3))

    # Downgrades (witness MAY) — three vectors covering the §7.2
    # "HP 主动降级" row.
    specs.append(build_downgrade_spec("down-g1-to-g2", 1, 2))
    specs.append(build_downgrade_spec("down-g2-to-g3", 2, 3))
    specs.append(build_downgrade_spec("down-g3-to-g4", 3, 4))

    # G0 Emergency Override (any current grade → Suspended) — three
    # vectors for diversity across §7.2 "G0 Override" row.
    specs.append(build_override_spec("override-g0-from-g1", 1))
    specs.append(build_override_spec("override-g0-from-g2", 2))
    specs.append(build_override_spec("override-g0-from-g4", 4))

    # Negative: upgrade missing human_witness → E_HUMAN_WITNESS_REQUIRED.
    specs.append(build_negative_no_witness_spec(
        "neg-up-g3-to-g2-no-witness", 3, 2
    ))
    specs.append(build_negative_no_witness_spec(
        "neg-up-g2-to-g1-no-witness", 2, 1
    ))

    # Emit every vector and aggregate the manifest.
    index_entries: List[Dict[str, Any]] = []
    for spec in specs:
        index_entries.append(write_vector(out_root, spec))

    index = {
        "spec_version": "Faying Protocol/1.0",
        "category": "GRADE_SWITCH",
        "generated_with":
            "vectors/grade-switch/_tools/generate.py",
        "deterministic_seed_sha256":
            hashlib.sha256(FAYING_VECTOR_SEED).hexdigest(),
        "schemas": {
            "cddl":    "schemas/fap-1.0.cddl",
            "ts_view": "schemas/types.ts",
        },
        "design_anchors": [
            "design.md §5.3.3 GRADE_SWITCH",
            "design.md §7.2 触发条件矩阵",
            "design.md §7.4 等级切换报文要求差异",
            "design.md §EH.1 错误码表",
        ],
        "freshness_table": {
            f"G{g}": {
                "max_staleness_ms": ms,
                "primary_signal_types": GRADE_PRIMARY_SIGNAL[g],
            }
            for g, ms in sorted(GRADE_MAX_STALENESS_MS.items())
        },
        "trigger_matrix": {
            "human-upgrade": {
                f"G{c}": TRIGGER_MATRIX[(c, "human-upgrade")]
                for c in (2, 3, 4)
            },
            "human-downgrade": {
                f"G{c}": TRIGGER_MATRIX[(c, "human-downgrade")]
                for c in (1, 2, 3)
            },
            "g0-override": {
                f"G{c}": TRIGGER_MATRIX[(c, "g0-override")]
                for c in (1, 2, 3, 4)
            },
        },
        "requirements_covered": ["6.1", "6.2", "6.3", "10.1", "10.3"],
        "vectors": index_entries,
    }
    (out_root / "index.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(index_entries)} vectors to {out_root}")


if __name__ == "__main__":
    main()
