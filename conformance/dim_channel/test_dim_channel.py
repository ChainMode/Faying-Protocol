"""Pytest suite for the channel-binding conformance dimension (task 5.5).

Validates the RFC 9266 TLS Exporter Channel Binding contract from
Requirement 9.2.3 / design.md §9.3 across BOOTSTRAP / DELEGATE / REVOKE
vectors, in both TLS-only and mTLS modes.

Acceptance gates (verbatim from tasks.md task 5.5):

* mTLS without a Channel Binding ⇒ rejected.
* TLS-only without a Channel Binding ⇒ accepted.

The suite is stdlib-only (it does not depend on ``cbor2`` or
``cryptography``); run it with::

    pytest conformance/dim_channel/test_dim_channel.py

or simply::

    pytest conformance/dim_channel/
"""

from __future__ import annotations

import pytest

from .rp_validator import (
    E_ATTESTATION_INVALID,
    E_PROTOCOL,
    validate_channel_binding,
)
from .scenarios import all_scenarios, run_all, run_scenario
from .tls_context import TLSContext


# ---------------------------------------------------------------------------
# TLSContext invariants — sanity checks before exercising the validator.
# ---------------------------------------------------------------------------
class TestTLSContext:
    def test_mtls_requires_client_auth(self) -> None:
        with pytest.raises(ValueError):
            TLSContext(mode="mtls", connection_id="x", client_authenticated=False)

    def test_tls_only_forbids_client_auth(self) -> None:
        with pytest.raises(ValueError):
            TLSContext(mode="tls-only", connection_id="x", client_authenticated=True)

    def test_unknown_mode_rejected(self) -> None:
        with pytest.raises(ValueError):
            TLSContext(mode="quic", connection_id="x")

    def test_exporter_is_32_bytes(self) -> None:
        ctx = TLSContext(mode="tls-only", connection_id="conn-A")
        assert len(ctx.exporter()) == 32

    def test_exporter_is_deterministic(self) -> None:
        ctx_a = TLSContext(mode="tls-only", connection_id="conn-A")
        ctx_b = TLSContext(mode="tls-only", connection_id="conn-A")
        assert ctx_a.exporter() == ctx_b.exporter()

    def test_distinct_connections_diverge(self) -> None:
        ctx_a = TLSContext(mode="tls-only", connection_id="conn-A")
        ctx_b = TLSContext(mode="tls-only", connection_id="conn-B")
        assert ctx_a.exporter() != ctx_b.exporter()

    def test_mode_changes_exporter(self) -> None:
        ctx_tls = TLSContext(mode="tls-only", connection_id="same-conn")
        ctx_mtls = TLSContext(
            mode="mtls", connection_id="same-conn", client_authenticated=True
        )
        # Different domain separation ⇒ different exporter even with same
        # connection_id; this prevents a TLS-only client from reusing an
        # mTLS exporter offline.
        assert ctx_tls.exporter() != ctx_mtls.exporter()

    def test_requires_channel_binding_flag(self) -> None:
        tls = TLSContext(mode="tls-only", connection_id="x")
        mtls = TLSContext(mode="mtls", connection_id="x", client_authenticated=True)
        assert tls.requires_channel_binding() is False
        assert mtls.requires_channel_binding() is True


