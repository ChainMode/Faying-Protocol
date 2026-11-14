// Reference Implementation, Not Normative — for conformance testing only.
//
// Deterministic CBOR (RFC 8949 §4.2.1 "Core Deterministic Encoding") codec.
//
// Why hand-rolled instead of ciborium's serde path?
// --------------------------------------------------
// The Faying Protocol/1.0 signature input is `Deterministic-CBOR(envelope
// without signature)` (design.md §6.3), and the official `vectors/` corpus is
// produced by Python's `cbor2.dumps(obj, canonical=True)`. To interoperate
// byte-for-byte (with that corpus AND with the TypeScript reference impl),
// every implementation must agree on the EXACT canonical bytes. ciborium does
// not sort map keys per RFC 8949 §4.2.1 (it preserves insertion order) and
// collapses CBOR tag 0 timestamps, so we carry our own small, fully-controlled
// codec for the canonical path. ciborium is still used (see `cbor.rs`) as an
// independent third-party decoder to cross-check well-formedness.
//
// Canonical rules implemented here (RFC 8949 §4.2.1):
//   * integers use the shortest possible encoding;
//   * map keys are sorted by their *encoded bytes* in bytewise lexicographic
//     order (matches cbor2 canonical=True and the TS detcbor.ts);
//   * definite-length encoding only;
//   * tag 0 (RFC 3339 date/time string) is preserved exactly.

use std::collections::BTreeMap;

/// The value model produced by `decode` and consumed by `encode`.
///
/// Map keys are always text strings in the protocol wire form. We keep a
/// `Vec<(String, Value)>` rather than a map type so decode preserves the
/// on-disk order for round-trip fidelity; the encoder re-sorts canonically.
#[derive(Debug, Clone, PartialEq)]
pub enum Value {
    Null,
    Bool(bool),
    /// Unsigned and negative integers; the protocol uses no floats on the wire.
    Int(i128),
    Text(String),
    Bytes(Vec<u8>),
    /// CBOR tag 0 (RFC 3339 date/time string), preserved verbatim.
    Tag0(String),
    Array(Vec<Value>),
    Map(Vec<(String, Value)>),
}

impl Value {
    /// Look up a key in a `Map` value.
    pub fn get(&self, key: &str) -> Option<&Value> {
        match self {
            Value::Map(entries) => entries.iter().find(|(k, _)| k == key).map(|(_, v)| v),
            _ => None,
        }
    }

    pub fn as_text(&self) -> Option<&str> {
        match self {
            Value::Text(s) => Some(s),
            _ => None,
        }
    }

    pub fn as_bytes(&self) -> Option<&[u8]> {
        match self {
            Value::Bytes(b) => Some(b),
            _ => None,
        }
    }

    pub fn as_int(&self) -> Option<i128> {
        match self {
            Value::Int(i) => Some(*i),
            _ => None,
        }
    }

    pub fn is_map(&self) -> bool {
        matches!(self, Value::Map(_))
    }

    /// Return a clone of this value with any top-level `signature` field removed.
    pub fn without_signature(&self) -> Value {
        match self {
            Value::Map(entries) => Value::Map(
                entries
                    .iter()
                    .filter(|(k, _)| k != "signature")
                    .cloned()
                    .collect(),
            ),
            other => other.clone(),
        }
    }
}

// ---------------------------------------------------------------------------
// Encoder
// ---------------------------------------------------------------------------

fn push_head(out: &mut Vec<u8>, major: u8, value: u64) {
    let mt = major << 5;
    if value < 24 {
        out.push(mt | value as u8);
    } else if value < 0x100 {
        out.push(mt | 24);
        out.push(value as u8);
    } else if value < 0x1_0000 {
        out.push(mt | 25);
        out.extend_from_slice(&(value as u16).to_be_bytes());
    } else if value < 0x1_0000_0000 {
        out.push(mt | 26);
        out.extend_from_slice(&(value as u32).to_be_bytes());
    } else {
        out.push(mt | 27);
        out.extend_from_slice(&value.to_be_bytes());
    }
}

fn encode_into(out: &mut Vec<u8>, v: &Value) {
    match v {
        Value::Null => out.push(0xf6),
        Value::Bool(false) => out.push(0xf4),
        Value::Bool(true) => out.push(0xf5),
        Value::Int(i) => {
            if *i >= 0 {
                push_head(out, 0, *i as u64);
            } else {
                push_head(out, 1, (-1 - *i) as u64);
            }
        }
        Value::Text(s) => {
            let bytes = s.as_bytes();
            push_head(out, 3, bytes.len() as u64);
            out.extend_from_slice(bytes);
        }
        Value::Bytes(b) => {
            push_head(out, 2, b.len() as u64);
            out.extend_from_slice(b);
        }
        Value::Tag0(s) => {
            push_head(out, 6, 0);
            encode_into(out, &Value::Text(s.clone()));
        }
        Value::Array(items) => {
            push_head(out, 4, items.len() as u64);
            for item in items {
                encode_into(out, item);
            }
        }
        Value::Map(entries) => {
            // Canonical key ordering: encode each key, sort by encoded bytes.
            let mut encoded: BTreeMap<Vec<u8>, &Value> = BTreeMap::new();
            for (k, val) in entries {
                let mut kb = Vec::new();
                encode_into(&mut kb, &Value::Text(k.clone()));
                encoded.insert(kb, val);
            }
            push_head(out, 5, encoded.len() as u64);
            for (kb, val) in &encoded {
                out.extend_from_slice(kb);
                encode_into(out, val);
            }
        }
    }
}

