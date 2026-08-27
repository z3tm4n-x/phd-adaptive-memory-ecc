# RQ-002 — Minimum adequate model of radiation-induced errors in SRAM

**Title:** Minimum adequate model of radiation-induced errors in SRAM  
**Source candidate:** C-RQ-02  
**Status:** `OPEN — ACTIVE GATE / HANDOFF READY / SEARCH NOT STARTED`  
**Registered:** 2026-08-26  
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

## Exclusions

- prior adoption of Poisson arrivals, independence or stationarity without evidence;
- numerical parameters without provenance;
- final codeword organization/interleaving choice;
- conversion of specific COSRAD outputs into an online controller signal;
- adaptive policy selection;
- automatic reinterpretation of `E_cap` as a decoder or system outcome.

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

## Evidence needed

- primary irradiation studies for SRAM;
- empirical SEU, MCU and MBU evidence;
- published stochastic/probabilistic error models;
- evidence that tests independence, stationarity and spatial/temporal correlation assumptions;
- model-validation studies in comparable conditions;
- evidence on mechanism provenance and topology needed to calculate `E_cap`;
- evidence sufficient to trigger or dismiss the C-RQ-05 escalation gate.

## Answer / decision criterion

RQ is answerable when:

1. relevant model classes are enumerated;
2. assumptions, parameters, observed level and validity domain are recorded for each;
3. a minimum adequate model or a small justified alternative set is selected;
4. excluded effects and bounds are explicit;
5. compatibility with the DEC-001 event, domain, window and initial-state contract is demonstrated.

**Decision gate:** if evidence shows that MCU/MBU or spatial correlation materially changes the structure or probability of `E_cap`, or their exclusion cannot be justified or bounded, C-RQ-05 must be promoted to a mandatory permanent RQ and answered before the main reliability model is built.

## Active gate / next action

Prepare the exact Literature Scout handoff and execute the expanded cross-publisher [`RQ-002_protocol.md`](../literature_mapping/RQ-002_protocol.md): IEEE Xplore; one independent cross-publisher index or explicit public fallback; targeted ScienceDirect/SpringerLink; Scite/ResearchRabbit expansion; NASA NTRS supplemental coverage. During screening, collect explicit evidence for the C-RQ-05 escalation rule.

The mapping has not started. eLibrary remains `DEFERRED / UNKNOWN COVERAGE` because it is unavailable to Literature Scout.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-003.
- Input decision: `DEC-001`.
- Conditional dependency: C-RQ-05.
- PAPER/CLM/EVD/HYP/EXP: TBD after targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Not assessed.
