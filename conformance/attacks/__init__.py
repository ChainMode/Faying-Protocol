"""Conformance attack-simulation suite (task 6.x).

Each module here encodes one adversary path described in
``design.md §9`` / ``requirements.md §9.x``. Tests embed a small
*reference verifier* that codifies the protocol's expected reaction;
the verifier is intentionally local to each module so that adding a
new threat does not entangle existing ones.

Not Normative — see ``conformance/README.md``.
"""
