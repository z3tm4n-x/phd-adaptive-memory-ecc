# Scientific disposition — CY62167

**Task:** CY62167-SCIENTIFIC-DISPOSITION-01  
**Reviewer:** independent Scientific Reviewer  
**Reviewed commit:** `d237f347571879096b1ad3d7744a7ed8cb862fb7`  
**Reviewed branch:** `research/cy62167-paper-completion-01`  
**Delivery branch:** `reviewer/cy62167-scientific-disposition-01`  
**Date:** 2026-09-07  
**Related:** RQ-002/003/005/006/007; DEC-001/002/003  
**Recommendation:** **REVISE**  
**Status:** Scientific Reviewer recommendation; acceptance remains an Orchestrator/PI action. No result or other research ID is created.

## 1. Scope and judgement

This review examines the existing registered-cluster → recovered external-address → declared ECC organization → event partition → reliability → restoration-period → actuation-cost chain. It uses the exact branch commit, not main. It does not reopen RES-001, evaluate novelty, search literature, review manuscript language, or execute the next study.

The package supports useful bounded address-recovery, restricted-family, normalization, sufficient-certificate and resource results. Two stronger claims cannot yet be accepted: a physical direct-risk floor derived from the present toggle partition, and the asserted synthetic reference bracket without its auditable source derivation. Neither defect automatically invalidates the weaker upper-risk construction or prevents specifying a conditional Stage A comparison.

The minimum path forward is to declare the absorbing construction as a conservative surrogate, correct the decision vocabulary, and either provide the synthetic bracket proof or demote that bracket to a numerical regression benchmark. A physical device model, proprietary W and COSRAD operator closure are not universal prerequisites for that path.

## 2. Evidence and execution boundary

Read the global/reviewer instructions, HANDOFF_CONTRACTS, lifecycle, research specification/status, DEC-001/002, relevant RQs and RES-001. Primary evidence is `experiments/RE-CY62167-PAPER-COMPLETION-01/`: REPORT, A/B validation and manifests, COSRAD contract, partition/mapping/cross-section/bound/reference/resource/operator code and relevant tests. The historical Phase A REPORT was read at `10661887694c075fbb27786df72a7b85f5664a05`. Git comparison of the partition, mapping-family and reference-solver sources at that commit and the target showed no changes. Upstream reports and selected source/tests were traced through the seven tasks listed in the handoff, including GOES sigma closure.

No full GOES, RADAR, mapping, Monte Carlo or Phase A/B production run was launched for this review. Recorded test success and deterministic output comparisons are engineering evidence, not newly reproduced scientific validation here.

### Committed provenance

Paths below are relative to the primary package unless qualified. Hashes are recorded provenance identifiers, not a claim that unavailable archives were independently rehashed.

| Input | Recorded identifier / limitation |
|---|---|
| Raw `New Folder(3).zip` | SHA256 `16ab27789329adbbccdf9a7e5d0e15e855440d3f52b8dd93a384317a4635770a`; 28 text files, 5,016,468 bytes, source MD5 agreement recorded; raw archive unavailable in the reviewed Git tree |
| Frozen mapping coefficients | Recorded Git blob `35f2410c8d6744bd80339bd38c08e31b90bc69b6` |
| PI COSRAD `results.zip` | SHA256 `84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb`; 38 members; receipt 2026-09-04 |
| AN88889 *D PDF | SHA256 `c91f9c9c52ca587e224adbcf5cc7f0b124aaa7283f9ffe4bb39351132b9060f2` |
| CY62167G30/GE30 datasheet *F | SHA256 `a7d9faf23208b6c0f3b2be402feb8653ff0c6f649306fc246605189018a9ed1f` |
| Article `Текст v2(2).pdf` | SHA256 `b301b0e639dcfa4c408420223305a9b29708494a0bc781ae09a05300420fd3f9` |
| External `stage5_report.md` | SHA256 `a833fbf25e0159c65070540e7ec84b530d3919390a7ad6d81d4be138255151a1`; proof text not available in the reviewed package |
| External stages 1–5 summary | SHA256 `26e148735b6dfaf935fc80915349b16515157cce17bcac57c23697ba1eba6a7c`; a hash/reference is not the missing proof |

