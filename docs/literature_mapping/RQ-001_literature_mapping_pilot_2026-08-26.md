# RQ-001 Targeted Literature Mapping — Pilot Report

**Task ID:** RQ-001 literature-mapping pilot  
**Related RQ:** RQ-001  
**Role:** Literature Scout  
**Execution date:** 2026-08-26 (UTC)  
**Protocol status at start:** READY — SEARCH NOT STARTED  
**Report status:** PARTIAL COMPLETION — REFINE / ADDITIONAL LIMITED CYCLE REQUIRED

## 1. Scope and evidence boundary

### Research Question

Как должны быть определены reliability event, соответствующая метрика, уровень агрегации и временной горизонт для SRAM, защищённой ECC и периодическим scrubbing, чтобы сформулировать проверяемое ограничение надёжности?

### Scout boundary

- This report records discovery, bibliographic-identity checking, title/metadata screening and abstract screening.
- `SOURCE` in this report means information visible in publisher metadata/abstracts or verified bibliographic records.
- `INFERENCE` means a screening judgment about relevance to RQ-001.
- No claim-level paper analysis was performed.
- No `HYP`, `CLM` or `EVD` records were created.
- No numerical reliability threshold was selected.
- This report does not answer RQ-001 and does not establish a research gap.

### Databases and layers used

1. IEEE Xplore — primary discovery; all four protocol strings executed.
2. eLibrary — primary source planned; execution blocked before query submission by `403 Forbidden` in Cloud Work.
3. Public academic web search — supplementary location of known/related primary records and earlier seminal work.
4. Scite — secondary identity/editorial-signal check only.
5. ResearchRabbit — one limited backward/forward/similar pass after seed selection.

## 2. Reproducible search log

### 2.1 IEEE Xplore

**Common settings:** all content types; all publishers; English query syntax; target first-pass window 2000–2026. When all matching results were later than 2000, IEEE displayed the actual result-year span rather than retaining 2000 as the lower UI value. No pre-2000 result was excluded from the four protocol strings; earlier seminal works were added only by chaining as required by the protocol.

| ID | Exact executed query | UI year span / filter outcome | Hits | Title/metadata screened | Abstract screened | CORE | RELATED | BACKGROUND | REJECT |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| IEEE-Q1 | `"SRAM" AND ("error correcting code" OR ECC OR EDAC) AND (scrub* OR "memory scrubbing") AND ("uncorrectable error" OR failure OR reliability)` | 2004–2026; attempt to set 2000 normalized to first matching year 2004 | 20 | 20 | 20 | 4 | 5 | 3 | 8 |
| IEEE-Q2 | `("radiation tolerant memory" OR "spaceborne memory") AND (ECC OR "error correction") AND (scrub* OR "memory scrubbing") AND ("failure probability" OR "error probability" OR reliability)` | 2010 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| IEEE-Q3 | `("memory reliability model" OR "reliability modeling") AND (ECC OR "error correcting code") AND (codeword OR bank OR "memory array") AND ("mission time" OR "time interval" OR horizon)` | no results | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| IEEE-Q4 | `(SRAM OR "semiconductor memory") AND (scrub* OR "error correction") AND ("data loss probability" OR "uncorrectable word" OR "reliability event")` | no results | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total** | — | — | **21** | **21** | **21** | **5** | **5** | **3** | **8** |

**Deduplication within protocol output:** no duplicate record occurred between IEEE-Q1 and IEEE-Q2.

### 2.2 eLibrary

The following protocol strings were prepared exactly, but could not be submitted. Both the eLibrary search endpoint and the site home page returned `403 Forbidden` to the Cloud Work browser. A domain-restricted public web lookup also returned no eLibrary records. Therefore, recording `0 hits` would be false; the correct value is `UNKNOWN — NOT EXECUTED`.

| ID | Exact query to execute locally | Status | Hits | Screened |
|---|---|---|---:|---:|
| ELIB-Q1 | `(SRAM ИЛИ «статическая оперативная память») И («коррекция ошибок» ИЛИ ECC ИЛИ EDAC) И (скраббинг ИЛИ «восстановление памяти») И («неисправимая ошибка» ИЛИ «вероятность отказа» ИЛИ надежность)` | NOT EXECUTED — access blocked before submission | UNKNOWN | 0 |
| ELIB-Q2 | `(«радиационно-стойкая память» ИЛИ «космическая память») И («помехоустойчивое кодирование» ИЛИ «коррекция ошибок») И (скраббинг ИЛИ регенерация) И (отказ ИЛИ надежность)` | NOT EXECUTED — access blocked before submission | UNKNOWN | 0 |
| ELIB-Q3 | `(«модель надежности памяти» ИЛИ «вероятность потери данных») И (кодовое слово ИЛИ банк ИЛИ массив) И («время миссии» ИЛИ «временной интервал»)` | NOT EXECUTED — access blocked before submission | UNKNOWN | 0 |

### 2.3 Supplementary refinement queries

