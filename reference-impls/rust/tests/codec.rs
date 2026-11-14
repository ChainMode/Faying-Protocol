// Reference Implementation, Not Normative — for conformance testing only.
//
// Integration tests for the Rust reference codec. Run with `cargo test`.

use faying_ref::crypto::{generate_keypair, sign, verify, Alg};
use faying_ref::detcbor::{decode, encode, Value};
use faying_ref::dimensions::run_all_dimensions;
use faying_ref::hash::{compute_hash, Hash};
use faying_ref::negotiation::negotiate;
use faying_ref::protocol::{signing_input_hash, verify_envelope};
use faying_ref::vectors::vectors_dir;
use std::fs;

#[test]
fn deterministic_cbor_sorts_keys_bytewise() {
    let m = Value::Map(vec![
        ("z".into(), Value::Int(1)),
        ("aa".into(), Value::Int(2)),
        ("b".into(), Value::Int(3)),
    ]);
    // Keys ordered by encoded bytes → b, z, aa.
    assert_eq!(hex::encode(encode(&m)), "a3616203617a0162616102");
}

#[test]
fn round_trips_encoding_equivalence_corpus_byte_for_byte() {
    for id in [
        "01-bootstrap",
        "02-presence",
        "03-grade-switch",
        "04-delegate",
        "05-revoke",
    ] {
        let dir = vectors_dir().join("encoding-equivalence").join(id);
        let cbor = fs::read(dir.join("message.cbor")).unwrap();
        let obj = decode(&cbor).unwrap();
        assert_eq!(
            hex::encode(encode(&obj)),
            hex::encode(&cbor),
            "{id} canonical re-encode must reproduce on-disk bytes"
        );
        let stored_hash = fs::read_to_string(dir.join("signature.input.hash.hex"))
            .unwrap()
            .trim()
            .to_string();
        assert_eq!(signing_input_hash(&obj), stored_hash, "{id} signing-input hash");
        assert!(verify_envelope(&obj), "{id} envelope signature verifies");
    }
}

#[test]
fn tag0_survives_round_trip() {
    let m = Value::Map(vec![("t".into(), Value::Tag0("2026-01-01T00:00:00Z".into()))]);
    let back = decode(&encode(&m)).unwrap();
    assert_eq!(back.get("t"), Some(&Value::Tag0("2026-01-01T00:00:00Z".into())));
}

#[test]
fn sign_verify_roundtrip_all_algorithms() {
    for alg in [Alg::Ed25519, Alg::Es256, Alg::MlDsa65] {
        let kp = generate_keypair(alg, &[7u8; 32]);
        let msg = b"interop message";
        let sig = sign(&kp, msg, "test");
        assert!(verify(alg.wire(), &kp.public_key, msg, &sig), "{} verifies", alg.wire());
        assert!(
            !verify(alg.wire(), &kp.public_key, b"other", &sig),
            "{} rejects tamper",
            alg.wire()
        );
    }
}

#[test]
fn both_hashes_produce_32_byte_digests() {
    let input = b"signing input";
    assert_eq!(compute_hash(Hash::Sha256, input).len(), 32);
    assert_eq!(compute_hash(Hash::Blake3, input).len(), 32);
}

#[test]
fn negotiation_strongest_and_disjoint() {
    assert_eq!(
        negotiate(&["Ed25519", "ML-DSA-65"], &["ES256", "ML-DSA-65"]).unwrap(),
        Alg::MlDsa65
    );
    assert_eq!(
        negotiate(&["Ed25519", "ES256", "ML-DSA-65"], &["Ed25519", "ES256"]).unwrap(),
        Alg::Ed25519
    );
    assert!(negotiate(&["Ed25519"], &["RSA"]).is_err());
}

#[test]
fn all_dimensions_pass_over_corpus() {
    for r in run_all_dimensions() {
        assert_eq!(r.failed, 0, "{}: {}", r.name, r.findings.join("; "));
        assert!(r.total > 0, "{} ran at least one check", r.name);
    }
}
