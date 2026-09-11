# INFORMATION CONTRACT REPAIR — RE-FIXED-ADAPTIVE-FEASIBILITY-01

The runtime controller is causal, but its tuning is not calibration-free.

## Offline design constants

The following are fixed offline design quantities in this experiment:

- the scalar SRAM error-rate figure `7.3e-7 errors/bit-day`, transferred to all 39 protected physical bits;
- retrospective `mean_old_per_hour` used to normalize the old five-year temporal shape;
- retrospective `max_old_per_hour` used as the calibrated peak/fallback rate;
- retrospective `lag1_eta` used to select the controller coefficient;
- the resulting `C=0.03560929815993128`.

`mean_old_per_hour`, `max_old_per_hour` and `lag1_eta` come from the same retrospective 2021--2025 project series. They are not runtime measurements, not an independent future qualification envelope, and were not validated on a held-out future environment in this experiment.

Therefore the supported scope is **causal execution conditional on a retrospectively calibrated/transferred environmental shape**, not prospective validation that the tuning transfers to an unseen mission.

## Runtime information

For hour `h>=1`, the action uses only the scalar estimate for the completed previous hour. The comparator assumes that value is available at the next hourly decision boundary. Additional operational publication/delivery latency is not established; positive extra latency is outside this experiment.

No current-hour or future-hour rate is supplied to the controller.

### First hour

Two cases are explicit.

**Warm start:** a valid completed pre-`t0` hour scalar is already available. The nominal 0.142447% resource lower edge belongs to this case.

**Cold start:** no valid pre-`t0` scalar is available. The first hour uses the calibrated peak-rate fallback. `nu0_old_per_hour` is not treated as runtime knowledge of the first hour.

### Missing later input

If the previous-hour scalar is unavailable, the next hour uses the calibrated peak-rate fallback.

That fallback is conditional on the transferred calibration envelope. This experiment does not independently establish that a future physical rate cannot exceed the retrospective calibrated maximum.

## Meaning of “causal”

Causal means only that a decision does not use samples after its information boundary. It does not imply that `C`, the historical maximum or `lag1_eta` were selected independently of the verification time series, that they transfer out of sample, or that a practical feed has zero additional latency.
