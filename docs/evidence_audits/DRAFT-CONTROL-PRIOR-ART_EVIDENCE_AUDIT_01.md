# DRAFT — CONTROL-PRIOR-ART Evidence Audit 01

**Task:** `CONTROL-PRIOR-ART-EVIDENCE-AUDIT-01`  
**Related:** `RQ-004`; `RQ-005`; future integrated adaptive-control RQ  
**Canonical base:** `d2c07e7365522fa528108ee0223a5533d884ffe1`  
**Controlled publications:** `PAPER-009` / S3; `PAPER-010` / S4; `PAPER-011` / S5  
**Status:** draft for Research Orchestrator acceptance  
**Date:** 2026-08-31

## 1. Audit boundary and evidence discipline

This is an atomic, bounded audit of the submitted candidate statements against the three accepted full-text Paper Cards, their accepted cross-version matrix, and DEC-002. It does not search the general control literature, assign permanent claim or evidence identifiers, select a project controller, or adjudicate literature-level novelty.

The controlled source relation is preserved throughout:

- **S3 / PAPER-009 / DFT 2023:** first forecast-driven PBD controller disclosure within this three-source set;
- **S4 / PAPER-010 / LATS 2024:** separate reactive HSIAO fault-injection/evaluation branch;
- **S5 / PAPER-011 / JETTA 2025:** explicit journal consolidation and bounded extension of S3 and S4.

The labels below mean:

- `[SOURCE]` — directly stated or directly reconstructible from checked full text at the cited location;
- `[INFERENCE]` — cross-source or project-contract comparison derived from the checked evidence;
- `[UNKNOWN]` — not established in the controlled full texts.

An absence assessment is restricted to S3/S4/S5. It is not a statement about all Chen publications or the wider literature.

## 2. Scite citation-context and editorial-status check

Scite was used only as a targeted context and editorial-status discovery layer for the exact three DOIs.

| Source | Indexed metadata / citation context | Editorial check | Audit interpretation |
|---|---|---|---|
| S3, DOI `10.1109/DFT59622.2023.10313560` | Metadata resolved. Returned tally: 0 classified citation statements and 2 citing publications; no actual incoming citation snippet was returned | Targeted retraction, correction, erratum and concern filters returned zero hits but also produced an internally inconsistent “DOI not present” notice despite metadata resolution | No material external qualification was available from Scite. Primary full text controls; zero returned notices is not proof of absence |
| S4, DOI `10.1109/LATS62223.2024.10534594` | Metadata resolved. Returned tally: 0 classified citation statements and 1 citing publication; no actual incoming citation snippet was returned | Same limitation | No material external qualification was available from Scite. Primary full text controls |
| S5, DOI `10.1007/s10836-025-06183-5` | Metadata resolved; no citation tally or incoming citation snippet was returned | Same limitation; the paper is also recent | No material external qualification was available from Scite. Primary full text controls |

No indexed correction, retraction, erratum, or editorial concern was located. Because the notice-filter response was internally inconsistent and citation context was sparse, the admissible conclusion is **“no indexed notice or material context located in the bounded check,” not “none exists.”** Citation counts play no role in the assessments.

## 3. Atomic disposition matrix

