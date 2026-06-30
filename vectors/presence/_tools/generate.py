"""
Generate PRESENCE test vectors for Faying Protocol/1.0.

This script produces 15 test vectors that exercise the
`presence-signal` rule of `schemas/fap-1.0.cddl` and the verdict
matrix derived from design.md §3.2 (Presence Channel), §5.3.2
(PRESENCE message) and §7.1 (Authorization Grades — max-staleness
table).

Output layout (relative to the parent directory of this file)::

    fresh-webauthn-uv/                   signal.{cbor,json}  expected.json
    fresh-face-continuous/               signal.{cbor,json}  expected.json
    fresh-fingerprint-tap/               signal.{cbor,json}  expected.json
    fresh-presence-heartbeat-only/       signal.{cbor,json}  expected.json
    fresh-intent-ticket/                 signal.{cbor,json}  expected.json
    stale-webauthn-uv/                   signal.{cbor,json}  expected.json
    stale-face-continuous/               signal.{cbor,json}  expected.json
    stale-fingerprint-tap/               signal.{cbor,json}  expected.json
    stale-presence-heartbeat-only/       signal.{cbor,json}  expected.json
    stale-intent-ticket/                 signal.{cbor,json}  expected.json
    tampered-webauthn-uv-bad-signature/  signal.{cbor,json}  expected.json
    tampered-face-continuous-bad-attestation/  signal.{cbor,json}  expected.json
    tampered-fingerprint-tap-replay/     signal.{cbor,json}  expected.json
    tampered-presence-heartbeat-only-bad-signature/  signal.{cbor,json}  expected.json
    tampered-intent-ticket-replay/       signal.{cbor,json}  expected.json
    index.json
    README.md

Determinism contract
--------------------
* Every Ed25519 keypair, nonce and synthetic payload byte is derived
  from a fixed master seed (``FAYING_VECTOR_SEED``). Re-running the
  script reproduces the exact same byte-for-byte output.
* CBOR is encoded with ``cbor2.dumps(canonical=True)`` (RFC 8949
  §4.2.1). The signing input for every Presence_Signal is the
  canonical CBOR encoding of the unsigned envelope, regardless of the
  wire encoding. JSON vectors mirror the CBOR shape via the
  ``{"$bytes": ...}`` and ``{"$tag": 0, "$value": ...}`` conventions
  introduced by the BOOTSTRAP vectors (see
  ``vectors/bootstrap/README.md``).
* Replay vectors carry a deliberately reused ``(mandate-id, nonce)``
  pair — the duplicate counterpart is recorded inside ``expected.json``
  so the verifier can simulate the seen-set hit.
* The device_attestation block is intentionally a *stub* (see README):
  a self-signed Ed25519 attestation. design.md §3.3 separately defines
  the full HP → MS → IF chain; for PRESENCE the Presence_Device's
  TPM/secure-element quote is out of scope of this vector batch.
"""

from __future__ import annotations

import base64
import datetime as _dt
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

# 32-byte fixed seed; identical to the ``presence`` salt below means
# every PRESENCE vector is independently reproducible from this file
# alone. Do not change without bumping the vectors' generation date.
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
        h.update(b"presence|")  # domain separator
        h.update(label.encode("utf-8"))
        h.update(counter.to_bytes(4, "big"))
        out += h.digest()
        counter += 1
    return out[:length]


