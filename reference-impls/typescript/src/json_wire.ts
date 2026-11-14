// Reference Implementation, Not Normative — for conformance testing only.
//
// JSON wire-form ⟷ value-model conversion for the Faying Protocol/1.0
// `application/faying-protocol+json` fallback encoding (design.md §5.1).
//
// JSON has no native bytes or CBOR-tag type, so the corpus uses explicit
// markers. This module lifts those markers into the same value model
// (Uint8Array / Tag0 / Map) the deterministic-CBOR codec uses, so a JSON
// message and its CBOR sibling collapse to byte-identical Det-CBOR signing
// input — the core of Requirement 10.1 / 10.2 equivalence.
//
// Recognised JSON conventions (mirrors conformance/dim_encoding/normalize.py):
//   * binary markers: {"$bytes": b64u|hex}, {"$b64u": ...}, {"$b64": ...}
//   * tag-0 markers:  {"$tag": 0, "$value": str} or {"$tag": 0, "value": str}
//   * path-keyed bare-string binary fields (encoding-equivalence vectors),
//     supplied via `binaryPaths`.

import { Tag0, type CborValue } from "./detcbor.ts";

function b64uDecode(s: string): Uint8Array {
  return new Uint8Array(Buffer.from(s, "base64url"));
}

function b64Decode(s: string): Uint8Array {
  return new Uint8Array(Buffer.from(s, "base64"));
}

const HEX_RE = /^[0-9a-fA-F]*$/;

function decodeBytesMarker(marker: string, value: string): Uint8Array {
  if (marker === "$bytes") {
    if (HEX_RE.test(value) && value.length % 2 === 0 && value.length >= 2) {
      return new Uint8Array(Buffer.from(value, "hex"));
    }
    return b64uDecode(value);
  }
  if (marker === "$b64u") return b64uDecode(value);
  if (marker === "$b64") return b64Decode(value);
  throw new Error(`unknown binary marker ${marker}`);
}

function detectBinaryMarker(node: Record<string, unknown>): string | null {
  const keys = Object.keys(node);
  if (keys.length !== 1) return null;
  const k = keys[0];
  return k === "$bytes" || k === "$b64u" || k === "$b64" ? k : null;
}

function tag0Marker(node: Record<string, unknown>): string | null {
  const keys = new Set(Object.keys(node));
  if (keys.size === 2 && keys.has("$tag") && node["$tag"] === 0) {
    if (keys.has("$value") && typeof node["$value"] === "string") return node["$value"] as string;
    if (keys.has("value") && typeof node["value"] === "string") return node["value"] as string;
  }
  return null;
}

/** Convert a parsed JSON tree into the CBOR value model. */
export function jsonToValueModel(obj: unknown, binaryPaths: string[] = []): CborValue {
  const pathSet = new Set(binaryPaths);
  return walk(obj, [], pathSet);
}

function walk(obj: unknown, path: string[], binaryPaths: Set<string>): CborValue {
  if (obj === null) return null;
  if (typeof obj === "boolean") return obj;
  if (typeof obj === "number") return obj;
  if (typeof obj === "string") {
    if (binaryPaths.has(path.join("."))) return b64uDecode(obj);
    return obj;
  }
  if (Array.isArray(obj)) {
    return obj.map((v) => walk(v, path, binaryPaths));
  }
  if (typeof obj === "object") {
    const rec = obj as Record<string, unknown>;
    const marker = detectBinaryMarker(rec);
    if (marker !== null) {
      const inner = rec[marker];
      if (typeof inner !== "string") throw new Error(`binary marker ${marker} expects string`);
      return decodeBytesMarker(marker, inner);
    }
    const ts = tag0Marker(rec);
    if (ts !== null) return new Tag0(ts);
    const m = new Map<string, CborValue>();
    for (const [k, v] of Object.entries(rec)) {
      m.set(k, walk(v, [...path, k], binaryPaths));
    }
    return m;
  }
  throw new Error(`json_wire: cannot convert ${typeof obj}`);
}

/** Serialize a value model into JSON wire form (markers for bytes / tag-0). */
export function valueModelToJson(value: CborValue): unknown {
  if (value instanceof Uint8Array) {
    return { $bytes: Buffer.from(value).toString("base64url") };
  }
  if (value instanceof Tag0) {
    return { $tag: 0, $value: value.value };
  }
  if (Array.isArray(value)) return value.map(valueModelToJson);
  if (value instanceof Map) {
    const out: Record<string, unknown> = {};
    for (const [k, v] of value) out[k] = valueModelToJson(v);
    return out;
  }
  return value;
}
