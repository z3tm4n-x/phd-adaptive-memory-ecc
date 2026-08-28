# RQ-002 — Minimum adequate model of radiation-induced errors in SRAM

**Title:** Minimum adequate model of radiation-induced errors in SRAM<br>
**Source candidate:** C-RQ-02<br>
**Status:** `OPEN — ACTIVE GATE / MAPPING ACCEPTED — PAPER ANALYST BATCH READY`<br>
**Registered:** 2026-08-26<br>
**Gate opened:** 2026-08-27 by [DEC-001](../decisions/DEC-001-rq001-reliability-contract.md)

## Question

Какая минимальная стохастическая модель радиационно-индуцированных ошибок SRAM одновременно физически обоснована и вычислительно пригодна для моделирования накопления ошибок и адаптивного scrubbing?

## Why it matters

Структура error model определяет вероятность выбранного reliability event, допустимость упрощающих допущений и необходимость учитывать MCU/MBU и корреляции до построения основной reliability model.

## Scope

- single-bit upsets и накопление ошибок между scrub cycles;
- stationary и non-stationary intensity;
- MCU/MBU;
- spatial и temporal correlation;
- levels bit/cell, codeword, partition and controller-managed domain;
- assumptions, parameters and validity domain of every model class;
- state variables required for the DEC-001 initial-state and exposure semantics.
- minimal post-mapping representation of one radiation event required to compute `E_cap` under accumulation and scrubbing;
- uncertainty propagation, empirical identifiability, domain of validity and computational tractability for adaptive scrubbing;
- explicit/parameterized post-`E_cap` correction, writeback, reset and scrub semantics rather than one hard-coded consequence.

## Exclusions

- prior adoption of Poisson arrivals, independence or stationarity without evidence;
- numerical parameters without provenance;
- final codeword organization/interleaving choice;
- conversion of specific COSRAD outputs into an online controller signal;
- adaptive policy selection;
- automatic reinterpretation of `E_cap` as a decoder or system outcome.
- permanent faults, cumulative TID degradation, destructive SEE/SEFI and other persistent mechanisms unless a later evidence-based scope decision reopens them;
- general inspection/maintenance/control prior art, which is a separate non-blocking backlog task.

## Input contract from RQ-001 / DEC-001

Candidate models must be evaluated against:

- primitive event `E_cap(A;t0,T)`;
- general metric `F_A(t0,T; μ_t0)`;
- explicit reporting window and initial state/distribution;
- explicitly declared controller-managed domain \(A\);
- required partitioning where ECC, \(W\), arrival, bank/block or scrubbing semantics differ;
- distinct direct same-particle and independent-accumulation paths with no untracked overlap;
- separate upset-count, per-codeword exposure, reporting and mission layers.

RQ-003 remains responsible for concrete ECC/decoder-outcome semantics.

`E_cap` and `τ_A` describe the underlying physical/codeword state. The future controller acts only on observable information; the dependency `RQ-003 outcome semantics ↔ RQ-004 observables/estimation` is recorded but not resolved here.

## Evidence needed

- primary irradiation studies for SRAM;
- empirical SEU, MCU and MBU evidence;
- published stochastic/probabilistic error models;
- evidence that tests independence, stationarity and spatial/temporal correlation assumptions;
- model-validation studies in comparable conditions;
- evidence on mechanism provenance and topology needed to calculate `E_cap`;
- evidence on the information lost when reducing full physical topology + `W` to joint marks, marginal per-word multiplicities or a scalar rate;
- uncertainty in physical-event classification and whether it propagates into reliability results;
- evidence sufficient to trigger or dismiss the C-RQ-05 escalation gate.

## Answer / decision criterion

RQ is answerable when:

1. relevant model classes are enumerated;
2. assumptions, parameters, observed level and validity domain are recorded for each;
3. a minimum adequate model or a small justified alternative set is selected;
4. excluded effects and bounds are explicit;
5. compatibility with the DEC-001 event, domain, window and initial-state contract is demonstrated.
6. the minimum arrival-process representation, event/mark representation, accumulation state and scrub/reset semantics are stated;
7. experimentally identifiable parameters, unresolved uncertainties, validation needs and computational feasibility are stated;
8. outputs required by RQ-003, RQ-004 and the first quantitative prototype are explicit.

**Decision gate:** if evidence shows that MCU/MBU or spatial correlation materially changes the structure or probability of `E_cap`, or their exclusion cannot be justified or bounded, C-RQ-05 must be promoted to a mandatory permanent RQ and answered before the main reliability model is built.

## Active gate / next action

The canonical [initial mapping report](../literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md) is accepted as sufficient for bounded decisive full-text analysis, but not as proof of saturation or as a final answer to RQ-002. ResearchRabbit and incomplete OpenAlex fallback coverage remain explicit non-blocking access limitations.

Execute `RQ-002-PA-BATCH-01` over C001, exact C005 with C006 version comparison, C008, C011 and C020. Paper Analyst must use actual full texts, return Draft Paper Cards and populate the common model-selection extraction fields without assigning permanent `PAPER` or `CLM` IDs.

The C-RQ-05 escalation condition is operationally triggered because topology, interleaving and mapping `W` cannot be safely excluded or bounded at discovery depth. Permanent promotion requires explicit user acceptance and must occur before the main quantitative reliability model is built.

eLibrary remains `DEFERRED / UNKNOWN COVERAGE`. No second general literature-search cycle is authorized without a named gap that blocks model selection, adequacy, validation or the first quantitative experiment.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-003.
- Input decision: `DEC-001`.
- Conditional dependency: C-RQ-05 — escalation condition triggered; permanent promotion pending explicit acceptance.
- Non-blocking future task: control prior-art threat in [`research_backlog.md`](../research_backlog.md).
- Mapping report: [`RQ-002_literature_mapping_initial_2026-08-27.md`](../literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md).
- PAPER/CLM/EVD/HYP/EXP: TBD after bounded full-text analysis and Orchestrator acceptance.

## Answer

UNKNOWN.

## Confidence

Not assessed.
