# RQ-002 Literature Mapping — Initial Cycle

**Task ID:** `RQ-002-LITERATURE-MAPPING-01`  
**Related RQ:** `RQ-002`  
**Role:** Literature Scout  
**Execution date:** 2026-08-27 (UTC)  
**Canonical repository:** `z3tm4n-x/phd-adaptive-memory-ecc`  
**Required revision:** `1387065b313a3a4759bbe50bd36f2be46d0b0679`  
**Revision check:** `main` resolved to the required SHA immediately before report assembly.  
**Evidence level:** discovery and screening only; not claim-level adjudication.  
**Repository disposition:** returned to Research Orchestrator; **no GitHub write performed**.

## 1. Executive disposition

**Recommendation: `ADDITIONAL LIMITED CYCLE — ACCESS-ONLY COMPLETION`, not a second general search cycle.**

The mandatory IEEE Xplore strings, targeted ScienceDirect and SpringerLink routes, NASA NTRS route, and Scite discovery/identity checks were executed. All mandatory known candidates were identified and screened, including exact `arXiv:1704.07271v2` and the separate RADECS DOI identity. Twenty-five accepted candidate records were deduplicated and classified; five decision-value seeds were selected.

The protocol stopping criterion is not fully satisfied for two technical reasons:

1. OpenAlex fallback queries F4–F9 could not be completed after the interactive environment became unavailable; F1–F3 were executed with explicit display limits.
2. ResearchRabbit was not accessible, so the required bounded backward/forward/similar pass was **not executed in ResearchRabbit**. A small manual publisher/reference-chain fallback is reported separately and is not represented as ResearchRabbit coverage.

Accordingly, saturation is **NOT DEMONSTRATED**. The only recommended continuation is to complete OpenAlex F4–F9 and one bounded ResearchRabbit pass over the selected seeds, then deduplicate against this register. No new general RQ-002 search is recommended.

**C-RQ-05 disposition:** `GATE LIKELY TRIGGERED`. At discovery depth, several independent records make physical event topology, interleaving/physical-to-codeword mapping, and direct-versus-accumulated-event classification material to memory reliability calculations. This is a bounded escalation signal for the Orchestrator, not a permanent RQ and not an answer to RQ-002.

No stochastic class is selected. No numerical `H_req`, `ε_req`, or reliability threshold is assigned. `DEC-001` is unchanged; RQ-001 is not reopened; RQ-003 and RQ-004 responsibilities are preserved.

## 2. Search frame

### 2.1 Research Question

Какая минимальная стохастическая модель радиационно-индуцированных ошибок SRAM одновременно физически обоснована и вычислительно пригодна для моделирования накопления ошибок и адаптивного scrubbing?

Mandatory representation sub-question:

> Какое минимальное представление одного radiation event необходимо сохранить после отображения на ECC architecture, чтобы корректно вычислять `E_cap` при accumulation и scrubbing?

### 2.2 Search concepts and synonyms

| Concept | Executed/searchable terms |
|---|---|
| Memory | `SRAM`, `static random access memory`, `semiconductor memory` |
| Transient radiation upset | `single-event upset`, `SEU`, `soft error`, `radiation-induced upset` |
| Multiplicity | `multiple-cell upset`, `MCU`, `multiple-bit upset`, `MBU`, `multi-cell upset` |
| Arrival/count process | `Poisson process`, `stochastic model`, `statistical model`, `arrival process`, `upset rate`, `event SER`, `bit-flip SER` |
| Dependence | `spatial correlation`, `temporal correlation`, `burst`, `clustering`, `common-mode`, `topology`, `topography` |
| Provenance | `direct same-particle`, `single-particle multiple upset`, `sequential accumulation`, `independent arrivals`, `false/pseudo MCU/MBU` |
| Mapping | `physical-to-logical mapping`, `physical-cell-to-codeword mapping`, `interleaving`, `interleaving distance`, `geometric factor`, `codeword impact` |
| Event representation | `event mark`, `marked point process`, `multiplicity mark`, `joint codeword-impact mark`, `marginal multiplicity` |
| State/repair | `accumulated-error state`, `word age`, `exposure age`, `correction`, `writeback`, `reset`, `scrubbing phase`, `scan position` |
| Uncertainty/observation | `classification uncertainty`, `cross-section uncertainty`, `censored`, `imperfect observation`, `latent intensity`, `filtering`, `state estimation`, `event-wise measurement` |

### 2.3 Inclusion criteria

- Primary empirical irradiation/field study for SRAM or demonstrably comparable semiconductor memory.
- A statistical/stochastic model is defined, or the source supplies data that can test its assumptions.
- Multiplicity, topology, dependence, arrival process, rate variation, mapping, mechanism provenance, or classification uncertainty is extractable.
- Device technology, radiation environment, and measurement conditions permit a validity-domain assessment.
- At least one evidence element can be connected to the RQ-002 representation/model-selection problem and the DEC-001 computation contract.
- Peer-reviewed metadata and abstract are verifiable, or the record is a version-controlled mandatory source.
- English or Russian.

### 2.4 Exclusion criteria

- Aggregate SER only, with no multiplicity/process/measurement context.
- Independence or Poisson assumptions asserted without supporting model detail or testable data.
- Logic/register-only study with no justified transfer to SRAM.
- Simulation-only injection with no physical or empirical radiation basis.
- Secondary summary used in place of a traceable primary source.
- Object, protection context, or measurement/model cannot be identified.
- Duplicate record; related versions are linked but not silently collapsed.
- Permanent faults, cumulative TID, destructive SEE/SEFI, or other persistent mechanisms without separable transient-upset evidence.
- General inspection/maintenance/control scheduling without a radiation-error-model contribution.

**Time filter:** 2000–2026 for the first pass; earlier seminal work is admissible through backward chaining. Mandatory anchors are included regardless of date.

## 3. Source access and coverage

| Route | Status | What was executed | Limitation / interpretation |
|---|---|---|---|
| GitHub canonical state | ACCESSIBLE | `main`, required commit, all mandated documents, and Issue #3 checked | Used only for project instructions/state; no write performed |
| IEEE Xplore | ACCESSIBLE / metadata and abstracts | IEEE-Q1…Q9, all returned pages traversed | Subscription full text not assumed; discovery inclusion is not full-text verification |
| Scopus | UNAVAILABLE | Access test | Site unavailable; no search claim |
| Web of Science | UNAVAILABLE | Access test | Login/subscription barrier; no search claim |
| Engineering Village / Compendex / Inspec | UNAVAILABLE | Access test | Connection/502 barrier; no search claim |
| OpenAlex public fallback | PARTIAL | F1…F3 executed; exact hit counts captured | UI rendered only ten records per page despite larger totals; F4…F9 blocked by environment outage |
| Crossref fallback | UNAVAILABLE | REST/search endpoint access attempted | Endpoint could not be opened in the available environment; not represented as searched |
| ScienceDirect | PARTIAL | Six exact domain-targeted strings plus mandatory venue/anchor checks | Search-layer return counts are locator results, not complete ScienceDirect database totals |
| SpringerLink | PARTIAL | Six exact domain-targeted strings plus JETTA and Science China venue checks | Search-layer return counts are visible locator results, not complete SpringerLink totals |
| Scite | ACCESSIBLE / secondary | Nine discovery queries; DOI/title identity checks; editorial-signal sanity check for seeds/anchors | Boolean searches were noisy; tally is not evidence; no full supporting/contrasting audit performed |
| ResearchRabbit | UNAVAILABLE | Access attempt and public locator check | Required interactive graph pass not executable; manual fallback is labelled separately |
| NASA NTRS | ACCESSIBLE / public records | NTRS-Q1…Q5 and record-level checks | Web locator capped/combined some result sets; technical reports not promoted to peer-reviewed evidence |
| eLibrary | `DEFERRED / UNKNOWN COVERAGE` | **Not queried**, per protocol | Unavailability is not a zero-result finding |

## 4. Reproducible search log

Unless otherwise noted, date was 2026-08-27, language unrestricted, year filter 2000–2026, and document type unrestricted at discovery followed by protocol screening.

### 4.1 IEEE Xplore

| ID | Exact executed query | Hits | Title/metadata screened | Abstract screening | Included |
|---|---|---:|---:|---:|---|
| IEEE-Q1 | `SRAM AND ("single event upset" OR SEU OR "soft error") AND ("stochastic model" OR "statistical model" OR probability OR "upset rate")` | 165 | 165 | candidate subset | deduplicated at route level |
| IEEE-Q2 | `SRAM AND ("multiple cell upset" OR MCU OR "multiple bit upset" OR MBU) AND (spatial OR correlation OR distribution OR model*)` | 127 | 127 | candidate subset | deduplicated at route level |
| IEEE-Q3 | `(SRAM OR "semiconductor memory") AND radiation AND (nonstationary OR "non-stationary" OR "time-varying" OR intensity) AND (error OR upset)` | 132 | 132 | candidate subset | deduplicated at route level |
| IEEE-Q4 | `("radiation induced errors" OR "single event effects") AND SRAM AND (clustering OR burst OR correlation OR independence) AND (model OR measurement)` | 8 | 8 | candidate subset | deduplicated at route level |
| IEEE-Q5 | `SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "independent arrivals" OR "same particle") AND (ECC OR codeword OR interleaving)` | 3 | 3 | 3 | deduplicated at route level |
| IEEE-Q6 | `SRAM AND radiation AND ("compound Poisson" OR "marked Poisson" OR "marked point process" OR NHPP OR Cox OR renewal OR "hidden state")` | 0 | 0 | 0 | 0 |
| IEEE-Q7 | `SRAM AND radiation AND ("semi-Markov" OR PDMP OR "piecewise deterministic Markov" OR "renewal process")` | 0 | 0 | 0 | 0 |
| IEEE-Q8 | `SRAM AND radiation AND (filtering OR "state estimation" OR "partially observed" OR censored OR "imperfect observation")` | 44 | 44 | candidate subset | no explicit class retained |
| IEEE-Q9 | `SRAM AND radiation AND ("stochastic ordering" OR association OR "positive dependence")` | 8 | 8 | 8 | 0 |
| **IEEE total** | — | **487 hit occurrences** | **487 occurrences / 439 unique records after title-metadata dedup** | **24 candidate abstracts inspected** | **14 unique accepted records carried to final register** |

