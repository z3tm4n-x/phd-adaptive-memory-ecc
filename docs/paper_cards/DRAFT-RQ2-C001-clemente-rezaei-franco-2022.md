# Draft Paper Card — RQ2-C001

**PAPER-ID:** `TBD until Orchestrator acceptance`  
**Candidate identity:** `RQ2-C001`  
**Related RQ:** `RQ-002`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommendation:** `CORE`  
**Exact full-text identity:** IEEE Transactions on Nuclear Science, vol. 69, no. 2, pp. 169–180, Feb. 2022  
**Full text used:** `Reliability of Error Correction Codes Against Multiple.pdf`; SHA-256 `9b5caea4b2f97787389a1b08dc699ade7ea61a8116bf1ba7a196980dd11bfbf0`

## Bibliographic identity

Juan A. Clemente, Mohammadreza Rezaei, and Francisco J. Franco, “Reliability of Error Correction Codes Against Multiple Events by Accumulation,” *IEEE Transactions on Nuclear Science*, vol. 69, no. 2, pp. 169–180, Feb. 2022. DOI: `10.1109/TNS.2022.3143652`.

`[SOURCE]` The analyzed IEEE full text and the primary IEEE record identify the authors in this order as Juan A. Clemente, Mohammadreza Rezaei, and Francisco J. Franco. The first page records receipt on 7 Sep. 2021, revision on 13 Dec. 2021, acceptance on 12 Jan. 2022, publication on 14 Jan. 2022, and current-version date 16 Feb. 2022 (p. 169).

## Common extraction summary

| Field | Extraction |
|---|---|
| Primitive arrival object | `[SOURCE]` A randomly located bit flip/hit, represented by address coordinate `x` and bit position `y`; Sec. II.B, pp. 171–172. |
| Count/arrival process | `[SOURCE]` The analytical model is conditional on total hits `m` (or observed bit flips `N_BF`), not elapsed time. The Poisson law in Sec. III models the **count of false MBUs**, not particle arrivals. |
| Independence/stationarity | `[SOURCE]` Hits are assumed independent and uniformly distributed over cells. `[UNKNOWN]` No empirical time-independence test or stationary/nonstationary temporal process is supplied. |
| Event multiplicity/topology | `[SOURCE]` Sequential independent hits may create false 2-, 3-, …, `k`-bit MBUs in one word. Physical event topology is excluded by the interleaving assumption. |
| Parent-event provenance | `[SOURCE]` The model represents accumulated independent hits only; true same-particle MBUs are outside scope. |
| Mapping `W` | `[SOURCE]` Statistical interleaving assumption: a single particle cannot produce an MBU. Logical state is `(address x, bit y)`; no physical coordinate map or interleaving distance is given. |
| Accumulation/initial state | `[SOURCE]` State is the hit/occupancy pattern over `L_A×W` cells; Monte Carlo begins all-zero. Repeated hits toggle and can cancel. No general initial distribution. |
| Repair/scrub semantics | `[SOURCE]` One or more equally spaced global scrubs reset accumulated errors; the paper does not model scan duration, per-word phase, or asynchronous word ages (Sec. III.C, Fig. 10). |
| Failure abstraction | `[SOURCE]` Probability of at least one false MBU beyond a code's correction pattern, called loss of data integrity; Eqs. (16)–(21). Decoder outcomes are not resolved. |
| Recombination | `[SOURCE]` Direct same-particle events are excluded rather than recombined with accumulation. |
| Uncertainty/validation | `[SOURCE]` Closed forms are checked by `10^5`-trial Monte Carlo with 95% standard-error bars and compared with sparse irradiation counts (Secs. II.C–II.D). |
| Exactness status | `[SOURCE]` Occupancy equations include explicit approximations/corrections for repeat hits; the Poisson failure layer treats an expected false-MBU count as its mean. |
| Relation to `E_cap`/`F_A` | `[INFERENCE]` Compatible as a conditional accumulation kernel for clean, globally reset intervals if an external count process supplies `m`; not equivalent to general windowed first passage `F_A(t0,T; μ_t0)`. |

