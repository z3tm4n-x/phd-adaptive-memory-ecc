# CLM-001 — Upset-count horizon requires additional time and repair semantics

**Claim:** The probability in `PAPER-001`, being conditioned on accumulated upset count `p`, cannot be interpreted as elapsed-time, scrub-cycle or mission reliability without an additional upset-count arrival model and repair/reset semantics.  
**Type:** `INFERENCE`  
**Status:** `SUPPORTED`  
**Related RQ:** `RQ-001`  
**Source candidate:** `RQ001-EA-CAND-04`  
**Accepted:** 2026-08-27

## Evidence

- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md), CAND-04 — `SUPPORTED`, high confidence.
- [PAPER-001](../paper_cards/PAPER-001-tausch-2009.md), Eq. 18 and horizon extraction.

## Limitation

The claim does not say that conversion to time is impossible; it requires an explicit, scenario-specific arrival and repair model.

## Used in

- [RQ-001 provisional definition package](../evidence_synthesis/RQ-001_provisional_definition_package.md).

**Last checked:** 2026-08-27
