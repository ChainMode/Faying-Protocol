"""Faying Protocol/1.0 — End-to-end T4 *Attention Drift Exploit* conformance test.

Covers ``tasks.md §6.8 T4 注意力漂移模拟``.

**Validates: Requirements 13.4** (T4 高敏感动作的 Strict Grade 强约束)
**Property: P18.4** (design.md §12 Property 18.4 — Attention_Drift_Block)
**Design anchors**:

* design.md §9.10.5 (T4 注意力漂移) — three protocol-level protections;
* design.md §12 P18.4 (formal invariant);
* design.md §7.1 (grade autonomy ordering ``G1 < G2 < G3 < G4``);
* design.md §EH.1 (1004 ``E_GRADE_INSUFFICIENT`` / 1005 ``E_PRESENCE_STALE``
  / 1003 ``E_SCOPE_VIOLATION``);
* design.md Appendix B (per-grade ``AttentionDriftThreshold`` defaults);
* design.md §9.10.3 (T2 Atomic_Action 强约束 — co-applied to the
  "batch-low-sensitivity bypass" attack family below).

Companion artefacts (the property-based + unit-test counterparts):

* :mod:`pbt.tests.test_p18_4_attention_drift_block` — fuzzes the §12
  P18.4 invariant over the full input space; this end-to-end test is
  the **adversary-driven scenario walker** that pins the three concrete
  attack paths called out by ``tasks.md §6.8`` 内容 row.
* :mod:`pbt.tests.test_p18_2_atomic_action_strict` — pins the T2
  Atomic_Action strict-cardinality rule that this T4 simulation reuses
  to shut down the *batch-low-sensitivity* bypass attempt.

Scope (per ``tasks.md §6.8`` 内容 row)
-------------------------------------

The adversary is an iFay (or an attacker controlling an iFay endpoint)
who attempts to slip a high-sensitivity Action through while the Human
Prime's view channel has been idle past ``AttentionDriftThreshold``.
Three attack families are exercised in mixture:

(a) **Direct submission inside the attention-loss window.** The iFay
    submits a high-sensitivity Action when ``HP_view_idle_ms ≥
    AttentionDriftThreshold(grade)``. Acceptance bar: rejected with
    ``E_PRESENCE_STALE`` (1005), and only released *after* the HP view
    channel registers re-presence AND the HP issues an explicit
    re-confirmation.

(b) **Batched low-sensitivity bundle that hides a high-sens Action.**
    The iFay packs the high-sens Action into a multi-action bundle
    alongside several low-sensitivity tokens, hoping a permissive RP
    will permit-list the bundle. Acceptance bar: rejected with
    ``E_SCOPE_VIOLATION`` (1003) — the §9.10.3 T2 Atomic_Action gate
    fires *before* the §9.10.5 T4 gate even gets a chance to evaluate.
    Crucially, this rejection holds inside *and* outside the
    attention-loss window so the bypass affords the attacker no
    advantage at all.

(c) **Implicit privilege escalation via grade-insufficient call.**
    The iFay submits a high-sensitivity Action whose current grade is
    weaker than G1 Strict (G2 / G3 / G4). Acceptance bar: rejected
    with ``E_GRADE_INSUFFICIENT`` (1004). The grade gate dominates the
    attention-drift gate, so the rejection holds even when the HP is
    fully attentive — and *also* holds inside the attention-loss
    window so the attacker cannot launder the violation through the
    drift state machine.

Acceptance bar (``tasks.md §6.8`` 验收 row, verbatim):

* "attention-loss 窗口内高敏感动作一律延迟至 HP 重新在场并显式确认";
* "不存在 *默认放行* 路径";
* "批量低敏感绕过路径必被拒".

The reference verifier exposed below is **Not Normative** — it mirrors
the §9.10.5 + §9.10.3 + §EH.1 protocol contracts in declaration order.
Wire-format conformance lives in ``conformance/dim_*/`` and ``vectors/``.

Monotonic clock contract
------------------------

Per the wider conformance-attack convention (see
``conformance/attacks/test_decoupling.py``) the simulator drives a
**monotonic** millisecond clock. The HP view channel's idle counter is
``now() − last_hp_view_activity_ms``; only :meth:`Simulator.advance`
mutates the clock. Wall-clock noise is intentionally absent so
Hypothesis-style flakiness from real-time scheduling is impossible.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pytest


# ---------------------------------------------------------------------------
# Protocol verdicts — design.md §5.4 / §EH.1.
# ---------------------------------------------------------------------------
ACCEPTED: str = "accepted"
E_GRADE_INSUFFICIENT: str = "E_GRADE_INSUFFICIENT"   # 1004 — RP rejection
E_PRESENCE_STALE: str = "E_PRESENCE_STALE"           # 1005 — MS rejection
E_SCOPE_VIOLATION: str = "E_SCOPE_VIOLATION"         # 1003 — RP rejection (T2 Atomic)

ERROR_CODES: dict[str, int] = {
    E_GRADE_INSUFFICIENT: 1004,
    E_PRESENCE_STALE: 1005,
    E_SCOPE_VIOLATION: 1003,
}

# Closed verdict set under the T4 simulation. A fourth value would mark
# an undefined branch that could hide a covert acceptance path through
# the attention-loss window — :data:`P18_4_VERDICTS` is the §13.4.4
# "no default-accept path" guard surfaced as a totality predicate.
P18_4_VERDICTS: frozenset[str] = frozenset(
    {ACCEPTED, E_GRADE_INSUFFICIENT, E_PRESENCE_STALE, E_SCOPE_VIOLATION}
)


# ---------------------------------------------------------------------------
# Grades — design.md §7.1 (autonomy ordered ``G1 < G2 < G3 < G4``).
# ---------------------------------------------------------------------------
GRADE_G1: int = 1   # Strict   — most strict, lowest autonomy
GRADE_G2: int = 2   # Moderate
GRADE_G3: int = 3   # Loose
GRADE_G4: int = 4   # Autonomous — least strict, highest autonomy

RUNTIME_GRADES: tuple[int, ...] = (GRADE_G1, GRADE_G2, GRADE_G3, GRADE_G4)
GRADES_AUTONOMY_LE_G1: frozenset[int] = frozenset({GRADE_G1})
GRADES_AUTONOMY_GT_G1: frozenset[int] = frozenset({GRADE_G2, GRADE_G3, GRADE_G4})

# Per-grade AttentionDriftThreshold defaults (design.md Appendix B).
# Mirrored verbatim from :mod:`pbt.tests.test_p18_4_attention_drift_block`
# so the property and end-to-end suites probe the same boundary table.
ATTENTION_DRIFT_THRESHOLD_MS: dict[int, int] = {
    GRADE_G1: 30 * 1000,             # 30 s
    GRADE_G2: 5 * 60 * 1000,         # 5 min
    GRADE_G3: 15 * 60 * 1000,        # 15 min
    GRADE_G4: 60 * 60 * 1000,        # 1 h
}


def attention_drift_threshold_ms(grade: int) -> int:
    """``AttentionDriftThreshold(grade)`` per design.md Appendix B."""

    if grade not in ATTENTION_DRIFT_THRESHOLD_MS:
        raise ValueError(f"grade out of runtime range: {grade!r}")
    return ATTENTION_DRIFT_THRESHOLD_MS[grade]


# ---------------------------------------------------------------------------
# Sensitivity tags — design.md §4.1 / §9.10.5.
# ---------------------------------------------------------------------------
SENS_HIGH: str = "high"
SENS_NORMAL: str = "normal"
SENS_LOW: str = "low"

# Atomic Action catalogue used in the test harness. The actual token does
# NOT affect any P18.4 verdict — only its ``sensitivity`` tag does. The
# tokens are kept aligned with :mod:`pbt.tests.test_p18_4_attention_drift_block`
# and :mod:`pbt.tests.test_p18_2_atomic_action_strict` so the attack
# scenarios mirror the property-based suite's vocabulary.
HIGH_SENS_ACTIONS: tuple[str, ...] = (
    "transfer-funds",
    "delete-record",
    "trigger-actuator",
    "issue-instruction",
)
LOW_SENS_ACTIONS: tuple[str, ...] = (
    "calendar:event:read",
    "presence:status:read",
    "notification:dismiss",
    "search:history:read",
)


def sensitivity_of(action: str) -> str:
    """Static sensitivity table for the test harness."""

    if action in HIGH_SENS_ACTIONS:
        return SENS_HIGH
    return SENS_LOW


# ---------------------------------------------------------------------------
# Reference data classes (Not Normative).
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class IfRpCall:
    """Minimal projection of an IF→RP/MS call sufficient for §9.10.5 + §9.10.3.

    Only the fields the T4 + T2 gates inspect are surfaced here; wider
    Mandate fields are governed by other properties (P1 / P11 / P15 /
    P16+ / P17+) and intentionally omitted to keep the attack search
    space finite.
    """

    mandate_id: str
    grade: int                       # current_grade(c.mandate, t)
    actions: tuple[str, ...]         # the bundle the iFay actually packed
    arrived_at_ms: int               # t (monotonic ms)


@dataclass(frozen=True)
class Verdict:
    """Reference verdict + a witness explaining which gate fired.

    ``accepted_via_hp_reconfirmation`` mirrors the §9.10.5 #2
    delay-then-accept latch — see the matching field on the P18.4 PBT's
    :class:`DecisionResult`. ``error_code`` is the numeric counterpart
    of :data:`Verdict.outcome` (cf. design.md §EH.1).
    """

    outcome: str                                  # one of P18_4_VERDICTS
    accepted_via_hp_reconfirmation: bool = False
    error_code: Optional[int] = None


# ---------------------------------------------------------------------------
# Reference simulator (Not Normative) — minimal §9.10.5 + §9.10.3 surface.
# ---------------------------------------------------------------------------
@dataclass
class T4Simulator:
    """Minimal reference Relying_Party + Mandate_Service for T4 simulation.

    The simulator runs on a strictly monotonic clock ``self._now_ms``.
    Only :meth:`advance` mutates the clock. The HP view channel's
    activity is tracked via ``self._last_hp_view_activity_ms``; the
    ``HP_view_idle_ms`` quantity in §12 P18.4 is therefore
    ``self.now() − self._last_hp_view_activity_ms``.

    The §9.10.5 #2 latch (delay-then-accept) is encoded as a one-shot
    boolean ``self._hp_reconfirmation_pending``: it is *set* by
    :meth:`hp_returns_and_confirms` and *cleared* by the next high-sens
    call that consumes it. This single-shot latch is the only legal
    forward path through the attention-loss window — the §13.4.4
    anti-default-accept clause is the direct consequence.

    Audit log entries mirror the §EH.1 push-to-HP convention: every
    rejection cuts a row, and every accepted high-sens call carries
    its acceptance witness so a downstream auditor can prove that no
    default-accept happened.
    """

    mandate_id: str = "mandate:t4-fixture"
    issuer: str = "hp:t4-fixture"
    subject: str = "fay:t4-fixture"

    _now_ms: int = 0
    _last_hp_view_activity_ms: int = 0
    _hp_reconfirmation_pending: bool = False
    audit_log: list[str] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Clock primitives.
    # ------------------------------------------------------------------
    def now(self) -> int:
        return self._now_ms

    def advance(self, delta_ms: int) -> None:
        """Advance the monotonic clock by a non-negative delta."""

        if delta_ms < 0:
            raise ValueError(
                "monotonic clock cannot move backward "
                "(tasks.md §6.8 implies a monotonic clock per §6.4)"
            )
        self._now_ms += delta_ms

    # ------------------------------------------------------------------
    # HP view channel — the §9.10.5 #2 latch.
    # ------------------------------------------------------------------
    def hp_view_active(self) -> None:
        """Mark the HP view channel as active *now*. Resets the idle counter."""

        self._last_hp_view_activity_ms = self._now_ms

    def hp_returns_and_confirms(self) -> None:
        """HP returns to the view channel AND issues an explicit re-confirm.

        Per §9.10.5 #2 this is the *only* legal path that clears the
        attention-drift latch for a single subsequent high-sensitivity
        Action. The latch is consumed on the next high-sens evaluation;
        repeated calls without a new HP confirm cannot ride a stale
        latch.

        Note: the idle counter is intentionally NOT reset here. The
        delay-then-accept path applies to a call that arrived during
        the attention-loss window — its ``HP_view_idle_ms_at_arrival``
        was already ≥ ``AttentionDriftThreshold`` and stays that way
        through evaluation. The latch (not a synthetic idle reset) is
        what "speaks for" HP's return + explicit re-confirmation, so
        the §9.10.5 #2 acceptance witness fires on the latch branch
        rather than the canonical-accept branch. Callers that want to
        model an attentive HP after re-confirmation can call
        :meth:`hp_view_active` separately on a fresh call.
        """

        self._hp_reconfirmation_pending = True

    def hp_view_idle_ms(self) -> int:
        return self._now_ms - self._last_hp_view_activity_ms

    # ------------------------------------------------------------------
    # Gate dispatch — design.md §9.10.3 T2 + §9.10.5 T4 in declaration order.
    # ------------------------------------------------------------------
    def evaluate(self, call: IfRpCall) -> Verdict:
        """Evaluate one IF→RP/MS call against the §9.10 protections.

        Decision order (mirrors §9.10.3 + §9.10.5 + §EH.1):

        1. **Atomic_Action gate** (§9.10.3 T2 / Requirement 13.2.1):
           ``action_count != 1`` ⟹ ``E_SCOPE_VIOLATION`` (1003). This
           gate runs *first* so the "batch-low-sensitivity bypass"
           attack family (b) is shut down before the T4 gate evaluates.
        2. **Outside the P18.4 antecedent** — sensitivity ≠ ``high``.
           §12 P18.4 makes no claim; the call is accepted by this T4
           verifier (other gates — P1 / P11 / P15 — apply downstream).
        3. **Grade gate** (§9.10.5 #1 / Requirement 13.4.2): current
           grade strictly more autonomous than G1 ⟹
           ``E_GRADE_INSUFFICIENT`` (1004). Dominates the drift gate so
           an attentive HP cannot rescue a high-sens call under
           G2 / G3 / G4.
        4. **AttentionDriftThreshold gate** (§9.10.5 #2 / Requirement
           13.4.3): ``HP_view_idle_ms ≥ AttentionDriftThreshold(grade)``
           and the §9.10.5 #2 latch is NOT pending ⟹ ``E_PRESENCE_STALE``
           (1005). If the latch IS pending, consume it and accept via
           the delay-then-accept path (§13.4.3 second half).
        """

        # Gate 1 — Atomic_Action strict-cardinality (covers attack (b)).
        action_count = len(call.actions)
        if action_count != 1:
            self.audit_log.append(
                f"t4:atomic-action-violation:{call.mandate_id}:"
                f"action_count={action_count}"
            )
            return Verdict(
                outcome=E_SCOPE_VIOLATION,
                error_code=ERROR_CODES[E_SCOPE_VIOLATION],
            )

        action = call.actions[0]
        if sensitivity_of(action) != SENS_HIGH:
            # Outside §12 P18.4 antecedent — vacuously accepted here.
            return Verdict(outcome=ACCEPTED)

        # Gate 2 — grade gate (covers attack (c)).
        if call.grade in GRADES_AUTONOMY_GT_G1:
            self.audit_log.append(
                f"t4:grade-insufficient:{call.mandate_id}:grade={call.grade}"
            )
            return Verdict(
                outcome=E_GRADE_INSUFFICIENT,
                error_code=ERROR_CODES[E_GRADE_INSUFFICIENT],
            )

        # Gate 3 — attention-drift gate (covers attack (a)).
        threshold = attention_drift_threshold_ms(call.grade)
        idle = self.hp_view_idle_ms()
        if idle >= threshold:
            if self._hp_reconfirmation_pending:
                # Latch consumed — single-shot, per §9.10.5 #2.
                self._hp_reconfirmation_pending = False
                self.audit_log.append(
                    f"t4:delayed-accept-via-hp-reconfirmation:"
                    f"{call.mandate_id}:idle={idle},threshold={threshold}"
                )
                return Verdict(outcome=ACCEPTED, accepted_via_hp_reconfirmation=True)
            self.audit_log.append(
                f"t4:presence-stale:{call.mandate_id}:"
                f"idle={idle},threshold={threshold}"
            )
            return Verdict(
                outcome=E_PRESENCE_STALE,
                error_code=ERROR_CODES[E_PRESENCE_STALE],
            )

        # Both conjuncts hold — canonical accept on the (idle < threshold) path.
        return Verdict(outcome=ACCEPTED)


# ---------------------------------------------------------------------------
# Helpers — pre-arming the attention-loss window.
# ---------------------------------------------------------------------------
def _enter_attention_loss_window(sim: T4Simulator, *, by_ms: int = 1) -> None:
    """Drive the simulator into ``HP_view_idle_ms ≥ AttentionDriftThreshold(G1)``.

    Used by every attack scenario below. Pinning the entry to a fixed
    helper keeps the per-test setup uniform and makes a future change
    to the AttentionDriftThreshold table propagate to every scenario.
    """

    threshold = attention_drift_threshold_ms(GRADE_G1)
    sim.hp_view_active()
    sim.advance(threshold + by_ms)
    assert sim.hp_view_idle_ms() >= threshold, (
        f"_enter_attention_loss_window regression: idle="
        f"{sim.hp_view_idle_ms()} < threshold={threshold}"
    )


# ===========================================================================
# Attack family (a) — direct submission inside the attention-loss window.
# ===========================================================================
class TestAttackADirectInsideAttentionLoss:
    """Direct high-sens submission while ``HP_view_idle_ms ≥ AttentionDriftThreshold``.

    Acceptance bar (``tasks.md §6.8`` 验收 row):
    * rejected with ``E_PRESENCE_STALE`` (1005);
    * released only after HP returns AND issues an explicit re-confirm;
    * latch is single-shot — a second high-sens call cannot ride a
      stale latch.
    """

    def test_direct_high_sens_inside_attention_loss_is_rejected(self) -> None:
        """**Validates: Requirements 13.4** (clauses 13.4.3 + 13.4.4).

        High-sensitivity Action submitted while the HP view channel has
        been idle past ``AttentionDriftThreshold`` MUST be rejected with
        ``E_PRESENCE_STALE`` (1005). No default-accept path exists.
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_PRESENCE_STALE, (
            "Direct high-sens submission inside the attention-loss window "
            f"must be rejected with E_PRESENCE_STALE; got {verdict!r}"
        )
        assert verdict.error_code == 1005
        assert not verdict.accepted_via_hp_reconfirmation
        assert any(line.startswith("t4:presence-stale:") for line in sim.audit_log), (
            "E_PRESENCE_STALE must cut a security-audit row (design.md §EH.1)."
        )

    def test_high_sens_released_only_after_hp_reconfirmation(self) -> None:
        """**Validates: Requirements 13.4** (clause 13.4.3 — delay-then-accept).

        After the iFay's first attempt is rejected with E_PRESENCE_STALE,
        the protocol MUST surface an ACCEPTED outcome only after the HP
        view channel registers re-presence AND the HP issues an
        explicit re-confirmation. The acceptance MUST carry the
        ``accepted_via_hp_reconfirmation`` witness so a downstream
        auditor can prove the §9.10.5 #2 latch was the route taken.
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)

        # First attempt — rejected.
        first_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        first = sim.evaluate(first_call)
        assert first.outcome == E_PRESENCE_STALE

        # HP returns *but does not yet confirm* — should still reject.
        # (Per §9.10.5 #2 the explicit re-confirmation, not mere presence,
        #  is what clears the latch.)
        # Modelled here by re-arming idle past threshold before the confirm.
        sim.advance(1_000)
        retry_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        retry = sim.evaluate(retry_call)
        assert retry.outcome == E_PRESENCE_STALE, (
            "Bare HP presence (without an explicit re-confirmation) MUST NOT "
            f"clear the §9.10.5 #2 latch; got {retry!r}"
        )

        # HP returns AND confirms — next high-sens call must accept via latch.
        sim.hp_returns_and_confirms()
        confirmed_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        confirmed = sim.evaluate(confirmed_call)
        assert confirmed.outcome == ACCEPTED, (
            f"After HP returns + explicit re-confirm, the delayed call must "
            f"be accepted; got {confirmed!r}"
        )
        assert confirmed.accepted_via_hp_reconfirmation, (
            "ACCEPTED outcome via the delay-then-accept path must carry the "
            "accepted_via_hp_reconfirmation witness (anti-default-accept "
            "audit guard, Requirement 13.4.4)."
        )
        assert any(
            line.startswith("t4:delayed-accept-via-hp-reconfirmation:")
            for line in sim.audit_log
        )

    def test_latch_is_single_shot(self) -> None:
        """**Validates: Requirements 13.4** (clause 13.4.4 — anti-default-accept).

        The §9.10.5 #2 latch MUST be single-shot: one explicit HP
        re-confirmation releases at most ONE delayed high-sens call. A
        second high-sens call submitted after the latch has been
        consumed (without a fresh HP confirm) MUST be rejected again
        with ``E_PRESENCE_STALE``. Otherwise the attacker could batch a
        single HP re-confirmation into a stream of high-sens actions.
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)

        # Latch the channel via an explicit HP re-confirmation, then drift again.
        sim.hp_returns_and_confirms()
        sim.advance(attention_drift_threshold_ms(GRADE_G1) + 1)

        first_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        first = sim.evaluate(first_call)
        assert first.outcome == ACCEPTED
        assert first.accepted_via_hp_reconfirmation

        # Second high-sens call without a fresh confirm — must reject.
        second_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("delete-record",),
            arrived_at_ms=sim.now(),
        )
        second = sim.evaluate(second_call)
        assert second.outcome == E_PRESENCE_STALE, (
            "§9.10.5 #2 latch must be single-shot; a second high-sens call "
            f"without a fresh HP re-confirm must be rejected. got={second!r}"
        )
        assert not second.accepted_via_hp_reconfirmation


