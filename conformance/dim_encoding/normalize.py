"""Normalization helpers — JSON wire-shape ⟷ CBOR-native shape.

The Faying Protocol/1.0 vector corpus uses three different JSON conventions
for binary fields and timestamps, all valid per design.md §5.1 ("identical
field semantics" between CBOR and JSON):

================================================================================
| group                                                                  | binary marker     | timestamp marker          |
================================================================================
| bootstrap, delegate, grade-switch, revoke, presence                  | ``{"$bytes":  b64u}`` | ``{"$tag": 0, "$value": str}`` |
| endorsement                                                          | ``{"$bytes":  hex}``  | ``{"$tag": 0, "value":  str}`` |
| faying-request                                                       | ``{"$b64":    b64}``   | bare RFC 3339 ``str``           |
| disclosure                                                           | ``{"$b64u":   b64u}``  | bare RFC 3339 ``str``           |
| encoding-equivalence                                                 | ``{"$bytes":  b64u}`` | bare RFC 3339 ``str``           |
| errors                                                               | bare ``..._hex`` keys (no marker) | bare RFC 3339 ``str``           |
================================================================================

This module collapses every shape into a single CBOR-native shape:

  * ``bytes`` instead of any binary marker
  * ``cbor2.CBORTag(0, str)`` (or ``datetime``) wherever the CBOR side carries
    one; bare RFC 3339 strings are left alone.

All five vector groups can then be compared with plain ``==`` against the
``cbor2.loads()`` of their CBOR sibling. The only group-specific knob is the
binary marker decoder: the CBOR side decides whether ``$bytes`` text is hex
or base64url (we only ever see one form per file, so detection is safe).

Reference / Not Normative.
"""

from __future__ import annotations

import base64
import datetime as _dt
import re
from typing import Any, Iterable, Mapping

import cbor2

# ---------------------------------------------------------------------------
# Public constants
# ---------------------------------------------------------------------------

# Binary markers we recognise in the JSON wire form. Order matters because
# ``$bytes`` is used by both hex- and b64u-encoded bytes; the value content
# disambiguates.
_BINARY_MARKERS = ("$bytes", "$b64u", "$b64")
# Timestamp marker emitted by some vectors to convey CBOR tag 0.
_TAG_MARKER_KEYS_VALUE = ("$tag", "$value")  # bootstrap / delegate / etc.
_TAG_MARKER_KEYS_VALUE2 = ("$tag", "value")   # endorsement variant


# ---------------------------------------------------------------------------
# Marker detection
# ---------------------------------------------------------------------------

_HEX_RE = re.compile(r"^[0-9a-fA-F]*$")


def detect_binary_marker(node: Mapping[str, Any]) -> str | None:
    """Return the marker key (e.g. ``"$bytes"``) iff ``node`` is exactly one of
    the recognised binary markers; otherwise ``None``.

    A marker dict has **only** the marker key — any sibling fields disqualify
    it (they would represent a regular object that happens to use a reserved
    name as a child key, which the corpus never does).
    """
    if not isinstance(node, dict) or len(node) != 1:
        return None
    only = next(iter(node))
    return only if only in _BINARY_MARKERS else None


def _is_tag0_marker(node: Mapping[str, Any]) -> tuple[bool, str | None]:
    """Recognise both observed CBOR-tag-0 marker shapes.

    Returns ``(is_marker, value_string_or_none)``.
    """
    if not isinstance(node, dict):
        return False, None
    keys = set(node.keys())
    if keys == {"$tag", "$value"} and node["$tag"] == 0:
        v = node["$value"]
        return (True, v) if isinstance(v, str) else (False, None)
    if keys == {"$tag", "value"} and node["$tag"] == 0:
        v = node["value"]
        return (True, v) if isinstance(v, str) else (False, None)
    return False, None


# ---------------------------------------------------------------------------
# Bytes decoding
# ---------------------------------------------------------------------------


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _b64_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.b64decode(s + pad)


