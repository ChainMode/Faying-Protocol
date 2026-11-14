// Reference Implementation, Not Normative — for conformance testing only.
//
// Cryptographic primitives for the Faying Protocol/1.0 TypeScript reference
// implementation. Mirrors the algorithm-suite semantics of the official
// vector toolchain (vectors/*/_tools/generate.py) and the Python conformance
// drivers (conformance/dim_signing/algorithms.py) so that messages produced
// here verify under the Rust reference impl, and vice versa.
//
// Algorithms (per design.md §6.1 signature-bundle.alg enum):
//   * Ed25519     — RFC 8032 EdDSA over Curve25519. Native Node crypto.
//   * ES256       — NIST P-256 ECDSA w/ SHA-256, signatures as fixed-length
//                   IEEE-P1363 r||s (64 bytes). Native Node crypto.
//   * ML-DSA-65   — FIPS 204. A vetted pure-JS implementation is not part of
//                   this reference impl; we reproduce the *deterministic
//                   placeholder* used by the vector toolchain so the
//                   algorithm-agility / negotiation path is exercised. The
//                   placeholder is NOT cryptography and MUST NOT ship in a
//                   production library. (Same stance as the Python driver.)
//
// Deterministic key derivation reproduces vectors/bootstrap/_tools/generate.py
// `derive()` (SHA-256 expansion of a seed) so a reference impl can reconstruct
// the exact keys behind a vector when desired.

import crypto from "node:crypto";

export type Alg = "Ed25519" | "ES256" | "ML-DSA-65";

export const SUPPORTED_ALGS: readonly Alg[] = ["Ed25519", "ES256", "ML-DSA-65"];

const ML_DSA_PUB_PREFIX = "test-only-ml-dsa-65-pubkey-";
const ML_DSA_SIG_PREFIX = "test-only-ml-dsa-65-sig-";

const P256_ORDER =
  0xffffffff00000000ffffffffffffffffbce6faada7179e84f3b9cac2fc632551n;

/** Normalize informal algorithm spellings to the wire enum. */
export function normalizeAlg(alg: string): Alg {
  switch (alg) {
    case "Ed25519":
    case "ed25519":
      return "Ed25519";
    case "ES256":
    case "es256":
    case "ECDSA-P256":
    case "ecdsa-p256":
      return "ES256";
    case "ML-DSA-65":
    case "ml-dsa-65":
      return "ML-DSA-65";
    default:
      throw new Error(`unsupported signing algorithm: ${alg}`);
  }
}

/** Deterministic seed expansion identical to the vector toolchain's derive(). */
export function derive(seed: Uint8Array, label: string, length = 32): Uint8Array {
  const out: number[] = [];
  let counter = 0;
  while (out.length < length) {
    const h = crypto.createHash("sha256");
    h.update(seed);
    h.update(Buffer.from(label, "utf8"));
    const ctr = Buffer.alloc(4);
    ctr.writeUInt32BE(counter >>> 0, 0);
    h.update(ctr);
    for (const b of h.digest()) out.push(b);
    counter += 1;
  }
  return Uint8Array.from(out.slice(0, length));
}

export interface KeyPair {
  alg: Alg;
  /** Algorithm-specific public-key bytes (raw32 / SEC1-uncompressed / placeholder). */
  publicKey: Uint8Array;
  /** Node KeyObject for real algorithms; null for the ML-DSA placeholder. */
  privateKey: crypto.KeyObject | null;
  /** Raw seed used to derive the key (for reproducibility). */
  seed: Uint8Array;
}

// ---- SPKI prefixes used to wrap raw public-key bytes for Node crypto ----
const ED25519_SPKI_PREFIX = Buffer.from("302a300506032b6570032100", "hex");
const P256_SPKI_PREFIX = Buffer.from(
  "3059301306072a8648ce3d020106082a8648ce3d030107034200",
  "hex",
);

function ed25519PublicKeyObject(raw: Uint8Array): crypto.KeyObject {
  return crypto.createPublicKey({
    key: Buffer.concat([ED25519_SPKI_PREFIX, Buffer.from(raw)]),
    format: "der",
    type: "spki",
  });
}

function p256PublicKeyObject(raw: Uint8Array): crypto.KeyObject {
  return crypto.createPublicKey({
    key: Buffer.concat([P256_SPKI_PREFIX, Buffer.from(raw)]),
    format: "der",
    type: "spki",
  });
}

/** Generate a deterministic keypair from a 32-byte seed. */
export function generateKeyPair(alg: Alg, seed: Uint8Array): KeyPair {
  const a = normalizeAlg(alg);
  const sk = derive(seed, `${a}:sk`, 32);
  if (a === "Ed25519") {
    const privateKey = crypto.createPrivateKey({
      key: Buffer.concat([
        Buffer.from("302e020100300506032b657004220420", "hex"),
        Buffer.from(sk),
      ]),
      format: "der",
      type: "pkcs8",
    });
    const publicKey = rawEd25519PublicKey(privateKey);
    return { alg: a, publicKey, privateKey, seed };
  }
  if (a === "ES256") {
    // Reduce the seed into a valid scalar in [1, n-1] (matches generate.py).
    let scalar = (bufToBigInt(sk) % (P256_ORDER - 1n)) + 1n;
    const privateKey = p256PrivateKeyFromScalar(scalar);
    const publicKey = rawP256PublicKey(privateKey);
    return { alg: a, publicKey, privateKey, seed };
  }
  // ML-DSA-65 placeholder.
  const publicKey = Buffer.concat([
    Buffer.from(ML_DSA_PUB_PREFIX, "utf8"),
    Buffer.from(derive(seed, "pubkey", 32)),
  ]);
  return { alg: a, publicKey: new Uint8Array(publicKey), privateKey: null, seed };
}

