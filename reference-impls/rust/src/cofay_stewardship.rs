// Reference Implementation, Not Normative — for conformance testing only.
//
// Faying Protocol/1.1 coFay Delegated Stewardship Profile & Atomic Dual-Signed
// Stewardship Transfer verifier for the Rust reference implementation.
// Mirrors `reference-impls/typescript/src/cofay_stewardship.ts` byte-for-byte
// on RFC 8785 JCS signing inputs and error codes.

use crate::crypto::verify;
use serde_json::Value;

pub const STEWARDSHIP_SIGNING_DOMAIN: &str = "ifay.faying.cofay-stewardship.v1:";
pub const TRANSFER_SIGNING_DOMAIN: &str = "ifay.faying.cofay-transfer.v1:";

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum StewardshipOutcome {
    Valid {
        runtime_state: &'static str,
        accountable_human_prime: String,
        effective_grade: i64,
    },
    Rejected {
        runtime_state: &'static str,
        error_code: u32,
        error_name: &'static str,
        reason: String,
    },
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum TransferOutcome {
    Valid {
        active_steward: String,
        accountable_human_prime: String,
        next_manager_fay_id: String,
    },
    Rejected {
        error_code: u32,
        error_name: &'static str,
        reason: String,
    },
}

/// RFC 8785 JCS deterministic serializer over `serde_json::Value`.
pub fn canonicalize_jcs(value: &Value) -> Result<String, String> {
    match value {
        Value::Null => Ok("null".to_string()),
        Value::Bool(b) => Ok(if *b { "true" } else { "false" }.to_string()),
        Value::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(i.to_string())
            } else if let Some(u) = n.as_u64() {
                Ok(u.to_string())
            } else if let Some(f) = n.as_f64() {
                if !f.is_finite() {
                    return Err("non-finite float in JCS".into());
                }
                if f == 0.0 {
                    Ok("0".to_string())
                } else {
                    serde_json::to_string(&f).map_err(|e| e.to_string())
                }
            } else {
                Err("unsupported JSON number".into())
            }
        }
        Value::String(s) => serde_json::to_string(s).map_err(|e| e.to_string()),
        Value::Array(arr) => {
            let mut parts = Vec::with_capacity(arr.len());
            for item in arr {
                parts.push(canonicalize_jcs(item)?);
            }
            Ok(format!("[{}]", parts.join(",")))
        }
        Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let mut parts = Vec::with_capacity(keys.len());
            for k in keys {
                let key_json = serde_json::to_string(k).map_err(|e| e.to_string())?;
                let val_json = canonicalize_jcs(&map[k])?;
                parts.push(format!("{key_json}:{val_json}"));
            }
            Ok(format!("{{{}}}", parts.join(",")))
        }
    }
}

fn match_prefixed_id(s: &str, prefix: &str) -> bool {
    let Some(rest) = s.strip_prefix(prefix) else {
        return false;
    };
    if rest.len() < 3 || rest.len() > 64 {
        return false;
    }
    let mut chars = rest.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    if !(first.is_ascii_lowercase() || first.is_ascii_digit()) {
        return false;
    }
    chars.all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '_' || c == '-')
}

fn is_hp_id(s: &str) -> bool {
    match_prefixed_id(s, "hp_")
}

fn is_steward_id(s: &str) -> bool {
    match_prefixed_id(s, "hp_") || match_prefixed_id(s, "org_")
}

fn is_ifay_id(s: &str) -> bool {
    match_prefixed_id(s, "ifay_")
}

fn is_cofay_id(s: &str) -> bool {
    match_prefixed_id(s, "cofay_")
}

/// Strict RFC 3339 UTC (`YYYY-MM-DDTHH:MM:SSZ`) lexicographical-comparable timestamp parser.
fn parse_utc_iso_key(s: &str) -> Option<i128> {
    if s.len() != 20 {
        return None;
    }
    let b = s.as_bytes();
    if b[4] != b'-' || b[7] != b'-' || b[10] != b'T' || b[13] != b':' || b[16] != b':' || b[19] != b'Z' {
        return None;
    }
    let year: i128 = s[0..4].parse().ok()?;
    let month: i128 = s[5..7].parse().ok()?;
    let day: i128 = s[8..10].parse().ok()?;
    let hour: i128 = s[11..13].parse().ok()?;
    let min: i128 = s[14..16].parse().ok()?;
    let sec: i128 = s[17..19].parse().ok()?;
    if !(1..=12).contains(&month)
        || !(1..=31).contains(&day)
        || !(0..=23).contains(&hour)
        || !(0..=59).contains(&min)
        || !(0..=59).contains(&sec)
    {
        return None;
    }
    Some(
        ((((year * 100 + month) * 100 + day) * 100 + hour) * 100 + min) * 100 + sec,
    )
}

