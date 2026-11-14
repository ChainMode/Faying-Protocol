// Reference Implementation, Not Normative — for conformance testing only.
//
// Algorithm-suite negotiation (Requirement 8.1 / 8.2). Mirrors
// conformance/dim_signing/negotiation.py exactly:
//   strength order = ML-DSA-65 > Ed25519 > ES256
//   empty intersection → E_PROTOCOL (1099)

import { normalizeAlg, type Alg } from "./crypto.ts";

export const NEGOTIATION_ORDER: readonly Alg[] = ["ML-DSA-65", "Ed25519", "ES256"];
export const MANDATORY_BASELINE: ReadonlySet<Alg> = new Set<Alg>(["Ed25519", "ES256"]);

export class NegotiationError extends Error {
  readonly errorName = "E_PROTOCOL";
  readonly errorCode = 1099;
}

function normalizeSet(algs: Iterable<string>): Set<Alg> {
  const out = new Set<Alg>();
  for (const a of algs) {
    try {
      out.add(normalizeAlg(a));
    } catch {
      // Unrecognised algorithm cannot be in any intersection.
    }
  }
  return out;
}

export function negotiate(clientSupports: Iterable<string>, serverSupports: Iterable<string>): Alg {
  const client = normalizeSet(clientSupports);
  const server = normalizeSet(serverSupports);
  const intersection = new Set([...client].filter((a) => server.has(a)));
  if (intersection.size === 0) {
    throw new NegotiationError(
      `E_PROTOCOL: no common signing algorithm between ${[...client]} and ${[...server]}`,
    );
  }
  for (const alg of NEGOTIATION_ORDER) {
    if (intersection.has(alg)) return alg;
  }
  throw new NegotiationError("E_PROTOCOL: intersection outside NEGOTIATION_ORDER");
}
