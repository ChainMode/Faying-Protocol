"""Faying Protocol/1.0 — End-to-end T3 *Selective Disclosure* conformance test.

Covers ``tasks.md §6.7 T3 避重就轻模拟（DISCLOSURE 字段缺失 / 不一致）``.

**Validates: Requirements 13.3** (T3 避重就轻 — 结构化 Disclosure_Report)
**Property: P18.3** (design.md §12 Property 18.3 — Disclosure_Mandatory_Fields)
**Design anchors**:

* design.md §5.3.7 (DISCLOSURE 报文与 ``mandatory_fields`` 强制集合);
* design.md §9.10.4 T3 (avoidance-by-omission — four protocol-level
  protections: structured DISCLOSURE, schema-level audit / 禁 free_text
  掩盖、高敏感动作前置披露、不一致即 ``ego-deviation`` Revoke);
* design.md §5.4 (error-code 1099 ``E_PROTOCOL`` row);
* design.md §EH.4 (Default-Deny 收敛——任何不可归类的 DISCLOSURE 异常
  统一以 ``E_PROTOCOL`` 拒绝);
* requirements.md §13.3.1–13.3.4 (4 EARS clauses).

Companion artefact:

* :mod:`pbt.tests.test_p18_3_disclosure_mandatory_fields` — fuzzes the
  §12 P18.3 invariant over the four formal injection paths
  (``single_field_missing`` / ``unparseable_field`` / ``order_misalignment``
  / ``inconsistent_with_actual``). This end-to-end test is the
  **adversary-driven scenario walker**: it imports the same reference
  decision functions and walks the four concrete attack families called
  out by ``tasks.md §6.7`` 内容 row, plus a ``free_text``-cover variant.

Scope (per ``tasks.md §6.7`` 内容 row)
-------------------------------------

The adversary is an iFay (or an attacker controlling an iFay endpoint)
that attempts to dodge HP review by mis-shaping its DISCLOSURE report.
Four attack families are exercised:

(a) **DISCLOSURE missing one of the six ``mandatory_fields``.** The iFay
    submits an otherwise valid DISCLOSURE in which exactly one of
    ``{action, scope_used, risk_level, reversibility, affected_resources,
    uncertainty_flags}`` is ``⊥`` (``None``). Acceptance bar: rejected
    with ``E_PROTOCOL`` (1099) and pushed to the HP view channel
    (§9.10.4 #1, requirements.md §13.3.3).

(b) **Inconsistent DISCLOSURE values vs. the actual executed action.**
    The DISCLOSURE is structurally valid but lies on at least one of:

    * ``risk_level`` 低报 — claim ``low/normal`` while executing
      ``high/critical``;
    * ``scope_used`` 缩小 — declare a narrower scope than the one the
      D-dimension call used;
    * ``affected_resources`` 漏报 — omit at least one resource the
      action actually touched.

    Acceptance bar: triggers ``RevokeReason="ego-deviation"`` per
    §9.10.4 #4 / requirements.md §13.3.4.

(c) **High-sensitivity action executed without prior DISCLOSURE.** The
    iFay runs a ``risk_level ∈ {high, critical}`` D-dimension call with
    no preceding HP-confirmed disclosure (or with a disclosure that
    arrives too late, ``d.ts ≥ a.ts``). Acceptance bar: rejected with
    ``E_PROTOCOL`` (1099) per §9.10.4 #3 / requirements.md §13.3.2.

(d) **``free_text`` cover-up.** The iFay submits a DISCLOSURE whose
    ``free_text`` is verbose and reassuring (``"已完成相关操作"``,
    long prose) but whose ``mandatory_fields`` are missing or
    structurally broken. Acceptance bar: ``free_text`` MUST NOT
    "rescue" a payload that fails the §9.10.4 #1 schema gate; the
    verdict is identical to family (a) — ``E_PROTOCOL``.

Acceptance bar (``tasks.md §6.7`` 验收 row, verbatim):

* ``mandatory_fields`` 缺失 → ``E_PROTOCOL``;
* 不一致 → 触发 ``RevokeReason="ego-deviation"`` Revoke;
* 高敏感动作未前置披露 → 必拒.

Reuse strategy — this test imports the reference decision functions
verbatim from ``pbt/tests/test_p18_3_disclosure_mandatory_fields.py``
so both the property and end-to-end suites probe the same enforcement
state machine. The import is wired through a local ``sys.path`` shim
(the PBT tree is not packaged as part of the conformance suite) and
gracefully skips the module if the PBT tree is absent from a partial
checkout — matching the approach already used by
:mod:`conformance.attacks.test_t6_audit_flooding`.

The reference decision model is **Not Normative** — it mirrors
design.md §5.3.7 + §5.4 + §9.10.4 + §12 P18.3 in declaration order;
any divergence between this module and the spec is a bug here.
"""

