"""Faying Protocol/1.0 — End-to-end T1 social-engineering attack-simulation suite.

Covers ``tasks.md §6.6 T1 社会工程模拟（深度伪造在场 + challenge-response 测试）``.

**Validates: Requirements 13.1** (T1 Spoofing Presence — challenge-response
与多模态组合验证)
**Property: P18.1** (Presence_Challenge_Response — design.md §12.5)
**Design anchors**:

* design.md §9.10.2 — T1 社会工程协议级防护（challenge-response 强约束、
  多模态组合验证、设备健康度联签）；
* design.md §EH.1 — ``E_PRESENCE_STALE`` (1005) / ``E_ATTESTATION_INVALID``
  (1007) 拒绝分支 + 安全审计 + 触发降级 / Revoke；
* design.md §EH.3 — ``E_ATTESTATION_INVALID`` 必入 HP 视野通道；
* design.md §12.5 Property 18.1 — challenge-response + ≥3 多模态信号的
  形式化不变式；
* requirements.md §13.1 子句 1–3 — challenge-response、G1/G2 多模态
  ≥ 3、失败映射到 ``E_PRESENCE_STALE`` / ``E_ATTESTATION_INVALID``。

Scope (per ``tasks.md §6.6`` 内容 row)
--------------------------------------

This module is the **end-to-end attack simulation** counterpart to the
property-based test :mod:`pbt.tests.test_p18_1_presence_challenge_response`.
Whereas the PBT fuzzes the formal P18.1 invariant over an abstract
generator, this suite walks the four concrete adversarial paths called
out by ``tasks.md §6.6``:

a. **Single-signal replay** — re-submit a previously accepted
   ``webauthn-uv-fresh`` or ``face-continuous`` PresenceSignal verbatim.
b. **Deepfake presence** — synthesised video / synthesised fingerprint
   simulator. The forged sample is structurally well-formed but cannot
   bind to a *fresh* server-issued ``nonce + micro-task`` because the
   synthesiser has no access to the live HP's response key.
c. **Multi-modal loss** — G1/G2 grade with one of the three required
   signal types missing.
d. **Challenge-response missing or inconsistent** — the ``challenge``
   is ``⊥`` or the ``challenge_response`` does not verify against the
   server-issued challenge.

Acceptance bar (``tasks.md §6.6`` 验收 row)
-------------------------------------------

* Every forgery path MUST be rejected (no "ACCEPTED" outcome).
* G1/G2 multi-modal loss MUST trigger a downgrade side-effect on the
  affected Mandate (``EFFECT_DOWNGRADE``).
* Challenge-response missing / mismatched MUST surface as either
  ``E_PRESENCE_STALE`` (1005) or ``E_ATTESTATION_INVALID`` (1007).

The reference Presence_Channel exposed here is **Not Normative** — it
mirrors the §9.10.2 enforcement order documented in design.md and is
identical in behaviour to the model in
:mod:`pbt.tests.test_p18_1_presence_challenge_response`. Wire-format
conformance lives in ``vectors/presence/`` and the §5 / §EH catalogue.
Any divergence between this module and the spec is a bug here.
"""

from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass, field
from typing import Iterable, Optional

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st


# ---------------------------------------------------------------------------
# Constants — kept in sync with design.md §5.4 / §EH.1 / §9.10.2.
# ---------------------------------------------------------------------------
ACCEPTED: str = "accepted"
E_PRESENCE_STALE: str = "E_PRESENCE_STALE"          # 1005 — design.md §EH.1
E_ATTESTATION_INVALID: str = "E_ATTESTATION_INVALID"  # 1007 — design.md §EH.1

# Closed set of decisions the §9.10.2 reference channel may emit.
DECISIONS: frozenset[str] = frozenset(
    {ACCEPTED, E_PRESENCE_STALE, E_ATTESTATION_INVALID}
)

# Mandate-side effects triggered by §EH.1 rows. ``EFFECT_REVOKE`` mirrors
# ``E_ATTESTATION_INVALID`` (Any → Revoked); ``EFFECT_DOWNGRADE`` mirrors
# ``E_PRESENCE_STALE`` (Active → Degraded). ``EFFECT_NONE`` belongs to
# the ACCEPTED branch.
EFFECT_NONE: str = "none"
EFFECT_DOWNGRADE: str = "downgrade"
EFFECT_REVOKE: str = "revoke"
EFFECTS: frozenset[str] = frozenset({EFFECT_NONE, EFFECT_DOWNGRADE, EFFECT_REVOKE})

# Faying grades — design.md §7. G0 Emergency Override is a control-plane
# event, not a runtime grade under §9.10.2; it is excluded here.
RUNTIME_GRADES: tuple[int, ...] = (1, 2, 3, 4)

