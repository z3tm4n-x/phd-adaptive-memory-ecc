# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-002 targeted literature mapping — corrected handoff issued / Literature Scout launched.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.3-draft`.

## Active gate

Receive and assess task `RQ-002-LITERATURE-MAPPING-01` executed against the corrected `docs/literature_mapping/RQ-002_protocol.md`. The Scout must explicitly disposition all mandatory anchors, preserve exact `arXiv:1704.07271v2`, map candidate stochastic/event-representation classes, apply the C-RQ-05 gate and return a bounded Paper Analyst handoff. eLibrary remains deferred.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / ACTIVE GATE / LITERATURE SCOUT LAUNCHED`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.

## Accepted RQ-001 decision

[DEC-001](decisions/DEC-001-rq001-reliability-contract.md) records:

- primitive event `E_cap` as ECC capability exceedance, not an automatic DUE/SDC/miscorrection/system-failure label;
- reporting window \(H(t_0,T)=[t_0,t_0+T]\);
- general metric \(F_A(t_0,T;\mu_{t_0})\), with the initial state/distribution required by every quantitative model;
- an explicitly declared controller-managed SRAM protection domain \(A\);
- mandatory partitioning of \(A\) when ECC, mapping \(W\), arrival, bank/block or scrubbing semantics differ;
- distinct upset-count, per-codeword exposure, reporting and mission horizons;
- sequential exposure as a working modeling requirement, not a literature-established fact.

## RQ-001 open dependencies

- concrete ECC/decoder outcomes — RQ-003;
- adequate error-arrival/correlation model — RQ-002;
- target physical mapping \(W\);
- nonstationary mission aggregation;
- system-visible consequence model;
- \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) — `TBD` pending traceable requirements;
- CAND-10 remains deferred.

## RQ-002 input contract

RQ-002 must evaluate candidate error models by whether they can produce the declared `E_cap` metric for:

- a stated reporting window and initial state/distribution;
- an explicitly declared or partitioned protection domain;
- direct same-particle and independent-accumulation mechanisms without untracked overlap;
- stationary and nonstationary scenarios within stated validity domains.

The C-RQ-05 escalation gate remains mandatory if MCU/MBU or spatial correlation is material or cannot be safely excluded/bounded.

The base failure domain is transient radiation-induced upsets. Permanent faults, cumulative TID degradation, destructive SEE/SEFI and other persistent mechanisms are out of scope unless a later evidence-based decision reopens them.

## RQ-002 pre-launch correction

- External-advisor statements remain `UNVERIFIED` search threats, not evidence or project decisions.
- DEC-001 is unchanged and RQ-001 remains `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- Mandatory anchors: C32, C51, C52, Zebrev-2015, exact `arXiv:1704.07271v2`, and the separately controlled RADECS DOI identity.
- The protocol now tests candidate process classes and the minimum information required after mapping `W`; no class or marginal representation is preselected.
- The [novelty workflow](novelty_workflow.md) prevents scope-limited `CLM-002…006` from becoming general literature claims before an adversarial pass.
- The separate inspection/maintenance/control prior-art threat is recorded in [research backlog](research_backlog.md) and does not block RQ-002.

## Pending throughput gates

- After the initial RQ-002 mapping, select 2–5 decisive sources, bound remaining model alternatives and define the first quantitative prototype/experiment before authorizing more general discovery.
- Future contribution alignment must preserve the chain `error model → reliability model → adaptive control → controller architecture → RTL → hardware validation`.
- Reassess the first `ART` candidate after the first independent `RES-xxx`; RQ-001 synthesis alone does not trigger publication.

## Active hypotheses and own results

- No `HYP-xxx` has been registered.
- No `RES-xxx` has been registered.
- `DEC-001` is a research decision, not an own experimental result.

## Next actions

1. Await the reproducible Literature Scout report for `RQ-002-LITERATURE-MAPPING-01`; do not run another general planning/search cycle first.
2. Verify explicit disposition of all mandatory anchors and exact Zebrev arXiv-v2 version control.
3. Apply the C-RQ-05 escalation and novelty-protection gates during Orchestrator review.
4. Select only decision-enabling Paper Analyst deep reads after the mapping matrix is available.
5. Keep RQ-001/DEC-001 unchanged and do not assign a numerical reliability requirement without traceable provenance.

## Notes

- eLibrary remains deferred where Literature Scout lacks access; an unavailable database is recorded as unknown coverage, not as zero results.
- Literature Scout is the only authorized active RQ-002 search role for this gate.
