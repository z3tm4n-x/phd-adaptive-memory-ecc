# DRAFT — CONTROL-PRIOR-ART-01 — S3/S4/S5 full-text comparison

**Task:** `CONTROL-PRIOR-ART-PA-01`<br>
**Canonical base:** `e1e7b93cc72b7b295a8298560adf2cd507d7256b`<br>
**Related:** future integrated adaptive-control RQ; `RQ-004`; `RQ-005`; `DEC-002`<br>
**Scope:** bounded comparison of three supplied peer-reviewed full texts; not literature-level novelty adjudication

## 1. Source and copy provenance

| ID | Exact identity | Full text / integrity | Disposition |
|---|---|---|---|
| S3 | J. Chen, M. Andjelkovic, M. Krstic, F. L. Vargas, “A Machine Learning-driven EDAC Method for Space-Application Memory,” DFT 2023, DOI `10.1109/DFT59622.2023.10313560` | `A Machine Learning-driven EDAC Method for.pdf`; 6 pages; SHA-256 `a0801e75ccc8747dd68d97813e94b199885f3c7e18548c9b9a25439603ef1316` | Full text accessible; `CORE` |
| S4 | J. Chen, L. Lu, M. Andjelkovic, F. L. Vargas, M. Krstic, “Space Radiation Flux Driven Fault Injection for Evaluating Dynamic Mitigation Strategies,” LATS 2024, DOI `10.1109/LATS62223.2024.10534594` | `Space Radiation Flux Driven Fault Injection for Evaluating Dynamic Mitigation Strategies(1).pdf`; 6 pages; SHA-256 `6476e5227537eaf7332dc4e2e2fef8641dabd3859c03678d69fceac9a36097f3` | Full text accessible; `RELATED` |
| S5 | J. Chen, L. Lu, M. Andjelkovic, F. L. Vargas, M. Krstic, “Dynamic Fault Mitigation for Space Radiation Using Fault Injection and Machine Learning,” *Journal of Electronic Testing* 41:273–285 (2025), DOI `10.1007/s10836-025-06183-5` | `Dynamic Fault Mitigation for Space Radiation Using Fault Injection(3).pdf`; 13 pages; SHA-256 `1e7b1d2514bf401e4a765804aac8f5a51602514f7091e4bc6a6a4ff6d654d6d9` | Full text accessible; `CORE` |

`[SOURCE]` S5 explicitly cites S3 and S4 as previous conference works [19,20] and calls the journal work an “extended and systematized framework” (S5 Sec. 2, journal p. 275).

## 2. Feature-by-feature cross-version matrix