# Strong-presence grades on which the right conjunct of P18.1 is
# non-vacuous (Requirement 13.1.2).
STRONG_PRESENCE_GRADES: frozenset[int] = frozenset({1, 2})

# Minimum concurrent signal types required by §9.10.2 / 13.1.2.
MIN_MULTIMODAL_SIGNALS: int = 3

# Closed enumeration of PresenceSignal.signal_type values mirrored from
# pbt/fap/strategies.PRESENCE_SIGNAL_TYPES (design.md §3.2 / §5.1.2).
# Hard-coded here so the conformance test does not depend on the PBT
# package layout — any future schema change must update both lists.
PRESENCE_SIGNAL_TYPES: tuple[str, ...] = (
    "webauthn-uv-fresh",
    "face-continuous",
    "fingerprint-tap",
    "presence-heartbeat-only",
    "intent-ticket",
)


# ---------------------------------------------------------------------------
# Reference Presence_Signal record (Not Normative).
#
# Mirrors the CDDL ``presence-signal`` map (design.md §4.2 / §5.1.2)
# extended with the ``challenge`` / ``challenge_response`` fields demanded
# by §9.10.2 + Requirement 13.1.1. Real wire payloads carry the challenge
# inside ``device-attestation.payload``; promoting it to a top-level field
# here keeps the attack assertions focused on the §9.10.2 invariant rather
# than on CBOR layout.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class PresenceSignal:
    """One in-presence calibration sample submitted to the PC."""

    mandate_id: str
    grade: int
    nonce: bytes
    # ``challenge = ⊥`` is encoded as ``None`` per the formal definition.
    challenge: Optional[bytes]
    challenge_response: Optional[bytes]
    # Server-issued expected response; verification succeeds iff
    # ``challenge_response == expected_response`` (encodes the
    # ``verify(s.challenge_response, s.challenge) = true`` predicate).
    expected_response: bytes
    signal_types_active: tuple[str, ...]
    produced_at_ms: int


@dataclass(frozen=True)
class Verdict:
    """Outcome of a §9.10.2 PC decision: code + Mandate-side effect."""

    code: str
    effect: str


@dataclass
class _SeenChallenges:
    """``(mandate_id, challenge) → first_seen_ms`` cache.

    Mirrors the seen-set described in design.md §9.2 / §9.10.2: the
    Presence_Channel rejects any second use of an already-consumed
    challenge with ``E_PRESENCE_STALE`` regardless of the rest of the
    payload. Without this guard a successfully-replayed challenge would
    trivially satisfy the left conjunct of P18.1.
    """

    _store: dict[tuple[str, bytes], int] = field(default_factory=dict)

    def first_seen(self, mandate_id: str, challenge: bytes) -> bool:
        key = (mandate_id, bytes(challenge))
        if key in self._store:
            return False
        self._store[key] = 1
        return True


# ---------------------------------------------------------------------------
# Reference Presence_Channel decision (Not Normative) — identical in
# semantics to ``pc_decide`` in
# ``pbt/tests/test_p18_1_presence_challenge_response.py``.
# ---------------------------------------------------------------------------
def pc_decide(signal: PresenceSignal, seen: _SeenChallenges) -> Verdict:
    """Reference §9.10.2 acceptance / rejection.

    The order of checks mirrors Requirement 13.1.3 (任一失败即拒). Replays
    are treated as ``E_PRESENCE_STALE`` so the test catches both
    "missing challenge" and "consumed challenge" branches of
    ``s.challenge ≠ ⊥``.
    """

    # (1) Challenge presence — left conjunct ``s.challenge ≠ ⊥``.
    if signal.challenge is None or signal.challenge_response is None:
        return Verdict(E_ATTESTATION_INVALID, EFFECT_REVOKE)

    # (2) Replay of an already-consumed challenge → treat as stale.
    if not seen.first_seen(signal.mandate_id, signal.challenge):
        return Verdict(E_PRESENCE_STALE, EFFECT_DOWNGRADE)

    # (3) Challenge-response verification — left conjunct
    #     ``verify(s.challenge_response, s.challenge) = true``.
    if signal.challenge_response != signal.expected_response:
        return Verdict(E_ATTESTATION_INVALID, EFFECT_REVOKE)

    # (4) Multi-modal threshold for the strong-presence grades.
    if signal.grade in STRONG_PRESENCE_GRADES:
        unique_signals = set(signal.signal_types_active)
        if len(unique_signals) < MIN_MULTIMODAL_SIGNALS:
            # §9.10.2 / Requirement 13.1.3: missing modality → downgrade.
            return Verdict(E_PRESENCE_STALE, EFFECT_DOWNGRADE)

    return Verdict(ACCEPTED, EFFECT_NONE)


