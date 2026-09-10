# Stage A — restoration control applicability and information headroom

**Status: PI ACCEPT WITH THREE CLARIFICATIONS / EXECUTION AUTHORIZED / NOT EXECUTED.**
PI accepted proposal edb987bd3bfe1f639a072f8f0b31a3dcb3197f0e subject to the
clarifications incorporated here: rho is a bit-rate allocation fraction;
the organization is declared post-W; direct-budget triviality is audited
before policy search. Piecewise-constant exposures are evaluated analytically.
This is the accepted execution/derivation contract, not a HYP, RES or novelty claim.
Date: 2026-09-07. Owner: Research Orchestrator.

## 1. Authorized scope

PI authorizes one bounded derivation-and-computation package that compares fixed,
precomputed and causal fully informed restoration choices under the same
finite scenario family, first-passage risk certificate and serial actuation
contract. Operational estimation/Stage B is not authorized by this approval.

The first slice is **proton-driven, data-only, conditional**. GOES rates and
CY62167 timing/word-size information ground its scale. Its two-level temporal
construction and post-W mark law are explicit experimental assumptions, not
a calibrated mission, real proprietary W or experimentally established MCU law.
It cannot by itself discharge the broader physically justified-domain objective
of RQ-007. Its purpose is to locate which parameter/interface uncertainty actually
changes a restoration/resource decision before requesting further calibration.

Heavy-ion angular transport, COSRAD matching, parity and ERR write estimation
are outside this execution. No physical applicability conclusion may silently
drop these mechanisms for a real mission.

## 2. Controlled basis and disposition

- Implementation/semantics: `619cb3538e296b3619f21301a176665f4611143f`.
- SR re-review: `e11e1b1db1ca26b79291dad59f818167f2441620`, report
  `docs/scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md`.
  Orchestrator accepts PASS_WITH_MINOR: both MAJOR findings closed; residual
  ERR consumer issue remains open and is contained by using U only here.
- Angular provenance: `313a3a3ff1ef7781f05fdf5461194071f631a4f3`,
  `experiments/CY62167-ANGULAR-FINDING-CONTROL-01/REPORT.md`.
  Accepted as bounded provenance/extraction; transcribed angular diagnostics
  without persisted original code are not quantitative inputs to this study.
- DEC-001/002, RQ-002…007 and RES-001 retain their accepted scopes.
- PA-DOM and Chen constrain eventual comparisons/novelty; no new search is required.

The two reports are sibling commits from 619cb353. The implementation must
read both at their exact commits, not assume that either branch contains the
other. This specification branch contains angular provenance and cites
the immutable SR commit; it does not modify their historical reports.

## 3. Frozen input and scenario construction

Use the committed file at 619cb353:
`experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv`.
Record its Git blob, SHA-256, row count and selected timestamps in the new manifest.
Do not download revised NOAA files or rerun transport/cross-section processing.

Run three separate architecture/environment cases: Al shielding d = 1, 3, 5 mm.
Use columns `d1_lambda_central_s-1`, `d3_lambda_central_s-1`,
`d5_lambda_central_s-1`, respectively. These are full-array bit/upset rates,
not parent-event rates. Verify units/array scaling against the frozen input
manifest; a mismatch stops execution rather than being silently rescaled.

Retain only paired-valid, finite nonnegative rows in the frozen Jan–Feb 2026
record. For each d define L = median and H = maximum of that column; median
means the average of the two central sorted values for an even row count.
Report the max timestamp and median bracketing timestamps/values. These
deterministic selections are prescribed before observing new control results.

For each d construct four independent 600 s scenario windows:
LL, LH, HL, HH. Each letter specifies a constant bit rate for one 300 s block.
This is a controlled two-level stress family based on measured-response range,
not an assertion that two consecutive peak blocks occurred or that transitions
have equal probability. No scenario probabilities or mission frequencies are
assigned; no weighted average benefit is reported. All four are required for
robust feasibility. Windows start clean; there is no carry between windows.
State DOES carry through t = 300 s within a window.

