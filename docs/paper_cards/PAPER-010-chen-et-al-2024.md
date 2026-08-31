# PAPER-010 — Chen et al. (2024): flux-driven fault injection and dynamic mitigation evaluation

**PAPER-ID:** `PAPER-010`<br>
**Candidate identity:** `CONTROL-S4`<br>
**Related RQ:** future integrated adaptive-control RQ; `RQ-004`; `RQ-005`<br>
**Classification recommendation:** `RELATED`<br>
**Evidence status:** `ACCEPTED` full-text analytical card; candidate statements remain unaccepted claims<br>
**Exact full text used:** `Space Radiation Flux Driven Fault Injection for Evaluating Dynamic Mitigation Strategies(1).pdf`, 6 PDF pages, SHA-256 `6476e5227537eaf7332dc4e2e2fef8641dabd3859c03678d69fceac9a36097f3`

## Bibliographic identity

Junchao Chen, Li Lu, Marko Andjelkovic, Fabian Luis Vargas, and Milos Krstic, “Space Radiation Flux Driven Fault Injection for Evaluating Dynamic Mitigation Strategies,” *2024 IEEE 25th Latin American Test Symposium (LATS)*, pp. 1–6, 2024. DOI: `10.1109/LATS62223.2024.10534594`.

- `[SOURCE]` Title, author order, venue, copyright year, and DOI are printed on PDF p. 1.

## Control and reliability extraction

| Field | Full-text extraction |
|---|---|
| Runtime observation vector | `[SOURCE]` Number/type of faults detected by word-by-word HSIAO decoding and rescrubbing, with a fault counter/log (Sec. III.C Steps A–F; Fig. 5, PDF p. 4). `[UNKNOWN]` Exact vector fields, counter resets, log lifetime, and classification algorithm are not specified. |
| Sampling period/history window | `[SOURCE]` Environment and injected-fault data have one-hour resolution; the initial simulation fixes one hour between scrubs (Sec. III.A; Sec. IV.A, PDF pp. 3, 5). `[UNKNOWN]` No controller history window is defined. |
| Measurement / forecast / inferred state | `[SOURCE]` The controller analyzes detected faults over a specified interval and adjusts scrub frequency against a preset threshold (Sec. III.C, PDF p. 4). Forecasting is mentioned as possible prior work, but the paper says its current focus is detection/correction optimization. `[INFERENCE]` S4 is reactive/evaluation-driven, not an implemented forecast-driven controller. |
| Offline inputs | `[SOURCE]` Historical GOES/ACE-SIS flux, reconstructed hourly spectra, proton/heavy-ion test cross sections, CREME96 HUP/PUP calculations, target design, and selected historical event (Secs. III.A–B, PDF pp. 2–3). |
| Online inputs | `[SOURCE]` Detected new faults, rescrub outcome, classified fault type, and counter/log values (Sec. III.C, PDF p. 4). |
| Controlled variable | `[SOURCE]` RAM scrub frequency/timer (Fig. 4 and Sec. III.C Step F, PDF p. 4). |
| Decision/update period | `[SOURCE]` Faults are analyzed in a specified time interval; the case study uses hourly injection/scrub intervals before adaptation (Secs. III.C and IV.A, PDF pp. 4–5). `[UNKNOWN]` Exact online update cadence after frequency adjustment is not stated. |
| Control law | `[SOURCE]` Compare detected-fault statistics with a pre-established correction-rate threshold and select a scrub frequency that limits faults between scrubs (Sec. III.C; Table I discussion, PDF pp. 4–5). `[INFERENCE]` The 780 faults/hour and 100 faults/scrub example implies eight scrubs/hour via upward rounding, but no formal law is given. |
| Threshold / rounding / saturation | `[SOURCE]` A Monte Carlo table relates injected faults/scrub to correction rate; for a target 99%, the paper chooses at most 100 faults/scrub and maps about 780 faults/hour to 8 scrubs/hour (Table I, PDF p. 5). `[UNKNOWN]` No hysteresis, saturation, hard minimum/maximum, or tie handling is specified. |
| Wash-frequency range | `[SOURCE]` The evaluated static policies range from 1 to 33 scrubs/hour over the 144-hour event, while the proposed schedule totals 294 scrubs (Table III, PDF pp. 5–6). These are experiment totals, not actuator bounds. |
| Persistent controller/memory state | `[SOURCE]` Timer, EDAC control, scrubbing control, fault counter/log, and codeword parity are represented (Figs. 4–5, PDF p. 4). `[UNKNOWN]` Persistent state across unsuccessful corrections and the initial distribution are not defined. |
| ECC and correction semantics | `[SOURCE]` HSIAO `(39,32)` adds seven check bits to a 32-bit data word and is described as SEC-DED; word-by-word decode, initial detection, rescrub, reclassification, logging, and adjustment form the workflow (Sec. III.C; Sec. IV.A, PDF pp. 4–5). `[UNKNOWN]` The paper does not formalize decoder syndromes, miscorrection, or how a second error arriving during rescrub is handled. |
| Failure/reliability event | `[SOURCE]` Table I uses correction rate after injected faults; Fig. 6 separates corrected, uncorrected, and undetected counts/percentages. Table III reports “Reliability (%)” / “effective protection” over a 144-hour event (Sec. IV, PDF pp. 5–6). `[UNKNOWN]` A single formal failure event and the denominator of Table III reliability are not defined. |
| Metric, units, horizon, aggregation | `[SOURCE]` SEU rate in upsets·bit⁻¹·day⁻¹; injected/corrected/uncorrected/detected faults as counts or percent; correction rate as percent; total scrubs over 144 h; target array 20 Mbit (Sec. IV, Tables I–III). |
| Accumulation model | `[SOURCE]` Time-series fault counts are injected randomly between scrubs; more faults between scrubs reduce HSIAO correction rate (Secs. III.B and IV.A, PDF pp. 3, 5). `[UNKNOWN]` Arrival times within an interval, repeated hits, parent events, and state beyond output-bit flips are not specified. |
| Placement/independence | `[SOURCE]` The RTL testbench generates random bit addresses; a wrapper flips selected RAM output bits (Sec. III.B, PDF p. 3). `[INFERENCE]` This implements marginal random placement, not measured MCU topology or an explicit `W`/interleaving map. |
| Reset/writeback semantics | `[SOURCE]` The flow performs decode/correction, then rescrubs words with newly detected faults to distinguish retained/permanent behavior (Sec. III.C, PDF p. 4). `[UNKNOWN]` Correction writeback timing, atomicity, scan duration, and counter reset are not specified. |
| Prediction uncertainty | `[SOURCE]` No predictor is part of the evaluated S4 branch; future-environment prediction is only mentioned by reference (Sec. III.C, PDF p. 4). |
| Resource costs | `[SOURCE]` Table III measures only total scrub operations and claims 4×/16× fewer scrubs than Worst Day/Peak 5 Minutes during the case event (Secs. IV.B–V, PDF pp. 5–6). `[UNKNOWN]` Energy, bandwidth, latency, area, controller overhead, and performance are not measured. |
| Implementation boundary | `[SOURCE]` A simulation RTL injection wrapper, testbench, target RAM, HSIAO control, and scrub timer are modeled (Fig. 4, PDF p. 4). FPGA implementation is future work (Conclusion, PDF p. 6). |
| Validation and baselines | `[SOURCE]` Case study: 65-nm Cypress SRAM sensitivity, 20-Mbit array, March 6–11 2012 event, RTL/random fault injection, Monte Carlo correction table, and five CREME96 static environment policies (Sec. IV; Figs. 6; Tables I–III). |

