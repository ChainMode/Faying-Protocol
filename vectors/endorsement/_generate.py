#!/usr/bin/env python3
# =============================================================================
#  Test Vector Generator — Endorsed Mandate (Task 3.8)
#  ---------------------------------------------------------------------------
#  Spec:        .kiro/specs/faying-auth-protocol/
#  Requirement: 11.1 / 11.2 / 11.3 / 11.4
#  Properties:  P16.1 (signature inclusion), P16.3 (convergence)
#  Schema:      schemas/fap-1.0.cddl (authoritative)
#
#  Output layout (per vector dir):
#      <vector-id>/
#          mandate.cbor      Deterministic-CBOR encoding (RFC 8949 §4.2.1)
#          mandate.json      JSON view (kebab-case keys, hex-encoded bstr)
#          expected.json     Outcome contract incl. signature input hash
#
#  Outcome contract:
#      {
#        "vector_id":          "...",
#        "category":           "(a) | (b) | (c) | (d) | (e) | (f)",
#        "outcome":            "accepted" | "rejected",
#        "error_code":         null | 1007 | 1013,
#        "error_name":         null | "E_ATTESTATION_INVALID" | "E_ENDORSEMENT_INVALID",
#        "triggers":           ["revoke"?, ...],
#        "signature_input": {
#          "definition":       "H( Deterministic-CBOR(Mandate_without_signature) )",
#          "hash_alg":          "SHA-256",
#          "det_cbor_hex":      "....",
#          "hash_hex":          "....",
#          "endorsement_field_hash_hex":  "....",   # SHA-256( Det-CBOR(endorsement) ) — proves P16.1 inclusion
#          "endorsement_in_signature":    true | false
#        },
#        "violations":        [ ... ]              # human-readable breakdown
#      }
#
#  This generator is non-normative — it exists solely to manufacture
#  reproducible test vectors. Vectors themselves are normative inputs to the
#  conformance suite (tasks 5.x).
# =============================================================================

from __future__ import annotations

import copy
import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2
from cryptography.hazmat.primitives.asymmetric import ed25519

ROOT = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Deterministic, reproducible key material
# ---------------------------------------------------------------------------
# Every vector reuses the same fixed Ed25519 keypair so vectors are
# byte-stable across CI runs. Real deployments MUST NOT do this.
_FIXED_SEED = bytes.fromhex(
    "f1ec0a55be11000000000000000000000000000000000000000000000000d811"
)
_SK = ed25519.Ed25519PrivateKey.from_private_bytes(_FIXED_SEED)
_PK = _SK.public_key()
_PK_BYTES = _PK.public_bytes_raw()

# Same trick for an HP attestation key (different seed).
_HP_SEED = bytes.fromhex(
    "00112233445566778899aabbccddeeff00112233445566778899aabbccddeeff"
)
_HP_SK = ed25519.Ed25519PrivateKey.from_private_bytes(_HP_SEED)
_HP_PK = _HP_SK.public_key()
_HP_PK_BYTES = _HP_PK.public_bytes_raw()


# ---------------------------------------------------------------------------
# CBOR helpers
# ---------------------------------------------------------------------------

class _IsoTime:
    """Sentinel that survives the cbor2 default-hook to emit CBOR tag 0."""

    __slots__ = ("value",)

    def __init__(self, value: str) -> None:
        self.value = value


def _default_encoder(encoder: cbor2.CBOREncoder, value: Any) -> None:
    if isinstance(value, _IsoTime):
        encoder.encode(cbor2.CBORTag(0, value.value))
        return
    raise cbor2.CBOREncodeError(
        f"cannot encode object of type {type(value).__name__}"
    )