| Feature | S3 — 2023 controller disclosure | S4 — 2024 evaluation branch | S5 — 2025 journal consolidation |
|---|---|---|---|
| Observation source | `[SOURCE]` Real-time target-memory PBD fault count; Fig. 1, Steps F–G, PDF pp. 2–3. | `[SOURCE]` HSIAO decode/rescrub, detected-fault count/type/log; Sec. III.C, PDF p. 4. | `[SOURCE]` PBD fault log/real-time observations represented as recent hourly SEU-rate samples; Secs. 3.1, 3.3–3.4, journal pp. 277–279. |
| Sampling/history | `[SOURCE]` Hourly data and next-hour prediction. `[UNKNOWN]` History length. | `[SOURCE]` Hourly environment/injection and initial one-hour scrub interval. No predictor history. | `[SOURCE]` Six past hourly rates predict `t+1`; Sec. 3.3, p. 278. |
| Prediction | `[SOURCE]` Five regressors; linear selected at `R²=0.94`, LSTM `0.95`; Sec. III, PDF p. 3. | `[SOURCE]` Prediction only cited as possible; evaluated branch is detection/correction optimization; Sec. III.C, PDF p. 4. | `[SOURCE]` Five regressors, normalization, 60/40 split, 10-fold CV, `R²`/RMSE; linear deployed; Sec. 3.3. |
| Controlled action | `[SOURCE]` PBD wash timer/frequency. | `[SOURCE]` HSIAO scrub timer/frequency. | `[SOURCE]` PBD wash timer/frequency. |
| Control-law form | `[SOURCE]` Predicted next-hour faults + selected PBD correct-count threshold → washes/hour; 600/460 → 2; Sec. V.A. | `[SOURCE]` Observed/injected faults + empirical correction threshold → scrubs/hour; 780/100 → 8; Secs. III.C, IV.A. | `[SOURCE]` S3 law restated; 600/460 → every 30 min; Sec. 4.1. |
| Rounding/saturation | `[INFERENCE]` Example implies upward integer rounding. `[UNKNOWN]` No formal rounding, saturation, hysteresis, min/max. | Same limitation. | Same limitation. |
| Reliability constraint | `[SOURCE]` `P` that all `F` random fault locations occupy distinct primary–redundant byte pairs, enabling correct count. | `[SOURCE]` Empirical HSIAO correction rate versus injected faults; Table III “Reliability” is undefined. | `[SOURCE]` S3 `P` retained, but Table 4 describes target as “correction rate,” creating terminology tension. |
| Relation to `E_cap/F_A` | `[INFERENCE]` Neither the distinct-pair correct-count event nor scenario tables are `E_cap`/`F_A`. | `[INFERENCE]` Corrected/uncorrected/undetected counts are related to ECC outcomes, but no first-passage event, `A`, or `μ_t0` is formalized. | `[INFERENCE]` Same mismatch as S3; no formal bridge added. |
| Uncertainty treatment | `[SOURCE]` Point `R²` only; no interval or propagation. | `[SOURCE]` No predictor; Monte Carlo table has no trial count/CI. | `[SOURCE]` Cross-validation and RMSE named, but RMSE values/intervals and action propagation absent. |
| ECC | `[SOURCE]` PBD: duplication + parity per byte; NE/EDC/EDNC/ENDNC. | `[SOURCE]` HSIAO `(39,32)` SEC-DED; decode and rescrub classification. | `[SOURCE]` PBD retained; other ECCs claimed architecturally compatible but not evaluated. |
| Scrubbing/washing semantics | `[SOURCE]` Byte-pair scan, parity check, copy valid byte, count, update timer. | `[SOURCE]` Word decode, detect, rescrub, classify/log, adjust. | `[SOURCE]` S3 PBD semantics restated; successful correction copies a byte. |
| Reset/writeback | `[SOURCE]` Writes update both copies and parity; successful wash copies byte. `[UNKNOWN]` Counter reset, scan time, residual state. | `[SOURCE]` Correction/rescrub present. `[UNKNOWN]` exact writeback/reset timing and word age. | Same unresolved details as S3. |
| Physical-event model | `[SOURCE]` Historical bit-level SEU rates and `F` randomly located faults. | `[SOURCE]` Historical hourly count sequence, random injected bit addresses. | `[SOURCE]` Both constructions consolidated. |
| MCU/MBU treatment | `[SOURCE]` PBD qualitative MBU outcomes; random-placement equation has no parent-event mark. | `[SOURCE]` Random bit flips; HSIAO DBU capability. No MCU topology. | `[SOURCE]` Qualitative PBD MBU limitations and inherited injection; no joint MCU mark. |
| Mapping `W` / interleaving | `[UNKNOWN]` None. | `[UNKNOWN]` None; random logical/RTL bit addresses only. | `[UNKNOWN]` None. |
| Placement/independence | `[SOURCE]` Equal-weight `F`-subsets of `B·2n` positions in the equation. | `[SOURCE]` Testbench random-address function. | `[SOURCE]` Both inherited. `[INFERENCE]` No empirical independence validation. |
| Internal memory/controller state | `[SOURCE]` Dual copies, parity, fault counter, wash timer, pretrained model. Predictor history unspecified. | `[SOURCE]` ECC/scrub timer, counter/log, rescrub outcome. | `[SOURCE]` Adds explicit six-hour input history and online-learning accumulated log alternative. |
| Resource metric | `[SOURCE]` Wash frequency; inherited 4% PBD area; qualitative performance concern. | `[SOURCE]` Total scrubs; no cost-vector measurements. | `[SOURCE]` Scrub totals/frequency and annual counts; qualitative power/performance claims; inherited area. |
| Controller implementation | `[SOURCE]` Architecture and prior hardware accelerator cited; no complete deployed controller evidence. | `[SOURCE]` RTL/testbench control evaluation; no prediction controller. | `[SOURCE]` Scikit-learn/Keras model plus architecture; complete hardware deployment not demonstrated. |
| Hardware implementation | `[SOURCE]` Prior PBD and predictor hardware evidence cited, not reproduced. | `[SOURCE]` RTL fault-injection model; FPGA is future work. | `[SOURCE]` Prior VHDL/LEON3 PBD cited; FPGA integration remains future work. |
| Validation data | `[SOURCE]` 36 Solar Cycle 24 SPEs / about 5107 h; 65-nm SRAM model; mathematical curve/tables. | `[SOURCE]` March 6–11 2012 case; 20-Mbit array; Monte Carlo and five static policies. | `[SOURCE]` 36 events / 5107 h, March case, five regressors, random RTL injection, five static policies. |
| Baselines | `[SOURCE]` Five regressors. | `[SOURCE]` Five static CREME96 policies. | `[SOURCE]` Both baseline sets. |
| Guarantee | `[UNKNOWN]` No formal guarantee; threshold is conditional on `F` and placement assumptions. | `[UNKNOWN]` No formal guarantee; 99/100% are simulation metrics. | `[UNKNOWN]` No formal guarantee or uncertainty margin. |
| Domain of validity | `[SOURCE]` Modeled 65-nm Cypress SRAM, PBD 24-bank organization, Solar Cycle 24-derived hourly sequences. | `[SOURCE]` Modeled 20-Mbit SRAM, HSIAO, March 2012 event, hourly injection. | `[SOURCE]` Consolidated modeled domain; transfer to other ECCs/components/environments is future work. |