from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path
from typing import Any, Iterable

import pytest
from hypothesis import HealthCheck, given, settings, strategies as st


# ---------------------------------------------------------------------------
# Reuse the §12 P18.3 reference decision model from the PBT module.
# ---------------------------------------------------------------------------
_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_PBT_TESTS = _REPO_ROOT / "pbt" / "tests"

if not _PBT_TESTS.exists():  # pragma: no cover - partial checkout guard
    pytest.skip(
        "pbt/tests/ is not present in this checkout; the T3 conformance "
        "test relies on the P18.3 reference decision model.",
        allow_module_level=True,
    )

if str(_PBT_TESTS) not in sys.path:
    sys.path.insert(0, str(_PBT_TESTS))

from test_p18_3_disclosure_mandatory_fields import (  # type: ignore[import-not-found]  # noqa: E402
    ACCEPTED,
    ATOMIC_ACTIONS,
    DisclosureReport,
    E_PROTOCOL,
    ERROR_CODES,
    ExecutedAction,
    HIGH_SENSITIVITY,
    MANDATORY_FIELDS,
    REVERSIBILITY_VALUES,
    REVOKE_REASON_EGO_DEVIATION,
    RISK_LEVELS,
    evaluate_audit_consistency,
    evaluate_high_sensitivity_action,
    inconsistent,
    parseable,
    validate_disclosure_schema,
)


# ---------------------------------------------------------------------------
# Sanity guards — fail loudly if the imported PBT module's invariants drift.
# ---------------------------------------------------------------------------
assert ERROR_CODES[E_PROTOCOL] == 1099, (
    "design.md §5.4 pins E_PROTOCOL to numeric code 1099"
)
assert set(MANDATORY_FIELDS) == {
    "action",
    "scope_used",
    "risk_level",
    "reversibility",
    "affected_resources",
    "uncertainty_flags",
}, "design.md §5.3.7 enumerates exactly six mandatory_fields"
assert HIGH_SENSITIVITY == frozenset({"high", "critical"}), (
    "design.md §9.10.4 #3 + §12 P18.3 second conjunct fix the "
    "high-sensitivity subset to {high, critical}"
)
assert REVOKE_REASON_EGO_DEVIATION == "ego-deviation", (
    "design.md §9.10.4 #4 / requirements.md §13.3.4 fix the Revoke "
    "reason code to 'ego-deviation'"
)


# ---------------------------------------------------------------------------
# Test-suite-local fixtures — a fully-populated baseline for both halves of
# the T3 attack matrix (the executed action + its honest disclosure twin).
# ---------------------------------------------------------------------------
HP: str = "hp:t3-fixture"
IF: str = "if:t3-fixture"
MANDATE: str = "mandate:t3-fixture"

# A canonical high-sensitivity executed action used by the prior-disclosure
# acceptance bar and as the ground-truth side of inconsistency probes.
_HIGH_SENS_ACTION: ExecutedAction = ExecutedAction(
    mandate_id=MANDATE,
    ts=10_000,
    action="transfer-funds",
    actual_scope={"domains": ["finance"], "actions": ["transfer"]},
    actual_risk_level="critical",
    actual_reversibility="irreversible",
    actual_affected_resources=("res:account:42", "res:ledger:main"),
    actual_uncertainty_flags=("ambiguous-target",),
)


def _well_formed_twin(a: ExecutedAction, *, hp_confirmed: bool = True) -> DisclosureReport:
    """Build the honest disclosure that mirrors ``a`` exactly.

    All inconsistency / cover-up scenarios mutate this twin so the
    counter-example stays minimal — exactly one mandatory field changes
    per scenario, which matches the §12 P18.3 PBT injection paths.
    """

    return DisclosureReport(
        mandate_id=a.mandate_id,
        ts=a.ts - 1,                           # strictly earlier — §12 P18.3 #2.
        hp_confirmed=hp_confirmed,
        action=a.action,
        scope_used=dict(a.actual_scope),
        risk_level=a.actual_risk_level,
        reversibility=a.actual_reversibility,
        affected_resources=list(a.actual_affected_resources),
        uncertainty_flags=list(a.actual_uncertainty_flags),
    )


# A long, reassuring free_text passage — the hallmark of the §9.10.4 T3
# threat model ("已完成相关操作 ..."). Used by Group D to demonstrate that
# free_text MUST NOT compensate for missing / unparseable mandatory fields.
_FREE_TEXT_COVER: str = (
    "已完成相关操作；过程顺利、未发现风险，所有相关方均已知悉，"
    "如有疑问可随时联系 iFay 助理。Operation completed without "
    "incident; no risk indicators surfaced, all stakeholders informed."
)


