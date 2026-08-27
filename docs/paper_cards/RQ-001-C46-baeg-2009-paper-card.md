# Paper Card — C46 (draft for acceptance)

**PAPER-ID:** `TBD` — permanent identifier is not assigned before acceptance  
**Candidate identity:** `C46`  
**Related RQ:** `RQ-001`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommended class after deep read:** `CORE`  
**Zotero item key:** `UNKNOWN` — not provided to Paper Analyst  
**Full text used:** `SRAM Interleaving Distance Selection With a Soft.pdf`, complete article, pp. 2111–2118  
**Attachment trace:** `file_0000000004f8820abbf3ef3558daaea5`; SHA-256 `2a0cda0c7470510ec86e93348d2c3e42185b050a118ae539b67a1129e6cebf0f`  
**Evidence level in this card:** full-text analysis only; no citation-context audit

## Bibliographic identity

S. Baeg, S. Wen, and R. Wong, “SRAM Interleaving Distance Selection With a Soft Error Failure Model,” *IEEE Transactions on Nuclear Science*, vol. 56, no. 4, pp. 2111–2118, Aug. 2009. DOI: [10.1109/TNS.2009.2015312](https://doi.org/10.1109/TNS.2009.2015312).

## RQ-001 extraction summary

| Dimension | Extraction |
|---|---|
| Reliability/failure event | `[SOURCE]` A leaf memory block has failed if at least one SEC-protected word contains at least two distinct upset cells. Repeated hits assigned to only one cell are not a failure (Section III, Eqs. 4–6; Fig. 5). |
| Metric and units | `[SOURCE]` `F(t)`: dimensionless cumulative failure probability; `R(t)=1-F(t)`; MTTF in the chosen time unit; FIT normalized as failures per `10^9` operating hours per megabit when the time base is hours (Eqs. 1, 8–9). |
| Independent variable / horizon | `[SOURCE]` Elapsed time `t` in a compound-Poisson count model. Simulation time units may be hour/day/year if `λ` is expressed consistently; the paper uses hours for illustrative simulations and seconds for the 45 nm test comparison (pp. 2115–2117). |
| Aggregation level | `[SOURCE]` Word → leaf block. The authors explicitly state that the model does not include multiple-block effects and `λ` must be a leaf-block parameter (p. 2115). |
| ECC / decoder outcome | `[SOURCE]` Single-error correction (SEC). At most one erroneous cell per word is repairable; two or more distinct upset cells in a word are labeled unrepairable. DUE, SDC, and miscorrection are not separately modeled (pp. 2113–2115). |
| Scrubbing | `[SOURCE]` No scan/repair stochastic process is modeled. A scrub interval is inferred as a time before `F(t)` exceeds an illustrative threshold (pp. 2111, 2116). |
| Error statistics | `[SOURCE]` Poisson event arrivals with rate `λ`; iid geometric upset multiplicity per arrival with parameter `r`; conditional placement of all individual upsets is uniform and independent over cells (Eqs. 2–6). |
| Interleaving / mapping | `[SOURCE]` Regular interleaving distance `ID`, defined as physical intra-word spacing in row-bit units. The model uses a structured leaf-block geometry, not an arbitrary physical-cell-to-codeword map (Figs. 1 and 5). |
| Direct MCU vs independent accumulation | `[SOURCE]` MCU multiplicity is represented in the compound-Poisson distribution of total upset count, but conditional failure probability maps every individual upset sequentially and does not retain a direct-MCU versus independent-event failure label (pp. 2114–2116). |
| Double-counting status | `[INFERENCE]` The paper uses one compound generative process and does not add two overlapping failure probabilities, so no explicit arithmetic double counting occurs internally. However, its total `F(t)` already includes MCU-bearing arrivals and independent-event combinations; adding a separate direct-MCU term later without partitioning would double count. |

## 1. Research problem

- `[SOURCE]` Memory designers need a predictive method for selecting interleaving distance while balancing soft-error reliability against area, power, routing, aspect ratio, and other implementation costs (Introduction and Section II-A, pp. 2111–2113).
- `[SOURCE]` A simple Poisson upset-count model is inadequate for MCU because one particle/event can produce multiple upset cells (Section III, p. 2114).

## 2. Objective

- `[SOURCE]` Develop an interleaving-dependent SEC memory failure-probability model that includes SCU and grouped MCU arrivals through a compound-Poisson process, and use it to compare interleaving choices and illustrative scrub intervals (pp. 2111–2117).

## 3. Studied system/model

- `[SOURCE]` Analytical object: one SRAM leaf block with a regular row/column interleaving architecture and SEC-protected logical words (Sections II-A, II-C, III).
- `[SOURCE]` Simulation block: 16 K cells, described using 256 row/word groups and five ID choices `1, 2, 4, 8, 16`; the associated number of bits per word in the simulation is reported as `64, 32, 16, 8, 4` (Section V, p. 2115).
- `[SOURCE]` Experimental basis: SRAM tests at 90, 65, and 45 nm; the detailed model comparison reuses the `45 nm-A` neutron-test data (Sections II-B and VI).
- `[SOURCE]` Devices were exposed to white neutron beams up to 800 MeV at LANSCE or neutron beams up to 180 MeV at TSL, under varying operating voltages and data patterns (p. 2113).

## 4. Method

- `[SOURCE]` Model the number `Y` of particle/error arrivals in time `t` as Poisson with rate `λ` (Eq. 2).
- `[SOURCE]` Model the number of upset cells produced per arrival by a geometric distribution; convolution with the Poisson arrivals gives a compound-Poisson distribution for total upset count `X` (Eqs. 2–3).
- `[SOURCE]` Conditional on `X`, enumerate mappings of the upset instances to `L` distinct physical cells and count mappings in which at least two occupied cells belong to the same SEC word (Eqs. 4–6; Fig. 5).
- `[SOURCE]` Sum conditional block-failure probability over total upset counts to obtain `F(t)` and derive `R(t)`, MTTF, and FIT (Eqs. 1, 8–9).
- `[SOURCE]` Compare ID choices in simulation and compare the model with a synthetic repartitioning of 45 nm neutron-test addresses (Sections V–VI).

## 5. Assumptions

- `[SOURCE]` Event arrivals follow a Poisson process with constant parameter `λ` over the modeled horizon (Eqs. 2–3).
- `[SOURCE]` Upset multiplicity per arrival is iid geometric, `f(x)=(1-r)r^{x-1}`, with a single fitted/selected parameter `r` (Section III, p. 2114).
- `[SOURCE]` Each word uses SEC; a word with one distinct erroneous cell is repairable and a word with at least two is a failure (Sections II-C and III).
- `[SOURCE]` In the conditional placement calculation, each upset instance — including members of an MCU — is mapped one at a time with probability `1/M` per cell. Physical locality is not used in Eq. 4 (p. 2114).
- `[SOURCE]` The base calculation permits multiple upset instances to map to one physical cell; if all instances occupy one cell, SEC repairs the state and it is not counted as failure (pp. 2114–2115).
- `[SOURCE]` Only one leaf block is modeled; multiple blocks/banks and their aggregation are excluded (p. 2115).
- `[SOURCE]` For the stated upper-bound interpretation, the MCU span in the row direction must not exceed `ID`, or such events must have negligible probability (Section IV, p. 2115).
- `[SOURCE]` The 45 nm device’s real hierarchy, block size, interleaving, and hardening structures were unavailable; the test addresses were arbitrarily partitioned into `256 × 64` blocks (Section VI, p. 2117).
- `[INFERENCE]` Errors persist until a hypothetical scrub time. Scrub coverage, duration, ordering, and imperfect repair are absent from the state model.

## 6. Independent/input variables

- `[SOURCE]` `t`: elapsed time, expressed in the same time unit used by `λ`.
- `[SOURCE]` `λ`: mean grouped-event arrival rate for one leaf block, in arrivals per time unit.
- `[SOURCE]` `r`: geometric multiplicity parameter, dimensionless.
- `[SOURCE]` `X`: total number of upset instances/cells represented by the compound process, a count.
- `[SOURCE]` `Y`: number of grouped arrivals/events, a count.
- `[SOURCE]` `M`: number of memory cells in the leaf block; `ID`: interleaving distance; `W` and `B`: geometry/word parameters used in the combinatorial model (Section III; Fig. 5 states `M=W×ID×B`).
- `[SOURCE]` Simulation comparisons vary `ID` and use `r=0.01`, `0.99`, and `0.57`; `λ=0.01` is explicitly arbitrary in the illustrative simulations (Section V).

## 7. Dependent/output variables

- `[SOURCE]` `P(X,t)`: probability of `X` upset instances by time `t`, dimensionless (Eqs. 2–3).
- `[SOURCE]` `P_f(X)`: conditional probability that the leaf block contains at least one failed SEC word after `X` upset instances, dimensionless (Eq. 4).
- `[SOURCE]` `F(t)`: cumulative block-failure probability, dimensionless; `R(t)=1-F(t)` (Eq. 1).
- `[SOURCE]` MTTF: expected time to failure in the time unit used for `t` (Eq. 8).
- `[SOURCE]` FIT: `10^9/(MTTF·M_Mbit)`; failures per billion operating hours normalized by memory size in megabits when MTTF is in hours (Eq. 9 and accompanying text).
- `[SOURCE]` PR/PRAI: ratios comparing model to data and adjacent-ID failure probabilities, dimensionless (Eq. 10; Fig. 12).

## 8. Baselines/comparators

- `[SOURCE]` Interleaving choices `ID=1,2,4,8,16` in the analytical/simulation model (Section V).
- `[SOURCE]` SCU-dominant (`r=0.01`), MCU-dominant (`r=0.99`), and test-trend (`r=0.57`) multiplicity cases (Figs. 7–9).
- `[SOURCE]` Model failure probabilities versus pseudo-ID failure probabilities reconstructed from `45 nm-A` neutron data (Section VI).
- `[SOURCE]` Commercially compiled ID choices `4,8,16,32` compared for normalized area, power, speed, and aspect ratio in an 80 nm example; these implementation comparisons motivate the reliability model but are not integrated into an optimization objective (Figs. 2–3).

## 9. Main equations/models

### 9.1 Reliability and failure probability

`[SOURCE]` Equation (1), p. 2114:

\[
R(t)=1-F(t),\qquad
F(t)=\sum_{X=1}^{\infty}P(X,t)P_f(X).
\]

`[SOURCE]` `P_f(X)` is conditional on the total number of upset instances and denotes whether at least one word in the modeled block has failed.

### 9.2 General and geometric compound-Poisson count model

`[SOURCE]` Equation (2):

\[
P(X,t)=\sum_{Y=0}^{\infty}
\frac{(\lambda t)^Y e^{-\lambda t}}{Y!}
f^{Y*}(X),
\]

where `f^{Y*}` is the `Y`-fold convolution of the per-arrival multiplicity distribution.

`[SOURCE]` With `f(x)=(1-r)r^{x-1}`, Eq. (3) becomes:

\[
P(X,t)=\sum_{Y=1}^{X}
\frac{(\lambda t)^Y e^{-\lambda t}}{Y!}
\binom{X-1}{Y-1}r^{X-Y}(1-r)^Y.
\]

### 9.3 Conditional failure probability and interleaving geometry

`[SOURCE]` Equation (4):

\[
P_f(X)=\sum_{L=2}^{X}G_L\,{}_LT_X\left(\frac{1}{M}\right)^X.
\]

`[SOURCE]` Equation (5):

\[
G_L=\binom{M}{L}-\binom{ID\cdot W}{L}B^L.
\]

`[SOURCE]` `G_L` counts `L`-cell groups that contain at least two cells belonging to the same word; the subtracted term represents groups whose occupied cells all correspond to different word locations under the regular interleaving model.

`[SOURCE]` Equation (6) recursively computes the number of onto assignments of `X` upset instances to all `L` occupied cells:

\[
{}_LT_X=L^X-
\left[
\binom{L}{L-1}{}_{L-1}T_X+
\binom{L}{L-2}{}_{L-2}T_X+
\cdots+
\binom{L}{1}{}_1T_X
\right],
\qquad {}_1T_X=1^X.
\]

### 9.4 MTTF and FIT

`[SOURCE]` Equations (8)–(9), p. 2116:

\[
MTTF=\int_0^{\infty}t f(t)\,dt
=\int_0^{\infty}R(t)\,dt,
\qquad
FIT=\frac{10^9}{MTTF\cdot M_{\mathrm{Mbit}}}.
\]

## 10. Main results

- `[SOURCE]` With `λ=0.01` and `r=0.01`, the paper reports at time 20 a failure probability of `0.0001` for `ID=1` and `0.000005` for `ID=16` (Fig. 7; p. 2115).
- `[SOURCE]` Using an illustrative block requirement `F<0.00005`, the authors state that `ID=1` and `ID=2` would require scrubbing every 20 and 25 hours, respectively (p. 2116). This is a paper example, not a sourced system requirement.
- `[SOURCE]` With `r=0.99`, the reported `ID=1` failure probability at time 20 is `0.015`, 150 times the SCU-dominant example (Fig. 8).
- `[SOURCE]` A fitted geometric constant `r=0.57` approximately follows the observed MCU-size trend; under this example, requiring `ID=1` failure probability below `0.1%` at time 20 leads to `ID≥4` or a scrub interval no greater than 7.5 hours (Fig. 9; p. 2116). Again, the threshold is illustrative.
- `[SOURCE]` FIT decreases as ID increases; the example reports `ID=1` FIT 4.3 times `ID=16` FIT (Fig. 10).
- `[SOURCE]` In the 45 nm comparison, model failure probability is generally larger than data-based failure probability; the authors introduce a probability ratio `α=7` and interpret the independent-location model as an upper bound (Section VI, p. 2117).
- `[SOURCE]` Adjacent-ID probability ratios track the test-derived ratios up to ID 4 and diverge more for larger ID because real physical structures exclude combinations permitted by the model (Fig. 12; p. 2117).

## 11. Author-stated limitations

- `[SOURCE]` The base `P_f(X)` calculation treats all upset locations as independent/equiprobable and does not include local physical clustering (Section IV).
- `[SOURCE]` The upper-bound relation is not valid when MCU row span exceeds ID with non-negligible probability; in that regime an MCU can deterministically create an unrepairable word (p. 2115).
- `[SOURCE]` The authors recommend coupling the analytical model with technology-specific data (p. 2115).
- `[SOURCE]` The model is one-leaf-block only and does not count multiple-block effects (p. 2115).
- `[SOURCE]` The true block structure and hardening of the 45 nm device were unknown; arbitrary partitioning may not reproduce the real ID and can change failure probability (p. 2117).
- `[SOURCE]` Physical block and well-tapping constraints increasingly explain model/data gaps for ID greater than 4; embedding such constraints is left for future work (p. 2117).

## 12. Methodological limitations inferred by us

- `[INFERENCE]` Compound-Poisson multiplicity preserves the number of upset bits per arrival in `P(X,t)`, but `P_f(X)` conditions only on total `X` and remaps all bits independently. It therefore does not preserve same-particle topology at the physical-cell-to-codeword stage.
- `[INFERENCE]` Absolute experimental agreement is not demonstrated without an empirical probability ratio; the strongest support is for conservative ordering/relative ID benefit in a limited ID range.
- `[INFERENCE]` Scrubbing is represented only by choosing a cutoff time. The method does not model scan sequencing, word-by-word exposure age, repair coverage, bandwidth, or reset after a scrub.
- `[INFERENCE]` The regular scalar ID abstraction is not equivalent to an arbitrary candidate mapping `\mathcal W`; it cannot evaluate nonuniform or undocumented logical-to-physical assignments.
- `[INFERENCE]` The failure state `≥2` distinct upset bits in a SEC word does not identify whether a real decoder detects, miscorrects, or silently outputs wrong data.
- `[INFERENCE]` The notation linking `M`, `W`, `ID`, and `B` should be reproduced carefully before reuse because the simulation changes reported word-bit counts with ID while holding block size fixed.

## 13. Threats to validity

- `[INFERENCE]` Model-form threat: constant-rate Poisson arrivals and a single geometric multiplicity parameter may not represent time-varying radiation or multimodal MCU distributions.
- `[INFERENCE]` Spatial threat: independent uniform cell placement includes physically impossible groups and may miss guaranteed harmful groups when MCU span exceeds ID.
- `[INFERENCE]` Architecture threat: unknown proprietary organization is replaced by arbitrary `256×64` partitions.
- `[INFERENCE]` Validation threat: the same 45 nm data supply the Poisson parameter and multiplicity trend used in the comparison, so the exercise is not an independent out-of-sample validation.
- `[INFERENCE]` Aggregation threat: leaf-block failure is not propagated to bank, device, memory service, or system failure.

## 14. What the paper actually demonstrates

- `[SOURCE]` A single compound-Poisson model can combine Poisson event arrivals with grouped upset multiplicity and produce an interleaving-dependent leaf-block failure probability for an SEC abstraction (Sections III–V).
- `[SOURCE]` Under the paper’s independent-location model, larger interleaving distance lowers predicted failure probability and FIT in the worked examples (Figs. 7–10).
- `[SOURCE]` The model is conservative relative to the analyzed 45 nm data when physical MCU span is small relative to ID; its relative ID trend is closest for lower ID values (Sections IV and VI).
- `[INFERENCE]` For `RQ-001`, C46 provides a time-domain leaf-block event and several metrics, but it does not provide a mechanism-separated direct-MCU and independent-accumulation decomposition.

## 15. What cannot legitimately be claimed from this paper

- `[INFERENCE]` It cannot establish a universal upper bound for all ID and MCU topologies; the authors explicitly restrict the bound condition.
- `[INFERENCE]` It cannot validate the true interleaving organization of the 45 nm device because that organization was unavailable.
- `[INFERENCE]` It cannot provide a mission-level requirement or project numerical threshold; the `0.00005` and `0.1%` limits are illustrative assumptions.
- `[INFERENCE]` It cannot attribute `F(t)` separately to direct same-particle word failures and temporal accumulation of independent events.
- `[INFERENCE]` It cannot give an operational scrub-period reliability model beyond a threshold-crossing example.
- `[INFERENCE]` It cannot determine an arbitrary physical mapping `\mathcal W` or decoder-level DUE/SDC probabilities.

## 16. Relevance to this dissertation

- `[INFERENCE]` Directly relevant to `RQ-001` because it supplies explicit event, metric, leaf-block aggregation, elapsed-time horizon, and stochastic assumptions.
- `[INFERENCE]` Provides a candidate mathematical route from grouped particle-event arrivals to total upset count, but RQ-002 must decide whether Poisson/geometric assumptions are adequate before reuse.
- `[INFERENCE]` Shows why physical mapping and MCU span must be checked before interpreting an interleaving model as conservative.
- `[INFERENCE]` Its total failure probability must not be combined with a separate direct-MCU term unless the event population is partitioned first.

## 17. Candidate claims for later Orchestrator/Evidence Auditor review

These are candidate statements only; no `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` C46 defines block failure as the existence of at least two distinct upset cells in one SEC word.
2. `[SOURCE-CANDIDATE]` C46 represents grouped MCU multiplicity through a compound-Poisson upset-count process with a geometric compounding distribution.
3. `[SOURCE-CANDIDATE]` The C46 independent-location calculation is an upper bound only when harmful MCU spans greater than ID are absent or negligible.
4. `[INFERENCE-CANDIDATE]` C46 does not retain direct-MCU versus independent-accumulation provenance in its final conditional failure probability.
5. `[SOURCE-CANDIDATE]` The published analytical model is scoped to one leaf block and excludes multiple-block aggregation.

## 18. Contradictions/tensions with other known papers

- `[UNKNOWN]` No cross-paper correctness judgement is made in this card.
- `[INFERENCE]` The paper simultaneously incorporates MCU multiplicity in `P(X,t)` and treats MCU member locations like independent SCUs in `P_f(X)`. This is an intentional conservative approximation under the stated span condition, not a topology-resolved MCU model.

## 19. Open questions created by this paper

1. `[UNKNOWN]` What measured event multiplicity distribution and arrival process are valid for the target radiation environment and SRAM?
2. `[UNKNOWN]` How should physical MCU topology be mapped through a candidate `\mathcal W` without replacing it by independent uniform placement?
3. `[UNKNOWN]` How should leaf-block failure be aggregated across blocks/banks and converted to a system-visible memory-service event?
4. `[UNKNOWN]` What scrub model is required when correction is sequential and different words have different exposure ages?
5. `[UNKNOWN]` Under what exact conditions does a direct same-particle MCU cross the selected ID and immediately create a multi-error word?

## Direct answers to the C46 handoff questions

### How is the failure event defined?

- `[SOURCE]` At least two distinct occupied upset cells occur in one SEC-protected word within the modeled leaf block by time `t`. `P_f(X)` is conditional on total upset count; `F(t)` averages that event over the compound-Poisson distribution (Eqs. 1 and 4–6).

### How is the compound-Poisson model constructed?

- `[SOURCE]` `Y` grouped arrivals follow a Poisson process with parameter `λt`; each arrival produces a geometrically distributed positive upset multiplicity. The `Y`-fold convolution gives total upset count `X`, yielding Eq. 3. Conditional failure then depends only on `X` and the interleaving combinatorics.

### Why is the result an upper bound?

- `[SOURCE]` The conditional placement model gives every upset equal independent access to every cell, so it counts physically impossible multi-cell combinations that real clustered MCU and layout structures exclude. Consequently `P_{f:SCU}(X)>P_{f:MCU}(X)` under Eq. 7. The bound requires MCU row span not to exceed ID with appreciable probability; otherwise a direct MCU may be more harmful and Eq. 7 may fail (Section IV).

### How are physical grouping and interleaving represented?

- `[SOURCE]` Grouping in time/multiplicity is represented by the compound-Poisson geometric distribution. Interleaving is represented by a regular scalar physical spacing `ID` and the combinatorial subtraction in `G_L`. Actual MCU spatial topology is not retained in the base `P_f(X)` calculation.

### Are direct MCU and independent accumulation separated?

- `[SOURCE]` No. MCU/SCU multiplicity affects the distribution of total `X`, and the final `F(t)` includes any combination of multiple events, explicitly including two independent SCUs. Conditional word failure is not labeled by whether its bits came from one MCU or multiple arrivals.
- `[INFERENCE]` The internal model does not add duplicate mechanism terms, but it cannot support mechanism-specific rates. Its `F(t)` must be treated as an already combined total if reused.

## Final disposition

- **Recommendation:** `CORE` for `RQ-001`.
- **Confidence:** high for equations, event definition, aggregation boundary, and bound condition; medium for interpretation of the proprietary 45 nm comparison.
- **Evidence gaps:** explicit topology-to-codeword map, mechanism-separated failure rates, decoder outcomes, multi-block aggregation, and an operational scrub process.
- **Next action:** Orchestrator acceptance and permanent `PAPER-xxx` assignment; send retained candidate claims to Evidence Auditor rather than accepting them automatically.
