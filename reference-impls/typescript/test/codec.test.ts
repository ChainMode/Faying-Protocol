// Reference Implementation, Not Normative — for conformance testing only.
//
// Unit tests for the TypeScript reference codec. Run with `node --test`.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import path from "node:path";
import { decode, encode, Tag0 } from "../src/detcbor.ts";
import { signingInput, signingInputHash, verifyEnvelope } from "../src/protocol.ts";
import { generateKeyPair, sign, verify } from "../src/crypto.ts";
import { computeHash } from "../src/hash.ts";
import { negotiate, NegotiationError } from "../src/negotiation.ts";
import { VECTORS_DIR } from "../src/vectors.ts";
import { runAllDimensions } from "../src/dimensions.ts";

test("deterministic CBOR sorts map keys bytewise (RFC 8949 §4.2.1)", () => {
  const m = new Map<string, any>([
    ["z", 1],
    ["aa", 2],
    ["b", 3],
  ]);
  // Expected: keys ordered by encoded bytes → b, z, aa.
  const hex = Buffer.from(encode(m)).toString("hex");
  assert.equal(hex, "a3616203617a0162616102");
});

test("round-trips the encoding-equivalence corpus byte-for-byte", () => {
  for (const id of ["01-bootstrap", "02-presence", "03-grade-switch", "04-delegate", "05-revoke"]) {
    const dir = path.join(VECTORS_DIR, "encoding-equivalence", id);
    const cbor = new Uint8Array(readFileSync(path.join(dir, "message.cbor")));
    const obj = decode(cbor);
    assert.equal(
      Buffer.from(encode(obj)).toString("hex"),
      Buffer.from(cbor).toString("hex"),
      `${id} canonical re-encode must reproduce on-disk bytes`,
    );
    const storedHash = readFileSync(path.join(dir, "signature.input.hash.hex"), "utf8").trim();
    assert.equal(signingInputHash(obj), storedHash, `${id} signing-input hash`);
    assert.ok(verifyEnvelope(obj), `${id} envelope signature verifies`);
  }
});

test("Tag0 timestamps survive a decode/encode round-trip", () => {
  const m = new Map<string, any>([["t", new Tag0("2026-01-01T00:00:00Z")]]);
  const back = decode(encode(m)) as Map<string, any>;
  assert.ok(back.get("t") instanceof Tag0);
  assert.equal((back.get("t") as Tag0).value, "2026-01-01T00:00:00Z");
});

test("sign/verify roundtrip for all three algorithms", () => {
  for (const alg of ["Ed25519", "ES256", "ML-DSA-65"] as const) {
    const kp = generateKeyPair(alg, new Uint8Array(32).fill(7));
    const msg = new TextEncoder().encode("interop message");
    const sig = sign(kp, msg, "test");
    assert.ok(verify(alg, kp.publicKey, msg, sig), `${alg} verifies`);
    assert.ok(!verify(alg, kp.publicKey, new TextEncoder().encode("other"), sig), `${alg} rejects tamper`);
  }
});

test("both hashes produce 32-byte digests over the signing input", () => {
  const m = new Map<string, any>([["a", 1]]);
  const input = signingInput(m);
  assert.equal(computeHash("SHA-256", input).length, 32);
  assert.equal(computeHash("BLAKE3", input).length, 32);
});

test("negotiation picks strongest mutual algorithm / rejects disjoint", () => {
  assert.equal(negotiate(["Ed25519", "ML-DSA-65"], ["ES256", "ML-DSA-65"]), "ML-DSA-65");
  assert.equal(negotiate(["Ed25519", "ES256", "ML-DSA-65"], ["Ed25519", "ES256"]), "Ed25519");
  assert.throws(() => negotiate(["Ed25519"], ["RSA"]), NegotiationError);
});

test("all data-plane dimensions pass over the corpus", () => {
  for (const r of runAllDimensions()) {
    assert.equal(r.failed, 0, `${r.name}: ${r.findings.join("; ")}`);
    assert.ok(r.total > 0, `${r.name} ran at least one check`);
  }
});
