#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faying Protocol/1.0 — Error code test vector generator
========================================================

Generates official, deterministic test vectors for every error code in
§5.4 / §EH.1 of the spec doc:

    1001 1002 1003 1004 1005 1006 1007 1008 1009 1010 1011 1012 1013 1014 1099

For each code, this script writes:

    vectors/errors/<code>-<NAME>/trigger.cbor
    vectors/errors/<code>-<NAME>/trigger.json
    vectors/errors/<code>-<NAME>/error.cbor
    vectors/errors/<code>-<NAME>/error.json
    vectors/errors/<code>-<NAME>/expected.json

It also emits the directory-level index:

    vectors/errors/index.json

NOTES
-----
* CBOR encoding follows RFC 8949 with deterministic options
  (canonical=True, sort_keys=True) — i.e. RFC 8949 §4.2.1 deterministic
  encoding profile. This matches §6.3 S2 of the spec doc.

* JSON is a NON-NORMATIVE debug fallback per §5.1; it carries the same
  field-level semantics as CBOR. Bytes / nonces are encoded as hex
  strings in JSON for readability.

* Triggers and error envelopes are SCHEMA-LEVEL examples. Real signature
  bundles are stubbed (alg/pubkey/sig are constants) — the goal of this
  vector set is to exercise the FIELD-LEVEL error-trigger conditions and
  the ERROR-envelope shape, NOT to verify cryptographic signatures
  (see vectors/bootstrap/, vectors/presence/ for crypto-bearing vectors).

* Error envelopes carry ONLY public-semantics fields per §EH.3 #3:
  no MS internal state, no private-key fingerprints, no other HP
  identifiers. The expected.json file declares the audit-log 5-tuple
  the protocol REQUIRES and the must-push-hp-view boolean.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import cbor2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent

# Reference instant. All vectors use a fixed reference now() so the corpus
# is fully deterministic and can be checked into git.
T_NOW = "2025-12-17T12:00:00Z"
T_BEFORE = "2025-12-17T11:00:00Z"
T_AFTER = "2025-12-17T13:00:00Z"
T_PAST_BEFORE = "2024-12-17T00:00:00Z"
T_PAST_AFTER = "2024-12-18T00:00:00Z"          # already expired at T_NOW
T_LONG_AFTER = "2025-12-18T11:00:00Z"          # 24h after not_before

# Stable IDs / fingerprints used across vectors
HP_ID = "hp:01HXR000000000000000000HP"
MS_ID = "ms:fap-test-ms-1"
RP_ID = "rp:fap-test-rp-1"
FAY_ID = "fay:01HXR000000000000000000IF"
MANDATE_ID = "mnd:01HXR000000000000000ACTIVE"
MANDATE_ID_REVOKED = "mnd:01HXR000000000000REVOKED"
MANDATE_ID_BUDGET = "mnd:01HXR000000000000BUDGET"
MANDATE_ID_DEGR = "mnd:01HXR000000000000DEGRADE"
MANDATE_ID_RR = "mnd:01HXR0000000000000000RRX"
MANDATE_ID_TAMPER = "mnd:01HXR00000000000TAMPERED"
DEVICE_ID = "dev:macbook-air-m2-test"
NONCE_HEX_A = "00112233445566778899aabbccddeeff"
NONCE_HEX_B = "0123456789abcdef0123456789abcdef"
NONCE_REPLAY = "deadbeefdeadbeefdeadbeefdeadbeef"

# Stub crypto material (for shape-level vectors)
PUBKEY_HEX = "11" * 32
SIG_HEX = "22" * 64
PUBKEY_HP_HEX = "33" * 32
SIG_HP_HEX = "44" * 64

