# NORMATIVE-BASELINE-01 — clause-level extraction matrix

## 1. Task metadata and scope

| Field | Value |
|---|---|
| Task | `NORMATIVE-BASELINE-01-EXTRACTION` |
| Related canonical objects | `DEC-002`; `RQ-002`; `RQ-006`; `EXP-001` |
| Canonical base | `e1e7b93cc72b7b295a8298560adf2cd507d7256b` |
| Working branch | `pa/normative-baseline-01` |
| Extraction date | 2026-08-30 |
| Source gate | Three supplied full-text PDF copies only; no broad standards search and no product-conformity assessment |
| Output status | `ACCEPTED WITH LIMITATION / PARTIAL — NAMED INPUT NEEDED`; no permanent evidence or claim IDs assigned |

Evidence labels used below:

- **SOURCE** — stated in the supplied full text; the clause/page is given.
- **INFERENCE** — interpretation needed to connect source objects without attributing the interpretation to the document.
- **UNKNOWN** — the controlled source set does not resolve the point.

For the two RD documents, printed page numbering begins after three front-matter PDF pages. Citations therefore give both printed page and PDF page when they differ. For the STO, printed and PDF page numbers coincide in the relevant body.

## 2. Source and copy provenance

| Source | Exact identity visible in supplied copy | Supplied-copy integrity | Copy disposition |
|---|---|---|---|
| `РД 134-0174-2009` | *Аппаратура радиоэлектронная бортовая космических аппаратов. Методы расчета показателей стойкости интегральных микросхем к воздействию заряженных частиц космического пространства по одиночным сбоям и отказам по результатам прямых испытаний на ускорителях заряженных частиц*. Approval/registration statements: approved in the 4th quarter of 2009, registered 2009-12-07 No. 19719; effective date 2010-07-01. 27 PDF pages. | Canonical PI-supplied copy SHA-256: `7de0db483fb6a912b0e8bcdbfff1b0cc46ff5216e0374e7cd4a05130584b8f37`. Paper Analyst processed-copy SHA-256: `272406fc0703177bd5fd59207a271033d878a218c4e08ee7fc651d3cd6bb0478`. | **SOURCE:** Identity is established from the title page/front matter. **ADMINISTRATIVE DISPOSITION:** the first hash identifies the canonical supplied source and the second a reprocessed analysis copy. The extraction is accepted as content-bounded; byte identity between copies is not claimed and scientific content is not reopened absent a material content difference. |
| `РД 134-0175-2009` | *Аппаратура радиоэлектронная бортовая космических аппаратов. Методы испытаний цифровых сверхбольших интегральных микросхем на стойкость к воздействию отдельных высокоэнергетических протонов и тяжелых заряженных частиц космического пространства на ускорителях заряженных частиц*. Front matter states reissue under notice No. 752-02-2012 with Amendment 1; registered 2009-12-07 No. 19720; effective date 2010-07-01. 37 PDF pages. | Canonical PI-supplied copy SHA-256: `5cb73d6ac1c42aa8050d669d1e303898e528785c43c6ed7ec1e9a64adf4792dd`. Paper Analyst processed-copy SHA-256: `4fc7f24edfa07c82de78c5b6d708ac96459e7887b0ea03e2509219ee5d89830e`. | **SOURCE:** Identity and reissue statement are visible in the supplied full text. **ADMINISTRATIVE DISPOSITION:** the first hash identifies the canonical supplied source and the second a reprocessed analysis copy. The extraction is accepted as content-bounded; byte identity is not claimed and scientific content is not reopened absent a material content difference. |
| `СТО ГК Роскосмос 04.01.0005–2022` | *Ракетно-космическая техника. База электронная компонентная. Порядок проведения испытаний с использованием типовых методик испытаний электронной компонентной базы на стойкость к воздействию ионизирующих излучений космического пространства по одиночным и дозовым эффектам с учетом специфики различных испытательных установок и оценкой их погрешностей*. 248 PDF pages. Front matter states approval by Roscosmos order of 2022-07-18 No. ЛА-319-рсп and registration on 2022-07-25 No. 22043; body gives effective date 2022-11-01. | SHA-256: `80373578c8fc04349743f9d084ef831e329147f29d8d2e8c929d78d0bbab9ff5`, matching the handoff. | **AMBIGUOUS. SOURCE:** The supplied copy repeatedly contains the marking `(Проект, окончательная редакция)` while also containing approval, registration, and effective-date statements (pp. 2, 11 and repeated headers). These statements do not establish that the file is the exact controlled edition. |

**Integrity note:** No scientific or normative statement below is generalized beyond the visible text of the supplied source identities. The two RD hash pairs are normalized as source-copy versus processed-copy provenance; they are not scientific blockers. The STO controlled-edition ambiguity remains unresolved.

## 3. Clause-level stage matrix