## 1. Research problem

- `[SOURCE]` Independent radiation events accumulated in an interleaved memory can place multiple erroneous bits in one word and defeat ECC even when a single particle cannot do so (Introduction; Sec. II.A, pp. 169–171).

## 2. Objective

- `[SOURCE]` Derive analytical expressions for false multiple-bit upsets caused by accumulation, validate them by Monte Carlo and irradiation datasets, and estimate failure probabilities for several ECC capabilities and scrubbing counts (Abstract; Secs. II–III).

## 3. System/model studied

- `[SOURCE]` An `L_A`-address memory with word width `W`, assumed sufficiently interleaved that one particle cannot create a multiple-bit upset in a word (Sec. II.A).
- `[SOURCE]` ECC examples include SEC-DED, DAEC, DEC-TED, TAEC, TEC, and SNC-DND (Sec. III.B, pp. 175–177).
- `[SOURCE]` Experimental comparisons use 2M×8 Infineon SRAMs in 65-, 90-, and 130-nm technologies under neutron, proton, and thermal-neutron irradiations (Sec. II.D, Tables I–IV).

## 4. Method

- `[SOURCE]` Treat random hits as balls assigned uniformly to address/bit cells; derive the expected number of addresses hit `k` times and correct for repeated hits/cancellations (Eqs. (1)–(12), Sec. II).
- `[SOURCE]` Validate with `10^5` Monte Carlo trials. Each trial initializes memory to zero, draws uniform `(x,y)` locations, toggles the selected bit, and counts final word patterns (Sec. II.B–II.C).
- `[SOURCE]` Use expected counts of uncorrectable false MBUs as Poisson means to compute at-least-one probabilities for ECCs (Eqs. (13)–(21), Sec. III).

## 5. Assumptions

- `[SOURCE]` Hit locations are independent and uniformly distributed over memory cells (Sec. II.B).
- `[SOURCE]` Memory is interleaved so a single particle cannot generate an MBU in one word, except mechanisms such as SEFI that are outside the model (Sec. II.A).
- `[SOURCE]` Repeated hits toggle cells; an even number of hits can cancel an observed error (Sec. II.B).
- `[SOURCE]` The Poisson count model in Sec. III uses the analytically expected false-MBU count as `λ`.
- `[SOURCE]` Scrub cycles are equally spaced and restore a clean state for the next accumulation segment (Sec. III.C, Fig. 10).
- `[INFERENCE]` There is no temporal stationarity assumption because time is absent; interpreting hit counts as time requires an external arrival model.

## 6. Input parameters

- `[SOURCE]` Memory length `L=L_AW`, address count `L_A`, word width `W`, actual hit count `m`, and observed bit-flip count `N_BF` (Sec. II, Eqs. (1)–(12)).
- `[SOURCE]` ECC capability/pattern class and number of equally spaced scrub operations (Sec. III).

## 7. Output parameters

- `[SOURCE]` Expected number of addresses hit `k` times, expected false `k`-bit MBU counts, adjacent/nonadjacent subsets, and Poisson probability of at least one uncorrectable false MBU (Eqs. (2)–(22)).
- `[SOURCE]` Outputs are dimensionless probabilities or counts conditional on total accumulated hits/observed bit flips, not time rates.

## 8. Baselines/comparators

- `[SOURCE]` Analytical formulas versus Monte Carlo simulations (Figs. 2–9).
- `[SOURCE]` Predicted false MBU counts versus observed MBU counts in published irradiation tests (Tables I–IV).
- `[SOURCE]` ECC families and different numbers of equal scrub cycles (Figs. 10–12).

## 9. Main equations/models

