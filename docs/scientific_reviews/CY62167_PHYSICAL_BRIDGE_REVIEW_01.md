# CY62167 physical bridge — Scientific Review 01

**Task:** CY62167-PHYSICAL-BRIDGE-SR-01. **Reviewer:** independent Scientific Reviewer. **Date:** 2026-09-11.

**Exact reviewed/base commit:** `0c979c34d537c9f328858010a8df6cdeab598735`.

**Review assignment:** `8cd4f0a43a6cc6d845b5556e570b1c818fa48034`, `docs/research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-01.md`.

**Delivery branch:** `reviewer/cy62167-physical-bridge-review-01`, based on the exact RE delivery, not on main or the assignment commit.

**Recommendation: REVISE.** No CRITICAL finding; two MAJOR findings and three MINOR corrections. The structural theorem and conditional probability-transfer lemma are sound. The delivered model pair does not yet prove decision non-identifiability over the whole declared CY62167 information family, and the frozen numerical registered upper has not been transferred to the new conditional-write execution contract. These are bounded proof/qualification gaps, not evidence that the device is physically infeasible or that a useful bridge is impossible.

**Limited acceptance is scientifically eligible:** the structural D3 result, the explicitly conditional coverage lemma, the traceable threshold arithmetic, and the conclusion that this delivery establishes neither full-device admissibility nor a positive physical D3 frequency lower bound. **Completion of the physical bridge under the original handoff is not established.** Canonical acceptance, Issue #15 and subsequent work remain Orchestrator/PI decisions; this report creates no RES/HYP and does not change path A.

## 1. Scope and evidence

Read the exact-target global operating rules, Scientific Reviewer role and handoff contracts; DEC-001/004; the RE assignment; the complete ten-file `experiments/RE-CY62167-PHYSICAL-BRIDGE-01/` package; both prior CY62167 Scientific Reviews and the controlling semantics-repair interpretation map/report. Traced the relevant ECC, mapping, observation and resource interfaces through RQ-003/005/006/007, the proton report/source manifest, address report/data contract, observability report/contract, restricted mapping-family contract/summary, and the historical ECC-risk report/model/source. Historical PASS-B/floor/exact headings do not override the accepted semantic qualifications.

This review does not repeat Stage A, GOES/RADAR/COSRAD, Phase A/B/C, raw parsing, mapping fitting/search, Monte Carlo, control optimization or a literature review. The exact named manufacturer-source lookup described in §7 is not a new literature cycle. No historical experiment, manifest, decision, result or review was edited.

Evidence labels used below: **SOURCE** is inspected committed provenance or identified prior source support; **ASSUMPTION** is a declared model condition; **OWN CHECK/INFERENCE** is this review's reasoning/check; **UNKNOWN** is not supplied or not established. Byte agreement demonstrates reproducibility, not scientific validity.

## 2. Disposition of the proposed results

