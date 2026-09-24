# INTERNAL-COUNT-GOES16-VALIDATION-REVIEW-01

**Recommendation: PASS — bounded scientific acceptance is recommended.**

Reviewer: Scientific Reviewer. Date: 2026-09-16. This is a recommendation to the Orchestrator, not registration or acceptance of a new RES.

## 1. Object, scope and evidence

Reviewed delivery: **`c0dd38ab3c01917e8e4bb165ecfae122b86dd9ae`**; preregistration/parent: `870a3c5d725793dd45ff2cc2feaf6e8885df0df9`; original base: `7b83f643efb37541547d7d93a65ba2f43acd43fd`. The review branch starts at the delivery. The later commit `82282a8b36b04b388cb3441c474bede30a1287a2` supplies the previously unavailable trial archive; it is an availability supplement, not a replacement scientific target. All three NPZ file hashes and their array hashes match the delivery's manifest.

The review follows the global operating rules, Scientific Reviewer instructions and HANDOFF_CONTRACTS, the supplied review handoff, DEC-001/004 and the relevant dissertation/RES-003/RQ interfaces. It examines the complete new task package, its use of the accepted internal-count controller, and the inherited input functions actually called. It does not reopen the accepted CTMC theorem or evaluate physical qualification, mission requirements, Issue 15, or the executor reference subsystem.

The direct parent chain and task-only delivery diff are verified. Eight frozen files — `prepare.py`, `experiment.py`, `check.py`, `config.json`, `PREREGISTRATION.md`, `selected_windows.json`, `derived_rates.csv`, `input_manifest.json` — are identical between preregistration and delivery. Referenced pipeline hashes and published output hashes match. This establishes the recorded Git ordering and absence of a delivery-time change to those objects; it cannot establish unrecorded historical independence.

## 2. Consolidated disposition

| Object | Disposition and admissible conclusion |
|---|---|
| Nominal GOES-derived input | Supported as the declared frozen reconstruction. Source identity, normalization, selection and calling path are consistent. Absolute calibration and physical representativeness remain assumptions; see the raw-decoding limitation below. |
| Own-count effect | Supported for the three fixed profiles and frozen controller. The primary resource estimand is a ratio of conditional mean passes on common survival, not an unconditional or equal-risk saving. |
| Risk tradeoff | Supported. Growth and peak show a positive paired risk increment with the declared family protection; all reported primary risk uppers remain below experimental epsilon=0.1. Typical-case zero observations do not establish zero risk or equivalence. |
| PA-DOM comparison | Supported only for the specified adaptation and pointwise intervals. There is no general dominance of Proposed. |
| Fixed300 | The sufficient bound and all three numerical instances are independently confirmed. A simple retrospectively certified regime exists on these profiles. No global optimality or CTMC-wide sufficiency follows. |
| Transfer of RES-003 theorem | Not made by this experiment. Its original CTMC validity domain remains unchanged. GOES results are empirical conditional model-mismatch evidence. |
| Journal use | Eligible for bounded acceptance with the wording and conditions in section 8. No new parameter sweep or controller retuning is necessary to support that wording. |

**CRITICAL:** none demonstrated. **MAJOR:** none demonstrated. **MINOR:** none requiring correction demonstrated. The limitations below are limits of evidence and scope, not concealed claims of completed reproduction.

**OPTIONAL-01 — portability of reproduction.** A portable environment recipe and an OS-neutral alternative to Windows `peak_wset` reporting would help future full-run reproduction. The archived trial data now permit the central statistical checks independently of that path. This suggestion does not affect a numerical result and is not an acceptance gate.

## 3. Input and information contract

The five official NOAA GOES-16 files were obtained independently and their SHA-256 identities matched the input manifest. Uncompressed metadata strings corroborate G16, Level 2, five-minute cadence and differential/integral units. **Typed HDF5 arrays were not independently decoded in this environment:** h5py and equivalent readers were unavailable. Consequently, yaw/version/quality array extraction is supported here by source inspection, the pinned raw objects and committed extraction records, not by a second raw-array implementation. Hash identity alone is not scientific validation of that extraction.

The reviewed loader uses the archived temperature-corrected L2 average flux, checks yaw=0, and consistently reorders the sensor fluxes and energies from West/East to East/West. Differential flux is converted from per-keV to per-MeV once; integral P11 is not given that factor. The rate path applies one solid-angle factor of 4pi, then the E/W arithmetic mean and 524288*32 conversion from per-bit to array intensity. There is no imported GOES-19 empirical correction. RADAR identity `b032505d4d1b15403b8ad06aef578339f6d1c6b4`, 3 mm Al, `main_loglog` and scale=1 remain fixed inputs.

