# PAPER-011 — Chen et al. (2025): dynamic fault mitigation with fault injection and ML

**PAPER-ID:** `PAPER-011`<br>
**Candidate identity:** `CONTROL-S5`<br>
**Related RQ:** future integrated adaptive-control RQ; `RQ-004`; `RQ-005`<br>
**Classification recommendation:** `CORE`<br>
**Evidence status:** `ACCEPTED` full-text analytical card; candidate statements remain unaccepted claims<br>
**Exact full text used:** `Dynamic Fault Mitigation for Space Radiation Using Fault Injection(3).pdf`, 13 PDF pages / journal pp. 273–285, SHA-256 `1e7b1d2514bf401e4a765804aac8f5a51602514f7091e4bc6a6a4ff6d654d6d9`

## Bibliographic identity

Junchao Chen, Li Lu, Marko Andjelkovic, Fabian Luis Vargas, and Milos Krstic, “Dynamic Fault Mitigation for Space Radiation Using Fault Injection and Machine Learning,” *Journal of Electronic Testing*, vol. 41, pp. 273–285, 2025. DOI: `10.1007/s10836-025-06183-5`.

- `[SOURCE]` The journal first page records received 31 Aug. 2024, accepted 21 May 2025, and published online 12 Jun. 2025 (journal p. 273 / PDF p. 1).
- `[SOURCE]` The article explicitly identifies S3 and S4 as previous conference works [19,20] and describes itself as an extended and systematized framework (Sec. 2, journal p. 275 / PDF p. 3).

## Control and reliability extraction