# Authoritative error code table (§5.4 / §EH.1)
ERROR_CODES: list[dict[str, Any]] = [
    {
        "code": 1001,
        "name": "E_NO_MANDATE",
        "summary": "请求未携带 Mandate",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": False,
        "hp_view": False,
        "trace": ["R2.1.1"],
    },
    {
        "code": 1002,
        "name": "E_MANDATE_EXPIRED",
        "summary": "Mandate 已过期（now > Mandate.not_after）",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R2.2.4"],
    },
    {
        "code": 1003,
        "name": "E_SCOPE_VIOLATION",
        "summary": "调用动作 ∉ Mandate.scope.actions",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R2.1.2"],
    },
    {
        "code": 1004,
        "name": "E_GRADE_INSUFFICIENT",
        "summary": "RP 要求的 grade 强于当前 Mandate.grade",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R6.3.3"],
    },
    {
        "code": 1005,
        "name": "E_PRESENCE_STALE",
        "summary": "presence.last_freshness 超过 max_staleness_ms",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R5.1.2"],
    },
    {
        "code": 1006,
        "name": "E_REVOKED",
        "summary": "Mandate 已撤销",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": True,
        "trace": ["R4.3.1", "R3.2.3"],
    },
    {
        "code": 1007,
        "name": "E_ATTESTATION_INVALID",
        "summary": "Attestation Chain 节点签名校验失败 / endorsement 篡改",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": True,
        "trace": ["R3.1.3", "R11.1.4"],
    },
    {
        "code": 1008,
        "name": "E_RR_UNAVAILABLE",
        "summary": "RR 查询超时 ≥ StaleBudget",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R2.1.4", "R4.2.4"],
    },
    {
        "code": 1009,
        "name": "E_REPLAY",
        "summary": "nonce 在 2 × max_message_lifetime 内对相同 subject 已被见",
        "trigger_msg_type": "PRESENCE",
        "audit": True,
        "hp_view": True,
        "trace": ["R9.1.2", "R3.2.3"],
    },
    {
        "code": 1010,
        "name": "E_HUMAN_WITNESS_REQUIRED",
        "summary": "等级升级 / 双向 Faying 缺人类见证",
        "trigger_msg_type": "GRADE_SWITCH",
        "audit": True,
        "hp_view": False,
        "trace": ["R6.1.2"],
    },
    {
        "code": 1011,
        "name": "E_ROGUE_DETECTED",
        "summary": "检测到 Rogue 行为（ego-deviation / 行为基线超阈）",
        "trigger_msg_type": "DISCLOSURE",
        "audit": True,
        "hp_view": True,
        "trace": ["R9.4.5", "R3.2.3"],
    },
    {
        "code": 1012,
        "name": "E_BUDGET_EXCEEDED",
        "summary": "调用累计超过 Scope.budget / ResourceBudget",
        "trigger_msg_type": "BUSINESS_CALL",
        "audit": True,
        "hp_view": False,
        "trace": ["R2.1.3"],
    },
    {
        "code": 1013,
        "name": "E_ENDORSEMENT_INVALID",
        "summary": "endorsement 收敛违反 / 篡改 / lifetime 越界",
        "trigger_msg_type": "BOOTSTRAP",
        "audit": True,
        "hp_view": True,
        "trace": ["R11.2.4", "R3.2.3"],
    },
    {
        "code": 1014,
        "name": "E_FAYING_REQUEST_NOT_CONFIRMED",
        "summary": "iFay 主动 FAYING_REQUEST 在 BootstrapTimeout 内未获 HP 见证",
        "trigger_msg_type": "FAYING_REQUEST",
        "audit": True,
        "hp_view": False,
        "trace": ["R1.3.3"],
    },
    {
        "code": 1099,
        "name": "E_PROTOCOL",
        "summary": "协议层错误（DISCLOSURE mandatory_fields 缺失或不可解析）",
        "trigger_msg_type": "DISCLOSURE",
        "audit": True,
        # 1099 default does NOT push to HP view; but DISCLOSURE-triggered
        # variant MUST. The vector below uses the DISCLOSURE path so we
        # set must-push-hp-view = True per §5.4 footnote.
        "hp_view": True,
        "trace": ["R13.3.1"],
    },
]

# ---------------------------------------------------------------------------
# Common envelope builders
# ---------------------------------------------------------------------------


def signature_bundle(stub: bool = True) -> dict[str, Any]:
    """A shape-level signature bundle. Real crypto verification is the
    domain of vectors/bootstrap/ and vectors/presence/.
    """
    return {
        "alg": "Ed25519",
        "pubkey_hex": PUBKEY_HEX,
        "sig_hex": SIG_HEX,
    }


