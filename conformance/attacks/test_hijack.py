"""Mandate hijack attack-simulation suite (task 6.2).

**Validates: Requirements 9.2** (anti-hijack, including RFC 9266 Channel Binding)

This module simulates an adversary that *strips* a legitimately issued
Mandate from the TLS channel on which it was bound and replays it on a
foreign channel — different ``device_id``, different TLS Exporter, or
both. The protocol's defence is two-layered (design.md §9.3):

1. **Device binding (always on).** Every Mandate is issued bound to the
   iFay instance's ``device_id`` + ``device_attestation``; cross-device
   reuse MUST be rejected and the caller MUST be redirected to the
   ``DELEGATE`` flow so a fresh device-bound child Mandate is issued.
2. **Channel binding (mTLS only, RFC 9266).** When the channel is mTLS
   the Mandate carries the TLS Exporter value bound at issuance; the
   Relying Party MUST recompute the exporter on the live connection and
   reject the request if it does not match. TLS-only sessions are not
   required to ship a TLS Exporter — Requirement 9.2.3 explicitly
   scopes the binding check to ``WHILE mTLS 被启用``.

The acceptance criteria (``tasks.md §6.2``) require:

* cross-device direct reuse → rejected, with a hint to take ``DELEGATE``;
* mTLS channel-binding mismatch → rejected.

Both must hold under the mixed mTLS / TLS-only matrix to make sure the
TLS-only branch does *not* short-circuit the device-binding check.

Implementation notes:

* The reference Relying Party here is **Not Normative** — it mirrors
  the rejection branch declared in design.md §9.3 / §EH.4 (Default-Deny
  convergence to ``E_PROTOCOL``). Wire-format conformance lives in
  ``conformance/dim_*/`` (tasks 5.2 – 5.5) and ``vectors/``.
* Hypothesis is used to widen the search around ``device_id`` and
  TLS-Exporter byte sequences so that boundary cases (collisions,
  empty bytes, off-by-one width) cannot hide.
* The attack scenarios deliberately fix the Mandate signature itself as
  *valid* — this test models *channel hijack*, not *signature forgery*
  (signature forgery is covered by Requirement 9.3 / task 6.3 phishing
  and by the P13 audit-chain property test).

References:
    requirements.md §9.2 (Acceptance Criteria 1–4)
    design.md §9.3 (抗劫持), §6.2 (Presence-Bound Mandate Key),
    design.md §5.4 (E_PROTOCOL / 1099), §EH.4 (Default-Deny)
"""

from __future__ import annotations

import hashlib
import os
import secrets
from dataclasses import dataclass, field
from typing import Optional

import pytest
from hypothesis import HealthCheck, assume, given, settings, strategies as st


# ---------------------------------------------------------------------------
# Constants — kept in sync with design.md §5.4 and §EH.4.
# ---------------------------------------------------------------------------
ACCEPTED = "accepted"

# Default-Deny convergence: design.md §EH.4 mandates that any rejection
# whose precise category is not codified collapses to E_PROTOCOL.
# Requirement 9.2 does not allocate a dedicated hijack code; both the
# cross-device reuse path and the channel-binding mismatch path therefore
# surface as E_PROTOCOL with a category-specific ``recovery_hint``.
E_PROTOCOL = "E_PROTOCOL"  # design.md §5.4 row 1099

# Recovery hints — surfaced via the ERROR envelope's ``recovery_hint``
# field (design.md §EH.1 column "IF 响应"). Stable strings let the
# conformance assertions pin the redirect target.
HINT_DELEGATE = "use DELEGATE for cross-device binding"
HINT_REBIND_CHANNEL = "rebind on the original mTLS channel"

# TLS Exporter width — RFC 9266 mandates the application caller picks a
# width; this reference uses 32 bytes (the practical default that
# matches TLS 1.3's exporter output size for HMAC-SHA-256).
TLS_EXPORTER_BYTES = 32


