# CLM-005 — Unpartitioned direct-MCU term overlaps the PAPER-002 total

**Claim:** Adding a separate direct-MCU probability or rate to the total failure metric of `PAPER-002` without partitioning its upstream event population would overlap events already contained in that total.  
**Type:** `INFERENCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-08`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-08 — `SUPPORTED`, medium-high confidence.
- [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md).

## Validity conditions

The existing and added terms must share the same event definition, upstream sample space, aggregate, horizon and units. This establishes set overlap, not its numerical magnitude; a disjoint marked-process construction would avoid the overlap.

## Used in

- RQ-001 mechanism-accounting rule and later novelty assessment.

**Last checked:** 2026-08-27
