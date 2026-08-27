# CLM-004 — PAPER-003 analytical probability loses failed-word mechanism provenance

**Claim:** The analytical failure probability in `PAPER-003` does not retain whether the multiple erroneous cells in a failed word originated from one MCU or from independent arrivals accumulated between repairs.  
**Type:** `INFERENCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-07`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-07 — `SUPPORTED`, medium-high confidence.
- [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md), Eqs. 5–9 and simulator-boundary extraction.

## Limitation

MCU/SBU labels exist inside the separate simulator; the provenance loss applies to the analytical probability output.

## Used in

- RQ-001 mechanism-accounting rule and later novelty assessment.

**Last checked:** 2026-08-27
