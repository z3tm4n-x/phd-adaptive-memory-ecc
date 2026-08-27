# Paper Card — C45 (draft for acceptance)

**PAPER-ID:** `TBD` — permanent identifier is not assigned before acceptance  
**Candidate identity:** `C45`  
**Related RQ:** `RQ-001`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommended class after deep read:** `CORE`  
**Zotero item key:** `UNKNOWN` — not provided to Paper Analyst  
**Full text used:** `Simplified Birthday Statistics and Hamming EDAC.pdf`, complete article, pp. 474–478  
**Attachment trace:** `file_000000004bd4820a930a97f38d89ba22`; SHA-256 `ee8dff2ed8e0d614c7cf22bb143a80b10122a623f7fb3237155cf52f84175b9d`  
**Evidence level in this card:** full-text analysis only; no citation-context audit

## Bibliographic identity

H. J. Tausch, “Simplified Birthday Statistics and Hamming EDAC,” *IEEE Transactions on Nuclear Science*, vol. 56, no. 2, pp. 474–478, Apr. 2009. DOI: [10.1109/TNS.2009.2012710](https://doi.org/10.1109/TNS.2009.2012710).

## RQ-001 extraction summary

| Dimension | Extraction |
|---|---|
| Reliability/failure event | `[SOURCE]` At least two distinct upset bits occur in one Hamming-protected word; the reported array event is that this happens in **at least one word anywhere in the memory** (pp. 474–477). |
| Metric and units | `[SOURCE]` Cumulative probability of the array event, dimensionless, conditional on the number `p` of random memory upsets (Eq. 17–18; Fig. 1). |
| Independent variable / horizon | `[SOURCE]` Upset count `p`; not elapsed time, fluence, or mission duration. The irradiation experiment is also reduced to total accumulated upset count before EDAC is enabled (pp. 476–477). |
| Aggregation level | `[SOURCE]` ECC word → complete memory array/device: an existential “some word” rule over 524,288 protected words in the worked example (pp. 475–477). |
| ECC / decoder outcome | `[SOURCE]` Hamming EDAC corrects one bit and detects a double-bit error. The model treats the first double-bit word as non-correctable/unusable; it does not model DUE, SDC, or miscorrection as separate outcomes (pp. 474–475). |
| Scrubbing | `[SOURCE]` No operational scrubbing model is defined. Errors accumulate until the first double-bit word; in the experiment, EDAC is off during exposure and enabled only after the beam is stopped (p. 477). |
| Error statistics | `[SOURCE]` Random isolated bit upsets over a large population, with a first-order approximation to birthday-collision statistics (Sections II–III). Direct harmful MBU is excluded from the main equation (Section V). |
| Interleaving / mapping | `[SOURCE]` No explicit mapping function is modeled. Section V explains qualitatively that the validity for MBU depends on logical-to-physical mapping and tile boundaries (p. 477). |
| Direct MCU vs independent accumulation | `[SOURCE]` The equation models isolated upsets that accumulate. A same-particle MBU capable of placing multiple bits in one word requires a separate probability component (p. 477). |
| Double-counting status | `[INFERENCE]` The published equation itself does not double count direct MCU because that mechanism is outside the equation. A later combined model would need a mutually exclusive event partition; the paper does not supply one. |

## 1. Research problem

- `[SOURCE]` The paper addresses how rapidly a Hamming-protected memory loses protection as random bit upsets accumulate and two erroneous bits eventually occupy the same protected word (Introduction, p. 474).
- `[SOURCE]` The original exact birthday-spacing equation is considered impractical for memory populations containing millions of cells because it requires factorials of very large numbers (Section II, p. 474).

## 2. Objective

- `[SOURCE]` Derive a simple approximation for the cumulative probability of a double-bit collision in a Hamming-protected memory as the number of random upsets increases, then compare it with an independent simulation and radiation-test data (pp. 474–477).

## 3. Studied system/model

- `[SOURCE]` Worked system: a nominal `512 K × 32` memory with 32 user-data bits and 7 Hamming protection bits per address, hence 39 physical bits per protected word and `2^19 = 524,288` words (p. 475).
- `[SOURCE]` Total modeled population: `n = 20,447,232` bit cells (`524,288 × 39`) (pp. 475–476).
- `[SOURCE]` Experimental device: a similar `512 K × 32` EDAC memory manufactured in the Texas Instruments 180 nm C05 bulk-silicon process (p. 477).

## 4. Method

- `[SOURCE]` The author starts from the Abramson–Moser birthday-spacing probability and applies a first-order approximation to obtain a closed-form collision probability suitable for large populations (Section II, Eqs. 1–17).
- `[SOURCE]` For the memory application, the population is all physical memory bits, the subset size is the number of accumulated random upset bits, and the collision range is approximated as one half of a 39-bit protected word (`k = 19.5`) (Section III, pp. 475–476).
- `[SOURCE]` An independent Monte Carlo-like program uses a `524,288 × 39` binary array, selects random cell positions, and stops when a word contains a second set bit. This experiment is repeated 100,000 times (p. 476).
- `[SOURCE]` Radiation validation accumulates a preset number of bit upsets with EDAC disabled, stops the beam, then reads with EDAC enabled to determine whether any non-correctable word exists (p. 477).

## 5. Assumptions

- `[SOURCE]` Each modeled bit upset is an isolated event; Section V calls this a theoretical best case (p. 477).
- `[SOURCE]` Upset locations are random over the total bit population (Sections I–III).
- `[SOURCE]` The simple expression uses a first-order approximation of the exponential/Taylor expansion (Eqs. 8–10, p. 475).
- `[SOURCE]` A single effective collision range `k = 19.5` is used for every location in a 39-bit word. The author checks this choice by simulation rather than deriving an exact word-boundary expression (pp. 475–476).
- `[SOURCE]` Errors remain present while the upset count grows; there is no correction between the counted upsets in the modeled trajectory (Sections III–IV).
- `[SOURCE]` All 39 bits, including the seven Hamming protection bits, belong to the collision population (p. 475).
- `[INFERENCE]` The model is conditional on an accumulated set/count of erroneous cells and does not itself specify a temporal arrival process, repair coverage, or nonstationary radiation environment.

## 6. Independent/input variables

- `[SOURCE]` `n`: size of the total population, in bit cells (Eq. 17).
- `[SOURCE]` `k`: collision range, in cell positions (Eq. 17).
- `[SOURCE]` `p`: size of the random subset / number of random memory upsets, a count (Eq. 17–18).
- `[SOURCE]` Worked values: `n = 20,447,232`, `k = 19.5`, and variable `p` (p. 476).
- `[SOURCE]` Experimental conditions include argon ions, LET `9.74 MeV·cm²/mg`, flux approximately `40 ions/(cm²·s)`, device cross section approximately `0.14 cm²`, and an observed bit-upset accumulation rate of approximately `6 s⁻¹` (p. 477). These are test conditions, not variables in Eq. 18.

## 7. Dependent/output variables

- `[SOURCE]` `PROB_K(n,p)(Collision)`: dimensionless cumulative probability that at least one colliding pair exists (Eq. 17).
- `[SOURCE]` In the memory interpretation, the output is the dimensionless probability that at least one Hamming word in the full memory contains a non-correctable double-bit upset after `p` random upsets (Eq. 18; Fig. 1).
- `[SOURCE]` Experimental probability is computed as attempts with at least one non-correctable upset divided by total attempts at a prescribed total-upset count (p. 477).

## 8. Baselines/comparators

- `[SOURCE]` Exact/general Abramson–Moser birthday-spacing equation versus the simplified approximation (Section II).
- `[SOURCE]` Simplified analytical curve versus the independent 100,000-run computer simulation (Figs. 2–3).
- `[SOURCE]` Analytical and simulation curves versus four experimental probability points (Fig. 4; Table I).

## 9. Main equations/models

### 9.1 Simplified collision probability

`[SOURCE]` Equation (17), p. 475:

\[
P_{\mathrm{collision}}(n,k,p)
\approx
1-\exp\!\left[-\frac{p(p-1)(2k-1)}{2n}\right].
\]

`[SOURCE]` Here `n` is the total population, `k` is the collision range, and `p` is the random-subset size.

### 9.2 Memory application

`[SOURCE]` Equation (18) uses the same form with:

\[
n=20{,}447{,}232,\qquad k=19.5,\qquad p=\text{number of random memory upsets}.
\]

`[INFERENCE]` In RQ-001 notation, the modeled quantity is best read as a conditional array-level probability:

\[
\Pr\!\left\{\exists w:\;N_w\ge 2\mid N_{\mathrm{array}}=p\right\},
\]

where `w` ranges over all Hamming-protected words. This notation is not printed by the author but makes the aggregation rule explicit without changing it.

### 9.3 Minimum additional time-domain layer

`[INFERENCE]` A transition from upset-count horizon to elapsed time requires a separate distribution for the accumulation-eligible upset count `N(t)`. The generic composition is:

\[
F_{\mathrm{acc}}(t)
=\sum_{p\ge0} P_{\mathrm{collision}}(n,k,p)\Pr\{N(t)=p\}.
\]

The paper does not choose or validate `Pr{N(t)=p}`. A Poisson, compound-Poisson, nonstationary, or data-driven arrival model would be an additional research choice, not a result of C45.

## 10. Main results

- `[SOURCE]` For the worked `512 K × 32` memory, the analytical model gives approximately 50% cumulative probability at 864 random upsets and 10% at 337 random upsets (p. 476).
- `[SOURCE]` The 100,000-run simulation and Eq. 18 are visually indistinguishable on the ordinary plot and remain close on a log-log plot; the author attributes the low-count deviation to limited simulation statistics (Figs. 2–3, p. 476).
- `[SOURCE]` The smallest simulated count producing a non-correctable word was six random upsets (p. 476). This is a sample extreme, not a deterministic threshold.
- `[SOURCE]` Experimental points were: `p=313`, 2/20 failed attempts (`0.10`); `p=688`, 11/32 (`0.344`); `p=1069`, 21/29 (`0.724`); and `p=1507`, 17/20 (`0.85`) (Table I, p. 477).
- `[SOURCE]` The author reports that the experimental points support the high-probability portion of the analytical curve (Section IV; Fig. 4).

## 11. Author-stated limitations

- `[SOURCE]` The principal equations assume isolated bit upsets and therefore represent a theoretical best case (Section V, p. 477).
- `[SOURCE]` Harmful MBU behavior depends on the physical arrangement of bit tiles and the logical-to-physical mapping (p. 477).
- `[SOURCE]` If one MBU can upset multiple tile-boundary cells belonging to the same Hamming word, the equation must be enhanced with a separate MBU probability component (p. 477).
- `[SOURCE]` The collision-range approximation and the first-order mathematical approximation are explicit simplifications (Sections II–III).

## 12. Methodological limitations inferred by us

- `[INFERENCE]` The paper validates probability as a function of accumulated upset count, not as a function of mission time, fluence, or scrub interval.
- `[INFERENCE]` The experiment disables EDAC during irradiation and only checks with EDAC after the beam stops; it is not a validation of continuous ECC operation or periodic scrubbing.
- `[INFERENCE]` Treating every `k≥2` word state as “unusable” collapses detected-uncorrectable, silent corruption, and decoder miscorrection into one failure label.
- `[INFERENCE]` The worked mapping uses regular 39-bit blocks and a scalar collision range; it does not represent an arbitrary physical-cell-to-codeword map `W`.
- `[INFERENCE]` A test on one 180 nm implementation does not establish validity for modern SRAMs with different MCU topology or proprietary mapping.
- `[INFERENCE]` The four experimental points have only 20–32 attempts each, so agreement at those points does not tightly constrain tail probabilities relevant to high-reliability requirements.

## 13. Threats to validity

- `[INFERENCE]` External validity: process, layout, EDAC implementation, and logical-to-physical mapping are device-specific.
- `[INFERENCE]` Construct validity: “non-correctable” is defined by error multiplicity, not by an observed system-visible incorrect output or service loss.
- `[INFERENCE]` Temporal validity: no arrival law or repair process connects `p` to operational time.
- `[INFERENCE]` Mechanism validity: direct same-particle MBU is outside the principal equation and only discussed qualitatively.
- `[INFERENCE]` Statistical precision: experimental sample sizes are small for estimating low failure probabilities.

## 14. What the paper actually demonstrates

- `[SOURCE]` A simple birthday-statistics approximation can reproduce, for the studied assumptions, the cumulative probability that random isolated upset bits produce the first double-error Hamming word in a large memory (Sections II–IV).
- `[SOURCE]` The result is explicitly array-wide: the event is a double-bit error in some protected word, not the failure probability of one preselected word (Abstract; Sections III–IV).
- `[SOURCE]` The paper identifies harmful same-particle MBU as a mapping-dependent mechanism requiring an additional model component (Section V).
- `[INFERENCE]` For RQ-001, C45 is a strong example of an event-count-conditioned array failure metric, but not of a scrub-cycle or mission-duration reliability metric.

## 15. What cannot legitimately be claimed from this paper

- `[INFERENCE]` It cannot supply a maximum scrub period or mission-time failure probability without an additional upset-arrival and repair/reset model.
- `[INFERENCE]` It cannot establish a direct-MBU cross section or rate.
- `[INFERENCE]` It cannot show that direct MBU and independent accumulation have been separated before rate calculation; only the accumulation mechanism is quantified.
- `[INFERENCE]` It cannot establish DUE, SDC, or miscorrection probabilities for a real decoder.
- `[INFERENCE]` It cannot justify a project-level numerical reliability threshold; the 10% and 50% values are descriptive points on the example curve.
- `[INFERENCE]` It cannot determine interleaving distance or an arbitrary mapping `W`.

## 16. Relevance to this dissertation

- `[INFERENCE]` Directly relevant to the `event × metric × aggregation × horizon × assumptions` matrix for `RQ-001` because it makes the array-wide existential event and upset-count horizon explicit.
- `[INFERENCE]` Provides a compact conditional accumulation model that could be used only after this project defines which events are accumulation-eligible and how their count evolves over time.
- `[INFERENCE]` Supports the need to keep logical-to-physical mapping explicit when same-particle MCU is present.
- `[INFERENCE]` Does not by itself answer `RQ-001`, because scrubbing, time aggregation, system-visible outcomes, and mission requirements remain unresolved.

## 17. Candidate claims for later Orchestrator/Evidence Auditor review

These are candidate statements only; no `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` Under isolated uniformly random upset locations, the cumulative probability that any Hamming word contains two upset bits can be expressed as a function of total accumulated upset count.
2. `[SOURCE-CANDIDATE]` In C45, “some word” denotes an array-wide existential event rather than a per-word probability.
3. `[SOURCE-CANDIDATE]` Harmful same-particle MBU is excluded from the main C45 equation and is identified as requiring a mapping-dependent separate component.
4. `[INFERENCE-CANDIDATE]` An upset-count-conditioned failure curve cannot be interpreted as a scrub-time or mission-time curve without a separate count-arrival and repair model.

## 18. Contradictions/tensions with other known papers

- `[UNKNOWN]` No cross-paper adjudication is performed in this card, as required by the handoff.
- `[INFERENCE]` The paper’s main model deliberately excludes direct harmful MBU, so any later model that already includes MCU multiplicity must not treat C45 as an independent add-on without checking event overlap.

## 19. Open questions created by this paper

1. `[UNKNOWN]` What stochastic law should govern the number of accumulation-eligible upset bits between scrubs under the target radiation environment?
2. `[UNKNOWN]` What exact mapping `W` defines the ECC word for every data and check-bit cell in the target memory?
3. `[UNKNOWN]` Which decoder outcomes should count as failure: any `k≥2` word state, DUE, SDC, miscorrection, or system-visible service loss?
4. `[UNKNOWN]` How should a direct same-particle multi-bit codeword event be partitioned from accumulation-eligible events before mission-rate calculation?
5. `[UNKNOWN]` How should per-cycle failure probability be aggregated over a nonstationary mission while preserving the reset semantics of scrubbing?

## Direct answers to the C45 handoff questions

### What does “some word” mean?

- `[SOURCE]` At least one of the `524,288` Hamming-protected 39-bit words in the complete worked memory contains two upset cells. It is an array-wide “exists a word” event, not a named or randomly selected single word (pp. 475–477).

### Is the horizon time, number of upsets, or fluence?

- `[SOURCE]` The independent variable in the model is the number `p` of random accumulated memory upsets. Fluence and elapsed time appear only as experimental conditions used to obtain an upset count; neither is the horizon in Eq. 18.

### How can it be converted to scrub/mission time?

- `[INFERENCE]` Add: (1) a traceable model for the count `N(t)` of accumulation-eligible upset bits; (2) a scrub model specifying correction coverage and reset timing; and (3) a mission aggregation/renewal model across scrub cycles. The generic first step is the conditional sum in Section 9.3. C45 supplies none of these three layers.

### Are same-particle MBUs included?

- `[SOURCE]` Not in the main equation: it assumes isolated bit upsets. Section V states that an MBU confined to a single bit tile may behave like errors at different addresses, but an MBU crossing tiles and placing multiple bits in one Hamming word requires a separate probability component governed by physical/logical mapping.

## Final disposition

- **Recommendation:** `CORE` for `RQ-001`.
- **Confidence:** high for the extracted definitions and formulas; medium for transfer to other memory layouts.
- **Evidence gaps:** time-domain arrival law, scrubbing/reset semantics, decoder outcomes, explicit mapping `W`, and a mutually exclusive direct-MBU/accumulation partition.
- **Next action:** Orchestrator acceptance and permanent `PAPER-xxx` assignment; candidate claims, if retained, go to Evidence Auditor rather than being accepted automatically.