# ---------------------------------------------------------------------------
# Group A — DISCLOSURE missing one of the six mandatory_fields (§9.10.4 #1).
# ---------------------------------------------------------------------------
class TestMissingMandatoryField:
    """Each missing ``mandatory_field`` MUST be rejected with ``E_PROTOCOL``.

    **Validates: Requirements 13.3.3**.

    Per design.md §9.10.4 #1 + §EH.4 the MS rejects any DISCLOSURE in
    which a member of ``mandatory_fields`` is ``⊥``. The verdict carries
    code ``E_PROTOCOL`` (1099) and the rejection MUST surface on the
    Human Prime view channel (callers of this test treat the schema
    rejection as the wire-level proxy for "must push to HP_view").
    """

    @pytest.mark.parametrize("missing", MANDATORY_FIELDS)
    def test_each_mandatory_field_missing_yields_e_protocol(
        self, missing: str
    ) -> None:
        twin = _well_formed_twin(_HIGH_SENS_ACTION)
        forged = replace(twin, **{missing: None})

        result = validate_disclosure_schema(forged)

        assert result.verdict == E_PROTOCOL, (
            f"missing mandatory field {missing!r} must yield E_PROTOCOL; "
            f"got {result.verdict!r}"
        )
        assert ERROR_CODES[result.verdict] == 1099, (
            "§5.4 pins E_PROTOCOL to numeric code 1099"
        )
        assert missing in result.missing_fields, (
            f"schema validator did not surface {missing!r} in "
            f"missing_fields={result.missing_fields!r}"
        )
        # Field-isolation guard: the rejection is attributable to the
        # missing field alone, not to a coincidental other defect.
        assert result.unparseable_fields == ()

    def test_all_mandatory_fields_missing_yields_e_protocol(self) -> None:
        """The pathological "submit only free_text" payload is rejected.

        Models the §9.10.4 threat narrative verbatim — an iFay that
        ships a DISCLOSURE whose mandatory_fields are *all* missing and
        relies entirely on a chatty ``free_text`` to placate the HP.
        The MS rejects with ``E_PROTOCOL`` and surfaces every missing
        field for the audit trail.
        """

        forged = DisclosureReport(
            mandate_id=MANDATE,
            ts=0,
            hp_confirmed=True,
            action=None,
            scope_used=None,
            risk_level=None,
            reversibility=None,
            affected_resources=None,
            uncertainty_flags=None,
            free_text=_FREE_TEXT_COVER,
            intent="report",
        )
        result = validate_disclosure_schema(forged)

        assert result.verdict == E_PROTOCOL
        assert ERROR_CODES[result.verdict] == 1099
        assert set(result.missing_fields) == set(MANDATORY_FIELDS), (
            "every mandatory field must surface in missing_fields when all "
            "six are absent"
        )

    @pytest.mark.parametrize("missing", MANDATORY_FIELDS)
    def test_missing_field_rejection_surfaces_to_hp_view(
        self, missing: str
    ) -> None:
        """Every schema rejection feeds the HP view channel (§9.10.4 #1).

        At the protocol-model level the "push to HP view" obligation is
        encoded by the rejection itself — design.md §9.10.4 #1 wires the
        ``E_PROTOCOL`` row in §EH.3 to the HP view channel. We assert
        that any schema-rejected DISCLOSURE produces a verdict whose
        ``missing_fields`` is non-empty (the audit payload that the HP
        view channel surfaces) — without it the HP would have no signal
        to inspect.
        """

        twin = _well_formed_twin(_HIGH_SENS_ACTION)
        result = validate_disclosure_schema(replace(twin, **{missing: None}))

        assert result.verdict == E_PROTOCOL
        assert result.missing_fields, (
            "§9.10.4 #1 requires the rejection to carry a non-empty "
            "missing_fields payload so the HP view channel has actionable "
            "audit content"
        )


