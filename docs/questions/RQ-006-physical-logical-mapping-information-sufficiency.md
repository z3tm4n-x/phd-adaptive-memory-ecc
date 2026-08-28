# RQ-006 — Physical-to-logical mapping and information sufficiency

**Title:** Physical-to-logical mapping and information sufficiency for ECC-aware SRAM reliability<br>
**Source candidate:** C-RQ-05<br>
**Status:** `OPEN / REGISTERED / PROTOTYPE-COUPLED`<br>
**Registered:** 2026-08-28 by explicit PI approval<br>
**Escalation basis:** accepted RQ-002 synthesis and [Evidence Audit 01](../evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md)

## Question

Какое минимальное представление физической топологии радиационного события и физико-логического отображения памяти `W` необходимо сохранять, чтобы корректно получить совместное воздействие события на ECC-кодовые слова и вычислять `E_cap` / `F_A(t0,T;μ_t0)`; при каких условиях редукция к marginal per-word multiplicities, multiplicity/rate statistics или исключение interleaving является точной, даёт проверяемую границу либо приемлемую аппроксимацию?

## Why it matters

Одинаковая физическая multiplicity не определяет ECC-level impact без размещения затронутых ячеек и `W`. Одновременно полная физическая топология может быть недоступна или избыточна. Поэтому основной вопрос — не «сохранять всё», а установить минимальную достаточную post-`W` информацию, её идентифицируемость и количественную цену дальнейшей редукции для reliability assessment и управляющего решения.

## Scope

- physical cell/address coordinates, event multiplicity and spatial topology before `W`;
- declared physical-cell-to-codeword mapping `W`, including interleaving, bank/block and word organization;
- parent-event provenance and joint post-`W` codeword-impact marks;
- the representation ladder: full physical topology + `W` → joint post-`W` mark → marginal per-word multiplicities → scalar rate;
- information preserved/lost at each reduction and the dependencies discarded;
- exactness, equivalence, conservative bounds, approximation error and systematic bias for `E_cap` and `F_A`;
- distinguishability/identifiability of required inputs from realistic irradiation-test observations;
- propagation of mapping/classification uncertainty into ECC-level reliability and a parameterized restoration decision;
- computational tractability of the retained representation.

## Exclusions

- selecting the temporal arrival-process family, which remains RQ-002 responsibility;
- defining DUE, SDC, miscorrection or other decoder/service outcomes, which remains RQ-003 responsibility;
- assuming that richer topology is always necessary, observable or superior;
- choosing a target interleaving layout or distance without a declared architecture and data;
- selecting the adaptive control law or scalar resource objective;
- treating logical addresses observed during tests as physical coordinates without a documented transformation;
- claiming a deficiency in Russian normative practice before the bounded normative extraction is accepted;
- permanent faults, cumulative TID degradation and destructive/persistent SEE mechanisms unless separately reopened.

## Dependencies

- [RQ-001 / DEC-001](../decisions/DEC-001-rq001-reliability-contract.md) supplies `E_cap`, `F_A`, `A`, horizon and initial-state semantics.
- [RQ-002](RQ-002-sram-radiation-error-model.md) supplies the bounded arrival/event/state representation and explicit repair semantics.
- [RQ-003](RQ-003-ecc-abstraction-baseline-class.md) supplies concrete ECC capability and decoder-outcome semantics.
- [DEC-002](../decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md) requires the mapping output to remain part of the evidence-to-adaptive-decision chain.
- The [normative-baseline protocol](../normative_baseline/NORMATIVE-BASELINE-01_protocol.md) determines which pre-`W` information is actually retained or reconstructible in the provided Russian test/calculation chain.

## Evidence needed

- accepted `PAPER-004…008`, with particular weight on mapping/topology comparisons and observation ambiguity;
- accepted RQ-002 Evidence Audit propositions 01–04, 07 and 09 in their scoped wording;
- bounded extraction from `РД 134-0174-2009`, `РД 134-0175-2009` and `СТО ГК Роскосмос 04.01.0005–2022`;
- a controlled quantitative comparison under common event streams, `A`, `W`, ECC capability, initial state and scrub semantics;
- exact or empirical equivalence checks between full-topology and joint post-`W` representations;
- error/bound/decision-change evidence for marginal and scalar reductions;
- target-specific mapping or test-log evidence before any device-specific conclusion.

## Answer / decision criterion

RQ-006 is answerable when:

1. the physical, observational and logical objects on both sides of `W` are formally distinguished;
2. a minimal lossless post-`W` representation is stated for the declared `E_cap` computation;
3. each further reduction has an exactness theorem, a verified bound or a measured approximation error over a declared validity domain;
4. joint inter-word dependence is either retained or shown irrelevant/bounded for the queried aggregate;
5. required test observables and their reconstruction/classification uncertainty are stated;
6. the effect of representation reduction is quantified for `F_A` and for at least one parameterized restoration-regime decision;
7. computational cost and target-specific data requirements are explicit;
8. interfaces to RQ-002, RQ-003 and RQ-004 are recorded without duplicating their responsibilities.

## Next action

Implement [EXP-001](../../experiments/EXP-001-event-representation-reduction-sensitivity.md), beginning with a lossless full-topology → joint post-`W` equivalence check and then testing marginal/scalar reductions under the same event streams. The normative extraction runs as a parallel input on real test-data availability, not as a blocker for the synthetic prototype.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-002, RQ-003, RQ-004.
- Decisions: DEC-001, DEC-002, DEC-003.
- Evidence: PAPER-004…008; RQ-002 Evidence Audit 01.
- Experiment: EXP-001.
- HYP/RES: none registered.

## Answer

UNKNOWN.

## Confidence

Not assessed.