Recorded commands, with the archive placeholders retained rather than invented:

```sh
# Working directory: experiments/RE-CY62167-PAPER-COMPLETION-01
CY62167_RAW_ARCHIVE=<controlled.zip> python run_phase_a.py
CY62167_RAW_ARCHIVE=<controlled.zip> python -m unittest discover -v -p 'test_*.py'
python run_phase_b.py --cosrad-results /path/to/results.zip
```

The A report records 33 passing tests (7.671 s); B records 30 (0.674 s) and compileall success. The exact B test-selection/compileall invocation and complete Python, OS, NumPy, SciPy, pandas and COSRAD build versions were not located in the committed provenance. B tests refer to `CY62167_COSRAD_RESULTS`. The historical A discovery command must not be presented as the exact final B suite command. No environment from another experiment is substituted.

### Independence of checks

* Held-out address values can falsify the affine predictor; they are independently recorded labels, although parsing and prediction share the implementation. Full-rank training and zero ordinary held-out residuals support the declared class, not a universal topology theorem.
* Population conservation, deduplication and ambiguity audits constrain preprocessing. Tests that read the fixed 45/9/1 CSV or repeat production mapping functions are consistency checks, not a second raw-data reconstruction. The Gaussian-binomial recurrence provides a separate arithmetic check of the family-size calculation.
* Reference tests matching frozen roots and constants verify implementation regression. They do not establish the dangerous-pair probability inequalities from a mark/state model. Residual toggle tests validate some transition examples; they do not prove that every direct mark is fatal in every safe state.
* Upstream direct Monte Carlo kills a sampled direct event immediately. Agreement with an absorbing analytic model therefore cannot falsify the direct-cancellation threat. Matrix-exponential checks share the specified residual generator; they support numerical implementation, not physical calibration.
* The COSRAD candidate-kernel comparison can falsify that operator hypothesis and did. Unit/Jacobian agreement tests a narrower transformation. Reproducing article numbers or deterministic CSVs cannot validate a rejected operator or confer statistical coverage.

### One bounded local falsification check

Purpose: test whether a two-bit toggle mark necessarily causes E_cap from every safe SEC pre-state. Scope: one 32-bit word, all clean/singleton pre-states and all distinct two-bit marks; standard library only, no production imports or stochastic run. Command executed from the repository:

```sh
python - <<'PY'
from itertools import combinations
states=[set()]+[{i} for i in range(32)]
marks=[set(p) for p in combinations(range(32),2)]
miss=sum(len(s^m)<=1 for s in states for m in marks)
print('Purpose: test state-independent E_cap implication of a two-bit toggle mark')
print('safe_pre_states=',len(states),'two_bit_marks=',len(marks),'cases=',len(states)*len(marks),'non_exceeding_post_states=',miss)
s=set(); s^={0}; print('clean -> singleton:',sorted(s)); s^={0,1}; print('after direct-class toggle:',sorted(s),'E_cap ever:',False)
PY
```

Outcome: 33 pre-states × 496 marks = 16,368 cases; 992 non-exceeding post-states. The clean-start sequence `{}` → `{0}` → `{1}` supplies the counterexample. The printed first-passage label describes this explicit two-event sequence, not a general trajectory checker.

## 3. Disposition by output