# ---------------------------------------------------------------------------
# Builders — well-formed + adversarial signals.
# ---------------------------------------------------------------------------
_DEFAULT_TRIPLET: tuple[str, ...] = (
    "webauthn-uv-fresh",
    "face-continuous",
    "fingerprint-tap",
)
"""§9.10.2 example triplet: ``webauthn-uv-fresh + face-continuous + 设备 attestation``."""


def _well_formed_signal(
    *,
    mandate_id: str = "mandate:t1-fixture",
    grade: int = 1,
    challenge: bytes = b"\xC0" * 16,
    expected: bytes = b"\xE1" * 32,
    signal_types: tuple[str, ...] = _DEFAULT_TRIPLET,
    produced_at_ms: int = 0,
    nonce: bytes = b"\x00" * 16,
) -> PresenceSignal:
    """Construct a baseline-good signal that ``pc_decide`` MUST ACCEPT."""

    return PresenceSignal(
        mandate_id=mandate_id,
        grade=grade,
        nonce=nonce,
        challenge=challenge,
        challenge_response=expected,
        expected_response=expected,
        signal_types_active=signal_types,
        produced_at_ms=produced_at_ms,
    )


# ---------------------------------------------------------------------------
# Synthesis simulators — emulate deepfake video / fingerprint forgers.
# ---------------------------------------------------------------------------
def _synthesise_face_video_response(
    challenge: bytes,
    *,
    synthesiser_seed: bytes = b"face-video-deepfake-v0",
) -> bytes:
    """Produce a *deepfake* face-continuous response.

    A synthesised video frame can mimic the visual texture of the live
    HP but it cannot derive the *anti-deepfake* response signature that
    binds the micro-task to the server-issued ``nonce``. We model this
    by deriving the synthesised response from the challenge plus a
    simulator-specific seed; the live HP, in contrast, would derive its
    response from the challenge plus its private response key
    (``expected``). The two derivations differ deterministically.
    """

    return hashlib.sha256(synthesiser_seed + b"|" + challenge).digest()


def _synthesise_fingerprint_response(
    challenge: bytes,
    *,
    simulator_seed: bytes = b"fingerprint-simulator-v0",
) -> bytes:
    """Produce a fingerprint-simulator response.

    Same model as the face-video deepfake: the simulator can replay a
    captured fingerprint feature vector but cannot bind to the live
    challenge.
    """

    return hashlib.sha256(simulator_seed + b"|" + challenge + b"|fp").digest()


# ---------------------------------------------------------------------------
# Group A — Single-signal replay (path (a) in tasks.md §6.6).
# ---------------------------------------------------------------------------
class TestSingleSignalReplay:
    """Replay of ``webauthn-uv-fresh`` or ``face-continuous`` MUST be rejected.

    **Validates: Requirements 13.1** (challenge-response strong constraint —
    challenge replay defeats the left conjunct of P18.1).

    Single-signal replay is the simplest form of T1: capture a
    legitimate PresenceSignal off the wire and re-submit it verbatim.
    Per design.md §9.10.2 the ``(mandate_id, challenge)`` seen-set
    rejects the replay with ``E_PRESENCE_STALE`` and triggers a
    downgrade — even if the original signal would otherwise have been
    accepted at G1 with a multi-modal triplet. The multi-modal
    threshold MUST NOT mask the replay rejection.
    """

    @pytest.mark.parametrize("replayed_type", ["webauthn-uv-fresh", "face-continuous"])
    def test_single_signal_replay_at_g1_is_rejected(self, replayed_type: str) -> None:
        seen = _SeenChallenges()
        # First arrival is a legitimate, multi-modal G1 signal that
        # incidentally exercises the ``replayed_type`` modality.
        signal = _well_formed_signal(
            mandate_id=f"mandate:replay-{replayed_type}",
            grade=1,
            signal_types=("webauthn-uv-fresh", "face-continuous", "fingerprint-tap"),
        )
        first = pc_decide(signal, seen)
        assert first.code == ACCEPTED, (
            f"baseline single-modality replay setup must accept the first "
            f"arrival; got {first.code!r}"
        )

        # Same byte-identical signal re-submitted by the attacker.
        replay_verdict = pc_decide(signal, seen)
        assert replay_verdict.code == E_PRESENCE_STALE, (
            f"replay of {replayed_type!r} signal must yield E_PRESENCE_STALE; "
            f"got {replay_verdict.code!r}"
        )
        assert replay_verdict.effect == EFFECT_DOWNGRADE, (
            f"requirements.md §13.1.3: challenge replay must trigger "
            f"downgrade on the affected Mandate; got {replay_verdict.effect!r}"
        )

    @pytest.mark.parametrize("replayed_type", ["webauthn-uv-fresh", "face-continuous"])
    @pytest.mark.parametrize("grade", RUNTIME_GRADES)
    def test_single_signal_replay_each_grade(
        self, replayed_type: str, grade: int
    ) -> None:
        """Replay rejection holds at *every* runtime grade.

        The §9.10.2 seen-set is grade-independent — any successful
        rebound of a stale challenge would let an attacker bypass the
        protocol regardless of the current authorisation tier.
        """

        # Use a multi-modal triplet at G1/G2 so the multi-modal
        # threshold does not pre-empt the replay rejection. At G3/G4 a
        # single signal is allowed by P18.1 but the replay still fails.
        if grade in STRONG_PRESENCE_GRADES:
            types: tuple[str, ...] = ("webauthn-uv-fresh", "face-continuous", "fingerprint-tap")
        else:
            types = (replayed_type,)
        seen = _SeenChallenges()
        signal = _well_formed_signal(
            mandate_id=f"mandate:replay-{replayed_type}-g{grade}",
            grade=grade,
            signal_types=types,
        )
        first = pc_decide(signal, seen)
        assert first.code == ACCEPTED

        replay = pc_decide(signal, seen)
        assert replay.code == E_PRESENCE_STALE
        assert replay.effect == EFFECT_DOWNGRADE

    def test_n_way_single_signal_replay_admits_exactly_one(self) -> None:
        """Flooding the channel with the same captured signal: 1 ACCEPTED, N-1 stale.

        Mirrors the cardinality form of P9 but applied to the §9.10.2
        challenge-response seen-set. Without this guard an attacker
        could amplify a single legitimate capture into many "fresh"
        Presence updates.
        """

        n = 6
        seen = _SeenChallenges()
        signal = _well_formed_signal(
            mandate_id="mandate:n-way-replay",
            grade=1,
            signal_types=_DEFAULT_TRIPLET,
        )
        verdicts = [pc_decide(signal, seen) for _ in range(n)]
        accepted = [v for v in verdicts if v.code == ACCEPTED]
        rejected = [v for v in verdicts if v.code == E_PRESENCE_STALE]
        assert len(accepted) == 1, (
            f"single-signal n-way replay must accept exactly one, got "
            f"{len(accepted)}; verdicts={[v.code for v in verdicts]!r}"
        )
        assert len(rejected) == n - 1
        for v in rejected:
            assert v.effect == EFFECT_DOWNGRADE


