# Scientific Review — EXP-001

**Task:** `EXP-001-SCIENTIFIC-REVIEW-01`  
**Reviewer role:** independent Scientific Reviewer  
**Canonical base reviewed:** `d2c07e7365522fa528108ee0223a5533d884ffe1`  
**Research Engineer source commit:** `84728d1b5768e7c91c508495d696c5980943ae57`  
**Related:** `RQ-001`; `RQ-002`; `RQ-006`; `DEC-001…003`  
**Review date:** 2026-08-31  
**Recommendation:** `REVISE`  
**Orchestrator disposition:** `ACCEPTED REVIEW RECORD / EXP-001 REVISE`<br>
**Result status:** no `RES-xxx` is created or accepted by this review

## 1. Review scope

This review covers the fixed EXP-001 synthetic configurations, implementation,
tests, committed bounded outputs, J-A/J-B analytical derivation, statistical
intervals and decision interpretation at the exact canonical base above.

The review specifically checked:

- configuration validation and fixed input provenance;
- physical-to-logical mapping and L0/L1 conversion paths;
- state transitions, distinct-bit state, first passage and scrub-boundary order;
- common-random-number coupling and J-A/J-B fairness;
- Wilson intervals, paired-difference intervals and declared precision rules;
- exact, Monte Carlo/Wilson-rule and identified-set-robust feasibility;
- the interpretation limits of the declared L2 reconstruction and L3-U
  comparator.

The review does **not** evaluate target-device calibration, physical SRAM
plausibility, empirical adequacy of HPP/NHPP, decoder/system outcomes, a project
reliability requirement, adaptive-control novelty or a final resource objective.
No literature search was performed.

## 2. Instruction and canonical-state check

The active handoff is consistent with
`docs/agents/00_GLOBAL_OPERATING_RULES.md` and
`docs/agents/05_SCIENTIFIC_REVIEWER.md`. The older supplied working-guide DOCX
uses the obsolete classes `blocker / major / minor / style`; the newer supplied
agent-regulation DOCX and canonical GitHub role card use
`CRITICAL / MAJOR / MINOR / OPTIONAL` and
`PASS / PASS_WITH_MINOR / REVISE / BLOCK`. This review follows the canonical
GitHub scheme. The discrepancy is administrative and does not alter the
scientific disposition.

## 3. Independent reproduction

### 3.1 Tests and compilation

Executed from the exact base:

```text
python -m unittest discover -s simulation/tests -v
python -m compileall -q simulation/src simulation/tests simulation/run_exp001.py
```

Result: 17 tests run, 17 passed, zero failures/errors/skips; compilation passed.

### 3.2 Full independent run

Executed into a separate temporary output directory, without overwriting
accepted experiment artefacts:

```text
python simulation/run_exp001.py \
  --bounded-config simulation/configs/EXP-001/bounded-phase1.json \
  --joint-config simulation/configs/EXP-001/joint-discriminator.json \
  --output-dir <temporary-review-directory> \
  --repo-root .
```

The run completed in 55.565 s on Linux. All declared precision and hard
invariants passed. The following seven scientific files were byte-for-byte
identical to the committed Windows-run files:

- `bounded-aggregate.csv`;
- `bounded-decisions.csv`;
- `joint-discriminator-aggregate.csv`;
- `joint-discriminator-decisions.csv`;
- `joint-discriminator-delta.csv`;
- `bounded-invariants.json`;
- `joint-discriminator-invariants.json`.

Runtime and peak-memory values differed by platform, as expected. Source and
configuration SHA-256 values in the run manifest match the reviewed files.
There are no source/config changes between the Research Engineer commit and the
canonical base; only the EXP specification/disposition was subsequently updated.

**Reproduction verdict:** PASS.

## 4. Summary judgement

The controlled J-A/J-B scientific result is analytically sound after making its
full validity domain explicit. The proposed range

\[
\frac16\le q\le\frac12
\]

and the formulas

\[
S(q,m)=e^{-m}\left(1+m+\frac{q m^2}{2}\right),\qquad
F_A(q,m,k)=1-S(q,m)^k
\]

are correct for the fixed synthetic model class defined in Section 7. J-B and
J-A attain the worst and best reliability endpoints, respectively. The exact
decision correction at `epsilon=0.55` is also correct: both endpoints select
`T_scrub=4`; the committed Wilson-rule 4-versus-2 difference is an estimation/
decision-rule effect, not a purely structural effect.