The distinction between native G16 P10 upper support 404 MeV and numerical transport cutoff 390 MeV is explicit. Transport stops at 390; the declared 390–500 bridge and >500 integral tail enter once. This is a reconstruction convention, not a claim that 390 is the measured channel edge. The inherited sigma function uses log-log interpolation within support, clipped local linear continuation below the first anchor and constant hold above 186 MeV. Unsupported transport energies and invalid flux are not interchangeable: invalid flux prevents a valid bin, whereas zero transport response outside the declared support is a model convention. The lower-energy spectral extension and retrospective median-gamma fallback remain assumptions. Fallback occurs in 34 East and 135 West bins.

The frozen derived-rate SHA-256 is `e3a1ce8f2a33cd9a60b22039c86ae8f1f7214458850d5a0b609042eace1bc3ac`. Independently checking its table and quality records gives 1440 contiguous 300-second bins, 1429 complete hour windows, nonnegative finite intensities, and the stated selections at indices 732, 753 and 157. All E/W-to-array multipliers agree. The valid-sample threshold permits partially sampled five-minute means; this is not evidence of continuous measurement throughout every bin. There is no interpolation of an invalid bin into a measured zero in the reviewed path.

Selection is input-only: maximum half-hour exposure increase, maximum hour exposure, and lower median hour exposure, with fixed tie rules. The calendar event is still a deliberately selected example, not a representative sample of operations. Retrospective reconstruction can use information from other times; that reconstructed profile drives the external simulator, not the controller observation interface. It establishes no online radiation-estimator capability.

## 4. State transitions, controller and independent checks

Per-bin Poisson counts followed by ordered uniform epochs implement the declared piecewise-constant NHPP. Independent uniform word/bit marks are shared across policies; each policy observes its own completed count. The 60,000 regenerated stream hashes match the archives. Common random numbers improve pairing and do not give one policy another policy's observations.

R2-U checks word j at pass start+(j+1)P/W. An arrival after an early word's check persists into the next service; there is no array-wide reset at pass completion. Repeated hits to the same bit toggle it clear. Two distinct erroneous positions cause first-passage absorption, even if later toggling could have removed an error. The initial state is clean. Terminal arrivals are included, while an unfinished pass supplies no completed count/update. Computational failures remain represented and prevent a successful summary rather than disappearing from the denominator; all archived samples are finite and reported computational-failure counts are zero.

The event-loop endpoint tolerance is 1e-12 seconds. The smallest actual event distance to the 0.1-second pass-end grid is approximately 2.146e-9, 1.176e-10 and 1.890e-7 seconds for the three archived families. Thus it does not change the classification of a published arrival at a pass endpoint. This is an actual-data check, not a claim of exact real-arithmetic behavior for every adversarial timestamp.

Inspection of the call graph and arguments finds no date, intensity profile, physical residual state or survival flag passed into Proposed's decision/filter helpers. Their inputs are the controller belief, resource state, time/action history and own count. Count-disabled propagates qP without conditioning on the count. PA-DOM's initial action uses its declared prior, and its cap/growth/zero-count handling remain frozen. Precomputed switches its action choice at relative time 1800, not on an observed event. Physical residual fields in the illustration are audit output, not controller inputs.

The RE word-set oracle has separately expressed physical state and check chronology, but shares controller helpers and tables. Its address-merging sentinel only challenges the physical mapping path. Repeating its 11 tests is useful reproduction, not a fully independent controller proof. The review therefore adds full-state dense matrix/reward comparisons: 64 action choices and 1536 enabled/disabled count updates, including saturated counts and shortened terminal actions. These are bounded examples linked to production helpers; the tables and accepted moment functions remain shared. The fixed slack and sampled beliefs do not exhaust every controller boundary. Source/algebra inspection supplies the accompanying justification of the affine reduction, rather than treating sampled agreement as a proof.

The accepted arithmetic bound 0.000143018263177913 is below the reserved 0.0002. The reproduced original certificate has floor 0.07667519552414698 and initial slack 0.023324804475853028. Neither quantity is a certificate for the external deterministic GOES profiles.

## 5. Statistical verification and findings