Public academic search was used only after the protocol strings exposed terminology gaps. The result engine did not expose stable exhaustive hit counts; only surfaced records were screened.

1. `"memory scrubbing" ECC reliability model uncorrectable error probability SRAM`
2. `"scrubbing" "mean time to failure" ECC memory`
3. `"two errors" "same word" memory scrubbing reliability`
4. `"periodic scrubbing" SRAM ECC reliability`

These queries exposed the terms `temporal double-bit error`, `ECC failure per scrub cycle`, `effective BER`, `MTTF`, `soft-error scrubbing recovery`, and `multiple events by accumulation`.

### 2.4 Scite secondary verification

Two targeted metadata batches were used:

- Seed/known-title identity batch: 10 titles supplied; 10 bibliographic records matched.
- ResearchRabbit expansion identity batch: 10 titles supplied; 10 bibliographic records matched.

For the three selected seeds, Scite returned no retraction, correction, expression-of-concern or erratum notice. It also returned zero classified contrasting statements. This is only an obvious-signal sanity check: absence of a returned signal is not an evidence audit and does not establish correctness or consensus.

### 2.5 ResearchRabbit limited pass

Default ranking was retained. For every non-empty route, the first 20 displayed records were title/abstract screened; results were deduplicated against the IEEE/Scite set.

| Seed | Similar total / screened | References total / screened | Cited-by total / screened | Main promoted records/categories |
|---|---:|---:|---:|---|
| Bajura et al., 2007 | 368 / 20 | 34 / 20 | 160 / 20 | Saleh 1990; Mukherjee 2004; Slayman 2005; SRAM MBU/interleaving studies; no new finite-mission requirement source |
| Maestro & Reviriego, 2009 | 457 / 20 | 33 / 20 | 31 / 20 | Goodman 1991; Yang 1995; Kontoleon 2003; Schiano 2004; Li 2013; MBU-aware reliability models |
| Rezaei et al., 2023 | 0 / 0 | 53 / 20 | 0 / 0 | Clemente et al. 2022 accumulation model; voltage-dependent SRAM radiation context |

**Expansion outcome:** new model/definition categories were added, especially an explicit accumulation-focused ECC reliability model and older Markov/scrubbing formulations. Consequently, the protocol’s saturation condition has not been met.

## 3. Screened candidate table

**Screening basis:** publisher title/metadata and abstract unless explicitly described as a chaining-only record. Classification is an `INFERENCE` for triage, not a finding about the paper’s full contents.

