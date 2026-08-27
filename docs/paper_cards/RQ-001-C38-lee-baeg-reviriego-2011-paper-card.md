# Paper Card — C38 (draft for acceptance)

**PAPER-ID:** `TBD` — permanent identifier is not assigned before acceptance  
**Candidate identity:** `C38`  
**Related RQ:** `RQ-001`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommended class after deep read:** `CORE`  
**Zotero item key:** `UNKNOWN` — not provided to Paper Analyst  
**Full text used:** `Memory Reliability Model for Accumulated.pdf`, complete article, pp. 2483–2492  
**Attachment trace:** `file_000000001510820aa3fc6c3fc4e3cd2b`; SHA-256 `cae5d2ad30dffcdbb4281cbcf911a004c06e30fe53c87c9e9542185deeacf1ae`  
**Evidence level in this card:** full-text analysis only; no citation-context audit

## Bibliographic identity

S. Lee, S. Baeg, and P. Reviriego, “Memory Reliability Model for Accumulated and Clustered Soft Errors,” *IEEE Transactions on Nuclear Science*, vol. 58, no. 5, pp. 2483–2492, Oct. 2011. DOI: [10.1109/TNS.2011.2164555](https://doi.org/10.1109/TNS.2011.2164555).

## RQ-001 extraction summary

| Dimension | Extraction |
|---|---|
| Reliability/failure event | `[SOURCE]` A word fails when its upset count exceeds the ECC correction capability. Memory failure is explicitly “one or more failing words” in the modeled memory. The row-level prose is internally inconsistent: it first says “more than one failing word” and immediately defines row failure probability as “one or more failing words” (pp. 2484, 2486–2487). |
| Metric and units | `[SOURCE]` Conditional row and memory failure probabilities; cumulative `F(t,ID)` and reliability `R(t,ID)=1-F(t,ID)`, all dimensionless; word MTBF in seconds for the reported test/simulation time base (Eqs. 4–10; Figs. 11–12). |
| Independent variable / horizon | `[SOURCE]` Total accumulated upset count `X` and elapsed time `t` since a refresh/reset, bounded by deterministic scrub interval `T_scr`; experimental/model plots use up to 3,000 s (pp. 2488–2491). |
| Aggregation level | `[SOURCE]` Word → physical row → modeled memory block/entire assumed memory; a separate formula derives “MTBF of a word.” No system-visible service event is modeled (Sections IV–V). |
| ECC / decoder outcome | `[SOURCE]` Main model uses SEC; a DEC-TED example changes the simulated row-failure distribution. The equations classify multiplicity beyond correction capability as failure but do not distinguish DUE, SDC, or miscorrection outcomes (pp. 2484–2487). |
| Scrubbing | `[SOURCE]` Periodic scan of the stored data, ECC correction, and writeback/reset of accumulated errors. `T_scr` is a deterministic full-memory interval; the model assumes accumulated errors remain until scrubbing or reset (pp. 2485, 2488). |
| Error statistics | `[SOURCE]` Empirical geometric distribution of row-group number with a count-dependent parameter; Weibull fit for row failure versus upsets; compound-Poisson total-upset count; Poisson arrival process and geometric MCU size in the simulator (Sections III–V). |
| Interleaving / mapping | `[SOURCE]` Regular scalar interleaving distance in physical-row bit units, routed through column multiplexing. The unknown 45 nm hierarchy is replaced by an assumed `8×16` block structure with `256×64` cells per block (pp. 2483–2484). |
| Direct MCU vs independent accumulation | `[SOURCE]` The event generator distinguishes an arrival as MCU or SBU, but the analytical row-group model intentionally plots accumulated upsets “without the distinctions of the MCU or SBU.” Final failure probability is not partitioned by causal mechanism (pp. 2485, 2490). |
| Double-counting status | `[INFERENCE]` The equations do not add separate direct and accumulated failure terms, so explicit double counting is not visible. Instead, the mechanisms are merged into total upset count and row grouping. The model cannot produce separate mechanism rates, and adding a separate direct-MCU term without repartitioning would overlap its existing total. |

## 1. Research problem

- `[SOURCE]` Existing interleaving selection models based on MCU row depth and total upset count do not adequately represent errors that continue accumulating between scrub/reset operations (Introduction and Section III, pp. 2483–2485).
- `[SOURCE]` A reliability model is needed that relates error accumulation, row clustering, ECC/interleaving, and scrub interval to memory failure probability (Abstract; Introduction).

## 2. Objective

- `[SOURCE]` Propose a statistical failure model incorporating row grouping of accumulated upsets, interleaving distance, and scrub interval; compare it with 45 nm SRAM accelerated-test data and use it to examine design cases (pp. 2483–2492).

## 3. Studied system/model

- `[SOURCE]` Target: SRAM protected primarily by SEC and regular interleaving; the method is illustrated for physical rows of 64 bits and IDs `2,4,8,16` (Sections II-B and IV-A).
- `[SOURCE]` Experimental data: five instances of an anonymized 45 nm SRAM, nine tests, different voltages and patterns, white neutron spectrum up to 800 MeV at LANSCE, average test duration 31,990 s (p. 2483).
- `[SOURCE]` Actual hierarchy was unavailable. Using address-scrambling information, the authors analyzed the memory as if it consisted of `8×16` blocks, each with 256 rows and 64 columns, and as if alternative ID schemes had been implemented (pp. 2483–2484).
- `[SOURCE]` For statistical analysis, data from multiple blocks were folded into one block because failure populations were small (Section III, p. 2485).

## 4. Method

- `[SOURCE]` Derive a row-group number (`rgn`) distribution from accumulated upset locations. `rgn=g` means a row contains `g` upset cells when the memory contains `X` upsets (Section III).
- `[SOURCE]` Fit the row-group distribution with a geometric law whose parameter decreases exponentially with total accumulated upset count (Eqs. 1–2).
- `[SOURCE]` Simulate one 64-bit row under SEC for several IDs and fit the row-failure distribution versus number of row upsets with a Weibull model (Eqs. 3–4; Figs. 8–10).
- `[SOURCE]` Aggregate row failure to memory failure using the row-group probability and the number of physical rows (Eqs. 5–6).
- `[SOURCE]` Combine conditional memory failure with the compound-Poisson total-upset distribution from the earlier C46 model to obtain time-dependent `F(t,ID)` and `R(t,ID)` (Eqs. 7–9).
- `[SOURCE]` Convert periodic-maintenance reliability to a word MTBF expression and compare analytical curves with averaged test data and a separate Monte Carlo simulator (Eq. 10; Section V).

## 5. Assumptions

- `[SOURCE]` A physical row is the word-line row; a logical word is the ECC-protected unit selected through column multiplexing (Section II-B, p. 2484).
- `[SOURCE]` Main ECC abstraction is SEC; word failure occurs when the number of upsets exceeds the number of correctable bits (p. 2484).
- `[SOURCE]` Accumulated row-group number follows a geometric distribution with parameter `r_rgn(X)` (Eq. 1).
- `[SOURCE]` The geometric parameter is modeled as `a_rgn exp(-b_rgn X)` and fitted to averaged test data (Eq. 2).
- `[SOURCE]` Row failure versus `L` upsets and ID follows a Weibull CDF whose parameters are obtained from MATLAB simulations (Eqs. 3–4; Table I).
- `[SOURCE]` Total upset count over time follows the compound-Poisson geometric model reused from C46 (Eq. 7).
- `[SOURCE]` The derivation requires total upset count `X≤X_max`; the authors state that a sufficiently short scrub interval can enforce this operating range (Eqs. 5–8; p. 2488).
- `[SOURCE]` Test results from different voltage/pattern conditions are mixed and averaged to avoid bias toward a particular condition (pp. 2484, 2488).
- `[SOURCE]` In the Monte Carlo simulator, event arrival is Poisson; each arrival is classified as MCU or SBU by a uniform random draw using an MCU ratio; MCU size is geometrically distributed (Fig. 15; p. 2490).
- `[SOURCE]` For failure simulations, MCU/SBU locations are randomly placed while MCU shapes and shape-occurrence rates follow test data (p. 2490).
- `[INFERENCE]` The full-memory scrub is treated as an effective reset with complete correction of all correctable states; scrub duration, ordering, imperfect coverage, and concurrent access are not in the equations.

## 6. Independent/input variables

- `[SOURCE]` `X`/`x`: total number of accumulated upsets in the modeled memory, count.
- `[SOURCE]` `g`: row-group number, i.e. number of upsets in one physical row, count.
- `[SOURCE]` `ID`: scalar interleaving distance in physical-row cell units.
- `[SOURCE]` `R_rows`: number of physical rows and `B`: number of bits in a physical row. The article uses `R` for row count while also using `R(t,ID)` for reliability; this card separates the symbols.
- `[SOURCE]` `λ`: event-arrival rate, in arrivals per second for the fitted test (`0.0099 s⁻¹`, Table II).
- `[SOURCE]` `r`: compound-Poisson geometric parameter (`0.5352` in the averaged test, Table II).
- `[SOURCE]` `a_rgn`, `b_rgn`: row-group parameter coefficients (`0.9428`, `0.001925` in Table II).
- `[SOURCE]` `α_ID`, `β_ID`: Weibull shape and scale parameters by ID (Table I).
- `[SOURCE]` `t` and `T_scr`: elapsed time and deterministic scrub interval, seconds in the reported figures.
- `[SOURCE]` Scenario variables in Section V-B: MCU ratio and SRAM aspect ratio/row-column organization (Table III).

## 7. Dependent/output variables

- `[SOURCE]` `p_rgn(g,X)`: probability that a row has exactly `g` upsets given `X` total upsets, dimensionless (Eq. 1).
- `[SOURCE]` `F_row(L,ID)`: probability of one or more failing words in a row according to the operational definition used in the model, dimensionless (Eq. 4 and adjacent prose).
- `[SOURCE]` `F_mem(X,ID)`: probability that the modeled memory has one or more failing words conditional on `X`, dimensionless (Eq. 5).
- `[SOURCE]` `F(t,ID)` and `R(t,ID)`: cumulative memory failure probability and reliability over one accumulation interval, dimensionless (Eqs. 8–9).
- `[SOURCE]` MTBF of a word under periodic maintenance, seconds for the plotted time base (Eq. 10; Figs. 12 and 20).

## 8. Baselines/comparators

- `[SOURCE]` Earlier C46 model based on total upset count and MCU row depth, described as unsuitable for accumulated errors because accumulated row depth does not retain the earlier geometric behavior (Introduction; Section III).
- `[SOURCE]` IDs `2,4,8,16` under SEC (Figs. 8–9 and 11–14).
- `[SOURCE]` SEC versus DEC-TED for `ID=2` in a row-level simulation (Fig. 10).
- `[SOURCE]` Analytical model versus averaged 45 nm test-derived failure probability (Figs. 11–12).
- `[SOURCE]` Analytical model versus a 1,000-repetition event simulator for three scenarios: test-like Case 1, high-MCU-ratio Case 2, and altered-aspect-ratio Case 3 (Tables III–IV; Figs. 18–20).

## 9. Main equations/models

### 9.1 Row-group distribution

`[SOURCE]` Equation (1), p. 2485:

\[
p_{rgn}(g,x)=r_{rgn}(x)\left(1-r_{rgn}(x)\right)^{g-1},
\qquad g\ge1,\;x\ge1.
\]

`[SOURCE]` Equation (2), p. 2486:

\[
r_{rgn}(x)=a_{rgn}\exp(-b_{rgn}x).
\]

### 9.2 Row-failure Weibull model

`[SOURCE]` Equations (3)–(4), p. 2487:

\[
f_{row}(L,ID)=
\frac{\alpha_{ID}}{\beta_{ID}}
\left(\frac{L}{\beta_{ID}}\right)^{\alpha_{ID}-1}
\exp\!\left[-\left(\frac{L}{\beta_{ID}}\right)^{\alpha_{ID}}\right],
\]

\[
F_{row}(L,ID)=
1-\exp\!\left[-\left(\frac{L}{\beta_{ID}}\right)^{\alpha_{ID}}\right].
\]

### 9.3 Word/row-to-memory aggregation

`[SOURCE]` Equation (5), p. 2487, rewritten only to disambiguate `R_rows` from reliability `R(t,ID)`:

\[
F_{mem}(X,ID)=
\sum_{g=2}^{b}
\frac{p_{rgn}(g,X)X}{g}
\frac{F_{row}(g,ID)}{R_{rows}}.
\]

`[SOURCE]` The upper limit `b` depends on `X` and row width `B`; `F_mem` is defined as the probability of one or more failing words in the memory.

`[SOURCE]` Equation (6):

\[
X_{max}=\sum_{g=1}^{B}p_{rgn}(g,x)\,g\,R_{rows}.
\]

### 9.4 Time-domain failure and reliability

`[SOURCE]` Equation (7) reuses the geometric compound-Poisson distribution:

\[
CP(X,t)=\sum_{Y=1}^{X}
\frac{(\lambda t)^Y e^{-\lambda t}}{Y!}
\binom{X-1}{Y-1}r^{X-Y}(1-r)^Y.
\]

`[SOURCE]` Equations (8)–(9), p. 2488:

\[
F(t,ID)=\sum_{x=2}^{X_{max}}CP(x,t)F_{mem}(x,ID),
\qquad
R(t,ID)=1-F(t,ID).
\]

### 9.5 Periodic-maintenance MTBF

`[SOURCE]` Equation (10), p. 2488, with the row-count symbol disambiguated:

\[
MTBF_{word}=
\frac{\int_0^{T_{scr}}R(t,ID)\,dt}
{1-R(T_{scr},ID)}
\cdot\frac{1}{ID\,R_{rows}}.
\]

`[SOURCE]` The expression is attributed to a periodic-maintenance approximation [19]. The current card does not independently audit that cited derivation.

## 10. Main results

- `[SOURCE]` The row-group parameter fitted to averaged test data decreases from near 1 as upset count grows; the fitted values shown for Fig. 6 are approximately `a_rgn=0.94` and `b_rgn=0.002` (p. 2486).
- `[SOURCE]` At a 3,000 s scrub interval, averaged test-derived failure probabilities are reported as `0.92%`, `0.23%`, `0.07%`, and `0.01%` for IDs `2,4,8,16` (Fig. 11; p. 2488).
- `[SOURCE]` The maximum and average absolute differences between the analytical model and test-derived failure probabilities are reported as `0.0007` and `0.00015`, respectively (p. 2488). The abstract expresses the average difference as `0.015%`.
- `[SOURCE]` Conditional example: if the required failure probability at 3,000 s is below `0.5%`, the authors state that IDs 8 and 16 are unnecessary and ID 2 can meet the same level with a 2,000 s scrub interval (p. 2488). This is not a project requirement.
- `[SOURCE]` The authors state that scrub interval should be less than the computed word MTBF; for the plotted ID 4 example they give a value below 2,500 s (Fig. 12; p. 2489).
- `[SOURCE]` In simulations, increasing MCU ratio from `0.29` to `0.8` increases total upsets and gives 2.8 times the Case 1 failure probability at 3,000 s; changing aspect ratio from `256×64` to `64×256` produces 11.8 times the Case 1 failure probability (Tables III–IV; Fig. 19, p. 2491).
- `[SOURCE]` The 1,000-run simulator reproduces the arrival-count trend with an average difference of 2.61 upsets/s, and the failure-probability maximum/average differences are reported as `0.0007`/`0.00011` (Figs. 16–17, p. 2490).
- `[SOURCE]` The paper labels 2,700 s and 1,200 s as optimal scrub intervals for Cases 1 and 2 based on comparison of MTBF with interval; Case 3 requires an interval below 1,000 s within the examined range (pp. 2491–2492). No resource-cost optimization is performed.

## 11. Author-stated limitations

- `[SOURCE]` Detailed hierarchy and physical architecture of the tested 45 nm SRAM were unavailable; only address scrambling was known, and alternative IDs were imposed analytically (p. 2483).
- `[SOURCE]` Data from different voltages and patterns were averaged; MCU characteristics are acknowledged to depend on conditions, layout, and architecture (p. 2484).
- `[SOURCE]` Multiple blocks were folded into one because the observed failure population was insufficient for statistical analysis (p. 2485).
- `[SOURCE]` Equation 5 is invalid for `X>X_max`; the authors require scrubbing to keep operation within the modeled range (p. 2488).
- `[SOURCE]` The compound-Poisson model controls total upset count but cannot directly adjust the MCU/SBU ratio; the simulator adds separate random processes for this purpose (pp. 2489–2490).
- `[SOURCE]` Parameters for the altered-aspect-ratio Case 3 depend on the upset-count range over which they are extracted (Table IV note, p. 2491).

## 12. Methodological limitations inferred by us

- `[INFERENCE]` “Accumulated” and “clustered” are overlapping descriptors, not mutually exclusive failure classes: the same physical upset can be part of an MCU, remain accumulated between scrubs, and contribute to a clustered row group.
- `[INFERENCE]` Direct same-particle word failure and temporal multi-event accumulation are not separately measurable in `F_mem` or `F(t,ID)` because event provenance is removed before the row-group aggregation.
- `[INFERENCE]` The 45 nm comparison is predominantly an in-sample calibration/reproduction exercise: `λ`, `r`, row-group parameters, assumed geometry, and MCU pattern information are derived from the same test corpus.
- `[INFERENCE]` The reported `0.015%` gap therefore does not establish out-of-sample predictive validity for another SRAM, layout, radiation spectrum, or mission environment.
- `[INFERENCE]` The “optimal scrub interval” criterion is only `T_scr<MTBF` within selected cases; no bandwidth, energy, latency, or controller-cost objective is optimized.
- `[INFERENCE]` The model assumes a synchronous effective reset at a full-memory scrub boundary and does not represent sequential scrub exposure ages.
- `[INFERENCE]` Decoder semantics are reduced to correction capability; narrative references to SDC and DUE are not mapped to separate mathematical states.

## 13. Threats to validity

- `[INFERENCE]` Architecture threat: the true device mapping and block hierarchy are replaced by an assumed `8×16` set of `256×64` blocks.
- `[INFERENCE]` Data-mixing threat: different voltages, patterns, chips, and runs are averaged despite acknowledged sensitivity of MCU distributions to those factors.
- `[INFERENCE]` Statistical threat: folding blocks increases sample size but may erase block-level heterogeneity; the statement that randomness is unchanged does not test independence between blocks.
- `[INFERENCE]` Model-form threat: geometric row grouping, exponential parameter drift, Weibull row failure, and compound-Poisson arrivals are all fitted/assumed layers whose joint uncertainty is not propagated.
- `[INFERENCE]` Event-definition threat: the row-failure prose is internally inconsistent (“more than one” versus “one or more” failing words), while the memory event is clearer.
- `[INFERENCE]` External-validity threat: accelerated terrestrial-neutron data do not directly validate mission-time scaling; the authors explicitly say the scrub interval must be scaled by the environmental arrival rate (p. 2490).

## 14. What the paper actually demonstrates

- `[SOURCE]` The authors construct a hierarchical probability model linking accumulated upset count, row grouping, ID-dependent row failure, compound-Poisson time evolution, and periodic-maintenance MTBF (Sections III–IV).
- `[SOURCE]` Within the assumed 45 nm architecture and fitted parameters, the analytical failure-probability curves closely reproduce test-derived curves for IDs `2,4,8,16` over 0–3,000 s (Fig. 11).
- `[SOURCE]` Simulation cases demonstrate that MCU ratio and memory aspect ratio can change total-upset evolution, row grouping, failure probability, and inferred scrub interval (Figs. 18–20).
- `[INFERENCE]` For `RQ-001`, the strongest contribution is an explicit word→row→memory aggregation over one scrub interval. It is not a mechanism-separated direct/accumulation model.

## 15. What cannot legitimately be claimed from this paper

- `[INFERENCE]` It cannot validate the true ID or physical-cell-to-codeword mapping of the tested 45 nm SRAM.
- `[INFERENCE]` It cannot show that “accumulated” and “clustered” failures are mutually exclusive categories.
- `[INFERENCE]` It cannot provide separate direct-MCU and independent-accumulation cross sections or rates.
- `[INFERENCE]` It cannot establish absence of double counting in a future model that adds an external direct-MCU rate; the published total already merges mechanisms.
- `[INFERENCE]` It cannot establish general mission reliability or a project numerical threshold from the accelerated 3,000 s examples.
- `[INFERENCE]` It cannot establish a globally optimal scrub interval because resource costs and service constraints are not optimized.
- `[INFERENCE]` It cannot distinguish DUE, SDC, and miscorrection at the decoder/system level.

## 16. Relevance to this dissertation

- `[INFERENCE]` Directly relevant to `RQ-001` as the most explicit of the three analyzed sources for codeword→row→memory aggregation and scrub-interval horizon.
- `[INFERENCE]` Its row-group abstraction may be useful as a comparator if this project tests whether event-resolved physical mapping `\mathcal W` provides information lost by aggregate row statistics.
- `[INFERENCE]` The source is also a warning that a combined total failure model cannot later be decomposed into direct and accumulation rates unless event identity is preserved upstream.
- `[INFERENCE]` The assumptions in C38 belong to RQ-002/RQ-003 evaluation and must not be adopted as project assumptions merely because the fit is close.

## 17. Candidate claims for later Orchestrator/Evidence Auditor review

These are candidate statements only; no `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` C38 defines memory failure as one or more ECC words exceeding correction capability in the modeled memory.
2. `[SOURCE-CANDIDATE]` C38 models accumulated row occupancy with a geometric row-group distribution whose parameter varies with total upset count.
3. `[SOURCE-CANDIDATE]` C38 combines conditional memory failure with a compound-Poisson total-upset process over a deterministic scrub interval.
4. `[INFERENCE-CANDIDATE]` The analytical C38 model merges direct-MCU and independent-event accumulation rather than producing mutually exclusive mechanism rates.
5. `[INFERENCE-CANDIDATE]` The reported 45 nm agreement validates in-sample reproduction under an assumed architecture, not general predictive validity.

## 18. Contradictions/tensions with other known papers

- `[SOURCE]` C38 explicitly states that the earlier C46 row-depth model is unsuitable when errors accumulate because accumulated row depth no longer follows the earlier geometric behavior (Introduction; Section III).
- `[SOURCE]` Nevertheless, C38 reuses C46’s compound-Poisson total-upset model as Eq. 7 and adds a new accumulated row-group layer (pp. 2488–2490).
- `[INFERENCE]` This is a change of spatial aggregation, not a clean direct-MCU/accumulation event partition. The card does not adjudicate which spatial abstraction is correct outside the tested conditions.

## 19. Open questions created by this paper

1. `[UNKNOWN]` Can the row-group law and its count dependence be reproduced on an independent SRAM/event-resolved dataset without fitting to the evaluation data?
2. `[UNKNOWN]` How much predictive information is lost when MCU/SBU provenance and event-resolved topology are collapsed into total `X` and row-group number?
3. `[UNKNOWN]` Which of the two contradictory row-failure phrases is intended operationally, and how does that affect Eq. 5?
4. `[UNKNOWN]` How should sequential scrubbing and nonuniform word exposure ages modify `F(t,ID)` and Eq. 10?
5. `[UNKNOWN]` How should DUE, SDC, and miscorrection be represented for a concrete SEC/SEC-DED decoder?
6. `[UNKNOWN]` How should uncertainty in `λ`, `r`, `a_rgn`, `b_rgn`, `α_ID`, and `β_ID` propagate to a reliability constraint?

## Direct answers to the C38 handoff questions

### How are accumulated and clustered errors defined?

- `[SOURCE]` Accumulated errors are MCU and/or SBU errors that remain between scrub/reset operations and can form temporal multi-bit word states (Section II-C). In the analytical layer, clustering is represented by how many accumulated upsets occupy the same physical row (`rgn`) and by the ID-dependent probability that those row upsets form a failing word (Sections III–IV).

### Are those categories mutually exclusive?

- `[SOURCE]` No such mutually exclusive partition is defined. The paper explicitly computes accumulated row depth without distinguishing MCU from SBU (p. 2485). The simulator classifies each arrival as MCU or SBU, but both feed the same accumulated memory state.
- `[INFERENCE]` “Accumulated” is temporal persistence and “clustered” is spatial grouping; one upset/state can have both properties.

### How are row clustering and interleaving handled?

- `[SOURCE]` Row clustering is summarized by `p_rgn(g,X)` with an upset-count-dependent geometric parameter. Interleaving enters through `F_row(g,ID)`, a Weibull fit obtained from random-fault row simulations. Eq. 5 aggregates the two to memory failure.

### What does the comparison with 45 nm SRAM data actually confirm?

- `[SOURCE]` It shows close numerical agreement between model and test-derived failure-probability curves over the assumed IDs and 0–3,000 s, with reported maximum/average absolute gaps `0.0007`/`0.00015`.
- `[INFERENCE]` Because the true architecture is unknown and major parameters are fitted from the same data, it confirms internal reproduction/calibration for the constructed representation, not general predictive validity or the actual physical ID of the device.

### Is there mechanism mixing or double counting?

- `[SOURCE]` Mechanisms are mixed in the final analytical state: total upset count and row grouping do not retain whether the bits came from one MCU or independent arrivals.
- `[INFERENCE]` There is no explicit sum of overlapping direct and accumulation probabilities in the published equations, so direct arithmetic double counting is not demonstrated. The limitation is conflation. A later addition of a separate direct-MCU term would require repartitioning the events already included in `F(t,ID)`.

## Final disposition

- **Recommendation:** `CORE` for `RQ-001`.
- **Confidence:** high for extracted equations, aggregation, and stated test setup; medium for the authors’ broad predictive interpretation because validation is architecture-assumed and in-sample.
- **Evidence gaps:** mutually exclusive mechanism partition, real physical mapping, decoder outcomes, sequential scrub semantics, uncertainty propagation, and external validation.
- **Next action:** Orchestrator acceptance and permanent `PAPER-xxx` assignment; send retained candidate claims to Evidence Auditor rather than accepting them automatically.
