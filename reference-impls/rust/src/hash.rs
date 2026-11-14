// Reference Implementation, Not Normative — for conformance testing only.
//
// Hash agility for the §6.3 signing-input expression. Both algorithms emit
// 32-byte digests; only the wrapper changes (design.md §6.1 / §6.3).

use sha2::{Digest, Sha256};

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum Hash {
    Sha256,
    Blake3,
}

pub const SUPPORTED_HASHES: [Hash; 2] = [Hash::Sha256, Hash::Blake3];

impl Hash {
    pub fn wire(&self) -> &'static str {
        match self {
            Hash::Sha256 => "SHA-256",
            Hash::Blake3 => "BLAKE3",
        }
    }
}

pub fn normalize_hash(name: &str) -> Option<Hash> {
    match name {
        "SHA-256" | "sha-256" | "sha256" | "SHA256" => Some(Hash::Sha256),
        "BLAKE3" | "blake3" | "Blake3" => Some(Hash::Blake3),
        _ => None,
    }
}

pub fn compute_hash(alg: Hash, data: &[u8]) -> Vec<u8> {
    let digest = match alg {
        Hash::Sha256 => Sha256::digest(data).to_vec(),
        Hash::Blake3 => blake3::hash(data).as_bytes().to_vec(),
    };
    assert_eq!(digest.len(), 32, "protocol fixes 32-byte digests");
    digest
}

pub fn hash_hex(alg: Hash, data: &[u8]) -> String {
    hex::encode(compute_hash(alg, data))
}
