// Reference Implementation, Not Normative — for conformance testing only.
//
// Discovery + loading of the official `vectors/` corpus (tasks 3.x). Both the
// TypeScript and Rust reference impls consume the SAME authoritative vectors
// and `schemas/fap-1.0.cddl` as shared inputs (per task 5.6 conventions); we
// never re-define protocol data here.
//
// The loader returns each signed envelope as a value model (Map / Uint8Array
// / Tag0) ready for signing-input computation and signature verification.

import { readFileSync, readdirSync, existsSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";
import { decodeCbor } from "./protocol.ts";
import { jsonToValueModel } from "./json_wire.ts";
import type { CborValue } from "./detcbor.ts";

const HERE = path.dirname(fileURLToPath(import.meta.url));
/** Repo root = reference-impls/typescript/src → ../../.. */
export const REPO_ROOT = path.resolve(HERE, "..", "..", "..");
export const VECTORS_DIR = path.join(REPO_ROOT, "vectors");
export const SCHEMAS_DIR = path.join(REPO_ROOT, "schemas");

// Priority-ordered envelope basenames (mirrors dim_hash/signing_input.py).
const ENVELOPE_BASENAMES = [
  "request",
  "disclosure",
  "faying-request",
  "faying_request",
  "envelope",
  "presence",
  "grade-switch",
  "grade_switch",
  "delegate",
  "revoke",
  "error",
  "response",
  "signal",
  "mandate",
  "message",
  "trigger",
];

export interface LoadedVector {
  category: string;
  caseName: string;
  dir: string;
  envelopeFile: string;
  encoding: "cbor" | "json";
  /** The decoded signed envelope value model. */
  envelope: CborValue;
  expected: Record<string, unknown>;
}

function findEnvelopeFile(dir: string): { file: string; encoding: "cbor" | "json" } | null {
  for (const base of ENVELOPE_BASENAMES) {
    const cbor = path.join(dir, `${base}.cbor`);
    if (existsSync(cbor)) return { file: cbor, encoding: "cbor" };
    const json = path.join(dir, `${base}.json`);
    if (existsSync(json)) return { file: json, encoding: "json" };
  }
  return null;
}

function readExpected(dir: string): Record<string, unknown> {
  const p = path.join(dir, "expected.json");
  if (!existsSync(p)) return {};
  try {
    return JSON.parse(readFileSync(p, "utf8"));
  } catch {
    return {};
  }
}

function binaryPathsFromExpected(expected: Record<string, unknown>): string[] {
  const paths = expected["binary_field_paths"];
  if (Array.isArray(paths)) return paths.filter((p) => typeof p === "string") as string[];
  return [];
}

function loadEnvelope(
  file: string,
  encoding: "cbor" | "json",
  expected: Record<string, unknown>,
): CborValue {
  if (encoding === "cbor") {
    return decodeCbor(new Uint8Array(readFileSync(file)));
  }
  const raw = JSON.parse(readFileSync(file, "utf8"));
  // encoding-equivalence vectors wrap nothing; bootstrap JSON vectors are
  // the full envelope at top-level. Use binary_field_paths when present.
  return jsonToValueModel(raw, binaryPathsFromExpected(expected));
}

/** Load every vector directory under `vectors/`. */
export function loadAllVectors(categories?: string[]): LoadedVector[] {
  const out: LoadedVector[] = [];
  const cats = readdirSync(VECTORS_DIR).filter((c) => {
    if (c.startsWith(".") || c.startsWith("_")) return false;
    return statSync(path.join(VECTORS_DIR, c)).isDirectory();
  });
  for (const category of cats.sort()) {
    if (categories && !categories.includes(category)) continue;
    const catDir = path.join(VECTORS_DIR, category);
    for (const entry of readdirSync(catDir).sort()) {
      if (entry.startsWith(".") || entry.startsWith("_")) continue;
      const dir = path.join(catDir, entry);
      if (!statSync(dir).isDirectory()) continue;
      if (!existsSync(path.join(dir, "expected.json"))) continue;
      const found = findEnvelopeFile(dir);
      if (!found) continue;
      const expected = readExpected(dir);
      let envelope: CborValue;
      try {
        envelope = loadEnvelope(found.file, found.encoding, expected);
      } catch {
        continue; // unparseable / non-envelope artefacts are skipped
      }
      out.push({
        category,
        caseName: entry,
        dir,
        envelopeFile: found.file,
        encoding: found.encoding,
        envelope,
        expected,
      });
    }
  }
  return out;
}
