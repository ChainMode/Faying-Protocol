"""Encoding-dimension driver — exercises Requirement 10.1 / 10.2 / 10.3 on
every CBOR ↔ JSON pair shipped by task 3.x.

For one pair the driver enforces the following invariants. Each one is a
direct lift of a single EARS clause:

I-E-1  *Bidirectional decode succeeds.*
       ``cbor2.loads(message.cbor)`` and ``json.loads(message.json)`` must
       both succeed without exception. (Requirement 10.1.3)

I-E-2  *Field semantics agree.*
       After lifting JSON-side binary markers (``$bytes`` / ``$b64`` /
       ``$b64u``) and tag-0 markers to their CBOR-native equivalents, the
       two trees are deeply equal under CBOR semantics (datetime ↔
       ``CBORTag(0, str)`` is treated as equal). (Requirement 10.1.3)

I-E-3  *Deterministic-CBOR signature input is bit-for-bit identical.*
       ``Det-CBOR(envelope_without_signature)`` derived from the CBOR side
       equals the same expression derived from the JSON-normalized side.
       (Requirement 10.2.1, Requirement 10.2.4)

I-E-4  *SHA-256 hash of the signature input matches both sides.*
       The ``signature_input.hash_hex`` (or ``digests.*_signing_input_sha256``)
       advertised in ``expected.json``, when present, equals
       ``SHA-256( Det-CBOR(envelope_without_signature) )`` derived from
       *each* encoding. (Requirement 10.2.4)

I-E-5  *Signature verification yields the same outcome on both encodings.*
       Where the vector ships a real Ed25519 signature (i.e. the bundle
       advertises ``alg = "Ed25519"`` and pubkey/sig look like 32/64-byte
       blobs rather than placeholder ``0x11…`` patterns), the verification
       result is the same when fed the CBOR-derived signature input vs.
       the JSON-derived signature input. (Requirement 10.1.3)

I-E-6  *JSON Content-Type is the registered media type.*
       The driver explicitly asserts the JSON wire form has Content-Type
       in ``ACCEPTED_JSON_CONTENT_TYPES`` — that is, either the modern
       ``application/faying-protocol+json`` (design.md §5.1, requirements
       10.1.2) or the legacy ``application/fap+json`` referenced by
       tasks 3.7 / 5.2 which the conformance suite still recognises as a
       compatibility alias. (Requirement 10.1.2)

I-E-7  *CBOR file is itself canonical.*
       Re-encoding the CBOR-decoded object with deterministic encoding
       reproduces the on-disk bytes. Vectors that are *not* canonical can
       still pass I-E-3 (they exercise the equivalence at the *signature
       input* layer), so this check is reported as INFO rather than FAIL
       — see ``CanonicalityCheck`` below.

The driver returns one ``EncodingCheckResult`` per pair; success is the
absence of any FAIL-level finding. ``run_all`` aggregates results across
the corpus.

Reference / Not Normative.
"""

from __future__ import annotations

import dataclasses as _dc
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, List, Tuple

import cbor2

from .normalize import (
    canonical_cbor,
    first_difference,
    json_to_cbor_shape,
    short_repr,
    strip_signature,
)
from .vectors_index import (
    EncodingPair,
    discover_pairs,
    load_expected_signature_hashes,
)

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

#: Accepted ``Content-Type`` values for the JSON wire form.
#:
#: design.md §5.1 mandates ``application/faying-protocol+json``; tasks 3.7 and
#: 5.2 (and ``vectors/encoding-equivalence/index.json`` / ``expected.json``)
#: also reference ``application/fap+json`` as the legacy alias. Both are
#: accepted by the conformance suite — but the driver records *which* one was
#: observed so any mismatch with the tasks' canonical form is loud.
ACCEPTED_JSON_CONTENT_TYPES: Tuple[str, ...] = (
    "application/faying-protocol+json",
    "application/fap+json",
)

#: The *normative* Content-Type per requirements.md §10.1.2 / design.md §5.1.
#: ``application/fap+json`` is a recognised alias but no longer normative.
NORMATIVE_JSON_CONTENT_TYPE: str = "application/faying-protocol+json"


# ---------------------------------------------------------------------------
# Result records
# ---------------------------------------------------------------------------


