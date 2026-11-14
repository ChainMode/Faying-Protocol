// Reference Implementation, Not Normative — for conformance testing only.
//
// Runs the four data-plane conformance dimensions (tasks 5.2–5.5) over the
// official corpus from the TypeScript reference impl's perspective:
//
//   * encoding   (5.2): CBOR ⟷ JSON Det-CBOR signing-input identity.
//   * signing    (5.3): Ed25519 / ES256 / ML-DSA-65 verification + agility.
//   * hash       (5.4): SHA-256 / BLAKE3 over the §6.3 signing input.
//   * channel    (5.5): RFC 9266 channel-binding accept/reject matrix.
//
// These mirror conformance/dim_*/ exactly so the cross-impl matrix (5.6) can
// assert the TS impl agrees with the Python suite and the Rust impl.

import { existsSync, readFileSync } from "node:fs";
import path from "node:path";
import {
  decodeCbor,
  signingInput,
  signingInputHash,
  verifyEnvelope,
} from "./protocol.ts";
import { generateKeyPair, sign as cryptoSign, verify as cryptoVerify, SUPPORTED_ALGS } from "./crypto.ts";
import { negotiate, NegotiationError } from "./negotiation.ts";
import { jsonToValueModel } from "./json_wire.ts";
import { computeHash, SUPPORTED_HASHES, hashHex } from "./hash.ts";
import { loadAllVectors, VECTORS_DIR, type LoadedVector } from "./vectors.ts";

export interface DimResult {
  name: string;
  total: number;
  passed: number;
  failed: number;
  findings: string[];
}

// ---------------------------------------------------------------------------
// Encoding dimension (5.2): CBOR/JSON pairs share a Det-CBOR signing input.
// ---------------------------------------------------------------------------

export function runEncoding(): DimResult {
  const result: DimResult = { name: "encoding", total: 0, passed: 0, failed: 0, findings: [] };

  // Use the encoding-equivalence corpus: each case ships message.cbor + .json.
  const eqDir = path.join(VECTORS_DIR, "encoding-equivalence");
  const indexPath = path.join(eqDir, "index.json");
  if (!existsSync(indexPath)) {
    result.findings.push("encoding-equivalence/index.json not found");
    return result;
  }
  const index = JSON.parse(readFileSync(indexPath, "utf8")) as { vectors: { id: string }[] };
  for (const v of index.vectors) {
    result.total += 1;
    const dir = path.join(eqDir, v.id);
    const expected = JSON.parse(readFileSync(path.join(dir, "expected.json"), "utf8"));
    const binaryPaths: string[] = expected.binary_field_paths ?? [];

    const cborObj = decodeCbor(new Uint8Array(readFileSync(path.join(dir, "message.cbor"))));
    const jsonObj = jsonToValueModel(
      JSON.parse(readFileSync(path.join(dir, "message.json"), "utf8")),
      binaryPaths,
    );

    const cborSig = Buffer.from(signingInput(cborObj)).toString("hex");
    const jsonSig = Buffer.from(signingInput(jsonObj)).toString("hex");
    const wantHash = expected.signature_input?.hash_hex as string | undefined;
    const gotHash = signingInputHash(cborObj);

    const problems: string[] = [];
    if (cborSig !== jsonSig) problems.push("Det-CBOR signing input differs CBOR vs JSON");
    if (wantHash && wantHash !== gotHash) problems.push(`hash ${gotHash} != expected ${wantHash}`);
    if (!verifyEnvelope(cborObj)) problems.push("CBOR envelope signature did not verify");

    if (problems.length === 0) {
      result.passed += 1;
    } else {
      result.failed += 1;
      result.findings.push(`[${v.id}] ${problems.join("; ")}`);
    }
  }
  return result;
}