| Item / disposition | Supported result and required assumptions | Maximum admissible wording | Forbidden generalization / unresolved limitation |
|---|---|---|---|
| External-address recovery — conditionally support | Rank-25 affine fit from C720, 5,122 training rows; zero mismatches in 143,590 ordinary held-out deduplicated rows, including 142,663 novel triples. Five ambiguous-address rows excluded by declared signatures. | “Within the declared affine class, the frozen map reproduces the observed ordinary external-address field, with zero ordinary held-out mismatches.” | Not proprietary ECC W or physical topology. First-field semantics remain inferred; two-field records do not independently validate A; unseen addresses remain model extrapolation. |
| Restricted W and 45/9/1 — support within family | Remove two of 21 address bits: 210 candidate four-address groups; supplied-coordinate spacing filter retains 55. Deduplicated registered clusters, 32 data bits/word, SEC threshold. | “Among these 55 candidate organizations, 45 have zero, nine have four and one has five direct-class registered clusters.” | Not all W, observed hardware organization, complete parent events or zero physical direct rate. Parity is outside the data-only count. |
| Direct/residual construction — accept only surrogate scope | Fixed partition, matched residual transitions/reset/initial state; exogenous independently marked Poisson processes for product formula. | “The absorbing-direct surrogate upper-bounds the corresponding toggle first-passage risk under the stated coupling; its product survival is exact for the declared surrogate.” | The partition alone does not prove E_D ⊆ E_cap or a physical floor. See MAJOR-01. |
| GOES decision boundaries — conditional sensitivity | Recorded GOES interval, E/W/isotropy convention, transport/cross-section continuation, parent reconstruction, declared W/SEC, clean reporting windows, direct surrogate and residual phase model. | “Within this scenario/model/action grid, theta changes the model decision or sufficient certificate as labelled.” | Theta is not measured physical direct probability; no global marginal-insufficiency or physical uncontrollability claim. Sixteen-phase approximation and low-energy extrapolation remain material scope constraints. |
| Article sufficient period — conditional support | Article effective normalization, explicit rate/mark law, uniform residual per-bit rates, clean start/reset gaps, data-only SEC and experimental T/epsilon. | “For the declared externally convolved model, tau_max^U is the largest period certified by this sufficient bound.” | Not the true maximal admissible period, a measured 95% device guarantee, or a project requirement. Budget exhaustion is not proof of physical infeasibility. |
| Synthetic reference bracket — arithmetic benchmark only pending proof | Frozen 39-bit synthetic constants and implemented formulas reproduce the asserted interval; external derivation is not available for independent audit. | “The frozen formulas yield approximately [315.224841, 315.744501] s; their status as bounds on the specified first-passage process remains unverified in this review.” | Not an accepted reference optimum or proven tightness/overhead ratio. Not the article's 32-bit device model. See MAJOR-02. |
| GEO reference blocker — support withholding | Exported-spectrum operator candidate fails internal SEE closure; GEO reference and comparison fields remain unreleased. | “No COSRAD-consistent GEO reference period or reference resource penalty is established by this package.” | Non-closure does not invalidate a separately labelled external-convolution calculation or prohibit a future explicitly external-only reference model. |
| Resources/architecture — conditional support, E labels need repair | R1 known grouping vs R2 full address scan; U unconditional vs E ERR-assisted writes; 45 ns serial read/write, no added overhead, declared restoration effect. | “These are conditional actuation transaction counts and pass-time/interface-cost calculations; E read-only values exclude model-dependent writes.” | Not cost of acquiring W/information, controller overhead, net adaptation benefit or demonstrated device timing. Hypothetical W recovery does not establish actual R1 access knowledge. |

The raw population is 299,154 cell rows / 173,835 registered clusters; ordinary population is 299,121 / 173,802, and event-local deduplication gives 299,026 / 173,802. The article's 299,206 cell total is not interchangeable with these populations. Service/ambiguous rows and duplicates must remain explicit. A registered cluster is the observation unit, not a demonstrated complete physical parent event.

For external addresses, matrix rank 21 and kernel on the three declared coordinate bits give eight preimages within the affine model. This supports the empirical external ×8 interpretation, not observation of proprietary ECC/parity. The 55-family selection uses distances in supplied coordinates; agreement of L1/L2/L-infinity selections does not establish physical spacing. The much larger 733,006,703,275 linear two-dimensional subspaces count is itself still a restricted mathematical family, not all conceivable organizations. The baseline W_00_01 is floor(A/4); the extra cluster in W_00_11 is the recorded 164 MeV proton cluster 5480, segment 1, K=29.

## 4. Transition semantics and the risk certificate

`event_partition.py` labels a registered cluster direct when at least two distinct data cells map to one word. `reference_solver.py::combined_reference_risk` instead declares an independent absorbing direct process. Its residual simulator toggles stable bit identities, starts clean, resets by word phase, and stops at first capability exceedance. These are different semantics unless further assumptions connect them.