def attestation(format_: str = "self-signed", payload_bytes: bytes = b"") -> dict[str, Any]:
    return {
        "format": format_,
        "payload_hex": payload_bytes.hex(),
        "signer": "presence-device-1",
        "signature": signature_bundle(),
    }


def envelope(
    msg_type: str,
    msg_id: str,
    grade: int,
    subject: str,
    issuer: str,
    claims: dict[str, Any],
    *,
    issued_at: str = T_NOW,
    expiry: str = T_AFTER,
    nonce_hex: str = NONCE_HEX_A,
) -> dict[str, Any]:
    return {
        "header": {
            "version": "Faying Protocol/1.0",
            "msg_type": msg_type,
            "msg_id": msg_id,
            "issued_at": issued_at,
            "expiry": expiry,
            "nonce_hex": nonce_hex,
            "grade": grade,
            "issuer": issuer,
            "subject": subject,
        },
        "claims": claims,
        "attestation": attestation(),
        "signature": signature_bundle(),
    }


def error_envelope(
    code: int,
    name: str,
    *,
    mandate_id: str | None,
    message: str,
    recovery_hint: str | None,
    msg_id: str,
    issuer: str = MS_ID,
    subject: str = FAY_ID,
    grade: int = 3,
) -> dict[str, Any]:
    """Build the canonical ERROR envelope per §5.2 / §5.4.

    `claims` body shape: { code, message, mandate_id?, recovery_hint? }.

    Per §EH.3 #3: the error response MUST NOT carry MS internal state,
    private-key fingerprints, or other HP identifiers. We deliberately
    keep `message` and `recovery_hint` to public-semantics strings only.
    """
    claims: dict[str, Any] = {
        "code": code,
        "name": name,        # not strictly required by §5.4; kept for human readability
        "message": message,
    }
    if mandate_id is not None:
        claims["mandate_id"] = mandate_id
    if recovery_hint is not None:
        claims["recovery_hint"] = recovery_hint

    return envelope(
        msg_type="ERROR",
        msg_id=msg_id,
        grade=grade,
        subject=subject,
        issuer=issuer,
        claims=claims,
        issued_at=T_NOW,
        expiry=T_AFTER,
        nonce_hex=NONCE_HEX_B,
    )


# ---------------------------------------------------------------------------
# Per-error trigger builders
# ---------------------------------------------------------------------------

# A reusable scope/grade/Mandate skeleton
DEFAULT_SCOPE = {
    "domains": ["api.example.com"],
    "actions": ["read:profile"],
}


def mandate_skeleton(
    *,
    id_: str = MANDATE_ID,
    not_before: str = T_BEFORE,
    not_after: str = T_LONG_AFTER,
    grade: int = 3,
    scope: dict[str, Any] | None = None,
    endorsement: dict[str, Any] | None = None,
    parent: str | None = None,
    tampered_attestation: bool = False,
) -> dict[str, Any]:
    m: dict[str, Any] = {
        "version": "Faying Protocol/1.0",
        "id": id_,
        "issued_at": T_BEFORE,
        "not_before": not_before,
        "not_after": not_after,
        "issuer": HP_ID,
        "ms_id": MS_ID,
        "subject": FAY_ID,
        "scope": scope if scope is not None else DEFAULT_SCOPE,
        "grade": grade,
        "presence_req": {
            "signal_types": ["fingerprint-tap"],
            "max_staleness_ms": 60_000,
            "on_loss": "downgrade-to:G3",
        },
        "attestation": attestation(
            format_="webauthn",
            payload_bytes=b"\x00\x01\x02\x03" if not tampered_attestation else b"\xff\xff\xff\xff",
        ),
        "signature": signature_bundle(),
    }
    if parent is not None:
        m["parent"] = parent
    if endorsement is not None:
        m["endorsement"] = endorsement
    return m


