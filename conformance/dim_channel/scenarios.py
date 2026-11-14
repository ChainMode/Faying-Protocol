"""Scenario matrix for the channel-binding conformance dimension.

Builds the cartesian product of:

* message-type ∈ {BOOTSTRAP, DELEGATE, REVOKE}  ← task 5.5 内容要求
* tls-mode    ∈ {tls-only, mtls}                ← task 5.5 维度
* binding-shape ∈ {present-and-correct,
                   present-and-tampered,
                   absent}                       ← 验收要求覆盖

For each scenario we declare:

* the live :class:`~conformance.dim_channel.tls_context.TLSContext`,
* the envelope to feed the validator (a stub envelope pulled from the
  task 3.x vectors with a ``channel_binding`` field overlaid per scenario),
* the expected :class:`~conformance.dim_channel.rp_validator.ValidationResult`
  shape.

The acceptance gate (task 5.5) is:

* mTLS without a binding is rejected → ``E_ATTESTATION_INVALID``.
* TLS-only without a binding is accepted (binding not required).

We also probe the negative-positive corners (mTLS with tampered binding,
TLS-only with stray binding) to make sure the validator does not silently
accept malformed envelopes.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .rp_validator import ValidationResult, validate_channel_binding
from .tls_context import TLSContext

# Repository layout: conformance/dim_channel/scenarios.py → parents
# [0]=dim_channel, [1]=conformance, [2]=<repo root>.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_VECTORS_DIR = _REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Vector loaders.
# ---------------------------------------------------------------------------
# We deliberately consume the *debug.json* views (the JSON renderings shipped
# next to each CBOR/JSON vector) instead of decoding the binary vectors
# directly. The dim_encoding (task 5.2) driver owns binary round-tripping;
# dim_channel only cares about envelope-level fields. Reading debug.json
# keeps this module stdlib-only.

def _load_debug_envelope(rel_path: str, side: str) -> Dict[str, Any]:
    """Return the request_view or response_view from a vector's debug.json.

    ``side`` ∈ ``{"request_view", "response_view"}``.
    """

    path = _VECTORS_DIR / rel_path / "debug.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    view = payload.get(side)
    if view is None:
        raise KeyError(f"{rel_path}/debug.json missing {side!r}")
    if not isinstance(view, dict):
        raise TypeError(f"{rel_path}/debug.json {side!r} is not an object")
    return view


# Anchor vectors: one positive-CBOR vector for each of the three message
# types task 5.5 names explicitly. Each is referenced through its known
# directory layout; if any vector is missing, scenario construction fails
# fast with a clear pointer to the offending task.
_ANCHOR_VECTORS = {
    "BOOTSTRAP": ("bootstrap/pos-cbor-ed25519", "request_view"),
    "DELEGATE": ("delegate/pos-depth-1", "request_view"),
    "REVOKE": ("revoke/reason-human-initiated", "request_view"),
}


# ---------------------------------------------------------------------------
# Scenario shape.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Scenario:
    """One row of the channel-binding conformance matrix."""

    scenario_id: str
    message_type: str          # BOOTSTRAP / DELEGATE / REVOKE
    tls_mode: str              # tls-only / mtls
    binding_shape: str         # present-correct / present-tampered / absent
    expected_accepted: bool
    expected_error_code: Optional[int]
    description: str

    # Built lazily via ``materialise`` so importers that only want to list
    # scenarios don't pay the IO cost of opening every debug.json.
    _envelope: Dict[str, Any] = field(default_factory=dict)
    _tls_context: Optional[TLSContext] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scenario_id": self.scenario_id,
            "message_type": self.message_type,
            "tls_mode": self.tls_mode,
            "binding_shape": self.binding_shape,
            "expected_accepted": self.expected_accepted,
            "expected_error_code": self.expected_error_code,
            "description": self.description,
        }


def _build_envelope(
    message_type: str,
    binding_shape: str,
    correct_binding: bytes,
) -> Dict[str, Any]:
    """Materialise the envelope for a scenario.

    The base envelope is taken from the task 3.x vector; we overlay the
    ``channel_binding`` field per the scenario's binding shape.
    """

    rel_path, side = _ANCHOR_VECTORS[message_type]
    envelope = json.loads(json.dumps(_load_debug_envelope(rel_path, side)))

    if binding_shape == "absent":
        envelope.pop("channel_binding", None)
        if isinstance(envelope.get("claims"), dict):
            envelope["claims"].pop("channel_binding", None)
    elif binding_shape == "present-correct":
        envelope["channel_binding"] = correct_binding
    elif binding_shape == "present-tampered":
        # Flip a single bit so the bytes still have the right length but
        # cannot match any conformant exporter output.
        tampered = bytearray(correct_binding)
        tampered[0] ^= 0x01
        envelope["channel_binding"] = bytes(tampered)
    else:  # pragma: no cover - guarded at construction time
        raise ValueError(f"unknown binding_shape: {binding_shape!r}")
    return envelope


def _expected_outcome(
    tls_mode: str, binding_shape: str
) -> tuple[bool, Optional[int]]:
    """Encode the validator matrix from rp_validator.validate_channel_binding."""

    if tls_mode == "mtls":
        if binding_shape == "present-correct":
            return True, None
        # Either absent or tampered → E_ATTESTATION_INVALID.
        return False, 1007
    # tls-only.
    if binding_shape == "absent":
        return True, None
    # Stray binding on a TLS-only channel is malformed.
    return False, 1099


def all_scenarios() -> List[Scenario]:
    """Enumerate the full channel × message × binding-shape product."""

    scenarios: List[Scenario] = []
    for message_type in ("BOOTSTRAP", "DELEGATE", "REVOKE"):
        for tls_mode in ("tls-only", "mtls"):
            for binding_shape in (
                "present-correct",
                "present-tampered",
                "absent",
            ):
                expected_accepted, expected_error_code = _expected_outcome(
                    tls_mode, binding_shape
                )
                sid = f"{message_type.lower()}__{tls_mode}__{binding_shape}"
                description = _scenario_description(
                    message_type, tls_mode, binding_shape
                )
                scenarios.append(
                    Scenario(
                        scenario_id=sid,
                        message_type=message_type,
                        tls_mode=tls_mode,
                        binding_shape=binding_shape,
                        expected_accepted=expected_accepted,
                        expected_error_code=expected_error_code,
                        description=description,
                    )
                )
    return scenarios


def _scenario_description(
    message_type: str, tls_mode: str, binding_shape: str
) -> str:
    if tls_mode == "mtls":
        if binding_shape == "absent":
            return (
                f"{message_type} on mTLS without RFC 9266 binding "
                "must be rejected (Requirement 9.2.3)"
            )
        if binding_shape == "present-tampered":
            return (
                f"{message_type} on mTLS with tampered RFC 9266 binding "
                "must be rejected (design.md §9.3)"
            )
        return (
            f"{message_type} on mTLS with matching RFC 9266 binding "
            "must be accepted"
        )
    # tls-only.
    if binding_shape == "absent":
        return (
            f"{message_type} on tls-only without binding must be accepted "
            "(channel binding not required)"
        )
    if binding_shape == "present-tampered":
        return (
            f"{message_type} on tls-only with tampered binding must be "
            "rejected as malformed"
        )
    return (
        f"{message_type} on tls-only with stray binding must be rejected "
        "as malformed"
    )


# ---------------------------------------------------------------------------
# Execution.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class ScenarioResult:
    """Outcome of running one scenario."""

    scenario: Scenario
    actual: ValidationResult
    passed: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            **self.scenario.to_dict(),
            "actual_accepted": self.actual.accepted,
            "actual_error_code": self.actual.error_code,
            "actual_error_name": self.actual.error_name,
            "actual_reason": self.actual.reason,
            "passed": self.passed,
        }


def _make_tls_context(scenario: Scenario) -> TLSContext:
    """Build the live TLS context for a scenario."""

    if scenario.tls_mode == "mtls":
        return TLSContext(
            mode="mtls",
            connection_id=f"conformance/dim_channel/{scenario.scenario_id}",
            client_authenticated=True,
        )
    return TLSContext(
        mode="tls-only",
        connection_id=f"conformance/dim_channel/{scenario.scenario_id}",
        client_authenticated=False,
    )


def run_scenario(scenario: Scenario) -> ScenarioResult:
    """Execute one scenario through the RP-side validator."""

    tls_context = _make_tls_context(scenario)
    correct_binding = tls_context.exporter()
    envelope = _build_envelope(
        scenario.message_type, scenario.binding_shape, correct_binding
    )
    actual = validate_channel_binding(envelope, tls_context)

    passed = (
        actual.accepted == scenario.expected_accepted
        and actual.error_code == scenario.expected_error_code
    )
    return ScenarioResult(scenario=scenario, actual=actual, passed=passed)


def run_all() -> List[ScenarioResult]:
    """Run every scenario in :func:`all_scenarios`."""

    return [run_scenario(s) for s in all_scenarios()]
