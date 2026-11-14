// Reference Implementation, Not Normative — for conformance testing only.
//
// Cryptographic primitives for the Faying Protocol/1.0 Rust reference impl.
// Mirrors the algorithm-suite semantics of the official vector toolchain
// (vectors/*/_tools/generate.py) and the TypeScript reference impl so that
// messages produced here verify under the TS impl, and vice versa.
//
//   * Ed25519     — RFC 8032 EdDSA (ed25519-dalek).
//   * ES256       — NIST P-256 ECDSA w/ SHA-256, fixed-length IEEE-P1363
//                   r||s (64 bytes) (p256 crate).
//   * ML-DSA-65   — FIPS 204. Deterministic PLACEHOLDER (NOT cryptography),
//                   identical format to the vector toolchain and the Python /
//                   TS drivers, so algorithm-agility / negotiation is
//                   exercised end-to-end.

use ed25519_dalek::{Signature as EdSignature, Signer, SigningKey, Verifier, VerifyingKey};
#[allow(unused_imports)]
use p256::ecdsa::signature::{Signer as P256Signer, Verifier as P256Verifier};
use p256::ecdsa::{Signature as P256Signature, SigningKey as P256SigningKey, VerifyingKey as P256VerifyingKey};
use sha2::{Digest, Sha256};

const ML_DSA_PUB_PREFIX: &[u8] = b"test-only-ml-dsa-65-pubkey-";
const ML_DSA_SIG_PREFIX: &[u8] = b"test-only-ml-dsa-65-sig-";

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Alg {
    Ed25519,
    Es256,
    MlDsa65,
}

impl Alg {
    pub fn wire(&self) -> &'static str {
        match self {
            Alg::Ed25519 => "Ed25519",
            Alg::Es256 => "ES256",
            Alg::MlDsa65 => "ML-DSA-65",
        }
    }
}

pub const SUPPORTED_ALGS: [Alg; 3] = [Alg::Ed25519, Alg::Es256, Alg::MlDsa65];

/// Normalize informal algorithm spellings to the wire enum.
pub fn normalize_alg(alg: &str) -> Option<Alg> {
    match alg {
        "Ed25519" | "ed25519" => Some(Alg::Ed25519),
        "ES256" | "es256" | "ECDSA-P256" | "ecdsa-p256" => Some(Alg::Es256),
        "ML-DSA-65" | "ml-dsa-65" => Some(Alg::MlDsa65),
        _ => None,
    }
}

/// Deterministic seed expansion identical to the vector toolchain's `derive()`
/// (and the TS impl's `derive`): SHA-256(seed || label || counter_be32).
pub fn derive(seed: &[u8], label: &str, length: usize) -> Vec<u8> {
    let mut out: Vec<u8> = Vec::new();
    let mut counter: u32 = 0;
    while out.len() < length {
        let mut h = Sha256::new();
        h.update(seed);
        h.update(label.as_bytes());
        h.update(counter.to_be_bytes());
        out.extend_from_slice(&h.finalize());
        counter += 1;
    }
    out.truncate(length);
    out
}

/// Algorithm-agnostic key handle.
pub struct KeyPair {
    pub alg: Alg,
    pub public_key: Vec<u8>,
    ed: Option<SigningKey>,
    es: Option<P256SigningKey>,
}

const P256_ORDER_MINUS_1: [u8; 32] = [
    0xff, 0xff, 0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff, 0xff,
    0xbc, 0xe6, 0xfa, 0xad, 0xa7, 0x17, 0x9e, 0x84, 0xf3, 0xb9, 0xca, 0xc2, 0xfc, 0x63, 0x25, 0x50,
];