All comparators know this family in advance. Their information is a benchmark
contract, not a claim that a real controller knows the future GOES record.
The original E/W/isotropy, low-energy extrapolation and cross-section limitations
remain attached. No heavy-ion multiplier or GEO average is added.

## 4. Declared post-W error models

N = 2^24 data bits, n = 32 data bits/word, Nw = 2^19 words, SEC threshold 1.
This is a declared post-W organization: 2^19 logical words x 32 data bits.
Events are generated directly in word/bit coordinates. W_00_01/floor(A/4)
is provenance for the corresponding CY62167 scale/organization and a comparator,
not a required mapping input or a physically identified W in this computation.
Parity and decoder/system consequences are outside the data-only event.

At total bit rate b(t), parameter rho defines disjoint independently marked
Poisson streams with deterministic blockwise intensities:

- residual singleton arrivals: nu_C(t) = (1-rho)b(t), uniform over N bits;
- two-bit same-word parent arrivals: nu_D(t) = rho*b(t)/2, uniform over words
  and unordered distinct bit pairs of that word.

Thus nu_C + 2 nu_D = b. Rho is the fraction of the total erroneous-bit rate
budget assigned to two-bit same-word parents, NOT their fraction among parent
events or a two-bit-event probability. Physical transitions in this declared model are toggles.
The comparison surrogate absorbs on a two-bit parent; it is not the exact
toggle model. Parent association is retained; no direct bits are recounted as
residual arrivals. Uniformity and multiplicity-two are modeling assumptions.

Use rho = 0, 1e-4, 1e-2 as three separately labelled sensitivity cases, plus
M_rho = {0, 1e-4, 1e-2} for a finite ambiguity calculation. These are not measured
probabilities, confidence limits, or an envelope of all physical possibilities.
No theorem about extrema between these values is assumed. Rho is never
identified with the earlier DCLUSTER theta without a separately derived conversion.

This construction is a minimal post-W mechanism comparator, not a replacement
for the accepted event-level extraction or a claim that full topology is needed.

## 5. Restoration and realizable actions

Primary access contract: R2-U, a full external-address scan with unconditional
writeback; 2^21 reads and 2^21 writes per pass, 45 ns per operation, serial,
no arbitration overhead. Assumed effective complete-word restoration must be
stated separately from physical manufacturer timing. Full-pass duration
P = 0.18874368 s is conditional on this service model, not measured throughput.

For an explicit conservative word-reset schedule, account for four external
addresses per word and credit its restoration only at the end of that group's
service. Word w = 0…Nw-1 has offset (w+1)P/Nw in a pass. Earlier corrections
are not credited; explain why this surrogate service abstraction is sufficient
for the retained certificate. Do not claim that it is an exact device trace.

U = {0.2, 0.5, 1, 2, 5, 10, 20, 30, 60, 100, 150, 300} seconds.
Every action is >= P and divides 300. P grounds the architectural minimum;
0.2 is the smallest grid action, a distinct quantity.

Within each 300 s block with selected tau, passes END at tau, 2tau, …, 300 s
relative to the block start; each pass starts P seconds before its end.
The array is not reset simultaneously. At the block boundary only each word's
actual last restoration time carries forward. No extra free reset is introduced.
Actions may change only at 0 and 300 s. T=600 s, mu_0=clean in every window.

## 6. Information and comparator classes

| Class | Available information | Policy restriction |
|---|---|---|
| Fixed | d, model family, time, U, epsilon | One tau for both blocks and all four paths |
| Precomputed | Same prior information and elapsed time | One pair (tau_1,tau_2) chosen before observing either level, common to all paths |
| Causal full-current-information | Same prior plus actual current L/H level at block start | tau_1 depends only on first level; tau_2 may depend on both observed levels and past action |

At t=0 both continuations L and H remain possible even for the full-current
comparator. It never receives the second level early, future parent arrivals,
realized error states or a trajectory identity. This is an ideal environment-
information comparator within the stated two-decision class, not a fully
state-informed oracle or an absolute bound over all possible adaptive policies.