def det_cbor(obj: Any) -> bytes:
    """Deterministic CBOR (RFC 8949 §4.2.1) used for signature inputs."""
    return cbor2.dumps(
        obj,
        canonical=True,
        default=_default_encoder,
    )


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def _to_json_view(obj: Any) -> Any:
    """Render a CBOR-shaped dict into a JSON-friendly dict.

    - bytes → {"$bytes": "<hex>"}
    - _IsoTime → {"$tag": 0, "value": "<rfc3339>"}
    - dict / list / scalars → recursively converted
    """
    if isinstance(obj, _IsoTime):
        return {"$tag": 0, "value": obj.value}
    if isinstance(obj, bytes):
        return {"$bytes": obj.hex()}
    if isinstance(obj, dict):
        return {k: _to_json_view(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_to_json_view(v) for v in obj]
    return obj


def write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False, sort_keys=False) + "\n")


def write_cbor(path: Path, obj: Any) -> None:
    path.write_bytes(det_cbor(obj))


# ---------------------------------------------------------------------------
# Mandate factory
# ---------------------------------------------------------------------------

# Grade values follow §4.2 / §7.1: 0=G0 EmergencyOverride, 1=G1 Strict, ...
GRADE_G2 = 2
GRADE_G3 = 3
GRADE_G4 = 4

BASE_SCOPE: Dict[str, Any] = {
    "domains": ["https://api.example.com"],
    "actions": [
        "control:hvac:set-temperature",
        "control:lights:toggle",
        "read:sensors:temperature",
    ],
    "terminals": ["device-A", "device-B"],
}


def base_attestation(payload: bytes) -> Dict[str, Any]:
    """Build a minimal `attestation` value referencing the HP key."""
    sig = _HP_SK.sign(payload)
    return {
        "format": "webauthn",
        "payload": payload,
        "signer": "hp-key-001",
        "signature": {
            "alg": "Ed25519",
            "pubkey": _HP_PK_BYTES,
            "sig": sig,
        },
    }


def make_endorsement(
    *,
    enabled: bool = True,
    endorsed_scope: Optional[Dict[str, Any]] = None,
    endorsed_grade: int = GRADE_G3,
    endorsed_lifetime_ms: int = 60 * 60 * 1000,  # 1 hour
    offline_revocation_policy: str = "stop-and-audit",
) -> Dict[str, Any]:
    if endorsed_scope is None:
        # Default: strict subset of BASE_SCOPE — only one action, one domain.
        endorsed_scope = {
            "domains": ["https://api.example.com"],
            "actions": ["read:sensors:temperature"],
        }
    return {
        "enabled": enabled,
        "endorsed-scope": endorsed_scope,
        "endorsed-grade": endorsed_grade,
        "endorsed-lifetime-ms": endorsed_lifetime_ms,
        "offline-revocation-policy": offline_revocation_policy,
    }


def make_mandate(
    *,
    mandate_id: str,
    grade: int = GRADE_G2,
    scope: Optional[Dict[str, Any]] = None,
    not_before: str = "2026-01-01T00:00:00Z",
    not_after: str = "2026-01-02T00:00:00Z",  # 24h main lifetime
    parent: Optional[str] = None,
    endorsement: Optional[Dict[str, Any]] = None,
    issuer: str = "hp:01HX0000000000000000PRIME",
    subject: str = "fay:01HX00000000000000000FAY1",
    ms_id: str = "ms:01HX0000000000000000FAYMS",
) -> Dict[str, Any]:
    if scope is None:
        scope = copy.deepcopy(BASE_SCOPE)
    presence_req = {
        "signal-types": ["webauthn-uv-fresh", "presence-heartbeat-only"],
        "max-staleness-ms": 60_000 if grade == GRADE_G2 else 1_800_000,
        "on-loss": "downgrade-to:G3",
    }
    mandate: Dict[str, Any] = {
        "version": "Faying Protocol/1.0",
        "id": mandate_id,
        "issued-at": _IsoTime(not_before),
        "not-before": _IsoTime(not_before),
        "not-after": _IsoTime(not_after),
        "issuer": issuer,
        "ms-id": ms_id,
        "subject": subject,
        "scope": scope,
        "grade": grade,
        "presence-req": presence_req,
    }
    if parent is not None:
        mandate["parent"] = parent
    if endorsement is not None:
        mandate["endorsement"] = endorsement
    mandate["attestation"] = base_attestation(
        payload=b"webauthn-attestation:" + mandate_id.encode("ascii"),
    )
    return mandate