fn str_list(val: Option<&Value>) -> Option<Vec<String>> {
    let arr = val?.as_array()?;
    let mut out = Vec::with_capacity(arr.len());
    for v in arr {
        let s = v.as_str()?;
        if s.is_empty() {
            return None;
        }
        out.push(s.to_string());
    }
    Some(out)
}

fn is_subset(sub: &[String], sup: &[String]) -> bool {
    if sub.is_empty() {
        return false;
    }
    sub.iter().all(|item| sup.contains(item))
}

fn is_scope_within(target: &Value, bound: &Value) -> bool {
    let Some(t_domains) = str_list(target.get("domains")) else {
        return false;
    };
    let Some(t_actions) = str_list(target.get("actions")) else {
        return false;
    };
    let Some(b_domains) = str_list(bound.get("domains")) else {
        return false;
    };
    let Some(b_actions) = str_list(bound.get("actions")) else {
        return false;
    };
    if !is_subset(&t_domains, &b_domains) || !is_subset(&t_actions, &b_actions) {
        return false;
    }
    if let Some(b_terms) = str_list(bound.get("terminals")) {
        if !b_terms.is_empty() {
            let Some(t_terms) = str_list(target.get("terminals")) else {
                return false;
            };
            if !is_subset(&t_terms, &b_terms) {
                return false;
            }
        }
    }
    if let Some(b_budget) = bound.get("budget").and_then(|v| v.as_object()) {
        let t_budget = target.get("budget").and_then(|v| v.as_object());
        if let Some(b_max_inv) = b_budget.get("max_invocations").and_then(|v| v.as_i64()) {
            let Some(t_max_inv) = t_budget
                .and_then(|tb| tb.get("max_invocations"))
                .and_then(|v| v.as_i64())
            else {
                return false;
            };
            if t_max_inv < 1 || t_max_inv > b_max_inv {
                return false;
            }
        }
        if let Some(b_max_cost) = b_budget.get("max_cost_units").and_then(|v| v.as_i64()) {
            let Some(t_max_cost) = t_budget
                .and_then(|tb| tb.get("max_cost_units"))
                .and_then(|v| v.as_i64())
            else {
                return false;
            };
            if t_max_cost < 1 || t_max_cost > b_max_cost {
                return false;
            }
        }
    }
    true
}

fn decode_lower_hex(s: &str) -> Option<Vec<u8>> {
    if s.is_empty()
        || !s.len().is_multiple_of(2)
        || !s.chars().all(|c| matches!(c, '0'..='9' | 'a'..='f'))
    {
        return None;
    }
    hex::decode(s).ok()
}

fn verify_sig_bundle(bundle: &Value, msg: &[u8]) -> bool {
    let Some(alg) = bundle.get("alg").and_then(|v| v.as_str()) else {
        return false;
    };
    let Some(pub_hex) = bundle.get("pubkey").and_then(|v| v.as_str()) else {
        return false;
    };
    let Some(sig_hex) = bundle.get("sig").and_then(|v| v.as_str()) else {
        return false;
    };
    let Some(pub_bytes) = decode_lower_hex(pub_hex) else {
        return false;
    };
    let Some(sig_bytes) = decode_lower_hex(sig_hex) else {
        return false;
    };
    verify(alg, &pub_bytes, msg, &sig_bytes)
}