| Item | Disposition / maximum admissible result | Conditions and unresolved boundary |
|---|---|---|
| Atomic D3 and `2t+1` criterion | **SUPPORTED structural theorem:** an atomic odd-toggle mark hitting at least `2t+1` distinct cells of one fixed actual codeword forces capability exceedance from any pre-state with at most `t` errors. | Fixed code/W and protected domain; no intervention inside the atomic mark; errors counted over data **and** parity; first passage retained. Not a frequency, decoder-outcome or system-failure theorem. |
| `F_A^pi(m;H) >= q3_m(H)` | **SUPPORTED per-model, all-policy inequality**, with the law separated from policy. | Exogenous physical event law, or explicitly policy-indexed event probability; correct horizon/initial semantics. A common exclusion needs a justified common lower bound. |
| Current `q3_lower=0`, full-device `[0,1]` | **SUPPORTED only as available trivial bounds / no qualified nontrivial bound established by this delivery.** | Not a proved sharp identified interval, `inf F_A=0`, or proof that no better bound could be derived from I. |
| Hidden parity projection | **SUPPORTED abstract erasure property.** An observation operator depending only on the data history cannot distinguish insertion of an otherwise unobserved parity-only component that leaves that history unchanged. | A toy data projection does not establish equality in law of every actual observable, membership in `M_full(I)`, or a passing physical m0. MAJOR-01. |
| CY62167 m0/m1 decision non-identifiability | **NOT ESTABLISHED as delivered.** Credible conditional construction, not a disproved construction. | Complete common observation law, admissible W/parity/time law, compatibility with included geometry/rate information and a qualified m0 action are missing. |
| Registered `U_reg` and delta threshold | **Reproduced arithmetic; conditional 16-phase/ideal-reset model estimate, not a qualified new physical-execution upper.** | The analytical union bound is valid for exact marginals; phase/numerical error and execution transfer are separate. MAJOR-02. |
| Coverage transfer | **SUPPORTED conditional lemma:** explicit event inclusion plus matching marginal upper bounds implies `F_full <= min(1,U_reg+delta_cov)`. | No independence required; same model, policy, horizon, initial and execution semantics. No measured/derived CY62167 delta supplied. |
| 55-family / 45–9–1 | **SUPPORTED reuse of the frozen restricted-family registered-class summary.** | Not new raw validation, actual W, all W, complete parents, D3 frequency or zero physical direct risk. |
| Exact W versus sufficient information | **SUPPORTED conditional sufficiency statements**, not minimality: qualified complete-codeword risk summaries can sometimes replace disclosure of W; W alone does not determine the event/observation/time law. | No proof that the proposed pair of summaries is minimal, observable from the present files, or sufficient without an execution/initial contract. |
| Full-device control class / Issue #15 | **NOT_ESTABLISHED**; no controller class selected or excluded from present physical data. | A conditional exclusion if a qualified D3 lower bound exceeds epsilon remains valid. Neither a failed upper certificate nor an unresolved coverage term is a physical impossibility proof. |

## 3. Structural theorem, first passage and quantifiers

For a fixed word, let E be its erroneous physical cells and M its atomic mark of cells toggled an odd number of times. Componentwise flipping gives

\[
|E\triangle M|=|E|+|M|-2|E\cap M|\ge |M|-|E|.
\]

For `|E|<=t`, `|M|>=2t+1`, the post-state has at least `t+1` errors. This is a statement about **distinct cells after parity of toggles**, not a raw count of hits. For SEC, any mark of at least three cells in the same actual 38-cell word suffices. It does not require clean t0 if the initial state is safe; if the horizon already includes an unsafe initial state, the horizon failure event is already true.

Let D be the first such mark in the horizon. If capability was exceeded before D, the horizon event already holds. Otherwise every protected word is still safe just before D, and the inequality forces exceedance at D. Later repair does not erase that occurrence. This proves the horizon inclusion, not just an endpoint statement. Boundary ordering must forbid an interleaved repair within the atomic mark, including a pending write completing partway through it. Memory replacement, disabling the protected domain or changing W/code is not a restoration-timing policy covered by this theorem.

The two-toggle counterexample is valid: from `{0}`, mark `{0,1}` leaves `{1}`. The clean-start sequence `{}` → `{0}` → `{1}` never exceeds SEC. Thus `t+1` toggles are not universally fatal. Conversely two toggles from a clean word can fail: D3 is sufficient, not necessary. D3 need not occur for accumulated, mixed data/parity or initial-state failure.

Use a model m for the physical law/architecture, and a separate policy pi for admissible causal service. Under an action-independent parent/mark law,

\[
\forall m\in\mathcal M(I),\ \forall\pi\in\Pi_{\rm atomic}:\quad
F_A(m,\pi;H)\ge q_{3,m}(H).
\]

CONTRACT §5 includes “a policy” in a complete model, while §7 optimizes over policy again. Remove this double parameterization, or formally define a common admissible set of pairs `(m,pi)`. If service changes the parent/mark law, write `q3_(m,pi)` and prove any policy-independent lower bound separately. A non-Poisson event probability is permitted; `1-exp(-Lambda3)` needs its own no-event law.

The distinctions relevant to a decision are:

- `inf_m q3_m > epsilon` excludes every allowed policy in every compatible model.
- One compatible m with `q3_m > epsilon` excludes a **single-policy robust guarantee** over that family, but does not make every model infeasible.
- A passing policy for one m and an excluding bound for another m would establish a decision contrast if both models have the same declared observations.
- `forall m exists pi` is not `exists pi forall m`; neither `inf_m inf_pi F` nor `sup_m sup_pi F` is the robust optimal risk `inf_pi sup_m F`.

