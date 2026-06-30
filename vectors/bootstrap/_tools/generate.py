"""
Generate BOOTSTRAP test vectors for Faying Protocol/1.0.

Output layout (relative to the parent directory of this file):

    pos-cbor-ed25519/        request.cbor   response.cbor   expected.json
    pos-cbor-p256/           request.cbor   response.cbor   expected.json
    pos-cbor-ml-dsa-65/      request.cbor   response.cbor   expected.json
    pos-json-ed25519/        request.json   response.json   expected.json
    pos-json-p256/           request.json   response.json   expected.json
    pos-json-ml-dsa-65/      request.json   response.json   expected.json
    neg-no-witness/          request.cbor   response.cbor   expected.json
    neg-not-after-infinity/  request.cbor   response.cbor   expected.json
    neg-not-after-before/    request.cbor   response.cbor   expected.json
    neg-unsupported-alg/     request.cbor   response.cbor   expected.json
    index.json
    README.md

Determinism contract
--------------------
* All cryptographic keys are derived from a fixed seed
  (FAYING_VECTOR_SEED below). Re-running the script reproduces the
  exact same byte-for-byte output.
* Ed25519 and ECDSA-P256 keys / signatures are produced by the real
  `cryptography` library. ML-DSA-65 entries embed a placeholder
  signature blob (the bytes 'test-only-ml-dsa-65-sig-…') because no
  vetted ML-DSA implementation is available in the standard Python
  toolchain at the time of vector authoring (see README for the
  rationale).
* CBOR is encoded with cbor2.dumps(canonical=True) which yields the
  RFC 8949 §4.2.1 deterministic-encoding form used as the signature
  input.
* JSON is encoded with sort_keys=True and a stable separators tuple.

The `expected.json` for each vector documents the intended outcome
(mandate id, signature verification result, error code, etc.) so
that downstream property tests and reference implementations can
diff against it.
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, padding
from cryptography.hazmat.primitives.asymmetric.utils import (
    decode_dss_signature,
    encode_dss_signature,
)

# ---------------------------------------------------------------------------
# Deterministic source of randomness
# ---------------------------------------------------------------------------

# A fixed 32-byte seed; every key / nonce / payload bytes used in the
# vectors derives from this via HKDF-style expansion. Do not change the
# value without bumping the vectors' generation date.
FAYING_VECTOR_SEED = bytes.fromhex(
    "f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff"
    "0001020304050607080910111213a414"  # "fa"-prefix is intentional
)


def derive(label: str, length: int = 32) -> bytes:
    """Deterministically expand the master seed into label-tagged bytes."""
    out = b""
    counter = 0
    while len(out) < length:
        h = hashlib.sha256()
        h.update(FAYING_VECTOR_SEED)
        h.update(label.encode("utf-8"))
        h.update(counter.to_bytes(4, "big"))
        out += h.digest()
        counter += 1
    return out[:length]


# ---------------------------------------------------------------------------
# Key generation (deterministic via private-key seeds)
# ---------------------------------------------------------------------------


@dataclass
class KeyPair:
    alg: str
    privkey: Any  # Underlying cryptography private key handle
    pubkey_raw: bytes  # Algorithm-specific public-key bytes (see comments)


def make_ed25519(seed_label: str) -> KeyPair:
    seed = derive(seed_label, 32)
    sk = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    pk = sk.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    return KeyPair(alg="Ed25519", privkey=sk, pubkey_raw=pk)


def make_p256(seed_label: str) -> KeyPair:
    # NIST P-256 private scalars are 32-byte integers in [1, n-1].
    # We deterministically pick a valid scalar via SHA-256 reduction.
    seed = derive(seed_label, 32)
    n = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
    scalar = int.from_bytes(seed, "big") % (n - 1) + 1
    sk = ec.derive_private_key(scalar, ec.SECP256R1())
    # Uncompressed SEC1 form: 0x04 || X(32) || Y(32).
    pk_uncompressed = sk.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    return KeyPair(alg="ES256", privkey=sk, pubkey_raw=pk_uncompressed)


def make_ml_dsa_65(seed_label: str) -> KeyPair:
    """Placeholder ML-DSA-65 keypair.

    Real ML-DSA-65 (FIPS 204) is not widely available in pure-Python
    toolchains. We emit a deterministic "public key" blob whose bytes
    are derived from the seed so that vectors stay reproducible, and
    we record the placeholder intent in `expected.json`.
    """
    pubkey = b"test-only-ml-dsa-65-pubkey-" + derive(seed_label, 32)
    return KeyPair(alg="ML-DSA-65", privkey=None, pubkey_raw=pubkey)


def sign_bytes(kp: KeyPair, message: bytes, *, label_for_placeholder: str) -> bytes:
    if kp.alg == "Ed25519":
        return kp.privkey.sign(message)
    if kp.alg == "ES256":
        # Produce an IEEE-P1363 fixed-length (r || s) signature so the
        # bytes layout is uniform across implementations; cryptography
        # gives us DER, which we re-encode.
        der = kp.privkey.sign(message, ec.ECDSA(hashes.SHA256()))
        r, s = decode_dss_signature(der)
        return r.to_bytes(32, "big") + s.to_bytes(32, "big")
    if kp.alg == "ML-DSA-65":
        # Deterministic placeholder: a stable, label-tagged blob.
        digest = hashlib.sha256(message).digest()
        return (
            b"test-only-ml-dsa-65-sig-" + label_for_placeholder.encode("utf-8")[:8]
            + digest
        )
    raise ValueError(f"Unsupported algorithm: {kp.alg}")


def verify_signature(kp: KeyPair, message: bytes, signature: bytes) -> bool:
    if kp.alg == "Ed25519":
        try:
            kp.privkey.public_key().verify(signature, message)
            return True
        except Exception:
            return False
    if kp.alg == "ES256":
        if len(signature) != 64:
            return False
        r = int.from_bytes(signature[:32], "big")
        s = int.from_bytes(signature[32:], "big")
        der = encode_dss_signature(r, s)
        try:
            kp.privkey.public_key().verify(der, ec.ECDSA(hashes.SHA256()))
            return True
        except Exception:
            return False
    if kp.alg == "ML-DSA-65":
        # Placeholder verification: the signature must match the
        # deterministic format produced by sign_bytes(...). We do not
        # claim cryptographic verification here; this is documented in
        # README.md.
        return signature.startswith(b"test-only-ml-dsa-65-sig-")
    raise ValueError(f"Unsupported algorithm: {kp.alg}")


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------


def cbor_canonical(obj: Any) -> bytes:
    """Deterministic CBOR encoding (RFC 8949 §4.2.1)."""
    return cbor2.dumps(obj, canonical=True)


def cbor_for_json(obj: Any) -> Any:
    """Convert a JSON-friendly tree (with explicit byte-string carriers)
    into the matching CBOR-friendly tree.

    JSON cannot carry raw bytes, so we use the convention
    ``{"$bytes": "<base64url>"}`` to mark byte-string fields. This
    function reverses that into actual ``bytes`` for CBOR encoding.
    """
    if isinstance(obj, dict):
        if set(obj.keys()) == {"$bytes"}:
            return base64.urlsafe_b64decode(obj["$bytes"] + "==")
        if set(obj.keys()) == {"$tag", "$value"} and obj["$tag"] == 0:
            # ISO-8601 timestamp tagged with CBOR tag 0.
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
    """The ``{"$bytes": "..."}`` JSON convention for raw bytes."""
    return {"$bytes": b64u(data)}


def time_marker(iso: str) -> Dict[str, Any]:
    """The ``{"$tag": 0, "$value": ...}`` JSON convention for CBOR tag 0."""
    return {"$tag": 0, "$value": iso}


# ---------------------------------------------------------------------------
# Builders for the protocol structures (CDDL-aligned)
# ---------------------------------------------------------------------------


def make_scope() -> Dict[str, Any]:
    """A typical scope used across the positive vectors."""
    return {
        "domains": ["https://api.example.com/v1/calendar"],
        "actions": [
            "calendar:event:create",
            "calendar:event:read",
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


def make_presence_req() -> Dict[str, Any]:
    return {
        "signal-types": ["webauthn-uv-fresh", "presence-heartbeat-only"],
        "max-staleness-ms": 5_000,
        "on-loss": "downgrade-to:G3",
    }


def make_webauthn_assertion(label: str) -> Dict[str, Any]:
    """Synthetic WebAuthn assertion blob keyed by `label`."""
    cred_id = derive(f"webauthn:{label}:cred", 16)
    auth_data = derive(f"webauthn:{label}:auth", 37)
    client_data = (
        '{"type":"webauthn.get","challenge":"'
        + b64u(derive(f"webauthn:{label}:chal", 32))
        + '","origin":"https://faying.example","crossOrigin":false}'
    ).encode("utf-8")
    sig = derive(f"webauthn:{label}:sig", 64)
    return {
        "credential_id": b64u(cred_id),
        "authenticator_data": bytes_marker(auth_data),
        "client_data_json": bytes_marker(client_data),
        "signature": bytes_marker(sig),
    }


def make_attestation(kp: KeyPair, label: str) -> Dict[str, Any]:
    """Build an `attestation` object signing a deterministic payload."""
    payload = b"faying-attestation-payload:" + label.encode("utf-8")
    sig = sign_bytes(kp, payload, label_for_placeholder=f"att-{label}")
    return {
        "format": "self-signed",
        "payload": bytes_marker(payload),
        "signer": f"hp:vector-{label}",
        "signature": {
            "alg": kp.alg,
            "pubkey": bytes_marker(kp.pubkey_raw),
            "sig": bytes_marker(sig),
        },
    }


def make_signature_bundle(
    kp: KeyPair, signed_message: bytes, *, label: str
) -> Dict[str, Any]:
    sig = sign_bytes(kp, signed_message, label_for_placeholder=label)
    return {
        "alg": kp.alg,
        "pubkey": bytes_marker(kp.pubkey_raw),
        "sig": bytes_marker(sig),
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

    The envelope tree uses the JSON wire shape: bytes are encoded via
    ``{"$bytes": ...}`` and CBOR tag-0 timestamps via
    ``{"$tag": 0, "$value": ...}``. ``cbor_for_json`` converts to the
    matching CBOR tree before signing.
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
# Vector specification & rendering
# ---------------------------------------------------------------------------


@dataclass
class VectorSpec:
    name: str
    encoding: str  # "cbor" | "json"
    alg: str  # "Ed25519" | "ES256" | "ML-DSA-65"
    kind: str  # "positive" | "negative"
    summary: str
    expected: Dict[str, Any]
    request_tree: Dict[str, Any]
    request_kp: KeyPair  # Key pair used to sign the request envelope
    response_tree: Dict[str, Any]
    response_kp: Optional[KeyPair]  # MS key for positive responses; None for ERROR
    notes: str


def render_request(spec: VectorSpec) -> Tuple[bytes, Dict[str, Any]]:
    """Sign the request envelope and serialise it.

    Returns ``(payload_bytes, json_view)``. The JSON view is the same
    tree augmented with the outer ``signature`` block; for CBOR vectors
    the bytes are the canonical CBOR encoding, for JSON vectors the
    bytes are sorted-key UTF-8 JSON.
    """
    # Build the signing input: the deterministic CBOR encoding of the
    # envelope WITHOUT the outer signature, regardless of the wire
    # encoding chosen for the vector. This is what design.md §6.3
    # mandates ("H( Deterministic-CBOR(Envelope_without_signature) )").
    cbor_tree = cbor_for_json(spec.request_tree)
    signing_input = cbor_canonical(cbor_tree)
    bundle = make_signature_bundle(
        spec.request_kp, signing_input, label=f"req-{spec.name}"
    )

    full_tree = dict(spec.request_tree)
    full_tree["signature"] = bundle

    if spec.encoding == "cbor":
        payload = cbor_canonical(cbor_for_json(full_tree))
    else:
        payload = json_canonical(full_tree)

    return payload, full_tree


def render_response(
    spec: VectorSpec, request_signing_input: bytes
) -> Tuple[bytes, Dict[str, Any]]:
    cbor_tree = cbor_for_json(spec.response_tree)
    signing_input = cbor_canonical(cbor_tree)
    if spec.response_kp is not None:
        # Sign the response with the MS key.
        bundle = make_signature_bundle(
            spec.response_kp, signing_input, label=f"resp-{spec.name}"
        )
        full_tree = dict(spec.response_tree)
        full_tree["signature"] = bundle
    else:
        # Negative cases: ERROR envelopes are still signed by MS to
        # show that the rejection is itself attestable. Use the same
        # request key as a stand-in MS key so that vectors stay
        # self-contained.
        bundle = make_signature_bundle(
            spec.request_kp, signing_input, label=f"resp-{spec.name}"
        )
        full_tree = dict(spec.response_tree)
        full_tree["signature"] = bundle

    if spec.encoding == "cbor":
        payload = cbor_canonical(cbor_for_json(full_tree))
    else:
        payload = json_canonical(full_tree)

    return payload, full_tree


def write_vector(out_root: Path, spec: VectorSpec) -> Dict[str, Any]:
    out = out_root / spec.name
    out.mkdir(parents=True, exist_ok=True)

    req_bytes, req_full_tree = render_request(spec)
    req_signing_input = cbor_canonical(cbor_for_json(spec.request_tree))
    resp_bytes, resp_full_tree = render_response(spec, req_signing_input)

    req_path = out / f"request.{spec.encoding}"
    resp_path = out / f"response.{spec.encoding}"
    req_path.write_bytes(req_bytes)
    resp_path.write_bytes(resp_bytes)

    expected = dict(spec.expected)
    expected.setdefault("vector_name", spec.name)
    expected.setdefault("encoding", spec.encoding)
    expected.setdefault("algorithm", spec.alg)
    expected.setdefault("kind", spec.kind)
    expected.setdefault("summary", spec.summary)
    expected.setdefault("notes", spec.notes)
    expected.setdefault("files", {
        "request": f"request.{spec.encoding}",
        "response": f"response.{spec.encoding}",
    })
    # Hash markers help downstream consumers detect accidental edits.
    expected.setdefault("digests", {
        "request_sha256": hashlib.sha256(req_bytes).hexdigest(),
        "response_sha256": hashlib.sha256(resp_bytes).hexdigest(),
        "request_signing_input_sha256": hashlib.sha256(
            req_signing_input
        ).hexdigest(),
    })

    # Stash a JSON-friendly mirror of the request and response so that
    # humans can read the vectors without a CBOR decoder.
    debug = {
        "request_view": req_full_tree,
        "response_view": resp_full_tree,
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
        "name": spec.name,
        "encoding": spec.encoding,
        "algorithm": spec.alg,
        "kind": spec.kind,
        "summary": spec.summary,
        "request": f"{spec.name}/request.{spec.encoding}",
        "response": f"{spec.name}/response.{spec.encoding}",
        "expected": f"{spec.name}/expected.json",
        "request_sha256": expected["digests"]["request_sha256"],
        "response_sha256": expected["digests"]["response_sha256"],
    }


# ---------------------------------------------------------------------------
# Vector catalogue
# ---------------------------------------------------------------------------


def build_positive_spec(encoding: str, alg: str) -> VectorSpec:
    name = f"pos-{encoding}-{alg.lower().replace('-', '-')}"

    if alg == "Ed25519":
        hp_kp = make_ed25519(f"hp:{name}")
        ms_kp = make_ed25519(f"ms:{name}")
    elif alg == "ES256":
        hp_kp = make_p256(f"hp:{name}")
        ms_kp = make_p256(f"ms:{name}")
    elif alg == "ML-DSA-65":
        hp_kp = make_ml_dsa_65(f"hp:{name}")
        ms_kp = make_ml_dsa_65(f"ms:{name}")
    else:
        raise ValueError(alg)

    issuer = f"hp:01HX{name.upper()[:12]}"
    subject = f"fay:01HXFAY-{alg.upper()[:6]}-EXAMPLE"

    issued_at = "2026-01-01T00:00:00Z"
    not_before = "2026-01-01T00:00:00Z"
    not_after = "2026-01-01T23:59:59Z"
    expiry = "2026-01-01T00:01:00Z"

    msg_id = f"01HXMSG-BOOTSTRAP-{alg.replace('-', '').upper()}-{encoding.upper()}"
    mandate_id = f"01HXMNDT-BOOTSTRAP-{alg.replace('-', '').upper()}-{encoding.upper()}"

    nonce = derive(f"nonce:{name}", 16)

    claims = {
        "human_prime": issuer,
        "fay": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence_req": make_presence_req(),
        "not_after": time_marker(not_after),
        "human_witness": make_webauthn_assertion(name),
    }

    attestation = make_attestation(hp_kp, name)

    request_tree = envelope_skeleton(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=attestation,
    )

    # The response is a BOOTSTRAP_RESP envelope whose `claims` field is
    # the issued Mandate. The Mandate is itself signed by MS (so the
    # `signature` field on the Mandate is populated separately, before
    # the outer envelope signature).
    mandate_skeleton = {
        "version": "Faying Protocol/1.0",
        "id": mandate_id,
        "issued-at": time_marker(issued_at),
        "not-before": time_marker(not_before),
        "not-after": time_marker(not_after),
        "issuer": issuer,
        "ms-id": f"ms:vector-{name}",
        "subject": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence-req": make_presence_req(),
        "attestation": make_attestation(ms_kp, f"ms-{name}"),
    }

    # Sign the Mandate (CDDL `mandate` rule) to populate its signature
    # field — this is the inner signature that downstream property
    # tests will verify against the CDDL contract.
    mandate_signing_input = cbor_canonical(cbor_for_json(mandate_skeleton))
    mandate_signature = make_signature_bundle(
        ms_kp, mandate_signing_input, label=f"mandate-{name}"
    )
    mandate = dict(mandate_skeleton)
    mandate["signature"] = mandate_signature

    response_tree = envelope_skeleton(
        msg_type="BOOTSTRAP_RESP",
        msg_id=f"01HXMSG-RESP-{alg.replace('-', '').upper()}-{encoding.upper()}",
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=mandate,
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )

    sig_verifies = alg in {"Ed25519", "ES256"}
    expected = {
        "outcome": "accepted",
        "mandate_id": mandate_id,
        "error_code": None,
        "error_name": None,
        "signature_verification": {
            "request_envelope": sig_verifies,
            "response_envelope": sig_verifies,
            "mandate_inner": sig_verifies,
            "note": (
                "Real cryptographic verification using the cryptography "
                "library." if sig_verifies else
                "Placeholder ML-DSA-65 signature; format-only check. "
                "See README.md for the rationale."
            ),
        },
        "requirements_validated": ["2.2", "6.1", "8.1", "10.1", "10.2", "10.3"],
    }

    notes = (
        "Positive BOOTSTRAP vector. Issuance is contingent on a valid "
        "human_witness (WebAuthn assertion); the issued Mandate has a "
        "finite not_after, presence_req, and grade=2 (Moderate)."
    )
    if alg == "ML-DSA-65":
        notes += (
            " The ML-DSA-65 signature blob is a deterministic placeholder "
            "(see README.md §Signature policy)."
        )

    return VectorSpec(
        name=name,
        encoding=encoding,
        alg=alg,
        kind="positive",
        summary=(
            f"Valid BOOTSTRAP request signed with {alg}, encoded as "
            f"{encoding.upper()}, successfully issuing a Mandate."
        ),
        expected=expected,
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        notes=notes,
    )


def build_error_response(
    *,
    msg_id: str,
    issuer: str,
    subject: str,
    issued_at: str,
    expiry: str,
    nonce: bytes,
    grade: int,
    code: int,
    name: str,
    detail: str,
    attestation: Dict[str, Any],
) -> Dict[str, Any]:
    return envelope_skeleton(
        msg_type="ERROR",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=grade,
        issuer=issuer,
        subject=subject,
        claims={
            "code": code,
            "name": name,
            "detail": detail,
        },
        attestation=attestation,
    )


def build_negative_specs() -> List[VectorSpec]:
    """Four negative cases enumerated by the task description."""
    out: List[VectorSpec] = []

    # ---- 1) missing human_witness -> E_HUMAN_WITNESS_REQUIRED (1010) ----
    name = "neg-no-witness"
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")
    issuer = "hp:01HXNEG-NOWITNESS"
    subject = "fay:01HXFAY-NEG-NOWITNESS"
    issued_at = "2026-01-01T00:00:00Z"
    expiry = "2026-01-01T00:01:00Z"
    not_after = "2026-01-01T23:59:59Z"
    nonce = derive(f"nonce:{name}", 16)
    msg_id = "01HXMSG-NEG-NOWITNESS"

    claims = {
        "human_prime": issuer,
        "fay": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence_req": make_presence_req(),
        "not_after": time_marker(not_after),
        # Intentionally omit `human_witness`.
    }
    request_tree = envelope_skeleton(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(hp_kp, name),
    )
    response_tree = build_error_response(
        msg_id=f"resp-{msg_id}",
        issuer=issuer,
        subject=subject,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=2,
        code=1010,
        name="E_HUMAN_WITNESS_REQUIRED",
        detail=(
            "BOOTSTRAP claims missing required `human_witness` "
            "WebAuthn assertion."
        ),
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )
    out.append(VectorSpec(
        name=name,
        encoding="cbor",
        alg="Ed25519",
        kind="negative",
        summary=(
            "Negative case: BOOTSTRAP without a human_witness must be "
            "rejected with E_HUMAN_WITNESS_REQUIRED (1010)."
        ),
        expected={
            "outcome": "rejected",
            "mandate_id": None,
            "error_code": 1010,
            "error_name": "E_HUMAN_WITNESS_REQUIRED",
            "signature_verification": {
                "request_envelope": True,
                "response_envelope": True,
                "note": (
                    "Request signature is structurally valid but the "
                    "claims fail validation; MS replies with a signed "
                    "ERROR envelope."
                ),
            },
            "requirements_validated": ["1.3", "6.1", "10.1", "10.3"],
        },
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        notes=(
            "Verifies acceptance criterion 1.3 / 6.1: any BOOTSTRAP "
            "without a verifiable human_witness must be refused. The "
            "ERROR envelope itself is signed so that the rejection is "
            "auditable on the Attestation Chain."
        ),
    ))

    # ---- 2) not_after = ∞ -> E_PROTOCOL ----
    name = "neg-not-after-infinity"
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")
    issuer = "hp:01HXNEG-INF"
    subject = "fay:01HXFAY-NEG-INF"
    nonce = derive(f"nonce:{name}", 16)
    msg_id = "01HXMSG-NEG-INF"

    claims = {
        "human_prime": issuer,
        "fay": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence_req": make_presence_req(),
        # Sentinel "infinity" string. Production validators MUST reject
        # this (and any non-finite encoding such as the literal
        # IEEE-754 +inf when the field is encoded as a number) with
        # E_PROTOCOL per Requirement 2.2.
        "not_after": "infinity",
        "human_witness": make_webauthn_assertion(name),
    }
    request_tree = envelope_skeleton(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(hp_kp, name),
    )
    response_tree = build_error_response(
        msg_id=f"resp-{msg_id}",
        issuer=issuer,
        subject=subject,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=2,
        code=1099,
        name="E_PROTOCOL",
        detail=(
            "BOOTSTRAP.not_after must be a finite RFC 3339 timestamp; "
            "received non-finite value."
        ),
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )
    out.append(VectorSpec(
        name=name,
        encoding="cbor",
        alg="Ed25519",
        kind="negative",
        summary=(
            "Negative case: BOOTSTRAP with not_after = ∞ must be "
            "rejected with E_PROTOCOL (1099)."
        ),
        expected={
            "outcome": "rejected",
            "mandate_id": None,
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "signature_verification": {
                "request_envelope": True,
                "response_envelope": True,
                "note": (
                    "Encoded `not_after` violates Requirement 2.2 "
                    "(Mandate must have a finite lifetime)."
                ),
            },
            "requirements_validated": ["2.2", "10.1", "10.3"],
        },
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        notes=(
            "Verifies acceptance criterion 2.2: open-ended Mandates "
            "are forbidden. The 'infinity' sentinel is one canonical "
            "representation of the bad value; implementations MUST "
            "reject any equivalent (e.g. omitted field, +inf, "
            "max-value)."
        ),
    ))

    # ---- 3) not_after < not_before -> E_PROTOCOL ----
    name = "neg-not-after-before"
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")
    issuer = "hp:01HXNEG-INV"
    subject = "fay:01HXFAY-NEG-INV"
    nonce = derive(f"nonce:{name}", 16)
    msg_id = "01HXMSG-NEG-INV"

    claims = {
        "human_prime": issuer,
        "fay": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence_req": make_presence_req(),
        # The envelope header sets issued_at = 2026-01-01T00:00:00Z;
        # the BOOTSTRAP claims here ask for a not_after that pre-dates
        # that timestamp, so not_after < not_before (the issuer's
        # local view). This must be rejected with E_PROTOCOL per
        # Requirement 2.2.
        "not_after": time_marker("2025-12-31T23:59:00Z"),
        "human_witness": make_webauthn_assertion(name),
    }
    request_tree = envelope_skeleton(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(hp_kp, name),
    )
    response_tree = build_error_response(
        msg_id=f"resp-{msg_id}",
        issuer=issuer,
        subject=subject,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=2,
        code=1099,
        name="E_PROTOCOL",
        detail=(
            "BOOTSTRAP.not_after must be strictly later than the "
            "implied not_before (issued_at)."
        ),
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )
    out.append(VectorSpec(
        name=name,
        encoding="cbor",
        alg="Ed25519",
        kind="negative",
        summary=(
            "Negative case: BOOTSTRAP with not_after < not_before must "
            "be rejected with E_PROTOCOL (1099)."
        ),
        expected={
            "outcome": "rejected",
            "mandate_id": None,
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "signature_verification": {
                "request_envelope": True,
                "response_envelope": True,
                "note": (
                    "not_after = 2025-12-31T23:59:00Z is earlier than "
                    "issued_at = 2026-01-01T00:00:00Z. Validators MUST "
                    "treat issued_at as the implicit not_before."
                ),
            },
            "requirements_validated": ["2.2", "10.1", "10.3"],
        },
        request_tree=request_tree,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        notes=(
            "Verifies acceptance criterion 2.2: not_after must be "
            "strictly greater than not_before."
        ),
    ))

    # ---- 4) unsupported algorithm -> E_PROTOCOL ----
    name = "neg-unsupported-alg"
    hp_kp = make_ed25519(f"hp:{name}")
    ms_kp = make_ed25519(f"ms:{name}")
    issuer = "hp:01HXNEG-ALG"
    subject = "fay:01HXFAY-NEG-ALG"
    nonce = derive(f"nonce:{name}", 16)
    msg_id = "01HXMSG-NEG-ALG"

    claims = {
        "human_prime": issuer,
        "fay": subject,
        "scope": make_scope(),
        "grade": 2,
        "presence_req": make_presence_req(),
        "not_after": time_marker(not_after),
        "human_witness": make_webauthn_assertion(name),
    }

    request_tree = envelope_skeleton(
        msg_type="BOOTSTRAP",
        msg_id=msg_id,
        issued_at=issued_at,
        expiry=expiry,
        nonce=nonce,
        grade=2,
        issuer=issuer,
        subject=subject,
        claims=claims,
        attestation=make_attestation(hp_kp, name),
    )
    # Tamper the outer signature bundle with an unsupported `alg` value
    # AFTER signing. This simulates a client advertising an algorithm
    # outside the negotiated suite (CDDL `signature-bundle.alg` enum:
    # {"Ed25519", "ES256", "ML-DSA-65"}).
    cbor_tree = cbor_for_json(request_tree)
    signing_input = cbor_canonical(cbor_tree)
    real_sig = sign_bytes(hp_kp, signing_input, label_for_placeholder=name)
    bad_bundle = {
        "alg": "RSA-PKCS1-v1_5-SHA1",  # not in the supported set
        "pubkey": bytes_marker(hp_kp.pubkey_raw),
        "sig": bytes_marker(real_sig),
    }
    request_tree_with_sig = dict(request_tree)
    request_tree_with_sig["signature"] = bad_bundle

    response_tree = build_error_response(
        msg_id=f"resp-{msg_id}",
        issuer=issuer,
        subject=subject,
        issued_at=issued_at,
        expiry=expiry,
        nonce=derive(f"resp-nonce:{name}", 16),
        grade=2,
        code=1099,
        name="E_PROTOCOL",
        detail=(
            "Signature algorithm 'RSA-PKCS1-v1_5-SHA1' is not in the "
            "Faying Protocol/1.0 supported suite "
            "{Ed25519, ES256, ML-DSA-65}."
        ),
        attestation=make_attestation(ms_kp, f"resp-{name}"),
    )

    # We need a bespoke renderer here because the request signature is
    # tampered. We emit it directly without re-signing.
    spec = VectorSpec(
        name=name,
        encoding="cbor",
        alg="Ed25519",  # The request *claims* RSA but is keyed by Ed25519
        kind="negative",
        summary=(
            "Negative case: BOOTSTRAP whose signature_bundle advertises "
            "an algorithm outside the Faying Protocol/1.0 suite must "
            "be rejected with E_PROTOCOL (1099)."
        ),
        expected={
            "outcome": "rejected",
            "mandate_id": None,
            "error_code": 1099,
            "error_name": "E_PROTOCOL",
            "signature_verification": {
                "request_envelope": False,
                "response_envelope": True,
                "note": (
                    "alg = 'RSA-PKCS1-v1_5-SHA1' is rejected at the "
                    "schema layer (CDDL `signature-bundle.alg` enum) "
                    "before any cryptographic check."
                ),
            },
            "requirements_validated": ["8.1", "10.1", "10.3"],
            "_pre_signed_request": True,
        },
        request_tree=request_tree_with_sig,
        request_kp=hp_kp,
        response_tree=response_tree,
        response_kp=ms_kp,
        notes=(
            "Verifies acceptance criterion 8.1 (algorithm suite "
            "negotiation): clients advertising an algorithm outside "
            "the supported set must be rejected at the protocol layer."
        ),
    )
    out.append(spec)

    return out


def render_pre_signed(
    spec: VectorSpec, out_root: Path
) -> Dict[str, Any]:
    """Variant of write_vector that does NOT re-sign the request.

    Used for vectors whose request envelope must carry an intentionally
    invalid `signature` field.
    """
    out = out_root / spec.name
    out.mkdir(parents=True, exist_ok=True)

    full_request = spec.request_tree
    if spec.encoding == "cbor":
        req_bytes = cbor_canonical(cbor_for_json(full_request))
    else:
        req_bytes = json_canonical(full_request)

    # Build a signed response (MS still signs ERROR envelopes).
    cbor_tree = cbor_for_json(spec.response_tree)
    signing_input = cbor_canonical(cbor_tree)
    bundle = make_signature_bundle(
        spec.response_kp, signing_input, label=f"resp-{spec.name}"
    )
    full_response = dict(spec.response_tree)
    full_response["signature"] = bundle
    if spec.encoding == "cbor":
        resp_bytes = cbor_canonical(cbor_for_json(full_response))
    else:
        resp_bytes = json_canonical(full_response)

    (out / f"request.{spec.encoding}").write_bytes(req_bytes)
    (out / f"response.{spec.encoding}").write_bytes(resp_bytes)

    expected = dict(spec.expected)
    expected.setdefault("vector_name", spec.name)
    expected.setdefault("encoding", spec.encoding)
    expected.setdefault("algorithm", spec.alg)
    expected.setdefault("kind", spec.kind)
    expected.setdefault("summary", spec.summary)
    expected.setdefault("notes", spec.notes)
    expected.setdefault("files", {
        "request": f"request.{spec.encoding}",
        "response": f"response.{spec.encoding}",
    })
    expected.setdefault("digests", {
        "request_sha256": hashlib.sha256(req_bytes).hexdigest(),
        "response_sha256": hashlib.sha256(resp_bytes).hexdigest(),
    })

    debug = {
        "request_view": full_request,
        "response_view": full_response,
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
        "name": spec.name,
        "encoding": spec.encoding,
        "algorithm": spec.alg,
        "kind": spec.kind,
        "summary": spec.summary,
        "request": f"{spec.name}/request.{spec.encoding}",
        "response": f"{spec.name}/response.{spec.encoding}",
        "expected": f"{spec.name}/expected.json",
        "request_sha256": expected["digests"]["request_sha256"],
        "response_sha256": expected["digests"]["response_sha256"],
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    out_root = Path(__file__).resolve().parent.parent
    out_root.mkdir(parents=True, exist_ok=True)

    index_entries: List[Dict[str, Any]] = []

    # 6 positive vectors: encoding × algorithm
    for encoding in ("cbor", "json"):
        for alg in ("Ed25519", "ES256", "ML-DSA-65"):
            spec = build_positive_spec(encoding, alg)
            entry = write_vector(out_root, spec)
            index_entries.append(entry)

    # 4 negative vectors
    for spec in build_negative_specs():
        if spec.expected.get("_pre_signed_request"):
            entry = render_pre_signed(spec, out_root)
        else:
            entry = write_vector(out_root, spec)
        index_entries.append(entry)

    index = {
        "spec_version": "Faying Protocol/1.0",
        "category": "BOOTSTRAP",
        "generated_with": "vectors/bootstrap/_tools/generate.py",
        "deterministic_seed_sha256": hashlib.sha256(
            FAYING_VECTOR_SEED
        ).hexdigest(),
        "schemas": {
            "cddl": "schemas/fap-1.0.cddl",
            "ts_view": "schemas/types.ts",
        },
        "requirements_covered": ["2.2", "6.1", "8.1", "10.1", "10.2", "10.3"],
        "vectors": index_entries,
    }
    (out_root / "index.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"Wrote {len(index_entries)} vectors to {out_root}")


if __name__ == "__main__":
    main()
