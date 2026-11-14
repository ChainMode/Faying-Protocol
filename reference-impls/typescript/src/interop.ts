// Reference Implementation, Not Normative — for conformance testing only.
//
// Cross-implementation interop: the TS impl PRODUCES protocol messages that
// the Rust impl must parse + verify, and VERIFIES messages the Rust impl
// produced. Both directions exercise the full 5.2–5.5 dimension space:
//
//   * encoding   : each message is emitted in BOTH CBOR and JSON.
//   * signing    : messages span Ed25519 / ES256 / ML-DSA-65.
//   * hash       : the SHA-256 and BLAKE3 of the §6.3 signing input are
//                  recorded in the manifest so the peer cross-checks them.
//   * channel    : each message declares a tls mode + channel-binding shape.
//
// Wire layout of an interop bundle (directory):
//
//   <out>/manifest.json                 ← index of all produced messages
//   <out>/<id>.cbor                     ← canonical CBOR wire form
//   <out>/<id>.json                     ← JSON fallback wire form
//
// The manifest records, per message, the producer, msg_type, alg, encoding,
// tls_mode, the signing-input SHA-256 + BLAKE3, and the expected verification
// outcome. The peer impl loads the manifest, re-derives the signing input
// from the wire bytes, re-verifies the signature, and recomputes both hashes,
// asserting they match the manifest. This is the byte-level contract that
// makes "TS-produced verified by Rust and vice versa" checkable.

import { mkdirSync, writeFileSync, readFileSync, existsSync } from "node:fs";
import path from "node:path";
import {
  buildEnvelope,
  buildScope,
  buildPresenceReq,
  buildAttestation,
  signEnvelope,
  encodeCbor,
  decodeCbor,
  signingInput,
  verifyEnvelope,
  readSignatureBundle,
  type Envelope,
  type HeaderInput,
} from "./protocol.ts";
import { generateKeyPair, verify as cryptoVerify, type Alg } from "./crypto.ts";
import { Tag0, type CborValue } from "./detcbor.ts";
import { valueModelToJson, jsonToValueModel } from "./json_wire.ts";
import { hashHex } from "./hash.ts";

const PRODUCER_TS = "typescript";

export interface InteropMessage {
  id: string;
  producer: string;
  msgType: string;
  alg: Alg;
  encoding: "cbor" | "json";
  tlsMode: "tls-only" | "mtls";
  bindingShape: "present-correct" | "absent";
  signingInputSha256: string;
  signingInputBlake3: string;
  expectedVerify: boolean;
}

export interface InteropManifest {
  spec: string;
  producer: string;
  note: string;
  messages: InteropMessage[];
}

interface MessagePlan {
  id: string;
  msgType: string;
  alg: Alg;
  tlsMode: "tls-only" | "mtls";
  buildClaims: () => Map<string, CborValue>;
}

const ISSUED_AT = "2026-02-01T00:00:00Z";
const EXPIRY = "2026-02-01T00:01:00Z";
const NOT_AFTER = "2026-02-01T23:59:59Z";

function nonceFor(id: string): Uint8Array {
  // 16 deterministic bytes derived from the id (stable across runs).
  const out = new Uint8Array(16);
  for (let i = 0; i < id.length; i++) out[i % 16] ^= id.charCodeAt(i) & 0xff;
  for (let i = 0; i < 16; i++) out[i] = (out[i] + i * 17 + 3) & 0xff;
  return out;
}

function bootstrapClaims(issuer: string, subject: string): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["human_prime", issuer],
    ["fay", subject],
    [
      "scope",
      buildScope({
        domains: ["https://api.example.com/v1/calendar"],
        actions: ["calendar:event:create"],
        terminals: ["terminal:laptop:fixed-1"],
      }),
    ],
    ["grade", 2],
    [
      "presence_req",
      buildPresenceReq({
        signalTypes: ["webauthn-uv-fresh", "presence-heartbeat-only"],
        maxStalenessMs: 5000,
        onLoss: "downgrade-to:G3",
      }),
    ],
    ["not_after", new Tag0(NOT_AFTER)],
    [
      "human_witness",
      new Map<string, CborValue>([
        ["credential_id", new TextEncoder().encode("interop-cred-id")],
        ["authenticator_data", new Uint8Array(37).fill(1)],
        ["client_data_json", new TextEncoder().encode('{"type":"webauthn.get"}')],
        ["signature", new Uint8Array(64).fill(2)],
      ]),
    ],
  ]);
}

