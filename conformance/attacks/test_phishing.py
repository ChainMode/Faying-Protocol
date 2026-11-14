"""Anti-phishing conformance tests — Requirement 9.3 / design.md §9.4.

This module implements task 6.3「跨域钓鱼模拟」of the Faying Protocol/1.0
spec. It exercises three adversary paths against a *reference verifier*
that codifies Requirement 9.3 (Acceptance Criteria 1–4):

1. **Cross-origin WebAuthn assertion** — WebAuthn binds the user-verification
   ceremony to a specific RP origin. A BOOTSTRAP that carries a
   ``human_witness`` whose ``clientDataJSON.origin`` is **not** the issuer's
   expected origin must be rejected. Acceptance: BOOTSTRAP rejected with
   ``E_HUMAN_WITNESS_REQUIRED`` (1010) — the witness is not verifiable for
   this RP, so it is treated as missing.
2. **"Remote link + single consent button" path** — design.md §9.4 mandates
   that BOOTSTRAP MUST be initiated by HP while physically holding the
   Presence Device. There is no protocol path where a remote URL plus a
   single-click consent yields a valid Mandate. Any envelope that signals
   the remote-consent affordance MUST be rejected, regardless of TLS
   posture or signature freshness.
3. **DELEGATE missing parent counter-signature** — design.md §9.4 / §6.3
   require ``signature.chain`` to carry the parent Mandate's signature on
   any DELEGATE response. A child Mandate whose ``signature.chain`` is
   absent or empty MUST be rejected with ``E_ATTESTATION_INVALID`` (1007).

The verifier exposed here is **not normative**: the authoritative rules
live in the spec and CDDL schema. It is just dense enough to make the
attack assertions concrete and to surface schema drift early.

Usage::

    pytest conformance/attacks/test_phishing.py -q

The tests degrade gracefully when ``hypothesis`` is unavailable
(``hypothesis``-decorated tests are skipped) but require ``cbor2`` to
load the official vectors; environments without ``cbor2`` skip the
vector-seeded tests and rely on the synthetic in-module fixtures.
"""

from __future__ import annotations

import base64
import copy
import json
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pytest

try:  # pragma: no cover - import guard
    import cbor2  # type: ignore[import-not-found]

    _HAS_CBOR2 = True
except ImportError:  # pragma: no cover - import guard
    cbor2 = None  # type: ignore[assignment]
    _HAS_CBOR2 = False

try:  # pragma: no cover - import guard
    from hypothesis import HealthCheck, given, settings, strategies as st

    _HAS_HYPOTHESIS = True
except ImportError:  # pragma: no cover - import guard
    _HAS_HYPOTHESIS = False


# ---------------------------------------------------------------------------
# Repository anchors.
# ---------------------------------------------------------------------------
HERE = Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent
VECTORS_DIR = REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Error codes (mirrored from design.md §5.4 — kept in sync manually).
# ---------------------------------------------------------------------------
E_HUMAN_WITNESS_REQUIRED = (1010, "E_HUMAN_WITNESS_REQUIRED")
E_ATTESTATION_INVALID = (1007, "E_ATTESTATION_INVALID")
E_PROTOCOL = (1099, "E_PROTOCOL")


# ---------------------------------------------------------------------------
# Reference verifier — encodes Requirement 9.3 acceptance criteria 1–4.
# ---------------------------------------------------------------------------
class VerifierReject(Exception):
    """Verifier rejected an envelope. Carries (code, name)."""

    def __init__(self, code: int, name: str, reason: str) -> None:
        super().__init__(f"{name} ({code}): {reason}")
        self.code = code
        self.name = name
        self.reason = reason


def _b64url_decode(s: str) -> bytes:
    # WebAuthn clientDataJSON is a UTF-8 byte string; the official vectors
    # encode it as base64url (sometimes padded, sometimes not). Be liberal
    # in what we accept since this is just an attack-simulation harness.
    pad = "=" * (-len(s) % 4)
    try:
        return base64.urlsafe_b64decode(s + pad)
    except Exception:  # pragma: no cover - exercised only on malformed input
        return base64.b64decode(s + pad)