/// Encode a value model into deterministic CBOR bytes (RFC 8949 §4.2.1).
pub fn encode(value: &Value) -> Vec<u8> {
    let mut out = Vec::new();
    encode_into(&mut out, value);
    out
}

// ---------------------------------------------------------------------------
// Decoder
// ---------------------------------------------------------------------------

struct Reader<'a> {
    buf: &'a [u8],
    pos: usize,
}

impl<'a> Reader<'a> {
    fn byte(&mut self) -> Result<u8, String> {
        if self.pos >= self.buf.len() {
            return Err("detcbor: unexpected end of input".into());
        }
        let b = self.buf[self.pos];
        self.pos += 1;
        Ok(b)
    }

    fn bytes(&mut self, n: usize) -> Result<&'a [u8], String> {
        if self.pos + n > self.buf.len() {
            return Err("detcbor: unexpected end of input".into());
        }
        let slice = &self.buf[self.pos..self.pos + n];
        self.pos += n;
        Ok(slice)
    }
}

fn read_arg(r: &mut Reader, info: u8) -> Result<u64, String> {
    match info {
        0..=23 => Ok(info as u64),
        24 => Ok(r.byte()? as u64),
        25 => {
            let b = r.bytes(2)?;
            Ok(u16::from_be_bytes([b[0], b[1]]) as u64)
        }
        26 => {
            let b = r.bytes(4)?;
            Ok(u32::from_be_bytes([b[0], b[1], b[2], b[3]]) as u64)
        }
        27 => {
            let b = r.bytes(8)?;
            let mut arr = [0u8; 8];
            arr.copy_from_slice(b);
            Ok(u64::from_be_bytes(arr))
        }
        _ => Err(format!(
            "detcbor: unsupported additional info {info} (indefinite-length not allowed)"
        )),
    }
}

fn decode_from(r: &mut Reader) -> Result<Value, String> {
    let initial = r.byte()?;
    let major = initial >> 5;
    let info = initial & 0x1f;
    match major {
        0 => Ok(Value::Int(read_arg(r, info)? as i128)),
        1 => Ok(Value::Int(-1 - read_arg(r, info)? as i128)),
        2 => {
            let len = read_arg(r, info)? as usize;
            Ok(Value::Bytes(r.bytes(len)?.to_vec()))
        }
        3 => {
            let len = read_arg(r, info)? as usize;
            let s = std::str::from_utf8(r.bytes(len)?)
                .map_err(|e| format!("detcbor: invalid utf-8 text string: {e}"))?;
            Ok(Value::Text(s.to_string()))
        }
        4 => {
            let len = read_arg(r, info)? as usize;
            let mut arr = Vec::with_capacity(len);
            for _ in 0..len {
                arr.push(decode_from(r)?);
            }
            Ok(Value::Array(arr))
        }
        5 => {
            let len = read_arg(r, info)? as usize;
            let mut entries = Vec::with_capacity(len);
            for _ in 0..len {
                let k = decode_from(r)?;
                let key = match k {
                    Value::Text(s) => s,
                    _ => return Err("detcbor: only text-string map keys are supported".into()),
                };
                let v = decode_from(r)?;
                entries.push((key, v));
            }
            Ok(Value::Map(entries))
        }
        6 => {
            let tag = read_arg(r, info)?;
            let inner = decode_from(r)?;
            if tag == 0 {
                match inner {
                    Value::Text(s) => Ok(Value::Tag0(s)),
                    _ => Err("detcbor: tag 0 must wrap a text string".into()),
                }
            } else {
                Err(format!("detcbor: unsupported tag {tag}"))
            }
        }
        7 => match info {
            20 => Ok(Value::Bool(false)),
            21 => Ok(Value::Bool(true)),
            22 => Ok(Value::Null),
            _ => Err(format!("detcbor: unsupported simple/float value {info}")),
        },
        _ => Err(format!("detcbor: unsupported major type {major}")),
    }
}

/// Decode deterministic CBOR bytes into the value model.
pub fn decode(buf: &[u8]) -> Result<Value, String> {
    let mut r = Reader { buf, pos: 0 };
    decode_from(&mut r)
}