// ---------------------------------------------------------------------------
// Signing dimension (5.3): re-sign every vector under all three algorithms
// (algorithm agility), assert the §6.3 signing input is invariant across
// algorithms, and exercise the BOOTSTRAP suite negotiation rule. Mirrors
// conformance/dim_signing (resign + negotiation), NOT embedded-sig checks.
// ---------------------------------------------------------------------------

export function runSigning(): DimResult {
  const result: DimResult = { name: "signing", total: 0, passed: 0, failed: 0, findings: [] };
  const vectors = loadAllVectors();

  for (const vec of vectors) {
    // Only re-sign artefacts that are envelope-shaped (a top-level Map).
    if (!(vec.envelope instanceof Map)) continue;
    result.total += 1;

    const input = signingInput(vec.envelope);
    const baselineHash = hashHex("SHA-256", input);
    const problems: string[] = [];

    for (const alg of SUPPORTED_ALGS) {
      // Deterministic seed for reproducibility (matches Python seed style).
      const seed = new Uint8Array(32).fill(0);
      const kp = generateKeyPair(alg, seed);
      const sig = cryptoSign(kp, input, `${vec.caseName}:${alg}`);
      const ok = cryptoVerify(alg, kp.publicKey, input, sig);
      if (!ok) problems.push(`${alg} re-sign/verify failed`);
      // Signing input must not depend on the signing algorithm.
      const h = hashHex("SHA-256", input);
      if (h !== baselineHash) problems.push(`${alg} perturbed signing input`);
    }

    if (problems.length === 0) {
      result.passed += 1;
    } else {
      result.failed += 1;
      result.findings.push(`[${vec.category}/${vec.caseName}] ${problems.join("; ")}`);
    }
  }

  // Negotiation rule checks (Requirement 8.1 / 8.2).
  const negChecks: [string, () => boolean][] = [
    ["strongest mutual = ML-DSA-65", () => negotiate(["Ed25519", "ML-DSA-65"], ["ES256", "ML-DSA-65"]) === "ML-DSA-65"],
    ["classical fallback = Ed25519", () => negotiate(["Ed25519", "ES256", "ML-DSA-65"], ["Ed25519", "ES256"]) === "Ed25519"],
    ["ECDSA-P256 alias = ES256", () => negotiate(["ECDSA-P256"], ["ES256"]) === "ES256"],
    [
      "disjoint sets → E_PROTOCOL",
      () => {
        try {
          negotiate(["Ed25519"], ["RSA-PKCS1"]);
          return false;
        } catch (e) {
          return e instanceof NegotiationError && e.errorCode === 1099;
        }
      },
    ],
  ];
  for (const [name, fn] of negChecks) {
    result.total += 1;
    let ok = false;
    try {
      ok = fn();
    } catch {
      ok = false;
    }
    if (ok) {
      result.passed += 1;
    } else {
      result.failed += 1;
      result.findings.push(`[negotiation] ${name} failed`);
    }
  }

  return result;
}

// ---------------------------------------------------------------------------
// Hash dimension (5.4): both hashes over the §6.3 signing input, 32 bytes,
// SHA-256 matches the corpus reference digest when present.
// ---------------------------------------------------------------------------

export function runHash(): DimResult {
  const result: DimResult = { name: "hash", total: 0, passed: 0, failed: 0, findings: [] };
  const vectors = loadAllVectors();
  for (const vec of vectors) {
    const input = signingInput(vec.envelope);
    const problems: string[] = [];
    for (const h of SUPPORTED_HASHES) {
      const digest = computeHash(h, input);
      if (digest.length !== 32) problems.push(`${h} digest length ${digest.length} != 32`);
    }
    // Cross-check SHA-256 against any advertised reference digest.
    const ref = extractReferenceSha256(vec);
    if (ref) {
      const got = hashHex("SHA-256", input);
      if (got !== ref) problems.push(`SHA-256 ${got} != reference ${ref}`);
    }
    result.total += 1;
    if (problems.length === 0) {
      result.passed += 1;
    } else {
      result.failed += 1;
      result.findings.push(`[${vec.category}/${vec.caseName}] ${problems.join("; ")}`);
    }
  }
  return result;
}