def _client_data_origin(client_data: Any) -> Optional[str]:
    """Extract the WebAuthn ``clientDataJSON.origin`` field if present.

    Accepts either raw bytes (CBOR ``bstr``), a base64url string, or a
    pre-decoded mapping. Returns ``None`` when the field cannot be parsed
    so the caller can treat this as a malformed witness.
    """

    if isinstance(client_data, dict):
        return client_data.get("origin")
    if isinstance(client_data, (bytes, bytearray)):
        raw = bytes(client_data)
    elif isinstance(client_data, str):
        raw = _b64url_decode(client_data)
    else:
        return None
    try:
        return json.loads(raw.decode("utf-8")).get("origin")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def _client_data_cross_origin(client_data: Any) -> Optional[bool]:
    if isinstance(client_data, dict):
        return client_data.get("crossOrigin")
    if isinstance(client_data, (bytes, bytearray)):
        raw = bytes(client_data)
    elif isinstance(client_data, str):
        raw = _b64url_decode(client_data)
    else:
        return None
    try:
        return json.loads(raw.decode("utf-8")).get("crossOrigin")
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def verify_bootstrap(envelope: Dict[str, Any], expected_origin: str) -> None:
    """Reference verifier for the BOOTSTRAP path.

    Encodes Requirement 9.3 sub-clauses 1, 2, and 4:
    * Sub-clause 1: BOOTSTRAP must be initiated locally by HP — surfaced
      via the protocol-level ``faying_initiation`` discriminator.
      ``faying_initiation = "remote-link-single-click"`` is treated as the
      "remote link + single consent button" affordance and rejected
      immediately.
    * Sub-clause 2: WebAuthn ``origin`` must match the RP's expected
      origin and ``crossOrigin`` must be ``false``.
    * Sub-clause 4: There is no legal "remote consent" path — any envelope
      that *self-declares* a remote-consent flag fails closed even if the
      structural fields look superficially valid.
    """

    claims = envelope.get("claims") if isinstance(envelope, dict) else None
    if not isinstance(claims, dict):
        raise VerifierReject(*E_PROTOCOL, "missing claims")

    # Sub-clause 4 — no legal remote-consent path.
    if claims.get("faying_initiation") == "remote-link-single-click":
        raise VerifierReject(
            *E_HUMAN_WITNESS_REQUIRED,
            "remote-link single-consent path is not a legal BOOTSTRAP path",
        )

    witness = claims.get("human_witness")
    if not isinstance(witness, dict):
        raise VerifierReject(*E_HUMAN_WITNESS_REQUIRED, "human_witness missing")

    cdata = witness.get("client_data_json")
    origin = _client_data_origin(cdata)
    cross = _client_data_cross_origin(cdata)
    if origin is None:
        raise VerifierReject(
            *E_HUMAN_WITNESS_REQUIRED,
            "human_witness.client_data_json missing origin",
        )

    # Sub-clause 2 — origin must match; crossOrigin must be false.
    if origin != expected_origin:
        raise VerifierReject(
            *E_HUMAN_WITNESS_REQUIRED,
            f"clientDataJSON.origin {origin!r} != expected {expected_origin!r}",
        )
    if cross is True:
        raise VerifierReject(
            *E_HUMAN_WITNESS_REQUIRED,
            "clientDataJSON.crossOrigin must be false",
        )


def verify_delegate(envelope: Dict[str, Any]) -> None:
    """Reference verifier for the DELEGATE response path (sub-clause 3).

    Requires ``claims.signature.chain`` to be a non-empty array of byte
    strings. An empty or missing chain means the parent Mandate did not
    counter-sign the child, which is exactly the attack vector enabling
    "single MS compromise → bulk forged delegations" (design.md §9.4).
    """

    claims = envelope.get("claims") if isinstance(envelope, dict) else None
    if not isinstance(claims, dict):
        raise VerifierReject(*E_PROTOCOL, "missing claims")

    sig = claims.get("signature")
    if not isinstance(sig, dict):
        raise VerifierReject(*E_ATTESTATION_INVALID, "signature missing")

    chain = sig.get("chain")
    if chain is None or chain == [] or not isinstance(chain, list):
        raise VerifierReject(
            *E_ATTESTATION_INVALID,
            "DELEGATE response missing parent Mandate counter-signature (signature.chain)",
        )
    for entry in chain:
        if not isinstance(entry, (bytes, bytearray)) or len(entry) == 0:
            raise VerifierReject(
                *E_ATTESTATION_INVALID,
                "signature.chain entry is not a non-empty bstr",
            )


