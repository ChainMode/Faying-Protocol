// Reference Implementation, Not Normative — for conformance testing only.
//
// Cross-implementation interop: the Rust impl PRODUCES protocol messages the
// TypeScript impl must parse + verify, and VERIFIES messages the TS impl
// produced. The wire layout and manifest schema are IDENTICAL to the TS impl's
// (see reference-impls/typescript/src/interop.ts) so bundles are mutually
// consumable:
//
//   <out>/manifest.json     index of every produced message
//   <out>/<id>.cbor         canonical CBOR wire form
//   <out>/<id>.json         JSON fallback wire form
//
// Manifest fields per message (camelCase, matching the TS impl):
//   id, producer, msgType, alg, encoding, tlsMode, bindingShape,
//   signingInputSha256, signingInputBlake3, expectedVerify.

use crate::crypto::{self, Alg};
use crate::detcbor::Value;
use crate::hash;
use crate::json_wire;
use crate::protocol::{self, HeaderInput};
use serde_json::{json, Value as Json};
use std::fs;
use std::path::Path;

const PRODUCER_RUST: &str = "rust";
const ISSUED_AT: &str = "2026-03-01T00:00:00Z";
const EXPIRY: &str = "2026-03-01T00:01:00Z";
const NOT_AFTER: &str = "2026-03-01T23:59:59Z";

fn nonce_for(id: &str) -> Vec<u8> {
    let mut out = [0u8; 16];
    for (i, b) in id.bytes().enumerate() {
        out[i % 16] ^= b;
    }
    for i in 0..16 {
        out[i] = out[i].wrapping_add((i as u8).wrapping_mul(17).wrapping_add(3));
    }
    out.to_vec()
}

struct Plan {
    id: &'static str,
    msg_type: &'static str,
    alg: Alg,
    tls_mode: &'static str,
}

fn plans() -> Vec<Plan> {
    vec![
        Plan { id: "bootstrap-ed25519", msg_type: "BOOTSTRAP", alg: Alg::Ed25519, tls_mode: "mtls" },
        Plan { id: "bootstrap-es256", msg_type: "BOOTSTRAP", alg: Alg::Es256, tls_mode: "tls-only" },
        Plan { id: "bootstrap-mldsa65", msg_type: "BOOTSTRAP", alg: Alg::MlDsa65, tls_mode: "tls-only" },
        Plan { id: "presence-ed25519", msg_type: "PRESENCE", alg: Alg::Ed25519, tls_mode: "tls-only" },
        Plan { id: "grade-switch-es256", msg_type: "GRADE_SWITCH", alg: Alg::Es256, tls_mode: "mtls" },
        Plan { id: "delegate-ed25519", msg_type: "DELEGATE", alg: Alg::Ed25519, tls_mode: "tls-only" },
        Plan { id: "revoke-ed25519", msg_type: "REVOKE", alg: Alg::Ed25519, tls_mode: "mtls" },
    ]
}

