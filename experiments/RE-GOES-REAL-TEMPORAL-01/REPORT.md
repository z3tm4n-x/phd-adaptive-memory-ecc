# RE-GOES-REAL-TEMPORAL-01 — current report after numerical repair

## Status

Historical implementation `bb900279876bad4a370589871eaa07a1d6ecd1ad` received Scientific Review 01 = `REVISE` at `bf34676d7842e6f843a716941178c695855bbf75` because the exhaustive numerical `g` map could merge/drop close transition roots and could serialize root enclosures without preserving their sign change.

`RE-GOES-REAL-TEMPORAL-NUMERICAL-REPAIR-01` corrects that numerical layer only. The accepted scientific contract and pre-control selected windows are unchanged. Full details are in `REPAIR_REPORT.md`. Research Engineer did not assign Scientific Review PASS. Scientific Review 02 at `63e189904a261124d219912bee27dd92267bb445` subsequently returned **PASS_WITH_MINOR**, closing MAJOR-01 and original MINOR-01...03. Orchestrator accepts the repaired package within Review 02 section 7's domain. The remaining diagnostic-label MINOR is closed by the explicit interpretation correction below, without changing calculations or outputs.

## Corrected map

- **14,781** resolved open policy regions;
- **14,061** decision-boundary rows = 12,869 certificate/selection enclosures + 1,192 exact model/replay-threshold enclosures;
- **2,632** explicit `g=0/1` and threshold-equality point records;
- **0** unresolved root/threshold clusters;
- **46,336** aligned resource rows, including 22,880 explicit `BOUNDARY-ENCLOSURE` rows excluded from saving/retention claims.

The mandatory SR control `LOWER_MEDIAN/d3/epsilon=0.1/L=0/g=0.6936659869408` is corrected from the historical false 75-pass map value to **90 passes**.

Every model/replay compatibility threshold is now represented by its exact rational numerator/denominator plus an outward Decimal enclosure; a rounded `g_min` display is never used as the certified boundary. Equality belongs to the compatible side under `<=`.

## Principal findings retained

For complete-reference baseline-certified cells at `g=1`, positive `Precomputed -> Delayed` saving remains **13/25** at `L=0` and **0/25** at `L=300,900,1800`.

`MAX_MEAN` retains no positive replay-compatible saving in any baseline-certified case.

`MAX_INCREASE/d3/epsilon=0.01/L=300/g=0.35` remains **2100/1200/900** passes for Precomputed/Delayed/Ideal. Its repaired selected-continuation threshold is enclosed at approximately `0.400402024122230256 +/- 1e-18`.

For complete-reference windows, positive saving exists for some replay-compatible `g` in **18/25, 13/25, 10/25, 10/25** baseline-certified cells for `L=0,300,900,1800`. `EARLIEST_INVALID` is kept separate: only compatible-completion stress is available; factual Ideal replay cost and retention remain `NA`.

Across the 576 compact summary cells, the historical boolean conclusions about existence of saving and certifiability gain are unchanged. All 100 complete-reference `g=1` action/pass rows are unchanged; one retention decimal differs only in the final `1e-16` serialization digit while its defining integer pass counts are unchanged.

## Verification

The repair includes an independent reset-timestamp exposure/Q oracle and an independent all-competitor selector. Final checks give:

- 7/7 SR MAJOR-01 witness regressions PASS;
- 12,869/12,869 serialized certificate brackets independently sign-enclose their root;
- 14,781/14,781 resolved representatives match independent all-competitor selection;
- 2,632/2,632 explicit point/threshold semantics agree with exact rational reconstruction;
- complete `g` coverage with explicit boundary bands;
- policy/resource alignment over 46,336 rows PASS;
- all eight numerical-repair test groups PASS.

See `REPAIR_REPORT.md`, `repair_verification.json`, `repair_regression_witnesses.csv`, `run_manifest.json` and `test_output.txt`.

## Interpretation boundary

The analytical upper-envelope result, accepted `Q` certificate, causal timing, no-free-reset semantics and conservative planning rule are unchanged. This remains a bounded hypothetical external-information comparator, not an operational GOES-fed controller architecture. The repair establishes numerical map correctness within the accepted model; it does not establish physical `B_d/g`, exact `F_A`, acquisition cost, spatial equivalence or net information benefit.

## Orchestrator closeout — Review 02

[Scientific Review 02](../../docs/scientific_reviews/GOES_REAL_TEMPORAL_REVIEW_02.md) independently checked all seven witnesses through regenerated-map lookup, both endpoints of all 14,781 resolved policy regions with the monotonicity/rank argument, all 12,869 certificate enclosures using exact rational signs, all 2,632 point records and full resource-interval containment. The repair is **ACCEPTED WITH THE DOCUMENTED MAP DOMAIN**; the numerical repair/re-review gate is complete.

An open-row claim requires g strictly inside its full-precision endpoints. Boundary enclosures, conservatively including their endpoints, are excluded from direct action/saving lookup unless an explicit point record or independently verified query resolves the input. Certificate-root equality means the exact root identified by its witness equation and enclosure, not a printed approximation. Zero unresolved clusters does not turn these tables into a total exact-g query service. A joined selected-policy region need not have an invariant full feasible set.

### MINOR-R2-01 — closed by relabelling, not recomputation

The two legacy fields below retain their machine keys and numerical bytes for reproduction compatibility. Their **controlling display labels and meanings** are corrected here and next to their export in summarize_results.py:

| Legacy CSV field | Correct display label / meaning |
|---|---|
| verified_boundary_enclosure_component_count_in_replay_domain | Boundary-enclosure component count selected by representative compatibility |
| verified_boundary_enclosure_total_g_width_in_replay_domain | Total boundary-enclosure g-width selected by representative compatibility |

The summarizer selects whole resource bands by their representative replay_compatible flag and counts adjacent components / sums full widths. These are **not** geometric counts or widths after clipping to the exact replay-compatible domain. Do not use the legacy suffix in_replay_domain as a geometric claim. The flag is not a universal compatibility statement inside a threshold-straddling band. Exact membership remains governed by the rational replay threshold.

Review 02's example therefore remains 7.2e-17 for the representative-selected diagnostic; approximately 7.3e-17 refers to a different, clipped-intersection diagnostic. Neither is probability mass, a scenario weight or an uncertainty probability. No new clipped widths are calculated or claimed by this closeout.

This uses the reviewer's explicitly permitted relabelling alternative. Scientific CSV files, map generation, selection, certificates, savings, retention, execution manifests and their historical identities are unchanged. Only report wording and source comments change; no production rerun or further Scientific Review is required.

### Accepted substantive interpretation

For the declared finite-decimal, known-rho=0, SEC/R2-U model with one replan, the greatest sequence in nonempty M(I) is attainable and maximizes the monotone sufficient certificate Q without an envelope relaxation gap. This is not exact F_A. In the controlled chronological replay, the usefulness of delayed external information depends jointly on its delay and the declared variation prior: the accepted g=1 counts, negative MAX_MEAN result and 2100/1200/900 example above remain supported. Compatibility of a retained section with a chosen g is a retrospective check, not independent validation of a future variation guarantee.

Completion does not register a permanent RES, assert novelty, authorize a new experiment, establish an operational GOES channel or demonstrate net savings after information/controller costs.