def business_call(
    *,
    action: str,
    mandate: dict[str, Any] | None,
    extra: dict[str, Any] | None = None,
    msg_id: str = "msg:business-call-0001",
) -> dict[str, Any]:
    """Synthetic BUSINESS_CALL container: not part of the §5.3 message
    set, but used to schematize the application-layer call that an RP
    receives carrying (or lacking) a Mandate. It is wrapped in the
    standard envelope for round-trip consistency with §5.2.
    """
    claims: dict[str, Any] = {
        "operation": action,
        "rp_id": RP_ID,
        "called_at": T_NOW,
        "mandate": mandate,
    }
    if extra is not None:
        claims.update(extra)
    return envelope(
        msg_type="BUSINESS_CALL",
        msg_id=msg_id,
        grade=mandate["grade"] if mandate else 3,
        subject=FAY_ID,
        issuer=HP_ID,
        claims=claims,
    )


# ---- 1001 E_NO_MANDATE ----

def trigger_1001() -> dict[str, Any]:
    return business_call(
        action="read:profile",
        mandate=None,
        msg_id="msg:err-1001-trigger",
    )


# ---- 1002 E_MANDATE_EXPIRED ----

def trigger_1002() -> dict[str, Any]:
    expired = mandate_skeleton(
        id_=MANDATE_ID,
        not_before=T_PAST_BEFORE,
        not_after=T_PAST_AFTER,
    )
    return business_call(
        action="read:profile",
        mandate=expired,
        extra={"now": T_NOW},
        msg_id="msg:err-1002-trigger",
    )


# ---- 1003 E_SCOPE_VIOLATION ----

def trigger_1003() -> dict[str, Any]:
    m = mandate_skeleton(scope={"domains": ["api.example.com"], "actions": ["read:profile"]})
    return business_call(
        action="write:profile",   # NOT in scope.actions
        mandate=m,
        msg_id="msg:err-1003-trigger",
    )


# ---- 1004 E_GRADE_INSUFFICIENT ----

def trigger_1004() -> dict[str, Any]:
    m = mandate_skeleton(grade=3)   # Loose
    return business_call(
        action="read:profile",
        mandate=m,
        extra={"rp_required_grade": 1},   # RP requires Strict
        msg_id="msg:err-1004-trigger",
    )


# ---- 1005 E_PRESENCE_STALE ----

def trigger_1005() -> dict[str, Any]:
    m = mandate_skeleton()
    return business_call(
        action="read:profile",
        mandate=m,
        extra={
            "presence_state": {
                "last_freshness": "2025-12-17T11:50:00Z",      # 600 s ago
                "max_staleness_ms": 60_000,
                "stale": True,
            },
        },
        msg_id="msg:err-1005-trigger",
    )


# ---- 1006 E_REVOKED ----

def trigger_1006() -> dict[str, Any]:
    m = mandate_skeleton(id_=MANDATE_ID_REVOKED)
    return business_call(
        action="read:profile",
        mandate=m,
        extra={
            "rr_query": {
                "mandate_id": MANDATE_ID_REVOKED,
                "status": "revoked",
                "reason": "human-initiated",
                "effective_at": T_BEFORE,
            },
        },
        msg_id="msg:err-1006-trigger",
    )


# ---- 1007 E_ATTESTATION_INVALID ----

def trigger_1007() -> dict[str, Any]:
    # Tamper the embedded endorsement so signature input no longer
    # matches Mandate.signature; per §6.3 S4 / S5 this trips 1007 at the
    # RP and 1013 at the MS. Here we model the RP-side trigger.
    m = mandate_skeleton(
        id_=MANDATE_ID_TAMPER,
        endorsement={
            "enabled": True,
            # original endorsed_scope was {"domains":["api.example.com"], "actions":["read:profile"]};
            # an attacker has expanded it post-signing — signature input no longer matches.
            "endorsed_scope": {
                "domains": ["api.example.com", "internal.example.com"],
                "actions": ["read:profile", "write:profile"],
            },
            "endorsed_grade": 3,
            "endorsed_lifetime_ms": 3_600_000,
            "offline_revocation_policy": "stop-and-audit",
        },
        tampered_attestation=False,
    )
    return business_call(
        action="read:profile",
        mandate=m,
        extra={
            "verification": {
                "signature_check": "failed",
                "reason": "endorsement-fields-mutated-after-signing",
            },
        },
        msg_id="msg:err-1007-trigger",
    )