# ---------------------------------------------------------------------------
# Reference data classes — Not Normative.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Mandate:
    """Subset of the §4 Mandate used by the hijack tests.

    Only the fields the §9.3 anti-hijack defence reads are modelled
    here. ``signature_ok`` short-circuits the cryptographic check that
    is exercised exhaustively by the P-tests; the hijack defence runs
    *after* signature verification has already succeeded.
    """

    mandate_id: str
    issuer: str           # Human Prime ID
    subject: str          # FayID
    bound_device_id: str  # design.md §9.3 — Mandate ↔ device_id
    # ``bound_channel_binding`` is None for TLS-only issuance; bytes for
    # mTLS issuance (RFC 9266 TLS Exporter snapshotted at BOOTSTRAP).
    bound_channel_binding: Optional[bytes]
    signature_ok: bool = True


@dataclass(frozen=True)
class Connection:
    """Live TLS connection presented at request time.

    ``mtls`` mirrors the conformance matrix's ``channel`` dimension
    (`tls-only` / `mtls`). When ``mtls`` is true the Relying Party
    snapshots the connection's TLS Exporter and demands it match the
    Mandate's pin. When ``mtls`` is false the Relying Party MUST NOT
    consult ``channel_binding`` (Requirement 9.2.3 scoping).

    ``presenting_device_id`` is the device the request *claims* to come
    from. The hijack scenarios deliberately drift this from
    ``Mandate.bound_device_id``.
    """

    presenting_device_id: str
    mtls: bool
    channel_binding: Optional[bytes]


@dataclass
class RelyingParty:
    """Reference §9.3 anti-hijack verifier — Not Normative.

    The ``verify`` method mirrors the rejection branch enumerated in
    design.md §9.3:

    * mismatched ``device_id``  → ``E_PROTOCOL`` + ``HINT_DELEGATE``
    * mismatched mTLS exporter  → ``E_PROTOCOL`` + ``HINT_REBIND_CHANNEL``
    * mTLS Mandate replayed onto TLS-only → also ``HINT_REBIND_CHANNEL``
      (the Mandate carries an exporter pin but no live exporter exists
      to compare against — design.md §9.3 still treats this as channel
      stripping)

    Audit events mirror the §EH.1 mandate that all such rejections cut a
    security-audit row.
    """

    audit_log: list[str] = field(default_factory=list)

    def verify(self, mandate: Mandate, conn: Connection) -> tuple[str, Optional[str]]:
        """Return ``(verdict, recovery_hint)``.

        ``verdict`` is :data:`ACCEPTED` or :data:`E_PROTOCOL`.
        ``recovery_hint`` is set whenever a hint is appropriate.
        """

        # Pre-condition: signature already verified upstream. Any
        # signature failure surfaces as ``E_ATTESTATION_INVALID`` (1007)
        # — that path is owned by Requirement 9.3 / task 6.3 and is not
        # part of the hijack defence proper.
        if not mandate.signature_ok:
            self.audit_log.append("E_ATTESTATION_INVALID")
            return ("E_ATTESTATION_INVALID", None)

        # Layer 1 — device binding (Requirement 9.2.1 + 9.2.2).
        if mandate.bound_device_id != conn.presenting_device_id:
            self.audit_log.append(
                f"hijack:cross-device:{mandate.mandate_id}:"
                f"{mandate.bound_device_id}->{conn.presenting_device_id}"
            )
            return (E_PROTOCOL, HINT_DELEGATE)

        # Layer 2 — RFC 9266 channel binding (Requirement 9.2.3).
        if mandate.bound_channel_binding is not None:
            # Mandate was issued on mTLS → the connection at use-time
            # MUST also be mTLS *and* its exporter MUST match.
            if not conn.mtls:
                self.audit_log.append(
                    f"hijack:mtls-stripped:{mandate.mandate_id}"
                )
                return (E_PROTOCOL, HINT_REBIND_CHANNEL)
            if conn.channel_binding != mandate.bound_channel_binding:
                self.audit_log.append(
                    f"hijack:channel-binding-mismatch:{mandate.mandate_id}"
                )
                return (E_PROTOCOL, HINT_REBIND_CHANNEL)
        else:
            # Mandate was issued on TLS-only → §9.3 does not require a
            # channel-binding check (Requirement 9.2.3 is scoped to
            # ``WHILE mTLS 被启用``). The presence of a stray exporter on
            # the connection is allowed and ignored.
            pass

        return (ACCEPTED, None)