| Candidate | Atomicity | Assessment | Confidence | Corrected/admissible wording | Later CLM consideration |
|---|---|---|---|---|---|
| 1 | Two linked tests: earliest within the controlled set; exact loop content | **SUPPORTED** | High | Within S3/S4/S5, S3 is the earliest publication that explicitly connects PBD-observed fault counts to an ML next-hour forecast and then to next-hour wash frequency | Suitable with the controlled-family boundary; not a wider priority statement |
| 2 | Three linked tests: S4 branch identity; reactive law; non-identity with S3/S5 loop | **SUPPORTED** | High | S4 evaluates a separate reactive HSIAO branch driven by hourly radiation-derived random logical fault injection and compared with static policies; it does not implement the PBD forecast-to-action loop of S3/S5 | Suitable with source-specific ECC, metric and implementation qualifiers |
| 3 | Decomposed into consolidation plus five alleged additions | **PARTIALLY_SUPPORTED** | High for consolidation; medium-high for additions | S5 explicitly consolidates S3 and S4. Relative to those conference papers it newly specifies the six-hour input window, 10-fold cross-validation and RMSE evaluation setup, an online-learning alternative, and annual scrub estimates; it **restates/makes explicit**, rather than first adds, the `t+1` target already present as next-hour prediction in S3 | Suitable only after this wording correction |
| 4 | Two tests: mathematical event; mismatch to DEC-001 object | **SUPPORTED** | High | In S3/S5, `P` is conditional on `F` distinct randomly placed faults and measures occupancy of distinct primary–redundant byte pairs, enabling accurate counting under the PBD model. It is neither DEC-001 `E_cap` nor `F_A(t0,T;μ_t0)` | Suitable; preserve the exact formula assumptions and avoid calling it mission reliability |
| 5 | Three absence tests: measurement, radiation-model and forecast uncertainty | **SUPPORTED** | Medium-high | Within S3/S4/S5, measurement/classification uncertainty and radiation-model/input uncertainty are not propagated into the scrub action; S3/S5 also do not propagate forecast uncertainty, while S4 has no implemented forecast in the evaluated branch | Suitable as a bounded family-level absence, with “forecast” marked not applicable to S4 |
| 6 | Three tests: parent-event marks; explicit `W`; consequence of random logical injection | **SUPPORTED** | High | S3/S4/S5 do not retain a joint physical MCU parent-event mark or an explicit physical-cell-to-logical mapping `W`. Their random logical bit placement cannot validate `W`-aware DEC-001 first-passage behavior | Suitable within the modeled domains; do not imply that the papers claim physical MCU fidelity |
| 7 | Two tests: proxy status; absence of measured cost vector | **SUPPORTED** | High | Scrub count/frequency is a measured or calculated resource proxy in the family. The family does not report a jointly measured vector of energy/power, traffic/bandwidth, latency, contention/performance interference, and controller hardware/update cost | Suitable; retain inherited/qualitative area and performance statements as limiting evidence |
| 8a | Atomic guarantee-under-uncertainty claim | **SUPPORTED** | High | S3/S4/S5 do not establish a formal reliability guarantee for the adaptive restoration action under propagated uncertainty | Suitable as a bounded absence; do not convert it into a general control-literature claim |
| 8b | Atomic complete-deployed-loop claim | **SUPPORTED** | High | S3/S4/S5 do not demonstrate one complete deployed hardware loop from online observation through prediction/risk and decision to physical scrub actuation. They demonstrate architectures, software/model analysis, RTL injection/evaluation, and cite prior component implementations | Suitable with “complete,” “deployed,” and “single integrated loop” retained |

## 4. Final bounded feature comparison

