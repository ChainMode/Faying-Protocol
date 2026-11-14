"""Re-sign Faying Protocol envelopes across all three signing algorithms.

The dim_signing conformance driver loads each official vector under
``vectors/`` and reproduces the signing flow under each of
``Ed25519`` / ``ES256`` / ``ML-DSA-65``. The acceptance criterion of
task 5.3 is:

    3/3 算法跑通；ML-DSA-65 作为 OPTIONAL 实现存在
    （即不支持时不影响 BOOTSTRAP）

Concretely, for every input envelope tree we:

  1. Strip the existing ``signature`` field.
  2. Compute the signing input ``H_input = Deterministic-CBOR(envelope)``
     per design.md §6.3.
  3. Sign ``H_input`` with a fresh keypair under each algorithm.
  4. Verify the produced signature with the same algorithm's verifier.
  5. Return a structured result so the test layer can assert per-algorithm
     pass/fail.

This module deliberately produces a *new* envelope per algorithm rather
than mutating the original, so tests can compare side-by-side without
clobbering vector state.

Vector layout heterogeneity
---------------------------
Different ``vectors/<category>/`` toolchains were authored at different
times and use different JSON conventions for binary data
(``{"$bytes": ...}`` vs ``{"$b64u": ...}``) and timestamp encodings
(CBOR-tag-0 wrapper vs inline ISO-8601 string). To stay
encoding-agnostic, this module loads the CBOR encoding of the envelope
directly via ``cbor2.loads`` whenever possible, because CBOR carries
bytes natively and avoids that JSON divergence entirely. JSON is the
fallback for vectors that ship a JSON-only payload.

The signing input is **always** the canonical CBOR encoding of the
envelope-without-outer-signature, regardless of how the vector was
loaded. This matches design.md §6.3 / property P16.1.
"""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2

from .algorithms import (
    ALG_ED25519,
    ALG_ES256,
    ALG_ML_DSA_65,
    SUPPORTED_ALGORITHMS,
    KeyPair,
    generate_keypair,
    sign,
    verify,
)