/// Reduce a 32-byte seed into a valid P-256 scalar in [1, n-1], matching the
/// vector toolchain (`int(seed) % (n-1) + 1`).
fn p256_scalar_from_seed(seed: &[u8]) -> [u8; 32] {
    // Compute (seed mod (n-1)) + 1 using big-endian byte arithmetic via u128
    // chunks would overflow; instead use a simple schoolbook mod over bytes.
    // We use num-free long division by treating seed and (n-1) as big-endian.
    let n_minus_1 = &P256_ORDER_MINUS_1;
    let mut rem = mod_bytes(seed, n_minus_1);
    // rem in [0, n-2]; add 1 → [1, n-1].
    add_one_be(&mut rem);
    let mut out = [0u8; 32];
    let start = 32 - rem.len();
    out[start..].copy_from_slice(&rem);
    out
}

/// Compute `value mod modulus` for big-endian byte slices, returning a
/// minimal big-endian remainder (length <= modulus length).
fn mod_bytes(value: &[u8], modulus: &[u8]) -> Vec<u8> {
    let mut rem: Vec<u8> = Vec::new();
    for &byte in value {
        for bit in (0..8).rev() {
            // rem = rem << 1 | bit
            shl1_be(&mut rem);
            if (byte >> bit) & 1 == 1 {
                or_lsb(&mut rem);
            }
            if cmp_be(&rem, modulus) != std::cmp::Ordering::Less {
                sub_be(&mut rem, modulus);
            }
        }
    }
    if rem.is_empty() {
        rem.push(0);
    }
    rem
}

fn shl1_be(v: &mut Vec<u8>) {
    let mut carry = 0u8;
    for byte in v.iter_mut().rev() {
        let new_carry = *byte >> 7;
        *byte = (*byte << 1) | carry;
        carry = new_carry;
    }
    if carry == 1 {
        v.insert(0, 1);
    }
}

fn or_lsb(v: &mut Vec<u8>) {
    if v.is_empty() {
        v.push(1);
    } else {
        let last = v.len() - 1;
        v[last] |= 1;
    }
}

fn cmp_be(a: &[u8], b: &[u8]) -> std::cmp::Ordering {
    let a_trim = trim_leading_zeros(a);
    let b_trim = trim_leading_zeros(b);
    if a_trim.len() != b_trim.len() {
        return a_trim.len().cmp(&b_trim.len());
    }
    a_trim.cmp(b_trim)
}

fn trim_leading_zeros(a: &[u8]) -> &[u8] {
    let mut i = 0;
    while i < a.len() && a[i] == 0 {
        i += 1;
    }
    &a[i..]
}

fn sub_be(a: &mut Vec<u8>, b: &[u8]) {
    // a = a - b, assuming a >= b. Both big-endian.
    let mut borrow = 0i16;
    let alen = a.len();
    let blen = b.len();
    for i in 0..alen {
        let ai = a[alen - 1 - i] as i16;
        let bi = if i < blen { b[blen - 1 - i] as i16 } else { 0 };
        let mut diff = ai - bi - borrow;
        if diff < 0 {
            diff += 256;
            borrow = 1;
        } else {
            borrow = 0;
        }
        a[alen - 1 - i] = diff as u8;
    }
    let trimmed = trim_leading_zeros(a).to_vec();
    *a = if trimmed.is_empty() { vec![0] } else { trimmed };
}

fn add_one_be(v: &mut Vec<u8>) {
    let mut carry = 1u16;
    for byte in v.iter_mut().rev() {
        let sum = *byte as u16 + carry;
        *byte = (sum & 0xff) as u8;
        carry = sum >> 8;
        if carry == 0 {
            break;
        }
    }
    if carry > 0 {
        v.insert(0, carry as u8);
    }
}

