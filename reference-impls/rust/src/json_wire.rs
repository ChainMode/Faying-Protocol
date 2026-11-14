// Reference Implementation, Not Normative — for conformance testing only.
//
// JSON wire-form ⟷ value-model conversion for the
// `application/faying-protocol+json` fallback encoding (design.md §5.1).
// Mirrors conformance/dim_encoding/normalize.py and the TS json_wire.ts.
//
// Recognised JSON conventions:
//   * binary markers: {"$bytes": b64u|hex}, {"$b64u": ...}, {"$b64": ...}
//   * tag-0 markers:  {"$tag": 0, "$value": str} | {"$tag": 0, "value": str}
//   * path-keyed bare-string binary fields (encoding-equivalence vectors).

use crate::detcbor::Value;
use base64::Engine;
use serde_json::Value as Json;
use std::collections::HashSet;

fn b64u_decode(s: &str) -> Result<Vec<u8>, String> {
    base64::engine::general_purpose::URL_SAFE_NO_PAD
        .decode(s.trim_end_matches('='))
        .map_err(|e| format!("base64url decode failed: {e}"))
}

fn b64_decode(s: &str) -> Result<Vec<u8>, String> {
    base64::engine::general_purpose::STANDARD_NO_PAD
        .decode(s.trim_end_matches('='))
        .map_err(|e| format!("base64 decode failed: {e}"))
}

fn is_hex(s: &str) -> bool {
    !s.is_empty() && s.len() % 2 == 0 && s.chars().all(|c| c.is_ascii_hexdigit())
}

fn decode_bytes_marker(marker: &str, value: &str) -> Result<Vec<u8>, String> {
    match marker {
        "$bytes" => {
            if is_hex(value) {
                hex::decode(value).map_err(|e| format!("hex decode failed: {e}"))
            } else {
                b64u_decode(value)
            }
        }
        "$b64u" => b64u_decode(value),
        "$b64" => b64_decode(value),
        _ => Err(format!("unknown binary marker {marker}")),
    }
}

fn detect_binary_marker(obj: &serde_json::Map<String, Json>) -> Option<&'static str> {
    if obj.len() != 1 {
        return None;
    }
    let k = obj.keys().next().unwrap().as_str();
    match k {
        "$bytes" => Some("$bytes"),
        "$b64u" => Some("$b64u"),
        "$b64" => Some("$b64"),
        _ => None,
    }
}

fn tag0_marker(obj: &serde_json::Map<String, Json>) -> Option<String> {
    if obj.len() != 2 {
        return None;
    }
    let tag_is_zero = matches!(obj.get("$tag"), Some(Json::Number(n)) if n.as_i64() == Some(0));
    if !tag_is_zero {
        return None;
    }
    if let Some(Json::String(s)) = obj.get("$value") {
        return Some(s.clone());
    }
    if let Some(Json::String(s)) = obj.get("value") {
        return Some(s.clone());
    }
    None
}

/// Convert a parsed JSON tree into the CBOR value model.
pub fn json_to_value(obj: &Json, binary_paths: &[String]) -> Result<Value, String> {
    let set: HashSet<&str> = binary_paths.iter().map(|s| s.as_str()).collect();
    walk(obj, &mut Vec::new(), &set)
}

fn walk(obj: &Json, path: &mut Vec<String>, binary_paths: &HashSet<&str>) -> Result<Value, String> {
    match obj {
        Json::Null => Ok(Value::Null),
        Json::Bool(b) => Ok(Value::Bool(*b)),
        Json::Number(n) => {
            if let Some(i) = n.as_i64() {
                Ok(Value::Int(i as i128))
            } else if let Some(u) = n.as_u64() {
                Ok(Value::Int(u as i128))
            } else {
                Err(format!("json_wire: non-integer number {n}"))
            }
        }
        Json::String(s) => {
            let joined = path.join(".");
            if binary_paths.contains(joined.as_str()) {
                Ok(Value::Bytes(b64u_decode(s)?))
            } else {
                Ok(Value::Text(s.clone()))
            }
        }
        Json::Array(items) => {
            let mut out = Vec::with_capacity(items.len());
            for item in items {
                out.push(walk(item, path, binary_paths)?);
            }
            Ok(Value::Array(out))
        }
        Json::Object(map) => {
            if let Some(marker) = detect_binary_marker(map) {
                let inner = map.values().next().unwrap();
                if let Json::String(s) = inner {
                    return Ok(Value::Bytes(decode_bytes_marker(marker, s)?));
                }
                return Err(format!("binary marker {marker} expects string"));
            }
            if let Some(ts) = tag0_marker(map) {
                return Ok(Value::Tag0(ts));
            }
            let mut entries = Vec::with_capacity(map.len());
            for (k, v) in map {
                path.push(k.clone());
                let val = walk(v, path, binary_paths)?;
                path.pop();
                entries.push((k.clone(), val));
            }
            Ok(Value::Map(entries))
        }
    }
}

/// Serialize a value model into JSON wire form (markers for bytes / tag-0).
pub fn value_to_json(value: &Value) -> Json {
    match value {
        Value::Null => Json::Null,
        Value::Bool(b) => Json::Bool(*b),
        Value::Int(i) => Json::Number(serde_json::Number::from(*i as i64)),
        Value::Text(s) => Json::String(s.clone()),
        Value::Bytes(b) => {
            let mut m = serde_json::Map::new();
            m.insert(
                "$bytes".to_string(),
                Json::String(base64::engine::general_purpose::URL_SAFE_NO_PAD.encode(b)),
            );
            Json::Object(m)
        }
        Value::Tag0(s) => {
            let mut m = serde_json::Map::new();
            m.insert("$tag".to_string(), Json::Number(serde_json::Number::from(0)));
            m.insert("$value".to_string(), Json::String(s.clone()));
            Json::Object(m)
        }
        Value::Array(items) => Json::Array(items.iter().map(value_to_json).collect()),
        Value::Map(entries) => {
            let mut m = serde_json::Map::new();
            for (k, v) in entries {
                m.insert(k.clone(), value_to_json(v));
            }
            Json::Object(m)
        }
    }
}