For safe SEC state S and mark M, the toggle state has size |S Δ M| = |S| + |M| − 2|S ∩ M|. A two-bit mark containing the current singleton leaves one error. A mark with at least three distinct bits in one word does force exceedance from every safe state of that word. Fresh disjoint errors or monotone set_error would also make a two-bit direct mark fatal, but cannot silently replace the declared toggles. Consequently the present E_D is not generally a subset of physical E_cap.

There is nevertheless a simple valid weaker result. Couple a full toggle process and a surrogate using identical exogenous events, initial states and restoration actions. The surrogate follows residual events identically and is killed at the first direct-class event. Before that event the trajectories coincide. Any earlier true failure is shared; any later true failure occurs after the surrogate has already failed. Thus F_true ≤ F_surrogate. No assumption that the direct mark itself necessarily fails is needed for this upper bound. This proof concerns the declared population/model, not unobserved physical events.

For independent Poisson thinning with fixed state-independent marks and deterministic exogenous rates,

`F_surrogate = 1 − exp(−Λ_D) S_residual`.

The product follows from independence of the thinned streams. A shared random environment requires conditional multiplication followed by averaging; multiplying marginal survivals is generally wrong. State-dependent partitioning or adaptive actions require a corresponding conditional/coupling argument. The existing fixed-action result must not automatically be reused as a causal-control formula.

For the article certificate, put N=2^24 data bits, n=32, beta=(n−1)/(2N). Assume simple independently marked Poisson residual events, at most one distinct bit per word per residual event, homogeneous per-bit rate r=nu_C/N, independent increments, clean initial state, and complete restoration of each surviving word with inter-reset gaps at most tau. Correlation across different words within an event is allowed. Any residual exceedance requires two distinct bits in one word hit in one reset interval. For such a pair the expected cross-event hit-pair count is r²L². Summing over pairs and reset intervals, using sum L² ≤ tau T, and applying the union bound yields

`F_true ≤ F_surrogate ≤ min(1, Q_U)`,

`Q_U = T nu_D + beta tau T nu_C²`.

Toggles can remove errors but do not invalidate this sufficient pair-count bound. Nonuniform marginals require the coefficient `sum_w sum_(i<j in w) r_i r_j`; total nu_C alone does not justify the uniform beta. Time-varying rates require interval-integrated pair exposure, not substitution of a window-average rate without proof. These are assumptions of the conditional calculation, not experimentally verified uniformity of this device.

The decision distinctions are essential:

| Evidence | Permitted conclusion |
|---|---|
| Exact probability for a declared model exceeds epsilon | That model/action is infeasible |
| Proven physical E_D subset and a justified hazard lower bound give 1−exp(−Λ_D)>epsilon | A physical direct floor rules out restoration-only control within that model |
| Q_U>epsilon, or T nu_D≥epsilon | This sufficient certificate fails; feasibility remains unresolved by it |
| No passing action in the declared realizable set | No admissible action in that set under the chosen rule; not impossibility over all periods |

Even in the absorbing model the exact floor threshold is Λ_D>−log(1−epsilon), not Λ_D≥epsilon. An upper estimate of direct intensity cannot establish a physical lower floor. Zero observed direct clusters cannot establish zero physical intensity. The output `DIRECT-BOUND-EXHAUSTED` is acceptable only with its certificate meaning; legacy `NO_POSITIVE_PERIOD` must not be inherited as a physical conclusion.

## 5. Normalization, COSRAD and reference status

ARTICLE-NORMALIZED EFFECTIVE FLUENCE uses `F_art = S/(N sigma_bit)` with the article heavy-ion Weibull (`2.6e−7`, threshold .15, width 70, shape 1.2). Thus the reconstructed total cross section equals N sigma_bit algebraically. This is a useful declared normalization, not independently measured fluence or a validation of the Weibull law. Direct and residual counts must come from the same stated population. The POINT interpolation/tail assumptions and the structured residual-fraction interpolation are model choices.

