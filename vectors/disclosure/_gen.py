#!/usr/bin/env python3
# ======================================================================
#  vectors/disclosure/_gen.py
#  ----------------------------------------------------------------------
#  Deterministic generator for the DISCLOSURE test-vector suite covering
#  Faying Protocol/1.0 §5.3.7 and §9.10.4 T3 (Requirement 13.3).
#
#  The generator emits, for each vector folder:
#    - disclosure.cbor   : Deterministic-CBOR (RFC 8949 §4.2.1) envelope
#    - disclosure.json   : application/fap+json equivalent (kebab-case)
#    - context.json      : surrounding context (action timeline,
#                          mandate state, endorsement state)
#    - expected.json     : { outcome, audit_notes, ... }
#
#  Plus the suite-level index.json.
#
#  Notes on cryptography:
#    These vectors exercise SCHEMA-LEVEL behaviour (Requirement 13.3).
#    Signatures and attestations are deterministic stubs (sentinel bytes
#    "STUB-SIG" / "STUB-PUBKEY" / "STUB-ATTESTATION") so that decoders may
#    parse and validate STRUCTURE without depending on a particular crypto
#    backend. Cross-encoding (CBOR ↔ JSON) signature equivalence is
#    covered by the dedicated `vectors/encoding-equivalence/` suite
#    (task 3.7), not here.
# ======================================================================

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cbor2

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------- #
# Base scaffolding (envelope, attestation, signature stubs)
# ---------------------------------------------------------------------- #

PROTO_VERSION = "Faying Protocol/1.0"

STUB_PUBKEY = b"STUB-PUBKEY-FAP-1.0\x00"
STUB_SIG = b"STUB-SIG-FAP-1.0\x00\x00\x00\x00\x00"
STUB_ATTEST_PAYLOAD = b"STUB-ATTESTATION-PAYLOAD"

ISSUER_HP = "hp:01HX4KZ8N0Y6F8MWQ8R7C0V0G2"
SUBJECT_FAY = "fay:01HX4KZBQ4P9JK1H6QY7V0X8B5"
MS_ID = "ms:01HX4KZD5T0M7Q3R8N1F4D6V2X"


def stub_signature_bundle() -> Dict[str, Any]:
    return {
        "alg": "Ed25519",
        "pubkey": STUB_PUBKEY,
        "sig": STUB_SIG,
    }


def stub_attestation() -> Dict[str, Any]:
    return {
        "format": "self-signed",
        "payload": STUB_ATTEST_PAYLOAD,
        "signer": ISSUER_HP,
        "signature": stub_signature_bundle(),
    }


# 16-byte deterministic nonces — derived from a per-vector counter so
# CBOR output is byte-stable across runs.
def nonce(seed: int) -> bytes:
    return seed.to_bytes(16, "big")


def envelope(
    *,
    msg_id: str,
    nonce_seed: int,
    issued_at: str,
    expiry: str,
    grade: int,
    claims: Dict[str, Any],
) -> Dict[str, Any]:
    """Wrap DisclosureClaims in a FayingProtocolEnvelope (§5.2)."""
    return {
        "header": {
            "version": PROTO_VERSION,
            "msg-type": "DISCLOSURE",
            "msg-id": msg_id,
            "issued-at": issued_at,
            "expiry": expiry,
            "nonce": nonce(nonce_seed),
            "grade": grade,
            "issuer": ISSUER_HP,
            "subject": SUBJECT_FAY,
        },
        "claims": claims,
        "attestation": stub_attestation(),
        "signature": stub_signature_bundle(),
    }


# ---------------------------------------------------------------------- #
# Disclosure-claim builders
# ---------------------------------------------------------------------- #

# Two reusable mandates: one regular Active mandate, and one Endorsed
# mandate (for the Disconnected-period vectors).