# ---------------------------------------------------------------------------
# Helpers — issuance under the matrix's mTLS / TLS-only branches.
# ---------------------------------------------------------------------------
def _issue_mandate(
    *,
    mandate_id: str,
    device_id: str,
    mtls: bool,
    channel_binding: Optional[bytes] = None,
    signature_ok: bool = True,
) -> Mandate:
    """Construct a Mandate as if just issued on the given channel.

    * ``mtls=True``  → ``bound_channel_binding`` MUST be set (the issued
      Mandate snapshots the TLS Exporter at BOOTSTRAP time, design.md
      §9.3). If the caller does not pass a value we synthesise one so
      the test fixture is well-formed.
    * ``mtls=False`` → ``bound_channel_binding`` is ``None``.
    """

    if mtls:
        cb = channel_binding if channel_binding is not None else os.urandom(
            TLS_EXPORTER_BYTES
        )
    else:
        # TLS-only issuance never pins an exporter.
        cb = None
    return Mandate(
        mandate_id=mandate_id,
        issuer="hp:01HXHP-HIJACK-FIXTURE",
        subject="fay:01HXFAY-HIJACK-FIXTURE",
        bound_device_id=device_id,
        bound_channel_binding=cb,
        signature_ok=signature_ok,
    )


# ---------------------------------------------------------------------------
# Hypothesis strategies.
# ---------------------------------------------------------------------------
# Device IDs follow the ``terminal:<form-factor>:<short-id>`` shape used
# by the existing delegate vectors so the search space mirrors the wire
# format conventions (vectors/delegate/pos-cross-device-binding).
_FORM_FACTORS = ("phone", "laptop", "tablet", "watch", "desktop")


def _device_id_strategy() -> st.SearchStrategy[str]:
    return st.builds(
        lambda f, s: f"terminal:{f}:{s}",
        st.sampled_from(_FORM_FACTORS),
        st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz0123456789-",
            min_size=3,
            max_size=10,
        ),
    )


def _exporter_strategy() -> st.SearchStrategy[bytes]:
    return st.binary(min_size=TLS_EXPORTER_BYTES, max_size=TLS_EXPORTER_BYTES)


# ---------------------------------------------------------------------------
# 1. Cross-device direct reuse — rejected with DELEGATE hint.
# ---------------------------------------------------------------------------
@given(
    bound=_device_id_strategy(),
    presenting=_device_id_strategy(),
    mtls=st.booleans(),
)
@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hijack_cross_device_reuse_is_rejected_with_delegate_hint(
    bound: str,
    presenting: str,
    mtls: bool,
) -> None:
    """**Validates: Requirements 9.2** (Acceptance Criteria 1 + 2).

    For any Mandate whose ``bound_device_id`` differs from the
    presenting device's ID, the Relying Party MUST reject the request
    AND surface a recovery hint pointing at the DELEGATE flow. The
    rejection MUST hold under both ``tls-only`` and ``mtls`` channels —
    device binding is independent of the channel dimension.
    """

    assume(bound != presenting)

    # When mtls is on, build a connection whose channel binding *matches*
    # the Mandate so the test isolates the device-binding check.
    cb = os.urandom(TLS_EXPORTER_BYTES) if mtls else None
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-CROSS-DEVICE",
        device_id=bound,
        mtls=mtls,
        channel_binding=cb,
    )
    conn = Connection(
        presenting_device_id=presenting,
        mtls=mtls,
        channel_binding=cb,
    )

    rp = RelyingParty()
    verdict, hint = rp.verify(mandate, conn)

    assert verdict == E_PROTOCOL, (
        "Cross-device direct reuse must be rejected with E_PROTOCOL; "
        f"got verdict={verdict!r} (mtls={mtls}, "
        f"bound={bound!r}, presenting={presenting!r})"
    )
    assert hint == HINT_DELEGATE, (
        "Requirement 9.2.2 mandates the recovery hint redirect to DELEGATE; "
        f"got hint={hint!r}"
    )
    assert any(line.startswith("hijack:cross-device:") for line in rp.audit_log), (
        "Cross-device hijack must cut a security-audit row (design.md §EH.1)."
    )


