warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/decision_sensitivity.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/dependence_validation.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/registered_direct_by_energy.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/risk_curves.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-ECC-RISK-BRIDGE-01/window_risk_summary.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-PAPER-COMPLETION-01/cosrad_member_manifest.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-PAPER-COMPLETION-01/cosrad_operator_closure.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-PAPER-COMPLETION-01/legacy_article_regression.csv', CRLF will be replaced by LF the next time Git touches it
warning: in the working copy of 'experiments/RE-CY62167-PAPER-COMPLETION-01/shielding_boundary_summary.csv', CRLF will be replaced by LF the next time Git touches it
# GOES-REAL-TEMPORAL-REVIEW-01

## 1. Scope and recommendation

**REVISE. One MAJOR finding; no CRITICAL finding.** The envelope theorem, causal information contract, recursive certificate preservation and independently checked principal examples are supported. The claim that the exported g-map is a complete certified decision/resource map is not supported: close-root processing produces demonstrated wrong action labels on narrow, replay-compatible intervals. Export rounding also invalidates some advertised root brackets. This requires a bounded numerical repair, not a new physical model, experiment, window selection or transport calculation.

- Reviewed implementation: `bb900279876bad4a370589871eaa07a1d6ecd1ad`.
- Review starting commit: `0422f2bc062eb85228a4a5f5174b7a1f3090c424`.
- Delivery branch: `reviewer/goes-real-temporal-review-01`.
- Date: 2026-09-09.

Read the global operating rules, Scientific Reviewer role, handoff contracts, current disposition, GOES real-temporal preexecution specification, complete new package including decoded source/tests, and retained Stage A reset/rate and causal-input contracts. The starting commit differs from the implementation only in `docs/current_status.md`; the experiment under review is unchanged.

Evidence labels used here: **recorded** means committed execution/provenance; **checked** means inspection or calculation actually performed in this review; **assumed** means the accepted conditional model, not measured physical validity. No earlier Stage A production matrix, transport, raw archive audit, Monte Carlo or literature search was run. No historical experiment file was edited.

## 2. Disposition of the required scientific questions

| Item | Disposition |
|---|---|
| Nonempty M(I), attainable upper envelope, sup Q=Q(u) | Supported analytically, conditional on anchor bounds and pairwise consistency. No envelope-relaxation gap for Q; no claim that Q equals F_A. |
| Causal observations/actions, fallback suppression | Supported by inspection, 144 independent delivered-anchor comparisons and 72 hidden/masked-value mutation cases. |
| Preserved first action and whole-window exposure | Supported analytically and by independent timestamp-derived production-Q checks. Updated information preserves the original certified continuation whenever consistent. |
| Selection at retained representative points | All 14,667 representative signatures matched independent all-competitor selection, including planned and executed second actions. This alone does not validate whole intervals. |
| Complete g-map and exact boundary semantics | REVISE: six exact-confirmed point counterexamples in five case/latency combinations; some exported brackets lose their sign enclosure. See MAJOR-01. |
| g=1 endpoint counts | Independently confirmed: 13/25 positive savings at L=0, zero at L=300/900/1800, on complete-reference baseline-certified cases. |
| MAX_MEAN negative result | Supported independently over all replay-compatible g, using a relaxed all-pair lower-cost argument, not merely a scan of saved resource rows. |
| MAX_INCREASE d3/epsilon=0.01/L=300 | Replay threshold, representative 2100/1200/900 counts, and the stated upper saving-transition bracket independently confirmed. |
| Saving versus certifiability gain | Correctly separated when the baseline is uncertified; no baseline resource subtraction is supplied there. |
| EARLIEST_INVALID | Compatible-completion stress case, not verified actual replay. Ideal/retention summary NA handling is supported, but report denominators/wording require correction. |

## 3. Reproduction actually performed

The wrapper was inspected before execution. It deletes a fixed directory and compares gzip/base64 container bytes. It was **not run as supplied**. One regeneration of the current package was performed in a fresh isolated directory, with stages executed sequentially on the same output:

```sh
mktemp -d /workspace/scratch/24e1723b7ed9/goes-review-run.XXXXXX
# Returned /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y
# Working directory for the following commands:
# experiments/RE-GOES-REAL-TEMPORAL-01 in the exact review checkout
python real_temporal.py --config config.json --output-dir /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y
python resource_map.py --config config.json --dir /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y
python summarize_results.py --dir /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y
python test_real_temporal.py --config config.json --dir /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y
```

Outcome: 14,667 policy regions, 13,947 boundaries, 20,341 aligned resource regions, 576 applicability rows and 100 g=1 rows. The committed focused suite completed with its declared `ALL 8 FOCUSED TEST GROUPS PASS` message. That message is not treated as independent scientific validation.

Review environment: Python 3.12.14, Clang 22.1.3; NumPy 2.3.5; Pandas 2.2.3. The recorded development reference is Python 3.13.5 on Linux. No claim of an uninterrupted historical wrapper run is made.

The core enforces the frozen rate SHA-256 `9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`, fallback gzip SHA-256 `c7e860ac62106078a5039f7abf372829d9b6ebcbbac1065e300fae01065675de`, decoded fallback SHA-256 `c0c63b632ee6cf3aabcd4f6c2c9aca592d79ea69b54db678af8460c9d1e5004f`, cadence and row/mask counts; these checks passed with canonical checkout inputs. Integrity-checking source loaders also passed. This is not a new check of the private raw radiation archive.

All six regenerated scientific/intermediate file hashes matched the manifest:

| File | SHA-256 |
|---|---|
| policy_regions.csv | `0ff76754d78f785bb3fd1b7a6d3e0cfbaca9ff637a38982d12261620b0f3a37d` |
| decision_boundaries.csv | `f2306b6478a85800159211da586d8a5df36a70c62d4f78b4506dd65904f9b083` |
| resource_comparison.csv | `c7e449f7ceb3c51fff94e87f24041d9d3d4129becc6bd1bba4dae095bc1aea28` |
| envelope_segments.csv | `a0c2ab29d6aa5caeee6ae794f0b4d5919f467f3203c80f3fcfcb439178bdde36` |
| information_timeline.csv | `59bc2f27639b1e1bd40e6f7c87d4ee291b7f2768b61e5a2ceb0562527675f076` |
| input_context.csv | `49090128d92eef6fc156e77e17ebe1b10054b0eda0f2c0aa3f5ce1a71707655f` |

The four compact plain CSVs (`baseline_actions`, `selection_recomputed`, `model_compatibility`, `g1_endpoint_summary`) were byte-identical. The decoded applicability CSV was byte-identical to the decoded committed container. Container identity was not a scientific acceptance criterion. Reproduction succeeds at scientific-content level; it reproduces the numerical defect too.

Git history confirms pre-control selection commits `432c932d6c5f41cc27e6fcc0c783afb42746e604` and `773b95ea8b1c713e0f3b1fcc79487aa63b588159`, followed by the implementation delivery. The final implementation diff contains only the nineteen files of this experiment. Selection starts reproduce exactly; the six selected windows are distinct. No savings-dependent replacement was found.

## 4. Analytical assessment

### 4.1 Compatible family and envelope

For B>0 and c=gB, anchor bounds 0<=y_i<=B and pairwise inequalities |y_i-y_k|<=c|i-k| are necessary. They are sufficient because

`u_j = min(B, min_i(y_i+c|j-i|))`

is nonnegative, bounded by B, c-Lipschitz on the whole integer context/window lattice, and equals y_k at every anchor k. A minimum of functions with a common Lipschitz bound retains that bound. Pairwise consistency makes every competing cone at k at least y_k. Every compatible sequence lies below u. With no anchors, the constant sequence B is feasible and greatest. An anchor outside [0,B] makes the family empty; zero/one in-range anchor needs no positive g threshold. Invalid anchors must not be converted to zero risk.