MANDATE_ID_ACTIVE = "mandate:01HX4M0T9V8H8Q4N6Z2K7G3J5W"
MANDATE_ID_ENDORSED = "mandate:01HX4M0Y6N7B8C4D9E2F1A0G3H"
ENDORSEMENT_ID_VALID = "endorsement:01HX4M11G3J5W8Q4N6Z2K7P9V0"
ENDORSEMENT_ID_BOGUS = "endorsement:DOES-NOT-EXIST-01"

# Reusable scope_used subsets.
SCOPE_USED_READ_ONLY: Dict[str, Any] = {
    "domains": ["urn:user:profile"],
    "actions": ["read:user-profile"],
}

SCOPE_USED_PAYMENT: Dict[str, Any] = {
    "domains": ["urn:wallet:account"],
    "actions": ["payment:transfer"],
}

SCOPE_USED_FILE_DELETE: Dict[str, Any] = {
    "domains": ["urn:storage:bucket-A"],
    "actions": ["storage:delete-object"],
}


# Each builder returns a *fresh* dict so callers can mutate / del fields
# to produce the negative cases.

def claims_full_low_risk() -> Dict[str, Any]:
    return {
        "mandate-id": MANDATE_ID_ACTIVE,
        "action": "read:user-profile",
        "scope-used": dict(SCOPE_USED_READ_ONLY),
        "risk-level": "low",
        "reversibility": "reversible",
        "affected-resources": ["urn:user:profile:01HX4M2P0Q3R5S7T8U"],
        "uncertainty-flags": [],
        "intent": "report",
    }


def claims_full_normal_risk_report() -> Dict[str, Any]:
    return {
        "mandate-id": MANDATE_ID_ACTIVE,
        "action": "calendar:create-event",
        "scope-used": {
            "domains": ["urn:calendar:primary"],
            "actions": ["calendar:create-event"],
        },
        "risk-level": "normal",
        "reversibility": "reversible",
        "affected-resources": ["urn:calendar:event:01HX4M3VWXYZ"],
        "uncertainty-flags": ["ambiguous-target"],
        "free-text": "已创建日程并通知与会者。",
        "intent": "report",
    }


def claims_high_risk_request_confirmation() -> Dict[str, Any]:
    """A canonical high-risk DISCLOSURE expected to be PRIOR-confirmed."""
    return {
        "mandate-id": MANDATE_ID_ACTIVE,
        "action": "payment:transfer",
        "scope-used": dict(SCOPE_USED_PAYMENT),
        "risk-level": "high",
        "reversibility": "irreversible",
        "affected-resources": [
            "urn:wallet:account:src:01HX4M5N8P0Q",
            "urn:wallet:account:dst:01HX4M5N8P0R",
        ],
        "uncertainty-flags": ["irreversible-funds-move"],
        "intent": "request-confirmation",
    }


def claims_endorsed_disconnected_action(
    *, with_endorsement_id: bool, endorsement_id: str = ENDORSEMENT_ID_VALID
) -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "mandate-id": MANDATE_ID_ENDORSED,
        "action": "iot:hvac-set-temperature",
        "scope-used": {
            "domains": ["urn:iot:home:hvac"],
            "actions": ["iot:hvac-set-temperature"],
        },
        "risk-level": "low",
        "reversibility": "reversible",
        "affected-resources": ["urn:iot:device:hvac:01HX4M7Z3"],
        "uncertainty-flags": [],
        "intent": "report",
        "free-text": "Disconnected 期间的预授权动作。",
    }
    if with_endorsement_id:
        base["endorsement-id"] = endorsement_id
    return base


# ---------------------------------------------------------------------- #
# Context builders
# ---------------------------------------------------------------------- #

def ctx_normal() -> Dict[str, Any]:
    return {
        "mandate_state": "Active",
        "mandate_id": MANDATE_ID_ACTIVE,
        "presence_state": "fresh",
        "is_disconnected": False,
        "endorsement_present": False,
        "audit_window": {
            "action_executed_at": "2025-11-25T10:00:01Z",
            "disclosure_submitted_at": "2025-11-25T10:00:02Z",
        },
        "actual_action": "read:user-profile",
    }