The implementation is reproducible, the J-A/J-B construction is fair, and the
reported Wilson and paired-normal arithmetic is correct. The L2 and L3-U
interpretations are mostly disciplined and do not establish a universal bias or
sufficiency statement.

However, the principal L0/L1 validation is not independent: both paths use the
same mapping conversion and the same state-transition engine. Consequently,
the reported 768,000 zero-mismatch checks cannot exclude a systematic error in
that shared path. This is a material weakness in the registered representation-
ladder validation and requires revision before the experiment receives a
passing disposition.

No CRITICAL defect was found. One MAJOR issue and four MINOR issues are recorded
below.

## 5. Issues by severity

### CRITICAL

None.

### MAJOR-01 — L0/L1 equivalence is not independently validated

**Demonstrated issue.** `simulate_physical_events` converts every physical event
with `physical_to_joint` and immediately delegates to `simulate_joint_events`.
The separately prepared L1 stream is produced by `convert_l0_to_l1`, which calls
the same `physical_to_joint`, and is then evaluated by the same
`simulate_joint_events`. Thus the large randomized comparison shares both the
mapping implementation and the state-transition implementation.

In addition, the full run sets `record_trace=False` and compares only
`SimulationResult.equivalence_signature()`: `e_cap`, first-passage time and final
state. It does not compare every intermediate state transition. The phrase
“768,000 trajectory checks” therefore overstates what is actually checked; these
are 768,000 final-signature/outcome comparisons over generated trajectories.

**Failure mechanism.** A systematic error in `physical_to_joint`, in either
declared `W`, or in the shared state-update/boundary logic can be reproduced by
both L0 and L1 and still yield zero mismatches. The current test suite contains
useful hand-checked mapping and state cases, so the issue does not demonstrate
that the implementation is wrong. It demonstrates that the registered
falsification gate cannot independently detect an important class of errors.

**Impact.** The analytical J-A/J-B theorem does not use L0 and is not invalidated.
The broader claim that the implementation independently validated L0→L1
losslessness is not yet admissible.

**Required corrective action.** Before a passing review:

1. add a test-only independent L0 oracle that computes both declared `W`
   mappings and applies scrub/event/state transitions directly, without calling
   `physical_to_joint`, `convert_l0_to_l1`, `simulate_joint_events` or the shared
   event-update helper;
2. compare complete transition traces, not only final signatures, for the
   deterministic cases and randomized streams under both `W` variants, clean
   and non-clean starts, repeat hits, immediate exceedance and scrub-boundary
   cases;
3. include a mutation/sentinel test showing that an intentionally altered
   mapping or conversion is detected by the oracle;
4. rerun the tests and fixed experiment, verify that scientific outputs remain
   unchanged, and correct “trajectory checks” to “outcome/final-signature
   checks” unless full traces are actually compared.

An independently reviewed formal equivalence proof plus exhaustive oracle tests
over the fixed 8×8 mapping domain would be an acceptable alternative to a second
production simulator.

### MINOR-01 — The analytical validity-domain list omitted load-bearing assumptions

The Orchestrator list is close but incomplete. Endpoint identification also
requires pair marks to be identically and independently drawn across parent
events and independent of arrival epochs/counts. It also requires scrub-phase
alignment and a reporting duration equal to an integer number of complete,
equal intervals. These assumptions hold in the fixed config/implementation, but
must be stated in any result.

This is load-bearing: with temporally dependent pair marks, identical one-event
per-word marginals do not imply `q=2(a²+c²+e²)`; consecutive pairs can be forced
to coincide or be disjoint, widening the possible two-event survival range.

**Correction:** use the complete domain in Section 7.4 in every theorem/result
statement.

### MINOR-02 — Confidence statements are pointwise, not simultaneous decision guarantees

Each Wilson interval is a two-sided pointwise 95% interval; using its upper
endpoint is the predeclared conservative decision statistic. The selected period
is obtained after checking four candidate periods, and many models/scenarios are
reported. No family-wise or simultaneous coverage guarantee is established.
Dependence caused by common random numbers does not repair this interpretation.

The paired-normal intervals are arithmetically correct and adequate as large-
sample pointwise intervals here: there are 20,000 paired trials and 1,170–2,021
discordant pairs for the four periods. Their signs are additionally established
by the exact derivation. They should not be presented as simultaneous 95%
coverage over all periods.

