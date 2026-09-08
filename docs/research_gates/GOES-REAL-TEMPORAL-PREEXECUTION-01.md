# GOES real-temporal continuation — proposed bounded contract

**DRAFT FOR PI ACCEPT / REVISE / REJECT. NOT AUTHORIZED FOR EXECUTION.**
2026-09-08. Owner: Research Orchestrator. Proposed task: RE-GOES-REAL-TEMPORAL-01.
Basis: `3d24da961a151bc1ce744fbd44bf289c41b58451` and its retained ancestors.
No EXP/HYP/RES registration or novelty claim is made by this proposal.

## 1. Disposition and research decision

Orchestrator accepts RE-GOES-CAUSAL-INPUT-CONTRACT-01 as completed for its bounded
input-audit purpose. The report, extraction predicate and retained mask establish
a usable delayed-data comparator contract. This is document/code traceability
review, not a new execution of the private raw archive. The source-level checks
and counts remain attributed to the RE execution recorded in its report.

The raw-data blocker is closed. Practical as-received GOES availability/version
timing remains UNKNOWN; it is a transfer limitation, not a reason to repeat this
audit. The frozen rate series remains a retrospective model reference. The 1,449
affected central-rate timestamps cannot enter a controller as local causal data.

Next question: on real chronological sections, how much actuation saving survives
completed-bin latency and a declared bound on future rate variation? In particular,
does useful saving require a future-variation assumption already contradicted by
the same section? Establish this before implementing an estimator.

This is a conditional replay/derivation using actual timestamped input sections,
not validation of an operational sensor or a physically calibrated SRAM controller.

## 2. Unchanged physical and service slice

Reuse [Stage A](STAGE-A-PREEXECUTION-01.md), its reviewed implementation and
[information continuation](STAGE-A-INFORMATION-INTERFACE-PREEXECUTION-01.md).
Known rho=0; 2^19 words x 32 data bits; independent uniform singleton Poisson
arrivals; data-only SEC/toggle semantics; conditional piecewise-constant bit rate.
Reuse d=1,3,5 mm; epsilon={1e-8,1e-7,1e-6,1e-5,1e-4,1e-3,1e-2,1e-1}; U and R2-U
exactly as defined in Stage A. These epsilons are not project requirements.

Every evaluation window lasts 600 s and has decisions at 0 and 300 s. A window
starts clean as an externally imposed scenario condition. Word reset ages carry
through 300 s; there is no free array reset. Separate windows do not form a
continuous mission. Available pre-window observations do not imply a pre-window
memory-state trajectory. Full-pass duration remains P=0.18874368 s under R2-U.

Each frozen five-minute central rate defines a CONSTANT reference intensity in
its own bin. This is a declared reconstruction, not a consequence of observing
an average and not a guarantee for all sub-bin burst patterns. Preserve E/W and
quality fields as diagnostics, not confidence limits. No transport or refit.

## 3. Fixed input-only window selection

Partition the complete retained record into non-overlapping 600 s windows anchored
at 2026-01-01 00:00 UTC. Use the d3 central column only for selecting case IDs;
evaluate all three d values on those same UTC windows. Before any risk calculation,
select the following windows and save their timestamps:

1. Lower-median rank by two-bin mean among windows with two valid central values;
   sort by mean then UTC, use zero-based rank floor((n-1)/2).
2. Largest two-bin mean among those valid windows.
3. Largest signed second-minus-first central-rate increase among those windows.
4. Smallest signed second-minus-first difference among those windows.
5. Largest count of fallback-affected directional rows among those valid windows.
6. Earliest window containing an invalid central value, if any.

For selections 2–5 break ties by earliest UTC. Keep all selection labels, but
compute duplicate windows once; do not add substitutes. Use the preceding 3,600 s
of archived bins as potential observation history, clipped at the archive start.
Unavailable prehistory means no observation. Selection may inspect retrospective
inputs; neither the selected case identity nor its future values reach a policy.
Fallback windows are deliberately retained. No filtering on feasibility/savings.

## 4. Information, missingness and future models

