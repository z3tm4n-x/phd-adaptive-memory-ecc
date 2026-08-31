# EXP-001 — Event-representation reduction sensitivity

**Status:** `IMPLEMENTED / INDEPENDENT VALIDATION PASS / SCIENTIFIC REVIEW PASS / PROMOTION CANDIDATE`<br>
**Registered:** 2026-08-28<br>
**Authorization:** [DEC-003](../docs/decisions/DEC-003-rq002-bounded-model-family-and-exp001.md)

## Objective

Quantify how successive reductions of one radiation event from full physical topology through `W` to joint, marginal and scalar representations change:

1. DEC-001 `F_A(t0,T;μ_t0)` under accumulation and periodic scrubbing; and
2. a parameterized restoration-regime decision made from that reliability assessment.

The experiment is intended to determine exactness, bounds, approximation error and decision sensitivity. It does not assume that richer information is always useful or that a reduced model is inadequate.

## Related RQ/HYP

- RQ-001 — event/metric/domain/horizon contract;
- RQ-002 — arrival/event/state representation;
- RQ-006 — mapping `W` and representation sufficiency;
- RQ-003/RQ-004 — future interface checks only;
- HYP: none registered at planning time.

## Code commit

Research Engineer implementation commit:
`84728d1b5768e7c91c508495d696c5980943ae57`. Configuration, code and environment
identities are fixed in `experiments/manifests/EXP-001/run-manifest.json`.

The implementation passed Orchestrator-level reproducibility checks, including an
independent Linux rerun whose scientific aggregate, decision, delta and invariant
files were byte-identical to the committed Windows outputs. The accepted
[Scientific Review 01](../docs/scientific_reviews/EXP-001_SCIENTIFIC_REVIEW_01.md)
returned `REVISE`: the analytical J-A/J-B result survived, but the production L0
and L1 checks share mapping and state-transition code and therefore do not
independently validate L0→L1 losslessness. Any `RES-xxx` remains blocked pending
the bounded validation repair and passing re-review; see
`experiments/manifests/EXP-001/orchestrator-disposition.md`.

Validation-repair commit
`072b70adabb9827ee59c94b2b3d5cf044b25cdf9` is accepted at Orchestrator level.
It adds the independent test-only oracle, full-trace and mutation checks and the
four required MINOR corrections without changing the fixed configurations or
seven scientific output files. The bounded
[Scientific Review 02](../docs/scientific_reviews/EXP-001_SCIENTIFIC_REREVIEW_02.md)
returns `PASS`, closes all five original findings and reports no new issue or
scientific regression. The corrective gate is closed. The prepared
[`DRAFT-RES-001`](../docs/result_candidates/DRAFT-RES-001-exp001-four-word-identified-set.md)
still requires explicit PI wording approval before permanent registration.

## Configuration

The Research Engineer must create versioned config files under `simulation/configs/EXP-001/`. At minimum they must declare:

- `A`: word count/partition and bits per word;
- `W`: deterministic physical-cell-to-word mapping, with named no-interleaving and interleaved synthetic variants;
- ECC capability `t_c(w)` without DUE/SDC reinterpretation;
- event topology/multiplicity distribution and parent-event mark;
- temporal arrival scenario and intensity parameters;
- physical bit-update semantics, including repeat-hit/toggle treatment;
- initial state or `μ_t0`;
- scrub schedule, correction/writeback/reset transition and reporting window;
- representation level `L0`, `L1`, `L2` or the Phase-1 scalar comparator `L3-U`;
- for every `L2` run, the reconstruction/dependence rule and every parameter not contained in the marginals;
- for `L3-U`, the primitive object, intensity units, calibration target and bit/word allocation rule;
- candidate scrub periods and parameterized `ε` grid;
- seeds, run count and statistical precision rule.

No numerical value in the initial config is a project reliability requirement or a device parameter unless separately sourced.

## Input data / provenance

Phase 1 uses synthetic, fully declared inputs only. The event stream is generated once per seed and reused across representation levels whenever coupling is mathematically valid. Russian normative documents, COSRAD data and device test records are not calibration inputs for Phase 1.

Later target-specific configurations require separate provenance and are outside this first run.

## Random seeds

Fixed deterministic batch-seed lists and trials per seed are declared in the
versioned Phase-1 configs and copied into the run manifest. Common random numbers
are used across `L0`, `L1`, `L2` and `L3-U` only where the config declares a valid
coupling. One seed is not treated as statistical evidence.

## Baselines / representation levels

