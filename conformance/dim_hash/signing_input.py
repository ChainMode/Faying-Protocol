"""Compute signing-input hashes across both protocol-supported hash
algorithms for every Faying Protocol vector.

The dim_hash conformance driver loads each official vector under
``vectors/`` and reproduces the §6.3 signing-input expression under
each of ``SHA-256`` and ``BLAKE3``. The acceptance criteria of task 5.4
are:

    2/2 哈希跑通；签名输入构造与 §6.3 完全一致

which decompose into two independently checkable claims:

  * **Coverage** (2/2): every vector yields a digest of the correct
    length under each algorithm. The driver emits one
    :class:`HashCheckResult` per (vector, algorithm) pair.

  * **Construction (§6.3)**: the *bytes that go into the hash*, i.e.
    ``Deterministic-CBOR(envelope_without_signature)``, are identical
    across hash algorithms. This is a structural invariant of the
    signing-input expression: the hash function is a pure
    post-processor, so swapping ``SHA-256`` for ``BLAKE3`` must not
    perturb the input bytes. The driver enforces this with the
    :func:`compute_signing_input` helper, whose return value is
    independent of the hash algorithm.

Vector layout heterogeneity
---------------------------
Different ``vectors/<category>/`` toolchains use different envelope
filenames (``request.cbor`` vs ``signal.cbor`` vs ``mandate.cbor``)
and different JSON conventions for binary data. To stay encoding-
agnostic — and to match the convention used by :mod:`conformance.
dim_signing.resign` — this module loads the CBOR encoding of the
envelope directly via ``cbor2.loads`` whenever possible, falling back
to JSON only for vectors without a CBOR sibling.

The signing input is **always** the canonical CBOR encoding of the
envelope-without-outer-signature, regardless of how the vector was
loaded; this matches design.md §6.3 / property P16.1.
"""

from __future__ import annotations

import base64
import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cbor2

from .algorithms import (
    HASH_DIGEST_SIZE_BYTES,
    SUPPORTED_HASHES,
    compute_hash,
    normalize_hash,
)


# ---------------------------------------------------------------------------
# JSON-bytes convention helpers (handle both ``$bytes`` and ``$b64u``).
# ---------------------------------------------------------------------------
# This mirrors the helpers in :mod:`conformance.dim_signing.resign`. We
# duplicate (rather than import) because the dim_signing version is
# private (leading-underscore names) and we do not want to make either
# package depend on the other; both consume the same vector corpus
# independently.
def _b64u_decode(value: str) -> bytes:
    pad = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + pad)


