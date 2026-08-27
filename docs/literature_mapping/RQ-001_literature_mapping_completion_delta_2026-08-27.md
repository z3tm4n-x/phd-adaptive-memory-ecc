# RQ-001 Literature Mapping Completion Cycle — Delta Report

**Task:** RQ-001 mapping completion cycle  
**Related RQ:** RQ-001  
**Role:** Literature Scout  
**Execution date:** 2026-08-27 (UTC)  
**Baseline:** `RQ-001_literature_mapping_pilot_2026-08-26.md`, candidate register C01…C36  
**Delta status:** ADDITIONAL LIMITED CYCLE REQUIRED

## 1. Scope and evidence boundary

This document records only the delta after the accepted partial pilot. IEEE-Q1…Q4 were not repeated.

- `SOURCE` means publisher/database metadata or an abstract inspected during this cycle.
- `INFERENCE` means a Literature Scout screening or coverage judgment.
- No full-paper claim adjudication was performed.
- No `HYP`, `CLM` or `EVD` was created.
- No numerical reliability threshold was selected.
- This delta does not answer RQ-001 and does not establish a research gap.
- No GitHub or Zotero mutation was performed.

## 2. Status of RQ-001-ELIB-LOCAL-01

### 2.1 Result retrieval

The requested `RQ-001-ELIB-LOCAL-01` result was searched for in the canonical GitHub repository, saved project files and available project-conversation context. No completed handoff result was found.

**Status:** `NOT RETURNED`.

### 2.2 Independent access check

On 2026-08-27 the eLibrary home page returned `403 Forbidden` twice before a search form was available. The public search index likewise exposed an eLibrary access-block page, not query results. Therefore none of the eLibrary strings could be submitted in this Cloud environment.

Recording `0 hits` would be false. The reproducible values remain `UNKNOWN — NOT EXECUTED`.

| ID | Exact required eLibrary query | Date | Intended filters | Hits | Screened | Included | Status |
|---|---|---|---|---:|---:|---:|---|
| ELIB-Q1 | `(SRAM ИЛИ «статическая оперативная память») И («коррекция ошибок» ИЛИ ECC ИЛИ EDAC) И (скраббинг ИЛИ «восстановление памяти») И («неисправимая ошибка» ИЛИ «вероятность отказа» ИЛИ надежность)` | 2026-08-27 | 2000–2026; English/Russian terms | UNKNOWN | 0 | 0 | NOT EXECUTED — 403 before submission |
| ELIB-Q2 | `(«радиационно-стойкая память» ИЛИ «космическая память») И («помехоустойчивое кодирование» ИЛИ «коррекция ошибок») И (скраббинг ИЛИ регенерация) И (отказ ИЛИ надежность)` | 2026-08-27 | 2000–2026; English/Russian terms | UNKNOWN | 0 | 0 | NOT EXECUTED — 403 before submission |
| ELIB-Q3 | `(«модель надежности памяти» ИЛИ «вероятность потери данных») И (кодовое слово ИЛИ банк ИЛИ массив) И («время миссии» ИЛИ «временной интервал»)` | 2026-08-27 | 2000–2026; English/Russian terms | UNKNOWN | 0 | 0 | NOT EXECUTED — 403 before submission |

### 2.3 Russian refinement strings still pending in eLibrary

The following exact refinements from the pilot also remain unexecuted for the same reason:

1. `«накопление мягких ошибок» И («кодовое слово» ИЛИ ECC) И (скраббинг ИЛИ регенерация)`
2. `«вероятность отказа кодированной памяти» И (ОЗУ ИЛИ СОЗУ)`
3. `«наработка на отказ» И ОЗУ И «коррекция ошибок» И регенерация`
4. `«многократный сбой» И «кодовое слово» И память`
5. `«радиационно-индуцированный отказ» И (СОЗУ ИЛИ SRAM) И EDAC`

