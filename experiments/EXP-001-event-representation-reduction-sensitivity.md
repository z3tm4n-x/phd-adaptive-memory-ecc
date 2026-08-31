# EXP-001 — Event-representation reduction sensitivity

**Status:** `IMPLEMENTED / ORCHESTRATOR TECHNICAL ACCEPTANCE / SCIENTIFIC REVIEW PENDING`<br>
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

The implementation passed Orchestrator-level technical acceptance, including an
independent Linux rerun whose scientific aggregate, decision, delta and invariant
files were byte-identical to the committed Windows outputs. Scientific
interpretation and any `RES-xxx` remain pending adversarial Scientific Reviewer
review; see `experiments/manifests/EXP-001/orchestrator-disposition.md`.

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
2. **Lossless-interface check.** For identical event traces, verify exact state/event equivalence of `L0` and `L1` for every deterministic test and then under randomized streams.
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
