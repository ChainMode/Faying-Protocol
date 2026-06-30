"""
Generate DELEGATE test vectors for Faying Protocol/1.0.

Output layout (relative to the parent directory of this file)::

    pos-depth-1/                  request.{cbor,json}  response.{cbor,json}  expected.json
    pos-depth-2/                  request.{cbor,json}  response.{cbor,json}  expected.json
    pos-depth-3/                  request.{cbor,json}  response.{cbor,json}  expected.json
    pos-cross-device-binding/     request.{cbor,json}  response.{cbor,json}  expected.json
    pos-chain-verify/             request.{cbor,json}  response.{cbor,json}  expected.json
    neg-scope-expansion-action/   request.{cbor,json}  response.{cbor,json}  expected.json
    neg-scope-expansion-domain/   request.{cbor,json}  response.{cbor,json}  expected.json
    neg-scope-expansion-terminal/ request.{cbor,json}  response.{cbor,json}  expected.json
    neg-grade-autonomy-up/        request.{cbor,json}  response.{cbor,json}  expected.json
    index.json
    README.md  (authored separately)

These vectors exercise:

* design.md §3.3 Attestation Chain (root HP → MS-Cert → parent Mandate
  → child Mandate co-signature chain; invariants I-AC-1..3).
* design.md §5.3.4 DELEGATE wire shape — `parent_mandate`,
  `child_subject`, `child_scope`, `child_grade`, optional `device_id`.
* design.md §6.3 multi-sign chain — child `signature_bundle.chain`
  carries the parent Mandate's signature so an independent verifier
  can walk root → MS → parent → child without out-of-band trust.
* design.md §9.7 derivation convergence — `child.scope ⊆ parent.scope`,
  `child.grade.autonomy ≤ parent.grade.autonomy`, cross-device binding
  to `device_id`.
* design.md §EH.1 / §5.4 — scope-expansion / grade-autonomy-increase
  rejected with `E_PROTOCOL` (1099).

Determinism contract
--------------------
* All Ed25519 keypairs, nonces, mandate / message ids, and synthetic
  payload bytes are derived from the fixed master seed
  ``FAYING_VECTOR_SEED``. The seed is intentionally identical to the
  one used by ``vectors/bootstrap/_tools/generate.py``,
  ``vectors/presence/_tools/generate.py`` and
  ``vectors/grade-switch/_tools/generate.py`` so all batches share a
  single reproducibility anchor.
* Every key derivation goes through the per-batch domain separator
  ``b"delegate|"`` so vectors here do not collide with the BOOTSTRAP /
  PRESENCE / GRADE_SWITCH batches.
* CBOR is encoded with ``cbor2.dumps(canonical=True)`` (RFC 8949
  §4.2.1). The signing input for every signed object is the
  canonical CBOR encoding of the unsigned object, regardless of wire
  encoding. JSON vectors mirror the CBOR shape via the
  ``{"$bytes": "<base64url>"}`` and ``{"$tag": 0, "$value": ...}``
  conventions established by the BOOTSTRAP / PRESENCE / GRADE_SWITCH
  batches.

Acceptance (task 3.4)
---------------------
* Depth 1 / 2 / 3 derivation trees represented (one positive vector
  per depth, plus cross-device + chain-verify diversity samples).
* Every accepted child Mandate's ``signature.chain`` array carries
  the parent Mandate's outer signature (and at deeper depths, the
  full ancestor chain root → MS → ... → parent).
* Negative vectors that expand scope or raise autonomy are rejected
  with ``E_PROTOCOL`` (1099).
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

# 32-byte fixed seed; identical to the BOOTSTRAP / PRESENCE / GRADE_SWITCH
# batches so the four are anchored on one reproducibility seed. The
# per-batch domain separator below ensures no key / nonce collision
# between batches.
FAYING_VECTOR_SEED = bytes.fromhex(
    "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    "0001020304050607080910111213a414"
)


def derive(label: str, length: int = 32) -> bytes:
    """Deterministically expand the master seed into label-tagged bytes.

    Uses SHA-256 in counter mode under the per-batch domain separator
    ``b"delegate|"`` so callers can name keys, nonces, and synthetic
    payload bytes by stable string labels and never collide with the
    other vector batches.
    """
    out = b""
    counter = 0
    while len(out) < length:
        h = hashlib.sha256()
        h.update(FAYING_VECTOR_SEED)
        h.update(b"delegate|")  # batch domain separator
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
# (Aligned with vectors/grade-switch/_tools/generate.py.)
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
# `attestation`, `signature-bundle`) and the §5.3.4 DELEGATE claims.
# ---------------------------------------------------------------------------


def make_attestation(kp: Ed25519KeyPair, label: str) -> Dict[str, Any]:
    """Build an ``attestation`` object signing a deterministic payload.

    Mirrors the BOOTSTRAP / PRESENCE / GRADE_SWITCH generators so the
    four batches share an identical attestation shape.
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
    (root → MS → ... → parent → this signer) round-trips through both
    CBOR and JSON encodings without losing bytes.
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
    GRADE_SWITCH generators so all four batches share the same
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
# Scope helpers — used by both positive and negative DELEGATE vectors
# ---------------------------------------------------------------------------


def make_parent_scope() -> Dict[str, Any]:
    """A roomy parent scope from which child scopes may be carved."""
    return {
        "domains": [
            "https://api.example.com/v1/calendar",
            "https://api.example.com/v1/mail",
        ],
        "actions": [
            "calendar:event:create",
            "calendar:event:read",
            "calendar:event:update",
            "mail:message:read",
            "mail:message:send",
        ],
        "terminals": [
            "terminal:laptop:fixed-1",
            "terminal:phone:mobile-1",
            "terminal:phone:mobile-2",
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
    """A strict subset of ``make_parent_scope`` for legal derivation."""
    return {
        "domains": [
            "https://api.example.com/v1/calendar",
        ],
        "actions": [
            "calendar:event:read",
            "calendar:event:update",
        ],
        "terminals": [
            "terminal:phone:mobile-1",
        ],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 50,  # tighter than parent
        },
    }


def make_grandchild_scope_subset() -> Dict[str, Any]:
    """Scope strictly contained in ``make_child_scope_subset``."""
    return {
        "domains": [
            "https://api.example.com/v1/calendar",
        ],
        "actions": [
            "calendar:event:read",
        ],
        "terminals": [
            "terminal:phone:mobile-1",
        ],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 10,  # tightest
        },
    }


