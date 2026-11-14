#!/usr/bin/env bash
# Reference Implementation harness, Not Normative — for conformance testing only.
#
# Faying Protocol/1.0 — Cross-implementation conformance matrix (task 5.6).
#
# Runs the full TS↔Rust interop demonstration:
#   1. Each reference impl runs the complete 5.2–5.5 dimension matrix over the
#      shared official `vectors/` corpus.
#   2. TS produces interop messages (CBOR + JSON, all algorithms) → Rust verifies.
#   3. Rust produces interop messages (CBOR + JSON, all algorithms) → TS verifies.
#
# A non-zero exit means at least one cross-impl case failed; see results.md for
# how to localise a failure to a specific vector or schema and file an Issue to
# the protocol committee.
#
# Prereqs:
#   * Node.js >= 22.6.0 (runs TypeScript directly; no build step)
#   * A Rust toolchain (cargo). If cargo is not on PATH, set CARGO=~/.cargo/bin/cargo.
#
# Usage:
#   conformance/cross-impl/run_cross_impl.sh

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$HERE/../.." && pwd)"
TS_DIR="$REPO_ROOT/reference-impls/typescript"
RUST_DIR="$REPO_ROOT/reference-impls/rust"
INTEROP_DIR="$HERE/_interop"
CARGO="${CARGO:-cargo}"

echo "=== Faying Protocol/1.0 cross-impl matrix (task 5.6) ==="
echo

echo "--- [1/5] TypeScript dependency install ---"
( cd "$TS_DIR" && npm install --no-audit --no-fund >/dev/null 2>&1 && echo "ok" )

echo "--- [2/5] TypeScript dimension matrix (5.2–5.5) ---"
( cd "$TS_DIR" && node src/cli.ts dims )

echo
echo "--- [3/5] Rust dimension matrix (5.2–5.5) ---"
( cd "$RUST_DIR" && "$CARGO" run --quiet -- dims )

echo
echo "--- [4/5] TS produces → Rust verifies ---"
( cd "$TS_DIR" && node src/cli.ts produce "$INTEROP_DIR/ts" )
( cd "$RUST_DIR" && "$CARGO" run --quiet -- verify "$INTEROP_DIR/ts" )

echo
echo "--- [5/5] Rust produces → TS verifies ---"
( cd "$RUST_DIR" && "$CARGO" run --quiet -- produce "$INTEROP_DIR/rust" )
( cd "$TS_DIR" && node src/cli.ts verify "$INTEROP_DIR/rust" )

echo
echo "=== cross-impl matrix complete: 100% PASS ==="
