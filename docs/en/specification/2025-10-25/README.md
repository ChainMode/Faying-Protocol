---
title: Faying Protocol — Directory Guide (README)
version: Faying Protocol/1.0
status: Final
editors:
  - Faying Protocol Committee
date: 2025-10-25
language: en
---

# Faying Protocol Directory Guide

> **Single-source declaration of the protocol body**: The protocol body is the single file [`Faying-Protocol-1.0.md`](./Faying-Protocol-1.0.md). This `README.md` is an **auxiliary document only** and **does not constitute the protocol body**.

This is the formal release (Final, published 2025-10-25) of the English Faying Protocol/1.0 specification.

## Protocol Body (start here)

- **[Faying-Protocol-1.0.md (single-file protocol specification — the body)](./Faying-Protocol-1.0.md)** ← the single authoritative source of the protocol body; §1..§11 plus Appendices A/B are all written into this single file.

## Version and Editors

| Field | Value |
| --- | --- |
| Protocol name | Faying Protocol (**FAP abbreviation abolished**; no separate short form — use the full name "Faying Protocol" when a short form is needed) |
| Version | `Faying Protocol/1.0` |
| Status | Final (published 2025-10-25) |
| Editors | Faying Protocol Committee |
| Date | 2025-10-25 |

> The version and editors fields above match exactly the YAML front matter of the protocol body [`Faying-Protocol-1.0.md`](./Faying-Protocol-1.0.md); any change on either side must be synchronized in both directions.

## Files in This Directory

| File | Role | Notes |
| --- | --- | --- |
| [`Faying-Protocol-1.0.md`](./Faying-Protocol-1.0.md) | **Protocol body (authoritative)** | The single authoritative source carrying all chapters and Appendices A/B |
| [`README.md`](./README.md) | Auxiliary document | This guide |

> Structural note: the English side is a **single-file** layout carrying §1–§11 and Appendices A/B. The Chinese side at `docs/zh-CN/specification/2025-10-25/` is split into 11 chapter files plus Appendices A/B/C (Appendix C is the changelog, maintained only on the Chinese side). The English single file is aligned with it at the **section-anchor level**, not file-by-file.

## Relationship Between the Two Language Sides

- The Chinese (`docs/zh-CN/specification/2025-10-25/`) and English (`docs/en/specification/2025-10-25/`) sides were released together in the same commit; one-sided release is prohibited.
- When ambiguity arises between the Chinese and English wordings, the Chinese version prevails and the English version is corrected at the next review.
- Chinese counterpart of the protocol body: [`../../../zh-CN/specification/2025-10-25/`](../../../zh-CN/specification/2025-10-25/).
- Subsequent errata are carried by a new release-date edition per §1.7.4 and do not change the protocol version number.
