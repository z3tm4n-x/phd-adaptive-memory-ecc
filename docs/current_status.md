# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-002 evidence extraction — initial literature mapping accepted with access limitations / bounded Paper Analyst batch ready.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.3-draft`.

## Active gate

Execute bounded task `RQ-002-PA-BATCH-01` over five decision-enabling work units: C001, exact C005 with C006 version comparison, C008, C011 and C020. The batch must use actual full texts, extract the model-selection fields required by the RQ-002 protocol and return Draft Paper Cards without permanent `PAPER` IDs. No second general literature-search cycle is authorized.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / ACTIVE GATE / MAPPING ACCEPTED — PAPER ANALYST BATCH READY`.
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

## RQ-002 initial mapping disposition

- The canonical [initial Literature Scout report](literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md) is accepted as sufficient for decisive full-text analysis, but not as proof of search saturation or as a final answer to RQ-002.
- All mandatory anchors received explicit discovery dispositions; exact `arXiv:1704.07271v2` remains distinct from the RADECS DOI identity pending full-text comparison.
- ResearchRabbit was unavailable and OpenAlex F4–F9 were not completed. These are recorded as non-blocking coverage limitations, not as zero results and not as grounds for another general cycle.
- The selected decisive sources are C001, C005, C008, C011 and C020; C006 is the controlled companion version for C005 comparison.
- The C-RQ-05 condition is operationally triggered because topology, interleaving and mapping `W` cannot be safely excluded or bounded from discovery evidence. Permanent promotion remains pending explicit user acceptance and is not created by this disposition.
- Candidate model classes remain alternatives; no HPP, NHPP, compound, marked, Cox or other process has been selected.

## Pending throughput gates

- After the initial RQ-002 mapping, select 2–5 decisive sources, bound remaining model alternatives and define the first quantitative prototype/experiment before authorizing more general discovery.
- Future contribution alignment must preserve the chain `error model → reliability model → adaptive control → controller architecture → RTL → hardware validation`.
- Reassess the first `ART` candidate after the first independent `RES-xxx`; RQ-001 synthesis alone does not trigger publication.

## Active hypotheses and own results

- No `HYP-xxx` has been registered.
- No `RES-xxx` has been registered.
- `DEC-001` is a research decision, not an own experimental result.

## Next actions

1. Launch `RQ-002-PA-BATCH-01` against the accepted mapping report and actual full texts for C001, C005/C006, C008, C011 and C020.
2. Return Draft Paper Cards, the C005/C006 version comparison and a common extraction matrix; do not assign permanent `PAPER` or `CLM` IDs.
3. After Orchestrator acceptance, build the bounded cross-paper model-selection matrix before requesting any additional deep read.
4. Obtain explicit user acceptance before promoting C-RQ-05 to a permanent RQ; promotion is required before the main quantitative reliability model is built.
5. Use another discovery/deep-read cycle only for a named gap that blocks model selection, adequacy, validation or the first quantitative experiment.
6. Keep RQ-001/DEC-001 unchanged and do not assign a numerical reliability requirement without traceable provenance.

## Notes

- eLibrary remains deferred where Literature Scout lacks access; an unavailable database is recorded as unknown coverage, not as zero results.
- Literature Scout discovery is complete for the present gate; Paper Analyst full-text extraction is the next authorized role action.