- `[SOURCE]` Eq. (1) estimates actual hits from observed flips: `m≈round(N_BF+N_BF^2/L)`.
- `[SOURCE]` Eq. (2) gives expected addresses hit exactly `k` times under uniform allocation; Eqs. (3)–(5) account for repeat-hit cancellation in false 2-, 3-, and 4-bit MBUs.
- `[SOURCE]` Eqs. (7)–(11) split adjacent/nonadjacent patterns; Eq. (12) handles SNC-DND nibble structure; Eq. (22) generalizes false `k`-bit MBU counts.
- `[SOURCE]` Eq. (13): cumulative false-MBU count `N_FM^+(k)=Σ_{i=k}^{W}N_FM(i)`.
- `[SOURCE]` Eqs. (14)–(15): Poisson PMF/CDF with mean `N_FM^+(k)`.
- `[SOURCE]` Eqs. (16)–(21): probability of at least one ECC-uncorrectable false pattern for SEC-DED, DEC-TED, TEC, DAEC, TAEC, and SNC-DND.

## 10. Main results

- `[SOURCE]` Closed-form predictions track Monte Carlo means across false-MBU multiplicities and adjacency classes within reported confidence intervals (Figs. 2–9).
- `[SOURCE]` Predicted accumulated false-MBU counts are comparable to the sparse observed counts in the cited irradiation datasets (Sec. II.D, Tables I–IV).
- `[SOURCE]` Increasing the number of equally spaced scrub cycles reduces the modeled probability of loss of data integrity in the evaluated count-conditioned scenarios (Sec. III.C, Figs. 10–12).
- `[INFERENCE]` Experimental count agreement is consistent with accumulation but cannot assign parent-particle provenance to each observed MBU.

## 11. Author-stated limitations

- `[SOURCE]` Check-bit errors are not included and are left for future work (Conclusion, p. 179).
- `[SOURCE]` The model focuses on accumulation in interleaved memories; true same-particle MBUs are outside scope (Sec. II.A).
- `[SOURCE]` The irradiation comparisons contain small observed MBU counts, limiting statistical strength (Sec. II.D tables/discussion).

## 12. Methodological limitations inferred

- `[INFERENCE]` The source gives no law for `m(t)`, so it cannot produce a mission-time or window-time probability without an external arrival/count model.
- `[INFERENCE]` The final occupancy can decrease through toggling. Therefore a word may cross ECC capability and later return below it; the paper's final/count-based event is not necessarily the first-passage event `E_cap`.
- `[INFERENCE]` Global equal scrubs erase word-age heterogeneity and do not represent sequential scanning or partial writeback.
- `[INFERENCE]` Direct events are excluded by assumption, so the paper does not establish a disjoint direct-plus-accumulation recombination rule.

## 13. Threats to validity

- `[INFERENCE]` Construct validity: “loss of data integrity” is inferred from error patterns, without decoder-specific DUE/SDC/miscorrection outcomes.
- `[INFERENCE]` External validity: uniform random hits and ideal interleaving may not hold for spatially correlated MCU topologies.
- `[INFERENCE]` Temporal validity: no time-varying intensity, burst process, or reporting-window phase is represented.
- `[INFERENCE]` Experimental identifiability: final bitmap/count data cannot reliably distinguish true direct MBUs from accumulated false MBUs.

## 14. What the paper actually demonstrates

- `[SOURCE]` Under uniform independent cell hits, false multiple-bit word patterns from accumulation can be predicted from memory dimensions and hit count and agree with the authors' Monte Carlo (Secs. II–III).
- `[SOURCE]` The conditional probabilities can differentiate ECC pattern capabilities and idealized equal scrub partitions (Eqs. (16)–(21), Figs. 10–12).
- `[INFERENCE]` It supplies a computationally cheap accumulation-state component, not a complete radiation-event process.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` The paper does not validate Poisson particle arrivals, temporal independence, or stationarity.
- `[INFERENCE]` It does not quantify true same-particle MCU rates/topology or combine them with accumulation.
- `[INFERENCE]` It does not provide a physical-to-codeword map `W` or preserve a joint post-`W` event mark.
- `[INFERENCE]` It does not compute general `F_A(t0,T; μ_t0)` or establish decoder outcomes.

## 16. Relevance to the dissertation

- `[INFERENCE]` Directly informs candidate accumulation state variables: cell/word occupancy, total hit count, and elapsed exposure since the last effective reset.
- `[INFERENCE]` Provides conditional false-MBU kernels that could be embedded beneath `E_cap` only after defining the external marked arrival process, `W`, repair semantics, and first-passage logic.
- `[INFERENCE]` Shows that observed `N_BF` may not equal actual hit count because repeat hits cancel.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` Independent uniformly located bit hits can create false multi-bit word errors by accumulation even when one particle cannot affect multiple bits in one word (Sec. II.A–II.B).
2. `[SOURCE-CANDIDATE]` Repeated hits can toggle/cancel errors, so actual hit count and observed erroneous-bit count differ (Eq. (1), Sec. II.B).
3. `[SOURCE-CANDIDATE]` The paper's Poisson layer applies to the number of false MBU occurrences conditional on accumulated hits, not to radiation arrival times (Sec. III.A, Eqs. (14)–(15)).
4. `[SOURCE-CANDIDATE]` Equal idealized scrub partitions reduce accumulated false-MBU probability in the studied scenarios (Sec. III.C, Figs. 10–12).
5. `[INFERENCE-CANDIDATE]` A final-occupancy model with toggling is not automatically a first-passage `E_cap` model.