# ---------------------------------------------------------------------------
# JSON-bytes convention helpers (handle both ``$bytes`` and ``$b64u``).
# ---------------------------------------------------------------------------
def _b64u_decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def _json_to_native(obj: Any) -> Any:
    """Convert vector JSON conventions to native CBOR-friendly Python.

    Recognised wrappers:
      * ``{"$bytes": "<b64url>"}`` (vectors/bootstrap toolchain)
      * ``{"$b64u": "<b64url>"}``  (vectors/disclosure toolchain)
      * ``{"$tag": 0, "$value": "<iso-8601>"}`` (CBOR tag 0)

    All other dicts / lists / scalars pass through. Inline ISO-8601
    strings remain strings; if the wire-format toolchain expects them
    to be CBOR tag 0, that conversion happens at the original encoder
    layer, not here.
    """

    if isinstance(obj, dict):
        keys = set(obj.keys())
        if keys == {"$bytes"} and isinstance(obj["$bytes"], str):
            return _b64u_decode(obj["$bytes"])
        if keys == {"$b64u"} and isinstance(obj["$b64u"], str):
            return _b64u_decode(obj["$b64u"])
        if keys == {"$tag", "$value"} and obj["$tag"] == 0:
            return cbor2.CBORTag(0, obj["$value"])
        return {k: _json_to_native(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_to_native(v) for v in obj]
    return obj


def _deterministic_cbor(obj: Any) -> bytes:
    """Encode ``obj`` per RFC 8949 §4.2.1 (Deterministic CBOR)."""

    return cbor2.dumps(obj, canonical=True)


# ---------------------------------------------------------------------------
# Envelope discovery within a vector directory.
# ---------------------------------------------------------------------------
# Files we treat as the "primary" signed envelope, in priority order. The
# order matters: ``request.*`` is the canonical name across the bootstrap /
# delegate / grade-switch / revoke / presence / errors vectors;
# ``disclosure.*`` is the disclosure family's name; ``faying-request.*``
# the FAYING_REQUEST family; etc. We always pick the first match per
# extension because each vector ships one envelope of interest.
_ENVELOPE_BASENAMES: Tuple[str, ...] = (
    "request",
    "disclosure",
    "faying-request",
    "faying_request",
    "envelope",
    "presence",
    "grade-switch",
    "grade_switch",
    "delegate",
    "revoke",
    "error",
    "response",
)


def _find_envelope_file(vector_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
    """Locate the canonical envelope file in ``vector_dir``.

    Returns ``(path, encoding)`` where ``encoding`` is ``"cbor"`` or
    ``"json"``. Prefers ``.cbor`` over ``.json`` (CBOR is the protocol's
    primary wire format per design.md §5.1) and prefers earlier names
    in :data:`_ENVELOPE_BASENAMES`.
    """

    for basename in _ENVELOPE_BASENAMES:
        cbor_path = vector_dir / f"{basename}.cbor"
        if cbor_path.exists():
            return cbor_path, "cbor"
        json_path = vector_dir / f"{basename}.json"
        if json_path.exists():
            return json_path, "json"
    return None, None


def load_envelope(vector_dir: Path) -> Tuple[Any, str]:
    """Load the signed envelope from a vector directory.

    Returns ``(envelope_native, source)`` where ``envelope_native`` is a
    Python tree with ``bytes`` carrying raw byte strings and
    ``cbor2.CBORTag`` carrying CBOR tags, ready for :func:`_deterministic_cbor`,
    and ``source`` is one of ``"cbor"`` / ``"json"`` indicating the file
    that was loaded.

    Raises:
        FileNotFoundError: if no envelope file can be found.
        ValueError: if the envelope is not a mapping (every Faying
            envelope is a CBOR map / JSON object).
    """

    envelope_path, encoding = _find_envelope_file(vector_dir)
    if envelope_path is None:
        raise FileNotFoundError(
            f"{vector_dir}: no envelope file found "
            f"(looked for any of {_ENVELOPE_BASENAMES} with .cbor/.json)"
        )

    if encoding == "cbor":
        envelope = cbor2.loads(envelope_path.read_bytes())
    else:
        envelope = _json_to_native(
            json.loads(envelope_path.read_text(encoding="utf-8"))
        )

    if not isinstance(envelope, dict):
        raise ValueError(
            f"{envelope_path}: expected a top-level mapping, got "
            f"{type(envelope).__name__}"
        )
    return envelope, encoding


# ---------------------------------------------------------------------------
# Re-signing.
# ---------------------------------------------------------------------------
@dataclass
class ResignResult:
    """Outcome of re-signing a single envelope under one algorithm."""

    vector_name: str
    algorithm: str
    signing_input_sha256: str
    signature_alg: str  # the wire-format value of signature.alg
    signature_length: int
    public_key_length: int
    verify_ok: bool
    notes: str = ""

    def passed(self) -> bool:
        return self.verify_ok and self.signature_alg in SUPPORTED_ALGORITHMS


def _strip_signature(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new tree without the outer ``signature`` field.

    Per design.md §6.3 the signing input is computed over the envelope
    *without* the outer signature. We do not touch nested signatures
    (e.g. ``claims.signature`` for response envelopes carrying a
    Mandate) because they are inputs to the outer signature and must be
    preserved bit-for-bit.
    """

    return {k: v for k, v in envelope.items() if k != "signature"}


def resign_envelope(
    envelope: Dict[str, Any],
    *,
    algorithm: str,
    seed: Optional[bytes] = None,
    label: str = "conformance",
) -> Tuple[Dict[str, Any], KeyPair, bytes, bytes]:
    """Sign ``envelope`` (without its outer signature) under ``algorithm``.

    Returns ``(envelope_with_new_signature, keypair, signing_input,
    signature_bytes)``.
    """

    kp = generate_keypair(algorithm, seed=seed)
    inner = _strip_signature(envelope)
    signing_input = _deterministic_cbor(inner)
    signature = sign(kp, signing_input, label=label)

    new_envelope = dict(inner)
    new_envelope["signature"] = {
        "alg": kp.alg,
        "pubkey": kp.public_key_bytes(),
        "sig": signature,
    }
    return new_envelope, kp, signing_input, signature


def resign_and_verify(
    envelope: Dict[str, Any],
    *,
    vector_name: str,
    algorithm: str,
    seed: Optional[bytes] = None,
) -> ResignResult:
    """Re-sign + verify in a single step; produce a :class:`ResignResult`."""

    label = f"{vector_name}:{algorithm}"
    new_envelope, kp, signing_input, signature = resign_envelope(
        envelope, algorithm=algorithm, seed=seed, label=label
    )
    ok = verify(kp, signing_input, signature)

    notes = ""
    if algorithm == ALG_ML_DSA_65:
        notes = (
            "ML-DSA-65 path uses a deterministic placeholder signature "
            "(see dim_signing/README.md); verification is format-only."
        )

    return ResignResult(
        vector_name=vector_name,
        algorithm=kp.alg,
        signing_input_sha256=hashlib.sha256(signing_input).hexdigest(),
        signature_alg=new_envelope["signature"]["alg"],
        signature_length=len(signature),
        public_key_length=len(kp.public_key_bytes()),
        verify_ok=ok,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Vector enumeration.
# ---------------------------------------------------------------------------
def iter_vector_dirs(vectors_root: Path) -> List[Path]:
    """Return every vector directory under ``vectors_root``.

    A "vector directory" is any directory that contains an
    ``expected.json`` file AND at least one envelope file the loader
    knows how to consume. We deliberately exclude ``_tools/`` /
    ``__pycache__`` and any other non-vector siblings.
    """

    out: List[Path] = []
    for category in sorted(vectors_root.iterdir()):
        if not category.is_dir() or category.name.startswith((".", "_")):
            continue
        for entry in sorted(category.iterdir()):
            if not entry.is_dir() or entry.name.startswith((".", "_")):
                continue
            if not (entry / "expected.json").exists():
                continue
            envelope_path, _ = _find_envelope_file(entry)
            if envelope_path is None:
                continue
            out.append(entry)
    return out


def resign_vector_across_algorithms(
    vector_dir: Path,
    *,
    algorithms: Tuple[str, ...] = SUPPORTED_ALGORITHMS,
    seed: Optional[bytes] = None,
) -> Dict[str, ResignResult]:
    """Run :func:`resign_and_verify` for every algorithm on a single vector."""

    envelope, _encoding = load_envelope(vector_dir)
    out: Dict[str, ResignResult] = {}
    for alg in algorithms:
        out[alg] = resign_and_verify(
            envelope,
            vector_name=vector_dir.name,
            algorithm=alg,
            seed=seed,
        )
    return out


__all__ = [
    "ResignResult",
    "iter_vector_dirs",
    "load_envelope",
    "resign_and_verify",
    "resign_envelope",
    "resign_vector_across_algorithms",
]