No positive common D3 lower bound is obtained here. Zero is always a legitimate lower bound; its optimality over `M_full(I)` is not proved by absent entries in a table. In particular, zero D3 probability does not imply zero accumulated first-passage risk. The package's `[0,1]` must remain an uninformative enclosure, not a sharp attainable set.

## 4. The proposed model pair: valid idea, incomplete physical compatibility proof

The delivered `independent_check.py` projects two visible singleton marks and an additional hidden parity triple onto six data bits. It proves that erasing parity and dropping zero-projection records gives the same list. It supplies no times, complete stochastic law, real registration operator, reset schedule or probability of failure for m0. Indeed two distinct visible hits in its toy word would already fail without an intervening reset; that fixture was not a demonstration of a positive m0 decision.

There is a precise **conditional** extension lemma behind the idea. Suppose a complete admissible base process X exists; all included observations are a measurable function O(X) of its data history and fixed exogenous metadata; adjoining a hidden parity process Z neither changes X nor O nor violates another model restriction. On the product probability space, give Z one triple-parity atomic mark with probability p and a specified time in `(t0,t0+H)` (otherwise none). Then O has the same law in both extensions, and the hidden mark gives `F_A(m1,pi)>=p` for every allowed policy. No Poisson assumption or measured interpretation of p is required. With a separately valid m0 certificate below epsilon and p above epsilon, this proves the desired contrast **for that explicitly extension-closed observation family**.

The delivery has not established the antecedents for all its I:

1. `M_reg(W32_seq)` is a homogeneous data-word marginal construction, not a specified full spatial marked process whose registration law reproduces all included cluster geometry, timestamps, multiplicities and sigma information. Matching a total rate/marginal survival is not matching a joint observation law. The finite records also need a declared meaning: sample compatibility, exact empirical distribution, or constraints with uncertainty.
2. W32_seq is a legitimate declared candidate in the restricted data-spacing family, but this alone does not complete actual parity placement or demonstrate compatibility with every manufacturer/test condition. Supplied-coordinate spacing is not an independently recovered physical metric.
3. The new parity process is structurally possible for a 38-cell SEC word, but its allowed time/mark law and relation to the same incident population/exposure are unspecified. No checked committed source imposes a device-specific hard span bound that disproves it; absence of such a bound is not itself a completed membership proof. Adding an unobserved upset process must not silently alter an observed incident-particle count or a total-device response if either is included in I.
4. Data-only observations with ECC disabled motivate parity erasure. Equality of the **entire** observation law also needs tester mode, cadence, filtering and any parity-sensitive outcome/timing to be either fixed identically or explicitly outside I. The upstream report retains missing run-specific metadata.
5. m0's claimed positive action imports the unqualified numerical/execution transfer in §5 below. It is not yet a passing full-device conditional-write model merely because hidden parity is set to zero.

Therefore **decision non-identifiability for the complete declared physical family is not yet proved**. The pair is not rejected as physically impossible, and a calibrated arbitrary p is not demanded. A fully specified abstract erasure example can be accepted as a conditional lemma; it cannot alone satisfy the handoff's requirement of a negative result linked to all included CY62167 information.

## 5. Frozen slice: what U_reg actually represents

### 5.1 Trace to the source, not just to constants

The selected source is `RE-CY62167-ECC-RISK-BRIDGE-01/risk_curves.csv` on scientific base `69e92fe36b3b7933cebccbedd457cc0309dd4d1c`, blob `cc5067f2c5eeba7b552839a4532fee9292b64398`. The unique full-key record is:

| Field | Frozen value |
|---|---:|
| Start / horizon | `2026-01-19T04:00:00+00:00` / 24 h |
| Shield / response / direction | 10 mm Al / main_loglog / central_mean |
| Registered scenario / period | DREG / 1 s |
| F_direct | 0 |
| F_acc_union_upper | 0.00030981194516809923 |
| F_total_upper, reused U_reg | 0.0003098119451681036 |
| F_acc_lower | 5.909252486385592e-10 |
| F_total_lower, reused lower | 5.90925197663239e-10 |
| epsilon_analysis − serialized U_reg | 0.0006901880548318964 |