def ctx_normal_create_event() -> Dict[str, Any]:
    c = ctx_normal()
    c["audit_window"] = {
        "action_executed_at": "2025-11-25T10:05:01Z",
        "disclosure_submitted_at": "2025-11-25T10:05:02Z",
    }
    c["actual_action"] = "calendar:create-event"
    return c


def ctx_high_risk_no_prior_disclosure() -> Dict[str, Any]:
    """High-risk action executed BEFORE any DISCLOSURE was issued."""
    return {
        "mandate_state": "Active",
        "mandate_id": MANDATE_ID_ACTIVE,
        "grade": 2,
        "presence_state": "fresh",
        "is_disconnected": False,
        "endorsement_present": False,
        "audit_window": {
            # Action attempted FIRST, disclosure arrives POST-HOC
            "action_attempted_at": "2025-11-25T11:00:00Z",
            "disclosure_submitted_at": "2025-11-25T11:00:05Z",
            "prior_disclosure_count": 0,
        },
        "actual_action": "payment:transfer",
        "violation": "high-sensitivity action executed without prior DISCLOSURE",
    }


def ctx_inconsistent_action() -> Dict[str, Any]:
    """Disclosed action does not match the action recorded in the
    Attestation Chain — triggers RevokeReason='ego-deviation'."""
    return {
        "mandate_state": "Active",
        "mandate_id": MANDATE_ID_ACTIVE,
        "presence_state": "fresh",
        "is_disconnected": False,
        "endorsement_present": False,
        "audit_window": {
            "action_executed_at": "2025-11-25T12:00:01Z",
            "disclosure_submitted_at": "2025-11-25T12:00:03Z",
        },
        # The DISCLOSURE will claim `read:user-profile` while the actual
        # audit-log entry shows `storage:delete-object`.
        "actual_action": "storage:delete-object",
        "actual_affected_resources": [
            "urn:storage:bucket-A:object:01HX4M9F7G"
        ],
        "actual_risk_level": "high",
        "actual_reversibility": "irreversible",
        "violation": "DISCLOSURE.action ≠ audit-log action",
    }


def ctx_disconnected(*, endorsement_present: bool) -> Dict[str, Any]:
    return {
        "mandate_state": "Disconnected",
        "mandate_id": MANDATE_ID_ENDORSED,
        "presence_state": "stale",
        "is_disconnected": True,
        "endorsement_present": endorsement_present,
        "endorsement_id": ENDORSEMENT_ID_VALID if endorsement_present else None,
        "endorsed_scope_actions": ["iot:hvac-set-temperature"],
        "endorsed_grade": 3,
        "endorsed_lifetime_ms": 3_600_000,
        "endorsement_start_at": "2025-11-25T13:00:00Z",
        "audit_window": {
            "action_executed_at": "2025-11-25T13:15:00Z",
            "disclosure_submitted_at": "2025-11-25T13:30:00Z",
        },
        "actual_action": "iot:hvac-set-temperature",
    }


# ---------------------------------------------------------------------- #
# Vector definitions
# ---------------------------------------------------------------------- #


def make_missing_field(field: str) -> Dict[str, Any]:
    c = claims_full_low_risk()
    del c[field]
    return c


def make_unparseable_risk_level() -> Dict[str, Any]:
    c = claims_full_low_risk()
    c["risk-level"] = "extreme"  # not in enum
    return c


def make_unparseable_reversibility() -> Dict[str, Any]:
    c = claims_full_low_risk()
    c["reversibility"] = "maybe"  # not in enum
    return c


def make_inconsistent_disclosure() -> Dict[str, Any]:
    """Disclosure asserts a benign read but the actual audit-log entry is
    `storage:delete-object` (high, irreversible)."""
    return {
        "mandate-id": MANDATE_ID_ACTIVE,
        "action": "read:user-profile",
        "scope-used": dict(SCOPE_USED_READ_ONLY),
        "risk-level": "low",
        "reversibility": "reversible",
        "affected-resources": ["urn:user:profile:01HX4M2P0Q3R5S7T8U"],
        "uncertainty-flags": [],
        "intent": "report",
        "free-text": "只读了一下用户资料。",
    }