### Stage 1 — irradiation input

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §§5.6–5.17, printed pp. 8–14 (PDF pp. 11–17); §§6–9, printed pp. 14–21 (PDF pp. 17–24) | **SOURCE:** Direct irradiation of digital VLSI by high-energy protons or heavy ions; test inputs include proton energy or ion LET, particle fluence, sample operating mode and temperature. Test conditions and controlled effect types are set in the test program/private PMI. | Energy: MeV; LET: MeV·cm²/mg; fluence: cm⁻²; flux: cm⁻²·s⁻¹. Fluence uncertainty is limited by §5.8; field nonuniformity by §5.9. Flux limits and energy/LET at the active surface are specified in §§5.10–5.13. | Retains radiation species/energy or LET, exposure and sample/test mode at test-stage level. It does not by itself retain cell topology or logical mapping. |
| `СТО 04.01.0005–2022`, §§6.5.1.1–6.5.1.9, pp. 56–58; §§6.5.2.6–6.5.2.14, pp. 59–61; §§7.5.1.1–7.5.1.5, pp. 91–92; §§7.5.2.4–7.5.2.13, pp. 92–94 | **SOURCE:** Heavy-ion and proton test sequences specify direct irradiation, LET/energy points, fluence monitoring, flux ranges, sample modes and stopping conditions. Ion tests stop at one of several conditions, including at least 100 events of a defined type or a fluence/dose/catastrophic-failure bound; proton tests likewise target at least 10² events of a defined type. | Ion LET: MeV·cm²/mg(Si); ion fluence: cm⁻²; ion flux: 10–10⁵ cm⁻²·s⁻¹ (§6.5.1.6). Proton energy: MeV; proton flux: 10⁶–10⁹ cm⁻²·s⁻¹ (§7.5.2.6). Conditions, modes and measurement periodicity are partly mandatory and partly private-PMI-dependent. Beam/fluence uncertainty is handled in §§6.4, 6.6, 6.7.5, 7.4, 7.6 and 7.7.5. | Retains irradiation settings and monitored fluence. Whether individual particles are timestamped or linked to diagnostic observations is **UNKNOWN** and PMI/software-dependent. |
| `РД 134-0174-2009`, §§6.2, 6.4, 6.6, printed pp. 7, 10–11 (PDF pp. 10, 13–14) | **SOURCE:** This is not a test procedure. It consumes experimental cross-section curves and mission differential particle spectra after shielding. | LET or energy spectra in differential-flux units; cross sections in cm²; orbit/shielding inputs are required by §6.6. | Raw irradiation and diagnostic records are already aggregated before this document's calculation begins. |

### Stage 2 — functional diagnosis

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §§5.14–5.16, printed pp. 9–11 (PDF pp. 12–14) | **SOURCE:** Remote functional diagnosis during irradiation must completely register SEU in memory/registers, SEFI, SEL and microdose effects. SEU is inverse state in one or more bits relative to the previously written state while the element remains writable. Circuit, clocking, initialization and other diagnostic conditions are set in PI/PMI. | Output is detected effect occurrence and functional/electrical observations; no standardized bit-log schema or timing unit is defined. Diagnostic completeness is mandatory, implementation is PMI-dependent. | Potentially retains bit-level observations in the test system, but the mandatory record structure, address semantics and event grouping are not specified. |
| `СТО`, §§6.4.6–6.4.12, pp. 55–56; §6.5.1.7, p. 58; §§6.7.3.1–6.7.3.2, pp. 84–85; §§7.7.3.1–7.7.3.3, pp. 99–100; §3.26, p. 23 | **SOURCE:** Functional diagnosis must remotely register events and allow separate registration or later classification of different ORE types. The algorithm and specialized software are part of the private PMI. Criteria for MBU/MCU/SMU and several other effects are also defined/refined/agreed in the private PMI; software or manual classification uses those criteria. | No universal sample interval, address format or classifier error model is specified. Completeness/separate classification are mandatory goals; concrete realization is PMI-dependent. | Direct diagnostic data can exist during testing, and §15.1 requires direct results in the test protocol. Exact raw-data preservation is **UNKNOWN** because the PMI/software schema is absent. |
| `РД 134-0174-2009` | **SOURCE:** No functional-diagnosis procedure. | Not applicable at this stage. | Does not consume raw diagnosis. |

### Stage 3 — raw bit/address observations

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §5.14, printed pp. 9–10 (PDF pp. 12–13) | **SOURCE:** Observation is a changed state in one or more bits relative to the written state. | Bit count is dimensionless. No address representation, sampling interval or relation between address and physical cell is given. | Bit inversion is observable. Physical cell coordinate, logical word identity, codeword identity and parent particle are **UNKNOWN**. |
| `СТО`, §7.6.9, p. 98; §§6.7.3 and 7.7.3, pp. 84–85, 99–100; §15.1, pp. 186–187 | **SOURCE:** Proton multibit analysis uses “analysis of adjacent upset addresses”; functional diagnosis and software are PMI-defined; the protocol includes direct test results and testing algorithms. | “Address” has no stated unit or formal address-space definition. | **UNKNOWN:** The registered address could be a logical interface address, a test-pattern position, a physical address exposed by the DUT, or another diagnostic identifier. The controlled texts do not establish that it is a physical cell coordinate. |
| `РД 134-0174-2009` | No raw bit/address input. | Not applicable. | Address/topology is absent. |

### Stage 4 — reconstruction and classification of SEU/MBU/MCU/SMU

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §5.14, printed pp. 9–10 (PDF pp. 12–13); Appendix A, printed p. 22 (PDF p. 25) | **SOURCE:** SEU may invert one or more bits and may have a multiple character under one particle. No MBU/MCU/SMU taxonomy or reconstruction rule is supplied. | Classification is effect-type-level and PI/PMI-dependent. | Multiplicity can be observed in principle, but no standardized topology or separate multiplicity classes are carried forward. |
| `СТО`, abbreviation list pp. 28–29; §6.3.2, p. 54; §6.4.12, p. 56; Table B.1, p. 189 | **SOURCE:** MBU is the general multiple-bit case in neighboring bistable elements; MCU is stated as multiple-bit upset within one logical memory cell; SMU is stated in the abbreviation list as multiple-bit upset within one data word. Table B.1 adds descriptions involving adjacent bits of one byte, adjacent logical cells of a data word, and simultaneous neighboring bistables under one proton/ion. Concrete criteria and identification are private-PMI/software-defined. | Multiplicity is a count; topology is qualitative (“neighboring”, “one byte”, “one word”). No distance metric, adjacency graph, time gate or classifier uncertainty is supplied. | A PMI can retain classification and possibly topology, but the normative cross-section path only requires counts by the selected effect type. Internal terminology tension is addressed in §6 below. |
| `РД 134-0174-2009`, §§3, 5–6 | **SOURCE:** Uses ОС/ОО type-specific cross sections and rates, not MBU/MCU/SMU reconstruction. | Not applicable. | Multiplicity/topology are lost unless supplied as separate effect-specific cross-section curves. |