# ---------------------------------------------------------------------------
# Group B — Inconsistent DISCLOSURE vs. actual action (§9.10.4 #4).
# ---------------------------------------------------------------------------
class TestInconsistentWithActualAction:
    """Field-by-field disagreement MUST trigger ``ego-deviation`` Revoke.

    **Validates: Requirements 13.3.4**.

    Per design.md §9.10.4 #4 + §12 P18.3 third conjunct, every audit-
    detected disagreement between a structurally-valid DISCLOSURE and
    the executed action MUST surface a Revoke with
    ``RevokeReason = "ego-deviation"``. We pin the three under-reporting
    patterns named in ``tasks.md §6.7`` (risk_level 低报 / scope_used
    缩小 / affected_resources 漏报) plus the wider matrix.
    """

    def test_risk_level_under_reported(self) -> None:
        """``risk_level`` 低报 — declare ``low`` for a ``critical`` action."""

        a = _HIGH_SENS_ACTION
        forged = replace(_well_formed_twin(a), risk_level="low")

        # Pre-condition: schema-valid + actually inconsistent on this axis.
        assert validate_disclosure_schema(forged).verdict == ACCEPTED
        assert inconsistent(forged, a)

        result = evaluate_audit_consistency(a, [forged])

        assert result.revoke_triggered is True, (
            "risk_level 低报 must trigger a Revoke per §9.10.4 #4"
        )
        assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION, (
            f"Revoke reason must be {REVOKE_REASON_EGO_DEVIATION!r}; "
            f"got {result.revoke_reason!r}"
        )

    def test_scope_used_narrowed(self) -> None:
        """``scope_used`` 缩小 — declare a strict subset of the actual scope."""

        a = _HIGH_SENS_ACTION
        # Drop the only action token, keep the domain — a narrowed scope.
        forged = replace(
            _well_formed_twin(a),
            scope_used={
                "domains": list(a.actual_scope["domains"]),
                "actions": ["read"],     # ≠ "transfer"
            },
        )

        assert validate_disclosure_schema(forged).verdict == ACCEPTED
        assert inconsistent(forged, a)

        result = evaluate_audit_consistency(a, [forged])

        assert result.revoke_triggered is True
        assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION

    def test_affected_resources_omitted(self) -> None:
        """``affected_resources`` 漏报 — drop a resource that was touched."""

        a = _HIGH_SENS_ACTION
        # Drop the ledger resource — the iFay only admits to touching
        # the account, hiding the side-effect on the main ledger.
        partial = list(a.actual_affected_resources[:-1])
        assert len(partial) < len(a.actual_affected_resources)
        forged = replace(_well_formed_twin(a), affected_resources=partial)

        assert validate_disclosure_schema(forged).verdict == ACCEPTED
        assert inconsistent(forged, a)

        result = evaluate_audit_consistency(a, [forged])

        assert result.revoke_triggered is True
        assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION

    @pytest.mark.parametrize(
        "field_name, mutate",
        [
            ("action", lambda d, a: replace(d, action="send-message")),
            ("reversibility", lambda d, a: replace(d, reversibility="reversible")),
            (
                "uncertainty_flags",
                lambda d, a: replace(d, uncertainty_flags=[]),
            ),
        ],
    )
    def test_other_inconsistency_axes_also_trigger_ego_deviation(
        self, field_name: str, mutate: Any
    ) -> None:
        """Every remaining mandatory-field axis also fires ego-deviation.

        Closes the matrix begun by the three named under-reporting
        patterns above. ``action`` divergence is the canonical T3
        attack (mislabel the action). ``reversibility`` flip and
        ``uncertainty_flags`` swallow are the §9.10.4 #4 "swallow the
        inconvenient signal" siblings.
        """

        a = _HIGH_SENS_ACTION
        forged = mutate(_well_formed_twin(a), a)

        # Pre-condition: schema-valid + actually inconsistent.
        assert validate_disclosure_schema(forged).verdict == ACCEPTED, (
            f"mutation on {field_name!r} must remain schema-valid"
        )
        assert inconsistent(forged, a), (
            f"mutation on {field_name!r} did not produce a real divergence"
        )

        result = evaluate_audit_consistency(a, [forged])

        assert result.revoke_triggered is True
        assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION

    def test_consistent_disclosure_does_not_trigger_revoke(self) -> None:
        """Sanity guard — agreement on every field MUST NOT fire ego-deviation.

        Without this row a "always Revoke" verifier would vacuously
        satisfy the inconsistency properties above. The honest twin is
        the witness for the bi-conditional half of P18.3 conjunct 3.
        """

        a = _HIGH_SENS_ACTION
        twin = _well_formed_twin(a)

        result = evaluate_audit_consistency(a, [twin])

        assert result.revoke_triggered is False
        assert result.revoke_reason is None