pub fn verify_stewardship_mandate(
    mandate: &Value,
    evaluated_at_iso: &str,
    upstream_state: &str,
) -> StewardshipOutcome {
    let version = mandate.get("version").and_then(|v| v.as_str()).unwrap_or("");
    let profile = mandate.get("profile").and_then(|v| v.as_str()).unwrap_or("");
    if version != "Faying Protocol/1.1" || profile != "cofay-stewardship" {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1099,
            error_name: "E_PROTOCOL",
            reason: "unsupported stewardship version or profile".into(),
        };
    }

    if upstream_state == "G0" || upstream_state == "Revoked" {
        return StewardshipOutcome::Rejected {
            runtime_state: "safe-state-halt",
            error_code: 1024,
            error_name: "E_UPSTREAM_EMERGENCY_HALT",
            reason: format!("upstream manager state {upstream_state} forces immediate safe-state-halt"),
        };
    }

    let steward_entity = mandate.get("steward_entity").and_then(|v| v.as_str()).unwrap_or("");
    let accountable_hp = mandate
        .get("accountable_human_prime")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    if !is_steward_id(steward_entity)
        || !is_hp_id(accountable_hp)
        || (steward_entity.starts_with("hp_") && steward_entity != accountable_hp)
    {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1010,
            error_name: "E_HUMAN_WITNESS_REQUIRED",
            reason: "stewardship chain lacks a valid accountable Human Prime anchor".into(),
        };
    }

    let hop_count = mandate.get("hop_count").and_then(|v| v.as_i64()).unwrap_or(-1);
    let max_hops = mandate
        .get("max_stewardship_hops")
        .and_then(|v| v.as_i64())
        .unwrap_or(-1);
    let manager_id = mandate.get("manager_fay_id").and_then(|v| v.as_str()).unwrap_or("");
    let subject_id = mandate.get("subject_cofay_id").and_then(|v| v.as_str()).unwrap_or("");
    if hop_count != 1 || max_hops != 1 || !is_ifay_id(manager_id) || !is_cofay_id(subject_id) {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1023,
            error_name: "E_STEWARDSHIP_HOP_LIMIT",
            reason: "coFay stewardship requires hop_count == 1 issued by an ifay_* manager to a cofay_* subject".into(),
        };
    }

    if mandate.get("on_upstream_g0").and_then(|v| v.as_str()) != Some("safe-state-halt") {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1099,
            error_name: "E_PROTOCOL",
            reason: "on_upstream_g0 MUST be safe-state-halt".into(),
        };
    }

    let grade = mandate.get("grade").and_then(|v| v.as_i64()).unwrap_or(-1);
    let manager_grade = mandate.get("manager_grade").and_then(|v| v.as_i64()).unwrap_or(-1);
    if !(0..=4).contains(&grade) || !(0..=4).contains(&manager_grade) || grade > manager_grade {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1021,
            error_name: "E_GRADE_AMPLIFICATION",
            reason: format!("stewardship grade {grade} exceeds manager_grade {manager_grade}"),
        };
    }

    let nb = mandate.get("not_before").and_then(|v| v.as_str()).and_then(parse_utc_iso_key);
    let na = mandate.get("not_after").and_then(|v| v.as_str()).and_then(parse_utc_iso_key);
    let mnb = mandate
        .get("manager_not_before")
        .and_then(|v| v.as_str())
        .and_then(parse_utc_iso_key);
    let mna = mandate
        .get("manager_not_after")
        .and_then(|v| v.as_str())
        .and_then(parse_utc_iso_key);
    let eval_ts = parse_utc_iso_key(evaluated_at_iso);
    let scope = mandate.get("scope").unwrap_or(&Value::Null);
    let charter_scope = mandate.get("charter_scope").unwrap_or(&Value::Null);
    let manager_scope = mandate.get("manager_scope").unwrap_or(&Value::Null);

    let time_ok = match (nb, na, mnb, mna, eval_ts) {
        (Some(nb), Some(na), Some(mnb), Some(mna), Some(ev)) => {
            nb < na && nb >= mnb && na <= mna && ev >= nb && ev <= na
        }
        _ => false,
    };
    if !time_ok || !is_scope_within(scope, charter_scope) || !is_scope_within(scope, manager_scope) {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1022,
            error_name: "E_SCOPE_ESCAPE",
            reason: "stewardship scope or validity window escapes charter_scope ∩ manager_scope".into(),
        };
    }

    let Some(sig_bundle) = mandate.get("manager_signature") else {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1003,
            error_name: "E_SIGNATURE_INVALID",
            reason: "missing manager_signature".into(),
        };
    };
    let mut unsigned = mandate.clone();
    if let Some(obj) = unsigned.as_object_mut() {
        obj.remove("manager_signature");
    }
    let Ok(jcs) = canonicalize_jcs(&unsigned) else {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1099,
            error_name: "E_PROTOCOL",
            reason: "failed to canonicalize mandate".into(),
        };
    };
    let msg = format!("{STEWARDSHIP_SIGNING_DOMAIN}{jcs}");
    if !verify_sig_bundle(sig_bundle, msg.as_bytes()) {
        return StewardshipOutcome::Rejected {
            runtime_state: "rejected",
            error_code: 1003,
            error_name: "E_SIGNATURE_INVALID",
            reason: "manager_signature verification failed".into(),
        };
    }

    StewardshipOutcome::Valid {
        runtime_state: "active",
        accountable_human_prime: accountable_hp.to_string(),
        effective_grade: grade,
    }
}

