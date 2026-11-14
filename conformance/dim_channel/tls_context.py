"""Synthetic TLS context for the channel-binding conformance dimension.

RFC 9266 (*Channel Bindings for TLS 1.3*) defines the binding type
``tls-exporter``: a 32-byte value derived from the TLS 1.3 exporter using::

    label   = "EXPORTER-Channel-Binding"
    context = empty
    length  = 32

A real interop test would obtain that value from the live TLS stack via
``SSL_export_keying_material`` (OpenSSL) or equivalent. For a hermetic
conformance test we derive a *deterministic* exporter value from a synthetic
``master_secret`` using HKDF-SHA256 with the same label. The output is
indistinguishable in shape (32-byte opaque token) and re-derives to the same
value across runs, which is what the dimensional acceptance gate requires.

This module is intentionally stdlib-only: it must be importable in any
contributor's environment without first installing ``pbt/`` extras.

References
----------
* `RFC 9266 — Channel Bindings for TLS 1.3 <https://www.rfc-editor.org/rfc/rfc9266>`_
* `RFC 5705 — Keying Material Exporters for TLS <https://www.rfc-editor.org/rfc/rfc5705>`_
* `RFC 5869 — HKDF <https://www.rfc-editor.org/rfc/rfc5869>`_
* design.md §9.3 (Anti-Hijack — Channel Binding)
* requirements.md §9.2.3 (mTLS MUST carry RFC 9266 TLS Exporter)
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

# RFC 9266 §3.1 fixes the label and length explicitly.
_RFC9266_LABEL = b"EXPORTER-Channel-Binding"
_EXPORTER_LENGTH = 32  # bytes


def _hkdf_extract(salt: bytes, ikm: bytes) -> bytes:
    """RFC 5869 §2.2."""

    if not salt:
        salt = b"\x00" * hashlib.sha256().digest_size
    return hmac.new(salt, ikm, hashlib.sha256).digest()


def _hkdf_expand(prk: bytes, info: bytes, length: int) -> bytes:
    """RFC 5869 §2.3."""

    hash_len = hashlib.sha256().digest_size
    n = (length + hash_len - 1) // hash_len
    if n > 255:
        raise ValueError("HKDF: requested length too large")
    okm = b""
    t = b""
    for i in range(1, n + 1):
        t = hmac.new(prk, t + info + bytes([i]), hashlib.sha256).digest()
        okm += t
    return okm[:length]


def _derive_exporter(master_secret: bytes) -> bytes:
    """Deterministically derive a 32-byte RFC 9266 exporter value.

    The derivation mimics the TLS 1.3 exporter (RFC 8446 §7.5) shape:
    HKDF-Expand(PRK, label, length). We collapse the two-stage derivation
    into a single Expand step keyed off ``master_secret``; the conformance
    gate only cares that:

    1. distinct connections produce distinct values (collision-resistant), and
    2. the same connection re-derives the same value across runs.
    """

    prk = _hkdf_extract(salt=b"faying-protocol/1.0/tls-exporter", ikm=master_secret)
    return _hkdf_expand(prk, info=_RFC9266_LABEL, length=_EXPORTER_LENGTH)


@dataclass(frozen=True)
class TLSContext:
    """A synthetic TLS connection context for conformance testing.

    Attributes:
        mode: ``"tls-only"`` or ``"mtls"``. Drives whether the RP-side
            validator demands an RFC 9266 exporter match.
        connection_id: stable identifier for this synthetic connection.
            Used to derive the exporter; must be unique per connection.
        client_authenticated: ``True`` only when ``mode == "mtls"`` and the
            client presented a valid certificate. The conformance suite
            ignores cert validity beyond this flag (the signing dimension —
            task 5.3 — owns crypto-level cert checks).
    """

    mode: str
    connection_id: str
    client_authenticated: bool = False

    def __post_init__(self) -> None:
        if self.mode not in ("tls-only", "mtls"):
            raise ValueError(
                f"TLSContext.mode must be 'tls-only' or 'mtls'; got {self.mode!r}"
            )
        if self.mode == "mtls" and not self.client_authenticated:
            # mTLS without client auth would be a misconfiguration, not a
            # protocol-layer concern. We refuse to construct such a context
            # so test scenarios cannot accidentally smuggle in an unauthed
            # mTLS session.
            raise ValueError(
                "TLSContext: mode='mtls' requires client_authenticated=True"
            )
        if self.mode == "tls-only" and self.client_authenticated:
            raise ValueError(
                "TLSContext: mode='tls-only' must have client_authenticated=False"
            )

    def exporter(self) -> bytes:
        """Return the RFC 9266 TLS Exporter value for this connection.

        The value is deterministically derived from :attr:`connection_id`
        so different test scenarios can assert "same channel ⇒ same
        exporter, different channel ⇒ different exporter" without standing
        up real TLS sessions.
        """

        master_secret = (
            f"faying-conformance/dim-channel/{self.mode}/{self.connection_id}"
        ).encode("utf-8")
        return _derive_exporter(master_secret)

    def requires_channel_binding(self) -> bool:
        """``True`` iff the RP-side validator must compare RFC 9266 binding."""

        return self.mode == "mtls"