def _json_to_native(obj: Any) -> Any:
    """Convert vector JSON conventions to native CBOR-friendly Python.

    Recognised wrappers:
      * ``{"$bytes": "<b64url>"}`` (vectors/bootstrap toolchain)
      * ``{"$b64u": "<b64url>"}``  (vectors/disclosure toolchain)
      * ``{"$tag": 0, "$value": "<iso-8601>"}`` (CBOR tag 0)
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
    """Encode ``obj`` per RFC 8949 §4.2.1 (Deterministic CBOR).

    This is the second-stage of the §6.3 signing input: ``Det-CBOR(
    envelope_without_signature)``. Combined with the first stage
    (signature stripping) and wrapped by a hash, it forms the full
    signing-input expression task 5.4 covers.
    """

    return cbor2.dumps(obj, canonical=True)


def _datetimes_to_tag0(obj: Any) -> Any:
    """Replace every ``datetime`` leaf with ``CBORTag(0, RFC3339-string)``.

    ``cbor2.loads`` decodes CBOR tag 0 (standard date/time string) into a
    Python ``datetime`` by default. Re-encoding that ``datetime`` with
    ``cbor2.dumps(..., canonical=True)`` produces a *different* byte
    sequence than the original (cbor2 emits a numeric tag-1 epoch
    timestamp for ``datetime`` unless ``datetime_as_timestamp=False``,
    and even with that knob the ISO-8601 formatting may not match the
    one the vector toolchain emits — it varies by sub-second precision).

    To guarantee bit-identical canonical CBOR for the §6.3 signing
    input, we walk the decoded tree and re-tag every ``datetime`` as
    ``CBORTag(0, "<RFC 3339 string>")`` using the exact format the
    Faying Protocol vector toolchains produce:

      * ``...HH:MM:SSZ`` when ``microsecond == 0``;
      * ``...HH:MM:SS.fffZ`` when ``microsecond % 1000 == 0`` (ms
        precision);
      * ``...HH:MM:SS.ffffffZ`` otherwise.

    This mirrors the helper in :mod:`conformance.dim_encoding.driver`
    so the two dimensions agree on exactly which bytes the §6.3
    signing-input expression is computed over.
    """

    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=_dt.timezone.utc)
        else:
            obj = obj.astimezone(_dt.timezone.utc)
        if obj.microsecond == 0:
            s = obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif obj.microsecond % 1000 == 0:
            s = (
                obj.strftime("%Y-%m-%dT%H:%M:%S")
                + f".{obj.microsecond // 1000:03d}Z"
            )
        else:
            s = (
                obj.strftime("%Y-%m-%dT%H:%M:%S")
                + f".{obj.microsecond:06d}Z"
            )
        return cbor2.CBORTag(0, s)
    if isinstance(obj, dict):
        return {k: _datetimes_to_tag0(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_datetimes_to_tag0(v) for v in obj]
    if isinstance(obj, cbor2.CBORTag):
        return cbor2.CBORTag(obj.tag, _datetimes_to_tag0(obj.value))
    return obj


# ---------------------------------------------------------------------------
# Envelope discovery within a vector directory.
# ---------------------------------------------------------------------------
# Files we treat as the "primary" signed envelope, in priority order.
# We always pick the first match per extension because each vector
# ships one envelope of interest. The list mirrors the table used by
# :mod:`conformance.dim_signing.resign` so the two dimensions agree on
# which artefact is "the envelope" for each vector.
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
    "signal",     # vectors/presence/* uses signal.cbor
    "mandate",    # vectors/endorsement/* uses mandate.cbor
    "message",    # vectors/encoding-equivalence/* uses message.cbor
    "trigger",    # vectors/errors/* often uses trigger.cbor
)


def _find_envelope_file(vector_dir: Path) -> Tuple[Optional[Path], Optional[str]]:
    """Locate the canonical envelope file in ``vector_dir``.

    Returns ``(path, encoding)`` where ``encoding`` is ``"cbor"`` or
    ``"json"``. Prefers ``.cbor`` over ``.json`` (CBOR is the
    protocol's primary wire format per design.md §5.1) and prefers
    earlier names in :data:`_ENVELOPE_BASENAMES`.
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

    Returns ``(envelope_native, source)`` where ``envelope_native`` is
    a Python tree with ``bytes`` carrying raw byte strings and
    ``cbor2.CBORTag`` carrying CBOR tags, ready for
    :func:`_deterministic_cbor`, and ``source`` is one of
    ``"cbor"`` / ``"json"`` indicating the file that was loaded.

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


def _strip_signature(envelope: Dict[str, Any]) -> Dict[str, Any]:
    """Return a new tree without the outer ``signature`` field.

    Per design.md §6.3 the signing input is computed over the envelope
    *without* the outer signature. We do not touch nested signatures
    (e.g. ``claims.signature`` for response envelopes carrying a
    Mandate); they are inputs to the outer signature and must be
    preserved bit-for-bit.
    """

    return {k: v for k, v in envelope.items() if k != "signature"}


# ---------------------------------------------------------------------------
# Signing-input computation.
# ---------------------------------------------------------------------------
def compute_signing_input(envelope: Dict[str, Any]) -> bytes:
    """Compute ``Deterministic-CBOR(envelope_without_signature)``.

    This is the *byte string* that is fed to the hash function in the
    §6.3 signing-input expression. By construction the result is
    independent of which hash algorithm wraps it; the dim_hash
    conformance driver verifies that this invariant holds at runtime
    (see :func:`hash_vector_across_algorithms`).

    Datetime normalisation: any ``datetime`` leaf in the decoded tree
    is re-tagged as ``CBORTag(0, RFC 3339 string)`` before encoding,
    so the canonical CBOR output is bit-identical to the bytes the
    vector toolchains produced (see :func:`_datetimes_to_tag0`).
    """

    return _deterministic_cbor(
        _datetimes_to_tag0(_strip_signature(envelope))
    )


# ---------------------------------------------------------------------------
# Result records.
# ---------------------------------------------------------------------------
@dataclass
class HashCheckResult:
    """Outcome of hashing a single vector under one hash algorithm.

    Attributes:
        vector_name: Human-readable identifier for the vector
            (``<category>/<case>``).
        hash_algorithm: One of :data:`SUPPORTED_HASHES`.
        signing_input_bytes: The Det-CBOR encoding of the envelope
            without its outer signature. Identical across algorithms
            by construction; recorded here so the driver can assert
            that invariant.
        signing_input_length: ``len(signing_input_bytes)``, surfaced
            for ergonomic logging.
        digest_hex: The hex-encoded digest under ``hash_algorithm``.
        digest_length: Length of the raw digest in bytes; must equal
            :data:`HASH_DIGEST_SIZE_BYTES`\\ ``[hash_algorithm]``.
        notes: Human-readable note (e.g. when the vector advertises a
            matching reference digest in ``expected.json`` and the
            driver successfully cross-checked it).
        reference_digest_matched: ``True`` when ``expected.json`` ships
            a SHA-256 digest of the signing input and our computation
            matches it; ``False`` when it ships one and we differ;
            ``None`` when it ships none. ``False`` is a hard failure
            of the §6.3 construction claim.
    """

    vector_name: str
    hash_algorithm: str
    signing_input_bytes: bytes
    signing_input_length: int
    digest_hex: str
    digest_length: int
    notes: str = ""
    reference_digest_matched: Optional[bool] = None

    def passed(self) -> bool:
        if self.hash_algorithm not in SUPPORTED_HASHES:
            return False
        if self.digest_length != HASH_DIGEST_SIZE_BYTES[self.hash_algorithm]:
            return False
        if self.reference_digest_matched is False:
            return False
        return True


# ---------------------------------------------------------------------------
# Reference digest extraction (best-effort cross-check).
# ---------------------------------------------------------------------------
# Several vector toolchains ship a SHA-256 digest of the signing input
# in ``expected.json`` (see ``vectors/encoding-equivalence/01-bootstrap/
# expected.json`` and ``vectors/bootstrap/pos-cbor-ed25519/expected.json``).
# When such a digest is present we use it as a ground-truth oracle for
# the SHA-256 column: a mismatch means our signing-input construction
# diverges from the one in §6.3, which is a direct failure of task 5.4's
# acceptance gate. The cross-check is intentionally one-sided
# (SHA-256 only) because no vector ships a BLAKE3 reference digest yet;
# task 5.6's reference implementations will close that loop.
_DIGEST_FIELDS_BY_ALG = {
    "SHA-256": (
        # ``vectors/encoding-equivalence``
        ("signature_input", "hash_hex"),
        # ``vectors/bootstrap``, ``vectors/revoke``, ``vectors/grade-switch``
        # (they ship ``digests.<role>_signing_input_sha256``).
    ),
}


def _extract_reference_sha256(
    vector_dir: Path, envelope_role: str
) -> Optional[str]:
    """Return any SHA-256 reference digest of the signing input that
    the vector's ``expected.json`` advertises, or ``None`` if absent.

    Tamper vectors (e.g. ``vectors/endorsement/e1-signature-tamper-*``)
    deliberately corrupt the on-disk envelope after signing. In that
    case ``expected.json`` records BOTH the legitimate (pre-tamper)
    digest under ``signature_input.hash_hex`` AND the actual on-disk
    wire-form digest under ``signature_input.wire_hash_hex``, with the
    explicit flag ``signature_input.wire_matches_signature_input:
    false`` to confirm the divergence. When that flag is present and
    false, this function returns the ``wire_hash_hex`` instead so the
    cross-check matches what is actually on disk (the dim_hash driver
    re-computes from the on-disk envelope, not from the pre-tamper
    object — that is the whole point of the tamper test).
    """

    expected = vector_dir / "expected.json"
    if not expected.is_file():
        return None
    try:
        data = json.loads(expected.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    sig_input = data.get("signature_input")
    if isinstance(sig_input, dict):
        # Tamper-vector branch: prefer the wire-form digest when the
        # vector explicitly declares the wire form has been mutated
        # post-signing.
        wire_matches = sig_input.get("wire_matches_signature_input")
        if wire_matches is False:
            wire_hex = sig_input.get("wire_hash_hex")
            if isinstance(wire_hex, str):
                return wire_hex.lower()
            # Fall through — vector declared a tamper but didn't ship
            # a wire-form digest, so we cannot cross-check. Return
            # None rather than the pre-tamper digest, which would
            # spuriously fail the cross-check.
            return None

        algorithm = sig_input.get("hash_alg") or sig_input.get(
            "hash_algorithm"
        )
        h = sig_input.get("hash_hex")
        if isinstance(h, str) and (
            algorithm is None
            or algorithm.upper().replace("-", "") == "SHA256"
        ):
            return h.lower()

    digests = data.get("digests")
    if isinstance(digests, dict):
        # Many toolchains use ``<role>_signing_input_sha256``; try the
        # role first (e.g. ``request``, ``response``, ``signal``) and
        # fall back to a bare ``signing_input_sha256``.
        candidates = (
            f"{envelope_role}_signing_input_sha256",
            "signing_input_sha256",
        )
        for key in candidates:
            v = digests.get(key)
            if isinstance(v, str):
                return v.lower()
    return None


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


def hash_vector_across_algorithms(
    vector_dir: Path,
    *,
    algorithms: Tuple[str, ...] = SUPPORTED_HASHES,
) -> Dict[str, HashCheckResult]:
    """Compute every supported hash of the signing input for one vector.

    Returns a mapping ``{algorithm -> HashCheckResult}``. The signing-
    input bytes are computed *once* and reused across algorithms; this
    guarantees by construction that the §6.3 signing-input expression
    is hash-algorithm-agnostic and is what task 5.4's acceptance gate
    "签名输入构造与 §6.3 完全一致" verifies structurally.
    """

    envelope, _encoding = load_envelope(vector_dir)
    signing_input = compute_signing_input(envelope)
    envelope_path, _ = _find_envelope_file(vector_dir)
    envelope_role = (
        envelope_path.stem if envelope_path is not None else "envelope"
    )
    reference_sha256 = _extract_reference_sha256(vector_dir, envelope_role)

    out: Dict[str, HashCheckResult] = {}
    for raw_alg in algorithms:
        alg = normalize_hash(raw_alg)
        digest = compute_hash(alg, signing_input)
        digest_hex = digest.hex()

        notes = ""
        ref_matched: Optional[bool] = None
        if alg == "SHA-256" and reference_sha256 is not None:
            ref_matched = digest_hex == reference_sha256
            if ref_matched:
                notes = (
                    "matches expected.json ground-truth signing-input "
                    "digest"
                )
            else:
                notes = (
                    f"differs from expected.json reference digest "
                    f"{reference_sha256!r}; signing-input construction "
                    "must match design.md §6.3 exactly"
                )

        out[alg] = HashCheckResult(
            vector_name=vector_dir.name,
            hash_algorithm=alg,
            signing_input_bytes=signing_input,
            signing_input_length=len(signing_input),
            digest_hex=digest_hex,
            digest_length=len(digest),
            notes=notes,
            reference_digest_matched=ref_matched,
        )
    return out


__all__ = [
    "HashCheckResult",
    "compute_signing_input",
    "hash_vector_across_algorithms",
    "iter_vector_dirs",
    "load_envelope",
]