| Required feature | S3 — DFT 2023 | S4 — LATS 2024 | S5 — JETTA 2025 | DEC-002 comparison disposition |
|---|---|---|---|---|
| Input / observable state | `[SOURCE]` Online PBD-detected fault count; historical hourly GOES/ACE-SIS-derived rates and target cross section for training. Exact counter/reset/history vector is `[UNKNOWN]` | `[SOURCE]` HSIAO detected fault count/type/log and rescrub result under hourly injected faults. No predictor history | `[SOURCE]` PBD fault log/recent hourly rate; explicit six-sample hourly history. Raw PBD-to-rate conversion remains `[UNKNOWN]` | `[INFERENCE]` The family supplies plausible external/environment and internal-memory channels, but not a closed observation model with latency, classification error and state-estimation semantics required by RQ-004 |
| Uncertainty treatment | `[SOURCE]` Five regressors and point `R²`; no intervals/calibration/action propagation | `[SOURCE]` Monte Carlo correction table without stated trial count or confidence interval; no predictor | `[SOURCE]` normalization, 60/40 split, 10-fold CV, `R²` and RMSE named; RMSE values, intervals and action propagation absent | `[INFERENCE]` No end-to-end uncertainty propagation from measurement/radiation model/forecast to the restoration action |
| ECC-level reliability / risk object | `[SOURCE]` PBD distinct-byte-pair correct-count probability `P`; qualitative NE/EDC/EDNC/ENDNC | `[SOURCE]` HSIAO `(39,32)` correction percentages and undefined Table III “Reliability” | `[SOURCE]` S3 `P` retained; Table 4 terminology shifts toward “correction rate” without redefining the event | `[INFERENCE]` None supplies DEC-001 `E_cap`, protection domain `A`, initial distribution `μ_t0`, or first-passage `F_A`; S3/S5 `P` and S4 correction percentages are not interchangeable |
| Restoration decision variable | `[SOURCE]` PBD washes/hour or wash timer | `[SOURCE]` HSIAO scrubs/hour or scrub timer | `[SOURCE]` PBD washes/hour or wash timer | `[SOURCE]` All three contain an actual restoration-frequency decision variable, so time-varying input alone is not the relevant difference |
| Decision law | `[SOURCE]` Forecast faults divided by permitted faults/wash; 600/460 gives two washes next hour. Upward rounding is inferred; bounds/hysteresis absent | `[SOURCE]` Detected/injected faults compared with empirical correction threshold; 780/100 gives eight scrubs/hour. Full law absent | `[SOURCE]` S3 law restated with explicit six-hour-to-next-hour predictor | `[INFERENCE]` Close adaptive prior art exists at the observation/forecast-to-frequency interface. Exact rounding, update, saturation, fallback and actuator feasibility remain `[UNKNOWN]` |
| Reliability constraint / guarantee | `[SOURCE]` User-selected PBD correct-count threshold conditional on `F` and uniform placement | `[SOURCE]` User-selected empirical correction-rate threshold; Table III denominator/event undefined | `[SOURCE]` Same PBD threshold; terminology tension with “correction rate” | `[INFERENCE]` These are source-specific thresholds/simulation metrics, not a formal guarantee under propagated uncertainty and not the project requirement |
| Resource-cost treatment | `[SOURCE]` Wash frequency; inherited 4% PBD area; qualitative resource/performance discussion | `[SOURCE]` Total scrubs; no measured energy, bandwidth, latency, area or controller overhead | `[SOURCE]` scrub totals and annual counts; inherited area and qualitative power/performance statements | `[INFERENCE]` The family supplies a valid scrub-operation proxy but not the measurable multi-component vector required by RQ-005 |
| Mapping / event-model assumptions | `[SOURCE]` Equal-weight `F`-subsets of logical bit positions; no physical parent mark or `W` | `[SOURCE]` Random logical RTL bit addresses; no parent-event mark or `W` | `[SOURCE]` Both constructions inherited; no physical MCU topology or `W` | `[INFERENCE]` The family does not implement the DEC-002 physical-event → `W` → joint ECC-state bridge; it cannot by itself validate `W`-aware `F_A` |
| Architecture / implementation evidence | `[SOURCE]` Controller architecture, mathematical evaluation, prior PBD/predictor hardware cited; no complete integrated deployment | `[SOURCE]` RTL fault-injection/testbench and HSIAO control simulation; FPGA is future work | `[SOURCE]` Scikit-learn/Keras processing, RTL injection and PBD architecture; prior VHDL/LEON3 PBD cited; integrated FPGA/deployment absent | `[INFERENCE]` The family contains a close architecture and simulation/model evidence, but not a complete deployed observation-to-actuation hardware loop |

## 5. Detailed candidate audits

### Candidate 1 — earliest S3 forecast-driven PBD loop

**Atomic decomposition.** (1a) S3 precedes S4/S5 within the fixed source set; (1b) S3 contains each element of the submitted loop.

**Strongest supporting evidence.** `[SOURCE]` S3 Fig. 1 (PDF p. 2) shows target-memory PBD observation, prediction and control. Section III (pp. 2–3) constructs and compares five regressors and states next-hour prediction. Section IV Steps F–G (p. 3) connects PBD fault counting to wash-timer adjustment. Section V.A (pp. 4–5) maps chosen `P` to a fault-per-wash allowance and gives the 600 predicted faults / 460 faults per wash → two washes in the following hour example. S3 is dated 2023; S4 and S5 are 2024 and 2025.