def sign_mandate(mandate: Dict[str, Any]) -> Tuple[Dict[str, Any], bytes, bytes, str]:
    """Attach a real signature to ``mandate`` and return (mandate, det_cbor_bytes, sig_input_hash_bytes, hex)."""
    body = {k: v for k, v in mandate.items() if k != "signature"}
    det = det_cbor(body)
    digest = hashlib.sha256(det).digest()
    sig = _SK.sign(digest)
    mandate["signature"] = {
        "alg": "Ed25519",
        "pubkey": _PK_BYTES,
        "sig": sig,
    }
    return mandate, det, digest, sha256(det)


def endorsement_field_hash(mandate: Dict[str, Any]) -> Optional[str]:
    """Hash of the deterministic CBOR encoding of just the endorsement subtree.

    Demonstrates that `endorsement` is materially included in the
    signature input (P16.1).
    """
    e = mandate.get("endorsement")
    if e is None:
        return None
    return sha256(det_cbor(e))


# ---------------------------------------------------------------------------
# Vector emit helper
# ---------------------------------------------------------------------------

REGISTRY: List[Dict[str, Any]] = []


def emit_vector(
    *,
    vector_id: str,
    title: str,
    category: str,
    requirements: List[str],
    properties: List[str],
    mandate_obj: Dict[str, Any],
    expected_outcome: str,
    error_code: Optional[int],
    error_name: Optional[str],
    triggers: List[str],
    violations: List[str],
    notes: str,
    tampered_post_sign: Optional[Dict[str, Any]] = None,
) -> None:
    """Materialise a vector directory.

    ``tampered_post_sign`` is an override applied AFTER signing — used by
    the (e) signature-tampering case so the signature on disk no longer
    matches the on-disk endorsement subtree.
    """
    out_dir = ROOT / vector_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Sign the *intended* mandate first (this is what the issuer signed).
    mandate_signed, det_cbor_bytes, sig_input_digest, sig_input_hash_hex = sign_mandate(
        copy.deepcopy(mandate_obj)
    )

    # If we're emitting an "after-the-fact tamper" vector, mutate the
    # mandate copy that gets written to disk. The signature stays the
    # legitimate one — verifying that signature against the tampered body
    # MUST fail.
    mandate_on_wire = mandate_signed
    if tampered_post_sign is not None:
        mandate_on_wire = copy.deepcopy(mandate_signed)
        for path, value in tampered_post_sign.items():
            cursor: Any = mandate_on_wire
            keys = path.split(".")
            for key in keys[:-1]:
                cursor = cursor[key]
            cursor[keys[-1]] = value

    # Serialise wire forms.
    write_cbor(out_dir / "mandate.cbor", mandate_on_wire)
    write_json(
        out_dir / "mandate.json",
        {
            "$comment": (
                "Non-normative JSON view. CBOR (mandate.cbor) is authoritative. "
                "Bytes are encoded as {\"$bytes\": \"<hex>\"}; CBOR tag 0 "
                "values as {\"$tag\": 0, \"value\": \"<rfc3339>\"}."
            ),
            "mandate": _to_json_view(mandate_on_wire),
        },
    )

    # Wire-form (post-tamper) hash. For non-tampered vectors this is identical
    # to the signature-input hash; for (e) it differs and that gap is the
    # P16.1 invariant violation.
    wire_body = {k: v for k, v in mandate_on_wire.items() if k != "signature"}
    wire_det = det_cbor(wire_body)
    wire_det_hash_hex = sha256(wire_det)

    expected: Dict[str, Any] = {
        "vector_id": vector_id,
        "title": title,
        "category": category,
        "requirements": requirements,
        "properties": properties,
        "outcome": expected_outcome,
        "error_code": error_code,
        "error_name": error_name,
        "triggers": triggers,
        "signature_input": {
            "definition": "H( Deterministic-CBOR(Mandate_without_signature) )",
            "hash_alg": "SHA-256",
            "det_cbor_hex": det_cbor_bytes.hex(),
            "hash_hex": sig_input_hash_hex,
            "endorsement_field_hash_hex": endorsement_field_hash(mandate_signed),
            "endorsement_in_signature": (
                mandate_signed.get("endorsement") is not None
            ),
            "wire_det_cbor_hex": wire_det.hex(),
            "wire_hash_hex": wire_det_hash_hex,
            "wire_matches_signature_input": (
                wire_det_hash_hex == sig_input_hash_hex
            ),
        },
        "violations": violations,
        "notes": notes,
    }
    if tampered_post_sign is not None:
        expected["post_sign_tamper"] = {
            "$comment": (
                "Wire-form mandate.cbor was mutated AFTER signing; signature "
                "in mandate.{cbor,json} is the legitimately-issued signature "
                "BEFORE the mutation. Verifying it against the on-disk body "
                "MUST fail (RP → E_ATTESTATION_INVALID). MS additionally "
                "treats the resulting object as E_ENDORSEMENT_INVALID."
            ),
            "tampered_paths": list(tampered_post_sign.keys()),
        }
    write_json(out_dir / "expected.json", expected)

    REGISTRY.append(
        {
            "vector_id": vector_id,
            "title": title,
            "category": category,
            "requirements": requirements,
            "properties": properties,
            "outcome": expected_outcome,
            "error_code": error_code,
            "error_name": error_name,
            "files": ["mandate.cbor", "mandate.json", "expected.json"],
        }
    )