# ---- 1008 E_RR_UNAVAILABLE ----

def trigger_1008() -> dict[str, Any]:
    m = mandate_skeleton(id_=MANDATE_ID_RR)
    return business_call(
        action="read:profile",
        mandate=m,
        extra={
            "rr_query": {
                "mandate_id": MANDATE_ID_RR,
                "status": "unavailable",
                "stale_budget_ms": 5_000,
                "elapsed_ms": 6_000,
            },
        },
        msg_id="msg:err-1008-trigger",
    )


# ---- 1009 E_REPLAY ----

def trigger_1009() -> dict[str, Any]:
    """A PRESENCE message reusing a previously-seen nonce."""
    return envelope(
        msg_type="PRESENCE",
        msg_id="msg:err-1009-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=HP_ID,
        nonce_hex=NONCE_REPLAY,
        claims={
            "mandate_id": MANDATE_ID,
            "signal": {
                "mandate_id": MANDATE_ID,
                "signal_type": "fingerprint-tap",
                "produced_at": T_NOW,
                "nonce_hex": NONCE_REPLAY,           # <-- already-seen
                "device_id": DEVICE_ID,
                "device_attestation": attestation(format_="platform-keystore"),
                "signature": signature_bundle(),
            },
            "device_health": {
                "secure_element": True,
                "tampered": False,
                "last_boot_at": T_BEFORE,
            },
            "seen_set_state": {
                "subject": FAY_ID,
                "nonce_hex": NONCE_REPLAY,
                "first_seen_at": "2025-12-17T11:55:00Z",
                "ttl_ms_remaining": 540_000,
            },
        },
    )


# ---- 1010 E_HUMAN_WITNESS_REQUIRED ----

def trigger_1010() -> dict[str, Any]:
    """A GRADE_SWITCH from G3 (current) to G1 (target = upgrade) with
    no `human_witness` field — must be rejected (§7.4)."""
    return envelope(
        msg_type="GRADE_SWITCH",
        msg_id="msg:err-1010-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=HP_ID,
        claims={
            "mandate_id": MANDATE_ID,
            "current_grade": 3,
            "target_grade": 1,
            "reason": "human-initiated",
            # human_witness is INTENTIONALLY ABSENT
        },
    )


# ---- 1011 E_ROGUE_DETECTED ----

def trigger_1011() -> dict[str, Any]:
    """A DISCLOSURE whose declared scope_used / action diverges from the
    actually executed action — the spec requires Revoke with reason
    `ego-deviation` (§9.5, §9.10.4 T3). Surfaces as 1011 at RP."""
    return envelope(
        msg_type="DISCLOSURE",
        msg_id="msg:err-1011-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=HP_ID,
        claims={
            "mandate_id": MANDATE_ID,
            "action": "transfer:funds",
            "scope_used": {"domains": ["api.example.com"], "actions": ["read:profile"]},
            "risk_level": "critical",
            "reversibility": "irreversible",
            "affected_resources": ["account:001"],
            "uncertainty_flags": [],
            "intent": "report",
            "executed_action_observed_by_rp": "transfer:funds:1000USD",
            "deviation_dimensions": ["scope_used", "risk_level"],
        },
    )


# ---- 1012 E_BUDGET_EXCEEDED ----

def trigger_1012() -> dict[str, Any]:
    m = mandate_skeleton(
        id_=MANDATE_ID_BUDGET,
        scope={
            "domains": ["api.example.com"],
            "actions": ["read:profile"],
            "budget": {
                "time_window": [T_BEFORE, T_LONG_AFTER],
                "max_invocations": 10,
            },
        },
    )
    return business_call(
        action="read:profile",
        mandate=m,
        extra={
            "budget_state": {
                "max_invocations": 10,
                "current_invocations": 11,
                "exceeded_at": T_NOW,
            },
        },
        msg_id="msg:err-1012-trigger",
    )


# ---- 1013 E_ENDORSEMENT_INVALID ----