**Strongest limit/contrast.** `[SOURCE]` S3 does not disclose the predictor history length, coefficients, formal rounding, saturation or uncertainty margin. `[INFERENCE]` “Earliest” is established only among S3/S4/S5, not among S1/S2, the complete Chen family, or the wider literature.

**Scope.** PBD duplicated memory with per-byte parity; 24-bank modeled domain; hourly marginal SEU/fault counts; one-hour forecast/action horizon; conditional count-observability metric; no explicit physical `W` or first passage.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** An earlier publication inside the explicitly controlled S3/S4/S5 set is impossible by identity; widening the priority population would create a different claim requiring a separate audit.

**Model-design consequence.** Forecast-driven selection of next-hour scrub/wash frequency is already a close comparison baseline and cannot serve alone as a differentiating method feature.

### Candidate 2 — separate reactive S4 branch

**Atomic decomposition.** (2a) S4 uses HSIAO rather than PBD; (2b) its evaluated action is reactive; (2c) its injection/static-comparison branch is distinct from the S3/S5 forecast loop.

**Strongest supporting evidence.** `[SOURCE]` S4 Secs. III.A–B (PDF pp. 2–3) reconstruct hourly radiation-derived rates and inject random logical bit addresses. Section III.C and Figs. 4–5 (p. 4) implement HSIAO `(39,32)` decode, rescrub, fault counting/logging and threshold-based frequency adjustment. Section IV, Tables I–III and Fig. 6 (pp. 5–6) compare the proposed schedule with five static CREME96 policies. The text states that prediction is possible but that the current focus is detection/correction optimization.

**Strongest limit/contrast.** `[SOURCE]` S4 contains a dynamic controller concept and radiation-derived time series; it is not “static.” `[UNKNOWN]` The exact update law, counter semantics, Monte Carlo uncertainty and Table III reliability denominator are not provided. The reactive classification is therefore a full-text `[INFERENCE]` about the evaluated decision boundary, not an author-supplied controller taxonomy.

**Scope.** Modeled 20-Mbit SRAM; HSIAO SEC-DED; hourly random logical injection; March 6–11 2012 / 144-hour case; correction percentage and scrub totals; no next-hour predictor in the evaluated branch.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** Source code or supplementary text showing that the evaluated S4 controller actually consumed a forecast would contradict (2b). No such evidence is present in the controlled source.

**Model-design consequence.** S4 must remain a separate reactive/evaluation baseline; its thresholds and results cannot be silently combined with PBD correct-count thresholds.

### Candidate 3 — S5 consolidation and bounded additions

**Atomic decomposition.** (3a) explicit consolidation; (3b) six-hour input history; (3c) `t+1` target; (3d) cross-validation details; (3e) online-learning alternative; (3f) annual scrub estimates.

**Strongest supporting evidence.** `[SOURCE]` S5 Sec. 2 (journal p. 275 / PDF p. 3) identifies S3 and S4 as previous conference works [19,20] and describes an extended/systematized framework. Section 3.3 (p. 278) specifies six previous hourly rates, target `t+1`, min-max normalization, a 60/40 split, 10-fold CV, and `R²`/RMSE evaluation. Section 3.1 (p. 277) discusses an online-learning alternative. Section 4.3 (p. 283) estimates 2920 annual scrubs for one wash/3 h and about 3950 for the dynamic schedule.

**Strongest limit/contrast.** `[SOURCE]` S3 already predicts the upcoming hour and acts during that hour (Secs. III and V.A). Therefore S5 does not first add the `t+1` idea; it makes the input/output window explicit. The online-learning option is discussed, not experimentally evaluated. RMSE is named but values and residuals are absent. S4/S5 nominally comparable March totals differ (294/1152/4752 versus 241/1008/3312) without reconciliation.

**Scope.** S5 combines the PBD controller and random-bit historical injection/static-policy methodology, but continues to use different PBD 24-bank and 20-Mbit comparison aggregations. It is a bounded extension primarily by consolidation, not evidence that all components form one validated hardware implementation.

**Assessment:** **PARTIALLY_SUPPORTED** at the submitted wording; High confidence in the correction.

**Wording correction.** Replace “adds … a `t+1` target” with “newly specifies the six-hour input vector and makes the already present next-hour/`t+1` target explicit.”