**Correction:** label all Monte Carlo intervals and CI-based decisions as
pointwise. If a later claim needs a formal confidence guarantee for the selected
period, predeclare simultaneous one-sided bounds or another selection-valid
procedure.

### MINOR-03 — J analytical preconditions are inspected but not all enforced by validation

The fixed config has `t_c=1`, a clean start, aligned full resets, period divisors
of the reporting duration and the declared trial totals. `validate_joint_config`
does not explicitly enforce all of these theorem preconditions. The declared
`total_trials_per_aggregate` is also not cross-checked against
`len(batch_seeds) × trials_per_seed`.

**Correction:** validate `t_c=1` for all four words, clean initial state,
supported distinct in-range pairs, full-reset/boundary semantics, phase/window
alignment for each analytical period, sufficient fresh-bit capacity and declared
versus derived trial totals before assigning analytical outputs.

### MINOR-04 — The analytical sanity tolerance is looser than the achieved Monte Carlo precision

The configured absolute sanity tolerance is 0.02, while the achieved Wilson
half-width is at most 0.006929. A material discrepancy could therefore pass the
declared tolerance. In the actual run, this did not occur: every exact J-A/J-B
value lies inside its pointwise Wilson interval, and absolute Monte Carlo error
is at most 0.003454.

**Correction:** add deterministic unit tests for the closed-form values and use
a precision-linked statistical check rather than the standalone 0.02 threshold.

### OPTIONAL

1. Record the exact analytical and robust decision table as a machine-readable
   review/future-result input so it cannot be confused with the Wilson decision
   table.
2. Add an exhaustive symbolic/rational unit test for the four-word degree
   constraints and J-A/J-B endpoint values.
3. If raw Bernoulli paths remain unpersisted, retain per-batch counts in future
   experiments to make seed heterogeneity and cluster-robust checks possible.

## 6. Implementation and fairness findings

### 6.1 Configuration and transition semantics

For the fixed files, the following are correctly implemented:

- explicit four-word J domain and 8×8 bounded-comparison domain;
- `t_c=1` and `E_cap` first passage without DUE/SDC reinterpretation;
- clean/non-clean states where declared;
- simultaneous complete-parent-mark update before capability checking;
- toggle semantics in the bounded matrix and fresh monotone `set_error`
  semantics in J-A/J-B;
- synchronous full clear and `scrub_then_event` boundary ordering;
- initial exceedance at `t0` and retention of first passage after later reset;
- explicit L3-U upset primitive, units and first-moment calibration; L3-E remains
  rejected/deferred.

### 6.2 J-A/J-B fairness

The controlled comparison is fair for its declared purpose:

- identical HPP parent epochs are used;
- the same independent selector uniform is mapped into each model's declared
  pair distribution;
- each word has exact impact probability 1/2 per parent event;
- every parent event impacts exactly two distinct words;
- domain, ECC capability, initial state, reporting window, state update and
  scrub semantics are common;
- only the pair-subset distribution differs;
- the common-uniform coupling affects Monte Carlo covariance/precision, not the
  marginal definition of either model.

The machine checks report 39,742 common parent epochs and 158,968 verified fresh
bit updates. No fairness confounder was found in J-A versus J-B.

### 6.3 L2 and L3-U scope

The declared L2 rule independently samples every per-word multiplicity marginal
at the reused parent epoch. It therefore discards both inter-word association and
the fixed total impacted-word cardinality. Its errors cannot be attributed to
only one of those losses. The existing report appropriately limits conclusions
to this reconstruction and domain; one failed reconstruction does not establish
universal marginal insufficiency.

The J-A/J-B pair is the clean discriminator for a narrower statement: even after
fixing every one-word marginal and total event cardinality, different admissible
joint pair association changes `F_A`.

L3-U is an independent ungrouped upset process calibrated only to expected total
upset exposure. Its comparison measures the consequence of discarding parent
grouping plus all higher-order process information. The observed positive and
negative errors do not establish a universal bias or a relation to deferred
L3-E.

## 7. Analytical derivation verdict

### 7.1 Pair-probability parameterization

Let the six unordered-pair probabilities be `p_ij`. Exact two-word cardinality
and per-word impact probability 1/2 give four degree equations. Solving them
yields

\[
p_{01}=p_{23}=a,\quad
p_{02}=p_{13}=c,\quad
p_{03}=p_{12}=e,
\qquad a,c,e\ge0,\quad a+c+e=\frac12.
\]

For two independent identically distributed parent marks, survival requires
disjoint pairs. The only disjoint pairings are the three opposite-edge pairs,
so