function presenceClaims(): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["mandate-id", "mdt:interop-presence"],
    [
      "signal",
      new Map<string, CborValue>([
        ["mandate-id", "mdt:interop-presence"],
        ["signal-type", "webauthn-uv-fresh"],
        ["produced-at", new Tag0(ISSUED_AT)],
        ["nonce", nonceFor("presence-signal")],
        ["device-id", "pd:interop-device"],
      ]),
    ],
  ]);
}

function gradeSwitchClaims(): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["mandate-id", "mdt:interop-gs"],
    ["target-grade", 1],
    ["reason", "human-initiated"],
    [
      "human-witness",
      new Map<string, CborValue>([
        ["credential-id", new TextEncoder().encode("interop-cred-id")],
        ["authenticator-data", new Uint8Array(37).fill(5)],
        ["client-data-json", new TextEncoder().encode('{"type":"webauthn.get"}')],
        ["signature", new Uint8Array(64).fill(6)],
      ]),
    ],
  ]);
}

function delegateClaims(): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["parent-mandate", "mdt:interop-parent"],
    ["child-subject", "fay:interop-child"],
    [
      "child-scope",
      buildScope({
        domains: ["https://api.example.com/v1/calendar"],
        actions: ["calendar:event:create"],
      }),
    ],
    ["child-grade", 3],
    ["device-id", "terminal:interop-2"],
  ]);
}

function revokeClaims(): Map<string, CborValue> {
  return new Map<string, CborValue>([
    ["mandate-id", "mdt:interop-revoke"],
    ["cascade", true],
    ["reason", "human-initiated"],
    ["effective-at", new Tag0(ISSUED_AT)],
  ]);
}

function plans(): MessagePlan[] {
  const issuer = "hp:interop-prime";
  const subject = "fay:interop-subject";
  return [
    { id: "bootstrap-ed25519", msgType: "BOOTSTRAP", alg: "Ed25519", tlsMode: "mtls", buildClaims: () => bootstrapClaims(issuer, subject) },
    { id: "bootstrap-es256", msgType: "BOOTSTRAP", alg: "ES256", tlsMode: "tls-only", buildClaims: () => bootstrapClaims(issuer, subject) },
    { id: "bootstrap-mldsa65", msgType: "BOOTSTRAP", alg: "ML-DSA-65", tlsMode: "tls-only", buildClaims: () => bootstrapClaims(issuer, subject) },
    { id: "presence-ed25519", msgType: "PRESENCE", alg: "Ed25519", tlsMode: "tls-only", buildClaims: presenceClaims },
    { id: "grade-switch-es256", msgType: "GRADE_SWITCH", alg: "ES256", tlsMode: "mtls", buildClaims: gradeSwitchClaims },
    { id: "delegate-ed25519", msgType: "DELEGATE", alg: "Ed25519", tlsMode: "tls-only", buildClaims: delegateClaims },
    { id: "revoke-ed25519", msgType: "REVOKE", alg: "Ed25519", tlsMode: "mtls", buildClaims: revokeClaims },
  ];
}

