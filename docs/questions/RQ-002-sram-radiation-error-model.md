# RQ-002 — Minimum adequate model of radiation-induced errors in SRAM

**Title:** Minimum adequate model of radiation-induced errors in SRAM<br>
**Source candidate:** C-RQ-02<br>
**Status:** `OPEN / RES-001 BOUNDED RESULT REGISTERED / NEXT GENERALIZATION GATE ACCEPTED`<br>
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

Under the integrated project roadmap, RQ-002 supplies the device-error representation consumed by the ECC-aware reliability layer and, through it, the adaptive-control decision. It must therefore distinguish information sufficient in principle from information identifiable in realistic radiation-test observations. This dependency does not turn RQ-002 into the complete adaptive-control problem and does not make richer event information preferable by assumption.

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

**Decision gate:** if evidence shows that MCU/MBU or spatial correlation materially changes the structure or probability of `E_cap`, or their exclusion cannot be justified or bounded, C-RQ-05 must be promoted to a mandatory permanent RQ and answered before the main reliability model is built. This gate has fired and the PI approved permanent promotion C-RQ-05 → [RQ-006](RQ-006-physical-logical-mapping-information-sufficiency.md) on 2026-08-28.

## Accepted initial evidence synthesis

The canonical [initial mapping report](../literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md), five accepted Paper Cards and [initial cross-paper synthesis](../evidence_synthesis/RQ-002_initial_evidence_synthesis.md) are sufficient to enter bounded model selection. They are not proof of search saturation and do not constitute a final answer to RQ-002. ResearchRabbit and incomplete OpenAlex fallback coverage remain explicit non-blocking access limitations.

Accepted inputs:

- [PAPER-004](../paper_cards/PAPER-004-clemente-rezaei-franco-2022.md) — independent accumulation/occupancy;
- [PAPER-005](../paper_cards/PAPER-005-zebrev-2017-arxiv-v2.md) — multiplicity partition and controlled C005/C006 comparison;
- [PAPER-006](../paper_cards/PAPER-006-moindjie-et-al-2017.md) — multiplicity-indexed event rates;
- [PAPER-007](../paper_cards/PAPER-007-ogden-mascagni-2017.md) — topology, mapping and event-driven state;
- [PAPER-008](../paper_cards/PAPER-008-gomi-et-al-2026.md) — quasi-event observation/classification and topology.

The synthesis rules out, as unsupported stand-alone choices, an unmarked scalar bit-arrival rate, a clean count-conditioned occupancy model and the simple low-`β` additive expression. It retains a bounded alternative set rather than selecting HPP, NHPP, compound/marked, observation-aware or event-driven models prematurely.

## Accepted Evidence Audit and bounded model decision

[RQ-002 Evidence Audit 01](../evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md) is accepted with one limitation: its candidate 04 does not establish universal insufficiency of marginal per-word multiplicities; it establishes that sufficiency cannot be presumed and must be tested or bounded. No permanent claims were created.

[DEC-003](../decisions/DEC-003-rq002-bounded-model-family-and-exp001.md) passes the literature/model-selection gate for the first prototype without selecting a universal stochastic family. It retains:

- an event-driven parent-event-preserving reference;
- a representation ladder from full physical topology through joint post-`W`, marginal and scalar levels;
- HPP and declared time-varying/NHPP scenarios only as synthetic controlled alternatives;
- explicit initial state, repair/writeback/reset and DEC-001 first-passage semantics.

The minimum adequate target model remains unknown until the reduction comparison, normative identifiability extraction and later target validation are available.

## Active gate / next action

1. Treat [EXP-001 Scientific Review 02](../scientific_reviews/EXP-001_SCIENTIFIC_REREVIEW_02.md)
   as `PASS` and [`RES-001`](../../results/RES-001-exp001-four-word-identified-set.md)
   as the only promoted EXP-001 result.
2. Preserve the separation of representation/dependence uncertainty, Monte
   Carlo uncertainty and CI-decision conservatism.
3. Obtain PI disposition of the
   [next quantitative gate](../research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md),
   then define nested information/model sets and a physically defensible
   arrival/event/state slice without selecting a universal process family.
4. Activate only the minimum RQ-003/RQ-004/RQ-005 interfaces required by that
   gate and use the accepted normative baseline to define realistic information
   outputs; do not infer normative deficiency.
5. Do not authorize another general literature cycle without a named gap that
   blocks model adequacy, validation or interpretation of the next quantitative step.

The former C-RQ-05 escalation condition is resolved by permanent [RQ-006](RQ-006-physical-logical-mapping-information-sufficiency.md). RQ-002 retains arrival/event/state responsibility; RQ-006 owns `W`, interleaving and reduction-sufficiency conditions.

eLibrary remains `DEFERRED / UNKNOWN COVERAGE`. No second general literature-search cycle is authorized without a named gap that blocks model selection, adequacy, validation or the first quantitative experiment.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-003.
- Input decision: `DEC-001`.
- Mapping dependency: [RQ-006](RQ-006-physical-logical-mapping-information-sufficiency.md) — permanently registered after the escalation condition fired.
- Non-blocking future task: control prior-art threat in [`research_backlog.md`](../research_backlog.md).
- Mapping report: [`RQ-002_literature_mapping_initial_2026-08-27.md`](../literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md).
- Accepted Paper Cards: `PAPER-004…PAPER-008`.
- Evidence synthesis: [`RQ-002_initial_evidence_synthesis.md`](../evidence_synthesis/RQ-002_initial_evidence_synthesis.md).
- Evidence Audit: [`RQ-002_EVIDENCE_AUDIT_01.md`](../evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md).
- Model decision: [`DEC-003`](../decisions/DEC-003-rq002-bounded-model-family-and-exp001.md).
- Experiment: [`EXP-001`](../../experiments/EXP-001-event-representation-reduction-sensitivity.md) — COMPLETE / SCIENTIFIC REVIEW PASS.
- Result: [`RES-001`](../../results/RES-001-exp001-four-word-identified-set.md) — accepted bounded four-word identified-set result.
- Next gate: [`Information-deficit control-price gate`](../research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md) — PI accepted; RQ-007 is permanently registered, while bounded prior-art closure, minimum RQ-003/RQ-004/RQ-005 interface decisions and separate EXP/derivation approval remain required.
- CLM/EVD/HYP: no new permanent artefact created at this gate.

## Answer

UNKNOWN.

## Confidence

Not assessed.
