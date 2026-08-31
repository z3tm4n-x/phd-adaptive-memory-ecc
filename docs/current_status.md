# Current Status

**Updated:** 2026-08-31

## Current phase

Scientific review of the first own quantitative experiment and bounded evidence
audit of the closest Chen/IHP/Potsdam adaptive-control family. The Russian
normative baseline extraction is accepted and now constrains the later
physical-input/observability interface.

## Infrastructure and specification

- GitHub, Zotero and the canonical agent operating model are operational.
- Research Specification: `v0.5-draft`.
- Controlling architecture remains [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md):
  radiation-test evidence → identifiable device-error representation → `W`/ECC
  organization → ECC-level reliability → online risk assessment → adaptive
  restoration decision.
- Adaptive restoration control remains the final/core dissertation layer.

## Active scientific gate

Obtain adversarial Scientific Reviewer disposition of EXP-001 before creating any
`RES-xxx`, while the Evidence Auditor performs the bounded Chen S3/S4/S5 feature
comparison against DEC-002.

The next quantitative gate, after those reviews, is to move from the deliberately
extremal synthetic discriminator to a physically defensible `W`/topology/event
domain and determine the magnitude and restoration-decision relevance of
information loss, or a validity domain in which a reduction is safe. The next
experiment must not merely repeat that dependence can matter.

## Active Research Questions

- RQ-001 — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; DEC-001 unchanged.
- RQ-002 — `OPEN / EXP-001 IMPLEMENTED / SCIENTIFIC REVIEW PENDING`.
- RQ-003 — `OPEN / QUEUED`; retains ECC capability and decoder-outcome semantics.
- RQ-004 — `OPEN / QUEUED`; must distinguish external exposure information from
  internal protected-memory state/history.
- RQ-005 — `OPEN / QUEUED`; measurable resource-cost vector remains required.
- RQ-006 — `OPEN / EXP-001 IMPLEMENTED / SCIENTIFIC REVIEW PENDING`; owns `W`,
  topology, joint post-`W` impact and reduction-sufficiency conditions.
- An integrated adaptive-control RQ remains required after the reliability,
  observation and cost interfaces are bounded.

## Controlling decisions

- [DEC-001](decisions/DEC-001-rq001-reliability-contract.md): `E_cap` is ECC
  capability exceedance; general metric is `F_A(t0,T;μ_t0)`; `A` is explicitly
  declared/partitioned; `H_req` and `ε_req` remain `TBD`.
- [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md):
  one causal evidence-to-adaptive-decision architecture.
- [DEC-003](decisions/DEC-003-rq002-bounded-model-family-and-exp001.md):
  event-driven reference, representation ladder and bounded EXP-001; no universal
  stochastic-process family selected.

## Orchestrator dispositions

### EXP-001 implementation

[EXP-001](../experiments/EXP-001-event-representation-reduction-sensitivity.md)
is `IMPLEMENTED / ORCHESTRATOR TECHNICAL ACCEPTANCE / SCIENTIFIC REVIEW PENDING`.
Research Engineer commit:
`84728d1b5768e7c91c508495d696c5980943ae57`.

Accepted for review:

- 17/17 tests pass;
- 768,000 `L0/L1` trajectory checks and 288,302 event marks have zero mismatch;
- all J-A/J-B construction invariants and declared precision rules pass;
- an independent Linux rerun reproduced all scientific aggregate, decision,
  delta and invariant files byte-for-byte; only runtime/memory fields differ from
  Windows;
- `L3-U` is explicit and `L3-E` remains deferred.

The [Orchestrator disposition](../experiments/manifests/EXP-001/orchestrator-disposition.md)
records an unverified analytical identified-set precheck. It also records one
mandatory interpretation correction: at experimental `epsilon=0.55`, exact J-A
and J-B both select `T_scrub=4`, while the Wilson-upper-bound rule selects 4 and 2.
That discrepancy is confidence-rule conservatism, not a purely structural model
difference. Exact/model, Monte Carlo and confidence-rule uncertainty must remain
separate.

No `HYP-xxx` or `RES-xxx` is created. A bounded `RES-001` is conditional on a
passing Scientific Reviewer disposition.

### Russian normative baseline

[NORMATIVE-BASELINE-01](normative_baseline/NORMATIVE-BASELINE-01_extraction_matrix.md)
is `ACCEPTED WITH LIMITATION / PARTIAL — NAMED INPUT NEEDED`.

Accepted practical chain:

