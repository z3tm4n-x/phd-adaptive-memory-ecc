# CLM-008 — The analyzed papers model multiplicity, not decoder or service outcome

**Claim:** `PAPER-001`, `PAPER-002` and `PAPER-003` define failure through erroneous-bit multiplicity beyond modeled correction capability rather than through an observed decoder output or system-visible loss-of-service event.  
**Type:** `INFERENCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-12`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-12 — `SUPPORTED`, high confidence.
- [PAPER-001](../paper_cards/PAPER-001-tausch-2009.md), [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md).

## Limitation

The bounded synthesis does not establish how a real decoder maps multi-error states to DUE, SDC, miscorrection or system-visible service loss.

## Used in

- RQ-001 event layering and RQ-003 dependency.

**Last checked:** 2026-08-27
