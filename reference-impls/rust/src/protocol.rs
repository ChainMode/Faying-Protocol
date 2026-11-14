// Reference Implementation, Not Normative — for conformance testing only.
//
// Faying Protocol/1.0 envelope model + signing-input construction (Rust side).
//
//     signing_input_bytes = Deterministic-CBOR( Envelope_without_signature )
//     signing_input_hash  = SHA-256( signing_input_bytes )
//
// The bytes feed Ed25519 / ES256 (which apply their own internal hash); the
// hash is the cross-encoding identity digest recorded in the vectors and the
// cross-impl manifest.

use crate::crypto::{self, KeyPair};
use crate::detcbor::{self, Value};
use sha2::{Digest, Sha256};

/// Strip the top-level `signature` field and Det-CBOR encode (the §6.3 input).
pub fn signing_input(value: &Value) -> Vec<u8> {
    detcbor::encode(&value.without_signature())
}

/// SHA-256 of the signing input — the cross-encoding identity digest.
pub fn signing_input_hash(value: &Value) -> String {
    hex::encode(Sha256::digest(signing_input(value)))
}

pub struct SignatureBundle {
    pub alg: String,
    pub pubkey: Vec<u8>,
    pub sig: Vec<u8>,
}

/// Read the outer signature bundle of an envelope, if present.
pub fn read_signature_bundle(value: &Value) -> Option<SignatureBundle> {
    let bundle = value.get("signature")?;
    let alg = bundle.get("alg")?.as_text()?.to_string();
    let pubkey = bundle.get("pubkey")?.as_bytes()?.to_vec();
    let sig = bundle.get("sig")?.as_bytes()?.to_vec();
    Some(SignatureBundle { alg, pubkey, sig })
}

/// Verify the outer signature of an envelope against its §6.3 signing input.
pub fn verify_envelope(value: &Value) -> bool {
    match read_signature_bundle(value) {
        Some(b) => crypto::verify(&b.alg, &b.pubkey, &signing_input(value), &b.sig),
        None => false,
    }
}

/// Attach a freshly computed signature bundle to an unsigned envelope.
pub fn sign_envelope(envelope_no_sig: &Value, kp: &KeyPair, label: &str) -> Value {
    let sig = crypto::sign(kp, &signing_input(envelope_no_sig), label);
    let bundle = Value::Map(vec![
        ("alg".to_string(), Value::Text(kp.alg.wire().to_string())),
        ("pubkey".to_string(), Value::Bytes(kp.public_key.clone())),
        ("sig".to_string(), Value::Bytes(sig)),
    ]);
    let mut entries = match envelope_no_sig {
        Value::Map(e) => e.clone(),
        _ => Vec::new(),
    };
    entries.push(("signature".to_string(), bundle));
    Value::Map(entries)
}

// ---------------------------------------------------------------------------
// Builders for produced interop messages.
// ---------------------------------------------------------------------------

pub struct HeaderInput<'a> {
    pub msg_type: &'a str,
    pub msg_id: &'a str,
    pub issued_at: &'a str,
    pub expiry: &'a str,
    pub nonce: Vec<u8>,
    pub grade: i128,
    pub issuer: &'a str,
    pub subject: &'a str,
}

pub fn build_header(h: &HeaderInput) -> Value {
    Value::Map(vec![
        ("version".into(), Value::Text("Faying Protocol/1.0".into())),
        ("msg_type".into(), Value::Text(h.msg_type.into())),
        ("msg_id".into(), Value::Text(h.msg_id.into())),
        ("issued_at".into(), Value::Tag0(h.issued_at.into())),
        ("expiry".into(), Value::Tag0(h.expiry.into())),
        ("nonce".into(), Value::Bytes(h.nonce.clone())),
        ("grade".into(), Value::Int(h.grade)),
        ("issuer".into(), Value::Text(h.issuer.into())),
        ("subject".into(), Value::Text(h.subject.into())),
    ])
}

pub fn build_attestation(kp: &KeyPair, label: &str) -> Value {
    let payload = format!("faying-attestation-payload:{label}").into_bytes();
    let sig = crypto::sign(kp, &payload, &format!("att-{label}"));
    Value::Map(vec![
        ("format".into(), Value::Text("self-signed".into())),
        ("payload".into(), Value::Bytes(payload)),
        ("signer".into(), Value::Text(format!("hp:ref-{label}"))),
        (
            "signature".into(),
            Value::Map(vec![
                ("alg".into(), Value::Text(kp.alg.wire().to_string())),
                ("pubkey".into(), Value::Bytes(kp.public_key.clone())),
                ("sig".into(), Value::Bytes(sig)),
            ]),
        ),
    ])
}

pub fn build_envelope(header: Value, claims: Value, attestation: Value) -> Value {
    Value::Map(vec![
        ("header".into(), header),
        ("claims".into(), claims),
        ("attestation".into(), attestation),
    ])
}

// ---------------------------------------------------------------------------
// Endorsement convergence (design.md §11 / §7.5).
// ---------------------------------------------------------------------------

const OFFLINE_REVOCATION_POLICIES: [&str; 3] = ["stop-and-audit", "stop-only", "graceful-stop"];

pub fn endorsement_converges(mandate: &Value) -> Result<(), String> {
    let endorsement = match mandate.get("endorsement") {
        Some(e) => e,
        None => return Ok(()),
    };
    if endorsement.get("enabled") != Some(&Value::Bool(true)) {
        return Ok(());
    }

    if let (Some(scope), Some(endorsed)) = (mandate.get("scope"), endorsement.get("endorsed-scope")) {
        for key in ["actions", "domains"] {
            let parent = collect_text_set(scope.get(key));
            if let Some(Value::Array(children)) = endorsed.get(key) {
                for c in children {
                    if let Value::Text(t) = c {
                        if !parent.contains(t.as_str()) {
                            return Err(format!("endorsed_scope.{key} ⊄ scope.{key} ({t})"));
                        }
                    }
                }
            }
        }
    }

    if let (Some(Value::Int(grade)), Some(Value::Int(eg))) =
        (mandate.get("grade"), endorsement.get("endorsed-grade"))
    {
        if eg > grade {
            return Err(format!("endorsed_grade.autonomy > grade.autonomy ({eg} > {grade})"));
        }
    }

    match endorsement.get("endorsed-lifetime-ms") {
        Some(Value::Int(ms)) if *ms > 0 => {}
        _ => return Err("endorsed_lifetime_ms missing/non-finite/non-positive".into()),
    }

    match endorsement.get("offline-revocation-policy") {
        Some(Value::Text(p)) if OFFLINE_REVOCATION_POLICIES.contains(&p.as_str()) => {}
        other => return Err(format!("offline_revocation_policy invalid: {other:?}")),
    }
    Ok(())
}

fn collect_text_set(v: Option<&Value>) -> std::collections::HashSet<String> {
    let mut set = std::collections::HashSet::new();
    if let Some(Value::Array(items)) = v {
        for item in items {
            if let Value::Text(t) = item {
                set.insert(t.clone());
            }
        }
    }
    set
}

/// Decode CBOR wire bytes into the envelope value model.
pub fn decode_cbor(buf: &[u8]) -> Result<Value, String> {
    detcbor::decode(buf)
}

/// Encode an envelope value model into deterministic CBOR wire bytes.
pub fn encode_cbor(value: &Value) -> Vec<u8> {
    detcbor::encode(value)
}
