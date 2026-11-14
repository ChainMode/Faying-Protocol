"""Faying Protocol/1.0 — Conformance dimension: channel (TLS-only / mTLS).

Task 5.5 deliverable. Implements the RFC 9266 TLS Exporter Channel Binding
check mandated by Requirement 9.2.3 (design.md §9.3).

The package is intentionally self-contained — it depends only on the Python
standard library and the existing ``conformance/runner.py`` matrix loader —
so it can be invoked from CI without first bootstrapping ``pbt/``'s
virtualenv. See :mod:`conformance.dim_channel.driver` for the CLI entry
point and :mod:`conformance.dim_channel.test_dim_channel` for the pytest
suite.
"""