`diagnostic observations → PMI/software classification → classified ORE counts →
cross sections → sensitivity representation → environment convolution → scalar
rate/probability`.

The extraction does not establish a normative deficiency. It identifies explicit
unresolved interfaces to parent-event reconstruction, address semantics, `W`, ECC
state, initial state and scrubbing. The RD provenance is normalized by recording
both canonical PI-supplied hashes and Paper Analyst processed-copy hashes; this is
not a scientific blocker. The supplied STO controlled-edition status remains
`AMBIGUOUS`.

### Chen/IHP/Potsdam control prior art

Three full-text analytical cards are formally accepted:

- [PAPER-009](paper_cards/PAPER-009-chen-et-al-2023.md) — S3 / DFT 2023 — `CORE`;
- [PAPER-010](paper_cards/PAPER-010-chen-et-al-2024.md) — S4 / LATS 2024 — `RELATED`;
- [PAPER-011](paper_cards/PAPER-011-chen-et-al-2025.md) — S5 / JETTA 2025 — `CORE`.

The [S3/S4/S5 comparison matrix](evidence_synthesis/CONTROL-PRIOR-ART-01_comparison_matrix.md)
is `ACCEPTED WITH LIMITATION / READY FOR EVIDENCE AUDITOR`. It establishes a close
adaptive-control prior-art threat within the bounded family but does not establish
literature-level novelty or non-novelty. S3 supplies the forecast-driven PBD loop,
S4 is the separate reactive HSIAO evaluation branch, and S5 consolidates both with
bounded additions. Version-specific metrics and numerical inconsistencies remain
explicit.

## What blocks the first RES

Only the following now block a permanent bounded result from EXP-001:

1. independent Scientific Reviewer verification of implementation fairness,
   statistics and interpretation;
2. acceptance, correction or rejection of the proposed J-A/J-B analytical
   identified-set derivation;
3. final separation of structural feasibility from Monte Carlo and Wilson-bound
   decision effects.

Target SRAM data, final `H_req/ε_req`, final ECC/observer/cost/hardware choices and
additional literature do not block this narrowly bounded review.

## What blocks the next physically defensible experiment

The next experiment needs a declared plausible domain rather than a final product:

- defensible event multiplicity/topology statistics with uncertainty;
- one or more plausible `W`/interleaving families;
- an explicit bridge from observable test outputs to the retained event mark;
- parameterized ECC/restoration semantics and decision thresholds;
- a preregistered future hypothesis or decision criterion before execution.

The accepted normative extraction and `PAPER-004…008` provide starting constraints.
A new literature or Paper Card cycle is permitted only for a named gap that blocks
model selection, adequacy, validation or the next experiment.

## Next bounded handoffs

1. **Scientific Reviewer:** adversarial review of EXP-001, including the proposed
   analytical identified set and exact/estimated/robust feasibility separation.
2. **Evidence Auditor:** audit the eight scoped Chen-family candidate statements
   against `PAPER-009…011`, the comparison matrix and DEC-002.
3. **Orchestrator after both returns:** accept/reject a bounded `RES-001`; then
   preregister the smallest physically plausible follow-up hypothesis/experiment.

No broad literature campaign or second general RQ-002 cycle is authorized.

## PI decisions and materials

No new PI decision is required for the two active reviews.

For the later physically defensible configuration, useful but currently
non-blocking material remains:

- controlled-edition or registry evidence for STO 04.01.0005–2022;
- one representative/de-identified SRAM private PMI and diagnostic/software log
  schema;
- target-like memory organization/interleaving information, if available;
- applicable current normative documents named in the accepted extraction.

If a review exposes a genuine branch choice, the Orchestrator will return a
specific decision request rather than narrowing scope automatically.

## Active hypotheses and results

- No `HYP-xxx` is registered; none is created retroactively for EXP-001.
- EXP-001 is implemented but is not yet a permanent result.
- No `RES-xxx` is registered.

## Constraints

- Do not reopen RQ-001 or revise DEC-001 without a concrete contradiction.
- Do not identify `E_cap` with DUE/SDC/miscorrection/system failure.
- Do not assign a numerical reliability requirement without traceable provenance.
- Do not generalize EXP-001 to physical SRAM topology or universal marginal-model
  insufficiency.
- Do not infer normative deficiency.
- Do not infer novelty from one missing Chen feature or conflate S3/S4/S5.
- Do not let the identification/mapping layer replace adaptive control as the
  dissertation core.