# ---------------------------------------------------------------------------
# Group C — High-sensitivity action without prior HP-confirmed disclosure.
# ---------------------------------------------------------------------------
class TestHighSensitivityRequiresPriorDisclosure:
    """``risk_level ∈ {high, critical}`` action without prior DISCLOSURE ⟹ reject.

    **Validates: Requirements 13.3.2**.

    Per design.md §9.10.4 #3 + §12 P18.3 second conjunct: every
    high-sensitivity D-dimension call MUST be preceded by a
    HP-confirmed, schema-valid DISCLOSURE of the same action under the
    same Mandate. The MS rejects any high-sens call that fails this
    test with ``E_PROTOCOL``.
    """

    @pytest.mark.parametrize("risk_level", sorted(HIGH_SENSITIVITY))
    def test_no_prior_disclosure_at_all(self, risk_level: str) -> None:
        """The "iFay simply skipped DISCLOSURE" worst case (§9.10.4 #3)."""

        a = replace(_HIGH_SENS_ACTION, actual_risk_level=risk_level)
        result = evaluate_high_sensitivity_action(a, [])

        assert result.verdict == E_PROTOCOL, (
            f"{risk_level!r} action with no prior disclosure must be "
            f"rejected; got {result.verdict!r}"
        )
        assert ERROR_CODES[result.verdict] == 1099

    @pytest.mark.parametrize("risk_level", sorted(HIGH_SENSITIVITY))
    def test_prior_disclosure_arrives_too_late(self, risk_level: str) -> None:
        """Order-misalignment — ``d.ts ≥ a.ts`` cannot satisfy 前置披露.

        The §12 P18.3 second conjunct uses strict ``<`` for the
        timestamp comparison; a disclosure emitted at or after the
        D-dimension call's execution moment provides no opportunity for
        HP intervention and therefore MUST NOT count as the witness.
        """

        a = replace(_HIGH_SENS_ACTION, actual_risk_level=risk_level)
        # Disclosure emitted *exactly at* a.ts (the strict-< boundary).
        late = replace(_well_formed_twin(a), ts=a.ts)
        # Schema-valid, but the timestamp invalidates 前置披露.
        assert validate_disclosure_schema(late).verdict == ACCEPTED
        assert late.ts >= a.ts

        result = evaluate_high_sensitivity_action(a, [late])

        assert result.verdict == E_PROTOCOL, (
            "order-misaligned disclosure (d.ts >= a.ts) cannot satisfy "
            "the §12 P18.3 prior-disclosure clause"
        )

    @pytest.mark.parametrize("risk_level", sorted(HIGH_SENSITIVITY))
    def test_prior_disclosure_not_hp_confirmed(self, risk_level: str) -> None:
        """Disclosure exists, on time, but ``hp_confirmed = false``.

        §9.10.4 #3 requires HP confirmation; a disclosure that has been
        emitted but not yet acknowledged by the HP cannot serve as the
        prior-disclosure witness.
        """

        a = replace(_HIGH_SENS_ACTION, actual_risk_level=risk_level)
        not_confirmed = _well_formed_twin(a, hp_confirmed=False)

        result = evaluate_high_sensitivity_action(a, [not_confirmed])

        assert result.verdict == E_PROTOCOL

    @pytest.mark.parametrize("risk_level", sorted(HIGH_SENSITIVITY))
    def test_prior_disclosure_for_a_different_action(
        self, risk_level: str
    ) -> None:
        """Action-mislabel attack — disclosure points at a different action.

        The canonical §9.10.4 T3 selective-disclosure pattern: the iFay
        emits a HP-confirmed disclosure for ``send-message`` and then
        runs ``transfer-funds`` while pointing at the previous
        disclosure as its witness. The audit predicate refuses to
        accept the mismatched disclosure as 前置披露.
        """

        a = replace(_HIGH_SENS_ACTION, actual_risk_level=risk_level)
        wrong_action = replace(
            _well_formed_twin(a), action="send-message"
        )
        # Sanity: the wrong-action disclosure is itself schema-valid;
        # the rejection must be attributable to the action mismatch,
        # not to a coincidental schema break.
        assert validate_disclosure_schema(wrong_action).verdict == ACCEPTED
        assert wrong_action.action != a.action

        result = evaluate_high_sensitivity_action(a, [wrong_action])

        assert result.verdict == E_PROTOCOL

    @pytest.mark.parametrize("risk_level", sorted(HIGH_SENSITIVITY))
    def test_well_formed_prior_hp_confirmed_disclosure_is_accepted(
        self, risk_level: str
    ) -> None:
        """Sanity guard — the §9.10.4 #3 admissible path actually accepts.

        Without this row the previous tests could be vacuously
        satisfied by an "always-reject" verifier. The honest twin is
        the witness for the bi-conditional half of P18.3 conjunct 2.
        """

        a = replace(_HIGH_SENS_ACTION, actual_risk_level=risk_level)
        twin = _well_formed_twin(a, hp_confirmed=True)

        result = evaluate_high_sensitivity_action(a, [twin])

        assert result.verdict == ACCEPTED