fn build_claims(plan: &Plan, issuer: &str, subject: &str) -> Value {
    match plan.msg_type {
        "BOOTSTRAP" => Value::Map(vec![
            ("human_prime".into(), Value::Text(issuer.into())),
            ("fay".into(), Value::Text(subject.into())),
            (
                "scope".into(),
                Value::Map(vec![
                    (
                        "domains".into(),
                        Value::Array(vec![Value::Text("https://api.example.com/v1/calendar".into())]),
                    ),
                    (
                        "actions".into(),
                        Value::Array(vec![Value::Text("calendar:event:create".into())]),
                    ),
                    (
                        "terminals".into(),
                        Value::Array(vec![Value::Text("terminal:laptop:fixed-1".into())]),
                    ),
                ]),
            ),
            ("grade".into(), Value::Int(2)),
            (
                "presence_req".into(),
                Value::Map(vec![
                    (
                        "signal-types".into(),
                        Value::Array(vec![
                            Value::Text("webauthn-uv-fresh".into()),
                            Value::Text("presence-heartbeat-only".into()),
                        ]),
                    ),
                    ("max-staleness-ms".into(), Value::Int(5000)),
                    ("on-loss".into(), Value::Text("downgrade-to:G3".into())),
                ]),
            ),
            ("not_after".into(), Value::Tag0(NOT_AFTER.into())),
            (
                "human_witness".into(),
                Value::Map(vec![
                    ("credential_id".into(), Value::Bytes(b"interop-cred-id".to_vec())),
                    ("authenticator_data".into(), Value::Bytes(vec![1u8; 37])),
                    (
                        "client_data_json".into(),
                        Value::Bytes(b"{\"type\":\"webauthn.get\"}".to_vec()),
                    ),
                    ("signature".into(), Value::Bytes(vec![2u8; 64])),
                ]),
            ),
        ]),
        "PRESENCE" => Value::Map(vec![
            ("mandate-id".into(), Value::Text("mdt:interop-presence".into())),
            (
                "signal".into(),
                Value::Map(vec![
                    ("mandate-id".into(), Value::Text("mdt:interop-presence".into())),
                    ("signal-type".into(), Value::Text("webauthn-uv-fresh".into())),
                    ("produced-at".into(), Value::Tag0(ISSUED_AT.into())),
                    ("nonce".into(), Value::Bytes(nonce_for("presence-signal"))),
                    ("device-id".into(), Value::Text("pd:interop-device".into())),
                ]),
            ),
        ]),
        "GRADE_SWITCH" => Value::Map(vec![
            ("mandate-id".into(), Value::Text("mdt:interop-gs".into())),
            ("target-grade".into(), Value::Int(1)),
            ("reason".into(), Value::Text("human-initiated".into())),
            (
                "human-witness".into(),
                Value::Map(vec![
                    ("credential-id".into(), Value::Bytes(b"interop-cred-id".to_vec())),
                    ("authenticator-data".into(), Value::Bytes(vec![5u8; 37])),
                    (
                        "client-data-json".into(),
                        Value::Bytes(b"{\"type\":\"webauthn.get\"}".to_vec()),
                    ),
                    ("signature".into(), Value::Bytes(vec![6u8; 64])),
                ]),
            ),
        ]),
        "DELEGATE" => Value::Map(vec![
            ("parent-mandate".into(), Value::Text("mdt:interop-parent".into())),
            ("child-subject".into(), Value::Text("fay:interop-child".into())),
            (
                "child-scope".into(),
                Value::Map(vec![
                    (
                        "domains".into(),
                        Value::Array(vec![Value::Text("https://api.example.com/v1/calendar".into())]),
                    ),
                    (
                        "actions".into(),
                        Value::Array(vec![Value::Text("calendar:event:create".into())]),
                    ),
                ]),
            ),
            ("child-grade".into(), Value::Int(3)),
            ("device-id".into(), Value::Text("terminal:interop-2".into())),
        ]),
        "REVOKE" => Value::Map(vec![
            ("mandate-id".into(), Value::Text("mdt:interop-revoke".into())),
            ("cascade".into(), Value::Bool(true)),
            ("reason".into(), Value::Text("human-initiated".into())),
            ("effective-at".into(), Value::Tag0(ISSUED_AT.into())),
        ]),
        other => Value::Map(vec![("msg".into(), Value::Text(other.into()))]),
    }
}

pub struct ProduceSummary {
    pub message_rows: usize,
}

/// Produce the full interop bundle into `out_dir`.
pub fn produce(out_dir: &Path) -> std::io::Result<ProduceSummary> {
    fs::create_dir_all(out_dir)?;
    let issuer = "hp:interop-prime";
    let subject = "fay:interop-subject";
    let mut messages: Vec<Json> = Vec::new();

    for plan in plans() {
        let mut seed = [0u8; 32];
        for (i, b) in plan.id.bytes().enumerate() {
            seed[i % 32] ^= b;
        }
        let kp = crypto::generate_keypair(plan.alg, &seed);

        let header = protocol::build_header(&HeaderInput {
            msg_type: plan.msg_type,
            msg_id: &format!("msg:{}", plan.id),
            issued_at: ISSUED_AT,
            expiry: EXPIRY,
            nonce: nonce_for(plan.id),
            grade: 2,
            issuer,
            subject,
        });
        let claims = build_claims(&plan, issuer, subject);
        let attestation = protocol::build_attestation(&kp, plan.id);
        let unsigned = protocol::build_envelope(header, claims, attestation);
        let signed = protocol::sign_envelope(&unsigned, &kp, plan.id);

        let sig_input = protocol::signing_input(&signed);
        let sha = hash::hash_hex(hash::Hash::Sha256, &sig_input);
        let b3 = hash::hash_hex(hash::Hash::Blake3, &sig_input);

        let cbor_bytes = protocol::encode_cbor(&signed);
        fs::write(out_dir.join(format!("{}.cbor", plan.id)), &cbor_bytes)?;
        let json_form = json_wire::value_to_json(&signed);
        fs::write(
            out_dir.join(format!("{}.json", plan.id)),
            serde_json::to_string_pretty(&json_form).unwrap(),
        )?;

        for encoding in ["cbor", "json"] {
            messages.push(json!({
                "id": plan.id,
                "producer": PRODUCER_RUST,
                "msgType": plan.msg_type,
                "alg": plan.alg.wire(),
                "encoding": encoding,
                "tlsMode": plan.tls_mode,
                "bindingShape": if plan.tls_mode == "mtls" { "present-correct" } else { "absent" },
                "signingInputSha256": sha,
                "signingInputBlake3": b3,
                "expectedVerify": true,
            }));
        }
    }

    let manifest = json!({
        "spec": "Faying Protocol/1.0",
        "producer": PRODUCER_RUST,
        "note": "Reference Implementation, Not Normative — interop bundle for conformance testing only.",
        "messages": messages,
    });
    fs::write(
        out_dir.join("manifest.json"),
        serde_json::to_string_pretty(&manifest).unwrap(),
    )?;

    Ok(ProduceSummary {
        message_rows: messages.len(),
    })
}