## 3. Control classification

| Source | Classification | Basis |
|---|---|---|
| S3 | `[INFERENCE]` **Hybrid observation/prediction pipeline; forecast-driven action** | Current PBD counts feed a model; the next-hour forecast, not the current count alone, selects the following-hour wash rate (Fig. 1; Sec. V.A). |
| S4 | `[INFERENCE]` **Reactive/evaluation-driven** | Detected/rescrubbed faults are compared with a preset correction threshold. Future prediction is mentioned but expressly not the current focus (Sec. III.C). |
| S5 | `[INFERENCE]` **Hybrid observation/prediction pipeline; forecast-driven action** | Six recent hourly rate observations feed a next-hour predictor; predicted intensity sets washing (Secs. 3.3–4.1). |

`[INFERENCE]` “Dynamic” is therefore not sufficient to classify a controller as predictive: S4 is dynamic without an implemented forecast loop.

## 4. First appearance, branch-specific features, and journal inheritance

| Question | Finding |
|---|---|
| Functions first explicit in S3 | `[SOURCE]` PBD online fault measurement, ML forecast, probability-to-fault-budget table, forecast-to-wash worked example, and NE/EDC/EDNC/ENDNC control flow (S3 Figs. 1, 3–5; Secs. III–V). |
| Separate S4 evaluation branch | `[SOURCE]` Historical time-series fault-injection platform, random RTL address injection, HSIAO decode/rescrub workflow, correction-rate Monte Carlo table, and five-static-policy comparison (S4 Figs. 1, 4–6; Tables I–III). |
| What S5 inherits | `[SOURCE]` It cites S3/S4 and combines S3's ML/PBD controller with S4's historical injection/static-baseline methodology (S5 Sec. 2; Figs. 2–7). |
| What S5 adds or makes explicit | `[SOURCE]` Six-hour history and `t+1` target; min-max normalization; 10-fold CV; RMSE named; online-learning alternative; explicit ECC-agnostic architectural claim; prior PBD experiment description; annual scrub estimate and cost discussion (S5 Secs. 3.1–4.3). |
| What S5 does not add | `[INFERENCE]` It does not add `W`, MCU provenance, a new formal reliability event, complete control bounds, uncertainty propagation, or measured cost vector. |

### Extension versus consolidation

- `[SOURCE]` S5 contains verifiable new disclosure relative to the two six-page conference papers, especially predictor-window/training details and extended annual-scrub/resource discussion.
- `[INFERENCE]` It is therefore a **real but bounded extension built primarily by consolidation**. The central control law and PBD collision equation already appear in S3, while the time-series injection/static comparison already appears in S4.
- `[INFERENCE]` This feature statement is not a novelty or priority judgment beyond these three texts.

## 5. Numerical and terminology inconsistencies

