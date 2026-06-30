#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faying Protocol/1.0 — CBOR ↔ JSON Encoding Equivalence Vectors
================================================================

This script regenerates `vectors/encoding-equivalence/{01..05}-*/` from a
fixed seed so that the output is byte-for-byte reproducible.

Per design.md §5.1 / §6.3:
- CBOR (RFC 8949) is the primary wire format.
- JSON (RFC 8259) is an interop fallback (Content-Type:
  `application/faying-protocol+json`).
- Signature input is `H( Deterministic-CBOR( Envelope_without_signature ) )`
  where Deterministic-CBOR follows RFC 8949 §4.2.1 (length-first key sort,
  shortest integer encoding, no indefinite-length items, etc.).
- `cbor2.dumps(obj, canonical=True)` implements that deterministic encoding.

Bytes carried in JSON are encoded as base64url (no padding) per the
convention recorded in this directory's README. The equivalence assertion
compares the CBOR-decoded dict against the JSON-decoded dict after applying
the binary-field reverse mapping.

Run:
    python3 vectors/encoding-equivalence/generate.py

Validates:
- Requirement 10.1 (CBOR / JSON equivalent under wire semantics)
- Requirement 10.2 (Deterministic CBOR signature input)
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import cbor2
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# ---------------------------------------------------------------------------
# Constants & deterministic key material
# ---------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parent
VECTOR_VERSION = "Faying Protocol/1.0"

# Deterministic seed → reproducible Ed25519 keypair (32-byte seed).
ED25519_SEED_HEX = (
    "00112233445566778899aabbccddeeff" "ffeeddccbbaa99887766554433221100"
)
ED25519_SEED = bytes.fromhex(ED25519_SEED_HEX)

PRIV = Ed25519PrivateKey.from_private_bytes(ED25519_SEED)
PUB: Ed25519PublicKey = PRIV.public_key()
PUBKEY_RAW: bytes = PUB.public_bytes(
    encoding=serialization.Encoding.Raw,
    format=serialization.PublicFormat.Raw,
)

# Helpers ----------------------------------------------------------------------


