#!/usr/bin/env python3
"""
Generator for `vectors/faying-request/` test vectors.

Covers Faying Protocol/1.0 §5.3.6 (FAYING_REQUEST / FAYING_REQUEST_RESP) and
§1.5.1 / §2.4 Phase A0 (IF-initiated 双向 Faying)。

8 vectors:

  vec-01-establish               (a) iFay-initiated reason_code=establish + (b) HP confirms via BOOTSTRAP
  vec-02-adjust-scope            (a) reason_code=adjust-scope + (b) HP confirms
  vec-03-adjust-grade            (a) reason_code=adjust-grade + (b) HP confirms
  vec-04-renew                   (a) reason_code=renew + (b) HP confirms
  vec-05-endorsement-request     (a) reason_code=endorsement-request + (b) HP confirms with endorsement
  vec-06-hp-rejected             (c) HP explicit reject FAYING_REQUEST_RESP{status="rejected"}
  vec-07-bootstrap-timeout       (d) BootstrapTimeout exceeded → E_FAYING_REQUEST_NOT_CONFIRMED (1014)
  vec-08-forged-ms-surrogate     (e) "MS confirms on behalf of HP" with no human_witness → E_HUMAN_WITNESS_REQUIRED (1010)

Each vector contains:
  request.{cbor,json}                       — IF→MS FAYING_REQUEST
  bootstrap-followup.{cbor,json}  (opt.)    — HP→MS BOOTSTRAP carrying faying_request_ref + human_witness
                                              (or for vec-08: BOOTSTRAP whose human_witness is missing —
                                              the path the protocol must reject)
  response.{cbor,json}                      — MS→IF FAYING_REQUEST_RESP (or BOOTSTRAP_RESP / ERROR)
  expected.json                             — outcome + Attestation Chain triple
                                              (initiator, confirm_ts, took_effect)

Field naming: per `schemas/types.ts` reference view, the on-the-wire keys are
snake_case (e.g. `msg_type`, `mandate_id`, `endorsed_scope`). CBOR encoding
uses Deterministic CBOR (RFC 8949 §4.2.1) for signature inputs.

Signatures: Ed25519 with deterministic seeds so vectors are reproducible byte
for byte.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cbor2
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

# ----------------------------------------------------------------------------
# Paths & constants
# ----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]  # vectors/faying-request/
PROTOCOL_VERSION = "Faying Protocol/1.0"
BOOTSTRAP_TIMEOUT_MS = 60_000  # default per appendix B

HUMAN_PRIME = "hp:prime-alice@example"
FAY_ID = "fay:alice/iFay-01"
MS_ID = "ms:alice-default"
RP_AUDIT_TS_BASE = "2026-01-15T09:00:00Z"


# ----------------------------------------------------------------------------
# Deterministic key material (test-only seeds — never use in production)
# ----------------------------------------------------------------------------

def _seed(name: str) -> bytes:
    return hashlib.sha256(("faying-request/test-seed/" + name).encode()).digest()


HP_SK = Ed25519PrivateKey.from_private_bytes(_seed("hp"))
HP_PK = HP_SK.public_key().public_bytes_raw() if hasattr(
    HP_SK.public_key(), "public_bytes_raw"
) else HP_SK.public_key().public_bytes(
    encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw,
    format=__import__("cryptography").hazmat.primitives.serialization.PublicFormat.Raw,
)

IF_SK = Ed25519PrivateKey.from_private_bytes(_seed("if"))
MS_SK = Ed25519PrivateKey.from_private_bytes(_seed("ms"))
PD_SK = Ed25519PrivateKey.from_private_bytes(_seed("pd"))


def _raw_pub(sk: Ed25519PrivateKey) -> bytes:
    from cryptography.hazmat.primitives import serialization
    return sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


HP_PK = _raw_pub(HP_SK)
IF_PK = _raw_pub(IF_SK)
MS_PK = _raw_pub(MS_SK)
PD_PK = _raw_pub(PD_SK)


# ----------------------------------------------------------------------------
# Helpers — Deterministic CBOR + signing
# ----------------------------------------------------------------------------

def det_cbor(obj: Any) -> bytes:
    """Deterministic CBOR per RFC 8949 §4.2.1 (canonical=True)."""
    return cbor2.dumps(obj, canonical=True)


def sign_detached(sk: Ed25519PrivateKey, payload_envelope_no_sig: dict) -> dict:
    """Compute SignatureBundle for a Faying Protocol envelope.

    Per design.md §6.3 the signature input is
        H( Deterministic-CBOR(Envelope_without_signature) )
    """
    canon = det_cbor(payload_envelope_no_sig)
    digest = hashlib.sha256(canon).digest()
    sig = sk.sign(digest)
    pk = _raw_pub(sk)
    return {
        "alg": "Ed25519",
        "pubkey": pk,
        "sig": sig,
    }


def webauthn_assertion(challenge: bytes, *, signed_by=PD_SK) -> dict:
    """Stub WebAuthn assertion: a self-attesting blob signed by the PD key."""
    auth_data = b"\x00" * 32 + b"\x05"  # rpIdHash + flags=UP|UV
    client_data = json.dumps(
        {
            "type": "webauthn.get",
            "challenge": challenge.hex(),
            "origin": "https://faying.example",
        },
        separators=(",", ":"),
        sort_keys=True,
    ).encode()
    sig = signed_by.sign(auth_data + hashlib.sha256(client_data).digest())
    return {
        "format": "webauthn",
        "payload": cbor2.dumps(
            {
                "auth_data": auth_data,
                "client_data_json": client_data,
                "user_present": True,
                "user_verified": True,
            },
            canonical=True,
        ),
        "signer": "pd:webauthn-key/alice",
        "signature": {
            "alg": "Ed25519",
            "pubkey": _raw_pub(signed_by),
            "sig": sig,
        },
    }


def self_signed_attestation(sk: Ed25519PrivateKey, signer: str, payload: bytes) -> dict:
    """A minimal self-signed attestation used as the `attestation` field of
    a Faying Protocol envelope (as opposed to the WebAuthn `human_witness`)."""
    sig = sk.sign(hashlib.sha256(payload).digest())
    return {
        "format": "self-signed",
        "payload": payload,
        "signer": signer,
        "signature": {
            "alg": "Ed25519",
            "pubkey": _raw_pub(sk),
            "sig": sig,
        },
    }


# ----------------------------------------------------------------------------
# Domain helpers
# ----------------------------------------------------------------------------

def make_scope(domains, actions, *, terminals=None, budget=None) -> dict:
    s = {"domains": list(domains), "actions": list(actions)}
    if terminals is not None:
        s["terminals"] = list(terminals)
    if budget is not None:
        s["budget"] = budget
    return s


def make_presence_req() -> dict:
    return {
        "signal_types": ["webauthn-uv-fresh", "presence-heartbeat-only"],
        "max_staleness_ms": 30_000,
        "on_loss": "downgrade-to:G3",
    }


def envelope(msg_type: str, msg_id: str, *, issued_at: str, expiry: str,
             nonce: bytes, grade: int, issuer: str, subject: str,
             claims: dict, attestation: dict, sk: Ed25519PrivateKey) -> dict:
    """Build a complete Faying Protocol envelope, sign it, and return the dict.
    The `signature` is computed over the deterministic CBOR encoding of the
    envelope without the `signature` field."""
    body = {
        "header": {
            "version": PROTOCOL_VERSION,
            "msg_type": msg_type,
            "msg_id": msg_id,
            "issued_at": issued_at,
            "expiry": expiry,
            "nonce": nonce,
            "grade": grade,
            "issuer": issuer,
            "subject": subject,
        },
        "claims": claims,
        "attestation": attestation,
    }
    sig = sign_detached(sk, body)
    body["signature"] = sig
    return body


# ----------------------------------------------------------------------------
# JSON serialisation: bytes → {"$b64": "..."} so the JSON form remains a
# faithful, lossless human-readable mirror of the canonical CBOR bytes.
# ----------------------------------------------------------------------------

import base64


def json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    if isinstance(value, tuple):
        return [json_safe(v) for v in value]
    if isinstance(value, (bytes, bytearray)):
        return {"$b64": base64.b64encode(bytes(value)).decode("ascii")}
    return value


def write_pair(out_dir: Path, name: str, obj: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    cbor_bytes = det_cbor(obj)
    (out_dir / f"{name}.cbor").write_bytes(cbor_bytes)
    (out_dir / f"{name}.json").write_text(
        json.dumps(json_safe(obj), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def write_expected(out_dir: Path, expected: dict) -> None:
    (out_dir / "expected.json").write_text(
        json.dumps(expected, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ----------------------------------------------------------------------------
# Vector builders
# ----------------------------------------------------------------------------

@dataclass
class VectorMeta:
    vid: str
    title: str
    reason_code: str | None
    outcome: str  # "effective" | "rejected" | "timeout" | "refused-no-witness"
    error_code: str | None  # "E_FAYING_REQUEST_NOT_CONFIRMED" | "E_HUMAN_WITNESS_REQUIRED" | None


def _common_proposed_scope() -> dict:
    return make_scope(
        domains=["calendar.example.com", "docs.example.com"],
        actions=["calendar:read", "docs:read"],
        terminals=["device:laptop-01"],
    )


def _faying_request_envelope(
    *,
    msg_id: str,
    nonce_seed: str,
    issued_at: str,
    reason_code: str,
    reason_text: str,
    proposed_scope: dict,
    proposed_grade: int,
    expected_lifetime_ms: int | None = None,
    proposed_endorsement: dict | None = None,
) -> dict:
    nonce = hashlib.sha256(("nonce/" + nonce_seed).encode()).digest()[:16]
    claims: dict[str, Any] = {
        "initiator": FAY_ID,
        "target_human": HUMAN_PRIME,
        "proposed_scope": proposed_scope,
        "proposed_grade": proposed_grade,
        "reason": reason_text,
        "reason_code": reason_code,
    }
    if expected_lifetime_ms is not None:
        claims["expected_lifetime_ms"] = expected_lifetime_ms
    if proposed_endorsement is not None:
        claims["proposed_endorsement"] = proposed_endorsement

    return envelope(
        msg_type="FAYING_REQUEST",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=_iso_plus_ms(issued_at, BOOTSTRAP_TIMEOUT_MS),
        nonce=nonce,
        grade=4,  # iFay sends from its current (most permissive) self-grade only
                  # — the *proposed_grade* lives in claims; this header.grade is
                  # the *current* session grade held by the iFay envelope.
        issuer=HUMAN_PRIME,
        subject=FAY_ID,
        claims=claims,
        attestation=self_signed_attestation(
            IF_SK,
            signer="if:" + FAY_ID,
            payload=b"if-self-attestation:" + msg_id.encode(),
        ),
        sk=IF_SK,
    )


def _bootstrap_envelope(
    *,
    msg_id: str,
    nonce_seed: str,
    issued_at: str,
    not_after_iso: str,
    proposed_scope: dict,
    proposed_grade: int,
    faying_request_ref: str,
    include_human_witness: bool,
    proposed_endorsement: dict | None = None,
    sk: Ed25519PrivateKey = HP_SK,
    issuer_override: str | None = None,
) -> dict:
    nonce = hashlib.sha256(("nonce/" + nonce_seed).encode()).digest()[:16]
    claims: dict[str, Any] = {
        "human_prime": HUMAN_PRIME,
        "fay": FAY_ID,
        "scope": proposed_scope,
        "grade": proposed_grade,
        "presence_req": make_presence_req(),
        "not_after": not_after_iso,
        "faying_request_ref": faying_request_ref,
    }
    if include_human_witness:
        claims["human_witness"] = webauthn_assertion(
            challenge=hashlib.sha256(("challenge/" + faying_request_ref).encode()).digest(),
        )
    if proposed_endorsement is not None:
        claims["endorsement"] = proposed_endorsement

    return envelope(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=_iso_plus_ms(issued_at, 5_000),
        nonce=nonce,
        grade=proposed_grade,
        issuer=issuer_override or HUMAN_PRIME,
        subject=FAY_ID,
        claims=claims,
        attestation=self_signed_attestation(
            sk,
            signer=("hp:" + HUMAN_PRIME) if sk is HP_SK else (
                "ms:" + MS_ID if sk is MS_SK else "if:" + FAY_ID
            ),
            payload=b"bootstrap-attestation:" + msg_id.encode(),
        ),
        sk=sk,
    )


def _faying_request_resp_envelope(
    *,
    msg_id: str,
    issued_at: str,
    request_msg_id: str,
    status: str,
    bootstrap_ref: str | None = None,
    reject_reason: str | None = None,
    nonce_seed: str | None = None,
) -> dict:
    nonce = hashlib.sha256(("nonce/" + (nonce_seed or msg_id)).encode()).digest()[:16]
    claims: dict[str, Any] = {
        "request_msg_id": request_msg_id,
        "status": status,
    }
    if bootstrap_ref is not None:
        claims["bootstrap_ref"] = bootstrap_ref
    if reject_reason is not None:
        claims["reject_reason"] = reject_reason

    return envelope(
        msg_type="FAYING_REQUEST_RESP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=_iso_plus_ms(issued_at, 30_000),
        nonce=nonce,
        grade=4,
        issuer=MS_ID,
        subject=FAY_ID,
        claims=claims,
        attestation=self_signed_attestation(
            MS_SK,
            signer="ms:" + MS_ID,
            payload=b"ms-resp-attestation:" + msg_id.encode(),
        ),
        sk=MS_SK,
    )


def _error_envelope(
    *,
    msg_id: str,
    issued_at: str,
    code: int,
    name: str,
    message: str,
    request_ref: str,
    mandate_id: str | None = None,
    recovery_hint: str | None = None,
) -> dict:
    nonce = hashlib.sha256(("nonce/error/" + msg_id).encode()).digest()[:16]
    claims: dict[str, Any] = {
        "code": code,
        "code_name": name,
        "message": message,
        "request_ref": request_ref,
    }
    if mandate_id is not None:
        claims["mandate_id"] = mandate_id
    if recovery_hint is not None:
        claims["recovery_hint"] = recovery_hint

    return envelope(
        msg_type="ERROR",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=_iso_plus_ms(issued_at, 10_000),
        nonce=nonce,
        grade=4,
        issuer=MS_ID,
        subject=FAY_ID,
        claims=claims,
        attestation=self_signed_attestation(
            MS_SK,
            signer="ms:" + MS_ID,
            payload=b"ms-error-attestation:" + msg_id.encode(),
        ),
        sk=MS_SK,
    )


# ----------------------------------------------------------------------------
# ISO time arithmetic (kept simple — vectors use whole-second timestamps)
# ----------------------------------------------------------------------------

from datetime import datetime, timedelta, timezone


def _parse(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(timezone.utc)


def _fmt(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _iso_plus_ms(iso: str, ms: int) -> str:
    return _fmt(_parse(iso) + timedelta(milliseconds=ms))


# ----------------------------------------------------------------------------
# Vector definitions
# ----------------------------------------------------------------------------

def build_happy_path(
    *,
    vid: str,
    reason_code: str,
    reason_text: str,
    proposed_scope: dict,
    proposed_grade: int,
    expected_lifetime_ms: int = 12 * 3600 * 1000,
    proposed_endorsement: dict | None = None,
) -> tuple[VectorMeta, Path]:
    out = ROOT / vid
    if out.exists():
        shutil.rmtree(out)

    t_request = "2026-01-15T09:00:00Z"
    t_bootstrap = "2026-01-15T09:00:30Z"  # 30s — within BootstrapTimeout
    t_resp = "2026-01-15T09:00:31Z"

    req = _faying_request_envelope(
        msg_id=f"req:{vid}:01HZZ0000000000000000{vid[-2:]}",
        nonce_seed=f"{vid}/req",
        issued_at=t_request,
        reason_code=reason_code,
        reason_text=reason_text,
        proposed_scope=proposed_scope,
        proposed_grade=proposed_grade,
        expected_lifetime_ms=expected_lifetime_ms,
        proposed_endorsement=proposed_endorsement,
    )

    bootstrap = _bootstrap_envelope(
        msg_id=f"bs:{vid}:01HZZ0000000000000001{vid[-2:]}",
        nonce_seed=f"{vid}/bs",
        issued_at=t_bootstrap,
        not_after_iso=_iso_plus_ms(t_bootstrap, expected_lifetime_ms),
        proposed_scope=proposed_scope,
        proposed_grade=proposed_grade,
        faying_request_ref=req["header"]["msg_id"],
        include_human_witness=True,
        proposed_endorsement=proposed_endorsement,
    )

    resp = _faying_request_resp_envelope(
        msg_id=f"resp:{vid}:01HZZ0000000000000002{vid[-2:]}",
        issued_at=t_resp,
        request_msg_id=req["header"]["msg_id"],
        status="accepted",
        bootstrap_ref=bootstrap["header"]["msg_id"],
    )

    write_pair(out, "request", req)
    write_pair(out, "bootstrap-followup", bootstrap)
    write_pair(out, "response", resp)

    expected = {
        "vid": vid,
        "title": f"IF-initiated FAYING_REQUEST({reason_code}) confirmed by HP within BootstrapTimeout",
        "outcome": "effective",
        "error_code": None,
        "spec_refs": [
            "§1.5.1 双向 Faying 由 HP 显式认可生效",
            "§2.4 Phase A0 — iFay-Initiated Faying Request",
            "§5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP",
        ],
        "requirements": ["1.3", "11.1"],
        "bootstrap_timeout_ms": BOOTSTRAP_TIMEOUT_MS,
        "timing": {
            "t_request": t_request,
            "t_bootstrap": t_bootstrap,
            "t_response": t_resp,
            "elapsed_ms_request_to_bootstrap": 30_000,
            "within_bootstrap_timeout": True,
        },
        "attestation_chain_entry": {
            "initiator": FAY_ID,
            "confirm_ts": t_bootstrap,
            "took_effect": True,
            "evidence": {
                "faying_request_msg_id": req["header"]["msg_id"],
                "bootstrap_msg_id": bootstrap["header"]["msg_id"],
                "human_witness_present": True,
                "human_witness_format": "webauthn",
                "faying_request_resp_msg_id": resp["header"]["msg_id"],
                "response_status": "accepted",
                "issuer_after_effect": HUMAN_PRIME,
            },
        },
        "hardness_checks": {
            "hp_witness_irreplaceable": True,
            "ms_cannot_surrogate_witness": True,
            "if_cannot_self_witness": True,
            "supervisory_agent_cannot_surrogate_witness": True,
        },
    }
    write_expected(out, expected)
    return (
        VectorMeta(vid=vid, title=expected["title"],
                   reason_code=reason_code,
                   outcome="effective", error_code=None),
        out,
    )


def build_hp_rejected(vid: str = "vec-06-hp-rejected") -> tuple[VectorMeta, Path]:
    out = ROOT / vid
    if out.exists():
        shutil.rmtree(out)

    t_request = "2026-01-15T10:00:00Z"
    t_resp = "2026-01-15T10:00:25Z"  # within BootstrapTimeout but HP says no

    req = _faying_request_envelope(
        msg_id=f"req:{vid}:01HZZ1000000000000000",
        nonce_seed=f"{vid}/req",
        issued_at=t_request,
        reason_code="establish",
        reason_text="iFay 请求初次建立 Faying（HP 不同意此次请求范围）",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=2,
        expected_lifetime_ms=4 * 3600 * 1000,
    )

    resp = _faying_request_resp_envelope(
        msg_id=f"resp:{vid}:01HZZ1000000000000001",
        issued_at=t_resp,
        request_msg_id=req["header"]["msg_id"],
        status="rejected",
        reject_reason="HP-explicit-reject: scope-too-broad",
    )

    write_pair(out, "request", req)
    write_pair(out, "response", resp)

    expected = {
        "vid": vid,
        "title": "HP explicitly rejects the IF-initiated FAYING_REQUEST",
        "outcome": "rejected",
        "error_code": None,
        "spec_refs": [
            "§5.3.6 FAYING_REQUEST_RESP { status='rejected' }",
            "§2.4 Phase A0 — HP rejects branch",
        ],
        "requirements": ["1.3"],
        "bootstrap_timeout_ms": BOOTSTRAP_TIMEOUT_MS,
        "timing": {
            "t_request": t_request,
            "t_response": t_resp,
            "elapsed_ms_request_to_response": 25_000,
            "within_bootstrap_timeout": True,
        },
        "attestation_chain_entry": {
            "initiator": FAY_ID,
            "confirm_ts": t_resp,
            "took_effect": False,
            "evidence": {
                "faying_request_msg_id": req["header"]["msg_id"],
                "faying_request_resp_msg_id": resp["header"]["msg_id"],
                "response_status": "rejected",
                "reject_reason": "HP-explicit-reject: scope-too-broad",
                "bootstrap_msg_id": None,
                "human_witness_present": False,
            },
        },
        "hardness_checks": {
            "no_state_change": True,
            "hp_witness_irreplaceable": True,
        },
    }
    write_expected(out, expected)
    return (
        VectorMeta(vid=vid, title=expected["title"], reason_code="establish",
                   outcome="rejected", error_code=None),
        out,
    )


def build_bootstrap_timeout(vid: str = "vec-07-bootstrap-timeout") -> tuple[VectorMeta, Path]:
    out = ROOT / vid
    if out.exists():
        shutil.rmtree(out)

    t_request = "2026-01-15T11:00:00Z"
    t_resp = "2026-01-15T11:01:01Z"  # 61s — past BootstrapTimeout (60 s)

    req = _faying_request_envelope(
        msg_id=f"req:{vid}:01HZZ2000000000000000",
        nonce_seed=f"{vid}/req",
        issued_at=t_request,
        reason_code="adjust-grade",
        reason_text="iFay 请求短暂提升至 G2，但 HP 未在 60s 内做出认可确认",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=2,
        expected_lifetime_ms=2 * 3600 * 1000,
    )

    resp = _faying_request_resp_envelope(
        msg_id=f"resp:{vid}:01HZZ2000000000000001",
        issued_at=t_resp,
        request_msg_id=req["header"]["msg_id"],
        status="timeout",
    )

    error = _error_envelope(
        msg_id=f"err:{vid}:01HZZ2000000000000002",
        issued_at=t_resp,
        code=1014,
        name="E_FAYING_REQUEST_NOT_CONFIRMED",
        message="iFay-initiated FAYING_REQUEST not confirmed by HP within BootstrapTimeout",
        request_ref=req["header"]["msg_id"],
    )

    write_pair(out, "request", req)
    write_pair(out, "response", resp)
    write_pair(out, "error", error)

    expected = {
        "vid": vid,
        "title": "BootstrapTimeout exceeded without HP confirmation → E_FAYING_REQUEST_NOT_CONFIRMED (1014)",
        "outcome": "timeout",
        "error_code": "E_FAYING_REQUEST_NOT_CONFIRMED",
        "error_code_numeric": 1014,
        "spec_refs": [
            "§5.4 错误码 1014 E_FAYING_REQUEST_NOT_CONFIRMED",
            "§5.3.6 — timeout branch",
            "§1.5.1 三条不可逾越的硬约束 (1)",
        ],
        "requirements": ["1.3"],
        "bootstrap_timeout_ms": BOOTSTRAP_TIMEOUT_MS,
        "timing": {
            "t_request": t_request,
            "t_response": t_resp,
            "elapsed_ms_request_to_response": 61_000,
            "within_bootstrap_timeout": False,
        },
        "attestation_chain_entry": {
            "initiator": FAY_ID,
            "confirm_ts": t_resp,
            "took_effect": False,
            "evidence": {
                "faying_request_msg_id": req["header"]["msg_id"],
                "faying_request_resp_msg_id": resp["header"]["msg_id"],
                "response_status": "timeout",
                "error_msg_id": error["header"]["msg_id"],
                "error_code_numeric": 1014,
                "error_code_name": "E_FAYING_REQUEST_NOT_CONFIRMED",
                "bootstrap_msg_id": None,
                "human_witness_present": False,
            },
            "audit_required": True,
            "hp_view_required": False,
        },
        "hardness_checks": {
            "no_state_change": True,
            "hp_witness_irreplaceable": True,
            "audit_records_three_step_triple": True,
        },
    }
    write_expected(out, expected)
    return (
        VectorMeta(vid=vid, title=expected["title"], reason_code="adjust-grade",
                   outcome="timeout", error_code="E_FAYING_REQUEST_NOT_CONFIRMED"),
        out,
    )


def build_forged_ms_surrogate(vid: str = "vec-08-forged-ms-surrogate") -> tuple[VectorMeta, Path]:
    """Forged 'MS confirms on behalf of HP' path:

    The MS (or any party other than HP) tries to dispatch a BOOTSTRAP that
    references the FAYING_REQUEST but **does not carry a `human_witness`**.
    Per Requirement 1.3 #5 and §5.3.6 hardness rule #3, this attempt MUST be
    rejected with `E_HUMAN_WITNESS_REQUIRED` (1010).
    """
    out = ROOT / vid
    if out.exists():
        shutil.rmtree(out)

    t_request = "2026-01-15T12:00:00Z"
    t_bootstrap = "2026-01-15T12:00:15Z"
    t_resp = "2026-01-15T12:00:16Z"

    req = _faying_request_envelope(
        msg_id=f"req:{vid}:01HZZ3000000000000000",
        nonce_seed=f"{vid}/req",
        issued_at=t_request,
        reason_code="establish",
        reason_text="iFay 请求建立 Faying；攻击者尝试由 MS 替 HP 同意（缺 human_witness）",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=3,
        expected_lifetime_ms=2 * 3600 * 1000,
    )

    # The forged BOOTSTRAP: MS-issued, MS-signed, references the FAYING_REQUEST,
    # but `human_witness` is *missing* — protocol-illegal per §5.3.6 hardness rule
    # "不存在任何由 MS / IF / Supervisory Agent 替代 HP 完成认可确认的合法路径".
    bootstrap_forged = _bootstrap_envelope(
        msg_id=f"bs:{vid}:01HZZ3000000000000001",
        nonce_seed=f"{vid}/bs",
        issued_at=t_bootstrap,
        not_after_iso=_iso_plus_ms(t_bootstrap, 2 * 3600 * 1000),
        proposed_scope=_common_proposed_scope(),
        proposed_grade=3,
        faying_request_ref=req["header"]["msg_id"],
        include_human_witness=False,           # ← forgery signal
        sk=MS_SK,                              # ← forged: signed by MS, not HP
        issuer_override=MS_ID,                 # ← forged: claims MS as issuer
    )

    error = _error_envelope(
        msg_id=f"err:{vid}:01HZZ3000000000000002",
        issued_at=t_resp,
        code=1010,
        name="E_HUMAN_WITNESS_REQUIRED",
        message="BOOTSTRAP references a FAYING_REQUEST but carries no verifiable human_witness; "
                "MS/IF/Supervisory Agent cannot surrogate the HP witness.",
        request_ref=req["header"]["msg_id"],
    )

    write_pair(out, "request", req)
    write_pair(out, "bootstrap-followup", bootstrap_forged)
    write_pair(out, "error", error)

    expected = {
        "vid": vid,
        "title": "Forged 'MS confirms on behalf of HP' path → E_HUMAN_WITNESS_REQUIRED (1010)",
        "outcome": "rejected",
        "error_code": "E_HUMAN_WITNESS_REQUIRED",
        "error_code_numeric": 1010,
        "spec_refs": [
            "§5.4 错误码 1010 E_HUMAN_WITNESS_REQUIRED",
            "§5.3.6 协议层硬约束第 3 条（不存在 MS/IF/SA 替代 HP 认可的合法路径）",
            "§1.5.1 三条不可逾越的硬约束 (2)",
            "Requirement 1.3 #5",
        ],
        "requirements": ["1.3"],
        "bootstrap_timeout_ms": BOOTSTRAP_TIMEOUT_MS,
        "timing": {
            "t_request": t_request,
            "t_forged_bootstrap": t_bootstrap,
            "t_error": t_resp,
            "elapsed_ms_request_to_forged_bootstrap": 15_000,
            "within_bootstrap_timeout": True,
        },
        "forged_path": {
            "purported_issuer": MS_ID,
            "actual_signer_role": "Mandate_Service",
            "human_witness_present": False,
            "faying_request_ref_present": True,
        },
        "attestation_chain_entry": {
            "initiator": FAY_ID,
            "confirm_ts": t_resp,
            "took_effect": False,
            "evidence": {
                "faying_request_msg_id": req["header"]["msg_id"],
                "forged_bootstrap_msg_id": bootstrap_forged["header"]["msg_id"],
                "human_witness_present": False,
                "error_msg_id": error["header"]["msg_id"],
                "error_code_numeric": 1010,
                "error_code_name": "E_HUMAN_WITNESS_REQUIRED",
                "rejected_surrogate_witness_party": "Mandate_Service",
            },
            "audit_required": True,
            "hp_view_required": False,
        },
        "hardness_checks": {
            "no_state_change": True,
            "hp_witness_irreplaceable": True,
            "ms_cannot_surrogate_witness": True,
            "if_cannot_self_witness": True,
            "supervisory_agent_cannot_surrogate_witness": True,
        },
    }
    write_expected(out, expected)
    return (
        VectorMeta(vid=vid, title=expected["title"], reason_code="establish",
                   outcome="refused-no-witness",
                   error_code="E_HUMAN_WITNESS_REQUIRED"),
        out,
    )


# ----------------------------------------------------------------------------
# Build all
# ----------------------------------------------------------------------------

def main() -> None:
    metas: list[VectorMeta] = []

    # (a) + (b): one per reason_code (5 vectors)
    metas.append(build_happy_path(
        vid="vec-01-establish",
        reason_code="establish",
        reason_text="iFay 请求初次建立 Faying：开始一段持续监护关系",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=3,
        expected_lifetime_ms=12 * 3600 * 1000,
    )[0])

    metas.append(build_happy_path(
        vid="vec-02-adjust-scope",
        reason_code="adjust-scope",
        reason_text="iFay 请求扩展 scope：在现有 Mandate 之外纳入 docs.example.com 读权限",
        proposed_scope=make_scope(
            domains=["calendar.example.com", "docs.example.com", "mail.example.com"],
            actions=["calendar:read", "docs:read", "mail:read"],
            terminals=["device:laptop-01"],
        ),
        proposed_grade=3,
        expected_lifetime_ms=8 * 3600 * 1000,
    )[0])

    metas.append(build_happy_path(
        vid="vec-03-adjust-grade",
        reason_code="adjust-grade",
        reason_text="iFay 请求短暂提升至 G2 以执行一次更敏感的协作动作",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=2,
        expected_lifetime_ms=1 * 3600 * 1000,
    )[0])

    metas.append(build_happy_path(
        vid="vec-04-renew",
        reason_code="renew",
        reason_text="iFay 请求续期：原 Mandate 即将到期，请求顺延一段同等条件的窗口",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=3,
        expected_lifetime_ms=12 * 3600 * 1000,
    )[0])

    # endorsement-request: ask for an Endorsed Mandate at the same time.
    endorsed_scope = make_scope(
        domains=["calendar.example.com"],
        actions=["calendar:read"],
        terminals=["device:laptop-01"],
    )
    proposed_endorsement = {
        "enabled": True,
        "endorsed_scope": endorsed_scope,
        "endorsed_grade": 3,                 # ≤ proposed_grade=3 (same here)
        "endorsed_lifetime_ms": 4 * 3600 * 1000,
        "offline_revocation_policy": "stop-and-audit",
    }
    metas.append(build_happy_path(
        vid="vec-05-endorsement-request",
        reason_code="endorsement-request",
        reason_text="iFay 请求 Endorsed Mandate：在限定 endorsed_scope 内允许失联期间继续读日历",
        proposed_scope=_common_proposed_scope(),
        proposed_grade=3,
        expected_lifetime_ms=12 * 3600 * 1000,
        proposed_endorsement=proposed_endorsement,
    )[0])

    # (c) HP explicit reject
    metas.append(build_hp_rejected()[0])

    # (d) BootstrapTimeout
    metas.append(build_bootstrap_timeout()[0])

    # (e) Forged "MS confirms on behalf of HP"
    metas.append(build_forged_ms_surrogate()[0])

    # ------------------------------------------------------------------
    # index.json
    # ------------------------------------------------------------------
    index = {
        "vector_set": "vectors/faying-request",
        "protocol": PROTOCOL_VERSION,
        "spec_refs": [
            "§1.5.1 双向 Faying 由 HP 显式认可生效",
            "§2.4 Phase A0 — iFay-Initiated Faying Request",
            "§5.3.6 FAYING_REQUEST / FAYING_REQUEST_RESP",
            "§5.4 错误码 1010 / 1014",
        ],
        "requirements": ["1.3", "11.1"],
        "bootstrap_timeout_ms": BOOTSTRAP_TIMEOUT_MS,
        "encoding": {
            "primary": "CBOR (RFC 8949), deterministic per §4.2.1",
            "fallback": "JSON mirror with bytes encoded as { \"$b64\": ... }",
            "signature_input": "SHA-256(Deterministic-CBOR(Envelope_without_signature))",
            "signature_alg": "Ed25519",
            "deterministic_seeds": "vectors are byte-reproducible from _tools/generate.py",
        },
        "vectors": [
            {
                "vid": m.vid,
                "title": m.title,
                "reason_code": m.reason_code,
                "outcome": m.outcome,
                "error_code": m.error_code,
                "files": [
                    "request.cbor", "request.json",
                    *(["bootstrap-followup.cbor", "bootstrap-followup.json"]
                      if (ROOT / m.vid / "bootstrap-followup.cbor").exists() else []),
                    *(["response.cbor", "response.json"]
                      if (ROOT / m.vid / "response.cbor").exists() else []),
                    *(["error.cbor", "error.json"]
                      if (ROOT / m.vid / "error.cbor").exists() else []),
                    "expected.json",
                ],
            }
            for m in metas
        ],
    }
    (ROOT / "index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Generated {len(metas)} vectors at {ROOT}")
    for m in metas:
        print(f"  - {m.vid:30s} reason={m.reason_code or '—':22s} "
              f"outcome={m.outcome:18s} err={m.error_code or '—'}")


if __name__ == "__main__":
    main()