\[
q=\Pr(\text{survive}\mid N=2)
  =2(a^2+c^2+e^2).
\]

By convexity under `a+c+e=1/2`, the minimum is attained at
`a=c=e=1/6`, giving `q=1/6`. The maximum of the simplex is attained when
one coordinate is 1/2 and the other two are zero, giving `q=1/2`.

J-B is the minimum-`q` endpoint; J-A is a maximum-`q` endpoint.

### 7.2 Interval and reporting-window survival

For one clean interval with HPP count `N~Poisson(m)`:

- `N=0` or `N=1` survives;
- `N=2` survives with probability `q`;
- `N>=3` necessarily gives at least one word two fresh errors because six word
  incidences cannot be placed over four words with all occupancies at most one.

Therefore

\[
S(q,m)=\Pr(N=0)+\Pr(N=1)+q\Pr(N=2)
=e^{-m}\left(1+m+\frac{q m^2}{2}\right).
\]

With `k` aligned equal intervals, HPP independent increments and full reset after
each interval,

\[
F_A(q,m,k)=1-S(q,m)^k.
\]

For `m>0`, `F_A` is strictly decreasing in `q`. Hence

\[
F_A\in\left[F_A(q=1/2),\;F_A(q=1/6)\right],
\]

with J-A and J-B attaining the respective endpoints.

**Verdict:** the derivation is accepted after adding the complete assumptions
below. It is an exact result for that model class, not an empirical physical-SRAM
bound.

### 7.3 Exact values for the fixed configuration

For parent rate 0.5, reporting duration 4 and the four candidate periods:

| `T_scrub` | Exact `F_A(J-A)` | Exact `F_A(J-B)` | MC J-A | MC J-B |
|---:|---:|---:|---:|---:|
| 0.5 | 0.1090539734 | 0.1660547350 | 0.10560 | 0.16410 |
| 1.0 | 0.1933388517 | 0.2760017321 | 0.19080 | 0.27710 |
| 2.0 | 0.3148651286 | 0.4126072776 | 0.31340 | 0.41445 |
| 4.0 | 0.4586588671 | 0.5488823892 | 0.45625 | 0.54965 |

Every exact value lies inside its reported pointwise 95% Wilson interval.

### 7.4 Complete validity domain required for endpoint attainment

The endpoint statement requires all of the following:

1. one declared domain containing exactly four logical words with common
   correction capability `t_c=1`;
2. clean state at the reporting-window start;
3. every parent event impacts exactly two distinct words;
4. every selected word receives exactly one fresh erroneous bit; no repeat hit,
   toggle-clear or within-interval repair is possible;
5. the one-event per-word impact probability is exactly 1/2 for every word;
6. one fixed pair-probability vector is used, and pair marks are i.i.d. across
   parent events;
7. pair marks are independent of HPP event times and counts;
8. parent arrivals form a simple homogeneous Poisson process, giving Poisson
   counts and independent increments;
9. parent impacts are simultaneous and `E_cap` is evaluated after the complete
   mark;
10. scrubbing is instantaneous, periodic, synchronous and clears the entire
    erroneous-bit state;
11. `t0` is aligned with the scrub phase and the reporting duration is exactly
    `k T_scrub`, with no partial leading/trailing interval;
12. deterministic-boundary events have probability zero under the HPP; the
    implementation's declared ordering is `scrub_then_event`;
13. `F_A` is the DEC-001 reporting-window first-passage event, so a capability
    exceedance remains counted even if a later scrub clears the state;
14. the logical word has sufficient unused bit positions for the generated
    fresh-bit construction over the finite run.

No endpoint claim survives automatically after relaxing these assumptions.

## 8. Exact versus estimated versus robust decisions

Notation: `{0.5,1,2}` is the complete feasible-period set and the selected period
is its maximum; `∅` means that no candidate is feasible. “Wilson” uses each
model's pointwise 95% Wilson upper endpoint. “Robust exact” requires feasibility
for every `q` in `[1/6,1/2]`, so it equals the exact J-B/worst-endpoint set.