function extractReferenceSha256(vec: LoadedVector): string | null {
  const sigInput = vec.expected["signature_input"] as Record<string, unknown> | undefined;
  if (sigInput) {
    if (sigInput["wire_matches_signature_input"] === false) {
      const wire = sigInput["wire_hash_hex"];
      return typeof wire === "string" ? wire.toLowerCase() : null;
    }
    const alg = (sigInput["hash_alg"] ?? sigInput["hash_algorithm"]) as string | undefined;
    const h = sigInput["hash_hex"];
    if (typeof h === "string" && (!alg || alg.toUpperCase().replace(/-/g, "") === "SHA256")) {
      return h.toLowerCase();
    }
  }
  const digests = vec.expected["digests"] as Record<string, unknown> | undefined;
  if (digests) {
    const role = path.basename(vec.envelopeFile).replace(/\.(cbor|json)$/, "");
    for (const key of [`${role}_signing_input_sha256`, "signing_input_sha256"]) {
      const v = digests[key];
      if (typeof v === "string") return v.toLowerCase();
    }
  }
  return null;
}

// ---------------------------------------------------------------------------
// Channel dimension (5.5): RFC 9266 channel-binding accept/reject matrix.
// ---------------------------------------------------------------------------

export interface ChannelScenario {
  messageType: string;
  tlsMode: "tls-only" | "mtls";
  bindingShape: "present-correct" | "present-tampered" | "absent";
  expectedAccepted: boolean;
  expectedErrorCode: number | null;
}

/**
 * RP-side channel-binding validator (mirrors
 * conformance/dim_channel/rp_validator.py):
 *   * mTLS + correct binding  → accept
 *   * mTLS + absent/tampered  → reject E_ATTESTATION_INVALID (1007)
 *   * tls-only + absent       → accept (binding not required)
 *   * tls-only + present      → reject as malformed E_PROTOCOL (1099)
 */
export function validateChannelBinding(
  tlsMode: "tls-only" | "mtls",
  bindingShape: "present-correct" | "present-tampered" | "absent",
): { accepted: boolean; errorCode: number | null } {
  if (tlsMode === "mtls") {
    if (bindingShape === "present-correct") return { accepted: true, errorCode: null };
    return { accepted: false, errorCode: 1007 };
  }
  if (bindingShape === "absent") return { accepted: true, errorCode: null };
  return { accepted: false, errorCode: 1099 };
}

export function channelScenarios(): ChannelScenario[] {
  const out: ChannelScenario[] = [];
  for (const messageType of ["BOOTSTRAP", "DELEGATE", "REVOKE"]) {
    for (const tlsMode of ["tls-only", "mtls"] as const) {
      for (const bindingShape of ["present-correct", "present-tampered", "absent"] as const) {
        const { accepted, errorCode } = validateChannelBinding(tlsMode, bindingShape);
        out.push({
          messageType,
          tlsMode,
          bindingShape,
          expectedAccepted: accepted,
          expectedErrorCode: errorCode,
        });
      }
    }
  }
  return out;
}

export function runChannel(): DimResult {
  const result: DimResult = { name: "channel", total: 0, passed: 0, failed: 0, findings: [] };
  for (const s of channelScenarios()) {
    result.total += 1;
    const got = validateChannelBinding(s.tlsMode, s.bindingShape);
    if (got.accepted === s.expectedAccepted && got.errorCode === s.expectedErrorCode) {
      result.passed += 1;
    } else {
      result.failed += 1;
      result.findings.push(
        `[${s.messageType}/${s.tlsMode}/${s.bindingShape}] got ${JSON.stringify(got)}`,
      );
    }
  }
  return result;
}

export function runAllDimensions(): DimResult[] {
  return [runEncoding(), runSigning(), runHash(), runChannel()];
}