pub struct VerifyReport {
    pub total: usize,
    pub passed: usize,
    pub failed: usize,
    pub findings: Vec<String>,
}

/// Verify an interop bundle (typically produced by the peer TS impl).
pub fn verify_bundle(in_dir: &Path) -> VerifyReport {
    let mut report = VerifyReport {
        total: 0,
        passed: 0,
        failed: 0,
        findings: Vec::new(),
    };
    let manifest_path = in_dir.join("manifest.json");
    let manifest: Json = match fs::read_to_string(&manifest_path).ok().and_then(|t| serde_json::from_str(&t).ok()) {
        Some(j) => j,
        None => {
            report.findings.push(format!("manifest.json not found in {in_dir:?}"));
            return report;
        }
    };
    let messages = match manifest.get("messages").and_then(|m| m.as_array()) {
        Some(m) => m.clone(),
        None => {
            report.findings.push("manifest has no messages array".into());
            return report;
        }
    };

    for msg in messages {
        report.total += 1;
        let id = msg.get("id").and_then(|v| v.as_str()).unwrap_or("?");
        let encoding = msg.get("encoding").and_then(|v| v.as_str()).unwrap_or("cbor");
        let mut problems = Vec::new();

        let file = in_dir.join(format!("{id}.{encoding}"));
        if !file.is_file() {
            report.failed += 1;
            report.findings.push(format!("[{id}/{encoding}] wire file missing"));
            continue;
        }

        let envelope: Value = if encoding == "cbor" {
            match protocol::decode_cbor(&fs::read(&file).unwrap_or_default()) {
                Ok(e) => e,
                Err(e) => {
                    report.failed += 1;
                    report.findings.push(format!("[{id}/cbor] decode: {e}"));
                    continue;
                }
            }
        } else {
            let raw: Json = serde_json::from_str(&fs::read_to_string(&file).unwrap_or_default())
                .unwrap_or(Json::Null);
            match json_wire::json_to_value(&raw, &[]) {
                Ok(e) => e,
                Err(e) => {
                    report.failed += 1;
                    report.findings.push(format!("[{id}/json] normalize: {e}"));
                    continue;
                }
            }
        };

        let sig_input = protocol::signing_input(&envelope);
        let sha = hash::hash_hex(hash::Hash::Sha256, &sig_input);
        let b3 = hash::hash_hex(hash::Hash::Blake3, &sig_input);
        if let Some(want) = msg.get("signingInputSha256").and_then(|v| v.as_str()) {
            if want != sha {
                problems.push(format!("SHA-256 {sha} != manifest {want}"));
            }
        }
        if let Some(want) = msg.get("signingInputBlake3").and_then(|v| v.as_str()) {
            if want != b3 {
                problems.push(format!("BLAKE3 {b3} != manifest {want}"));
            }
        }

        let bundle = protocol::read_signature_bundle(&envelope);
        let verified = bundle
            .as_ref()
            .map(|b| crypto::verify(&b.alg, &b.pubkey, &sig_input, &b.sig))
            .unwrap_or(false);
        let expected_verify = msg.get("expectedVerify").and_then(|v| v.as_bool()).unwrap_or(true);
        if verified != expected_verify {
            problems.push(format!("signature verify={verified}, expected {expected_verify}"));
        }
        if let (Some(b), Some(want_alg)) = (&bundle, msg.get("alg").and_then(|v| v.as_str())) {
            if b.alg != want_alg {
                problems.push(format!("alg {} != manifest {want_alg}", b.alg));
            }
        }
        if protocol::verify_envelope(&envelope) != verified {
            problems.push("verify_envelope disagrees with manual verification".into());
        }

        if problems.is_empty() {
            report.passed += 1;
        } else {
            report.failed += 1;
            report.findings.push(format!("[{id}/{encoding}] {}", problems.join("; ")));
        }
    }
    report
}
