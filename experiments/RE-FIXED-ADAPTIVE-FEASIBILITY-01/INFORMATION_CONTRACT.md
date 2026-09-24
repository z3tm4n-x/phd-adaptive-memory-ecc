# INFORMATION CONTRACT — POST-SR COLD-START DISPOSITION

Task: `RE-FIXED-ADAPTIVE-FEASIBILITY-01`.
Reviewed delivery: `03e6c4ad8570fa3351378c9c77b1f9c2fe943f15`.
Scientific Review: `619492db33cb8793710fb4e454616f543993c982`.

The overall Scientific Review verdict for the full delivery remains **REVISE**. Orchestrator selected the reviewer's limited-acceptance alternative that restricts the supported result to **cold start**. This document does not convert the full package to PASS and does not alter accepted RES artefacts.

## Correct provenance for lag1_eta

The retrospective `lag1_eta=1.04935369403` is sourced from:

- repository `z3tm4n-x/chapter4-risk-limited-scrubber`;
- ref `cf7ab706224f7872fdafcf34febda70e3f6c8dd1`;
- `results/schedules/ch3_five_year_summary.csv`, blob `7f64b1f6a7ba544c610325588ee26f7b10d03bb4`;
- row `delayed_1h`, field `eta_shape`.

The corresponding implementation is `scripts/run_ch3_five_year_schedule.py`, blob `10ea6f0911bf5782f5034a39d95e647f181480fc`:

- `delayed_estimate(values, delay_steps=1)` uses `values[max(0,index-delay_steps)]`;
- `eta_shape(nu_values, estimate_values, dt_hours)` computes `(integral nu_hat dt)*(integral nu^2/nu_hat dt)/(integral nu dt)^2` by the discrete hourly sums in that script.

The earlier pointer to `ch3_lag_sweep_summary.csv` is historical provenance only and is not the current source citation for `lag1_eta`.

## Offline design constants

The following remain retrospective offline design quantities for this experiment:

- scalar SRAM error-rate figure `7.3e-7 errors/bit-day`, transferred to all 39 protected physical bits;
- `mean_old_per_hour` and `max_old_per_hour` from the pinned 2021--2025 temporal profile;
- `lag1_eta=1.04935369403` from the source above;
- the already-fixed controller coefficient `C`.

The review did not establish out-of-sample transfer of these quantities to an unseen mission. The result remains conditional on the retrospectively calibrated/transferred temporal shape.

## Accepted runtime information contract

Only the **cold-start** contract is selected for limited acceptance:

1. At `t0`, no pre-`t0` completed-hour scalar is assumed available.
2. The first hour uses the calibrated peak-rate fallback.
3. For hour `h>=1`, a decision may use only the completed scalar estimate for the immediately preceding hour, assuming it is available at the hourly decision boundary.
4. If that previous-hour scalar is unavailable, the next hour uses the same calibrated peak-rate fallback.
5. The limited accepted case allows at most **148 additional fallback hours** after the first cold-start hour.
6. No current-hour or future-hour scalar is supplied to the controller.
7. Positive operational publication/delivery latency beyond the declared hourly boundary is not established.
8. The retrospective maximum is a calibration envelope in this model, not a qualified future physical ceiling.

## Warm-start status

The earlier warm-start rows in `outputs/budget_domains_repair.json`, `REPAIR_DISPOSITION.md` and related historical artefacts are preserved for provenance. They are **not certified for an arbitrary valid pre-t0 scalar** and are not part of the selected limited acceptance.

No further warm-start analysis is performed by this documentary release.

## Scientific scope

The selected result is an existence/feasibility result under the declared transferred-profile assumption and the cold-start/fallback information contract above. It is not prospective calibration, operational qualification of the environmental feed, proof of optimality, or proof that the simple controller is universally necessary across other ECC architectures.