ARTICLE-CONFIDENCE-STYLE includes the prescribed count uplift and assumed 10% normalization adjustment; for three direct counts at LET 57 the multiplier is `2.4*(3+.67)/(3*(1−.10))`. The resulting step cross section above LET 33 is conditional. No independent provenance here establishes measured, normative or simultaneous 95% coverage of that construction, its spectra, mapping or decisions.

The article proton comparator uses `8e−14/bit` at E≥10 MeV and its declared .5 geometry factor. It is separate from the GOES low-energy response/transport model and its E/W, 4π and extrapolation conventions. Neither normalization may be imported into the other without an explicit conversion. The article's zero proton direct component is an assumption, not proof of zero physical direct probability.

The candidate COSRAD spectral kernel `exp(−10 L0/L) H(L−L0)` does not reconstruct internal SEE responses: recorded maximum relative discrepancies are approximately .99157248 for GCR and 1 for SEP. The LET coordinate/Jacobian transformation agrees to about 5.625e−15; that validates the transformation only. Internal unit SEE responses, external spectral convolution and fitted basis/NNLS diagnostics must remain separate. A good fit to a limited basis, or clipping signed coefficients, does not resolve arbitrary sharp direct-response operators.

The GCR article-background scenario is the supplied mean-solar, circular 36,000 km, inclination-zero scenario with the stated ten-year horizon. The SEP peak with probability .1 has no supplied duration; it must not become a ten-year SEP exposure. The .15 threshold versus printed .2 is a recorded rounding interpretation, not an independently recovered internal setting.

External-convolution article numbers therefore remain conditionally usable: baseline W_00_01, ARTICLE-CONFIDENCE-STYLE gives tau_max^U ≈20.4586265 s at 2.5 g/cm² and 45.6849282 s at 3.0 g/cm². The 2.0 case exhausts the sufficient budget. The f_D=1 shielding bracket [2.0,2.25] and interpolation ≈2.0842900 concern that budget, not measured physical controllability. S_D=−f_D/(1−f_D) differentiates with nu_C held fixed; it is not automatically the sensitivity to theta when repartition changes both rates.

The synthetic benchmark is separate: n=39, 131,072 words, T=315,576,000 s (article T=315,600,000 s), bank/multiplicity/pair/phase constants frozen from an external Stage 5 report. Code computes a first-moment upper expression and a purported Bonferroni lower expression, then bisects roots. Matching [315.224841226,315.744500579] s and sufficient value 243.55401798 s does not independently validate those bounds. The missing proof must connect dangerous pairs, their intersections, phase treatment and first passage. Under toggles, existence of a dangerous pair need not itself imply first passage: same-bit hits can cancel before a later distinct-bit hit. This observation identifies a proof obligation; it does not by itself disprove the unavailable Stage 5 model, which may impose stronger conditions.

Withholding GEO tau_ref, eta and reference-relative resource penalties is appropriate. Operator closure is necessary for the promised COSRAD-consistent reference interpretation, not merely for reproducing labelled external-convolution integrals. A separately specified external-only reference is a possible later scope choice, not a result of this review.

## 6. GOES scope and restoration resources

GOES conclusions are conditional on the January–February 2026 sample (16,992 timestamps, 16,971 paired valid, 21 excluded), the E/W isotropy-equivalent convention, response continuation and transport settings. The low-energy continuation, registered-multiplicity parent reconstruction and assumed low-energy direct fraction are not measured parent-event cross sections. Sigma closure with a digitized simulated FLUKA comparator does not turn it into measured calibration; unchanged rankings do not eliminate the recorded magnitude sensitivity. The transport convergence check addresses its numerical discretization, not these modelling assumptions.

The bridge uses independent cell-toggle residual semantics with a direct absorbing branch, 16 phase representatives and clean starts per reporting window. Its product/union/lower formulas inherit Section 4's scope. Recorded phase convergence below .5% is not a rigorous error envelope for every finite-word decision. Theta roots are scenario sensitivity boundaries within the tested action domain; loss of a union-bound certificate is not exact infeasibility. The upstream minimum grid action 1 s is not the R1/R2 architectural floor. Neither the theta tables nor experimental epsilon establish a numerical project reliability requirement.