def make_great_grandchild_scope_subset() -> Dict[str, Any]:
    """Scope strictly contained in ``make_grandchild_scope_subset``."""
    return {
        "domains": [
            "https://api.example.com/v1/calendar",
        ],
        "actions": [
            "calendar:event:read",
        ],
        # Terminal narrowed further at depth 3.
        "terminals": [
            "terminal:phone:mobile-1",
        ],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T06:00:00Z"),
                time_marker("2026-01-01T18:00:00Z"),
            ],
            "max-invocations": 5,
        },
    }


def make_presence_req(grade: int) -> Dict[str, Any]:
    """Presence requirement consistent with §7.1 for the given grade."""
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
    """A Mandate alongside its outer signature bytes and ancestor chain.

    The ``chain`` field stores the *raw* outer-signature bytes of every
    ancestor on the path from the chain root (HP) down to the
    immediate parent. A child Mandate's ``signature_bundle.chain``
    array reproduces this list verbatim so that an independent
    verifier can walk root → MS-Cert → parent → child without any
    out-of-band trust.
    """
    tree: Dict[str, Any]            # full Mandate tree (incl. signature)
    signing_input: bytes            # canonical CBOR of the unsigned tree
    outer_sig: bytes                # this Mandate's own outer signature
    chain: List[bytes] = field(default_factory=list)
    chain_labels: List[str] = field(default_factory=list)


def make_ms_cert_signature(
    *,
    hp_kp: Ed25519KeyPair,
    ms_kp: Ed25519KeyPair,
    label: str,
) -> Tuple[bytes, Dict[str, Any]]:
    """Synthesize the HP-signed MS-Cert that anchors the AC chain.

    The MS-Cert binds the MS public key to the HP root key. We model
    the cert as a deterministic CBOR map so its canonical encoding is
    stable, then sign it with the HP key. The returned signature byte
    string is what every Mandate (and every DELEGATE response chain)
    references as the second link of the AC chain.

    Returns ``(hp_signature_over_ms_cert, ms_cert_tree)``.
    """
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
    """Build and sign a Mandate (CDDL ``mandate`` rule).

    ``chain`` carries the ancestor signatures (root HP → MS-Cert →
    ... → parent) so the child Mandate's
    ``signature.chain`` reproduces the verifier's walk path. For a
    root-derived child (depth 1) the chain has two entries:
    ``[hp_sig_over_ms_cert, parent_outer_sig]``. Each additional
    derivation depth appends one more parent signature.
    """
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
        # Build human-readable chain labels for expected.json so
        # reviewers can read off "root → MS-Cert → parent → child"
        # without decoding raw bytes.
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
# Vector specification
# ---------------------------------------------------------------------------


@dataclass
class VectorSpec:
    name: str
    kind: str               # "positive" | "negative"
    chain_depth: int        # 1 / 2 / 3 — depth of the *new* child Mandate
    summary: str
    requirements: List[str]
    request_tree: Dict[str, Any]
    request_kp: Ed25519KeyPair       # MS signs the DELEGATE envelope
    response_tree: Dict[str, Any]
    response_kp: Ed25519KeyPair      # MS signs the response envelope
    parent_id: str
    child_id: Optional[str]          # None on negative vectors
    expected_extras: Dict[str, Any]
    notes: str
    error_code: Optional[int] = None
    error_name: Optional[str] = None


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


# ---------------------------------------------------------------------------
# DELEGATE request / response builders
# ---------------------------------------------------------------------------


