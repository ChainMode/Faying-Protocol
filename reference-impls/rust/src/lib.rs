// Reference Implementation, Not Normative — for conformance testing only.
//
// Faying Protocol/1.0 Rust reference implementation library. Exists solely to
// support the互操作合规测试套件 (`conformance/`) and the cross-impl matrix
// (task 5.6). It is NOT the protocol itself and carries no normative weight;
// the authoritative wire-format definition is `schemas/fap-1.0.cddl`.

pub mod crypto;
pub mod detcbor;
pub mod dimensions;
pub mod hash;
pub mod interop;
pub mod json_wire;
pub mod negotiation;
pub mod protocol;
pub mod vectors;
