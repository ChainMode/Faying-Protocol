"""Faying Protocol/1.0 — End-to-end T6 audit-flooding conformance test.

Covers ``tasks.md §6.10 T6 审计洪流模拟``.

**Validates: Requirements 13.6** (T6 审计洪流 — Priority-Bucketed
Notification + ConfirmationRateLimit)
**Property: P18.6** (priority bucket + rate limit; design.md §12, §9.10.7)
**Design anchors**:

* design.md §9.10.7 (T6 Audit Flooding — five protocol-level
  protections: priority-bucketed notification, ConfirmationRateLimit,
  auto downgrade / suspend, critical penetration, FAYING_REQUEST
  coverage);
* design.md §EH.3 (the four "must-push to HP view" error codes —
  ``E_ROGUE_DETECTED`` / ``E_ATTESTATION_INVALID`` / ``E_REVOKED`` /
  ``E_REPLAY``);
* design.md §5.3.6 (FAYING_REQUEST / FAYING_REQUEST_RESP — IF-initiated
  Faying request channel that §9.10.7 #5 folds into the same budget);
* design.md Appendix B (ConfirmationRateLimit default 10/min,
  hard ceiling 60/min);
* requirements.md §13.6 (4 EARS clauses, see below).

Acceptance-criteria coverage (requirements.md §13.6, mirrored from
``tasks.md §6.10`` 验收 row):

* §13.6.1 — every event reaching the HP view channel carries a bucket
  in ``{critical, high, normal, low}``; the four §EH.3 must-push error
  codes plus the G0 Override candidate are forced to ``critical`` even
  if upstream mislabels them. Pinned by
  :class:`TestPriorityBucketTotality` and the per-event-type
  parametrisation.
* §13.6.2 — per ``(HP, IF)`` pair, MS enforces ``ConfirmationRateLimit``
  on confirmation traffic per unit window. Pinned by
  :func:`test_audit_flood_critical_penetration_under_saturation`
  (saturating-stream variant).
* §13.6.3 — over-budget confirmation traffic auto-downgrades or
  suspends the IF, AND every such decision is appended to the
  Attestation_Chain AND surfaced on the HP view channel. Pinned by
  :class:`TestAutoDowngradeOrSuspendChainAudit`.
* §13.6.4 — ``critical`` bucket events MUST penetrate to HP_view even
  while the pair is under downgrade / suspend; never silently dropped.
  Pinned by :func:`test_audit_flood_critical_penetration_under_saturation`.

Scope (per ``tasks.md §6.10`` 内容 row)

This module is the **end-to-end audit-flooding attack simulation**,
counterpart to the property-based test
``pbt.tests.test_p18_6_priority_bucket_and_rate_limit``. The PBT module
fuzzes random event streams against four §12 P18.6 conjuncts; this
test feeds **fixed adversary scenarios** through the *same reference
:class:`Dispatcher` model* so the two suites validate the same model
from independent angles. Three adversary scenarios are exercised
explicitly per ``tasks.md §6.10``:

1. **海量 low / normal 噪声 + 少量 critical 事件**：critical 桶事件
   100% 送达 HP 视野 (§13.6.1, §13.6.4).
2. **超频 CONFIRMATION_REQUEST 洪流**：触发 auto downgrade / suspend
   且记录写入 Attestation_Chain 并 push 到 HP 视野 (§13.6.2, §13.6.3).
3. **高频 FAYING_REQUEST 滥用**：与 CONFIRMATION_REQUEST 共享同一
   ``ConfirmationRateLimit`` 预算 (§9.10.7 #5 / Q12 抗钓鱼锚点).

The reference :class:`Dispatcher` is **Not Normative**; the
authoritative contract is design.md §9.10.7 / §EH.3 + the §12 P18.6
invariant. Any divergence between this module and the spec is a bug
in this file.

Reuse strategy — this test imports the reference :class:`Dispatcher`
verbatim from ``pbt/tests/test_p18_6_priority_bucket_and_rate_limit.py``
so both the property and end-to-end suites probe the same enforcement
state machine. The import is wired through a local ``sys.path`` shim
(the PBT tree is not packaged) and gracefully skips the module if the
PBT tree is absent from a partial checkout.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest


# ---------------------------------------------------------------------------
# Reuse the §9.10.7 reference dispatcher from the P18.6 PBT module.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_PBT_TESTS = _REPO_ROOT / "pbt" / "tests"

if not _PBT_TESTS.exists():  # pragma: no cover - partial checkout guard
    pytest.skip(
        "pbt/tests/ is not present in this checkout; the T6 conformance "
        "test relies on the P18.6 reference dispatcher.",
        allow_module_level=True,
    )

if str(_PBT_TESTS) not in sys.path:
    sys.path.insert(0, str(_PBT_TESTS))

from test_p18_6_priority_bucket_and_rate_limit import (  # type: ignore[import-not-found]  # noqa: E402
    BUCKET_CRITICAL,
    BUCKET_HIGH,
    BUCKET_LOW,
    BUCKET_NORMAL,
    CONFIRMATION_EVENT_TYPES,
    CONFIRMATION_RATE_LIMIT_DEFAULT,
    CONFIRMATION_RATE_LIMIT_MAX,
    CRITICAL_EVENT_TYPES,
    EFFECT_DOWNGRADE,
    EFFECT_NONE,
    EFFECT_SUSPEND,
    EVENT_AUDIT_INFO,
    EVENT_CONFIRMATION_REQUEST,
    EVENT_E_ATTESTATION_INVALID,
    EVENT_E_REPLAY,
    EVENT_E_REVOKED,
    EVENT_E_ROGUE_DETECTED,
    EVENT_FAYING_REQUEST,
    EVENT_G0_OVERRIDE,
    EVENT_HEARTBEAT,
    NOISE_EVENT_TYPES,
    PRIORITY_BUCKETS,
    PRIORITY_BUCKETS_SET,
    AttestationChainEntry,
    Dispatcher,
    Event,
)


# ---------------------------------------------------------------------------
# Test-suite-local constants.
# ---------------------------------------------------------------------------
HP: str = "hp:alice"
IF: str = "if:phi"
HP_OTHER: str = "hp:bob"
IF_OTHER: str = "if:psi"

# Default flood scenario tuned per ``tasks.md §6.10`` 内容 row:
#   - 海量 low / normal 事件 (high volume, no budget impact)
#   - 少量 critical 事件 (must always reach HP_view)
#   - 高频 FAYING_REQUEST 滥用流量 (must consume the same budget)
NOISE_VOLUME: int = 256
CRITICAL_VOLUME: int = 4
FAYING_FLOOD_VOLUME: int = 32  # > default ConfirmationRateLimit (10)
CONFIRMATION_FLOOD_VOLUME: int = 32  # > default ConfirmationRateLimit (10)


# Sanity guards — fail loudly if the imported module's invariants drift.
assert CONFIRMATION_RATE_LIMIT_DEFAULT == 10, (
    "design.md Appendix B pins ConfirmationRateLimit default = 10/min"
)
assert CONFIRMATION_RATE_LIMIT_MAX == 60, (
    "design.md Appendix B pins ConfirmationRateLimit hard ceiling = 60/min"
)
assert PRIORITY_BUCKETS_SET == frozenset(
    {BUCKET_CRITICAL, BUCKET_HIGH, BUCKET_NORMAL, BUCKET_LOW}
), "design.md §9.10.7 #1 enumerates exactly four buckets"
assert {
    EVENT_E_ROGUE_DETECTED,
    EVENT_E_ATTESTATION_INVALID,
    EVENT_E_REVOKED,
    EVENT_E_REPLAY,
}.issubset(CRITICAL_EVENT_TYPES), (
    "design.md §EH.3 lists four must-push error codes — they MUST be "
    "members of the critical event-type catalogue."
)
assert {EVENT_CONFIRMATION_REQUEST, EVENT_FAYING_REQUEST} == set(
    CONFIRMATION_EVENT_TYPES
), (
    "design.md §9.10.7 #5 requires CONFIRMATION_REQUEST and "
    "FAYING_REQUEST to share the same ConfirmationRateLimit budget."
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------
def _make_event(
    *,
    event_type: str,
    hp: str = HP,
    if_id: str = IF,
    window: int = 0,
    hint_bucket: str = BUCKET_NORMAL,
) -> Event:
    """Construct a §9.10.7 dispatcher-input event with sensible defaults."""

    return Event(
        hp=hp,
        if_id=if_id,
        event_type=event_type,
        window=window,
        hint_bucket=hint_bucket,
    )


def _run_stream(stream: list[Event], rate_limit: int) -> Dispatcher:
    """Drive an event stream through a fresh :class:`Dispatcher`."""

    dispatcher = Dispatcher(rate_limit=rate_limit)
    for ev in stream:
        dispatcher.dispatch(ev)
    return dispatcher


def _delivered_events(dispatcher: Dispatcher) -> list[Event]:
    """Return the chronological list of events surfaced on HP_view."""

    return [ev for ev, _bucket in dispatcher.delivered]


def _delivered_buckets(dispatcher: Dispatcher) -> list[str]:
    """Return the chronological list of bucket labels surfaced on HP_view."""

    return [bucket for _ev, bucket in dispatcher.delivered]


# ---------------------------------------------------------------------------
# 1. Bucket totality + critical override (Requirement 13.6.1).
# ---------------------------------------------------------------------------
class TestPriorityBucketTotality:
    """Every event reaching HP_view carries a bucket in the §9.10.7 #1 set.

    Covers Requirement 13.6.1: ``critical / high / normal / low`` are
    the four buckets the protocol mandates; classification is total
    (no "unbucketed" tail) and **critical event types are forced into
    the ``critical`` bucket even when the upstream module mislabels
    them**. The four §EH.3 must-push error codes plus the G0 Override
    candidate cover this catalogue verbatim.
    """

    @pytest.mark.parametrize(
        "event_type",
        sorted(CRITICAL_EVENT_TYPES),
    )
    @pytest.mark.parametrize("hint", PRIORITY_BUCKETS)
    def test_critical_event_types_forced_to_critical_bucket(
        self, event_type: str, hint: str
    ) -> None:
        """**Validates: Requirements 13.6.1** — critical override.

        For every (event_type ∈ §EH.3 ∪ G0 Override, hint_bucket) pair
        the dispatcher MUST classify the event into ``critical`` even
        if upstream supplied a non-critical hint. This is the
        "关键事件不得被低优先级流量淹没" anchor of §9.10.7 #1.
        """

        ev = _make_event(event_type=event_type, hint_bucket=hint)
        bucket = Dispatcher.classify(ev)
        assert bucket == BUCKET_CRITICAL, (
            f"Req 13.6.1 / §9.10.7 #1 violated: event_type={event_type!r} "
            f"with hint_bucket={hint!r} was classified as {bucket!r}, "
            "expected 'critical'."
        )

    @pytest.mark.parametrize("hint", PRIORITY_BUCKETS)
    def test_noise_event_types_honour_upstream_hint(self, hint: str) -> None:
        """Non-critical event types preserve the upstream bucket hint.

        The §9.10.7 #1 invariant only forces critical event types into
        the critical bucket; a ``HEARTBEAT`` hinted as ``low`` MUST stay
        in ``low`` so the four-bucket ordering remains meaningful for
        prioritisation. This is the negative-arm of the bucket-totality
        contract — required so that §13.6.4 critical-penetration is the
        *unique* way an event reaches HP_view under throttling.
        """

        ev = _make_event(event_type=EVENT_HEARTBEAT, hint_bucket=hint)
        bucket = Dispatcher.classify(ev)
        assert bucket == hint, (
            f"§9.10.7 #1 totality violated: noise event with "
            f"hint={hint!r} was reclassified to {bucket!r}; only critical "
            "event types may be promoted."
        )

    def test_every_delivered_event_has_a_valid_bucket(self) -> None:
        """**Validates: Requirements 13.6.1** — totality on a flood stream.

        Drives a full audit-flood mix (noise + critical + confirmation
        + faying-request) and asserts every event surfaced on HP_view
        carries a bucket label inside the closed four-bucket set.
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        stream: list[Event] = []
        # §9.10.7 #1 — bucket totality holds even with mass low/normal noise.
        for i in range(NOISE_VOLUME):
            stream.append(
                _make_event(
                    event_type=EVENT_AUDIT_INFO if i % 2 == 0 else EVENT_HEARTBEAT,
                    hint_bucket=BUCKET_LOW if i % 3 == 0 else BUCKET_NORMAL,
                )
            )
        # Sprinkle critical events through the stream.
        for i in range(CRITICAL_VOLUME):
            stream.append(
                _make_event(
                    event_type=sorted(CRITICAL_EVENT_TYPES)[i % len(CRITICAL_EVENT_TYPES)],
                    # Mislabel as low — classifier MUST promote.
                    hint_bucket=BUCKET_LOW,
                )
            )
        # And add some confirmation traffic to exercise the budget path.
        for _ in range(rate_limit + 1):  # +1 to push exactly over the edge
            stream.append(
                _make_event(
                    event_type=EVENT_CONFIRMATION_REQUEST,
                    hint_bucket=BUCKET_HIGH,
                )
            )

        dispatcher = _run_stream(stream, rate_limit)
        for ev, bucket in dispatcher.delivered:
            assert bucket in PRIORITY_BUCKETS_SET, (
                f"Req 13.6.1 violated: event {ev.event_type!r} surfaced on "
                f"HP_view with bucket={bucket!r} ∉ {sorted(PRIORITY_BUCKETS)}"
            )