### Stage 5 — parent-event association

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §§3.5–3.9, printed pp. 4–5 (PDF pp. 7–8); §5.14; Appendix A | **SOURCE:** Definitions connect a single radiation effect to an individual proton or heavy ion, and Appendix A says multiple-bit character can arise under an individual particle. | No event timestamp, coincidence window, scan period or grouping algorithm. | Physical single-particle provenance is definitional, but reconstruction from multiple addresses to one observed parent event is **UNKNOWN**. Independent sequential upsets are not explicitly separated. |
| `СТО`, abbreviation list pp. 28–29; Table B.1 p. 189; §6.4.12 p. 56; §7.6.9 p. 98 | **SOURCE:** Table B.1 associates one multiple-upset description with simultaneous neighboring bistables under one proton/ion; proton processing groups via adjacent upset addresses. Criteria are PMI-defined. | No formal simultaneity interval or rate-dependent false-association model. | Parent-event provenance may be inferred by a PMI-specific diagnostic method, but it is not guaranteed by adjacency alone. **INFERENCE:** Without timing/grouping rules, direct same-particle events and coincident/accumulated independent errors can be conflated. |
| `РД 134-0174-2009` | No parent-event object. | Not applicable. | Provenance is absent before convolution. |

### Stage 6 — classified counts

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §§5.6–5.9, printed pp. 8–9 (PDF pp. 11–12); Appendix G, printed pp. 26–29 (PDF pp. 29–32) | **SOURCE:** For each controlled ORE type and energy/LET point, the test produces event count `N_i` and fluence `Φ_i`; each ORE type is processed separately. | `N_i`: events; `Φ_i`: cm⁻². Random count error is modeled by a Poisson distribution; fluence has random/systematic error. | Retains type, sample and irradiation point. Loses individual address/topology/event mark unless retained in a separate test record. |
| `СТО`, §§6.4.1–6.4.3 pp. 54; §§6.6.1.1–6.6.1.3 pp. 76–77; §§7.4.1–7.4.3 p. 90; §§7.6.1–7.6.3 pp. 94–95; §7.6.9 p. 98 | **SOURCE:** Counts of a defined registered ORE type are formed at each fluence/energy/LET point. Proton multibit counts are first determined by adjacent-upset-address analysis, then processed through the common cross-section procedure. | Count is dimensionless/event count; fluence is cm⁻². Poisson count uncertainty and fluence uncertainty are explicit in §§6.6.1.2 and 7.6.2. | Type/multiplicity can be retained if separately classified. Address list and parent-event detail need not survive into `N_i`. |
| `РД 134-0174-2009` | Does not use classified counts directly. | Not applicable. | Count-level information is already reduced to cross section. |

### Stage 7 — cross-section calculation

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, §3.15 printed p. 6 (PDF p. 9); Appendix G printed pp. 26–29 (PDF pp. 29–32) | **SOURCE:** Cross section of a defined ORE type is based on observed type-specific event count divided by fluence. Appendix G treats zero-count, mixed and all-positive sample cases and returns central/upper/lower estimates. | `σ`, `σ_H`, `σ_L`: cm²; `Φ`: cm⁻²; confidence probability `P`: dimensionless. Poisson counts plus random/systematic fluence errors. Mandatory Appendix G. | Retains ORE type, irradiation point, sample/pool choice and confidence bounds. Discards event topology, addresses, timing and parent marks. |
| `СТО`, §3.23 p. 22; §§6.6.1.1–6.6.1.10 pp. 76–80, Eqs. (6.3)–(6.9); §§7.6.1–7.6.9 pp. 94–98, Eqs. (7.4)–(7.10) | **SOURCE:** Same type-specific estimator structure: zero-count upper bound; pooled estimator `(0.67 + ΣN_i)/ΣΦ_i`; per-sample estimator `(0.67 + N_i)/Φ_i`; confidence limits include fluence error and coefficients dependent on confidence and count. Multibit counts can be processed separately under §7.6.9. | cm². Count uncertainty is Poisson; fluence error is included multiplicatively. Separate cross sections are possible when the PMI defines and separately registers the effect type. | A scalar curve per selected class remains. Topology and provenance are not represented in the formula. |
| `РД 134-0174-2009`, §3.13 printed p. 4 (PDF p. 7); §§6.2–6.5 printed pp. 7–11 (PDF pp. 10–14) | **SOURCE:** Consumes `Σ_TЗЧ(Λ)` and `Σ_ВЭП(E)`; it does not reproduce the count estimator. | Cross section: cm²; the OSOT interface uses cm²/bit (Appendix A §3.3, printed p. 16/PDF p. 19). | Per-bit or device-scaled curve only; no event mark. |