For all five: date `2026-08-27`; target filter `2000–2026`; hits `UNKNOWN`; screened `0`; included `0`; status `NOT EXECUTED — eLibrary access blocker`.

## 3. Refinement search-log delta

### 3.1 Database and filters

**Database:** IEEE Xplore  
**Date:** 2026-08-27  
**Content filters:** all content types; all publishers  
**Time filter used for screening counts:** 2000–2026. IEEE retained the requested range in the URL/filter state; where appropriate its controls displayed the actual matching-year endpoints.  
**Screening:** every filtered hit received title/metadata and abstract screening. Abstracts for records already in C01…C36 were reused from the pilot rather than interpreted again.

The raw all-year count is included to explain two pre-2000 records that disappeared under the protocol window: C26 (Saleh 1990) in REF-Q3 and C28 (Goodman 1991) in REF-Q6. Both were already in the register through backward chaining.

| ID | Exact executed query | Raw all-year hits | Hits after 2000–2026 | Title/metadata screened | Abstract screened | Included occurrences | New accepted | New rejected |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| REF-Q1 | `"temporal double-bit error" AND (SRAM OR cache OR memory) AND (scrub* OR SECDED)` | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| REF-Q2 | `("ECC failure" OR "uncorrectable memory upset") AND ("scrub cycle" OR "scrubbing rate") AND SRAM` | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| REF-Q3 | `("probability of failing" OR MTTF OR "mean time to failure") AND ("single-error correction" OR SECDED) AND memory AND scrub*` | 9 | 8 | 8 | 8 | 7 | 4 | 1 |
| REF-Q4 | `("multiple events by accumulation" OR "error accumulation") AND ECC AND (SRAM OR memory)` | 5 | 5 | 5 | 5 | 4 | 2 | 1 |
| REF-Q5 | `("on-orbit soft error rate" OR "mission reliability") AND EDAC AND SRAM AND scrub*` | 1 | 1 | 1 | 1 | 1 | 0 | 0 |
| REF-Q6 | `("data integrity" OR reliability) AND "semiconductor RAM" AND "soft-error scrubbing"` | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| **Total occurrences** | — | **17** | **15** | **15** | **15** | **13** | **6** | **2** |

### 3.2 Deduplication result

- Filtered result occurrences: 15.
- Unique records after within-batch deduplication: 14; C10 appeared in REF-Q1 and REF-Q3.
- Already present in C01…C36: C02, C10, C18, C25, C32 and C36.
- New accepted records: six (C37–C40, C43–C44).
- New rejected records: two (C41–C42).
- No C01…C36 record was reclassified.

## 4. Bounded citation-expansion log

ResearchRabbit default ranking was retained. For every route, only the first 20 displayed records were screened; shorter lists were screened completely. The parent anchor and route are recorded below. No records were saved to ResearchRabbit.

| Parent anchor | Route | Total shown | Title/metadata screened | Abstract-screened survivors | New accepted candidates |
|---|---|---:|---:|---:|---|
| C32 — Clemente et al. 2022 | Similar | 384 | 20 | 2 | C49, C50 |
| C32 — Clemente et al. 2022 | References | 37 | 20 | 4 | C45, C51, C52, C53 |
| C32 — Clemente et al. 2022 | Cited by | 8 | 8 | 0 | none |
| C36 — Li et al. 2013 | Similar | 816 | 20 | 1 | C46 |
| C36 — Li et al. 2013 | References | 6 | 6 | 2 | C47, C48 |
| C36 — Li et al. 2013 | Cited by | 30 | 20 | 1 borderline | none |
| **Total route occurrences** | — | — | **94** | **10** | **9** |

The 84 route occurrences not promoted after title/metadata screening were duplicates, already covered model families, or outside protocol scope. Dominant exclusions were:

- Josephson/superconducting, domain-wall and spintronic memory mechanisms;
- FPGA configuration-memory TMR, placement and scrubbing implementation without a protected data-memory reliability definition;
- raw SEU/MCU characterization without a link to an ECC/scrubbing reliability event;
- ECC construction papers without a reliability metric, aggregation rule or horizon;
- non-peer-reviewed application notes and broad surveys that added no primary definition.

One borderline C36-cited-by record, Bentoutou et al. 2025, DOI `10.1016/j.micpro.2025.105208`, had stable metadata but no abstract in the inspected sources. It was not promoted because the title alone cannot establish an event, metric, aggregation level or horizon.

## 5. Candidate-register delta

**Classification basis:** publisher/ResearchRabbit metadata and abstracts. Every classification is an `INFERENCE` for screening, not a claim about the full paper.

| ID | Publication | Year / venue | DOI / identifier | Discovery route and parent | Class | Screening reason |
|---|---|---|---|---|---|---|
| C37 | Y. Yigit et al., “Reliability Analysis of Fault Tolerant Memory Systems” | 2023, SEEDA-CECNSM | [10.1109/SEEDA-CECNSM61561.2023.10470763](https://doi.org/10.1109/SEEDA-CECNSM61561.2023.10470763) | IEEE REF-Q3 | CORE | Abstract explicitly combines SEC-DED, exponential/deterministic/mixed scrubbing, reliability and MTTF. Full text must establish the failure state and whether the model materially extends earlier work. |
| C38 | S. Lee, S. Baeg and P. Reviriego, “Memory Reliability Model for Accumulated and Clustered Soft Errors” | 2011, IEEE TNS | [10.1109/TNS.2011.2164555](https://doi.org/10.1109/TNS.2011.2164555) | IEEE REF-Q3 | CORE | SRAM failure probability model includes accumulated upsets, row clustering and interleaving, with abstract-level comparison to 45-nm SRAM test data. |
| C39 | P. Reviriego and J. A. Maestro, “Study of the Effects of Multibit Error Correction Codes on the Reliability of Memories in the Presence of MBUs” | 2009, IEEE TDMR | [10.1109/TDMR.2008.2007647](https://doi.org/10.1109/TDMR.2008.2007647) | IEEE REF-Q3 | CORE | Reliability modelling for multibit protection codes in the presence of MBUs; abstract states that both scrubbed and unscrubbed cases are analysed. |
| C40 | S. G. Miremadi and H. R. Zarandi, “Reliability of protecting techniques used in fault-tolerant cache memories” | 2005, CCECE | [10.1109/CCECE.2005.1557054](https://doi.org/10.1109/CCECE.2005.1557054) | IEEE REF-Q3 | RELATED | Derives reliability/MTTF for cache protection including scrubbing and SEC-DED. Cache-specific access and validity assumptions limit direct transfer to standalone SRAM. |
| C41 | S. Ollivier et al., “Toward Comprehensive Shifting Fault Tolerance for Domain-Wall Memories With PIETT” | 2023, IEEE Transactions on Computers | [10.1109/TC.2022.3188206](https://doi.org/10.1109/TC.2022.3188206) | IEEE REF-Q3 | REJECT | Domain-wall memory shifting/pinning faults are a different storage technology and failure mechanism; SRAM transferability is not established. |
| C42 | E. Cheshmikhani, H. Farbeh and H. Asadi, “Enhancing Reliability of STT-MRAM Caches by Eliminating Read Disturbance Accumulation” | 2019, DATE | [10.23919/DATE.2019.8714946](https://doi.org/10.23919/DATE.2019.8714946) | IEEE REF-Q4 | REJECT | STT-MRAM read-disturb accumulation is not the radiation-induced SRAM/ECC/scrubbing object of RQ-001. |
| C43 | Y. Lu et al., “A Self-Adaptive SEU Mitigation Scheme for Embedded Systems in Extreme Radiation Environments” | 2022, IEEE Systems Journal | [10.1109/JSYST.2022.3144019](https://doi.org/10.1109/JSYST.2022.3144019) | IEEE REF-Q4 | RELATED | SRAM, ECC and refresh/error-accumulation mitigation are explicit, but the abstract reports implementation/irradiation outcomes rather than a formal reliability event or mission horizon. Check relation to C03 as a possible conference-to-journal extension. |
| C44 | N. A. Koca et al., “Exploring Error Correction Circuits on RISC-V based Systems for Space Applications” | 2024, ISCAS | [10.1109/ISCAS58744.2024.10558401](https://doi.org/10.1109/ISCAS58744.2024.10558401) | IEEE REF-Q4 | RELATED | SRAM ECC/TMR comparison and self-refresh scheduling address accumulation, but the abstract exposes implementation resilience/overhead rather than a formal mission reliability constraint. |
| C45 | H. J. Tausch, “Simplified Birthday Statistics and Hamming EDAC” | 2009, IEEE TNS | [10.1109/TNS.2009.2012710](https://doi.org/10.1109/TNS.2009.2012710) | ResearchRabbit C32 → References | CORE | Defines cumulative probability that an uncorrectable double-bit error occurs in some Hamming-protected word as the number of random upsets increases. Adds an event-count horizon that must not be silently equated with time. |
| C46 | S. Baeg et al., “SRAM Interleaving Distance Selection With a Soft Error Failure Model” | 2009, IEEE TNS | [10.1109/TNS.2009.2015312](https://doi.org/10.1109/TNS.2009.2015312) | ResearchRabbit C36 → Similar | CORE | Failure probability explicitly depends on SEC, interleaving and grouped MCU events represented by a compound Poisson process; abstract reports an upper-bound comparison with 45-nm SRAM neutron data. |
| C47 | J.-M. Ayache and M. Díaz, “A Reliability Model for Error Correcting Memory Systems” | 1979, IEEE Transactions on Reliability | [10.1109/TR.1979.5220616](https://doi.org/10.1109/TR.1979.5220616) | ResearchRabbit C36 → References | CORE | Foundational model stresses that the reliability event depends on physical chip failure modes and the implemented memory-system hardware, rather than a bit-only abstraction. |
| C48 | S. A. Elkind and D. P. Siewiorek, “Reliability and Performance of Error-Correcting Memory and Register Arrays” | 1980, IEEE Transactions on Computers | [10.1109/TC.1980.1675475](https://doi.org/10.1109/TC.1980.1675475) | ResearchRabbit C36 → References | CORE | SEC memory-array model explicitly includes support circuitry and states that it can dominate system reliability; directly relevant to aggregation boundary. |
| C49 | R. Glein et al., “BRAM implementation of a single-event upset sensor for adaptive single-event effect mitigation in reconfigurable FPGAs” | 2017, NASA/ESA AHS | [10.1109/AHS.2017.8046352](https://doi.org/10.1109/AHS.2017.8046352) | ResearchRabbit C32 → Similar | RELATED | BRAM sensor uses ECC and scrubbing and reports a system failure rate in `a⁻¹`; useful system-level metric example, but the object is an FPGA radiation sensor rather than general protected SRAM service. |
| C50 | A. Pérez-Celis, C. Thurlow and M. Wirthlin, “Identifying Radiation-Induced Micro-SEFIs in SRAM FPGAs” | 2021, IEEE TNS | [10.1109/TNS.2021.3108572](https://doi.org/10.1109/TNS.2021.3108572) | ResearchRabbit C32 → Similar | RELATED | Defines and measures a common-mode functional event affecting CRAM/BRAM that can overcome ECC/TMR. It broadens event taxonomy but does not supply a scrubbing reliability model. |
| C51 | F. J. Franco et al., “Inherent Uncertainty in the Determination of Multiple Event Cross Sections in Radiation Tests” | 2020, IEEE TNS | [10.1109/TNS.2020.2977698](https://doi.org/10.1109/TNS.2020.2977698) | ResearchRabbit C32 → References | RELATED | Quantifies false multi-cell events caused by accidental proximity of independent bitflips and the resulting limit on cross-section accuracy. Relevant to provenance of the event-rate input, not a protected-memory reliability model itself. |
| C52 | F. J. Franco et al., “Influence of Randomness During the Interpretation of Results From Single-Event Experiments on SRAMs” | 2019, IEEE TDMR | [10.1109/TDMR.2018.2886358](https://doi.org/10.1109/TDMR.2018.2886358) | ResearchRabbit C32 → References | RELATED | Provides a correction framework for false multiple events in SRAM radiation data; relevant to separating measured event classes before reliability aggregation. |
| C53 | A. Neale and M. Sachdev, “A New SEC-DED Error Correction Code Subclass for Adjacent MBU Tolerance in Embedded Memory” | 2013, IEEE TDMR | [10.1109/TDMR.2012.2232671](https://doi.org/10.1109/TDMR.2012.2232671) | ResearchRabbit C32 → References | RELATED | Adds adjacent-error detection/correction and miscorrection semantics that may alter the reliability event, but does not expose a scrubbing metric or horizon in the abstract. |

### 5.1 Delta and cumulative counts

| Class | Pilot C01…C36 | New C37…C53 | Updated total |
|---|---:|---:|---:|
| CORE | 17 | 7 | 24 |
| RELATED | 8 | 8 | 16 |
| BACKGROUND | 3 | 0 | 3 |
| REJECT | 8 | 2 | 10 |
| **Total candidates** | **36** | **17** | **53** |

### 5.2 Scite secondary sanity check

All 15 newly accepted DOI records (C37–C40 and C43–C53) matched stable bibliographic identities in Scite. No retraction/correction/editorial-concern notice and no classified contrasting statement was returned for these records on 2026-08-27.

This is only an obvious-signal check. A returned zero is not evidence of correctness, consensus or absence of disagreement; full supporting/contrasting citation audit remains Evidence Auditor work. Citation totals were not used for classification.

## 6. Updated evidence-coverage matrix

| RQ-001 evidence category | Pilot coverage | Delta candidates | Updated status | Remaining need |
|---|---|---|---|---|
| Formal reliability/failure event | Temporal double error, ECC failure per cycle, MBU and accumulation candidates | C45 any double error in any Hamming word; C47 failure hypothesis tied to chip/hardware; C50 micro-SEFI boundary; C53 adjacent-error/miscorrection outcomes | STRONGER, MULTIPLE NON-EQUIVALENT EVENTS | Paper Analyst must state detected-uncorrectable, wrong-read, miscorrection, absorbing state and common-mode event semantics separately. |
| Metric | Reliability function, interval probability, MTTF, effective BER and SER | C37/C40 MTTF and reliability; C38/C46 failure probability; C45 cumulative probability by upset count; C49 system failure rate `a⁻¹`; C51/C52 cross-section uncertainty | COVERED BY SEVERAL METRIC FAMILIES | Establish units, conditioning and legitimate conversions; do not equate cross section, event rate, probability, MTTF and SER. |
| Codeword-level aggregation | Covered by C10/C23/C25/C32/C36 | C38, C39, C45, C46, C53 | STRONG | Extract word size, code capability, check-bit treatment and “any word fails” rule. |
| Word → bank/array/device/system aggregation | Partial | C47 chip/hardware implementation; C48 support circuitry; C49 system-level BRAM sensor; C50 functional interrupt | IMPROVED BUT STILL PARTIAL | Bank-level and system-visible memory-service rules remain poorly exposed at abstract level. |
| Scrub-cycle/interval horizon | Covered by several candidates | C37 exponential/deterministic/mixed; C39 scrubbed/unscrubbed; C40 cache scrubbing | STRONG | Extract deterministic, probabilistic/access-driven and mixed timing definitions source by source. |
| Operating/mission horizon | Partial | C45 accumulated-upset-count horizon; C49 rate per year | PARTIAL | Explicit mission-duration probability and its provenance remain unresolved. Event-count is not automatically a time horizon. |
| Correctable / DUE / undetected / miscorrection outcomes | Partial | C53 explicitly adds adjacent correction/detection and miscorrection concern; C45 SEC/double-error event | IMPROVED BUT PARTIAL | Full-text extraction is still needed for silent corruption and decoder behavior. |
| Event-measurement validity and provenance | Limited | C51/C52 false-MCU correction and accuracy limit | NEWLY COVERED | Determine how measurement uncertainty propagates into a reliability constraint; this is not a Scout-stage derivation. |
| Direct MBU versus independent accumulation | Partial | C38 accumulated + clustered model; C45 independent random-upset accumulation; C46 grouped MCU process; C51/C52 accidental false grouping | STRONGER, MECHANISMS STILL MUST BE SEPARATED | Extract whether each model mixes direct and accumulated mechanisms and whether double counting is possible. |
| Traceable numerical system/mission requirement | Gap | none | GAP | Threshold remains `TBD`; no numerical value may be assigned from mapping alone. |
| Russian/eLibrary coverage | Gap | none | GAP / EXECUTION BLOCKER | Complete RQ-001-ELIB-LOCAL-01 in an environment with working eLibrary access. |

## 7. New evidence/model/measurement categories

The completion cycle did not yield `none`; it added the following categories:

1. **Accumulated-upset-count horizon** — C45 expresses cumulative failure probability against the number of random upsets, not directly against elapsed time.
2. **Interleaving-aware grouped-event failure probability** — C46 uses a compound Poisson representation for grouped MCU events and compares failure-probability bounds with SRAM test data.
3. **Combined accumulated-and-clustered SRAM model** — C38 includes row clustering and interleaving in a failure-probability model.
4. **Support-circuit aggregation boundary** — C48 treats memory support circuitry as part of system reliability and reports that it can dominate the array contribution.
5. **Measurement uncertainty / false multiple events** — C51/C52 distinguish true multiple events from accidental spatial coincidence of independent upsets and constrain cross-section accuracy.
6. **Common-mode functional-event boundary** — C50 introduces micro-SEFI as a system-visible event capable of overcoming ECC/TMR, although it is only RELATED to the central data-SRAM model.

These are `INFERENCE` categories for routing work to Paper Analyst; they are not cross-paper conclusions.

## 8. Saturation test

| Stopping condition | Result |
|---|---|
| IEEE-Q1…Q4 complete | PASS — accepted pilot; not repeated |
| ELIB-Q1…Q3 complete | FAIL — no local result; Cloud access blocked before submission |
| All evidence categories covered or explicit gap | PASS — candidates or explicit gaps recorded |
| 2–5 strong seeds | PASS — pilot seeds retained |
| Required C32/C36 bounded expansion | PASS |
| Two consecutive batches with no new category | FAIL — both refinement and expansion added categories |
| Updated candidate table and handoffs | PASS |

**Saturation result:** `NOT REACHED`.

The failure is substantive, not paper-count based: eLibrary remains unexecuted and the second expansion batch still added new event/metric/aggregation categories.

## 9. Updated HANDOFF TO ZOTERO — delta only

```text
HANDOFF TO ZOTERO

Action:
Import or merge the accepted delta records C37–C40 and C43–C53.
Do not import C41, C42 or the unpromoted Bentoutou 2025 record solely from this mapping.

Target collection:
DISSERTATION / RQ / RQ-001

Records — class/CORE:
C37  10.1109/SEEDA-CECNSM61561.2023.10470763
C38  10.1109/TNS.2011.2164555
C39  10.1109/TDMR.2008.2007647
C45  10.1109/TNS.2009.2012710
C46  10.1109/TNS.2009.2015312
C47  10.1109/TR.1979.5220616
C48  10.1109/TC.1980.1675475

Records — class/RELATED:
C40  10.1109/CCECE.2005.1557054
C43  10.1109/JSYST.2022.3144019
C44  10.1109/ISCAS58744.2024.10558401
C49  10.1109/AHS.2017.8046352
C50  10.1109/TNS.2021.3108572
C51  10.1109/TNS.2020.2977698
C52  10.1109/TDMR.2018.2886358
C53  10.1109/TDMR.2012.2232671

Required common tags:
rq/RQ-001
topic/reliability-event
topic/reliability-metric
topic/memory-scrubbing
memory/SRAM
exactly one class/CORE or class/RELATED tag

Duplicate policy:
1. Match normalized DOI case-insensitively.
2. If DOI is absent, match normalized title + year + first author and verify against the publisher record.
3. Merge into an existing canonical item; preserve notes, tags and nonduplicate attachments.
4. Do not merge C47 automatically with the separate 1980 Microelectronics Reliability record
   DOI 10.1016/0026-2714(80)90408-4 merely because the title is almost identical; verify their relationship.
5. Check whether C43 is an extended journal version of C03 and link related items rather than treating
   them as an accidental duplicate.

Metadata checks:
Full author list; canonical title; publication/conference; year; volume/issue/pages;
DOI; publisher landing URL; abstract; item type. Verify online-first versus issue year.

PDF / attachment expectations:
Attach a lawful publisher or author-manuscript PDF when available; otherwise retain the publisher link.
Scite exposed open author-manuscript routes for C51 and C52; verify locally before attachment.
Do not purchase documents as part of this handoff.

Expected result:
ZOTERO HANDOFF RESULT with Added, Duplicates skipped/merged, Metadata conflicts,
Zotero item keys, PDF status, references.bib updated yes/no, and blockers.
```

## 10. Updated HANDOFF TO PAPER ANALYST — delta only

```text
HANDOFF

From:
Literature Scout

To:
Paper Analyst

Task ID:
RQ-001-PAPER-DELTA-02

Related RQ:
RQ-001

Boundary:
Use verified full text. Do not create cross-paper claims from abstracts.
Produce one Paper Card per source and mark every substantial statement SOURCE or INFERENCE.

Priority 1 — C45, Tausch 2009
1. Define the exact uncorrectable event and “some word” aggregation rule.
2. Identify the independent variable: upset count, fluence, time, or another quantity.
3. Extract all assumptions behind the cumulative probability equation.
4. Determine whether direct same-particle MBUs are excluded, included, or indistinguishable.
5. State what additional model is required to convert upset count to scrub/mission time.

Priority 2 — C46, Baeg et al. 2009
1. Define the failure event and time/probability variable.
2. Extract the compound-Poisson event model and grouped-event definition.
3. Extract physical-cell-to-word/interleaving assumptions.
4. Identify why the result is an upper bound and under which conditions.
5. Determine whether independent accumulation and direct MCU are separated.

Priority 3 — C38, Lee et al. 2011
1. Define accumulated versus clustered errors and their mutual exclusivity.
2. Extract failure probability, aggregation level and horizon.
3. Extract the row-clustering/interleaving representation.
4. Identify what the reported 45-nm SRAM comparison actually validates.
5. Compare its event partition with C46 without adjudicating which is correct.

Priority 4 — C37, Yigit et al. 2023
1. Define failure/absorbing states, reliability function and MTTF.
2. Extract exponential, deterministic and mixed scrubbing schedules exactly.
3. Identify word-size and memory-size aggregation.
4. Determine the relationship to Saleh et al. 1990 and whether this is a new model or a re-analysis.

Priority 5 — C47 and C48, foundational aggregation models
Create separate Paper Cards.
1. Define each failure hypothesis and the modelled hardware boundary.
2. Identify bit, chip, array, support-circuit and system aggregation.
3. Separate transient soft-error assumptions from permanent/component failures.
4. State which parts are transferable to ECC-protected SRAM with periodic scrubbing.

Priority 6 — C51 and C52, measurement validity
Create separate Paper Cards.
1. Define a false multiple event and the classification/search-distance rule.
2. Extract the estimator/correction and its uncertainty or accuracy limit.
3. Identify assumptions about independence and spatial uniformity.
4. Explain which measured cross sections are affected.
5. Do not propagate the correction into a reliability equation at Analyst stage unless explicitly done by the source.

Priority 7 — C49, Glein et al. 2017
1. Define the event underlying λ = 0.05 a⁻¹ and the aggregation boundary.
2. Extract the derivation, mission/operating horizon and provenance of inputs.
3. Separate sensor self-failure from protected application-memory failure.

Priority 8 — C53, Neale and Sachdev 2013
1. Extract corrected, detected-uncorrectable, adjacent-error and miscorrection outcomes.
2. State physical adjacency/codeword placement assumptions.
3. Identify which outcome could legitimately enter an RQ-001 reliability event.

Expected output:
Paper Cards with exact event, metric, aggregation, horizon, assumptions and limitations;
no cross-paper evidence adjudication and no numerical project threshold.
```

## 11. Renewed local eLibrary handoff

```text
HANDOFF

From:
Cloud Literature Scout

To:
Local Codex / researcher with working eLibrary access

Task ID:
RQ-001-ELIB-LOCAL-01 (still open)

Related RQ:
RQ-001

Required action:
1. Execute ELIB-Q1…Q3 and all five Russian refinement strings exactly as recorded in sections 2.2–2.3.
2. First-pass filter: 2000–2026; earlier works only by backward chaining.
3. Record exact syntax accepted by eLibrary, date, filters, hits, title/metadata screened,
   abstract screened and included counts.
4. Deduplicate against the updated C01…C53 register.
5. Return new CORE/RELATED/BACKGROUND/REJECT records with reasons and DOI/eLibrary identifier.
6. State explicitly whether any new event/metric/aggregation/horizon category was added.

Do not:
Report zero hits without successful submission; infer full-paper content from titles;
broaden to a general reliability review; import before duplicate checks.

Expected result:
ZOTERO HANDOFF RESULT-compatible delta table plus exact eLibrary search log.
```

## 12. Final recommendation

### Recommendation: ADDITIONAL LIMITED CYCLE

RQ-001 mapping should not be marked COMPLETE yet.

Reasons:

1. Required ELIB-Q1…Q3 and five Russian refinements remain unexecuted; the local handoff result was not returned.
2. The refinement batch added combined accumulated/clustered and multibit-ECC reliability candidates.
3. The C32/C36 expansion added new event-count, support-circuit and measurement-uncertainty categories.
4. Two consecutive no-new-category batches have therefore not occurred.

### Strictly bounded next cycle

1. Complete `RQ-001-ELIB-LOCAL-01` against C01…C53.
2. Use only C45 and C46 as final expansion anchors: first 20 backward, first 20 forward and first 20 related records per non-empty route.
3. Stop if the eLibrary batch and the C45/C46 batch add no new event/metric/aggregation/horizon category.
4. If either adds a category, return the exact category and candidates to Orchestrator; do not expand recursively without a new decision.

## 13. Confidence and unresolved items

- **High:** IEEE refinement strings, live hit counts and 2000–2026 filter state observed on 2026-08-27.
- **High:** ResearchRabbit route totals and bounded screening counts.
- **High:** DOI/title identities matched by IEEE/ResearchRabbit and Scite for accepted delta records.
- **Medium:** CORE/RELATED screening, because it is intentionally abstract-level.
- **Unknown:** eLibrary coverage and hit counts.
- **Unknown:** final RQ-001 event, metric, aggregation and horizon; Paper Analyst and later Evidence Auditor work is required.
- **TBD:** any numerical reliability requirement and its mission/system provenance.