An observation of bin j can be delivered only at t_j+300+L. Sweep additional
L={0,300,900,1800} s; these are experimental delays, not measured GOES delays.
At a decision, include equality-time deliveries before choosing the action.
Messages arriving between decisions wait until the next permitted action epoch.

For this first decomposition a delivered, paired-valid NON-fallback central value
is exact relative to the declared frozen rate model. It is not exact physical
intensity. Do not add an estimator, a new sensor-noise eta or a fitted confidence
interval. Uncertainty comes from missing/delayed observations and future variation.
This deliberately leaves physical calibration and measurement uncertainty open.

If either direction used the historical global-median fallback, suppress that
central observation. Suppress invalid central observations too. Do not substitute
the other direction, zero, interpolation, forward fill, or the frozen fallback.
Fallback values may remain in the retrospective reference trajectory; distinguish
that use from delivery to the controller. Masking removes information, NOT exposure.
Quality/mask status becomes available with its associated record, not in advance.
No assumption about the probability or intensity-dependence of missingness is used.

Proposed experimental prior family, shared by ALL comparators:

    0 <= x_j <= B_d,
    |x_(j+1)-x_j| <= g B_d,   0 <= g <= 1,

for consecutive five-minute reference bins in the context and reporting window.
Use B_d equal to the already frozen Stage A high-rate scale, explicitly as a
COUNTERFACTUAL KNOWN BENCHMARK CEILING. It is NOT an operationally established
prior, not a physical upper bound, and not a value learned causally from this test
record. PI approval of this proposal is requested specifically for this modelling
assumption. A real-channel guarantee would need independent evidence for B_d and g.
Using the previous maximum as an assumed domain does not turn its provenance into
an a priori measurement. No ceiling or growth limit is fitted to obtain savings.

M(I) consists of all sequences in this family matching the observations actually
delivered by that decision. Retain earlier observed constraints when replanning.
The primary sensitivity parameter g covers [0,1], including the no-inter-bin-
restriction endpoint g=1. Derive action/feasibility breakpoints instead of choosing
a favourable g after replay. A previous completed average alone is not a future
upper bound: any restriction it places on x_0,x_1 comes only through this family.

Before policy calculation derive information age at each action epoch and the
componentwise upper envelope permitted by the delivered constraints. A candidate
expression is min(B_d, min_i[y_i+g B_d |j-i|]) when the set is nonempty; establish
its attainability and consistency with lower constraints before using it. With
no observations use B_d, not the subsequently realized rate. An empty M(I) is
MODEL/INPUT-CONTRACT-VIOLATION, never zero risk or permission for a longer period.

Audit replay membership separately over the context plus window using every valid
reference bin, including retrospective fallback values. For missing reference bins,
report whether a completion exists; do not invent a point trajectory. A replay
outside the declared class cannot support a guarantee even if the numerical
certificate on some other compatible sequence passes. Preserve all exclusions
in the boundary map; do not retune g or remove inconvenient windows.

## 5. Comparators and one explicit planning rule

All comparators share B_d,g,U,epsilon, the exposure model and action times.

| Comparator | Information and commitment |
|---|---|
| Fixed | One constant period, certified over the whole prior family; same action across all selected windows for a given d/epsilon/g. |
| Precomputed | One pair selected before any section-specific observation, certified over the same prior family and common to all windows. No retrospective window label/profile. |
| Delayed causal | Timestamped eligible observations, including available pre-window data; replans only at 0 and 300 s. |
| Ideal current-rate comparator | Same prior plus exact reference bin rates through the current bin at each decision, never future bins or Poisson events. |

No justified a priori orbit/time profile is available for this dataset; do not
manufacture one. Consequently Precomputed may coincide with Fixed. The ideal
information object is a comparator assumption, not early availability of a GOES
average. For a window with missing reference values, an exact ideal replay cost
is NOT AVAILABLE; provide only compatible-set stress results, without inventing
an ideal point trajectory.

Use the following implementable, estimator-free experimental rule for every
information class. At t=0 enumerate the 144 action pairs. Retain those with the
whole-window upper certificate <=epsilon for EVERY sequence in current M(I).
Select minimum total pass count; ties lexicographically maximize (tau_1,tau_2).
Fixed restricts the enumeration to equal periods. Precomputed commits both actions.
Causal variants execute tau_1; at t=300 retain that actual first action and choose
the fewest-pass certified continuation, ties by largest tau_2, using updated M(I).
Ignoring a new report remains an admissible option when the contract is consistent.
No future observation is assumed in the initial safety certificate.

