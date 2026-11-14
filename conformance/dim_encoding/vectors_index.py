"""Vector discovery — pair every CBOR file with its JSON sibling.

A *pair* is a single logical message that ships in both wire forms. Each task
3.x deliverable lays out its vectors in one of two shapes:

  * **Side-by-side**: ``request.cbor`` + ``request.json`` next to each other
    (every group except disconnection).
  * **Single envelope wrapper**: the JSON file wraps the same payload under a
    top-level ``"mandate": {...}`` key (endorsement). The driver unwraps that
    so the comparison happens at the same nesting level.

Disconnection vectors don't ship a CBOR/JSON pair (only ``timeline.json`` and
``expected.json``); they are *out of scope* for this dimension because there
is nothing to switch between. Their inclusion in the matrix at axis level is
covered by other dimensions (signing / hash / channel).

Reference / Not Normative.
"""

from __future__ import annotations

import dataclasses as _dc
import json
import os
from pathlib import Path
from typing import Any, Iterator

# Repository root resolution. ``conformance/dim_encoding/vectors_index.py``
# lives three levels deep; ``vectors/`` sits at the root.
_HERE = Path(__file__).resolve().parent
REPO_ROOT = _HERE.parent.parent
VECTORS_ROOT = REPO_ROOT / "vectors"


# ---------------------------------------------------------------------------
# Naming pairs
# ---------------------------------------------------------------------------

# Each tuple is ``(cbor_filename, json_filename, json_wrapper_key_or_None)``.
# ``json_wrapper_key`` lets us peel off the ``{"mandate": {...}}`` envelope
# that endorsement vectors use. Only keys that the JSON wraps but the CBOR
# does not should be listed here.
_PAIRS_BY_GROUP: dict[str, tuple[tuple[str, str, str | None], ...]] = {
    "bootstrap": (
        ("request.cbor", "request.json", None),
        ("response.cbor", "response.json", None),
    ),
    "delegate": (
        ("request.cbor", "request.json", None),
        ("response.cbor", "response.json", None),
    ),
    "grade-switch": (
        ("request.cbor", "request.json", None),
        ("response.cbor", "response.json", None),
    ),
    "revoke": (
        ("request.cbor", "request.json", None),
        ("response.cbor", "response.json", None),
    ),
    "presence": (
        ("signal.cbor", "signal.json", None),
    ),
    "errors": (
        ("trigger.cbor", "trigger.json", None),
        ("error.cbor", "error.json", None),
    ),
    "encoding-equivalence": (
        ("message.cbor", "message.json", None),
    ),
    "endorsement": (
        ("mandate.cbor", "mandate.json", "mandate"),
    ),
    "faying-request": (
        ("request.cbor", "request.json", None),
        ("response.cbor", "response.json", None),
        ("bootstrap-followup.cbor", "bootstrap-followup.json", None),
        ("error.cbor", "error.json", None),
    ),
    "disclosure": (
        ("disclosure.cbor", "disclosure.json", None),
    ),
}

# disconnection is intentionally absent — see module docstring.


# ---------------------------------------------------------------------------
# Pair record
# ---------------------------------------------------------------------------


@_dc.dataclass(frozen=True)
class EncodingPair:
    """One CBOR ↔ JSON sibling pair from the vector corpus.

    A *pair* may be one-sided. When ``cbor_path`` exists but ``json_path``
    does not (or vice versa), the driver still parses the available side,
    validates its signature where possible, and asserts media-type
    expectations — but cannot exercise the cross-encoding invariants
    (I-E-2/3/4/5). One-sided cases are deliberate in the bootstrap corpus,
    where ``pos-cbor-*`` and ``pos-json-*`` ship as separate directories.
    """

    group: str
    """Top-level vector category (``bootstrap``, ``delegate``, ...)."""

    case: str
    """Case directory name within the group (``pos-cbor-ed25519``, ...)."""

    role: str
    """Logical role of this message inside its case (``request``,
    ``response``, ``signal``, ``mandate``, ``trigger``, ``error``,
    ``message``, ``disclosure``, ``bootstrap-followup``)."""

    cbor_path: Path
    """May not exist on disk; check ``has_cbor`` first."""

    json_path: Path
    """May not exist on disk; check ``has_json`` first."""

    json_wrapper_key: str | None
    """If non-``None``, the CBOR-equivalent payload sits at ``json[key]``."""

    @property
    def has_cbor(self) -> bool:
        return self.cbor_path.is_file()

    @property
    def has_json(self) -> bool:
        return self.json_path.is_file()

    @property
    def is_two_sided(self) -> bool:
        return self.has_cbor and self.has_json

    @property
    def vector_id(self) -> str:
        """Stable, dotted identifier for log lines and audit records."""
        return f"{self.group}/{self.case}/{self.role}"

    def relative(self, root: Path = VECTORS_ROOT) -> str:
        """Repo-relative directory of the pair, for friendlier diagnostics."""
        case_dir = (
            self.cbor_path.parent if self.has_cbor else self.json_path.parent
        )
        try:
            return str(case_dir.relative_to(root.parent))
        except ValueError:
            return str(case_dir)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def _role_from_filename(fname: str) -> str:
    return os.path.splitext(fname)[0]


