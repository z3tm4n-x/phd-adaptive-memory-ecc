# Stage A continuation — information-interface sensitivity

**Status: PI ACCEPT WITH TWO QUALIFICATIONS / BOUNDED EXECUTION AUTHORIZED / NOT YET EXECUTED.**
Date: 2026-09-08. Owner: Research Orchestrator. Related: RQ-004/005/007;
RQ-002/003/006 supply unchanged model interfaces. No EXP/HYP/RES is registered.

## 1. Purpose and controlling basis

Determine which delay and observation uncertainty still permit the ideal
current-information action, or retain a declared fraction of its pathwise
actuation saving over Precomputed. This is **information-interface sensitivity
of Stage A**, not validation of a practical controller or sensor.

Base: `924b1069faf576636e8bbf55a8ec29b3b1f4904d`.
Reuse [Stage A specification](STAGE-A-PREEXECUTION-01.md),
[implementation](../../experiments/STAGE-A-IMPLEMENTATION-01/REPORT.md),
[derivation](../../experiments/STAGE-A-IMPLEMENTATION-01/derivation.md),
configuration and retained passing sets in the same implementation directory,
and [Scientific Review](../scientific_reviews/STAGE_A_SCIENTIFIC_REVIEW_01.md).

Orchestrator disposition: Stage A scientific findings are supported within the
reviewed finite class; the subsequent reproduction-only repair closes the
blocking packaging finding without changing science. No additional broad SR
or production rerun is requested for that repair. This does not promote a RES.
Historical review/run records remain unchanged. Older project-wide summaries
still describe the pre-Stage-A gate; they do not override these specific records.

Known: zero Precomputed-to-Ideal minimax pass gap coexists with positive
LL/LH/HL savings. Unknown: how much survives imperfect information and whether
the absolute saving merits an implementable observation channel.

## 2. Freeze everything except the information interface

Use **known rho=0 only**, not a newly estimated rho and not the ambiguous-rho
family. Retain all three shielding cases, frozen L/H values, experimental
epsilon grid, 600 s window, clean start, four LL/LH/HL/HH paths, post-W data-only
SEC organization, singleton arrival/toggle law, R2-U, U, and the Stage A Q bound.
State carries through 300 s; no free reset. Decisions remain ONLY at 0 and 300 s.
No probabilities of scenarios, sensor errors or mission frequencies are added.

The same whole-window certificate Q <= epsilon is required on every compatible
true path and allowed observation history. Q is not exact F_A; certificate
failure is not physical infeasibility. Reuse Stage A arithmetic and passing
action pairs; do not repeat input transport, full production or physical sweeps.

## 3. Parameterized external-information channel — proposed assumption