| ID | Candidate publication | Year / venue | DOI or stable identifier | Discovery route | Class | Screening reason |
|---|---|---|---|---|---|---|
| C01 | V. Vlagkoulis et al., “Configuration Memory Scrubbing of SRAM-Based FPGAs Using a Mixed 2-D Coding Technique” | 2022, IEEE TNS | IEEE 9714333 | IEEE-Q1 | REJECT | FPGA configuration-frame correction; abstract does not establish the RQ-001 data-SRAM event/metric/horizon. |
| C02 | Z. Zhang et al., “Extrapolation Method of On-Orbit Soft Error Rates of EDAC SRAM Devices From Accelerator-Based Tests” | 2018, IEEE TNS | [10.1109/TNS.2018.2875051](https://doi.org/10.1109/TNS.2018.2875051) | IEEE-Q1 | CORE | EDAC SRAM, scrub-time dependence and on-orbit SER; directly relevant to event-rate and mission aggregation. |
| C03 | Y. Lu et al., “A self-scrubbing scheme for embedded systems in radiation environments” | 2020, IOLTS | IEEE 9159718 | IEEE-Q1 | RELATED | Data SRAM and self-scrubbing architecture; formal event/aggregation requires full-text extraction. |
| C04 | X. Li et al., “A Fault-tolerant Method of SRAM FPGA Based on Processor Scrubbing” | 2021, IAEAC | IEEE 9390706 | IEEE-Q1 | REJECT | Processor scrubbing of FPGA configuration memory; outside the selected memory-service object. |
| C05 | M. Rezaei et al., “A Method to Neutralize the Impact of DVS on the Reliability of COTS SRAMs With ECC by Using Periodic Scrubbing” | 2023, IEEE TNS | [10.1109/TNS.2023.3332635](https://doi.org/10.1109/TNS.2023.3332635) | IEEE-Q1 | CORE | Modern COTS SRAM, embedded ECC, periodic scrubbing and a reliability constraint; DVS context limits direct transfer. |
| C06 | E. Marañon Aguilar et al., “Hardening a RISC-V Softcore for Embedded Aerospace Applications in SRAM-based FPGA” | 2024, SBCCI | IEEE 10703996 | IEEE-Q1 | REJECT | Configuration-memory TMR study rather than ECC-protected data-SRAM reliability definition. |
| C07 | R. Giordano et al., “A Self-Repairing and Adaptive FPGA-based High-speed Serial Link” | 2018, NSS/MIC | IEEE 8824418 | IEEE-Q1 | REJECT | Serial-link/FPGA-configuration application without the required memory reliability abstraction. |
| C08 | H. Zhang et al., “GUARD: GUAranteed reliability in dynamically reconfigurable systems” | 2014, DAC | IEEE 6881359 | IEEE-Q1 | RELATED | Reliability-guarantee and scrubbing/adaptation vocabulary may inform metric structure, but the object is reconfigurable configuration state. |
| C09 | E. Marañon et al., “Reliable AI Accelerator Design Using Multiple Fault-Tolerance Techniques on SRAM-Based APSoCs” | 2026, IEEE TNS | IEEE 11422045 | IEEE-Q1 | REJECT | System/accelerator design-space paper; no direct RQ-001 event/metric/horizon in the screened abstract. |
| C10 | S. S. Mukherjee et al., “Cache scrubbing in microprocessors: myth or necessity?” | 2004, PRDC | [10.1109/PRDC.2004.1276550](https://doi.org/10.1109/PRDC.2004.1276550) | IEEE-Q1; RR refs/similar | CORE | Defines temporal double-bit error in an ECC word, MTTF and fixed-interval scrubbing for SRAM cache. Transfer to standalone SRAM must be checked. |
| C11 | C. W. Slayman, “Cache and memory error detection, correction, and reduction techniques for terrestrial servers and workstations” | 2005, IEEE TDMR | IEEE 1545899 | IEEE-Q1; RR refs/similar | BACKGROUND | Broad trade-off/context source; not treated as primary formal evidence at Scout stage. |
| C12 | W. Grignani et al., “Characterization of a Fault-Tolerant RISC-V SoC in an SRAM-based FPGA Under Proton Irradiation” | 2026, LATS | IEEE 11480385 | IEEE-Q1 | REJECT | Configuration-memory irradiation/mitigation focus; no direct RQ-001 formalization in abstract. |
| C13 | H. Zhang et al., “Resource budgeting for reliability in reconfigurable architectures” | 2016, DAC | IEEE 7544353 | IEEE-Q1 | RELATED | Defines a reliability-oriented metric under scrubbing, but for reconfigurable accelerators; more relevant later to RQ-005. |
| C14 | C. J. Elash et al., “Design and Testing of a 32-bit Radiation-Tolerant RISC-V Microcontroller at the 22-nm FD SOI Node” | 2026, IEEE TNS | IEEE 11244098 | IEEE-Q1 | RELATED | Contains embedded SRAM and ECC outcome context; scrubbing/horizon relevance is unproven from abstract. |
| C15 | M. M. H. Galib et al., “Supply Voltage Decision Methodology to Minimize SRAM Standby Power Under Radiation Environment” | 2015, IEEE TNS | [10.1109/TNS.2015.2420094](https://doi.org/10.1109/TNS.2015.2420094) | IEEE-Q1 | CORE | Abstract links SRAM scrubbing power and radiation reliability; candidate for constraint and scrub-rate definitions. |
| C16 | U. Maffazioli et al., “Heavy-Ion Radiation Fault Analysis of URSA: A Reconfigurable Systolic Array for CNN Acceleration in SRAM-Based APSoC” | 2026, IEEE TNS | IEEE 11514164 | IEEE-Q1 | REJECT | Application-level APSoC fault analysis; not a reliability-event model for ECC-protected data SRAM. |
| C17 | J. Chen et al., “Space Radiation Flux Driven Fault Injection for Evaluating Dynamic Mitigation Strategies” | 2024, LATS | IEEE 10534594 | IEEE-Q1 | REJECT | Dynamic mitigation context but insufficient ECC-protected SRAM event/metric connection for RQ-001. |
| C18 | J. Gebelein et al., “Preparation of COTS TMS570 MCU for use in ionizing radiation environments” | 2016, RADECS | IEEE 8093205 | IEEE-Q1 | RELATED | CPU-coupled SRAM and dynamic scrubbing implementation; formal reliability outcome requires full text. |
| C19 | A. Simevski et al., “Scalable and Configurable Multi-Chip SRAM in a Package for Space Applications” | 2019, DFT | IEEE 8875489 | IEEE-Q1 | BACKGROUND | SRAM/space architecture context; no formal event/metric/horizon in screened abstract. |
| C20 | D. Yu-Lam et al., “SEE-Hardened-by-Design Area-Efficient SRAMs” | 2005, IEEE Aerospace | IEEE 1559543 | IEEE-Q1; RR refs | BACKGROUND | Self-scrubbing EDAC SRAM architecture and device SER context; not yet a formal model candidate. |
| C21 | E. Hwang et al., “Scrubbing with partial side information for radiation-tolerant memory” | 2010, GLOBECOM Workshops | [10.1109/GLOCOMW.2010.5700282](https://doi.org/10.1109/GLOCOMW.2010.5700282) | IEEE-Q2 | CORE | Direct radiation-tolerant-memory scrubbing formulation; event, metric and side-information assumptions need extraction. |
| C22 | J. A. Maestro and P. Reviriego, “Study of the effects of MBUs on the reliability of a 150 nm SRAM device” | 2008, DAC | [10.1145/1391469.1391704](https://doi.org/10.1145/1391469.1391704) | refined web; Scite; RR | RELATED | SRAM MBU reliability and scrubbing interaction; important for distinguishing direct multi-cell events from accumulation. |
| C23 | M. A. Bajura et al., “Models and Algorithmic Limits for an ECC-Based Approach to Hardening Sub-100-nm SRAMs” | 2007, IEEE TNS | [10.1109/TNS.2007.892119](https://doi.org/10.1109/TNS.2007.892119) | refined web; Scite | CORE | Abstract explicitly identifies BER model, ECC, scrubbing and sub-100-nm SRAM; publisher page exposes ECC-failure probability per scrub cycle/effective BER terminology. |
| C24 | J. M. Kontoleon, “Soft error recovery in simplex and triplex memory systems” | 2009, Microelectronics Reliability | [10.1016/j.microrel.2008.12.009](https://doi.org/10.1016/j.microrel.2008.12.009) | refined web; Scite | CORE | Markov/MTTF memory configurations with periodic scrubbing; configuration-specific transfer needs Paper Analyst review. |
| C25 | J. A. Maestro and P. Reviriego, “Reliability of Single-Error Correction Protected Memories” | 2009, IEEE Transactions on Reliability | [10.1109/TR.2008.2006470](https://doi.org/10.1109/TR.2008.2006470) | refined web; Scite; RR | CORE | Formal reliability of SEC-protected memories; word/memory aggregation and treatment of repeated errors are central to RQ-001. |
| C26 | A. M. Saleh, J. J. Serrano and J. H. Patel, “Reliability of scrubbing recovery-techniques for memory systems” | 1990, IEEE Transactions on Reliability | [10.1109/24.52622](https://doi.org/10.1109/24.52622) | backward chaining; Scite; RR | CORE | Seminal pre-2000 SEC-DED scrubbing reliability source; likely defines reliability/MTTF under scrub models. |
| C27 | L. Schiano, M. Ottavi and F. Lombardi, “Markov models of fault-tolerant memory systems under SEU” | 2004, MTDT | [10.1109/MTDT.2004.1327982](https://doi.org/10.1109/MTDT.2004.1327982) | RR refs; Scite | CORE | Explicit Markov reliability-model candidate; states, failure event and time basis require extraction. |
| C28 | R. M. Goodman and M. Sayano, “The reliability of semiconductor RAM memories with on-chip error-correction coding” | 1991, IEEE Transactions on Information Theory | [10.1109/18.79957](https://doi.org/10.1109/18.79957) | RR refs; Scite | CORE | Foundational coded-RAM reliability and word-to-memory aggregation candidate; scrubbing scope is unknown. |
| C29 | P. Reviriego, J. A. Maestro and C. Cervantes, “Reliability Analysis of Memories Suffering Multiple Bit Upsets” | 2007, IEEE TDMR | [10.1109/TDMR.2007.910443](https://doi.org/10.1109/TDMR.2007.910443) | RR similar; Scite | CORE | Abstract explicitly mentions MTTF and probability of failure in a given interval; adds MBU-aware event semantics. |
| C30 | J. M. Kontoleon and J. Andrianakis, “Reliability analysis of simplex and duplex memory systems with SEC and soft-error scrubbing recovery” | 2003, International Journal of Quality & Reliability Management | [10.1108/02656710310476561](https://doi.org/10.1108/02656710310476561) | RR refs; Scite | CORE | SEC plus scrubbing reliability; system arrangement and failure state require extraction. |
| C31 | D. G. Mavis, P. Eaton and M. Sibley, “Multiple Bit Upsets and Error Mitigation in Ultra-Deep Submicron SRAMs” | 2008, IEEE TNS | [10.1109/TNS.2008.2006893](https://doi.org/10.1109/TNS.2008.2006893) | RR similar; Scite | RELATED | MBU/error-mitigation context; relevance is mainly the boundary between direct multi-bit events and temporal accumulation. |
| C32 | J. A. Clemente et al., “Reliability of Error Correction Codes Against Multiple Events by Accumulation” | 2022, IEEE TNS | [10.1109/TNS.2022.3143652](https://doi.org/10.1109/TNS.2022.3143652) | RR refs; Scite | CORE | Explicit accumulation-focused ECC reliability source; newly added model category and high-priority Paper Analyst target. |
| C33 | D. Radaelli et al., “Investigation of multi-bit upsets in a 150 nm technology SRAM device” | 2005, IEEE TNS | [10.1109/TNS.2005.860675](https://doi.org/10.1109/TNS.2005.860675) | RR refs; Scite | RELATED | Primary SRAM MBU/topology evidence; informs event partitioning but does not by itself define mission reliability. |
| C34 | M. Blaum, R. M. Goodman and R. J. McEliece, “The Reliability of Single-Error Protected Computer Memories” | 1988, IEEE Transactions on Computers | [10.1109/12.75143](https://doi.org/10.1109/12.75143) | RR similar/refs; Scite | CORE | Pre-2000 foundational formal reliability model for single-error-protected memory. |
| C35 | G.-C. Yang, “Reliability of semiconductor RAMs with soft-error scrubbing techniques” | 1995, IEE Proceedings — Computers and Digital Techniques | [10.1049/ip-cdt:19952162](https://doi.org/10.1049/ip-cdt:19952162) | RR refs; Scite | CORE | Direct coded-RAM/scrubbing reliability candidate; scrub schedule and system aggregation require extraction. |
| C36 | Y. Li, B. Nelson and M. Wirthlin, “Reliability Models for SEC/DED Memory With Scrubbing in FPGA-Based Designs” | 2013, IEEE TNS | [10.1109/TNS.2013.2251902](https://doi.org/10.1109/TNS.2013.2251902) | RR similar; Scite | CORE | Explicit SEC/DED-memory-with-scrubbing model; FPGA implementation context may constrain generalization. |

### Screening totals after deduplication

| Class | Count |
|---|---:|
| CORE | 17 |
| RELATED | 8 |
| BACKGROUND | 3 |
| REJECT | 8 |
| **Total unique candidates** | **36** |

## 4. Seed papers

Three seeds were selected before ResearchRabbit expansion. They span a physical-BER-to-ECC model, a formal SEC-memory reliability model, and a modern SRAM/ECC/periodic-scrubbing constraint.

### Seed S1 — Bajura et al., 2007

**Citation:** M. A. Bajura et al., “Models and Algorithmic Limits for an ECC-Based Approach to Hardening Sub-100-nm SRAMs,” *IEEE Transactions on Nuclear Science*, vol. 54, no. 4, pp. 935–945, 2007. DOI: [10.1109/TNS.2007.892119](https://doi.org/10.1109/TNS.2007.892119).

**Why selected:** `SOURCE` abstract explicitly covers SRAM, ECC, scrubbing and a mathematical BER model. `INFERENCE` it is the strongest initial bridge between physical upset rate, ECC failure per scrub cycle and post-mitigation error-rate metric.

### Seed S2 — Maestro & Reviriego, 2009

**Citation:** J. A. Maestro and P. Reviriego, “Reliability of Single-Error Correction Protected Memories,” *IEEE Transactions on Reliability*, vol. 58, no. 1, pp. 193–201, 2009. DOI: [10.1109/TR.2008.2006470](https://doi.org/10.1109/TR.2008.2006470).

**Why selected:** `SOURCE` the paper’s bibliographic identity and abstract concern reliability of SEC-protected memory in radiation environments. `INFERENCE` it is a primary candidate for formal word-level failure, memory aggregation and finite-time/MTTF definitions.

### Seed S3 — Rezaei et al., 2023

**Citation:** M. Rezaei, F. J. Franco, G. Hubert and J. A. Clemente, “A Method to Neutralize the Impact of DVS on the Reliability of COTS SRAMs With ECC by Using Periodic Scrubbing,” *IEEE Transactions on Nuclear Science*, vol. 70, no. 12, pp. 2578–2589, 2023. DOI: [10.1109/TNS.2023.3332635](https://doi.org/10.1109/TNS.2023.3332635).

**Why selected:** `SOURCE` title/abstract metadata directly combine COTS SRAM, ECC, periodic scrubbing and reliability. `INFERENCE` it is the most modern system-oriented candidate for a finite reliability constraint and admissible scrub-period definition, while its DVS-specific assumptions must be separated from reusable structure.

### Scite seed sanity check

| Seed | Retraction/correction/concern signal returned | Classified contrasting statements returned | Interpretation |
|---|---|---:|---|
| S1 Bajura 2007 | none | 0 | No obvious signal detected; not an audit. |
| S2 Maestro 2009 | none | 0 | No obvious signal detected; not an audit. |
| S3 Rezaei 2023 | none | 0 | No obvious signal detected; low citation-context coverage must not be read as validation. |

Citation totals were not used as a quality criterion.

## 5. Evidence coverage matrix

| Evidence category required by RQ-001 | Candidate coverage | Status after pilot | Remaining extraction need |
|---|---|---|---|
| Alternative formal reliability/failure events | C10 temporal double-bit error; C23 ECC failure per scrub cycle; C25/C34 single-error-protected memory failure; C29 MBU-aware failure; C32 accumulation beyond ECC capability | COVERED BY PLAUSIBLE CANDIDATES | Establish exact state semantics and whether event is detected-uncorrectable, any wrong output, or modeled absorbing state. |
| Metric | Reliability function / probability of failure in interval (C25, C29, C34); MTTF (C10, C24, C26, C29); effective BER / ECC failure rate (C23); on-orbit SER (C02) | COVERED, MULTIPLE NON-EQUIVALENT FORMS | Determine dimensions, conditioning and conversion rules; do not equate BER, SER, FIT, MTTF and finite-horizon probability. |
| Codeword-level aggregation | C10, C23, C25, C32, C36 | COVERED BY CANDIDATES | Extract exact word length, check-bit treatment, correction/detection capability and error-distribution assumptions. |
| Word → bank/array/device/system aggregation | C02, C26, C28, C29, C35 | PARTIAL | Identify independence/common-cause assumptions and whether the event is “any failed word,” corrupted read, device SER, or system service failure. Bank-level definitions were not clearly exposed by abstracts. |
| Scrub-cycle/interval horizon | C10, C23, C26, C30, C35, C36 | COVERED BY CANDIDATES | Distinguish deterministic periodic, exponential/random, access-triggered and continuous models. |
| Operating/mission horizon | C02 on-orbit SER; C05 modern SRAM constraint; C29 probability in a given interval | PARTIAL | Extract explicit finite-horizon equations and whether mission duration is an input or only an implied rate conversion. |
| Correctable / detected-uncorrectable / undetected / miscorrection outcomes | SEC/DED context in C10, C26, C36; accumulation in C32 | PARTIAL | Undetected and miscorrection outcomes are not consistently visible at abstract level; Paper Analyst must separate them. |
| Traceable numerical system/mission requirement | none | GAP | No project-applicable numerical reliability threshold with provenance was found. Keep threshold `TBD`. |
| SRAM-specific transferability | C02, C05, C15, C22, C23, C31, C33 | COVERED WITH CAVEATS | Separate data SRAM from FPGA configuration memory and SRAM cache; record voltage/technology/radiation-domain assumptions. |

## 6. Terminology learned and query refinements

### Terms surfaced by sources

- `temporal double-bit error` — two separate events accumulate in the same ECC-protected word before correction/scrub;
- `ECC failure probability per scrub cycle`;
- `effective BER` versus `physical BER`;
- `soft-error scrubbing recovery`;
- `probability of failing in a given time interval`;
- `multiple events by accumulation`;
- `on-orbit soft error rate (SER)`;
- `data integrity` versus system reliability;
- `single-error protected memory` and `coded memory system`;
- deterministic/periodic versus exponential/random scrubbing.

### Proposed IEEE/other-database refinement strings

1. `"temporal double-bit error" AND (SRAM OR cache OR memory) AND (scrub* OR SECDED)`
2. `("ECC failure" OR "uncorrectable memory upset") AND ("scrub cycle" OR "scrubbing rate") AND SRAM`
3. `("probability of failing" OR MTTF OR "mean time to failure") AND ("single-error correction" OR SECDED) AND memory AND scrub*`
4. `("multiple events by accumulation" OR "error accumulation") AND ECC AND (SRAM OR memory)`
5. `("on-orbit soft error rate" OR "mission reliability") AND EDAC AND SRAM AND scrub*`
6. `("data integrity" OR reliability) AND "semiconductor RAM" AND "soft-error scrubbing"`

### Proposed Russian refinements for the local eLibrary cycle

- `«накопление мягких ошибок» И («кодовое слово» ИЛИ ECC) И (скраббинг ИЛИ регенерация)`;
- `«вероятность отказа кодированной памяти» И (ОЗУ ИЛИ СОЗУ)`;
- `«наработка на отказ» И ОЗУ И «коррекция ошибок» И регенерация`;
- `«многократный сбой» И «кодовое слово» И память`;
- `«радиационно-индуцированный отказ» И (СОЗУ ИЛИ SRAM) И EDAC`.

These are protocol-refinement proposals, not silently executed replacements for ELIB-Q1…Q3.

## 7. Gaps, conflicts and borderline exclusions

1. **eLibrary coverage gap.** All three required eLibrary strings remain unexecuted; Russian-language and local-domain evidence coverage is unknown.
2. **No numerical requirement provenance.** No system/mission requirement suitable for the project was found. Numerical threshold remains `TBD`.
3. **Metric non-equivalence.** Sources use reliability, failure probability, MTTF, BER, effective BER and SER. These cannot be merged without dimensional and event-semantic analysis.
4. **Event-semantic ambiguity.** “ECC failure,” “uncorrectable error,” detected double error, corrupted read, miscorrection, silent corruption and an absorbing reliability-model state may denote different events.
5. **Aggregation ambiguity.** Codeword, cache line, entire memory, device and system/service levels are mixed across literature. Transfer requires explicit aggregation assumptions.
6. **Horizon ambiguity.** Scrub interval, time between independent events, operating time, MTTF and mission duration are not interchangeable.
7. **Data SRAM versus FPGA configuration memory.** The literal term `SRAM` strongly attracts configuration-memory studies. Eight records were rejected because this would cause scope drift.
8. **Cache transferability.** C10 is formally useful, but cache validity time, eviction/write policies and architectural vulnerability may differ from standalone SRAM.
9. **Direct MBU versus accumulation.** C22/C29/C31/C33 concern multi-bit/multi-cell events, while C10/C32 concern temporal accumulation. Paper Analyst must check whether each model separates or mixes these mechanisms.
10. **Scrub scheduling model.** Periodic/deterministic, exponential/random, access-driven and continuous scrub assumptions may yield different reliability expressions.
11. **Physical-process assumptions.** Poisson arrival, independence, stationarity and uniform distribution were not accepted at Scout stage and must be extracted source by source.
12. **EDAC circuitry contribution.** C02 indicates that on-orbit SER may include both array and EDAC circuitry; the modeled event may not be a pure codeword-data failure.
13. **New category found in expansion.** C32 adds explicit accumulation reliability. Because the first expansion batch was productive, saturation has not been demonstrated.

## 8. HANDOFF TO ZOTERO

**Action:** Import/merge all accepted `CORE`, `RELATED` and `BACKGROUND` records below after local duplicate checking. Do not import `REJECT` records into the RQ-001 collection solely because they appeared in the search log.

**Target collection:** `DISSERTATION / RQ / RQ-001`

**Required common tags:**

- `rq/RQ-001`
- `topic/reliability-event`
- `topic/reliability-metric`
- `topic/memory-scrubbing`
- `memory/SRAM`
- exactly one of `class/CORE`, `class/RELATED`, `class/BACKGROUND`

**Records — CORE:**

1. C02 — DOI `10.1109/TNS.2018.2875051`
2. C05 — DOI `10.1109/TNS.2023.3332635`
3. C10 — DOI `10.1109/PRDC.2004.1276550`
4. C15 — DOI `10.1109/TNS.2015.2420094`
5. C21 — DOI `10.1109/GLOCOMW.2010.5700282`
6. C23 — DOI `10.1109/TNS.2007.892119`
7. C24 — DOI `10.1016/j.microrel.2008.12.009`
8. C25 — DOI `10.1109/TR.2008.2006470`
9. C26 — DOI `10.1109/24.52622`
10. C27 — DOI `10.1109/MTDT.2004.1327982`
11. C28 — DOI `10.1109/18.79957`
12. C29 — DOI `10.1109/TDMR.2007.910443`
13. C30 — DOI `10.1108/02656710310476561`
14. C32 — DOI `10.1109/TNS.2022.3143652`
15. C34 — DOI `10.1109/12.75143`
16. C35 — DOI `10.1049/ip-cdt:19952162`
17. C36 — DOI `10.1109/TNS.2013.2251902`

**Records — RELATED:**

1. C03 — title + IEEE document `9159718`
2. C08 — title + IEEE document `6881359`
3. C13 — title + IEEE document `7544353`
4. C14 — title + IEEE document `11244098`
5. C18 — title + IEEE document `8093205`
6. C22 — DOI `10.1145/1391469.1391704`
7. C31 — DOI `10.1109/TNS.2008.2006893`
8. C33 — DOI `10.1109/TNS.2005.860675`

**Records — BACKGROUND:**

1. C11 — title + IEEE document `1545899`
2. C19 — title + IEEE document `8875489`
3. C20 — title + IEEE document `1559543`

**Duplicate policy:**

1. Match DOI case-insensitively after normalization.
2. When DOI is absent, match normalized title + year + first author, then verify publisher record.
3. Merge with an existing canonical Zotero item; do not create a parallel record.
4. Preserve existing notes, tags and attachments unless an attachment is demonstrably duplicate.
5. Do not create a new collection/tag taxonomy if the local canonical taxonomy uses an equivalent path; map this logical destination first.

**Metadata checks:** full author list; canonical title; venue; year; volume/issue/pages; DOI; publisher landing URL; abstract; item type. In particular, verify year/online-first differences for C25 and title capitalization for older IEEE records.

**PDF/attachment expectations:** attach open or institutionally available publisher/author manuscript PDFs when lawful; otherwise retain publisher link and mark full text unavailable. Do not purchase content as part of this handoff. C05 was reported open-access by Scite; verify the actual accessible file locally.

**Expected result:** return a `ZOTERO HANDOFF RESULT` listing matched existing items, newly created items, unresolved identities, metadata corrections, attachment status and duplicate actions.

## 9. HANDOFF TO PAPER ANALYST

**Related RQ:** RQ-001  
**Do not assign claims from abstracts. Use verified full text.**

### Priority 1 — C32, Clemente et al. 2022

Extraction questions:

1. What exact event terminates successful ECC operation?
2. Does “multiple events by accumulation” mean independent particle events, independent bit errors, or another process?
3. What ECC outcomes are represented: corrected, detected-uncorrectable, undetected or miscorrected?
4. What is the aggregation unit: bit, codeword, full memory or system?
5. What is the time horizon and scrub model?
6. Are direct same-particle multi-bit events excluded, combined, or outside scope?
7. What independence, stationarity and arrival-process assumptions are used?

### Priority 2 — C23, Bajura et al. 2007

Extraction questions:

1. Define physical BER, ECC-failure probability per scrub cycle and effective BER exactly, with dimensions.
2. Identify the failure event and whether detection/miscorrection distinctions are modeled.
3. Extract codeword parameters, correction capability and memory-size aggregation.
4. Extract deterministic/random scrub assumptions and how scrub rate enters the model.
5. Determine whether a finite mission probability can legitimately be derived from the reported rate.

### Priority 3 — C25, Maestro & Reviriego 2009

Extraction questions:

1. Define the reliability function and modeled absorbing/failure states.
2. Identify word-level versus memory-level aggregation.
3. Determine whether repeated errors that hit the same bit can cancel/reinforce and how this affects the event.
4. Extract MTTF and finite-time probability relations.
5. Determine whether scrubbing is explicit, implicit or absent.

### Priority 4 — C05, Rezaei et al. 2023

Extraction questions:

1. State the reliability requirement mathematically and identify its provenance.
2. Identify the evaluation horizon and whether it is mission time, operating time or scrub interval.
3. Extract the condition for an admissible scrub period and all required inputs.
4. Separate reusable ECC/scrubbing model structure from DVS-specific upset-rate assumptions.
5. Identify modeled decoder outcomes and treatment of check-bit/EDAC-circuit errors.

### Priority 5 — C02, Zhang et al. 2018

Extraction questions:

1. Define the reported on-orbit SER event and its unit.
2. Separate memory-array and EDAC-circuit contributions.
3. Identify how accelerator data, ion flux and scrub time are combined.
4. Determine whether SER is a device-level observed error, an uncorrectable event rate or another outcome.
5. Identify any mission-duration conversion and its assumptions.

### Priority 6 — C26, Saleh et al. 1990

Extraction questions:

1. Define system states, failure event, reliability function and MTTF.
2. Compare deterministic versus exponential/random scrubbing if both are modeled.
3. Identify memory hierarchy/aggregation and SEC-DED assumptions.
4. Record which assumptions later papers retain or modify.

**Expected Paper Analyst output:** one Paper Card per selected source, with every substantial statement marked `SOURCE` or `INFERENCE`; explicit extraction of event, metric, aggregation, horizon and assumptions; no cross-paper adjudication.

## 10. Local handoff for the blocked eLibrary stage

```text
HANDOFF

From:
Cloud Literature Scout

To:
Local Codex / researcher with working eLibrary access

Task ID:
RQ-001-ELIB-LOCAL-01

Related RQ:
RQ-001

Known:
Cloud Work could not submit ELIB-Q1...Q3 because eLibrary returned 403.

Required action:
1. Execute ELIB-Q1, ELIB-Q2 and ELIB-Q3 exactly as recorded in section 2.2.
2. First-pass window: 2000–2026; include earlier seminal records only by chaining.
3. Record exact syntax actually accepted by eLibrary, date, filters, hits and screening counts.
4. Screen title/metadata and abstract using the canonical RQ-001 protocol.
5. Deduplicate against DOI/title list C01...C36.
6. Return CORE/RELATED/BACKGROUND/REJECT classifications and reasons.

Do not:
- report 0 hits unless the query is actually submitted;
- broaden into a general Russian-language reliability review;
- infer full-paper conclusions from title/abstract;
- import to Zotero before duplicate/metadata checks.

Expected output:
ZOTERO HANDOFF RESULT-compatible table plus exact eLibrary search log.
```

## 11. Recommendation and stopping decision

### Recommendation: REFINE PROTOCOL AND RUN ONE ADDITIONAL LIMITED CYCLE

Do **not** stop RQ-001 mapping yet.

Reasons:

1. Required eLibrary strings remain unexecuted.
2. The first ResearchRabbit expansion batch added new model/definition categories, especially C32 and older coded-memory/scrubbing models.
3. Two consecutive no-new-category batches have not occurred.
4. Mission/system numerical requirement provenance remains a declared gap.

### Next limited cycle

1. Complete the local eLibrary handoff.
2. Execute refinement strings 1–6 from section 6 in IEEE Xplore/appropriate academic databases and record exact counts.
3. Use C32 and C36 as expansion anchors for one additional bounded citation pass.
4. Stop the discovery cycle if that batch and the eLibrary batch add no new event/metric/aggregation/horizon category; otherwise return to Orchestrator with the specific new category rather than expanding indefinitely.

## 12. Pilot conclusion

**SOURCE:** The pilot found verified publication identities spanning SEC/DED scrubbing reliability, MTTF and finite-time failure probability, ECC-failure probability per scrub cycle/effective BER, on-orbit EDAC SRAM SER, MBU-aware reliability and accumulation-focused ECC reliability.

**INFERENCE:** The literature does not appear to use one universally interchangeable reliability event or metric. At least five distinct measurement/model families require later Paper Analyst extraction and Evidence Auditor comparison.

**UNKNOWN:** Which definition is appropriate for this dissertation; how codeword-level events should aggregate to the selected system level; which evaluation horizon is required; whether any traceable numerical mission requirement exists.

**Confidence:**

- High for IEEE Xplore query strings and hit counts observed on 2026-08-26.
- High for DOI/title identity of Scite-matched records.
- Medium for CORE/RELATED/BACKGROUND screening because it is intentionally abstract-level.
- Incomplete for overall coverage because eLibrary is missing and saturation was not reached.

No GitHub or Zotero mutation was performed by the Literature Scout.