VECTORS: List[Dict[str, Any]] = [
    # ---------- (a) all mandatory_fields legal ----------
    {
        "id": "01-accepted-low-risk-report",
        "case": "a",
        "title": "全字段合法 DISCLOSURE（low risk, report）",
        "claims": claims_full_low_risk(),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA1A1A1A1A1A1A1A1A1A1",
        "nonce_seed": 0x01,
        "issued_at": "2025-11-25T10:00:02Z",
        "expiry": "2025-11-25T10:05:02Z",
        "grade": 2,
        "expected": {
            "outcome": "accepted",
            "ms_action": "log-and-forward",
            "audit_notes": [
                "All mandatory_fields present and parseable.",
                "Disclosure is consistent with audit-log entry.",
                "Written to Attestation Chain as a DISCLOSURE record.",
            ],
        },
    },
    {
        "id": "02-accepted-normal-risk-report",
        "case": "a",
        "title": "全字段合法 DISCLOSURE（normal risk, free_text 辅助）",
        "claims": claims_full_normal_risk_report(),
        "context": ctx_normal_create_event(),
        "msg_id": "msg:01HX4MA2A2A2A2A2A2A2A2A2A2",
        "nonce_seed": 0x02,
        "issued_at": "2025-11-25T10:05:02Z",
        "expiry": "2025-11-25T10:10:02Z",
        "grade": 2,
        "expected": {
            "outcome": "accepted",
            "ms_action": "log-and-forward",
            "audit_notes": [
                "free_text supplements but does not replace mandatory_fields.",
                "uncertainty_flags ['ambiguous-target'] surfaced to HP view.",
            ],
        },
    },
    # ---------- (b) each mandatory_field individually missing ----------
    {
        "id": "03-missing-action",
        "case": "b",
        "title": "缺失 mandatory_field: action → E_PROTOCOL",
        "claims": make_missing_field("action"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA3A3A3A3A3A3A3A3A3A3",
        "nonce_seed": 0x03,
        "issued_at": "2025-11-25T10:10:00Z",
        "expiry": "2025-11-25T10:15:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "action",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "DISCLOSURE-path E_PROTOCOL MUST be pushed to HP view per §5.4 note `*`.",
            ],
        },
    },
    {
        "id": "04-missing-scope-used",
        "case": "b",
        "title": "缺失 mandatory_field: scope_used → E_PROTOCOL",
        "claims": make_missing_field("scope-used"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA4A4A4A4A4A4A4A4A4A4",
        "nonce_seed": 0x04,
        "issued_at": "2025-11-25T10:11:00Z",
        "expiry": "2025-11-25T10:16:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "scope_used",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "DISCLOSURE-path E_PROTOCOL MUST be pushed to HP view.",
            ],
        },
    },
    {
        "id": "05-missing-risk-level",
        "case": "b",
        "title": "缺失 mandatory_field: risk_level → E_PROTOCOL",
        "claims": make_missing_field("risk-level"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA5A5A5A5A5A5A5A5A5A5",
        "nonce_seed": 0x05,
        "issued_at": "2025-11-25T10:12:00Z",
        "expiry": "2025-11-25T10:17:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "risk_level",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Without risk_level the MS cannot route to HP confirmation buckets.",
            ],
        },
    },
    {
        "id": "06-missing-reversibility",
        "case": "b",
        "title": "缺失 mandatory_field: reversibility → E_PROTOCOL",
        "claims": make_missing_field("reversibility"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA6A6A6A6A6A6A6A6A6A6",
        "nonce_seed": 0x06,
        "issued_at": "2025-11-25T10:13:00Z",
        "expiry": "2025-11-25T10:18:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "reversibility",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Reversibility is a hard input to the HP confirmation UI.",
            ],
        },
    },
    {
        "id": "07-missing-affected-resources",
        "case": "b",
        "title": "缺失 mandatory_field: affected_resources → E_PROTOCOL",
        "claims": make_missing_field("affected-resources"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA7A7A7A7A7A7A7A7A7A7",
        "nonce_seed": 0x07,
        "issued_at": "2025-11-25T10:14:00Z",
        "expiry": "2025-11-25T10:19:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "affected_resources",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Empty list `[]` is allowed; the field itself MUST be present.",
            ],
        },
    },
    {
        "id": "08-missing-uncertainty-flags",
        "case": "b",
        "title": "缺失 mandatory_field: uncertainty_flags → E_PROTOCOL",
        "claims": make_missing_field("uncertainty-flags"),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA8A8A8A8A8A8A8A8A8A8",
        "nonce_seed": 0x08,
        "issued_at": "2025-11-25T10:15:00Z",
        "expiry": "2025-11-25T10:20:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "missing_field": "uncertainty_flags",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Empty list `[]` is allowed; the field itself MUST be present.",
            ],
        },
    },
    # ---------- (c) unparseable field ----------
    {
        "id": "09-unparseable-risk-level",
        "case": "c",
        "title": "risk_level 不在枚举（'extreme'）→ E_PROTOCOL",
        "claims": make_unparseable_risk_level(),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MA9A9A9A9A9A9A9A9A9A9",
        "nonce_seed": 0x09,
        "issued_at": "2025-11-25T10:16:00Z",
        "expiry": "2025-11-25T10:21:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "unparseable_field": "risk_level",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Permitted enum: low | normal | high | critical (§5.3.7).",
            ],
        },
    },
    {
        "id": "10-unparseable-reversibility",
        "case": "c",
        "title": "reversibility 不在枚举（'maybe'）→ E_PROTOCOL",
        "claims": make_unparseable_reversibility(),
        "context": ctx_normal(),
        "msg_id": "msg:01HX4MAAAAAAAAAAAAAAAAAAA1",
        "nonce_seed": 0x0A,
        "issued_at": "2025-11-25T10:17:00Z",
        "expiry": "2025-11-25T10:22:00Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "unparseable_field": "reversibility",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "Permitted enum: reversible | partially-reversible | irreversible.",
            ],
        },
    },
    # ---------- (d) high-sensitivity action without prior DISCLOSURE ----------
    {
        "id": "11-high-risk-no-prior-disclosure",
        "case": "d",
        "title": "高敏感动作（risk_level=high）未前置披露即执行 → 拒绝",
        "claims": claims_high_risk_request_confirmation(),
        "context": ctx_high_risk_no_prior_disclosure(),
        "msg_id": "msg:01HX4MABBBBBBBBBBBBBBBBBBB",
        "nonce_seed": 0x0B,
        "issued_at": "2025-11-25T11:00:05Z",
        "expiry": "2025-11-25T11:05:05Z",
        "grade": 2,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "ms_action": "reject + push-to-hp-view",
            "rejected_action": "payment:transfer",
            "audit_notes": [
                "§5.3.7 hard rule: risk_level ∈ {high, critical} MUST be PRE-disclosed.",
                "Here action_attempted_at < disclosure_submitted_at → action rejected.",
                "G4 Autonomous + main-scope exception does not apply (grade=G2).",
                "Post-hoc DISCLOSURE is recorded but does NOT retroactively legalise the action.",
            ],
        },
    },
    # ---------- (e) DISCLOSURE inconsistent with actual action ----------
    {
        "id": "12-inconsistent-disclosure-ego-deviation",
        "case": "e",
        "title": "DISCLOSURE 与实际动作不一致 → ego-deviation Revoke",
        "claims": make_inconsistent_disclosure(),
        "context": ctx_inconsistent_action(),
        "msg_id": "msg:01HX4MACCCCCCCCCCCCCCCCCCC",
        "nonce_seed": 0x0C,
        "issued_at": "2025-11-25T12:00:03Z",
        "expiry": "2025-11-25T12:05:03Z",
        "grade": 2,
        "expected": {
            "outcome": "ego-deviation-revoke",
            "revoke_reason": "ego-deviation",
            "ms_action": "revoke-mandate + push-to-hp-view",
            "audit_notes": [
                "Disclosure asserts read:user-profile / low / reversible.",
                "Audit-log shows storage:delete-object / high / irreversible.",
                "Mandate MUST be revoked with RevokeReason='ego-deviation' (§9.10.4 T3 #4).",
                "Triggers E_REVOKED on subsequent calls under this mandate_id.",
            ],
        },
    },
    # ---------- (f) Disconnected period DISCLOSURE must carry endorsement_id ----------
    {
        "id": "13-disconnected-with-endorsement-id-accepted",
        "case": "f",
        "title": "Disconnected 期间 DISCLOSURE 携带合法 endorsement_id → accepted",
        "claims": claims_endorsed_disconnected_action(with_endorsement_id=True),
        "context": ctx_disconnected(endorsement_present=True),
        "msg_id": "msg:01HX4MADDDDDDDDDDDDDDDDDDD",
        "nonce_seed": 0x0D,
        "issued_at": "2025-11-25T13:30:00Z",
        "expiry": "2025-11-25T13:35:00Z",
        "grade": 3,
        "expected": {
            "outcome": "accepted",
            "ms_action": "log-and-forward",
            "endorsement_id_resolved": ENDORSEMENT_ID_VALID,
            "audit_notes": [
                "Disclosure carries endorsement_id linking the action to a specific endorsement.",
                "Action is within endorsed_scope.actions and within endorsed_lifetime.",
                "Independently verifiable: (mandate_id, endorsement_id, action, ts) tuple recoverable.",
            ],
        },
    },
    {
        "id": "14-disconnected-missing-endorsement-id",
        "case": "f",
        "title": "Disconnected 期间 DISCLOSURE 缺 endorsement_id → E_PROTOCOL",
        "claims": claims_endorsed_disconnected_action(with_endorsement_id=False),
        "context": ctx_disconnected(endorsement_present=True),
        "msg_id": "msg:01HX4MAEEEEEEEEEEEEEEEEEEE",
        "nonce_seed": 0x0E,
        "issued_at": "2025-11-25T13:31:00Z",
        "expiry": "2025-11-25T13:36:00Z",
        "grade": 3,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "ms_action": "reject + push-to-hp-view",
            "audit_notes": [
                "§5.3.7 final bullet: Disconnected-period DISCLOSURE MUST carry endorsement_id.",
                "Absence breaks independent traceability of the offline action.",
            ],
        },
    },
    {
        "id": "15-disconnected-bogus-endorsement-id",
        "case": "f",
        "title": "Disconnected 期间 DISCLOSURE 携带不存在的 endorsement_id → E_PROTOCOL",
        "claims": claims_endorsed_disconnected_action(
            with_endorsement_id=True, endorsement_id=ENDORSEMENT_ID_BOGUS
        ),
        "context": ctx_disconnected(endorsement_present=True),
        "msg_id": "msg:01HX4MAFFFFFFFFFFFFFFFFFFF",
        "nonce_seed": 0x0F,
        "issued_at": "2025-11-25T13:32:00Z",
        "expiry": "2025-11-25T13:37:00Z",
        "grade": 3,
        "expected": {
            "outcome": "E_PROTOCOL",
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "ms_action": "reject + push-to-hp-view",
            "endorsement_id_referenced": ENDORSEMENT_ID_BOGUS,
            "endorsement_id_resolves": False,
            "audit_notes": [
                "endorsement_id refers to an endorsement not present on the Mandate.",
                "Independently-verifiable linkage fails — schema-level rejection.",
            ],
        },
    },
]