To avoid confusing the low level L with latency, write levels b_L,b_H and
latency ell (the PI's L). These symbols are local proposed definitions, not
parallel replacements for canonical terminology.

Two potential measurements have declared timestamps s_1 in [0,300) and
s_2 in [300,600). Delivery is at s_i+ell, ell >= 0; a report delivered exactly
at a decision is available before that decision. Both measurements are enabled
by default; fixed, predeclared suppression of either or both gives missing-update
comparators. There are no samples before the clean-start window. Update moments,
their separation s_2-s_1 and latency are channel parameters, NOT new action times.
The aligned endpoint is s_1=0, s_2=300, ell=0.

A delivered value y_i measures the rate AT ITS TIMESTAMP, with declared bound
|y_i-b(s_i)| <= eta*(b_H-b_L), eta >= 0. No estimator or error distribution is
selected. Negative measurement values may occur mathematically; they are not
negative physical rates. The controller receives the timestamp and compatible
set S_i={b in {b_L,b_H}: |y_i-b| <= eta*(b_H-b_L)}. Empty sets violate the channel
contract and must trigger an input failure, not removal of an inconvenient path.

The interface deliberately retains only S_i, not additional information in y_i.
Enumerate exactly which singleton/ambiguous S_i can occur at each eta, including
boundary equality. All allowed errors are covered robustly; no averaging or
independence of measurement errors is assumed. Reports are exogenous to Poisson
arrivals and memory state: adversarial choices do not observe realized upsets.

M(I) is the subset of the ORIGINAL four paths consistent with all delivered
timestamped sets and the already selected actions. A first-block report never
identifies the second level; absence of a report at a known delivery time must
not leak a hidden level. Past actions carry exposure history, not a free reset.

Before ANY policy enumeration, analytically derive the finite observational-equivalence regions of
(ell,s_1,s_2,eta,enabled updates). Do not choose a dense numerical parameter grid.
With fixed action times, positive delays can be indistinguishable. In particular,
for aligned samples, 0<ell<=300 delivers only the first-level report by the second
decision; the second-level report is too late. Reports sampled later within a
block do not create intra-block reactions. Include boundary and missing-report
cases explicitly. Binary level uncertainty can likewise have stepwise regions.
A broad region of identical actions is a valid boundary result, not a reason to
invent intermediate levels, a smoother curve, or faster decisions.
PI explicitly accepts a finite, stepwise map as a substantive outcome. Export
the analytical timing and eta boundaries, including equality cases, before
enumerating the distinct policy problems; no separate PI pause is needed there.

## 4. Comparison and robust policy contract

Compare Precomputed -> Delayed/uncertain Causal -> Ideal Causal. Reuse Fixed as
an absolute resource baseline, not a new optimization problem.

A policy assigns the same action to indistinguishable histories. At 0 its
choice must admit a certified continuation for every compatible future path
and report; at 300 choose only continuations satisfying the whole-window Q.
Never optimize true paths independently and label the collection a causal policy.
Show why conditioning on an exogenous true path AND an allowed report history
leaves the Stage A deterministic-action certificate applicable.

Retain the Stage A selection rule with the minimum required robust extension:
minimize worst pass count across paths AND allowed report histories; then
lexicographically minimize the four pathwise WORST-report pass counts in
LL,LH,HL,HH order; then lexicographically maximize realized periods in that
path/time order, with histories ordered canonically by timestamp and S_i
({b_L}, {b_H}, {b_L,b_H}). Publish this ordering. At the ideal and no-information
endpoints it must recover the original rule/results. No hidden cost weights.

Record BOTH achievable ranges across reports and guaranteed worst-report costs.
Additional information may be ignored. Verify class inclusion and use the
reviewed HH argument rather than presenting minimax equality as a new discovery.
Selected per-path actions need not be componentwise ordered when policies trade
actions between blocks; label trade-offs rather than calling every change
"more conservative".

## 5. Required boundary and absolute-resource outputs

For each distinct information region and retained d/epsilon/path, report:
compatible paths, admissible continuations, selected periods, Q/margin, pass
count and the two questions separately:

1. Can the Stage A ideal selected action/tree be implemented with this channel
   while respecting shared histories and its own preceding actions?
2. Does the common selection rule actually select that same action/tree?

Do not graft an ideal second action onto a different first action without
checking its actual accumulated exposure. Distinguish action equality, equal
cost with different actions, grid-induced invariance, tie-rule effects and
certificate conservatism. "Uncertified" is distinct from "no saving".

Let p_P(path) be Precomputed passes, p_I(path) ideal passes, and
p_D^worst(path) the selected imperfect policy's worst-report passes.
Report G=p_P-p_D^worst and loss=p_D^worst-p_I, with signs retained. For
p_P-p_I>0 report retention R=G/(p_P-p_I); otherwise R is NOT APPLICABLE.
Report optimistic report-conditioned values separately, never as guaranteed ones.
No path probabilities, average gain, or automatically clipped ratios.

Construct the set of parameters where the ideal action is implementable and
the set where R >= gamma for each LL/LH/HL path, and their intersection.
Gamma in [0,1] is a reporting target, not a reliability requirement: export
the attained retention breakpoints so any target can be queried without reruns.
Give maximal allowable latency only when a maximum exists; otherwise report
the admissible set/supremum and open/closed endpoints. Do not presume monotonicity
of tie-selected pathwise results; justify any simplification used.
Every maximum/supremum is conditional on this Stage A contract, especially the
absence of pre-window observations and the fixed decision times. It is NOT a
maximum permissible latency for a real external sensor channel.

Alongside every saving report absolute p, reads=writes=p*2^21,
occupied seconds=p*0.18874368 and occupied fraction=p*0.18874368/600 for
Fixed, Precomputed, imperfect and ideal. Report savings in seconds and percentage
POINTS of interface occupancy, not only percent reduction of scrub activity.
Under the declared serial equal-time service this is the bandwidth-service
fraction; it is not measured workload latency, application throughput or energy.

Use absolute values for an early viability assessment. If no engineering
significance threshold is justified, report scale and sensitivity, not an
invented "negligible" cutoff. Acquisition/storage/processing and controller
overhead remain UNKNOWN and separate. Actuation saving is at most a componentwise
overhead allowance under a later compatible accounting model, not net benefit.

## 6. Minimal execution after approval and stop rule

Derive observation regions first; reuse Stage A passing sets and perform only
the new finite shared-history policy calculation. Skip previously uncertified
known-rho=0 families when class inclusion proves that extra restrictions cannot
restore feasibility. Do not recalculate unchanged model tables for every region.

Deliver one compact derivation/report, machine-readable region/action/resource
map, policy implementation and focused tests in one new task directory.
Tests: timestamp boundary ordering; indistinguishable-history actions; all allowed
true-level/report combinations; whole-window carry; ideal/no-information endpoint
recovery; finite class inclusion; resource identities; exact threshold handling.
One pinned base plus paths identifies reused Git artefacts; no duplicate hash
inventory or packaging-only scientific-review cycle. Independent review should
focus on the NEW observation reduction, robust policy logic and boundary claims.

Stop this two-level sensitivity study after the finite map. If timing/uncertainty
collapse most cases to a few regions, report that result and do not expand the
action grid, observation model or scenario family to force a richer map.
No estimator, COSRAD/angular calculation, new rho, parity/ERR model, Monte Carlo,
literature campaign, permanent result or practical-controller claim is authorized.

## 7. Following interface, not part of this execution

The next proposal after this sensitivity result must use real temporal segments
and an explicitly available external/internal observable, with update/latency
semantics and separate acquisition/controller costs. It must not be another
unbounded two-level parameter sweep. Choose that proposal using the map and
absolute resource scale, including zero/unresolved outcomes.

PI's candidate distinction between T_rel (accumulation) and T_obs (risk before
detecting an increase through scrub corrections) is retained as an UNVERIFIED
derivation question, not a registered hypothesis or additional current constraint.
Internal counts depend on exposure, previous actions, detection semantics and
random arrivals; latency is not automatically equal to T_scrub. Such policies
do not automatically inherit this exogenous-report conditioning argument.
Before deriving T_obs, specify the count/reset interface, detection criterion
and transition-risk allocation; do not import historical formulas. This belongs
to the subsequent RQ-003/004/007 interface, with RQ-005 cost accounting.

**PI disposition:** ACCEPT, with the two qualifications incorporated above:
derive the timing/eta equivalence boundaries before policy enumeration and keep
every latency boundary conditional on the no-pre-window-observation contract.
RE may execute this bounded contract without another conceptual approval cycle.
Task: STAGE-A-INFORMATION-INTERFACE-01. Delivery: a separate branch
`research/stage-a-information-interface-01`; new files only in
`experiments/STAGE-A-INFORMATION-INTERFACE-01/`. Preserve prior outputs and main;
do not create a PR or merge. Return the implementation for Orchestrator disposition
and focused Scientific Review of the new analysis; RE does not assign review PASS.