| Field | Full-text extraction |
|---|---|
| Runtime observation vector | `[SOURCE]` Logged PBD faults/real-time fault observations feed prediction and schedule adjustment (Sec. 3.1 online-learning paragraph; Sec. 3.4; Fig. 7, journal pp. 277–281). The deployed predictor uses a sliding vector of the past six hourly SEU-rate values (Sec. 3.3, journal p. 278). `[UNKNOWN]` How PBD fault counts are converted into those six rate samples, including missed/uncorrected faults, is not specified. |
| Sampling period/history window | `[SOURCE]` One-hour rate samples; six-hour sliding input; target is the rate at `t+1` (Secs. 3.1 and 3.3, journal pp. 277–278). |
| Measurement / forecast / inferred state | `[SOURCE]` Historical flux and cross sections yield training/evaluation rates; runtime fault observations supply recent SEU-rate samples; linear regression forecasts the next hour; predicted intensity drives scrub scheduling (Figs. 2, 5; Secs. 3.1–3.4). `[INFERENCE]` S5 is hybrid end-to-end and forecast-driven at the action boundary. |
| Offline inputs | `[SOURCE]` GOES-SEM and ACE-SIS hourly flux, reconstructed spectra, 65-nm SRAM Weibull parameters, CREME96 HUP/PUP outputs, 36 SPEs / 5107 hours, and model training settings (Secs. 3.1–3.3; Table 1). |
| Online inputs | `[SOURCE]` Recent onboard fault/SEU-rate observations; alternatively, an incrementally trained online model may operate without pre-characterized cross sections (Sec. 3.1, journal p. 277). `[UNKNOWN]` The alternative is discussed, not evaluated in the reported experiments. |
| Controlled variable | `[SOURCE]` PBD scrub/wash timer and frequency (Sec. 3.4; Fig. 7, journal pp. 279–281). |
| Decision/update period | `[SOURCE]` Prediction target and environmental sampling are hourly; scheduling example acts over the next hour (Secs. 3.3 and 4.1, journal pp. 278, 281). `[UNKNOWN]` The controller's execution cadence within an hour is not separately specified. |
| Control law | `[SOURCE]` Choose `P`, use Table 2 to obtain maximum faults per wash, predict next-hour faults, and schedule washes so each interval stays below that count; 600/460 yields one wash every 30 minutes (Sec. 4.1, journal pp. 281–282). `[INFERENCE]` This is consistent with a ceiling ratio but the paper provides no explicit rounding equation. |
| Threshold / rounding / saturation | `[SOURCE]` Table 2 gives the same PBD mapping as S3: 99.99/99.9/99/95/90% to 143/460/1464/3307/4739 faults (journal p. 282). `[UNKNOWN]` No hysteresis, saturation, feasibility rule, or hard min/max exists. |
| Wash-frequency range | `[SOURCE]` With `P=99.9%`, Table 6 reports 2, 2–20, 20–200, and >200 washes/hour during SPE categories; non-SPE prose recommends about one wash per three hours (journal pp. 282–283). These are scenario-derived settings rather than controller limits. |
| Persistent controller/memory state | `[SOURCE]` Trained linear model, six-sample history, fault counter/log, wash timer, two memory copies, and per-byte parity (Secs. 3.3–3.4; Figs. 6–7). `[SOURCE]` Online-learning alternative accumulates operational logs and improves over time (Sec. 3.1). `[UNKNOWN]` Predictor initialization and unsuccessful-correction state are not formalized. |
| ECC and correction semantics | `[SOURCE]` PBD mirrors the memory, adds parity per byte, compares byte pairs, recomputes parity, corrects by copying a byte identified via valid parity, logs faults, and updates the schedule. Outcomes: NE, EDC, EDNC, ENDNC (Sec. 3.4; Figs. 6–7, journal pp. 279–281). `[SOURCE]` Other deterministic, bounded-latency ECCs are claimed architecturally compatible, but comparative evaluation is future work (journal p. 279). |
| Failure/reliability event | `[SOURCE]` The equation's event is at most one fault in every primary–redundant byte pair, ensuring accurate counting under the model (Sec. 4.1, journal p. 281). Tables 4/6 additionally use “Reliability (%)” and qualitative mitigation of accumulation (journal pp. 282–283). `[UNKNOWN]` No formal mission failure event or mapping from NE/EDC/EDNC/ENDNC to one probability is supplied. |
| Metric, units, horizon, aggregation | `[SOURCE]` `P` is dimensionless conditional probability over `F` faults between washes; rate is upsets·bit⁻¹·day⁻¹; counts are faults/hour; action is washes/hour; prediction horizon one hour; modeled PBD domain is 24 banks / 1,811,939,328 bits, while static comparison uses a 20-Mbit SRAM (Secs. 4.1–4.3). `[INFERENCE]` The paper uses two array aggregations without an explicit conversion narrative. |
| Accumulation model | `[SOURCE]` `F` distinct fault locations are treated combinatorially; a collision occurs when more than one fault occupies a primary–redundant byte pair between washes (Sec. 4.1). `[UNKNOWN]` Time-of-arrival, repeat hits, parent-event multiplicity, and persistent residuals are not in the equation. |
| Placement/independence | `[SOURCE]` RTL injection generates random fault bit addresses (Sec. 3.2, journal p. 278); the equation gives equal weight to `F`-subsets of `B·2n` positions (Sec. 4.1). `[INFERENCE]` No measured spatial correlation, MCU topology, `W`, or interleaving is preserved. |
| Reset/writeback semantics | `[SOURCE]` A successful wash copies the valid byte; writes compute and store parity in both copies (Sec. 3.4). `[UNKNOWN]` Scan duration, atomicity, counter reset, EDNC/ENDNC persistence, sequential word ages, and interruptions by regular access are not modeled. |
| Prediction uncertainty | `[SOURCE]` Five regressors, min-max normalization, 60/40 split, 10-fold cross-validation, `R²` and RMSE metrics; LSTM and linear regression report `R²=0.95/0.94`, and linear regression is deployed (Sec. 3.3, journal p. 278). `[UNKNOWN]` RMSE values, intervals, calibration, event-wise split, and uncertainty propagation to action are absent. |
| Resource costs | `[SOURCE]` Scrub count/frequency is measured or calculated: Table 4 compares total scrubs; annual estimates are 2920 for one scrub/3 h and about 3950 for dynamic operation. The paper asserts short/overlappable washes, negligible aggregate performance impact, moderate power overhead, and inherited 4% PBD area overhead (Secs. 3.4 and 4.3, journal pp. 279, 283). `[UNKNOWN]` No direct energy, traffic, latency, contention, controller-area, or power measurements validate those assertions. |
| Implementation boundary | `[SOURCE]` Software data processing/training uses Scikit-learn/Keras; fault injection is RTL/testbench; PBD's previous VHDL/LEON3 implementation is cited; hardware compatibility is argued but this paper does not report a complete deployed controller (Secs. 3.2–3.4). |
| Validation and baselines | `[SOURCE]` Historical data from all 36 Solar Cycle 24 SPEs; March 2012 plots; 65-nm SRAM cross sections; random RTL injection; five ML regressors; five CREME96 static policies; PBD mathematical analysis (Secs. 3–4). `[SOURCE]` The data-availability statement says no data are associated with the manuscript (journal p. 284). |

## 1. Research problem

