# RQ-001 — Provisional definition package

**Status:** `PROPOSED — PENDING USER APPROVAL`  
**Date:** 2026-08-27  
**Related RQ:** `RQ-001`  
**Evidence basis:** `PAPER-001…003`, `RQ-001-EVIDENCE-AUDIT-01`, `CLM-001…008`  
**Numerical reliability requirement:** `TBD`

This package proposes a project definition for approval. It is not yet a `DEC-xxx`, does not close `RQ-001`, and does not select a numerical reliability threshold.

## 1. Decision requested

Approve, amend, or reject the proposed:

1. primitive reliability event;
2. primary metric;
3. default aggregation boundary;
4. exposure and reporting horizons;
5. separation between physical ECC-capability exceedance and decoder/system outcomes;
6. assumptions and unresolved dependencies.

## 2. Known from accepted evidence

- `[SOURCE SYNTHESIS]` The three accepted papers use an existential multi-error codeword state as their primitive failure event, although their aggregate objects and horizons differ.
- `[SUPPORTED INFERENCE]` An upset-count-conditioned probability cannot be treated as a time-domain or mission-domain probability without an arrival and repair/reset model (`CLM-001`).
- `[SOURCE]` Harmful same-particle MBU lies outside the main isolated-upset equation of `PAPER-001` (`CLM-002`).
- `[SUPPORTED INFERENCE]` The analytical totals in `PAPER-002` and `PAPER-003` do not preserve direct-MCU versus independent-arrival provenance (`CLM-003`, `CLM-004`).
- `[SUPPORTED INFERENCE]` Adding an overlapping direct-MCU term to either unpartitioned total can repeat event histories (`CLM-005`, `CLM-006`).
- `[SOURCE]` The `PAPER-002` upper-bound interpretation is conditional on MCU span relative to interleaving distance (`CLM-007`).
- `[SUPPORTED SYNTHESIS]` The three papers model multiplicity beyond correction capability rather than an observed decoder or system-service outcome (`CLM-008`).

## 3. Proposed primitive reliability event

Let:

- `A` be an explicitly named protected SRAM aggregate containing ECC codewords;
- `W` be the physical-cell-to-codeword mapping;
- `t_c` be the number of distinct erroneous bits that the selected ECC is guaranteed to correct in one codeword;
- `N_w(t)` be the number of distinct erroneous bit cells currently present in codeword `w`, after accounting for its most recent successful correction/writeback.

Proposed primitive event over operating interval `H`:

\[
E_{cap}(A,H)=
\left\{
\exists\,t\in H,\;\exists\,w\in A:
N_w(t)>t_c
\right\}.
\]

For a SEC abstraction, `t_c=1`, so the event is the existence of at least two distinct erroneous bits in one codeword before successful correction.

**Proposed interpretation:** `ECC capability-exceedance event`.

This is a physical/codeword-state event. It must not automatically be called DUE, SDC, miscorrection or system failure.

## 4. Proposed primary metric

Define the first event time:

\[
\tau_A=
\inf\left\{
t:\exists w\in A,\;N_w(t)>t_c
\right\}.
\]

Proposed primary metric for a declared reporting horizon `H`:

\[
F_A(H)=\Pr\{\tau_A\le H\},
\qquad
R_A(H)=1-F_A(H).
\]

- `F_A(H)` and `R_A(H)` are dimensionless.
- Hazard, rate, MTTF or FIT may be derived only when their stochastic assumptions and units are explicitly stated.
- An upset-count-conditioned curve may be an intermediate conditional model, but it is not the primary operational metric.

Proposed requirement form:

\[
F_A(H_{req})\le \varepsilon_{req}.
\]

Both `H_req` and `ε_req` require traceable system/mission provenance. Until then they remain `TBD`.

## 5. Proposed aggregation boundary

### Primitive level

One ECC codeword.

### Default model aggregate

The complete SRAM region protected and scrubbed by the modeled controller, represented as an explicit set `A` of codewords.

Required parameters include:

- number of codewords;
- codeword composition, including treatment of check bits;
- bank/block partition if it changes arrival or repair semantics;
- mapping `W` or an explicitly declared mapping abstraction.

### Not implied

The event does not by itself establish bank outage, device loss, memory-service interruption or system failure. Those require an additional consequence/aggregation model.

## 6. Proposed horizon semantics

Three layers must remain distinct:

1. **Upset-count horizon** — an intermediate conditional variable only.
2. **Codeword exposure horizon** — time since the most recent successful correction/writeback of each codeword.
3. **Reporting horizon `H`** — the operating or mission interval over which the first-passage probability is reported.