def test_hijack_cross_device_rejection_under_tls_only_branch() -> None:
    """Pin: TLS-only branch must still reject cross-device reuse.

    Sanity row of the matrix's ``channel`` dimension: the TLS-only path
    MUST NOT short-circuit device binding (Requirement 9.2.1 has no
    ``WHILE`` guard).
    """

    mandate = _issue_mandate(
        mandate_id="01HXMNDT-TLS-ONLY-XDEV",
        device_id="terminal:laptop:alpha-001",
        mtls=False,
    )
    conn = Connection(
        presenting_device_id="terminal:phone:beta-002",
        mtls=False,
        channel_binding=None,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_DELEGATE


def test_hijack_cross_device_rejection_under_mtls_branch() -> None:
    """Pin: mTLS branch with matching exporter still rejects cross-device.

    The mTLS path proves that even an attacker who replays the original
    TLS Exporter (e.g. via a co-resident process exfiltrating the
    keying material) cannot bypass device binding.
    """

    cb = os.urandom(TLS_EXPORTER_BYTES)
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-MTLS-XDEV",
        device_id="terminal:laptop:alpha-001",
        mtls=True,
        channel_binding=cb,
    )
    conn = Connection(
        presenting_device_id="terminal:phone:beta-002",
        mtls=True,
        channel_binding=cb,  # exporter matches but device drifts
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_DELEGATE


# ---------------------------------------------------------------------------
# 2. mTLS channel-binding mismatch — rejected with rebind hint.
# ---------------------------------------------------------------------------
@given(
    bound_cb=_exporter_strategy(),
    presented_cb=_exporter_strategy(),
)
@settings(
    max_examples=200,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hijack_mtls_channel_binding_mismatch_is_rejected(
    bound_cb: bytes,
    presented_cb: bytes,
) -> None:
    """**Validates: Requirements 9.2** (Acceptance Criterion 3).

    Under mTLS, when the Mandate's pinned TLS Exporter does not match
    the live connection's exporter, the Relying Party MUST reject the
    request. The device dimension is held constant so the property
    isolates the §9.3 channel-binding leg.
    """

    assume(bound_cb != presented_cb)

    device = "terminal:laptop:cb-isolated"
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-CB-MISMATCH",
        device_id=device,
        mtls=True,
        channel_binding=bound_cb,
    )
    conn = Connection(
        presenting_device_id=device,
        mtls=True,
        channel_binding=presented_cb,
    )
    rp = RelyingParty()
    verdict, hint = rp.verify(mandate, conn)

    assert verdict == E_PROTOCOL, (
        "mTLS channel-binding mismatch must be rejected with E_PROTOCOL; "
        f"got verdict={verdict!r}, "
        f"bound_cb_hex={bound_cb.hex()[:16]}..., "
        f"presented_cb_hex={presented_cb.hex()[:16]}..."
    )
    assert hint == HINT_REBIND_CHANNEL, (
        "RFC 9266 mismatch must redirect the caller to rebind on the "
        f"original mTLS channel; got hint={hint!r}"
    )
    assert any(
        line.startswith("hijack:channel-binding-mismatch:")
        for line in rp.audit_log
    )


def test_hijack_mtls_channel_binding_match_is_accepted() -> None:
    """Sanity: identical exporter on the same device MUST accept.

    Without this row the mismatch property could vacuously pass via an
    over-strict reference Relying Party. The acceptance branch is the
    Requirement 9.2 invariant in its positive form.
    """

    cb = b"\xa1" * TLS_EXPORTER_BYTES
    device = "terminal:laptop:cb-match"
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-CB-MATCH",
        device_id=device,
        mtls=True,
        channel_binding=cb,
    )
    conn = Connection(
        presenting_device_id=device,
        mtls=True,
        channel_binding=cb,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == ACCEPTED
    assert hint is None


def test_hijack_mtls_mandate_replayed_on_tls_only_is_rejected() -> None:
    """Pin: a Mandate issued under mTLS MUST NOT be replayed on TLS-only.

    Requirement 9.2.3's binding requirement is asymmetric — once a
    Mandate carries a TLS Exporter pin the channel cannot be downgraded
    to TLS-only at use time without losing the binding evidence.
    """

    cb = os.urandom(TLS_EXPORTER_BYTES)
    device = "terminal:laptop:downgrade"
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-MTLS-DOWNGRADE",
        device_id=device,
        mtls=True,
        channel_binding=cb,
    )
    conn = Connection(
        presenting_device_id=device,
        mtls=False,
        channel_binding=None,
    )
    rp = RelyingParty()
    verdict, hint = rp.verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_REBIND_CHANNEL
    assert any(
        line.startswith("hijack:mtls-stripped:") for line in rp.audit_log
    )