| `epsilon` | Exact J-A | Exact J-B | Wilson J-A | Wilson J-B | Robust exact over set |
|---:|---|---|---|---|---|
| 0.02 | ∅ | ∅ | ∅ | ∅ | ∅ |
| 0.05 | ∅ | ∅ | ∅ | ∅ | ∅ |
| 0.10 | ∅ | ∅ | ∅ | ∅ | ∅ |
| 0.15 | {0.5} | ∅ | {0.5} | ∅ | ∅ |
| 0.25 | {0.5,1} | {0.5} | {0.5,1} | {0.5} | {0.5} |
| 0.35 | {0.5,1,2} | {0.5,1} | {0.5,1,2} | {0.5,1} | {0.5,1} |
| 0.45 | {0.5,1,2} | {0.5,1,2} | {0.5,1,2} | {0.5,1,2} | {0.5,1,2} |
| 0.55 | {0.5,1,2,4} | {0.5,1,2,4} | {0.5,1,2,4} | {0.5,1,2} | {0.5,1,2,4} |
| 0.65 | {0.5,1,2,4} | {0.5,1,2,4} | {0.5,1,2,4} | {0.5,1,2,4} | {0.5,1,2,4} |

Consequences:

- at `epsilon=0.15`, `0.25` and `0.35`, exact endpoint decisions differ;
- at `epsilon=0.55`, exact J-A and J-B both select 4;
- J-B's exact value at period 4 is 0.5488823892, while its Wilson upper endpoint
  is 0.5565350802;
- the Wilson 4-versus-2 discrepancy at 0.55 is therefore decision-rule
  conservatism under finite-sample estimation, not a structural identified-set
  discrepancy;
- robust exact feasibility is governed by J-B only within the complete domain in
  Section 7.4.

The three uncertainty objects must remain separate:

1. **representation/joint-dependence uncertainty:** variation of exact `F_A`
   over admissible `q`;
2. **Monte Carlo estimation uncertainty:** uncertainty in an estimated model
   probability at fixed `q`;
3. **CI-decision conservatism:** additional restriction caused by using a CI
   upper endpoint rather than the exact/point estimate.

## 9. Residual risks

Even after MAJOR-01 is corrected, the following remain outside the result:

- no evidence shows that real radiation-event pair dependence is i.i.d., has
  one-word marginals 1/2, or approaches either endpoint;
- no real SRAM `W`, topology statistics, test-observation model or classification
  uncertainty is represented;
- no non-Poisson, temporally dependent mark, partial/asynchronous scrub,
  finite-latency correction or repeat-hit model is bounded by this derivation;
- `E_cap` is not a decoder or system failure outcome;
- the epsilon grid is not a project requirement;
- the L2 and L3-U error ranges are descriptive for the tested reconstructions,
  not universal bounds;
- no adaptive-control law, resource optimum or novelty statement follows.

These are validity-domain limits, not defects that must be closed for a narrowly
synthetic result.

## 10. Recommendation and RES-001 gate

**Recommendation: `REVISE`.**

The current base does not receive a passing Scientific Reviewer disposition
because MAJOR-01 leaves the registered L0/L1 falsification gate non-independent.
Accordingly, a permanent `RES-001` candidate should **not proceed yet** under the
current workflow. No retroactive `HYP-xxx` is warranted.

After MAJOR-01 is closed and the MINOR wording/statistical qualifications are
incorporated, a narrowly bounded result candidate may proceed. No target-device
or physical-SRAM extension is required to close this review; that belongs to the
next experiment.

### Maximum scientifically admissible result wording after revision

> In a synthetic four-word `t_c=1` model with clean starts, HPP parent arrivals,
> i.i.d. exactly-two-word fresh-error marks independent of those arrivals, per-word
> one-event impact probability 1/2, and aligned synchronous full-reset scrubbing,
> the one-event per-word marginal impact distributions and fixed event
> cardinality do not point-identify the DEC-001 reporting-window probability
> `F_A`. The admissible pair distributions yield
> `q∈[1/6,1/2]` and the exact identified interval
> `[F_A(q=1/2), F_A(q=1/6)]`, whose endpoints are attained by J-A and J-B.
> For the fixed rate 0.5, four-time-unit window and candidate periods
> `{0.5,1,2,4}`, endpoint-specific exact maximal feasible periods differ at the
> experiment parameters `epsilon=0.15,0.25,0.35`, but not at `epsilon=0.55`.
> Monte Carlo estimates reproduce the exact endpoint probabilities within the
> reported pointwise Wilson intervals.

This wording must be accompanied by the complete validity domain in Section 7.4.
It must not be shortened to “marginals are insufficient,” “inter-word dependence
always matters,” “J-A/J-B bound real SRAM,” or “the optimal scrub period differs.”