| Issue | Source evidence | Disposition |
|---|---|---|
| Scrub totals for March 2012 | S4 Table III: proposed 294, Worst Day 1152, Peak 5 Minutes 4752. S5 Table 4: 241, 1008, 3312. | `[UNKNOWN]` No reconciliation, changed rounding rule, or changed event slice is stated. |
| Improvement factor | S4 abstract/conclusion: up to 16×. S5 abstract: up to 13×. | `[SOURCE]` The change follows the differing totals but the methodological cause is not disclosed. |
| Reliability terminology | S3/S5 equation defines probability of accurate count; S5 Sec. 4.2 calls 99.99% a correction-rate target; S4 uses empirical correction rate and separately labels Table III “Reliability.” | `[INFERENCE]` These metrics are not interchangeable and must remain source-specific. |
| Solar Minimum/Maximum rate order | S4 Table II and S5 Table 3 both list Solar Minimum `4.01×10⁻⁷` above Solar Maximum `1.52×10⁻⁷`. | `[UNKNOWN]` Possibly label/model convention or error; the texts do not explain it. |
| Peak proton “flux” | S4 Sec. IV.A describes peak proton flux as `6530 MeV`. | `[SOURCE]` Unit/quantity inconsistency; do not convert or repair without source data. |
| Memory size wording | S3/S5 describe 24 banks with “1 Mbit words” of 32-bit width and also give 1,811,939,328 total bits; S4/S5 static comparison uses a 20-Mbit target. | `[INFERENCE]` Multiple scenario domains are present; direct threshold transfer requires explicit normalization. |
| Author display | S3 PDF prints “Vargas Fabian Luis”; S4/S5 use “Fabian Luis Vargas.” | `[SOURCE]` Bibliographic normalization does not change source author order/person identity. |

## 6. Scoped DEC-002 architecture comparison

| DEC-002 stage | S3 | S4 | S5 | Remaining interface gap |
|---|---|---|---|---|
| Radiation/test evidence | `[SOURCE]` Prior target cross sections + GOES/ACE data. | `[SOURCE]` Same inputs drive historical injection. | `[SOURCE]` Gives Weibull table and reconstruction flow. | `[UNKNOWN]` Cross-section and environment uncertainty are not propagated. |
| Device-error representation | `[SOURCE]` Marginal hourly bit-upset rate / fault count. | `[SOURCE]` Hourly count + random bit addresses. | `[SOURCE]` Both. | `[INFERENCE]` No marked MCU/topology process or parent-event provenance. |
| `W`/ECC reliability | `[SOURCE]` PBD organization and collision surrogate. | `[SOURCE]` HSIAO simulation/correction table. | `[SOURCE]` PBD surrogate; ECC-agnostic assertion. | `[UNKNOWN]` No explicit physical-to-logical `W`, `E_cap`, initial distribution, or sequential word age. |
| Online risk assessment | `[SOURCE]` Next-hour point forecast. | `[SOURCE]` Reactive fault count/threshold. | `[SOURCE]` Six-hour-to-next-hour point forecast. | `[UNKNOWN]` No calibrated risk distribution or forecast-error propagation. |
| Adaptive restoration decision | `[SOURCE]` Threshold table → wash frequency. | `[SOURCE]` Correction table → scrub frequency. | `[SOURCE]` S3 decision plus extended summaries. | `[UNKNOWN]` No complete law with actuator bounds, costs, latency, or formal guarantee. |

`[INFERENCE]` The family is closest to the last two DEC-002 stages. The physical-event/`W`/ECC first-passage bridge remains materially different from the integrated roadmap.

## 7. Agreements and incompatible assumptions

### Agreements

- `[SOURCE]` All sources use hourly target fault/rate sequences derived from historical space-radiation data and a target SRAM response.
- `[SOURCE]` All treat scrub frequency/count as the principal controllable resource.
- `[SOURCE]` All evaluate by simulation/model-derived fault sequences, not an in-orbit closed-loop deployment.

### Incompatible definitions or aggregation levels

- `[INFERENCE]` S3/S5 PBD `P` is a byte-pair collision/correct-count probability; S4 Table I is an array/code correction percentage. Their numerical thresholds cannot be mixed.
- `[INFERENCE]` PBD duplicates byte segments and has NE/EDC/EDNC/ENDNC; HSIAO `(39,32)` is SEC-DED with a different word-level state and rescrub flow.
- `[INFERENCE]` S3/S5 model a 24-bank duplicated array for the PBD equation; S4 and S5 static comparisons cite a 20-Mbit target.
- `[INFERENCE]` S4 is reactive; S3/S5 are forecast-driven at the decision boundary. A shared “dynamic” label hides this interface difference.

## 8. Information retained and lost

| Stage | Retained | Lost / not represented |
|---|---|---|
| Historical environment → hourly rate | Proton/heavy-ion marginal hourly rate by target sensitivity | Particle/event identity, sub-hour burst structure, cross-section uncertainty |
| Rate → RTL faults | Hourly count and random logical bit locations | Parent particle, multiplicity, spatial topology/correlation, physical coordinates |
| Memory/ECC state | PBD byte pair or HSIAO codeword outcomes during scan | Explicit `W`, heterogeneous bank mapping, word exposure ages, general initial distribution |
| Observation → predictor | Scalar recent rate/count history (six values explicitly only in S5) | Classification uncertainty, missed ENDNC state, calibrated posterior/risk distribution |
| Predictor → action | Selected threshold and washes/hour | Formal feasibility bounds, controller latency, resource-cost vector, robust margin |