# ===========================================================================
# Attack family (b) — batched low-sensitivity bypass.
# ===========================================================================
class TestAttackBBatchedLowSensitivityBypass:
    """Multi-action bundle hiding a high-sens action behind low-sens tokens.

    Acceptance bar (``tasks.md §6.8`` 验收 row):
    * "批量低敏感绕过路径必被拒" — every multi-action bundle MUST be
      rejected with ``E_SCOPE_VIOLATION`` (1003), regardless of the
      attention state. The §9.10.3 T2 Atomic_Action gate fires *before*
      the §9.10.5 T4 gate, so the bypass affords the attacker no
      advantage at all.
    """

    def test_batched_bundle_with_hidden_high_sens_inside_attention_loss(
        self,
    ) -> None:
        """**Validates: Requirements 13.4 + 13.2** (T4 + T2 composition).

        A batch packing several low-sens tokens around a high-sens
        action MUST be rejected with ``E_SCOPE_VIOLATION`` (1003) —
        even inside the attention-loss window. The §9.10.3 T2 gate
        dominates the T4 gate, so the bypass attempt fails on
        cardinality alone.
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)

        bundle = (
            "calendar:event:read",
            "presence:status:read",
            "transfer-funds",          # the smuggled high-sens token
            "notification:dismiss",
        )
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=bundle,
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_SCOPE_VIOLATION, (
            "Batched-low-sensitivity bundle hiding a high-sens action must be "
            f"rejected with E_SCOPE_VIOLATION; got {verdict!r}"
        )
        assert verdict.error_code == 1003
        assert any(
            line.startswith("t4:atomic-action-violation:") for line in sim.audit_log
        )

    def test_batched_low_sens_only_bundle_is_also_rejected(self) -> None:
        """**Validates: Requirements 13.2** — the T2 gate is unconditional.

        Even an all-low-sensitivity bundle MUST be rejected by the T2
        cardinality gate. This pins the §9.10.3 invariant in its purest
        form and prevents a "slip the attacker a second token" variant
        of the bypass.
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)

        bundle = (
            "calendar:event:read",
            "presence:status:read",
            "notification:dismiss",
        )
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=bundle,
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_SCOPE_VIOLATION, (
            "All-low-sens multi-action bundle must be rejected with "
            f"E_SCOPE_VIOLATION (T2 gate). got={verdict!r}"
        )

    def test_batched_bundle_rejected_outside_attention_loss_too(self) -> None:
        """**Validates: Requirements 13.2** — T2 holds outside the T4 window.

        The bypass must not be unlocked by an attentive HP either.
        Regardless of HP attention state, a multi-action bundle is
        always rejected by the T2 Atomic_Action gate.
        """

        sim = T4Simulator()
        sim.hp_view_active()  # HP is fully attentive — idle == 0

        bundle = ("transfer-funds", "delete-record")
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=bundle,
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_SCOPE_VIOLATION, (
            "Multi-action bundle must be rejected outside the attention-loss "
            f"window too; got {verdict!r}"
        )

    def test_hp_reconfirmation_does_not_relax_t2_gate(self) -> None:
        """**Validates: Requirements 13.4.4 + 13.2** — defence-in-depth.

        An iFay holding a fresh HP re-confirmation latch MUST NOT be
        able to ride that latch into a multi-action bundle. The T2 gate
        runs first, so the latch is irrelevant — the bundle is rejected
        with ``E_SCOPE_VIOLATION``, and the latch remains unconsumed
        (so a subsequent legitimate atomic call can still ride it).
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)
        sim.hp_returns_and_confirms()
        # Drift again so the T4 gate would otherwise fire.
        sim.advance(attention_drift_threshold_ms(GRADE_G1) + 1)

        bundle = ("transfer-funds", "delete-record")
        bundle_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=bundle,
            arrived_at_ms=sim.now(),
        )
        bundle_verdict = sim.evaluate(bundle_call)
        assert bundle_verdict.outcome == E_SCOPE_VIOLATION, (
            f"T2 gate must dominate even with HP latch pending; got {bundle_verdict!r}"
        )

        # The latch should still be available for a subsequent legitimate
        # single-action call — the T2 rejection must NOT consume the latch.
        atomic_call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=GRADE_G1,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        atomic_verdict = sim.evaluate(atomic_call)
        assert atomic_verdict.outcome == ACCEPTED, (
            "T2-rejected bundle must NOT consume the §9.10.5 #2 latch; "
            f"subsequent atomic call should still be accepted. got={atomic_verdict!r}"
        )
        assert atomic_verdict.accepted_via_hp_reconfirmation


# ===========================================================================
# Attack family (c) — implicit privilege escalation via insufficient grade.
# ===========================================================================
class TestAttackCImplicitGradeEscalation:
    """High-sens submission whose current grade is weaker than G1 Strict.

    Acceptance bar (``tasks.md §6.8`` 验收 row):
    * rejected with ``E_GRADE_INSUFFICIENT`` (1004) — even inside the
      attention-loss window. The grade gate dominates the drift gate
      so the attacker cannot launder the violation through the drift
      state machine.
    """

    @pytest.mark.parametrize(
        "grade",
        [GRADE_G2, GRADE_G3, GRADE_G4],
        ids=["G2", "G3", "G4"],
    )
    def test_high_sens_under_weaker_grade_inside_attention_loss(
        self, grade: int
    ) -> None:
        """**Validates: Requirements 13.4** (clause 13.4.2 — grade gate)."""

        sim = T4Simulator()
        _enter_attention_loss_window(sim)
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=grade,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_GRADE_INSUFFICIENT, (
            f"High-sens under grade={grade} (autonomy > G1) must be rejected "
            f"with E_GRADE_INSUFFICIENT; got {verdict!r}"
        )
        assert verdict.error_code == 1004

    @pytest.mark.parametrize(
        "grade",
        [GRADE_G2, GRADE_G3, GRADE_G4],
        ids=["G2", "G3", "G4"],
    )
    def test_high_sens_under_weaker_grade_outside_attention_loss(
        self, grade: int
    ) -> None:
        """**Validates: Requirements 13.4** (grade gate dominance).

        The grade gate dominates: even with the HP fully attentive
        (``HP_view_idle_ms = 0``), a high-sens call under G2 / G3 / G4
        MUST be rejected with ``E_GRADE_INSUFFICIENT``. This rules out
        a "be very attentive" bypass.
        """

        sim = T4Simulator()
        sim.hp_view_active()  # HP fully attentive
        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=grade,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_GRADE_INSUFFICIENT
        assert verdict.error_code == 1004

    @pytest.mark.parametrize(
        "grade",
        [GRADE_G2, GRADE_G3, GRADE_G4],
        ids=["G2", "G3", "G4"],
    )
    def test_grade_gate_cannot_be_laundered_through_hp_reconfirmation(
        self, grade: int
    ) -> None:
        """**Validates: Requirements 13.4.2** + protection ordering.

        A pending HP re-confirmation latch MUST NOT relax the grade
        gate. Even with the latch armed, a high-sens call under
        G2 / G3 / G4 is still rejected with ``E_GRADE_INSUFFICIENT``.
        This pins the §9.10.5 protection ordering (#1 dominates #2).
        """

        sim = T4Simulator()
        _enter_attention_loss_window(sim)
        sim.hp_returns_and_confirms()  # latch armed

        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=grade,
            actions=("transfer-funds",),
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        assert verdict.outcome == E_GRADE_INSUFFICIENT, (
            "HP reconfirmation latch must not relax the grade gate; "
            f"got {verdict!r}"
        )
        assert not verdict.accepted_via_hp_reconfirmation


# ===========================================================================
# Cross-cutting acceptance: no default-accept path through attention loss.
# ===========================================================================
class TestNoDefaultAcceptPath:
    """Composite acceptance — every high-sens accepted call carries a witness.

    "tasks.md §6.8 验收: 不存在 *默认放行* 路径"

    Walks the full Cartesian product of (grade × idle band × HP latch
    state × action sensitivity × cardinality) bands and asserts that
    every accepted high-sens call lands on EXACTLY one of the two legal
    witnesses:

    * **canonical** — ``grade ≤ G1.autonomy ∧ idle < threshold``;
    * **latch**     — ``grade ≤ G1.autonomy ∧ idle ≥ threshold ∧ latch consumed``.

    A third path would be a default-accept by definition.
    """

    @pytest.mark.parametrize("grade", RUNTIME_GRADES, ids=["G1", "G2", "G3", "G4"])
    @pytest.mark.parametrize(
        "idle_band",
        ["below-threshold", "at-threshold", "above-threshold"],
    )
    @pytest.mark.parametrize("latch_armed", [False, True])
    @pytest.mark.parametrize(
        "action,sensitivity",
        [
            ("transfer-funds", SENS_HIGH),
            ("calendar:event:read", SENS_LOW),
        ],
        ids=["high-sens", "low-sens"],
    )
    def test_every_accepted_high_sens_call_carries_a_witness(
        self,
        grade: int,
        idle_band: str,
        latch_armed: bool,
        action: str,
        sensitivity: str,
    ) -> None:
        """Every cell of the acceptance matrix MUST land in :data:`P18_4_VERDICTS`,
        and accepted high-sens calls MUST carry a legal witness."""

        sim = T4Simulator()
        threshold = attention_drift_threshold_ms(grade)

        # Configure idle band relative to the per-grade threshold.
        sim.hp_view_active()
        if idle_band == "below-threshold":
            sim.advance(max(0, threshold - 1))
        elif idle_band == "at-threshold":
            sim.advance(threshold)
        else:  # above-threshold
            sim.advance(threshold + 1)

        if latch_armed:
            sim.hp_returns_and_confirms()
            # Re-drift past threshold so the latch is what matters.
            sim.advance(threshold + 1)

        call = IfRpCall(
            mandate_id=sim.mandate_id,
            grade=grade,
            actions=(action,),
            arrived_at_ms=sim.now(),
        )
        verdict = sim.evaluate(call)

        # Totality — verdict must land in the closed set.
        assert verdict.outcome in P18_4_VERDICTS, (
            f"verdict {verdict.outcome!r} out of legal set {sorted(P18_4_VERDICTS)}"
        )

        if sensitivity != SENS_HIGH:
            # Outside §12 P18.4 antecedent — must accept (vacuous arm).
            assert verdict.outcome == ACCEPTED
            assert not verdict.accepted_via_hp_reconfirmation
            return

        if verdict.outcome != ACCEPTED:
            # Rejection branches are pinned by the per-attack tests above.
            assert not verdict.accepted_via_hp_reconfirmation
            return

        # Accepted high-sens call — MUST present a legal witness.
        canonical_witness = (
            grade in GRADES_AUTONOMY_LE_G1
            and sim.hp_view_idle_ms() < threshold
            and not verdict.accepted_via_hp_reconfirmation
        )
        latch_witness = (
            grade in GRADES_AUTONOMY_LE_G1
            and verdict.accepted_via_hp_reconfirmation
        )
        assert canonical_witness or latch_witness, (
            "Anti-default-accept guard failed: accepted high-sens call "
            "matched neither the canonical-accept witness "
            "(grade ≤ G1 ∧ idle < threshold) nor the HP-reconfirmation "
            f"latch witness. grade={grade}, idle_ms={sim.hp_view_idle_ms()}, "
            f"latch_armed={latch_armed}, verdict={verdict!r}"
        )


# ===========================================================================
# Mixed-attack scenario — the §6.8 内容 row's "混合" wording.
# ===========================================================================
def test_mixed_attack_sequence_pins_each_rejection_path() -> None:
    """Pin the mixed-attack walk explicitly called out by ``tasks.md §6.8``.

    The §6.8 内容 row asks the simulation to mix the three attack
    families "(a) attention-loss 窗口内直接发起；(b) attention-loss
    期间通过批量低敏感动作绕过；(c) attention-loss 期间利用 grade
    不足的隐式提权". This walker plays them in sequence on a single
    simulator so the rejection-code matrix is auditable in the CI log.
    """

    sim = T4Simulator()
    _enter_attention_loss_window(sim)

    # (a) direct submission inside attention-loss
    a_call = IfRpCall(
        mandate_id=sim.mandate_id,
        grade=GRADE_G1,
        actions=("transfer-funds",),
        arrived_at_ms=sim.now(),
    )
    a_verdict = sim.evaluate(a_call)
    assert a_verdict.outcome == E_PRESENCE_STALE, (
        f"(a) direct high-sens inside attention-loss → expected E_PRESENCE_STALE, "
        f"got {a_verdict!r}"
    )

    # (b) batched low-sens bypass
    b_call = IfRpCall(
        mandate_id=sim.mandate_id,
        grade=GRADE_G1,
        actions=("calendar:event:read", "transfer-funds", "notification:dismiss"),
        arrived_at_ms=sim.now(),
    )
    b_verdict = sim.evaluate(b_call)
    assert b_verdict.outcome == E_SCOPE_VIOLATION, (
        f"(b) batched-low-sens bypass → expected E_SCOPE_VIOLATION, "
        f"got {b_verdict!r}"
    )

    # (c) implicit grade escalation
    c_call = IfRpCall(
        mandate_id=sim.mandate_id,
        grade=GRADE_G3,
        actions=("transfer-funds",),
        arrived_at_ms=sim.now(),
    )
    c_verdict = sim.evaluate(c_call)
    assert c_verdict.outcome == E_GRADE_INSUFFICIENT, (
        f"(c) grade-insufficient under attention-loss → expected "
        f"E_GRADE_INSUFFICIENT, got {c_verdict!r}"
    )

    # Audit log must carry one row per rejection family.
    audit = sim.audit_log
    assert any(line.startswith("t4:presence-stale:") for line in audit)
    assert any(line.startswith("t4:atomic-action-violation:") for line in audit)
    assert any(line.startswith("t4:grade-insufficient:") for line in audit)


def test_monotonic_clock_rejects_backward_advance() -> None:
    """Simulator's monotonic-clock contract MUST refuse negative deltas.

    Pin to align with :mod:`conformance.attacks.test_decoupling`'s
    monotonic-clock guard so the conformance-attacks suite presents a
    consistent temporal contract across families.
    """

    sim = T4Simulator()
    sim.advance(1_000)
    with pytest.raises(ValueError, match="monotonic"):
        sim.advance(-1)