# ---------------------------------------------------------------------------
# Group B — Deepfake presence (path (b) in tasks.md §6.6).
# ---------------------------------------------------------------------------
class TestDeepfakePresence:
    """Synthesised video / fingerprint MUST be rejected at the challenge step.

    **Validates: Requirements 13.1** (challenge-response 反深伪挑战).

    A deepfake video can mimic the live HP's appearance but cannot
    derive the live response signature that binds the server-issued
    ``nonce + micro-task`` (e.g. random head-turn or short-phrase
    reading). The simulator's ``challenge_response`` therefore differs
    from ``expected_response``; per design.md §9.10.2 the PC MUST
    reject with ``E_ATTESTATION_INVALID`` and trigger Revoke.
    """

    def test_deepfake_face_video_rejected_with_attestation_invalid(self) -> None:
        challenge = b"deepfake-face-challenge-1234567890"[:16]
        expected = b"\xA0" * 32  # the legitimate HP's response.
        forged = _synthesise_face_video_response(challenge)
        # Pre-condition: the synthesiser cannot collide with the live HP.
        assert forged != expected, (
            "test fixture invariant: synthesised response must differ from "
            "the live HP's response — otherwise the deepfake threat model "
            "is mis-configured"
        )

        signal = PresenceSignal(
            mandate_id="mandate:deepfake-face",
            grade=1,
            nonce=b"\x10" * 16,
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID, (
            f"deepfake face-video MUST yield E_ATTESTATION_INVALID; "
            f"got {verdict.code!r}"
        )
        assert verdict.effect == EFFECT_REVOKE, (
            f"requirements.md §13.1.3: failed challenge-response on a "
            f"deepfake must trigger Revoke; got {verdict.effect!r}"
        )

    def test_synthetic_fingerprint_simulator_rejected_with_attestation_invalid(
        self,
    ) -> None:
        challenge = b"fp-sim-challenge-9876543210abcdef"[:16]
        expected = b"\xB0" * 32
        forged = _synthesise_fingerprint_response(challenge)
        assert forged != expected

        signal = PresenceSignal(
            mandate_id="mandate:fingerprint-sim",
            grade=2,
            nonce=b"\x20" * 16,
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE

    def test_deepfake_with_full_multimodal_still_rejected(self) -> None:
        """Even a deepfake that ships a ≥3 multi-modal payload is rejected.

        Pins the Requirement 13.1 invariant that multi-modal presence
        is **necessary but not sufficient**: a synthesised triplet still
        fails the challenge-response check on every modality, so the
        rejection comes from the §9.10.2 step (3) gate, not the step (4)
        threshold.
        """

        challenge = b"\xCC" * 16
        expected = b"\xDD" * 32
        forged = _synthesise_face_video_response(challenge)

        signal = PresenceSignal(
            mandate_id="mandate:deepfake-full-modal",
            grade=1,
            nonce=b"\x30" * 16,
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=tuple(PRESENCE_SIGNAL_TYPES),  # all 5
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE

    @given(
        synthesiser_seed=st.binary(min_size=4, max_size=64),
        challenge=st.binary(min_size=16, max_size=32),
        expected=st.binary(min_size=16, max_size=32),
        grade=st.sampled_from(RUNTIME_GRADES),
    )
    @settings(
        max_examples=200,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
    )
    def test_random_deepfake_simulators_never_accepted(
        self,
        synthesiser_seed: bytes,
        challenge: bytes,
        expected: bytes,
        grade: int,
    ) -> None:
        """Random deepfake-simulator seeds MUST NOT collide with the live response.

        Models the practical attacker who tries thousands of synthesiser
        configurations. Each random seed produces a distinct forgery;
        none should be accepted unless the forgery happens to collide
        with the live HP's response (a negligible-probability event on
        a 32-byte SHA-256 digest, which we assume away to keep the
        property tight).
        """

        forged = hashlib.sha256(synthesiser_seed + b"|" + challenge).digest()
        assume(forged != expected)  # negligible-probability collision

        # G1/G2 must include a multi-modal triplet so the rejection is
        # attributable to the challenge-response step, not the
        # multi-modal threshold.
        if grade in STRONG_PRESENCE_GRADES:
            types: tuple[str, ...] = _DEFAULT_TRIPLET
        else:
            types = ("face-continuous",)
        signal = PresenceSignal(
            mandate_id="mandate:random-deepfake",
            grade=grade,
            nonce=os.urandom(16),
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=types,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID, (
            f"random deepfake forgery accepted: forged={forged.hex()[:16]}..., "
            f"expected={expected.hex()[:16]}..., grade=G{grade}"
        )
        assert verdict.effect == EFFECT_REVOKE


# ---------------------------------------------------------------------------
# Group C — Multi-modal loss (path (c) in tasks.md §6.6).
# ---------------------------------------------------------------------------
class TestMultiModalLoss:
    """G1/G2 with any of the three required signal types missing MUST downgrade.

    **Validates: Requirements 13.1.2 + 13.1.3**.

    Per §9.10.2 the protocol requires ≥ 3 concurrent in-presence signal
    types at G1 Strict and G2 Moderate. Dropping any one signal — even
    when the remaining signals carry valid challenge-responses — MUST
    yield ``E_PRESENCE_STALE`` and trigger a downgrade. This is the
    explicit acceptance row in ``tasks.md §6.6`` (G1/G2 多模态丢失任一
    信号 → 必触发降级).
    """

    @pytest.mark.parametrize("grade", sorted(STRONG_PRESENCE_GRADES))
    @pytest.mark.parametrize(
        "dropped",
        ["webauthn-uv-fresh", "face-continuous", "fingerprint-tap"],
    )
    def test_g1_g2_drop_one_of_three_required_signals(
        self, grade: int, dropped: str
    ) -> None:
        remaining = tuple(t for t in _DEFAULT_TRIPLET if t != dropped)
        assert len(remaining) == MIN_MULTIMODAL_SIGNALS - 1

        signal = _well_formed_signal(
            mandate_id=f"mandate:drop-{dropped}-g{grade}",
            grade=grade,
            signal_types=remaining,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_PRESENCE_STALE, (
            f"G{grade} with {dropped!r} dropped must yield E_PRESENCE_STALE; "
            f"got {verdict.code!r}"
        )
        assert verdict.effect == EFFECT_DOWNGRADE, (
            f"tasks.md §6.6: G{grade} multi-modal loss MUST trigger downgrade; "
            f"got {verdict.effect!r}"
        )

    @pytest.mark.parametrize("grade", sorted(STRONG_PRESENCE_GRADES))
    @pytest.mark.parametrize("count", (0, 1, 2))
    def test_g1_g2_below_threshold_each_count(self, grade: int, count: int) -> None:
        """Strict / Moderate grades reject signals carrying ``count < 3`` modalities."""

        types = _DEFAULT_TRIPLET[:count]
        signal = _well_formed_signal(
            mandate_id=f"mandate:below-threshold-g{grade}-{count}",
            grade=grade,
            signal_types=types,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_PRESENCE_STALE
        assert verdict.effect == EFFECT_DOWNGRADE

    @pytest.mark.parametrize("grade", sorted(STRONG_PRESENCE_GRADES))
    def test_g1_g2_three_unique_signals_accepted(self, grade: int) -> None:
        """Sanity row: G1/G2 with exactly the §9.10.2 example triplet accepts."""

        signal = _well_formed_signal(
            mandate_id=f"mandate:triplet-g{grade}",
            grade=grade,
            signal_types=_DEFAULT_TRIPLET,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == ACCEPTED, (
            "without a sanity-accept row the downgrade properties above "
            "could be vacuously satisfied by an over-restrictive verifier"
        )
        assert verdict.effect == EFFECT_NONE

    @pytest.mark.parametrize("grade", (3, 4))
    def test_g3_g4_single_signal_accepted(self, grade: int) -> None:
        """G3/G4 are out-of-scope for the multi-modal threshold (§9.10.2)."""

        signal = _well_formed_signal(
            mandate_id=f"mandate:g{grade}-single-modal",
            grade=grade,
            signal_types=("presence-heartbeat-only",),
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == ACCEPTED
        assert verdict.effect == EFFECT_NONE

    @given(
        grade=st.sampled_from(sorted(STRONG_PRESENCE_GRADES)),
        types=st.lists(
            st.sampled_from(PRESENCE_SIGNAL_TYPES),
            min_size=0,
            max_size=2,
            unique=True,
        ).map(tuple),
    )
    @settings(
        max_examples=100,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
    )
    def test_random_g1_g2_below_threshold_always_downgrades(
        self, grade: int, types: tuple[str, ...]
    ) -> None:
        assert len(set(types)) < MIN_MULTIMODAL_SIGNALS

        signal = _well_formed_signal(
            mandate_id="mandate:rand-below-threshold",
            grade=grade,
            signal_types=types,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_PRESENCE_STALE
        assert verdict.effect == EFFECT_DOWNGRADE


# ---------------------------------------------------------------------------
# Group D — Challenge-response missing or inconsistent (path (d)).
# ---------------------------------------------------------------------------
class TestChallengeResponseInconsistency:
    """Missing / mismatched challenge-response MUST surface as 1005 or 1007.

    **Validates: Requirements 13.1.1 + 13.1.3**.

    Per ``tasks.md §6.6`` 验收 row: ``challenge-response 不一致 →
    E_PRESENCE_STALE 或 E_ATTESTATION_INVALID``. The §9.10.2 enforcement
    order pins each branch:

    * ``challenge = ⊥``               → ``E_ATTESTATION_INVALID`` + Revoke
    * ``challenge_response = ⊥``      → ``E_ATTESTATION_INVALID`` + Revoke
    * stale ``challenge`` (replayed)  → ``E_PRESENCE_STALE`` + Downgrade
    * mismatched ``challenge_response`` → ``E_ATTESTATION_INVALID`` + Revoke
    """

    @pytest.mark.parametrize("grade", RUNTIME_GRADES)
    def test_missing_challenge_at_each_grade(self, grade: int) -> None:
        signal = PresenceSignal(
            mandate_id="mandate:missing-challenge",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=None,
            challenge_response=b"\xAB" * 32,
            expected_response=b"\xAB" * 32,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE

    @pytest.mark.parametrize("grade", RUNTIME_GRADES)
    def test_missing_challenge_response_at_each_grade(self, grade: int) -> None:
        signal = PresenceSignal(
            mandate_id="mandate:missing-response",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=b"\xAB" * 16,
            challenge_response=None,
            expected_response=b"\xCD" * 32,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE

    @pytest.mark.parametrize("grade", RUNTIME_GRADES)
    def test_mismatched_challenge_response_at_each_grade(self, grade: int) -> None:
        signal = PresenceSignal(
            mandate_id="mandate:mismatched-response",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=b"\x12" * 16,
            challenge_response=b"\x34" * 32,
            expected_response=b"\x56" * 32,  # ≠ above
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE

    def test_replayed_challenge_yields_e_presence_stale(self) -> None:
        """A previously-consumed challenge MUST resurface as 1005, not 1007.

        The order of checks in ``pc_decide`` deliberately puts the replay
        check ahead of the response-verification check so that an
        attacker re-using a captured ``(challenge, challenge_response)``
        pair surfaces as ``E_PRESENCE_STALE`` (a presence-loss event)
        rather than as ``E_ATTESTATION_INVALID``. This keeps the §EH.1
        rotate / downgrade branches consistent with the §9.2 anti-replay
        semantics.
        """

        seen = _SeenChallenges()
        signal = _well_formed_signal(
            mandate_id="mandate:cr-replay",
            grade=2,
            signal_types=_DEFAULT_TRIPLET,
        )
        first = pc_decide(signal, seen)
        assert first.code == ACCEPTED
        replayed = pc_decide(signal, seen)
        assert replayed.code == E_PRESENCE_STALE
        assert replayed.effect == EFFECT_DOWNGRADE

    @given(
        challenge=st.binary(min_size=16, max_size=32),
        response=st.binary(min_size=16, max_size=32),
        expected=st.binary(min_size=16, max_size=32),
        grade=st.sampled_from(RUNTIME_GRADES),
    )
    @settings(
        max_examples=200,
        deadline=None,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
    )
    def test_random_mismatch_always_attestation_invalid(
        self,
        challenge: bytes,
        response: bytes,
        expected: bytes,
        grade: int,
    ) -> None:
        """Random ``challenge_response != expected_response`` MUST reject.

        Hypothesis-driven counterpart to the parametrised mismatch test.
        ``assume`` discards the negligible-probability collision so the
        property remains decidable.
        """

        assume(response != expected)

        # Strong-presence grades use a multi-modal triplet so the
        # rejection is attributable to step (3) of ``pc_decide``.
        if grade in STRONG_PRESENCE_GRADES:
            types: tuple[str, ...] = _DEFAULT_TRIPLET
        else:
            types = ("face-continuous",)
        signal = PresenceSignal(
            mandate_id="mandate:rand-mismatch",
            grade=grade,
            nonce=os.urandom(16),
            challenge=challenge,
            challenge_response=response,
            expected_response=expected,
            signal_types_active=types,
            produced_at_ms=0,
        )
        verdict = pc_decide(signal, _SeenChallenges())
        assert verdict.code == E_ATTESTATION_INVALID
        assert verdict.effect == EFFECT_REVOKE


# ---------------------------------------------------------------------------
# 5. Coverage matrix — every (path, grade) cell is exercised.
#
# This parametrised test acts as the human-readable "matrix table" of
# the §6.6 attack scenarios. It is redundant with the class-level tests
# above but makes the path × grade coverage explicit at-a-glance, which
# the §6.6 acceptance criteria call out by name.
# ---------------------------------------------------------------------------
_T1Case = tuple[str, str, int, str, str]
"""Tuple shape: ``(label, attack_path, grade, expected_code, expected_effect)``."""


def _enumerate_t1_matrix() -> Iterable[_T1Case]:
    """Yield the (path, grade, expected) cells covered by ``tasks.md §6.6``."""

    paths = ("replay", "deepfake-face", "deepfake-fingerprint", "missing-challenge",
             "missing-response", "mismatched-response")
    for path in paths:
        for grade in RUNTIME_GRADES:
            if path == "replay":
                yield (
                    f"replay/g{grade}",
                    path,
                    grade,
                    E_PRESENCE_STALE,
                    EFFECT_DOWNGRADE,
                )
            elif path in ("deepfake-face", "deepfake-fingerprint"):
                yield (
                    f"{path}/g{grade}",
                    path,
                    grade,
                    E_ATTESTATION_INVALID,
                    EFFECT_REVOKE,
                )
            elif path == "missing-challenge":
                yield (
                    f"missing-challenge/g{grade}",
                    path,
                    grade,
                    E_ATTESTATION_INVALID,
                    EFFECT_REVOKE,
                )
            elif path == "missing-response":
                yield (
                    f"missing-response/g{grade}",
                    path,
                    grade,
                    E_ATTESTATION_INVALID,
                    EFFECT_REVOKE,
                )
            elif path == "mismatched-response":
                yield (
                    f"mismatched-response/g{grade}",
                    path,
                    grade,
                    E_ATTESTATION_INVALID,
                    EFFECT_REVOKE,
                )
    # Dedicated G1/G2 multi-modal-loss row — only meaningful at strong
    # presence grades.
    for grade in sorted(STRONG_PRESENCE_GRADES):
        yield (
            f"multimodal-loss/g{grade}",
            "multimodal-loss",
            grade,
            E_PRESENCE_STALE,
            EFFECT_DOWNGRADE,
        )


_T1_MATRIX: tuple[_T1Case, ...] = tuple(_enumerate_t1_matrix())


def _build_attack_signal(path: str, grade: int) -> tuple[PresenceSignal, _SeenChallenges]:
    """Compose the (signal, pre-loaded seen-set) pair for one matrix cell."""

    seen = _SeenChallenges()

    if path == "replay":
        signal = _well_formed_signal(
            mandate_id=f"mandate:matrix-replay-g{grade}",
            grade=grade,
            signal_types=_DEFAULT_TRIPLET if grade in STRONG_PRESENCE_GRADES
                else ("webauthn-uv-fresh",),
        )
        # Pre-load the seen-set so the next ``pc_decide`` sees a replay.
        first = pc_decide(signal, seen)
        assert first.code == ACCEPTED
        return signal, seen

    if path == "deepfake-face":
        challenge = hashlib.sha256(f"matrix-df-face-g{grade}".encode()).digest()[:16]
        expected = hashlib.sha256(f"matrix-df-face-expected-g{grade}".encode()).digest()
        forged = _synthesise_face_video_response(challenge)
        signal = PresenceSignal(
            mandate_id=f"mandate:matrix-df-face-g{grade}",
            grade=grade,
            nonce=hashlib.sha256(f"nonce-df-face-g{grade}".encode()).digest()[:16],
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        return signal, seen

    if path == "deepfake-fingerprint":
        challenge = hashlib.sha256(f"matrix-df-fp-g{grade}".encode()).digest()[:16]
        expected = hashlib.sha256(f"matrix-df-fp-expected-g{grade}".encode()).digest()
        forged = _synthesise_fingerprint_response(challenge)
        signal = PresenceSignal(
            mandate_id=f"mandate:matrix-df-fp-g{grade}",
            grade=grade,
            nonce=hashlib.sha256(f"nonce-df-fp-g{grade}".encode()).digest()[:16],
            challenge=challenge,
            challenge_response=forged,
            expected_response=expected,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        return signal, seen

    if path == "missing-challenge":
        signal = PresenceSignal(
            mandate_id=f"mandate:matrix-no-challenge-g{grade}",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=None,
            challenge_response=b"\xAA" * 32,
            expected_response=b"\xAA" * 32,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        return signal, seen

    if path == "missing-response":
        signal = PresenceSignal(
            mandate_id=f"mandate:matrix-no-response-g{grade}",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=b"\xBB" * 16,
            challenge_response=None,
            expected_response=b"\xCC" * 32,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        return signal, seen

    if path == "mismatched-response":
        signal = PresenceSignal(
            mandate_id=f"mandate:matrix-mismatch-g{grade}",
            grade=grade,
            nonce=b"\x00" * 16,
            challenge=b"\xDD" * 16,
            challenge_response=b"\xEE" * 32,
            expected_response=b"\xFF" * 32,
            signal_types_active=_DEFAULT_TRIPLET,
            produced_at_ms=0,
        )
        return signal, seen

    if path == "multimodal-loss":
        # Multi-modal loss is only defined at G1/G2; caller is expected
        # to filter the (path, grade) pair via ``_enumerate_t1_matrix``.
        signal = _well_formed_signal(
            mandate_id=f"mandate:matrix-modal-loss-g{grade}",
            grade=grade,
            signal_types=("webauthn-uv-fresh", "face-continuous"),  # 2 < 3
        )
        return signal, seen

    raise AssertionError(f"unknown attack path: {path!r}")  # pragma: no cover


@pytest.mark.parametrize(
    "label,path,grade,expected_code,expected_effect",
    _T1_MATRIX,
    ids=[c[0] for c in _T1_MATRIX],
)
def test_t1_matrix(
    label: str,
    path: str,
    grade: int,
    expected_code: str,
    expected_effect: str,
) -> None:
    """**Validates: Requirements 13.1** (combined T1 matrix).

    Walks every (attack-path × grade) cell from ``tasks.md §6.6``. Each
    row is a deterministic, named instance of the property tests above
    so the matrix coverage is auditable in the CI log without scrolling
    through Hypothesis statistics.
    """

    signal, seen = _build_attack_signal(path, grade)
    verdict = pc_decide(signal, seen)

    assert verdict.code == expected_code, (
        f"matrix row {label!r}: expected {expected_code!r}, got {verdict.code!r}"
    )
    assert verdict.effect == expected_effect, (
        f"matrix row {label!r}: expected effect {expected_effect!r}, "
        f"got {verdict.effect!r}"
    )

    # Acceptance bar from ``tasks.md §6.6``: every forgery path MUST be
    # rejected. The matrix has no ACCEPTED row by construction.
    assert verdict.code != ACCEPTED, (
        f"T1 acceptance bar violated: matrix row {label!r} produced ACCEPTED"
    )


# ---------------------------------------------------------------------------
# 6. Cross-cutting decision-totality guard.
# ---------------------------------------------------------------------------
def test_t1_decisions_are_total_into_known_sets() -> None:
    """Every matrix row's verdict lives in the design.md §EH.1 closed set.

    Sanity guard against future changes to ``pc_decide`` accidentally
    introducing a third decision branch — design.md §9.10.2 enumerates
    exactly ``{ACCEPTED, E_PRESENCE_STALE, E_ATTESTATION_INVALID}``.
    """

    for label, path, grade, _expected_code, _expected_effect in _T1_MATRIX:
        signal, seen = _build_attack_signal(path, grade)
        verdict = pc_decide(signal, seen)
        assert verdict.code in DECISIONS, (
            f"matrix row {label!r}: out-of-set code {verdict.code!r}"
        )
        assert verdict.effect in EFFECTS, (
            f"matrix row {label!r}: out-of-set effect {verdict.effect!r}"
        )
