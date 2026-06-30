"""
Generate REVOKE test vectors for Faying Protocol/1.0.

Output layout (relative to the parent directory of this file)::

    reason-human-initiated/                request.{cbor,json}  response.{cbor,json}  expected.json
    reason-expiry/                         …
    reason-task-completed/                 …
    reason-human-prime-unreachable/        …
    reason-ego-deviation/                  …
    reason-fay-credential-invalid/         …
    reason-human-prime-credential-invalid/ …
    reason-regulatory-order/               …
    reason-terminal-disconnected/          …
    cascade-depth-2/                       …  (cascade=true, derivation tree depth 2)
    cascade-disabled/                      …  (cascade=false; children stay Active)
    irreversibility-double-revoke/         …  (second REVOKE on Revoked Mandate is idempotent)
    irreversibility-rebootstrap-new-id/    …  (only recovery path = fresh BOOTSTRAP, new mandate_id)
    neg-use-after-revoke/                  …  (post-Revoke RP call → E_REVOKED 1006)
    index.json
    README.md  (authored separately)

These vectors exercise:

* design.md §5.3.5 — REVOKE wire shape (`mandate_id`, `cascade`,
  `reason ∈ RevokeReason`, `effective_at`) and `REVOKE_RECEIPT`
  carrying post-revocation state (cascaded child IDs).
* design.md §3.4 / §9.6 — `RevocationVisibilityBudget` (default 1s)
  upper-bounds the latency from `effective_at` to RR-visible
  `revoked` status; every vector records the expected RR visibility
  timestamp `≤ effective_at + 1000ms`.
* design.md §4.3 / §8.1 — Mandate state machine: Revoked is a
  terminal state; no `Revoked → Active` transition exists.
* design.md §7.5 / §9.7 — cascade revocation propagates to every
  descendant Mandate in the derivation subtree (`child.parent ==
  parent.id`), and no new DELEGATE may use the Revoked parent.
* design.md §EH.1 — `1006 E_REVOKED` is returned to any RP that
  presents a Revoked Mandate.
* Blueprint chapter 13 — the nine `RevokeReason` enum values
  exhaustively cover the nine decoupling triggers.

Determinism contract
--------------------
* All Ed25519 keypairs, nonces, mandate / message ids, and
  synthetic payload bytes are derived from the fixed master seed
  ``FAYING_VECTOR_SEED``. The seed is intentionally identical to
  the one used by the BOOTSTRAP / PRESENCE / GRADE_SWITCH /
  DELEGATE batches so all batches share a single reproducibility
  anchor.
* Every key derivation goes through the per-batch domain separator
  ``b"revoke|"`` so vectors here do not collide with other batches.
* CBOR is encoded with ``cbor2.dumps(canonical=True)`` (RFC 8949
  §4.2.1). The signing input for every signed object is the
  canonical CBOR encoding of the unsigned object, regardless of
  wire encoding. JSON vectors mirror the CBOR shape via the
  ``{"$bytes": "<base64url>"}`` and ``{"$tag": 0, "$value": ...}``
  conventions established by the other batches.

Acceptance (task 3.5)
---------------------
* Every one of the nine ``RevokeReason`` enum values has at least
  one positive vector emitting a signed REVOKE → REVOKE_RECEIPT
  pair.
* The cascade-true vector targets a derivation tree of depth 2
  (parent → child → grandchild) and the receipt enumerates all
  affected mandate ids in topological order.
* Revocation irreversibility (Requirement 4.3) is documented by a
  double-revoke idempotence vector and a re-bootstrap-after-revoke
  vector showing the recovery path issues a fresh Mandate with a
  *different* ``mandate_id``.
* Every vector's ``expected.json`` records the RR visibility
  timestamp (`effective_at + RevocationVisibilityBudget`), the
  affected mandate id list, and the audit-event five-tuple
  ``(error_code, mandate_id, ts, rp_id, reason)`` written to the
  Attestation Chain.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519


# ---------------------------------------------------------------------------
# Deterministic source of randomness
# ---------------------------------------------------------------------------

# 32-byte fixed seed; identical to the BOOTSTRAP / PRESENCE /
# GRADE_SWITCH / DELEGATE batches so the five are anchored on one
# reproducibility seed. The per-batch domain separator below ensures
# no key / nonce collision between batches.
FAYING_VECTOR_SEED = bytes.fromhex(
    "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    "0001020304050607080910111213a414"
)

# design.md §9.6 / Appendix B — `RevocationVisibilityBudget` default
# is 1000ms. Every vector materialises the expected RR-visibility
# timestamp as `effective_at + REVOCATION_VISIBILITY_BUDGET_MS`.
REVOCATION_VISIBILITY_BUDGET_MS = 1000


def derive(label: str, length: int = 32) -> bytes:
    """Deterministically expand the master seed into label-tagged bytes.

    Uses SHA-256 in counter mode under the per-batch domain separator
    ``b"revoke|"`` so callers can name keys, nonces, and synthetic
    payload bytes by stable string labels and never collide with the
    other vector batches.
    """
    out = b""
    counter = 0
    while len(out) < length:
        h = hashlib.sha256()
        h.update(FAYING_VECTOR_SEED)
        h.update(b"revoke|")  # batch domain separator
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
# §7.1 freshness budgets and primary signal types
# (Aligned with vectors/delegate/_tools/generate.py.)
# ---------------------------------------------------------------------------


GRADE_MAX_STALENESS_MS: Dict[int, int] = {
    1:        5_000,
    2:       60_000,
    3:      300_000,
    4:    1_800_000,
}

GRADE_PRIMARY_SIGNAL: Dict[int, List[str]] = {
    1: ["webauthn-uv-fresh", "face-continuous"],
    2: ["fingerprint-tap"],
    3: ["intent-ticket"],
    4: ["presence-heartbeat-only"],
}


# ---------------------------------------------------------------------------
# Builders aligned with CDDL (`mandate`, `scope`, `presence-requirement`,
# `attestation`, `signature-bundle`) and the §5.3.5 REVOKE claims.
# ---------------------------------------------------------------------------


def make_attestation(kp: Ed25519KeyPair, label: str) -> Dict[str, Any]:
    """Build an ``attestation`` object signing a deterministic payload.

    Mirrors the BOOTSTRAP / PRESENCE / GRADE_SWITCH / DELEGATE
    generators so the five batches share an identical attestation
    shape.
    """
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
    kp: Ed25519KeyPair,
    signed_message: bytes,
    *,
    chain: Optional[List[bytes]] = None,
) -> Dict[str, Any]:
    """Build the CDDL ``signature-bundle`` rule.

    When ``chain`` is provided, every entry is base64url-encoded into
    the ``$bytes`` JSON marker so that the full ancestor chain
    round-trips through both CBOR and JSON encodings without losing
    bytes.
    """
    bundle: Dict[str, Any] = {
        "alg": "Ed25519",
        "pubkey": bytes_marker(kp.pubkey_raw),
        "sig": bytes_marker(sign(kp, signed_message)),
    }
    if chain is not None:
        bundle["chain"] = [bytes_marker(c) for c in chain]
    return bundle


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

    Mirrors the structure used by the BOOTSTRAP / PRESENCE /
    GRADE_SWITCH / DELEGATE generators so all batches share the same
    canonical-CBOR signing-input convention.
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


# ---------------------------------------------------------------------------
# Scope helpers
# ---------------------------------------------------------------------------


def make_scope() -> Dict[str, Any]:
    """A standard scope for the Mandate that gets revoked."""
    return {
        "domains": [
            "https://api.example.com/v1/calendar",
            "https://api.example.com/v1/mail",
        ],
        "actions": [
            "calendar:event:read",
            "calendar:event:update",
            "mail:message:read",
        ],
        "terminals": [
            "terminal:laptop:fixed-1",
            "terminal:phone:mobile-1",
        ],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 100,
        },
    }


def make_child_scope_subset() -> Dict[str, Any]:
    return {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": ["calendar:event:read", "calendar:event:update"],
        "terminals": ["terminal:phone:mobile-1"],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 50,
        },
    }


def make_grandchild_scope_subset() -> Dict[str, Any]:
    return {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": ["calendar:event:read"],
        "terminals": ["terminal:phone:mobile-1"],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 10,
        },
    }


def make_presence_req(grade: int) -> Dict[str, Any]:
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


# ---------------------------------------------------------------------------
# Mandate construction with full attestation chain support
# ---------------------------------------------------------------------------


@dataclass
class SignedMandate:
    tree: Dict[str, Any]
    signing_input: bytes
    outer_sig: bytes
    chain: List[bytes] = field(default_factory=list)
    chain_labels: List[str] = field(default_factory=list)


def make_ms_cert_signature(
    *,
    hp_kp: Ed25519KeyPair,
    ms_kp: Ed25519KeyPair,
    label: str,
) -> Tuple[bytes, Dict[str, Any]]:
    """Synthesize the HP-signed MS-Cert that anchors the AC chain."""
    cert_tree = {
        "version": "Faying Protocol/1.0",
        "kind": "ms-cert",
        "hp-pubkey": bytes_marker(hp_kp.pubkey_raw),
        "ms-pubkey": bytes_marker(ms_kp.pubkey_raw),
        "ms-id": f"ms:vector-{label}",
        "issued-at": time_marker("2026-01-01T00:00:00Z"),
        "not-after": time_marker("2026-12-31T23:59:59Z"),
    }
    signing_input = cbor_canonical(cbor_for_json(cert_tree))
    return sign(hp_kp, signing_input), cert_tree


def make_signed_mandate(
    *,
    mandate_id: str,
    issuer: str,
    subject: str,
    grade: int,
    issued_at: str,
    not_before: str,
    not_after: str,
    scope: Dict[str, Any],
    ms_kp: Ed25519KeyPair,
    label: str,
    parent_id: Optional[str] = None,
    chain: Optional[List[bytes]] = None,
) -> SignedMandate:
    skeleton: Dict[str, Any] = {
        "version": "Faying Protocol/1.0",
        "id": mandate_id,
        "issued-at": time_marker(issued_at),
        "not-before": time_marker(not_before),
        "not-after": time_marker(not_after),
        "issuer": issuer,
        "ms-id": f"ms:vector-{label}",
        "subject": subject,
        "scope": scope,
        "grade": grade,
        "presence-req": make_presence_req(grade),
        "attestation": make_attestation(ms_kp, f"ms-{label}"),
    }
    if parent_id is not None:
        skeleton["parent"] = parent_id
    signing_input = cbor_canonical(cbor_for_json(skeleton))
    outer_sig = sign(ms_kp, signing_input)

    full = dict(skeleton)
    full["signature"] = make_signature_bundle(
        ms_kp, signing_input, chain=chain
    )
    chain_labels: List[str] = []
    if chain is not None:
        chain_labels = (
            ["hp-root:ms-cert"]
            + [f"parent-{i}:outer-sig" for i in range(len(chain) - 1)]
        )
    return SignedMandate(
        tree=full,
        signing_input=signing_input,
        outer_sig=outer_sig,
        chain=list(chain) if chain is not None else [],
        chain_labels=chain_labels,
    )


# ---------------------------------------------------------------------------
# Chain construction primitives (subset of vectors/delegate)
# ---------------------------------------------------------------------------


@dataclass
class ChainContext:
    hp_kp: Ed25519KeyPair
    ms_kp: Ed25519KeyPair
    ms_cert_sig: bytes
    ms_cert_tree: Dict[str, Any]


def make_chain_ctx(label: str) -> ChainContext:
    hp_kp = make_ed25519(f"chain:hp:{label}")
    ms_kp = make_ed25519(f"chain:ms:{label}")
    ms_cert_sig, ms_cert_tree = make_ms_cert_signature(
        hp_kp=hp_kp, ms_kp=ms_kp, label=label
    )
    return ChainContext(
        hp_kp=hp_kp,
        ms_kp=ms_kp,
        ms_cert_sig=ms_cert_sig,
        ms_cert_tree=ms_cert_tree,
    )


# ---------------------------------------------------------------------------
# Time / id helpers
# ---------------------------------------------------------------------------


def _common_window() -> Tuple[str, str, str, str]:
    """Issued-at / not-before / not-after / envelope expiry tuple."""
    issued_at  = "2026-01-01T00:00:00Z"
    not_before = "2026-01-01T00:00:00Z"
    not_after  = "2026-01-01T23:59:59Z"
    expiry     = "2026-01-01T00:01:00Z"
    return issued_at, not_before, not_after, expiry


def _suffix(name: str) -> str:
    return name.upper().replace("-", "_")


def _add_ms(iso: str, delta_ms: int) -> str:
    """Add ``delta_ms`` milliseconds to an ISO timestamp.

    Used to materialise the RR-visibility timestamp = effective_at +
    REVOCATION_VISIBILITY_BUDGET_MS without dragging in a datetime
    dependency that would obscure the deterministic-output guarantee.
    """
    from datetime import datetime, timedelta, timezone

    dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
    out = dt + timedelta(milliseconds=delta_ms)
    out = out.astimezone(timezone.utc)
    # Produce a millisecond-resolution RFC 3339 string. We only emit
    # millisecond precision when the delta makes it necessary, so
    # whole-second timestamps remain whole-second on the wire.
    if out.microsecond == 0:
        return out.strftime("%Y-%m-%dT%H:%M:%SZ")
    return (
        out.strftime("%Y-%m-%dT%H:%M:%S.")
        + f"{out.microsecond // 1000:03d}Z"
    )



# ---------------------------------------------------------------------------
# REVOKE / REVOKE_RECEIPT envelope builders
# ---------------------------------------------------------------------------


def _build_revoke_request(
    *,
    name: str,
    grade: int,
    issuer: str,
    subject: str,
    msg_id_req: str,
    target_mandate_id: str,
    cascade: bool,
    reason: str,
    effective_at: str,
    requesting_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    """Build the REVOKE envelope per design.md §5.3.5.

    The envelope is signed by the HP root key (``requesting_kp``);
    REVOKE is the symmetric counterpart of BOOTSTRAP, so the
    authentication strength on the way out matches the authentication
    strength on the way in (Requirement 4.1.3).
    """
    issued_at, _not_before, _not_after, expiry = _common_window()
    nonce = derive(f"req-nonce:{name}", 16)
    claims: Dict[str, Any] = {
        "mandate_id":   target_mandate_id,
        "cascade":      cascade,
        "reason":       reason,
        "effective_at": time_marker(effective_at),
    }
    return envelope_skeleton(
        msg_type="REVOKE",
        msg_id=msg_id_req,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=grade,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(requesting_kp, f"req-{name}"),
    )


def _build_revoke_receipt(
    *,
    name: str,
    grade: int,
    issuer: str,
    subject: str,
    msg_id_resp: str,
    target_mandate_id: str,
    reason: str,
    revoked_at: str,
    cascade: bool,
    cascaded_mandate_ids: List[str],
    ms_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    """Build the REVOKE_RECEIPT envelope.

    Carries the post-revocation state so downstream RPs can
    short-circuit cached Mandate evaluations (design.md §5.3.5):

      * ``mandate_id`` — the directly-revoked Mandate.
      * ``reason``     — mirrored from the request.
      * ``revoked_at`` — when the revocation became authoritative
                         (typically equals the request's
                         ``effective_at``).
      * ``cascade``    — mirrored from the request so verifiers can
                         confirm cascade semantics.
      * ``cascaded_mandate_ids`` — child IDs revoked transitively
                         in the same atomic transaction.
    """
    issued_at, _not_before, _not_after, expiry = _common_window()
    claims: Dict[str, Any] = {
        "mandate_id":           target_mandate_id,
        "reason":               reason,
        "revoked_at":           time_marker(revoked_at),
        "cascade":              cascade,
        "cascaded_mandate_ids": list(cascaded_mandate_ids),
    }
    return envelope_skeleton(
        msg_type="REVOKE_RECEIPT",
        msg_id=msg_id_resp,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=grade,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


def _build_error_response(
    *,
    name: str,
    grade: int,
    issuer: str,
    subject: str,
    msg_id_resp: str,
    target_mandate_id: str,
    code: int,
    error_name: str,
    detail: str,
    ms_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    """Build an ERROR envelope for negative vectors (e.g. 1006 E_REVOKED)."""
    issued_at, _not_before, _not_after, expiry = _common_window()
    return envelope_skeleton(
        msg_type="ERROR",
        msg_id=msg_id_resp,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=grade,
        issuer=issuer,
        subject=subject,
        claims={
            "code":       code,
            "name":       error_name,
            "detail":     detail,
            "mandate_id": target_mandate_id,
        },
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


def _audit_event(
    *,
    error_code: Optional[int],
    mandate_id: str,
    ts: str,
    rp_id: str,
    reason: str,
    notes: str,
) -> Dict[str, Any]:
    """Render the audit-log five-tuple §9.6 prescribes.

    The five-tuple ``(error_code, mandate_id, ts, rp_id, reason)`` is
    what an independent auditor uses to reconstruct accountability
    end-to-end. ``error_code`` is ``null`` for the success path
    (REVOKE → REVOKE_RECEIPT) and equals 1006 for post-revocation
    use-after-revoke.
    """
    return {
        "error_code": error_code,
        "mandate_id": mandate_id,
        "ts":         time_marker(ts),
        "rp_id":      rp_id,
        "reason":     reason,
        "notes":      notes,
    }


# ---------------------------------------------------------------------------
# Vector specification
# ---------------------------------------------------------------------------


@dataclass
class VectorSpec:
    name: str
    kind: str               # "positive" | "negative"
    summary: str
    requirements: List[str]
    request_tree: Dict[str, Any]
    request_kp: Ed25519KeyPair       # HP signs REVOKE; MS signs ERROR
    response_tree: Dict[str, Any]
    response_kp: Ed25519KeyPair      # MS signs the response envelope
    target_mandate_id: str
    cascade: bool
    reason: Optional[str]
    affected_mandate_ids: List[str]
    expected_extras: Dict[str, Any]
    notes: str
    error_code: Optional[int] = None
    error_name: Optional[str] = None



# ---------------------------------------------------------------------------
# Per-RevokeReason positive vector builder
# ---------------------------------------------------------------------------


# `RevokeReason` ↔ blueprint chapter-13 trigger map (design.md §5.3.5).
# Every entry materialises a positive REVOKE → REVOKE_RECEIPT pair.
REVOKE_REASON_TRIGGER_MAP: Dict[str, Dict[str, str]] = {
    "human-initiated": {
        "trigger": "Human Prime explicitly initiates REVOKE",
        "summary_extra": (
            "Canonical symmetric-revocation path: HP issues REVOKE "
            "with the same authentication strength as BOOTSTRAP "
            "(Requirement 4.1.3)."
        ),
    },
    "expiry": {
        "trigger": "Mandate `not_after` has elapsed",
        "summary_extra": (
            "Lifecycle-driven revocation: MS detects "
            "`now > Mandate.not_after` and emits a self-issued "
            "REVOKE on behalf of the issuing HP."
        ),
    },
    "task-completed": {
        "trigger": "iFay reports task completion (DISCLOSURE → HP confirmation)",
        "summary_extra": (
            "iFay-initiated decoupling per Requirement 4.1.4-5. The "
            "iFay's report is treated as a Disclosure_Report and HP "
            "confirms via REVOKE; the iFay never revokes its own "
            "Mandate."
        ),
    },
    "human-prime-unreachable": {
        "trigger": "HP unreachable beyond `HumanReachabilityBudget`",
        "summary_extra": (
            "Auto-revocation per Requirement 9.4.4: when HP cannot "
            "be reached, MS auto-revokes related Mandates with this "
            "reason and broadcasts via RR within "
            "`RevocationVisibilityBudget`."
        ),
    },
    "ego-deviation": {
        "trigger": "MS or RP detects iFay behavior outside Ego boundary",
        "summary_extra": (
            "Auto-revocation per Requirement 9.4.5 / §9.10.4 T3: "
            "DISCLOSURE inconsistent with the actual action triggers "
            "this reason."
        ),
    },
    "fay-credential-invalid": {
        "trigger": "iFay's credential failed attestation",
        "summary_extra": (
            "Triggered when the iFay's session key, device "
            "attestation, or signature chain fails verification "
            "(see §9.5 ‘异常脱钩’)."
        ),
    },
    "human-prime-credential-invalid": {
        "trigger": "Human Prime root key compromised or rotated out",
        "summary_extra": (
            "When HP's root credential is invalidated (compromise or "
            "rotation), every Mandate it issued is auto-revoked "
            "with this reason."
        ),
    },
    "regulatory-order": {
        "trigger": "Authoritative regulatory order requires immediate revocation",
        "summary_extra": (
            "Per Requirement 4.1.4: revocation initiated by a "
            "regulator-authority path that is still made visible "
            "through HP's view channel."
        ),
    },
    "terminal-disconnected": {
        "trigger": "Bound terminal disconnected past Reconciliation timeout",
        "summary_extra": (
            "Per design.md §4.3 Disconnected → Revoked: when "
            "Reconciliation cannot complete and the Mandate is not "
            "Endorsed (or `endorsed_lifetime` lapsed), MS revokes "
            "with this reason."
        ),
    },
}


def _make_target_mandate(
    *,
    ctx: ChainContext,
    name: str,
    grade: int = 2,
) -> SignedMandate:
    """Build the Mandate that the REVOKE vector targets.

    Every positive REVOKE vector revokes a freshly-built Mandate.
    Building a real Mandate (rather than a placeholder id) lets
    verifiers cross-check the receipt against the Mandate that
    actually existed before revocation: ``mandate_id``, ``parent``
    (if any), ``not_after`` for the expiry-driven reason, and
    ``presence_req`` for the terminal-disconnected reason.
    """
    issued_at, not_before, not_after, _expiry = _common_window()
    return make_signed_mandate(
        mandate_id=f"01HXMNDT-TARGET-{_suffix(name)}",
        issuer=f"hp:01HXHP-{_suffix(name)}",
        subject=f"fay:01HXFAY-{_suffix(name)}",
        grade=grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_scope(),
        ms_kp=ctx.ms_kp,
        label=f"target-{name}",
        chain=[ctx.ms_cert_sig],
    )


def build_reason_positive_spec(reason: str) -> VectorSpec:
    """Build one positive REVOKE vector for the given ``RevokeReason``.

    Design choices:

    * The directly-revoked Mandate is freshly constructed in this
      vector so the receipt's ``mandate_id`` and the Attestation
      Chain entries can both reference it.
    * ``cascade`` is left at its default ``true`` per §5.3.5; the
      parent here has no children, so ``cascaded_mandate_ids`` is
      empty for these vectors. The dedicated ``cascade-depth-2``
      vector exercises non-empty cascade.
    * ``effective_at`` is set to a fixed ISO timestamp so the RR
      visibility budget upper bound (``effective_at +
      RevocationVisibilityBudget``) is materialised verbatim in
      ``expected.json``.
    """
    name = f"reason-{reason}"
    ctx = make_chain_ctx(name)
    target = _make_target_mandate(ctx=ctx, name=name, grade=2)

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-RVK-RCT-{_suffix(name)}"
    issuer = target.tree["issuer"]
    subject = target.tree["subject"]

    effective_at = "2026-01-01T12:00:00Z"
    rr_visible_by = _add_ms(effective_at, REVOCATION_VISIBILITY_BUDGET_MS)

    request_tree = _build_revoke_request(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason=reason,
        effective_at=effective_at,
        requesting_kp=ctx.hp_kp,   # HP signs REVOKE per Requirement 4.1
    )
    response_tree = _build_revoke_receipt(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=target.tree["id"],
        reason=reason,
        revoked_at=effective_at,
        cascade=True,
        cascaded_mandate_ids=[],   # leaf — no descendants
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=None,
        mandate_id=target.tree["id"],
        ts=effective_at,
        rp_id=f"rp:vector-{name}",
        reason=f"REVOKE accepted; reason={reason}",
        notes=(
            "Per design.md §9.6, every successful REVOKE is "
            "recorded as a five-tuple in audit-log; error_code is "
            "null because the path is the success path. "
            f"Trigger: {REVOKE_REASON_TRIGGER_MAP[reason]['trigger']}."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "revoke_reason": reason,
        "trigger": REVOKE_REASON_TRIGGER_MAP[reason]["trigger"],
        "cascade": True,
        "affected_mandate_ids": [target.tree["id"]],
        "cascaded_mandate_ids": [],
        "rr_visibility": {
            "effective_at":               time_marker(effective_at),
            "visibility_budget_ms":       REVOCATION_VISIBILITY_BUDGET_MS,
            "rr_visible_by":              time_marker(rr_visible_by),
            "broadcast_channels":         ["pull-ocsp-like", "push-websocket-sse-mqtt"],
        },
        "post_state": {
            "mandate_status": "Revoked",
            "terminal_state": True,
            "no_revoked_to_active_path": True,
            "subsequent_use_error_code": 1006,
            "subsequent_use_error_name": "E_REVOKED",
        },
        "audit_event": audit_event,
        "irreversibility_note": (
            "Per Requirement 4.3 the Mandate's status is now "
            "terminal-Revoked; any subsequent RP call referencing "
            "this mandate_id MUST fail with 1006 E_REVOKED. The "
            "only recovery path is a fresh BOOTSTRAP that issues a "
            "new Mandate with a different mandate_id."
        ),
    }

    return VectorSpec(
        name=name,
        kind="positive",
        summary=(
            f"REVOKE with reason={reason!r}: "
            f"{REVOKE_REASON_TRIGGER_MAP[reason]['summary_extra']}"
        ),
        requirements=["4.1", "4.2", "4.3", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason=reason,
        affected_mandate_ids=[target.tree["id"]],
        expected_extras=expected_extras,
        notes=(
            f"Validates that `RevokeReason = {reason!r}` produces a "
            "well-formed REVOKE → REVOKE_RECEIPT round-trip. "
            f"Trigger: {REVOKE_REASON_TRIGGER_MAP[reason]['trigger']}. "
            "Requirement 9.4 categorises this reason as a "
            "decoupling-state recognition trigger; the receipt "
            "lists exactly the directly-revoked Mandate (no children "
            "in this vector — see `cascade-depth-2` for the cascade "
            "case)."
        ),
    )


# ---------------------------------------------------------------------------
# Cascade vectors (depth-2 derivation tree)
# ---------------------------------------------------------------------------


def _build_cascade_tree(
    *,
    ctx: ChainContext,
    name: str,
) -> Tuple[SignedMandate, SignedMandate, SignedMandate]:
    """Build a depth-2 derivation tree: parent → child → grandchild.

    Each derivation hop tightens scope and either preserves or
    decreases autonomy (G3 → G2 → G1), so the tree is a
    well-formed DELEGATE chain. The cascade vectors revoke the
    *parent* and observe propagation across both descendants.

    Returns
    -------
    (parent, child, grandchild)
    """
    issued_at, not_before, not_after, _expiry = _common_window()

    parent = make_signed_mandate(
        mandate_id=f"01HXMNDT-PARENT-{_suffix(name)}",
        issuer=f"hp:01HXHP-{_suffix(name)}",
        subject=f"fay:01HXFAY-PARENT-{_suffix(name)}",
        grade=3,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_scope(),
        ms_kp=ctx.ms_kp,
        label=f"parent-{name}",
        chain=[ctx.ms_cert_sig],
    )
    child = make_signed_mandate(
        mandate_id=f"01HXMNDT-CHILD-{_suffix(name)}",
        issuer=parent.tree["issuer"],
        subject=f"fay:01HXFAY-CHILD-{_suffix(name)}",
        grade=2,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_child_scope_subset(),
        ms_kp=ctx.ms_kp,
        label=f"child-{name}",
        parent_id=parent.tree["id"],
        chain=parent.chain + [parent.outer_sig],
    )
    grandchild = make_signed_mandate(
        mandate_id=f"01HXMNDT-GRANDCHILD-{_suffix(name)}",
        issuer=parent.tree["issuer"],
        subject=f"fay:01HXFAY-GCHILD-{_suffix(name)}",
        grade=1,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_grandchild_scope_subset(),
        ms_kp=ctx.ms_kp,
        label=f"grandchild-{name}",
        parent_id=child.tree["id"],
        chain=child.chain + [child.outer_sig],
    )
    return parent, child, grandchild


def build_cascade_depth2_spec() -> VectorSpec:
    """REVOKE on a depth-2 derivation tree with cascade=true.

    Validates Requirement 7.2: a single REVOKE on the parent atomically
    marks every descendant Mandate as ``Revoked`` and forbids any
    new DELEGATE that names the parent. The receipt enumerates both
    descendants in topological order (child first, grandchild
    last).
    """
    name = "cascade-depth-2"
    ctx = make_chain_ctx(name)
    parent, child, grandchild = _build_cascade_tree(ctx=ctx, name=name)

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-RVK-RCT-{_suffix(name)}"
    issuer = parent.tree["issuer"]
    subject = parent.tree["subject"]
    effective_at = "2026-01-01T12:00:00Z"
    rr_visible_by = _add_ms(effective_at, REVOCATION_VISIBILITY_BUDGET_MS)

    cascaded = [child.tree["id"], grandchild.tree["id"]]
    affected = [parent.tree["id"], *cascaded]

    request_tree = _build_revoke_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=parent.tree["id"],
        cascade=True,
        reason="human-initiated",
        effective_at=effective_at,
        requesting_kp=ctx.hp_kp,
    )
    response_tree = _build_revoke_receipt(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=parent.tree["id"],
        reason="human-initiated",
        revoked_at=effective_at,
        cascade=True,
        cascaded_mandate_ids=cascaded,
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=None,
        mandate_id=parent.tree["id"],
        ts=effective_at,
        rp_id=f"rp:vector-{name}",
        reason="REVOKE accepted; reason=human-initiated; cascade=true",
        notes=(
            "Per Requirement 7.2.1 the cascade marks every "
            "descendant of the parent as Revoked in the same "
            "transaction; per 7.2.2 no new DELEGATE referencing the "
            "Revoked parent may succeed. Per 7.2.3 RR pushes "
            "REVOKE notifications to RPs of every cascaded child "
            "within RevocationVisibilityBudget."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "revoke_reason": "human-initiated",
        "trigger": REVOKE_REASON_TRIGGER_MAP["human-initiated"]["trigger"],
        "cascade": True,
        "tree_depth": 2,
        "tree": {
            "parent_mandate_id":     parent.tree["id"],
            "child_mandate_id":      child.tree["id"],
            "grandchild_mandate_id": grandchild.tree["id"],
        },
        "affected_mandate_ids": affected,
        "cascaded_mandate_ids": cascaded,
        "rr_visibility": {
            "effective_at":               time_marker(effective_at),
            "visibility_budget_ms":       REVOCATION_VISIBILITY_BUDGET_MS,
            "rr_visible_by":              time_marker(rr_visible_by),
            "broadcast_channels":         ["pull-ocsp-like", "push-websocket-sse-mqtt"],
            "pushed_to_descendants_rps":  True,
        },
        "post_state": {
            "parent_status":             "Revoked",
            "child_status":              "Revoked",
            "grandchild_status":         "Revoked",
            "terminal_state":            True,
            "no_revoked_to_active_path": True,
            "new_delegate_using_parent": "rejected",
            "new_delegate_error_code":   1006,
            "new_delegate_error_name":   "E_REVOKED",
        },
        "audit_event": audit_event,
        "irreversibility_note": (
            "Cascade revocation is just as irreversible as direct "
            "revocation: every descendant's status becomes "
            "terminal-Revoked. To resume operations the HP must run "
            "BOOTSTRAP again, yielding a fresh root Mandate with a "
            "new mandate_id (Requirement 4.3.3)."
        ),
    }

    return VectorSpec(
        name=name,
        kind="positive",
        summary=(
            "Cascade REVOKE on a depth-2 derivation tree (parent G3 → "
            "child G2 → grandchild G1). One REVOKE on the parent "
            "atomically marks both descendants as Revoked and the "
            "receipt enumerates them in topological order."
        ),
        requirements=["4.1", "4.2", "4.3", "7.2", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=parent.tree["id"],
        cascade=True,
        reason="human-initiated",
        affected_mandate_ids=affected,
        expected_extras=expected_extras,
        notes=(
            "Tree depth 2 satisfies the task-3.5 acceptance criterion "
            "‘cascade=true 级联派生树 + 子 Mandate 撤销结果, "
            "深度 2’. Validates Requirement 7.2.1 (atomic cascade), "
            "7.2.2 (no further DELEGATE off Revoked parent), and "
            "7.2.3 (RR push to every affected RP)."
        ),
    )


def build_cascade_disabled_spec() -> VectorSpec:
    """REVOKE on a depth-2 tree with cascade=false.

    Demonstrates the boundary case: only the directly-targeted
    Mandate becomes Revoked; descendants stay Active. This exercises
    the explicit override of the §5.3.5 default (`cascade=true`) and
    documents that ``cascade`` is wire-controlled rather than
    implementation-defined.
    """
    name = "cascade-disabled"
    ctx = make_chain_ctx(name)
    parent, child, grandchild = _build_cascade_tree(ctx=ctx, name=name)

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-RVK-RCT-{_suffix(name)}"
    issuer = parent.tree["issuer"]
    subject = parent.tree["subject"]
    effective_at = "2026-01-01T12:00:00Z"
    rr_visible_by = _add_ms(effective_at, REVOCATION_VISIBILITY_BUDGET_MS)

    request_tree = _build_revoke_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=parent.tree["id"],
        cascade=False,
        reason="task-completed",
        effective_at=effective_at,
        requesting_kp=ctx.hp_kp,
    )
    response_tree = _build_revoke_receipt(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=parent.tree["id"],
        reason="task-completed",
        revoked_at=effective_at,
        cascade=False,
        cascaded_mandate_ids=[],
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=None,
        mandate_id=parent.tree["id"],
        ts=effective_at,
        rp_id=f"rp:vector-{name}",
        reason="REVOKE accepted; reason=task-completed; cascade=false",
        notes=(
            "cascade=false is explicit on the wire; descendant "
            "Mandates retain their pre-revoke state. RR still "
            "broadcasts the parent's revocation within "
            "RevocationVisibilityBudget."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "revoke_reason": "task-completed",
        "trigger": REVOKE_REASON_TRIGGER_MAP["task-completed"]["trigger"],
        "cascade": False,
        "tree_depth": 2,
        "tree": {
            "parent_mandate_id":     parent.tree["id"],
            "child_mandate_id":      child.tree["id"],
            "grandchild_mandate_id": grandchild.tree["id"],
        },
        "affected_mandate_ids": [parent.tree["id"]],
        "cascaded_mandate_ids": [],
        "rr_visibility": {
            "effective_at":               time_marker(effective_at),
            "visibility_budget_ms":       REVOCATION_VISIBILITY_BUDGET_MS,
            "rr_visible_by":              time_marker(rr_visible_by),
            "broadcast_channels":         ["pull-ocsp-like", "push-websocket-sse-mqtt"],
            "pushed_to_descendants_rps":  False,
        },
        "post_state": {
            "parent_status":     "Revoked",
            "child_status":      "Active",
            "grandchild_status": "Active",
            "terminal_state_for_parent": True,
            "no_revoked_to_active_path": True,
            "note": (
                "cascade=false leaves descendants Active. Per "
                "Requirement 7.2.2, no NEW DELEGATE can be issued "
                "with the Revoked parent as `parent_mandate`, but "
                "existing children retain their state until they "
                "expire on their own `not_after` or are explicitly "
                "revoked."
            ),
        },
        "audit_event": audit_event,
        "irreversibility_note": (
            "Even with cascade=false, the parent's Revoked status "
            "is irreversible. A new Mandate covering the parent's "
            "scope requires a fresh BOOTSTRAP."
        ),
    }

    return VectorSpec(
        name=name,
        kind="positive",
        summary=(
            "REVOKE with cascade=false on a depth-2 tree; only the "
            "parent becomes Revoked; descendants stay Active. "
            "Validates that ``cascade`` is an explicit, wire-level "
            "boolean rather than implementation-defined behaviour."
        ),
        requirements=["4.1", "4.3", "7.2", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=parent.tree["id"],
        cascade=False,
        reason="task-completed",
        affected_mandate_ids=[parent.tree["id"]],
        expected_extras=expected_extras,
        notes=(
            "Boundary case for §5.3.5 cascade default. The vector "
            "explicitly sets cascade=false and records the "
            "expected post-state for both descendants (Active) so "
            "implementations cannot silently revoke children when "
            "the wire says otherwise."
        ),
    )



# ---------------------------------------------------------------------------
# Irreversibility documentation vectors
# ---------------------------------------------------------------------------


def build_irreversibility_double_revoke_spec() -> VectorSpec:
    """Second REVOKE on an already-Revoked Mandate is idempotent.

    Validates Requirement 4.3.1-2: ``Revoked → Revoked`` is the
    only transition allowed on a Revoked Mandate; in particular
    there is no ``Revoked → Active`` path. The MS replies with a
    REVOKE_RECEIPT confirming the prior revocation timestamp
    (``revoked_at`` reflects the *original* revocation, not the
    duplicate request) so verifiers can prove the underlying state
    has not been mutated.
    """
    name = "irreversibility-double-revoke"
    ctx = make_chain_ctx(name)
    target = _make_target_mandate(ctx=ctx, name=name, grade=2)

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-RVK-RCT-{_suffix(name)}"
    issuer = target.tree["issuer"]
    subject = target.tree["subject"]

    # The Mandate has already been Revoked at original_revoked_at;
    # the request we model is a *second* REVOKE that arrives later.
    original_revoked_at = "2026-01-01T10:00:00Z"
    duplicate_request_at = "2026-01-01T12:00:00Z"
    rr_visible_by = _add_ms(
        original_revoked_at, REVOCATION_VISIBILITY_BUDGET_MS
    )

    request_tree = _build_revoke_request(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason="human-initiated",
        effective_at=duplicate_request_at,
        requesting_kp=ctx.hp_kp,
    )
    # The receipt advertises the *original* revoked_at, not the new
    # duplicate-request timestamp — the Revoked state is immutable.
    response_tree = _build_revoke_receipt(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=target.tree["id"],
        reason="human-initiated",
        revoked_at=original_revoked_at,
        cascade=True,
        cascaded_mandate_ids=[],
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=None,
        mandate_id=target.tree["id"],
        ts=duplicate_request_at,
        rp_id=f"rp:vector-{name}",
        reason=(
            "REVOKE on already-Revoked Mandate; idempotent receipt "
            "returns the original revoked_at."
        ),
        notes=(
            "Per Requirement 4.3.1-2, Revoked is terminal. A "
            "duplicate REVOKE produces a REVOKE_RECEIPT pointing "
            "to the *prior* revoked_at; no state mutation occurs. "
            "Auditors can confirm the Mandate was already Revoked "
            "by comparing the receipt's revoked_at against the "
            "original audit-log entry."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted-idempotent",
        "revoke_reason": "human-initiated",
        "cascade": True,
        "affected_mandate_ids": [target.tree["id"]],
        "cascaded_mandate_ids": [],
        "rr_visibility": {
            "effective_at":               time_marker(original_revoked_at),
            "visibility_budget_ms":       REVOCATION_VISIBILITY_BUDGET_MS,
            "rr_visible_by":              time_marker(rr_visible_by),
            "broadcast_channels":         ["pull-ocsp-like", "push-websocket-sse-mqtt"],
            "duplicate_request_observed_at": time_marker(duplicate_request_at),
            "duplicate_request_changes_visibility": False,
        },
        "post_state": {
            "mandate_status":             "Revoked",
            "terminal_state":             True,
            "no_revoked_to_active_path":  True,
            "subsequent_use_error_code":  1006,
            "subsequent_use_error_name":  "E_REVOKED",
            "second_revoke_mutates_state": False,
        },
        "audit_event": audit_event,
        "irreversibility_assertion": {
            "requirement": "4.3.1-2",
            "claim": (
                "For all t1 < t2, Mandate.status(t1)=Revoked ⟹ "
                "Mandate.status(t2)=Revoked."
            ),
            "no_legal_path_back_to": ["Active", "Degraded", "Suspended"],
        },
    }

    return VectorSpec(
        name=name,
        kind="positive",
        summary=(
            "Double REVOKE: a second REVOKE on an already-Revoked "
            "Mandate produces an idempotent receipt that points to "
            "the *original* revoked_at. Documents Requirement 4.3.1-2: "
            "Revoked is a terminal state."
        ),
        requirements=["4.3", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason="human-initiated",
        affected_mandate_ids=[target.tree["id"]],
        expected_extras=expected_extras,
        notes=(
            "Vector documents the irreversibility invariant "
            "(Requirement 4.3.1-2 / design.md §4.3 状态机) by "
            "showing that a duplicate REVOKE does NOT advance the "
            "revoked_at timestamp and does NOT change the "
            "Mandate's status."
        ),
    )


def build_irreversibility_rebootstrap_new_id_spec() -> VectorSpec:
    """The only recovery path is a fresh BOOTSTRAP yielding a new mandate_id.

    Per Requirement 4.3.3, when HP wishes to restore authorisation
    over the same (subject, scope) after a REVOKE, the Mandate
    Service MUST issue a brand-new Mandate with a *different*
    ``mandate_id``. This vector materialises the receipt of the
    original REVOKE *and* the relationship between the original
    Mandate id (Revoked) and the new Mandate id (Active) so
    verifiers can assert that no implementation reuses the old id.
    """
    name = "irreversibility-rebootstrap-new-id"
    ctx = make_chain_ctx(name)

    issued_at, not_before, not_after, _expiry = _common_window()

    # Original Mandate — to be revoked.
    old_mandate = make_signed_mandate(
        mandate_id=f"01HXMNDT-OLD-{_suffix(name)}",
        issuer=f"hp:01HXHP-{_suffix(name)}",
        subject=f"fay:01HXFAY-{_suffix(name)}",
        grade=2,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_scope(),
        ms_kp=ctx.ms_kp,
        label=f"old-{name}",
        chain=[ctx.ms_cert_sig],
    )
    # Replacement Mandate — must have a different id even though
    # subject and scope match. We post-date its issued_at by 5
    # minutes to capture the realistic ‘re-bootstrap after revoke’
    # timeline.
    new_mandate_issued_at = "2026-01-01T12:05:00Z"
    new_mandate = make_signed_mandate(
        mandate_id=f"01HXMNDT-NEW-{_suffix(name)}",
        issuer=old_mandate.tree["issuer"],
        subject=old_mandate.tree["subject"],   # SAME subject
        grade=2,
        issued_at=new_mandate_issued_at,
        not_before=new_mandate_issued_at,
        not_after="2026-01-02T12:05:00Z",
        scope=make_scope(),                    # SAME scope
        ms_kp=ctx.ms_kp,
        label=f"new-{name}",
        chain=[ctx.ms_cert_sig],
    )
    assert old_mandate.tree["id"] != new_mandate.tree["id"], (
        "Re-bootstrap MUST produce a different mandate_id"
    )

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-RVK-RCT-{_suffix(name)}"
    issuer = old_mandate.tree["issuer"]
    subject = old_mandate.tree["subject"]
    effective_at = "2026-01-01T12:00:00Z"
    rr_visible_by = _add_ms(effective_at, REVOCATION_VISIBILITY_BUDGET_MS)

    # The vector's request/response pair is the REVOKE for the
    # OLD mandate. The new mandate's metadata sits inside
    # expected.json so verifiers can confirm id-disjointness without
    # an extra wire round.
    request_tree = _build_revoke_request(
        name=name,
        grade=old_mandate.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=old_mandate.tree["id"],
        cascade=True,
        reason="human-initiated",
        effective_at=effective_at,
        requesting_kp=ctx.hp_kp,
    )
    response_tree = _build_revoke_receipt(
        name=name,
        grade=old_mandate.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=old_mandate.tree["id"],
        reason="human-initiated",
        revoked_at=effective_at,
        cascade=True,
        cascaded_mandate_ids=[],
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=None,
        mandate_id=old_mandate.tree["id"],
        ts=effective_at,
        rp_id=f"rp:vector-{name}",
        reason="REVOKE accepted; recovery via re-BOOTSTRAP yields new mandate_id",
        notes=(
            "Per Requirement 4.3.3, recovery requires a fresh "
            "BOOTSTRAP. The new Mandate's mandate_id MUST differ "
            "from the Revoked one even when (subject, scope) match. "
            "Verifiers MUST refuse any path that reuses the old id."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "revoke_reason": "human-initiated",
        "cascade": True,
        "affected_mandate_ids": [old_mandate.tree["id"]],
        "cascaded_mandate_ids": [],
        "rr_visibility": {
            "effective_at":               time_marker(effective_at),
            "visibility_budget_ms":       REVOCATION_VISIBILITY_BUDGET_MS,
            "rr_visible_by":              time_marker(rr_visible_by),
            "broadcast_channels":         ["pull-ocsp-like", "push-websocket-sse-mqtt"],
        },
        "post_state": {
            "old_mandate_status":         "Revoked",
            "new_mandate_status":         "Active",
            "no_revoked_to_active_path":  True,
            "old_mandate_id":             old_mandate.tree["id"],
            "new_mandate_id":             new_mandate.tree["id"],
            "ids_differ":                 True,
            "subject_matches":            True,
            "scope_matches":              True,
            "recovery_path":              "re-BOOTSTRAP issuing a fresh Mandate",
        },
        "audit_event": audit_event,
        "irreversibility_assertion": {
            "requirement": "4.3.3",
            "claim": (
                "When HP needs to restore authorisation over the "
                "same (subject, scope), the MS MUST run BOOTSTRAP "
                "again and issue a Mandate with a different "
                "mandate_id. The old id stays Revoked forever."
            ),
        },
    }

    return VectorSpec(
        name=name,
        kind="positive",
        summary=(
            "Recovery after REVOKE: re-BOOTSTRAP issues a fresh "
            "Mandate with a *different* mandate_id even when "
            "(subject, scope) match. The old id remains Revoked "
            "forever. Validates Requirement 4.3.3."
        ),
        requirements=["4.1", "4.3", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=old_mandate.tree["id"],
        cascade=True,
        reason="human-initiated",
        affected_mandate_ids=[old_mandate.tree["id"]],
        expected_extras=expected_extras,
        notes=(
            "The vector's wire pair is the REVOKE for the original "
            "Mandate; the related new Mandate's metadata "
            "(post-recovery) sits inside expected.json so verifiers "
            "can assert id disjointness without a second wire "
            "round-trip. Mandate ids MUST be globally unique even "
            "across re-bootstrap of the same (subject, scope)."
        ),
    )


def build_neg_use_after_revoke_spec() -> VectorSpec:
    """Negative: any RP call presenting the Revoked Mandate fails 1006.

    Once a Mandate is Revoked, every subsequent RP call MUST be
    rejected with ``E_REVOKED`` (1006). The wire pair we emit here
    is the REVOKE → ERROR pair that an RP returns when the iFay
    submits a REVOKE on a Mandate the RP already considers
    revoked. Whilst this is technically a degenerate REVOKE, the
    important normative artefact is the **error response**: it
    proves the system surfaces 1006 with the correct mandate_id and
    pushes the event into HP's view channel (§EH.3 mandates `critical`
    bucket for E_REVOKED).
    """
    name = "neg-use-after-revoke"
    ctx = make_chain_ctx(name)
    target = _make_target_mandate(ctx=ctx, name=name, grade=2)

    msg_id_req  = f"01HXMSG-RVK-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-ERR-{_suffix(name)}"
    issuer = target.tree["issuer"]
    subject = target.tree["subject"]
    effective_at = "2026-01-01T12:30:00Z"

    request_tree = _build_revoke_request(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_req=msg_id_req,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason="human-initiated",
        effective_at=effective_at,
        requesting_kp=ctx.hp_kp,
    )
    response_tree = _build_error_response(
        name=name,
        grade=target.tree["grade"],
        issuer=issuer,
        subject=subject,
        msg_id_resp=msg_id_resp,
        target_mandate_id=target.tree["id"],
        code=1006,
        error_name="E_REVOKED",
        detail=(
            "Mandate already Revoked at an earlier timestamp; any "
            "subsequent RP-side use is rejected with 1006. ERROR "
            "responses MUST NOT leak MS internal state, private "
            "key fingerprints, or other HP identities (design.md "
            "§EH.3)."
        ),
        ms_kp=ctx.ms_kp,
    )

    audit_event = _audit_event(
        error_code=1006,
        mandate_id=target.tree["id"],
        ts=effective_at,
        rp_id=f"rp:vector-{name}",
        reason="E_REVOKED — call presented an already-Revoked Mandate",
        notes=(
            "Per design.md §EH.3, E_REVOKED is one of the four "
            "errors that MUST be pushed into HP's view channel "
            "(critical bucket). Per Requirement 9.4.1, the iFay "
            "must immediately stop D-dimension actions on receipt "
            "of REVOKE-NOTIFY."
        ),
    )

    expected_extras: Dict[str, Any] = {
        "outcome":           "rejected",
        "revoke_reason":     "human-initiated",
        "cascade":           True,
        "affected_mandate_ids": [target.tree["id"]],
        "post_state": {
            "mandate_status":             "Revoked",
            "terminal_state":             True,
            "no_revoked_to_active_path":  True,
            "rp_side_effect":             "no D-dimension action permitted",
            "if_side_effect":             "stop D-dimension immediately",
            "hp_view_channel_pushed":     True,
            "hp_view_channel_priority":   "critical",
        },
        "audit_event": audit_event,
        "error_response_constraints": {
            "no_ms_internal_state":         True,
            "no_private_key_fingerprint":   True,
            "no_other_hp_identifiers":      True,
        },
    }

    return VectorSpec(
        name=name,
        kind="negative",
        summary=(
            "Use-after-revoke: presenting a Revoked Mandate yields "
            "an ERROR response with code=1006 / name=E_REVOKED. The "
            "ERROR is pushed to HP's view channel in the critical "
            "bucket (§EH.3). Validates Requirement 9.4.1."
        ),
        requirements=["4.3", "9.4", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.hp_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        target_mandate_id=target.tree["id"],
        cascade=True,
        reason="human-initiated",
        affected_mandate_ids=[target.tree["id"]],
        expected_extras=expected_extras,
        notes=(
            "Couples Requirement 4.3 (irreversibility) with §EH.3 "
            "(audit and HP view channel routing for E_REVOKED). "
            "The error claims field carries `mandate_id` so "
            "auditors can reconstruct the five-tuple (error_code, "
            "mandate_id, ts, rp_id, reason)."
        ),
        error_code=1006,
        error_name="E_REVOKED",
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
        req_bytes  = cbor_canonical(cbor_for_json(req_full))
        resp_bytes = cbor_canonical(cbor_for_json(resp_full))
    elif encoding == "json":
        req_bytes  = json_canonical(req_full)
        resp_bytes = json_canonical(resp_full)
    else:  # pragma: no cover - defensive
        raise ValueError(encoding)

    return req_bytes, req_full, resp_bytes, resp_full, req_signing_input


def write_vector(out_root: Path, spec: VectorSpec) -> Dict[str, Any]:
    out = out_root / spec.name
    out.mkdir(parents=True, exist_ok=True)

    cbor_req, req_full, cbor_resp, resp_full, req_signing_input = (
        _render_pair(spec, encoding="cbor")
    )
    json_req, _, json_resp, _, _ = _render_pair(spec, encoding="json")

    (out / "request.cbor").write_bytes(cbor_req)
    (out / "request.json").write_bytes(json_req)
    (out / "response.cbor").write_bytes(cbor_resp)
    (out / "response.json").write_bytes(json_resp)

    expected: Dict[str, Any] = {
        "vector_name":       spec.name,
        "kind":               spec.kind,
        "target_mandate_id": spec.target_mandate_id,
        "cascade":           spec.cascade,
        "revoke_reason":     spec.reason,
        "affected_mandate_ids": spec.affected_mandate_ids,
        "summary":           spec.summary,
        "notes":             spec.notes,
        "error_code":        spec.error_code,
        "error_name":        spec.error_name,
        "encodings":         ["cbor", "json"],
        "files": {
            "request_cbor":  "request.cbor",
            "request_json":  "request.json",
            "response_cbor": "response.cbor",
            "response_json": "response.json",
        },
        "signature_verification": {
            "request_envelope":  True,
            "response_envelope": True,
            "note": (
                "REVOKE envelope is signed by HP (Requirement 4.1.3 — "
                "REVOKE auth-strength ≥ BOOTSTRAP auth-strength). "
                "REVOKE_RECEIPT / ERROR is signed by MS. Both "
                "envelopes use canonical CBOR as signing input "
                "regardless of wire encoding."
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
        "name":               spec.name,
        "kind":               spec.kind,
        "target_mandate_id":  spec.target_mandate_id,
        "cascade":            spec.cascade,
        "revoke_reason":      spec.reason,
        "affected_mandate_ids": spec.affected_mandate_ids,
        "summary":            spec.summary,
        "request_cbor":       f"{spec.name}/request.cbor",
        "request_json":       f"{spec.name}/request.json",
        "response_cbor":      f"{spec.name}/response.cbor",
        "response_json":      f"{spec.name}/response.json",
        "expected":           f"{spec.name}/expected.json",
        "request_cbor_sha256":
            expected["digests"]["request_cbor_sha256"],
        "response_cbor_sha256":
            expected["digests"]["response_cbor_sha256"],
        "error_code":         spec.error_code,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    out_root = Path(__file__).resolve().parent.parent
    out_root.mkdir(parents=True, exist_ok=True)

    specs: List[VectorSpec] = [
        # 1. Nine RevokeReason values, one positive vector each.
        build_reason_positive_spec("human-initiated"),
        build_reason_positive_spec("expiry"),
        build_reason_positive_spec("task-completed"),
        build_reason_positive_spec("human-prime-unreachable"),
        build_reason_positive_spec("ego-deviation"),
        build_reason_positive_spec("fay-credential-invalid"),
        build_reason_positive_spec("human-prime-credential-invalid"),
        build_reason_positive_spec("regulatory-order"),
        build_reason_positive_spec("terminal-disconnected"),
        # 2. Cascade behaviour on a depth-2 derivation tree.
        build_cascade_depth2_spec(),
        build_cascade_disabled_spec(),
        # 3. Revocation irreversibility (Requirement 4.3).
        build_irreversibility_double_revoke_spec(),
        build_irreversibility_rebootstrap_new_id_spec(),
        # 4. Negative — use-after-revoke surfaces 1006 E_REVOKED.
        build_neg_use_after_revoke_spec(),
    ]

    index_entries: List[Dict[str, Any]] = []
    for spec in specs:
        index_entries.append(write_vector(out_root, spec))

    # Sanity: every RevokeReason enum value is represented at least once.
    seen_reasons = {
        e["revoke_reason"] for e in index_entries
        if e["revoke_reason"] is not None
    }
    expected_reasons = set(REVOKE_REASON_TRIGGER_MAP.keys())
    missing = expected_reasons - seen_reasons
    if missing:  # pragma: no cover - defensive
        raise SystemExit(
            f"Missing RevokeReason coverage: {sorted(missing)!r}"
        )

    index = {
        "spec_version": "Faying Protocol/1.0",
        "category":     "REVOKE",
        "generated_with":
            "vectors/revoke/_tools/generate.py",
        "deterministic_seed_sha256":
            hashlib.sha256(FAYING_VECTOR_SEED).hexdigest(),
        "domain_separator": "revoke|",
        "schemas": {
            "cddl":    "schemas/fap-1.0.cddl",
            "ts_view": "schemas/types.ts",
        },
        "design_anchors": [
            "design.md §5.3.5 REVOKE wire shape (`mandate_id`, `cascade`, `reason`, `effective_at`) and REVOKE_RECEIPT post-revocation state",
            "design.md §3.4 / §9.6 Revocation Registry visibility within RevocationVisibilityBudget (default 1s)",
            "design.md §4.3 / §8.1 Mandate state machine — Revoked is a terminal state",
            "design.md §7.5 / §9.7 cascade revocation across a derivation subtree",
            "design.md §EH.1 / §EH.3 — 1006 E_REVOKED routes to audit-log + HP view channel (critical bucket)",
            "Blueprint chapter 13 — nine RevokeReason values exhaustively cover the nine decoupling triggers",
        ],
        "revoke_reason_coverage": sorted(seen_reasons),
        "revocation_visibility_budget_ms": REVOCATION_VISIBILITY_BUDGET_MS,
        "cascade_tree_depth_max": 2,
        "irreversibility_vectors": [
            "irreversibility-double-revoke",
            "irreversibility-rebootstrap-new-id",
            "neg-use-after-revoke",
        ],
        "freshness_table": {
            f"G{g}": {
                "max_staleness_ms": ms,
                "primary_signal_types": GRADE_PRIMARY_SIGNAL[g],
            }
            for g, ms in sorted(GRADE_MAX_STALENESS_MS.items())
        },
        "requirements_covered": ["4.1", "4.2", "4.3", "7.2", "9.4", "10.1", "10.3"],
        "vectors": index_entries,
    }
    (out_root / "index.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(index_entries)} REVOKE vectors to {out_root}")


if __name__ == "__main__":
    main()