For the accepted rho=0 model, each interval exposure is a nonnegative linear combination of the two bin rates and Q is 496 times the sum of squared per-bit exposures over words/reset intervals. Therefore Q is coordinatewise nondecreasing on the nonnegative domain. The **same entire** u is feasible and maximizes every exposure simultaneously, so sup over M(I) is attained at Q(u). This is exact maximization of a sufficient certificate. It does not remove Q's conservatism relative to first-passage F_A or establish physical B/g.

The replay audit uses all known reference bins, including fallback values; delayed delivery suppresses fallback values. Those are different legitimate uses. When a reference value is missing, pairwise consistency proves existence of a completion, not membership of the unknown actual realization.

### 4.2 Causality and recursive preservation

Delayed anchors satisfy `300*j+300+L<=decision`, validity, and absence of either-direction fallback. Their values alone constrain planning; future label/profile and undelivered quality do not enter action selection. The freshest possible bins at decisions 0/300 are (-1,0), (-2,-1), (-4,-3), (-7,-6) for the four latencies. Equality deliveries are included. At L=0 the replan learns completed first-bin exposure, not current second-bin intensity.

The t=300 anchor set retains the t=0 set. A consistent update gives M(I300) subset M(I0), so the worst Q for the original pair cannot increase. Retaining actual tau1 preserves the old reset schedule and accumulated exposure; the planned tau2 remains an admissible fallback within this mathematical rule. Contradiction terminates the guarantee label, not the exposure history. Masking removes information, not radiation exposure. Exogeneity of reports to realized upsets is required to reuse the conditional Poisson/reset certificate.

The implementation restricts replanning to the actual first action, evaluates whole-window Q, and does not insert a reset at t=300. Initial clean state is an externally imposed per-window condition, not evidence of a clean prehistory or a continuous-mission simulation.

### 4.3 Declared selection rule

For each initial information set, enumerating U squared with key `(total passes, -tau1, -tau2)` implements the specified rule. With tau1 fixed, maximizing feasible tau2 minimizes remaining passes. The Decimal selection functions do this directly. The fast production route uses relaxed floating comparisons; `exactify_fast_result` evaluates only the chosen pair and neither reselects nor rejects a chosen pair exceeding epsilon. Thus it cannot independently establish the optimizer or boundary-side certification.

All saved representative choices pass independent enumeration; this supports those points, not the whole exported intervals. No global optimality or universal pathwise ordering follows from this conservative open-loop-plus-one-replan rule.

## 5. Independent verification and shared dependencies

Review-only scripts were executed outside the repository:

```sh
python /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y/review_check.py
python /workspace/scratch/24e1723b7ed9/goes-review-run.RS1S6y/boundary_check.py
```

Their independent construction was as follows, so the check is not identified merely by an ephemeral filename:

1. Enumerate actual reset timestamps `k*tau1-a` and `300+k*tau2-a`, bounded by initial 0 and final 600. Integrate the two unit-rate basis functions over successive intervals, explicitly splitting exposure at 300 without splitting the squared exposure of a crossing interval.
2. Use integer time ticks of 1e-8 s at virtual word phases a=0,P/2,P. The three sums determine the quadratic dependence on phase. Sum it over the actual equally spaced Nw phases using exact rational quadrature weights: with m1=(Nw-1)/(2Nw), m2=(Nw-1)(2Nw-1)/(6Nw^2), the weights are (1-3m1+2m2, 4(m1-m2), 2m2-m1). Scale by 496*Nw/N_bits^2. This derives all 144 rate-quadratic coefficient triples without copying `q_raw` or `_q_float_coeffs`.
3. Independently express arrival/mask constraints, pairwise compatibility, and pointwise cone minima. Enumerate all 144 initial competitors and all compatible fixed-first-action continuations with Decimal arithmetic and the exact declared ordering.
4. Compare against all saved representatives. Separately isolate all action thresholds using the independent coefficients and long-double vector bisection, keeping distinct nodes without the production distance-based merging. Inspect interiors of the resulting intervals. Recompute every discovered mismatch with Decimal all-competitor selection before treating it as a demonstrated flaw.
5. Recompute the signs at the **serialized** endpoints of every reported certificate/selection bracket using the independently derived Q, not exported residual fields.

