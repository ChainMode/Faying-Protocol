// Reference Implementation, Not Normative — for conformance testing only.
//
// Hash agility for the §6.3 signing-input expression. Both algorithms emit
// 32-byte digests; only the wrapper changes, the input bytes do not
// (design.md §6.1 / §6.3). Mirrors conformance/dim_hash/algorithms.py.

import crypto from "node:crypto";
import { blake3 } from "@noble/hashes/blake3";

export type Hash = "SHA-256" | "BLAKE3";

export const SUPPORTED_HASHES: readonly Hash[] = ["SHA-256", "BLAKE3"];

export function normalizeHash(name: string): Hash {
  switch (name) {
    case "SHA-256":
    case "sha-256":
    case "sha256":
    case "SHA256":
      return "SHA-256";
    case "BLAKE3":
    case "blake3":
    case "Blake3":
      return "BLAKE3";
    default:
      throw new Error(`unsupported hash algorithm: ${name}`);
  }
}

export function computeHash(alg: Hash, data: Uint8Array): Uint8Array {
  const a = normalizeHash(alg);
  let digest: Uint8Array;
  if (a === "SHA-256") {
    digest = new Uint8Array(crypto.createHash("sha256").update(data).digest());
  } else {
    digest = blake3(data);
  }
  if (digest.length !== 32) {
    throw new Error(`${a} produced ${digest.length}-byte digest; protocol fixes 32 bytes`);
  }
  return digest;
}

export function hashHex(alg: Hash, data: Uint8Array): string {
  return Buffer.from(computeHash(alg, data)).toString("hex");
}