### Stage 8 — sensitivity parameterization

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009`, test sections and Appendix G | **SOURCE:** Produces discrete cross-section points and confidence bounds; sensitivity-curve fitting is not the principal extraction in this document. | Energy/LET versus cm². | Retains discrete points; fitting is downstream. |
| `СТО`, §6.6.1.11 p. 80; §7.5.2.9 pp. 93–94 | **SOURCE:** Heavy-ion experimental cross-section dependencies are approximated to obtain threshold LET and saturation cross section for each PMI-registered effect using the referenced RD methods. A Bendel-type proton approximation is permitted for a specified control-test case and explicitly described as conservative. | Threshold LET: MeV·cm²/mg; saturation cross section: cm²; fit parameters depend on selected function. | Retains selected class and curve parameters; detailed observations are reduced. Parameter covariance is not provided in these clauses. |
| `РД 134-0174-2009`, §§6.3–6.5, Eqs. (6.2)–(6.8), printed pp. 7–11 (PDF pp. 10–14) | **SOURCE:** Fits ion cross section with a four-parameter Weibull or two-parameter alternative; introduces number of sensitive regions `B`, geometry and chord-length averaging. Proton cross section is fitted with recommended analytic functions. | `Λ_c`, `W`: LET units; `σ_SAT`: cm² per sensitive region/bit context; `B`: count; geometry: μm; device cross section: cm². Missing design data can be replaced by stated recommended/conservative geometry assumptions. | Retains class-specific curve and coarse sensitive-volume model. Loses address topology and logical organization except coarse scalar `B`; `B=N×k` for RAM SEU in Table 6.1. |

### Stage 9 — environment convolution

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009` | **SOURCE:** No mission-environment convolution. | Not applicable. | Stops at experimental cross sections. |
| `СТО` | **SOURCE:** The controlled clauses analyzed here define testing and cross-section extraction, not mission-spectrum convolution. | Not applicable in the selected chain. | Stops at cross section/sensitivity. |
| `РД 134-0174-2009`, §§6.1–6.6, Eqs. (6.1), (6.4), (6.6), printed pp. 6–11 (PDF pp. 9–14) | **SOURCE:** Integrates LET-dependent heavy-ion cross section against differential LET spectrum and energy-dependent proton cross section against differential proton spectrum. Radiation-field branches are calculated separately and then summed. Mission spectra derive from the system specification or referenced environment models with shielding. | Output `ν`: s⁻¹. Spectrum units are given in §§6.2 and 6.4; cross section is cm². Assumes the selected cross-section function and mission spectra are applicable. | Retains separate radiation-field contributions until summation. Does not retain individual event multiplicity/topology or time-varying mission history unless represented by the chosen spectrum/mode. |

### Stage 10 — rate calculation

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009` | No mission rate. | Not applicable. | — |
| `СТО` | No mission rate in the controlled extraction path. | Not applicable. | — |
| `РД 134-0174-2009`, §§5.3, 6.1–6.8, printed pp. 6–12 (PDF pp. 9–15); Appendix A §§3–4, printed pp. 14–21 (PDF pp. 17–24) | **SOURCE:** `ν` is the number of ОС/ОО per unit time. Separate proton/heavy-ion field contributions are summed. OSOT supports full-mission event number, mean per-day rate for a selected worst-year/solar-event case, and peak per-second rate for short mission intervals. The largest calculated sample rate can be selected for the lot (§6.8). | s⁻¹, day⁻¹, or event count over mission, depending on reporting mode. | Scalar type-specific rate/count remains. The selected horizon differs by OSOT mode and must not be conflated with a scrub or reporting window. |

### Stage 11 — probability indicator

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009` | No mission probability indicator. Confidence probabilities in Appendix G concern parameter estimation, not mission failure probability. | Dimensionless confidence probability `P`; distinct meaning from mission event probability. | No time/state model. |
| `СТО` | Confidence levels/bounds concern cross-section estimation. No `F_A`-like mission first-passage probability is defined. | Dimensionless confidence probability; not a mission reliability metric. | No memory state or windowed failure event. |
| `РД 134-0174-2009`, §5.3 Eq. (5.1), printed p. 6 (PDF p. 9) | **SOURCE:** `p = 1 − exp(−νT)`, where `T` is time the powered device is exposed to the mission proton/heavy-ion environment. | `p`: dimensionless; `ν`: time⁻¹; `T`: time. **INFERENCE:** The exponential no-event form corresponds to a constant-rate Poisson-style occurrence model over `T`. The document does not state a memory error state, repair process, initial distribution or codeword threshold. | Reduces the chain to one scalar occurrence probability for the selected ОС/ОО type and horizon. |

### Stage 12 — downstream interface to `W`, ECC, `E_cap` and `F_A`

| Document and location | Source object, inputs and outputs | Units, obligation, assumptions and uncertainty | Information retention / loss |
|---|---|---|---|
| `РД 134-0175-2009` | **SOURCE:** Does not define physical-to-logical mapping `W`, ECC decoder capability, protected domain `A`, scrub schedule or first-passage event. | **UNKNOWN:** Required downstream architecture fields. | Raw diagnosis might contain useful bits/addresses, but the standard does not require a post-`W` joint event mark. |
| `СТО`, §§3.26, 6.4.12, 6.7.3, 7.6.9, 7.7.3 and 15.1 | **SOURCE:** Private PMI must define algorithms, criteria, circuits, modes, software and reporting; adjacent upset addresses may be analyzed. No normative `W`/ECC transformation is supplied. | Target-specific inputs are mandatory downstream but not supplied by these sources. | Counts/cross sections alone cannot reconstruct physical topology, parent provenance or codeword occupancy. A retained raw diagnostic log may augment the interface if its semantics are documented. |
| `РД 134-0174-2009`, Table 6.1 printed p. 8 (PDF p. 11); Eq. (5.1) | **SOURCE:** Coarse RAM scaling uses `B=N×k`; a note mentions error correction for one flash-memory case. No codeword mapping, ECC threshold or repair semantics enter the rate/probability equations. | `N`, `k`, `B`: counts; `ν`: time⁻¹; `p`: dimensionless. | **INFERENCE:** `ν` or type-specific cross sections can serve as upstream inputs, but `p` is not automatically `F_A`. Mapping, event marks, state and controller semantics must be added. |

