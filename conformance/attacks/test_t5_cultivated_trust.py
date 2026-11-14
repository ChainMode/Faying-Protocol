"""Faying Protocol/1.0 — End-to-end T5 *Cultivated Trust Manipulation* conformance test.

Covers ``tasks.md §6.9 T5 刻板信任培养模拟``.

**Validates: Requirements 13.5** (T5 Behavior_Baseline 与 Action Reputation Decay)
**Property: P18.5** (design.md §12 Property 18.5 — Behavior_Baseline_Witness)
**Design anchors**:

* design.md §3.6 (Behavior_Baseline_Service — interface ``record /
  evaluate / decay`` and invariants I-BBS-1..3);
* design.md §9.10.6 (T5 Cultivated Trust Manipulation — four
  protocol-level protections: Behavior_Baseline 维护, 超基线触发额外见证,
  Action Reputation Decay, 基线计算口径写入审计链);
* design.md §12 P18.5 (formal invariant — extra-witness antecedent +
  ``trust_score`` step bound + ``TrustCap``);
* design.md §EH.1 (1010 ``E_HUMAN_WITNESS_REQUIRED``);
* design.md §3.3 (Attestation Chain).

Acceptance-criteria coverage (``tasks.md §6.9`` 验收 row, mirrored to
requirements.md §13.5):

* §13.5.2 — 突发高风险动作必触发 ``E_HUMAN_WITNESS_REQUIRED`` (1010).
  Pinned by :class:`TestBurstHighRiskRejection` and the cultivated-
  trust scenarios below.
* §13.5.3 — 信任分超过 ``TrustCap`` 必被截断 (I-BBS-1). Pinned by
  :class:`TestTrustCapTruncation`.
* §13.5.4 — 超基线触发额外见证事件必写入 Attestation Chain 并推送至
  HP 视野通道 (I-BBS-2). Pinned by :class:`TestAttestationChainAudit`
  and :func:`test_t5_cultivated_trust_chain_audit_under_max_score`.

Scope (``tasks.md §6.9`` 内容 row)
----------------------------------

This module is the **end-to-end cultivated-trust attack simulation**,
counterpart to the property-based test
``pbt.tests.test_p18_5_behavior_baseline_witness``. The PBT module
fuzzes random "long benign + sudden burst" trajectories against the §12
P18.5 invariant; this test feeds **fixed adversary scenarios** through
the *same reference decision model* so the two suites validate the
same model from independent angles. Three adversary scenarios are
exercised explicitly per ``tasks.md §6.9`` 内容 row:

1. **长期低风险累积 → 突发高风险**：iFay 通过持续低风险动作拉长基线，
   再尝试突袭高敏感动作; 仍必须返回 ``E_HUMAN_WITNESS_REQUIRED`` 且
   I-BBS-2 审计链条目落地 (§13.5.2 / §13.5.4).
2. **信任分接近 ``TrustCap`` 时稀释攻击**：在重复加分使 ``trust_score``
   逼近 / 触顶 ``TrustCap`` 后再发起突袭; 信任分被截断在 ``TrustCap``
   且突袭仍被拒 (§13.5.2 / §13.5.3 / I-BBS-1).
3. **混合时间衰减场景**：在突袭前夹杂随机长度的衰减窗口; 基线
   ``deviation`` 不被衰减影响; 突袭仍被拒 + 审计链条目仍落地.

The reference :class:`MandateService` is **Not Normative** — it wraps
the §12 P18.5 reference primitives imported from the P18.5 PBT module
with a thin Attestation Chain recorder so the I-BBS-2 / §13.5.4 audit
obligation becomes observable. Any divergence between this module and
design.md §3.6 / §9.10.6 / §12 P18.5 is a bug in this file.

Reuse strategy — this test imports the reference primitives verbatim
from ``pbt/tests/test_p18_5_behavior_baseline_witness.py`` so both the
property and end-to-end suites probe the same decision model. The
import is wired through a local ``sys.path`` shim (the PBT tree is not
packaged) and gracefully skips the module if the PBT tree is absent
from a partial checkout.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

import pytest


# ---------------------------------------------------------------------------
# Reuse the §12 P18.5 reference primitives from the PBT module.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_PBT_TESTS = _REPO_ROOT / "pbt" / "tests"

if not _PBT_TESTS.exists():  # pragma: no cover - partial checkout guard
    pytest.skip(
        "pbt/tests/ is not present in this checkout; the T5 conformance "
        "test relies on the P18.5 reference primitives.",
        allow_module_level=True,
    )

if str(_PBT_TESTS) not in sys.path:
    sys.path.insert(0, str(_PBT_TESTS))

from test_p18_5_behavior_baseline_witness import (  # type: ignore[import-not-found]  # noqa: E402
    ACCEPTED,
    ADMISSIBLE_WITNESS_PRINCIPALS,
    DEVIATION_DIMENSIONS,
    E_HUMAN_WITNESS_REQUIRED,
    ERROR_CODES,
    HIGH_SENSITIVITY,
    WITNESS_HP,
    WITNESS_SUPERVISORY,
    AtomicAction,
    Baseline,
    BaselineDeviation,
    BehaviorSample,
    Call,
    DecisionResult,
    TrustState,
    Witness,
    build_baseline,
    deviation,
    evaluate_call,
    extra_witness_provided,
    require_extra_witness,
    update_trust,
)


# ---------------------------------------------------------------------------
# Test-suite-local constants — fixed identifiers and scenario tuning knobs.
# ---------------------------------------------------------------------------
HP: str = "hp:alice"
FAY: str = "fay:phi"
HP_OTHER: str = "hp:bob"
FAY_OTHER: str = "fay:psi"

# A "long" benign accumulation as called out by ``tasks.md §6.9`` 内容
# row — large enough that the iFay can plausibly claim a stable baseline
# before pivoting to the high-risk burst.
BENIGN_VOLUME: int = 64

# Closed envelope of benign tokens — the §3.6 ``BehaviorSample`` axes
# (``scope_used`` / ``affected_resources``) are populated from this set
# so the burst's deviation predicate has a meaningful "novelty" signal.
COMMON_SCOPE: tuple[str, ...] = ("read", "list")
COMMON_RESOURCES: tuple[str, ...] = ("res:acct", "res:profile")
NOVEL_SCOPE: str = "transfer"
NOVEL_RESOURCE: str = "res:treasury"

# Trust-score scenario knobs — chosen to drive the §9.10.6 #3 / I-BBS-1
# saturation behaviour through both the "near-cap" and "well-over-cap"
# accumulation paths.
TRUST_CAP: float = 100.0
SATURATION_CREDIT_PER_STEP: float = 30.0  # > TRUST_CAP / 4 ⇒ saturates fast
SATURATION_STEPS: int = 20                # 20 × 30 = 600 ≫ TRUST_CAP


# Sanity guards — fail loudly if the imported module's invariants drift.
assert HIGH_SENSITIVITY == frozenset({"high", "critical"}), (
    "design.md §3.6 / §12 P18.5 pin the high-sensitivity subset to "
    "{high, critical}; the imported module disagrees."
)
assert ERROR_CODES[E_HUMAN_WITNESS_REQUIRED] == 1010, (
    "design.md §EH.1 pins E_HUMAN_WITNESS_REQUIRED to numeric code 1010."
)
assert ADMISSIBLE_WITNESS_PRINCIPALS == frozenset(
    {WITNESS_HP, WITNESS_SUPERVISORY}
), (
    "design.md §9.10.6 #2 admits exactly Human_Prime / Supervisory_Agent "
    "as extra-witness principals; the imported module disagrees."
)
assert set(DEVIATION_DIMENSIONS) == {
    "risk_level",
    "scope_used",
    "affected_resources",
}, (
    "design.md §3.6 BaselineDeviation.dimensions enumerates exactly the "
    "three axes; the imported module disagrees."
)


# ---------------------------------------------------------------------------
# Audit / view-channel projections for the §3.6 I-BBS-2 obligation.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class AttestationChainEntry:
    """One §3.3 Attestation Chain entry recording a §13.5.4 audit event.

    The §3.6 invariant **I-BBS-2** reads "每次 *超基线触发额外见证* 的事件
    必须写入 Attestation Chain 并推送至 HP 视野通道". The trigger is
    **firing of the §12 P18.5 antecedent** (high-sensitivity AND
    deviation), not the verdict — so an accepted-with-witness call still
    produces a chain entry, mirroring the audit semantics of §EH.3.
    """

    sequence: int                    # zero-based monotonic counter
    hp: str
    fay: str
    action: AtomicAction
    deviation_dimensions: tuple[str, ...]
    verdict: str                     # ACCEPTED | E_HUMAN_WITNESS_REQUIRED
    extra_witness_principal: str | None
    extra_witness_valid: bool
    trust_score_at_event: float      # snapshot at the time of the call
    trust_cap: float                 # immutable per-pair TrustCap
    ts_ms: int


@dataclass(frozen=True)
class HPViewEntry:
    """One push on the Human_Prime view channel for a §13.5.4 audit event.

    Cross-linked to the corresponding :class:`AttestationChainEntry` by
    ``chain_sequence`` so an auditor reading the chain and a
    ``Human_Prime`` watching the view channel must observe the same set
    of events (the I-BBS-2 co-observability leg, mirroring §9.10.7 #3
    in the T6 dispatcher).
    """

    chain_sequence: int
    hp: str
    fay: str
    verdict: str
    ts_ms: int


# ---------------------------------------------------------------------------
# Reference Mandate_Service — wraps the P18.5 primitives + audit recorder.
# ---------------------------------------------------------------------------
@dataclass
class MandateService:
    """Reference §3.6 Mandate_Service projection for §13.5 / I-BBS-1..2.

    Composes the imported P18.5 primitives with two pieces of state that
    make the §13.5.4 audit obligation observable end-to-end:

    1. ``samples`` — per-(hp, fay) :class:`BehaviorSample` history. The
       :meth:`evaluate` method recomputes the baseline from scratch so
       the deviation predicate is always evaluated against the
       *current* historical envelope (matches §3.6
       ``BehaviorBaselineService.evaluate``).
    2. ``trust_state`` — per-(hp, fay) :class:`TrustState`. Each
       ``record_evidence`` / ``decay`` call applies :func:`update_trust`
       so the running score honours the §9.10.6 #3 / I-BBS-1
       step-bound + ``TrustCap`` truncation.

    Side-effect channels:

    * ``attestation_chain`` — append-only list of
      :class:`AttestationChainEntry` (I-BBS-2 chain leg).
    * ``hp_view_channel`` — append-only list of :class:`HPViewEntry`
      (I-BBS-2 view-channel leg).
    """

    trust_cap: float = TRUST_CAP
    samples: dict[tuple[str, str], list[BehaviorSample]] = field(
        default_factory=dict
    )
    trust_state: dict[tuple[str, str], TrustState] = field(default_factory=dict)
    attestation_chain: list[AttestationChainEntry] = field(default_factory=list)
    hp_view_channel: list[HPViewEntry] = field(default_factory=list)

    # ------------------------------------------------------------------
    # Behavior baseline maintenance.
    # ------------------------------------------------------------------
    def record_benign(self, sample: BehaviorSample) -> None:
        """Append one §3.6 ``BehaviorSample`` to the per-(hp, fay) history.

        Mirrors ``BehaviorBaselineService.record``. No deviation is
        evaluated here — that happens on the high-sensitivity ``call``
        path (:meth:`evaluate`).
        """

        key = (sample.issuer, sample.subject)
        self.samples.setdefault(key, []).append(sample)

    def baseline_for(self, hp: str, fay: str) -> Baseline:
        """Return the current ``Baseline(hp, fay, t)`` snapshot."""

        return build_baseline(
            self.samples.get((hp, fay), []), issuer=hp, subject=fay
        )

    # ------------------------------------------------------------------
    # Trust-score maintenance — §9.10.6 #3 / I-BBS-1.
    # ------------------------------------------------------------------
    def _trust_for(self, hp: str, fay: str) -> TrustState:
        return self.trust_state.setdefault(
            (hp, fay),
            TrustState(score=0.0, cap=self.trust_cap, last_update_ms=0),
        )

    def record_evidence(
        self,
        hp: str,
        fay: str,
        *,
        now_ms: int,
        decay_coef: float = 1.0,
        new_evidence_credit: float = 0.0,
    ) -> TrustState:
        """Apply one ``record + decay`` step to the (hp, fay) trust score.

        Returns the post-update state so callers can chain assertions
        directly on the truncated value.
        """

        state = self._trust_for(hp, fay)
        next_state = update_trust(
            state,
            now_ms=now_ms,
            decay_coef=decay_coef,
            new_evidence_credit=new_evidence_credit,
        )
        # I-BBS-1 — every transition must respect ``score ≤ cap``.
        assert next_state.score <= self.trust_cap + 1e-9, (
            "I-BBS-1 violated: post-update score "
            f"{next_state.score} exceeds TrustCap={self.trust_cap}"
        )
        self.trust_state[(hp, fay)] = next_state
        return next_state

    # ------------------------------------------------------------------
    # Decision path — §12 P18.5 + I-BBS-2 audit recorder.
    # ------------------------------------------------------------------
    def evaluate(self, call: Call) -> DecisionResult:
        """Evaluate one ``call`` against the current per-(hp, fay) baseline.

        On firing of the §12 P18.5 antecedent (high-sensitivity AND
        deviation), this method **always** appends an
        :class:`AttestationChainEntry` and a paired :class:`HPViewEntry`
        — irrespective of whether a valid extra witness is provided —
        per §13.5.4 / I-BBS-2: the audit obligation is keyed on the
        antecedent, not the verdict.
        """

        baseline = self.baseline_for(call.issuer, call.subject)
        result = evaluate_call(call, baseline)

        if not result.require_extra_witness:
            # Antecedent didn't fire — §13.5.4 audit obligation does not
            # apply (other §9.10.x protections handle non-burst calls).
            return result

        trust_now = self._trust_for(call.issuer, call.subject)
        principal = (
            call.extra_witness.principal if call.extra_witness else None
        )
        valid = bool(call.extra_witness and call.extra_witness.valid)
        sequence = len(self.attestation_chain)
        entry = AttestationChainEntry(
            sequence=sequence,
            hp=call.issuer,
            fay=call.subject,
            action=call.action,
            deviation_dimensions=result.deviation_dimensions,
            verdict=result.verdict,
            extra_witness_principal=principal,
            extra_witness_valid=valid,
            trust_score_at_event=trust_now.score,
            trust_cap=self.trust_cap,
            ts_ms=call.ts_ms,
        )
        self.attestation_chain.append(entry)
        self.hp_view_channel.append(
            HPViewEntry(
                chain_sequence=sequence,
                hp=call.issuer,
                fay=call.subject,
                verdict=result.verdict,
                ts_ms=call.ts_ms,
            )
        )
        return result


# ---------------------------------------------------------------------------
# Helpers — scenario builders shared across multiple test classes.
# ---------------------------------------------------------------------------
def _benign_samples(
    *,
    hp: str = HP,
    fay: str = FAY,
    n: int = BENIGN_VOLUME,
    start_ms: int = 0,
    step_ms: int = 1_000,
) -> Iterator[BehaviorSample]:
    """Yield ``n`` low-risk samples cycling through the benign envelope."""

    for i in range(n):
        risk = "low" if i % 2 == 0 else "normal"
        scope = (COMMON_SCOPE[i % len(COMMON_SCOPE)],)
        resource = (COMMON_RESOURCES[i % len(COMMON_RESOURCES)],)
        yield BehaviorSample(
            issuer=hp,
            subject=fay,
            action=AtomicAction(
                risk_level=risk,
                scope_used=scope,
                affected_resources=resource,
            ),
            ts_ms=start_ms + i * step_ms,
        )


def _burst_action(
    *,
    risk_level: str = "critical",
    inject_scope: bool = True,
    inject_resource: bool = True,
) -> AtomicAction:
    """Construct a high-risk burst that diverges on requested axes.

    The ``risk_level`` axis always trips against a benign baseline (the
    benign envelope is ``{low, normal}`` only), so the antecedent of
    §12 P18.5 fires unconditionally. ``inject_scope`` and
    ``inject_resource`` add divergences on the other two axes for
    cross-axis coverage.
    """

    scope = (NOVEL_SCOPE,) if inject_scope else (COMMON_SCOPE[0],)
    resource = (NOVEL_RESOURCE,) if inject_resource else (COMMON_RESOURCES[0],)
    return AtomicAction(
        risk_level=risk_level,
        scope_used=scope,
        affected_resources=resource,
    )


def _seeded_service(
    *,
    hp: str = HP,
    fay: str = FAY,
    n: int = BENIGN_VOLUME,
    start_ms: int = 0,
    step_ms: int = 1_000,
    trust_cap: float = TRUST_CAP,
) -> MandateService:
    """Return a :class:`MandateService` pre-loaded with a benign baseline."""

    ms = MandateService(trust_cap=trust_cap)
    for sample in _benign_samples(
        hp=hp, fay=fay, n=n, start_ms=start_ms, step_ms=step_ms
    ):
        ms.record_benign(sample)
    return ms


# ---------------------------------------------------------------------------
# 1. Burst high-risk action MUST trigger E_HUMAN_WITNESS_REQUIRED (§13.5.2).
# ---------------------------------------------------------------------------
class TestBurstHighRiskRejection:
    """``tasks.md §6.9`` 内容 row #1 — long-tail benign + sudden burst.

    Every cell of the (risk_level × axis) cross-product MUST end with
    ``E_HUMAN_WITNESS_REQUIRED`` (1010) when no admissible extra witness
    accompanies the burst, and MUST end with ``ACCEPTED`` once a valid
    HP / Supervisory_Agent witness is supplied. This is the §12 P18.5
    first conjunct end-to-end.
    """

    @pytest.mark.parametrize("burst_risk", sorted(HIGH_SENSITIVITY))
    @pytest.mark.parametrize("axis", DEVIATION_DIMENSIONS)
    def test_burst_without_witness_rejected_with_1010(
        self, burst_risk: str, axis: str
    ) -> None:
        """**Validates: Requirements 13.5.2** — rejection branch.

        For every (high-sensitivity risk_level × deviation axis) cell:
        a long benign baseline followed by a single burst with **no**
        extra witness MUST be rejected with code ``1010``
        (``E_HUMAN_WITNESS_REQUIRED``). The risk_level axis always
        trips because the benign envelope is ``{low, normal}``; the
        scope_used / affected_resources cells additionally inject a
        novel token along the requested axis to exercise that arm of
        the deviation predicate.
        """

        ms = _seeded_service()
        # Build a burst that tips the requested axis on top of risk_level.
        action = AtomicAction(
            risk_level=burst_risk,
            scope_used=(
                (NOVEL_SCOPE,) if axis == "scope_used" else (COMMON_SCOPE[0],)
            ),
            affected_resources=(
                (NOVEL_RESOURCE,)
                if axis == "affected_resources"
                else (COMMON_RESOURCES[0],)
            ),
        )
        call = Call(
            issuer=HP,
            subject=FAY,
            action=action,
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=None,
        )
        result = ms.evaluate(call)

        assert result.verdict == E_HUMAN_WITNESS_REQUIRED, (
            "Req 13.5.2 violated: burst without witness must reject with "
            f"E_HUMAN_WITNESS_REQUIRED, got {result.verdict!r}"
        )
        assert ERROR_CODES[result.verdict] == 1010, (
            "design.md §EH.1 pins E_HUMAN_WITNESS_REQUIRED to code 1010; "
            f"got {ERROR_CODES.get(result.verdict)!r}"
        )
        assert result.require_extra_witness is True
        # And the §12 P18.5 deviation MUST register on at least the
        # requested axis (risk_level always trips, plus the targeted axis).
        assert "risk_level" in result.deviation_dimensions
        if axis != "risk_level":
            assert axis in result.deviation_dimensions, (
                f"P18.5 deviation predicate did not trip on axis {axis!r}: "
                f"got {result.deviation_dimensions}"
            )

    @pytest.mark.parametrize("burst_risk", sorted(HIGH_SENSITIVITY))
    @pytest.mark.parametrize(
        "principal", sorted(ADMISSIBLE_WITNESS_PRINCIPALS)
    )
    def test_burst_with_admissible_witness_is_accepted(
        self, burst_risk: str, principal: str
    ) -> None:
        """**Validates: Requirements 13.5.2** — acceptance branch.

        The same burst MUST be ``ACCEPTED`` when an admissible witness
        (``Human_Prime`` or ``Supervisory_Agent``) with valid signature
        bytes accompanies the call. This pins the converse of the
        rejection branch: absence of the witness is the *sole*
        rejection cause for an exceeded-threshold burst.
        """

        ms = _seeded_service()
        call = Call(
            issuer=HP,
            subject=FAY,
            action=_burst_action(risk_level=burst_risk),
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=Witness(principal=principal, valid=True),
        )
        result = ms.evaluate(call)

        assert result.verdict == ACCEPTED
        # The witness requirement still fires — P18.5 says the *call*
        # is accepted, but the protocol acknowledges that the
        # antecedent held.
        assert result.require_extra_witness is True

    @pytest.mark.parametrize(
        "principal,valid",
        [
            (WITNESS_HP, False),         # admissible principal, invalid bytes
            (WITNESS_SUPERVISORY, False),
            ("iFay_Instance", True),     # surrogate — never admissible
            ("anonymous", True),         # unknown principal
        ],
    )
    def test_inadmissible_or_invalid_witness_still_rejected(
        self, principal: str, valid: bool
    ) -> None:
        """Pin the §9.10.6 #2 admissible-witness set + verifiability gate.

        Anything other than a valid ``Human_Prime`` / ``Supervisory_Agent``
        witness leaves the call indistinguishable from "no witness",
        hence ``1010``.
        """

        ms = _seeded_service()
        call = Call(
            issuer=HP,
            subject=FAY,
            action=_burst_action(),
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=Witness(principal=principal, valid=valid),
        )
        result = ms.evaluate(call)
        assert result.verdict == E_HUMAN_WITNESS_REQUIRED
        assert ERROR_CODES[result.verdict] == 1010

    @pytest.mark.parametrize("low_risk", ("low", "normal"))
    def test_low_risk_call_does_not_engage_p18_5(self, low_risk: str) -> None:
        """Antecedent guard — ``risk_level ∉ {high, critical}`` short-circuits.

        Even when the call introduces novel scope / resource tokens,
        a low/normal risk level keeps the §12 P18.5 antecedent off and
        the audit obligation does not fire (those calls are governed by
        other §9.10.x protections).
        """

        ms = _seeded_service()
        call = Call(
            issuer=HP,
            subject=FAY,
            action=AtomicAction(
                risk_level=low_risk,
                scope_used=(NOVEL_SCOPE,),
                affected_resources=(NOVEL_RESOURCE,),
            ),
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=None,
        )
        result = ms.evaluate(call)
        assert result.verdict == ACCEPTED
        assert result.require_extra_witness is False
        # And no audit chain entry — §13.5.4 obligation only fires on
        # the antecedent firing.
        assert ms.attestation_chain == []
        assert ms.hp_view_channel == []


# ---------------------------------------------------------------------------
# 2. trust_score saturates at TrustCap (§13.5.3 / I-BBS-1).
# ---------------------------------------------------------------------------
class TestTrustCapTruncation:
    """``tasks.md §6.9`` 内容 row #2 — trust-score saturation.

    Action Reputation Decay (§9.10.6 #3 / I-BBS-1) requires the per-pair
    ``trust_score`` to be hard-capped by ``TrustCap``. Repeated high
    credits MUST saturate at the cap, not run away to infinity, and a
    later burst MUST still be rejected without a witness regardless of
    the accumulated score.
    """

    def test_repeated_credits_saturate_at_trust_cap(self) -> None:
        """**Validates: Requirements 13.5.3** — TrustCap truncation.

        Hammer the (hp, fay) pair with ``SATURATION_STEPS`` high-credit
        events under no decay (``decay_coef = 1.0``). The running score
        MUST be hard-capped by ``TrustCap`` from the first step that
        the cumulative credit exceeds ``TrustCap``, and MUST remain at
        ``TrustCap`` for every subsequent step.
        """

        ms = _seeded_service()
        history: list[float] = []
        for k in range(1, SATURATION_STEPS + 1):
            state = ms.record_evidence(
                HP,
                FAY,
                now_ms=k * 1_000,
                decay_coef=1.0,  # no decay — pure accumulation path
                new_evidence_credit=SATURATION_CREDIT_PER_STEP,
            )
            history.append(state.score)

        # Step bound — every transition adds at most ``credit`` net of
        # decay. Without decay this collapses to score(t2) ≤ score(t1)
        # + credit, identical to the §12 P18.5 step inequality.
        for prev, nxt in zip(history, history[1:]):
            assert nxt <= prev + SATURATION_CREDIT_PER_STEP + 1e-9, (
                "Req 13.5.3 violated: trust_score step bound broken — "
                f"prev={prev}, credit={SATURATION_CREDIT_PER_STEP}, next={nxt}"
            )

        # Cap truncation — every observed score is bounded by TrustCap.
        for i, s in enumerate(history):
            assert s <= TRUST_CAP + 1e-9, (
                f"Req 13.5.3 / I-BBS-1 violated: step {i} produced "
                f"trust_score={s} > TrustCap={TRUST_CAP}"
            )

        # And the tail must be exactly TrustCap — once saturated, the
        # cap is sticky as long as decay stays at 1.0.
        assert history[-1] == pytest.approx(TRUST_CAP, abs=1e-9), (
            "Req 13.5.3 violated: post-saturation tail did not pin to "
            f"TrustCap={TRUST_CAP}, got {history[-1]}"
        )
        # Pre-condition for the saturation claim — the cumulative
        # credit MUST exceed TrustCap; otherwise the test would not
        # actually exercise the truncation branch.
        assert SATURATION_STEPS * SATURATION_CREDIT_PER_STEP > TRUST_CAP

    def test_trust_score_is_per_pair(self) -> None:
        """``trust_score`` is keyed by ``(HP, IF)`` — saturation is per-pair.

        Saturating ``(hp:alice, fay:phi)`` MUST NOT pollute
        ``(hp:bob, fay:psi)`` — the §3.6 BBS interface scopes the
        score to one pair, so a single noisy iFay cannot raise the
        baseline trust of unrelated pairs.
        """

        ms = _seeded_service(hp=HP, fay=FAY)
        # Saturate pair A.
        for k in range(1, SATURATION_STEPS + 1):
            ms.record_evidence(
                HP,
                FAY,
                now_ms=k * 1_000,
                decay_coef=1.0,
                new_evidence_credit=SATURATION_CREDIT_PER_STEP,
            )
        # Pair B has never recorded any evidence — score MUST default
        # to zero, not inherit pair A's saturated value.
        b_state = ms._trust_for(HP_OTHER, FAY_OTHER)
        assert b_state.score == 0.0, (
            "Req 13.5.3 violated: per-pair scope leaked — pair B picked "
            f"up trust_score={b_state.score} from pair A's saturation."
        )

    def test_decay_does_not_amplify_score(self) -> None:
        """Decay coefficient ``∈ (0, 1]`` MUST never amplify the score.

        Pin the lower edge of the decay schedule: ``decay_coef = 0.5``
        with zero new credit must monotonically shrink the score, and
        the score MUST stay non-negative throughout (no underflow).
        """

        ms = _seeded_service()
        # Prime the score to TrustCap.
        ms.record_evidence(
            HP,
            FAY,
            now_ms=1_000,
            decay_coef=1.0,
            new_evidence_credit=TRUST_CAP,
        )
        prev_score = ms._trust_for(HP, FAY).score
        for k in range(2, 10):
            state = ms.record_evidence(
                HP,
                FAY,
                now_ms=k * 1_000,
                decay_coef=0.5,
                new_evidence_credit=0.0,
            )
            assert state.score <= prev_score + 1e-9, (
                "Action Reputation Decay must not amplify the score — "
                f"step {k}: prev={prev_score}, next={state.score}"
            )
            assert state.score >= 0.0, (
                f"trust_score must remain non-negative — got {state.score}"
            )
            prev_score = state.score


# ---------------------------------------------------------------------------
# 3. Attestation Chain audit obligation (§13.5.4 / I-BBS-2).
# ---------------------------------------------------------------------------
class TestAttestationChainAudit:
    """``tasks.md §6.9`` 验收 row #3 — chain audit + HP view co-observability.

    Per §13.5.4 / I-BBS-2: every event in which the §12 P18.5
    antecedent fires MUST append exactly one Attestation Chain entry
    AND push exactly one HP view-channel event. The pair is keyed by
    ``chain_sequence`` so an auditor reading the chain and a
    Human_Prime watching the view channel see the same event log.
    """

    def test_rejected_burst_emits_chain_and_view_entry(self) -> None:
        """**Validates: Requirements 13.5.4** — rejection arm.

        A long benign baseline followed by a no-witness burst MUST
        produce exactly one chain entry AND one HP view-channel push,
        both labelled ``E_HUMAN_WITNESS_REQUIRED``. This is the
        rejection arm of I-BBS-2.
        """

        ms = _seeded_service()
        call = Call(
            issuer=HP,
            subject=FAY,
            action=_burst_action(),
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=None,
        )
        result = ms.evaluate(call)

        assert result.verdict == E_HUMAN_WITNESS_REQUIRED
        assert len(ms.attestation_chain) == 1, (
            "Req 13.5.4 / I-BBS-2 violated: rejected burst did not "
            f"append exactly one chain entry; got "
            f"{len(ms.attestation_chain)}."
        )
        assert len(ms.hp_view_channel) == 1, (
            "Req 13.5.4 / I-BBS-2 violated: rejected burst did not "
            f"push exactly one HP view event; got "
            f"{len(ms.hp_view_channel)}."
        )

        entry = ms.attestation_chain[0]
        view = ms.hp_view_channel[0]
        assert entry.sequence == 0
        assert entry.hp == HP and entry.fay == FAY
        assert entry.verdict == E_HUMAN_WITNESS_REQUIRED
        assert entry.deviation_dimensions, (
            "Req 13.5.4 violated: chain entry must record the §3.6 "
            "BaselineDeviation.dimensions that tripped the antecedent."
        )
        assert "risk_level" in entry.deviation_dimensions
        # Cross-link integrity — chain_sequence MUST point back to the
        # same chain entry (the I-BBS-2 co-observability leg).
        assert view.chain_sequence == entry.sequence
        assert (view.hp, view.fay) == (entry.hp, entry.fay)
        assert view.verdict == entry.verdict
        assert view.ts_ms == entry.ts_ms

    def test_accepted_burst_with_witness_still_emits_chain_entry(self) -> None:
        """**Validates: Requirements 13.5.4** — acceptance arm.

        I-BBS-2 keys the audit obligation on the **antecedent** of
        §12 P18.5, NOT the verdict. So a burst that is accepted because
        a valid HP / Supervisory_Agent witness was supplied MUST still
        produce a chain entry — only this way can an auditor later
        reconstruct that the high-sensitivity policy fired and was
        satisfied (rather than silently bypassed).
        """

        ms = _seeded_service()
        call = Call(
            issuer=HP,
            subject=FAY,
            action=_burst_action(),
            ts_ms=BENIGN_VOLUME * 1_000 + 1,
            extra_witness=Witness(principal=WITNESS_HP, valid=True),
        )
        result = ms.evaluate(call)

        assert result.verdict == ACCEPTED
        assert len(ms.attestation_chain) == 1, (
            "Req 13.5.4 / I-BBS-2 violated: accepted-with-witness burst "
            "did not append a chain entry — the audit obligation keys "
            "on the antecedent, not the verdict."
        )
        entry = ms.attestation_chain[0]
        assert entry.verdict == ACCEPTED
        assert entry.extra_witness_principal == WITNESS_HP
        assert entry.extra_witness_valid is True
        # Co-observability — paired view-channel push.
        assert len(ms.hp_view_channel) == 1
        assert ms.hp_view_channel[0].chain_sequence == entry.sequence
        assert ms.hp_view_channel[0].verdict == ACCEPTED

    def test_chain_entries_isolated_per_hp_fay_pair(self) -> None:
        """Per-pair scope — saturating one pair never logs against another.

        Pins the §3.6 BBS per-pair semantic at the audit layer: a
        burst on ``(hp:alice, fay:phi)`` MUST NOT inject a chain entry
        for ``(hp:bob, fay:psi)``. This is the cross-pair isolation
        invariant the audit obligation relies on.
        """

        ms = _seeded_service(hp=HP, fay=FAY)
        # Seed a benign baseline for pair B as well so its baseline
        # is well-formed (otherwise the deviation predicate would also
        # trip on a bare empty baseline).
        for sample in _benign_samples(hp=HP_OTHER, fay=FAY_OTHER):
            ms.record_benign(sample)

        # Burst on pair A (rejected, witness absent) — chain entry on A.
        ms.evaluate(
            Call(
                issuer=HP,
                subject=FAY,
                action=_burst_action(),
                ts_ms=BENIGN_VOLUME * 1_000 + 1,
                extra_witness=None,
            )
        )
        # Low-risk call on pair B — antecedent does not fire, no entry.
        ms.evaluate(
            Call(
                issuer=HP_OTHER,
                subject=FAY_OTHER,
                action=AtomicAction(
                    risk_level="low",
                    scope_used=(COMMON_SCOPE[0],),
                    affected_resources=(COMMON_RESOURCES[0],),
                ),
                ts_ms=BENIGN_VOLUME * 1_000 + 2,
                extra_witness=None,
            )
        )

        offending_pairs = {(e.hp, e.fay) for e in ms.attestation_chain}
        assert offending_pairs == {(HP, FAY)}, (
            "Req 13.5.4 violated: chain entries leaked beyond the "
            f"offending pair: {offending_pairs}"
        )
        # And the HP view channel mirrors the chain — no extra pushes.
        assert {(v.hp, v.fay) for v in ms.hp_view_channel} == {(HP, FAY)}

    def test_chain_sequence_is_monotonic_and_dense(self) -> None:
        """Every chain entry receives a unique strictly-increasing index.

        Pins §3.3 Attestation Chain ordering: an auditor must be able
        to replay the chain in submission order without gaps, so
        ``sequence`` MUST be ``0, 1, 2, ...`` over the lifetime of the
        ``MandateService`` regardless of which (hp, fay) pair produced
        each entry.
        """

        ms = _seeded_service(hp=HP, fay=FAY)
        for sample in _benign_samples(hp=HP_OTHER, fay=FAY_OTHER):
            ms.record_benign(sample)

        # Three rejected bursts mixed across pairs.
        bursts = [
            (HP, FAY),
            (HP_OTHER, FAY_OTHER),
            (HP, FAY),
        ]
        for i, (hp, fay) in enumerate(bursts):
            ms.evaluate(
                Call(
                    issuer=hp,
                    subject=fay,
                    action=_burst_action(),
                    ts_ms=BENIGN_VOLUME * 1_000 + 10 + i,
                    extra_witness=None,
                )
            )

        sequences = [e.sequence for e in ms.attestation_chain]
        assert sequences == list(range(len(bursts))), (
            "§3.3 chain ordering violated: sequences must be dense "
            f"and monotonically increasing, got {sequences}"
        )
        view_sequences = [v.chain_sequence for v in ms.hp_view_channel]
        assert view_sequences == sequences, (
            "I-BBS-2 co-observability violated: chain and view-channel "
            f"sequences diverged ({sequences} vs {view_sequences})."
        )


# ---------------------------------------------------------------------------
# 4. Composite scenario — TrustCap-saturated dilution attempt + decay mix.
# ---------------------------------------------------------------------------
def test_t5_cultivated_trust_chain_audit_under_max_score() -> None:
    """**Validates: Requirements 13.5.2 + 13.5.3 + 13.5.4** (composite).

    Composite scenario per ``tasks.md §6.9`` 内容 row:

    1. **Long benign accumulation** — ``BENIGN_VOLUME`` low-risk
       samples build the §3.6 Behavior_Baseline.
    2. **Trust-score saturation** — the iFay's ``trust_score`` is
       hammered to ``TrustCap`` to model the cultivated-trust attacker
       (the goal is to "dilute" the future witness requirement).
    3. **Mixed time decay** — alternating decay windows are interleaved
       with the credit hammers so the score traverses a non-trivial
       schedule before the burst.
    4. **Sudden burst** — one critical ``Atomic_Action`` with no extra
       witness, mislabelled to deviate on every axis simultaneously.

    Acceptance gates (``tasks.md §6.9`` 验收 row):

    * 突发高风险动作必触发 ``E_HUMAN_WITNESS_REQUIRED`` (§13.5.2);
    * 信任分超过 ``TrustCap`` 必被截断 (§13.5.3 / I-BBS-1);
    * 超基线触发额外见证事件必写入 Attestation Chain 并推送至 HP 视野
      通道 (§13.5.4 / I-BBS-2).

    The composite scenario is the load-bearing one: it pins that the
    three protocol obligations remain orthogonal — the trust-score
    saturation must not "buy" the iFay any concession on the witness
    requirement, and the audit obligation must fire regardless of how
    the trust score is moving.
    """

    ms = _seeded_service()
    now = BENIGN_VOLUME * 1_000

    # Phase 2 — trust-score saturation. Repeatedly hammer credits well
    # in excess of TrustCap to drive the running score to the cap.
    for k in range(1, SATURATION_STEPS + 1):
        now += 1_000
        ms.record_evidence(
            HP,
            FAY,
            now_ms=now,
            decay_coef=1.0,  # no decay during the saturation hammer
            new_evidence_credit=SATURATION_CREDIT_PER_STEP,
        )
    saturated = ms._trust_for(HP, FAY)
    assert saturated.score == pytest.approx(TRUST_CAP, abs=1e-9), (
        "Req 13.5.3 violated: trust_score did not saturate at "
        f"TrustCap={TRUST_CAP} after {SATURATION_STEPS} × "
        f"{SATURATION_CREDIT_PER_STEP} credits; got {saturated.score}"
    )

    # Phase 3 — mixed decay windows. Even with random-looking decay
    # the score MUST stay bounded by TrustCap and must never go negative.
    decay_schedule = [
        (0.9, 0.0, 60_000),    # gentle decay, no credit
        (0.5, 5.0, 120_000),   # heavy decay + small credit
        (1.0, 0.0, 30_000),    # idle window, no decay no credit
        (0.8, 100.0, 5_000),   # burst credit > residual headroom ⇒ cap truncation
    ]
    for decay_coef, credit, dt in decay_schedule:
        now += dt
        state = ms.record_evidence(
            HP,
            FAY,
            now_ms=now,
            decay_coef=decay_coef,
            new_evidence_credit=credit,
        )
        assert state.score <= TRUST_CAP + 1e-9, (
            "Req 13.5.3 / I-BBS-1 violated under mixed decay schedule: "
            f"score={state.score} exceeded TrustCap={TRUST_CAP}"
        )
        assert state.score >= 0.0

    # Phase 4 — burst with NO extra witness. The §12 P18.5 antecedent
    # must fire (deviation on every axis), the verdict MUST be
    # E_HUMAN_WITNESS_REQUIRED, and the audit obligation MUST land an
    # Attestation Chain entry + HP view-channel push.
    now += 1_000
    burst = AtomicAction(
        risk_level="critical",
        scope_used=(NOVEL_SCOPE,),
        affected_resources=(NOVEL_RESOURCE,),
    )
    call = Call(
        issuer=HP,
        subject=FAY,
        action=burst,
        ts_ms=now,
        extra_witness=None,
    )
    result = ms.evaluate(call)

    # ---------------------------------------------------------------
    # Acceptance 1 — burst rejected with E_HUMAN_WITNESS_REQUIRED.
    # ---------------------------------------------------------------
    assert result.verdict == E_HUMAN_WITNESS_REQUIRED, (
        "Req 13.5.2 violated: cultivated-trust burst did not return "
        f"E_HUMAN_WITNESS_REQUIRED; got {result.verdict!r}"
    )
    assert ERROR_CODES[result.verdict] == 1010
    # Every axis contributed to the deviation (the burst was crafted
    # to maximise the antecedent signal).
    assert set(result.deviation_dimensions) == set(DEVIATION_DIMENSIONS), (
        "Composite burst should trip every §3.6 deviation dimension; "
        f"got {result.deviation_dimensions}"
    )

    # ---------------------------------------------------------------
    # Acceptance 2 — trust score still capped (the saturation attempt
    # did not "leak" past TrustCap during the burst).
    # ---------------------------------------------------------------
    assert ms._trust_for(HP, FAY).score <= TRUST_CAP + 1e-9

    # ---------------------------------------------------------------
    # Acceptance 3 — chain audit + HP view-channel co-observability.
    # ---------------------------------------------------------------
    assert len(ms.attestation_chain) == 1, (
        "Req 13.5.4 / I-BBS-2 violated: composite cultivated-trust "
        f"scenario did not append exactly one chain entry; got "
        f"{len(ms.attestation_chain)}."
    )
    chain_entry = ms.attestation_chain[0]
    assert chain_entry.hp == HP and chain_entry.fay == FAY
    assert chain_entry.verdict == E_HUMAN_WITNESS_REQUIRED
    assert chain_entry.extra_witness_principal is None
    assert chain_entry.extra_witness_valid is False
    # The chain entry must record the trust score AT THE TIME OF the
    # event — the I-BBS-1 / I-BBS-2 audit fingerprint that lets a
    # later auditor see the dilution attempt.
    assert chain_entry.trust_score_at_event <= TRUST_CAP + 1e-9
    assert chain_entry.trust_score_at_event > 0, (
        "Composite scenario should produce a non-zero trust_score "
        "snapshot at audit time — the cultivated-trust attempt is "
        "supposed to inflate the score before the burst."
    )

    assert len(ms.hp_view_channel) == 1
    view_entry = ms.hp_view_channel[0]
    assert view_entry.chain_sequence == chain_entry.sequence
    assert view_entry.verdict == E_HUMAN_WITNESS_REQUIRED


# ---------------------------------------------------------------------------
# 5. Boundary regression — empty baseline + first-ever burst.
# ---------------------------------------------------------------------------
def test_t5_empty_baseline_first_burst_rejected_with_chain_entry() -> None:
    """Empty-baseline edge — the very first call may be a burst.

    Pins the lower edge of the BBS state machine: when no historical
    samples exist for a (hp, fay) pair, the baseline is empty, so any
    high-sensitivity action diverges trivially on every axis. The
    §13.5 audit obligations still apply: rejection with ``1010`` and
    one chain + view-channel entry.
    """

    ms = MandateService(trust_cap=TRUST_CAP)  # no benign seed
    call = Call(
        issuer=HP,
        subject=FAY,
        action=_burst_action(),
        ts_ms=1,
        extra_witness=None,
    )
    result = ms.evaluate(call)

    assert result.verdict == E_HUMAN_WITNESS_REQUIRED
    assert ERROR_CODES[result.verdict] == 1010
    # All three axes diverge against the empty baseline.
    assert set(result.deviation_dimensions) == set(DEVIATION_DIMENSIONS)
    # And the audit obligation lands exactly once.
    assert len(ms.attestation_chain) == 1
    assert len(ms.hp_view_channel) == 1


# ---------------------------------------------------------------------------
# 6. Boundary regression — chain audit fires under both verdicts.
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "extra_witness,expected_verdict",
    [
        (None, E_HUMAN_WITNESS_REQUIRED),
        (Witness(principal=WITNESS_HP, valid=True), ACCEPTED),
        (Witness(principal=WITNESS_SUPERVISORY, valid=True), ACCEPTED),
        (Witness(principal=WITNESS_HP, valid=False), E_HUMAN_WITNESS_REQUIRED),
        (Witness(principal="iFay_Instance", valid=True), E_HUMAN_WITNESS_REQUIRED),
    ],
)
def test_t5_chain_entry_fires_on_antecedent_regardless_of_verdict(
    extra_witness: Witness | None, expected_verdict: str
) -> None:
    """**Validates: Requirements 13.5.4** — antecedent-keyed audit obligation.

    For every ``(extra_witness, expected_verdict)`` cell where the §12
    P18.5 antecedent fires, the chain entry MUST be emitted. The
    matrix covers:

    * no witness → reject + chain entry;
    * valid HP witness → accept + chain entry;
    * valid Supervisory_Agent witness → accept + chain entry;
    * invalid HP witness → reject + chain entry;
    * surrogate principal → reject + chain entry.

    This is the strongest statement of I-BBS-2: chain audit is keyed
    on antecedent firing, NOT on the verdict, so an attacker cannot
    "dodge the audit" by submitting a malformed witness.
    """

    ms = _seeded_service()
    call = Call(
        issuer=HP,
        subject=FAY,
        action=_burst_action(),
        ts_ms=BENIGN_VOLUME * 1_000 + 1,
        extra_witness=extra_witness,
    )
    result = ms.evaluate(call)

    assert result.verdict == expected_verdict
    assert len(ms.attestation_chain) == 1, (
        "Req 13.5.4 violated: chain entry missing for verdict="
        f"{expected_verdict!r}, witness={extra_witness!r}."
    )
    assert len(ms.hp_view_channel) == 1
    entry = ms.attestation_chain[0]
    assert entry.verdict == expected_verdict
    if extra_witness is None:
        assert entry.extra_witness_principal is None
        assert entry.extra_witness_valid is False
    else:
        assert entry.extra_witness_principal == extra_witness.principal
        assert entry.extra_witness_valid == extra_witness.valid