def _decode_bytes_marker(marker: str, value: str) -> bytes:
    """Decode the inner string of a binary marker into raw bytes.

    ``$bytes`` is overloaded across the corpus:
      * endorsement vectors store **hex**;
      * everywhere else stores **base64url-no-padding**.

    We disambiguate purely on the value's character set: a string that is
    valid hex (all ``[0-9a-fA-F]`` and even length) is treated as hex,
    otherwise as base64url. The corpus never produces a value that satisfies
    both, so this decision is unambiguous in practice.

    ``$b64`` always means standard base64 (RFC 4648 §4); ``$b64u`` always
    means base64url (RFC 4648 §5). Both are decoded permissively (extra
    padding tolerated).
    """
    if marker == "$bytes":
        if _HEX_RE.fullmatch(value) and len(value) % 2 == 0 and len(value) >= 2:
            return bytes.fromhex(value)
        return _b64url_decode(value)
    if marker == "$b64u":
        return _b64url_decode(value)
    if marker == "$b64":
        return _b64_decode(value)
    raise ValueError(f"unknown binary marker {marker!r}")


# ---------------------------------------------------------------------------
# JSON tree → CBOR-native tree
# ---------------------------------------------------------------------------


def json_to_cbor_shape(
    obj: Any,
    *,
    binary_paths: Iterable[str] = (),
) -> Any:
    """Recursively convert a JSON-decoded tree into the CBOR-native shape.

    Specifically:

      * dicts with **exactly one** binary marker key are replaced by raw
        ``bytes``;
      * dicts with the CBOR-tag-0 marker shape are replaced by a
        ``cbor2.CBORTag(0, str)`` so that ``cbor2.dumps(..., canonical=True)``
        on the result matches a CBOR-side ``datetime`` (both serialise to
        the same canonical bytes);
      * any **bare string** sitting at a dotted path enumerated in
        ``binary_paths`` is base64url-decoded into raw ``bytes``. This is
        the encoding-equivalence vectors' convention, where binary fields
        ride as plain strings and the schema is declared out-of-band in
        ``expected.json``;
      * everything else is recursively walked.

    Encoding-equivalence vectors drop the tag-0 marker entirely and carry
    bare RFC 3339 strings; we leave those alone so they continue to compare
    equal to the CBOR side (which also stores them as ``str``).
    """
    binary_path_set: set[tuple[str, ...]] = {
        tuple(p.split(".")) for p in binary_paths
    }
    return _walk_to_cbor_shape(obj, (), binary_path_set)


