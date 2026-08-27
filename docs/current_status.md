# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-001 provisional definition — user approval gate.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.2-draft`.

## Active gate

Review and approve/amend/reject `docs/evidence_synthesis/RQ-001_provisional_definition_package.md`. Until approval, RQ-001 remains `INVESTIGATING`, RQ-002 remains queued, and no project numerical reliability threshold is assigned.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `INVESTIGATING / PROVISIONAL DEFINITION PENDING`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / QUEUED`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.

## RQ-001 evidence state

- Literature discovery: `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`.
- eLibrary: `DEFERRED / UNKNOWN COVERAGE`; not a blocker for the current gate.
- Accepted Paper Cards: `PAPER-001`, `PAPER-002`, `PAPER-003`, all `CORE`.
- Cross-paper synthesis: complete as an initial, non-final synthesis.
- Evidence Audit `RQ-001-EVIDENCE-AUDIT-01`: accepted with limitation.
- Audit result: 11 candidate propositions supported; `RQ001-EA-CAND-10` partially supported and deferred.
- Synthesis typo `seven exact claims` corrected to `twelve exact claims`.

## Accepted claims

- `CLM-001` — count horizon requires an arrival and repair model before time interpretation.
- `CLM-002` — harmful same-particle MBU is outside the main PAPER-001 equation.
- `CLM-003`/`CLM-004` — PAPER-002/PAPER-003 analytical totals lose failed-word mechanism provenance.
- `CLM-005`/`CLM-006` — an unpartitioned direct-MCU term overlaps those totals under matched scope/horizon/units.
- `CLM-007` — PAPER-002 upper-bound interpretation is conditional on MCU span relative to ID.
- `CLM-008` — the analyzed papers model multiplicity beyond capability, not decoder/service outcome.

Candidate source facts `RQ001-EA-CAND-01…03` remain in Paper Cards and the matrix rather than receiving redundant `CLM` records.

## Deferred claim

`RQ001-EA-CAND-10` is not accepted as a permanent claim. Its missing word-specific exposure-age component is supported, while the stronger effective-global-reset interpretation requires the primary periodic-maintenance derivation or equivalent scrub-state evidence.

## Active hypotheses and own results

- No `HYP-xxx` has been registered.
- No `RES-xxx` has been registered.
- Paper Cards, claims and evidence audits are literature-analysis artefacts, not own experimental results.

## Current unknowns / TBD

- Approval of the proposed primitive event `E_cap(A,H)` — pending.
- Approval of primary metric `F_A(H)` and aggregation boundary — pending.
- Exact ECC/decoder outcomes — RQ-003 dependency.
- Target physical mapping `W` and error process — later RQ-002/RQ-003 work.
- Mission aggregation for nonstationary conditions — unresolved.
- System-visible consequence model — unresolved.
- Numerical requirement `H_req` and `ε_req` — `TBD` pending traceable requirements.
- Sequential scrub implementation details — unresolved; global reset is not adopted as a literature-established fact.

## Next actions

1. Review the six approval questions in the provisional definition package.
2. If approved, record the accepted RQ-001 working definition and status `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
3. Only after that gate may RQ-002 begin with the accepted event/metric contract as input.
4. Revisit the deferred scrub-abstraction claim only if it changes the selected model or decision.
5. Reconcile six contextual audit sources with Zotero before they are used as cited evidence in publication text; no automatic Paper Cards.

## Notes

- Illustrative thresholds and scrub intervals from `PAPER-002`/`PAPER-003` are not project requirements.
- Upset-count, per-codeword exposure, scrub-cycle and mission horizons remain distinct.
- No new literature search is active.