This is conservative open-loop planning with one causal replan, NOT the previously
enumerated globally optimal finite policy tree. This change is explicit and part
of the proposed PI approval. Do not claim global optimality, universal information
value, or monotone pathwise cost order. All history-dependent choices follow this
one rule; never solve each realized future trajectory as if known at t=0.
Show recursive certificate preservation for compatible added information. If no
action is certified, report UN-CERTIFIED; do not claim an emergency fallback is
safe or execute an undefined default. A later contract violation terminates the
guarantee label, even if earlier information did not expose the violation.

## 6. Derivation, output and acceptance tests

Reuse the reviewed whole-window Q for rho=0 with actual individual word-reset
intervals; exposures crossing 300 s integrate both rates. Derive maximization over
M(I), exploiting nonnegative exposure coefficients only after proving that the
proposed upper sequence belongs to M(I). Q is an upper certificate, not exact F_A.
Conditioning on exogenous environment/report histories must leave the deterministic
reset calculation applicable. No observation of random errors or memory state.

For each selected window/d/epsilon/L derive and report g-regions of model
compatibility, certified action-pair/continuation sets, selected actions and costs.
Use piecewise analytic envelopes and polynomial certificate boundaries where
possible; isolate numerical roots with stated upper/lower error when needed.
Do not turn action discretization into numerical error. If g-regions of selected
cost are not monotone, report a set rather than a single threshold.

Required outputs are a compact derivation, window/input table and boundary/resource
map, with a causal information timeline. Report certificate margins, compatibility
status, passes, reads/writes, occupied seconds and occupancy percentage points.
All actuation components use the same R2-U definitions. Show signed Precomputed-
minus-Delayed and Delayed-minus-Ideal differences, with the absolute scale beside
relative percentages. Retention is reported only where Precomputed-minus-Ideal>0;
do not clip negative or >1 values or infer an optimal-policy theorem from this rule.
At missing-reference windows mark ideal/retention NA. No weighted mean over cases.

Distinguish losses caused by measurement-bin completion, additional latency,
fallback/missingness, the assumed variation bound, the conservative planning rule,
the certificate and U/ties. Do not promise a causal decomposition from a single
combined number. Information acquisition and controller costs remain separate and
UNKNOWN; no net benefit or invented engineering significance threshold.

Focused verification: no future delivery; same-history same-action; masked rates
cannot affect controller messages; changing hidden future inputs cannot change an
earlier action; nonempty-model/envelope checks; no free reset; independent small-
word exposure summation; retained planned continuation after compatible updates;
exact/interval-verified decision boundaries and resource identities. Test the
limiting no-observation and g=1 contracts without assuming a cost result in advance.
No rerun of old production matrices, transport, Monte Carlo or raw NetCDF audit.

After PI approval, RE may execute ONLY this package in a new task directory, then
return it for one Scientific Review focused on the new envelope/replanning claims.
Stop after this map. No estimator, faster action grid, revised ceilings, internal
counter, topology/parity work or larger mission study is automatically authorized.

## 7. Decision enabled and scientific interfaces

A useful output says which assumed variation bounds and delays retain certified,
absolute actuation savings AND whether the selected real sections satisfy those
bounds. Saving only under contradicted or unsubstantiated bounds is not practical
evidence for adaptation. No saving is a valid stop result for this declared rule
and family, not proof that all adaptive control is useless.

RQ-004 supplies causal delivery and future-information limits; RQ-007 supplies
robust feasibility and decision consequences; RQ-005 supplies actuation accounting.
RQ-002/003/006 provide the unchanged conditional model/reset/organization slice.
Operational timing, physical B_d/g justification, intra-bin bursts and calibration
remain explicit transfer gaps. PA-DOM/Chen closure is reused; no literature search.

PI is asked to approve this bounded proposal, particularly the assumed ceiling/
variation family and the common conservative replanning rule. No additional data
are requested now. This file is a reviewable proposal, not permission to execute.