## 1. Research problem

- `[SOURCE]` Static environment models cannot accurately evaluate and tune mitigation for time-varying SPE radiation (Introduction, PDF p. 1).

## 2. Objective

- `[SOURCE]` Develop a time-dependent radiation-flux-driven fault-injection method and use it to evaluate a dynamic HSIAO scrub strategy (Introduction; Fig. 1, PDF pp. 1–2).

## 3. Studied system/model

- `[SOURCE]` A 20-Mbit SRAM modeled after a 65-nm bulk-CMOS Cypress device, protected by HSIAO `(39,32)` SEC-DED and a dynamic scrub controller (Sec. IV.A, PDF p. 4).

## 4. Method

- `[SOURCE]` Reconstruct hourly historical spectra, convolve with target cross sections using CREME96, generate random fault addresses from hourly counts, inject at RTL, and compare adaptive versus five static policies (Secs. III–IV).

## 5. Assumptions

- `[SOURCE]` One-hour environmental resolution is selected to match GOES/ACE-SIS sampling and balance rapid variation against analysis simplicity (Sec. III.A, PDF p. 3).
- `[SOURCE]` Fault injection uses random bit addresses (Sec. III.B, PDF p. 3).
- `[INFERENCE]` No empirical basis is provided for independence/uniformity of bit locations or for collapsing MCU/MBU events into independent flips.

## 6. Independent/input variables

- `[SOURCE]` Hourly SEU/fault sequence, static environment model, faults between scrubs, target correction-rate threshold, and scrub frequency (Sec. IV; Tables I–III).

## 7. Dependent/output variables

- `[SOURCE]` Corrected, uncorrected, and undetected faults; correction rate; Table III reliability percentage; and total scrub count (Sec. IV, Fig. 6 and Tables I–III).

## 8. Baselines/comparators

- `[SOURCE]` CREME96 Solar Minimum, Solar Maximum, Worst Week, Worst Day, and Peak 5 Minutes static models (Sec. IV.B, Tables II–III).

## 9. Main equations/models

- `[SOURCE]` No closed-form control equation is given. Table I is a Monte Carlo relationship: 50/100/150/200/300 faults correspond to 99.76/99.04/97.84/96.19/91.62% correction (PDF p. 5).

## 10. Main results

- `[SOURCE]` One-hour scrubbing can fall to about 60% correction near the event peak while detection remains higher (Fig. 6, PDF p. 5).
- `[SOURCE]` The proposed schedule totals 294 scrubs and reports 100% Table III reliability, versus 1152 and 4752 scrubs for the two 100% static baselines (Table III, PDF p. 5).