# ---------------------------------------------------------------------------
# 3. TLS-only path — Channel Binding is *not required* (9.2.3 scoping).
# ---------------------------------------------------------------------------
@given(
    stray_cb=st.one_of(st.none(), _exporter_strategy()),
    device=_device_id_strategy(),
)
@settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)
def test_hijack_tls_only_does_not_require_channel_binding(
    stray_cb: Optional[bytes],
    device: str,
) -> None:
    """**Validates: Requirements 9.2.3** scoping clause (``WHILE mTLS 被启用``).

    A Mandate issued on TLS-only carries no TLS Exporter pin. The
    Relying Party MUST NOT spuriously reject such a request even if the
    live connection happens to advertise a stray exporter (e.g. mTLS
    *was* negotiated but the issuance side opted out of the binding).
    The acceptance branch here is necessary so the §9.2 mismatch test
    above is genuinely tight rather than an artefact of an
    overzealous reference verifier.
    """

    mandate = _issue_mandate(
        mandate_id="01HXMNDT-TLS-ONLY",
        device_id=device,
        mtls=False,
    )
    conn = Connection(
        presenting_device_id=device,
        mtls=stray_cb is not None,
        channel_binding=stray_cb,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == ACCEPTED, (
        "TLS-only Mandates must not gate on Channel Binding (9.2.3 scoping). "
        f"verdict={verdict!r}, hint={hint!r}, stray_cb_set={stray_cb is not None}"
    )
    assert hint is None


# ---------------------------------------------------------------------------
# 4. Combined hijack (cross-device AND CB mismatch) — device check wins.
# ---------------------------------------------------------------------------
def test_hijack_combined_cross_device_and_cb_mismatch_returns_delegate_hint() -> None:
    """Pin: when both layers are violated, the device-binding hint wins.

    The protocol's user-facing recovery story prefers the most specific
    actionable hint. Cross-device reuse is recoverable via DELEGATE
    (a flow the caller can initiate on its own), whereas a CB mismatch
    is only recoverable by re-binding on the *original* channel — a
    weaker affordance. Surfacing :data:`HINT_DELEGATE` first keeps the
    caller on the more productive recovery path.
    """

    bound_cb = b"\x01" * TLS_EXPORTER_BYTES
    presented_cb = b"\x02" * TLS_EXPORTER_BYTES
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-DOUBLE-VIOLATION",
        device_id="terminal:laptop:alpha-001",
        mtls=True,
        channel_binding=bound_cb,
    )
    conn = Connection(
        presenting_device_id="terminal:phone:beta-002",
        mtls=True,
        channel_binding=presented_cb,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_DELEGATE


# ---------------------------------------------------------------------------
# 5. Coverage matrix — every (channel, attack) cell is exercised.
# ---------------------------------------------------------------------------
# This parametrised test acts as the human-readable "matrix table" of
# the hijack scenarios. It is redundant with the property tests above
# but makes the channel × attack-class coverage explicit at-a-glance,
# which the §6.2 acceptance criteria call out by name (``混合 mTLS 与
# TLS-only 两种场景``).
_HijackCase = tuple[str, bool, str, str, Optional[str]]
_CASES: tuple[_HijackCase, ...] = (
    # (label, mtls, attack, expected_verdict, expected_hint)
    ("mtls/cross-device", True, "cross-device", E_PROTOCOL, HINT_DELEGATE),
    ("tls-only/cross-device", False, "cross-device", E_PROTOCOL, HINT_DELEGATE),
    ("mtls/cb-mismatch", True, "cb-mismatch", E_PROTOCOL, HINT_REBIND_CHANNEL),
    ("mtls/cb-stripped", True, "cb-stripped", E_PROTOCOL, HINT_REBIND_CHANNEL),
    ("mtls/baseline", True, "baseline", ACCEPTED, None),
    ("tls-only/baseline", False, "baseline", ACCEPTED, None),
)


@pytest.mark.parametrize("label,mtls,attack,expected_verdict,expected_hint", _CASES)
def test_hijack_matrix(
    label: str,
    mtls: bool,
    attack: str,
    expected_verdict: str,
    expected_hint: Optional[str],
) -> None:
    """**Validates: Requirements 9.2** (combined matrix).

    Walks the (channel × attack) cells listed in :data:`_CASES`. Each
    row is a deterministic, named instance of the property tests above
    so the matrix coverage is auditable in the CI log without scrolling
    through Hypothesis statistics.
    """

    bound_device = "terminal:laptop:matrix-bound"
    presenting_device = bound_device
    bound_cb: Optional[bytes] = None
    presented_cb: Optional[bytes] = None
    presenting_mtls = mtls

    if mtls:
        # Deterministic exporter so the matrix row is reproducible.
        bound_cb = hashlib.sha256(f"matrix:{label}:bound".encode("ascii")).digest()
        presented_cb = bound_cb  # baseline parity

    if attack == "cross-device":
        presenting_device = "terminal:phone:matrix-attacker"
    elif attack == "cb-mismatch":
        # Only meaningful under mTLS.
        presented_cb = hashlib.sha256(
            f"matrix:{label}:presented".encode("ascii")
        ).digest()
    elif attack == "cb-stripped":
        # Mandate issued under mTLS but presented on TLS-only.
        presenting_mtls = False
        presented_cb = None
    elif attack == "baseline":
        pass
    else:  # pragma: no cover - defensive
        raise AssertionError(f"unknown attack class: {attack}")

    mandate = _issue_mandate(
        mandate_id=f"01HXMNDT-MATRIX-{label}",
        device_id=bound_device,
        mtls=mtls,
        channel_binding=bound_cb,
    )
    conn = Connection(
        presenting_device_id=presenting_device,
        mtls=presenting_mtls,
        channel_binding=presented_cb,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == expected_verdict, (
        f"matrix row {label!r} verdict mismatch: "
        f"expected {expected_verdict!r}, got {verdict!r}"
    )
    assert hint == expected_hint, (
        f"matrix row {label!r} hint mismatch: "
        f"expected {expected_hint!r}, got {hint!r}"
    )


# ---------------------------------------------------------------------------
# 6. Regression seeds — concrete bytes lifted from vectors/delegate/.
# ---------------------------------------------------------------------------
def test_hijack_regression_cross_device_seed_from_vectors() -> None:
    """Seed test using the exact device IDs from
    ``vectors/delegate/pos-cross-device-binding/``.

    The seed binds the test to a published vector so that drift between
    the vectors and the conformance suite surfaces here first.
    """

    # Bound device matches the parent Mandate's issuing terminal in the
    # delegate vector; the presenting device matches the child's. The
    # vector exists *because* of the §9.3 cross-device defence — direct
    # reuse without DELEGATE must be rejected.
    parent_terminal = "terminal:laptop:mobile-1"
    child_terminal = "terminal:phone:mobile-2"

    mandate = _issue_mandate(
        mandate_id="01HXMNDT-PARENT-POS_CROSS_DEVICE_BINDING",
        device_id=parent_terminal,
        mtls=False,
    )
    conn = Connection(
        presenting_device_id=child_terminal,
        mtls=False,
        channel_binding=None,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_DELEGATE


def test_hijack_regression_attacker_cannot_forge_exporter() -> None:
    """Seed test: an attacker generating fresh random bytes never wins.

    Pins the practical security claim: even with full control over the
    presented exporter (random sampling), the probability of colliding
    with a 32-byte SHA-256 digest is negligible. ``secrets.token_bytes``
    is used so the fixture is non-deterministic across runs without
    introducing flakiness (the negative path is satisfied by *any*
    differing exporter).
    """

    bound_cb = hashlib.sha256(b"hijack:regression:bound").digest()
    forged_cb = secrets.token_bytes(TLS_EXPORTER_BYTES)
    assert forged_cb != bound_cb  # negligible-probability sanity guard

    device = "terminal:laptop:regression"
    mandate = _issue_mandate(
        mandate_id="01HXMNDT-REGRESSION-CB",
        device_id=device,
        mtls=True,
        channel_binding=bound_cb,
    )
    conn = Connection(
        presenting_device_id=device,
        mtls=True,
        channel_binding=forged_cb,
    )
    verdict, hint = RelyingParty().verify(mandate, conn)

    assert verdict == E_PROTOCOL
    assert hint == HINT_REBIND_CHANNEL
