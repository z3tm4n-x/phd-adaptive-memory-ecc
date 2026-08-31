# EXP-001 — Orchestrator disposition

**Status:** `SCIENTIFIC REVIEW REVISE / VALIDATION REPAIR REQUIRED / NOT RES-xxx`
**Research Engineer commit:** `84728d1b5768e7c91c508495d696c5980943ae57`
**Scientific review:** [EXP-001-SCIENTIFIC-REVIEW-01](../../../docs/scientific_reviews/EXP-001_SCIENTIFIC_REVIEW_01.md) — `REVISE`
**Related:** `DEC-001`; `DEC-002`; `DEC-003`; `RQ-002`; `RQ-006`

## Acceptance scope

The implementation, tests, fixed configurations, manifests and bounded aggregate
outputs are accepted as a reproducible implementation of the registered EXP-001
design. This acceptance does not accept a scientific result, physical SRAM model,
novelty claim, numerical reliability requirement, `HYP-xxx` or `RES-xxx`.

Independent Orchestrator verification found:

- all 17 unit/invariant tests pass;
- `python -m compileall` succeeds;
- a complete Linux rerun satisfies all declared precision and invariant rules;
- bounded aggregate/decision/invariant files and joint
  aggregate/decision/delta/invariant files reproduce byte-for-byte from the
  committed Windows run;
- only runtime and peak-memory fields differ across platforms, as expected.

The implementation correctly keeps `L3-U` distinct from deferred `L3-E`, records
zero `L0/L1` mismatches and machine-checks the declared J-A/J-B controlled-pair
invariants.

## Results admitted to Scientific Reviewer review

- `L0/L1`: 768,000 outcome/final-signature comparisons and 288,302 converted
  parent-event marks, with zero mismatch. These comparisons reuse production
  mapping/state code and are not independent full-trajectory validation.
- J-A/J-B: identical per-word impact marginals and fixed two-word event
  cardinality, but different joint pair association.
- Monte Carlo `F_A(J-B)-F_A(J-A)` is positive for all four scrub periods in the
  tested synthetic configuration, with all paired pointwise 95% intervals above
  zero; no simultaneous coverage claim is made.
- The declared L2 reconstruction and L3-U comparator exhibit both positive and
  negative signed error versus L1; no general conservatism direction is admitted.

All statements remain limited to the declared synthetic configurations and
representation rules.

## Accepted bounded analytical result for J-A/J-B

Scientific Review 01 independently accepts the derivation in this section for
the complete fixed validity domain recorded in its Section 7.4. This acceptance
does not create `RES-xxx`; the experiment still has a validation repair gate.

Under exactly the declared four-word discriminator assumptions, equal word
marginals imply that the unordered-pair probabilities can be parameterized as

\[
p_{01}=p_{23}=a,\quad p_{02}=p_{13}=c,\quad p_{03}=p_{12}=e,
\qquad a+c+e=\tfrac12.
\]

For two parent events, survival requires that their selected pairs are disjoint,
so the proposed probability is

\[
q=2(a^2+c^2+e^2), \qquad \tfrac16\le q\le\tfrac12.
\]

The lower endpoint is attained by J-B
(`a=c=e=1/6`) and the upper endpoint by J-A (one coordinate `1/2`, the others
zero). If the parent-event count in one scrub interval is Poisson with mean `m`,
then `N<=1` survives, `N=2` survives with probability `q`, and `N>=3` necessarily
causes a word to receive at least two fresh errors. The proposed one-interval
survival and equal-interval reporting-window result are therefore

\[
S(q,m)=e^{-m}\left(1+m+\frac{q m^2}{2}\right),
\qquad F_A(q,m,k)=1-S(q,m)^k.
\]

Because `F_A` decreases with `q`, the proposed identified set over this bounded
pair-distribution class is

\[
F_A\in[F_A(q=1/2),\;F_A(q=1/6)],
\]

with J-A and J-B attaining the endpoints. The endpoint result requires every one
of these fourteen conditions from Scientific Review 01 Section 7.4:

1. one declared domain contains exactly four logical words with common
   correction capability `t_c=1`;
