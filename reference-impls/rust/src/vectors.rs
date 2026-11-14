// Reference Implementation, Not Normative — for conformance testing only.
//
// Discovery + loading of the official `vectors/` corpus (tasks 3.x). Both the
// Rust and TypeScript reference impls consume the SAME authoritative vectors
// and `schemas/fap-1.0.cddl` (per task 5.6 conventions). The loader returns
// each signed envelope as a value model ready for signing-input computation
// and verification.

use crate::detcbor::Value;
use crate::json_wire;
use crate::protocol;
use serde_json::Value as Json;
use std::fs;
use std::path::{Path, PathBuf};

const ENVELOPE_BASENAMES: [&str; 16] = [
    "request",
    "disclosure",
    "faying-request",
    "faying_request",
    "envelope",
    "presence",
    "grade-switch",
    "grade_switch",
    "delegate",
    "revoke",
    "error",
    "response",
    "signal",
    "mandate",
    "message",
    "trigger",
];

pub struct LoadedVector {
    pub category: String,
    pub case_name: String,
    pub dir: PathBuf,
    pub envelope_file: PathBuf,
    pub encoding: String,
    pub envelope: Value,
    pub expected: Json,
}

/// Repo root, computed relative to this crate (`reference-impls/rust` → `../..`),
/// preferring runtime `CARGO_MANIFEST_DIR` / `current_dir` discovery over the
/// compile-time path so moving a checkout never breaks cached test binaries.
pub fn repo_root() -> PathBuf {
    if let Some(runtime_manifest) = std::env::var_os("CARGO_MANIFEST_DIR") {
        let p = PathBuf::from(runtime_manifest);
        if let Some(root) = p.parent().and_then(|parent| parent.parent()) {
            if root.join("vectors").is_dir() {
                return root.to_path_buf();
            }
        }
    }
    if let Ok(mut cwd) = std::env::current_dir() {
        loop {
            if cwd.join("vectors").is_dir() && cwd.join("schemas").is_dir() {
                return cwd;
            }
            if !cwd.pop() {
                break;
            }
        }
    }
    let manifest = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    manifest
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .unwrap_or(manifest)
}

pub fn vectors_dir() -> PathBuf {
    repo_root().join("vectors")
}

pub fn schemas_dir() -> PathBuf {
    repo_root().join("schemas")
}

fn find_envelope_file(dir: &Path) -> Option<(PathBuf, String)> {
    for base in ENVELOPE_BASENAMES {
        let cbor = dir.join(format!("{base}.cbor"));
        if cbor.is_file() {
            return Some((cbor, "cbor".to_string()));
        }
        let json = dir.join(format!("{base}.json"));
        if json.is_file() {
            return Some((json, "json".to_string()));
        }
    }
    None
}

fn read_expected(dir: &Path) -> Json {
    let p = dir.join("expected.json");
    if let Ok(text) = fs::read_to_string(&p) {
        if let Ok(j) = serde_json::from_str(&text) {
            return j;
        }
    }
    Json::Null
}

fn binary_paths_from_expected(expected: &Json) -> Vec<String> {
    if let Some(Json::Array(arr)) = expected.get("binary_field_paths") {
        return arr
            .iter()
            .filter_map(|v| v.as_str().map(|s| s.to_string()))
            .collect();
    }
    Vec::new()
}

fn load_envelope(file: &Path, encoding: &str, expected: &Json) -> Result<Value, String> {
    if encoding == "cbor" {
        let bytes = fs::read(file).map_err(|e| format!("read {file:?}: {e}"))?;
        protocol::decode_cbor(&bytes)
    } else {
        let text = fs::read_to_string(file).map_err(|e| format!("read {file:?}: {e}"))?;
        let raw: Json = serde_json::from_str(&text).map_err(|e| format!("json parse: {e}"))?;
        json_wire::json_to_value(&raw, &binary_paths_from_expected(expected))
    }
}

/// Load every vector directory under `vectors/`.
pub fn load_all_vectors() -> Vec<LoadedVector> {
    let mut out = Vec::new();
    let root = vectors_dir();
    let mut cats: Vec<PathBuf> = match fs::read_dir(&root) {
        Ok(rd) => rd
            .filter_map(|e| e.ok().map(|e| e.path()))
            .filter(|p| {
                p.is_dir()
                    && !p
                        .file_name()
                        .and_then(|n| n.to_str())
                        .map(|n| n.starts_with('.') || n.starts_with('_'))
                        .unwrap_or(true)
            })
            .collect(),
        Err(_) => return out,
    };
    cats.sort();
    for cat_dir in cats {
        let category = cat_dir
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("")
            .to_string();
        let mut entries: Vec<PathBuf> = match fs::read_dir(&cat_dir) {
            Ok(rd) => rd
                .filter_map(|e| e.ok().map(|e| e.path()))
                .filter(|p| {
                    p.is_dir()
                        && !p
                            .file_name()
                            .and_then(|n| n.to_str())
                            .map(|n| n.starts_with('.') || n.starts_with('_'))
                            .unwrap_or(true)
                })
                .collect(),
            Err(_) => continue,
        };
        entries.sort();
        for dir in entries {
            if !dir.join("expected.json").is_file() {
                continue;
            }
            let found = match find_envelope_file(&dir) {
                Some(f) => f,
                None => continue,
            };
            let expected = read_expected(&dir);
            let envelope = match load_envelope(&found.0, &found.1, &expected) {
                Ok(e) => e,
                Err(_) => continue,
            };
            let case_name = dir
                .file_name()
                .and_then(|n| n.to_str())
                .unwrap_or("")
                .to_string();
            out.push(LoadedVector {
                category: category.clone(),
                case_name,
                dir: dir.clone(),
                envelope_file: found.0,
                encoding: found.1,
                envelope,
                expected,
            });
        }
    }
    out
}