For 45 ns serial reads/writes, the declared unconditional contracts give:

| Contract | Reads / pass | Writes / pass | Conditional pass time |
|---|---:|---:|---:|
| R1-U, one representative per known word | 524,288 | 524,288 | .04718592 s |
| R2-U, full external-address scan | 2,097,152 | 2,097,152 | .18874368 s |
| R1-E, read component only | 524,288 | Model-dependent | ≥.02359296 s |
| R2-E, read component only | 2,097,152 | Model-dependent | ≥.09437184 s |

These require the declared full-word restoration effect, correct surviving-state writeback, serial timing and no additional arbitration/controller overhead. The source timing audit supports conditional use of 45 ns, not measured sustained system performance. A sequential sweep can support the sufficient bound through maximum per-word reset gaps; it must not be described as simultaneous physical reset.

R2-U interface usage at 20 s and 45 s is .9437184% and .4194304%. The fourfold R2/R1 transaction ratio is an actuation consequence of the declared grouping-access contracts. It measures neither the cost of learning W nor adaptation benefit. For E, `phase_b_core.resource_rows` omits writes when unknown, and the export drops `write_cost_status`. Its numeric interface fraction is then a read-only lower bound, and its read-floor feasibility test alone is insufficient. At the reported large positive periods, an explicit at-most-one-write-per-read bound can establish feasibility using the U pass time, but cannot make the E cost exact.

## 7. Findings and minimum closure actions

**CRITICAL: none identified within this bounded scope.**

### MAJOR-01 — physical floor and exact-risk interpretation exceed transition semantics

**Evidence/impact:** the direct classifier is state independent, while residual/physical errors toggle. The counterexample and coupling proof in Section 4 show that the absorbing construction supports an upper risk surrogate, not automatically a physical E_D subset. Physical no-period claims or lower-bound transfers through that direct branch are not justified. This affects the interpretation of upstream floor/decision-boundary results, not the restricted observed counts.

**Smallest corrective action:** explicitly adopt the absorbing surrogate for the bounded chain; attach the coupling and sufficient-bound assumptions; relabel inherited floor/exhaustion/infeasibility statements as surrogate-model, certificate or declared-action-set conclusions as appropriate. Add the clean→singleton→two-bit-toggle cancellation fixture and assert the intended surrogate/physical distinction. If a physical floor is retained instead, prove statewise fatality for the selected marks and supply a justified intensity lower bound; merely rerunning the existing absorbing Monte Carlo cannot close this issue.

**Closure criterion:** every retained downstream decision names its model, probability/bound direction and action set; no physical floor relies solely on the ≥2 mark classifier; the cancellation example cannot be misreported as an inevitable true failure. The conditional article upper certificate can remain numerically unchanged. This is a correction request, not authorization to silently alter accepted artifacts.

### MAJOR-02 — synthetic reference bracket lacks auditable probability proof

**Evidence/impact:** `reference_solver.py` imports numerical constants from an externally referenced Stage 5 report; tests reproduce the formulas/roots. The reviewed package does not supply an independently auditable derivation of pair probability, shared-event correction, phase factor and the link to first-passage risk. Proven tightness and reference-relative overhead cannot be accepted on this evidence alone.

**Smallest corrective action:** either provide the exact hashed Stage 5 report/model and trace each constant and probability inequality to it, or explicitly demote/omit the claimed probabilistic bracket and derived optimality/tightness comparisons, retaining only a frozen arithmetic benchmark. If providing the proof, audit state transitions, dangerous-pair inclusion, intersection counting, finite-horizon/reset phases and monotonicity on the root-search domain. A full Monte Carlo run is not requested.

**Closure criterion:** a reviewer can independently verify lower≤true model risk≤upper and the consequent period bracket, or no retained scientific conclusion depends on that unverified bracket. This need not block Stage A if that benchmark is unused.

### MINOR-01 — incomplete execution provenance

Record the actual A/B environment versions, exact B test-selection and compileall commands, and COSRAD build/settings provenance when available; otherwise preserve explicit unknowns. Do not reconstruct them by guessing. Existing hashes and reports remain useful but do not constitute a complete executable environment record.

