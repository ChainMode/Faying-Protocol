// Reference Implementation, Not Normative — for conformance testing only.
//
// Deterministic CBOR (RFC 8949 §4.2.1 "Core Deterministic Encoding") codec.
//
// Why a hand-rolled codec instead of cbor-x's encoder?
// -----------------------------------------------------
// The Faying Protocol/1.0 signature input is defined (design.md §6.3) as
//
//     signing_input = Deterministic-CBOR( Envelope_without_signature )
//
// and the official `vectors/` corpus is produced by Python's
// `cbor2.dumps(obj, canonical=True)`. To interoperate byte-for-byte with
// that corpus (and with the Rust reference impl, which uses ciborium +
// a canonical re-serialiser), every implementation must agree on the
// *exact bytes* of the deterministic encoding. cbor-x does not sort map
// keys per RFC 8949 §4.2.1, and it collapses CBOR tag 0 timestamps into a
// representation that cannot be re-encoded losslessly. We therefore carry
// our own small, fully-controlled codec for the canonical path.
//
// cbor-x is still used (see `cbor.ts`) as an independent, third-party
// decoder to cross-check that the bytes we emit are well-formed CBOR a
// mainstream library accepts.
//
// Canonical rules implemented here (RFC 8949 §4.2.1):
//   * integers use the shortest possible encoding;
//   * the keys in every map are sorted by their *encoded bytes* in
//     bytewise lexicographic order (this matches cbor2 canonical=True);
//   * definite-length encoding only (no indefinite-length items);
//   * tag 0 (standard date/time string) is preserved exactly.

/** A CBOR tag-0 (RFC 3339 date/time string) value, preserved verbatim. */
export class Tag0 {
  readonly value: string;
  constructor(value: string) {
    this.value = value;
  }
}

/** The value model produced by `decode` and consumed by `encode`. */
export type CborValue =
  | number
  | bigint
  | boolean
  | null
  | string
  | Uint8Array
  | Tag0
  | CborValue[]
  | Map<string, CborValue>;

// ---------------------------------------------------------------------------
// Encoder
// ---------------------------------------------------------------------------

function pushHead(out: number[], major: number, value: number | bigint): void {
  const mt = major << 5;
  const v = typeof value === "bigint" ? value : BigInt(value);
  if (v < 24n) {
    out.push(mt | Number(v));
  } else if (v < 0x100n) {
    out.push(mt | 24, Number(v));
  } else if (v < 0x10000n) {
    const n = Number(v);
    out.push(mt | 25, (n >> 8) & 0xff, n & 0xff);
  } else if (v < 0x100000000n) {
    const n = Number(v);
    out.push(mt | 26, (n >>> 24) & 0xff, (n >>> 16) & 0xff, (n >>> 8) & 0xff, n & 0xff);
  } else {
    out.push(mt | 27);
    for (let shift = 56n; shift >= 0n; shift -= 8n) {
      out.push(Number((v >> shift) & 0xffn));
    }
  }
}

function encodeInto(out: number[], v: CborValue): void {
  if (v === null) {
    out.push(0xf6);
    return;
  }
  if (typeof v === "boolean") {
    out.push(v ? 0xf5 : 0xf4);
    return;
  }
  if (typeof v === "number") {
    if (!Number.isInteger(v)) {
      throw new Error(`detcbor: non-integer numbers are not used by the protocol wire form: ${v}`);
    }
    if (v >= 0) {
      pushHead(out, 0, v);
    } else {
      pushHead(out, 1, -v - 1);
    }
    return;
  }
  if (typeof v === "bigint") {
    if (v >= 0n) {
      pushHead(out, 0, v);
    } else {
      pushHead(out, 1, -v - 1n);
    }
    return;
  }
  if (typeof v === "string") {
    const bytes = new TextEncoder().encode(v);
    pushHead(out, 3, bytes.length);
    for (const b of bytes) out.push(b);
    return;
  }
  if (v instanceof Uint8Array) {
    pushHead(out, 2, v.length);
    for (const b of v) out.push(b);
    return;
  }
  if (v instanceof Tag0) {
    pushHead(out, 6, 0);
    encodeInto(out, v.value);
    return;
  }
  if (Array.isArray(v)) {
    pushHead(out, 4, v.length);
    for (const item of v) encodeInto(out, item);
    return;
  }
  if (v instanceof Map) {
    // Canonical key ordering: encode each key, then sort by encoded bytes.
    const entries: { keyBytes: Uint8Array; value: CborValue }[] = [];
    for (const [k, val] of v) {
      const kb: number[] = [];
      encodeInto(kb, k);
      entries.push({ keyBytes: Uint8Array.from(kb), value: val });
    }
    entries.sort((a, b) => compareBytes(a.keyBytes, b.keyBytes));
    pushHead(out, 5, entries.length);
    for (const e of entries) {
      for (const b of e.keyBytes) out.push(b);
      encodeInto(out, e.value);
    }
    return;
  }
  throw new Error(`detcbor: cannot encode value of type ${Object.prototype.toString.call(v)}`);
}

