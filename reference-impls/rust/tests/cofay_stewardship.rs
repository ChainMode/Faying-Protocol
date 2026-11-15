// Reference Implementation, Not Normative — for conformance testing only.

use faying_ref::cofay_stewardship::{
    negotiate_protocol_version, verify_stewardship_mandate, verify_transfer_authorization,
    StewardshipOutcome, TransferOutcome,
};
use serde_json::Value;
use std::fs;
use std::path::PathBuf;

#[test]
fn verifies_all_cofay_stewardship_v1_1_vectors() {
    let manifest_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    let vectors_path = manifest_dir.join("../../vectors/cofay-stewardship-v1.1.json");
    let raw = fs::read_to_string(&vectors_path).expect("read cofay-stewardship-v1.1.json");
    let corpus: Value = serde_json::from_str(&raw).expect("parse corpus JSON");

    assert_eq!(
        corpus.get("version").and_then(|v| v.as_str()),
        Some("Faying Protocol/1.1")
    );
    let vectors = corpus
        .get("vectors")
        .and_then(|v| v.as_array())
        .expect("vectors array");
    assert_eq!(vectors.len(), 10);

    for vec_entry in vectors {
        let id = vec_entry.get("id").and_then(|v| v.as_str()).unwrap();
        let kind = vec_entry.get("kind").and_then(|v| v.as_str()).unwrap();
        let eval_at = vec_entry
            .get("evaluated_at")
            .and_then(|v| v.as_str())
            .unwrap();
        let payload = vec_entry.get("payload").unwrap();
        let expected = vec_entry.get("expected").unwrap();
        let expected_valid = expected.get("valid").and_then(|v| v.as_bool()).unwrap();

        if kind == "stewardship" {
            let upstream = vec_entry
                .get("upstream_state")
                .and_then(|v| v.as_str())
                .unwrap_or("Active");
            let outcome = verify_stewardship_mandate(payload, eval_at, upstream);
            match outcome {
                StewardshipOutcome::Valid {
                    runtime_state,
                    accountable_human_prime,
                    effective_grade,
                } => {
                    assert!(expected_valid, "vector {id} expected rejection, got valid");
                    assert_eq!(
                        Some(runtime_state),
                        expected.get("runtime_state").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(accountable_human_prime.as_str()),
                        expected
                            .get("accountable_human_prime")
                            .and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(effective_grade),
                        expected.get("effective_grade").and_then(|v| v.as_i64()),
                        "vector {id}"
                    );
                }
                StewardshipOutcome::Rejected {
                    runtime_state,
                    error_code,
                    error_name,
                    ..
                } => {
                    assert!(!expected_valid, "vector {id} expected valid, got rejected");
                    assert_eq!(
                        Some(runtime_state),
                        expected.get("runtime_state").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(error_code as u64),
                        expected.get("error_code").and_then(|v| v.as_u64()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(error_name),
                        expected.get("error_name").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                }
            }
        } else {
            let outcome = verify_transfer_authorization(payload, eval_at);
            match outcome {
                TransferOutcome::Valid {
                    active_steward,
                    accountable_human_prime,
                    next_manager_fay_id,
                } => {
                    assert!(expected_valid, "vector {id} expected rejection, got valid");
                    assert_eq!(
                        Some(active_steward.as_str()),
                        expected.get("active_steward").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(accountable_human_prime.as_str()),
                        expected
                            .get("accountable_human_prime")
                            .and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(next_manager_fay_id.as_str()),
                        expected.get("next_manager_fay_id").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                }
                TransferOutcome::Rejected {
                    error_code,
                    error_name,
                    ..
                } => {
                    assert!(!expected_valid, "vector {id} expected valid, got rejected");
                    assert_eq!(
                        Some(error_code as u64),
                        expected.get("error_code").and_then(|v| v.as_u64()),
                        "vector {id}"
                    );
                    assert_eq!(
                        Some(error_name),
                        expected.get("error_name").and_then(|v| v.as_str()),
                        "vector {id}"
                    );
                }
            }
        }
    }
}

#[test]
fn negotiates_protocol_version_per_1_7_3() {
    assert_eq!(
        negotiate_protocol_version(&["1.0", "1.1"], &["Faying Protocol/1.0"]),
        Ok("Faying Protocol/1.0".to_string())
    );
    assert_eq!(
        negotiate_protocol_version(&["1.0", "1.1"], &["1.0", "1.1"]),
        Ok("Faying Protocol/1.1".to_string())
    );
    assert_eq!(
        negotiate_protocol_version(&["2.0"], &["1.0", "1.1"]),
        Err(1099)
    );
}
