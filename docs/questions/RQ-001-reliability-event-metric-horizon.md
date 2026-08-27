# RQ-001 — Reliability event, metric and evaluation horizon for ECC-protected SRAM

**Title:** Reliability event, metric and evaluation horizon for ECC-protected SRAM  
**Source candidate:** C-RQ-01  
**Status:** `PARTIALLY ANSWERED — OPEN DEPENDENCIES`  
**Registered:** 2026-08-26  
**Decision recorded:** 2026-08-27 as [DEC-001](../decisions/DEC-001-rq001-reliability-contract.md)

## Question

Как должны быть определены reliability event, соответствующая метрика, уровень агрегации и временной горизонт для SRAM, защищённой ECC и периодическим scrubbing, чтобы сформулировать проверяемое ограничение надёжности?

## Why it matters

Без явного события, метрики и горизонта нельзя однозначно построить reliability model, сравнить варианты ECC/scrubbing или проверить выполнение ограничения надёжности.

## Scope

- primitive ECC-capability-exceedance event;
- codeword and controller-managed protection-domain aggregation;
- reporting-window and initial-state semantics;
- per-codeword exposure under scrubbing;
- separation from decoder and system-visible outcomes;
- form, but not numerical value, of a future reliability constraint.

## Exclusions

- arbitrary numerical reliability requirement;
- selection of the stochastic radiation-error model;
- final ECC/decoder choice;
- resource-cost vector or adaptive policy;
- target-platform parameters without provenance.

## Evidence basis

- Literature discovery: `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`.
- eLibrary: `DEFERRED / UNKNOWN COVERAGE`.
- Accepted Paper Cards: [PAPER-001](../paper_cards/PAPER-001-tausch-2009.md), [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md).
- [Initial cross-paper synthesis](../evidence_synthesis/RQ-001_initial_evidence_synthesis.md).
- [Accepted Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md).
- Accepted claims: [CLM-001…008](../claims/README.md).
- Approved definition package: [record](../evidence_synthesis/RQ-001_provisional_definition_package.md).

## Partial answer accepted by DEC-001

### Primitive event

For reporting window \(H(t_0,T)=[t_0,t_0+T]\),

\[
E_{\mathrm{cap}}(A;t_0,T)=
\{\exists t\in H(t_0,T),\ \exists w\in A:N_w(t)>t_c(w)\}.
\]

This is an ECC-capability-exceedance state. It is not automatically DUE, SDC, miscorrection or system-visible failure.

### Metric

With declared initial state/distribution \(\mu_{t_0}\),

\[
F_A(t_0,T;\mu_{t_0})
=
\Pr_{\mu_{t_0}}\{\tau_A(t_0)\le t_0+T\}.
\]

`F_A(t0,T)` is shorthand only when \(\mu_{t_0}\) is fixed elsewhere. `F_A(T)=Pr{τ_A≤T}` is allowed only for an explicit time origin and initial state/distribution. Nonstationary models retain start-time semantics.

### Aggregate

\(A\) is an explicitly declared controller-managed SRAM protection domain. If ECC, mapping \(W\), arrival process, bank/block semantics or scrubbing/correction semantics differ within \(A\), use an explicit disjoint partition \(A=\biguplus_j A_j\) before quantitative aggregation. Dependence between partitions must be modeled.

### Horizons

Upset-count, per-codeword exposure, reporting-window and mission horizons remain distinct. Per-codeword/sequential exposure is a `WORKING DEFINITION / MODELING REQUIREMENT`, not a literature-established fact. CAND-10 remains deferred.

### Requirement boundary

A future requirement may use

\[
F_A(t_{0,\mathrm{req}},T_{\mathrm{req}};\mu_{t_{0,\mathrm{req}}})
\le \varepsilon_{\mathrm{req}},
\]

but \(H_{\mathrm{req}}\), \(\varepsilon_{\mathrm{req}}\), decoder outcomes and system consequences remain `OPEN/TBD`.

## Dependencies / unresolved elements

- RQ-002 — error-arrival, multiplicity, correlation and nonstationarity model.
- RQ-003 — ECC capability and decoder-outcome semantics.
- Target mapping \(W\) and target architecture.
- Mission aggregation and system consequence model.
- Traceable system/mission reliability requirement.
- Deferred CAND-10 if its resolution materially changes exposure semantics.

## Answer / decision criterion

The primitive event, metric form, domain/partition rule and horizon semantics are answered at working-definition level. RQ-001 remains open until dependencies needed for quantitative use and decoder/system interpretation are resolved or explicitly bounded.

## Next action

Use DEC-001 as the input contract for RQ-002. Revisit RQ-001 after RQ-002 and RQ-003 decisions or when traceable system requirements become available.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-002, RQ-003.
- PAPER: `PAPER-001…003`.
- CLM: `CLM-001…008`.
- DEC: `DEC-001`.
- HYP/EXP: none.

## Answer

`PARTIAL.` The project adopts `E_cap`, `F_A(t0,T; μ_t0)`, an explicitly declared and, where necessary, partitioned controller-managed domain \(A\), and layered horizon semantics. Decoder/system outcomes and numerical requirements remain open.

## Confidence

High that the decision is traceable to the bounded evidence and explicit project constraints. Model adequacy remains unassessed until RQ-002 and RQ-003 are answered.