**What could change it.** A line-by-line showing that S3 did not in fact target the upcoming hour would be needed to restore the original “adds `t+1`” wording; the checked S3 text directly contradicts that reading.

**Model-design consequence.** S5 is the strongest single family-level architecture comparator, while S3 remains necessary for feature provenance and S4 for the separate evaluation branch.

### Candidate 4 — PBD threshold versus DEC-001 reliability

**Atomic decomposition.** (4a) exact random-placement event; (4b) interpretation as accurate counting; (4c) non-identity with DEC-001 `E_cap/F_A`.

**Strongest supporting evidence.** `[SOURCE]` S3 Sec. V.A (PDF pp. 4–5) and S5 Sec. 4.1 (journal p. 281) define

`P = C(B,F)(2n)^F / C(B·2n,F)`.

The denominator chooses `F` distinct fault positions among `B·2n` bits; the numerator chooses `F` distinct primary–redundant byte pairs and one of `2n` bit positions in each. The favorable event is therefore no pair collision, allowing accurate PBD fault counting under the model. `[INFERENCE]` DEC-001 instead defines first passage to ECC-capability exceedance over declared domain `A`, horizon and initial distribution.

**Strongest limit/contrast.** `[SOURCE]` S3/S5 qualitatively discuss EDC/EDNC/ENDNC and use broader “reliability/correction-rate” terminology in result tables. These outcomes are related to protection behavior, but neither source defines a mission-window first-passage event or maps the combinatorial `P` to `F_A`. S4's empirical HSIAO correction percentage is a third, incompatible metric.

**Scope.** PBD duplication plus parity per byte; conditional on fixed `F`; uniform sampling without replacement; one wash interval; dimensionless `P`; no arrival timing, parent multiplicity, general initial state, or protection-domain first passage.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** A formal source derivation equating the PBD event to a declared `E_cap` for a restricted domain, initial state and repair policy could support a restricted bridge; none is present.

**Model-design consequence.** Chen's threshold can be reproduced as a source-specific comparator, but it cannot be substituted for the project reliability contract.

### Candidate 5 — uncertainty is not propagated to action

**Atomic decomposition.** (5a) measurement/classification uncertainty; (5b) radiation/cross-section/environment-model uncertainty; (5c) forecast uncertainty.

**Strongest supporting evidence.** `[SOURCE]` S3 reports a 60/40 split and point `R²`; it supplies no confidence/prediction interval or action margin. S4's Monte Carlo correction table reports no trial count or confidence interval and has no predictor. S5 adds 10-fold CV and names RMSE, but publishes neither RMSE values nor residual/calibration intervals and passes a point forecast to the threshold rule. Across the family, GOES/ACE-SIS inputs, reconstructed spectra, target cross sections/Weibull parameters and CREME96 outputs are used as fixed inputs. PBD/HSIAO missed, uncorrected or classification behavior is not converted into observation uncertainty at the controller input.

**Strongest limit/contrast.** `[SOURCE]` Cross-validation and comparative predictive metrics in S3/S5 are uncertainty-related validation evidence, and S4 uses Monte Carlo. They are not propagated uncertainty. `[INFERENCE]` The absence claim concerns the action computation, not a claim that the papers perform no stochastic or validation analysis.

**Scope.** Measurement noise/classification, physical-rate model uncertainty, and predictive uncertainty are different objects. Forecast uncertainty is not applicable to S4's evaluated controller, but no family member propagates all relevant uncertainty to the action.

**Assessment:** **SUPPORTED**, Medium-high confidence.

**What could change it.** Supplementary code or equations showing intervals/posteriors entering the threshold, rounding or robust action would contradict the claim for that version. No such material is identified in the accepted cards.

**Model-design consequence.** A future project law can treat uncertainty-to-action propagation as a comparison dimension only if it is defined and quantitatively shown to affect feasibility, risk or action.

### Candidate 6 — no physical MCU parent marks or explicit `W`

**Atomic decomposition.** (6a) joint parent-event mark; (6b) explicit physical-to-logical `W`; (6c) evidential consequence of random logical injection.