For each policy the review reconstructs failures, survivors, pass means, stop costs, partial service, and the published intervals from the original trial arrays. Clopper–Pearson endpoints are obtained by binomial-tail inversion, independently of production beta quantiles. Empirical variances are obtained from exact integer sums and sums of squares, independently of production variance accumulation.

The primary family has twelve objects: two risks, one paired risk difference and one common-survival gain for each of three cases. Each receives alpha_m=0.05/12. Two-sided CP risk uppers are conservative for the requested upper-bound use. For a paired difference, the two discordant probabilities each receive a two-sided CP interval at alpha_m/2; subtraction and a union bound give the stated interval. The correlations between policies and overlapping calendar windows do not invalidate that union bound.

The empirical Bernstein construction agrees with [Maurer and Pontil, Theorem 4](https://arxiv.org/html/0907.3740v1). For a two-sided mean interval at error alpha, its radius is sqrt(2*s^2*log(4/alpha)/n)+7*R*log(4/alpha)/(3*(n-1)). The ratio uses two mean intervals at alpha_m/2. Bounds on completed surviving passes are [12,18000]; the denominator is at least 12. Zero sample variance therefore retains a nonzero range term. The implementation retains full bounds when the sample is too small.

Conditioning is legitimate for the stated estimand: with a fixed profile and fixed policies, independent trials give i.i.d. pairs; conditional on the number selected by joint survival J, selected pairs have the law conditional on J. Applying the bound for each selected size and averaging over that size preserves coverage. This does not turn J-conditional costs into unconditional operating costs. Individual survivors, common J and costs stopped at first E_cap are different populations and are kept separate.

| Case | Primary paired cells: J / P-only E_cap / disabled-only / both | G_J, family interval (%) | Risk difference, family interval (percentage points) | Proposed family risk upper |
|---|---|---|---|---|
| Growth | 19976 / 21 / 0 / 3 | 75.1706 [74.4789, 75.8548] | +0.105 [+0.0139429, +0.196368] | 0.0020859738 |
| Peak | 19960 / 37 / 0 / 3 | 71.2206 [70.5051, 71.9284] | +0.185 [+0.0709861, +0.298951] | 0.0030862276 |
| Typical | 20000 / 0 / 0 / 0 | 89.3384 [88.7374, 89.9331] | 0 [-0.0343288, +0.0343288] | 0.0003086417 |

All gain lower bounds exceed the preregistered 10% criterion. Growth and peak require an explicit risk–resource tradeoff statement. Typical's interval does not establish risk equivalence. These confidence statements cover Monte Carlo uncertainty conditional on the frozen profiles; they do not cover response calibration, within-bin variation or mission transfer.

PA-DOM is a separate pointwise comparison. Proposed's individual-survivor means are 731.227/847.553/313.983 passes; PA-DOM's are 182.610/182.238/348.325. On common J, Proposed uses approximately 4.0043 and 4.6507 times PA-DOM's passes on growth and peak. Peak has a lower Proposed risk, with pointwise difference interval approximately [-0.349416, -0.119217] percentage points. Typical's pointwise gain is 9.8592%, interval [2.8838,16.2952]%; this supports a positive effect but not a confirmed effect of at least 10%. No family-wide PA-DOM superiority follows.

## 6. Independent Fixed300 derivation and arithmetic

Let d_j=P*(W-1-j)/W and word checks occur at 300k-d_j. With clean start, the per-word history partitions into an initial interval, eleven crossing intervals and a terminal interval. Their array exposures are r_0*(300-d_j), r_(k-1)*d_j+r_k*(300-d_j), and r_11*d_j. The terminal interval is retained even though there is no final reset at H for an earlier-checked word.

A first two-bit capability exceedance requires at least one pair of arrivals in different bits of the same word since its last clean check. Toggle clearing can prevent such a pair from causing failure; it cannot make the necessary pair disappear from the event history. Independent uniform marking of the Poisson stream gives expected unordered distinct-bit pairs choose(32,2)*(L/(32W))^2=(31/64)*(L/W)^2. Union/Markov bounds over words and intervals yield a sufficient upper, without assuming independence of failure events.

The review integrates each of the 524288 word phases explicitly with integer numerators and rational binary64 inputs, rather than reusing production closed-form moment sums. All three exact rationals equal the published values. The decimal ceilings and binary floating-point published uppers both round outwards.

| Profile | Sufficient Fixed300 upper, displayed approximately | Relation to 0.1 |
|---|---|---|
| Growth | 0.03220400957769035 | Below |
| Peak | 0.06291257029543656 | Below |
| Typical | 0.0000006833770851920664 | Below |

These are bounds, not estimated or exact failure probabilities. Fixed300 completes twelve passes over an hour without absorption. Its retrospective certification under a known profile has a different information/robustness status from the original CTMC-certified controls. Nonetheless, it rules out claiming that these examples demonstrate the necessity or resource optimality of complex adaptation. The internal stationary mean approximately 3.06248 s^-1 exceeds these profile means (0.17694, 0.24564 and 0.00082535 s^-1). Conservative initial design is a plausible contributor to the observed channel benefit, not an independently identified sole cause.

## 7. Execution record and limits of independence

Review-owned checkers and saved results are under `checks/internal_count_goes16_validation_review_01/`. The actual commands were executed with `OPENBLAS_NUM_THREADS=1`, Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0 on Linux, with data outside the repository:

```sh
python3 -B docs/scientific_reviews/checks/internal_count_goes16_validation_review_01/check_review.py --data /workspace/scratch/24e1723b7ed9/goes16-review-data --out /workspace/scratch/24e1723b7ed9/goes16-review-data/independent.json
python3 -B docs/scientific_reviews/checks/internal_count_goes16_validation_review_01/check_python_bodies.py --data /workspace/scratch/24e1723b7ed9/goes16-review-data --out /workspace/scratch/24e1723b7ed9/goes16-review-data/python_bodies.json
```

The first command independently checks the archives/statistics, all stream identities and all-word Fixed300 arithmetic without production imports. Raw files were checked separately by SHA-256 and selected metadata-string presence; `raw_identity.json` records that narrower check. The first command's optional `--raw DIR` can repeat hash checking, but its saved invocation did not use that option.

The second executes unchanged Python function bodies extracted in memory, omitting Numba imports/decorators and unused HDF5 imports. Source files were not patched. It passes 11 RE tests, the 64/1536 additional controller checks, and 60 policy-trial replays: trials 0,1,2,19999 times five policies times three cases. The first seven sample fields agree exactly; maximum reward-field discrepancy is 1.4224732503009818e-16. The fixed illustration reproduces all 737 rows/17 fields, maximum discrepancy 6.661338147750939e-16. This is numerical agreement in Python, not byte-identical JIT reproduction. Discrete results agree exactly.

RE's Windows/JIT execution, compileall, fresh-cache derived-rate reproduction and byte-identical aggregate records were inspected as records. The review did **not** execute the full 300000 policy-trial matrix, the JIT path, a fresh transport calculation, typed raw-array extraction or `deliver.py`. It did reconstruct the statistical quantities directly from all 60000 archived trial streams' results. A separate checkout/data area preserved published outputs. Shared RNG design, accepted controller tables, source inputs and inherited physical response assumptions are explicitly retained dependencies. Hashes establish identity, the new numerical checks establish particular implementation properties, and the Fixed300 argument supplies an independent mathematical bound; those are different forms of evidence.

## 8. Maximum admissible result and remaining conditions

> In three preregistered GOES-16-derived hourly examples under the declared nominal response and marked-NHPP memory model, enabling the controller's own completed-count observation reduces the ratio of mean completed passes on common-survival trials relative to disabling that observation in the same frozen method. The estimated reductions are 75.17%, 71.22% and 89.34%, with the declared simultaneous Monte Carlo intervals. In the growth and peak examples this accompanies a statistically established increase in capability-exceedance risk; the family-protected risk uppers remain below the experimental level 0.1. A separate sufficient-bound calculation certifies Fixed300 on all three declared profiles. These examples therefore establish a conditional informational effect and a risk–resource tradeoff, not superiority over simple policies or a physical operating guarantee. RES-003 retains its original CTMC domain.

Conditions are the exact profiles and normalization, clean hourly starts, W=524288 and 32 data bits, uniform singleton toggles, piecewise-constant exogenous intensity, stated R2-U chronology/P, frozen policy/action/count/numerical settings, the specific survival-conditioned resource estimand and statistical family. Acquisition, controller computation and system-level failure costs are not measured. E_cap is not system failure; epsilon=0.1 is not a mission requirement. Neither joint physical coverage nor real-device/multi-bit-event validity is established.

**Orchestrator recommendation:** the evidence supports limited acceptance for the first article in this domain, including its unfavorable comparison with a simple sufficient regime. There is no blocking correction or requirement for a new experiment. Scientific acceptance and subsequent use remain Orchestrator/PI decisions; this review does not change RES-003, DEC-004, main or the physical-transfer track.