def _build_delegate_request(
    *,
    name: str,
    grade: int,
    issuer: str,
    child_subject: str,
    msg_id_req: str,
    parent_mandate_id: str,
    child_scope: Dict[str, Any],
    child_grade: int,
    requesting_kp: Ed25519KeyPair,
    device_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the inner claims and envelope for a DELEGATE request.

    The ``header.subject`` is the parent Mandate's subject (the
    requesting iFay) per §5.3.4 — DELEGATE is initiated by the parent
    iFay on behalf of a new child subject. ``claims.child_subject``
    declares the new FayID being granted. ``device_id`` binds the
    derivation to a specific terminal when set.
    """
    issued_at, _not_before, _not_after, expiry = _common_window()
    nonce = derive(f"req-nonce:{name}", 16)

    claims: Dict[str, Any] = {
        "parent_mandate": parent_mandate_id,
        "child_subject": child_subject,
        "child_scope": child_scope,
        "child_grade": child_grade,
    }
    if device_id is not None:
        claims["device_id"] = device_id

    # The DELEGATE envelope's `subject` is the parent FayID — the
    # initiator. The child subject lives inside `claims.child_subject`.
    parent_subject = f"fay:01HXFAY-PARENT-{_suffix(name)}"

    return envelope_skeleton(
        msg_type="DELEGATE",
        msg_id=msg_id_req,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=grade,
        issuer=issuer,
        subject=parent_subject,
        claims=claims,
        attestation=make_attestation(requesting_kp, f"req-{name}"),
    )


def _build_delegate_response(
    *,
    name: str,
    grade: int,
    issuer: str,
    child_subject: str,
    msg_id_resp: str,
    child_mandate: Dict[str, Any],
    ms_kp: Ed25519KeyPair,
) -> Dict[str, Any]:
    """Build a DELEGATE_RESP envelope carrying the child Mandate."""
    issued_at, _not_before, _not_after, expiry = _common_window()
    return envelope_skeleton(
        msg_type="DELEGATE_RESP",
        msg_id=msg_id_resp,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=grade,
        issuer=issuer,
        subject=child_subject,
        claims=child_mandate,
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


def _build_error_response(
    *,
    name: str,
    grade: int,
    issuer: str,
    parent_subject: str,
    msg_id_resp: str,
    parent_mandate_id: str,
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
        grade=grade,
        issuer=issuer,
        subject=parent_subject,
        claims={
            "code": code,
            "name": error_name,
            "detail": detail,
            "parent_mandate_id": parent_mandate_id,
        },
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )


# ---------------------------------------------------------------------------
# Chain construction primitives
# ---------------------------------------------------------------------------


@dataclass
class ChainContext:
    """Bundles the HP / MS keypairs and the HP-signed MS-Cert.

    Every vector that emits a Mandate references the same ChainContext
    so the AC chain root (HP public key) and the MS-Cert signature
    are shared across the vector — exactly what an independent
    verifier would observe in production.
    """
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


def build_parent_mandate(
    *,
    ctx: ChainContext,
    label: str,
    grade: int = 2,
) -> SignedMandate:
    """Build the parent (root-derived) Mandate.

    A root-derived Mandate's ``signature.chain`` carries exactly one
    ancestor link: the HP signature over the MS-Cert. The Mandate
    itself is signed by MS, so the verifier's walk is
    HP-pubkey → ms-cert (HP-signed) → mandate (MS-signed).
    """
    issued_at, not_before, not_after, _expiry = _common_window()
    return make_signed_mandate(
        mandate_id=f"01HXMNDT-PARENT-{_suffix(label)}",
        issuer=f"hp:01HXHP-{_suffix(label)}",
        subject=f"fay:01HXFAY-PARENT-{_suffix(label)}",
        grade=grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=make_parent_scope(),
        ms_kp=ctx.ms_kp,
        label=f"parent-{label}",
        chain=[ctx.ms_cert_sig],
    )


def build_child_mandate(
    *,
    ctx: ChainContext,
    label: str,
    parent: SignedMandate,
    child_subject: str,
    child_scope: Dict[str, Any],
    child_grade: int,
) -> SignedMandate:
    """Build a child Mandate derived from ``parent``.

    The child's ``signature.chain`` reproduces the parent's chain and
    appends the parent's outer signature, so the verifier's walk is
    HP-pubkey → ms-cert → parent → child. This is the multi-sign
    chain prescribed by design.md §6.3 for DELEGATE.
    """
    issued_at, not_before, not_after, _expiry = _common_window()
    new_chain = list(parent.chain) + [parent.outer_sig]
    return make_signed_mandate(
        mandate_id=f"01HXMNDT-CHILD-{_suffix(label)}",
        issuer=parent.tree["issuer"],
        subject=child_subject,
        grade=child_grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=child_scope,
        ms_kp=ctx.ms_kp,
        label=f"child-{label}",
        parent_id=parent.tree["id"],
        chain=new_chain,
    )


def build_grandchild_mandate(
    *,
    ctx: ChainContext,
    label: str,
    child: SignedMandate,
    subject: str,
    scope: Dict[str, Any],
    grade: int,
) -> SignedMandate:
    """Build a depth-2 Mandate derived from a depth-1 child."""
    issued_at, not_before, not_after, _expiry = _common_window()
    new_chain = list(child.chain) + [child.outer_sig]
    return make_signed_mandate(
        mandate_id=f"01HXMNDT-GRANDCHILD-{_suffix(label)}",
        issuer=child.tree["issuer"],
        subject=subject,
        grade=grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=scope,
        ms_kp=ctx.ms_kp,
        label=f"grandchild-{label}",
        parent_id=child.tree["id"],
        chain=new_chain,
    )


def build_great_grandchild_mandate(
    *,
    ctx: ChainContext,
    label: str,
    grandchild: SignedMandate,
    subject: str,
    scope: Dict[str, Any],
    grade: int,
) -> SignedMandate:
    """Build a depth-3 Mandate derived from a depth-2 grandchild."""
    issued_at, not_before, not_after, _expiry = _common_window()
    new_chain = list(grandchild.chain) + [grandchild.outer_sig]
    return make_signed_mandate(
        mandate_id=f"01HXMNDT-GGCHILD-{_suffix(label)}",
        issuer=grandchild.tree["issuer"],
        subject=subject,
        grade=grade,
        issued_at=issued_at,
        not_before=not_before,
        not_after=not_after,
        scope=scope,
        ms_kp=ctx.ms_kp,
        label=f"ggchild-{label}",
        parent_id=grandchild.tree["id"],
        chain=new_chain,
    )


# ---------------------------------------------------------------------------
# Per-vector specifications
# ---------------------------------------------------------------------------


def _post_state_for_child(child: SignedMandate, depth: int) -> Dict[str, Any]:
    return {
        "mandate_status":   "Active",
        "child_mandate_id": child.tree["id"],
        "parent_mandate_id": child.tree.get("parent"),
        "chain_depth": depth,
        "child_grade": f"G{child.tree['grade']}",
        "presence_req_max_staleness_ms":
            GRADE_MAX_STALENESS_MS[child.tree["grade"]],
        "chain_walk": ["hp-root"]
            + [f"chain[{i}]:{lbl}" for i, lbl in enumerate(child.chain_labels)]
            + ["child:outer-sig"],
    }


def build_pos_depth1_spec() -> VectorSpec:
    """Legal depth-1 derivation: parent → child.

    Verifies the canonical DELEGATE happy path:
    * `child.scope ⊆ parent.scope` (strict subset)
    * `child.grade.autonomy ≤ parent.grade.autonomy`

    NOTE on autonomy direction: design.md §7.1 numbers grades so that
    `G1=Strict` carries the smallest autonomy and `G4=Autonomous` the
    largest. The autonomy axis therefore runs *parallel* to the
    grade integer, so "child.grade.autonomy ≤ parent.grade.autonomy"
    is equivalent to **child.grade_number ≤ parent.grade_number** on
    the wire. Every positive vector in this batch picks a child
    grade with grade_number ≤ its parent's; equality is permitted
    (see `pos-chain-verify`).

    Here parent = G3 (Loose) and child = G2 (Moderate). G2 carries
    *less* autonomy than G3 (since smaller grade_number means
    stricter / less autonomous in this protocol's numbering), so
    child.grade_number ≤ parent.grade_number holds and the
    derivation is legal.
    """
    name = "pos-depth-1"
    ctx = make_chain_ctx(name)

    parent = build_parent_mandate(ctx=ctx, label=name, grade=3)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"
    child = build_child_mandate(
        ctx=ctx,
        label=name,
        parent=parent,
        child_subject=child_subject,
        child_scope=make_child_scope_subset(),
        child_grade=2,  # one step less autonomy than parent G3
    )

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]

    request_tree = _build_delegate_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=parent.tree["id"],
        child_scope=make_child_scope_subset(),
        child_grade=2,
        requesting_kp=ctx.ms_kp,
    )
    response_tree = _build_delegate_response(
        name=name,
        grade=child.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_resp=msg_id_resp,
        child_mandate=child.tree,
        ms_kp=ctx.ms_kp,
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "chain_depth": 1,
        "post_state": _post_state_for_child(child, 1),
        "convergence_assertions": {
            "child_scope_subset_of_parent": True,
            "child_grade_autonomy_le_parent": True,
            "child_actions_count": len(child.tree["scope"]["actions"]),
            "parent_actions_count": len(parent.tree["scope"]["actions"]),
        },
        "signature_chain": {
            "length": len(child.chain),
            "labels": child.chain_labels,
            "anchors_root": True,
        },
        "parent_mandate_id_in_response": parent.tree["id"],
    }

    return VectorSpec(
        name=name,
        kind="positive",
        chain_depth=1,
        summary=(
            "Depth-1 legal DELEGATE: child.scope ⊂ parent.scope and "
            "child.grade=G3 equals parent.grade=G3 (lateral derivation "
            "with equal autonomy — the ≤ in §9.7 is non-strict). The "
            "child Mandate's signature.chain carries [HP→MS-Cert, "
            "parent outer sig] so the verifier walks root → MS → "
            "parent → child."
        ),
        requirements=["7.1", "9.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=parent.tree["id"],
        child_id=child.tree["id"],
        expected_extras=expected_extras,
        notes=(
            "Canonical happy path. Verifies §5.3.4 wire shape, §3.3 "
            "AC chain construction, §6.3 multi-sign chain, §9.7 "
            "convergence rules and Requirement 7.1 acceptance items "
            "1–4 in one shot."
        ),
    )


def build_pos_depth2_spec() -> VectorSpec:
    """Depth-2 derivation: root → MS → parent → child → grandchild.

    The DELEGATE request carries the *child* Mandate as the parent of
    the new grandchild. The response Mandate's `signature.chain`
    therefore has length = 3
    (`[hp_sig_over_ms_cert, parent_outer_sig, child_outer_sig]`).

    Autonomy descends monotonically across the chain:
    parent G3 (autonomy = high) → child G2 (autonomy = medium) →
    grandchild G1 (autonomy = lowest). This validates Requirement
    7.1.2 across two derivation hops.
    """
    name = "pos-depth-2"
    ctx = make_chain_ctx(name)

    parent = build_parent_mandate(ctx=ctx, label=name, grade=3)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"
    child = build_child_mandate(
        ctx=ctx,
        label=name,
        parent=parent,
        child_subject=child_subject,
        child_scope=make_child_scope_subset(),
        child_grade=2,  # tighter than parent G3
    )

    grandchild_subject = f"fay:01HXFAY-GCHILD-{_suffix(name)}"
    grandchild = build_grandchild_mandate(
        ctx=ctx,
        label=name,
        child=child,
        subject=grandchild_subject,
        scope=make_grandchild_scope_subset(),
        grade=1,  # tightest leaf
    )

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]

    request_tree = _build_delegate_request(
        name=name,
        grade=child.tree["grade"],
        issuer=issuer,
        child_subject=grandchild_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=child.tree["id"],
        child_scope=make_grandchild_scope_subset(),
        child_grade=1,
        requesting_kp=ctx.ms_kp,
    )
    response_tree = _build_delegate_response(
        name=name,
        grade=grandchild.tree["grade"],
        issuer=issuer,
        child_subject=grandchild_subject,
        msg_id_resp=msg_id_resp,
        child_mandate=grandchild.tree,
        ms_kp=ctx.ms_kp,
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "chain_depth": 2,
        "post_state": _post_state_for_child(grandchild, 2),
        "convergence_assertions": {
            "leaf_scope_subset_of_intermediate": True,
            "intermediate_scope_subset_of_root": True,
            "leaf_grade_autonomy_le_intermediate": True,
            "intermediate_grade_autonomy_le_root": True,
        },
        "signature_chain": {
            "length": len(grandchild.chain),
            "labels": grandchild.chain_labels,
            "anchors_root": True,
        },
        "parent_mandate_id_in_response": child.tree["id"],
        "ancestor_mandate_ids": [parent.tree["id"], child.tree["id"]],
    }

    return VectorSpec(
        name=name,
        kind="positive",
        chain_depth=2,
        summary=(
            "Depth-2 legal DELEGATE: root HP → MS-Cert → parent (G3) → "
            "child (G2) → grandchild (G1). Autonomy descends "
            "monotonically (G3 → G2 → G1, each step stricter). "
            "signature.chain has length 3, walking root → MS-Cert → "
            "parent → child → grandchild."
        ),
        requirements=["7.1", "9.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=child.tree["id"],
        child_id=grandchild.tree["id"],
        expected_extras=expected_extras,
        notes=(
            "Verifies that scope and grade autonomy converge "
            "monotonically across two derivation hops, and that the "
            "AC chain accumulates one new parent signature per hop."
        ),
    )


def build_pos_depth3_spec() -> VectorSpec:
    """Depth-3 derivation: root → MS → parent → child → grandchild → great-grandchild.

    Autonomy descends across all four levels:
    G4 → G3 → G2 → G1. The leaf at G1 is the strictest, and every
    hop honors `child.grade.autonomy ≤ parent.grade.autonomy`.
    """
    name = "pos-depth-3"
    ctx = make_chain_ctx(name)

    parent = build_parent_mandate(ctx=ctx, label=name, grade=4)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"
    child = build_child_mandate(
        ctx=ctx,
        label=name,
        parent=parent,
        child_subject=child_subject,
        child_scope=make_child_scope_subset(),
        child_grade=3,
    )

    grandchild_subject = f"fay:01HXFAY-GCHILD-{_suffix(name)}"
    grandchild = build_grandchild_mandate(
        ctx=ctx,
        label=name,
        child=child,
        subject=grandchild_subject,
        scope=make_grandchild_scope_subset(),
        grade=2,
    )

    leaf_subject = f"fay:01HXFAY-GGCHILD-{_suffix(name)}"
    leaf = build_great_grandchild_mandate(
        ctx=ctx,
        label=name,
        grandchild=grandchild,
        subject=leaf_subject,
        scope=make_great_grandchild_scope_subset(),
        grade=1,
    )

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]

    request_tree = _build_delegate_request(
        name=name,
        grade=grandchild.tree["grade"],
        issuer=issuer,
        child_subject=leaf_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=grandchild.tree["id"],
        child_scope=make_great_grandchild_scope_subset(),
        child_grade=1,
        requesting_kp=ctx.ms_kp,
    )
    response_tree = _build_delegate_response(
        name=name,
        grade=leaf.tree["grade"],
        issuer=issuer,
        child_subject=leaf_subject,
        msg_id_resp=msg_id_resp,
        child_mandate=leaf.tree,
        ms_kp=ctx.ms_kp,
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "chain_depth": 3,
        "post_state": _post_state_for_child(leaf, 3),
        "convergence_assertions": {
            "scope_monotone_subset": True,
            "grade_autonomy_monotone_decreasing": True,
        },
        "signature_chain": {
            "length": len(leaf.chain),
            "labels": leaf.chain_labels,
            "anchors_root": True,
        },
        "parent_mandate_id_in_response": grandchild.tree["id"],
        "ancestor_mandate_ids": [
            parent.tree["id"],
            child.tree["id"],
            grandchild.tree["id"],
        ],
    }

    return VectorSpec(
        name=name,
        kind="positive",
        chain_depth=3,
        summary=(
            "Depth-3 legal DELEGATE: root HP → MS-Cert → parent (G4) → "
            "child (G3) → grandchild (G2) → leaf (G1). Autonomy "
            "descends monotonically across all four levels. "
            "signature.chain carries 4 ancestor sigs so the AC walk "
            "root → MS-Cert → parent → child → grandchild → leaf is "
            "fully self-contained."
        ),
        requirements=["7.1", "9.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=grandchild.tree["id"],
        child_id=leaf.tree["id"],
        expected_extras=expected_extras,
        notes=(
            "Maximum depth in this batch; demonstrates that the chain "
            "accumulates exactly one entry per hop and that scope / "
            "grade convergence is preserved at each level. P14 "
            "(cascade revocation) reuses this depth in vectors/revoke."
        ),
    )


def build_pos_cross_device_spec() -> VectorSpec:
    """Depth-1 derivation that explicitly binds the child to a new device.

    `claims.device_id` is set so the Mandate Service binds the child
    Mandate to a different terminal than the parent. This is the
    canonical cross-device DELEGATE flow described in design.md §9.7
    Mermaid figure (M_parent on IF1 device → M_child on IF2 device).
    """
    name = "pos-cross-device-binding"
    ctx = make_chain_ctx(name)

    parent = build_parent_mandate(ctx=ctx, label=name, grade=3)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"
    # Cross-device binding: explicit, narrow terminal in child scope.
    cross_device_scope = {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": [
            "calendar:event:read",
            "calendar:event:update",
        ],
        "terminals": ["terminal:phone:mobile-2"],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 30,
        },
    }
    child = build_child_mandate(
        ctx=ctx,
        label=name,
        parent=parent,
        child_subject=child_subject,
        child_scope=cross_device_scope,
        child_grade=2,  # tighter than parent G3
    )

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]

    request_tree = _build_delegate_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=parent.tree["id"],
        child_scope=cross_device_scope,
        child_grade=2,
        requesting_kp=ctx.ms_kp,
        device_id="terminal:phone:mobile-2",
    )
    response_tree = _build_delegate_response(
        name=name,
        grade=child.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_resp=msg_id_resp,
        child_mandate=child.tree,
        ms_kp=ctx.ms_kp,
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "chain_depth": 1,
        "post_state": _post_state_for_child(child, 1),
        "device_id_bound": "terminal:phone:mobile-2",
        "convergence_assertions": {
            "child_scope_subset_of_parent": True,
            "child_grade_autonomy_le_parent": True,
            "child_terminal_subset_of_parent_terminals": True,
        },
        "signature_chain": {
            "length": len(child.chain),
            "labels": child.chain_labels,
            "anchors_root": True,
        },
        "parent_mandate_id_in_response": parent.tree["id"],
    }

    return VectorSpec(
        name=name,
        kind="positive",
        chain_depth=1,
        summary=(
            "Depth-1 cross-device DELEGATE: claims.device_id binds the "
            "child Mandate to terminal:phone:mobile-2 (a member of "
            "parent.scope.terminals). Validates Requirement 9.2: each "
            "Mandate is bound to a specific iFay device and cross-device "
            "use must go through DELEGATE."
        ),
        requirements=["7.1", "9.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=parent.tree["id"],
        child_id=child.tree["id"],
        expected_extras=expected_extras,
        notes=(
            "Cross-device binding is the operational reason DELEGATE "
            "exists at all. design.md §9.3 mandates that a Mandate "
            "be bound to its issuing device's `device_id` and "
            "`device_attestation`; cross-device reuse must take the "
            "DELEGATE path so a fresh device-bound child Mandate is "
            "issued (Requirement 9.2 acceptance items 1–2)."
        ),
    )


def build_pos_chain_verify_spec() -> VectorSpec:
    """Depth-1 derivation focused on chain-walk auditability.

    Functionally identical to `pos-depth-1` but `expected.json`
    additionally records the SHA-256 of every chain entry and the
    full ancestor mandate-id list. Useful as a stand-alone fixture
    for property tests that want to assert chain-walk verification
    without re-deriving the chain.
    """
    name = "pos-chain-verify"
    ctx = make_chain_ctx(name)

    parent = build_parent_mandate(ctx=ctx, label=name, grade=2)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"
    child = build_child_mandate(
        ctx=ctx,
        label=name,
        parent=parent,
        child_subject=child_subject,
        child_scope=make_child_scope_subset(),
        child_grade=2,  # equal autonomy is allowed (≤)
    )

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]

    request_tree = _build_delegate_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=parent.tree["id"],
        child_scope=make_child_scope_subset(),
        child_grade=2,
        requesting_kp=ctx.ms_kp,
    )
    response_tree = _build_delegate_response(
        name=name,
        grade=child.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_resp=msg_id_resp,
        child_mandate=child.tree,
        ms_kp=ctx.ms_kp,
    )

    chain_digests = [
        hashlib.sha256(b).hexdigest() for b in child.chain
    ]

    expected_extras: Dict[str, Any] = {
        "outcome": "accepted",
        "chain_depth": 1,
        "post_state": _post_state_for_child(child, 1),
        "convergence_assertions": {
            "child_scope_subset_of_parent": True,
            "child_grade_autonomy_le_parent": True,
            "equal_autonomy_allowed": True,
        },
        "signature_chain": {
            "length": len(child.chain),
            "labels": child.chain_labels,
            "entry_sha256": chain_digests,
            "anchors_root": True,
            "hp_pubkey_b64u": b64u(ctx.hp_kp.pubkey_raw),
            "ms_pubkey_b64u": b64u(ctx.ms_kp.pubkey_raw),
            "ms_cert_signing_input_sha256":
                hashlib.sha256(
                    cbor_canonical(cbor_for_json(ctx.ms_cert_tree))
                ).hexdigest(),
        },
        "parent_mandate_id_in_response": parent.tree["id"],
    }

    return VectorSpec(
        name=name,
        kind="positive",
        chain_depth=1,
        summary=(
            "Depth-1 DELEGATE with full chain-walk metadata in "
            "expected.json. child.grade equals parent.grade (the "
            "autonomy ≤ parent boundary case). Useful for property "
            "tests that assert root → MS-Cert → parent → child "
            "without re-deriving keys."
        ),
        requirements=["7.1", "9.2", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=parent.tree["id"],
        child_id=child.tree["id"],
        expected_extras=expected_extras,
        notes=(
            "Boundary case for §3.3 I-AC-3: child.grade.autonomy = "
            "parent.grade.autonomy is permitted (the ≤ in §9.7 is "
            "non-strict). Verifies that an independent verifier can "
            "walk the AC using only the chain digests + HP root key."
        ),
    )


# ---------------------------------------------------------------------------
# Negative DELEGATE vectors — all reject with E_PROTOCOL (1099)
# ---------------------------------------------------------------------------


def _build_negative_spec(
    *,
    name: str,
    summary: str,
    detail: str,
    notes: str,
    expansion_kind: str,
    request_child_scope: Dict[str, Any],
    request_child_grade: int,
    convergence_failure: Dict[str, Any],
    requirement_focus: str,
) -> VectorSpec:
    """Common builder for the four negative DELEGATE vectors.

    All negative vectors share the same parent Mandate construction
    (legal, root-derived, G2) and only differ in the *requested*
    child claims. This isolates the rejected protocol invariant.
    """
    ctx = make_chain_ctx(name)
    parent = build_parent_mandate(ctx=ctx, label=name, grade=2)
    child_subject = f"fay:01HXFAY-CHILD-{_suffix(name)}"

    msg_id_req  = f"01HXMSG-DLG-REQ-{_suffix(name)}"
    msg_id_resp = f"01HXMSG-DLG-RESP-{_suffix(name)}"
    issuer = parent.tree["issuer"]
    parent_subject = parent.tree["subject"]

    request_tree = _build_delegate_request(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        child_subject=child_subject,
        msg_id_req=msg_id_req,
        parent_mandate_id=parent.tree["id"],
        child_scope=request_child_scope,
        child_grade=request_child_grade,
        requesting_kp=ctx.ms_kp,
    )
    response_tree = _build_error_response(
        name=name,
        grade=parent.tree["grade"],
        issuer=issuer,
        parent_subject=parent_subject,
        msg_id_resp=msg_id_resp,
        parent_mandate_id=parent.tree["id"],
        code=1099,
        error_name="E_PROTOCOL",
        detail=detail,
        ms_kp=ctx.ms_kp,
    )

    expected_extras: Dict[str, Any] = {
        "outcome": "rejected",
        "chain_depth": 1,
        "expansion_kind": expansion_kind,
        "convergence_failure": convergence_failure,
        "post_state": {
            "mandate_status": "Active",
            "parent_mandate_id": parent.tree["id"],
            "note": (
                "Rejection does not mutate any state; the parent "
                "Mandate remains Active. No child Mandate is issued "
                "and no signature.chain entry is produced."
            ),
        },
        "requirement_focus": requirement_focus,
    }

    return VectorSpec(
        name=name,
        kind="negative",
        chain_depth=1,
        summary=summary,
        requirements=["7.1", "10.1", "10.3"],
        request_tree=request_tree,
        request_kp=ctx.ms_kp,
        response_tree=response_tree,
        response_kp=ctx.ms_kp,
        parent_id=parent.tree["id"],
        child_id=None,
        expected_extras=expected_extras,
        notes=notes,
        error_code=1099,
        error_name="E_PROTOCOL",
    )


def build_neg_scope_expansion_action_spec() -> VectorSpec:
    """Negative: child requests a `scope.actions` entry not in parent."""
    expanded_scope = {
        "domains": [
            "https://api.example.com/v1/calendar",
        ],
        "actions": [
            "calendar:event:read",
            "calendar:event:update",
            # Below is NOT in parent.scope.actions — scope expansion.
            "calendar:event:delete",
        ],
        "terminals": ["terminal:phone:mobile-1"],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 10,
        },
    }
    return _build_negative_spec(
        name="neg-scope-expansion-action",
        summary=(
            "Negative DELEGATE: child.scope.actions includes "
            "'calendar:event:delete' which is NOT in parent.scope. "
            "Must be rejected with E_PROTOCOL (1099)."
        ),
        detail=(
            "DELEGATE child.scope.actions must be a subset of "
            "parent.scope.actions; received 'calendar:event:delete' "
            "which is not present in parent."
        ),
        notes=(
            "Verifies Requirement 7.1 acceptance items 1 & 3: "
            "child.scope ⊆ parent.scope, with rejection on any "
            "expansion. Uses scope.actions as the expansion axis."
        ),
        expansion_kind="actions",
        request_child_scope=expanded_scope,
        request_child_grade=3,
        convergence_failure={
            "axis": "scope.actions",
            "expanded_action": "calendar:event:delete",
            "parent_actions": [
                "calendar:event:create",
                "calendar:event:read",
                "calendar:event:update",
                "mail:message:read",
                "mail:message:send",
            ],
        },
        requirement_focus=(
            "Requirement 7.1 — child.scope ⊆ parent.scope (actions axis)."
        ),
    )


def build_neg_scope_expansion_domain_spec() -> VectorSpec:
    """Negative: child requests a `scope.domains` entry not in parent."""
    expanded_scope = {
        "domains": [
            "https://api.example.com/v1/calendar",
            # Below is NOT in parent.scope.domains — scope expansion.
            "https://api.example.com/v1/files",
        ],
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
    return _build_negative_spec(
        name="neg-scope-expansion-domain",
        summary=(
            "Negative DELEGATE: child.scope.domains adds "
            "'https://api.example.com/v1/files' which is NOT in "
            "parent.scope.domains. Must be rejected with "
            "E_PROTOCOL (1099)."
        ),
        detail=(
            "DELEGATE child.scope.domains must be a subset of "
            "parent.scope.domains; received "
            "'https://api.example.com/v1/files' which is not present "
            "in parent."
        ),
        notes=(
            "Verifies Requirement 7.1 along the scope.domains axis. "
            "A common misimplementation lets implementers reuse a "
            "delegated Mandate to reach domains the parent cannot; "
            "this vector explicitly rejects that path."
        ),
        expansion_kind="domains",
        request_child_scope=expanded_scope,
        request_child_grade=3,
        convergence_failure={
            "axis": "scope.domains",
            "expanded_domain": "https://api.example.com/v1/files",
            "parent_domains": [
                "https://api.example.com/v1/calendar",
                "https://api.example.com/v1/mail",
            ],
        },
        requirement_focus=(
            "Requirement 7.1 — child.scope ⊆ parent.scope (domains axis)."
        ),
    )


def build_neg_scope_expansion_terminal_spec() -> VectorSpec:
    """Negative: child binds to a terminal not in parent.scope.terminals."""
    expanded_scope = {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": ["calendar:event:read"],
        "terminals": [
            # Below is NOT in parent.scope.terminals — scope expansion.
            "terminal:tablet:roaming-1",
        ],
        "budget": {
            "time-window": [
                time_marker("2026-01-01T00:00:00Z"),
                time_marker("2026-01-02T00:00:00Z"),
            ],
            "max-invocations": 10,
        },
    }
    return _build_negative_spec(
        name="neg-scope-expansion-terminal",
        summary=(
            "Negative DELEGATE: child.scope.terminals targets "
            "'terminal:tablet:roaming-1' which is NOT in "
            "parent.scope.terminals. Must be rejected with "
            "E_PROTOCOL (1099)."
        ),
        detail=(
            "DELEGATE child.scope.terminals must be a subset of "
            "parent.scope.terminals; received "
            "'terminal:tablet:roaming-1' which is not present in "
            "parent. Cross-device DELEGATE is allowed but only to "
            "terminals already enumerated in the parent's scope."
        ),
        notes=(
            "Verifies Requirement 7.1 along the scope.terminals "
            "axis. Distinct from `pos-cross-device-binding` (which "
            "stays inside parent.scope.terminals); this vector "
            "documents the boundary between legal cross-device "
            "DELEGATE and illegal terminal expansion."
        ),
        expansion_kind="terminals",
        request_child_scope=expanded_scope,
        request_child_grade=3,
        convergence_failure={
            "axis": "scope.terminals",
            "expanded_terminal": "terminal:tablet:roaming-1",
            "parent_terminals": [
                "terminal:laptop:fixed-1",
                "terminal:phone:mobile-1",
                "terminal:phone:mobile-2",
            ],
        },
        requirement_focus=(
            "Requirement 7.1 — child.scope ⊆ parent.scope "
            "(terminals axis)."
        ),
    )


def build_neg_grade_autonomy_up_spec() -> VectorSpec:
    """Negative: child.grade has greater autonomy than parent.

    Per design.md §7.1, smaller grade number = stricter / less
    autonomous (G1=Strict has the lowest autonomy; G4=Autonomous the
    highest). The autonomy axis runs *parallel* to the grade
    integer, so `child.grade.autonomy ≤ parent.grade.autonomy` is
    equivalent to `child.grade_number ≤ parent.grade_number` on the
    wire. Here parent = G2 (Moderate) and child requests G4
    (Autonomous), an autonomy escalation that must be rejected.
    """
    legal_scope = make_child_scope_subset()
    return _build_negative_spec(
        name="neg-grade-autonomy-up",
        summary=(
            "Negative DELEGATE: parent.grade=G2 but request asks for "
            "child.grade=G4 (more autonomy than parent). Must be "
            "rejected with E_PROTOCOL (1099)."
        ),
        detail=(
            "DELEGATE child.grade.autonomy must be ≤ "
            "parent.grade.autonomy. Per design.md §7.1, G2 (Moderate) "
            "carries lower autonomy than G4 (Autonomous); a request "
            "to derive a G4 child from a G2 parent escalates "
            "autonomy and is rejected."
        ),
        notes=(
            "Verifies Requirement 7.1 acceptance items 2 & 3. "
            "design.md §7.1 places G1=Strict (lowest autonomy) at "
            "one end and G4=Autonomous (highest autonomy) at the "
            "other, with the autonomy axis parallel to the grade "
            "integer. The convergence rule child.grade.autonomy ≤ "
            "parent.grade.autonomy translates to child.grade_number "
            "≤ parent.grade_number on the wire. This vector picks "
            "parent=G2 and child=G4 to make the violation obvious."
        ),
        expansion_kind="grade-autonomy",
        request_child_scope=legal_scope,
        request_child_grade=4,  # higher autonomy than parent G2
        convergence_failure={
            "axis": "grade.autonomy",
            "parent_grade_number": 2,
            "parent_grade_label": "G2 (Moderate)",
            "requested_child_grade_number": 4,
            "requested_child_grade_label": "G4 (Autonomous — higher autonomy than G2)",
            "explanation": (
                "Smaller grade_number means lower autonomy. "
                "child.grade.autonomy ≤ parent.grade.autonomy "
                "requires child.grade_number ≤ parent.grade_number "
                "(2); the request violates this with grade_number=4."
            ),
        },
        requirement_focus=(
            "Requirement 7.1 — child.grade.autonomy ≤ "
            "parent.grade.autonomy (G2 → G4 raises autonomy)."
        ),
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
    # --- Request: MS signs canonical CBOR of unsigned envelope ---
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
        "kind":          spec.kind,
        "chain_depth":   spec.chain_depth,
        "parent_mandate_id": spec.parent_id,
        "child_mandate_id": spec.child_id,
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
            "child_mandate_inner": (spec.error_code is None),
            "note": (
                "Real Ed25519 signatures over canonical CBOR. The "
                "child Mandate's signature.chain reproduces the "
                "ancestor outer signatures so verifiers can walk "
                "root → MS-Cert → ... → parent → child without "
                "out-of-band trust."
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
        "name":          spec.name,
        "kind":          spec.kind,
        "chain_depth":   spec.chain_depth,
        "parent_mandate_id": spec.parent_id,
        "child_mandate_id":  spec.child_id,
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

    specs: List[VectorSpec] = [
        # Positive — depths 1, 2, 3 (each carries a full ancestor
        # signature chain in `child.signature.chain`).
        build_pos_depth1_spec(),
        build_pos_depth2_spec(),
        build_pos_depth3_spec(),
        # Positive — cross-device device_id binding & explicit
        # chain-walk metadata for property tests.
        build_pos_cross_device_spec(),
        build_pos_chain_verify_spec(),
        # Negative — every scope-expansion or grade-autonomy-up
        # case is rejected with E_PROTOCOL (1099).
        build_neg_scope_expansion_action_spec(),
        build_neg_scope_expansion_domain_spec(),
        build_neg_scope_expansion_terminal_spec(),
        build_neg_grade_autonomy_up_spec(),
    ]

    index_entries: List[Dict[str, Any]] = []
    for spec in specs:
        index_entries.append(write_vector(out_root, spec))

    index = {
        "spec_version": "Faying Protocol/1.0",
        "category": "DELEGATE",
        "generated_with":
            "vectors/delegate/_tools/generate.py",
        "deterministic_seed_sha256":
            hashlib.sha256(FAYING_VECTOR_SEED).hexdigest(),
        "domain_separator": "delegate|",
        "schemas": {
            "cddl":    "schemas/fap-1.0.cddl",
            "ts_view": "schemas/types.ts",
        },
        "design_anchors": [
            "design.md §3.3 Attestation Chain (root → MS-Cert → parent → child)",
            "design.md §5.3.4 DELEGATE wire shape",
            "design.md §6.3 multi-sign chain (signature_bundle.chain)",
            "design.md §9.7 派生 scope/grade 收敛",
            "design.md §EH.1 错误码表 (1099 E_PROTOCOL)",
        ],
        "depth_coverage": [1, 2, 3],
        "freshness_table": {
            f"G{g}": {
                "max_staleness_ms": ms,
                "primary_signal_types": GRADE_PRIMARY_SIGNAL[g],
            }
            for g, ms in sorted(GRADE_MAX_STALENESS_MS.items())
        },
        "convergence_axes_negative_coverage": [
            "scope.actions",
            "scope.domains",
            "scope.terminals",
            "grade.autonomy",
        ],
        "requirements_covered": ["7.1", "9.2", "10.1", "10.3"],
        "vectors": index_entries,
    }
    (out_root / "index.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"Wrote {len(index_entries)} DELEGATE vectors to {out_root}")


if __name__ == "__main__":
    main()