# ---------------------------------------------------------------------------
# Key generation (deterministic)
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
    """Convert a JSON-friendly tree into a CBOR-friendly tree.

    Reverses the ``{"$bytes": ...}`` and ``{"$tag": 0, "$value": ...}``
    conventions used in the JSON wire form so that the same logical
    payload yields the same canonical CBOR bytes regardless of
    encoding.
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
# Builders aligned with CDDL `presence-signal` and §5.3.2
# ---------------------------------------------------------------------------


# §7.1 max-staleness table (Authorization Grade -> max-staleness in
# milliseconds). Keys are descriptive labels used by the vectors and
# echoed into ``expected.json``.
GRADE_BUDGETS: Dict[str, Dict[str, Any]] = {
    "G1": {"max_staleness_ms": 5_000,         "description": "G1 Strict — real-time presence (≤ 5s)"},
    "G2": {"max_staleness_ms": 60_000,        "description": "G2 Moderate — task-level presence (≤ 60s)"},
    "G3": {"max_staleness_ms": 300_000,       "description": "G3 Loose — key-step intent ticket (≤ 5min)"},
    "G4": {"max_staleness_ms": 1_800_000,     "description": "G4 Autonomous — periodic heartbeat (≤ 30min)"},
}


# Map signal-type → which Authorization Grade it primarily binds to,
# per design.md §3.2 ("信号类型" table). The fresh-/stale-/tampered-
# vectors all carry the matching freshness window so reviewers can
# diff against §7.1.
SIGNAL_TO_GRADE: Dict[str, str] = {
    "webauthn-uv-fresh":          "G1",
    "face-continuous":            "G1",
    "fingerprint-tap":            "G2",
    "presence-heartbeat-only":    "G4",
    "intent-ticket":              "G3",
}


def make_device_attestation_stub(label: str) -> Dict[str, Any]:
    """Self-signed device attestation stub.

    The full Presence_Device attestation chain (TPM quote / WebAuthn
    AAGUID / platform keystore) is out of scope of these vectors —
    design.md §3.3 captures it. We emit a minimally valid CDDL
    `attestation` shape so the wire form decodes against
    `schemas/fap-1.0.cddl`, with a self-signed Ed25519 signature.
    """
    kp = make_ed25519(f"att:{label}")
    payload = b"presence-device-attestation:" + label.encode("utf-8")
    sig = sign(kp, payload)
    return {
        "format": "self-signed",
        "payload": bytes_marker(payload),
        "signer": f"presence-device:{label}",
        "signature": {
            "alg": "Ed25519",
            "pubkey": bytes_marker(kp.pubkey_raw),
            "sig": bytes_marker(sig),
        },
    }


def presence_signal_skeleton(
    *,
    mandate_id: str,
    signal_type: str,
    produced_at: str,
    nonce: bytes,
    device_id: str,
    attestation: Dict[str, Any],
) -> Dict[str, Any]:
    """Build a `presence-signal` tree minus the outer signature."""
    return {
        "mandate-id":         mandate_id,
        "signal-type":        signal_type,
        "produced-at":        time_marker(produced_at),
        "nonce":              bytes_marker(nonce),
        "device-id":          device_id,
        "device-attestation": attestation,
    }


# ---------------------------------------------------------------------------
# Vector specification & rendering
# ---------------------------------------------------------------------------


@dataclass
class VectorSpec:
    name: str
    state: str  # "fresh" | "stale" | "tampered"
    signal_type: str
    grade: str  # "G1" | "G2" | "G3" | "G4"
    summary: str
    notes: str
    expected: Dict[str, Any]
    # Builder produces an unsigned-envelope tree plus the device-key to
    # sign it (matches CDDL `presence-signal.signature`).
    signal_tree: Dict[str, Any]
    device_kp: Ed25519KeyPair
    # Optional tampering hook: if set, mutates the signed tree (after
    # the genuine signature was produced) to simulate the attack the
    # vector documents.
    tamper: Optional[str] = None
    # Replay companion: when not None, contains a `(produced_at, nonce)`
    # pair representing an earlier signal that the verifier should
    # treat as already-seen. Recorded into expected.json.
    replay_of: Optional[Dict[str, Any]] = None


def render_signal(spec: VectorSpec) -> Tuple[bytes, bytes, Dict[str, Any], bytes]:
    """Sign the presence signal and emit canonical CBOR + JSON bytes.

    Returns a tuple ``(cbor_bytes, json_bytes, full_tree_json,
    signing_input)``. The full tree carries the JSON wire shape (with
    the bytes / tag-0 markers) so it can be written to debug.json /
    decoded with `cbor_for_json` later.
    """
    # 1. Compute the canonical-CBOR signing input over the unsigned
    #    envelope — this is the contract design.md §6.3 mandates.
    cbor_tree = cbor_for_json(spec.signal_tree)
    signing_input = cbor_canonical(cbor_tree)
    sig = sign(spec.device_kp, signing_input)

    # 2. Add the outer signature block.
    full_tree = dict(spec.signal_tree)
    full_tree["signature"] = {
        "alg": "Ed25519",
        "pubkey": bytes_marker(spec.device_kp.pubkey_raw),
        "sig": bytes_marker(sig),
    }

    # 3. If the spec asks for tampering, mutate AFTER signing so the
    #    on-disk vector represents a real attack — verifiers must
    #    reject it as `attestation-invalid`.
    if spec.tamper == "bad-signature":
        # Flip the last byte of the outer signature.
        bad = bytearray(sig)
        bad[-1] ^= 0xFF
        full_tree["signature"]["sig"] = bytes_marker(bytes(bad))
    elif spec.tamper == "bad-attestation":
        # Flip the last byte of the device-attestation signature, then
        # RE-SIGN the outer envelope so the only verification failure
        # is localised to the device-attestation block. Without this
        # re-signing the outer envelope signature would also fail
        # (because device-attestation is part of its signed input),
        # which makes the vector indistinguishable from `bad-signature`.
        att_sig_b64 = full_tree["device-attestation"]["signature"]["sig"]
        att_sig = base64.urlsafe_b64decode(att_sig_b64["$bytes"] + "==")
        bad = bytearray(att_sig)
        bad[-1] ^= 0xFF
        full_tree["device-attestation"]["signature"]["sig"] = bytes_marker(
            bytes(bad)
        )
        # Re-compute the outer signature over the tampered tree.
        unsigned_after_tamper = {
            k: v for k, v in full_tree.items() if k != "signature"
        }
        new_signing_input = cbor_canonical(cbor_for_json(unsigned_after_tamper))
        new_sig = sign(spec.device_kp, new_signing_input)
        full_tree["signature"]["sig"] = bytes_marker(new_sig)
        signing_input = new_signing_input
    elif spec.tamper == "replay":
        # No payload mutation — the vector is byte-identical to a
        # previously-seen signal. The replay history lives in
        # ``expected.json`` and the verifier confirms the seen-set
        # would reject this on the second consumption.
        pass

    cbor_bytes = cbor_canonical(cbor_for_json(full_tree))
    json_bytes = json_canonical(full_tree)
    return cbor_bytes, json_bytes, full_tree, signing_input


def write_vector(out_root: Path, spec: VectorSpec) -> Dict[str, Any]:
    out = out_root / spec.name
    out.mkdir(parents=True, exist_ok=True)

    cbor_bytes, json_bytes, full_tree, signing_input = render_signal(spec)
    (out / "signal.cbor").write_bytes(cbor_bytes)
    (out / "signal.json").write_bytes(json_bytes)

    expected = dict(spec.expected)
    expected.setdefault("vector_name", spec.name)
    expected.setdefault("state", spec.state)
    expected.setdefault("signal_type", spec.signal_type)
    expected.setdefault("summary", spec.summary)
    expected.setdefault("notes", spec.notes)
    expected.setdefault("files", {
        "signal_cbor": "signal.cbor",
        "signal_json": "signal.json",
    })
    expected.setdefault("digests", {
        "signal_cbor_sha256": hashlib.sha256(cbor_bytes).hexdigest(),
        "signal_json_sha256": hashlib.sha256(json_bytes).hexdigest(),
        "signing_input_sha256": hashlib.sha256(signing_input).hexdigest(),
    })

    (out / "expected.json").write_text(
        json.dumps(expected, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    # Human-readable mirror so reviewers can diff without a CBOR decoder.
    (out / "debug.json").write_text(
        json.dumps(full_tree, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    return {
        "name": spec.name,
        "state": spec.state,
        "signal_type": spec.signal_type,
        "grade": spec.grade,
        "verdict": expected["verdict"],
        "summary": spec.summary,
        "signal_cbor": f"{spec.name}/signal.cbor",
        "signal_json": f"{spec.name}/signal.json",
        "expected": f"{spec.name}/expected.json",
        "signal_cbor_sha256": expected["digests"]["signal_cbor_sha256"],
        "signal_json_sha256": expected["digests"]["signal_json_sha256"],
    }


# ---------------------------------------------------------------------------
# Per-state vector builders
# ---------------------------------------------------------------------------


# A common "now" anchor used by every vector. Every freshness window
# is computed relative to this instant so the reviewer can verify
# (now − produced_at) ≤ max_staleness_ms by inspection.
NOW_ISO = "2026-03-15T12:00:00Z"
NOW_DT = _dt.datetime(2026, 3, 15, 12, 0, 0, tzinfo=_dt.timezone.utc)


def _produced_at_within(grade: str, *, margin_ms: int) -> str:
    """Return an RFC-3339 timestamp ``margin_ms`` before NOW.

    Negative margin is treated as zero (clamped) so callers can
    request "exactly at the boundary".
    """
    delta = max(0, margin_ms)
    ts = NOW_DT - _dt.timedelta(milliseconds=delta)
    return ts.strftime("%Y-%m-%dT%H:%M:%S") + (
        ".{:03d}Z".format(ts.microsecond // 1000)
        if ts.microsecond
        else "Z"
    )


def _build_signal_spec(
    *,
    name: str,
    state: str,
    signal_type: str,
    produced_at: str,
    age_ms: int,
    grade: str,
    summary: str,
    notes: str,
    verdict: str,
    error_code: Optional[int],
    error_name: Optional[str],
    requirements: List[str],
    tamper: Optional[str] = None,
    replay_of: Optional[Dict[str, Any]] = None,
) -> VectorSpec:
    mandate_id = f"01HXMNDT-PRESENCE-{name.upper()}"
    device_id = f"presence-device:vector-{name}"
    nonce = derive(f"nonce:{name}", 16)

    if replay_of is not None:
        # Replay vectors use the same nonce as the earlier signal they
        # are claiming to be. We record the original timestamp inside
        # `expected.json` so the verifier can simulate the seen-set.
        nonce = base64.urlsafe_b64decode(replay_of["nonce"] + "==")

    device_kp = make_ed25519(f"device:{name}")
    attestation = make_device_attestation_stub(f"device-{name}")

    signal_tree = presence_signal_skeleton(
        mandate_id=mandate_id,
        signal_type=signal_type,
        produced_at=produced_at,
        nonce=nonce,
        device_id=device_id,
        attestation=attestation,
    )

    budget = GRADE_BUDGETS[grade]
    expected = {
        "verdict": verdict,
        "error_code": error_code,
        "error_name": error_name,
        "freshness_window": {
            "grade": grade,
            "max_staleness_ms": budget["max_staleness_ms"],
            "produced_at": produced_at,
            "evaluated_at": NOW_ISO,
            "age_ms": age_ms,
            "within_budget": age_ms <= budget["max_staleness_ms"],
            "description": budget["description"],
        },
        "mandate_id": mandate_id,
        "signal_type": signal_type,
        "device_id": device_id,
        "nonce_b64u": b64u(nonce),
        "tamper": tamper,
        "requirements_validated": requirements,
    }
    if replay_of is not None:
        expected["replay_of"] = replay_of

    return VectorSpec(
        name=name,
        state=state,
        signal_type=signal_type,
        grade=grade,
        summary=summary,
        notes=notes,
        expected=expected,
        signal_tree=signal_tree,
        device_kp=device_kp,
        tamper=tamper,
        replay_of=replay_of,
    )


def build_fresh_vectors() -> List[VectorSpec]:
    """5 fresh vectors — one per signal type, well within max-staleness."""
    out: List[VectorSpec] = []

    # Signal 1: webauthn-uv-fresh — G1 budget 5s; pick 1.5s old.
    out.append(_build_signal_spec(
        name="fresh-webauthn-uv",
        state="fresh",
        signal_type="webauthn-uv-fresh",
        produced_at=_produced_at_within("G1", margin_ms=1500),
        age_ms=1500,
        grade="G1",
        summary=(
            "Fresh webauthn-uv-fresh signal at G1 (age 1.5s ≤ 5s); "
            "verifier MUST accept with verdict=ok."
        ),
        notes=(
            "Drives the §3.2 strong-presence path: WebAuthn user-"
            "verification anchors the G1 Strict budget."
        ),
        verdict="ok",
        error_code=None,
        error_name=None,
        requirements=["5.1", "10.1", "10.3"],
    ))

    # Signal 2: face-continuous — G1 budget 5s; pick 2.5s old.
    out.append(_build_signal_spec(
        name="fresh-face-continuous",
        state="fresh",
        signal_type="face-continuous",
        produced_at=_produced_at_within("G1", margin_ms=2500),
        age_ms=2500,
        grade="G1",
        summary=(
            "Fresh face-continuous signal at G1 (age 2.5s ≤ 5s); "
            "verifier MUST accept with verdict=ok."
        ),
        notes=(
            "Continuous face presence is a strong G1 anchor; on loss "
            "design.md §3.2 says it degrades to G2 — see the "
            "stale-face-continuous vector for that path."
        ),
        verdict="ok",
        error_code=None,
        error_name=None,
        requirements=["5.1", "10.1", "10.3"],
    ))

    # Signal 3: fingerprint-tap — G2 budget 60s; pick 20s old.
    out.append(_build_signal_spec(
        name="fresh-fingerprint-tap",
        state="fresh",
        signal_type="fingerprint-tap",
        produced_at=_produced_at_within("G2", margin_ms=20_000),
        age_ms=20_000,
        grade="G2",
        summary=(
            "Fresh fingerprint-tap signal at G2 (age 20s ≤ 60s); "
            "verifier MUST accept with verdict=ok."
        ),
        notes=(
            "Mid-strength one-shot signal. Re-tap is required before "
            "the next sensitive sub-task per §3.2."
        ),
        verdict="ok",
        error_code=None,
        error_name=None,
        requirements=["5.1", "10.1", "10.3"],
    ))

    # Signal 4: presence-heartbeat-only — G4 budget 30min; pick 10min old.
    out.append(_build_signal_spec(
        name="fresh-presence-heartbeat-only",
        state="fresh",
        signal_type="presence-heartbeat-only",
        produced_at=_produced_at_within("G4", margin_ms=10 * 60 * 1000),
        age_ms=10 * 60 * 1000,
        grade="G4",
        summary=(
            "Fresh heartbeat at G4 (age 10min ≤ 30min); verifier MUST "
            "accept with verdict=ok."
        ),
        notes=(
            "Heartbeat-only signals at G4 keep autonomous loops alive "
            "but cannot anchor G1/G2 sensitive actions."
        ),
        verdict="ok",
        error_code=None,
        error_name=None,
        requirements=["5.1", "10.1", "10.3"],
    ))

    # Signal 5: intent-ticket — G3 budget 5min; pick 90s old.
    out.append(_build_signal_spec(
        name="fresh-intent-ticket",
        state="fresh",
        signal_type="intent-ticket",
        produced_at=_produced_at_within("G3", margin_ms=90_000),
        age_ms=90_000,
        grade="G3",
        summary=(
            "Fresh intent-ticket at G3 (age 1.5min ≤ 5min); verifier "
            "MUST accept with verdict=ok."
        ),
        notes=(
            "Intent-ticket is a one-shot supplementary signal per "
            "§3.2; once consumed it is dropped from the seen-set "
            "regardless of remaining freshness."
        ),
        verdict="ok",
        error_code=None,
        error_name=None,
        requirements=["5.1", "10.1", "10.3"],
    ))

    return out


def build_stale_vectors() -> List[VectorSpec]:
    """5 stale vectors — produced more than max-staleness ago."""
    out: List[VectorSpec] = []

    # Signal 1: webauthn-uv-fresh stale — 6s past 5s budget.
    out.append(_build_signal_spec(
        name="stale-webauthn-uv",
        state="stale",
        signal_type="webauthn-uv-fresh",
        produced_at=_produced_at_within("G1", margin_ms=11_000),
        age_ms=11_000,
        grade="G1",
        summary=(
            "Stale webauthn-uv-fresh signal at G1 (age 11s > 5s); "
            "verifier MUST reject with verdict=stale."
        ),
        notes=(
            "Demonstrates Requirement 5.1 #2 and §EH.1 row "
            "`E_PRESENCE_STALE`: produced_at + freshness_window < now."
        ),
        verdict="stale",
        error_code=1005,
        error_name="E_PRESENCE_STALE",
        requirements=["5.1", "5.2", "9.1", "10.1", "10.3"],
    ))

    # Signal 2: face-continuous stale — 6s past 5s budget.
    out.append(_build_signal_spec(
        name="stale-face-continuous",
        state="stale",
        signal_type="face-continuous",
        produced_at=_produced_at_within("G1", margin_ms=8_000),
        age_ms=8_000,
        grade="G1",
        summary=(
            "Stale face-continuous signal at G1 (age 8s > 5s); "
            "verifier MUST reject with verdict=stale."
        ),
        notes=(
            "Drives the §3.2 'face-continuous → degrade to G2' path: "
            "the verifier rejects this signal with E_PRESENCE_STALE "
            "and the operator policy (`on-loss`) decides whether to "
            "downgrade or suspend."
        ),
        verdict="stale",
        error_code=1005,
        error_name="E_PRESENCE_STALE",
        requirements=["5.1", "5.2", "9.1", "10.1", "10.3"],
    ))

    # Signal 3: fingerprint-tap stale — 90s past 60s budget.
    out.append(_build_signal_spec(
        name="stale-fingerprint-tap",
        state="stale",
        signal_type="fingerprint-tap",
        produced_at=_produced_at_within("G2", margin_ms=90_000),
        age_ms=90_000,
        grade="G2",
        summary=(
            "Stale fingerprint-tap signal at G2 (age 90s > 60s); "
            "verifier MUST reject with verdict=stale."
        ),
        notes=(
            "Triggers `E_PRESENCE_STALE` and the §3.2 descent to G3 "
            "Loose; subsequent sensitive sub-task requires a fresh tap."
        ),
        verdict="stale",
        error_code=1005,
        error_name="E_PRESENCE_STALE",
        requirements=["5.1", "5.2", "9.1", "10.1", "10.3"],
    ))

    # Signal 4: presence-heartbeat-only stale — 35min past 30min budget.
    out.append(_build_signal_spec(
        name="stale-presence-heartbeat-only",
        state="stale",
        signal_type="presence-heartbeat-only",
        produced_at=_produced_at_within("G4", margin_ms=35 * 60 * 1000),
        age_ms=35 * 60 * 1000,
        grade="G4",
        summary=(
            "Stale heartbeat at G4 (age 35min > 30min); verifier MUST "
            "reject with verdict=stale."
        ),
        notes=(
            "G4 has no stricter grade to descend to, so the policy in "
            "§7.2 is to move directly to Suspended; the verdict here "
            "is `stale` and the lifecycle action is recorded by the "
            "consuming MS / RP."
        ),
        verdict="stale",
        error_code=1005,
        error_name="E_PRESENCE_STALE",
        requirements=["5.1", "5.2", "9.1", "10.1", "10.3"],
    ))

    # Signal 5: intent-ticket stale — 6min past 5min budget.
    out.append(_build_signal_spec(
        name="stale-intent-ticket",
        state="stale",
        signal_type="intent-ticket",
        produced_at=_produced_at_within("G3", margin_ms=6 * 60 * 1000),
        age_ms=6 * 60 * 1000,
        grade="G3",
        summary=(
            "Stale intent-ticket at G3 (age 6min > 5min); verifier "
            "MUST reject with verdict=stale."
        ),
        notes=(
            "Even one-shot supplementary signals must satisfy the "
            "freshness budget; expired tickets are rejected before "
            "consumption."
        ),
        verdict="stale",
        error_code=1005,
        error_name="E_PRESENCE_STALE",
        requirements=["5.1", "9.1", "10.1", "10.3"],
    ))

    return out


def build_tampered_vectors() -> List[VectorSpec]:
    """5 tampered vectors — bad signature, bad attestation or replay.

    The five vectors split as:

      * 2 outer-signature tampers (webauthn-uv, presence-heartbeat-only)
      * 1 device-attestation tamper (face-continuous)
      * 2 replays (fingerprint-tap, intent-ticket)

    All five MUST be rejected by a conformant verifier:
      - bad-signature / bad-attestation → verdict=attestation-invalid
      - replay                          → verdict=replay
    """
    out: List[VectorSpec] = []

    # Signal 1: webauthn-uv with outer-signature tamper.
    out.append(_build_signal_spec(
        name="tampered-webauthn-uv-bad-signature",
        state="tampered",
        signal_type="webauthn-uv-fresh",
        produced_at=_produced_at_within("G1", margin_ms=2000),
        age_ms=2000,
        grade="G1",
        summary=(
            "Tampered webauthn-uv-fresh: outer signature flipped "
            "after signing; verifier MUST reject with "
            "verdict=attestation-invalid."
        ),
        notes=(
            "Drives §EH.1 row `E_ATTESTATION_INVALID` (1007). The "
            "signal would otherwise be fresh; the verifier MUST NOT "
            "fall back to verdict=ok on signature failure."
        ),
        verdict="attestation-invalid",
        error_code=1007,
        error_name="E_ATTESTATION_INVALID",
        requirements=["5.1", "9.1", "10.1", "10.3"],
        tamper="bad-signature",
    ))

    # Signal 2: face-continuous with device-attestation tamper.
    out.append(_build_signal_spec(
        name="tampered-face-continuous-bad-attestation",
        state="tampered",
        signal_type="face-continuous",
        produced_at=_produced_at_within("G1", margin_ms=1000),
        age_ms=1000,
        grade="G1",
        summary=(
            "Tampered face-continuous: device-attestation signature "
            "flipped after signing; verifier MUST reject with "
            "verdict=attestation-invalid."
        ),
        notes=(
            "The presence-signal envelope signature is intact — the "
            "rejection comes from the device-attestation block "
            "failing verification."
        ),
        verdict="attestation-invalid",
        error_code=1007,
        error_name="E_ATTESTATION_INVALID",
        requirements=["5.1", "9.1", "10.1", "10.3"],
        tamper="bad-attestation",
    ))

    # Signal 3: fingerprint-tap replay (re-using nonce of a prior signal).
    earlier_nonce = derive("replay-source:fingerprint-tap", 16)
    earlier_produced_at = _produced_at_within("G2", margin_ms=15_000)
    out.append(_build_signal_spec(
        name="tampered-fingerprint-tap-replay",
        state="tampered",
        signal_type="fingerprint-tap",
        produced_at=_produced_at_within("G2", margin_ms=10_000),
        age_ms=10_000,
        grade="G2",
        summary=(
            "Replay fingerprint-tap: identical (mandate-id, nonce) "
            "tuple as a previously-accepted signal; verifier MUST "
            "reject with verdict=replay."
        ),
        notes=(
            "Drives Requirement 9.1 #2 and §EH.1 row `E_REPLAY` "
            "(1009). `expected.replay_of` lists the `(produced_at, "
            "nonce)` pair that the seen-set must remember."
        ),
        verdict="replay",
        error_code=1009,
        error_name="E_REPLAY",
        requirements=["5.1", "9.1", "10.1", "10.3"],
        tamper="replay",
        replay_of={
            "produced_at": earlier_produced_at,
            "nonce": b64u(earlier_nonce),
        },
    ))

    # Signal 4: presence-heartbeat-only with outer-signature tamper.
    out.append(_build_signal_spec(
        name="tampered-presence-heartbeat-only-bad-signature",
        state="tampered",
        signal_type="presence-heartbeat-only",
        produced_at=_produced_at_within("G4", margin_ms=5 * 60 * 1000),
        age_ms=5 * 60 * 1000,
        grade="G4",
        summary=(
            "Tampered heartbeat: outer signature flipped after "
            "signing; verifier MUST reject with "
            "verdict=attestation-invalid."
        ),
        notes=(
            "Even at G4 (lowest in-place strength), a signature "
            "failure forces `E_ATTESTATION_INVALID` rather than "
            "lenient acceptance."
        ),
        verdict="attestation-invalid",
        error_code=1007,
        error_name="E_ATTESTATION_INVALID",
        requirements=["5.1", "9.1", "10.1", "10.3"],
        tamper="bad-signature",
    ))

    # Signal 5: intent-ticket replay (re-using nonce of a prior signal).
    earlier_ticket_nonce = derive("replay-source:intent-ticket", 16)
    earlier_ticket_at = _produced_at_within("G3", margin_ms=120_000)
    out.append(_build_signal_spec(
        name="tampered-intent-ticket-replay",
        state="tampered",
        signal_type="intent-ticket",
        produced_at=_produced_at_within("G3", margin_ms=60_000),
        age_ms=60_000,
        grade="G3",
        summary=(
            "Replay intent-ticket: identical (mandate-id, nonce) "
            "tuple as a previously-consumed ticket; verifier MUST "
            "reject with verdict=replay."
        ),
        notes=(
            "Intent tickets are one-shot per §3.2 — a second "
            "consumption is unconditionally `E_REPLAY` even if the "
            "freshness window has not yet expired."
        ),
        verdict="replay",
        error_code=1009,
        error_name="E_REPLAY",
        requirements=["5.1", "9.1", "10.1", "10.3"],
        tamper="replay",
        replay_of={
            "produced_at": earlier_ticket_at,
            "nonce": b64u(earlier_ticket_nonce),
        },
    ))

    return out


# ---------------------------------------------------------------------------
# Top-level driver
# ---------------------------------------------------------------------------


def build_index(out_root: Path) -> None:
    specs: List[VectorSpec] = []
    specs.extend(build_fresh_vectors())
    specs.extend(build_stale_vectors())
    specs.extend(build_tampered_vectors())

    entries: List[Dict[str, Any]] = []
    for spec in specs:
        entries.append(write_vector(out_root, spec))

    index = {
        "category": "PRESENCE",
        "spec_version": "Faying Protocol/1.0",
        "schemas": {
            "cddl": "schemas/fap-1.0.cddl",
            "ts_view": "schemas/types.ts",
        },
        "evaluated_at": NOW_ISO,
        "deterministic_seed_sha256": hashlib.sha256(FAYING_VECTOR_SEED).hexdigest(),
        "generated_with": "vectors/presence/_tools/generate.py",
        "freshness_table": {
            grade: {
                "max_staleness_ms": budget["max_staleness_ms"],
                "description": budget["description"],
            }
            for grade, budget in GRADE_BUDGETS.items()
        },
        "signal_grade_binding": SIGNAL_TO_GRADE,
        "verdicts": ["ok", "stale", "replay", "attestation-invalid"],
        "requirements_covered": [
            "5.1", "5.2", "9.1", "10.1", "10.3",
        ],
        "vectors": entries,
    }
    (out_root / "index.json").write_text(
        json.dumps(index, sort_keys=True, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    out_root = Path(__file__).resolve().parent.parent
    build_index(out_root)
    print(f"Generated PRESENCE vectors under {out_root}")


if __name__ == "__main__":
    main()