All result pages were traversed: Q1 `100+65`, Q2 `100+27`, Q3 `100+32`; Q4–Q9 fit on one page. Because records overlapped across Boolean strings, per-query inclusion counts were not retained as additive counts; the final candidate table supplies the stable deduplicated IDs and route provenance. This is an explicit reproducibility limitation rather than a reconstructed number.

### 4.2 Independent cross-publisher fallback

| ID | Exact executed query | Hits | Screened | Included | Status/notes |
|---|---|---:|---:|---:|---|
| OA-F1 | `SRAM "single event upset" stochastic model` | 255 | first 10 rendered | 0 new | UI claimed a larger page size but rendered ten; known records deduplicated |
| OA-F2 | `SRAM "multiple cell upset" spatial correlation topology` | 14 | first 10 rendered | 0 new | relevant identities already present through IEEE/publisher routes |
| OA-F3 | `SRAM radiation nonstationary time-varying upset rate` | 5 | 5 | 0 | all five title-level rejects or device-transient rather than SRAM arrival-process evidence |
| OA-F4 | `SRAM error accumulation scrubbing ECC reliability` | UNKNOWN | 0 | 0 | attempted; environment became unavailable |
| OA-F5 | `SRAM multiple event direct accumulation codeword interleaving` | UNKNOWN | 0 | 0 | not completed due same blocker |
| OA-F6 | `SRAM radiation compound Poisson marked process NHPP Cox renewal` | UNKNOWN | 0 | 0 | not completed due same blocker |
| OA-F7 | `SRAM radiation semi-Markov PDMP renewal process` | UNKNOWN | 0 | 0 | not completed due same blocker |
| OA-F8 | `SRAM radiation filtering state estimation partially observed censored` | UNKNOWN | 0 | 0 | not completed due same blocker |
| OA-F9 | `SRAM radiation stochastic ordering association positive dependence` | UNKNOWN | 0 | 0 | not completed due same blocker |

No equivalence to Scopus/WoS/Compendex coverage is claimed.

### 4.3 ScienceDirect targeted backfill

Counts below are records returned by the available domain/publisher locator, not complete database totals.

| ID | Exact executed query | Returned | Screened | Included |
|---|---|---:|---:|---|
| SD-Q1 | `SRAM AND "single event upset" AND ("stochastic model" OR "statistical model" OR "upset rate")` | 0 | 0 | 0 through exact locator; anchor/venue lookups added records separately |
| SD-Q2 | `SRAM AND ("multiple cell upset" OR MCU OR MBU) AND ("spatial correlation" OR topology OR multiplicity)` | 0 | 0 | 0 through exact locator |
| SD-Q3 | `SRAM AND radiation AND (nonstationary OR "time-varying" OR clustering OR burst)` | 2 | 2 | 0; both unrelated domains |
| SD-Q4 | `SRAM AND ("Poisson process" OR "arrival process") AND ("soft error" OR upset)` | 10 | 10 | 3 (`RQ2-C007`, `RQ2-C008`, `RQ2-C024`) |
| SD-Q5 | `SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "same particle") AND (ECC OR codeword OR interleaving)` | 0 | 0 | 0 through exact locator |
| SD-Q6 | `SRAM AND radiation AND ("compound Poisson" OR "marked point process" OR NHPP OR Cox OR renewal)` | 0 | 0 | 0 through exact locator |

Mandatory venue/anchor checks added: Microelectronics Reliability (`RQ2-C007`, `C008`, `C023`); NIM A (`C004` and one scope reject); NIM B and Radiation Physics and Chemistry produced no relevant record in the executed locator route. This is **NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTE**, not a database-wide zero.

### 4.4 SpringerLink targeted backfill

| ID | Exact executed query | Visible returned | Screened | Included |
|---|---|---:|---:|---|
| SPR-Q1 | `SRAM "multiple cell upset" spatial correlation` | 4 | 4 | 0 new |
| SPR-Q2 | `SRAM "single event upset" stochastic model` | 3 | 3 | 0 new |
| SPR-Q3 | `SRAM radiation upset multiplicity topology` | 10 | 10 | `RQ2-C017`; additional general background not registered as CORE |
| SPR-Q4 | `SRAM soft error accumulation scrubbing ECC` | 9 | 9 | background only |
| SPR-Q5 | `SRAM multiple event direct accumulation codeword mapping` | 1 | 1 | 0; unrelated proceedings result |
| SPR-Q6 | `SRAM radiation marked process nonhomogeneous Poisson hidden state` | 10 | 10 | 0; all unrelated/generic |

Mandatory title checks: Journal of Electronic Testing yielded `RQ2-C025` as BACKGROUND; Science China Technological Sciences yielded `RQ2-C016` as CORE plus layout/review background records. The available locator did not expose stable complete-journal hit totals.

### 4.5 NASA NTRS supplemental route

Exact strings:

1. `SRAM "multiple cell upset" radiation`
2. `SRAM SEU test heavy ion proton neutron`
3. `SRAM "soft error rate" model`
4. `SRAM scrubbing reliability radiation`
5. `SRAM multiple event accumulation ECC interleaving`

Q1–Q4 returned a capped/combined set of 30 public locator records; all 30 titles/metadata were screened, eight abstracts/record summaries were inspected, and three accepted identities were retained or cross-linked (`RQ2-C013`, `RQ2-C015`, and technical guidance as BACKGROUND). Q5 returned one record, *Strategies for SEE Hardness Assurance*, classified BACKGROUND. Per-query totals for Q1–Q4 were not exposed by the locator and are therefore not invented.

### 4.6 Scite secondary discovery

| ID | Exact executed query | Total indexed matches | Top records screened | New accepted |
|---|---|---:|---:|---|
| SCITE-Q1 | `SRAM AND ("single event upset" OR SEU OR "soft error") AND ("stochastic model" OR "statistical model" OR "Poisson process" OR "upset rate")` | 210 | 10 | `RQ2-C023` |
| SCITE-Q2 | `SRAM AND ("multiple cell upset" OR MCU OR "multiple bit upset" OR MBU) AND ("spatial correlation" OR topology OR multiplicity OR distribution)` | 2069 | 10 | 0 new; several existing identities |
| SCITE-Q3 | `SRAM AND radiation AND (nonstationary OR "non-stationary" OR "time-varying" OR burst OR clustering)` | 1265 | 10 | 0 new; `RQ2-C018` already known |
| SCITE-Q4 | `SRAM AND (scrubbing OR repair OR accumulation) AND ("error process" OR "arrival process" OR reliability) AND (ECC OR "error correction")` | 904 | 10 | 0 new |
| SCITE-Q5 | `SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "independent arrivals" OR "same particle") AND (ECC OR codeword OR interleaving)` | 202 | 10 | `RQ2-C021` |
| SCITE-Q6 | `SRAM AND radiation AND ("compound Poisson" OR "marked Poisson" OR "marked point process" OR NHPP OR "Cox process" OR renewal OR "hidden state")` | 527 | 10 | `RQ2-C022`; its abstract does not establish any queried advanced process class |
| SCITE-Q7 | `SRAM AND radiation AND ("semi-Markov" OR PDMP OR "piecewise deterministic Markov" OR "renewal process")` | 12 | 9 returned | 0 |
| SCITE-Q8 | `SRAM AND radiation AND (filtering OR "state estimation" OR "partially observed" OR censored OR "imperfect observation")` | 1449 | 10 | 0 |
| SCITE-Q9 | `SRAM AND radiation AND ("stochastic ordering" OR association OR "positive dependence")` | 2093 | 10 | 0 |

The high totals and many off-topic top results show that this corpus/interface did not enforce the concept intersection as tightly as IEEE Xplore. The counts are retained for reproducibility, but the presence of a lexical match is not treated as model evidence.

## 5. Deduplicated candidate register

Stable IDs below are discovery IDs for this report only. They are not permanent `PAPER` identifiers. `CORE` means direct decision value for RQ-002; it does not mean the full text has been adjudicated.