def trigger_1013() -> dict[str, Any]:
    """A BOOTSTRAP whose endorsement.endorsed_scope ⊄ Mandate.scope —
    must be rejected by MS at signing time (§7.5, §11.2)."""
    bad_endorsement = {
        "enabled": True,
        # Mandate.scope.actions = ["read:profile"], but endorsed_scope
        # tries to widen to write:profile — convergence violation.
        "endorsed_scope": {
            "domains": ["api.example.com", "internal.example.com"],
            "actions": ["read:profile", "write:profile"],
        },
        "endorsed_grade": 3,
        "endorsed_lifetime_ms": 4 * 3_600_000,
        "offline_revocation_policy": "stop-and-audit",
    }
    return envelope(
        msg_type="BOOTSTRAP",
        msg_id="msg:err-1013-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=HP_ID,
        claims={
            "human_prime": HP_ID,
            "fay": FAY_ID,
            "scope": DEFAULT_SCOPE,
            "grade": 3,
            "presence_req": {
                "signal_types": ["fingerprint-tap"],
                "max_staleness_ms": 60_000,
                "on_loss": "downgrade-to:G3",
            },
            "not_after": T_LONG_AFTER,
            "human_witness": {
                "format": "webauthn",
                "user_present": True,
                "user_verified": True,
                "signature_hex": SIG_HP_HEX,
            },
            "endorsement": bad_endorsement,
        },
    )


# ---- 1014 E_FAYING_REQUEST_NOT_CONFIRMED ----

def trigger_1014() -> dict[str, Any]:
    """A FAYING_REQUEST that timed out — HP did not BOOTSTRAP within
    `BootstrapTimeout` (§5.3.6, §EH.1 row 1014)."""
    return envelope(
        msg_type="FAYING_REQUEST",
        msg_id="msg:err-1014-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=FAY_ID,            # IF-initiated
        claims={
            "initiator": FAY_ID,
            "target_human": HP_ID,
            "proposed_scope": DEFAULT_SCOPE,
            "proposed_grade": 3,
            "reason": "establish a new monitored relationship",
            "reason_code": "establish",
            "expected_lifetime_ms": 3_600_000,
            "timeline": {
                "issued_at": "2025-12-17T11:58:00Z",
                "bootstrap_timeout_ms": 60_000,
                "confirmation_deadline": "2025-12-17T11:59:00Z",
                "now": T_NOW,
                "hp_witness_received": False,
            },
        },
    )


# ---- 1099 E_PROTOCOL ----

def trigger_1099() -> dict[str, Any]:
    """A DISCLOSURE missing `risk_level` (one of the mandatory_fields,
    §5.3.7). Per §5.4 footnote, DISCLOSURE-path 1099 also pushes to HP
    view."""
    return envelope(
        msg_type="DISCLOSURE",
        msg_id="msg:err-1099-trigger",
        grade=3,
        subject=FAY_ID,
        issuer=HP_ID,
        claims={
            "mandate_id": MANDATE_ID,
            "action": "read:profile",
            "scope_used": DEFAULT_SCOPE,
            # "risk_level" is INTENTIONALLY ABSENT — mandatory_fields violation
            "reversibility": "reversible",
            "affected_resources": ["resource:001"],
            "uncertainty_flags": [],
            "intent": "report",
        },
    )


TRIGGERS: dict[int, Any] = {
    1001: trigger_1001,
    1002: trigger_1002,
    1003: trigger_1003,
    1004: trigger_1004,
    1005: trigger_1005,
    1006: trigger_1006,
    1007: trigger_1007,
    1008: trigger_1008,
    1009: trigger_1009,
    1010: trigger_1010,
    1011: trigger_1011,
    1012: trigger_1012,
    1013: trigger_1013,
    1014: trigger_1014,
    1099: trigger_1099,
}


# ---------------------------------------------------------------------------
# Per-error ERROR-envelope builders
# ---------------------------------------------------------------------------