## 4. Cross-section → rate → probability formula chain

### 4.1 Test counts to cross section

**SOURCE — `РД 134-0175-2009`, Appendix G, printed pp. 26–29 (PDF pp. 29–32); STO §§6.6.1 and 7.6, pp. 76–80 and 94–98:**

For a defined effect type at one energy/LET point, the observed objects are event counts `N_i` and fluences `Φ_i` for samples `i`.

- Zero events for all samples: only an upper confidence bound is returned, of the form

  `σ_H = z(P) / [(1 − e_Φ) Σ_i Φ_i]`,

  where the supplied documents use their respective total relative fluence-error symbol.
- Some samples with events and some without:

  `σ = (0.67 + Σ_i N_i) / Σ_i Φ_i`.
- At least one event in every sample:

  `σ_i = (0.67 + N_i) / Φ_i`.
- Confidence bounds multiply the count estimator by tabulated `t_H(P,n)` or `t_L(P,n)` and divide by `(1 ∓ e_Φ)` times fluence.

**SOURCE:** Both documents state that observed count uncertainty is described by a Poisson distribution and combine it with random/systematic fluence uncertainty. The `0.67 + N` numerator is described as a median estimate of the Poisson mean.

**INFERENCE:** This Poisson statement is an inference model for test counts at a fixed irradiation point. It does not, by itself, establish a stationary Poisson process for mission-time errors within each SRAM word.

### 4.2 Cross-section points to sensitivity functions

**SOURCE — `РД 134-0174-2009`, Eqs. (6.2)–(6.8), printed pp. 9–11 (PDF pp. 12–14); STO §6.6.1.11 p. 80:**

- Heavy-ion cross-section points may be approximated by a four-parameter Weibull form with threshold `Λ_c`, saturation `σ_SAT`, scale `W` and shape `α`, multiplied by sensitive-region count `B`, or by the specified two-parameter alternative.
- `РД 134-0174` adds sensitive-volume geometry and chord-length angular averaging for an isotropic field.
- Proton cross-section points are approximated as functions of proton energy; the STO additionally permits a specified conservative Bendel-type relation for its control-test case.

**UNKNOWN:** The controlled source set does not require a joint covariance representation for fitted parameters or propagation of classification uncertainty from MBU/MCU/SMU grouping into the fit.

### 4.3 Sensitivity function to mission rate

**SOURCE — `РД 134-0174-2009`, Eqs. (6.1) and (6.6), printed pp. 7 and 10 (PDF pp. 10 and 13):**

`ν_TЗЧ = ∫_{Λ_c}^{Λ_max} Σ_TЗЧ(Λ) F_TЗЧ(Λ) dΛ`,

`ν_ВЭП = ∫_{E_c}^{E_max} Σ_ВЭП(E) F_ВЭП(E) dE`.

Radiation-field components are calculated separately and then summed (§6.1). Inputs require the mission orbit/environment and shielding (§6.6). Output is an effect rate, ordinarily time⁻¹.

**INFERENCE:** Recombination here is additive recombination of scalar rates for separately calculated radiation-field branches. It is not recombination of joint physical event marks, not a codeword mapping, and not a rule for preventing overlap between classification categories.

### 4.4 Rate to probability

**SOURCE — `РД 134-0174-2009`, Eq. (5.1), printed p. 6 (PDF p. 9):**

`p = 1 − exp(−νT)`.

**SOURCE:** `T` is powered exposure time and `ν` is the selected ОС/ОО intensity.

**INFERENCE:** This is a scalar at-least-one-occurrence probability under a constant-rate exponential survival form. It is compatible with `F_A(t0,T; μ_t0)` only in a specially reduced case where the paper's occurrence event, protected domain, initial state and absence/presence of restoration are explicitly matched. The normative text does not establish those conditions.

## 5. Information-retention matrix

| Representation level | Information retained | Information aggregated or discarded | Can parent event / address / topology be reconstructed? |
|---|---|---|---|
| Irradiation monitor + functional diagnosis | Radiation point, fluence/flux, device mode; bit-state changes and other functional/electrical effects may be directly observed | Depends on diagnostic hardware/software and test cadence | **UNKNOWN / PMI-dependent.** Potentially yes for some fields, but no mandatory raw-log schema is present. |
| Raw upset-address record | Address identifiers and changed values if the diagnostic software emits them | Physical coordinates, logical decoding and timing may be absent | Address identity is **UNKNOWN** without PMI, DUT documentation and software schema. Topology cannot be assumed from numerical adjacency. |
| Reconstructed SEU/MBU/MCU/SMU event | Effect label; potentially multiplicity, qualitative adjacency and a grouped parent | Unselected topology details; grouping ambiguity; false association | Only if the PMI explicitly defines event window, adjacency and provenance. The supplied sources do not. |
| Classified count `N_i` | Effect type, sample, energy/LET point, total events | Per-event addresses, multiplicity distribution within a broad class, topology, timestamps and parent marks | No. |
| Cross section `σ(type, E/LET)` + confidence bounds | Effect type, exposure coordinate and scalar occurrence area | Same as counts, plus sample/event individuality depending on pooling | No. |
| Sensitivity parameters | Selected effect type and reduced curve parameters | Individual data points unless separately retained; parameter dependence may be lost | No. |
| Environment-convolved rate `ν` | Selected effect type and scalar rate; separate radiation-field branches before sum | Energy/LET detail, event marks and topology | No. |
| Probability `p=1−exp(−νT)` | One scalar event probability and horizon `T` | All state, mapping, repair, word-age, topology and decoder-outcome information | No. |