def _walk_to_cbor_shape(
    obj: Any,
    path: tuple[str, ...],
    binary_path_set: set[tuple[str, ...]],
) -> Any:
    if isinstance(obj, dict):
        marker = detect_binary_marker(obj)
        if marker is not None:
            inner = obj[marker]
            if not isinstance(inner, str):
                raise ValueError(
                    f"binary marker {marker!r} at path {list(path)} expects "
                    f"str payload, got {type(inner).__name__}"
                )
            return _decode_bytes_marker(marker, inner)
        is_tag, ts = _is_tag0_marker(obj)
        if is_tag:
            return cbor2.CBORTag(0, ts)
        return {
            k: _walk_to_cbor_shape(v, path + (k,), binary_path_set)
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [
            _walk_to_cbor_shape(v, path, binary_path_set)
            for v in obj
        ]
    if isinstance(obj, str) and path in binary_path_set:
        # Path-keyed binary convention (encoding-equivalence vectors).
        # Strings here are always base64url-no-padding per
        # vectors/encoding-equivalence/index.json.
        return _b64url_decode(obj)
    return obj


# ---------------------------------------------------------------------------
# Canonical CBOR helpers
# ---------------------------------------------------------------------------


def canonical_cbor(obj: Any) -> bytes:
    """Encode ``obj`` per RFC 8949 §4.2.1 Core Deterministic Encoding.

    ``cbor2.dumps(..., canonical=True)`` performs key ordering by lexical
    bytes-order on the encoded keys, smallest-int integer encoding, and
    definite-length structures — i.e. the rules design.md §5.1 cites by
    reference for all signature inputs.
    """
    return cbor2.dumps(obj, canonical=True, datetime_as_timestamp=False)


# ---------------------------------------------------------------------------
# Signature stripping
# ---------------------------------------------------------------------------


def strip_signature(envelope: Any) -> Any:
    """Return ``envelope`` minus its top-level ``signature`` field.

    Per design.md §6.3 S2 the signature input is
    ``H(Det-CBOR(envelope_without_signature))``. Vectors that don't carry an
    envelope-shaped object (e.g. an endorsement Mandate that places the
    signature directly inside a ``mandate`` wrapper) are returned unchanged
    here; the wrapper-aware caller decides which subtree to strip.
    """
    if isinstance(envelope, dict) and "signature" in envelope:
        return {k: v for k, v in envelope.items() if k != "signature"}
    return envelope


# ---------------------------------------------------------------------------
# Diagnostic helpers (used by the driver to produce humane failure messages)
# ---------------------------------------------------------------------------


def short_repr(obj: Any, *, limit: int = 80) -> str:
    """Truncated ``repr`` for error messages."""
    s = repr(obj)
    return s if len(s) <= limit else s[: limit - 1] + "…"


def iter_paths(obj: Any, prefix: tuple[Any, ...] = ()) -> Iterable[tuple[tuple[Any, ...], Any]]:
    """Yield ``(path, leaf)`` for every leaf in ``obj``."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from iter_paths(v, prefix + (k,))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from iter_paths(v, prefix + (i,))
    else:
        yield prefix, obj


def first_difference(a: Any, b: Any, prefix: tuple[Any, ...] = ()) -> str | None:
    """Return a path-qualified description of the first deep ``a != b`` site,
    or ``None`` if the two trees compare equal.

    Used by the driver to show *where* CBOR and JSON disagree without
    dumping the entire envelope.

    The check is **CBOR-semantic** rather than Python-strict: ``datetime``
    on one side and ``CBORTag(0, str)`` on the other are treated as equal
    when they encode to the same RFC 8949 §4.2.1 canonical bytes (both
    encode to a tag-0 string per §3.4.1). This matters because cbor2
    decodes tag-0 to ``datetime`` by default while we lift JSON-side tag-0
    markers to ``CBORTag(0, str)``.
    """
    # CBOR-equivalence shortcut for tag-0 datetime vs CBORTag.
    if _tag0_equivalent(a, b):
        return None
    if type(a) is not type(b):
        # Allow datetime ⟷ CBORTag(0, str) cross-type via the shortcut above;
        # any other type mismatch is real.
        return f"path={list(prefix)} type({type(a).__name__}) != type({type(b).__name__})"
    if isinstance(a, dict):
        if a.keys() != b.keys():
            extra_a = sorted(set(a) - set(b))
            extra_b = sorted(set(b) - set(a))
            return (
                f"path={list(prefix)} key sets differ: "
                f"only_in_cbor={extra_a} only_in_json={extra_b}"
            )
        for k in a:
            d = first_difference(a[k], b[k], prefix + (k,))
            if d:
                return d
        return None
    if isinstance(a, list):
        if len(a) != len(b):
            return f"path={list(prefix)} list length {len(a)} != {len(b)}"
        for i, (x, y) in enumerate(zip(a, b)):
            d = first_difference(x, y, prefix + (i,))
            if d:
                return d
        return None
    if isinstance(a, cbor2.CBORTag):
        if a.tag != b.tag:
            return f"path={list(prefix)} CBORTag tag {a.tag} != {b.tag}"
        return first_difference(a.value, b.value, prefix + (f"<tag{a.tag}>",))
    if a != b:
        return f"path={list(prefix)} {short_repr(a)} != {short_repr(b)}"
    return None


def _tag0_equivalent(a: Any, b: Any) -> bool:
    """Return ``True`` when ``a`` and ``b`` both denote the same RFC 3339
    UTC instant via tag 0, regardless of which Python representation each
    side happens to use."""
    if isinstance(a, _dt.datetime) and isinstance(b, cbor2.CBORTag) and b.tag == 0:
        return _datetime_iso_z(a) == b.value
    if isinstance(b, _dt.datetime) and isinstance(a, cbor2.CBORTag) and a.tag == 0:
        return _datetime_iso_z(b) == a.value
    if isinstance(a, _dt.datetime) and isinstance(b, _dt.datetime):
        return a == b
    return False


def _datetime_iso_z(dt: _dt.datetime) -> str:
    """Format a UTC datetime as an RFC 3339 ``...Z`` string matching the
    forms the corpus uses on the JSON side."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    else:
        dt = dt.astimezone(_dt.timezone.utc)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
