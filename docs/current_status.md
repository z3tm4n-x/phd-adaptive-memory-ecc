# Current Status

**Updated:** 2026-08-28

## Current phase

RQ-002 bounded model selection and preparation of the first parameterized own-result experiment.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.4-draft`.

## Active gate

Audit the decision-carrying propositions from the accepted RQ-002 Paper Analyst batch, bound the remaining model alternatives, and specify the smallest quantitative prototype that can test the effect of event-information reduction on `E_cap`, `F_A(t0,T;μ_t0)` and an eventual adaptive restoration decision. No second general RQ-002 discovery cycle is authorized without a named blocking evidence gap.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / INITIAL EVIDENCE SYNTHESIS ACCEPTED / MODEL-SELECTION GATE`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`; retains decoder-outcome semantics.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`; must distinguish external exposure information from internal memory-state/history information.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.
- C-RQ-05 — physical/logical mapping and interleaving — escalation condition confirmed by RQ-002 evidence; proposed promotion is C-RQ-05 → `RQ-006`, subject to explicit PI acceptance before the main reliability model is fixed.
- An integrated adaptive-control RQ remains required to join RQ-002…RQ-005 outputs into an actual restoration-regime decision; its exact registration and relation to C-RQ-08/C-RQ-09/C-RQ-11 remain pending PI review.

## Accepted RQ-001 decision

[DEC-001](decisions/DEC-001-rq001-reliability-contract.md) remains controlling and unchanged:

- primitive event `E_cap` is ECC capability exceedance, not an automatic DUE/SDC/miscorrection/system-failure label;
- reporting window is `H(t0,T) = [t0,t0+T]`;
- general metric is `F_A(t0,T; μ_t0)`, with the initial state/distribution required by every quantitative model;
- `A` is an explicitly declared controller-managed SRAM protection domain and must be partitioned when ECC, mapping `W`, arrival, bank/block or scrubbing semantics differ;
- upset-count, per-codeword exposure, reporting and mission horizons remain distinct;
- `H_req` and `ε_req` remain `TBD` pending traceable requirements.

## Accepted integrated roadmap decision

[DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md) records the PI-directed working architecture:

`radiation-test evidence → identifiable device-error representation → mapping W / ECC organization → ECC-level reliability → observable risk assessment → adaptive restoration decision`.

The three scientific layers — identification, ECC-aware reliability and adaptive control — are one causal method, not automatically three independent novelty claims. The active scientific question is the adequacy and quantitative price of information reduction between radiation-test observations and the final control decision. A richer representation is not presumed superior; exact reductions, bounded reductions and declared approximations are all admissible outcomes.

## RQ-002 accepted evidence

The corrected PA Batch 01 provenance at base commit `314b040de3bd8096ba1114edf1dc165da06e2360` has no blocking identity issue. The following full-text analytical cards are formally accepted:

- [PAPER-004](paper_cards/PAPER-004-clemente-rezaei-franco-2022.md) — Clemente, Rezaei and Franco, 2022;
- [PAPER-005](paper_cards/PAPER-005-zebrev-2017-arxiv-v2.md) — exact Zebrev arXiv v2, with C006 retained as a controlled companion publication rather than a separate Paper Card;
- [PAPER-006](paper_cards/PAPER-006-moindjie-et-al-2017.md) — Moindjie et al., 2017;
- [PAPER-007](paper_cards/PAPER-007-ogden-mascagni-2017.md) — Ogden and Mascagni, 2017;
- [PAPER-008](paper_cards/PAPER-008-gomi-et-al-2026.md) — Gomi et al., 2026.

Acceptance covers completeness, traceability and fitness for bounded synthesis. It does not adopt source assumptions, accept candidate claims, select a process family or establish novelty.

The canonical [RQ-002 initial evidence synthesis](evidence_synthesis/RQ-002_initial_evidence_synthesis.md) preserves the cross-paper distinctions in primitive arrival object, temporal process, event mark/topology, `W`, accumulation state, repair, observation error, aggregation and horizon.

## Remaining model alternatives

No family is selected. The bounded alternatives are:

- multiplicity-indexed marked HPP;
- time-varying marked Poisson/NHPP;
- compound marked Poisson;
- event-driven physical/post-`W` marked simulation;
- independent-accumulation occupancy model with a separately defined direct-event layer;
- discrete-time scan/repair state model;
- observation-aware latent-event model.

Each alternative must be evaluated against the minimum event/mark representation, joint post-`W` dependence, initial state, repair/writeback semantics, observation uncertainty, validation domain and computational tractability.

## Revised scientific roadmap

1. **Identification layer:** determine what event/topology/multiplicity information is observable or identifiable from realistic radiation tests and with what reconstruction uncertainty.
2. **ECC-aware reliability layer:** transform that information through declared `W`, ECC capability and restoration semantics into `E_cap` and `F_A(t0,T;μ_t0)`; quantify the effect of successive representation reductions.
3. **Adaptive-control layer:** use physically available external and internal observations to choose an actual restoration regime under a parameterized or traceable reliability constraint and a measurable resource-cost vector.
4. **Implementation/validation layer:** connect the method to controller architecture, RTL and hardware/resource/timing evidence without treating RTL alone as novelty.

Russian normative practice is a primary practical baseline for the whole chain. Its retained and aggregated information must be extracted before any claim of deficiency. The identification/mapping prior-art threat and the Chen/IHP/Potsdam adaptive-control prior-art threat remain separate checks.

## Actual blockers

1. **PI decision:** approve or reject permanent promotion of C-RQ-05. The promotion is required before fixing the main quantitative reliability model.
2. **Normative source material:** exact controlled copies/editions of `РД 134-0175-2009`, `РД 134-0174-2009` and any companion documents the PI considers applicable are required before normative-chain extraction.
3. **Closest adaptive-control source identity:** exact Chen/IHP/Potsdam title, DOI/report identity or full text is required before a control-layer novelty statement can be assessed.
4. **Target-specific conclusions:** a declared protection-domain architecture `A`, mapping `W`, and traceable event/rate data are required before device- or mission-specific quantitative conclusions.

## Non-blockers for a parameterized prototype

- unresolved numerical `H_req` and `ε_req`;
- final decoder-outcome semantics from RQ-003;
- final observation channel/estimator from RQ-004;
- final resource weights or scalar objective from RQ-005/C-RQ-11;
- final FPGA/RTL platform;
- deferred eLibrary and unavailable ResearchRabbit coverage.

These quantities may remain explicit parameters or bounded alternatives in the first model-comparison experiment. The prototype must not claim satisfaction of an unstated requirement.

## Active hypotheses and own results

- No `HYP-xxx` has been registered.
- No `EXP-xxx` has been registered.
- No `RES-xxx` has been registered.
- `DEC-001` and `DEC-002` are research decisions, not own experimental results.

## Next actions

1. Run one bounded Evidence Auditor task over the decision-carrying RQ-002 propositions from `PAPER-004…008`; do not create permanent claims automatically.
2. Obtain the PI decision on C-RQ-05 promotion and then register the mapping/interleaving RQ if approved.
3. When the PI supplies the Russian normative documents, run a document-bounded extraction of the normative calculation chain and retained information; do not perform a broad normative search first.
4. After exact Chen/IHP/Potsdam identity is available, run a bounded feature-by-feature close-prior-art check for the adaptive-control layer.
5. Define a common parameterized `A/W/ECC/scrub` test system, a representation ladder, comparison metrics and the first `EXP-xxx` specification. Register an experiment only after the bounded evidence/model-selection decision states what it discriminates.
6. Authorize new literature or deep-read work only for a named gap that blocks model selection, adequacy, validation or the first own-result experiment.

## Constraints

- Do not reopen RQ-001 or revise DEC-001 without a concrete contradiction.
- External-advisor statements remain unverified threats until checked against primary evidence.
- Do not claim that the normative chain is deficient before examining the applicable documents.
- Do not claim novelty for radiation variation/prediction → adaptive scrub-frequency adjustment without the close control-layer prior-art pass.
- Do not assign a numerical reliability requirement without traceable provenance.
- Do not let the identification problem replace adaptive control as the dissertation core.