# ---------------------------------------------------------------------------
# Vector loaders (best-effort; gracefully skipped on missing files).
# ---------------------------------------------------------------------------
EXPECTED_ORIGIN = "https://faying.example"
"""All official vectors use this origin (see vectors/bootstrap/.../debug.json)."""


def _load_cbor(path: Path) -> Optional[Any]:
    if not _HAS_CBOR2 or not path.exists():
        return None
    with path.open("rb") as fh:
        return cbor2.load(fh)  # type: ignore[union-attr]


def _bootstrap_seed() -> Optional[Dict[str, Any]]:
    """Return a deep copy of the canonical positive BOOTSTRAP envelope.

    Falls back to a synthetic envelope shaped like the CDDL when the
    official vectors are missing or ``cbor2`` is not installed. The deep
    copy lets each test mutate independently without leaking state.
    """

    seed = _load_cbor(VECTORS_DIR / "bootstrap" / "pos-cbor-ed25519" / "request.cbor")
    if isinstance(seed, dict) and "claims" in seed:
        return copy.deepcopy(seed)
    return _synthetic_bootstrap()


def _delegate_seed() -> Optional[Dict[str, Any]]:
    seed = _load_cbor(VECTORS_DIR / "delegate" / "pos-chain-verify" / "response.cbor")
    if isinstance(seed, dict) and "claims" in seed:
        return copy.deepcopy(seed)
    return _synthetic_delegate_response()


def _synthetic_bootstrap() -> Dict[str, Any]:
    """Minimal BOOTSTRAP envelope sufficient for the verifier."""

    client_data = json.dumps(
        {
            "type": "webauthn.get",
            "challenge": "TvNo7bLSIm6dRi59Ehsi7fXxDn22ro69_ki9HZlkZ3U",
            "origin": EXPECTED_ORIGIN,
            "crossOrigin": False,
        },
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "header": {
            "version": "Faying Protocol/1.0",
            "msg_type": "BOOTSTRAP",
            "issuer": "hp:test",
            "subject": "fay:test",
            "grade": 2,
        },
        "claims": {
            "fay": "fay:test",
            "human_prime": "hp:test",
            "grade": 2,
            "human_witness": {
                "credential_id": "test-credential",
                "client_data_json": client_data,
                "authenticator_data": b"\x00" * 37,
                "signature": b"\x00" * 64,
            },
            "scope": {"actions": ["calendar:event:read"], "domains": ["https://api.example.com"]},
        },
        "signature": {"alg": "Ed25519", "pubkey": b"\x00" * 32, "sig": b"\x00" * 64},
        "attestation": {"format": "self-signed", "payload": b"", "signer": "hp:test",
                        "signature": {"alg": "Ed25519", "pubkey": b"\x00" * 32, "sig": b"\x00" * 64}},
    }


def _synthetic_delegate_response() -> Dict[str, Any]:
    return {
        "header": {
            "version": "Faying Protocol/1.0",
            "msg_type": "DELEGATE_RESP",
            "issuer": "hp:test",
            "subject": "fay:child",
            "grade": 2,
        },
        "claims": {
            "id": "01H-TEST-CHILD",
            "parent": "01H-TEST-PARENT",
            "issuer": "hp:test",
            "subject": "fay:child",
            "grade": 2,
            "scope": {"actions": ["calendar:event:read"], "domains": ["https://api.example.com"]},
            "signature": {
                "alg": "Ed25519",
                "pubkey": b"\x00" * 32,
                "sig": b"\x00" * 64,
                "chain": [b"\x01" * 64],  # parent counter-sig
            },
        },
        "signature": {"alg": "Ed25519", "pubkey": b"\x00" * 32, "sig": b"\x00" * 64},
        "attestation": {"format": "self-signed", "payload": b"", "signer": "hp:test",
                        "signature": {"alg": "Ed25519", "pubkey": b"\x00" * 32, "sig": b"\x00" * 64}},
    }


