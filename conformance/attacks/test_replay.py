"""Faying Protocol/1.0 — End-to-end replay-attack conformance test.

Covers ``tasks.md §6.1 重放攻击模拟``.

**Validates: Requirements 9.1** (抗重放)
**Property: P9** (anti-replay; design.md §12, §9.2)
**Design anchors**:

* design.md §9.2 (抗重放: ``(subject, nonce)`` seen-set, TTL =
  ``2 × max_message_lifetime``, ``E_REPLAY`` + 安全告警);
* design.md §EH.1 (rejection branch ``E_REPLAY`` 1009: 拒绝 + 安全告警 +
  立即 rotate 会话密钥);
* design.md §EH.3 (``E_REPLAY`` is must-push to HP view);
* requirements.md §9.1 (4 EARS clauses, see below).

Acceptance-criteria coverage (requirements.md §9.1, mirrored from
``tasks.md §6.1`` 验收 row):

* §9.1.1 — seen-set keyed by ``(subject, nonce)``; TTL ≥
  ``2 × max_message_lifetime``. Pinned by :data:`MAX_MESSAGE_LIFETIME_MS`
  and exercised by every test below.
* §9.1.2 — second consumption inside TTL ⇒ exactly one accepted, the
  rest ``E_REPLAY``. Tested by
  :func:`test_replay_within_ttl_returns_e_replay` and
  :func:`test_concurrent_replay_admits_exactly_one`.
* §9.1.3 — every captured envelope carries a 16-byte ``nonce`` and an
  ``issued_at`` timestamp. Pinned by :func:`_extract_envelope_keys`,
  asserted explicitly in :func:`test_captured_envelopes_are_well_formed`.
* §9.1.4 — ``E_REPLAY`` triggers a security-audit record AND a
  session-key rotate. Verified by
  :func:`test_replay_records_audit_and_rotates_session_key`.

Scope (per ``tasks.md §6.1`` 内容 row)

This module is the **end-to-end attack simulation**. It is the
counterpart to the property-based test :mod:`pbt.tests.test_p9_anti_replay`:
that test fuzzes generated envelopes through a model, this test feeds the
**captured legitimate envelopes** produced by tasks 3.1 (BOOTSTRAP),
3.3 (GRADE_SWITCH), 3.4 (DELEGATE), and 3.9 (FAYING_REQUEST) into the
same reference seen-set. The replay attacker is modelled by re-submitting
the *same byte-for-byte CBOR envelope* twice (and concurrently); the
expected behaviour is captured by the §9.2 seen-set contract.

Two replay groups are exercised explicitly per ``tasks.md §6.1``:

1. **TTL 内重放** (`delta_ms ≤ 2 × max_message_lifetime`) — second
   submission MUST return ``E_REPLAY``, MUST emit a security-audit
   record, and MUST trigger a session-key rotate.
2. **TTL 外同 nonce** (`delta_ms > 2 × max_message_lifetime`) — second
   submission is treated as a fresh envelope per design.md §9.2; both
   submissions accepted, no audit record, no rotate.

The reference :class:`SeenSet` is **Not Normative**; the authoritative
contract is design.md §9.2. Any divergence between this model and the
spec is a bug in this file.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import cbor2
import pytest


# ---------------------------------------------------------------------------
# Constants — kept in sync with design.md §9.2 / §EH.1 / requirements.md §9.1.
# ---------------------------------------------------------------------------
ACCEPTED: str = "accepted"
E_REPLAY: str = "E_REPLAY"  # protocol error code 1009 (design.md §5.4 / §EH.1)

# ``max_message_lifetime`` is a per-deployment protocol parameter
# (design.md §6.3 / §EH.1). Appendix B does not pin a single canonical
# value, so this conformance module fixes a reasonable 30 s default —
# anything smaller would still satisfy the ``≥ 2 × max_message_lifetime``
# TTL floor mandated by requirements.md §9.1.1. The value is mirrored
# verbatim from ``pbt/tests/test_p9_anti_replay.py`` so the property and
# end-to-end suites probe the same boundary.
MAX_MESSAGE_LIFETIME_MS: int = 30_000  # 30 s
SEEN_SET_TTL_MS: int = 2 * MAX_MESSAGE_LIFETIME_MS  # 60 s


# ---------------------------------------------------------------------------
# Repository layout (conformance/attacks/test_replay.py → repo root is 2 up).
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_VECTORS_DIR = _REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Reference model — Captured envelope view + Seen-set.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CapturedEnvelope:
    """A captured legitimate envelope from ``vectors/<family>/<case>/``.

    Only the fields the §9.2 seen-set inspects are surfaced here:

    * ``subject`` — envelope ``header.subject`` (FayID); part of the
      seen-set key.
    * ``nonce``   — envelope ``header.nonce`` (16 bytes per
      requirements.md §9.1.3); part of the seen-set key.
    * ``issued_at_ms`` — envelope ``header.issued_at`` normalised to a
      monotonic millisecond integer; the test driver advances its clock
      relative to this anchor.
    * ``raw_cbor`` — the *captured byte sequence* of the original
      envelope. The replay attacker re-submits this verbatim — the
      ``(subject, nonce)`` seen-set key MUST detect the collision even
      though the bytes are bit-for-bit identical to the legitimate
      first arrival.
    * ``family`` / ``case`` — diagnostics for failure messages and
      parametrize ids.
    """

    family: str
    case: str
    subject: str
    nonce: bytes
    issued_at_ms: int
    raw_cbor: bytes


@dataclass(frozen=True)
class AuditEvent:
    """Mirror of the §EH.1 security-audit record cut on ``E_REPLAY``.

    requirements.md §9.1.4 mandates an audit record + a session-key
    rotate on every ``E_REPLAY``. The reference model emits both as
    side-effects of the seen-set's rejection branch.
    """

    error_code: str
    subject: str
    nonce: bytes
    first_seen_ms: int
    rejected_at_ms: int


@dataclass
class SeenSet:
    """``(subject, nonce) → first_seen_ms`` cache with TTL eviction.

    Mirrors design.md §9.2 verbatim:

    * TTL is fixed at ``2 × max_message_lifetime`` by default
      (requirements.md §9.1.1 floor).
    * Repeated consumption of the same key inside the TTL is rejected
      with :data:`E_REPLAY` (design.md §EH.1 row "重放").
    * Each rejection appends an :class:`AuditEvent` and increments the
      ``session_key_rotations`` counter, enforcing requirements.md
      §9.1.4 ("写入安全审计并触发会话密钥 rotate").

    Eviction is performed lazily on every call. Lazy eviction is
    sufficient because the model is single-threaded; concurrency is
    simulated by reordering the submissions (see
    :func:`test_concurrent_replay_admits_exactly_one`).

    .. note::
        Not Normative. The authoritative contract is design.md §9.2;
        this class is a reference seen-set used only to drive the
        conformance assertions.
    """

    ttl_ms: int = SEEN_SET_TTL_MS
    _store: dict[tuple[str, bytes], int] = field(default_factory=dict)
    audit_log: list[AuditEvent] = field(default_factory=list)
    session_key_rotations: int = 0

    def consume(self, env: CapturedEnvelope, now_ms: int) -> str:
        """Return :data:`ACCEPTED` or :data:`E_REPLAY` for ``env`` at ``now_ms``.

        Eviction is performed *before* the lookup so an expired entry on
        the same ``(subject, nonce)`` is treated as a fresh arrival —
        i.e. a TTL-out-of-window same-nonce envelope is accepted, per
        design.md §9.2. The boundary case
        ``now_ms - first_seen == ttl_ms`` is *inside* the window (still
        a replay); ``> ttl_ms`` is *outside* (fresh).
        """

        expired = [k for k, ts in self._store.items() if now_ms - ts > self.ttl_ms]
        for k in expired:
            del self._store[k]

        key = (env.subject, bytes(env.nonce))
        if key in self._store:
            self.audit_log.append(
                AuditEvent(
                    error_code=E_REPLAY,
                    subject=env.subject,
                    nonce=bytes(env.nonce),
                    first_seen_ms=self._store[key],
                    rejected_at_ms=now_ms,
                )
            )
            self.session_key_rotations += 1
            return E_REPLAY

        self._store[key] = now_ms
        return ACCEPTED


# ---------------------------------------------------------------------------
# Vector loader — captured legitimate envelopes from tasks 3.x.
# ---------------------------------------------------------------------------
# Each entry maps a vector family produced by tasks 3.x to the relative
# request file inside each case directory. We use the **CBOR** form
# everywhere because that is the protocol's primary wire format
# (design.md §5.1 / Requirement 10.1) and CBOR carries the 16-byte
# ``nonce`` as a native byte string — no JSON/base64 decoding step on
# the critical path.
_FAMILY_REQUEST_FILE: dict[str, str] = {
    "bootstrap": "request.cbor",       # task 3.1
    "grade-switch": "request.cbor",    # task 3.3
    "delegate": "request.cbor",        # task 3.4
    "faying-request": "request.cbor",  # task 3.9
}

# Discrimination of "legitimate" cases per family. Negative / failure
# vectors (e.g. ``neg-no-witness``, ``neg-up-g3-to-g2-no-witness``) are
# excluded because §9.2 only governs envelopes that *would otherwise be
# accepted*; replaying a malformed envelope is covered by other §EH.1
# rows.
def _is_positive_case(family: str, vec: dict[str, Any]) -> bool:
    """Return True iff ``vec`` is a legitimate (non-error) capture."""

    # Negative cases declare ``kind == "negative"`` (bootstrap / delegate /
    # grade-switch families) or carry a non-null ``error_code``
    # (faying-request family). Both shapes are filtered here.
    if vec.get("kind") == "negative":
        return False
    if vec.get("error_code") is not None:
        return False
    # ``faying-request`` includes ``vec-06-hp-rejected`` (outcome=rejected)
    # and ``vec-07-bootstrap-timeout`` (outcome=timeout) which are not
    # legitimate steady-state envelopes for §9.2 replay testing.
    outcome = vec.get("outcome")
    if outcome in ("rejected", "timeout", "refused-no-witness"):
        return False
    return True


def _normalise_issued_at(value: Any) -> int:
    """Return ``issued_at`` as a monotonic millisecond integer.

    The CBOR form decodes ``issued_at`` as a ``datetime.datetime``
    (CBOR tag 0). The JSON profile uses ISO-8601 strings. Both shapes
    are mapped to milliseconds since the Unix epoch.
    """

    # cbor2 returns datetimes for tag 0 timestamps.
    if hasattr(value, "timestamp"):
        return int(value.timestamp() * 1000)
    if isinstance(value, str):
        from datetime import datetime, timezone

        # Tolerate trailing 'Z' (CBOR/JSON profile §5.1 uses ISO-8601 UTC).
        normalised = value.replace("Z", "+00:00")
        return int(
            datetime.fromisoformat(normalised).astimezone(timezone.utc).timestamp() * 1000
        )
    if isinstance(value, (int, float)):
        return int(value * 1000) if isinstance(value, float) else value
    raise TypeError(
        f"unsupported issued_at shape {type(value).__name__}: {value!r}"
    )


def _extract_envelope_keys(
    *, family: str, case: str, raw_cbor: bytes
) -> CapturedEnvelope:
    """Decode ``raw_cbor`` and pull out the §9.2 seen-set keys.

    Raises :class:`AssertionError` if the captured envelope violates
    requirements.md §9.1.3 (16-byte nonce + ``issued_at`` present) so
    that a malformed vector fails the test loudly rather than silently
    skipping a family.
    """

    decoded = cbor2.loads(raw_cbor)
    assert isinstance(decoded, dict), (
        f"{family}/{case}: top-level envelope must be a CBOR map, "
        f"got {type(decoded).__name__}"
    )
    header = decoded.get("header")
    assert isinstance(header, dict), (
        f"{family}/{case}: envelope.header missing or not a map; "
        f"design.md §5.2 mandates a header on every report"
    )
    nonce = header.get("nonce")
    assert isinstance(nonce, (bytes, bytearray)), (
        f"{family}/{case}: header.nonce must be CBOR bstr, "
        f"got {type(nonce).__name__}"
    )
    assert len(nonce) == 16, (
        f"{family}/{case}: header.nonce must be 16 bytes per "
        f"requirements.md §9.1.3, got {len(nonce)}"
    )
    subject = header.get("subject")
    assert isinstance(subject, str) and subject, (
        f"{family}/{case}: header.subject must be a non-empty string"
    )
    issued_at = header.get("issued_at")
    assert issued_at is not None, (
        f"{family}/{case}: header.issued_at must be present per "
        f"requirements.md §9.1.3"
    )
    return CapturedEnvelope(
        family=family,
        case=case,
        subject=subject,
        nonce=bytes(nonce),
        issued_at_ms=_normalise_issued_at(issued_at),
        raw_cbor=raw_cbor,
    )


def _iter_captured_envelopes() -> Iterable[CapturedEnvelope]:
    """Yield every legitimate captured envelope from tasks 3.x."""

    if not _VECTORS_DIR.exists():  # pragma: no cover - vectors must exist
        return

    for family, request_file in _FAMILY_REQUEST_FILE.items():
        family_dir = _VECTORS_DIR / family
        index_path = family_dir / "index.json"
        if not (family_dir.exists() and index_path.exists()):
            continue
        index = json.loads(index_path.read_text(encoding="utf-8"))
        for vec in index.get("vectors", []):
            if not _is_positive_case(family, vec):
                continue
            case = vec.get("name") or vec.get("vid") or vec.get("vector_id")
            if not case:
                continue
            request_path = family_dir / case / request_file
            if not request_path.exists():
                continue
            raw_cbor = request_path.read_bytes()
            try:
                yield _extract_envelope_keys(
                    family=family, case=case, raw_cbor=raw_cbor
                )
            except AssertionError:
                # Re-raise so a malformed vector does not silently
                # disappear from the parametrize list.
                raise


# Materialise once at collection time so pytest can name parametrize ids.
_CAPTURED: list[CapturedEnvelope] = list(_iter_captured_envelopes())


def _envelope_id(env: CapturedEnvelope) -> str:
    return f"{env.family}/{env.case}"


# ---------------------------------------------------------------------------
# Sanity guard — at least one capture per family must exist.
# ---------------------------------------------------------------------------
def test_captured_envelopes_are_well_formed() -> None:
    """**Validates: Requirements 9.1.3** + sanity over tasks 3.x output.

    The end-to-end replay test only carries weight if it actually
    consumes captured legitimate envelopes from each task-3.x family.
    This guard fails loudly if the vector loader returns an empty set
    for any required family or if any captured envelope violates the
    16-byte nonce + ``issued_at`` invariants.
    """

    assert _CAPTURED, (
        "No captured envelopes loaded. tasks.md §6.1 requires consuming "
        "legitimate vectors produced by tasks 3.1 / 3.3 / 3.4 / 3.9; "
        "is the vectors/ tree present at the expected path?"
    )
    families_seen = {env.family for env in _CAPTURED}
    expected = set(_FAMILY_REQUEST_FILE.keys())
    missing = expected - families_seen
    assert not missing, (
        f"Replay attack test must cover every task-3.x positive-vector "
        f"family. Missing: {sorted(missing)}; saw: {sorted(families_seen)}."
    )
    # 16-byte nonce + present issued_at are invariants for every vector.
    for env in _CAPTURED:
        assert len(env.nonce) == 16, (
            f"{_envelope_id(env)}: nonce width must be 16 bytes "
            f"(requirements.md §9.1.3), got {len(env.nonce)}"
        )
        assert env.issued_at_ms > 0, (
            f"{_envelope_id(env)}: issued_at must be present and positive"
        )


# ---------------------------------------------------------------------------
# Group A — TTL 内重放 must return E_REPLAY.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "envelope",
    _CAPTURED,
    ids=[_envelope_id(e) for e in _CAPTURED],
)
def test_replay_within_ttl_returns_e_replay(envelope: CapturedEnvelope) -> None:
    """**Validates: Requirements 9.1.2** — TTL 内重放 → ``E_REPLAY``.

    The captured envelope is submitted twice into the seen-set with a
    ``delta_ms`` strictly inside the §9.2 TTL window. The first
    submission MUST be accepted (it is the legitimate first arrival),
    the second MUST be rejected with ``E_REPLAY`` because the
    ``(subject, nonce)`` key is already in the seen-set.

    Tested deltas exercise the inside-window range, including the sharp
    boundaries 0 ms (true concurrent replay) and exactly
    ``2 × max_message_lifetime`` (last instant still inside).
    """

    seen = SeenSet()
    t0 = envelope.issued_at_ms

    # Boundary deltas to widen coverage without explosive parametrize:
    # 0 ms (simultaneous), mid-window, just-inside, and the floor TTL.
    inside_deltas = (0, 1, SEEN_SET_TTL_MS // 2, SEEN_SET_TTL_MS - 1, SEEN_SET_TTL_MS)
    for delta in inside_deltas:
        # Fresh seen-set per delta so previous iterations cannot mask
        # the second-submission rejection branch.
        seen = SeenSet()
        v1 = seen.consume(envelope, t0)
        v2 = seen.consume(envelope, t0 + delta)
        assert v1 == ACCEPTED, (
            f"{_envelope_id(envelope)}: first arrival of legitimate envelope "
            f"must be accepted, got {v1!r}"
        )
        assert v2 == E_REPLAY, (
            f"{_envelope_id(envelope)} delta_ms={delta}: replay inside "
            f"TTL=2×max_message_lifetime ({SEEN_SET_TTL_MS}ms) MUST return "
            f"E_REPLAY (design.md §9.2 / §EH.1), got {v2!r}"
        )


@pytest.mark.parametrize(
    "envelope",
    _CAPTURED,
    ids=[_envelope_id(e) for e in _CAPTURED],
)
def test_concurrent_replay_admits_exactly_one(
    envelope: CapturedEnvelope,
) -> None:
    """**Validates: Requirements 9.1.2** — concurrent replay race.

    Concurrent submission of the *same captured envelope* (modelled by
    submitting the byte-identical envelope twice at the same monotonic
    instant, in either order) MUST be serialised by the seen-set:
    exactly one arrival is accepted and the other is rejected with
    ``E_REPLAY``. This is the cardinality form of the §12 P9 invariant
    transposed onto a real captured legitimate envelope.
    """

    for swap_order in (False, True):
        seen = SeenSet()
        # Both arrivals reach the seen-set at the same monotonic instant.
        if swap_order:
            v_first = seen.consume(envelope, envelope.issued_at_ms)
            v_second = seen.consume(envelope, envelope.issued_at_ms)
        else:
            v_first = seen.consume(envelope, envelope.issued_at_ms)
            v_second = seen.consume(envelope, envelope.issued_at_ms)
        accepted = sum(1 for v in (v_first, v_second) if v == ACCEPTED)
        rejected = sum(1 for v in (v_first, v_second) if v == E_REPLAY)
        assert accepted == 1 and rejected == 1, (
            f"{_envelope_id(envelope)} swap_order={swap_order}: concurrent "
            f"submission of identical (subject, nonce) MUST yield exactly "
            f"one ACCEPTED + one E_REPLAY, got "
            f"accepted={accepted}, rejected={rejected}, "
            f"verdicts=({v_first!r}, {v_second!r})"
        )


# ---------------------------------------------------------------------------
# Group A — audit + session-key rotate side-effects (Requirement 9.1.4).
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "envelope",
    _CAPTURED,
    ids=[_envelope_id(e) for e in _CAPTURED],
)
def test_replay_records_audit_and_rotates_session_key(
    envelope: CapturedEnvelope,
) -> None:
    """**Validates: Requirements 9.1.4** — ``E_REPLAY`` ⇒ 安全审计 + rotate.

    Per design.md §EH.1 row "重放" the ``E_REPLAY`` rejection branch is
    "拒绝 + 安全告警 + 立即 rotate 会话密钥". On every TTL-internal
    replay of a captured legitimate envelope the seen-set MUST:

    1. append exactly one :class:`AuditEvent` with ``error_code ==
       'E_REPLAY'`` and the colliding ``(subject, nonce)`` key;
    2. increment ``session_key_rotations`` by exactly one;
    3. leave the audit log untouched on the legitimate first arrival.
    """

    seen = SeenSet()
    # First arrival is the legitimate captured envelope.
    v1 = seen.consume(envelope, envelope.issued_at_ms)
    assert v1 == ACCEPTED
    assert seen.audit_log == [], (
        f"{_envelope_id(envelope)}: legitimate first arrival must not cut "
        f"an audit record"
    )
    assert seen.session_key_rotations == 0, (
        f"{_envelope_id(envelope)}: legitimate first arrival must not "
        f"trigger a session-key rotate"
    )

    # Replay inside TTL — the §EH.1 contract kicks in.
    v2 = seen.consume(envelope, envelope.issued_at_ms + 1)
    assert v2 == E_REPLAY
    assert len(seen.audit_log) == 1, (
        f"{_envelope_id(envelope)}: E_REPLAY must cut exactly one audit "
        f"record (requirements.md §9.1.4); got {seen.audit_log!r}"
    )
    audit = seen.audit_log[0]
    assert audit.error_code == E_REPLAY
    assert audit.subject == envelope.subject, (
        f"{_envelope_id(envelope)}: audit record must capture the "
        f"colliding subject; got {audit.subject!r}"
    )
    assert audit.nonce == envelope.nonce, (
        f"{_envelope_id(envelope)}: audit record must capture the "
        f"colliding nonce; got {audit.nonce!r}"
    )
    assert seen.session_key_rotations == 1, (
        f"{_envelope_id(envelope)}: E_REPLAY must trigger exactly one "
        f"session-key rotate (requirements.md §9.1.4); "
        f"got {seen.session_key_rotations}"
    )


# ---------------------------------------------------------------------------
# Group B — TTL 外同 nonce per §9.2 definition.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "envelope",
    _CAPTURED,
    ids=[_envelope_id(e) for e in _CAPTURED],
)
def test_same_nonce_outside_ttl_is_fresh(envelope: CapturedEnvelope) -> None:
    """**Validates: Requirements 9.1.1** — TTL 外行为符合 §9.2 定义.

    Once the §9.2 TTL elapses, the seen-set MUST forget the prior
    consumption: a same-``(subject, nonce)`` envelope arriving past the
    TTL is treated as a fresh message. Both submissions therefore land
    as :data:`ACCEPTED`, no audit record is cut, and no session-key
    rotation is triggered. This is the negative arm of the replay
    attack contract — it pins the upper bound of the seen-set's
    rejection authority.
    """

    outside_deltas = (
        SEEN_SET_TTL_MS + 1,        # 1ms past the boundary
        SEEN_SET_TTL_MS + 1_000,    # 1s past the boundary
        2 * SEEN_SET_TTL_MS,        # 2× TTL
        10 * SEEN_SET_TTL_MS,       # well past
    )
    for delta in outside_deltas:
        seen = SeenSet()
        v1 = seen.consume(envelope, envelope.issued_at_ms)
        v2 = seen.consume(envelope, envelope.issued_at_ms + delta)
        assert v1 == ACCEPTED, (
            f"{_envelope_id(envelope)}: first arrival must be accepted, "
            f"got {v1!r}"
        )
        assert v2 == ACCEPTED, (
            f"{_envelope_id(envelope)} delta_ms={delta}: same nonce past "
            f"TTL ({SEEN_SET_TTL_MS}ms) MUST be treated as fresh per "
            f"design.md §9.2; got {v2!r}"
        )
        assert seen.audit_log == [], (
            f"{_envelope_id(envelope)} delta_ms={delta}: out-of-window "
            f"replay must not cut an audit record"
        )
        assert seen.session_key_rotations == 0, (
            f"{_envelope_id(envelope)} delta_ms={delta}: out-of-window "
            f"replay must not trigger session-key rotate"
        )


# ---------------------------------------------------------------------------
# TTL boundary sharpness — cross-cutting guard.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "delta_ms,expected",
    [
        (0, E_REPLAY),                       # simultaneous duplicate
        (1, E_REPLAY),                       # 1ms inside TTL
        (SEEN_SET_TTL_MS - 1, E_REPLAY),     # just inside the boundary
        (SEEN_SET_TTL_MS, E_REPLAY),         # exactly on the 2× boundary
        (SEEN_SET_TTL_MS + 1, ACCEPTED),     # 1ms past — fresh
        (10 * SEEN_SET_TTL_MS, ACCEPTED),    # well past — fresh
    ],
)
def test_replay_ttl_boundary_is_sharp(delta_ms: int, expected: str) -> None:
    """**Validates: Requirements 9.1.1** — TTL = 2 × max_message_lifetime.

    Pins the exact-cut-off behaviour of the §9.2 seen-set against a
    single captured envelope. The ``delta_ms == 2 ×
    max_message_lifetime`` cell is the canonical boundary case
    requested by ``tasks.md §6.1`` 内容 row.
    """

    if not _CAPTURED:  # pragma: no cover - covered by sanity guard
        pytest.skip("no captured envelopes available")
    envelope = _CAPTURED[0]
    seen = SeenSet()
    v1 = seen.consume(envelope, envelope.issued_at_ms)
    v2 = seen.consume(envelope, envelope.issued_at_ms + delta_ms)
    assert v1 == ACCEPTED, f"first arrival must be accepted, got {v1!r}"
    assert v2 == expected, (
        f"{_envelope_id(envelope)}: TTL boundary violated; "
        f"delta_ms={delta_ms} (TTL={SEEN_SET_TTL_MS}); "
        f"expected {expected!r}, got {v2!r}"
    )


# ---------------------------------------------------------------------------
# N-way replay — repeated submission of the same captured envelope.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "envelope",
    _CAPTURED,
    ids=[_envelope_id(e) for e in _CAPTURED],
)
def test_n_way_replay_admits_exactly_one_per_envelope(
    envelope: CapturedEnvelope,
) -> None:
    """**Validates: Requirements 9.1.2** — generalised cardinality.

    A real attacker may flood the seen-set with the same captured
    envelope. Per the §12 P9 invariant generalised to ``N`` arrivals:
    when ``N`` byte-identical copies all fall inside the TTL window,
    exactly one is accepted and ``N − 1`` are rejected with
    ``E_REPLAY``; each rejection cuts one audit record and rotates the
    session key once.
    """

    n = 5
    seen = SeenSet()
    verdicts: list[str] = []
    for i in range(n):
        # All arrivals fall well within the TTL window.
        verdicts.append(
            seen.consume(envelope, envelope.issued_at_ms + i)
        )
    accepted = verdicts.count(ACCEPTED)
    rejected = verdicts.count(E_REPLAY)
    assert accepted == 1, (
        f"{_envelope_id(envelope)}: n-way replay must accept exactly one, "
        f"got accepted={accepted}, verdicts={verdicts!r}"
    )
    assert rejected == n - 1, (
        f"{_envelope_id(envelope)}: every non-winning collider must be "
        f"E_REPLAY, got rejected={rejected} (expected {n - 1})"
    )
    assert len(seen.audit_log) == n - 1, (
        f"{_envelope_id(envelope)}: every E_REPLAY must cut one audit "
        f"record, got {len(seen.audit_log)}"
    )
    assert seen.session_key_rotations == n - 1, (
        f"{_envelope_id(envelope)}: every E_REPLAY must rotate the "
        f"session key once, got {seen.session_key_rotations}"
    )
