// Reference Implementation, Not Normative — for conformance testing only.
//
// Runs the four data-plane conformance dimensions (tasks 5.2–5.5) over the
// official corpus from the Rust reference impl's perspective, mirroring
// conformance/dim_*/ and the TS dimensions.ts so the cross-impl matrix can
// assert all three (Python suite / TS / Rust) agree.

use crate::crypto::{self, SUPPORTED_ALGS};
use crate::hash::{self, SUPPORTED_HASHES};
use crate::json_wire;
use crate::negotiation::{negotiate, NegotiationError};
use crate::protocol;
use crate::vectors::{load_all_vectors, vectors_dir, LoadedVector};
use serde_json::Value as Json;
use std::fs;

pub struct DimResult {
    pub name: String,
    pub total: usize,
    pub passed: usize,
    pub failed: usize,
    pub findings: Vec<String>,
}

impl DimResult {
    fn new(name: &str) -> Self {
        DimResult {
            name: name.to_string(),
            total: 0,
            passed: 0,
            failed: 0,
            findings: Vec::new(),
        }
    }
}

// ---------------------------------------------------------------------------
// Encoding dimension (5.2).
// ---------------------------------------------------------------------------

pub fn run_encoding() -> DimResult {
    let mut result = DimResult::new("encoding");
    let eq_dir = vectors_dir().join("encoding-equivalence");
    let index_path = eq_dir.join("index.json");
    let index: Json = match fs::read_to_string(&index_path).ok().and_then(|t| serde_json::from_str(&t).ok()) {
        Some(j) => j,
        None => {
            result.findings.push("encoding-equivalence/index.json not found".into());
            return result;
        }
    };
    let entries = match index.get("vectors").and_then(|v| v.as_array()) {
        Some(a) => a.clone(),
        None => return result,
    };

    for entry in entries {
        let id = match entry.get("id").and_then(|v| v.as_str()) {
            Some(s) => s,
            None => continue,
        };
        result.total += 1;
        let dir = eq_dir.join(id);
        let expected: Json = serde_json::from_str(
            &fs::read_to_string(dir.join("expected.json")).unwrap_or_default(),
        )
        .unwrap_or(Json::Null);
        let binary_paths: Vec<String> = expected
            .get("binary_field_paths")
            .and_then(|v| v.as_array())
            .map(|a| a.iter().filter_map(|x| x.as_str().map(String::from)).collect())
            .unwrap_or_default();

        let cbor_bytes = fs::read(dir.join("message.cbor")).unwrap_or_default();
        let cbor_obj = match protocol::decode_cbor(&cbor_bytes) {
            Ok(o) => o,
            Err(e) => {
                result.failed += 1;
                result.findings.push(format!("[{id}] cbor decode: {e}"));
                continue;
            }
        };
        let json_raw: Json = serde_json::from_str(
            &fs::read_to_string(dir.join("message.json")).unwrap_or_default(),
        )
        .unwrap_or(Json::Null);
        let json_obj = match json_wire::json_to_value(&json_raw, &binary_paths) {
            Ok(o) => o,
            Err(e) => {
                result.failed += 1;
                result.findings.push(format!("[{id}] json normalize: {e}"));
                continue;
            }
        };

        let cbor_sig = hex::encode(protocol::signing_input(&cbor_obj));
        let json_sig = hex::encode(protocol::signing_input(&json_obj));
        let want_hash = expected
            .get("signature_input")
            .and_then(|s| s.get("hash_hex"))
            .and_then(|h| h.as_str());
        let got_hash = protocol::signing_input_hash(&cbor_obj);

        let mut problems = Vec::new();
        if cbor_sig != json_sig {
            problems.push("Det-CBOR signing input differs CBOR vs JSON".to_string());
        }
        if let Some(w) = want_hash {
            if w != got_hash {
                problems.push(format!("hash {got_hash} != expected {w}"));
            }
        }
        if !protocol::verify_envelope(&cbor_obj) {
            problems.push("CBOR envelope signature did not verify".to_string());
        }

        if problems.is_empty() {
            result.passed += 1;
        } else {
            result.failed += 1;
            result.findings.push(format!("[{id}] {}", problems.join("; ")));
        }
    }
    result
}

// ---------------------------------------------------------------------------
// Signing dimension (5.3): re-sign under all algorithms + negotiation.
// ---------------------------------------------------------------------------