## 9. Candidate claims for Evidence Auditor

No `CLM-xxx` is created. The following seven statements warrant later audit:

1. `[SOURCE-CANDIDATE]` S3 is the earliest of these three texts to disclose the PBD fault-count → ML forecast → next-hour wash-frequency loop (S3 Fig. 1; Secs. III–V).
2. `[SOURCE-CANDIDATE]` S4 is a separate reactive HSIAO evaluation branch based on hourly flux-driven random fault injection and static-policy comparison (S4 Secs. III–IV).
3. `[SOURCE-CANDIDATE]` S5 explicitly consolidates S3 and S4 and adds a six-hour history, `t+1` target, 10-fold CV, online-learning alternative, and annual scrub estimates (S5 Secs. 2–4.3).
4. `[SOURCE-CANDIDATE]` The PBD threshold in S3/S5 is probability of accurate fault counting under distinct byte-pair occupancy, not a first-passage ECC failure probability (S3 Sec. V.A; S5 Sec. 4.1).
5. `[INFERENCE-CANDIDATE]` None of S3/S4/S5 propagates measurement, model, or forecast uncertainty into the scrub decision.
6. `[INFERENCE-CANDIDATE]` None preserves joint physical MCU marks or an explicit mapping `W`; random bit-address injection cannot establish `W`-aware `E_cap/F_A` behavior.
7. `[INFERENCE-CANDIDATE]` Scrub totals/frequency are resource proxies; energy, latency, bandwidth, and controller cost claims remain unmeasured.

## 10. Exact unresolved gaps

1. `[UNKNOWN]` **Observation interface:** conversion from PBD/HSIAO raw outcomes, including EDNC/ENDNC, into the predictor's hourly rate/count sample.
2. `[UNKNOWN]` **Prediction validation:** event-wise train/test separation, published coefficients, RMSE values, residual distribution, calibration, and missed-onset behavior.
3. `[UNKNOWN]` **Decision law:** exact rounding, update cadence, hysteresis, saturation, maximum feasible frequency, and fallback for invalid/missing forecasts.
4. `[UNKNOWN]` **Reliability semantics:** formal event and denominator behind S4 Table III/S5 Table 4 “Reliability,” and its relation to correction/counting metrics.
5. `[UNKNOWN]` **Physical model:** parent-event multiplicity, MCU topology, temporal clustering, physical coordinates, and explicit `W`/interleaving.
6. `[UNKNOWN]` **State/reset:** counter reset, correction writeback timing, scan duration, per-word age, initial state/distribution, and residual uncorrected faults.
7. `[UNKNOWN]` **Uncertainty:** propagation from radiation/test data and forecast error into an online risk bound and action.
8. `[UNKNOWN]` **Resource vector:** measured traffic, bandwidth, latency, energy, contention, area, and controller overhead as functions of scrub frequency.
9. `[UNKNOWN]` **Version reconciliation:** why S4 and S5 report different March-event scrub totals and improvement factors.

## 11. Bounded sufficiency assessment

- `[INFERENCE]` **SUFFICIENT FOR BOUNDED NOVELTY-THREAT COMPARISON WITHIN THIS THREE-SOURCE CHEN/IHP/POTSDAM FAMILY.** All three mandatory full texts are available; S3 establishes the controller disclosure, S4 isolates the evaluation branch, and S5 shows inheritance plus bounded additions.
- `[INFERENCE]` **NOT SUFFICIENT FOR LITERATURE-LEVEL NOVELTY OR NON-NOVELTY ADJUDICATION.** The bounded set does not cover the broader adaptive-control literature, and the handoff expressly forbids that conclusion.
- `[INFERENCE]` The strongest source for close architecture comparison is S5 (`CORE`), S3 remains `CORE` for priority/feature provenance within the family, and S4 is `RELATED` but necessary to avoid conflating HSIAO evaluation with PBD forecast control.

## 12. Stop disposition

All three named sources received full-text disposition. No S1/S2 expansion or broad search was performed. Remaining issues are named feature/evidence gaps for Orchestrator review; no permanent claim, threshold, novelty conclusion, or project control model is created.
