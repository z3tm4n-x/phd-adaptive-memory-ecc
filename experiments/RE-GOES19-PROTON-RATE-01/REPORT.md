# RE-GOES19-PROTON-RATE-01 — GOES-19 → RADAR → CY62167 bit-flip rate

## Disposition

**PARTIAL, but usable as a bounded Stage A physical-input interface.** The full 5-minute chain was completed for 0, 1, 2, 3, 5, 7 and 10 mm Al-equivalent. Units and solid angle are explicitly closed, GOES-19 is audited, the pinned RADAR transport is numerically validated, and East/West are retained separately. The result is not promoted to a single calibration-grade absolute truth because the device response itself requires extrapolation outside the experimental energy support; the 0-mm case additionally depends materially on the unmeasured 0.614–0.92 MeV environmental spectrum.

The task ends at `lambda_bit(t,d)`. No MCU/MBU, ECC, mapping W, failure probability, scrub period, or adaptive-control calculation is included.

## 1. GOES-19 audit

- Product: **GOES-19 SEISS/SGPS Level 2, 5-minute Flux Averages**, 2026-01-01T00:00:00+00:00 through 2026-02-28T23:55:00+00:00.
- Cadence: exactly **300 s**; 16,992 source timestamps.
- Product versions: algorithm 3.2 in 12 daily files and 3.3 in 47; boundary 2026-01-13. Energy metadata remain constant after the explicit P1–P5 correction, and no checked channel shows a boundary jump larger than its local p99 one-step variability.
- Paired-valid E/W intervals: **16,971 / 16,992 = 99.8764%**. 21 timestamps contain an invalid/missing direction and are not filled from neighboring times.
- Native differential-flux units are `protons/(cm^2 sr keV s)`; values are converted numerically to per-MeV by ×1000. Integral P11 remains `protons/(cm^2 sr s)` above 500 MeV.
- East and West are reconstructed from sensor/yaw metadata before any rate calculation.
- L2 fill/nonfinite values and unresolved yaw are hard-invalid. L2 DQF counters and the `IgnoredL1bDQFs` bitmask are retained as audit/warning metadata; valid L2 averages are not silently deleted merely because some contributing 1-s samples carried a threshold flag.
- The supplied files retain the legacy P1–P5 bounds. NOAA’s GOES-19 SGPS Provisional ReadMe publishes the revised bounds/geometric factors and multiplicative factors 0.656, 0.688, 0.708, 0.625, 0.618 and 0.753 and states that the corrected operational L2 replacement is pending. The adapter therefore applies those factors **exactly once** when legacy bounds are detected.

### Energy channels after the controlled P1–P5 correction

| channel | East lower–upper, MeV | East effective, MeV | West lower–upper, MeV | West effective, MeV |
|---|---:|---:|---:|---:|
| P1 | 0.92–1.8 | 1.2869 | 0.92–1.8 | 1.2869 |
| P2A | 1.8–2.2 | 1.99 | 1.8–2.2 | 1.99 |
| P2B | 2.2–3.2 | 2.6533 | 2.2–3.2 | 2.6533 |
| P3 | 3.3–6.2 | 4.5233 | 3.3–6.2 | 4.5233 |
| P4 | 6.3–11.7 | 8.5855 | 6.3–11.7 | 8.5855 |
| P5 | 12.4–23.3 | 16.998 | 12.4–23.3 | 16.998 |
| P6 | 25.9–35.2 | 30.194 | 25.9–35.2 | 30.194 |
| P7 | 41–74 | 55.082 | 41–74 | 55.082 |
| P8A | 78–99.7 | 88.185 | 83–100.7 | 91.423 |
| P8B | 97.9–120.3 | 108.52 | 98.6–120.6 | 109.05 |
| P8C | 114.6–136.1 | 124.89 | 113.4–142.4 | 127.08 |
| P9 | 150.7–225.1 | 184.18 | 155.2–231.5 | 189.55 |
| P10 | 267–390 | 322.69 | 267–390 | 322.69 |

## 2. GOES → RADAR → РД-174 unit contract

**PASS.** РД 134-0174-2009, eq. (6.6), defines the proton-event rate by energy convolution and explicitly defines `F_ВЭП(E)` in `(cm²·s·MeV)^−1` as the differential spectrum of an **isotropic** proton flux in the full solid angle `Ω=4π`. The supplied SGPS object is instead directional differential intensity `J(E)` with `sr^-1`.

Therefore each direction is handled as a separate isotropy-equivalent scenario:

`F_4π^E,W(E,t) = 4π J_E,W(E,t)`.

RADAR receives `cm^-2 s^-1 MeV^-1`, i.e. the `sr^-1` has already been removed exactly once. No `π`, `2π` or second `4π` factor is applied downstream. The final bit rate is

`lambda_bit = N_bits ∫ F_sh(E,t,d) sigma_bit(E) dE`,  `N_bits = 16,777,216`.

Dimensionally: `[bit] [cm^-2 s^-1 MeV^-1] [cm^2 bit^-1] [MeV] = s^-1`.

