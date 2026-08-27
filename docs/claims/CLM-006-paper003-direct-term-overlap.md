# CLM-006 — Unpartitioned direct-MCU term overlaps the PAPER-003 total

**Claim:** Adding a separate direct-MCU probability or rate to the total failure metric of `PAPER-003` without partitioning its upstream event population would overlap events already contained in that total.  
**Type:** `INFERENCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-09`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-09 — `SUPPORTED`, medium-high confidence.
- [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md).

## Validity conditions

The existing and added terms must share the same event definition, upstream sample space, aggregate, horizon and units. This establishes set overlap, not its numerical magnitude; explicit upstream partitioning can avoid the overlap.

## Used in

- RQ-001 mechanism-accounting rule and later novelty assessment.

**Last checked:** 2026-08-27