# ---------------------------------------------------------------------------
# Group D — ``free_text`` cover-up (§9.10.4 #2).
# ---------------------------------------------------------------------------
class TestFreeTextCoverUp:
    """Verbose ``free_text`` MUST NOT rescue a payload that breaks the schema.

    **Validates: Requirements 13.3.2 + 13.3.3**.

    Per design.md §9.10.4 #2 the Supervisory Agent / MS audits
    DISCLOSURE at the schema level; the ``free_text`` field is
    auxiliary and CANNOT compensate for missing or unparseable
    mandatory fields. ``tasks.md §6.7`` 内容 row (d) calls out the
    "free_text 充斥而 mandatory_fields 缺" attack pattern explicitly.
    """

    @pytest.mark.parametrize("missing", MANDATORY_FIELDS)
    def test_free_text_does_not_rescue_missing_field(
        self, missing: str
    ) -> None:
        """A long, reassuring ``free_text`` cannot mask a missing field."""

        twin = _well_formed_twin(_HIGH_SENS_ACTION)
        forged = replace(
            twin,
            **{missing: None},
            free_text=_FREE_TEXT_COVER,
        )
        # Pre-condition: free_text really is non-empty / verbose.
        assert forged.free_text and len(forged.free_text) > 32

        result = validate_disclosure_schema(forged)

        assert result.verdict == E_PROTOCOL, (
            f"free_text MUST NOT rescue a payload missing {missing!r}; "
            f"got {result.verdict!r}"
        )
        assert missing in result.missing_fields

    @pytest.mark.parametrize(
        "field_name, bad_value",
        [
            ("action", "transfer-*"),                                   # wildcard
            ("scope_used", "scope-as-string"),                          # wrong shape
            ("risk_level", "very-high"),                                # off-enum
            ("reversibility", "maybe"),                                 # off-enum
            ("affected_resources", "res:single"),                       # str ≠ list[str]
            ("uncertainty_flags", [1, 2, 3]),                           # list[int]
        ],
    )
    def test_free_text_does_not_rescue_unparseable_field(
        self, field_name: str, bad_value: Any
    ) -> None:
        """A long ``free_text`` cannot mask an unparseable mandatory field."""

        twin = _well_formed_twin(_HIGH_SENS_ACTION)
        forged = replace(
            twin,
            **{field_name: bad_value},
            free_text=_FREE_TEXT_COVER,
        )
        # Sanity guard for the parametrise table — the chosen value
        # must really be unparseable per the §5.3.7 schema.
        assert not parseable(field_name, bad_value), (
            f"test table entry ({field_name!r}, {bad_value!r}) is "
            "actually parseable — fix the table"
        )

        result = validate_disclosure_schema(forged)

        assert result.verdict == E_PROTOCOL
        assert field_name in result.unparseable_fields

    def test_pure_free_text_payload_is_rejected(self) -> None:
        """The "已完成相关操作" payload — every mandatory field absent."""

        forged = DisclosureReport(
            mandate_id=MANDATE,
            ts=0,
            hp_confirmed=True,
            action=None,
            scope_used=None,
            risk_level=None,
            reversibility=None,
            affected_resources=None,
            uncertainty_flags=None,
            free_text=_FREE_TEXT_COVER,
            intent="report",
        )

        result = validate_disclosure_schema(forged)

        assert result.verdict == E_PROTOCOL
        assert ERROR_CODES[result.verdict] == 1099
        assert set(result.missing_fields) == set(MANDATORY_FIELDS)


# ---------------------------------------------------------------------------
# Hypothesis-driven random-adversary coverage.
#
# Models the practical attacker who randomises which field they drop /
# corrupt / lie about across a large run. Each path corresponds 1-to-1
# with a §12 P18.3 conjunct so the property remains decidable and the
# generators stay simple. These complement the parametrised matrices
# above: the matrices give human-readable rows; Hypothesis explores the
# adjacent space for shrunken counter-examples.
# ---------------------------------------------------------------------------
@given(missing=st.sampled_from(MANDATORY_FIELDS))
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_random_missing_field_always_rejected(missing: str) -> None:
    """**Validates: Requirements 13.3.3** (random missing-field path)."""

    twin = _well_formed_twin(_HIGH_SENS_ACTION)
    forged = replace(twin, **{missing: None})

    result = validate_disclosure_schema(forged)
    assert result.verdict == E_PROTOCOL
    assert missing in result.missing_fields