This does **not** mean that `(E+W)/2` is a measured omnidirectional spectrum. E and W remain separately reported; the arithmetic mean is only the declared central estimator after both complete chains are evaluated.

## 3. Continuous device-response interface `sigma_hat_bit(E)`

**Status: PARTIAL.** The Task-1 experimental points remain the primary object. The reference representation uses:

- log-log interpolation between positive experimental points;
- no synthetic 29-MeV point;
- a local linear continuation below 0.9 MeV through the 0.9 and 1.0 MeV experimental points, clipped at zero; the resulting zero crossing is **0.613982 MeV**;
- constant hold above the highest experimental point, rather than a Weibull/FLUKA substitution.

Sensitivity alternatives are `linear_energy`, `gap_linear_5_40`, and `low_hold`. They are not confidence intervals. Their spread is large for some shield thicknesses because Al transports surviving protons into the steep ~1-MeV response region. Median alternative-model range relative to the reference is about **93% at 1 mm**, **84% at 3 mm**, and **34% at 10 mm**. This is one of the dominant limitations of the absolute rate.

## 4. Environmental spectrum extrapolation

The corrected P1 support begins at 0.92 MeV, while the reference device-response continuation remains nonzero to ~0.614 MeV. For **d=0 only**, the missing environmental band is represented explicitly by

`J(E)=J_P1 (E/0.92 MeV)^(-gamma)`, with `gamma=0,2,4`.

`gamma=2` is the reproducible reference scenario, not a measured spectral index. At d=0 the median rates are **0.5079 / 0.5682 / 0.6591 s^-1** for gamma 0/2/4, compared with **0.3128 s^-1** from measured differential support alone. Thus the low-energy spectrum extrapolation is material at d=0.

For shields >=1 mm, incident protons in this sub-0.92-MeV band stop in Al on the selected transport grid, so the **environmental** low-energy extrapolation no longer contributes. Device-response extrapolation at low output energy can still matter and is retained in the sigma sensitivity.

The differential SGPS spectrum ends at P10 (390 MeV), while P11 measures integral flux above 500 MeV. The 390–500 MeV bridge is a power law constrained simultaneously by P10 and P11: its index is fitted per timestamp/direction from the P10 anchor and P11 integral when possible, with a direction-median fitted index used only when P10 is unusable. This bridge is labeled extrapolated, not measured. P11 >500 MeV is included analytically because the reference high-energy sigma is held constant.

## 5. Pinned RADAR shielding validation

**PASS.** Pinned commit: `b032505d4d1b15403b8ad06aef578339f6d1c6b4`.

- Existing proton-Al shielding tests: **21/21 PASS** in GitHub Actions.
- Production energy grid: **192 points**, 0.11–390 MeV.
- Direct convolution convergence 144→192: max relative change **0.302%**, below the 0.5% criterion.
- Secondary-depth integration convergence: max **0.0069%**.
- d=0 primary identity max absolute error: `2.998e-15`; d=0 secondary max: `0.000e+00`.
- Primary and secondary spectra are nonnegative.
- Monoenergetic CSDA peak-grid checks: max relative peak error **2.63%**.

The pinned compact TENDL nonelastic/secondary tables end at 200 MeV. No nuclear reaction model is invented above that limit. As a conservative diagnostic, holding the 200-MeV nonelastic cross section (0.36612 barn) constant would attenuate at most **2.18%** of an >200-MeV component through 10 mm Al; even at the 10-mm p99 >200-MeV rate fraction this corresponds to about **1.55% of the total rate**. This limitation is therefore retained but is not the leading uncertainty in this bounded study.

## 6. Five-minute `lambda_bit(t,d)`

### Reference central-estimator summary

| Al, mm | status | median, s^-1 | mean, s^-1 | p95 | p99 | max, s^-1 | max UTC | total expected bit flips |
|---:|---|---:|---:|---:|---:|---:|---|---:|
| 0 | PARTIAL_LOW_SPECTRUM_AND_SIGMA_EXTRAPOLATION | 0.5682 | 15.51 | 15.79 | 70.96 | 1.1033e+04 | 2026-01-19T19:30:00+00:00 | 7.8964e+07 |
| 1 | PARTIAL_SIGMA_EXTRAPOLATION | 1.0147e-04 | 0.07364 | 0.0108 | 0.3467 | 58.71 | 2026-01-19T19:20:00+00:00 | 3.7494e+05 |
| 2 | PARTIAL_SIGMA_EXTRAPOLATION | 6.0844e-05 | 0.01822 | 0.001963 | 0.09356 | 12.36 | 2026-01-19T19:20:00+00:00 | 9.2782e+04 |
| 3 | PARTIAL_SIGMA_EXTRAPOLATION | 2.8887e-05 | 0.009199 | 9.3267e-04 | 0.04986 | 6.125 | 2026-01-19T19:20:00+00:00 | 4.6837e+04 |
| 5 | PARTIAL_SIGMA_EXTRAPOLATION | 7.1682e-06 | 0.002486 | 2.0156e-04 | 0.01495 | 1.536 | 2026-01-19T19:15:00+00:00 | 1.2657e+04 |
| 7 | PARTIAL_SIGMA_EXTRAPOLATION | 6.7420e-06 | 0.001426 | 1.1687e-04 | 0.008713 | 0.8755 | 2026-01-19T19:15:00+00:00 | 7261 |
| 10 | PARTIAL_SIGMA_EXTRAPOLATION | 6.1578e-06 | 5.3074e-04 | 4.6217e-05 | 0.003323 | 0.3181 | 2026-01-19T19:15:00+00:00 | 2702 |