function bufToBigInt(b: Uint8Array): bigint {
  let v = 0n;
  for (const x of b) v = (v << 8n) | BigInt(x);
  return v;
}

function bigIntTo32(v: bigint): Buffer {
  const out = Buffer.alloc(32);
  for (let i = 31; i >= 0; i--) {
    out[i] = Number(v & 0xffn);
    v >>= 8n;
  }
  return out;
}

function rawEd25519PublicKey(privateKey: crypto.KeyObject): Uint8Array {
  const pub = crypto.createPublicKey(privateKey);
  const spki = pub.export({ format: "der", type: "spki" }) as Buffer;
  // Raw key is the trailing 32 bytes of the SPKI structure.
  return new Uint8Array(spki.subarray(spki.length - 32));
}

function p256PrivateKeyFromScalar(scalar: bigint): crypto.KeyObject {
  // Build a PKCS#8 EC private key from the raw scalar via JWK import.
  const dBytes = bigIntTo32(scalar);
  // Derive the public point by importing the private scalar through a
  // throwaway PKCS#8; Node needs the public coords for JWK, so instead we
  // construct the key via SEC1 DER which carries only the private key and
  // lets Node compute the point.
  const sec1 = buildSec1Ec(dBytes);
  return crypto.createPrivateKey({ key: sec1, format: "der", type: "sec1" });
}

function buildSec1Ec(dBytes: Buffer): Buffer {
  // SEC1 ECPrivateKey for prime256v1:
  //   SEQUENCE { INTEGER 1, OCTET STRING d(32), [0] OID prime256v1 }
  // DER assembled by hand with fixed lengths.
  const version = Buffer.from("020101", "hex"); // INTEGER 1
  const privOctet = Buffer.concat([
    Buffer.from("0420", "hex"), // OCTET STRING (32)
    dBytes,
  ]);
  const oidParams = Buffer.from("a00a06082a8648ce3d030107", "hex"); // [0] OID prime256v1
  const body = Buffer.concat([version, privOctet, oidParams]);
  const seq = Buffer.concat([Buffer.from([0x30, body.length]), body]);
  return seq;
}

function rawP256PublicKey(privateKey: crypto.KeyObject): Uint8Array {
  const jwk = privateKey.export({ format: "jwk" }) as crypto.JsonWebKey;
  const x = Buffer.from(jwk.x as string, "base64url");
  const y = Buffer.from(jwk.y as string, "base64url");
  return new Uint8Array(Buffer.concat([Buffer.from([0x04]), x, y]));
}

// ---------------------------------------------------------------------------
// Signing / verification over a message (the Det-CBOR signing input).
// ---------------------------------------------------------------------------

export function sign(kp: KeyPair, message: Uint8Array, label = "ref"): Uint8Array {
  if (kp.alg === "Ed25519") {
    return new Uint8Array(crypto.sign(null, message, kp.privateKey!));
  }
  if (kp.alg === "ES256") {
    const sig = crypto.sign("sha256", message, {
      key: kp.privateKey!,
      dsaEncoding: "ieee-p1363",
    });
    return new Uint8Array(sig);
  }
  // ML-DSA-65 deterministic placeholder (matches generate.py / Python driver).
  const digest = crypto.createHash("sha256").update(message).digest();
  const labelBytes = Buffer.alloc(8);
  Buffer.from(label, "utf8").copy(labelBytes, 0, 0, 8);
  return new Uint8Array(
    Buffer.concat([Buffer.from(ML_DSA_SIG_PREFIX, "utf8"), labelBytes, digest]),
  );
}

/**
 * Verify a signature over `message` using a public key in the wire form
 * (raw bytes from a signature-bundle). Returns true/false, never throws on
 * a cryptographic mismatch — matching the branch-free style of the Python
 * conformance drivers.
 */
export function verify(
  alg: string,
  publicKey: Uint8Array,
  message: Uint8Array,
  signature: Uint8Array,
): boolean {
  let a: Alg;
  try {
    a = normalizeAlg(alg);
  } catch {
    return false;
  }
  try {
    if (a === "Ed25519") {
      if (publicKey.length !== 32 || signature.length !== 64) return false;
      const keyObj = ed25519PublicKeyObject(publicKey);
      return crypto.verify(null, message, keyObj, Buffer.from(signature));
    }
    if (a === "ES256") {
      if (publicKey.length !== 65 || signature.length !== 64) return false;
      const keyObj = p256PublicKeyObject(publicKey);
      return crypto.verify(
        "sha256",
        message,
        { key: keyObj, dsaEncoding: "ieee-p1363" },
        Buffer.from(signature),
      );
    }
    // ML-DSA-65 placeholder: format + embedded digest check only.
    const prefix = Buffer.from(ML_DSA_SIG_PREFIX, "utf8");
    const sig = Buffer.from(signature);
    if (!sig.subarray(0, prefix.length).equals(prefix)) return false;
    if (sig.length !== prefix.length + 8 + 32) return false;
    const embedded = sig.subarray(sig.length - 32);
    const digest = crypto.createHash("sha256").update(message).digest();
    return embedded.equals(digest);
  } catch {
    return false;
  }
}

/** Detect the placeholder all-same-byte signatures used by illustrative vectors. */
export function isPlaceholderBytes(b: Uint8Array): boolean {
  if (b.length === 0) return true;
  return b.every((x) => x === b[0]);
}