# ---------------------------------------------------------------------------
# 2. Auto downgrade / suspend + Attestation_Chain audit (Req 13.6.3).
# ---------------------------------------------------------------------------
class TestAutoDowngradeOrSuspendChainAudit:
    """Over-budget confirmation flows trigger auto downgrade/suspend.

    Covers Requirement 13.6.3: every breach of ``ConfirmationRateLimit``
    MUST automatically downgrade or suspend the offending IF, and the
    decision MUST be appended both to the Attestation_Chain (§3.3) and
    to the HP view channel (§9.10.7 #3).
    """

    def test_under_budget_confirmation_does_not_downgrade(self) -> None:
        """Boundary case — exactly ``rate_limit`` confirmations is OK.

        The §9.10.7 #2 trigger predicate is *strict-greater-than*, so
        a window with exactly ``rate_limit`` confirmations MUST NOT
        fire downgrade / suspend. This pins the lower edge of the
        Attestation_Chain audit obligation: no breach ⇒ no chain entry,
        no synthetic critical push.
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        stream = [
            _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
            for _ in range(rate_limit)
        ]
        dispatcher = _run_stream(stream, rate_limit)

        assert not dispatcher.auto_downgrade_or_suspend(HP, IF), (
            f"Req 13.6.3 boundary violated: exactly rate_limit="
            f"{rate_limit} confirmations triggered downgrade/suspend; "
            "the §9.10.7 #2 predicate must be strict-greater-than."
        )
        assert dispatcher.attestation_chain == [], (
            "Req 13.6.3 violated: Attestation_Chain received an entry "
            "even though the rate-limit was not breached."
        )
        # All delivered events must be the legitimate confirmations.
        assert len(dispatcher.delivered) == rate_limit
        assert all(
            ev.event_type == EVENT_CONFIRMATION_REQUEST
            for ev, _b in dispatcher.delivered
        )

    def test_over_budget_confirmation_triggers_chain_audit(self) -> None:
        """**Validates: Requirements 13.6.2 + 13.6.3** — Chain audit.

        Submitting ``rate_limit + N`` confirmations in a single window
        MUST:
        1. flip ``auto_downgrade_or_suspend((HP, IF)) → True``;
        2. append exactly one Attestation_Chain entry per over-budget
           edge (the first edge → ``downgrade``; subsequent edges →
           ``suspend``);
        3. push a synthetic ``critical`` event to HP_view per
           Attestation_Chain entry (the §9.10.7 #3 visibility clause).
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        over_count = 3
        stream = [
            _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
            for _ in range(rate_limit + over_count)
        ]
        dispatcher = _run_stream(stream, rate_limit)

        assert dispatcher.auto_downgrade_or_suspend(HP, IF), (
            "Req 13.6.3 violated: over-budget confirmation flood did not "
            f"flip auto_downgrade_or_suspend({HP!r}, {IF!r}) to True."
        )
        # One chain entry per over-budget edge.
        assert len(dispatcher.attestation_chain) == over_count, (
            "Req 13.6.3 violated: expected one Attestation_Chain entry "
            f"per over-budget edge ({over_count}), got "
            f"{len(dispatcher.attestation_chain)}."
        )

        # First edge → downgrade; subsequent → suspend (sticky).
        first, *rest = dispatcher.attestation_chain
        assert first.effect == EFFECT_DOWNGRADE, (
            "Req 13.6.3 violated: first over-budget edge must yield "
            f"effect={EFFECT_DOWNGRADE!r}, got {first.effect!r}."
        )
        for entry in rest:
            assert entry.effect == EFFECT_SUSPEND, (
                "Req 13.6.3 violated: subsequent over-budget edge must "
                f"escalate to {EFFECT_SUSPEND!r}, got {entry.effect!r}."
            )

        # Every chain entry must reference the offending pair and carry
        # ``confirmation_count > rate_limit``.
        for entry in dispatcher.attestation_chain:
            assert (entry.hp, entry.if_id) == (HP, IF), (
                "Req 13.6.3 violated: chain entry references the wrong "
                f"(HP, IF) pair: ({entry.hp!r}, {entry.if_id!r})."
            )
            assert entry.confirmation_count > entry.rate_limit, (
                "Req 13.6.3 violated: chain entry must record an "
                f"over-budget count, got count={entry.confirmation_count} "
                f"≤ rate_limit={entry.rate_limit}."
            )
            assert entry.rate_limit == rate_limit, (
                "Req 13.6.3 violated: chain entry rate_limit drifted from "
                f"the deployment value (got {entry.rate_limit}, expected "
                f"{rate_limit})."
            )

        # Each chain entry must also surface as a synthetic ``critical``
        # event on HP_view per §9.10.7 #3.
        critical_pushes = [
            ev
            for ev, bucket in dispatcher.delivered
            if bucket == BUCKET_CRITICAL
            and ev.event_type in {EVENT_E_REVOKED, EVENT_E_ROGUE_DETECTED}
            and ev.hp == HP
            and ev.if_id == IF
        ]
        assert len(critical_pushes) >= len(dispatcher.attestation_chain), (
            "Req 13.6.3 violated: every Attestation_Chain entry MUST "
            "also push a synthetic critical event to HP_view; got "
            f"{len(critical_pushes)} critical pushes for "
            f"{len(dispatcher.attestation_chain)} chain entries."
        )

    def test_chain_entries_isolated_per_hp_if_pair(self) -> None:
        """Over-budget on one pair MUST NOT throttle a different pair.

        Pins the §9.10.7 #2 *per-pair* clause: the budget is keyed by
        ``(HP, IF)``, so saturating ``(hp:alice, if:phi)`` leaves
        ``(hp:bob, if:psi)`` unaffected. This is the cross-pair
        isolation invariant the audit-flooding mitigation relies on
        (otherwise a single noisy IF could silence every HP at once).
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        stream: list[Event] = []
        # Pair A: deep saturation.
        for _ in range(rate_limit + 5):
            stream.append(
                _make_event(
                    event_type=EVENT_CONFIRMATION_REQUEST,
                    hp=HP,
                    if_id=IF,
                )
            )
        # Pair B: well within budget.
        for _ in range(rate_limit - 1):
            stream.append(
                _make_event(
                    event_type=EVENT_CONFIRMATION_REQUEST,
                    hp=HP_OTHER,
                    if_id=IF_OTHER,
                )
            )
        dispatcher = _run_stream(stream, rate_limit)

        assert dispatcher.auto_downgrade_or_suspend(HP, IF), (
            "Req 13.6.3 violated: pair A should be throttled."
        )
        assert not dispatcher.auto_downgrade_or_suspend(HP_OTHER, IF_OTHER), (
            "Req 13.6.2 (per-pair scope) violated: pair B was throttled "
            "even though its confirmation count stayed under the limit."
        )
        # Chain entries reference pair A only.
        offending_pairs = {
            (entry.hp, entry.if_id) for entry in dispatcher.attestation_chain
        }
        assert offending_pairs == {(HP, IF)}, (
            "Req 13.6.3 violated: Attestation_Chain leaked entries for "
            f"non-offending pairs: {offending_pairs}"
        )


# ---------------------------------------------------------------------------
# 3. FAYING_REQUEST shares the same budget (Requirement 13.6.2 / §9.10.7 #5).
# ---------------------------------------------------------------------------
class TestFayingRequestSameBudget:
    """``FAYING_REQUEST`` floods consume the same rate-limit budget.

    Covers the §9.10.7 #5 anti-phishing anchor (Open Questions Q12):
    iFay-initiated ``FAYING_REQUEST`` events MUST count against the
    same per-pair ``ConfirmationRateLimit`` budget as MS-pushed
    ``CONFIRMATION_REQUEST`` events. This closes the "abuse the legal
    Faying-request channel as a confirmation flood" surface.
    """

    def test_pure_faying_flood_triggers_downgrade(self) -> None:
        """**Validates: Requirements 13.6.2 / §9.10.7 #5** — FAYING-only flood.

        A burst of ``rate_limit + N`` ``FAYING_REQUEST`` events on a
        single window MUST throttle the pair just like a
        ``CONFIRMATION_REQUEST`` flood — proving the budget is shared,
        not scoped to MS-pushed traffic.
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        stream = [
            _make_event(event_type=EVENT_FAYING_REQUEST)
            for _ in range(rate_limit + 2)
        ]
        dispatcher = _run_stream(stream, rate_limit)

        assert dispatcher.auto_downgrade_or_suspend(HP, IF), (
            "Req 13.6.2 / §9.10.7 #5 violated: FAYING_REQUEST-only "
            f"flood ({rate_limit + 2} events vs rate_limit={rate_limit}) "
            "did not trigger auto downgrade/suspend — FAYING_REQUEST is "
            "treated outside the ConfirmationRateLimit budget."
        )
        assert dispatcher.attestation_chain, (
            "Req 13.6.3 violated: FAYING_REQUEST-only over-budget flood "
            "produced no Attestation_Chain entry."
        )

    def test_mixed_flood_shares_single_budget(self) -> None:
        """Mixed CONFIRMATION + FAYING flood saturates one shared budget.

        With ``rate_limit / 2`` of each event type — neither in
        isolation crosses the limit, but their **sum** does. The §9.10.7
        #5 invariant requires the budget to be shared, so the joint
        count MUST drive the trigger.
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT
        # Choose counts where each is below rate_limit but the sum
        # strictly exceeds it — pins the "joint budget" property.
        n_confirm = rate_limit // 2 + 1
        n_faying = rate_limit // 2 + 1
        assert n_confirm <= rate_limit and n_faying <= rate_limit
        assert n_confirm + n_faying > rate_limit

        stream = [
            _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
            for _ in range(n_confirm)
        ] + [
            _make_event(event_type=EVENT_FAYING_REQUEST)
            for _ in range(n_faying)
        ]
        dispatcher = _run_stream(stream, rate_limit)

        assert dispatcher.auto_downgrade_or_suspend(HP, IF), (
            "Req 13.6.2 / §9.10.7 #5 violated: mixed flood "
            f"({n_confirm} CONFIRMATION + {n_faying} FAYING = "
            f"{n_confirm + n_faying} > rate_limit={rate_limit}) did not "
            "trigger throttling. The joint count must drive the trigger."
        )

    def test_faying_flood_does_not_bypass_per_window_isolation(self) -> None:
        """Per-window scope — distinct windows do not pool the budget.

        The §12 P18.6 conjunct 2 reads ``confirmation_count(HP, IF, Δt)
        ≤ ConfirmationRateLimit`` — the window index is part of the
        key. Spreading ``2 × rate_limit`` ``FAYING_REQUEST`` events over
        two distinct windows (each at ``rate_limit``) MUST stay inside
        budget; collapsing them into a single window MUST trigger
        downgrade. Pins both directions of the per-window scope.
        """

        rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT

        # Spread across two windows — under budget per window.
        spread_stream: list[Event] = []
        for _ in range(rate_limit):
            spread_stream.append(
                _make_event(event_type=EVENT_FAYING_REQUEST, window=0)
            )
        for _ in range(rate_limit):
            spread_stream.append(
                _make_event(event_type=EVENT_FAYING_REQUEST, window=1)
            )
        spread = _run_stream(spread_stream, rate_limit)
        assert not spread.auto_downgrade_or_suspend(HP, IF), (
            "§12 P18.6 violated: per-window count == rate_limit must NOT "
            "trigger downgrade (the predicate is strict-greater-than)."
        )
        assert spread.attestation_chain == [], (
            "Req 13.6.3 violated: under-budget windows must not append "
            "Attestation_Chain entries."
        )

        # Collapsed into one window — over budget.
        collapsed_stream = [
            _make_event(event_type=EVENT_FAYING_REQUEST, window=0)
            for _ in range(2 * rate_limit)
        ]
        collapsed = _run_stream(collapsed_stream, rate_limit)
        assert collapsed.auto_downgrade_or_suspend(HP, IF), (
            "Req 13.6.2 violated: collapsing the flood into a single "
            "window must trigger downgrade — the per-window scope is "
            "the only thing protecting the spread case."
        )


# ---------------------------------------------------------------------------
# 4. Critical penetration under saturation (Requirement 13.6.4).
# ---------------------------------------------------------------------------
def test_audit_flood_critical_penetration_under_saturation() -> None:
    """**Validates: Requirements 13.6.4** — critical events 100% delivered.

    Composite scenario per ``tasks.md §6.10`` 内容 row:

    1. inject mass low/normal noise (no budget impact);
    2. inject high-frequency ``CONFIRMATION_REQUEST`` and
       ``FAYING_REQUEST`` traffic that combined exceeds the rate limit
       (drives the pair into auto downgrade/suspend);
    3. inject the four §EH.3 must-push events plus the G0 Override
       candidate **after** saturation has set in.

    Acceptance per ``tasks.md §6.10`` 验收 row: ``critical`` 桶事件
    100% 送达 HP 视野; FAYING_REQUEST 滥用必被同一速率限制约束;
    所有降级/暂停事件必写入 Attestation Chain.
    """

    rate_limit = CONFIRMATION_RATE_LIMIT_DEFAULT

    # Phase 1 — noise (low/normal) flood. No budget impact.
    noise_phase: list[Event] = [
        _make_event(
            event_type=EVENT_AUDIT_INFO if i % 2 == 0 else EVENT_HEARTBEAT,
            hint_bucket=BUCKET_LOW if i % 3 == 0 else BUCKET_NORMAL,
        )
        for i in range(NOISE_VOLUME)
    ]

    # Phase 2 — high-frequency confirmation + faying flood. Drives
    # the (HP, IF) pair into auto-downgrade.
    confirm_flood: list[Event] = [
        _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
        for _ in range(CONFIRMATION_FLOOD_VOLUME)
    ]
    faying_flood: list[Event] = [
        _make_event(event_type=EVENT_FAYING_REQUEST)
        for _ in range(FAYING_FLOOD_VOLUME)
    ]

    # Phase 3 — critical events arriving AFTER saturation. Each event
    # is mislabelled as `low`/`normal` so the §9.10.7 #1 critical
    # promotion is exercised concurrently with §9.10.7 #4 penetration.
    critical_after_saturation: list[Event] = [
        _make_event(
            event_type=EVENT_E_ROGUE_DETECTED,
            window=2,
            hint_bucket=BUCKET_LOW,
        ),
        _make_event(
            event_type=EVENT_E_ATTESTATION_INVALID,
            window=2,
            hint_bucket=BUCKET_NORMAL,
        ),
        _make_event(
            event_type=EVENT_E_REVOKED,
            window=3,
            hint_bucket=BUCKET_LOW,
        ),
        _make_event(
            event_type=EVENT_E_REPLAY,
            window=3,
            hint_bucket=BUCKET_HIGH,
        ),
        _make_event(
            event_type=EVENT_G0_OVERRIDE,
            window=3,
            hint_bucket=BUCKET_NORMAL,
        ),
    ]

    stream = noise_phase + confirm_flood + faying_flood + critical_after_saturation
    dispatcher = _run_stream(stream, rate_limit)

    # ---------------------------------------------------------------
    # Acceptance 1 — pair is throttled.
    # ---------------------------------------------------------------
    assert dispatcher.auto_downgrade_or_suspend(HP, IF), (
        "Req 13.6.2 + 13.6.3 violated: combined CONFIRMATION + FAYING "
        f"flood ({CONFIRMATION_FLOOD_VOLUME} + {FAYING_FLOOD_VOLUME} > "
        f"rate_limit={rate_limit}) did not throttle the pair."
    )

    # ---------------------------------------------------------------
    # Acceptance 2 — Attestation_Chain captured every downgrade/suspend.
    # ---------------------------------------------------------------
    assert dispatcher.attestation_chain, (
        "Req 13.6.3 violated: no Attestation_Chain entries despite "
        "deep saturation; every downgrade/suspend MUST be auditable."
    )
    for entry in dispatcher.attestation_chain:
        assert entry.effect in (EFFECT_DOWNGRADE, EFFECT_SUSPEND), (
            "Req 13.6.3 violated: Attestation_Chain entry recorded "
            f"effect={entry.effect!r}, expected downgrade or suspend."
        )
        assert (entry.hp, entry.if_id) == (HP, IF), (
            "Req 13.6.3 violated: chain entry references unexpected pair "
            f"({entry.hp!r}, {entry.if_id!r})."
        )

    # ---------------------------------------------------------------
    # Acceptance 3 — every critical event is delivered to HP_view 100%.
    # ---------------------------------------------------------------
    delivered = _delivered_events(dispatcher)
    delivered_buckets = _delivered_buckets(dispatcher)

    for ev in critical_after_saturation:
        # Match by (event_type, window) — the dispatcher does not mutate
        # those fields, so we can find each submission in the delivery
        # log unambiguously.
        matches = [
            (i, d, b)
            for i, (d, b) in enumerate(zip(delivered, delivered_buckets))
            if d.event_type == ev.event_type
            and d.window == ev.window
            and d.hp == ev.hp
            and d.if_id == ev.if_id
        ]
        assert matches, (
            f"Req 13.6.4 violated: critical event {ev.event_type!r} "
            f"(window={ev.window}) was NOT delivered to HP_view despite "
            "§9.10.7 #4 critical-penetration carve-out."
        )
        # Every match MUST carry the ``critical`` bucket label — the
        # §9.10.7 #1 promotion fires even on mislabelled hints.
        for _i, _d, bucket in matches:
            assert bucket == BUCKET_CRITICAL, (
                f"Req 13.6.1 violated: critical event {ev.event_type!r} "
                f"surfaced under bucket {bucket!r}; §9.10.7 #1 mandates "
                "critical promotion regardless of upstream hint."
            )

    # ---------------------------------------------------------------
    # Acceptance 4 — non-critical noise generated DURING throttling
    # is dropped (otherwise the §9.10.7 #4 carve-out would be vacuous).
    # ---------------------------------------------------------------
    # Pull the noise events that arrived after saturation must have
    # started — Phase 2's confirm_flood + faying_flood is enough to
    # tip the budget on the very first over-budget event, so any
    # subsequent low/normal traffic on (HP, IF) is throttled.
    # Verify by re-running just the noise after a forced saturation
    # primer; this isolates the throttle-drop semantics from the
    # composite-stream order.
    primer = [
        _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
        for _ in range(rate_limit + 1)
    ]
    suspended = _run_stream(primer, rate_limit)
    assert suspended.auto_downgrade_or_suspend(HP, IF)
    pre_drop_count = len(suspended.delivered)
    # Now feed a low-priority audit event — the §9.10.7 #4 carve-out
    # only protects critical, so this MUST be dropped.
    suspended.dispatch(
        _make_event(event_type=EVENT_AUDIT_INFO, hint_bucket=BUCKET_LOW)
    )
    assert len(suspended.delivered) == pre_drop_count, (
        "§9.10.7 #4 carve-out leaked: a low-bucket noise event was "
        "delivered to HP_view while the pair was under suspend; "
        "only critical events may penetrate."
    )

    # And the symmetric guard — a critical event in the same throttled
    # state MUST still penetrate (otherwise Acceptance 3 above would
    # not be a proof).
    suspended.dispatch(
        _make_event(
            event_type=EVENT_E_REVOKED,
            window=99,
            hint_bucket=BUCKET_LOW,
        )
    )
    penetrated = [
        (ev, b)
        for ev, b in suspended.delivered
        if ev.event_type == EVENT_E_REVOKED and ev.window == 99
    ]
    assert penetrated, (
        "Req 13.6.4 violated: critical event submitted under suspend "
        "did not penetrate to HP_view."
    )
    assert all(b == BUCKET_CRITICAL for _ev, b in penetrated), (
        "Req 13.6.1 violated: critical event under suspend was promoted "
        "but surfaced with the wrong bucket label."
    )


# ---------------------------------------------------------------------------
# Boundary regression — rate-limit edge cases.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "rate_limit",
    [1, 5, CONFIRMATION_RATE_LIMIT_DEFAULT, CONFIRMATION_RATE_LIMIT_MAX],
)
def test_t6_rate_limit_boundary(rate_limit: int) -> None:
    """**Validates: Requirements 13.6.2** — strict-greater-than predicate.

    Pins the trigger boundary at ``count == rate_limit`` (no throttle)
    vs ``count == rate_limit + 1`` (throttle) for representative
    deployment values: 1 (degenerate), 5, the default 10, and the
    Appendix B hard ceiling 60.
    """

    # count == rate_limit — under budget, no chain entry.
    inside = _run_stream(
        [
            _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
            for _ in range(rate_limit)
        ],
        rate_limit,
    )
    assert not inside.auto_downgrade_or_suspend(HP, IF), (
        f"rate_limit={rate_limit}: count == rate_limit must NOT trigger "
        "the §9.10.7 #2 strict-greater-than predicate."
    )
    assert inside.attestation_chain == []

    # count == rate_limit + 1 — over budget by one event.
    over = _run_stream(
        [
            _make_event(event_type=EVENT_CONFIRMATION_REQUEST)
            for _ in range(rate_limit + 1)
        ],
        rate_limit,
    )
    assert over.auto_downgrade_or_suspend(HP, IF), (
        f"rate_limit={rate_limit}: count == rate_limit + 1 MUST trigger "
        "auto downgrade/suspend per §9.10.7 #2."
    )
    assert len(over.attestation_chain) == 1, (
        f"rate_limit={rate_limit}: a single-edge breach must append "
        "exactly one Attestation_Chain entry."
    )
    assert over.attestation_chain[0].effect == EFFECT_DOWNGRADE


# ---------------------------------------------------------------------------
# Cross-cutting invariant — no chain entry without HP_view push.
# ---------------------------------------------------------------------------
def test_t6_chain_entries_co_occur_with_hp_view_push() -> None:
    """**Validates: Requirements 13.6.3** — chain ⇔ HP_view co-observability.

    Per §9.10.7 #3, every Attestation_Chain entry MUST also surface as
    a synthetic critical-bucket push on HP_view. This is the
    "co-observability" leg of the audit obligation: an auditor reading
    the Attestation_Chain and a Human_Prime watching the view channel
    must see the same set of throttle decisions.
    """

    rate_limit = 2
    # Two over-budget edges in window 0; one independent over-budget
    # edge in window 1 (windows reset the counter).
    stream = (
        [_make_event(event_type=EVENT_CONFIRMATION_REQUEST, window=0) for _ in range(4)]
        + [_make_event(event_type=EVENT_FAYING_REQUEST, window=1) for _ in range(3)]
    )
    dispatcher = _run_stream(stream, rate_limit)

    # 2 over-budget edges in window 0 (counts 3 and 4) + 1 in window 1
    # (count 3) ⇒ 3 chain entries total.
    assert len(dispatcher.attestation_chain) == 3, (
        "Req 13.6.3 violated: expected 3 Attestation_Chain entries "
        f"(2 over-budget edges in window 0 + 1 in window 1), got "
        f"{len(dispatcher.attestation_chain)}."
    )

    # And exactly the same number of synthetic critical pushes on HP_view.
    synthetic_critical_pushes = [
        ev
        for ev, bucket in dispatcher.delivered
        if bucket == BUCKET_CRITICAL
        and ev.event_type in {EVENT_E_REVOKED, EVENT_E_ROGUE_DETECTED}
    ]
    assert len(synthetic_critical_pushes) == len(dispatcher.attestation_chain), (
        "Req 13.6.3 violated: chain ⇔ HP_view co-observability broken — "
        f"{len(dispatcher.attestation_chain)} chain entries vs "
        f"{len(synthetic_critical_pushes)} synthetic critical pushes."
    )