def _iter_case_dirs(group_dir: Path) -> Iterator[Path]:
    """Yield each case directory inside a group, skipping ``_tools`` and
    files."""
    for child in sorted(group_dir.iterdir()):
        if not child.is_dir():
            continue
        if child.name.startswith("_") or child.name.startswith("."):
            continue
        yield child


# Bootstrap is unusual: ``pos-cbor-*`` and ``pos-json-*`` are *independent*
# vectors (different signer, different mandate ID), so we do not cross-pair
# them. The cross-encoding equivalence the requirements need is delivered
# by the ``encoding-equivalence`` group; each bootstrap directory exercises
# the *single-encoding* canonicality + signature-verification path on its
# own.
_CROSS_DIR_GROUPS: tuple[str, ...] = ()


def discover_pairs(*, vectors_root: Path = VECTORS_ROOT) -> list[EncodingPair]:
    """Return every CBOR or JSON file under ``vectors_root`` that participates
    in the encoding axis.

    The traversal order is stable (group → case → file role) so output
    ordering is reproducible across runs and across operating systems.

    Each known message role gets emitted **at most once** per case, even if
    only one wire form is present on disk. The driver then decides per-pair
    which invariants apply.

    Bootstrap is a special case: ``pos-cbor-*`` and ``pos-json-*`` cases
    are *independent vectors* (different mandate IDs, different signers),
    not two encodings of the same message — so they are emitted as
    one-sided pairs, not cross-paired. Each one still exercises the
    encoding's own canonicality / signature-verification path
    (Requirement 10.1.1, 10.2.1) at the per-pair level, while the
    cross-encoding equivalence (Requirement 10.1.3) is exercised by the
    ``encoding-equivalence`` group's two-sided pairs.
    """
    pairs: list[EncodingPair] = []

    # Defensive: ``vectors/`` must exist; this driver is meaningless without
    # task 3.x's deliverables.
    if not vectors_root.exists():
        raise FileNotFoundError(
            f"vectors directory not found at {vectors_root!r}; "
            "task 3.x must deliver test vectors before task 5.2 can run"
        )

    for group_name in sorted(_PAIRS_BY_GROUP.keys()):
        group_dir = vectors_root / group_name
        if not group_dir.is_dir():
            # Still allowed: the corpus may not yet ship every group on
            # every branch.
            continue
        recipe = _PAIRS_BY_GROUP[group_name]

        for case_dir in _iter_case_dirs(group_dir):
            for cbor_name, json_name, wrapper_key in recipe:
                cp = case_dir / cbor_name
                jp = case_dir / json_name
                if not cp.is_file() and not jp.is_file():
                    continue
                pairs.append(
                    EncodingPair(
                        group=group_name,
                        case=case_dir.name,
                        role=_role_from_filename(cbor_name),
                        cbor_path=cp,
                        json_path=jp,
                        json_wrapper_key=wrapper_key,
                    )
                )

    return pairs


# ---------------------------------------------------------------------------
# Expected-state hints (best-effort; never required)
# ---------------------------------------------------------------------------


def load_expected_signature_hashes(case_dir: Path) -> dict[str, str]:
    """Read ``expected.json`` and return any ``signing_input_sha256``-style
    digests it advertises.

    The corpus uses several spellings (``request_signing_input_sha256``,
    ``signature_input.hash_hex``, ``signing_input_sha256``); we collect them
    all under their canonical role names (``request`` / ``response`` /
    ``signal`` / ``mandate`` / ``message``).
    """
    expected = case_dir / "expected.json"
    if not expected.is_file():
        return {}
    try:
        data = json.loads(expected.read_text("utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    out: dict[str, str] = {}

    digests = data.get("digests")
    if isinstance(digests, dict):
        for k, v in digests.items():
            if not isinstance(v, str):
                continue
            for role in ("request", "response", "signal", "mandate", "message"):
                if k == f"{role}_signing_input_sha256":
                    out[role] = v
                elif k == "signing_input_sha256":
                    out.setdefault(role, v)

    sig_input = data.get("signature_input")
    if isinstance(sig_input, dict):
        h = sig_input.get("hash_hex")
        if isinstance(h, str):
            out.setdefault("message", h)

    return out