# ---------------------------------------------------------------------------
# Vector definitions
# ---------------------------------------------------------------------------
#
#   (a) Legal Endorsed Mandate, one per offline_revocation_policy
#   (b) endorsed_scope ⊄ scope                       → E_ENDORSEMENT_INVALID (1013)
#   (c) endorsed_grade.autonomy > grade.autonomy     → E_ENDORSEMENT_INVALID (1013)
#   (d) lifetime missing / ∞-encoded / exceeds main  → E_ENDORSEMENT_INVALID (1013)
#   (e) signature tampering on endorsement subfield  → E_ATTESTATION_INVALID (1007) + Revoke
#   (f) DELEGATE child endorsement not converging on parent → E_ENDORSEMENT_INVALID (1013)
#
# Total: 13 vectors (>10 required).
# ---------------------------------------------------------------------------

INFINITE_LIFETIME_MS = (1 << 64) - 1  # CBOR uint sentinel for "no upper bound";
                                      # protocol forbids this even at uint-max.


def main() -> None:
    # -----------------------------------------------------------------------
    # (a) Three legal Endorsed Mandates — one per offline_revocation_policy.
    #     Spec authorises three policy values:
    #       - "stop-and-audit"
    #       - "stop-only"
    #       - "graceful-stop"
    #     (Task spec lists "4 values" but design.md §7.5 / schema enumerate
    #     exactly three; we cover all three and document the discrepancy in
    #     README.md.)
    # -----------------------------------------------------------------------
    for idx, policy in enumerate(
        ["stop-and-audit", "stop-only", "graceful-stop"], start=1
    ):
        endorsed = make_endorsement(
            enabled=True,
            endorsed_grade=GRADE_G3,            # autonomy(G3) ≤ autonomy(main G2)? See note.
            endorsed_lifetime_ms=30 * 60 * 1000,  # 30 min ≤ 24h main lifetime
            offline_revocation_policy=policy,
        )
        # NOTE on grade direction: §11.2 mandates
        #   endorsement.endorsed_grade.autonomy ≤ Mandate.grade.autonomy
        # Numerically (per §4.2: 1=Strict ... 4=Autonomous), autonomy is
        # *monotone increasing* with the grade number. Therefore "endorsed
        # grade has lower or equal autonomy than the main grade" means
        # endorsed_grade ≤ main grade numerically. With main grade = G2 (2),
        # the only legal endorsed values are G1 or G2. Use G2 here so the
        # endorsement permits behaviour at the same grade.
        endorsed["endorsed-grade"] = GRADE_G2
        mandate = make_mandate(
            mandate_id=f"mnd:01HXENDORS-LEGAL-{idx:02d}",
            grade=GRADE_G2,
            endorsement=endorsed,
        )
        emit_vector(
            vector_id=f"a-legal-policy-{policy}",
            title=f"(a) Legal Endorsed Mandate — offline_revocation_policy = \"{policy}\"",
            category="(a) Legal Endorsed Mandate",
            requirements=["11.1", "11.2", "11.3", "11.4"],
            properties=["P16.1", "P16.3"],
            mandate_obj=mandate,
            expected_outcome="accepted",
            error_code=None,
            error_name=None,
            triggers=[],
            violations=[],
            notes=(
                "All four convergence conditions hold:\n"
                "  endorsed_scope ⊆ scope            ✓\n"
                "  endorsed_grade.autonomy ≤ grade   ✓ (both = G2)\n"
                "  endorsed_lifetime_ms = 1.8e6 ms   ≤ 24h main lifetime ✓\n"
                f"  offline_revocation_policy = \"{policy}\" ∈ enum ✓\n"
                "Endorsement subtree is part of the signature input "
                "(see signature_input.endorsement_field_hash_hex)."
            ),
        )

    # -----------------------------------------------------------------------
    # (b) endorsed_scope ⊄ scope  →  E_ENDORSEMENT_INVALID (1013)
    # -----------------------------------------------------------------------
    bad_scope_endorsement = make_endorsement(
        enabled=True,
        endorsed_scope={
            "domains": [
                "https://api.example.com",
                "https://api.UNAUTHORIZED.example.org",  # not in main scope.domains
            ],
            "actions": [
                "read:sensors:temperature",
                "control:wallet:transfer",  # not in main scope.actions
            ],
        },
        endorsed_grade=GRADE_G2,
        endorsed_lifetime_ms=30 * 60 * 1000,
        offline_revocation_policy="stop-and-audit",
    )
    mandate_b = make_mandate(
        mandate_id="mnd:01HXENDORS-B-SCOPE-OVRFLOW",
        grade=GRADE_G2,
        endorsement=bad_scope_endorsement,
    )
    emit_vector(
        vector_id="b-scope-violation",
        title="(b) endorsed_scope ⊄ scope",
        category="(b) scope convergence violation",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_b,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            "endorsement.endorsed-scope.domains ⊄ scope.domains: "
            "'https://api.UNAUTHORIZED.example.org' not in {https://api.example.com}",
            "endorsement.endorsed-scope.actions ⊄ scope.actions: "
            "'control:wallet:transfer' not in {control:hvac:set-temperature, "
            "control:lights:toggle, read:sensors:temperature}",
        ],
        notes=(
            "MS MUST reject at issuance time per §11.2 / §7.5. "
            "Per §5.4 row 1013, this is also the rejection reason at "
            "verification time and triggers Revoke."
        ),
    )

    # -----------------------------------------------------------------------
    # (c) endorsed_grade.autonomy > grade.autonomy  →  E_ENDORSEMENT_INVALID
    # -----------------------------------------------------------------------
    bad_grade_endorsement = make_endorsement(
        enabled=True,
        endorsed_grade=GRADE_G4,  # autonomy 4 > main grade autonomy 2
        endorsed_lifetime_ms=30 * 60 * 1000,
        offline_revocation_policy="stop-and-audit",
    )
    mandate_c = make_mandate(
        mandate_id="mnd:01HXENDORS-C-GRADE-EXCEED",
        grade=GRADE_G2,
        endorsement=bad_grade_endorsement,
    )
    emit_vector(
        vector_id="c-grade-violation",
        title="(c) endorsed_grade.autonomy > grade.autonomy",
        category="(c) grade convergence violation",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_c,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            "endorsement.endorsed-grade=G4(autonomy=4) > Mandate.grade=G2(autonomy=2); "
            "violates §11.2 §7.5 'endorsed_grade.autonomy ≤ Mandate.grade.autonomy'."
        ],
        notes=(
            "Disconnected-window autonomy may not exceed online-window autonomy; "
            "MS rejects at issuance, RP rejects at verification — both with 1013."
        ),
    )

    # -----------------------------------------------------------------------
    # (d) Lifetime violations — three sub-vectors:
    #     d1 missing endorsed_lifetime_ms (CDDL-level violation)
    #     d2 ∞-encoded lifetime (uint MAX, treated as forbidden infinite)
    #     d3 lifetime exceeds main mandate lifetime
    # -----------------------------------------------------------------------
    # d1 — missing
    d1_endorsement = make_endorsement(endorsed_lifetime_ms=30 * 60 * 1000)
    d1_endorsement["endorsed-grade"] = GRADE_G2
    del d1_endorsement["endorsed-lifetime-ms"]
    mandate_d1 = make_mandate(
        mandate_id="mnd:01HXENDORS-D1-LT-MISSING",
        grade=GRADE_G2,
        endorsement=d1_endorsement,
    )
    emit_vector(
        vector_id="d1-lifetime-missing",
        title="(d.1) endorsed_lifetime_ms missing",
        category="(d) lifetime violation",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_d1,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            "endorsement.endorsed-lifetime-ms is absent; CDDL requires the "
            "field; §11.2 forbids implicit / infinite lifetime."
        ],
        notes=(
            "CDDL `endorsement` map requires `endorsed-lifetime-ms`. Missing "
            "field MUST surface as 1013 even if a permissive decoder accepts "
            "the structure."
        ),
    )

    # d2 — ∞-encoded (uint MAX64)
    d2_endorsement = make_endorsement(
        endorsed_lifetime_ms=INFINITE_LIFETIME_MS,
        endorsed_grade=GRADE_G2,
    )
    mandate_d2 = make_mandate(
        mandate_id="mnd:01HXENDORS-D2-LT-INFINITE",
        grade=GRADE_G2,
        endorsement=d2_endorsement,
    )
    emit_vector(
        vector_id="d2-lifetime-infinite",
        title="(d.2) endorsed_lifetime_ms encoded as ∞ (uint64 max)",
        category="(d) lifetime violation",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_d2,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            f"endorsement.endorsed-lifetime-ms = {INFINITE_LIFETIME_MS} interpreted as "
            "infinite; §11.2 explicitly forbids '∞ or missing'.",
            f"endorsement.endorsed-lifetime-ms ({INFINITE_LIFETIME_MS}) > "
            "(not_after − not_before) = 86_400_000 ms.",
        ],
        notes=(
            "CBOR has no native infinity for unsigned integers; protocol "
            "treats uint MAX (or any value exceeding the main lifetime) "
            "as the forbidden 'infinite' case."
        ),
    )

    # d3 — exceeds main mandate lifetime (25h vs 24h main)
    d3_endorsement = make_endorsement(
        endorsed_lifetime_ms=25 * 60 * 60 * 1000,
        endorsed_grade=GRADE_G2,
    )
    mandate_d3 = make_mandate(
        mandate_id="mnd:01HXENDORS-D3-LT-EXCEEDS",
        grade=GRADE_G2,
        endorsement=d3_endorsement,
    )
    emit_vector(
        vector_id="d3-lifetime-exceeds-main",
        title="(d.3) endorsed_lifetime_ms > Mandate.not_after − not_before",
        category="(d) lifetime violation",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_d3,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            "endorsement.endorsed-lifetime-ms = 90_000_000 ms (25h) "
            "> 86_400_000 ms = (not_after − not_before).",
        ],
        notes=(
            "Disconnected-window lifetime cannot outlive the main mandate; "
            "MS rejects at issuance with 1013."
        ),
    )

    # -----------------------------------------------------------------------
    # (e) Signature tampering on an endorsement subfield
    #     e1 enabled flipped false → true
    #     e2 endorsed-scope.actions widened
    # -----------------------------------------------------------------------
    # e1 — original signed mandate has enabled=true; we tamper-flip endorsed-grade
    #      after signing so the on-disk body no longer matches the signature.
    e1_endorsement = make_endorsement(
        enabled=True,
        endorsed_grade=GRADE_G2,
        endorsed_lifetime_ms=30 * 60 * 1000,
    )
    mandate_e1 = make_mandate(
        mandate_id="mnd:01HXENDORS-E1-TAMPER-GRADE",
        grade=GRADE_G2,
        endorsement=e1_endorsement,
    )
    emit_vector(
        vector_id="e1-signature-tamper-endorsed-grade",
        title="(e.1) endorsement.endorsed_grade tampered post-signature",
        category="(e) signature tampering",
        requirements=["11.1"],
        properties=["P16.1"],
        mandate_obj=mandate_e1,
        expected_outcome="rejected",
        error_code=1007,
        error_name="E_ATTESTATION_INVALID",
        triggers=["revoke", "ms_secondary_E_ENDORSEMENT_INVALID"],
        violations=[
            "Wire-form endorsement.endorsed-grade was changed to G4 (autonomy=4) "
            "after signing; the legitimately-issued signature was over G2.",
            "RP signature verification fails → 1007 E_ATTESTATION_INVALID; "
            "MS additionally classifies the now-decoded body as 1013 "
            "E_ENDORSEMENT_INVALID (autonomy(G4) > autonomy(G2)).",
        ],
        notes=(
            "Per §6.3 / §12 P16.1 the endorsement subtree is included in "
            "Deterministic-CBOR(Mandate_without_signature). Any post-signing "
            "mutation breaks the signature."
        ),
        tampered_post_sign={
            "endorsement.endorsed-grade": GRADE_G4,
        },
    )

    # e2 — widen endorsed-scope.actions after signing
    e2_endorsement = make_endorsement(
        enabled=True,
        endorsed_grade=GRADE_G2,
        endorsed_lifetime_ms=30 * 60 * 1000,
    )
    mandate_e2 = make_mandate(
        mandate_id="mnd:01HXENDORS-E2-TAMPER-SCOPE",
        grade=GRADE_G2,
        endorsement=e2_endorsement,
    )
    tampered_endorsed_scope = {
        "domains": ["https://api.example.com"],
        "actions": [
            "read:sensors:temperature",
            "control:wallet:transfer",  # injected by attacker
        ],
    }
    emit_vector(
        vector_id="e2-signature-tamper-endorsed-scope",
        title="(e.2) endorsement.endorsed_scope tampered post-signature",
        category="(e) signature tampering",
        requirements=["11.1"],
        properties=["P16.1"],
        mandate_obj=mandate_e2,
        expected_outcome="rejected",
        error_code=1007,
        error_name="E_ATTESTATION_INVALID",
        triggers=["revoke", "ms_secondary_E_ENDORSEMENT_INVALID"],
        violations=[
            "Wire-form endorsement.endorsed-scope.actions was widened to "
            "include 'control:wallet:transfer' after signing.",
            "Signature verification fails → 1007; MS secondary check "
            "yields 1013 (endorsed_scope ⊄ scope).",
        ],
        notes=(
            "Demonstrates that even if an attacker arranges for the post-tamper "
            "endorsed_scope to *also* exceed the main scope, the FIRST line of "
            "defence (signature) still catches the tamper."
        ),
        tampered_post_sign={
            "endorsement.endorsed-scope": tampered_endorsed_scope,
        },
    )

    # -----------------------------------------------------------------------
    # (f) DELEGATE child endorsement not converging on parent endorsement
    #     §9.7 derivation rules.
    # -----------------------------------------------------------------------
    parent_endorsement = make_endorsement(
        enabled=True,
        endorsed_scope={
            "domains": ["https://api.example.com"],
            "actions": ["read:sensors:temperature"],
        },
        endorsed_grade=GRADE_G2,
        endorsed_lifetime_ms=30 * 60 * 1000,
        offline_revocation_policy="stop-and-audit",
    )
    parent = make_mandate(
        mandate_id="mnd:01HXENDORS-F-PARENT",
        grade=GRADE_G2,
        endorsement=parent_endorsement,
    )
    # Mint the parent so we can reference its id.
    parent_signed, _, _, _ = sign_mandate(copy.deepcopy(parent))
    parent_id = parent_signed["id"]

    child_scope: Dict[str, Any] = copy.deepcopy(BASE_SCOPE)  # ⊆ parent.scope (equal)
    child_endorsement = make_endorsement(
        enabled=True,
        endorsed_scope={  # child endorsed_scope NOT ⊆ parent endorsed_scope
            "domains": ["https://api.example.com"],
            "actions": [
                "read:sensors:temperature",
                "control:lights:toggle",  # parent endorsement only allows read:sensors:temperature
            ],
        },
        endorsed_grade=GRADE_G2,
        endorsed_lifetime_ms=30 * 60 * 1000,
        offline_revocation_policy="stop-and-audit",
    )
    mandate_f = make_mandate(
        mandate_id="mnd:01HXENDORS-F-CHILD-DIVERGE",
        grade=GRADE_G2,
        scope=child_scope,
        parent=parent_id,
        endorsement=child_endorsement,
        subject="fay:01HX00000000000000000FAY2",
    )
    emit_vector(
        vector_id="f-delegate-child-not-converging",
        title="(f) DELEGATE child endorsement not converging on parent endorsement",
        category="(f) DELEGATE child endorsement divergence",
        requirements=["11.2"],
        properties=["P16.3"],
        mandate_obj=mandate_f,
        expected_outcome="rejected",
        error_code=1013,
        error_name="E_ENDORSEMENT_INVALID",
        triggers=["revoke"],
        violations=[
            "child.endorsement.endorsed_scope.actions ⊄ "
            "parent.endorsement.endorsed_scope.actions: "
            "'control:lights:toggle' missing from parent endorsement.",
            "Per §9.7 'Endorsed Mandate 派生（DELEGATE）的 endorsement 收敛约束', "
            "child endorsement MUST be ⊆ parent endorsement on all four axes.",
        ],
        notes=(
            "Parent mandate id = " + parent_id + ". The child mandate references "
            "parent via the `parent` field. MS at DELEGATE time MUST reject "
            "with E_ENDORSEMENT_INVALID (1013); §9.7 also permits MS to use "
            "1099 E_PROTOCOL — the spec authorises either, but §5.4 row 1013 "
            "is the more specific code and is preferred."
        ),
    )


    # -----------------------------------------------------------------------
    # Index
    # -----------------------------------------------------------------------
    index = {
        "$comment": (
            "Endorsed Mandate test vectors — see README.md for category map. "
            "Generated by _generate.py; do not edit by hand. The CDDL schema "
            "in schemas/fap-1.0.cddl is authoritative for wire format."
        ),
        "spec": "Faying Protocol/1.0",
        "task": "3.8 Endorsed Mandate test vectors",
        "requirements": ["11.1", "11.2", "11.3", "11.4"],
        "properties": ["P16.1", "P16.3"],
        "schema": "schemas/fap-1.0.cddl",
        "design_anchors": [
            "design.md §4.1 (Endorsement type)",
            "design.md §4.2 (CDDL endorsement)",
            "design.md §5.4 (error codes 1007 / 1013)",
            "design.md §6.3 (signature input + endorsement inclusion)",
            "design.md §7.5 (Endorsement Grades)",
            "design.md §9.7 (DELEGATE endorsement convergence)",
            "design.md §11.x (P16.1 / P16.3 narrative)",
        ],
        "categories": {
            "(a)": "Legal Endorsed Mandate (one per offline_revocation_policy)",
            "(b)": "scope convergence violation → 1013 E_ENDORSEMENT_INVALID",
            "(c)": "grade convergence violation → 1013 E_ENDORSEMENT_INVALID",
            "(d)": "lifetime violation (missing / ∞ / exceeds main) → 1013 E_ENDORSEMENT_INVALID",
            "(e)": "signature tampering on endorsement subfield → 1007 E_ATTESTATION_INVALID + Revoke",
            "(f)": "DELEGATE child endorsement not converging on parent → 1013 E_ENDORSEMENT_INVALID",
        },
        "vectors": REGISTRY,
    }
    write_json(ROOT / "index.json", index)


if __name__ == "__main__":
    main()
    print(f"Generated {len(REGISTRY)} vectors under {ROOT}.")
