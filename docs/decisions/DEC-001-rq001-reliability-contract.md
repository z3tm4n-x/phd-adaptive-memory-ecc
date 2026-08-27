# DEC-001 — RQ-001 working reliability event, metric, aggregate and horizon semantics

**Decision:** Accept the bounded working reliability contract defined below.  
**Date:** 2026-08-27  
**Status:** `ACCEPTED`  
**Related RQ:** `RQ-001`  
**Enables:** `RQ-002` targeted literature mapping  
**Does not close:** `RQ-001`

## Context

RQ-001 required a primitive reliability event, a measurable probability form, an aggregation boundary and explicit horizon semantics for ECC-protected SRAM with scrubbing. The decision is based on `PAPER-001…003`, the initial cross-paper synthesis, Evidence Audit `RQ-001-EVIDENCE-AUDIT-01` and `CLM-001…008`.

The evidence supports a bounded ECC-capability-exceedance state, but it does not establish decoder-visible or system-visible consequences, a numerical reliability requirement, a target physical mapping, or a complete stochastic error model.

## Decision

### 1. Primitive event

Let:

- \(A\) be an explicitly declared controller-managed SRAM protection domain;
- \(w\in A\) be an ECC codeword;
- \(t_c(w)\) be the number of distinct erroneous bits the declared ECC configuration guarantees to correct in \(w\);
- \(N_w(t)\) be the current number of distinct erroneous bit cells in \(w\), under the declared correction/writeback semantics;
- \(H(t_0,T)=[t_0,t_0+T]\), where \(T\ge 0\), be the reporting window.

The accepted primitive event is

\[
E_{\mathrm{cap}}(A;t_0,T)=
\left\{
\exists\,t\in[t_0,t_0+T],\ \exists\,w\in A:
N_w(t)>t_c(w)
\right\}.
\]

For a homogeneous SEC abstraction, \(t_c=1\), so the event occurs when at least one codeword contains at least two distinct erroneous bits before the relevant successful correction/writeback.

`E_cap` is an `ECC-capability-exceedance event` at the physical/codeword-state layer. It is not automatically equivalent to DUE, SDC, miscorrection, loss of data, memory-service loss or system-visible failure.

### 2. Metric and initial-state semantics

For a quantitative model, let \(\mu_{t_0}\) denote the declared state or state distribution at the start of the reporting window. It must cover every state variable needed by the model, including, where applicable:

- the erroneous-bit state of the protected words;
- the last successful correction/writeback time or exposure age of each word;
- controller/scrubber phase and scan position;
- environmental or latent state required by a nonstationary arrival model.

Define

\[
\tau_A(t_0)=
\inf\left\{
t\ge t_0:\exists\,w\in A,\ N_w(t)>t_c(w)
\right\}.
\]

The accepted general metric is

\[
F_A(t_0,T;\mu_{t_0})=
\Pr_{\mu_{t_0}}
\left\{
\tau_A(t_0)\le t_0+T
\right\},
\qquad
R_A(t_0,T;\mu_{t_0})=1-F_A(t_0,T;\mu_{t_0}).
\]

`F_A` and `R_A` are dimensionless; `t_0` and `T` use explicitly declared, compatible time units.

`F_A(t0,T)` is an admissible abbreviation only when \(\mu_{t_0}\) is fixed elsewhere in the model specification. The shorter form

\[
F_A(T)=\Pr\{\tau_A\le T\}
\]

is admissible only when the time origin, initial state/distribution and conditioning assumptions are explicit. For a nonstationary model, start-time/window semantics must be retained unless time-origin invariance has been established.

Hazard, rate, MTTF, MTBF or FIT may be derived only with explicit stochastic assumptions and units.

### 3. Aggregation domain and partitioning

The default aggregate is not an implicitly homogeneous “whole memory.” It is an explicitly declared controller-managed SRAM protection domain \(A\).

If any of the following differ within \(A\), the domain must be partitioned before quantitative aggregation:

- ECC configuration or correction capability;
- physical-cell-to-codeword mapping \(W\);
- arrival process or its parameters;
- bank/block organization relevant to the event;
- scrubbing, correction or writeback semantics.

Use an explicit disjoint partition

\[
A=\biguplus_{j=1}^{m} A_j.
\]

For the domain event,

\[
E_{\mathrm{cap}}(A;t_0,T)
=
\bigcup_{j=1}^{m}
E_{\mathrm{cap}}(A_j;t_0,T).
\]

The aggregate probability must follow the declared joint model. Independence between partitions, product-form reliability and simple addition of rates are not assumed automatically.

### 4. Horizon and scrubbing semantics

The model must distinguish:

1. upset-count horizon — an intermediate conditional variable;
2. per-codeword exposure horizon — time since the relevant successful correction/writeback;
3. reporting window \(H(t_0,T)\);
4. mission aggregation, when it spans multiple reporting or repair windows.

Per-codeword/sequential exposure semantics are accepted as a `WORKING DEFINITION / MODELING REQUIREMENT`. They are not recorded as a literature-established fact. `RQ001-EA-CAND-10` remains deferred.

An instantaneous synchronous global reset may be used only as an explicit approximation with a stated validity domain.

### 5. Open outcome and requirement semantics

The following remain `OPEN/TBD`:

- DUE, SDC and miscorrection semantics;
- mapping from `E_cap` to decoder outputs;
- system-visible consequence and service-failure semantics;
- the required reporting window \(H_{\mathrm{req}}\);
- the numerical bound \(\varepsilon_{\mathrm{req}}\).

If a quantitative requirement is later available, its general form may be written as

\[
F_A(t_{0,\mathrm{req}},T_{\mathrm{req}};\mu_{t_{0,\mathrm{req}}})
\le \varepsilon_{\mathrm{req}},
\]

with \(H_{\mathrm{req}}=[t_{0,\mathrm{req}},t_{0,\mathrm{req}}+T_{\mathrm{req}}]\). Every numerical value and conditioning assumption requires traceable system/mission provenance.

## Known

- The three accepted papers use an existential codeword state beyond modeled correction capability, while their aggregates and horizons differ.
- Upset-count probability cannot become time/mission probability without arrival and repair semantics (`CLM-001`).
- The accepted evidence does not equate multiplicity beyond correction capability with a decoder or service outcome (`CLM-008`).
- Mechanism populations must be partitioned or combined with explicit event algebra to avoid overlap (`CLM-002…006`).

## Working definitions / modeling requirements

- `E_cap` is the primitive event.
- `F_A(t0,T; μ_t0)` is the general probability form.
- \(A\) is an explicitly declared controller-managed protection domain.
- Heterogeneous domains are partitioned before aggregation.
- Initial state/distribution and sequential word exposure semantics are part of the quantitative model specification.

These are project decisions motivated by evidence; they are not presented as universal literature facts.

## Unknown / TBD

- the adequate radiation-induced error-arrival and correlation model — `RQ-002`;
- concrete ECC/decoder outcomes and \(t_c(w)\) semantics — `RQ-003`;
- target mapping \(W\);
- mission aggregation under nonstationary conditions;
- system-visible consequences;
- \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\).

## Alternatives considered

| Alternative | Disposition | Rationale |
|---|---|---|
| DUE or SDC as primitive event | Deferred | Requires concrete decoder semantics from RQ-003 |
| System-visible failure as primitive event | Deferred | Requires a consequence/service model |
| Accumulated upset count as primary horizon | Rejected | Not an operational time window without arrival and repair layers |
| Scalar endpoint without start-time semantics | Restricted shorthand only | Invalid for a general nonstationary model |
| Implicitly homogeneous complete memory | Rejected | Can hide incompatible ECC, mapping, arrival and scrubbing semantics |
| Synchronous global reset as literature fact | Not accepted | CAND-10 remains deferred |

## Rationale

This contract is the smallest decision that makes RQ-002 answerable without inventing decoder outcomes, system requirements or a stochastic process. It preserves nonstationary start-time semantics, prevents invalid aggregation across heterogeneous memory regions and separates project modeling requirements from literature-supported claims.

## Evidence

- [RQ-001 initial evidence synthesis](../evidence_synthesis/RQ-001_initial_evidence_synthesis.md)
- [RQ-001 Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md)
- [CLM-001…008 registry](../claims/README.md)
- [PAPER-001…003 registry](../paper_cards/README.md)

## Consequences

- `RQ-001` becomes `PARTIALLY ANSWERED / OPEN DEPENDENCIES`, not closed.
- The RQ-002 gate is opened; literature search is not started by this decision.
- RQ-002 must evaluate error models against `E_cap`, the declared domain/partition and `F_A(t0,T; μ_t0)`.
- RQ-003 retains responsibility for decoder-outcome semantics.
- No numerical reliability requirement is assigned.
- No `HYP-xxx`, `EVD-xxx` or `RES-xxx` is created.

## Revisit when

Revisit this decision if:

- RQ-002 evidence makes the event state, partitioning rule or state variables inadequate;
- RQ-003 establishes decoder semantics that require a different primitive or additional outcome layer;
- a target SRAM architecture, mapping \(W\), scrub implementation or mission requirement is selected;
- a traceable system/mission requirement supplies \(H_{\mathrm{req}}\) or \(\varepsilon_{\mathrm{req}}\);
- evidence resolving CAND-10 materially changes the exposure-age model.
