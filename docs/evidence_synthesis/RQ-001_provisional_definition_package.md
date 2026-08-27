# RQ-001 — Accepted definition package

**Status:** `APPROVED WITH CLARIFICATIONS — RECORDED AS DEC-001`  
**Approved:** 2026-08-27  
**Related RQ:** `RQ-001`  
**Canonical decision:** [DEC-001](../decisions/DEC-001-rq001-reliability-contract.md)  
**Evidence basis:** `PAPER-001…003`, `RQ-001-EVIDENCE-AUDIT-01`, `CLM-001…008`  
**Numerical reliability requirement:** `TBD`

This document records the disposition of the six approval questions. `DEC-001` is authoritative if a concise decision record is needed. Approval does not close RQ-001 and does not assign a numerical reliability threshold.

## 1. Approval disposition

1. `APPROVED` — `E_cap` is the primitive ECC-capability-exceedance event and is not automatically DUE, SDC, miscorrection or system-visible failure.
2. `APPROVED WITH CLARIFICATION` — the general metric preserves reporting-window start time and initial-state semantics.
3. `APPROVED WITH CLARIFICATION` — the default aggregate is an explicitly declared controller-managed protection domain \(A\), partitioned before aggregation when its internal semantics differ.
4. `APPROVED` — upset-count, per-codeword exposure and reporting/mission horizons remain distinct; sequential exposure is a working modeling requirement, not a literature fact. CAND-10 remains deferred.
5. `APPROVED` — decoder/system outcomes, \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) remain `OPEN/TBD`.
6. `APPROVED` — RQ-001 becomes `PARTIALLY ANSWERED / OPEN DEPENDENCIES` and the RQ-002 gate opens.

## 2. Evidence boundary

### Known from accepted evidence

- The accepted papers use an existential codeword state beyond modeled correction capability, but differ in aggregate and horizon.
- A count-conditioned probability requires an arrival and repair model before time interpretation (`CLM-001`).
- The papers do not establish decoder/service outcomes for the multiplicity event (`CLM-008`).
- Direct and accumulation mechanisms require explicit event-population accounting (`CLM-002…006`).

### Working definitions / modeling requirements

- reporting-window and initial-state semantics;
- explicitly declared controller-managed domain and required partitioning;
- per-codeword exposure state for sequential scrubbing unless a simpler approximation is justified.

These are accepted project definitions, not asserted literature facts.

### Unknown / TBD

- error-arrival/correlation model;
- concrete decoder outcomes;
- target mapping \(W\);
- nonstationary mission aggregation;
- system consequence model;
- \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\).

## 3. Accepted primitive event

Let \(H(t_0,T)=[t_0,t_0+T]\). For an explicitly declared controller-managed SRAM protection domain \(A\),

\[
E_{\mathrm{cap}}(A;t_0,T)=
\left\{
\exists\,t\in[t_0,t_0+T],\ \exists\,w\in A:
N_w(t)>t_c(w)
\right\}.
\]

For homogeneous SEC, \(t_c=1\). This is a physical/codeword-state event only.

## 4. Accepted metric

Let \(\mu_{t_0}\) be the declared initial state or state distribution and

\[
\tau_A(t_0)=
\inf\{t\ge t_0:\exists\,w\in A,\ N_w(t)>t_c(w)\}.
\]

The general metric is

\[
F_A(t_0,T;\mu_{t_0})
=
\Pr_{\mu_{t_0}}\{\tau_A(t_0)\le t_0+T\}.
\]

`F_A` is dimensionless; `t_0` and `T` require explicit, compatible time units.

`F_A(t0,T)` may abbreviate this only when \(\mu_{t_0}\) is fixed elsewhere. `F_A(T)=Pr{τ_A≤T}` is allowed only for an explicit origin and initial state/distribution. Nonstationary models retain \(t_0\) unless time-origin invariance is established.

The model specification must declare the initial erroneous-bit state and any relevant word ages, scrubber phase and environmental/latent state.

## 5. Accepted aggregation rule

\(A\) is the declared controller-managed SRAM protection domain. If ECC, \(W\), arrival process, bank/block organization or scrubbing/correction semantics differ inside it, use

\[
A=\biguplus_{j=1}^{m} A_j
\]

before quantitative aggregation. Then

\[
E_{\mathrm{cap}}(A;t_0,T)=
\bigcup_j E_{\mathrm{cap}}(A_j;t_0,T).
\]

Dependence between partitions must be modeled; independence or additive rates are not assumed automatically.

## 6. Accepted horizon semantics

Keep distinct:

1. upset-count horizon;
2. per-codeword exposure since successful correction/writeback;
3. reporting window \(H(t_0,T)\);
4. mission aggregation across windows or repair cycles.

Per-codeword/sequential exposure is a `WORKING DEFINITION / MODELING REQUIREMENT`. CAND-10 remains deferred, and synchronous global reset is not adopted as a literature-established fact.

## 7. Requirement and outcome boundary

A future requirement may take the form

\[
F_A(t_{0,\mathrm{req}},T_{\mathrm{req}};\mu_{t_{0,\mathrm{req}}})
\le \varepsilon_{\mathrm{req}},
\]

but \(H_{\mathrm{req}}\), \(\varepsilon_{\mathrm{req}}\), DUE, SDC, miscorrection and system-visible consequences remain `OPEN/TBD` pending traceable evidence or system requirements.

## 8. Consequences

- RQ-001: `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 gate: open; targeted literature search not yet run.
- RQ-003: retains decoder-outcome responsibility.
- No numerical threshold, hypothesis or project result is created.
