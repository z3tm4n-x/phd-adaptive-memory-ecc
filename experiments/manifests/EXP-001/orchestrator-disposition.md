# EXP-001 — Orchestrator disposition

**Status:** `TECHNICALLY ACCEPTED / SCIENTIFIC REVIEW REQUIRED / NOT RES-xxx`
**Research Engineer commit:** `84728d1b5768e7c91c508495d696c5980943ae57`
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

- `L0/L1`: 768,000 trajectory checks and 288,302 converted parent-event marks,
  with zero mismatch.
- J-A/J-B: identical per-word impact marginals and fixed two-word event
  cardinality, but different joint pair association.
- Monte Carlo `F_A(J-B)-F_A(J-A)` is positive for all four scrub periods in the
  tested synthetic configuration, with all paired 95% intervals above zero.
- The declared L2 reconstruction and L3-U comparator exhibit both positive and
  negative signed error versus L1; no general conservatism direction is admitted.

All statements remain limited to the declared synthetic configurations and
representation rules.

## Unverified analytical precheck for J-A/J-B

This section records an Orchestrator algebra check for independent Scientific
Reviewer verification; it is not yet an accepted result.

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

with J-A and J-B attaining the endpoints. This statement requires all of the
following: four equivalent words, `t_c=1`, every parent event affects exactly two
distinct words, identical word marginals `1/2`, clean start, fresh monotone
within-word error accumulation, HPP parent arrivals, periodic synchronous full
reset and equal scrub intervals. It is not a bound for arbitrary physical SRAM
topologies, event cardinalities, repeat-hit semantics, non-Poisson arrivals or
partial/asynchronous restoration.

## Structural feasibility versus confidence-rule feasibility

The committed decision table uses a Wilson-upper-bound rule. Exact analytical
feasibility under `F_A<=epsilon` must be reported separately:

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
also pending Scientific Reviewer verification.

## Required Scientific Reviewer disposition

The Reviewer must independently:

1. reproduce the implementation tests and selected aggregates;
2. verify fairness of common inputs and the J-A/J-B invariants;
3. prove, correct or reject the `q`, `S(q,m)` and identified-set derivation;
4. state every assumption required for endpoint attainment;
5. distinguish exact/model, estimated/Wilson and robust-over-set feasibility for
   every candidate scrub period;
6. verify the paired-interval construction and precision interpretation;
7. assess whether L2/L3-U conclusions stay within their declared reconstruction
   rules and synthetic domains;
8. return `PASS`, `PASS WITH MINOR ISSUES`, `REVISE` or `BLOCK` with severities.

Only after a passing scientific review may a narrowly scoped `RES-001` candidate
be proposed. No retroactive hypothesis is permitted.