**Strongest supporting evidence.** `[SOURCE]` S3/S5 give equal weight to `F`-subsets of logical bit positions in the PBD equation. S4 Sec. III.B and S5 Sec. 3.2 use a random RTL bit-address generator. S3/S5 qualitatively enumerate PBD MBU outcomes and S4 evaluates HSIAO double-bit behavior, but none stores a particle identity, physical coordinates/topology or a joint multiword mark, and none defines a physical-cell-to-logical map/interleaver `W`.

**Strongest limit/contrast.** `[SOURCE]` The family does model logical multiple-fault consequences and ECC-specific correction behavior; it is not devoid of multiple-bit analysis. `[INFERENCE]` The limitation is specifically provenance and mapping. A random logical location model could be adequate in a restricted domain if its reduction validity were separately demonstrated, but these texts do not provide that demonstration for DEC-001 `F_A`.

**Scope.** Modeled marginal hourly fault count and random logical placement; PBD byte-pair or HSIAO word aggregation; no physical event-to-cell-to-word transformation; no DEC-001 first-passage output.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** A controlled supplement containing physical event labels, coordinate topology and an explicit `W`, or a proof that their reduction preserves the queried first-passage metric, would narrow the claim.

**Model-design consequence.** Event provenance/`W` is potentially load-bearing only if the project demonstrates a reliability- or decision-level effect or a valid reduction bound; its mere absence from Chen is not a contribution statement.

### Candidate 7 — scrub proxy versus multi-component resource vector

**Atomic decomposition.** (7a) status of scrub count/frequency; (7b) measured coverage of the submitted resource components.

**Strongest supporting evidence.** `[SOURCE]` S3 reports washes/hour and qualitative high-frequency performance concern. S4 Table III reports total scrubs and comparative scrub-count factors. S5 Tables 4/6 and Sec. 4.3 report event totals and annual counts. `[SOURCE]` S3/S5 cite inherited 4% PBD area and make qualitative performance/power statements. `[UNKNOWN]` None measures energy/power, memory traffic/bandwidth occupancy, latency, contention/interference, and controller hardware/update overhead together as functions of action.

**Strongest limit/contrast.** It would be incorrect to say the family contains no resource information: scrub operations are a valid operational proxy; S3/S5 discuss area and computational demand; S5 estimates annual totals. The absence is of a measured multi-component vector, not of all resource consideration.

**Scope.** Scrub count is dimensionless over an event/year and frequency is washes/hour. The missing RQ-005 components require platform-specific units or justified proxies and an identified measurement stage.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** A source-linked implementation report measuring the named components across scrub regimes could supply the vector. Qualitative “negligible” or “moderate” statements alone would not.

**Model-design consequence.** Scrub count should be retained as one baseline resource component, but future comparison cannot infer energy, bandwidth or latency improvement directly from fewer scrubs.

### Candidate 8a — no formal reliability guarantee under propagated uncertainty

**Atomicity.** Atomic after separation from deployment evidence.

**Strongest supporting evidence.** `[SOURCE]` S3/S5 provide conditional PBD correct-count thresholds and point forecasts; S4 provides empirical correction percentages and scenario “Reliability.” `[SOURCE]` No version supplies a theorem, probabilistic bound, confidence-aware constraint, robust margin or formal relation to a mission/window failure event. Candidate 5 establishes that uncertainty is not propagated to action.

**Strongest limit/contrast.** `[SOURCE]` Threshold tables constrain modeled operation, and S4/S5 report 100% in selected simulation tables. These are meaningful modeled criteria/results, but their event definitions, uncertainty and external validity do not make them formal guarantees. The candidate must not be paraphrased as “no reliability treatment.”

**Scope.** Source-specific PBD or HSIAO metrics, modeled arrays and historical-derived scenarios; no DEC-001 first-passage contract and no propagated uncertainty.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** A formal guarantee with a declared event, domain, horizon, assumptions, estimator uncertainty and actuator feasibility would contradict the claim for the supplying version.

**Model-design consequence.** A project guarantee would be load-bearing only if it closes this full interface and is verified; merely renaming a threshold as reliability would not.

### Candidate 8b — no complete deployed observation-to-actuation loop

**Atomicity.** Atomic after separation from the mathematical guarantee claim.

