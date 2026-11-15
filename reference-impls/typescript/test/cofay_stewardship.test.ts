// Reference Implementation, Not Normative — for conformance testing only.

import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { describe, it } from "node:test";
import { fileURLToPath } from "node:url";
import {
  negotiateProtocolVersion,
  verifyStewardshipMandate,
  verifyTransferAuthorization,
  type CofayStewardshipMandate,
  type CofayTransferAuthorization,
  type UpstreamState,
} from "../src/cofay_stewardship.ts";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const vectorsPath = path.resolve(__dirname, "../../../vectors/cofay-stewardship-v1.1.json");

interface VectorEntry {
  id: string;
  kind: "stewardship" | "transfer";
  evaluated_at: string;
  upstream_state?: UpstreamState;
  payload: CofayStewardshipMandate | CofayTransferAuthorization;
  expected: Record<string, unknown>;
}

describe("Faying Protocol/1.1 coFay Delegated Stewardship & Transfer Vectors", () => {
  const corpus = JSON.parse(fs.readFileSync(vectorsPath, "utf8")) as {
    version: string;
    vectors: VectorEntry[];
  };

  it("loads 10 deterministic v1.1 vectors", () => {
    assert.equal(corpus.version, "Faying Protocol/1.1");
    assert.equal(corpus.vectors.length, 10);
  });

  for (const vec of corpus.vectors) {
    it(`verifies vector ${vec.id}`, () => {
      if (vec.kind === "stewardship") {
        const res = verifyStewardshipMandate(
          vec.payload as CofayStewardshipMandate,
          vec.evaluated_at,
          vec.upstream_state ?? "Active",
        );
        assert.equal(res.valid, vec.expected.valid);
        if (res.valid) {
          assert.equal(res.runtime_state, vec.expected.runtime_state);
          assert.equal(res.accountable_human_prime, vec.expected.accountable_human_prime);
          assert.equal(res.effective_grade, vec.expected.effective_grade);
        } else {
          assert.equal(res.runtime_state, vec.expected.runtime_state);
          assert.equal(res.error_code, vec.expected.error_code);
          assert.equal(res.error_name, vec.expected.error_name);
        }
      } else {
        const res = verifyTransferAuthorization(
          vec.payload as CofayTransferAuthorization,
          vec.evaluated_at,
        );
        assert.equal(res.valid, vec.expected.valid);
        if (res.valid) {
          assert.equal(res.active_steward, vec.expected.active_steward);
          assert.equal(res.accountable_human_prime, vec.expected.accountable_human_prime);
          assert.equal(res.next_manager_fay_id, vec.expected.next_manager_fay_id);
        } else {
          assert.equal(res.error_code, vec.expected.error_code);
          assert.equal(res.error_name, vec.expected.error_name);
        }
      }
    });
  }

  it("negotiates MAJOR.MINOR backward compatibility per §1.7.3", () => {
    assert.equal(
      negotiateProtocolVersion(["1.0", "1.1"], ["Faying Protocol/1.0"]),
      "Faying Protocol/1.0",
    );
    assert.equal(
      negotiateProtocolVersion(["1.0", "1.1"], ["1.0", "1.1"]),
      "Faying Protocol/1.1",
    );
    assert.throws(
      () => negotiateProtocolVersion(["2.0"], ["1.0", "1.1"]),
      /E_PROTOCOL/,
    );
  });
});