In the M_rho calculation all three comparators remain robust over the same
unobserved rho set. Separately report known-rho cases; do not attribute knowledge
of rho to the environment observation channel. The information states therefore
reduce one common model family without changing the physical scenarios.

## 7. Risk and mandatory derivation before computation

F_A is first capability exceedance in the whole data-only domain during the
600 s window, including failures before any later reset. Use epsilon in
{1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2,1e-1}; all are experiment parameters.

The proposed sufficient certificate for each scenario/action path is

Q = min(1, Lambda_D + sum_w choose(32,2) * sum_J [integral_J r(t)dt]^2),

where r(t)=nu_C(t)/N, Lambda_D=integral_0^600 nu_D(t)dt, and J are word-specific
intervals split by actual credited restorations, clipped at 0 and 600.
A reset interval crossing t=300 is integrated across BOTH intensity blocks.
Evaluate each exposure analytically as sum(rate x overlap duration) for the
piecewise-constant rate. No numerical quadrature is needed. Derive the phase
sum analytically where possible and check it against independent explicit
interval summation; account for floating-point and boundary arithmetic errors.
Do not sum independently clean block risks or insert an average intensity into
the old stationary formula. Record numerical error separately from model scope.

Required derivation: show the distinct-bit pair counting and first-passage
inclusion, including sequential reset phases and the boundary transition.
For this comparator, control observes exogenous levels only, never Poisson
arrivals/state; conditioning on a scenario makes its actions deterministic.
Prove that this permits scenario-wise use of the certificate. A future internal
counter controller does not inherit that proof automatically.

This formula is PROPOSED, not established here by executing a new derivation.
If its assumptions or service abstraction fail, return the exact failed step;
do not silently change the model or start Monte Carlo to mask a proof gap.

Certified feasibility: Q plus justified numerical upper error <= epsilon for
every scenario/rho compatible with that policy's declared information.
Unresolved numerical threshold comparisons remain UNRESOLVED.
No claim of exact physical infeasibility follows from Q > epsilon.

## 8. Common selection rule and finite computation

### Mandatory direct-term triviality audit BEFORE policy search

First export Lambda_D(d,rho,path) = rho*(300*b_1 + 300*b_2)/2 for the
36 d/rho/path combinations, with classifications for all eight epsilon values.
This small audit precedes any policy optimization or full certificate table.
If Lambda_D > epsilon, label DIRECT-CERTIFICATE-BUDGET-EXHAUSTED and skip
policy search for that case. Equality is recorded separately as zero remaining
residual budget; do not reject an exact equality solely by the strict test.
An unresolved floating-point comparison must not be pruned as proven exhaustion.

If one required path/model exhausts the budget, the corresponding whole robust
family is uncertified. Never silently remove that path/model to manufacture a
robust feasible set. Report the witness and distinguish this outcome from zero
value of current information. Known-rho cases, especially rho=0, remain the
primary information-headroom comparison. Other paths may be reported as local
diagnostics but not as the original all-path robust result.

Do not change rho={0,1e-4,1e-2} post hoc. If both nonzero cases produce only
trivial certificate exhaustion, report that outcome and continue eligible
known-rho cases. A new rho grid requires a separate PI decision. No exhaustion
classification is called a physical floor or physical infeasibility.

### Selection and reusable tables

All classes use one experimental rule: among robustly certified policies,
minimize the worst-case total pass count across LL,LH,HL,HH (and rho if ambiguous).
Break ties by lexicographically minimizing path pass-count vector in fixed order
LL,LH,HL,HH, then lexicographically maximizing realized periods in that same
path/time order. Disclose tie-dependent selected-action differences separately
from unavoidable differences between admissible sets.

This explicit primary activity criterion is not a final RQ-005 scalar objective.
For fixed R2-U service, reads, writes and occupied time are proportional to pass
count; verify this identity. Do not assign weights to unrelated cost components.
Report pathwise results, worst case, and componentwise dominance, not a fictitious
scenario-frequency mean. A change of tie ordering may change a selected policy;
any action-invariance conclusion is conditional on this declared rule.

