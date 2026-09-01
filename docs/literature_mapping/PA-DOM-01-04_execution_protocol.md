# PA-DOM-01…04 — Bounded domestic prior-art closure protocol

**Status:** `AUTHORIZED / ACTIVE HANDOFF GATE / NOT A BROAD SEARCH`<br>
**Authorized:** 2026-09-01 by explicit PI `ACCEPT` of RQ-007<br>
**Related RQ:** RQ-002; RQ-003; RQ-004; RQ-005; RQ-006; RQ-007<br>
**Controlling gate:** [Information-deficit control-price gate](../research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md)<br>
**Execution consequence:** required before the next experiment/derivation
specification; does not authorize that experiment

## Purpose

Convert four PI-identified domestic prior-art lines into controlled comparison
points for the next RQ-007 method. The closure must determine which methods,
assumptions, reconstruction interfaces and control features are already occupied
and which therefore become mandatory baselines or design boundaries.

This is not a general Russian-language literature review and not a novelty
decision.

## Fixed work units

### PA-DOM-01 — Meshchanov / Lushnikov / Krasnikov

Control the most complete primary source or controlled source family for:

`registered/corrected single-error count → current intensity estimate → change of regeneration/restoration period`.

Extract:

- exact observable and counting semantics;
- estimator and update window/timing;
- action variable, action set and decision rule;
- reliability metric, constraint or guarantee, if any;
- resource objective or reported saving;
- ECC, event, mapping `W`, reset and initial-state assumptions;
- validation and implementation evidence;
- exact occupied method chain and exact missing interface relative to RQ-007.

**Stop:** one primary source, or one controlled family only if no single source
specifies the complete chain.

### PA-DOM-02 — Podzolko, 2017

Control and analyze the exact 2017 primary text addressing ECC-protected memory,
periodic background scanning/restoration and the probability of an
uncorrectable state under independent-error assumptions.

Extract:

- failure/reliability event, metric, units and aggregation level;
- horizon and initial state;
- arrival, independence and stationarity assumptions;
- ECC capability and decoder-outcome semantics;
- scan, correction, writeback and reset semantics;
- relation between risk and `T_scrub`;
- action/optimization rule, if any;
- required inputs and reproducibility limits;
- whether the model can be implemented as the independent-error baseline for a
  future RQ-007 experiment.

**Stop:** the model is reproducible, or every missing blocking input is named.

### PA-DOM-03 — Boruzdina / Ulanova / Chumakov

Mandatory controlled set:

1. A. B. Boruzdina 2014 dissertation abstract;
2. the already identified primary topology paper DOI
   `10.1134/S1063739714020036`;
3. at most one additional primary methods paper only if the mandatory pair does
   not establish the reconstruction/error proposition needed below.

Extract:

- physical versus logical multiple-upset definitions;
- multiplicity, form/topology and address observables;
- false grouping/merging of independent events;
- reconstruction/classification method and assumptions;
- quantified reconstruction/classification error and validity domain;
- whether the output exists before or after `W`;
- what parent-event or joint information is retained or lost;
- downstream output and whether it is sufficient for DEC-001-compatible `F_A`;
- exact role as a physically plausible information-state or reconstruction
  baseline for RQ-006/RQ-007.

**Stop:** the strongest controlled proposition about retained/reconstructed
event information and its error is known.

### PA-DOM-04 — Zebrev / Galimov

Reuse [PAPER-005](../paper_cards/PAPER-005-zebrev-2017-arxiv-v2.md) and its exact
arXiv `1704.07271v2` source first. Do not order a new deep read merely because
another related source exists.

Extract specifically:

- reduced experimental inputs;
- recovered multiplicity distributions or partial event rates;
- additional model assumptions required for recovery;
- uncertainty and declared validity domain;
- whether reconstruction is physical-multiplicity-level, topology-level or
  post-`W`;
- what `W`/interleaving assumptions remain external;
- whether the reconstructed output is sufficient for DEC-001-compatible
  `F_A(t0,T;μ_t0)` or only supplies an upstream rate/mark input;
