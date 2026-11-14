"""Faying Protocol/1.0 — End-to-end decoupling-signal conformance test.

Covers ``tasks.md §6.4 脱钩态识别端到端测试``.

**Validates: Requirements 9.4** (脱钩态识别)
**Design anchors**: design.md §9.5 (脱钩态识别)、§5.3.5 (RevokeReason
enumeration)、§3.3 (Attestation Chain)、§3.4 (Revocation Registry).

Scope
-----
End-to-end simulation of the four decoupling-signal families enumerated by
design.md §9.5 / Requirement 9.4. For each signal the test asserts the
``≤ 60s`` co-observability acceptance bar:

==========  ===============================  =================================
Family      Trigger (design.md §9.5)         Expected RevokeReason (§5.3.5)
==========  ===============================  =================================
主动        HP issues an explicit REVOKE     ``human-initiated``
被动        Presence stale beyond            ``terminal-disconnected``
            ``max_staleness_ms`` →
            Disconnected → reconcile
            timeout → Revoked
异常        Attestation Chain node failure   ``fay-credential-invalid``
失联        HP unreachable for longer than   ``human-prime-unreachable``
            ``HumanReachabilityBudget``
==========  ===============================  =================================

For each family the test:

1. spins up an in-memory simulator that emulates the Mandate_Service,
   Revocation_Registry, Attestation_Chain, the Human_Prime view channel,
   and one Relying_Party audit-log;
2. drives the trigger event at simulated ``t = 0`` on a **monotonic
   clock** (the simulator's ``now()`` is a strictly non-decreasing
   integer in milliseconds — wall-clock noise is intentionally absent);
3. samples the HP view channel and the RP audit-log every second up to
   ``+ 60 s`` and asserts that **both** observers see a record carrying
   the expected ``RevokeReason`` within the budget.

The acceptance criterion is a **single sample-window invariant** for each
of the four families: ``observe_window_ms ≤ 60_000`` AND ``HP view``
contains the expected ``RevokeReason`` AND ``RP audit-log`` contains the
same ``RevokeReason`` for the same ``mandate_id``.

The simulator is **Not Normative** — it is a minimal reference model
sufficient to exercise the temporal/observability surface of §9.5. Wire
codec, signature algebra, and grade transitions are out of scope; those
surfaces are covered by ``vectors/`` and ``pbt/tests/test_p13_audit_chain.py``.

Monotonic clock contract
------------------------
Per ``tasks.md §6.4`` the unified clock is **monotonic**. The simulator
tracks ``self._now_ms`` as a non-negative integer initialised to 0 and
mutated only by :meth:`Simulator.advance`. There is no wall-clock read
anywhere — Hypothesis-style flakiness from real-time scheduling is thus
impossible.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import pytest


# ---------------------------------------------------------------------------
# Constants — kept in sync with design.md §9.5 / Appendix B.
# ---------------------------------------------------------------------------
DECOUPLING_OBSERVABILITY_BUDGET_MS: int = 60_000
"""Acceptance bar: HP + RP must co-observe within 60 s (Requirement 9.4.6)."""

# Default budgets from design.md Appendix B / requirements.md §Glossary.
PRESENCE_MAX_STALENESS_MS: int = 5_000          # G1 default
RECONCILE_TIMEOUT_MS: int = 10_000              # default reconciliation deadline
HUMAN_REACHABILITY_BUDGET_MS: int = 30 * 60_000  # 30 min (Appendix B default)

# Sample cadence for the ≤ 60 s observability window. We sample every 1 s
# starting at the trigger event (t = 0). 1 s is well below the 60 s budget
# and matches RevocationVisibilityBudget granularity.
SAMPLE_CADENCE_MS: int = 1_000


# Canonical RevokeReason strings (design.md §5.3.5 enum). Restricted here
# to the four values triggered by §9.5 categories.
REASON_HUMAN_INITIATED = "human-initiated"
REASON_TERMINAL_DISCONNECTED = "terminal-disconnected"
REASON_FAY_CREDENTIAL_INVALID = "fay-credential-invalid"
REASON_HUMAN_PRIME_UNREACHABLE = "human-prime-unreachable"


# Cross-check that the four reasons we drive here all appear in the
# generated revoke vectors index. This makes the test fail loudly if
# vectors/revoke/index.json drops one of the canonical reasons during
# spec evolution — the conformance bar then becomes inconsistent.
@pytest.fixture(scope="module")
def revoke_reasons_in_vectors() -> set[str]:
    """RevokeReasons enumerated by ``vectors/revoke/index.json``.

    The vectors are the ground-truth artefact for Requirement 4.x; if a
    reason listed in design.md §9.5 disappears from the vector index the
    end-to-end test must fail rather than silently skip the family.
    """

    here = Path(__file__).resolve()
    repo_root = here.parents[2]
    index_path = repo_root / "vectors" / "revoke" / "index.json"
    if not index_path.exists():  # pragma: no cover - vectors must exist
        pytest.skip(f"revoke vectors index not found at {index_path}")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return set(payload.get("revoke_reason_coverage", []))


# ---------------------------------------------------------------------------
# Reference simulator (Not Normative) — minimal §9.5 surface.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class HpViewEvent:
    """A single record on the Human_Prime view channel.

    Mirrors the §EH.3 push-to-HP envelope at the granularity needed by
    §9.5: the HP must see ``mandate_id`` and ``RevokeReason`` (plus a
    monotonic timestamp).
    """

    mandate_id: str
    reason: str
    ts_ms: int


@dataclass(frozen=True)
class RpAuditEvent:
    """A single record on the Relying_Party audit-log.

    Per Requirement 3.2 the audit-log carries ``(error_code, mandate_id,
    ts, RP_id, reason)`` for every error-class rejection. For decoupling
    signals the relevant code is ``E_REVOKED`` (1006) or ``E_RR_UNAVAILABLE``
    (1011); we expose ``reason`` directly so the assertion can match the
    RevokeReason without parsing payloads.
    """

    mandate_id: str
    reason: str
    ts_ms: int
    error_code: str = "E_REVOKED"


@dataclass
class Simulator:
    """Minimal reference simulator for design.md §9.5 four families.

    The simulator runs on a **monotonic clock** ``self._now_ms`` (always
    non-decreasing). Only :meth:`advance` mutates the clock. All state
    transitions are deterministic functions of the clock value, the
    Mandate's last presence-signal time, and the trigger events the test
    enqueues.
    """

    mandate_id: str
    issuer: str = "hp:alice"
    subject: str = "fay:bob-laptop"
    rp_id: str = "rp:test-001"

    _now_ms: int = 0
    _hp_view: list[HpViewEvent] = field(default_factory=list)
    _rp_audit: list[RpAuditEvent] = field(default_factory=list)
    _ac_node_failed: bool = False
    _last_presence_ms: int = 0
    _presence_stale_armed: bool = False
    _disconnected_since_ms: int | None = None
    _hp_unreachable_since_ms: int | None = None
    _revoked_reason: str | None = None

    # ------------------------------------------------------------------
    # Clock primitives
    # ------------------------------------------------------------------
    def now(self) -> int:
        return self._now_ms

    def advance(self, delta_ms: int) -> None:
        """Advance the monotonic clock by a strictly non-negative delta."""

        if delta_ms < 0:
            raise ValueError(
                "monotonic clock cannot move backward "
                "(tasks.md §6.4 requires monotonic time)"
            )
        target = self._now_ms + delta_ms
        # Advance in 1-second increments so the simulator can detect
        # stale-presence / reconcile-timeout / hp-unreachable thresholds
        # crossed between explicit events.
        while self._now_ms < target:
            step = min(SAMPLE_CADENCE_MS, target - self._now_ms)
            self._now_ms += step
            self._tick()

    def _tick(self) -> None:
        """Per-tick deterministic state evaluation."""

        # 异常：Attestation Chain node failure → immediate revoke.
        if self._ac_node_failed and self._revoked_reason is None:
            self._publish_revoke(REASON_FAY_CREDENTIAL_INVALID)
            return

        # 失联：HumanReachabilityBudget elapsed.
        if self._hp_unreachable_since_ms is not None and self._revoked_reason is None:
            elapsed = self._now_ms - self._hp_unreachable_since_ms
            if elapsed >= HUMAN_REACHABILITY_BUDGET_MS:
                self._publish_revoke(REASON_HUMAN_PRIME_UNREACHABLE)
                return

        # 被动：Presence stale → Disconnected → reconcile timeout → Revoked.
        # Only evaluated when the test explicitly arms the passive family
        # via :meth:`presence_stale`. This avoids cross-family contamination:
        # the HP-unreachable family must not race the presence-stale path
        # before its own trigger fires, and the pre-trigger sanity test
        # must observe a clean baseline.
        if self._presence_stale_armed and self._revoked_reason is None:
            stale_age = self._now_ms - self._last_presence_ms
            if stale_age >= PRESENCE_MAX_STALENESS_MS:
                if self._disconnected_since_ms is None:
                    self._disconnected_since_ms = self._now_ms
                else:
                    in_disconnected = (
                        self._now_ms - self._disconnected_since_ms
                    )
                    if in_disconnected >= RECONCILE_TIMEOUT_MS:
                        self._publish_revoke(REASON_TERMINAL_DISCONNECTED)
                        return

    # ------------------------------------------------------------------
    # Trigger events (the four §9.5 categories)
    # ------------------------------------------------------------------
    def hp_revoke(self) -> None:
        """主动脱钩 — HP issues an explicit REVOKE."""

        if self._revoked_reason is None:
            self._publish_revoke(REASON_HUMAN_INITIATED)

    def fail_attestation_chain_node(self) -> None:
        """异常脱钩 — flip the AC node-failed flag (revoke happens on _tick)."""

        self._ac_node_failed = True

    def hp_becomes_unreachable(self) -> None:
        """失联脱钩 — start the HumanReachabilityBudget countdown."""

        if self._hp_unreachable_since_ms is None:
            self._hp_unreachable_since_ms = self._now_ms

    def presence_stale(self) -> None:
        """被动脱钩 — arm and trigger the presence-stale path.

        Sets ``_presence_stale_armed`` so subsequent ticks evaluate the
        passive-decoupling state machine, then forces the last presence
        signal beyond ``PRESENCE_MAX_STALENESS_MS`` so the very next tick
        enters Disconnected.
        """

        self._presence_stale_armed = True
        # Move the last presence beyond max-staleness so the next _tick()
        # immediately enters Disconnected and starts the reconcile timer.
        self._last_presence_ms = self._now_ms - PRESENCE_MAX_STALENESS_MS - 1

    # ------------------------------------------------------------------
    # Refresh signals (used by the negative / pre-trigger branches)
    # ------------------------------------------------------------------
    def refresh_presence(self) -> None:
        self._last_presence_ms = self._now_ms
        self._disconnected_since_ms = None
        self._presence_stale_armed = False

    def hp_becomes_reachable(self) -> None:
        self._hp_unreachable_since_ms = None

    # ------------------------------------------------------------------
    # Internal: publish a Revoke to HP view + RP audit-log atomically.
    # ------------------------------------------------------------------
    def _publish_revoke(self, reason: str) -> None:
        if self._revoked_reason is not None:  # idempotent (Requirement 4.3.1)
            return
        self._revoked_reason = reason
        self._hp_view.append(
            HpViewEvent(mandate_id=self.mandate_id, reason=reason, ts_ms=self._now_ms)
        )
        self._rp_audit.append(
            RpAuditEvent(
                mandate_id=self.mandate_id,
                reason=reason,
                ts_ms=self._now_ms,
                error_code="E_REVOKED",
            )
        )

    # ------------------------------------------------------------------
    # Observers
    # ------------------------------------------------------------------
    def hp_view(self) -> list[HpViewEvent]:
        return list(self._hp_view)

    def rp_audit(self) -> list[RpAuditEvent]:
        return list(self._rp_audit)


# ---------------------------------------------------------------------------
# Acceptance helper
# ---------------------------------------------------------------------------
def assert_co_observed_within_budget(
    sim: Simulator,
    *,
    expected_reason: str,
    family_label: str,
    budget_ms: int = DECOUPLING_OBSERVABILITY_BUDGET_MS,
    cadence_ms: int = SAMPLE_CADENCE_MS,
) -> None:
    """Drive the simulator forward in fixed-cadence ticks and assert co-observability.

    The acceptance bar (tasks.md §6.4) is:

      ``family signal triggered at t = 0 ⟹ HP view ∋ reason
        ∧ RP audit-log ∋ reason  within  t ≤ budget_ms``

    where both observers see a record with the exact ``expected_reason``
    for the same ``mandate_id``. Each sample is taken on a monotonic
    clock (no wall-clock reads).
    """

    t0 = sim.now()
    last_hp_count = 0
    last_audit_count = 0

    while sim.now() - t0 <= budget_ms:
        # Sample current observers.
        hp = sim.hp_view()
        rp = sim.rp_audit()

        # Make sure observers grow monotonically — channel records must
        # never be dropped or reordered (Requirement 3.3.1 / §EH.3).
        assert len(hp) >= last_hp_count, (
            f"{family_label}: HP view shrank from {last_hp_count} to {len(hp)}"
        )
        assert len(rp) >= last_audit_count, (
            f"{family_label}: RP audit-log shrank from "
            f"{last_audit_count} to {len(rp)}"
        )
        last_hp_count, last_audit_count = len(hp), len(rp)

        hp_match = [e for e in hp if e.mandate_id == sim.mandate_id and e.reason == expected_reason]
        rp_match = [
            e for e in rp if e.mandate_id == sim.mandate_id and e.reason == expected_reason
        ]
        if hp_match and rp_match:
            elapsed = sim.now() - t0
            assert elapsed <= budget_ms, (
                f"{family_label}: co-observability appeared at +{elapsed}ms, "
                f"exceeds budget {budget_ms}ms"
            )
            # Both events MUST refer to the same monotonic instant —
            # design.md §9.5 contract: "RP and HP observe simultaneously".
            # We allow a single-tick drift (cadence) because the simulator
            # publishes both records atomically inside _publish_revoke,
            # but external implementations may stagger the two channels.
            ts_drift = abs(hp_match[-1].ts_ms - rp_match[-1].ts_ms)
            assert ts_drift <= cadence_ms, (
                f"{family_label}: HP/RP timestamp drift {ts_drift}ms "
                f"exceeds one sample cadence ({cadence_ms}ms)"
            )
            return

        if sim.now() - t0 >= budget_ms:
            break
        sim.advance(cadence_ms)

    # If we exit the loop without matching, the signal was not co-observed.
    pytest.fail(
        f"{family_label}: did not see RevokeReason={expected_reason!r} on "
        f"both HP view and RP audit-log within {budget_ms}ms. "
        f"Final HP view = {sim.hp_view()!r}; "
        f"final RP audit = {sim.rp_audit()!r}."
    )


def _enumerate_families() -> Iterable[tuple[str, str, str]]:
    """Yield ``(family_label, trigger_attr, expected_reason)`` triples."""

    return (
        ("主动 (active HP REVOKE)", "hp_revoke", REASON_HUMAN_INITIATED),
        (
            "被动 (presence stale → reconcile timeout)",
            "presence_stale",
            REASON_TERMINAL_DISCONNECTED,
        ),
        (
            "异常 (Attestation Chain node failure)",
            "fail_attestation_chain_node",
            REASON_FAY_CREDENTIAL_INVALID,
        ),
        (
            "失联 (HP unreachable > HumanReachabilityBudget)",
            "hp_becomes_unreachable",
            REASON_HUMAN_PRIME_UNREACHABLE,
        ),
    )


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "family_label, trigger_attr, expected_reason",
    list(_enumerate_families()),
    ids=lambda v: v if isinstance(v, str) else None,
)
def test_decoupling_co_observable_within_60s(
    family_label: str,
    trigger_attr: str,
    expected_reason: str,
    revoke_reasons_in_vectors: set[str],
) -> None:
    """4/4 decoupling signals MUST land on HP view + RP audit-log within 60 s.

    **Validates: Requirements 9.4** — every §9.5 category produces
    matching ``RevokeReason`` records on both observers within the
    Requirement 9.4.6 acceptance bar (60 s).
    """

    # Sanity: the reason we will assert must also appear in vectors/revoke
    # so the conformance surface stays consistent with task 3.5.
    assert expected_reason in revoke_reasons_in_vectors, (
        f"{family_label}: expected reason {expected_reason!r} not enumerated "
        f"by vectors/revoke/index.json. Tasks 3.5 / 6.4 must agree on the "
        f"RevokeReason list."
    )

    # 失联 path needs a budget large enough to elapse
    # HumanReachabilityBudget (30 min default). 60 s is far less than
    # 30 min, so we override the simulator's default budget *only for
    # this family* to keep the §9.5 acceptance contract testable. The
    # spec wording guarantees ≤ 60 s observability *after the revoke
    # decision*, not after the start of HP unreachability; design.md
    # §9.5 row "失联脱钩" says the protocol response is "auto Revoke
    # with reason=human-prime-unreachable", and §9.4.6 then mandates
    # ≤ 60 s co-observability of that Revoke.
    if expected_reason == REASON_HUMAN_PRIME_UNREACHABLE:
        sim = Simulator(mandate_id=f"mandate:{expected_reason}")
        getattr(sim, trigger_attr)()  # start the HP-unreachable timer at t=0
        # Fast-forward exactly to HumanReachabilityBudget so the very
        # next tick triggers the auto-Revoke. From that instant the 60 s
        # co-observability budget kicks in.
        sim.advance(HUMAN_REACHABILITY_BUDGET_MS)
    else:
        sim = Simulator(mandate_id=f"mandate:{expected_reason}")
        sim.refresh_presence()  # establish a fresh baseline before triggering
        getattr(sim, trigger_attr)()

    assert_co_observed_within_budget(
        sim,
        expected_reason=expected_reason,
        family_label=family_label,
    )


def test_monotonic_clock_rejects_backward_advance() -> None:
    """Simulator's monotonic-clock contract MUST refuse negative deltas.

    **Validates: Requirements 9.4** — ``tasks.md §6.4`` mandates a
    unified monotonic clock; this guard prevents accidental wall-clock
    drift from the test driver.
    """

    sim = Simulator(mandate_id="mandate:monotonic-guard")
    sim.advance(1_000)
    with pytest.raises(ValueError, match="monotonic"):
        sim.advance(-1)


def test_revoke_publish_is_idempotent() -> None:
    """Once published, a Revoke MUST NOT duplicate on later triggers.

    **Validates: Requirements 4.3.1** — Revoked is a terminal state and
    repeated triggers are no-ops at the HP view / RP audit observability
    layer. This safeguards against a §9.5 race where two families fire
    in sequence.
    """

    sim = Simulator(mandate_id="mandate:idempotent")
    sim.refresh_presence()
    sim.hp_revoke()
    sim.advance(1_000)
    sim.hp_revoke()  # second trigger must be a no-op
    sim.fail_attestation_chain_node()  # later AC failure must be a no-op too
    sim.advance(2_000)

    hp = sim.hp_view()
    rp = sim.rp_audit()
    assert len(hp) == 1, f"HP view duplicated revoke records: {hp!r}"
    assert len(rp) == 1, f"RP audit duplicated revoke records: {rp!r}"
    assert hp[0].reason == REASON_HUMAN_INITIATED
    assert rp[0].reason == REASON_HUMAN_INITIATED


def test_no_co_observability_before_trigger() -> None:
    """Before any trigger fires, both observers MUST be empty.

    Sanity guard against a model that always reports ``revoked``: in the
    absence of a §9.5 decoupling event the HP view and RP audit-log must
    contain zero records (Requirement 4.3 contrapositive: ``Active`` is
    not equivalent to ``Revoked``).
    """

    sim = Simulator(mandate_id="mandate:pre-trigger")
    sim.refresh_presence()
    sim.advance(30_000)  # half the observability budget without any trigger
    assert sim.hp_view() == []
    assert sim.rp_audit() == []
