# CLM-007 — PAPER-002 upper-bound interpretation is conditional on MCU span

**Claim:** The independent-location failure calculation in `PAPER-002` is an upper bound only when MCU row spans greater than the modeled interleaving distance are absent or negligible.  
**Type:** `SOURCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-11`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-11 — `SUPPORTED`, high confidence.
- [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), Section IV extraction.

## Limitation

This is not a universal upper bound over arbitrary physical layouts, mappings or MCU distributions.

## Used in

- RQ-001 assumptions and the later RQ-002/C-RQ-05 mapping gate.

**Last checked:** 2026-08-27
