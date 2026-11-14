// Reference Implementation, Not Normative — for conformance testing only.
//
// Algorithm-suite negotiation (Requirement 8.1 / 8.2). Mirrors
// conformance/dim_signing/negotiation.py and the TS negotiation.ts:
//   strength order = ML-DSA-65 > Ed25519 > ES256
//   empty intersection → E_PROTOCOL (1099)

use crate::crypto::{normalize_alg, Alg};

pub const NEGOTIATION_ORDER: [Alg; 3] = [Alg::MlDsa65, Alg::Ed25519, Alg::Es256];

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct NegotiationError {
    pub error_name: &'static str,
    pub error_code: u32,
    pub message: String,
}

fn normalize_set(algs: &[&str]) -> Vec<Alg> {
    let mut out = Vec::new();
    for a in algs {
        if let Some(alg) = normalize_alg(a) {
            if !out.contains(&alg) {
                out.push(alg);
            }
        }
    }
    out
}

pub fn negotiate(client: &[&str], server: &[&str]) -> Result<Alg, NegotiationError> {
    let c = normalize_set(client);
    let s = normalize_set(server);
    let intersection: Vec<Alg> = c.iter().copied().filter(|a| s.contains(a)).collect();
    if intersection.is_empty() {
        return Err(NegotiationError {
            error_name: "E_PROTOCOL",
            error_code: 1099,
            message: "no common signing algorithm".into(),
        });
    }
    for alg in NEGOTIATION_ORDER {
        if intersection.contains(&alg) {
            return Ok(alg);
        }
    }
    Err(NegotiationError {
        error_name: "E_PROTOCOL",
        error_code: 1099,
        message: "intersection outside NEGOTIATION_ORDER".into(),
    })
}