The tiny total/accumulation differences at zero direct rate arise from floating-point recombination `1-exp(-hd)*(1-x)`; the lower difference is about `5.10e-17`. They are not evidence of a new physical component. This arithmetic is correctly reproduced, but the stored decimal is not a certified numerical enclosure.

The decoded, **unexecuted** `risk_bridge.py` source traces the value through `compute_risk_for_rate` → `cyclic_phase_aggregate_multi` → `aggregate_domain`. DREG reconstructs a parent-rate interface using bit rates divided by mean registered multiplicity; its direct rate is zero under its explicit measured-support interpolation and no-direct low-energy extension. Zero observed proton direct clusters is not a zero physical rate, nor does the reconstruction resolve missing file-aligned fluence.

For each residual word the declared independently marked NHPP has at most one hit per word/event, uniform per-bit rate r(t), and independent increments. Its safe-state generator per integrated per-bit exposure is

\[
Q_0=\begin{pmatrix}-32&32\\1&-32\end{pmatrix}.
\]

State 0 goes to one error at rate 32; state 1 clears at rate 1 and exits the safe set at rate 31. The exact analytical clean survival over an integrated exposure mu is therefore legitimate for this marginal model. Products across a word's deterministic clean-reset intervals are legitimate. Across words the **sum of exact marginal risks** is an upper bound without independence; the product reduction requires independence. Homogeneous rates and the full marginal time law do not follow from an aggregate measured bit cross section alone.

At the selected DREG row the direct term is zero, so a surrogate direct lower-bound controversy is not needed to reject or accept this particular lower value. `max_w F_w` is a lower bound for the matching ideal registered model with actual represented phases. It is not a lower bound on all compatible physical models. For a nonzero direct surrogate, its lower bound would not automatically be a physical-toggle lower bound either.

### 5.2 Phase and numerical qualification

`model_contract.json` declares a uniform phase on `[0,tau)` **approximated by 16 midpoint phases**. The code returns `W*mean(F_word)` for W=524288 and `max(F_word)` at those samples. It does not sum the actual W distinct sequential phases or supply an outward phase-error bound. The prior reviews explicitly retained this approximation; they did not turn every historical CSV number into a physical certificate. The validated stationary article pair-count Q_U is also not the same numerical algorithm as this nonstationary marginal-survival CSV.

An exact **16-phase grouped surrogate** could assign W/16=32768 words to each phase and use the analytical marginal sum. That makes the mathematical aggregation meaningful for that explicitly idealized schedule; it does not establish a realizable sequential schedule with that many simultaneous word restorations. It would be an explicit narrowed model interpretation, not discovery of the real phase distribution.

The independent SR check conditions on the Poisson number of hits and evolves the 0/1 jump chain, without the production eigenformula/Taylor helper. For a small stationary fixture (r=`1e-5` per bit/s, T=300 s, tau=1 s), it gives:

| Calculation | Single-word phase-mean failure |
|---|---:|
| Independent 16-phase | 0.00001486015561498531761 |
| Production 16-phase | 0.000014860155614985255 |
| Independent 128-phase | 0.00001486018739145330113 |

The finer average exceeds the 16-phase value by `3.17764679835e-11`. This is a demonstrated counterexample to treating midpoint output as automatically outward, **not** a measured error for the frozen CY slice or a demonstrated epsilon flip. Analytically, for constant rates and integer T/tau the pair-exposure sum at phase phi is `T*tau-2*tau*phi+2*phi^2`; its P-midpoint average is below the continuous average by `tau^2/(6P^2)`. Numerical sensitivity/convergence alone has no one-sided guarantee. The production small-mu Taylor and floating-point evaluation also require an error allowance for literal upper-bound last digits; six targeted primitive checks support implementation agreement but are not uniform error certification.

### 5.3 Conditional-write transfer

The source scrub engine concatenates intervals starting from clean state at deterministic phase times. It has no read latch, correcting-write decision, read-to-write delay or conditional no-write branch. The new CONTRACT expressly places physical repair at write completion. Merely using tau=1 s on both sides does not match state transitions.

Two independent explicit traces demonstrate the issue:

- **Reset interpreted at read:** singleton error → correcting read → distinct-bit upset before write → write completion. Physical first passage occurs in the RMW interval even though the write can later clear the array; a clean-at-read surrogate can stay safe.
- **Reset interpreted at completion:** clean read → upset before nominal completion → no correcting write → another distinct upset. A model that resets unconditionally at that nominal completion deletes an error that conditional execution retains.

These demonstrate failure of an automatic pathwise transfer, not a numerical failure at the selected CY rate. A properly coupled ideal-at-read process plus an explicit RMW/scan-delay event bound may retain a sufficient upper with margin. Alternatively restrict the numerical result to ideal instantaneous restoration and withdraw the physical-execution positive claim. No controller redesign or full upstream rerun is necessary to make that scope correction.

Until qualified, `0.0006901880548318964` is **the exact subtraction of the serialized inputs**, or a conditional budget *if that U is a valid matching upper*. For a physical transfer with certified nonnegative errors, the applicable condition is instead of the form

\[
\delta_{\rm cov}^{m,\pi}+e_{\rm phase}+e_{\rm num}+\delta_{\rm exec}
\le 0.0006901880548318964.
\]

All terms must have proved meanings for the same horizon; avoid double-counting if execution is already included in B_cov. No such errors are estimated here. The large displayed slack makes a corrected positive certificate plausible, but plausibility cannot replace qualification. The frozen slice has not been replaced or recomputed from radiation inputs.

## 6. Coverage, mixed paths and sufficient information

On a common probability space for each `(m,pi)`, define the full failure event A, the matched registered surrogate event R, and a measurable coverage event B. The needed premise is `A subset R union B`, together with `P(R)<=U_reg` and `P(B)<=delta_cov`. Then

\[
P(A)\le P(R\cup B)\le P(R)+P(B)\le\min(1,U_{\rm reg}+\delta_{\rm cov}).
\]

Independence is unnecessary. A conditional shared-environment bound must be averaged or made uniform correctly, not evaluated by substituting a mean environment. The scripts' addition/subtraction identities do **not** test this inclusion.

The minimal tautological choice `B=A\R` makes the inequality true but offers no new way to bound the unknown physical failure. A noncircular sufficient route is an explicit bad-driver/transition event: any omitted physical mark, parity hit, unrepresented split/merge effect, mapping mismatch or unmatched initial/service transition that can break the coupling; prove pathwise agreement/domination on its complement. Such a B may deliberately overcount and need not be directly observed, but its probability needs an independently justified upper if a numerical physical certificate is claimed. The present package supplies no such estimate. That absence is an honest limitation, not a reason to reject the conditional union lemma.

Mixed paths are essential. One data error followed by one parity error in the same SEC word produces E_cap with no D3 and no data-only exceedance. The SR trace confirms this. Counting only hidden triple marks or parity-only exceedances would not cover this path. Counting **any** omitted parity hit can cover it, conservatively, if the remainder of the coupling is valid.

Write `B_cov^(m,pi)(t0,H,mu0,execution)` and its probability accordingly. With fixed unknown W, probability is over physical histories, not a fictitious prior on W. A worst-case physical certificate needs, for one admissible policy,

\[
\sup_{m\in\mathcal M(I)}[U_{\rm reg}^{m,\pi}+\delta_{\rm cov}^{m,\pi}]\le\epsilon
\]

with any numerical/execution allowance included. A mismatched fixed W may make a coarse coverage bound equal to one; uncertainty alone supplies no fractional probability of that mismatch.

Qualified bounds on q3 or coverage can be sufficient for particular exclusion/admission decisions without revealing every coordinate of W. Conversely even exact W leaves the physical mark/time/registration law unspecified. These are sound conditional information statements. They do not show that q3/delta are the *weakest* possible observations, that both are necessary, or that either can currently be measured from these files. No new irradiation campaign is automatically required; the first corrective step is a defined compatible family and an auditable existing-source constraint ledger.

The package adds an explicit lower/upper decision-summary proposal, its logical hidden-parity threat and one frozen-slice arithmetic threshold. Symmetric difference, the union bound and the `2t+1` candidate already in DEC-004 are not newly invented tools. No novelty or completed physical-information theorem is inferred from them alone.

## 7. Device/source and initial-state limits