- exact comparator role for the future information-state lattice.

If PAPER-005 does not contain the named reduced-data reconstruction proposition,
return one exact missing proposition and, if identifiable from its references,
one exact source identity. Do not start another search or Paper Card without
Orchestrator disposition.

## Source-control sequence

1. Literature Scout identity-controls the exact primary sources for PA-DOM-01,
   PA-DOM-02 and the mandatory PA-DOM-03 pair.
2. For each identity, record title, authors, year, venue/document type,
   DOI/identifier, version relation, access/full-text status and why it is the
   bounded target.
3. eLibrary access is not assumed. If an exact target cannot be obtained without
   it, return `ACCESS BLOCKER` with the controlled identity; do not broaden the
   search.
4. Paper Analyst performs full-text or explicitly limited targeted extraction
   only after source identity and access are controlled.
5. PA-DOM-04 may proceed from accepted PAPER-005 without another discovery pass.

## Common comparison columns

Every work unit must populate the same columns:

1. available input/observation;
2. reconstructed or assumed information;
3. uncertainty/error and validity domain;
4. position relative to `W`;
5. ECC reliability object and horizon;
6. restoration action and decision law;
7. reliability guarantee/constraint;
8. resource-cost treatment;
9. exact distinction that can change the next RQ-007 method or experiment.

Also record:

- source-supported facts versus project inference;
- applicability to RQ-002, RQ-006 or RQ-007;
- what cannot legitimately be claimed;
- exact baseline equations/algorithms that require reproduction;
- any named RQ-003/RQ-004/RQ-005 interface dependency.

## Output contract

### Literature Scout

Create one bounded identity/access report:

`docs/literature_mapping/PA-DOM-01-03_identity_control.md`

Return no general candidate table and no saturation claim.

### Paper Analyst

Create one draft cross-work-unit extraction matrix:

`docs/evidence_synthesis/DRAFT-RQ-007_PA-DOM-01-04_comparison_matrix.md`

Create a full DRAFT Paper Card only for a source whose complete method is both
decision-enabling and cannot be traced adequately in the targeted matrix. Do
not assign `PAPER-xxx`, `CLM-xxx` or `EVD-xxx`.

The matrix must end with:

1. occupied method chains;
2. mandatory baselines for the next quantitative work;
3. mandatory design boundaries/non-claims;
4. reconstruction/model assumptions that must be parameterized or tested;
5. minimum RQ-003/RQ-004/RQ-005 interface implications;
6. named blockers, if any;
7. explicit stop-rule disposition for each PA-DOM unit.

## Hard stop rule

Stop when all four work units have controlled identities/full-text scope and the
common matrix can state which baseline, reconstruction and control features the
next design must not reclaim generically.

A new source is allowed only for one named proposition blocking:

- definition of `M(I)`;
- physical plausibility of the event/`W` domain;
- reproduction of a required baseline;
- interpretation of an exactness/bound/controlled-error claim;
- an exact comparison used in the proposed experiment/derivation.

Do not continue because more thematically related publications exist.

## Do not

- do not launch a broad Russian or international literature mapping;
- do not use eLibrary unavailability as a reason to expand elsewhere without a
  named gap;
- do not create a novelty or non-novelty conclusion;
- do not claim that full physical topology is always required;
- do not claim that marginal/reconstructed information is always sufficient;
- do not assign a numerical `H_req` or `epsilon_req`;
- do not create `HYP-xxx`, `EXP-xxx`, `RES-xxx`, `CLM-xxx` or `EVD-xxx`;
- do not start calculations for the next experiment;
- do not expand into classical inspection/maintenance literature at this gate.

## Closure consequence

After Orchestrator acceptance of the matrix, the next deliverable is a bounded
synthesis of mandatory baselines/design boundaries, minimum RQ-003/RQ-004/RQ-005
interface decisions and an exact experiment/derivation proposal for separate PI
`ACCEPT / REVISE / REJECT`. No calculation precedes that approval.