Precompute the 12x12 action-pair certificate/cost table for each of four level
paths, three d values and three rho values: at most 5,184 elementary cases,
pruned first by the direct audit. Reuse these
tables for epsilon and ambiguity comparisons. Fixed policies use its diagonal;
schedule policies use one common pair. The causal policy tree has two first-stage
nodes and four second-stage nodes; impose shared first actions across matching
prefixes. Use finite constraint enumeration/pruning or dynamic programming on
these tables, not independent post-hoc per-path optimal action choices.

No new mapping sweep, radiation transport, COSRAD, general stochastic simulation,
parameter fit or large policy search is needed. Unknown software runtime is not
a promise of a particular wall-clock cost. First implement exact finite tables
and invariants; stop on proof/input inconsistency.

## 9. Outputs, conclusions and stopping rules

Per d/rho/epsilon/path report: selected actions, passing-action/policy sets,
Q and numerical margin, total passes, reads, writes, occupied seconds and
occupied fraction of 600 s. These last quantities are not workload latency,
energy, information cost, controller overhead or net value of information.

Report componentwise fixed-minus-full and schedule-minus-full costs on each
path; negative, zero and mixed differences are permitted. Since comparator
classes are restricted, these are class-bounded gaps, not universal maximal
adaptation/online-information headroom. Do not use selected-action gaps as proof
that a future physical controller realizes them.

Map outcomes separately:
- all tested actions uncertified (physical feasibility unresolved);
- a certified model action below the service limit, only if separately examined
  and justified (not inferred from failure on U);
- exact model/physical-floor exclusion, only with a separate valid lower proof
  (not supplied by direct absorbing surrogate; mark NOT ESTABLISHED here);
- same action due to grid, same admissible set, or tie-rule selection;
- cost difference caused by certificate/model uncertainty;
- robust finite-rho action versus known-rho action and its resource consequence.

No automatic Stage B launch. Preparation of Stage B is justified only if the
schedule/full-current gap survives numerical uncertainty and changes a measured
actuation component within U. This is evidence of a remaining opportunity in
the model, not proof of engineering significance. No unsupported significance
threshold is invented. If no gap appears, stop this slice, state its conditional
scope and do not conclude that real online information is unnecessary.

If certificate conservatism prevents answering the central question, identify
the smallest consequential model/action subset for a later exact-risk check.
Do not run it automatically. If angular/parity/event calibration is required to
transfer a conclusion to hardware, record that transfer gap rather than turning
the bounded calculation into a physical guarantee.

## 10. Verification, delivery and subsequent gate

RE deliverables after PI approval: one implementation/report directory, machine-
readable frozen config/manifest, derivation, finite tables, selected policy trees,
focused tests, and a concise applicability/resource map. No HYP/RES promotion.

Independent checks must cover: rate conservation; identical prefix actions;
same feasibility constraints for all comparators; no boundary free reset;
between-phase integrated exposure; stationary reduction to the reviewed bound;
zero residual/direct limits; resource counts and architectural lower limit;
certificate class inclusion Fixed subset Schedule subset Causal (with equal
information about rho); invariance to scenario row storage order; explicit
tie-order dependence; numerical precision near decision boundaries.

Use an independently written small-word explicit reset-interval summation to
check any closed-form phase-sum acceleration. Production tests must not merely
repeat that acceleration. No claim of Monte Carlo uncertainty: MC is not used.

One Scientific Reviewer pass on the completed derivation/comparison precedes
any scientific promotion. It is not another pre-execution conceptual review.
RQ-003 supplies SEC/reset semantics; RQ-004 supplies the ideal current-rate
information boundary; RQ-005 supplies actuation accounting; RQ-002/006 retain
mark/observation calibration ownership; RQ-007 owns the policy comparison.

**PI disposition:** ACCEPT WITH THREE CLARIFICATIONS, incorporated above.
RE may execute this bounded contract under the exact-base handoff without a
further conceptual approval cycle. New rho choices, scope expansion, Stage B
and permanent result promotion require their corresponding separate decisions.