Results:

- 1,728 production-Q comparisons: 144 pairs, three shields, rising/falling/stationary and unequal positive basis-rate cases. Maximum absolute discrepancy 1e-60 at the working Decimal precision.
- All 14,667 saved representative signatures matched, including first action, planned second action, executed second action, total passes and noncertified status. For every independently selected certified representative, the old planned continuation remained certified under the update.
- 144 independent delayed-anchor comparisons and 72 mutations of masked/hidden values preserved the earlier delivered set/action.
- Independent threshold partition inspected 75,373 open cells, including 3,408 with width below 3e-10. Six point mismatches were confirmed with Decimal. This is a bounded falsification search, not a proof that exactly six errors exist.
- Of 12,857 reported certificate/selection brackets, 165 fail the advertised `f(lo)<=0<f(hi)` when Q is recomputed at the serialized endpoints. The stored residual signs do not prove the exported intervals valid.

Shared dependencies remain explicit: the reviewer uses the pinned input/configuration, accepted physical/reset semantics, and the production loader/section objects. It does not independently recalibrate rates or re-audit raw archive inputs. The independent Q route and selection enumeration do not call production Q/selection helpers to obtain expected values. The long-double root search is a detection path; Decimal confirms counterexamples, but a repaired exhaustive boundary guarantee still requires verified enclosures/order or explicit unresolved bands.

The committed small-word test compares two local test formulas without calling production Q. The hidden-future test exercises the Decimal helper rather than the actual fast map generation. Boundary/resource/recursive checks partly inspect production-generated columns. They are useful consistency/regression checks, not substitutes for the production-linked independent path above.

## 6. Demonstrated findings

### MAJOR-01 — The exported certified g-map is numerically unsound near merged boundaries

**Failure mechanism.** `critical_roots` excludes roots within 3e-12 of domain ends; `policy_regions` averages nodes separated by at most 2e-12 and labels intervals from representative signatures. Resource alignment discards intervals below 2e-12; subsequent merging uses tolerances up to 3e-10. A retained witness is refined afterward, but the exported policy interval is not rebuilt from that verified enclosure. Consequently the map can extend a cheaper action beyond its actual Q threshold. Refining a nearby retained witness does not recover a discarded transition or correct the map endpoint.

**Concrete replay-compatible counterexample:** LOWER_MEDIAN, d3, epsilon=0.1, L=0, g=`0.6936659869408`.

- The regenerated and manifest-matching policy map labels the open region `(0.6798058090460052, 0.6936659869413377)` with tau1=5, planned tau2=5, executed tau2=20: **75 passes**.
- Independently enumerating the declared rule gives tau1=5, planned tau2=5, executed tau2=10: **90 passes**.
- For the map's executed pair, independent whole-window `Q-epsilon = 6.5091592778526145e-13 > 0`. The map's CERTIFIED action is therefore not certified by the required inequality at this point.
- Direct fast selection at nearby independently checked witnesses chooses the correct more expensive action: the interval labelling defect persists even where the point selector itself is correct.

Additional confirmed witnesses, all LOWER_MEDIAN and L=0:

| Shield / epsilon | g | Map passes | Independent passes |
|---|---|---:|---:|
| d3 / 0.01 | 0.6936536239361873553 | 750 | 900 |
| d3 / 0.1 | 0.40048695890843278108 | 35 | 40 |
| d3 / 0.1 | 0.6936659869395377387 | 75 | 90 |
| d3 / 0.1 | 0.69366598694086486387 | 75 | 90 |
| d5 / 0.001 | 0.5532557245343374802 | 360 | 450 |
| d5 / 0.1 | 0.7142569798627903833 | 4 | 5 |

The affected independent open cells have widths about 6.64e-13 to 2.00e-12. Their small g measure is not concealed: no material change in the principal examples or broad count conclusions was demonstrated. Nevertheless, the advertised exhaustive certified map is false, and discrete actuation labels differ. Severity is based on those counterexamples, not the presence of tolerances alone. This does **not** demonstrate F_A>epsilon or physical failure.