@given(
    risk_level=st.sampled_from(sorted(HIGH_SENSITIVITY)),
    reversibility=st.sampled_from(REVERSIBILITY_VALUES),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_random_high_sensitivity_action_without_disclosure_rejected(
    risk_level: str, reversibility: str
) -> None:
    """**Validates: Requirements 13.3.2** (random high-sens, no DISCLOSURE)."""

    a = replace(
        _HIGH_SENS_ACTION,
        actual_risk_level=risk_level,
        actual_reversibility=reversibility,
    )
    result = evaluate_high_sensitivity_action(a, [])
    assert result.verdict == E_PROTOCOL


@given(
    target=st.sampled_from(("risk_level", "affected_resources", "scope_used")),
)
@settings(
    max_examples=50,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_random_under_reporting_triggers_ego_deviation(target: str) -> None:
    """**Validates: Requirements 13.3.4** (random under-reporting Revoke).

    Walks the three ``tasks.md §6.7`` 内容 row (b) under-reporting
    patterns under Hypothesis: each iteration concentrates the
    divergence on exactly one mandatory field so the counter-example
    shrinks to a single mutated axis.
    """

    a = _HIGH_SENS_ACTION
    twin = _well_formed_twin(a)

    if target == "risk_level":
        # Lower the declared risk_level below the actual ``critical`` row.
        forged = replace(twin, risk_level="low")
    elif target == "affected_resources":
        forged = replace(
            twin,
            affected_resources=list(a.actual_affected_resources[:-1]),
        )
    else:  # scope_used
        forged = replace(
            twin,
            scope_used={
                "domains": list(a.actual_scope["domains"]),
                "actions": ["read"],
            },
        )

    assert validate_disclosure_schema(forged).verdict == ACCEPTED
    assert inconsistent(forged, a), (
        f"random under-reporting on {target!r} did not produce a divergence"
    )

    result = evaluate_audit_consistency(a, [forged])
    assert result.revoke_triggered is True
    assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION


# ---------------------------------------------------------------------------
# T3 coverage matrix — every (path × scenario) cell is exercised.
#
# This parametrised test acts as the human-readable "matrix table" of
# the §6.7 attack scenarios. It is redundant with the class-level tests
# above but makes the path × variant coverage explicit at-a-glance,
# matching the layout used by ``test_t1_social_engineering._T1_MATRIX``.
# ---------------------------------------------------------------------------
PATH_MISSING: str = "missing-field"
PATH_INCONSISTENT: str = "inconsistent"
PATH_NO_PRIOR: str = "no-prior-disclosure"
PATH_FREE_TEXT_COVER: str = "free-text-cover"

# Each row: (label, path, payload-hint, expected_verdict, expected_revoke)
_T3Case = tuple[str, str, str, str, bool]


def _enumerate_t3_matrix() -> Iterable[_T3Case]:
    """Yield the (path × variant) cells covered by ``tasks.md §6.7``."""

    # Group A — six missing-field variants.
    for f in MANDATORY_FIELDS:
        yield (
            f"{PATH_MISSING}/{f}",
            PATH_MISSING,
            f,
            E_PROTOCOL,
            False,
        )
    # Group B — six inconsistency axes; each fires ego-deviation Revoke.
    for f in MANDATORY_FIELDS:
        yield (
            f"{PATH_INCONSISTENT}/{f}",
            PATH_INCONSISTENT,
            f,
            ACCEPTED,                  # schema-valid; only the audit fires.
            True,
        )
    # Group C — high-sensitivity 前置披露 variants.
    for hint in ("none", "late", "not-confirmed", "wrong-action"):
        yield (
            f"{PATH_NO_PRIOR}/{hint}",
            PATH_NO_PRIOR,
            hint,
            E_PROTOCOL,
            False,
        )
    # Group D — free_text cover-up: every missing-field variant + the
    # all-missing payload.
    for f in MANDATORY_FIELDS:
        yield (
            f"{PATH_FREE_TEXT_COVER}/{f}",
            PATH_FREE_TEXT_COVER,
            f,
            E_PROTOCOL,
            False,
        )
    yield (
        f"{PATH_FREE_TEXT_COVER}/all-missing",
        PATH_FREE_TEXT_COVER,
        "all-missing",
        E_PROTOCOL,
        False,
    )


_T3_MATRIX: tuple[_T3Case, ...] = tuple(_enumerate_t3_matrix())


def _build_attack(
    path: str, hint: str
) -> tuple[str, ExecutedAction, list[DisclosureReport]]:
    """Compose the (mode, action, disclosures) triple for one matrix cell.

    ``mode`` is one of ``{"schema", "prior", "audit"}`` and selects which
    reference decision function the matrix runner invokes:

    * ``schema`` — :func:`validate_disclosure_schema` on a single
      forged disclosure;
    * ``prior``  — :func:`evaluate_high_sensitivity_action` on the
      executed action and the supplied disclosure list;
    * ``audit``  — :func:`evaluate_audit_consistency` on the executed
      action and the supplied disclosure list.
    """

    a = _HIGH_SENS_ACTION

    if path == PATH_MISSING:
        twin = _well_formed_twin(a)
        forged = replace(twin, **{hint: None})
        return "schema", a, [forged]

    if path == PATH_INCONSISTENT:
        twin = _well_formed_twin(a)
        if hint == "action":
            forged = replace(twin, action="send-message")
        elif hint == "scope_used":
            forged = replace(
                twin,
                scope_used={
                    "domains": list(a.actual_scope["domains"]),
                    "actions": ["read"],
                },
            )
        elif hint == "risk_level":
            forged = replace(twin, risk_level="low")
        elif hint == "reversibility":
            forged = replace(twin, reversibility="reversible")
        elif hint == "affected_resources":
            forged = replace(
                twin,
                affected_resources=list(a.actual_affected_resources[:-1]),
            )
        elif hint == "uncertainty_flags":
            forged = replace(twin, uncertainty_flags=[])
        else:  # pragma: no cover - exhaustive over MANDATORY_FIELDS
            raise AssertionError(f"unknown inconsistency axis: {hint!r}")
        return "audit", a, [forged]

    if path == PATH_NO_PRIOR:
        if hint == "none":
            return "prior", a, []
        if hint == "late":
            late = replace(_well_formed_twin(a), ts=a.ts)
            return "prior", a, [late]
        if hint == "not-confirmed":
            not_confirmed = _well_formed_twin(a, hp_confirmed=False)
            return "prior", a, [not_confirmed]
        if hint == "wrong-action":
            wrong = replace(_well_formed_twin(a), action="send-message")
            return "prior", a, [wrong]
        raise AssertionError(f"unknown no-prior variant: {hint!r}")  # pragma: no cover

    if path == PATH_FREE_TEXT_COVER:
        if hint == "all-missing":
            forged = DisclosureReport(
                mandate_id=MANDATE,
                ts=0,
                hp_confirmed=True,
                action=None,
                scope_used=None,
                risk_level=None,
                reversibility=None,
                affected_resources=None,
                uncertainty_flags=None,
                free_text=_FREE_TEXT_COVER,
                intent="report",
            )
            return "schema", a, [forged]
        twin = _well_formed_twin(a)
        forged = replace(twin, **{hint: None}, free_text=_FREE_TEXT_COVER)
        return "schema", a, [forged]

    raise AssertionError(f"unknown attack path: {path!r}")  # pragma: no cover


@pytest.mark.parametrize(
    "label,path,hint,expected_verdict,expected_revoke",
    _T3_MATRIX,
    ids=[c[0] for c in _T3_MATRIX],
)
def test_t3_matrix(
    label: str,
    path: str,
    hint: str,
    expected_verdict: str,
    expected_revoke: bool,
) -> None:
    """**Validates: Requirements 13.3** (combined T3 matrix).

    Walks every (attack-path × variant) cell from ``tasks.md §6.7``.
    Each row is a deterministic, named instance of the property tests
    above so the matrix coverage is auditable in the CI log without
    scrolling through Hypothesis statistics.
    """

    mode, a, disclosures = _build_attack(path, hint)

    if mode == "schema":
        result = validate_disclosure_schema(disclosures[0])
        assert result.verdict == expected_verdict, (
            f"matrix row {label!r}: expected {expected_verdict!r}, "
            f"got {result.verdict!r}"
        )
        if expected_verdict == E_PROTOCOL:
            # The rejection must carry an audit payload (missing OR
            # unparseable). Without it the HP view channel would be
            # blind to the cause of the §9.10.4 #1 rejection.
            assert result.missing_fields or result.unparseable_fields, (
                f"matrix row {label!r}: schema rejection produced no "
                "audit payload (missing/unparseable both empty)"
            )
        assert result.revoke_triggered is expected_revoke

    elif mode == "prior":
        result = evaluate_high_sensitivity_action(a, disclosures)
        assert result.verdict == expected_verdict, (
            f"matrix row {label!r}: expected {expected_verdict!r}, "
            f"got {result.verdict!r}"
        )

    elif mode == "audit":
        result = evaluate_audit_consistency(a, disclosures)
        assert result.revoke_triggered is expected_revoke, (
            f"matrix row {label!r}: expected revoke_triggered="
            f"{expected_revoke}; got {result.revoke_triggered}"
        )
        if expected_revoke:
            assert result.revoke_reason == REVOKE_REASON_EGO_DEVIATION, (
                f"matrix row {label!r}: expected ego-deviation Revoke; "
                f"got {result.revoke_reason!r}"
            )

    else:  # pragma: no cover - exhaustive over modes
        raise AssertionError(f"unknown mode {mode!r}")


# ---------------------------------------------------------------------------
# Cross-cutting decision-totality guard — every matrix row's verdict lives
# in the design.md §5.4 closed set ``{ACCEPTED, E_PROTOCOL}``.
# ---------------------------------------------------------------------------
def test_t3_decisions_are_total_into_known_sets() -> None:
    """Sanity guard against a future refactor introducing a third branch.

    P18.3 enumerates exactly two outcomes at the schema / prior /
    audit-consistency stage: ``ACCEPTED`` or ``E_PROTOCOL`` (with the
    audit-stage Revoke being orthogonal to the schema verdict). Any
    third decision branch would mark an undefined acceptance path that
    could hide a covert §9.10.4 bypass.
    """

    permitted_verdicts: frozenset[str] = frozenset({ACCEPTED, E_PROTOCOL})
    for label, path, hint, _expected_verdict, _expected_revoke in _T3_MATRIX:
        mode, a, disclosures = _build_attack(path, hint)
        if mode == "schema":
            result = validate_disclosure_schema(disclosures[0])
        elif mode == "prior":
            result = evaluate_high_sensitivity_action(a, disclosures)
        else:  # mode == "audit"
            result = evaluate_audit_consistency(a, disclosures)

        assert result.verdict in permitted_verdicts, (
            f"matrix row {label!r}: out-of-set verdict {result.verdict!r}"
        )