## 6. Terminology conflicts and controlled meanings

| Term | SOURCE definition(s) | Analytical disposition |
|---|---|---|
| SEU / ОС | `РД 134-0175` §5.14 allows inverse state in one or more bits; its Appendix A says the upset may be multiple under one particle. STO §6.4.6 describes reversible inverted information restored after rewriting. | **INFERENCE:** “Single event” refers to radiation-event provenance, not necessarily one bit. A count of SEU is not automatically a count of upset bits. |
| MBU | STO abbreviation list p. 28: general multiple-bit upset in neighboring bistable elements/memory elements; Table B.1 p. 189: general multiple upsets. | Broad umbrella; exact grouping is PMI-dependent. |
| MCU | STO abbreviation list p. 28: multiple-bit upsets within one logical memory cell. Table B.1 p. 189 places descriptions involving adjacent bits of one byte and adjacent logical cells of a data word under the MCU row. | **SOURCE conflict/tension:** The text does not define a physical cell versus logical cell mapping. The “data word” description overlaps the abbreviation-list meaning of SMU. Do not import external conventional meanings. |
| SMU | STO abbreviation list p. 29: multiple-bit upset within one data word. Table B.1 p. 189 instead describes simultaneous upsets in neighboring bistables on a die under one proton/ion. | **SOURCE conflict/tension:** Table and abbreviation list emphasize different grouping axes (word versus physical simultaneity/adjacency). A private PMI must disambiguate the operational classifier. |
| “Address” | STO §7.6.9 uses “adjacent upset addresses” without a formal address definition. | **UNKNOWN:** Physical cell, logical address, test-pattern position and codeword position cannot be distinguished from the controlled texts. |
| Confidence probability vs mission probability | `РД 134-0175` Appendix G and STO §§6.6/7.6 use `P` for confidence bounds; `РД 134-0174` Eq. (5.1) gives an occurrence probability over exposure time. | These are incompatible statistical objects and must not be combined or reported as one probability. |

## 7. Answers to mandatory extraction questions

1. **What does a registered address mean?**
   **UNKNOWN.** STO §7.6.9, p. 98, only says that multibit counts are found by analyzing adjacent upset addresses. §§3.26, 6.7.3 and 7.7.3 defer the diagnostic algorithm/software to the private PMI. Neither RD document resolves whether the identifier is a physical cell, logical interface address, test-pattern position or another object.

2. **How are several upset addresses linked to one parent event?**
   **SOURCE:** The STO uses adjacency analysis and describes some multiple upsets as simultaneous under an individual proton/ion (Table B.1, p. 189), while criteria are PMI-defined (§6.4.12, p. 56).
   **UNKNOWN:** No coincidence window, scan period, timestamp requirement, adjacency graph or false-association rule is defined. Parent-event reconstruction is therefore PMI/software-dependent.

3. **Where and how are MBU/MCU/SMU defined?**
   **SOURCE:** STO abbreviation list pp. 28–29 and Table B.1 p. 189; operational criteria in §6.4.12 p. 56. The definitions and internal tension are recorded in §6 of this draft. `РД 134-0175` only says SEU can have a multiple-bit character; it does not define these three classes.

4. **Are multiplicity, topology, address and event provenance retained?**
   **SOURCE:** Type-specific counts can be retained and separately processed; multibit addresses may exist during diagnosis.
   **INFERENCE:** Cross-section formulas retain a selected type count but not the joint mark. Multiplicity distributions, topology, addresses and parent provenance survive only if separately preserved by the PMI-defined diagnostic log; this is not mandated by the controlled formulas.

5. **Which data exist only during functional diagnosis?**
   **INFERENCE from §§5.14–5.16 RD 134-0175; §§3.26, 6.7.3, 7.7.3 and 15.1 STO:** individual bit values, address identifiers, observation timing/order, test-pattern context, rewrite/reset actions and potentially raw current/function traces can exist at diagnosis time. Their exact schema and retention are **UNKNOWN** without the PMI, software description and test protocol.

6. **Which data pass into the normative cross section?**
   **SOURCE:** Classified effect count `N_i`, fluence `Φ_i`, irradiation coordinate (energy or LET), sample identity/pooling case, fluence uncertainty and confidence probability. The result is a type-specific scalar cross section and bounds in cm².

7. **Are separate cross sections by multiplicity/type/mechanism allowed or required?**
   **SOURCE:** `РД 134-0175` Appendix G processes each controlled ORE type separately; STO §§6.4.3, 6.6.1.11 and 7.6.9 allow separate registered types, including a multibit class, to receive separate processing. Which types are controlled is PMI-dependent.
   **UNKNOWN:** A complete multiplicity-resolved series and separate same-particle versus accumulated/false-event cross sections are not universally required.