**Related exported-enclosure defect.** `ds` rounds Decimal endpoints to 16 significant digits without directed outward rounding. Example: LOWER_MEDIAN/d1/epsilon=0.01/Delayed/L=0 exports `[0.01023173745449132, 0.01023173745449895]`. Independent residuals are approximately -1.4913312890e-14 and -1.7646166724e-18: both endpoints are on the feasible side. There are 165 such sign-enclosure failures among the 12,857 exported brackets. Internal pre-serialization residuals cannot certify different serialized coordinates.

**Smallest corrective action:** repair only boundary construction, selection certification and serialization in this package. Preserve distinct roots until equality/order is verified; do not average or discard close roots solely by distance. Derive policy/resource intervals from verified root enclosures and compatible-domain endpoints. Near unresolved clusters, refine adaptively or explicitly label an unresolved band rather than certify it. Recheck competing actions near boundaries and reject/reselect any action failing exact/verified Q<=epsilon or model nonemptiness. Serialize enclosures outward (or retain adequate exact digits) and recompute residual signs from the serialized values. State ownership of equality points, g=0, g=1 and model/replay thresholds under the actual <= rule; open-interval tables alone do not specify these actions.

**Closure criterion:** the witnesses above return the independently required actions or are explicitly excluded as unresolved, never falsely certified; serialized brackets enclose their roots; close-root clusters, equality points and all selected feasibility/status transitions survive policy-to-resource alignment; corrected independent all-competitor checks agree. Regenerate only this package's affected maps/summaries and record changed hashes and the effect, if any, on counts. No old Stage A matrix, radiation rerun, new g selection or broader scientific cycle is needed.

### MINOR-01 — Complete replay and missing-reference completion are mixed in a headline denominator

REPORT's “real section itself” wording followed by 23/30,18/30,15/30,15/30 conflates different evidence. Correct presentation:

| L, seconds | Complete-reference cells with some compatible saving | Missing-reference compatible-completion stress cells |
|---:|---:|---:|
| 0 | 18/25 | 5/5 |
| 300 | 13/25 | 5/5 |
| 900 | 10/25 | 5/5 |
| 1800 | 10/25 | 5/5 |

EARLIEST_INVALID does not prove actual missing-bin membership. Retention is blank in all 4,964 aligned missing-reference rows; compact Ideal point costs are blank. The full resource table contains 4,784 numerical `ideal_passes` stress values with `ideal_exact_replay_available=0`; identify them explicitly as compatible-set stress costs, not realized Ideal costs (or separate the column). The exact-reference denominator for g=1 is correctly 25, not 30. This is a local interpretation/table-labelling correction, not a reason to replace the window.

### MINOR-02 — Reproduction wrapper and reproducibility wording

Replace the fixed-name destructive temporary directory with a fresh isolated directory; compare decoded scientific CSVs rather than requiring cross-environment gzip/base64 identity. Preserve the historical interrupted-wrapper disclosure. This review's staged reproduction passed scientific hashes; it does not establish that the unmodified wrapper passed. No scientific recalculation beyond MAJOR-01's bounded repair is required for this correction.

### MINOR-03 — Verification independence is overstated

Relabel local-formula, production-helper and saved-residual checks according to their actual dependencies. Retain a production-linked timestamp/exposure oracle and an all-competitor boundary check in the repair tests. Reading saved residuals is not independent recomputation, even with Decimal fields. The review supplies a working falsification path; no new general validation campaign is requested.

**OPTIONAL:** include NumPy/Pandas versions in future run provenance. Python/platform alone do not completely identify this numerical/reporting environment.

## 7. Independently supported main results

At g=1, the t=0 delayed envelope is (B,B) because no current-bin observation exists. For L>=300 this is still true at t=300; there is no information-driven reduction of window exposure. Independent all-pair selection confirmed zero savings in all 25 complete-reference baseline-certified cells at each of those latencies. At L=0 the completed first bin can reduce the certificate at the replan; exactly 13/25 cells save. This is a timing/certificate/rule result, not a measured real-sensor requirement.

