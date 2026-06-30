#!/usr/bin/env bash
# Validate every BOOTSTRAP_RESP-carried Mandate against the
# authoritative CDDL schema using the official Ruby `cddl` gem.
#
# This script is run from the repository root.
#
# Usage:   bash vectors/bootstrap/_tools/validate-with-cddl.sh
#
# Exits 0 when every positive vector's inner Mandate validates against
# `mandate-only.cddl` (a schema shim that re-orders schemas/fap-1.0.cddl
# so that `mandate` is the entry rule expected by `cddl validate`).
#
# Requires:
#   - the `cddl` gem installed (gem install cddl --user-install)
#   - the cddl binary on PATH (or located via $CDDL_BIN)

set -euo pipefail

CDDL_BIN="${CDDL_BIN:-$(command -v cddl || true)}"
if [[ -z "$CDDL_BIN" ]]; then
  for cand in \
    "$HOME/.gem/ruby/2.6.0/bin/cddl" \
    "$HOME/.gem/ruby/3.0.0/bin/cddl" \
    "$HOME/.gem/ruby/3.1.0/bin/cddl" \
    "$HOME/.gem/ruby/3.2.0/bin/cddl"; do
    if [[ -x "$cand" ]]; then CDDL_BIN="$cand"; break; fi
  done
fi
if [[ -z "$CDDL_BIN" ]]; then
  echo "cddl tool not found; install with: gem install cddl --user-install" >&2
  exit 2
fi

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SHIM="$ROOT/_tools/mandate-only.cddl"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

POSITIVES=(
  pos-cbor-ed25519
  pos-cbor-es256
  pos-cbor-ml-dsa-65
  pos-json-ed25519
  pos-json-es256
  pos-json-ml-dsa-65
)

for name in "${POSITIVES[@]}"; do
  out="$TMPDIR/${name}-mandate.cbor"
  python3 - "$ROOT/$name" "$out" <<'PY'
import sys, cbor2, json
from pathlib import Path
folder = Path(sys.argv[1])
out = Path(sys.argv[2])
# Load whichever encoding this vector uses; convert to canonical CBOR
# so the CDDL validator sees the wire-format object.
req = next(folder.glob("response.cbor"), None) or next(folder.glob("response.json"))
if req.suffix == ".cbor":
    env = cbor2.loads(req.read_bytes())
else:
    import base64
    raw = json.loads(req.read_text(encoding="utf-8"))
    def materialise(node):
        if isinstance(node, dict):
            if set(node.keys()) == {"$bytes"}:
                return base64.urlsafe_b64decode(node["$bytes"] + "==")
            if set(node.keys()) == {"$tag", "$value"} and node["$tag"] == 0:
                return cbor2.CBORTag(0, node["$value"])
            return {k: materialise(v) for k, v in node.items()}
        if isinstance(node, list):
            return [materialise(x) for x in node]
        return node
    env = materialise(raw)
mandate = env["claims"]
out.write_bytes(cbor2.dumps(mandate, canonical=True))
PY
  if "$CDDL_BIN" "$SHIM" validate "$out" >/dev/null 2>&1; then
    echo "  ok  $name (mandate validates against CDDL)"
  else
    echo "  FAIL  $name" >&2
    "$CDDL_BIN" "$SHIM" validate "$out" >&2 || true
    exit 1
  fi
done

echo
echo "All 6 positive Mandates validate against schemas/fap-1.0.cddl."