# ---------------------------------------------------------------------------
# Validator unit tests — encode the §9.3 truth table directly.
# ---------------------------------------------------------------------------
class TestValidator:
    def test_mtls_missing_binding_rejected(self) -> None:
        ctx = TLSContext(
            mode="mtls", connection_id="conn-1", client_authenticated=True
        )
        result = validate_channel_binding({}, ctx)
        assert result.accepted is False
        assert result.error_code == E_ATTESTATION_INVALID

    def test_mtls_matching_binding_accepted(self) -> None:
        ctx = TLSContext(
            mode="mtls", connection_id="conn-1", client_authenticated=True
        )
        envelope = {"channel_binding": ctx.exporter()}
        result = validate_channel_binding(envelope, ctx)
        assert result.accepted is True
        assert result.error_code is None

    def test_mtls_tampered_binding_rejected(self) -> None:
        ctx = TLSContext(
            mode="mtls", connection_id="conn-1", client_authenticated=True
        )
        tampered = bytearray(ctx.exporter())
        tampered[-1] ^= 0xFF
        envelope = {"channel_binding": bytes(tampered)}
        result = validate_channel_binding(envelope, ctx)
        assert result.accepted is False
        assert result.error_code == E_ATTESTATION_INVALID

    def test_tls_only_without_binding_accepted(self) -> None:
        ctx = TLSContext(mode="tls-only", connection_id="conn-1")
        result = validate_channel_binding({}, ctx)
        assert result.accepted is True
        assert result.error_code is None

    def test_tls_only_with_stray_binding_rejected_as_protocol(self) -> None:
        ctx = TLSContext(mode="tls-only", connection_id="conn-1")
        envelope = {"channel_binding": b"\x00" * 32}
        result = validate_channel_binding(envelope, ctx)
        assert result.accepted is False
        assert result.error_code == E_PROTOCOL

    def test_binding_in_claims_block_is_extracted(self) -> None:
        # Some vectors mirror BOOTSTRAP/DELEGATE inner Mandate structures and
        # therefore carry the binding inside ``claims`` rather than at the
        # envelope top-level. The validator must accept either location.
        ctx = TLSContext(
            mode="mtls", connection_id="conn-1", client_authenticated=True
        )
        envelope = {"claims": {"channel_binding": ctx.exporter()}}
        result = validate_channel_binding(envelope, ctx)
        assert result.accepted is True

    def test_b64_wrapped_binding_is_decoded(self) -> None:
        # JSON-encoded vectors pass bytes through ``{"__b64__": "..."}`` —
        # the validator must transparently decode and compare the bytes.
        import base64

        ctx = TLSContext(
            mode="mtls", connection_id="conn-1", client_authenticated=True
        )
        envelope = {
            "channel_binding": {
                "__b64__": base64.b64encode(ctx.exporter()).decode("ascii")
            }
        }
        result = validate_channel_binding(envelope, ctx)
        assert result.accepted is True


# ---------------------------------------------------------------------------
# Scenario matrix — the actual task 5.5 acceptance gate.
# ---------------------------------------------------------------------------
class TestScenarioMatrix:
    @pytest.mark.parametrize(
        "scenario", all_scenarios(), ids=lambda s: s.scenario_id
    )
    def test_scenario_matches_expectation(self, scenario) -> None:
        result = run_scenario(scenario)
        assert result.passed, (
            f"scenario {scenario.scenario_id} failed: "
            f"expected accepted={scenario.expected_accepted} "
            f"error_code={scenario.expected_error_code}; "
            f"actual accepted={result.actual.accepted} "
            f"error_code={result.actual.error_code} "
            f"reason={result.actual.reason}"
        )

    def test_matrix_covers_three_message_types(self) -> None:
        message_types = {s.message_type for s in all_scenarios()}
        assert message_types == {"BOOTSTRAP", "DELEGATE", "REVOKE"}

    def test_matrix_covers_both_tls_modes(self) -> None:
        modes = {s.tls_mode for s in all_scenarios()}
        assert modes == {"tls-only", "mtls"}

    def test_acceptance_gate_mtls_missing_binding_rejected(self) -> None:
        """Task 5.5 verbatim: mTLS without Channel Binding must be rejected."""

        target = [
            r
            for r in run_all()
            if r.scenario.tls_mode == "mtls"
            and r.scenario.binding_shape == "absent"
        ]
        assert target, "expected at least one mTLS-without-binding scenario"
        for r in target:
            assert r.actual.accepted is False, (
                f"scenario {r.scenario.scenario_id} unexpectedly accepted"
            )
            assert r.actual.error_code == E_ATTESTATION_INVALID

    def test_acceptance_gate_tls_only_without_binding_accepted(self) -> None:
        """Task 5.5 verbatim: TLS-only without Channel Binding still passes."""

        target = [
            r
            for r in run_all()
            if r.scenario.tls_mode == "tls-only"
            and r.scenario.binding_shape == "absent"
        ]
        assert target, "expected at least one TLS-only-without-binding scenario"
        for r in target:
            assert r.actual.accepted is True, (
                f"scenario {r.scenario.scenario_id} unexpectedly rejected: "
                f"{r.actual.reason}"
            )

    def test_acceptance_gate_covers_bootstrap_delegate_revoke(self) -> None:
        """Both gates must be exercised against all three message types."""

        for mt in ("BOOTSTRAP", "DELEGATE", "REVOKE"):
            mtls_absent = [
                r
                for r in run_all()
                if r.scenario.message_type == mt
                and r.scenario.tls_mode == "mtls"
                and r.scenario.binding_shape == "absent"
            ]
            assert mtls_absent, f"missing mTLS-absent gate for {mt}"
            assert all(not r.actual.accepted for r in mtls_absent)
            tls_absent = [
                r
                for r in run_all()
                if r.scenario.message_type == mt
                and r.scenario.tls_mode == "tls-only"
                and r.scenario.binding_shape == "absent"
            ]
            assert tls_absent, f"missing TLS-only-absent gate for {mt}"
            assert all(r.actual.accepted for r in tls_absent)