| Level | Representation | Required behavior |
|---|---|---|
| `L0` | full physical topology + explicit `W` | event-driven reference |
| `L1` | joint post-`W` codeword-impact mark with parent provenance | must reproduce the `L0` state update exactly for the same events |
| `L2` | marginal per-word multiplicities plus declared reconstruction/dependence rule | tested reduction; no assumed bias direction |
| `L3-U` | scalar ungrouped bit/upset-arrival intensity over `A` | required Phase-1 coarse comparator; individual upsets are the primitive objects and parent-event grouping is discarded |
| `L3-E` | scalar parent-event-arrival intensity with no impact mark | deferred from Phase 1; it is a distinct primitive and would require a separately declared event-to-state reconstruction before use |

Optional source-inspired low-`β` or occupancy formulas may be added only as separately labelled comparators with their source assumptions; they are not reference truth.

`L3-U` and `L3-E` must never be treated as interchangeable. Converting a
parent-event intensity into an upset intensity using expected event multiplicity is
permitted only as an explicitly declared first-moment calibration under stated
assumptions; it does not make the two arrival processes or their reliability
consequences equivalent.

## Mandatory joint-sufficiency discriminator

EXP-001 must include at least one controlled pair of joint post-`W` models,
`J-A` and `J-B`, satisfying all of the following by construction:

- identical parent-arrival process and arrival epochs;
- identical `A`, ECC capability, initial state, reporting window, scrub transition and candidate restoration regimes;
- identical per-word marginal multiplicity distributions for every named word class;
- identical distribution of the total number of impacted words per parent event, so that this quantity is not a confounder;
- different joint inter-word dependence / parent-event association and no other intentional difference.

A minimum admissible synthetic construction uses four otherwise equivalent words and
one new erroneous bit in each selected word per parent event. `J-A` selects
`{w1,w2}` or `{w3,w4}` with equal probability; `J-B` selects uniformly among all six
two-word subsets. Both models then give every word impact probability `1/2` per
parent event and exactly two impacted words per event, while their joint
association differs. The within-word update and repeat-hit semantics must be identical
and explicit; an equivalent construction is allowed only if these invariants are
machine-checked.

For this pair, compute and compare the `L1` reference `F_A` values and the
parameterized restoration decisions. Also show that the derived `L2` marginal input is
identical for the pair, then evaluate each declared `L2` reconstruction consistently.
No sign or materiality of the joint-dependence effect is assumed.

## Metrics

- `F_A(t0,T;μ_t0)` and confidence interval for each configuration;
- absolute and relative error against `L0/L1`;
- paired trajectory/event disagreement where common event streams are available;
- exact invariant checks for the `J-A`/`J-B` marginals and all controlled quantities;
- `ΔF_A` and restoration-decision discrepancy between `J-A` and `J-B` under otherwise identical conditions;
- false-safe classification over the swept `ε`: reduced model reports feasible while reference is infeasible;
- false-conservative classification: reduced model reports infeasible while reference is feasible;
- feasible set of candidate `T_scrub` values under each representation;
- difference in maximal feasible `T_scrub` or an explicitly declared alternative decision rule;
- scrub-operation count as an experiment-local resource proxy, reported separately from reliability;
- runtime and memory use for computational-feasibility comparison.

## Procedure

1. **Deterministic unit cases.** Construct single-event and two-event traces with known post-`W` word states, repeat hits, immediate capability exceedance and accumulation across a scrub boundary.
2. **Lossless-interface check.** For identical physical-event traces, validate the production L0 and L1 paths separately against a test-only independent physical-event oracle that does not reuse production mapping conversion or state-transition helpers. Compare complete transition traces for deterministic cases and bounded randomized streams under both declared `W` variants, and include a mutation/sentinel case that the oracle must reject.
3. **Joint-sufficiency discriminator.** Run the mandatory `J-A`/`J-B` controlled pair, verify its identical marginals and other invariants, and compare both `F_A` and the parameterized restoration decision. Treat a difference as evidence about joint-dependence relevance only for the tested model pair/domain; treat equality as invariance only for that domain.
4. **Representation comparison.** Compare each declared `L2` reconstruction and `L3-U` with `L0/L1` across single-cell, compact multi-cell and spatially separated event classes and at least two `W` variants. Keep `L3-E` deferred in Phase 1.
5. **Temporal sensitivity.** Repeat the comparison under one constant-rate marked HPP scenario and one explicitly synthetic deterministic time-varying intensity/NHPP scenario. Do not infer empirical adequacy of either family.
6. **Initial-state and scrub sensitivity.** Include a clean initial state and at least one declared non-clean `μ_t0`; sweep candidate scrub periods under one explicit periodic scrub transition.
7. **Decision comparison.** Sweep `ε`, compute feasible scrub-period sets and record false-safe/false-conservative and selected-period discrepancies.
8. **Robustness and cost.** Report precision, seed sensitivity, runtime and memory scaling. Keep raw outputs outside Git; commit configs, manifests, tests and bounded aggregate tables.