## 11. Author-stated limitations

- `[SOURCE]` The study is a case study and proposes evaluating additional mitigation methods and FPGA platforms in future work (Conclusion, PDF p. 6).
- `[SOURCE]` The focus is correction/detection optimization; advanced forecasting is outside S4's present evaluation (Sec. III.C, PDF p. 4).

## 12. Methodological limitations inferred

- `[INFERENCE]` Table III's “Reliability” lacks a formal event/denominator and cannot be mapped directly to a probability over `E_cap`.
- `[INFERENCE]` A random bit-address generator cannot preserve parent-event multiplicity or physical topology and supplies no physical-to-logical map `W`.
- `[INFERENCE]` The threshold is empirical for one array/code/injection setup; it is not a project requirement or general guarantee.

## 13. Threats to validity

- `[INFERENCE]` Internal validity: the Monte Carlo procedure, trial count, randomization seed, and uncertainty intervals are not reported.
- `[INFERENCE]` Construct validity: “Reliability (%)” and “effective protection” are not formally tied to corrected/uncorrected/undetected event definitions.
- `[INFERENCE]` External validity: one event, one SRAM sensitivity model, one array size, and one ECC organization limit transfer.

## 14. What the paper actually demonstrates

- `[SOURCE]` S4 supplies a reusable method for driving fault injection with an hourly historical radiation-derived count sequence and demonstrates a reactive HSIAO scrub case study against static environment baselines.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` S4 does not demonstrate ML prediction, uncertainty-aware control, physical MCU/MBU modeling, explicit interleaving, or a mission-level reliability guarantee.
- `[INFERENCE]` The reported scrub reduction is not a measured energy or performance reduction.

## 16. Relevance to this dissertation

- `[INFERENCE]` S4 is strong evidence for the evaluation/fault-injection branch of DEC-002 and for scrub-count as one RQ-005 resource observable.
- `[INFERENCE]` It does not close the DEC-002 device-error → `W` → ECC-risk link or RQ-004 forecast interface.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` S4 converts historical hourly radiation data into a target-specific time-series fault-injection dataset (Secs. III.A–B, PDF pp. 2–3).
2. `[SOURCE-CANDIDATE]` S4 evaluates a reactive HSIAO `(39,32)` dynamic scrub flow rather than an implemented forecast-driven controller (Sec. III.C, PDF p. 4).
3. `[SOURCE-CANDIDATE]` In the S4 case study, a 99% empirical correction target is mapped to at most 100 faults/scrub and about 780 peak faults/hour to eight scrubs/hour (Table I discussion, PDF p. 5).
4. `[INFERENCE-CANDIDATE]` S4's random bit-address injection loses MCU parent-event provenance and cannot validate a `W`-aware failure probability.
5. `[INFERENCE-CANDIDATE]` Total scrub count is a resource proxy, not evidence of energy, latency, or bandwidth savings.

## 18. Contradictions/tensions

- `[SOURCE]` Table II lists Solar Minimum `4.01×10⁻⁷` and Solar Maximum `1.52×10⁻⁷` upsets·bit⁻¹·day⁻¹, an ordering that is not explained (PDF p. 5).
- `[SOURCE]` Sec. IV.A describes peak proton flux as “6530 MeV,” conflating a flux statement with an energy unit (PDF p. 4).
- `[INFERENCE]` S4's HSIAO threshold and correction metric are incompatible with direct reuse of S3/S5 PBD correct-count thresholds.

## 19. Open questions

1. `[UNKNOWN]` What exact event and denominator define Table III “Reliability (%)”?
2. `[UNKNOWN]` How are fault types classified after rescrub, and how are transient and permanent indications separated?
3. `[UNKNOWN]` What temporal distribution is used for injected faults within each hour?
4. `[UNKNOWN]` What resource costs correspond to a scrub in the target implementation?
5. `[UNKNOWN]` How would measured MCU topology and mapping `W` change the correction-rate table?

## Relation to DEC-001 and DEC-002

- `[INFERENCE]` The source gives an environment → count-series → ECC-injection → scrub-decision evaluation path, but no explicit `E_cap(A;t0,T)` or `F_A(t0,T;μ_t0)`.
- `[INFERENCE]` Compatibility requires a declared domain `A`, initial state, an event-mark/mapping layer, word-age/reset semantics, and a formal first-passage event.

## Equations/assumptions requiring reproduction

- Reproduce the hourly rate-to-injected-count conversion and random-address generator.
- Reproduce Table I with documented Monte Carlo trial count, seed, and confidence intervals.
- Reproduce Table III only after resolving the reliability event/denominator and the reported numerical anomalies.

## Final disposition

- **Orchestrator disposition:** `ACCEPTED / RELATED` — decisive for the separate evaluation branch and version comparison, but not the closest forecast-driven controller source.
- **Next action:** bounded Evidence Auditor comparison using the canonical S3/S4/S5 matrix; retain all metric ambiguities as unresolved.
