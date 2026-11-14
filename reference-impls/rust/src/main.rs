// Reference Implementation, Not Normative — for conformance testing only.
//
// CLI for the Faying Protocol/1.0 Rust reference implementation.
//
// Usage:
//   cargo run -- dims                 Run the 5.2–5.5 dimension matrix.
//   cargo run -- produce <outDir>     Produce an interop bundle (CBOR+JSON).
//   cargo run -- verify  <inDir>      Verify an interop bundle (e.g. TS's).
//   cargo run -- matrix               Alias for `dims`.
//
// Exit code is non-zero if any check fails, so it can gate CI / cross-impl.

use std::path::PathBuf;
use std::process::exit;

use faying_ref::dimensions::run_all_dimensions;
use faying_ref::interop::{produce, verify_bundle};

const BANNER: &str = "Faying Protocol/1.0 — Rust Reference Implementation (Not Normative)";

fn cmd_dims() -> i32 {
    println!("{BANNER}");
    println!("Running data-plane dimensions (tasks 5.2–5.5)\n");
    let results = run_all_dimensions();
    let mut failed = 0usize;
    for r in &results {
        let status = if r.failed == 0 { "PASS" } else { "FAIL" };
        println!("  [{}] {:<10} {}/{} passed", status, r.name, r.passed, r.total);
        if r.failed > 0 {
            failed += r.failed;
            for f in &r.findings {
                println!("        {f}");
            }
        }
    }
    println!();
    if failed == 0 {
        println!("All dimensions PASS");
        0
    } else {
        println!("{failed} dimension check(s) FAILED");
        1
    }
}

fn cmd_produce(out: Option<String>) -> i32 {
    let out = match out {
        Some(o) => o,
        None => {
            eprintln!("usage: cargo run -- produce <outDir>");
            return 2;
        }
    };
    match produce(&PathBuf::from(&out)) {
        Ok(summary) => {
            println!("{BANNER}");
            println!("Produced {} interop message rows into {out}", summary.message_rows);
            println!("  ({} messages × {{cbor, json}})", summary.message_rows / 2);
            0
        }
        Err(e) => {
            eprintln!("produce failed: {e}");
            1
        }
    }
}

fn cmd_verify(dir: Option<String>) -> i32 {
    let dir = match dir {
        Some(d) => d,
        None => {
            eprintln!("usage: cargo run -- verify <inDir>");
            return 2;
        }
    };
    let report = verify_bundle(&PathBuf::from(&dir));
    println!("{BANNER}");
    println!("Verifying interop bundle in {dir}\n");
    let status = if report.failed == 0 { "PASS" } else { "FAIL" };
    println!("  [{}] {}/{} interop messages verified", status, report.passed, report.total);
    for f in &report.findings {
        println!("        {f}");
    }
    if report.failed == 0 && report.total > 0 {
        0
    } else {
        1
    }
}

fn main() {
    let args: Vec<String> = std::env::args().skip(1).collect();
    let cmd = args.first().map(|s| s.as_str()).unwrap_or("");
    let arg = args.get(1).cloned();
    let code = match cmd {
        "dims" | "matrix" => cmd_dims(),
        "produce" => cmd_produce(arg),
        "verify" => cmd_verify(arg),
        _ => {
            eprintln!("{BANNER}");
            eprintln!("commands: dims | matrix | produce <outDir> | verify <inDir>");
            2
        }
    };
    exit(code);
}