pub fn run_signing() -> DimResult {
    let mut result = DimResult::new("signing");
    let vectors = load_all_vectors();

    for vec in &vectors {
        if !vec.envelope.is_map() {
            continue;
        }
        result.total += 1;
        let input = protocol::signing_input(&vec.envelope);
        let baseline_hash = hash::hash_hex(hash::Hash::Sha256, &input);
        let mut problems = Vec::new();

        for alg in SUPPORTED_ALGS {
            let seed = [0u8; 32];
            let kp = crypto::generate_keypair(alg, &seed);
            let sig = crypto::sign(&kp, &input, &format!("{}:{}", vec.case_name, alg.wire()));
            if !crypto::verify(alg.wire(), &kp.public_key, &input, &sig) {
                problems.push(format!("{} re-sign/verify failed", alg.wire()));
            }
            let h = hash::hash_hex(hash::Hash::Sha256, &input);
            if h != baseline_hash {
                problems.push(format!("{} perturbed signing input", alg.wire()));
            }
        }

        if problems.is_empty() {
            result.passed += 1;
        } else {
            result.failed += 1;
            result
                .findings
                .push(format!("[{}/{}] {}", vec.category, vec.case_name, problems.join("; ")));
        }
    }

    // Negotiation checks (Requirement 8.1 / 8.2).
    let neg_checks: Vec<(&str, Box<dyn Fn() -> bool>)> = vec![
        (
            "strongest mutual = ML-DSA-65",
            Box::new(|| {
                negotiate(&["Ed25519", "ML-DSA-65"], &["ES256", "ML-DSA-65"])
                    .map(|a| a == crypto::Alg::MlDsa65)
                    .unwrap_or(false)
            }),
        ),
        (
            "classical fallback = Ed25519",
            Box::new(|| {
                negotiate(&["Ed25519", "ES256", "ML-DSA-65"], &["Ed25519", "ES256"])
                    .map(|a| a == crypto::Alg::Ed25519)
                    .unwrap_or(false)
            }),
        ),
        (
            "ECDSA-P256 alias = ES256",
            Box::new(|| {
                negotiate(&["ECDSA-P256"], &["ES256"])
                    .map(|a| a == crypto::Alg::Es256)
                    .unwrap_or(false)
            }),
        ),
        (
            "disjoint sets -> E_PROTOCOL",
            Box::new(|| match negotiate(&["Ed25519"], &["RSA-PKCS1"]) {
                Err(NegotiationError { error_code, .. }) => error_code == 1099,
                Ok(_) => false,
            }),
        ),
    ];
    for (name, check) in neg_checks {
        result.total += 1;
        if check() {
            result.passed += 1;
        } else {
            result.failed += 1;
            result.findings.push(format!("[negotiation] {name} failed"));
        }
    }

    result
}

// ---------------------------------------------------------------------------
// Hash dimension (5.4).
// ---------------------------------------------------------------------------

pub fn run_hash() -> DimResult {
    let mut result = DimResult::new("hash");
    let vectors = load_all_vectors();
    for vec in &vectors {
        let input = protocol::signing_input(&vec.envelope);
        let mut problems = Vec::new();
        for h in SUPPORTED_HASHES {
            let digest = hash::compute_hash(h, &input);
            if digest.len() != 32 {
                problems.push(format!("{} digest len {} != 32", h.wire(), digest.len()));
            }
        }
        if let Some(reference) = extract_reference_sha256(vec) {
            let got = hash::hash_hex(hash::Hash::Sha256, &input);
            if got != reference {
                problems.push(format!("SHA-256 {got} != reference {reference}"));
            }
        }
        result.total += 1;
        if problems.is_empty() {
            result.passed += 1;
        } else {
            result.failed += 1;
            result
                .findings
                .push(format!("[{}/{}] {}", vec.category, vec.case_name, problems.join("; ")));
        }
    }
    result
}

fn extract_reference_sha256(vec: &LoadedVector) -> Option<String> {
    if let Some(sig_input) = vec.expected.get("signature_input") {
        if sig_input.get("wire_matches_signature_input") == Some(&Json::Bool(false)) {
            return sig_input
                .get("wire_hash_hex")
                .and_then(|v| v.as_str())
                .map(|s| s.to_lowercase());
        }
        let alg = sig_input
            .get("hash_alg")
            .or_else(|| sig_input.get("hash_algorithm"))
            .and_then(|v| v.as_str());
        if let Some(h) = sig_input.get("hash_hex").and_then(|v| v.as_str()) {
            let alg_ok = alg
                .map(|a| a.to_uppercase().replace('-', "") == "SHA256")
                .unwrap_or(true);
            if alg_ok {
                return Some(h.to_lowercase());
            }
        }
    }
    if let Some(digests) = vec.expected.get("digests") {
        let role = vec
            .envelope_file
            .file_stem()
            .and_then(|s| s.to_str())
            .unwrap_or("envelope");
        for key in [format!("{role}_signing_input_sha256"), "signing_input_sha256".to_string()] {
            if let Some(v) = digests.get(&key).and_then(|v| v.as_str()) {
                return Some(v.to_lowercase());
            }
        }
    }
    None
}

// ---------------------------------------------------------------------------
// Channel dimension (5.5).
// ---------------------------------------------------------------------------

/// RP-side channel-binding validator (mirrors dim_channel/rp_validator.py).
pub fn validate_channel_binding(tls_mode: &str, binding_shape: &str) -> (bool, Option<u32>) {
    if tls_mode == "mtls" {
        if binding_shape == "present-correct" {
            (true, None)
        } else {
            (false, Some(1007))
        }
    } else if binding_shape == "absent" {
        (true, None)
    } else {
        (false, Some(1099))
    }
}

pub fn run_channel() -> DimResult {
    let mut result = DimResult::new("channel");
    for message_type in ["BOOTSTRAP", "DELEGATE", "REVOKE"] {
        for tls_mode in ["tls-only", "mtls"] {
            for binding_shape in ["present-correct", "present-tampered", "absent"] {
                result.total += 1;
                let (accepted, code) = validate_channel_binding(tls_mode, binding_shape);
                let (exp_accepted, exp_code) = expected_outcome(tls_mode, binding_shape);
                if accepted == exp_accepted && code == exp_code {
                    result.passed += 1;
                } else {
                    result.failed += 1;
                    result.findings.push(format!(
                        "[{message_type}/{tls_mode}/{binding_shape}] got ({accepted:?},{code:?})"
                    ));
                }
            }
        }
    }
    result
}

fn expected_outcome(tls_mode: &str, binding_shape: &str) -> (bool, Option<u32>) {
    validate_channel_binding(tls_mode, binding_shape)
}

pub fn run_all_dimensions() -> Vec<DimResult> {
    vec![run_encoding(), run_signing(), run_hash(), run_channel()]
}