# ---------------------------------------------------------------------- #
# JSON serialisation helpers (CBOR bstr → base64url-no-pad in JSON)
# ---------------------------------------------------------------------- #

import base64


def _b64u(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def to_json_safe(value: Any) -> Any:
    """Recursively convert bytes/bytearray to base64url-no-pad strings."""
    if isinstance(value, (bytes, bytearray)):
        return {"$b64u": _b64u(bytes(value))}
    if isinstance(value, dict):
        return {k: to_json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_json_safe(v) for v in value]
    return value


# ---------------------------------------------------------------------- #
# Vector emission
# ---------------------------------------------------------------------- #


def emit_vector(v: Dict[str, Any]) -> Dict[str, Any]:
    folder = ROOT / v["id"]
    folder.mkdir(parents=True, exist_ok=True)

    env = envelope(
        msg_id=v["msg_id"],
        nonce_seed=v["nonce_seed"],
        issued_at=v["issued_at"],
        expiry=v["expiry"],
        grade=v["grade"],
        claims=v["claims"],
    )

    # --- CBOR (Deterministic, RFC 8949 §4.2.1) ---
    cbor_bytes = cbor2.dumps(env, canonical=True)
    (folder / "disclosure.cbor").write_bytes(cbor_bytes)

    # --- JSON (application/fap+json) ---
    json_payload = to_json_safe(env)
    (folder / "disclosure.json").write_text(
        json.dumps(json_payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    # --- context.json ---
    (folder / "context.json").write_text(
        json.dumps(
            {
                "vector_id": v["id"],
                "case": v["case"],
                "title": v["title"],
                "context": v["context"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    # --- expected.json ---
    (folder / "expected.json").write_text(
        json.dumps(
            {
                "vector_id": v["id"],
                "case": v["case"],
                **v["expected"],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "id": v["id"],
        "case": v["case"],
        "title": v["title"],
        "outcome": v["expected"]["outcome"],
        "files": {
            "disclosure_cbor": f"{v['id']}/disclosure.cbor",
            "disclosure_json": f"{v['id']}/disclosure.json",
            "context": f"{v['id']}/context.json",
            "expected": f"{v['id']}/expected.json",
        },
        "cbor_size_bytes": len(cbor_bytes),
    }


def emit_index(entries: List[Dict[str, Any]]) -> None:
    by_case: Dict[str, List[str]] = {}
    for e in entries:
        by_case.setdefault(e["case"], []).append(e["id"])

    index = {
        "spec": "Faying Protocol/1.0",
        "section_refs": ["§5.3.7", "§9.10.4 T3"],
        "requirement": "13.3",
        "property_ref": "P18.3 (Disclosure_Mandatory_Fields)",
        "encoding": {
            "cbor": "RFC 8949 Deterministic CBOR (§4.2.1); on-the-wire keys kebab-case",
            "json": "application/fap+json; bytes encoded as { \"$b64u\": <base64url-no-pad> }",
        },
        "case_legend": {
            "a": "全字段合法 DISCLOSURE",
            "b": "单 mandatory_field 缺失 → E_PROTOCOL",
            "c": "字段不可解析（枚举越界）→ E_PROTOCOL",
            "d": "高敏感动作未前置披露即执行 → 拒绝",
            "e": "DISCLOSURE 与实际动作不一致 → ego-deviation Revoke",
            "f": "Disconnected 期间 DISCLOSURE 必带 endorsement_id",
        },
        "case_coverage": by_case,
        "vectors": entries,
        "outcomes_present": sorted({e["outcome"] for e in entries}),
        "stub_signature_disclaimer": (
            "Signatures and attestations in these vectors are deterministic stubs; "
            "they exist only to keep the envelope CDDL-valid. Cryptographic "
            "verification is covered by vectors/encoding-equivalence/ (task 3.7) "
            "and conformance/dim_signing/ (task 5.3)."
        ),
    }

    (ROOT / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    entries: List[Dict[str, Any]] = []
    for v in VECTORS:
        entries.append(emit_vector(v))
    emit_index(entries)

    # --- Suite-wide invariants ---
    seen_cases = {e["case"] for e in entries}
    required_cases = {"a", "b", "c", "d", "e", "f"}
    assert required_cases <= seen_cases, (
        f"missing case coverage: {required_cases - seen_cases}"
    )
    assert len(entries) >= 10, f"need ≥10 vectors, got {len(entries)}"

    print(f"OK: emitted {len(entries)} vectors covering cases {sorted(seen_cases)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