8. **How is recombination performed?**
   **SOURCE:** `РД 134-0174` §6.1 calculates radiation-field/proton/heavy-ion contributions separately and sums the calculated scalar rates.
   **UNKNOWN:** The source set supplies no non-overlap rule for MBU/MCU/SMU categories and no recombination rule for a joint post-mapping event mark. Double counting is possible if PMI-defined categories overlap and their rates are later summed without a partition rule.

9. **Which statistical assumptions apply to tests and which to mission extrapolation?**
   **SOURCE:** Test-count uncertainty is Poisson in `РД 134-0175` Appendix G and STO §§6.6.1.2/7.6.2; fluence has random/systematic uncertainty. Mission convolution uses cross-section curves and environment spectra in `РД 134-0174` §§6.1–6.6. Eq. (5.1) applies an exponential occurrence-probability form.
   **INFERENCE:** The test Poisson count model does not prove stationary independent arrivals to each codeword in mission operation. Eq. (5.1) is consistent with a constant scalar rate over `T`, but no marked accumulation or repair process is specified.

10. **How are reset, correction, rewrite and reinitialization handled?**
    **SOURCE:** STO §6.4.6 says an SEU is restored by rewriting the affected element. `РД 134-0175` §5.14 distinguishes short power interruption for SEL, reinitialization without power interruption for SEFI, and non-restoration for microdose hard error; §5.16 makes initialization conditions PMI-dependent. STO has analogous effect-specific restoration rules and PMI-defined algorithms.
    **UNKNOWN:** Timing of memory rewrite relative to observations, scrub policy, ECC correction/writeback, whether rewriting clears all accumulated errors, and word-age reset semantics are not specified for SRAM reliability modeling.

11. **What exactly does `РД 134-0174` aggregate?**
    **SOURCE:** It fits effect-type cross section versus LET/energy, scales/averages through sensitive-region/geometry assumptions, convolves with shielded mission spectra, sums separate radiation-field contributions into a scalar ОС/ОО rate, and optionally maps that rate to `p=1−exp(−νT)`. Table 6.1 uses `B=N×k` for RAM SEU.
    **INFERENCE:** It aggregates over physical locations, addresses, event topology, codeword mapping and repair history. OSOT reporting modes also aggregate over different mission horizons, which must remain distinct from scrub intervals.

12. **How does the probability indicator relate to DEC-001 `F_A`, and where is matching impossible?**
    **SOURCE:** `РД 134-0174` provides the probability of at least one selected ОС/ОО occurrence during powered exposure `T`. DEC-001 defines first passage of a word in explicit domain `A` beyond ECC capability, conditional on initial state/distribution `μ_t0`.
    **INFERENCE:** They can coincide only after an explicit reduction proves that one normative occurrence is exactly the `E_cap` event for the declared `A`, with compatible initial state and repair semantics. The controlled source set lacks this proof. In general, the normative `p` is not `F_A`.

13. **Which additional `W`/ECC assumptions are needed downstream?**
    **INFERENCE:** At minimum: physical/logical address semantics; deterministic or statistical mapping `W` from affected physical cells to ECC words/bits; interleaving and bank/row organization; post-`W` joint multiplicity mark; ECC threshold `t_c(w)` and decoder behavior; protected domain partition `A`; initial error state/distribution; correction/writeback/scrub schedule; word exposure ages; and a rule separating direct same-particle events from sequential accumulation and false grouping.

## 8. Compatibility, augmentation and incompatibility matrix

| Target | Compatible source elements | Required augmentation | Incompatibility / non-equivalence |
|---|---|---|---|
| `DEC-001` primitive event and `E_cap(A;t0,T)` | Type-specific empirical cross sections, confidence bounds, mission spectra and scalar rates can be upstream event-intensity inputs. | Declare `A`; map physical event marks through `W`; define word occupancy, `t_c(w)`, initial state and restoration semantics. | ОС/ОО occurrence and `p=1−exp(−νT)` are not automatically `E_cap`/`F_A`; confidence probability is a different object. |
| `DEC-001` `F_A(t0,T; μ_t0)` | `РД 134-0174` provides a time-horizon probability form for one scalar occurrence process. | State-transition/first-passage model, `μ_t0`, sequential ages, repair/scrub events, heterogeneous-domain partition and uncertainty propagation. | The normative scalar probability has no explicit word state, codeword threshold or first-passage path. |
| `RQ-002` arrival/error model | Test data support count-based rate estimation; test-count uncertainty is explicitly Poisson. Separate radiation mechanisms/fields can be evaluated. | Decide primitive arrival object; retain event mark; quantify stationarity/nonstationarity and clustering; model direct MCU versus independent accumulation; define state/reset. | Poisson test-count uncertainty does not establish HPP mission arrivals; Eq. (5.1) does not model accumulation. |
| `RQ-006` physical-logical mapping sufficiency | Functional diagnosis may expose changed bits/addresses; multibit classification uses adjacency; private PMI can define algorithms/software. | Obtain raw diagnostic schema, address semantics, physical floorplan/row/bank data, logical organization, interleaving and `W`; test sufficiency of reduced marks. | Type-specific marginal cross sections and counts cannot recover joint post-`W` occupancy or parent provenance. |
| `EXP-001` practical input chain | Provides a concrete test → count → cross-section → sensitivity → environment-rate → scalar-probability baseline. | Add target architecture, ECC/controller data, initial state, scrub policy and mapping; carry confidence/classification uncertainty. | The baseline does not by itself yield a W/ECC-aware adaptive restoration decision. |

## 9. Named unresolved inputs, each tied to one link