ERROR_DETAILS: dict[int, dict[str, Any]] = {
    1001: dict(
        mandate_id=None,        # no Mandate context
        message="business call rejected: no Mandate present",
        recovery_hint="obtain a Mandate via BOOTSTRAP before calling RP",
    ),
    1002: dict(
        mandate_id=MANDATE_ID,
        message="mandate has expired",
        recovery_hint="bootstrap a new Mandate; new mandate_id will not equal the old one",
    ),
    1003: dict(
        mandate_id=MANDATE_ID,
        message="action not in mandate scope",
        recovery_hint="adjust action to fall within Mandate.scope.actions",
    ),
    1004: dict(
        mandate_id=MANDATE_ID,
        message="current grade insufficient for requested action",
        recovery_hint="trigger GRADE_SWITCH-up with HP human_witness",
    ),
    1005: dict(
        mandate_id=MANDATE_ID,
        message="presence signal stale",
        recovery_hint="resend PRESENCE within max_staleness_ms",
    ),
    1006: dict(
        mandate_id=MANDATE_ID_REVOKED,
        message="mandate has been revoked",
        recovery_hint="bootstrap a new Mandate; new mandate_id will not equal the old one",
    ),
    1007: dict(
        mandate_id=MANDATE_ID_TAMPER,
        message="attestation chain verification failed",
        recovery_hint=None,
    ),
    1008: dict(
        mandate_id=MANDATE_ID_RR,
        message="revocation registry unreachable; default-deny applied",
        recovery_hint="retry with backoff; do not bypass revocation check",
    ),
    1009: dict(
        mandate_id=MANDATE_ID,
        message="nonce replay detected",
        recovery_hint="rotate session key and reissue with fresh nonce",
    ),
    1010: dict(
        mandate_id=MANDATE_ID,
        message="human witness required for grade upgrade",
        recovery_hint="resubmit GRADE_SWITCH with valid human_witness (e.g. WebAuthn UV)",
    ),
    1011: dict(
        mandate_id=MANDATE_ID,
        message="rogue behavior detected; mandate revoked",
        recovery_hint=None,
    ),
    1012: dict(
        mandate_id=MANDATE_ID_BUDGET,
        message="resource budget exceeded",
        recovery_hint="wait for budget window refresh or trigger GRADE_SWITCH-down",
    ),
    1013: dict(
        mandate_id=None,        # bootstrap rejected before mandate was issued
        message="endorsement field invalid",
        recovery_hint="ensure endorsed_scope ⊆ scope, endorsed_grade.autonomy ≤ grade.autonomy, "
                      "and endorsed_lifetime_ms ≤ (not_after − not_before)",
    ),
    1014: dict(
        mandate_id=None,        # no Mandate produced
        message="faying request not confirmed by Human Prime within BootstrapTimeout",
        recovery_hint="resubmit FAYING_REQUEST within ConfirmationRateLimit",
    ),
    1099: dict(
        mandate_id=MANDATE_ID,
        message="protocol error: disclosure missing mandatory field",
        recovery_hint="resubmit DISCLOSURE with all mandatory_fields populated and parseable",
    ),
}


def build_error_envelope_for(code: int, name: str) -> dict[str, Any]:
    d = ERROR_DETAILS[code]
    return error_envelope(
        code=code,
        name=name,
        mandate_id=d["mandate_id"],
        message=d["message"],
        recovery_hint=d.get("recovery_hint"),
        msg_id=f"msg:err-{code}-error",
    )


# ---------------------------------------------------------------------------
# Expected (audit + HP-view) builders
# ---------------------------------------------------------------------------

def expected_for(spec: dict[str, Any]) -> dict[str, Any]:
    code = spec["code"]
    name = spec["name"]

    err = ERROR_DETAILS[code]
    mandate_id = err["mandate_id"]

    if spec["audit"]:
        audit_log_entry = {
            "error_code": code,
            "mandate_id": mandate_id,           # may be null for 1013/1014
            "ts": T_NOW,
            "rp_id": RP_ID,
            "reason": spec["summary"],
        }
    else:
        audit_log_entry = None                  # 1001 has no Mandate context

    return {
        "code": code,
        "name": name,
        "summary": spec["summary"],
        "audit-log-entry": audit_log_entry,
        "must-push-hp-view": spec["hp_view"],
        "trace": spec["trace"],
        "spec_anchors": [
            "§5.4",
            "§EH.1",
            "§EH.3",
        ],
    }