The inspected proton report/source manifest attributes 32 data + 6 parity, Hamming SEC and 16-bit interleaving to **AN88889**, and no automatic corrected-read writeback to **datasheet 002-20054**. These are existing source-supported architecture records, not properties inferred from the fitted address map. The primary PDFs are absent from this checkout. The exact-source lookup reached the [manufacturer AN88889 landing page](https://www.infineon.com/gated/infineon-an88889-mitigating-single-event-upsets-using-infineon-65-nm-asynchronous-sram-applicationnotes-en_51c95116-9950-41e2-a23a-ec4fcfdff7a2), which requires login; it was not bypassed. The [manufacturer product page](https://www.infineon.com/part/CY62167GE30-45ZXIT) corroborates 16-Mbit organization and single-bit correction but does not substitute for the exact historical PDF sections. No claim of freshly rehashing or fully rereading those PDFs is made.

For a physical completion, the precise existing-source request is AN88889 `001-88889 Rev. *D, 2026-02-19`, ECC organization/interleaving sections (recorded SHA256 `c91f9c9c52ca587e224adbcf5cc7f0b124aaa7283f9ffe4bb39351132b9060f2`), and datasheet `002-20054 Rev. *F, 2020-03-18`, ECC read/writeback description (`a7d9faf23208b6c0f3b2be402feb8653ff0c6f649306fc246605189018a9ed1f`). No page number is invented. For the stronger **every included run was ECC-disabled/data-only** assertion, the needed linkage is the Zenodo file/segment → campaign/protocol record; the already identified Cecchetto thesis `CERN-THESIS-2021-330 / tel-03391539` is protocol context, not automatically that linkage.

The proton report explicitly retains unknown run-specific mode, package state, exact read/correct cadence and fluence alignment. Therefore its general “ECC disabled” description must not silently establish all these settings for every included record. For the abstract erasure lemma, disabled/data-only observation may be a declared condition. For a physically compatible m0/m1 construction, list which runs/observables satisfy it, what is assumed and what remains UNKNOWN. No contrary ECC-enabled run is demonstrated here; this is an evidentiary boundary, not a fabricated contradiction.

D3 covers any safe pre-state. The numerical marginal survival and m0 positive-action proposal require physically clean initial codewords and specified phase/age. Cold/warm availability of an external observation does not establish clean memory. The reviewed 24-hour record is one clean-start reporting window; sliding outputs must not be concatenated as free fresh starts over a mission.

E_cap counts data plus parity beyond SEC capability. A triple parity event may leave data bits unchanged, yet satisfies E_cap; decoder output can still be correct in some beyond-radius patterns. Neither DUE nor SDC nor system failure follows automatically, and `(32,38)` must not be silently changed to SEC-DED `(39,32)`. No numerical decoder or mission reliability guarantee is accepted here. Epsilon=0.001 remains an analysis line.

## 8. Findings and smallest corrective actions

**CRITICAL: none.** The supported structural/conditional results survive; no completed full-device safety guarantee is accepted in this review.

### MAJOR-01 — incomplete compatible-model decision witness

**Type:** demonstrated proof omission, with a credible physical-compatibility question; not a demonstrated impossibility of m0/m1. **Locations:** CONTRACT §§4–5, 7, 9; REPORT §§3–4, 11–12; projection checker.

**Impact:** the central claim that two complete models compatible with all I give different physical control decisions is not supported by the toy projection. The “completed negative physical bridge” conclusion cannot yet be accepted.

**Minimum correction:** separate law m from policy pi; state what observational compatibility means; specify one full base process, W/parity extension, time law, observation operator, initial state and permitted executor. Give a compact constraint-by-constraint check against the actual I, including geometry, bit-rate support, interleaving and test-mode scope. Prove equality of the entire included observation law under a specified hidden extension and establish a passing m0 action using a qualified bound. A conditionally extension-closed abstract family is an acceptable narrower theorem, but must not be labelled completion for the full physical I.

**Closure:** an independent reader can verify both memberships, observational equality and opposite decisions without substituting “parity is invisible” for the missing steps. If the existing sources cannot support that construction, return the exact missing constraint and retain `NOT_ESTABLISHED`; do not invent a p calibration, run a broad search or require full proprietary topology by default.

### MAJOR-02 — frozen numerical upper not qualified for the new execution/domain

**Type:** demonstrated mismatch of model interfaces and absent one-sided transfer; no demonstrated epsilon crossing for the frozen slice. **Locations:** CONTRACT §§3, 7–8; REPORT §§0, 3.2, 4–5, 7–8; `REG_CONDITIONAL_TAU1` / `FULL_IF_COVERAGE_BOUND` rows; historical `scrub_model.py` and `ecc_word_model.py`.

**Impact:** the exact delta threshold and a sufficient conditional-write tau=1 s action are stronger than source provenance and prior SR establish. This also leaves m0's positive decision unqualified. Severity is driven by the claimed physical-execution transfer, not merely by floating-point tolerances or phase sensitivity.

**Minimum correction:** either (a) explicitly retain U as an ideal 16-phase registered-model numerical value and the delta threshold as conditional arithmetic, removing positive physical-executor claims; or (b) qualify **this same frozen slice** with an outward phase/numerical bound and a conditional-write timing/coupling allowance, with identical initial/action semantics. Put all allowances into the coverage budget once. No replacement slice, controller retuning or full production rerun is requested.

**Closure:** every supported positive row identifies a matching analytical upper and its execution/phase/numerical conditions. If a physical tau=1 action is retained, the total certified upper is below the analysis line. Narrowing under option (a) closes the overclaim, but does not by itself complete MAJOR-01's physical decision contrast.

### MINOR-01 — sharpness and minimal-information terminology

Replace “strongest universally justified”/“weakest” by “no positive lower bound established here”/“one sufficient decision-capable summary”, unless an extremal/minimality proof is supplied. Label `[0,1]` an uninformative enclosure, not an identified attainable interval. Use the quantifiers in §3. No new experiment is needed for these wording corrections.

### MINOR-02 — three-valued machine-readable contract

`decision_table.csv` uses `SUFFICIENT_CONDITIONAL` and `INSUFFICIENT_CONDITIONAL` despite CONTRACT §10 specifying exactly three statuses. Its condition column prevents a completely hidden assumption, so this is a limited schema defect, not a separate scientific failure. Export `SUFFICIENT`/`INSUFFICIENT` in an explicitly assumption-augmented model scope, with condition/qualification fields; keep current unqualified physical rows `NOT_ESTABLISHED`. The status of `REG_CONDITIONAL_TAU1` must also follow MAJOR-02 rather than inherit an unqualified positive label.

### MINOR-03 — source-access and assertion labels

`INPUTS.json` pins 14 controlled Git files but does not distinguish primary PDFs/raw inputs actually reread in this execution from historical source identities, nor attach SOURCE/ASSUMPTION/UNKNOWN to the all-runs ECC-disabled assertion. Add that distinction, the exact existing primary locators and unresolved run linkage. Preserve old manifests/history. This is a disclosure correction for the narrowed abstract result; physical compatibility of any retained strong claim remains part of MAJOR-01.

**OPTIONAL:** expose B_cov as a named driver/transition event rather than a list of “omitted failure routes”; a conservative decomposed bound is often more auditable than a minimal but circular event. This is not a demand for a measured delta when only a conditional lemma is claimed.

## 9. Reproduction and independent checks actually performed

Before running either script, checked all eight MANIFEST file byte sizes/SHA256 identities against the exact delivery blobs and all 14 INPUTS Git blob identities against their named refs: **all match**. CONTRACT blob is unchanged at `e367d63d1dd30c12c78924425e639066f5bc4643`. Git parents are exactly:

`69e92fe… → 9ea66664… (handoff) → 4bac6ec1… (CONTRACT) → 0c979c34… (delivery)`.

The handoff-to-delivery diff adds only the ten files in the new experiment directory. This establishes document order in Git, not an external independent timestamp of computation.

Copied the package to fresh isolated `/workspace/scratch/24e1723b7ed9/physical-bridge-checks.WODzBG/rerun`; executed there, in order:

```sh
python3 checks.py
python3 independent_check.py
```

Both exited 0. First enumeration: **329004** cases, no counterexample. Second: **294** cases, `passed=true`. Both regenerated JSON files are byte-identical to the originals:

| Output | SHA256 |
|---|---|
| `outputs/checks.json` | `f14e7eff8aec32c2abf1f33abe4ca25ccd9c5422002cd58f20052a3de648c222` |
| `outputs/independent_check.json` | `bc7dcfb2902d8b9353f9b6b9dd58c35980a7f599223f27da7fdd120009f7ed7b` |

RE environment: Python 3.13.5, Linux 6.18.35 x86_64/glibc 2.41. SR: Python **3.12.14**, Clang 22.1.3, Linux 6.18.35 x86_64/glibc **2.39**. These two RE scripts use only the standard library and contain the same U/epsilon constants; they neither read the historical CSV nor validate a physical coverage probability. “Independent” names a second implementation within the RE delivery, not independence of scientific evidence or inputs.

The additional reviewer-owned checker is [checks/cy62167_physical_bridge_review_01.py](checks/cy62167_physical_bridge_review_01.py). Executed from the review checkout:

```sh
python3 -B docs/scientific_reviews/checks/cy62167_physical_bridge_review_01.py /workspace/scratch/24e1723b7ed9/physical-bridge-review
```

It exited 0 and independently checks:

- pinned provenance, the unique CSV record and subtraction; all 55 summary rows give 45/9/1, with only W_00_11 having one proton direct-class cluster;
- 294, 841 and 837 componentwise-flip cases for `(n,t)=(6,1),(7,2),(8,3)`; sticky first passage despite a later clean endpoint;
- a mixed data/parity failure and two read/write timing counterexamples;
- six production marginal-survival inputs against a separately expressed Poisson jump-chain recurrence, and production 16-phase output against an explicit stationary interval calculation; the finer-phase counterexample in §5.

Production-linked numerical checks import only the old `ecc_word_model`/`scrub_model` primitives, using NumPy **2.3.5** and SciPy **1.17.0**. No driver is run. The independent recurrence and timing fixtures do not import the RE checks or reuse its set/projection formulas. The recurrence necessarily tests the **same declared marginal law**; it is not independent physical calibration. Decimal finite sums here are high-precision diagnostics, not a new rigorous interval-arithmetic certification. The script's successful assertions include expected counterexamples and must not be labelled “full bridge PASS”.

No raw cluster archive, original PDF, complete radiation trace or old production matrix was regenerated/revalidated. No output hash is offered as a proof of model compatibility.

## 10. Maximum wording and decision returned to Orchestrator

> For the declared fixed-code, fixed-word, atomic-toggle model, an event toggling at least three distinct physical cells of one SEC word forces capability exceedance from every safe pre-event state. Its horizon occurrence probability is therefore a lower bound on first-passage risk for every permitted restoration-timing policy. The present delivery establishes no positive common physical occurrence lower bound for CY62167. A registered-surrogate upper can be transferred to a complete-word model by an explicit coverage coupling and an independently qualified coverage-probability upper, with matching initial and execution semantics. Such a coverage estimate is not obtained here. The frozen registered calculation yields the arithmetic remainder 0.0006901880548318964 at epsilon=0.001; using it as a physical coverage budget additionally requires qualifying the registered upper, phase approximation and conditional-write execution. A hidden parity extension illustrates an observation ambiguity under an explicit data-erasure interface, but the delivered descriptions do not yet prove a decision-changing pair compatible with all declared CY62167 information.

Answers requested by the handoff:

1. **Accepted as structural fact:** D3/`2t+1`, cancellation limitation, first-passage inclusion and their carefully stated policy quantifiers.
2. **Still conditional transfer:** the union lemma and all numerical coverage/physical-action implications. No delta or q3 calibration, physical direct floor, complete device upper, DUE/SDC or system guarantee is established.
3. **Claimed non-identifiability proved?** For a narrowly specified parity-erasure extension, the observation lemma is valid. For the full I and opposite physical admissibility decisions, **not yet**; MAJOR-01 and m0's MAJOR-02 dependency remain.
4. **Physical bridge completed under the original handoff?** **No.** There are valid reusable pieces, but neither a qualified physical positive slice nor a completed I-compatible negative decision witness. This is a bounded repair request, not a conclusion that completing path A is impossible.

**Next corrective action:** return the two MAJOR items to RE as one bounded completion: a complete compatible-pair/observation proof and either a qualified same-slice executor upper or an explicit demotion of its numerical status. Terminology/schema/source-access corrections need no broad new review cycle. No new control study, full W search, irradiation campaign, RES registration or Issue closure is authorized by this recommendation.
