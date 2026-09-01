# DRAFT — RQ-007 PA-DOM-01…04 common comparison matrix

**Task:** `PA-DOM-04-CANONICAL-REUSE-01`

**Related RQs:** `RQ-002`, `RQ-003`, `RQ-005`, `RQ-006`, `RQ-007`

**Canonical base:** `83d4db20ce43ff238d58551610f487e7cf3c2c6e`

**Lifecycle:** draft synthesis artefact; no permanent identifier assigned

**PA-DOM-04 disposition:** `CLOSED BY CANONICAL REUSE`

## Scope and evidence discipline

This draft populates PA-DOM-04 only. It condenses the accepted
[PAPER-005](../paper_cards/PAPER-005-zebrev-2017-arxiv-v2.md) and accepted
[RQ-002 initial evidence synthesis](RQ-002_initial_evidence_synthesis.md). No
primary publication was opened or re-read for this task.

Labels retain the status already controlled in the accepted artefacts:

- `SOURCE` — a source-supported statement retained from PAPER-005;
- `INFERENCE` — an accepted project interpretation, not promoted to source fact;
- `UNKNOWN` — the accepted artefacts do not establish the proposition.

For PA-DOM-01…03 the exact placeholder required by the protocol is used. No
scientific content is inferred from project descriptions.

## Common comparison matrix