| ID | Publication | Identifier | Route / parent | Type / review | Class | Discovery-depth reason |
|---|---|---|---|---|---|---|
| RQ2-C001 | Clemente, Rezaei & Franco, **“Reliability of Error Correction Codes Against Multiple Events by Accumulation”** (2022), IEEE TNS | [10.1109/TNS.2022.3143652](https://doi.org/10.1109/TNS.2022.3143652) | mandatory C32; IEEE-Q5; Scite identity | journal / peer reviewed | CORE | Directly targets accumulation, ECC reliability and multiple events; exact mechanism partition and state semantics require PA |
| RQ2-C002 | Franco et al., **“Inherent Uncertainty in the Determination of Multiple Event Cross Sections in Radiation Tests”** (2020), IEEE TNS | [10.1109/TNS.2020.2977698](https://doi.org/10.1109/TNS.2020.2977698) | mandatory C51; IEEE-Q2; Scite | journal / peer reviewed / OA author copy located | CORE | Explicit false/ambiguous multiple-event classification and uncertainty |
| RQ2-C003 | Franco et al., **“Influence of Randomness During the Interpretation of Results From Single-Event Experiments on SRAMs”** (2019), IEEE TDMR | [10.1109/TDMR.2018.2886358](https://doi.org/10.1109/TDMR.2018.2886358) | mandatory C52; IEEE-Q2; Scite | journal / peer reviewed / OA author copy located | CORE | Statistical randomness can affect grouping of bitflips into multiple events |
| RQ2-C004 | Zebrev et al., **“Statistics and methodology of multiple cell upset characterization under heavy ion irradiation”** (2015), NIM A 775, 41–45 | [10.1016/j.nima.2014.11.106](https://doi.org/10.1016/j.nima.2014.11.106) | mandatory anchor; NIM A check; Scite | journal / peer reviewed | CORE | Multiplicity partitioning and experimental characterization; mapping and uncertainty propagation need PA |
| RQ2-C005 | Zebrev et al., **“Multiple Cell Upset Partitioning for Simulation of Soft Error Rates in Space Systems with Error Correcting Codes”** (2017) | exact [`arXiv:1704.07271v2`](https://arxiv.org/abs/1704.07271v2) | mandatory exact-version target | versioned preprint / not peer reviewed as this record | CORE | Extended equations for multiplicity partition and SEC-DED scrubbing; exact v2 controlled separately |
| RQ2-C006 | Zebrev et al., **“Multiple Cell Event Partitioning for Simulation of Soft Error Rates in Space Systems with Embedded Error Correcting Codes”** (2017), RADECS | [10.1109/RADECS.2017.8696217](https://doi.org/10.1109/RADECS.2017.8696217) | mandatory related identity; IEEE; Scite | conference / peer reviewed | CORE | Peer-reviewed related version; substantive relation to C005 remains unknown pending comparison |
| RQ2-C007 | Maestro & Reviriego, **“A method to eliminate the event accumulation problem from a memory affected by multiple bit upsets”** (2009), Microelectronics Reliability 49(7), 707–715 | [10.1016/j.microrel.2009.05.002](https://doi.org/10.1016/j.microrel.2009.05.002) | SD-Q4; manual chain from C001 | journal / peer reviewed | CORE | Explicitly juxtaposes direct MBU and accumulation; Poisson and correction assumptions require PA |
| RQ2-C008 | Moindjie et al., **“Multi-Poisson process analysis of real-time soft-error rate measurements in bulk 65 nm and 40 nm SRAMs”** (2017), Microelectronics Reliability 76–77, 53–57 | [10.1016/j.microrel.2017.07.045](https://doi.org/10.1016/j.microrel.2017.07.045) | SD-Q4; Scite | journal / peer reviewed / OA repository copy located | CORE | Abstract explicitly states independent Poisson processes by event multiplicity and neutron/alpha measurements |
| RQ2-C009 | Lee, Baeg & Reviriego, **“Memory Reliability Model for Accumulated and Clustered Soft Errors”** (2011), IEEE TNS 58(5), 2483–2492 | [10.1109/TNS.2011.2164555](https://doi.org/10.1109/TNS.2011.2164555) | IEEE-Q1/Q2; manual chain from C011 | journal / peer reviewed | CORE | Reliability model explicitly spans accumulated and clustered errors; detailed process/W semantics need PA |
| RQ2-C010 | Baeg, Wen & Wong, **“SRAM Interleaving Distance Selection With a Soft Error Failure Model”** (2009), IEEE TNS 56(4), 2111–2118 | [10.1109/TNS.2009.2015312](https://doi.org/10.1109/TNS.2009.2015312) | IEEE-Q2; manual chain from C011 | journal / peer reviewed | CORE | Connects physical interleaving distance to a failure model; direct relevance to mapping `W` |
| RQ2-C011 | Ogden & Mascagni, **“The Impact of Soft Error Event Topography on the Reliability of Computer Memories”** (2017), IEEE Transactions on Reliability 66(4), 966–979 | [10.1109/TR.2017.2765484](https://doi.org/10.1109/TR.2017.2765484) | IEEE-Q1/Q2; Scite identity | journal / peer reviewed | CORE | Abstract reports reliability sensitivity to full event topography, ECC, interleaving and periodic scrubbing |
| RQ2-C012 | Clemente et al., **“Impact of the Bitcell Topology on the Multiple-Cell Upsets Observed in VLSI Nanoscale SRAMs”** (2021), IEEE TNS 68(9), 2383–2391 | [10.1109/TNS.2021.3099202](https://doi.org/10.1109/TNS.2021.3099202) | IEEE-Q2 | journal / peer reviewed | CORE | Empirical/physical evidence that bitcell topology affects observed MCU structure |
| RQ2-C013 | Black et al., **“Characterizing SRAM Single Event Upset in Terms of Single and Multiple Node Charge Collection”** (2008), IEEE TNS | [10.1109/TNS.2008.2007231](https://doi.org/10.1109/TNS.2008.2007231); NTRS 20080038642 | NASA-Q1/Q2; IEEE-Q2 | journal / peer reviewed; NASA record cross-link | RELATED | Mechanism evidence for direct single/multiple-node charge collection, not a complete error process |
| RQ2-C014 | Lawrence & Kelly, **“Single Event Effect Induced Multiple-Cell Upsets in a Commercial 90 nm CMOS Digital Technology”** (2008), IEEE TNS 55(6), 3367–3374 | [10.1109/TNS.2008.2005981](https://doi.org/10.1109/TNS.2008.2005981) | IEEE-Q2 | journal / peer reviewed | CORE | Direct same-particle MCU mechanism and technology-domain evidence |
| RQ2-C015 | Tipton et al., **“Device-Orientation Effects on Multiple-Bit Upset in 65 nm SRAMs”** (2008), IEEE TNS | [10.1109/TNS.2008.2006503](https://doi.org/10.1109/TNS.2008.2006503); NTRS 20080034465 | NASA-Q1/Q2; IEEE-Q2 | journal / peer reviewed; NASA record cross-link | RELATED | Orientation-dependent MBU structure; informs domain transfer and topology |
| RQ2-C016 | Chen, Chen & Yao, **“Characterization of single-event multiple cell upsets in a custom SRAM in a 65 nm triple-well CMOS technology”** (2015), Science China Technological Sciences 58, 1726–1730 | [10.1007/s11431-015-5906-0](https://doi.org/10.1007/s11431-015-5906-0) | Springer venue check | journal / peer reviewed | CORE | Non-IEEE primary MCU characterization in a specified SRAM technology |
| RQ2-C017 | Boruzdina, Grigor’ev & Ulanova, **“Effect of topological placement of memory cells in memory chips on multiplicity of cell upsets from heavy charged particles”** (2014), Russian Microelectronics 43, 96–101 | [10.1134/S1063739714020036](https://doi.org/10.1134/S1063739714020036) | SPR-Q3 | journal / peer reviewed | RELATED | Topological placement and multiplicity evidence; transfer to post-`W` event mark requires PA |
| RQ2-C018 | Chen et al., **“Solar Particle Event and Single Event Upset Prediction from SRAM-Based Monitor and Supervised Machine Learning”** (2022), IEEE TETC | [10.1109/TETC.2022.3147376](https://doi.org/10.1109/TETC.2022.3147376) | IEEE-Q3; SCITE-Q3 | journal / peer reviewed | RELATED | Supports material time variation in radiation intensity and hourly SEU-rate estimation; not itself selection of NHPP/Cox |
| RQ2-C019 | Franco et al., **“Best-Fit Techniques to Estimate SBU/MCU Cross Sections From Radiation-Ground Tests in Memories”** (2025), IEEE TNS 72(4), 1403–1411 | [10.1109/TNS.2025.3539956](https://doi.org/10.1109/TNS.2025.3539956) | IEEE-Q1/Q2 | journal / peer reviewed | CORE | Parameter estimation and SBU/MCU identifiability/uncertainty evidence |
| RQ2-C020 | Gomi et al., **“Quasi Event-Wise Measurement and Simulation of Neutron-Induced Multiple-Cell Upsets in 22- and 55-nm SRAMs”** (2026), IEEE TNS 73(8), 2935–2947 | [10.1109/TNS.2026.3675003](https://doi.org/10.1109/TNS.2026.3675003) | IEEE-Q2; Scite identity; manual chain | journal / peer reviewed | CORE | Abstract explicitly identifies the static-bitmap trade-off between pseudo MCUs and spatially distant MCUs |
| RQ2-C021 | Clemente, Franco, Baylac et al., **“Statistical Anomalies of Bitflips in SRAMs to Discriminate MCUs from SEUs”** (2015), RADECS | [10.1109/RADECS.2015.7365670](https://doi.org/10.1109/RADECS.2015.7365670) | SCITE-Q5; manual uncertainty chain | conference / peer reviewed / OA author copy located | CORE | Statistical discrimination of MCU versus SEU in neutron tests; direct observation-classification relevance |
| RQ2-C022 | Maestro & Reviriego, **“Study of the effects of MBUs on the reliability of a 150 nm SRAM device”** (2008), conference proceedings | [10.1145/1391469.1391704](https://doi.org/10.1145/1391469.1391704) | SCITE-Q6; manual chain from C011 | conference / peer reviewed | CORE | Early MBU-aware SRAM reliability model; advanced process-class terms in Q6 are not established by the abstract |
| RQ2-C023 | Sajid, Chechenin & Sill Torres, **“Single Event Upset rate determination for 65 nm SRAM bit-cell in LEO radiation environments”** (2017), Microelectronics Reliability 78, 11–16 | [10.1016/j.microrel.2017.07.084](https://doi.org/10.1016/j.microrel.2017.07.084) | SCITE-Q1; publisher venue check | journal / peer reviewed | RELATED | Environment-to-rate calculation and validation domain; aggregate-rate reduction risk remains |
| RQ2-C024 | Epiphany & Sugantha, **“Radiation hardened 11T memory cell for space applications”** (2023), Microprocessors and Microsystems 102, 104914 | [10.1016/j.micpro.2023.104914](https://doi.org/10.1016/j.micpro.2023.104914) | SD-Q4 | journal / peer reviewed | BACKGROUND | Cell-hardening context; a compound-Poisson mention is not empirical validation of that class for RQ-002 |
| RQ2-C025 | Marques, Meinhardt & Butzen, **“Soft Errors Sensitivity of SRAM Cells in Hold, Write, Read and Half-Selected Conditions”** (2021), Journal of Electronic Testing 37, 263–270 | [10.1007/s10836-021-05944-2](https://doi.org/10.1007/s10836-021-05944-2) | Springer JETTA check; Scite identity | journal / peer reviewed | BACKGROUND | Operating-condition sensitivity; useful boundary context, not a complete event/accumulation model |

### 5.1 Representative rejects and borderline exclusions

| Record/group | Disposition | Reason |
|---|---|---|
| Ding et al., *Analysis of multiple cell upset characteristics for logical circuits in radiation environment* (NIM A; PII `S0168900220308548`) | REJECT | Logic-circuit focus; no justified SRAM-process transfer in discovery metadata |
| Timepix/spatiotemporally correlated SEE detector records | REJECT | Detector-event processing, not an SRAM radiation arrival/accumulation model |
| FPGA configuration-memory scrubbing/mitigation papers without transferable physical SRAM process evidence | REJECT or BACKGROUND | Architecture/mitigation only; base RQ is the transient SRAM error process |
| Pure hardened-cell/topology designs with no process or measurement model | BACKGROUND | Relevant device context but insufficient for arrival/mark/state selection |
| TID, permanent-fault, destructive SEE/SEFI records | REJECT | Explicit failure-domain exclusion |
| Generic inspection/maintenance/control scheduling | REJECT / route to backlog | Explicitly outside this cycle |
| General reliability, neuroscience, seismology, networking, and software-NHPP lexical matches | REJECT | Boolean lexical collision; wrong object/domain |

## 6. Mandatory-anchor and Zebrev version control

| Required identity | Verified metadata/access | Screening | Version/relation status | Next action |
|---|---|---|---|---|
| C32 → RQ2-C001 | DOI/title/authors/year/venue verified in IEEE and Scite; subscription full text not assumed | CORE | Single journal identity | Zotero record; priority Paper Analyst extraction |
| C51 → RQ2-C002 | DOI `10.1109/TNS.2020.2977698`; IEEE TNS 67(7), 1547–1554; OA author copy located | CORE | Single journal identity | Zotero; targeted uncertainty/classification extraction |
| C52 → RQ2-C003 | DOI `10.1109/TDMR.2018.2886358`; IEEE TDMR 19(1), 104–111; OA author copy located | CORE | Single journal identity | Zotero; targeted randomness/false-event extraction |
| Zebrev-2015 → RQ2-C004 | DOI/title/venue/pages verified through publisher/Scite; full text not assumed | CORE | Separate 2015 journal source | Zotero; multiplicity/uncertainty extraction if needed after C005 |
| Exact Zebrev-v2 → RQ2-C005 | `arXiv:1704.07271v2`; title and five authors verified; v1 submitted 24 Apr 2017 15:08:16 UTC; **v2 revised 15 Oct 2017 14:44:18 UTC**, 324 KB, 5 pages, 8 figures; exact v2 abstract page and PDF URL located | CORE | Mandatory preprint identity. The generic DOI `10.48550/arXiv.1704.07271` does not by itself encode `v2` | Attach exact v2 PDF in Zotero; highest-priority PA target |
| RADECS → RQ2-C006 | DOI `10.1109/RADECS.2017.8696217`; title/authors/year verified in IEEE/Scite | CORE | Separate peer-reviewed conference identity. Title differs from C005: **“Multiple Cell Event…”** and **“with Embedded Error Correcting Codes”** | Cross-link, do not merge; compare against exact v2 |

**Substantive difference status for RQ2-C005 versus RQ2-C006:** `UNKNOWN — REQUIRES FULL-TEXT COMPARISON`.

No earlier arXiv version, conference manuscript, or RADECS file is accepted as a substitute for `arXiv:1704.07271v2`.

## 7. Strong seed papers

Seeds were chosen for model-selection value and complementary coverage, not citation count.

| Seed | Decision value |
|---|---|
| RQ2-C001 — Clemente et al. 2022 | Directly addresses ECC reliability under multiple-event accumulation and is the strongest bridge to DEC-001 state/window semantics |
| RQ2-C005 — Zebrev et al. exact arXiv v2 | Contains the mandatory multiplicity partition and SEC-DED scrubbing equations; RQ2-C006 remains a linked, separate comparison identity |
| RQ2-C008 — Moindjie et al. 2017 | Empirical real-time SRAM measurements with explicit independent multi-Poisson processes by event multiplicity and radiation mechanism |
| RQ2-C011 — Ogden & Mascagni 2017 | Tests how much reliability changes when full event topography is retained versus reduced, under ECC/interleaving/scrubbing choices |
| RQ2-C018 — Chen et al. 2022 | Provides the strongest discovered time-variation/nonstationarity signal and a concrete hourly-rate estimation context |

RQ2-C020 is not counted as a sixth seed but is a high-priority Paper Analyst candidate because it targets the observation/classification ambiguity that can confound direct MCU with accumulated/pseudo MCU.

## 8. Eight-category DEC-001 coverage matrix

| Evidence category | Plausible candidates | Discovery coverage | Named gap / DEC-001 implication |
|---|---|---|---|
| 1. Arrival/count process | C007, C008, C018, C023 | PARTIAL | HPP/multi-Poisson examples and time-varying rate motivation exist; no discovered source establishes the minimum class for `F_A(t0,T; μ_t0)` |
| 2. Stationarity/nonstationarity | C008, C018, C023 | WEAK–PARTIAL | C018 supports material time variation; an explicit NHPP/Cox/latent-intensity SRAM model was not found |
| 3. MCU/MBU multiplicity distribution | C004–C006, C008, C012–C017, C019–C022 | STRONG at discovery | Physical multiplicity is well represented, but sufficiency after mapping `W` is not established |
| 4. Spatial topology/correlation | C010–C017, C020 | STRONG at discovery | Topology/interleaving can matter; exact joint inter-word dependence and transferable parametrization remain PA questions |
| 5. Direct-event vs independent-accumulation provenance | C001–C009, C020–C022 | PARTIAL–STRONG | All three concerns—direct event, sequential accumulation, false grouping—are represented, but disjointness/recombination and double-counting require full text |
| 6. Mapping/partition implications for `E_cap` | C001, C005–C006, C009–C011 | PARTIAL | Interleaving and codeword-level models exist; explicit physical-cell-to-codeword mapping `W` and exact post-mapping joint event mark are often absent or unknown |
| 7. Initial state, exposure age and scrub-state variables | C001, C005, C007, C009, C011 | WEAK | No discovery source clearly specifies the complete `μ_t0`, sequential word ages, scrubber phase/scan state, and correction/writeback semantics required by DEC-001 |
| 8. Empirical validation and domain of validity | C002–C004, C008, C012–C023 | PARTIAL–STRONG by mechanism | Many device/test domains are available; cross-technology/environment transfer, model-form uncertainty, and propagation to `E_cap/F_A` remain unresolved |

Each category has at least one plausible candidate or an explicit gap. Coverage is not a claim that the evidence is sufficient or mutually consistent.

## 9. Candidate model-class sensitivity

| Candidate class | Relevant discovery evidence | Primitive/state/mark implications | Identifiability, validation, computation | Disposition |
|---|---|---|---|---|
| Homogeneous Poisson process (HPP) | C007 invokes Poisson accumulation; C008 explicitly reports independent Poisson processes by multiplicity | Requires event definition, rate(s), multiplicity mark, and reset semantics | Rates can be fitted in a declared stationary regime; goodness-of-fit and transfer domain need PA | RELEVANT EVIDENCE FOUND; not selected |
| Nonhomogeneous Poisson process (NHPP) | C018 supports large time variation and hourly rate estimation but does not, at discovery level, identify an NHPP model | Deterministic time-varying intensity plus event mark/state | Intensity data may be estimable; exact likelihood/validation/computation unknown | NO DIRECT SRAM/RADIATION NHPP EVIDENCE FOUND IN EXECUTED ROUTES |
| Compound Poisson process | C024 contains only background-level mention; C009/C022 may be structurally related but abstracts do not establish the class | Parent-event arrivals plus batch/multiplicity mark | Requires event-rate versus bit-flip-rate separation | NO DECISION-GRADE DIRECT EVIDENCE FOUND; `UNKNOWN — PAPER ANALYST` for C009/C022 |
| Cox / doubly stochastic process | None relevant | Latent random intensity and its state/filter | Requires replicated/temporal data and latent-intensity validation | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |
| Marked point / marked Poisson process | Sources use multiplicity/topography conceptually (C004–C012), but no executed record explicitly establishes this named class | Arrival plus joint post-`W` mark | Mark distribution and dependence must be identifiable | NO EXPLICIT CLASS EVIDENCE FOUND; event-mark interpretation remains an inference, not a project choice |
| Renewal process | None relevant | Interarrival-age state beyond HPP | Needs non-exponential interarrival evidence | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |
| Semi-Markov process | None relevant | Discrete state plus non-exponential dwell times | Larger state/estimation burden | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |
| PDMP | None relevant | Continuous age/intensity state with jump/reset dynamics | Potentially tractable but no empirical justification found | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |
| Hidden/partially observed process | C002, C003, C020, C021 motivate latent true-event grouping behind imperfect observations | Hidden parent-event/provenance state and observation model | Classification probabilities may be estimable; no complete hidden-state process found | IMPERFECT-OBSERVATION MOTIVATION FOUND; explicit process class not found |
| Filtering/state estimation | C018 uses supervised prediction; this is not evidence for filtering the memory error state | Would require observation process and latent state | RQ-004 boundary must be preserved | NO RELEVANT SRAM ACCUMULATION-STATE FILTERING EVIDENCE FOUND |
| Censored/imperfect observations | C002, C003, C020, C021 | True event topology/provenance may be latent or misgrouped | Strong empirical motivation; propagation to reliability largely unknown | RELEVANT EVIDENCE FOUND; no stochastic observation model selected |
| Stochastic ordering | None relevant; IEEE-Q9 and Scite-Q9 were false/general matches | Would require ordered dependence assumptions and proof | Bound validity cannot be inferred | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |
| Positive dependence/association | Topological clustering is observed, but association in the mathematical sense was not established | Requires joint law and checked association assumptions | No conservative bound accepted without proof | NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES |

Absence in the executed routes is not interpreted as mathematical impossibility.

## 10. Required per-paper/model fields — discovery-depth extraction

Legend: `EXP` = explicit in title/abstract/verified metadata; `IND` = indicated but requires full-text confirmation; `U-PA` = `UNKNOWN — PAPER ANALYST`; `N/A-scope` = source is evidence for a narrower component, not a complete operational model.

### 10.1 Arrival, mark and mapping fields

| ID | Primitive arrival object | Count/arrival process and intensity | Stationarity | Multiplicity / topology / temporal clustering | Parent-event provenance | `W` and post-mapping event representation |
|---|---|---|---|---|---|---|
| C001 | Multiple event affecting protected memory/ECC context (IND) | Accumulation model; exact process/rates U-PA | U-PA | Multiple events; topology U-PA | Direct versus sequential separation U-PA | ECC context EXP; explicit `W` and joint mark U-PA |
| C002 | Observed bitflips grouped as candidate multiple events (EXP) | Radiation-test counts; exact temporal law U-PA | Test-regime only; U-PA | Spatial-neighbour false grouping EXP | True parent event latent/ambiguous EXP | Physical/test partition; codeword `W` absent at discovery |
| C003 | Observed bitflips/candidate SBU-MBU grouping (EXP) | Random grouping/count model IND | U-PA | Separation-distance/randomness effects IND | Parent link uncertain EXP | `W` absent at discovery |
| C004 | Heavy-ion physical event (IND) | Multiplicity-resolved event/cross-section statistics IND | U-PA | Multiplicity EXP; full topology U-PA | Event grouping retained at physical level IND | Mapping to ECC word U-PA/absent in metadata |
| C005 | Ion-induced event (IND) | Multiplicity-partitioned rates, Eqs. (2)–(11), exact law U-PA | U-PA | Multiplicity EXP; topology dependence U-PA | Parent event appears retained before reduction (IND) | ECC conversion and Section III.D are mandatory U-PA targets; exact `W` treatment U-PA |
| C006 | Same candidate physical class as C005 (IND) | U-PA pending version comparison | U-PA | Event partition EXP | U-PA | Embedded-ECC context EXP; exact mapping U-PA |
| C007 | Direct MBU event plus independent-event accumulation (EXP/IND) | Poisson accumulation indicated; parameterization U-PA | Likely fixed irradiation regime; not verified | Direct multiplicity and sequential accumulation EXP; topology U-PA | Mechanisms distinguished at least conceptually EXP | Memory/ECC handling U-PA; explicit `W` unknown |
| C008 | Single soft-error event with bit-flip multiplicity (EXP) | Independent parallel Poisson processes by multiplicity; neutron/alpha rates EXP | Fixed-rate test windows indicated; fit tests U-PA | Multiplicity mark EXP; spatial topology U-PA; no burst evidence in abstract | Parent event retained in event-wise measurement (IND) | No ECC-word mapping in discovery metadata |
| C009 | Accumulated and clustered soft errors (EXP) | Reliability process U-PA | U-PA | Accumulated vs clustered EXP; detailed topology U-PA | Likely distinguishes clusters; exact provenance U-PA | Memory/ECC representation U-PA |
| C010 | Soft-error event under SRAM failure model (IND) | Process law U-PA | U-PA | Spatial separation/interleaving distance EXP | Parent-event handling U-PA | Interleaving distance is explicit abstraction of `W`; joint mark U-PA |
| C011 | Soft-error event with event topography (EXP) | Arrival law U-PA | U-PA | Full topography versus reduced representation EXP; temporal clustering U-PA | Full event identity/topography retained (IND) | ECC, interleaving and periodic scrubbing scenarios EXP; formal `W` U-PA |
| C012 | Radiation event causing MCU (EXP) | Empirical event counts/cross sections IND | Declared irradiation regime only | Bitcell topology and MCU multiplicity EXP | Same-particle event context IND | Physical topology EXP; post-codeword mapping absent |
| C014 | Single-event-induced MCU (EXP) | Empirical event/cross-section context IND | Declared irradiation regime only | Direct MCU/charge-sharing mechanism EXP | Same-particle provenance EXP | `W` absent |
| C016 | Single-event MCU in custom 65 nm SRAM (EXP) | Empirical characterization; process law U-PA | Declared irradiation regime only | Multiplicity EXP; spatial details U-PA | Same-event provenance IND | `W` absent |
| C018 | SEU counts/rate from SRAM monitor (EXP) | Time-varying/hourly estimated rate EXP; named stochastic class absent | Nonstationarity motivation EXP | Scalar SEU rate; multiplicity/topology not central | Parent-event detail absent | `W` absent; aggregate-rate level |
| C019 | Observed SBU/MCU radiation-test events (EXP) | Best-fit estimation of mechanism-specific cross sections EXP | Test-regime stationarity U-PA | Multiplicity classes EXP; topology U-PA | Classification/model latent elements IND | `W` absent at discovery |
| C020 | Neutron event approximated by rapid successive scans (EXP) | Event-wise count process; temporal law U-PA | Test-regime only | Multiplicity and spatially distant MCUs EXP | Quasi-event-wise provenance retained with measurement limits EXP | Physical addresses/topology; ECC `W` absent |
| C021 | Observed bitflips grouped as SEU/MCU (EXP) | Statistical discrimination model EXP; temporal law U-PA | Test-regime only | Multiplicity and spatial anomaly EXP | True parent event is latent target EXP | `W` absent |
| C022 | Soft-error/MBU event (EXP) | Reliability model exists; exact count law U-PA | U-PA | MBU multiplicity EXP; topology U-PA | U-PA | SRAM reliability context EXP; mapping/interleaving U-PA |

### 10.2 State, repair, uncertainty, validation and DEC-001 fields

| ID | Accumulation state / initial distribution | Correction, writeback, reset, scrub / word age | Uncertainty treatment | Empirical validation and validity domain | Computational tractability | Connection to `E_cap` / `F_A` |
|---|---|---|---|---|---|---|
| C001 | Accumulated multi-error state IND; `μ_t0` U-PA | ECC handling EXP; exact correction/reset/scrub and word-age U-PA | U-PA | Model/domain U-PA | Analytic/numerical model exists; cost U-PA | High potential; exact mapping to DEC event/window U-PA |
| C002 | N/A-scope; test bitmap/grouping state | No operational scrub semantics | Cross-section/classification uncertainty EXP | SRAM/FPGA radiation tests EXP; transfer domain U-PA | Statistical computation likely bounded; cost U-PA | Propagation from test uncertainty to `F_A` U-PA |
| C003 | N/A-scope; observed bitmap/grouping state | No operational scrub semantics | Random false-event uncertainty EXP | SRAM experiments EXP | Statistical method; cost U-PA | Reliability propagation U-PA |
| C004 | N/A-scope or multiplicity-rate state; initial operational state absent | Scrub semantics absent in discovery | Statistical methodology indicated; exact uncertainty U-PA | Heavy-ion data/domain EXP | Partition computation indicated | Supplies physical event-rate inputs; DEC integration U-PA |
| C005 | Error-count/word state implied by SEC-DED equations; initial state U-PA | Section III.D, Eqs. (15)–(19) mandatory; sequential word age U-PA | U-PA | Abstract claims ground/on-orbit validation; exact scope U-PA | Closed-form approximation indicated; domain/cost U-PA | Directly targets ECC/system rate; equivalence to `E_cap` must not be assumed |
| C006 | U-PA | U-PA pending comparison | U-PA | Peer-reviewed conference; validation content U-PA | U-PA | U-PA pending comparison |
| C007 | Accumulated-errors state IND; initial state U-PA | Correction used to eliminate accumulation; exact writeback/reset U-PA | U-PA | Memory under MBU context; empirical basis U-PA | Likely analytic; verify | Strong accumulation bridge; DEC window/initial-state compatibility U-PA |
| C008 | Real-time measurement state; operational accumulation state limited/absent | Detection followed by writeback indicated; exact reset semantics U-PA; word age absent | Rate-fit uncertainty U-PA | 65/40 nm bulk SRAM; altitude/underground; neutron/alpha EXP | Multi-Poisson fit computationally light in principle; verify | Supplies candidate arrival/mark inputs, not complete `E_cap` computation |
| C009 | Accumulated per-word error state likely; `μ_t0` U-PA | ECC/scrub semantics U-PA; word age U-PA | U-PA | Validation/model domain U-PA | Model computation U-PA | Potential direct bridge; requires full equations |
| C010 | Failure-model state U-PA; initial state U-PA | ECC handling indicated; scrub/reset/age U-PA | U-PA | SRAM/interleaving domain EXP | Selection/model calculation likely bounded; verify | Strong `W` sensitivity input; DEC event semantics U-PA |
| C011 | Memory state under topographic events; initial state U-PA | Periodic scrubbing and ECC scenarios EXP; exact correction/writeback/phase/age U-PA | U-PA | Computer-memory model; event data/validation domain U-PA | Simulation/model cost U-PA | Tests information loss relevant to `E_cap`; exact DEC mapping U-PA |
| C012 | N/A-scope; physical-event evidence | No operational repair semantics | Measurement uncertainty U-PA | VLSI nanoscale SRAM, bitcell-topology domain EXP | N/A-scope | Supports need to retain topology before `W` |
| C014 | N/A-scope; direct physical mechanism | No operational repair semantics | Measurement uncertainty U-PA | Commercial 90 nm technology EXP | N/A-scope | Supplies direct-event mechanism input |
| C016 | N/A-scope; empirical event data | No operational repair semantics | U-PA | Custom 65 nm triple-well SRAM EXP | N/A-scope | Supplies multiplicity/topology input; DEC mapping U-PA |
| C018 | Rate-estimation state; operational memory state absent | No correction/reset/scrub semantics in discovery | Prediction uncertainty U-PA | SRAM monitor; solar-particle-event regime EXP | Hourly prediction appears tractable; verify | Supports time-varying intensity input, not full `F_A` |
| C019 | Test-level fit state | No operational scrub semantics | Fit/cross-section uncertainty central EXP | Ground radiation tests in memories EXP | Best-fit estimation likely bounded; verify | Parameter uncertainty propagation to `F_A` U-PA |
| C020 | Rapid-scan bitmap and event-grouping state EXP | Self-scan/write timing EXP; operational ECC scrub U-PA | False/pseudo versus missed-distant MCU classification central EXP | Neutron tests, 22/55 nm SRAM EXP | Measurement/simulation cost U-PA | Critical for identifying valid event marks before `W`; reliability propagation U-PA |
| C021 | Test bitmap/grouping state | No operational scrub semantics | Statistical discrimination uncertainty EXP | 130/90 nm Cypress SRAM, neutron tests EXP | Statistical method likely bounded; verify | Corrects candidate event-rate inputs; propagation U-PA |
| C022 | Reliability state U-PA; initial state U-PA | ECC/scrub/age U-PA | U-PA | 150 nm SRAM model/device context EXP | U-PA | MBU-aware reliability bridge; exact DEC compatibility U-PA |

The dominant common unknown is the operational state contract: complete initial distribution, per-word exposure age, scrubber phase/scan position, and parameterized correction/writeback/reset semantics.

## 11. Minimal event-representation hierarchy

| Reduction level | Retained information | Lost information/dependencies | Parent-event provenance | Discovery evidence | Exact / bound / approximation / bias status |
|---|---|---|---|---|---|
| **Full physical event topology + declared `W`** | Particle/event identity; physical cell addresses; spatial shape; multiplicity; full deterministic mapping to codewords; joint cross-word impact | None relative to the declared physical observation/model, except unobserved device physics | Preserved | C011, C012, C014–C017, C020 support topology/mechanism relevance; explicit full `W` is uncommon | Candidate exact input only if event topology and `W` are known without grouping error; measurement/model approximation otherwise |
| **Joint post-mapping codeword-impact mark** | Parent-event time/ID; set or vector of affected codewords; bit positions/multiplicities per word; cross-word dependence | Detailed track/charge geometry and physical distances not needed after mapping; device-level causal detail | Preserved if mark is event-indexed | C001, C005–C006, C010–C011 motivate codeword/ECC/interleaving representation | Potentially exact for the DEC-001 physical/codeword event conditional on correct `W`, mark construction and repair semantics; no executed source proves sufficiency generally |
| **Marginal per-word multiplicity distributions** | Distribution of number of affected bits in an individual word or class | Joint inter-word dependence; spatial topology; which word impacts share one parent event; cross-partition common cause | Usually lost | C004–C008 supply multiplicity partitions/rates; C010–C011 warn that mapping/topography can matter | Approximation unless factorization/symmetry/sufficiency is proved. No bound was verified; systematic bias in `E_cap` is possible |
| **Scalar event rate or bit-upset rate** | Mean count intensity at one chosen aggregation level | Multiplicity, topology, mark law, parent-event grouping, cross-word dependence, event-rate versus bit-flip-rate distinction, and often time variation | Lost | C018/C023 provide rate-level inputs; C008 explicitly distinguishes event and bit-flip related quantities | Exact only for metrics depending solely on the chosen scalar count under checked assumptions; otherwise a potentially biased reduction for accumulation/scrubbing |

No executed source establishes that marginal `q_k` is sufficient. No association or stochastic-ordering bound is accepted.

## 12. Direct same-particle versus independent accumulation

Legend: `E` explicit in discovery material; `I` indicated; `U` = `UNKNOWN — PAPER ANALYST`; `A` absent from discovery; `N/S` not source scope.

### 12.1 Mechanism, partition and mapping

| ID | Direct same-particle | Independent accumulation | False/ambiguous classification | Partition level | Representation of `W` |
|---|---|---|---|---|---|
| C001 | U | E (title/abstract scope) | U | ECC/multiple-event reliability; exact level U | U; ECC context only at discovery |
| C002 | I as true-event comparator | E as accidental independent bitflips | E | Observed physical-neighbour/event classification | A at discovery |
| C003 | I as true-event comparator | E as random coincident bitflips | E | Test bitmap/spatial grouping | A at discovery |
| C004 | E/IND heavy-ion MCU | U | U | Physical multiplicity/cross section | U/A at discovery |
| C005 | E/IND ion-induced multiplicity | Section III.D likely includes sequential term; exact status U | U | Physical multiplicity then ECC-rate conversion; exact ordering U | Statistical/geometric assumption U; mandatory PA target |
| C006 | I | U | U | Event partition and embedded ECC; details U | U pending version comparison |
| C007 | E | E | U | Memory/MBU and accumulated-event level; exact physical/post-`W` level U | U |
| C008 | E/IND event multiplicity | Independent Poisson event streams E; operational accumulation not central | Measurement grouping U | Event multiplicity and radiation mechanism | A at discovery |
| C009 | Clustered errors E/IND | Accumulated errors E | U | Reliability-model level U | U |
| C011 | Topographic parent event I | Accumulation under event arrivals/scrub U | U | Full event topography and mapped memory scenarios | Interleaving/model abstraction E; exact `W` U |
| C020 | Direct MCU E | Pseudo MCU from independent events E | E | Quasi-event-wise physical bitmap/topology | A for ECC; physical addresses retained |
| C021 | True MCU E/IND | Independent SEUs as false MCU E | E | Statistical/spatial test classification | A |
| C022 | MBU E/IND | U | U | SRAM reliability model; exact level U | U |

### 12.2 Separate quantities, recombination and uncertainty

| ID | Separate mechanism-specific cross sections / probabilities / rates | Recombination rule | Disjointness vs additive approximation | Asymptotic/small parameter | Classification uncertainty | Propagation into reliability |
|---|---|---|---|---|---|---|
| C001 | U | U | U | U | U | Reliability is target; uncertainty propagation U |
| C002 | Multiple-event cross-section uncertainty E | Statistical correction/interval IND | Exact non-overlap U | U | E | Remains at test/cross-section level in discovery; operational propagation U |
| C003 | SBU/MBU grouping quantities IND | Statistical correction IND | U | Approximation conditions U | E | U |
| C004 | Multiplicity-specific quantities IND | Sum/partition details U | U | U | U | U |
| C005 | `R_w(n≥1)` and `R_w(n≥2)` are explicit PA targets | Eq. (15) terms must be interpreted | **U — core PA question** | `β << 1` is explicit PA target | U | U |
| C006 | U | U | U | U | U | U |
| C007 | Separate direct/accumulation terms IND | Elimination/correction method IND | U | U | U | Reliability result IND; uncertainty U |
| C008 | Separate neutron/alpha and multiplicity-process rates E | Superposition/recombination details U | Independence is stated; validation U | U | U | Rate-model fit; ECC reliability propagation A/U |
| C009 | Clustered/accumulated components IND | U | U | U | U | Reliability result IND |
| C011 | Topography alternatives E | Reliability simulation/model U | Not a mechanism-addition claim | U | U | Reliability sensitivity EXP/IND; uncertainty U |
| C020 | Event-wise versus pseudo/distant classification E | Measurement/simulation grouping rule IND | Classification trade-off E; exact error rates U | Scan-window assumptions IND | E | Reliability propagation U |
| C021 | Statistical true/false grouping quantities E | Discrimination/correction IND | Exact disjointness U | Test/count regime assumptions U | E | U |
| C022 | U | U | U | U | U | Reliability is target; details U |

This matrix does not establish double counting or novelty. It names the cells that must be checked in full text.

## 13. Discovery-depth novelty-threat matrix

`CLM-002…006` remain scoped only to `PAPER-001…003`. The matrix below is an adversarial discovery map, not a novelty finding.

| Source | Mechanism partition | Partition after `W` | Mechanism-specific quantities | Non-overlap rule | Beyond-small-parameter validity | Joint inter-word dependence | Observation/estimation layer | Adaptive control / guarantee | Domain |
|---|---|---|---|---|---|---|---|---|---|
| C001 Clemente-2022 | Accumulation explicit; direct comparator U | U | U | U | U | U | U | Not indicated | ECC reliability under accumulated multiple events; exact device/radiation domain U |
| C002 Franco-2020 | False multiple events vs true events explicit | No post-`W` evidence | Cross-section uncertainty explicit | U | U | Spatial grouping only; joint codeword dependence U | Strong classification layer | Not indicated | SRAM/FPGA radiation tests |
| C003 Franco-2019 | Random coincident events versus MCU explicit | No post-`W` evidence | IND | U | U | U | Strong randomness/classification layer | Not indicated | SRAM single-event experiments |
| C004 Zebrev-2015 | Physical multiplicity partition IND | U | Multiplicity-resolved cross sections/rates IND | U | U | Likely reduced to multiplicity; U-PA | Measurement methodology IND | Not indicated | Heavy-ion irradiation |
| C005 Zebrev-v2 | Direct multiplicity and SEC-DED accumulation terms must be resolved | ECC conversion present; ordering relative to `W` U | `R_w` quantities explicit target | Eq. (15) disjointness U | `β << 1` exact target | U; likely reduced representation | U | Scrubbing efficiency, not adaptive control; guarantee U | Space SER with ECC; validation scope U |
| C006 Zebrev-RADECS | Same broad theme as C005; details U | U | U | U | U | U | U | Not indicated | Conference version; substantive relation U |
| C007 Maestro-2009 | Direct MBU versus accumulation explicit | U | IND | U | U | U | U | Correction method, not adaptive guarantee at discovery | Memory affected by MBU |
| C008 Moindjie-2017 | Separate event multiplicities/mechanisms; accumulation model limited | No post-`W` treatment | Multiplicity and neutron/alpha rates explicit | Independent processes stated; fit assumptions U | U | Marginal event multiplicity; inter-word joint law absent | Real-time measurement layer EXP | Not indicated | 65/40 nm bulk SRAM, altitude/underground |
| C009 Lee-2011 | Accumulated versus clustered explicit | U | U | U | U | Cluster representation U | U | Not indicated | Memory reliability model |
| C011 Ogden-2017 | Event topography retained; direct/accumulation split U | Interleaving/ECC scenarios explicit; formal `W` U | U | N/S | U | Core comparison: full topography versus reduction | U | Periodic scrubbing only; no adaptive guarantee indicated | Computer-memory model/domain U |
| C020 Gomi-2026 | Direct event versus pseudo accumulation explicit | ECC mapping absent | Event-wise measurement quantities IND | Grouping-window trade-off explicit; exact non-overlap U | Scan-time assumptions U | Physical topology retained within measurement limits | Strong imperfect-observation layer | Not indicated | Neutron-induced MCU, 22/55 nm SRAM |
| C021 Clemente-2015 | MCU versus SEU discrimination explicit | No post-`W` treatment | Statistical grouping quantities IND | U | U | Physical/spatial grouping only | Strong statistical classification layer | Not indicated | 130/90 nm SRAM, neutron tests |

The strongest novelty threats are C001, C005/C006, C007, C009, C011, C020 and C021. Decisive feature cells remain `UNKNOWN` until full-text comparison; no literature-level novelty statement is supportable from this mapping alone.

## 14. Scite sanity check and bounded citation expansion

### 14.1 Scite seed/identity check

Scite was used as a secondary identity and obvious-signal layer, not as a complete evidence audit.

| Seed/identity | Identity result | Returned citation/editorial signal | Interpretation |
|---|---|---|---|
| C001, DOI `10.1109/TNS.2022.3143652` | Exact DOI/title/year match | tally returned 0 contrasting classifications; no editorial notice returned | No obvious signal in returned record; **not evidence of absence** |
| C005, generic DOI `10.48550/arXiv.1704.07271` | Title match | OA record; Scite identity does not preserve `v2` in the DOI | arXiv exact-v2 page remains canonical for version control |
| C006, DOI `10.1109/RADECS.2017.8696217` | Exact DOI/title/year match | 0 contrasting classifications in returned tally; no editorial notice returned | Separate version identity retained |
| C008, DOI `10.1016/j.microrel.2017.07.045` | Exact DOI/title/year match | 0 contrasting classifications in returned tally; no editorial notice returned | Returned OA repository access; no citation audit inference |
| C011, DOI `10.1109/TR.2017.2765484` | Exact DOI/title/year match | 0 contrasting classifications in returned tally; no editorial notice returned | No obvious signal in returned record |
| C018, DOI `10.1109/TETC.2022.3147376` | Exact DOI/title/year match | 0 contrasting classifications in returned tally; no editorial notice returned | No obvious signal in returned record |
| C020, DOI `10.1109/TNS.2026.3675003` | Exact DOI/title/year match | New paper; tally contained no contrasting classification; no editorial notice returned | Low citation maturity; tally has no decision weight |

DOI-filtered Scite editorial searches (`has_retraction`, `has_correction`, `has_erratum`, `has_concern`) returned no matching notice for the checked seed set. Because index completeness and classifier coverage are not established, correction/retraction/contrasting status remains **“no obvious signal returned by this sanity check”**, not a definitive audit. Full supporting/contrasting adjudication belongs to Evidence Auditor.

### 14.2 ResearchRabbit status

`UNAVAILABLE — REQUIRED PASS NOT EXECUTED.` The available environment exposed neither an authenticated ResearchRabbit connector nor a working interactive browser path. Public web locator searches did not expose the needed backward/forward/similar graph. The report therefore does not claim ResearchRabbit coverage.

### 14.3 Manual bounded fallback (not ResearchRabbit)

| Parent anchor | Route | Records surfaced/cross-linked | New category? |
|---|---|---|---|
| C001 Clemente-2022 | publisher related/citation chain | C002, C003, C007, C009, C021 | No category beyond accumulation/classification already found; strengthens provenance threat cluster |
| C005 Zebrev-v2 | arXiv references/related-version links | C004, C006 and multiplicity-partition lineage | No new category; version relation remains unresolved |
| C008 Moindjie-2017 | publisher references/related records | C023 and event-SER versus bit-flip-SER terminology | No new model class |
| C011 Ogden-2017 | IEEE/publisher reference chain | C009, C010, C022 | No new category; strengthens topology/interleaving/reliability cluster |
| C020 Gomi-2026 | publisher reference chain | C002, C003, C012, C014, C015, C021 | No new category beyond imperfect event classification/topology |

These records were deduplicated by DOI and cross-linked to their parent anchors. This manual fallback is useful discovery provenance but does not satisfy the ResearchRabbit stopping condition.

### 14.4 Saturation test

| Batch | New accepted records | New model/definition/measurement category |
|---|---:|---|
| IEEE + targeted publisher/NASA batch | 22 accepted candidates before later Scite additions | Arrival-rate, multiplicity, topology, accumulation, mapping/interleaving, nonstationarity, and uncertainty categories established |
| Scite secondary batch | 3 new accepted candidates (C021–C023) | Added/strengthened explicit statistical discrimination and environment-to-rate terminology; therefore not a no-new-category batch |
| Manual citation fallback | 0 new unique records after dedup | None |

Only one consecutive batch produced no new category, and the prescribed ResearchRabbit batch is missing. **Saturation criterion: NOT MET.**

## 15. Terms discovered and query refinement

### 15.1 Useful terms

- `event SER` versus `total bit-flip SER`;
- `multi-Poisson process` (parallel processes by event multiplicity; not automatically compound Poisson);
- `event topography` / `event topology`;
- `pseudo MCU`, `false MCU/MBU`, `statistical anomaly`, `birthday statistics`;
- `quasi event-wise measurement`;
- `static bitmap` versus real-time/event-wise measurement;
- `distant MCU`;
- `interleaving distance`, `row depth`, `geometric factor`;
- `single-node` versus `multiple-node charge collection`;
- `physical multiplicity` versus `multiplicity within one ECC word`;
- `event accumulation problem`;
- `event rate` versus `upset/bit-flip rate`.

No new canonical project symbol is proposed here.

### 15.2 Exact named-gap refinement strings

Use only if the Orchestrator authorizes the access-only completion:

1. Complete the already prescribed OpenAlex F4–F9 strings without semantic broadening.
2. In the bounded ResearchRabbit pass, use C001, C005, C008, C011 and C018 as seeds; retain C020 as a targeted similar-work check.
3. If ResearchRabbit returns a sparse observation cluster, one targeted locator string is justified:  
   `SRAM AND ("pseudo MCU" OR "false MCU" OR "false MBU" OR "quasi event-wise")`.
4. If `W` remains absent after deep read, one targeted locator string is justified:  
   `SRAM AND ("event topography" OR "event topology") AND (codeword OR interleaving OR "physical-to-logical mapping")`.

These are named-gap refinements, not authorization for a second general cycle.

## 16. Gaps, conflicts and borderline decisions

### 16.1 Blocking or decision-relevant gaps

1. **Complete initial state:** no discovery source clearly specifies `μ_t0` over accumulated word errors, word exposure ages, and scrubber phase/scan position.
2. **Explicit `W`:** physical topology evidence is plentiful, but deterministic physical-cell-to-codeword mapping and the resulting joint codeword-impact mark are rarely explicit in discovery material.
3. **Repair semantics:** correction, writeback, reset and scrubbing are often model-specific or omitted; a single post-`E_cap` consequence cannot be assumed.
4. **Mechanism recombination:** direct same-particle, sequential accumulation and false test classification are all represented, but exact disjoint sample spaces versus additive approximations are unresolved.
5. **Nonstationarity class:** time variation is supported as a concern, but no direct discovery evidence selects NHPP, Cox or another nonstationary process.
6. **Uncertainty propagation:** classification/cross-section uncertainty is measured in several sources; propagation into `E_cap/F_A` is generally unknown.
7. **Validation transfer:** technologies, radiation particles, layouts and operating conditions differ; no cross-domain validity rule has been established.
8. **Computational feasibility:** several analytic/simulation models exist, but cost for repeated adaptive-scrubbing evaluation remains a PA/prototype question.
9. **Zebrev version relation:** exact v2 versus RADECS substantive differences remain unknown.

### 16.2 Terminology and model conflicts to adjudicate later

- `MCU` is a physical-cell/event grouping; `MBU` may be used for bits within one logical word or more loosely. Neither term can be mapped automatically to `E_cap`.
- A `multi-Poisson` superposition by multiplicity is not automatically a compound Poisson process, marked process, or proof of independent marks.
- Static bitmap grouping can merge independent events into a pseudo MCU, while short grouping windows can miss physically distant cells from one event.
- Event topography/interleaving studies suggest loss from marginalization, whereas rate-only models intentionally collapse that information; the appropriate reduction depends on the declared `W`, ECC and scrub semantics.
- Time-stationary fits in a controlled measurement window do not contradict mission-scale time variation; they occupy different validity domains.
- arXiv-v2 and RADECS titles/lengths differ; neither identity may silently replace the other.

## 17. C-RQ-05 disposition

**`GATE LIKELY TRIGGERED`**

Bounded rationale:

- C011 directly studies the reliability impact of event topography under ECC/interleaving/scrubbing scenarios.
- C010 connects interleaving distance to a soft-error failure model.
- C012, C014–C017 and C020 supply independent physical/measurement evidence that MCU topology and grouping depend on device/layout/test conditions.
- C001, C007, C009, C020 and C021 show that direct events, sequential accumulation and false grouping cannot be treated as one undifferentiated count without checking the sample-space and observation assumptions.

This evidence is enough to make safe exclusion of MCU/MBU/spatial structure doubtful at discovery depth. It is **not** a final finding about quantitative materiality, not a proof of any conservative bound, and not authorization for the Literature Scout to create a permanent RQ. The Orchestrator must decide whether to promote C-RQ-05.

## 18. HANDOFF TO ZOTERO

**Status:** structured request only. No Zotero import is claimed.

```yaml
handoff_type: HANDOFF TO ZOTERO
related_rq: RQ-002
target_collection: "DISSERTATION / RQ / RQ-002"
base_tags:
  - rq/RQ-002
  - topic/error-model
  - topic/arrival-process
  - topic/multiple-cell-upset
  - topic/event-topology
  - topic/physical-logical-mapping
  - topic/error-accumulation
  - topic/uncertainty
  - memory/SRAM
class_tags:
  CORE: class/CORE
  RELATED: class/RELATED
  BACKGROUND: class/BACKGROUND
required_checks:
  - deduplicate by DOI; for no-DOI records use normalized title + year + first author
  - keep related versions as separate items until full-text comparison
  - verify title, full author list, venue, year, volume/issue/pages and DOI
  - record discovery ID in Extra or a temporary note, not as permanent PAPER identity
  - attach an authorized PDF when available; otherwise preserve DOI/publisher/OA link
  - record peer-review and version status explicitly
  - do not infer successful import from this handoff
```

### 18.1 Priority records

| Priority | Records | Requested Zotero action |
|---|---|---|
| P0 exact-version control | C005 and C006 | Create/verify **separate** items; for C005 attach exact `https://arxiv.org/pdf/1704.07271v2`, record `arXiv:1704.07271v2`, v2 date `2017-10-15`, and do not substitute v1/generic PDF/RADECS; for C006 use DOI and cross-link as related version |
| P1 mandatory/decisive | C001–C004, C008, C011, C018, C020 | Verify metadata and PDF/link; add `class/CORE` except C018 (`class/RELATED`); route to named PA questions below |
| P2 additional CORE | C007, C009, C010, C012, C014, C016, C019, C021, C022 | Import only after dedup; attach accessible author copies where lawful; retain discovery class |
| P3 RELATED | C013, C015, C017, C023 | Import/cross-link for mechanism, topology or validity-domain evidence |
| P4 BACKGROUND | C024, C025 | Import only if useful for contextual comparison; do not treat as model-validation evidence |

### 18.2 Exact mandatory metadata notes

- C002: DOI `10.1109/TNS.2020.2977698`; OA author-copy link was located during Scite access resolution.
- C003: DOI `10.1109/TDMR.2018.2886358`; OA author-copy link was located.
- C005: authors Gennady I. Zebrev, Artur M. Galimov, Liza V. Mrozovskaya, Maxim S. Gorbunov, Konstantin A. Petrov; exact title uses **“Upset”** and **“with Error Correcting Codes”**.
- C006: same five-author identity; title uses **“Event”** and **“with Embedded Error Correcting Codes”**; DOI `10.1109/RADECS.2017.8696217`.
- C005/C006 relation note: `UNKNOWN — REQUIRES FULL-TEXT COMPARISON`.

## 19. HANDOFF TO PAPER ANALYST

**Scope:** five primary decision-enabling work units. Do not create Paper Cards for every candidate merely because it is CORE. Preserve discovery uncertainty and return feature-level extraction, equations, assumptions, validity domain and exact quotations/locations as required by the Paper Analyst protocol.

### PA-1 — RQ2-C005 exact Zebrev arXiv v2, with RQ2-C006 version comparison

**Required full text:** exact `arXiv:1704.07271v2`, not v1 and not the RADECS paper. Keep RQ2-C006 as a separate companion record.

**Mandatory equation/section targets:**

- Eqs. (2)–(11): MCU/event partitioning by multiplicity;
- Eqs. (13)–(14): transition from multiplicity-resolved event rates to ECC/system error rate;
- Section III.D, Eqs. (15)–(19): “Scrubbing efficiency for a simple SEC-DED procedure”.

**All 15 mandatory questions:**

1. What does the first term of Eq. (15) mean?
2. What does the second term of Eq. (15) mean?
3. Are they mutually exclusive sample spaces or an approximate additive construction?
4. Where are direct same-particle and sequential multiple-arrival mechanisms separated?
5. What are `R_w(n≥1)` and `R_w(n≥2)`?
6. How is physical MCU multiplicity converted into multiplicity within one ECC word?
7. Why does factor `1/2` appear?
8. Which interleaving / physical-to-word mapping assumption stands behind `1/2`?
9. Which `n≥3` events are omitted and why?
10. What is the exact meaning and validity domain of `β << 1`?
11. Does the source claim validity beyond `β << 1`?
12. Are separate experimental cross sections/rates available for direct and accumulation mechanisms?
13. Is partitioning performed before mapping, after mapping or only by physical multiplicity?
14. Is overlap/double counting possible?
15. Which parts are experimentally/on-orbit validated and which are an illustrative SEC-DED approximation?

**Version-comparison additions:** compare equation inventory, assumptions, validation data, omitted material and conclusions in C005 versus C006; return `VERIFIED DIFFERENCE`, `VERIFIED NO SUBSTANTIVE DIFFERENCE`, or preserve `UNKNOWN` for each feature. Do not make a whole-paper identity judgment from title similarity.

### PA-2 — RQ2-C001 Clemente et al. 2022

Extract:

1. Primitive event and stochastic arrival law; evidence for Poisson/independence/stationarity.
2. Exact definition of an “event by accumulation” and whether direct same-particle events are a separate sample space.
3. State variables, initial state/distribution, and any word-age/exposure-age representation.
4. Physical-to-codeword mapping/interleaving assumptions and whether a joint post-`W` mark is retained.
5. ECC capability and failure event used; do not equate it to DEC-001 `E_cap` without a feature map.
6. Correction, writeback, reset and scrub timing semantics.
7. Mechanism-specific rates/probabilities and recombination/non-overlap rule.
8. Small-parameter/asymptotic assumptions, uncertainty and validation domain.
9. Computational method/cost and inputs required to evaluate a windowed probability.
10. Feature-by-feature compatibility and mismatch with `E_cap(A;t0,T)` and `F_A(t0,T; μ_t0)`.

### PA-3 — RQ2-C008 Moindjie et al. 2017

Extract:

1. Whether “multi-Poisson” means independent HPPs indexed by event multiplicity, a superposition, a compound process, or another construction.
2. Primitive counted object: physical event, detected event, or bit flip; exact event SER versus total bit-flip SER definitions.
3. Goodness-of-fit/model-comparison evidence for Poisson and independence.
4. Fixed versus time-varying intensity; test-window length and stationarity domain.
5. Multiplicity distribution/parameters and whether spatial topology or parent provenance survives.
6. Separate neutron/alpha rates and the rule for combining mechanisms.
7. Real-time detection/writeback/reset semantics and observation limitations.
8. Parameter uncertainty, technology/environment domain and computational inputs reusable for an initial prototype.

### PA-4 — RQ2-C011 Ogden & Mascagni 2017

Extract:

1. Formal representation of full event topography and every compared reduction.
2. Exact mapping/interleaving representation and whether `W` is deterministic, statistical or implicit.
3. Which joint intra-word/inter-word dependencies and parent-event links are preserved or discarded.
4. Quantitative direction/magnitude of reliability changes only after checking full text, scenarios and uncertainty.
5. Arrival process, event-rate/bit-rate definitions and stationarity assumptions.
6. Initial memory state, ECC capability abstraction, periodic-scrub phase, correction/writeback/reset and word-age semantics.
7. Empirical versus simulated input data and domain of validity.
8. Computational complexity and whether a joint post-mapping mark is sufficient for its reliability calculation.

### PA-5 — RQ2-C020 Gomi et al. 2026

Extract:

1. Exact quasi-event-wise measurement procedure, scan period and grouping rule.
2. Formal definitions of true MCU, pseudo MCU from independent SEUs, and distant MCU missed by a short window.
3. How parent-event provenance is inferred and what remains unobservable.
4. Classification error model, uncertainty/confidence intervals and sensitivity to scan timing.
5. Spatial topology/multiplicity outputs and whether physical addresses can be mapped through an external `W`.
6. Separate cross sections/rates for direct and false/accumulated mechanisms, if available.
7. Simulation validation, neutron/technology domain and transfer limits.
8. How measurement uncertainty could propagate into an `E_cap/F_A` computation; preserve `UNKNOWN` if the paper stops at cross sections.

### Conditional secondary extraction, only if a named gap remains

- **C002 + C003 + C021:** compare statistical definitions of false multiple events, independence assumptions, spatial thresholds, uncertainty intervals and whether corrections propagate beyond cross-section estimation.
- **C018:** determine whether the rate predictor supplies a deterministic intensity path, a random latent process, or only point forecasts; extract timescale, uncertainty and data needed for a nonstationary arrival model. Do not move observability/control decisions out of RQ-004.
- **C009/C010/C022:** use only if C001/C011 fail to resolve accumulated/clustered-error state or mapping/interleaving adequacy.

## 20. Final recommendation and bounded post-mapping note

### 20.1 Recommended next action

Perform **one named, access-only completion**:

1. run OpenAlex F4–F9 exactly as prescribed;
2. run one ResearchRabbit backward/forward/closely-related pass for C001, C005, C008, C011 and C018, with C020 as a targeted similar-work check;
3. deduplicate against `RQ2-C001…C025` and record whether the batch adds a genuinely new model/definition/measurement category.

If that batch adds no new category, mark mapping complete and proceed to the bounded Paper Analyst queue. If it adds one new category, screen only that named category; do not restart a general RQ-002 cycle.

The Paper Analyst deep reads for PA-1…PA-5 can begin as soon as the Orchestrator accepts this report; they address named model-selection/prototype blockers rather than general reading volume.

### 20.2 Potentially decisive sources (five)

1. C001 — accumulation/ECC reliability state.
2. C005 — exact multiplicity-to-ECC/scrub equations.
3. C008 — empirically fitted multiplicity-indexed Poisson rates.
4. C011 — information loss from event-topography reduction and mapping/interleaving.
5. C020 — identifiability of true versus pseudo/distant MCU.

### 20.3 Remaining competing model alternatives

- stationary HPP or independent multiplicity-indexed Poisson streams in a declared validity regime;
- deterministic time-varying intensity / NHPP-like alternative motivated by radiation-environment variation;
- parent-event batch/mark representation retaining multiplicity and possibly joint post-`W` codeword impact;
- explicit imperfect-observation layer for event grouping, if operational/test data require it.

Cox, renewal, semi-Markov, PDMP, stochastic ordering and positive association remain unevidenced candidates in the executed routes, not rejected mathematical possibilities.

### 20.4 Specific gap blocking the first quantitative prototype

The immediate blocker is not a numerical reliability threshold. It is the absence of a checked combination of:

1. event primitive and arrival/intensity law;
2. minimum post-`W` joint mark versus justified reduction;
3. accumulated-error/initial state and scrub/reset/writeback semantics;
4. empirically identifiable rate/multiplicity parameters with classification uncertainty.

PA-1…PA-5 are designed to close those four items. Until then, a prototype skeleton can be designed, but choosing and parameterizing one error model would be premature.

## 21. Compliance statement

- eLibrary was not queried and remains `DEFERRED / UNKNOWN COVERAGE`.
- No `HYP`, `CLM`, `EVD`, `DEC`, `EXP`, `RES`, permanent `RQ`, or permanent `PAPER` ID was created.
- No answer to RQ-002, dissertation contribution, novelty claim or research gap is declared.
- No numerical requirement or threshold was assigned.
- `docs/research_spec.md` and all canonical repository files were not modified.
- No Zotero operation is claimed; the Zotero section is a structured handoff.
- No GitHub write was performed; this report is returned to the Research Orchestrator for acceptance.