For sequential scrubbing, codewords may have different exposure ages. A scalar `T_scr` must therefore be defined operationally as either:

- maximum revisit time between successful corrections of the same word; or
- full-sweep period under an explicit approximation relating it to per-word exposure age.

An instantaneous synchronous global reset is not adopted as a literature-established fact. It may be introduced later only as an explicit approximation with a stated validity domain.

## 7. Mechanism accounting rule

The same capability-exceedance event can be reached through:

- a direct same-particle multi-error codeword mechanism;
- accumulation of errors from multiple independent arrivals;
- other mechanisms retained by the selected RQ-002 model.

Before separate mechanism probabilities or rates are added, their upstream sample spaces must be mutually exclusive or their intersection must be handled explicitly. Probabilities/rates may be combined only when event definition, aggregate, horizon and units match.

This rule does not yet select the stochastic error model; that remains RQ-002.

## 8. Decoder and system outcomes

Proposed layered semantics:

1. `E_cap` — ECC correction capability exceeded;
2. decoder outcome — detected uncorrectable, miscorrection, silent corruption or other outcome;
3. system consequence — service degradation, loss of data integrity, recovery action or system failure.

Only layer 1 is proposed for the current primitive RQ-001 event. Layer 2 depends on RQ-003. Layer 3 requires system architecture/requirements.

## 9. Assumptions required for any quantitative use

- codeword definition and correction capability are explicit;
- physical/logical mapping `W` is explicit or its abstraction is declared;
- accumulation state resets only after a defined successful correction/writeback;
- arrival and spatial-correlation assumptions are stated and later justified by RQ-002;
- aggregation set `A` and reporting horizon `H` are named;
- probabilities and rates are not mixed;
- direct and accumulation contributions are disjoint or combined through explicit event algebra;
- numerical requirement provenance is traceable.

## 10. Alternatives considered

| Alternative | Disposition | Rationale |
|---|---|---|
| Primitive event = ECC capability exceedance | `RECOMMENDED` | Supported across the bounded evidence set and does not invent decoder/system consequences |
| Primitive event = DUE or SDC | `DEFER` | Requires concrete ECC/decoder semantics from RQ-003 |
| Primitive event = system-visible service loss | `DEFER` | Requires system architecture and consequence model |
| Primary horizon = accumulated upset count | `REJECT AS PRIMARY` | Not an operational time horizon without additional layers |
| Primary aggregate = one preselected word | `REJECT AS PROJECT DEFAULT` | Does not directly express failure somewhere in the protected SRAM region |
| Synchronous global reset at each scrub boundary | `NOT ADOPTED` | Current evidence supports missing sequential ages but does not establish a global-reset interpretation |

## 11. Known, assumed and unknown after proposed approval

### Known / evidence-supported

- the primitive multiplicity event is literature-grounded;
- aggregation and horizon must be explicit;
- count, time, scrub-cycle and mission horizons are not interchangeable;
- mechanism provenance matters for double-counting control.

### Proposed working choices

- use `E_cap` as the primitive event;
- use `F_A(H)` as primary metric;
- use the complete controller-protected SRAM region as default aggregate;
- represent sequential word exposure ages unless a simpler approximation is explicitly justified.

### Remains unknown or TBD

- exact ECC and `t_c` beyond the SEC starting abstraction;
- DUE/SDC/miscorrection mapping;
- target physical mapping `W`;
- stochastic arrival/correlation model;
- mission aggregation for nonstationary conditions;
- `H_req` and `ε_req`;
- system-visible consequence model.

## 12. Proposed RQ-001 disposition after approval

If this package is approved:

- RQ-001 becomes `PARTIALLY ANSWERED / OPEN DEPENDENCIES`;
- the primitive event, metric form and default aggregation semantics are accepted;
- numerical requirement and decoder/system consequences remain `TBD/UNKNOWN`;
- RQ-002 may start, because the event and metric that its error model must support will be defined;
- RQ-003 remains responsible for decoder-outcome refinement.

If the package is not approved, RQ-001 remains `INVESTIGATING` and RQ-002 stays queued.

## 13. Explicit approval questions

1. Approve `E_cap(A,H)` as the primitive reliability event?
2. Approve `F_A(H)=Pr{τ_A≤H}` as the primary metric form?
3. Approve the complete controller-protected SRAM region as the default aggregate?
4. Approve the distinction between upset-count, per-codeword exposure and reporting/mission horizons?
5. Approve leaving DUE/SDC/system consequence and `H_req`, `ε_req` unresolved?
6. Approve RQ-001 status `PARTIALLY ANSWERED / OPEN DEPENDENCIES` after these choices are accepted?