| Comparison field | PA-DOM-01 | PA-DOM-02 | PA-DOM-03 | PA-DOM-04 |
|---|---|---|---|---|
| 1. available input/observation | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — available reduced inputs include the LET-dependent mean cross section `σ(Λ)`, particle-flux spectrum `φ(Λ)`, cell area `a_c`, mean multiplicity `m(Λ)` or partial multiplicity probabilities when supplied, and ECC vulnerability coefficients `V_n`. `UNKNOWN` — no online controller observation is established in the accepted scope. [Trace T1](#trace-t1) |
| 2. reconstructed or assumed information | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — a conditional-on-LET multiplicity conjecture may reconstruct `p_n(Λ)` and hence partial cross sections/rates `R_n`; `V_n` then recombines multiplicity classes into an abstract ECC/system rate. The physical parent-event rate `Σ_n R_n` remains distinct from the bit/upset rate `Σ_n nR_n`. `INFERENCE` — this conditional multiplicity model must not be re-described as a temporal Poisson-arrival model. [Trace T2](#trace-t2) |
| 3. uncertainty/error and validity domain | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — the Poisson multiplicity law is a conjecture; the illustrated cross-section interpolation is approximate; the simple SEC-DED conversion requires `β≪1`, neglects `n≥3` contributions in Eqs. (17)–(18), and assumes that one half of two-fold MCUs enters one word. No parameter confidence intervals are propagated end to end. `INFERENCE` — Eq. (15) is an approximate additive construction, and its direct and sequential addends are not proved to be disjoint. `UNKNOWN` — no numerical validity boundary or error bound outside `β≪1` is established. [Trace T3](#trace-t3) |
| 4. position relative to `W` | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — physical multiplicity is partitioned before logical mapping. No explicit physical-cell-to-codeword map or topology is supplied; the later word-level conversion uses a statistical one-half allocation for two-fold events rather than an explicit `W`. `INFERENCE` — the scalar allocation is not a universal mapping and is insufficient for arbitrary target organizations without additional post-mapping information. [Trace T4](#trace-t4) |
| 5. ECC reliability object and horizon | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — Eqs. (13)–(14) define an abstract `R_syst` rate through multiplicity vulnerabilities, while Eqs. (15)–(19) give one simple SEC-DED illustration over an exogenous scrub interval `t_s` in the low-`β` regime. `INFERENCE` — the illustration implies a corrected/clean cycle start rather than a general `μ_t0`; neither `R_syst` nor the one-interval expression is DEC-001 `F_A(t0,T;μ_t0)` or automatically `E_cap`, DUE, SDC, miscorrection, or system-visible failure. [Trace T5](#trace-t5) |
| 6. restoration action and decision law | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — `t_s` is an exogenous scrub interval in a simple SEC-DED approximation; operational scan, correction/writeback, and sequential word-age semantics are not modeled. `UNKNOWN` — the accepted scope provides no adaptive action set, update rule, online estimator, or law selecting `T_scrub`. [Trace T6](#trace-t6) |
| 7. reliability guarantee/constraint | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — `β≪1` is a validity condition for the illustrative approximation. `INFERENCE` — it is not a project reliability requirement and must not be interpreted as `H_req` or `ε_req`. `UNKNOWN` — no DEC-001-compatible windowed reliability constraint or guarantee is provided in the accepted scope. [Trace T7](#trace-t7) |
| 8. resource-cost treatment | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `SOURCE` — the accepted synthesis characterizes the rate sums as closed-form and computationally inexpensive. `INFERENCE` — compact analytical form or computational simplicity is not a measured resource benefit. `UNKNOWN` — no RQ-005 resource-cost vector, controller overhead, bandwidth, energy, latency, or disturbance measurement is provided. [Trace T8](#trace-t8) |
| 9. exact distinction affecting the next RQ-007 method or experiment | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED | `INFERENCE` — PAPER-005 is an upstream reconstruction/rate comparator occupying a conditional multiplicity-reconstruction approach from reduced physical inputs. It is not an integrated `information → F_A → adaptive T_scrub` baseline. Whether its recovered information is sufficient for target `W`, DEC-001 `F_A`, and restoration selection remains a downstream open question. [Trace T9](#trace-t9) |

All nine PA-DOM-04 comparison fields are populated. Some propositions within
those fields remain explicitly `UNKNOWN`; none is a named canonical gap that
prevents this bounded matrix population.

## Traceability ledger

### Trace T1

- PAPER-005: Common extraction summary (`Count/arrival process`,
  `Stationarity/intensity`); §6 `Input parameters`; §§9.1–9.2, Eqs. (1)–(14),
  source pp. 1–4 as already controlled.
- RQ-002 synthesis: §3 `Common extraction matrix — process and event
  representation`; §9 `Incompatible aggregation levels`.

### Trace T2

- PAPER-005: §4 `Method`; §7 `Output parameters`; §§9.1–9.2, especially Eqs.
  (3)–(5), (8)–(11), and (13)–(14), source pp. 1–4 as already controlled; §15
  `What cannot legitimately be claimed`.
- RQ-002 synthesis: §3; §7 `Different definitions that must not be merged`; §9.

### Trace T3

- PAPER-005: §5 `Assumptions`; §§11–13; Mandatory questions 3, 7–11, and
  14–15 on Eqs. (15)–(19), source p. 4 as already controlled.
- RQ-002 synthesis: §5 `Common extraction matrix — evidence, validity, and
  contract fit`; §8 `Incompatible assumptions`; §11 work-unit WU1; §14
  `Alternatives narrowed or ruled insufficient as stand-alone models`.

### Trace T4

- PAPER-005: Common extraction summary (`Mapping W`); §§9.1 and 9.3; §§12 and
  18; Mandatory questions 6, 8, and 13, Eqs. (17)–(18), source p. 4 as already
  controlled.
- RQ-002 synthesis: §4 `Common extraction matrix — mapping, state, and repair`;
  §8; §12 `Unresolved model-selection gaps`.

### Trace T5

- PAPER-005: §7; §§9.2–9.3, Eqs. (13)–(19), source p. 4 as already controlled;
  §§13–16; Mandatory questions 1–2 and 10–11.
- RQ-002 synthesis: §5; §§9–10; §14.

### Trace T6

- PAPER-005: Common extraction summary (`Repair semantics`); §§3 and 6; §9.3,
  Eqs. (15)–(19), source p. 4 as already controlled; §§16 and 19.
- RQ-002 synthesis: §4; §10 `Incompatible horizons`; §12.

### Trace T7

- PAPER-005: §§5, 11, and 15; Mandatory questions 10–11, Eqs. (16)–(19), source
  p. 4 as already controlled.
- RQ-002 synthesis: §5; §14.

### Trace T8

- PAPER-005: §4; §9; §16.
- RQ-002 synthesis: §5 (`Computational tractability`); §12, gap 9.

### Trace T9

- PAPER-005: §§14–16; §§18–19.
- RQ-002 synthesis: §§12–15; §17 `Orchestrator disposition and downstream
  gate`.

## Fields retaining UNKNOWN propositions

The nine matrix fields are populated, but the accepted scope leaves the
following propositions `UNKNOWN` or not provided:

- an online controller observation and temporal stationarity/nonstationarity
  model;
- an explicit `W`, spatial topology, or sufficient joint post-mapping mark;
- a general `μ_t0`, sequential word ages, and operational
  correction/writeback/reset timing;
- the numerical boundary/error outside `β≪1` and a proof of disjoint
  direct-versus-sequential recombination;
- end-to-end uncertainty propagation into `F_A`;
- an adaptive action/update/selection law and DEC-001-compatible guarantee;
- an RQ-005 resource-cost vector and measured controller costs.

These absences remain downstream evidence/design gaps; they do not justify
opening the primary source in this bounded reuse task.

## Occupied method chains

- `SOURCE` — PAPER-005 occupies the chain `LET-dependent reduced physical
  inputs → conditional multiplicity reconstruction → multiplicity-resolved
  rates R_n → ECC vulnerability recombination → abstract R_syst`, with a
  separate low-`β` SEC-DED scrub-interval illustration (PAPER-005 §§4, 6, and
  9; RQ-002 synthesis §§3–5).
- `INFERENCE` — for RQ-007 this is an upstream reconstruction/rate chain, not a
  complete observation-to-control chain (PAPER-005 §§14–16; RQ-002 synthesis
  §§12–15 and 17).
- Cross-unit occupied-chain synthesis is pending PA-DOM-01…03.

## Mandatory baselines

- `INFERENCE` — the next quantitative comparison must preserve PAPER-005's
  distinction between physical-event rate, bit/upset rate, and abstract
  ECC/system recombination (PAPER-005 §§9.1–9.2; RQ-002 synthesis §§6 and 9).
- `INFERENCE` — Eqs. (2)–(14) are the reduced-input multiplicity/rate comparator;
  Eqs. (15)–(19) may be used only as the explicitly low-`β`, scalar-mapping
  illustrative SEC-DED comparator, not as an exact integrated baseline
  (PAPER-005 §§9–12; RQ-002 synthesis §§11 and 14).
- Cross-unit mandatory-baseline selection is pending PA-DOM-01…03.

## Mandatory design boundaries/non-claims

- `INFERENCE` — do not call the conditional-on-LET Poisson multiplicity law a
  temporal Poisson-arrival process (PAPER-005 §15; RQ-002 synthesis §7).
- `INFERENCE` — do not treat the scalar one-half allocation as a universal `W`
  or claim that multiplicity alone determines codeword harm under arbitrary
  organization (PAPER-005 §§12, 15, and 18; RQ-002 synthesis §§8 and 14).
- `INFERENCE` — do not claim Eq. (15) is exact or that its direct and sequential
  terms are mutually exclusive (PAPER-005 §12 and Mandatory questions 3 and 14;
  RQ-002 synthesis §§11 and 14).
- `INFERENCE` — do not identify `R_syst` with DEC-001 `F_A`, `E_cap`, DUE, SDC,
  miscorrection, or system-visible failure; do not reinterpret `β≪1` as a
  project reliability threshold (PAPER-005 §§13 and 15; RQ-002 synthesis §§5,
  10, and 14).
- `INFERENCE` — do not reclassify analytical compactness as a measured RQ-005
  resource benefit (PAPER-005 §§4 and 9; RQ-002 synthesis §5).
- Cross-unit design-boundary synthesis is pending PA-DOM-01…03.

## Assumptions to parameterize or test

- `SOURCE` — conditional multiplicity model, cross-section interpolation,
  `n≥3` omission in Eqs. (17)–(18), scalar one-half word allocation, and
  `β≪1` regime (PAPER-005 §§5 and 11; RQ-002 synthesis §§5 and 8).
- `INFERENCE` — target `W`/topology sufficiency, disjoint direct-versus-sequential
  recombination, temporal arrivals, general initial state/word ages, operational
  repair semantics, and uncertainty propagation require separate
  parameterization or tests (PAPER-005 §§12–13 and 19; RQ-002 synthesis §§12–15).
- Cross-unit assumption reconciliation is pending PA-DOM-01…03.

## Minimum RQ-003/RQ-004/RQ-005 implications

- `INFERENCE` — RQ-003 must supply target ECC capability/vulnerability and keep
  decoder outcomes separate from PAPER-005's abstract `R_syst` (PAPER-005 §§13
  and 15; RQ-002 synthesis §§5 and 12).
- `UNKNOWN` — PAPER-005 supplies no online observation interface for RQ-004;
  any runtime information source, latency, history, and uncertainty handling
  must be supplied outside the accepted scope (PAPER-005 Common extraction
  summary and §19; RQ-002 synthesis §12).
- `UNKNOWN` — PAPER-005 supplies no RQ-005 cost vector or measured restoration/
  controller cost; those objects must be defined and measured separately
  (PAPER-005 §§4, 9, and 16; RQ-002 synthesis §§5 and 12).
- Cross-unit interface synthesis is pending PA-DOM-01…03.

## Named blockers

- `INFERENCE` — no named canonical gap blocks PA-DOM-04 evidence reuse or
  population of its nine comparison fields.
- `UNKNOWN` — the overall PA-DOM comparison cannot be completed until
  PA-DOM-01…03 pass source control and receive their separately authorized
  extraction. No cross-unit conclusion is made here.

## Stop-rule disposition

| Work unit | Disposition |
|---|---|
| PA-DOM-01 | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED |
| PA-DOM-02 | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED |
| PA-DOM-03 | PENDING LS SOURCE CONTROL — NO EXTRACTION PERFORMED |
| PA-DOM-04 | **CLOSED BY CANONICAL REUSE** |

PA-DOM-04 is closed at the evidence-acquisition and matrix-population levels.
PA-DOM-01…03 and the overall PA-DOM protocol remain open; no cross-unit
synthesis or overall closure is yet possible.