# ---------------------------------------------------------------------------
# Helpers for mutating the WebAuthn clientDataJSON in place.
# ---------------------------------------------------------------------------
def _set_client_data(envelope: Dict[str, Any], **fields: Any) -> Dict[str, Any]:
    """Replace ``human_witness.client_data_json`` with the given fields.

    ``client_data_json`` may be stored as raw bytes (CBOR ``bstr``) or as
    a base64url string. Whatever we read in, we always re-encode as raw
    UTF-8 bytes — that's the wire-format the CDDL declares.
    """

    witness = envelope["claims"]["human_witness"]
    raw = witness.get("client_data_json")
    decoded: Dict[str, Any]
    if isinstance(raw, (bytes, bytearray)):
        try:
            decoded = json.loads(bytes(raw).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = {"type": "webauthn.get", "challenge": "x", "origin": EXPECTED_ORIGIN, "crossOrigin": False}
    elif isinstance(raw, str):
        try:
            decoded = json.loads(_b64url_decode(raw).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            decoded = {"type": "webauthn.get", "challenge": "x", "origin": EXPECTED_ORIGIN, "crossOrigin": False}
    else:
        decoded = {"type": "webauthn.get", "challenge": "x", "origin": EXPECTED_ORIGIN, "crossOrigin": False}
    decoded.update(fields)
    witness["client_data_json"] = json.dumps(decoded, separators=(",", ":")).encode("utf-8")
    return envelope


# ---------------------------------------------------------------------------
# Pytest fixtures.
# ---------------------------------------------------------------------------
@pytest.fixture
def bootstrap_envelope() -> Dict[str, Any]:
    env = _bootstrap_seed()
    if env is None:
        pytest.skip("no BOOTSTRAP seed available (cbor2 missing or vectors absent)")
    return env


@pytest.fixture
def delegate_envelope() -> Dict[str, Any]:
    env = _delegate_seed()
    if env is None:
        pytest.skip("no DELEGATE seed available (cbor2 missing or vectors absent)")
    return env


# ---------------------------------------------------------------------------
# 1. Cross-origin WebAuthn BOOTSTRAP — Requirement 9.3 sub-clauses 1 & 2.
# ---------------------------------------------------------------------------
class TestCrossOriginBootstrap:
    """Cross-origin WebAuthn assertions must fail BOOTSTRAP."""

    def test_baseline_positive_envelope_passes(self, bootstrap_envelope: Dict[str, Any]) -> None:
        # Sanity: the verifier accepts the canonical positive vector when
        # the expected origin matches the one baked into the vectors.
        verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)

    def test_cross_origin_url_rejected(self, bootstrap_envelope: Dict[str, Any]) -> None:
        _set_client_data(bootstrap_envelope, origin="https://attacker.example")
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_cross_origin_subdomain_rejected(self, bootstrap_envelope: Dict[str, Any]) -> None:
        # Subdomains are *not* the same WebAuthn origin; the spec relies on
        # exact match, which is also how WebAuthn user agents enforce it.
        _set_client_data(bootstrap_envelope, origin="https://evil.faying.example")
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_scheme_downgrade_rejected(self, bootstrap_envelope: Dict[str, Any]) -> None:
        # http:// vs https:// is a different WebAuthn origin.
        _set_client_data(bootstrap_envelope, origin="http://faying.example")
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_cross_origin_flag_rejected(self, bootstrap_envelope: Dict[str, Any]) -> None:
        # Even if origin matches, crossOrigin=true means the assertion was
        # produced from an embedded iframe — the WebAuthn binding the
        # protocol relies on no longer holds.
        _set_client_data(bootstrap_envelope, origin=EXPECTED_ORIGIN, crossOrigin=True)
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_missing_client_data_origin_rejected(self, bootstrap_envelope: Dict[str, Any]) -> None:
        witness = bootstrap_envelope["claims"]["human_witness"]
        # Strip the origin field entirely — corresponds to a hand-rolled
        # clientDataJSON the attacker forged without bothering to mirror the
        # WebAuthn schema.
        witness["client_data_json"] = json.dumps(
            {"type": "webauthn.get", "challenge": "x"}
        ).encode("utf-8")
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED


# ---------------------------------------------------------------------------
# 2. "Remote link + single consent button" path — Requirement 9.3 sub-clause 4.
# ---------------------------------------------------------------------------
class TestRemoteSingleConsentPath:
    """No protocol path may accept BOOTSTRAP from a remote-link single click."""

    def test_self_declared_remote_consent_rejected(
        self, bootstrap_envelope: Dict[str, Any]
    ) -> None:
        # An attacker may try to sneak in a "remote-link-single-click" flag,
        # hoping a permissive RP routes it through. The verifier must fail
        # closed regardless of whether the witness payload looks valid.
        bootstrap_envelope["claims"]["faying_initiation"] = "remote-link-single-click"
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_remote_consent_with_valid_origin_still_rejected(
        self, bootstrap_envelope: Dict[str, Any]
    ) -> None:
        # Origin is intact and crossOrigin is false — the verifier must
        # *still* reject because Requirement 9.3 sub-clause 4 forbids the
        # affordance entirely. This is the property the spec enshrines as
        # "not just absent, but inexpressible legally".
        _set_client_data(bootstrap_envelope, origin=EXPECTED_ORIGIN, crossOrigin=False)
        bootstrap_envelope["claims"]["faying_initiation"] = "remote-link-single-click"
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(bootstrap_envelope, EXPECTED_ORIGIN)
        assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED

    def test_no_legal_remote_consent_path_exists(
        self, bootstrap_envelope: Dict[str, Any]
    ) -> None:
        """Acceptance: there exists no legal accepting path for remote consent.

        Enumerate the salient envelope-level toggles a remote-consent UX
        might attempt to flip (skip witness, swap origin, mark crossOrigin)
        — every combination must be rejected when the remote-consent
        affordance is set.
        """

        toggles: list[Tuple[str, Dict[str, Any]]] = [
            ("origin-mismatch", {"origin": "https://attacker.example", "crossOrigin": False}),
            ("cross-origin-flag", {"origin": EXPECTED_ORIGIN, "crossOrigin": True}),
            ("origin-match", {"origin": EXPECTED_ORIGIN, "crossOrigin": False}),
        ]
        for label, fields in toggles:
            env = _bootstrap_seed() or _synthetic_bootstrap()
            _set_client_data(env, **fields)
            env["claims"]["faying_initiation"] = "remote-link-single-click"
            with pytest.raises(VerifierReject) as excinfo:
                verify_bootstrap(env, EXPECTED_ORIGIN)
            assert (excinfo.value.code, excinfo.value.name) == E_HUMAN_WITNESS_REQUIRED, (
                f"toggle {label!r} unexpectedly accepted"
            )


# ---------------------------------------------------------------------------
# 3. DELEGATE missing parent counter-signature — Requirement 9.3 sub-clause 3.
# ---------------------------------------------------------------------------
class TestDelegateMissingChain:
    """DELEGATE without parent Mandate counter-sig must fail with 1007."""

    def test_baseline_positive_chain_passes(self, delegate_envelope: Dict[str, Any]) -> None:
        # Sanity: the canonical pos-chain-verify vector verifies cleanly.
        verify_delegate(delegate_envelope)

    def test_chain_field_missing_rejected(self, delegate_envelope: Dict[str, Any]) -> None:
        delegate_envelope["claims"]["signature"].pop("chain", None)
        with pytest.raises(VerifierReject) as excinfo:
            verify_delegate(delegate_envelope)
        assert (excinfo.value.code, excinfo.value.name) == E_ATTESTATION_INVALID

    def test_chain_empty_array_rejected(self, delegate_envelope: Dict[str, Any]) -> None:
        delegate_envelope["claims"]["signature"]["chain"] = []
        with pytest.raises(VerifierReject) as excinfo:
            verify_delegate(delegate_envelope)
        assert (excinfo.value.code, excinfo.value.name) == E_ATTESTATION_INVALID

    def test_chain_entry_zero_length_rejected(
        self, delegate_envelope: Dict[str, Any]
    ) -> None:
        delegate_envelope["claims"]["signature"]["chain"] = [b""]
        with pytest.raises(VerifierReject) as excinfo:
            verify_delegate(delegate_envelope)
        assert (excinfo.value.code, excinfo.value.name) == E_ATTESTATION_INVALID

    def test_chain_entry_wrong_type_rejected(
        self, delegate_envelope: Dict[str, Any]
    ) -> None:
        # An attacker who controls the MS could attempt to slip a string
        # placeholder into the chain. The CDDL declares ``chain`` as
        # ``[+ bstr]``; non-bstr entries are rejected.
        delegate_envelope["claims"]["signature"]["chain"] = ["not-bytes"]
        with pytest.raises(VerifierReject) as excinfo:
            verify_delegate(delegate_envelope)
        assert (excinfo.value.code, excinfo.value.name) == E_ATTESTATION_INVALID


# ---------------------------------------------------------------------------
# Property-based coverage (Hypothesis): random origins & chain shapes.
# ---------------------------------------------------------------------------
@pytest.mark.skipif(not _HAS_HYPOTHESIS, reason="hypothesis not installed")
class TestPropertyBased:
    """Random-input fuzzing of the three rejection paths."""

    @staticmethod
    def _origin_strategy() -> Any:  # pragma: no cover - trivial
        scheme = st.sampled_from(["http", "https"])
        host = st.text(
            alphabet="abcdefghijklmnopqrstuvwxyz.-",
            min_size=3,
            max_size=24,
        ).filter(lambda s: not s.startswith(".") and not s.endswith(".") and ".." not in s)
        return st.builds(lambda s, h: f"{s}://{h}", scheme, host)

    @given(origin=_origin_strategy.__func__())  # type: ignore[misc]
    @settings(max_examples=50, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_any_non_matching_origin_is_rejected(self, origin: str) -> None:
        if origin == EXPECTED_ORIGIN:
            return  # tautologically not the cross-origin case
        env = _bootstrap_seed() or _synthetic_bootstrap()
        _set_client_data(env, origin=origin, crossOrigin=False)
        with pytest.raises(VerifierReject) as excinfo:
            verify_bootstrap(env, EXPECTED_ORIGIN)
        assert excinfo.value.code == E_HUMAN_WITNESS_REQUIRED[0]

    @given(cross=st.booleans())
    @settings(max_examples=20, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cross_origin_flag_only_accepts_when_false(self, cross: bool) -> None:
        env = _bootstrap_seed() or _synthetic_bootstrap()
        _set_client_data(env, origin=EXPECTED_ORIGIN, crossOrigin=cross)
        if cross:
            with pytest.raises(VerifierReject):
                verify_bootstrap(env, EXPECTED_ORIGIN)
        else:
            verify_bootstrap(env, EXPECTED_ORIGIN)  # accepts

    @given(
        chain=st.one_of(
            st.just(None),
            st.just([]),
            st.lists(st.binary(min_size=0, max_size=0), min_size=1, max_size=3),
            st.lists(st.text(min_size=1, max_size=4), min_size=1, max_size=3),
        )
    )
    @settings(max_examples=30, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_invalid_chain_shapes_rejected(self, chain: Any) -> None:
        env = _delegate_seed() or _synthetic_delegate_response()
        if chain is None:
            env["claims"]["signature"].pop("chain", None)
        else:
            env["claims"]["signature"]["chain"] = chain
        with pytest.raises(VerifierReject) as excinfo:
            verify_delegate(env)
        assert excinfo.value.code == E_ATTESTATION_INVALID[0]