def b64u(data: bytes) -> str:
    """Base64url encode without padding (RFC 4648 §5)."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def b64u_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


# Set of dotted JSON paths that carry CBOR `bstr` (binary) values. The path
# uses '.' for object keys and '[]' for array elements, matching how we walk
# the structure below. This is the *minimal* set actually present in our
# vectors; the README documents the convention.
BINARY_FIELDS_BY_TYPE: dict[str, set[tuple[str, ...]]] = {
    # Common envelope fields
    "_envelope_common": {
        ("header", "nonce"),
        ("attestation", "payload"),
        ("attestation", "signature", "pubkey"),
        ("attestation", "signature", "sig"),
        ("signature", "pubkey"),
        ("signature", "sig"),
    },
    # Per-message extras (unioned with common)
    "BOOTSTRAP": {
        ("claims", "human-witness", "credential-id"),
        ("claims", "human-witness", "authenticator-data"),
        ("claims", "human-witness", "client-data-json"),
        ("claims", "human-witness", "signature"),
    },
    "PRESENCE": {
        ("claims", "signal", "nonce"),
        ("claims", "signal", "device-attestation", "payload"),
        ("claims", "signal", "device-attestation", "signature", "pubkey"),
        ("claims", "signal", "device-attestation", "signature", "sig"),
        ("claims", "signal", "signature", "pubkey"),
        ("claims", "signal", "signature", "sig"),
    },
    "GRADE_SWITCH": {
        ("claims", "human-witness", "credential-id"),
        ("claims", "human-witness", "authenticator-data"),
        ("claims", "human-witness", "client-data-json"),
        ("claims", "human-witness", "signature"),
    },
    "DELEGATE": set(),
    "REVOKE": set(),
}


def binary_paths_for(msg_type: str) -> set[tuple[str, ...]]:
    return BINARY_FIELDS_BY_TYPE["_envelope_common"] | BINARY_FIELDS_BY_TYPE[msg_type]


# ---------------------------------------------------------------------------
# JSON ↔ CBOR-shape helpers
# ---------------------------------------------------------------------------


def to_json_shape(obj: Any, path: tuple[str, ...], binary_paths: set[tuple[str, ...]]) -> Any:
    """Recursively convert a CBOR-shape dict (bytes for bstr) to JSON-shape
    (base64url strings for known binary paths)."""
    if isinstance(obj, dict):
        return {k: to_json_shape(v, path + (k,), binary_paths) for k, v in obj.items()}
    if isinstance(obj, list):
        return [to_json_shape(v, path, binary_paths) for v in obj]
    if isinstance(obj, bytes):
        if path in binary_paths:
            return b64u(obj)
        # Unexpected binary at unmapped path — surface loudly.
        raise ValueError(f"Unmapped binary field at path {path!r}")
    return obj


def from_json_shape(obj: Any, path: tuple[str, ...], binary_paths: set[tuple[str, ...]]) -> Any:
    if isinstance(obj, dict):
        return {k: from_json_shape(v, path + (k,), binary_paths) for k, v in obj.items()}
    if isinstance(obj, list):
        return [from_json_shape(v, path, binary_paths) for v in obj]
    if path in binary_paths and isinstance(obj, str):
        return b64u_decode(obj)
    return obj


# ---------------------------------------------------------------------------
# Envelope construction
# ---------------------------------------------------------------------------

# Common attestation block reused by every envelope. The bytes are
# placeholders — these vectors test wire-format equivalence, not the inner
# attestation semantics (those are exercised by other vector sets).
COMMON_ATTESTATION = {
    "format": "self-signed",
    "payload": b"attestation-payload-placeholder-v1",
    "signer": "ms:demo-mandate-service",
    "signature": {
        "alg": "Ed25519",
        "pubkey": PUBKEY_RAW,
        "sig": b"\x00" * 64,  # placeholder; not verified for equivalence test
    },
}


def make_header(msg_type: str, msg_id: str, nonce: bytes, issuer: str, subject: str) -> dict[str, Any]:
    return {
        "version": VECTOR_VERSION,
        "msg-type": msg_type,
        "msg-id": msg_id,
        "issued-at": "2025-11-25T10:00:00Z",
        "expiry": "2025-11-25T10:01:00Z",
        "nonce": nonce,
        "grade": 2,  # G2 Moderate as illustrative session grade
        "issuer": issuer,
        "subject": subject,
    }


# ---------------------------------------------------------------------------
# Per-message claim builders
# ---------------------------------------------------------------------------


def claims_bootstrap() -> dict[str, Any]:
    return {
        "human-prime": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "fay": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "scope": {
            "domains": ["agent://mailbox/inbox"],
            "actions": ["read:user-profile"],
        },
        "grade": 2,
        "presence-req": {
            "signal-types": ["webauthn-uv-fresh"],
            "max-staleness-ms": 60_000,
            "on-loss": "downgrade-to:G3",
        },
        "not-after": "2025-11-26T10:00:00Z",
        "human-witness": {
            "credential-id": b"webauthn-credential-id-bytes-32b",
            "authenticator-data": b"\x01" * 37,  # rpIdHash(32)+flags(1)+counter(4)
            "client-data-json": b'{"type":"webauthn.get","challenge":"AA","origin":"https://example.org"}',
            "signature": b"\x02" * 64,
        },
    }


def claims_presence() -> dict[str, Any]:
    return {
        "mandate-id": "mdt:01HX8K3F2Q7JX9V5N6T4R8M3PD",
        "signal": {
            "mandate-id": "mdt:01HX8K3F2Q7JX9V5N6T4R8M3PD",
            "signal-type": "webauthn-uv-fresh",
            "produced-at": "2025-11-25T09:59:55Z",
            "nonce": bytes.fromhex("a1b2c3d4e5f60718293a4b5c6d7e8f90"),
            "device-id": "pd:01HX8K3F2Q7JX9V5N6T4R8M4QE",
            "device-attestation": {
                "format": "platform-keystore",
                "payload": b"presence-device-attestation-blob",
                "signer": "pd:01HX8K3F2Q7JX9V5N6T4R8M4QE",
                "signature": {
                    "alg": "Ed25519",
                    "pubkey": PUBKEY_RAW,
                    "sig": b"\x03" * 64,
                },
            },
            "signature": {
                "alg": "Ed25519",
                "pubkey": PUBKEY_RAW,
                "sig": b"\x04" * 64,
            },
        },
        "device-health": {
            "secure-element": True,
            "tampered": False,
            "last-boot-at": "2025-11-25T08:00:00Z",
        },
    }


def claims_grade_switch() -> dict[str, Any]:
    return {
        "mandate-id": "mdt:01HX8K3F2Q7JX9V5N6T4R8M3PD",
        "target-grade": 1,  # upgrade direction (G2 → G1) → human-witness REQUIRED
        "reason": "human-initiated",
        "human-witness": {
            "credential-id": b"webauthn-credential-id-bytes-32b",
            "authenticator-data": b"\x05" * 37,
            "client-data-json": b'{"type":"webauthn.get","challenge":"BB","origin":"https://example.org"}',
            "signature": b"\x06" * 64,
        },
    }


def claims_delegate() -> dict[str, Any]:
    return {
        "parent-mandate": "mdt:01HX8K3F2Q7JX9V5N6T4R8M3PD",
        "child-subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M5RF",
        "child-scope": {
            "domains": ["agent://mailbox/inbox"],
            "actions": ["read:user-profile"],
        },
        "child-grade": 2,  # ≥ parent.grade (1), satisfies child.autonomy ≤ parent.autonomy
        "device-id": "term:macbook-2025",
    }


def claims_revoke() -> dict[str, Any]:
    return {
        "mandate-id": "mdt:01HX8K3F2Q7JX9V5N6T4R8M3PD",
        "cascade": True,
        "reason": "human-initiated",
        "effective-at": "2025-11-25T10:00:30Z",
    }


# ---------------------------------------------------------------------------
# Build, sign, encode, write
# ---------------------------------------------------------------------------

MESSAGES = [
    {
        "dir": "01-bootstrap",
        "msg-type": "BOOTSTRAP",
        "msg-id": "msg:01HX8K3F2Q7JX9V5N6T4R8MA001",
        "nonce-hex": "00010203040506070809101112131415",
        "issuer": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "claims": claims_bootstrap,
        "summary": "Human Prime issues a fresh G2 Mandate to an iFay (single-action read scope, WebAuthn UV witness).",
    },
    {
        "dir": "02-presence",
        "msg-type": "PRESENCE",
        "msg-id": "msg:01HX8K3F2Q7JX9V5N6T4R8MB002",
        "nonce-hex": "10111213141516171819202122232425",
        "issuer": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "claims": claims_presence,
        "summary": "iFay heartbeats a fresh webauthn-uv-fresh presence signal to refresh PresenceState.last_freshness.",
    },
    {
        "dir": "03-grade-switch",
        "msg-type": "GRADE_SWITCH",
        "msg-id": "msg:01HX8K3F2Q7JX9V5N6T4R8MC003",
        "nonce-hex": "20212223242526272829303132333435",
        "issuer": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "claims": claims_grade_switch,
        "summary": "Human Prime upgrades an active Mandate from G2 → G1 (autonomy strengthens), carrying a WebAuthn human_witness.",
    },
    {
        "dir": "04-delegate",
        "msg-type": "DELEGATE",
        "msg-id": "msg:01HX8K3F2Q7JX9V5N6T4R8MD004",
        "nonce-hex": "30313233343536373839404142434445",
        "issuer": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "claims": claims_delegate,
        "summary": "Parent iFay derives a child Mandate to a new terminal — child.scope ⊆ parent.scope, child.grade ≥ parent.grade.",
    },
    {
        "dir": "05-revoke",
        "msg-type": "REVOKE",
        "msg-id": "msg:01HX8K3F2Q7JX9V5N6T4R8ME005",
        "nonce-hex": "40414243444546474849505152535455",
        "issuer": "hp:01HX8K3F2Q7JX9V5N6T4R8M1ZA",
        "subject": "fay:01HX8K3F2Q7JX9V5N6T4R8M2WC",
        "claims": claims_revoke,
        "summary": "Human Prime revokes a Mandate with cascade=true, reason=human-initiated.",
    },
]


def build_envelope(msg: dict[str, Any]) -> dict[str, Any]:
    nonce = bytes.fromhex(msg["nonce-hex"])
    return {
        "header": make_header(
            msg["msg-type"], msg["msg-id"], nonce, msg["issuer"], msg["subject"]
        ),
        "claims": msg["claims"](),
        "attestation": COMMON_ATTESTATION,
        # signature is filled in after we sign Det-CBOR(envelope_without_signature)
    }


def sign_envelope(envelope_no_sig: dict[str, Any]) -> tuple[bytes, bytes, bytes]:
    """Return (det_cbor_bytes, sha256_hash, ed25519_signature)."""
    det_cbor = cbor2.dumps(envelope_no_sig, canonical=True)
    digest = hashlib.sha256(det_cbor).digest()
    sig = PRIV.sign(det_cbor)
    return det_cbor, digest, sig


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content + ("\n" if not content.endswith("\n") else ""), encoding="utf-8")


def write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def main() -> None:
    index_entries: list[dict[str, Any]] = []

    for msg in MESSAGES:
        out_dir = ROOT / msg["dir"]
        msg_type = msg["msg-type"]
        binary_paths = binary_paths_for(msg_type)

        envelope = build_envelope(msg)

        # 1) Det-CBOR signature input + signature
        det_cbor_input, sig_hash, sig_bytes = sign_envelope(envelope)

        # 2) Attach signature bundle to envelope
        envelope["signature"] = {
            "alg": "Ed25519",
            "pubkey": PUBKEY_RAW,
            "sig": sig_bytes,
        }

        # 3) Encode full signed envelope to canonical CBOR
        cbor_bytes = cbor2.dumps(envelope, canonical=True)

        # 4) Encode full signed envelope to JSON shape
        json_shape = to_json_shape(envelope, (), binary_paths)
        json_text = json.dumps(json_shape, indent=2, sort_keys=True, ensure_ascii=False)

        # 5) Equivalence sanity check (same logical object after binary mapping)
        cbor_decoded = cbor2.loads(cbor_bytes)
        json_reconstructed = from_json_shape(json.loads(json_text), (), binary_paths)
        assert cbor_decoded == json_reconstructed, (
            f"CBOR/JSON semantic mismatch for {msg_type}"
        )

        # 6) Re-derive signature input from BOTH encodings; they must match
        #    bit-for-bit because both routes go through Det-CBOR.
        cbor_no_sig = {k: v for k, v in cbor_decoded.items() if k != "signature"}
        json_no_sig = {k: v for k, v in json_reconstructed.items() if k != "signature"}
        sig_in_from_cbor = cbor2.dumps(cbor_no_sig, canonical=True)
        sig_in_from_json = cbor2.dumps(json_no_sig, canonical=True)
        assert sig_in_from_cbor == sig_in_from_json == det_cbor_input, (
            f"Signature input mismatch across encodings for {msg_type}"
        )
        assert hashlib.sha256(sig_in_from_cbor).digest() == sig_hash
        assert hashlib.sha256(sig_in_from_json).digest() == sig_hash

        # 7) Verify ed25519 signature against the shared signature input.
        #    Both encodings must verify identically.
        PUB.verify(sig_bytes, det_cbor_input)  # raises on failure

        # 8) Write artefacts
        write_bytes(out_dir / "message.cbor", cbor_bytes)
        write_text(out_dir / "message.cbor.hex", cbor_bytes.hex())
        write_text(out_dir / "message.json", json_text)
        write_text(out_dir / "signature.input.det-cbor.hex", det_cbor_input.hex())
        write_text(out_dir / "signature.input.hash.hex", sig_hash.hex())

        expected = {
            "msg_type": msg_type,
            "msg_id": msg["msg-id"],
            "summary": msg["summary"],
            "binary_field_paths": [".".join(p) for p in sorted(binary_paths)],
            "encodings": {
                "cbor": {
                    "filename": "message.cbor",
                    "content_type": "application/faying-protocol+cbor",
                    "size_bytes": len(cbor_bytes),
                    "deterministic": "RFC 8949 §4.2.1",
                },
                "json": {
                    "filename": "message.json",
                    "content_type": "application/faying-protocol+json",
                    "binary_encoding": "base64url-no-padding",
                    "key_naming": "kebab-case (per CDDL fap-1.0.cddl)",
                },
            },
            "signature_input": {
                "definition": "H( Deterministic-CBOR( Envelope_without_signature ) )  per design.md §6.3 S2",
                "det_cbor_filename": "signature.input.det-cbor.hex",
                "det_cbor_size_bytes": len(det_cbor_input),
                "hash_algorithm": "SHA-256",
                "hash_hex": sig_hash.hex(),
            },
            "signature": {
                "alg": "Ed25519",
                "pubkey_hex": PUBKEY_RAW.hex(),
                "sig_hex": sig_bytes.hex(),
            },
            "equivalence_assertions": {
                "semantic_equality": (
                    "cbor2.loads(message.cbor) == apply_binary_decode("
                    "json.loads(message.json), binary_field_paths) "
                    "→ True"
                ),
                "signature_input_identical_across_encodings": True,
                "signature_input_hash_identical_across_encodings": True,
                "signature_verification_result_identical_across_encodings": True,
                "verification_outcome": "ed25519.verify(pubkey, sig, det_cbor_input) → OK",
            },
            "_normative_references": [
                "design.md §5.1 (encoding rules)",
                "design.md §5.2 (envelope structure)",
                "design.md §6.3 S2 (signature input definition)",
                "RFC 8949 §4.2.1 (Core Deterministic Encoding)",
                "RFC 8259 (JSON)",
                "RFC 4648 §5 (base64url)",
                "schemas/fap-1.0.cddl (authoritative wire schema)",
            ],
            "_traceability": {
                "requirements": ["10.1", "10.2"],
                "ears_clauses": [
                    "R10.1.3", "R10.1.4",
                    "R10.2.1", "R10.2.4",
                ],
            },
        }
        write_text(
            out_dir / "expected.json",
            json.dumps(expected, indent=2, sort_keys=True, ensure_ascii=False),
        )

        index_entries.append(
            {
                "id": msg["dir"],
                "msg_type": msg_type,
                "msg_id": msg["msg-id"],
                "summary": msg["summary"],
                "files": {
                    "message.cbor": f"{msg['dir']}/message.cbor",
                    "message.cbor.hex": f"{msg['dir']}/message.cbor.hex",
                    "message.json": f"{msg['dir']}/message.json",
                    "signature.input.det-cbor.hex": f"{msg['dir']}/signature.input.det-cbor.hex",
                    "signature.input.hash.hex": f"{msg['dir']}/signature.input.hash.hex",
                    "expected.json": f"{msg['dir']}/expected.json",
                },
                "signature_input_hash_hex": sig_hash.hex(),
                "cbor_size_bytes": len(cbor_bytes),
                "det_cbor_input_size_bytes": len(det_cbor_input),
            }
        )

    # ---------------------------- index.json ---------------------------------
    index = {
        "spec": "Faying Protocol/1.0",
        "vector_set": "encoding-equivalence",
        "purpose": (
            "Demonstrate that CBOR (primary) and JSON (fallback) wire encodings "
            "are equivalent under §5.1 / §6.3: both deserialize to the same "
            "logical object, share a single Deterministic-CBOR signature input, "
            "and yield identical signature verification results."
        ),
        "covers_message_types": [m["msg-type"] for m in MESSAGES],
        "fixed_seed": {
            "ed25519_seed_hex": ED25519_SEED_HEX,
            "ed25519_pubkey_hex": PUBKEY_RAW.hex(),
            "note": (
                "Reproducible across runs. Generated by "
                "vectors/encoding-equivalence/generate.py."
            ),
        },
        "binary_field_convention_in_json": {
            "scheme": "base64url",
            "padding": "stripped (RFC 4648 §5, no '=' padding)",
            "rationale": (
                "JSON has no native bytes type; base64url avoids '+', '/', "
                "and '=' which require quoting in URLs and HTTP headers. "
                "Receivers re-hydrate bytes by decoding the documented "
                "binary_field_paths in expected.json before comparing to "
                "the CBOR-decoded shape."
            ),
        },
        "key_naming_convention": "kebab-case (matches CDDL keys in schemas/fap-1.0.cddl)",
        "deterministic_cbor_rules": "RFC 8949 §4.2.1 Core Deterministic Encoding",
        "signature_input_definition": "H( Deterministic-CBOR( Envelope_without_signature ) )  (design.md §6.3 S2)",
        "hash_algorithm": "SHA-256",
        "signature_algorithm": "Ed25519",
        "vectors": index_entries,
        "traceability": {
            "requirements": ["10.1", "10.2"],
            "design_sections": ["§5.1", "§5.2", "§6.3"],
            "tasks": ["3.7"],
        },
    }
    write_text(
        ROOT / "index.json",
        json.dumps(index, indent=2, sort_keys=False, ensure_ascii=False),
    )


if __name__ == "__main__":
    main()