2. the reporting window starts from a clean state;
3. every parent event impacts exactly two distinct words;
4. every selected word receives exactly one fresh erroneous bit, with no repeat
   hit, toggle-clear or within-interval repair;
5. every word has one-event impact probability exactly `1/2`;
6. one fixed pair-probability vector is used and pair marks are i.i.d. across
   parent events;
7. pair marks are independent of HPP event times and counts;
8. parent arrivals form a simple HPP, giving Poisson counts and independent
   increments;
9. parent impacts are simultaneous and `E_cap` is evaluated after the complete
   mark;
10. scrubbing is instantaneous, periodic, synchronous and clears the complete
    erroneous-bit state;
11. `t0` is aligned with the scrub phase and the reporting duration is exactly
    `k*T_scrub`, with no partial leading or trailing interval;
12. deterministic-boundary events have probability zero under the HPP and the
    implementation ordering is `scrub_then_event`;
13. `F_A` is the DEC-001 reporting-window first-passage event, so an exceedance
    remains counted even if a later scrub clears the state;
14. every logical word has enough unused bit positions for the generated
    fresh-bit construction over the finite run.

It is not a bound for arbitrary physical SRAM topologies, temporally dependent
marks, event cardinalities, repeat-hit semantics, non-Poisson arrivals or
partial/asynchronous restoration.

## Structural feasibility versus confidence-rule feasibility

The committed decision table uses each model/period's pointwise Wilson upper
bound. These CI-based decisions are not simultaneous or selection-valid
confidence guarantees over the candidate grid. Exact analytical feasibility
under `F_A<=epsilon` must be reported separately:

| `epsilon` | Exact J-A / J-B selected `T_scrub` | Wilson-rule J-A / J-B | Disposition |
|---:|---|---|---|
| 0.15 | 0.5 / none | 0.5 / none | structural/model difference retained |
| 0.25 | 1.0 / 0.5 | 1.0 / 0.5 | structural/model difference retained |
| 0.35 | 2.0 / 1.0 | 2.0 / 1.0 | structural/model difference retained |
| 0.55 | 4.0 / 4.0 | 4.0 / 2.0 | Wilson-bound conservatism creates the reported decision discrepancy |

At `epsilon=0.55`, exact J-B gives `F_A=0.5488823892`, while its Monte Carlo
Wilson upper bound is `0.5565350802`. Therefore this row must not be counted as a
purely structural decision change. The scientific interpretation must keep
separate:

1. representation/joint-dependence uncertainty;
2. Monte Carlo estimation uncertainty;
3. conservatism introduced by the confidence-bound decision rule.

For a candidate period, robust feasibility over the proposed identified set
would require the J-B/worst-endpoint exact value to satisfy the constraint;
feasibility only at the J-A/best endpoint is not robust. This interpretation is
accepted within the same complete validity domain.

## Required validation repair and bounded re-review

Scientific Review 01 found no `CRITICAL` issue and accepted the central
identified-set derivation, but returned `REVISE` because `MAJOR-01` shows that
the current L0/L1 equivalence paths share both mapping conversion and state
transition code.

Research Engineer must:

1. add a test-only independent L0 oracle for both declared `W` variants without
   calling production mapping conversion, joint simulators or shared event-update
   helpers;
2. compare complete transition traces for deterministic and bounded randomized
   cases covering clean/non-clean starts, repeat hits, immediate exceedance and
   scrub boundaries;
3. add a mutation/sentinel test proving that a wrong mapping/conversion is
   detected;
4. incorporate the four `MINOR` corrections: complete validity assumptions,
   pointwise interval wording, validation of analytical preconditions and
   deterministic/precision-linked analytical checks;
5. rerun tests and the fixed experiment and show that all seven scientific
   aggregate/decision/delta/invariant files are unchanged, unless a separately
   documented implementation defect is found.

The subsequent Scientific Reviewer task is limited to verifying closure of
these findings and absence of regression. A passing `PASS` or
`PASS_WITH_MINOR` disposition makes a narrowly bounded `RES-001` admissible but
does not create it automatically. No retroactive hypothesis is permitted.