| Gap | Exact missing input | Unresolved link it controls |
|---|---|---|
| G1 — controlled-copy provenance | Exact controlled edition of `СТО ГК Роскосмос 04.01.0005–2022` or authoritative registry/controlled-copy extract reconciling the approval statements with the repeated `(Проект, окончательная редакция)` mark | Whether clause wording in the supplied ambiguous copy can be cited as the exact controlled edition |
| G2 — RD copy provenance | **RESOLVED ADMINISTRATIVELY:** canonical PI-supplied and Paper Analyst processed-copy hashes are both recorded in §2 | No remaining scientific blocker; byte identity is not asserted and content review reopens only if a material difference is found |
| G3 — private PMI | Representative SRAM private PMI fields: controlled effect types; MBU/MCU/SMU criteria; test pattern; address-space definition; diagnostic cadence; event grouping window; adjacency rule; initialization/rewrite/reset sequence; reporting fields | Raw observations → reconstructed/classified event; direct-event versus independent-accumulation partition |
| G4 — diagnostic software/log schema | Specialized functional-diagnosis software description and a representative raw output/protocol schema | Whether timestamps, multiple addresses, bit values, event IDs, topology and parent provenance are retained or recoverable |
| G5 — DUT physical/logical organization | Memory datasheet/architecture or test-house mapping: bank/row/column, cell-to-address decoding, word organization and any physical adjacency information | Meaning of “adjacent upset addresses” and construction of `W` |
| G6 — target ECC/controller fields | Codeword layout, interleaving, check-bit placement, ECC capability `t_c(w)`, decoder outcomes, correction/writeback policy, scrub/reset timing and protected-domain partition `A` | Cross section/rate → `E_cap`; state transition and controller-managed restoration |
| G7 — initial state and ages | `μ_t0` or explicit initial error state, per-word exposure age and last-correction/writeback state | Rate process → windowed first-passage probability `F_A(t0,T; μ_t0)` |
| G8 — mission radiation input | Applicable mission specification: orbit, duration/reporting windows, shielding distribution, proton/ion spectra and solar-event assumptions | Cross-section curve → environment convolution/rate for a particular mission |
| G9 — current applicability/currency layer | The applicable current normative calculation/testing documents named in canonical project status (`ГОСТ РВ 0020–57.415–2020`, `СТО 04.01.0008–2024`, `СТО 04.01.0010–2025`) and a determination of which supersedes/augments the supplied RD chain | Whether the extracted 2009 calculation/testing route is the current applicable route; this draft does not make that applicability claim |
| G10 — classification uncertainty | PMI- or experiment-specific false-split/false-merge model, confidence interval or validation for MBU/MCU/SMU grouping | Propagation of measurement/classification uncertainty into type-specific cross sections and then `E_cap/F_A` |

## 10. Explicit SOURCE / INFERENCE / UNKNOWN synthesis

### SOURCE

- The controlled documents provide a complete **scalar** chain from type-specific test observations (`N_i`, `Φ_i`) through cross sections and sensitivity fits to environment-convolved ОС/ОО rates and an exponential occurrence probability.
- Test-count uncertainty is modeled with a Poisson distribution; fluence has separately recognized measurement uncertainty.
- Separate effect types can be registered and processed separately when defined in the private PMI.
- The STO requires remote functional diagnosis and allows/uses adjacent-upset-address analysis for multibit classification.
- Concrete multibit criteria, diagnostic algorithms and specialized software are private-PMI-dependent.
- `РД 134-0174` sums separately calculated radiation-field contributions and provides multiple reporting modes/horizons.

### INFERENCE

- The scalar normative chain is a practical upstream baseline but is not a W/ECC-aware reliability model.
- Address/topology/provenance information is lost no later than conversion to class counts unless the test protocol separately preserves it.
- Adjacency without a documented address map and coincidence rule cannot establish a common parent particle.
- Summing overlapping PMI-defined multibit classes without a partition/non-overlap rule would create a double-counting risk.
- The exponential probability form is compatible with a constant scalar occurrence rate; it does not establish the stateful marked-arrival model needed for accumulation and adaptive scrubbing.

### UNKNOWN

- Exact controlled-edition status of the supplied STO copy.
- Byte relationship between the two supplied RD PDFs and the handoff-expected hashes.
- Meaning of “address” in the actual diagnostic system.
- Parent-event grouping window and error rate.
- Whether raw address/topology/provenance data are retained in the actual test protocol.
- Separate direct-same-particle versus accumulated/false-event cross sections.
- Target `W`, ECC capability/decoder semantics, `A`, `μ_t0`, scrub/writeback/reset schedule and word ages.
- Applicability of the legacy calculation chain to a particular present-day product/program without the current normative and PMI layers.

## 11. Final disposition

**Orchestrator acceptance: `ACCEPTED WITH LIMITATION`.**

**Scientific-chain classification: `PARTIAL — NAMED INPUT NEEDED`.**

**Rationale — INFERENCE:** The three supplied documents are sufficient to extract a reproducible practical baseline through the scalar test → cross-section → environment-rate → occurrence-probability chain. They do not contain the named PMI, raw-diagnostic, target-mapping, ECC/controller, initial-state and mission inputs required to extend that chain to `W`, `E_cap(A;t0,T)` and `F_A(t0,T; μ_t0)`. The ambiguous STO controlled-edition status remains a provenance limitation; the two RD hash differences are normalized as source-copy versus processed-copy provenance. No claim of normative deficiency or product compliance is made.

All three documents have an explicit disposition for every stage. Each remaining unresolved link is assigned to a named document, PMI field or target-architecture input in §9. Stop criterion for this bounded extraction is therefore met.