### MINOR-02 — ERR-assisted resource export loses its qualification

Retain the write-cost-status field or label E interface values as read-only lower bounds and E pass times as read floors. Separate necessary read feasibility from a verified complete-pass bound. For existing periods, the stated U worst-case write bound can close feasibility without a new production run; expected E cost still requires a write/ERR model.

### MINOR-03 — phase/grid precision and sensitivity labels

Keep GOES decisions conditional on the implemented phase approximation and tested grid; distinguish model probabilities from certificates. A Stage A specification may define the finite-phase model exactly, or require an error margin before claiming full-word robust decisions near a threshold. Do not promote a measured-support energy label to measured calibration throughout interpolated/extrapolated tails.

**OPTIONAL:** make the evidence table explicitly distinguish held-out labels, independent mathematics, shared-code tests and fixed-output regressions. This improves future acceptance audits without expanding the experiment.

## 8. Next-stage readiness and promotion limits

**Can be accepted now, within the stated domain:** observed external-address recovery; the restricted-family 45/9/1 registered-cluster count; article effective-normalization arithmetic and labelled external convolution; the conditional sufficient-risk formula established in Section 4; unconditional actuation accounting; and the decision to withhold a COSRAD-consistent GEO reference. These are recommendations for bounded acceptance, not creation of RES.

**Needs wording correction only:** zero observed versus zero physical events; effective versus measured fluence; confidence-style versus guaranteed coverage; certificate exhaustion versus impossibility; theta sensitivity versus measured direct probability; R1/R2 actuation ratio versus information/adaptation benefit; read-only E cost; operator non-closure versus invalidation of every external integral. Some corrections form part of MAJOR-01 closure.

**Needs new verification:** the synthetic probabilistic bracket if retained; a physical floor if retained; an actual ERR-write cost if exact E costs are requested; COSRAD operator semantics only if a COSRAD-consistent reference claim is requested. Those stronger claims are not mandatory for a bounded Stage A formulation.

**What blocks an unqualified Stage A specification:** carrying physical-floor/exact-feasibility claims from the present direct model into it. Resolve MAJOR-01 by the surrogate choice and explicit certificate semantics. The specification must also declare, rather than leave implicit, the scenario set and weights/robust criterion, available period/scan actions, reporting horizon and initial/carry-over state, risk budget as a study parameter, and the reset timing under action changes. These are choices needed to define the comparison, not a request for additional radiation data.

The three comparators need one common state/risk/resource contract: (1) a single period feasible across the declared scenarios; (2) a precomputed schedule using only the declared prior information; (3) a causal comparator with specified instantaneous information, no future trajectory access, and a declared decision cadence. “Full information” must say whether it exposes current rate/environment, error state or both, and with what delay. Schedules cannot grant the causal controller future scenario knowledge or grant any arm a clean reset at every decision boundary. An integrated risk budget and interval exposures are needed for changing rates/actions; pointwise stationary tau tables alone are not that proof.

**What does not block that formulation:** absent proprietary W if a hypothetical family is declared; absent complete physical topology; unresolved real-parent observability if the registered-event model is explicit; missing COSRAD closure when the external route is chosen; the unused synthetic bracket; no measured numerical project epsilon; and no information/controller cost when the comparison is expressly limited to actuation cost. If net adaptation benefit including those costs is requested, their contracts become required inputs, not optional deductions from the present table.

**Bounded candidates for later promotion:** the empirical affine recovery result and 55-family registered-cluster distribution; the absorbing-surrogate coupling theorem plus conditional sufficient-period calculation; and architecture-dependent actuation-count/pass-time results. Maximum wording is given in Section 3 and the full assumptions in Sections 4–6. None establishes real SRAM topology, complete data-and-parity device reliability, universal marginal-model insufficiency or adaptation benefit.

**Disposition:** REVISE the stronger semantics/proof claims; permit preparation of a narrowly conditional Stage A specification after explicitly adopting the upper-certificate interpretation. Do not execute that study or promote a result on the authority of this report alone.