# ---------------------------------------------------------------------------
# Determinism helpers
# ---------------------------------------------------------------------------

def cbor_dumps_deterministic(obj: Any) -> bytes:
    """RFC 8949 §4.2.1 deterministic encoding (canonical=True)."""
    return cbor2.dumps(obj, canonical=True)


def json_dumps_canonical(obj: Any) -> str:
    """Stable JSON output: sort keys, no extraneous spaces."""
    return json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def vector_dirname(spec: dict[str, Any]) -> str:
    return f"{spec['code']}-{spec['name']}"


def emit_vector(spec: dict[str, Any]) -> dict[str, Any]:
    code = spec["code"]
    name = spec["name"]
    dirname = vector_dirname(spec)
    out_dir = ROOT / dirname
    out_dir.mkdir(parents=True, exist_ok=True)

    trigger = TRIGGERS[code]()
    error = build_error_envelope_for(code, name)
    expected = expected_for(spec)

    trigger_cbor = cbor_dumps_deterministic(trigger)
    error_cbor = cbor_dumps_deterministic(error)

    (out_dir / "trigger.cbor").write_bytes(trigger_cbor)
    (out_dir / "trigger.json").write_text(json_dumps_canonical(trigger), encoding="utf-8")
    (out_dir / "error.cbor").write_bytes(error_cbor)
    (out_dir / "error.json").write_text(json_dumps_canonical(error), encoding="utf-8")
    (out_dir / "expected.json").write_text(json_dumps_canonical(expected), encoding="utf-8")

    return {
        "code": code,
        "name": name,
        "summary": spec["summary"],
        "directory": dirname,
        "trigger_msg_type": spec["trigger_msg_type"],
        "must_push_hp_view": spec["hp_view"],
        "audit_required": spec["audit"],
        "files": {
            "trigger.cbor": {
                "size": len(trigger_cbor),
                "sha256": sha256_hex(trigger_cbor),
            },
            "trigger.json": {"path": f"{dirname}/trigger.json"},
            "error.cbor": {
                "size": len(error_cbor),
                "sha256": sha256_hex(error_cbor),
            },
            "error.json": {"path": f"{dirname}/error.json"},
            "expected.json": {"path": f"{dirname}/expected.json"},
        },
        "trace": spec["trace"],
    }


def main() -> None:
    # Quick sanity-check: every error code in the §5.4 table is covered.
    expected_codes = {1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008,
                      1009, 1010, 1011, 1012, 1013, 1014, 1099}
    have = {s["code"] for s in ERROR_CODES}
    missing = expected_codes - have
    extra = have - expected_codes
    assert not missing, f"missing error codes: {sorted(missing)}"
    assert not extra, f"unexpected error codes: {sorted(extra)}"

    entries = []
    for spec in ERROR_CODES:
        entries.append(emit_vector(spec))

    index = {
        "spec": {
            "name": "Faying Protocol",
            "version": "Faying Protocol/1.0",
            "anchor": "§5.4 / §EH.1 / §EH.3",
            "doc": "docs/zh-CN/specification/draft/Faying-Protocol-1.0.md",
        },
        "generator": {
            "script": "vectors/errors/_generator.py",
            "deterministic_now": T_NOW,
            "cbor_profile": "RFC 8949 §4.2.1 deterministic (canonical=True)",
            "json_profile": "sort_keys=True, indent=2, ensure_ascii=False",
        },
        "totals": {
            "error_codes_in_spec": 15,
            "error_codes_covered": len(entries),
            "must_push_hp_view_count": sum(1 for e in entries if e["must_push_hp_view"]),
            "audit_required_count": sum(1 for e in entries if e["audit_required"]),
        },
        "vectors": entries,
    }

    (ROOT / "index.json").write_text(json_dumps_canonical(index), encoding="utf-8")
    print(f"emitted {len(entries)} error-code vector directories under {ROOT}")
    print(f"index.json -> {ROOT / 'index.json'}")


if __name__ == "__main__":
    main()