pub fn verify_transfer_authorization(transfer: &Value, evaluated_at_iso: &str) -> TransferOutcome {
    let version = transfer.get("version").and_then(|v| v.as_str()).unwrap_or("");
    let profile = transfer.get("profile").and_then(|v| v.as_str()).unwrap_or("");
    if version != "Faying Protocol/1.1" || profile != "cofay-transfer" {
        return TransferOutcome::Rejected {
            error_code: 1099,
            error_name: "E_PROTOCOL",
            reason: "unsupported transfer version or profile".into(),
        };
    }

    let cofay_id = transfer.get("cofay_id").and_then(|v| v.as_str()).unwrap_or("");
    let from_steward = transfer.get("from_steward").and_then(|v| v.as_str()).unwrap_or("");
    let to_steward = transfer.get("to_steward").and_then(|v| v.as_str()).unwrap_or("");
    let from_hp = transfer.get("from_human_prime").and_then(|v| v.as_str()).unwrap_or("");
    let to_hp = transfer.get("to_human_prime").and_then(|v| v.as_str()).unwrap_or("");
    let next_mgr = transfer
        .get("next_manager_fay_id")
        .and_then(|v| v.as_str())
        .unwrap_or("");
    let nonce = transfer.get("nonce").and_then(|v| v.as_str()).unwrap_or("");
    let issued_ts = transfer
        .get("issued_at")
        .and_then(|v| v.as_str())
        .and_then(parse_utc_iso_key);
    let expires_ts = transfer
        .get("expires_at")
        .and_then(|v| v.as_str())
        .and_then(parse_utc_iso_key);
    let eval_ts = parse_utc_iso_key(evaluated_at_iso);

    let window_ok = match (issued_ts, expires_ts, eval_ts) {
        (Some(i), Some(e), Some(ev)) => i < e && ev >= i && ev <= e,
        _ => false,
    };
    if !is_cofay_id(cofay_id)
        || !is_steward_id(from_steward)
        || !is_steward_id(to_steward)
        || !is_hp_id(from_hp)
        || !is_hp_id(to_hp)
        || !is_ifay_id(next_mgr)
        || from_steward == to_steward
        || nonce.len() < 8
        || !window_ok
    {
        return TransferOutcome::Rejected {
            error_code: 1026,
            error_name: "E_TRANSFER_WINDOW_OR_PARTY_INVALID",
            reason: "invalid transfer party identifiers, self-transfer, or expired transfer window".into(),
        };
    }

    let Some(from_sig) = transfer.get("from_steward_signature") else {
        return TransferOutcome::Rejected {
            error_code: 1025,
            error_name: "E_TRANSFER_DUAL_SIG_REQUIRED",
            reason: "missing from_steward_signature".into(),
        };
    };
    let Some(to_sig) = transfer.get("to_steward_signature") else {
        return TransferOutcome::Rejected {
            error_code: 1025,
            error_name: "E_TRANSFER_DUAL_SIG_REQUIRED",
            reason: "missing to_steward_signature".into(),
        };
    };

    let mut unsigned = transfer.clone();
    if let Some(obj) = unsigned.as_object_mut() {
        obj.remove("from_steward_signature");
        obj.remove("to_steward_signature");
    }
    let Ok(jcs) = canonicalize_jcs(&unsigned) else {
        return TransferOutcome::Rejected {
            error_code: 1099,
            error_name: "E_PROTOCOL",
            reason: "failed to canonicalize transfer".into(),
        };
    };
    let msg = format!("{TRANSFER_SIGNING_DOMAIN}{jcs}");
    if !verify_sig_bundle(from_sig, msg.as_bytes()) || !verify_sig_bundle(to_sig, msg.as_bytes()) {
        return TransferOutcome::Rejected {
            error_code: 1025,
            error_name: "E_TRANSFER_DUAL_SIG_REQUIRED",
            reason: "atomic transfer requires valid cryptographic signatures from both from_steward and to_steward".into(),
        };
    }

    TransferOutcome::Valid {
        active_steward: to_steward.to_string(),
        accountable_human_prime: to_hp.to_string(),
        next_manager_fay_id: next_mgr.to_string(),
    }
}

/// §1.7.3 MAJOR.MINOR protocol version negotiation.
pub fn negotiate_protocol_version(client: &[&str], server: &[&str]) -> Result<String, u32> {
    fn parse_ver(raw: &str) -> Option<(u32, u32)> {
        let trimmed = raw.strip_prefix("Faying Protocol/").unwrap_or(raw);
        let (maj, min) = trimmed.split_once('.')?;
        Some((maj.parse().ok()?, min.parse().ok()?))
    }

    let c_vers: Vec<(u32, u32)> = client.iter().filter_map(|s| parse_ver(s)).collect();
    let mut common: Vec<(u32, u32)> = server
        .iter()
        .filter_map(|s| parse_ver(s))
        .filter(|v| c_vers.contains(v))
        .collect();
    if common.is_empty() {
        return Err(1099);
    }
    common.sort_by(|a, b| b.0.cmp(&a.0).then_with(|| b.1.cmp(&a.1)));
    let (maj, min) = common[0];
    Ok(format!("Faying Protocol/{maj}.{min}"))
}