`proton_rate_5min.csv` also reports, for each shielding thickness, `lambda_E`, `lambda_W`, the central estimate, `lambda_h = 3600 lambda`, `m5 = 300 lambda`, and the central primary/secondary decomposition. `m5` is an expected number of flipped bits in a 5-minute interval; it is **not** a probability of an event or failure.

### Physical structure

- The dominant maximum occurs on **2026-01-19**. Dynamic ranges are ~2×10^4 at 0 mm and ~5×10^4–6×10^5 for shielded cases, so real time variability spans far more than calibration/directional uncertainty.
- Shielding strongly decreases the absolute reference rate over this grid; no increase of total `lambda_bit` with added Al is observed in the selected 0–10 mm points.
- Nevertheless, the hypothesized spectral-translation effect is real in the calculation: the **0.8–1.2 MeV output band contributes ~66% of the mean reference rate at 1 mm, ~65% at 2 mm, ~60% at 3 mm**, and remains ~27% at 10 mm. Around p99 the fraction is ~69% across most shielded cases. Thus Al degradation does move a major part of the surviving response weight into the ~1-MeV high-sensitivity region, even though the reduction in transmitted flux dominates and total rate falls.
- Secondary protons are numerically small in this RADAR configuration: mean contribution rises from ~0.010% at 1 mm to ~0.041% at 10 mm, with maxima below 0.3%. Primary-only is therefore already an excellent approximation for this specific screening, but the secondary layer is retained.

### East/West and calibration uncertainty

E/W disagreement is not negligible: the median relative E/W discrepancy is roughly 26–72% depending on shielding, with larger upper quantiles. The L2 uncertainty-envelope median half-width is roughly 42–56%. Both are important for absolute normalization, but they remain tiny compared with the multi-order-of-magnitude temporal excursion between background and the January event. The central `(E+W)/2` series is therefore useful as a screening estimator only because the two directional chains remain available alongside it.

NOAA also warns that provisional SGPS P1–P9 background outside SEP events can be higher than the actual GCR proton flux, P5 may have electron contamination, and P8C cross-calibration can be high. Consequently the quiet-time baseline should not be interpreted with the same confidence as event-time changes.

## Answers to the six required questions

1. **GOES → RADAR → РД-174 units/solid angle:** **PASS.** The dimensional interface is closed explicitly. `4π` is applied exactly once, after E/W separation, to construct direction-specific isotropy-equivalent full-solid-angle fluxes required by РД-174. The central mean is not called an omnidirectional measurement.
2. **Chosen `sigma_hat_bit(E)` and interpolation sensitivity:** reference = log-log between experimental points, local linear low-energy continuation to zero, constant high-energy hold; **interface PARTIAL**. Interpolation/extrapolation sensitivity is material and can be of order unity in shielded cases.
3. **Five-minute `lambda_bit(t)` across shielding:** calculated and released for all seven thicknesses. The series is strongly nonstationary; shielding lowers the total reference rate by many orders at typical times.
4. **Secondary protons:** small for this screening (<~0.3% maximum rate fraction in the released grid). They do not drive the result.
5. **East/West and calibration vs temporal variability:** E/W and L2 uncertainties are large enough to matter for absolute normalization, but actual temporal variability is far larger. Quiet-time SGPS background systematics are an additional limitation.
6. **Usability for next Stage A:** **YES, as a bounded/sensitivity-aware physical input, not as a single calibration-grade absolute truth.** Stage A should ingest the reference series together with the E/W chains and sigma/environment sensitivity metadata. It must not treat d=0 gamma=2 or the low-energy sigma continuation as measured facts.

## Final interface status

- `GOES→RD174 unit contract`: **PASS**
- `sigma(E) interface`: **PARTIAL**
- `RADAR shielding`: **PASS**
- `lambda_bit(t,d)`: **PARTIAL**

## Reproducibility

### Controlled-input drift check

A final comparison against the current NOAA public archive on 2026-09-02 found that **52 of the 59** daily public files still match the PI-controlled SHA-256 values byte-for-byte. Seven consecutive files, `20260114` through `20260120` (all `v3-0-3`), have since been replaced or rewritten in the public archive and no longer match the controlled copies. The calculations in this task remain tied to the PI-provided archive and its hashes; the later public revisions are not silently substituted. This is a provenance difference, not evidence that the controlled calculation should be retroactively changed.

Large raw GOES NetCDF files and the transport/spectrum arrays are not committed. Exact input hashes are in `input_manifest.json`; transport is regenerated from the pinned RADAR SHA. The committed full 5-minute rate table is deterministic from those inputs and the task code.
