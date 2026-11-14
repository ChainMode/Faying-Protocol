// Reference Implementation, Not Normative — for conformance testing only.
//
// CLI for the Faying Protocol/1.0 TypeScript reference implementation.
//
// Usage:
//   node src/cli.ts dims                 Run the 5.2–5.5 dimension matrix.
//   node src/cli.ts produce <outDir>     Produce an interop bundle (CBOR+JSON).
//   node src/cli.ts verify  <inDir>      Verify an interop bundle (e.g. Rust's).
//   node src/cli.ts matrix               Alias for `dims` (human-readable).
//
// Exit code is non-zero if any check fails, so it can gate CI / cross-impl.

import { runAllDimensions } from "./dimensions.ts";
import { produce, verifyBundle } from "./interop.ts";

const BANNER = "Faying Protocol/1.0 — TypeScript Reference Implementation (Not Normative)";

function cmdDims(): number {
  console.log(BANNER);
  console.log("Running data-plane dimensions (tasks 5.2–5.5)\n");
  const results = runAllDimensions();
  let failed = 0;
  for (const r of results) {
    const status = r.failed === 0 ? "PASS" : "FAIL";
    console.log(`  [${status}] ${r.name.padEnd(10)} ${r.passed}/${r.total} passed`);
    if (r.failed > 0) {
      failed += r.failed;
      for (const f of r.findings) console.log(`        ${f}`);
    }
  }
  console.log("");
  console.log(failed === 0 ? "All dimensions PASS" : `${failed} dimension check(s) FAILED`);
  return failed === 0 ? 0 : 1;
}

function cmdProduce(outDir: string | undefined): number {
  if (!outDir) {
    console.error("usage: node src/cli.ts produce <outDir>");
    return 2;
  }
  const manifest = produce(outDir);
  console.log(BANNER);
  console.log(`Produced ${manifest.messages.length} interop message rows into ${outDir}`);
  console.log(`  (${manifest.messages.length / 2} messages × {cbor, json})`);
  return 0;
}

function cmdVerify(inDir: string | undefined): number {
  if (!inDir) {
    console.error("usage: node src/cli.ts verify <inDir>");
    return 2;
  }
  const report = verifyBundle(inDir);
  console.log(BANNER);
  console.log(`Verifying interop bundle in ${inDir}\n`);
  const status = report.failed === 0 ? "PASS" : "FAIL";
  console.log(`  [${status}] ${report.passed}/${report.total} interop messages verified`);
  for (const f of report.findings) console.log(`        ${f}`);
  return report.failed === 0 && report.total > 0 ? 0 : 1;
}

function main(argv: string[]): number {
  const [cmd, arg] = argv;
  switch (cmd) {
    case "dims":
    case "matrix":
      return cmdDims();
    case "produce":
      return cmdProduce(arg);
    case "verify":
      return cmdVerify(arg);
    default:
      console.error(BANNER);
      console.error("commands: dims | matrix | produce <outDir> | verify <inDir>");
      return 2;
  }
}

process.exit(main(process.argv.slice(2)));
