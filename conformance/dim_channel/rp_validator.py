"""RP-side channel-binding validator (RFC 9266) for the channel dimension.

Implements the contract described by:

* Requirement 9.2.3 — *WHILE mTLS 被启用，THE Mandate SHALL 携带由 RFC 9266
  定义的 TLS Exporter 通道绑定值，且 Relying_Party SHALL 在校验阶段比对该值。*
* design.md §9.3 — Channel Binding clause, including the "Channel Binding
  value enters the signature input" extension that elevates a binding
  mismatch to ``E_ATTESTATION_INVALID`` (1007).

The validator is encoding-agnostic: it consumes a parsed envelope dict
(produced by either CBOR or JSON decoders, which is the encoding dimension's
job — task 5.2) plus the live :class:`~conformance.dim_channel.tls_context.TLSContext`,
and returns a :class:`ValidationResult`. Test drivers compare the result
against the per-vector ``expected.json`` to determine PASS / FAIL.

The validator never fakes data: it cross-checks the binding bytes against
the live exporter, and emits the precise error code the protocol mandates
when they diverge.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .tls_context import TLSContext


# Error codes — kept as constants so test assertions stay grep-able and the
# numeric values stay synchronized with §5.4 of the protocol spec.
E_OK: Optional[int] = None
E_ATTESTATION_INVALID = 1007
E_PROTOCOL = 1099


# Envelope key under which the conformance suite carries the RFC 9266
# binding bytes. The protocol spec leaves the wire shape implementation-
# defined as long as the binding "enters the signature input" (design.md
# §9.3 / §6.3). We pick a stable name here so vectors and reference
# implementations can interoperate against this conformance dimension.
CHANNEL_BINDING_FIELD = "channel_binding"


@dataclass(frozen=True)
class ValidationResult:
    """Outcome of an RP-side channel-binding check.

    Attributes:
        accepted: ``True`` iff the call would be accepted by an RP.
        error_code: ``None`` on accept, otherwise the §5.4 numeric code.
        error_name: human-readable §5.4 mnemonic, or ``None`` on accept.
        reason: free-form diagnostic. Never used by automated equality
            checks; surfaced in CLI / test failure messages.
    """

    accepted: bool
    error_code: Optional[int]
    error_name: Optional[str]
    reason: str

    @classmethod
    def accept(cls, reason: str = "channel binding satisfied") -> "ValidationResult":
        return cls(accepted=True, error_code=None, error_name=None, reason=reason)

    @classmethod
    def reject_attestation(cls, reason: str) -> "ValidationResult":
        return cls(
            accepted=False,
            error_code=E_ATTESTATION_INVALID,
            error_name="E_ATTESTATION_INVALID",
            reason=reason,
        )

    @classmethod
    def reject_protocol(cls, reason: str) -> "ValidationResult":
        return cls(
            accepted=False,
            error_code=E_PROTOCOL,
            error_name="E_PROTOCOL",
            reason=reason,
        )


def _extract_binding(envelope: Dict[str, Any]) -> Optional[bytes]:
    """Return the RFC 9266 binding bytes from ``envelope`` if present.

    Conformance vectors may carry the binding either at envelope top-level
    (the most common shape used by reference implementations) or inside the
    ``claims`` block (so vectors that mirror BOOTSTRAP / DELEGATE inner
    Mandate structures stay valid). We accept either location.
    """

    for container in (envelope, envelope.get("claims") or {}):
        if not isinstance(container, dict):
            continue
        value = container.get(CHANNEL_BINDING_FIELD)
        if value is None:
            continue
        if isinstance(value, (bytes, bytearray)):
            return bytes(value)
        # Test vectors that round-trip through JSON serialise bytes as
        # ``{"__b64__": "..."}`` (see pbt/fap/__init__.py). Decode lazily.
        if isinstance(value, dict) and "__b64__" in value:
            import base64

            try:
                return base64.b64decode(value["__b64__"])
            except Exception:  # pragma: no cover - malformed vector
                return None
    return None


def validate_channel_binding(
    envelope: Dict[str, Any],
    tls_context: TLSContext,
) -> ValidationResult:
    """Apply the RFC 9266 channel-binding check to a single call.

    The matrix encoded by Requirement 9.2.3 / design.md §9.3 is::

        mode      | binding present | binding matches exporter | result
        ----------|-----------------|--------------------------|----------------------
        tls-only  | absent          | n/a                      | accept (not required)
        tls-only  | present         | matches                  | accept
        tls-only  | present         | mismatches               | reject E_PROTOCOL
                  |                 |                          |   (binding without mTLS
                  |                 |                          |    is malformed; see §9.3)
        mtls      | absent          | n/a                      | reject E_ATTESTATION_INVALID
        mtls      | present         | matches                  | accept
        mtls      | present         | mismatches               | reject E_ATTESTATION_INVALID

    Note: the "binding present without mTLS" row is treated as a malformed
    envelope (E_PROTOCOL), not a security failure, because the binding has
    nothing to compare against on a TLS-only channel.
    """

    binding = _extract_binding(envelope)
    expected = tls_context.exporter()

    if tls_context.requires_channel_binding():
        # mTLS — Requirement 9.2.3 hard requirement.
        if binding is None:
            return ValidationResult.reject_attestation(
                "mTLS channel requires RFC 9266 TLS Exporter binding (Requirement 9.2.3)"
            )
        if binding != expected:
            return ValidationResult.reject_attestation(
                "RFC 9266 TLS Exporter binding does not match live TLS context "
                "(design.md §9.3 — Mandate stripped to another TLS channel)"
            )
        return ValidationResult.accept(
            "mTLS: RFC 9266 TLS Exporter binding matches live exporter"
        )

    # tls-only — binding is OPTIONAL. We still reject envelopes that ship a
    # binding but the live channel is not mTLS, because such an envelope
    # cannot have been produced by a conformant client (the binding has no
    # peer to bind to) and silently accepting it would let a misconfigured
    # client downgrade itself to TLS-only without anyone noticing.
    if binding is not None:
        return ValidationResult.reject_protocol(
            "channel_binding present on a tls-only channel (no peer to bind to)"
        )
    return ValidationResult.accept(
        "tls-only: channel binding not required (Requirement 9.2.3 conditional)"
    )