@_dc.dataclass(frozen=True)
class Finding:
    """A single observation about a pair.

    ``level`` is one of ``"FAIL"`` (drives the suite to a non-zero exit) or
    ``"INFO"`` (advisory; surfaces in reports without failing the run).
    """

    level: str
    code: str
    message: str


@_dc.dataclass
class EncodingCheckResult:
    """Outcome of running every invariant against a single pair."""

    pair: EncodingPair
    findings: List[Finding] = _dc.field(default_factory=list)

    # Captured artefacts for downstream auditing.
    signature_input_hash_hex: str | None = None
    json_content_type: str | None = None
    signature_alg: str | None = None
    signature_verify_outcome: str | None = None  # "ok" / "invalid" / "skipped"

    @property
    def passed(self) -> bool:
        return not any(f.level == "FAIL" for f in self.findings)

    def add_fail(self, code: str, message: str) -> None:
        self.findings.append(Finding("FAIL", code, message))

    def add_info(self, code: str, message: str) -> None:
        self.findings.append(Finding("INFO", code, message))


# ---------------------------------------------------------------------------
# JSON Content-Type extraction
# ---------------------------------------------------------------------------


def _expected_json_content_type(case_dir: Path) -> str | None:
    """Read ``expected.json`` and return any declared JSON Content-Type."""
    expected = case_dir / "expected.json"
    if not expected.is_file():
        return None
    try:
        data = json.loads(expected.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    encodings = data.get("encodings")
    if not isinstance(encodings, dict):
        return None
    json_block = encodings.get("json")
    if not isinstance(json_block, dict):
        return None
    ct = json_block.get("content_type")
    return ct if isinstance(ct, str) else None


def _binary_paths_from_expected(case_dir: Path) -> Tuple[str, ...]:
    """Read the ``binary_field_paths`` array used by encoding-equivalence."""
    expected = case_dir / "expected.json"
    if not expected.is_file():
        return ()
    try:
        data = json.loads(expected.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    paths = data.get("binary_field_paths")
    if not isinstance(paths, list):
        return ()
    return tuple(p for p in paths if isinstance(p, str))


# ---------------------------------------------------------------------------
# Signature reading and verification
# ---------------------------------------------------------------------------


def _is_placeholder_byte_pattern(b: bytes) -> bool:
    """Detect the ``0x11…`` / ``0x22…`` style placeholder signatures used by
    several negative / illustrative vectors (e.g. errors/1001).

    These vectors exist to exercise envelope shape, not crypto; we therefore
    skip the Ed25519 verification step on them rather than emit spurious
    FAIL findings."""
    if len(b) == 0:
        return True
    return len(set(b)) == 1


def _read_outer_signature(envelope: Any) -> tuple[str | None, bytes | None, bytes | None]:
    """Pull ``(alg, pubkey_bytes, sig_bytes)`` out of a top-level signature.

    Supports both the ``{pubkey: bytes, sig: bytes}`` and
    ``{pubkey_hex: str, sig_hex: str}`` conventions used in the corpus.
    Returns ``(None, None, None)`` if no signature is recoverable.
    """
    if not isinstance(envelope, dict):
        return None, None, None
    bundle = envelope.get("signature")
    if not isinstance(bundle, dict):
        return None, None, None

    alg = bundle.get("alg")
    if not isinstance(alg, str):
        alg = None

    pub = bundle.get("pubkey")
    sig = bundle.get("sig")
    if isinstance(pub, bytes) and isinstance(sig, bytes):
        return alg, pub, sig

    pub_hex = bundle.get("pubkey_hex")
    sig_hex = bundle.get("sig_hex")
    if isinstance(pub_hex, str) and isinstance(sig_hex, str):
        try:
            return alg, bytes.fromhex(pub_hex), bytes.fromhex(sig_hex)
        except ValueError:
            return alg, None, None

    return alg, None, None


def _verify_ed25519(pubkey: bytes, sig: bytes, message: bytes) -> bool:
    """Return ``True`` iff ``sig`` is a valid Ed25519 signature of
    ``message`` under ``pubkey``.

    All non-cryptographic failure modes (wrong length, malformed pubkey)
    are folded into a ``False`` return — the caller surfaces them as a
    failed verification, exactly as a conformant verifier would."""
    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric.ed25519 import (
            Ed25519PublicKey,
        )
    except ImportError:
        return False
    if len(pubkey) != 32 or len(sig) != 64:
        return False
    try:
        pk = Ed25519PublicKey.from_public_bytes(pubkey)
        pk.verify(sig, message)
        return True
    except InvalidSignature:
        return False
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Per-pair runner
# ---------------------------------------------------------------------------


def _canonical_via_json_shape(
    cbor_bytes: bytes,
    *,
    strip_top_signature: bool,
) -> bytes:
    """Re-encode the on-disk CBOR after stripping the top-level ``signature``
    field, *without* round-tripping any tag-0 timestamp through
    ``datetime``.

    Currently unused by the per-pair driver (which works with the decoded
    object directly), but exposed for downstream tools that want a single
    canonical-CBOR byte stream from raw on-disk bytes without dragging in
    the rest of the driver. Kept here so it lives next to the
    ``_datetimes_to_tag0`` formatting it depends on.
    """
    obj = cbor2.loads(cbor_bytes)
    if strip_top_signature and isinstance(obj, dict):
        obj = {k: v for k, v in obj.items() if k != "signature"}
    obj = _datetimes_to_tag0(obj)
    return canonical_cbor(obj)


def _datetimes_to_tag0(obj: Any) -> Any:
    """Replace every ``datetime`` leaf with ``CBORTag(0, RFC3339-string)``.

    The string format mirrors what the corpus' generators produce:

      * ``...HH:MM:SSZ`` when ``microsecond == 0``;
      * ``...HH:MM:SS.fffZ`` when the microsecond count is divisible by
        1000 (i.e. millisecond precision);
      * ``...HH:MM:SS.ffffffZ`` otherwise (fully precise — the corpus does
        not currently emit this form, but we cover it for completeness).
    """
    import datetime as _dt

    if isinstance(obj, _dt.datetime):
        if obj.tzinfo is None:
            obj = obj.replace(tzinfo=_dt.timezone.utc)
        else:
            obj = obj.astimezone(_dt.timezone.utc)
        if obj.microsecond == 0:
            s = obj.strftime("%Y-%m-%dT%H:%M:%SZ")
        elif obj.microsecond % 1000 == 0:
            s = obj.strftime("%Y-%m-%dT%H:%M:%S") + f".{obj.microsecond // 1000:03d}Z"
        else:
            s = obj.strftime("%Y-%m-%dT%H:%M:%S") + f".{obj.microsecond:06d}Z"
        return cbor2.CBORTag(0, s)
    if isinstance(obj, dict):
        return {k: _datetimes_to_tag0(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_datetimes_to_tag0(v) for v in obj]
    if isinstance(obj, cbor2.CBORTag):
        return cbor2.CBORTag(obj.tag, _datetimes_to_tag0(obj.value))
    return obj


def _peel_wrapper(jo: Any, key: str | None) -> Any:
    if key is None:
        return jo
    if not isinstance(jo, dict) or key not in jo:
        raise ValueError(
            f"JSON wrapper key {key!r} not found at top level"
        )
    return jo[key]


def run_pair(pair: EncodingPair) -> EncodingCheckResult:
    """Apply I-E-1 .. I-E-7 to a single pair and return the result.

    Behaviour by side count:

    * **Two-sided** (CBOR + JSON present): all seven invariants apply.
    * **CBOR-only**: parse CBOR, exercise I-E-7 (canonicality), record an
      INFO that cross-encoding invariants are not exercisable.
    * **JSON-only**: parse JSON, lift markers, encode canonical CBOR for
      its own internal sanity. We still record an INFO since the CBOR
      sibling is absent.

    A pair therefore *fails* only when an invariant that *applies* to it is
    violated; a missing sibling alone never causes failure.
    """
    result = EncodingCheckResult(pair=pair)

    have_cbor = pair.has_cbor
    have_json = pair.has_json
    if not have_cbor and not have_json:
        result.add_fail(
            "E1.empty",
            f"neither {pair.cbor_path.name} nor {pair.json_path.name} found",
        )
        return result

    # ------------------------------------------------------------------
    # CBOR side: read + decode (when present)
    # ------------------------------------------------------------------
    cbor_bytes: bytes | None = None
    cbor_obj: Any = None
    if have_cbor:
        try:
            cbor_bytes = pair.cbor_path.read_bytes()
        except OSError as exc:
            result.add_fail("E1.cbor.read", f"cannot read {pair.cbor_path}: {exc}")
            have_cbor = False
        else:
            try:
                # The CBOR file is the authoritative reference. We decode it
                # for *structural* checks (signature stripping, content
                # traversal) but we never re-encode datetimes inside it for
                # canonical comparison — see ``_datetimes_to_tag0``.
                cbor_obj = cbor2.loads(cbor_bytes)
            except Exception as exc:
                result.add_fail(
                    "E1.cbor.decode", f"cbor2.loads failed: {exc!r}"
                )
                have_cbor = False

    # ------------------------------------------------------------------
    # JSON side: read + decode + normalize (when present)
    # ------------------------------------------------------------------
    json_obj: Any = None
    binary_paths = _binary_paths_from_expected(
        (pair.cbor_path if have_cbor else pair.json_path).parent
    )
    if have_json:
        try:
            json_text = pair.json_path.read_text("utf-8")
        except OSError as exc:
            result.add_fail("E1.json.read", f"cannot read {pair.json_path}: {exc}")
            have_json = False
        else:
            try:
                json_raw = json.loads(json_text)
            except json.JSONDecodeError as exc:
                result.add_fail("E1.json.decode", f"json.loads failed: {exc}")
                have_json = False
            else:
                try:
                    json_payload = _peel_wrapper(
                        json_raw, pair.json_wrapper_key
                    )
                    json_obj = json_to_cbor_shape(
                        json_payload, binary_paths=binary_paths
                    )
                except Exception as exc:
                    result.add_fail(
                        "E1.json.normalize",
                        f"failed to lift JSON binary/tag markers: {exc!r}",
                    )
                    have_json = False

    # ------------------------------------------------------------------
    # I-E-2: deep semantic equality (only when both sides present)
    # ------------------------------------------------------------------
    cbor_obj_norm: Any = None
    if have_cbor and cbor_obj is not None:
        cbor_obj_norm = _datetimes_to_tag0(cbor_obj)
    if have_cbor and have_json and cbor_obj_norm is not None and json_obj is not None:
        diff = first_difference(cbor_obj_norm, json_obj)
        if diff is not None:
            result.add_fail(
                "E2.semantic",
                f"CBOR ≠ JSON after lift: {diff}",
            )
    elif not (have_cbor and have_json):
        result.add_info(
            "E0.one_sided",
            "only one wire form present; cross-encoding invariants "
            "(I-E-2/3/4/5) are not exercisable for this pair",
        )

    # ------------------------------------------------------------------
    # I-E-3: deterministic CBOR signature input identity
    # ------------------------------------------------------------------
    cbor_sig_input: bytes | None = None
    json_sig_input: bytes | None = None
    if have_cbor and cbor_obj_norm is not None:
        try:
            cbor_sig_input = canonical_cbor(strip_signature(cbor_obj_norm))
        except Exception as exc:
            result.add_fail(
                "E3.cbor.det_encode", f"Det-CBOR(cbor−sig) failed: {exc!r}"
            )
    if have_json and json_obj is not None:
        try:
            json_sig_input = canonical_cbor(strip_signature(json_obj))
        except Exception as exc:
            result.add_fail(
                "E3.json.det_encode", f"Det-CBOR(json−sig) failed: {exc!r}"
            )

    if cbor_sig_input is not None and json_sig_input is not None:
        if cbor_sig_input != json_sig_input:
            result.add_fail(
                "E3.sig_input.diff",
                "Det-CBOR(envelope−signature) differs across encodings "
                f"(cbor={len(cbor_sig_input)}B, json={len(json_sig_input)}B)",
            )

    # Record the SHA-256 (any side will do — they're equal when I-E-3 holds).
    sig_input_for_hash = cbor_sig_input or json_sig_input
    if sig_input_for_hash is not None:
        result.signature_input_hash_hex = hashlib.sha256(sig_input_for_hash).hexdigest()

    # ------------------------------------------------------------------
    # I-E-4: hash matches expected.json (when available)
    # ------------------------------------------------------------------
    case_dir = (pair.cbor_path if have_cbor else pair.json_path).parent
    expected_hashes = load_expected_signature_hashes(case_dir)
    if expected_hashes and result.signature_input_hash_hex is not None:
        # Match strictly on this pair's role; never fall back to a different
        # role's hash. The corpus often advertises only ``request_*`` digests,
        # in which case the response message has no expected hash to compare
        # to and we leave I-E-4 uninformed (which is fine — I-E-3 already
        # proves the *cross-encoding* identity, and I-E-4 is an extra check
        # against the upstream task 3.x ground truth).
        candidate = expected_hashes.get(pair.role)
        if candidate is not None and candidate != result.signature_input_hash_hex:
            result.add_fail(
                "E4.hash.expected",
                f"SHA-256(signature_input) {result.signature_input_hash_hex} "
                f"!= expected.json {candidate}",
            )

    # ------------------------------------------------------------------
    # I-E-5: signature verification outcome agrees across encodings
    # ------------------------------------------------------------------
    sig_holder = cbor_obj if have_cbor else json_obj
    alg, pub, sig = _read_outer_signature(sig_holder)
    result.signature_alg = alg
    if alg == "Ed25519" and pub is not None and sig is not None:
        if (
            _is_placeholder_byte_pattern(pub)
            or _is_placeholder_byte_pattern(sig)
            or len(pub) != 32
            or len(sig) != 64
        ):
            result.signature_verify_outcome = "skipped"
            result.add_info(
                "E5.skipped",
                f"signature looks like a placeholder "
                f"(pubkey {len(pub)}B, sig {len(sig)}B); "
                "cryptographic verify skipped",
            )
        elif cbor_sig_input is not None and json_sig_input is not None:
            ok_cbor = _verify_ed25519(pub, sig, cbor_sig_input)
            ok_json = _verify_ed25519(pub, sig, json_sig_input)
            if ok_cbor != ok_json:
                result.add_fail(
                    "E5.verify.diverge",
                    f"Ed25519 verify outcome differs across encodings "
                    f"(cbor={ok_cbor}, json={ok_json})",
                )
            result.signature_verify_outcome = "ok" if ok_cbor else "invalid"
            if not ok_cbor and not ok_json:
                result.add_info(
                    "E5.invalid",
                    "Ed25519 verification fails on both encodings "
                    "(consistent rejection across CBOR/JSON)",
                )
        elif cbor_sig_input is not None or json_sig_input is not None:
            # One-sided pair — verify the available side as a self-test.
            sig_input = cbor_sig_input if cbor_sig_input is not None else json_sig_input
            ok = _verify_ed25519(pub, sig, sig_input)
            result.signature_verify_outcome = "ok" if ok else "invalid"
            if not ok:
                result.add_info(
                    "E5.invalid",
                    "Ed25519 verification fails on the only available encoding",
                )
        else:
            result.signature_verify_outcome = "skipped"
    else:
        result.signature_verify_outcome = "skipped"

    # ------------------------------------------------------------------
    # I-E-6: Content-Type assertion
    # ------------------------------------------------------------------
    declared_ct = _expected_json_content_type(case_dir)
    if declared_ct is not None:
        result.json_content_type = declared_ct
        if declared_ct not in ACCEPTED_JSON_CONTENT_TYPES:
            result.add_fail(
                "E6.content_type",
                f"JSON Content-Type {declared_ct!r} is not in the accepted "
                f"set {list(ACCEPTED_JSON_CONTENT_TYPES)}",
            )
        elif declared_ct != NORMATIVE_JSON_CONTENT_TYPE:
            result.add_info(
                "E6.content_type.legacy",
                f"JSON Content-Type {declared_ct!r} is the legacy alias; "
                f"normative form is {NORMATIVE_JSON_CONTENT_TYPE!r}",
            )

    # ------------------------------------------------------------------
    # I-E-7: CBOR canonicality (advisory)
    # ------------------------------------------------------------------
    if have_cbor and cbor_obj is not None and cbor_bytes is not None:
        try:
            redumped = canonical_cbor(_datetimes_to_tag0(cbor_obj))
            if redumped != cbor_bytes:
                result.add_info(
                    "E7.cbor.noncanonical",
                    "CBOR file decode→encode does not reproduce on-disk "
                    "bytes; this is allowed but flagged for follow-up",
                )
        except Exception as exc:
            result.add_info(
                "E7.cbor.encode",
                f"could not re-encode CBOR for canonicality check: {exc!r}",
            )

    return result


# ---------------------------------------------------------------------------
# Suite runner
# ---------------------------------------------------------------------------


@_dc.dataclass
class SuiteSummary:
    """Aggregate result of running ``run_all``."""

    total: int
    passed: int
    failed: int
    one_sided: int
    """How many pairs ship only one wire form."""
    two_sided: int
    """How many pairs ship both CBOR and JSON."""
    info_count: int
    fail_codes: List[str]
    results: List[EncodingCheckResult]
    accepted_content_types: Tuple[str, ...] = ACCEPTED_JSON_CONTENT_TYPES
    normative_content_type: str = NORMATIVE_JSON_CONTENT_TYPE

    @property
    def ok(self) -> bool:
        return self.failed == 0


def run_all(*, pairs: Iterable[EncodingPair] | None = None) -> SuiteSummary:
    """Discover or take a list of pairs, run the per-pair checks, and
    aggregate."""
    if pairs is None:
        pairs = discover_pairs()
    pair_list = list(pairs)
    results = [run_pair(p) for p in pair_list]

    failed = sum(1 for r in results if not r.passed)
    info = sum(
        sum(1 for f in r.findings if f.level == "INFO") for r in results
    )
    two_sided = sum(1 for p in pair_list if p.is_two_sided)
    one_sided = len(pair_list) - two_sided
    fail_codes = sorted(
        {f.code for r in results for f in r.findings if f.level == "FAIL"}
    )
    return SuiteSummary(
        total=len(results),
        passed=len(results) - failed,
        failed=failed,
        one_sided=one_sided,
        two_sided=two_sided,
        info_count=info,
        fail_codes=fail_codes,
        results=results,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _format_text(summary: SuiteSummary, *, verbose: bool = False) -> str:
    lines: list[str] = []
    lines.append(
        "Faying Protocol/1.0 — Conformance dim_encoding (task 5.2)"
    )
    lines.append(f"  accepted JSON Content-Type(s): {list(summary.accepted_content_types)}")
    lines.append(f"  normative JSON Content-Type  : {summary.normative_content_type!r}")
    lines.append(f"  total pairs        : {summary.total}")
    lines.append(f"  two-sided (cbor+json): {summary.two_sided}")
    lines.append(f"  one-sided          : {summary.one_sided}")
    lines.append(f"  passed             : {summary.passed}")
    lines.append(f"  failed             : {summary.failed}")
    lines.append(f"  info findings      : {summary.info_count}")
    if summary.fail_codes:
        lines.append("  fail codes seen    : " + ", ".join(summary.fail_codes))
    lines.append("")

    for r in summary.results:
        status = "PASS" if r.passed else "FAIL"
        rel = r.pair.relative()
        lines.append(f"  [{status}] {r.pair.vector_id:60s}  ({rel})")
        if verbose or not r.passed:
            for f in r.findings:
                lines.append(f"        {f.level} {f.code}: {f.message}")
    return "\n".join(lines)


def _format_json(summary: SuiteSummary) -> str:
    payload = {
        "accepted_content_types": list(summary.accepted_content_types),
        "normative_content_type": summary.normative_content_type,
        "total": summary.total,
        "two_sided": summary.two_sided,
        "one_sided": summary.one_sided,
        "passed": summary.passed,
        "failed": summary.failed,
        "info_count": summary.info_count,
        "fail_codes": summary.fail_codes,
        "results": [
            {
                "vector_id": r.pair.vector_id,
                "group": r.pair.group,
                "case": r.pair.case,
                "role": r.pair.role,
                "cbor": str(r.pair.cbor_path),
                "json": str(r.pair.json_path),
                "passed": r.passed,
                "signature_input_hash_hex": r.signature_input_hash_hex,
                "signature_alg": r.signature_alg,
                "signature_verify_outcome": r.signature_verify_outcome,
                "json_content_type": r.json_content_type,
                "findings": [
                    {"level": f.level, "code": f.code, "message": f.message}
                    for f in r.findings
                ],
            }
            for r in summary.results
        ],
    }
    return json.dumps(payload, indent=2, ensure_ascii=False)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="conformance/dim_encoding/driver.py",
        description=(
            "Run the encoding-dimension (CBOR ↔ JSON) conformance "
            "checks across every CBOR/JSON pair in vectors/."
        ),
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="output format (default: text)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="show all findings, not just failures",
    )
    args = parser.parse_args(argv)

    summary = run_all()
    if args.format == "json":
        print(_format_json(summary))
    else:
        print(_format_text(summary, verbose=args.verbose))
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