- `[SOURCE]` Static radiation/fault-injection assumptions cannot tune mitigation efficiently for dynamic SPE conditions, and a deployable flow must combine environment data, prediction, injection, and mitigation (Introduction, journal pp. 273–275).

## 2. Objective

- `[SOURCE]` Integrate historical flux-driven fault injection with machine-learning-enhanced dynamic PBD scrubbing and evaluate it across historical solar events (Abstract; Secs. 1 and 3).

## 3. Studied system/model

- `[SOURCE]` A 65-nm Cypress SRAM sensitivity model, random-bit RTL fault injection, a six-hour-to-one-hour linear predictor, and a duplicated parity-per-byte memory scrub controller (Secs. 3–4).

## 4. Method

- `[SOURCE]` Reconstruct spectra, compute hourly SEU rates, train/test regressors, inject time-varying random faults, derive a collision threshold, and compare dynamic scheduling with five static models (Figs. 2–7; Tables 1–6).

## 5. Assumptions

- `[SOURCE]` One-hour resolution matches GOES/ACE-SIS sampling and is treated as adequate for variation tracking (Sec. 3.1).
- `[SOURCE]` Cross-section response is represented by Weibull parameters and CREME96 HUP/PUP (Table 1; Sec. 3.1).
- `[SOURCE]` Fault positions are random/equiprobable in the injection and collision model (Secs. 3.2 and 4.1).
- `[INFERENCE]` Forecast errors and spatially correlated MCU marks are assumed away at the decision interface rather than bounded.

## 6. Independent/input variables

- `[SOURCE]` Six previous hourly rates, `B,n,F`, chosen `P`, target cross-section parameters, historical flux sequence, ECC organization, and static-policy baseline (Secs. 3–4).

## 7. Dependent/output variables

- `[SOURCE]` Next-hour SEU rate/fault count, `R²`/RMSE, correct-count probability, allowable faults/wash, wash frequency/count, and reported reliability percentage (Secs. 3.3–4.3).

## 8. Baselines/comparators

- `[SOURCE]` Five regressors and five CREME96 static environment/scrub policies (Secs. 3.3 and 4.2).

## 9. Main equations/models

- `[SOURCE]` `P = C(B,F)(2n)^F / C(B·2n,F)` for collision-free placement over primary–redundant byte pairs (Sec. 4.1, journal p. 281).
- `[SOURCE]` Prediction is supervised mapping from six past hourly rates to rate at `t+1`; the linear coefficients are not published (Sec. 3.3, journal p. 278).

## 10. Main results

- `[SOURCE]` Linear regression is chosen at reported `R²=0.94` versus LSTM `0.95` (Sec. 3.3).
- `[SOURCE]` Table 4 reports 241 proposed scrubs with 100% “Reliability” for the March 2012 event, compared with 1008 Worst-Day and 3312 Peak-5-Minutes scrubs at 100% (journal p. 282).
- `[SOURCE]` The abstract reports up to 13× scrub-performance improvement; Sec. 4.3 estimates about 3950 dynamic scrubs/year versus 2920 for a fixed one-per-three-hours policy, while concentrating extra activity during bursts (journal pp. 273, 283).

## 11. Author-stated limitations

- `[SOURCE]` Online learning may have reduced accuracy early in a mission because little data have accumulated (Sec. 3.1, journal p. 277).
- `[SOURCE]` Comprehensive comparison of ECC choices, fine-grained refresh interleaving, energy-aware thresholds/throttling, refined ML, other environments/components, and FPGA platforms are future work (Secs. 3.4, 4.3, 5).
- `[SOURCE]` PBD has EDNC/ENDNC and collision-driven counting limitations (Sec. 4.1).

## 12. Methodological limitations inferred

- `[INFERENCE]` The controlled probability is a count-observability surrogate, not the DEC-001 reliability probability.
- `[INFERENCE]` The online-learning alternative is architectural discussion, not validated evidence.
- `[INFERENCE]` Fixed midpoint assumptions in annual scrub estimates and absent measured cost prevent a resource-optimality claim.

## 13. Threats to validity

- `[INFERENCE]` Temporal validation may be optimistic because event-wise separation of train/test folds is not reported.
- `[INFERENCE]` Spatial validity is limited by random independent bit addresses and absence of `W`/MCU marks.
- `[INFERENCE]` Construct validity is limited because “reliability,” “accuracy,” and correct counting are used at different levels.
- `[INFERENCE]` Reproducibility is limited by unpublished coefficients/RMSE and the statement that no data are associated with the manuscript.

## 14. What the paper actually demonstrates