## Expected falsification / acceptance criterion

The experiment implementation is invalid if `L0` and `L1` disagree for the same physical event stream under the declared state semantics. Such a disagreement means the proposed joint post-`W` mark is not lossless or the implementation is incorrect.

For `L2` and `L3-U`, no preferred result is specified. A valid result may show exact agreement in a restricted domain, a conservative/non-conservative bound, measurable error, or control-decision invariance/change. Every result must state the tested domain and uncertainty.

Failure of one `L2` reconstruction rule supports a conclusion only about that rule and
tested domain. It must not be reported as universal insufficiency of all marginal
per-word statistics. If the controlled `J-A`/`J-B` pair has different reference
outcomes despite identical marginals, the admissible conclusion is narrower: the
declared marginal summary alone does not identify `F_A` or the restoration decision
over that tested pair/model class. If the outcomes agree, no general sufficiency claim
follows.

The first `RES-xxx` may be proposed only after:

- deterministic tests pass;
- statistical precision is met;
- the Scientific Reviewer checks the configuration, fairness of common inputs and interpretation;
- the statement is limited to the tested representations and validity domain.

## Scientific Review 01 disposition and corrective gate

The accepted review has recommendation `REVISE`, no `CRITICAL` finding, one
`MAJOR` and four `MINOR` findings.

- The pair-probability parameterization, `1/6 <= q <= 1/2`, the exact
  `S(q,m)`/reporting-window `F_A`, endpoint attainment and identified-set
  interpretation are accepted only under the complete fourteen-condition domain
  in Scientific Review 01 Section 7.4.
- The 768,000 production L0/L1 comparisons are outcome/final-signature checks,
  not independent full-trajectory validation.
- `MAJOR-01` requires an independent test-only L0 oracle, full-trace comparisons
  and a mutation/sentinel test before the experiment can pass.
- The four `MINOR` corrections require the complete theorem assumptions,
  pointwise rather than simultaneous confidence wording, explicit validation of
  analytical preconditions and deterministic/precision-linked analytical checks.
- The fixed experiment must be rerun after repair and its seven scientific
  aggregate/decision/delta/invariant files must remain unchanged unless a
  documented defect is found.

The analytical endpoint/identified-set statement and every exact decision made
from it require all fourteen conditions below; citing only a subset is not an
admissible EXP-001 result statement:

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

The Wilson and paired-normal intervals in the fixed tables are pointwise 95%
intervals. Decisions based on their upper endpoints are pointwise-interval-based
decisions, not simultaneous or selection-valid confidence guarantees over the
period/model grid.

After those checks, a Scientific Reviewer re-review is limited to closure of the
listed findings and regression detection. No target-device extension, new
literature cycle, retroactive `HYP-xxx` or redesigned scientific question is part
of this repair.

## Scientific Review 02 disposition

Scientific Review 02 returns `PASS`:

- `MAJOR-01` and `MINOR-01…04` are closed;
- no new `CRITICAL`, `MAJOR`, `MINOR` or required `OPTIONAL` issue is present;
- the analytical parameterization, `1/6 <= q <= 1/2`, exact `S(q,m)` and
  reporting-window `F_A`, endpoint attainment and identified-set interpretation
  remain accepted only within the complete fourteen-condition domain above;
- representation uncertainty, Monte Carlo estimation uncertainty and
  confidence-rule conservatism remain separate;
- a narrow first result is scientifically admissible but not automatically
  promoted.

The PI accepts the review disposition and closes the EXP-001 corrective gate.
No permanent `RES-001` exists until the bounded candidate wording is explicitly
approved.

## Output locations

- implementation: `simulation/src/`;
- tests: `simulation/tests/`;
- configs: `simulation/configs/EXP-001/`;
- run manifests: `experiments/manifests/EXP-001/`;
- bounded aggregate outputs/figures after review: `results/` with a future `RES-xxx` link;
- large/raw outputs: local external path recorded in the manifest, not committed.

## Explicit non-claims

EXP-001 does not by itself establish:

- a target SRAM radiation model;
- the empirical correctness of HPP or NHPP;
- a deficiency in Russian normative practice;
- a final ECC/decoder outcome model;
- a numerical reliability requirement;
- the final resource-cost objective;
- universal sufficiency or insufficiency of marginal per-word statistics;
- equivalence of scalar parent-event and scalar bit/upset arrival primitives;
- novelty of the integrated adaptive-control method.
