# RE-GOES-REAL-TEMPORAL-NUMERICAL-REPAIR-01 — repair report

## Disposition

**Research Engineer corrective delivery: COMPLETE FOR ORCHESTRATOR INSPECTION AND MINIMAL SCIENTIFIC RE-REVIEW.**

Starting commit: `77f299bdc3f5abaac36e5d8ef79359f557e56065`. Historical implementation: `bb900279876bad4a370589871eaa07a1d6ecd1ad`. Scientific Review 01: `bf34676d7842e6f843a716941178c695855bbf75` (`REVISE`, MAJOR-01, no CRITICAL).

The repair changes only numerical boundary construction, equality/compatibility semantics, serialization, policy/resource alignment, tests, reproduction and reporting inside `experiments/RE-GOES-REAL-TEMPORAL-01/`. Frozen rates, selected windows, `rho=0`, SEC/R2-U model, `B_d`, `g in [0,1]`, `L`, epsilon grid, action grid `U`, horizon, reset semantics, comparator classes and planning/tie rule are unchanged. No transport/COSRAD, raw-data audit, Stage-A production matrices, Monte Carlo, estimator or literature work was run.

## MAJOR-01 repair

The historical map could drop/average close roots, accept a fast-selected action without mandatory all-competitor reselection after exact failure, merge narrow downstream resource cells, and serialize a certified bracket so that its written endpoints no longer enclosed the root.

The corrected implementation:

1. solves action-feasibility transitions on each affine-envelope segment with Decimal arithmetic;
2. does not merge distinct roots by distance; duplicate events are collapsed only when the underlying threshold equation is identical;
3. writes outward certificate/selection enclosures with ordinary width `2e-18` and recomputes signs from the serialized/re-read endpoints;
4. verifies each resolved open policy cell by independent all-competitor selection and exact `Q<=epsilon` semantics;
5. represents model-nonempty and replay-compatibility thresholds as exact rational numbers, with numerator/denominator plus outward Decimal enclosure; rounded display values never define certified partition boundaries;
6. separates resolved open cells, boundary-enclosure bands and explicit equality/end-point records; no saving/retention claim is assigned inside an enclosure band;
7. propagates boundary bands through resource alignment instead of discarding or proximity-merging narrow cells;
8. exports any unresolved ordering cluster as `UNRESOLVED`; the repaired run has zero such clusters.

Equality at exact model/replay or certificate threshold is owned by the feasible/compatible side under the accepted `<=` rule. `g=0`, `g=1` and threshold equalities are explicit point records rather than inherited from an adjacent open cell.

## Mandatory regression findings

For the SR control witness

`LOWER_MEDIAN / d3 / epsilon=0.1 / L=0 / g=0.6936659869408`

the corrected independent all-competitor path gives `tau1=5 s`, planned `tau2=5 s`, executed `tau2=10 s`, **90 passes**, `CERTIFIED`. The historical false 75-pass label is absent.

All six additional MAJOR-01 witnesses are corrected. The repaired 75-to-90 transition is enclosed by serialized endpoints around `0.693665986938542394...`; independent residual signs at the re-read endpoints have opposite sign. The historical serialization witness `LOWER_MEDIAN/d1/epsilon=0.01/Delayed/L=0` is also enclosed after serialization.

The final independent repair suite reports:

- all 7 MAJOR-01 witness regressions: PASS;
- `12,869/12,869` serialized certificate/selection brackets retain the required sign enclosure;
- `14,781/14,781` resolved policy representatives match independent all-competitor selection;
- all `2,632` explicit endpoint/equality/threshold points match independent exact-threshold reconstruction;
- no silent `g` coverage gaps: PASS;
- policy/resource alignment including boundary bands: PASS;
- retained `g=1`, `MAX_MEAN`, `MAX_INCREASE` and historical serialization regressions: PASS;
- `EARLIEST_INVALID` stress/NA semantics: PASS;
- **ALL 8 NUMERICAL-REPAIR TEST GROUPS PASS**.

The independent expected-value path enumerates reset timestamps, integrates two unit-rate basis functions across actual reset intervals including the crossing interval at 300 s, reconstructs the quadratic whole-window `Q`, rebuilds delivered/Ideal anchor sets and exact rational compatibility thresholds, and enumerates all 144 competitors. It shares the accepted config/input and SEC/R2-U semantics, but it does not call production `Q` or production selection helpers to obtain expected decisions. Saved production residual columns are not treated as independent evidence.