/** Produce the full interop bundle into `outDir`. */
export function produce(outDir: string): InteropManifest {
  mkdirSync(outDir, { recursive: true });
  const messages: InteropMessage[] = [];
  const issuer = "hp:interop-prime";
  const subject = "fay:interop-subject";

  for (const plan of plans()) {
    // Deterministic key derived from the plan id so output is reproducible.
    const seed = new Uint8Array(32);
    for (let i = 0; i < plan.id.length; i++) seed[i % 32] ^= plan.id.charCodeAt(i);
    const kp = generateKeyPair(plan.alg, seed);

    const header: HeaderInput = {
      msgType: plan.msgType,
      msgId: `msg:${plan.id}`,
      issuedAt: ISSUED_AT,
      expiry: EXPIRY,
      nonce: nonceFor(plan.id),
      grade: 2,
      issuer,
      subject,
    };
    const unsigned: Envelope = buildEnvelope({
      header,
      claims: plan.buildClaims(),
      attestation: buildAttestation(kp, plan.id),
    });
    const signed = signEnvelope(unsigned, kp, plan.id);

    const sigInput = signingInput(signed);
    const sha = hashHex("SHA-256", sigInput);
    const b3 = hashHex("BLAKE3", sigInput);

    // Emit both encodings.
    const cborBytes = encodeCbor(signed);
    writeFileSync(path.join(outDir, `${plan.id}.cbor`), Buffer.from(cborBytes));
    const jsonForm = valueModelToJson(signed);
    writeFileSync(
      path.join(outDir, `${plan.id}.json`),
      JSON.stringify(jsonForm, null, 2),
      "utf8",
    );

    for (const encoding of ["cbor", "json"] as const) {
      messages.push({
        id: plan.id,
        producer: PRODUCER_TS,
        msgType: plan.msgType,
        alg: plan.alg,
        encoding,
        tlsMode: plan.tlsMode,
        bindingShape: plan.tlsMode === "mtls" ? "present-correct" : "absent",
        signingInputSha256: sha,
        signingInputBlake3: b3,
        expectedVerify: true,
      });
    }
  }

  const manifest: InteropManifest = {
    spec: "Faying Protocol/1.0",
    producer: PRODUCER_TS,
    note: "Reference Implementation, Not Normative — interop bundle for conformance testing only.",
    messages,
  };
  writeFileSync(path.join(outDir, "manifest.json"), JSON.stringify(manifest, null, 2), "utf8");
  return manifest;
}

export interface VerifyReport {
  total: number;
  passed: number;
  failed: number;
  findings: string[];
}

/** Verify an interop bundle (typically produced by the peer impl). */
export function verifyBundle(inDir: string): VerifyReport {
  const report: VerifyReport = { total: 0, passed: 0, failed: 0, findings: [] };
  const manifestPath = path.join(inDir, "manifest.json");
  if (!existsSync(manifestPath)) {
    report.findings.push(`manifest.json not found in ${inDir}`);
    return report;
  }
  const manifest = JSON.parse(readFileSync(manifestPath, "utf8")) as InteropManifest;

  for (const msg of manifest.messages) {
    report.total += 1;
    const problems: string[] = [];

    const file = path.join(inDir, `${msg.id}.${msg.encoding}`);
    if (!existsSync(file)) {
      report.failed += 1;
      report.findings.push(`[${msg.id}/${msg.encoding}] wire file missing`);
      continue;
    }

    let envelope: CborValue;
    if (msg.encoding === "cbor") {
      envelope = decodeCbor(new Uint8Array(readFileSync(file)));
    } else {
      // JSON wire form produced via valueModelToJson uses $bytes / $tag markers.
      envelope = jsonToValueModel(JSON.parse(readFileSync(file, "utf8")));
    }

    // Re-derive the §6.3 signing input and cross-check both hashes.
    const sigInput = signingInput(envelope);
    const sha = hashHex("SHA-256", sigInput);
    const b3 = hashHex("BLAKE3", sigInput);
    if (sha !== msg.signingInputSha256) {
      problems.push(`SHA-256 ${sha} != manifest ${msg.signingInputSha256}`);
    }
    if (b3 !== msg.signingInputBlake3) {
      problems.push(`BLAKE3 ${b3} != manifest ${msg.signingInputBlake3}`);
    }

    // Re-verify the signature.
    const bundle = readSignatureBundle(envelope);
    const verified = bundle !== null && cryptoVerify(bundle.alg, bundle.pubkey, sigInput, bundle.sig);
    if (verified !== msg.expectedVerify) {
      problems.push(`signature verify=${verified}, expected ${msg.expectedVerify}`);
    }
    if (bundle && bundle.alg !== msg.alg) {
      problems.push(`alg ${bundle.alg} != manifest ${msg.alg}`);
    }

    // Sanity: full verifyEnvelope agrees with the manual path.
    if (verifyEnvelope(envelope) !== verified) {
      problems.push("verifyEnvelope disagrees with manual verification");
    }

    if (problems.length === 0) {
      report.passed += 1;
    } else {
      report.failed += 1;
      report.findings.push(`[${msg.id}/${msg.encoding}] ${problems.join("; ")}`);
    }
  }
  return report;
}