function compareBytes(a: Uint8Array, b: Uint8Array): number {
  const n = Math.min(a.length, b.length);
  for (let i = 0; i < n; i++) {
    if (a[i] !== b[i]) return a[i] - b[i];
  }
  return a.length - b.length;
}

/** Encode a value model into deterministic CBOR bytes (RFC 8949 §4.2.1). */
export function encode(value: CborValue): Uint8Array {
  const out: number[] = [];
  encodeInto(out, value);
  return Uint8Array.from(out);
}

// ---------------------------------------------------------------------------
// Decoder
// ---------------------------------------------------------------------------

class Reader {
  readonly buf: Uint8Array;
  pos = 0;
  constructor(buf: Uint8Array) {
    this.buf = buf;
  }
  byte(): number {
    if (this.pos >= this.buf.length) throw new Error("detcbor: unexpected end of input");
    return this.buf[this.pos++];
  }
  bytes(n: number): Uint8Array {
    if (this.pos + n > this.buf.length) throw new Error("detcbor: unexpected end of input");
    const slice = this.buf.subarray(this.pos, this.pos + n);
    this.pos += n;
    return slice;
  }
}

function readArg(r: Reader, info: number): bigint {
  if (info < 24) return BigInt(info);
  if (info === 24) return BigInt(r.byte());
  if (info === 25) {
    const b = r.bytes(2);
    return BigInt((b[0] << 8) | b[1]);
  }
  if (info === 26) {
    const b = r.bytes(4);
    return BigInt(((b[0] << 24) >>> 0) + (b[1] << 16) + (b[2] << 8) + b[3]);
  }
  if (info === 27) {
    const b = r.bytes(8);
    let v = 0n;
    for (const x of b) v = (v << 8n) | BigInt(x);
    return v;
  }
  throw new Error(`detcbor: unsupported additional info ${info} (indefinite-length not allowed)`);
}

function bigToNum(v: bigint): number | bigint {
  return v <= BigInt(Number.MAX_SAFE_INTEGER) ? Number(v) : v;
}

function decodeFrom(r: Reader): CborValue {
  const initial = r.byte();
  const major = initial >> 5;
  const info = initial & 0x1f;

  switch (major) {
    case 0:
      return bigToNum(readArg(r, info));
    case 1:
      return bigToNum(-1n - readArg(r, info));
    case 2: {
      const len = Number(readArg(r, info));
      return Uint8Array.from(r.bytes(len));
    }
    case 3: {
      const len = Number(readArg(r, info));
      return new TextDecoder().decode(r.bytes(len));
    }
    case 4: {
      const len = Number(readArg(r, info));
      const arr: CborValue[] = [];
      for (let i = 0; i < len; i++) arr.push(decodeFrom(r));
      return arr;
    }
    case 5: {
      const len = Number(readArg(r, info));
      const m = new Map<string, CborValue>();
      for (let i = 0; i < len; i++) {
        const k = decodeFrom(r);
        if (typeof k !== "string") {
          throw new Error("detcbor: only text-string map keys are used by the protocol");
        }
        m.set(k, decodeFrom(r));
      }
      return m;
    }
    case 6: {
      const tag = Number(readArg(r, info));
      const inner = decodeFrom(r);
      if (tag === 0) {
        if (typeof inner !== "string") throw new Error("detcbor: tag 0 must wrap a text string");
        return new Tag0(inner);
      }
      throw new Error(`detcbor: unsupported tag ${tag}`);
    }
    case 7: {
      if (info === 20) return false;
      if (info === 21) return true;
      if (info === 22) return null;
      throw new Error(`detcbor: unsupported simple/float value ${info}`);
    }
    default:
      throw new Error(`detcbor: unsupported major type ${major}`);
  }
}

/** Decode deterministic CBOR bytes into the value model. */
export function decode(buf: Uint8Array): CborValue {
  const r = new Reader(buf);
  const v = decodeFrom(r);
  return v;
}