**Strongest supporting evidence.** `[SOURCE]` S3 presents an architecture and analytical/historical evaluation and cites prior PBD/predictor hardware. S4 evaluates RTL random fault injection and HSIAO control without the forecast loop; FPGA is future work. S5 uses Scikit-learn/Keras processing, RTL injection and PBD architecture and cites prior VHDL/LEON3 PBD work; it does not report a single integrated deployed controller. All three evaluate modeled/simulated historical-derived sequences rather than a complete in-orbit or integrated FPGA observation-to-actuation system.

**Strongest limit/contrast.** The family contains more than a paper algorithm: there is RTL/testbench evidence, architectural control flow and cited prior component implementation. The admissible absence is the **complete integrated deployed loop**, not “no hardware evidence.”

**Scope.** Deployment evidence means one traced implementation containing observation acquisition, predictor/risk computation, decision, timer update and physical scrub actuation with measured timing/resource behavior.

**Assessment:** **SUPPORTED**, High confidence.

**What could change it.** A controlled implementation paper or artifact demonstrating the complete integrated chain would overturn this family-level absence. Separate component papers would narrow the implementation gap but would not alone establish integration.

**Model-design consequence.** Complete hardware closure is a later feasibility/validation dimension. It should not be treated as a unique method feature unless its architectural consequence is specified and tested.

## 6. Cross-version limitations that constrain all assessments

1. `[UNKNOWN]` S4 and S5 give different nominal March 2012 scrub totals: 294/1152/4752 versus 241/1008/3312, and 16× versus 13×, without a stated methodological reconciliation.
2. `[UNKNOWN]` S4 Table III and S5 Table 4 do not formally define the reported “Reliability” event/denominator.
3. `[SOURCE]` S5 calls a 99.99% value a correction-rate target although its preceding equation/table define a PBD correct-count probability.
4. `[UNKNOWN]` The PBD 24-bank / 1,811,939,328-bit calculation and the 20-Mbit static comparison are not linked by an explicit normalization narrative.
5. `[UNKNOWN]` The exact observation transformation, controller rounding/update/saturation, reset/writeback timing and invalid-forecast behavior are not specified.

These inconsistencies do not defeat the structural feature assessments above, but they prevent numerical threshold or scrub-saving transfer into the project.

## 7. Does the Chen family contain the same integrated DEC-002 feature combination?

**Bounded answer: no at the load-bearing interface level, but it contains a close high-level architectural analogue.**

`[SOURCE]` S5 combines historical radiation-derived rates, random logical fault injection, a PBD protection surrogate, recent-rate prediction and adaptive wash-frequency selection. S3 directly establishes the forecast-driven control law, while S4 supplies the separate time-series injection/static-comparison branch.

`[INFERENCE]` This overlaps materially with the latter portions of DEC-002 and is close prior art for:

- internal memory fault-count/rate observation;
- next-hour point forecasting;
- threshold-to-restoration-frequency selection;
- historical time-varying fault-injection evaluation;
- scrub count/frequency as a resource proxy.

`[INFERENCE]` It is not the same complete DEC-002 combination because the controlled family does not supply, in one validated chain:

- physical parent-event/MCU marks transformed through explicit `W`;
- a declared ECC-capability first-passage event and `F_A(t0,T;μ_t0)` bridge;
- an observation model covering classification error, latency and state identifiability;
- propagated measurement/radiation/forecast uncertainty in the decision;
- a formal reliability guarantee under that uncertainty and actuator constraints;
- a measured RQ-005 multi-component resource-cost vector;
- a complete deployed observation-to-actuation hardware implementation.

This finding is a bounded feature comparison. It neither announces novelty nor non-novelty.

## 8. Load-bearing future method-design dimensions

The following differences are genuinely load-bearing **only if the project makes them operational and demonstrates a decision-relevant consequence or a validity bound**:

1. **Physical-event and mapping bridge:** retained parent-event/topology information, explicit `W`, and quantified effect of reduction on ECC-level risk and selected restoration action.
2. **Reliability semantics:** an explicit DEC-001-compatible event, domain, initial state, trajectory/restoration semantics and first-passage calculation rather than a count/correction surrogate.
3. **Observation-to-state interface:** traceable conversion of internal/external observations into the estimator state, including missed/classified events, latency and update cadence.
4. **Uncertainty-to-action propagation:** measurement, radiation-model and forecast uncertainty carried to a risk bound or decision margin with stated coverage/robustness semantics.
5. **Action feasibility and resource vector:** bounds, rounding, hysteresis/fallback and a measured vector for scrub operations, traffic/bandwidth, latency/contention, energy/power and controller hardware/update cost.
6. **Integrated implementation evidence:** one complete observation → estimation/risk → decision → actuation implementation with reproducible timing and resource measurements.

The following are **not** usable as differentiating method features by themselves because S3/S5 already establish them or the family already covers them materially:

- radiation variation or point prediction;
- online fault-count/rate input;
- ML next-hour forecasting;
- adaptive wash/scrub-frequency selection;
- threshold lookup followed by frequency adjustment;
- historical radiation-driven random fault injection;
- static-policy comparison;
- scrub-count reduction alone.

## 9. Evidence gaps, blockers and additional-source recommendation

### Current blocker disposition

**No additional Chen-family source is required before proceeding with bounded future method design or RQ-004/RQ-005 mapping.** S3, S4 and S5 are sufficient to establish the family-level feature boundary and close comparison baseline.

No newly material external source was identified in the targeted Scite check, so no `HANDOFF TO ZOTERO` is issued.

### Named gaps that do not currently justify another Paper Card

| Gap | Exact missing proposition | Exact source class that would be needed if it becomes decision-blocking | Current disposition |
|---|---|---|---|
| `G-CHEN-OBS` | A deployed transformation from raw PBD/HSIAO outcomes, including EDNC/ENDNC and resets, into the hourly predictor input with latency/error characterization | Upstream Chen predictor/monitor full text or implementation artifact that specifies the runtime interface; S2 (2022) is the first bounded candidate already identified | Not blocking now; relevant only when RQ-004 selects this channel |
| `G-CHEN-HW` | One integrated hardware implementation of observation, prediction/risk, decision and scrub actuation | Peer-reviewed integrated FPGA/ASIC implementation report or reproducible artifact, not separate cited component demonstrations | Not blocking analytic method design; later implementation-validation gap |
| `G-CHEN-COST` | Measured action-dependent energy, bandwidth, latency/contention and controller cost | Hardware measurement study over multiple scrub regimes with operational definitions and uncertainty | Belongs to targeted RQ-005 evidence, not a reason to expand the Chen family automatically |
| `G-CHEN-NUM` | Reconciliation of S4/S5 March totals, event slice, rounding and “Reliability” denominator | Author correction/supplement, reproducible data/code, or an explicit journal-method appendix | Blocks numerical reuse of those totals, not structural comparison |

### When a bounded additional evidence task would be justified

A narrow task is justified only if a pending decision explicitly depends on one of these propositions—for example, whether a PBD counter can serve as a feasible RQ-004 observable with known latency/error, or whether a claimed hardware/resource distinction survives the authors' cited component implementations. In that case, the handoff should name the exact upstream source or implementation artifact and the single interface proposition to verify. It should not become a general control-literature search.

## 10. Recommendation to the Research Orchestrator

1. Accept candidates 1, 2, 4, 5, 6, 7, 8a and 8b for later claim consideration only with the bounded wording in Section 3.
2. Accept candidate 3 only after correcting “adds `t+1`” to “makes the existing next-hour target explicit while newly specifying the six-hour input window.”
3. Treat S5 as the strongest single architecture comparator, while retaining S3 for feature provenance and S4 for the distinct HSIAO evaluation branch.
4. Carry the six load-bearing dimensions in Section 8 into future method design as testable comparison axes, not as novelty statements.
5. Do not request another Chen-family Paper Card before proceeding. Open a bounded evidence task only when a named RQ-004/RQ-005 or implementation decision turns on `G-CHEN-OBS`, `G-CHEN-HW`, `G-CHEN-COST`, or `G-CHEN-NUM`.

No permanent claim/evidence identifier, project control model, numerical reliability requirement, or change to DEC-002 is created by this draft.