## Repaired map sizes

Historical row counts were not preserved artificially.

| object | historical | repaired |
|---|---:|---:|
| resolved policy regions | 14,667 | **14,781** |
| decision-boundary rows | 13,947 | **14,061** |
| certificate/selection enclosures | not separately reliable | **12,869** |
| model/replay-threshold enclosures | not separately exported | **1,192** |
| explicit endpoint/equality point records | not separate | **2,632** |
| unresolved regions | not explicit | **0** |
| aligned resource rows | 20,341 | **46,336** |
| aligned `BOUNDARY-ENCLOSURE` rows | not explicit | **22,880** |

Total `g` width of certificate/selection enclosures is `2.5738e-14`; model/replay threshold enclosures contribute `2.384e-15`. After Delayed/Ideal/resource alignment, boundary-enclosure rows occupy `4.5760e-14` total `g` width across section/case rows. None is counted as certified resource saving.

## Effect on substantive results

The independently supported principal conclusions are unchanged.

At `g=1`, among the 25 complete-reference baseline-certified cells, positive `Precomputed -> Delayed` saving remains **13/25** for `L=0` and **0/25** for `L=300/900/1800`.

`MAX_MEAN` still has no positive replay-compatible saving in any baseline-certified case.

For `MAX_INCREASE / d3 / epsilon=0.01 / L=300 / g=0.35`, the result remains **2100 / 1200 / 900 passes** for Precomputed / Delayed / Ideal. The selected-continuation transition near `g=0.40040202412223` remains inside the independently reviewed bracket; exact equality retains the 1200-pass continuation under `Q<=epsilon`.

Across all 576 compact section/case/latency rows, both boolean fields — existence of replay-compatible saving and existence of replay-compatible certifiability gain — are unchanged from the historical package. For complete-reference baseline-certified cells, saving exists for some replay-compatible `g` in `18/25`, `13/25`, `10/25`, `10/25` cases for `L=0,300,900,1800`. Missing-reference compatible-completion stress remains `5/5` at each latency and is reported separately.

All 100 complete-reference `g=1` rows retain the same Precomputed, Delayed and Ideal integer pass counts and pass differences. One printed retention value differs only in the last floating serialization digit (`...3077` versus `...3076`) while being computed from the same integer counts; this is not an action/resource change.

## MINOR-01…03

**MINOR-01:** complete-reference replay and `EARLIEST_INVALID` compatible-completion stress are separated. Missing-reference numerical values are labelled `ideal_compatible_completion_stress_passes`; factual `ideal_passes` and retention are blank/NA when exact replay is unavailable.

**MINOR-02:** `reproduce.sh` creates a fresh `mktemp -d` directory with cleanup trap. The compressed compact summary is decoded/decompressed and compared as scientific CSV bytes; gzip-container identity is not a scientific gate. The historical interrupted-wrapper note for `bb900279...` remains provenance only.

**MINOR-03:** the report/tests distinguish independent reset-time/all-competitor calculations from shared accepted inputs and production-output consistency checks. Reading stored residuals is not called independent verification.

## Reproduction

From repository root:

```bash
cd experiments/RE-GOES-REAL-TEMPORAL-01
./reproduce.sh
```

The final repair release wrapper completed end-to-end with exit code 0 using a fresh temporary directory. It regenerated the corrected maps, aligned resources and summaries, ran all eight repair-test groups, checked unchanged baseline decisions/resources, reproduced all transient scientific SHA-256 values, compared decompressed compact scientific CSV content, and cleaned its temporary directory.

Exact software reference is recorded in `run_manifest.json` (Python 3.13.5, NumPy 2.3.5, Pandas 2.2.3 on Linux for the recorded repair environment).

## Remaining limitations

Boundary-enclosure bands intentionally carry no certified resource-saving claim; an exact queried `g` at a boundary must use the explicit equality/point semantics. `EARLIEST_INVALID` still lacks a factual complete reference trajectory. All original physical/operational limitations remain: GOES is only chronological reference plus hypothetical external-channel signal content; no target-spacecraft delivery architecture, measured operational latency, physical `B_d/g`, exact `F_A`, full acquisition/net resource balance, global policy optimality or novelty is established.

Research Engineer does **not** assign Scientific Review PASS. The next gate is the authorized minimal Scientific Reviewer re-review of MAJOR-01 and local MINOR closure.