- `[SOURCE]` S5 consolidates a time-series injection branch and a prediction-guided PBD branch and adds explicit predictor-window/training details plus broader scenario/resource-proxy summaries.
- `[SOURCE]` It evaluates the integrated flow on historical-derived rate sequences, not on a flight-deployed adaptive controller.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` S5 does not establish novelty over the full control literature, a formal reliability guarantee, MCU-aware reliability, an optimal/admissible control policy, or measured power/performance savings.
- `[INFERENCE]` Its statement that the framework is ECC-agnostic is architectural assertion, not validation across ECC semantics.

## 16. Relevance to this dissertation

- `[INFERENCE]` S5 is the strongest single close-prior-art source for the DEC-002 online-risk/adaptive-restoration interface and exposes concrete RQ-004 observables and RQ-005 scrub proxies.
- `[INFERENCE]` Its missing `W`, first-passage event, uncertainty propagation, and measurable cost vector delimit the comparison without establishing novelty.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` S5 uses a six-hour sliding SEU-rate history to predict the next hourly rate and applies the forecast to dynamic scrub scheduling (Sec. 3.3; Sec. 4.1, journal pp. 278, 281).
2. `[SOURCE-CANDIDATE]` S5's PBD threshold is the probability that `F` random fault locations occupy distinct primary–redundant byte pairs, enabling accurate counting (Sec. 4.1, journal p. 281).
3. `[SOURCE-CANDIDATE]` S5 explicitly consolidates earlier S3 and S4 branches while adding cross-validation, an online-learning alternative, ECC-agnostic discussion, and annual scrub estimates (Secs. 2–4.3).
4. `[INFERENCE-CANDIDATE]` S5 does not propagate forecast or measurement uncertainty into the control action.
5. `[INFERENCE-CANDIDATE]` S5's random-bit injection and collision equation do not preserve physical MCU provenance or mapping `W`.
6. `[INFERENCE-CANDIDATE]` S5's scrub-count reductions cannot be upgraded to energy/performance reductions without measurements.

## 18. Contradictions/tensions

- `[SOURCE]` S5 Table 4 reports proposed/Worst-Day/Peak-5-Minutes totals of 241/1008/3312 and the abstract says up to 13×; S4 reports 294/1152/4752 and up to 16× for the nominally same 144-hour March 2012 comparison. No reconciliation is supplied.
- `[SOURCE]` S5 calls Table 4's target a 99.99% “correction rate” although Table 2 derives 99.99% as correct-count probability under the PBD collision model (Secs. 4.1–4.2).
- `[INFERENCE]` The non-SPE one-wash/three-hours action extends beyond the one-hour prediction horizon without specifying forecast chaining or update behavior.

## 19. Open questions

1. `[UNKNOWN]` How are raw PBD observations transformed into the six hourly SEU-rate inputs in deployment?
2. `[UNKNOWN]` What event defines Table 4 “Reliability (%)” and how is 100% estimated with uncertainty?
3. `[UNKNOWN]` Why do S4 and S5 scrub totals and improvement factors differ?
4. `[UNKNOWN]` What hard timing/bandwidth/energy limits cap feasible wash frequency?
5. `[UNKNOWN]` How should forecast intervals and measurement classification error alter the control law?
6. `[UNKNOWN]` How are MCU event marks mapped by `W` into PBD byte-pair state?

## Relation to DEC-001 and DEC-002

- `[INFERENCE]` S5 covers test/environment inputs, a marginal device-rate representation, simulated ECC behavior, online forecast, and an adaptive action. It does not provide the joint post-`W` event/state model or first-passage calculation required between those blocks.
- `[INFERENCE]` Neither the PBD `P` nor Table 4 “Reliability” is `F_A(t0,T;μ_t0)`; no explicit `A`, `μ_t0`, or `E_cap` event is supplied.

## Equations/assumptions requiring reproduction

- Reproduce six-hour-to-`t+1` predictor evaluation with event-wise folds and publish coefficients, RMSE, residual distribution, and intervals.
- Reproduce `P` under uniform sampling without replacement and compare it with clustered/repeated-event alternatives.
- Reproduce Tables 4 and 6 from the hourly series and state rounding, update, saturation, and cost rules.

## Final disposition

- **Orchestrator disposition:** `ACCEPTED / CORE` for the consolidated close prior-art architecture and explicit control interface.
- **Next action:** bounded Evidence Auditor comparison using the canonical S3/S4/S5 matrix; no novelty or project-model decision follows from this card alone.