## 18. Tensions/conflicts

- `[INFERENCE]` The interleaving assumption intentionally removes direct same-particle MCU, while RQ-002 must retain that mechanism unless bounded away for the declared domain.
- `[INFERENCE]` The source's count-conditioned horizon is incompatible with direct use as a mission/reporting-window probability.

## 19. Open questions/evidence gaps

1. `[UNKNOWN]` What external arrival/count process maps mission exposure to `m` for each partition of `A`?
2. `[UNKNOWN]` What initial occupancy distribution `μ_t0` applies when a reporting window begins mid-scrub cycle?
3. `[UNKNOWN]` How should direct same-particle post-`W` marks be recombined without overlap?
4. `[UNKNOWN]` How should first passage be tracked when later hits can cancel earlier errors?
5. `[UNKNOWN]` What scan/writeback policy creates nonuniform word ages in the target controller?

## Feature map to the DEC-001 contract

| Contract feature | Compatibility assessment |
|---|---|
| `E_cap(A;t0,T)` | `[INFERENCE]` Partial match: the ECC-exceeding pattern is related, but the paper computes a count/final-state at-least-one event and does not guarantee first passage within `[t0,t0+T]`. |
| Declared domain `A` | `[INFERENCE]` Memory dimensions are explicit, but heterogeneous banks/mappings are not partitioned. |
| `F_A(t0,T; μ_t0)` | `[INFERENCE]` Mismatch as published: no `t0`, `T`, or general `μ_t0`. A conditional kernel could be reused after supplying these externally. |
| Initial state | `[SOURCE]` Clean all-zero Monte Carlo start and clean scrub segments only. |
| Mapping `W` | `[SOURCE]` Only an ideal statistical interleaving assumption; no explicit map. |
| Repair semantics | `[SOURCE]` Equal instantaneous global reset segments; no sequential ages. |
| Direct/accumulation partition | `[SOURCE]` Accumulation only; direct events excluded, no recombination. |
| Decoder outcomes | `[SOURCE]` Capability-pattern abstraction only; RQ-003 semantics remain unresolved. |

## Equations and assumptions requiring reproduction

- Reproduce Eqs. (1)–(5) and (22) with exact rounding/toggle-cancellation rules before using observed `N_BF` as a proxy for hits.
- Reproduce Eqs. (13)–(21) separately from the occupancy layer; verify that the expected false-MBU count is used as a Poisson mean.
- Reproduce the Monte Carlo with all-zero start, uniform independent `(x,y)` draws, toggling on repeat hits, and `10^5` trials.
- Treat equal scrubs as `k+1` clean, equal exposure segments; do not insert scan duration or word-age semantics absent from the source.

## Final disposition

- **Recommendation:** `CORE` for accumulation state and conditional false-MBU modeling.
- **Confidence:** high for formulas/simulation assumptions; medium for irradiation interpretation because mechanism provenance is not observed.
- **Evidence gaps:** temporal arrival law, nonstationarity, explicit `W`, direct-event recombination, first-passage state, realistic sequential scrubbing, and uncertainty propagation into `F_A`.