/// Generate a deterministic keypair for `alg` from a 32-byte seed.
pub fn generate_keypair(alg: Alg, seed: &[u8]) -> KeyPair {
    let sk_seed = derive(seed, &format!("{}:sk", alg.wire()), 32);
    match alg {
        Alg::Ed25519 => {
            let mut arr = [0u8; 32];
            arr.copy_from_slice(&sk_seed);
            let signing = SigningKey::from_bytes(&arr);
            let public_key = signing.verifying_key().to_bytes().to_vec();
            KeyPair {
                alg,
                public_key,
                ed: Some(signing),
                es: None,
            }
        }
        Alg::Es256 => {
            let scalar = p256_scalar_from_seed(&sk_seed);
            let signing = P256SigningKey::from_bytes((&scalar).into())
                .expect("valid P-256 scalar");
            let verifying = signing.verifying_key();
            let public_key = verifying
                .to_encoded_point(false)
                .as_bytes()
                .to_vec();
            KeyPair {
                alg,
                public_key,
                ed: None,
                es: Some(signing),
            }
        }
        Alg::MlDsa65 => {
            let mut public_key = ML_DSA_PUB_PREFIX.to_vec();
            public_key.extend_from_slice(&derive(seed, "pubkey", 32));
            KeyPair {
                alg,
                public_key,
                ed: None,
                es: None,
            }
        }
    }
}

/// Sign a message (the Det-CBOR signing input) with `kp`.
pub fn sign(kp: &KeyPair, message: &[u8], label: &str) -> Vec<u8> {
    match kp.alg {
        Alg::Ed25519 => {
            let sig = kp.ed.as_ref().expect("ed key").sign(message);
            sig.to_bytes().to_vec()
        }
        Alg::Es256 => {
            let sig: P256Signature = kp.es.as_ref().expect("es key").sign(message);
            // p256 ecdsa Signature is fixed-length r||s (64 bytes).
            sig.to_bytes().to_vec()
        }
        Alg::MlDsa65 => {
            let digest = Sha256::digest(message);
            let mut label_bytes = [0u8; 8];
            let lb = label.as_bytes();
            let n = lb.len().min(8);
            label_bytes[..n].copy_from_slice(&lb[..n]);
            let mut out = ML_DSA_SIG_PREFIX.to_vec();
            out.extend_from_slice(&label_bytes);
            out.extend_from_slice(&digest);
            out
        }
    }
}

/// Verify a signature over `message` using a wire-form public key.
/// Returns true/false; never panics on a cryptographic mismatch.
pub fn verify(alg: &str, public_key: &[u8], message: &[u8], signature: &[u8]) -> bool {
    let a = match normalize_alg(alg) {
        Some(a) => a,
        None => return false,
    };
    match a {
        Alg::Ed25519 => {
            if public_key.len() != 32 || signature.len() != 64 {
                return false;
            }
            let mut pk = [0u8; 32];
            pk.copy_from_slice(public_key);
            let vk = match VerifyingKey::from_bytes(&pk) {
                Ok(v) => v,
                Err(_) => return false,
            };
            let mut sig = [0u8; 64];
            sig.copy_from_slice(signature);
            let signature = EdSignature::from_bytes(&sig);
            vk.verify(message, &signature).is_ok()
        }
        Alg::Es256 => {
            if public_key.len() != 65 || signature.len() != 64 {
                return false;
            }
            let vk = match P256VerifyingKey::from_sec1_bytes(public_key) {
                Ok(v) => v,
                Err(_) => return false,
            };
            let sig = match P256Signature::from_slice(signature) {
                Ok(s) => s,
                Err(_) => return false,
            };
            vk.verify(message, &sig).is_ok()
        }
        Alg::MlDsa65 => {
            if !signature.starts_with(ML_DSA_SIG_PREFIX) {
                return false;
            }
            if signature.len() != ML_DSA_SIG_PREFIX.len() + 8 + 32 {
                return false;
            }
            let embedded = &signature[signature.len() - 32..];
            let digest = Sha256::digest(message);
            embedded == &digest[..]
        }
    }
}

/// Detect placeholder all-same-byte signatures used by illustrative vectors.
pub fn is_placeholder_bytes(b: &[u8]) -> bool {
    if b.is_empty() {
        return true;
    }
    b.iter().all(|&x| x == b[0])
}