For MAX_MEAN, an independent stronger check removes the preceding-action restriction and allows all 144 pairs using t=300 information at the minimum replay-compatible g. Across all four latencies the resulting minimum counts are still the Precomputed counts (2100,210,900,90,10 for the five baseline cases). For larger g the envelope cannot decrease, so even this relaxed feasible set cannot offer fewer passes. The actual rule is a subset of that relaxed class. Thus no replay-compatible saving for MAX_MEAN follows without relying on potentially merged map intervals.

For MAX_INCREASE/d3/epsilon=0.01/L=300:

- Independent pairwise replay threshold: `0.3274298543911712439265436272...`.
- At g=0.35, initial Precomputed pair is (0.5,0.2); Delayed keeps tau1=0.5 and replans tau2 to 0.5, giving 1200 passes versus baseline 2100. Ideal uses (1,0.5), giving 900 passes.
- The independently recomputed selected continuation threshold lies between `0.4004020241222228` and `0.4004020241222305`. At the exported lower endpoint, Q-epsilon is approximately -7.4504267507e-17; at the upper endpoint it is +2.4363215402e-18. Independent all-competitor choices give 1200 and 2100 passes respectively. Unlike the 165 failing brackets elsewhere, this advertised bracket is valid after serialization.
- At exact threshold equality the (0.5,0.5) continuation is feasible under <=; do not equate a rounded decimal approximation to the exact root.
- Saving at g=0.35 is 900 passes, each with 2^21 reads and writes: 1,887,436,800 reads and the same number of writes avoided, 169.869312 occupied seconds, 28.311552 occupancy percentage points, retention 0.75.

When Precomputed is UN-CERTIFIED, full resource tables leave baseline differences blank. Information-enabled certification there is **certifiability gain**, not resource saving or proof of physical infeasibility without information. The benchmark ceiling is a shared assumed prior, not learned causally from this replay. The action-dependent resource accounting excludes acquisition, communication, estimation, controller computation, workload effects and energy.

## 8. Maximum admissible wording and acceptance boundary

**Admissible now, as checked bounded candidates:** In the accepted known-rho=0, data-only Stage A model with the declared finite action grid and sequential R2-U resets, a consistent bounded-Lipschitz external-information family has an attainable greatest rate sequence. Evaluating the monotone whole-window Q certificate at that sequence introduces no envelope-relaxation gap. Compatible causal updates preserve a previously certified continuation. Independent checks confirm the stated g=1 savings counts, the MAX_MEAN no-saving result in the baseline-certified cases, and the MAX_INCREASE representative calculation and stated transition bracket.

**Not admissible yet:** the entire exported g-map is complete, every labelled interval is certified, or all serialized brackets are verified enclosures. Those claims and promotion of the complete numerical map await MAJOR-01 closure. Correctly proven weaker results are not invalidated by failure of that stronger map claim.

Every accepted wording must retain: the imposed clean start for each separate 600-second window; unchanged words/data bits, rho=0, uniform singleton Poisson model, Q, U, reset timing and R2-U; piecewise-constant reference-rate reconstruction; decisions only at 0/300; bounded prehistory; exogenous exact-relative-to-reference eligible reports; equality delivery, fallback/invalid masking; counterfactual B_d and declared g; whole-context/window replay membership or separately labelled completion existence; the specific conservative planning/tie rule; no weighted case average or significance threshold.

GOES remains a chronological reference and hypothetical channel content. No GOES-fed architecture, target-spacecraft spatial equivalence, measured operational latency, physically validated B_d/g, exact F_A, full resource balance, global policy optimality or novelty is established. A violation of the variation contract terminates the conditional guarantee; it must not be repaired by tuning g after observing savings or substituting windows.

**Next action:** one bounded numerical-map repair with the closure tests above, plus the three local wording/packaging corrections. No additional PI data or physical-model expansion is needed to perform that repair. The complete-map promotion/next scientific decision based on its exact boundaries remains blocked; analytical and individually verified results may be considered separately by Orchestrator/PI with this limitation explicit. This review creates no HYP/RES and authorizes no next experiment, PR or merge.
