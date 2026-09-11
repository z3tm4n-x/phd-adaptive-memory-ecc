# LS-MEMORY-PROTECTION-TRADEOFF-01 — targeted literature map

## 1. Task control

| Field | Value |
|---|---|
| Task | `LS-MEMORY-PROTECTION-TRADEOFF-01` |
| Related RQs | `RQ-004`, `RQ-005`, `RQ-007` |
| Canonical base | `59603d231b923ee7426056cb62779a5ad16c8413` |
| Execution date | 2026-09-11 UTC |
| Role boundary | Literature Scout: discovery, identity control, and screening; no final architecture selection or claim-level adjudication |
| Last experiment boundary | Full delivery at `03e6c4a…` remains `REVISE`; only the cold-start limited statement in disposition `a88d6a2…`, based on SR `619492d…`, is treated as accepted context |

## 2. Search protocol fixed before execution

### 2.1 Research question

Which runtime-available memory-protection mechanisms have operational,
prototype, measured, synthesized, or otherwise experimentally credible evidence
that they can satisfy a stated reliability objective at lower system cost than
a strong static or simple-control alternative? Does any mechanism provide a
natural dissertation direction beyond merely reducing the number of complete
scrub passes?

The search does not presume that `T_scrub` remains the only action, that
RES-003/004 must be deployed, or that a positive example in DRAM, Flash, FPGA
configuration memory, or processor-core protection transfers to SRAM.

### 2.2 Concepts and synonyms

| Concept | Search terms and distinctions |
|---|---|
| Runtime scrub control | `adaptive scrubbing`, `dynamic scrubbing`, `patrol scrub`, `demand scrub`, `selective scrub`, `bank-aware scrub`, `region-aware scrub`, `scrub scheduling`, `memory scanning`, `memory washing`, `regeneration period` |
| Switched/selective redundancy | `adaptive ECC`, `dynamic ECC`, `reconfigurable ECC`, `selective ECC`, `variable-strength ECC`, `stronger code`, `mirroring`, `replication`, `lockstep`, `redundancy mode switching` |
| Resource reallocation | `page retirement`, `page offlining`, `memory sparing`, `dynamic bit steering`, `post-package repair`, `data migration`, `bank remapping`, `bad block retirement`, `spare rows` |
| Observation/control | `corrected error counter`, `syndrome counter`, `CE threshold`, `radiation monitor`, `space weather warning`, `fault prediction`, `local fallback`, `telemetry`, `scrub result` |
| Reliability/cost evidence | `uncorrectable error`, `DUE`, `SDC`, `failure probability`, `availability`, `bandwidth`, `latency`, `energy`, `power`, `area`, `overhead`, `performance`, `prototype`, `in-orbit`, `measurement` |
| Memory/error scope | `SRAM`, `DRAM`, `NAND flash`, `FPGA configuration memory`, `cache`; radiation upset versus retention/disturbance/permanent defect |
| Russian variants | `адаптивное восстановление памяти`, `изменение периода регенерации`, `фоновая проверка памяти`, `коррекция одиночных сбоев`, `динамическое резервирование`, `исключение неисправных блоков` |

### 2.3 Planned sources and roles

| Route | Planned role |
|---|---|
| IEEE Xplore / ACM DL / SpringerLink / ScienceDirect | Primary peer-reviewed discovery and identity control |
| NASA NTRS, ESA/agency repositories | Flight and instrument implementation evidence |
| Processor, memory-controller, FPGA and memory-vendor documentation | Actual runtime mechanisms and disclosed RAS semantics; not treated as independent scientific validation |
| Russian publisher/institutional sources and public academic indexes | Exact Russian-language primary-source discovery |
| Scite | Secondary identity/correction/retraction/obvious contrasting-signal sanity check only |
| ResearchRabbit | One bounded backward/forward/similar pass after seeds, only if authenticated browser access is available and it can change the architectural map |
| Public web / Crossref-like metadata | Exact-title/DOI/full-text locator and fallback; not a substitute for full-text evidence |

### 2.4 Inclusion criteria

A candidate is included when it provides at least one of the following:

1. a runtime-adjustable protection action with a defined observation or trigger;
2. a measured or reproducible relation between the action and reliability plus
   at least one system-cost component;
3. an implemented controller, memory subsystem, spacecraft computer, FPGA
   scrubber, or server RAS mechanism whose runtime semantics are documented;
4. a strong static/simple comparator that materially constrains whether an
   adaptive mechanism is worthwhile;
5. a distinct architecture class that could change the dissertation decision,
   with memory/error scope kept explicit.

For every substantial candidate, screening seeks: system and memory type; ECC;
error mechanism; runtime action; observation/latency/uncertainty; returned
resource; absolute and relative effect with baseline; evidence level; switching
and standing overhead; strongest simple/static alternative.

### 2.5 Exclusion criteria

- design-time-only ECC selection presented as runtime adaptation;
- generic fault tolerance without a memory-protection action;
- pure radiation/environment prediction without a linked protection decision;
- pure reliability modelling without an actuator or a strong baseline role;
- storage media or persistent-defect repair silently generalized to transient
  SRAM upsets;
- golden-copy recovery where no valid reference copy exists for the data;
- title/abstract-only claims of system benefit without a full-text handoff;
- secondary summaries when a primary paper/manual is identifiable;
- sources already closed in the Chen or PA-DOM mappings unless used as an
  explicit baseline rather than rediscovered.

### 2.6 Evidence classes

- `CORE` — can directly change the architecture/baseline decision;
- `RELATED` — useful adjacent mechanism or evidence in another memory/error
  domain that requires an explicit transfer argument;
- `BACKGROUND` — terminology or implementation context;
- `REJECT` — outside the bounded question or insufficiently controlled.

Evidence level is recorded separately as: flight/field operation, physical
prototype/measurement, RTL/FPGA synthesis or emulation, trace-driven/numerical
evaluation, analytical model, or vendor capability statement.

### 2.7 Strong comparators required by protocol

1. strong fixed ECC with interleaving;
2. PA-DOM-01-B simple corrected-error-count regulator;
3. Chen S3/S5 external/history-informed prediction plus local observation;
4. external warning/monitor with local safe fallback;
5. golden-copy recovery only for demonstrably reconstructible data.

### 2.8 Stopping rule

Stop when the three requested direction groups, the mandatory strong
comparators, and the important memory/error-domain alternatives are represented
by controlled candidates or explicit `NO RELEVANT EVIDENCE FOUND IN EXECUTED
ROUTES`; then perform at most one bounded seed expansion. Stop the expansion if
the next screened batch adds no new action class, evidence level, resource
object, or architecture-changing competitor. The result is a strategic map,
not a saturation or non-existence claim.

## 3. Executed search and access log

### 3.1 Route status

| Route | Status on 2026-09-11 | Use and limitation |
|---|---|---|
| IEEE Xplore | `PARTIAL` | Search and metadata/abstract pages were accessible; some full texts require subscription. Exact DOI/title checks were completed for the IEEE candidates. |
| ACM DL | `PARTIAL` | Metadata and DOI identity were accessible through publisher/DBLP/institutional mirrors; publisher PDFs were not uniformly open. |
| ScienceDirect | `PARTIAL` | DEMC metadata, abstract, highlights, and DOI were accessible; the article PDF requires organizational/subscription access. |
| SpringerLink | `PARTIAL` | Existing Chen identities were reused from the controlled mapping; no repeat broad search was run. |
| Institutional repositories / author pages | `ACCESSIBLE` | Used for Lu 2022 version-of-record, MAGE/ARCC/ECC-Parity author copies or metadata, and exact identity control. |
| Vendor documentation | `ACCESSIBLE` | Intel Xeon RAS and NVIDIA A100 memory-error-management documentation were accessible. These are capability/operation evidence, not independent scientific validation. |
| Patent records | `ACCESSIBLE` | Google Patents/Espacenet metadata and disclosure were accessible for the Intel ECS family. Patent disclosure is an architecture threat, not measured benefit. |
| NASA NTRS | `UNAVAILABLE` | Two bounded SRAM/EDAC/scrubbing queries and the NTRS search endpoint returned no usable result page. Coverage is unknown, not zero. |
| Gaisler documentation | `UNAVAILABLE` | The bounded GRLIB/EDAC manual endpoint failed to render. Coverage is unknown, not zero. |
| Russian public academic/web search | `ACCESSIBLE` | Four bounded queries were executed; no new primary source passed inclusion. This does not establish absence. |
| Scite | `UNAVAILABLE` | Secondary sanity-check call reached the account's monthly MCP limit (next reset shown as 2026-10-04). No correction/retraction conclusion was inferred. |
| ResearchRabbit | `PARTIAL` | Authenticated browser access succeeded and exact-title identity checks were used. A single CARE-seeded related-work pass failed at the service's `Reload/Reconnect` overlay after one reload; it was not silently reported as zero results. |
| eLibrary | `NOT USED` | Cloud Literature Scout has no direct eLibrary/Zotero Desktop access. Russian coverage was sought through public routes; bibliographic operations are handed off. |

### 3.2 Exact queries and screening counts

`Hits` is `UNKNOWN` where the public index did not expose a stable total. A
screened record means that its title plus metadata or abstract was inspected;
duplicate appearances inside a query group are counted once. Counts do not
pretend to be database-wide systematic-review counts.

| Log ID | Route and exact query strings | Filters | Hits | Screened | Included or retained |
|---|---|---|---:|---:|---:|
| Q1 | Public scholarly search: `"adaptive scrubbing" memory radiation SRAM`; `"self-adaptive" SEU mitigation SRAM scrubbing`; `"selective scrubbing" FPGA configuration memory radiation`; `"demand scrubbing" memory ECC` | 2000-present; English; primary source preferred | `UNKNOWN` | 18 | 6 |
| Q2 | IEEE/ACM/cross-publisher discovery: `"adaptive ECC" memory controller runtime error rate`; `"dynamic ECC" memory per block reliability energy`; `"reconfigurable ECC" memory runtime`; `"selective memory protection" ECC energy reliability` | 2000-present; runtime actuator required for `CORE` | `UNKNOWN` | 22 | 10 |
| Q3 | Cross-publisher discovery: `"adaptive reliability chipkill correct"`; `"MAGE adaptive granularity and ECC"`; `"CARE coordinated augmentation elastic resilience DRAM"`; `"configurable ECC" high bandwidth memory` | Exact title/family identity | `UNKNOWN` | 11 | 8 |
| Q4 | Vendor/primary documentation: `Intel adaptive double device data correction memory RAS`; `NVIDIA dynamic page offlining row remapping memory errors`; `adaptive internal memory error scrubbing error handling`; `patrol scrub priority addresses host hints memory` | Runtime semantics; vendor/manual/patent primary record | `UNKNOWN` | 10 | 3 |
| Q5 | Russian public search: `"адаптивная защита памяти" изменение кода коррекции ошибок ОЗУ`; `"динамическая коррекция ошибок" память адаптивный контроллер ECC`; `"адаптивное скраббирование памяти" радиация ОЗУ`; `"регулирование периода регенерации памяти" количество исправленных ошибок` | Russian; primary source; exact memory actuator | `UNKNOWN` | 14 | 0 new |
| Q6 | Agency/vendor bounded check: `site:ntrs.nasa.gov spacecraft SRAM memory scrubbing EDAC background scrubber`; `site:gaisler.com SRAM EDAC memory scrubber patrol scrub technical manual` | Exact domain endpoints only | `UNKNOWN` | 0 usable | 0; access blockers |
| Q7 | Exact identity control: `"A self-adaptive SEU mitigation system for FPGAs" Glein venue 2014`; `"A self-adaptive SEU mitigation scheme for embedded systems in extreme radiation environments"`; `"Memory Controller with Adaptive ECC for Reliable System Operation"`; `"DEMC: A Dynamic Multi-ECC Memory Controller with Per-Block Adaptation"` | Exact title/DOI/author control | `UNKNOWN` | 9 | 4 controlled; Glein venue unresolved |
| RR-ID | ResearchRabbit exact-title lookup of Lu 2022, CARE, MAGE, Virtualized ECC, LOT-ECC, Configurable-ECC, Stefani 2023, and DEMC 2026 | Exact titles; no relevance ranking by citation count | 8 exact queries | 8 | 8 identity matches; one corrupt Glein record rejected |
| RR-EXP | ResearchRabbit: seed `CARE: Coordinated Augmentation for Elastic Resilience on DRAM Errors in Data Centers` -> `Find related articles` | One anchor; one reload only | `UNKNOWN — SERVICE ERROR` | 0 usable | 0; access failure, not saturation evidence |
| SCITE-1 | Scite DOI/title sanity-check request for the decision-value seed set | Identity/correction/retraction only | `UNAVAILABLE` | 0 | 0; monthly limit |

### 3.3 Borderline and identity-control notes

- ResearchRabbit returned a corrupt exact-title record for Glein et al.: wrong
  author/year/venue and invalid-looking DOI `10.1109/.77`. It is recorded as
  `REJECT — CORRUPT SECONDARY RECORD`; the title/author family is retained with
  an identity blocker, not repaired by guesswork.
- FPGA configuration memory, DRAM retention, RowHammer, STT-MRAM disturbance,
  NAND wear/retention, and persistent DRAM-device defects are separate physical
  domains. They remain only where the control action or cost evidence changes
  the architecture decision.
- The 2023 Stefani conference paper and 2026 DEMC article appear to be a source
  family, but substantive extension and duplicate-result relations are
  `UNKNOWN — PAPER ANALYST`; similar authors/titles alone are insufficient.
- The Intel patent family is controlled through international publication
  `WO2022066178A1` (priority 2020-09-26; publication 2022-03-31) and national
  record `NL2029034A` (publication 2022-05-24). It is one patent family, not two
  independent validation sources.

## 4. Screened candidates

The `MPT-Cxx` labels are task-local discovery handles only. They are not
permanent project `PAPER-xxx` identifiers.

| ID | Exact identity / stable identifier | Domain and evidence | Class | Discovery route and bounded reason |
|---|---|---|---|---|
| MPT-C01 | Y. Lu, X. Zhai, S. Saha, S. Ehsan, K. D. McDonald-Maier, “A self-scrubbing scheme for embedded systems in radiation environments,” IOLTS 2020. DOI `10.1109/IOLTS50870.2020.9159718` | SRAM ECC self-scrubber; neutron experiment and hardware implementation | `CORE` baseline | Q1; a strong fixed concurrent scrub implementation, not an adaptive controller |
| MPT-C02 | Y. Lu, X. Zhai, S. Saha, S. Ehsan, K. D. McDonald-Maier, “A Self-Adaptive SEU Mitigation Scheme for Embedded Systems in Extreme Radiation Environments,” *IEEE Systems Journal* 16(1), 1436–1447, 2022. DOI `10.1109/JSYST.2022.3144019` | SRAM on Artix-7; fault injection plus neutron test; repository version of record available | `CORE` | Q1/Q7/RR-ID; closest direct SRAM/radiation implementation, but the runtime meaning of “self-adaptive” requires full text |
| MPT-C03 | R. Glein, B. Schmidt, F. Rittner, J. Teich, D. Ziener, “A Self-Adaptive SEU Mitigation System for FPGAs with an Internal Block RAM Radiation Particle Sensor,” 2014; venue/DOI `UNKNOWN` | FPGA logic redundancy selected from on-chip BRAM sensor; abstract-level case-study numbers | `CORE — IDENTITY BLOCKER` | Q1/Q7; unusually close sensor-to-protection-mode competitor; corrupt RR metadata rejected |
| MPT-C04 | L. Gantel, Q. Berthet, E. Amri, A. Karlov, A. Upegui, “Fault-Tolerant FPGA-Based Nanosatellite Balancing High-Performance and Safety for Cryptography Application,” *Electronics* 10(17):2148, 2021. DOI `10.3390/electronics10172148` | Zynq UltraScale+ MPSoC; runtime performance/safety modes, TMR/configuration scrubbing/DPR; fault injection | `CORE` | Q1/Q2; protection-mode switching beyond scrub rate, but FPGA configuration/logic is not external SRAM data |
| MPT-C05 | B. Schmidt, D. Ziener, J. Teich, G. Zöllner, “Optimizing Scrubbing by Netlist Analysis for FPGA Configuration Bit Classification and Floorplanning,” 2017. arXiv `1707.08134`; journal-version DOI `UNKNOWN` | FPGA configuration memory; design-time essential-bit selection/floorplanning; measured MTTR claim | `RELATED` | Q1; strong scope-reduction comparator, not runtime adaptation |
| MPT-C06 | R. Giordano et al., “Intermodular Configuration Scrubbing of On-detector FPGAs for the ARICH at Belle II,” 2020. arXiv `2010.16194`; peer-reviewed identity `UNKNOWN` | Peer-copy/majority restoration of identical FPGA configurations; injection and neutron tests | `RELATED` | Q1; valid golden-copy-like case only because configurations are replicated/reconstructible |
| MPT-C07 | Controlled Chen family: S3 (DFT 2023, DOI `10.1109/DFT59622.2023.10313560`), S4 (LATS 2024, DOI `10.1109/LATS62223.2024.10534594`), S5 (*JETTA* 2025, DOI `10.1007/s10836-025-06183-5`) | External/history input -> next-window prediction -> scrub/wash frequency | `CORE` comparator | Canonical reuse, not rediscovery; closest forecast-driven period controller, already bounded by `CONTROL-PRIOR-ART-01` |
| MPT-C08 | A. A. Krasnikov et al., controlled PA-DOM-01-B source, *Electronics. Series 3*, 2018, no. 1(169), pp. 68–76; stable identifier as in canonical PA-DOM report | Corrected count per completed regeneration cycle -> next period | `CORE` comparator | Canonical reuse; strongest simple count regulator |
| MPT-C09 | C. A. M. Marcon, F. Silva, M. Stefani, J. A. N. da Silveira, “Memory Controller with Adaptive ECC for Reliable System Operation,” SBCCI 2023. DOI `10.1109/SBCCI60457.2023.10261959` | General/server memory; per-block runtime error rate -> recode to stronger/weaker ECC; experimental evaluation | `CORE` | Q2/Q7/RR-ID; direct variable-strength ECC competitor, full text pending |
| MPT-C10 | M. Stefani, F. Silva, J. Silveira, G. Borba, L. Vargas, E. Moreno, C. Marcon, “DEMC: A Dynamic Multi-ECC Memory Controller with Per-Block Adaptation,” *Integration* 109, 102728, 2026. DOI `10.1016/j.vlsi.2026.102728` | DDR SDRAM; real-time local error rate -> Parity/Hamming/LPC per block; synthesis/evaluation | `CORE` | Q2/Q7/RR-ID; abstract reports up to 70% energy saving and 99.956% application success under its baseline/scenario; transfer to radiation SRAM is unverified |
| MPT-C11 | X. Jian, R. Kumar, “Adaptive Reliability Chipkill Correct (ARCC),” HPCA 2013, pp. 270–281. DOI `10.1109/HPCA.2013.6522325` | Server DRAM; initially weaker protection, page-by-page strength increase after faults; evaluation | `CORE` | Q2/Q3; reports 36% average memory-power reduction versus commercial SCCDCD with same storage overhead and “similar reliability”; exact model/trigger requires full text |
| MPT-C12 | J. Chen, X. Jiang, Y. Zhang, L.-Y. Liu, H. Xu, Q. Liu, “CARE: Coordinated Augmentation for Elastic Resilience on DRAM Errors in Data Centers,” HPCA 2021. DOI `10.1109/HPCA51647.2021.00052` | Data-center DRAM; dynamic error tracking and elastic protection; architecture evaluation | `CORE` | Q2/Q3/RR-ID; reports near-Chipkill reliability against SEC-DED with 58 KB controller state, no memory-capacity penalty, and negligible performance overhead at abstract level |
| MPT-C13 | S. Li, D. H. Yoon, K. Chen, J. Zhao, J. H. Ahn, J. B. Brockman, Y. Xie, N. P. Jouppi, “MAGE: Adaptive Granularity and ECC for Resilient and Power Efficient Memory Systems,” SC 2012. DOI `10.1109/SC.2012.73` | Main-memory channel; ECC/access granularity adapted to application behavior; simulation | `CORE` | Q2/Q3/RR-ID; reports over 28% EDP improvement over the best static granularity/ECC systems; error-risk adaptation versus workload adaptation must remain distinct |
| MPT-C14 | D.-H. Yoon, M. Erez, “Virtualized and Flexible ECC for Main Memory,” ASPLOS 2010. DOI `10.1145/1736020.1736064` | DRAM; ECC stored in memory namespace, flexible/two-tier protection; trace evaluation | `RELATED` | Q2/RR-ID; strong flexible architecture, but runtime decision semantics need full text |
| MPT-C15 | A. N. Udipi, N. Muralimanohar, R. Balasubramonian, A. Davis, N. P. Jouppi, “LOT-ECC: Localized and Tiered Reliability Mechanisms for Commodity Memory Systems,” ISCA 2012. DOI `10.1145/2366231.2337192` | Commodity DRAM; localized/tiered detection and correction; simulated controller/firmware | `RELATED` | Q2/RR-ID; reports up to 44.8% power and 46.9% latency reduction; primarily an architectural/static comparator |
| MPT-C16 | H.-M. Chen, S.-Y. Lee, T. Mudge, C.-J. Wu, C. Chakrabarti, “Configurable-ECC: Architecting a Flexible ECC Scheme to Support Different Sized Accesses in High Bandwidth Memory Systems,” *IEEE Transactions on Computers*, 2019. DOI `10.1109/TC.2018.2886884` | HBM/GPU; access-size-aware two-tier ECC; simulation/synthesis | `RELATED` | Q2/RR-ID; reports 17–21% HBM energy reduction, 20x lower FIT, 1.2% performance overhead versus fixed 64-byte ECC; not error-rate-driven adaptation |
| MPT-C17 | X. Jian, R. Kumar, “ECC Parity: A Technique for Efficient Memory Error Resilience for Multi-Channel Memory Systems,” SC 2014, pp. 1035–1046. DOI `10.1109/SC.2014.89` | Server DRAM; correction bits materialized for faulty regions, parity otherwise; evaluation | `RELATED` | Q2/Q3; strong selective-storage comparator; reports 54.4%/20.6% memory-energy reduction against commercial Chipkill/DIMM-kill baselines |
| MPT-C18 | J. Liu, B. Jaiyen, R. Veras, O. Mutlu, “RAIDR: Retention-Aware Intelligent DRAM Refresh,” ISCA 2012. DOI `10.1145/2366231.2337161` | DRAM retention; per-bin row refresh using Bloom filters; simulation | `RELATED` | Q1/Q2/RR-ID; reports 74.6% fewer refreshes, 16.1% DRAM-power reduction, 8.6% performance gain, and 1.25 KB controller state; physics is not radiation scrubbing |
| MPT-C19 | Intel, “New Reliability, Availability, and Serviceability (RAS) Features in the Intel Xeon Processor Family,” technical article 672700, 2017 | Deployed server DRAM ADDDC; threshold-triggered bank/rank lockstep/sparing | `RELATED` | Q4; actual runtime feature, but persistent/degrading device-fault domain and no controlled benchmark in the article |
| MPT-C20 | NVIDIA, “GPU Memory Error Management” — Dynamic Page Offlining, Row Remapping, and SRAM Uncorrectable Errors, A100/A800 documentation | Deployed GPU DRAM page exclusion/spare rows; SRAM UCE threshold only flags RMA | `RELATED` | Q4; actual mechanism and useful non-transferability contrast; permanent/degrading faults, not transient SRAM accumulation |
| MPT-C21 | R. Agarwal, O. Avelar Suarez, G. Porwal, T. Yigsaw, R. Z. Loop, S. Panda, K. E. Criss, J. G. Holm, K. Bains, “Adaptive internal memory error scrubbing and error handling,” patent family `WO2022066178A1` / `NL2029034A`, Intel, 2022 | DRAM/on-die ECS; rate, target address, host hint, offlined-row exclusion, weighted arbitration | `CORE` architecture threat | Q4; directly covers both scrub intensity and scope, but supplies patent disclosure rather than independent performance/reliability validation |
| MPT-C22 | S. Baeg, S. Wen, R. Wong, “SRAM Interleaving Distance Selection with a Soft Error Failure Model,” *IEEE Transactions on Nuclear Science*, 2009. DOI `10.1109/TNS.2009.2015312` | Radiation SRAM; strong fixed ECC/interleaving modelling and implementation trade-off | `CORE` comparator | Canonical `PAPER-002`; mandatory strong static comparator, not rediscovered |
| MPT-C23 | A. Malkowski, P. Raghavan, M. Kandemir, “Analyzing the Soft Error Resilience of Linear Solvers on Multicore Multiprocessors,” IPDPS 2010. DOI `10.1109/IPDPS.2010.5470411` | Processor caches; application-specific selective protection; simulation | `RELATED` | Q2; evidence that selective protection can return energy, but cache/workload assumptions do not transfer automatically to SRAM store integrity |

### 4.1 Rejected or deferred records needed to avoid future confusion

| Record/class | Disposition | Reason |
|---|---|---|
| ResearchRabbit Glein record (`Li`, 2013, “FCCM”, DOI `10.1109/.77`) | `REJECT — CORRUPT SECONDARY RECORD` | Conflicts with the controlled title/author family and lacks a valid DOI. |
| Hoque et al., TMR partitioning plus scrub-frequency optimization | `BACKGROUND` | Design-time optimization; no runtime actuator satisfying this task. |
| Adaptive ECC for NoC/OLS codes, STT-MRAM caches, NAND Flash, PCM | `RELATED` only where retained; otherwise `REJECT` | Useful mechanism analogies but different protected object and dominant error physics. |
| General radiation-hardened SRAM-cell designs | `REJECT` | Static circuit design without runtime protection control. |
| General inspection/maintenance/control literature | `REJECT` | Outside the bounded memory-protection question. |
| Russian public-search results | `NO NEW RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES` | Results were general ECC summaries, teaching material, or duplicates of the controlled PA-DOM chain; no new controlled primary source passed inclusion. |

## 5. Mechanism map and strategic screening

### 5.1 Compact mechanism map

| Mechanism class | Runtime action and observation | Resource plausibly returned | Reliability/cost evidence and strongest baseline | Evidence level | Domain-transfer judgment |
|---|---|---|---|---|---|
| Fixed concurrent self-scrub | Dedicated ECC read-correct-write loop operates beside functional access; no adaptive observation | CPU time and access latency relative to software/serial scrubbing | Lu 2020/2022 neutron and injection evidence; compare fixed strong ECC+interleaving and fixed full scrub | Prototype + radiation measurement | Direct SRAM/radiation evidence; whether C02 has a genuine runtime policy remains for PA |
| Period-only adaptation | Corrected counts or external/history prediction change scrub period; local fallback may cap risk | Background memory bandwidth, controller occupancy, energy | PA-DOM-01-B simple count controller; Chen family; accepted cold-start experiment only under exact disposition constraints | Algorithm/prototype/model; current system evidence incomplete | Direct project domain, but already-known competitor; does not by itself answer the broader action question |
| Priority/region-aware scrubbing | Error counts, host hints, access patterns, environment, or critical-bit classification alter scrub target order/scope | Avoided reads/writes to low-risk or irrelevant regions; shorter repair time | Intel ECS patent covers runtime rate and address weighting but has no independent benefit measurement; Schmidt reports design-time FPGA MTTR reduction | Patent disclosure; FPGA experiment | Strong architecture threat; no controlled radiation-SRAM evaluation with DEC-001-compatible reliability found |
| Protection-mode switching | Local radiation/fault level selects no/DMR/TMR or performance/safe mode | Replicated compute area/throughput/power when risk is low | Glein abstract-level 3x throughput and large PFH change; Gantel fault-injection prototype | FPGA prototype; proposed in-orbit concept | Natural beyond-period action, but protects FPGA configuration/logic, not arbitrary SRAM data |
| Per-block variable-strength ECC | Runtime local error rate/first fault triggers recoding to stronger ECC; clean blocks use weaker code | ECC energy, activated chips, code storage/capacity, latency | DEMC reports up to 70% energy; ARCC reports 36% memory power vs SCCDCD; CARE reports near-Chipkill vs SEC-DED at low overhead | Architecture simulation/synthesis; no radiation test | Strongest action-class competitor; transfer to external radiation SRAM and codeword mapping is unverified |
| Workload/access-granularity-aware ECC | Application behavior or access size selects ECC/granularity | Memory bandwidth, overfetch energy, access latency | MAGE >28% EDP vs best static combination; Configurable-ECC 17–21% energy vs fixed 64 B | Architecture simulation/synthesis | Shows system-cost leverage, but its observation optimizes workload behavior rather than radiation risk |
| Selective/tiered redundancy storage | Detection and correction separated; strong correction material stored/activated only for faulty regions | Capacity, DRAM activations, energy, latency | LOT-ECC and ECC Parity compare against strong static Chipkill-class baselines | Architecture simulation | Important static/conditional alternative; runtime trigger and transient-SRAM applicability need separate proof |
| Failing-resource exclusion/remapping | CE/UCE thresholds identify a failing page/device; page, row, bank, or rank is retired/remapped/locked-step | Continued service and reduced protection cost for healthy regions; usually consumes spares/capacity | Intel ADDDC and NVIDIA page offlining/row remapping are deployed features; no radiation-SRAM trade-off metric | Vendor operational capability | Relevant mainly to persistent/degrading DRAM faults. NVIDIA documentation explicitly treats SRAM UCE as an RMA signal, not an online repair path |
| Golden/peer-copy restoration | Majority/known bitstream reconstructs configuration | Avoids per-device golden memory or enables module repair | Giordano configuration-scrubbing tests | Prototype/beam test | Valid only for immutable/reconstructible or replicated content; not a generic SRAM-data action |
| Strong fixed ECC + interleaving | No runtime switch; mapping spreads correlated bits before decoding | No returned resource; consumes constant redundancy/access cost | Baeg et al. is the mandatory radiation-SRAM baseline; best adaptive claim must beat it under same event model | Model + implementation trade-off | Direct SRAM/radiation comparator and mandatory baseline |

### 5.2 Observation/action/cost boundary for decision-value candidates

| Candidate | Observation, latency, uncertainty | Runtime action | Absolute/relative effect and exact baseline at discovery depth | Switch/standing cost | Unknown for PA |
|---|---|---|---|---|---|
| C02 Lu 2022 | ECC/scrub state; timing and uncertainty not stated in metadata | ECC plus self-refresh/scrub | 32 kB Artix-7 RAM: zero observed flips vs 32 in unprotected RAM during 1.5 h at reported neutron flux | “Small/transparent/no added latency” at abstract level; exact area/bandwidth unknown | Is any protection parameter changed at runtime, or is “adaptive” architectural/self-running only? |
| C04 Gantel 2021 | Local fault and radiation-level estimates; delay/uncertainty unknown | Low-power/safe/high-performance configuration, TMR, scrubbing, DPR | Fault-injection evaluation; exact absolute reliability and cost baselines require full text | Reconfiguration time, state transfer, standing triplication metadata unknown | Which modes affect memory protection versus compute replication, and is reliability explicitly constrained? |
| C10 DEMC 2026 | Real-time local per-block error rate; estimator window/false classification unknown | Parity/Hamming/LPC selection and recoding | Up to 70% energy saving and 99.956% application success under multi-bitflip conditions, relative baseline details pending | Metadata/recoding storage, atomicity, write bandwidth, decoder multiplexing unknown | Exact fault model, best static comparator, switching policy, failure metric, and common-mode/mapping assumptions |
| C11 ARCC 2013 | First/accumulated faults by page; classification latency/uncertainty pending | Raise Chipkill strength page by page | 36% average memory-power reduction vs commercial SCCDCD, same storage overhead, similar reliability as claimed | Fault-map and activation/switch costs pending | Reliability model and whether faults are transient, intermittent, or permanent; trigger and recovery semantics |
| C12 CARE 2021 | Dynamic DRAM error tracking; 58 KB controller structure at abstract level | Elastic augmentation/protection of risky locations | Near-Chipkill vs SEC-DED, no memory-capacity penalty, negligible performance overhead at abstract level | 58 KB standing state; update/recovery costs pending | Error taxonomy, false positives, field-trace provenance, strongest static comparator, and uncertainty treatment |
| C21 Intel ECS patent | Error-rate change/prediction, sensors, host hints, access patterns, load, temperature; no characterized uncertainty | Rate change; target-address weighting; skip offlined rows | No controlled performance/reliability experiment | Registers, counters, arbitration described; implementation cost unmeasured | Whether any product implements the complete chain and its measured trade-off |

### 5.3 Strategic interpretation at discovery depth

The map supports a bounded **candidate direction**, not an architecture
selection: an action vector containing at least protection **scope/region** and
protection **strength/mode**, with a local safe fallback, deserves comparison
against period-only control. Per-block ECC switching (ARCC/DEMC/CARE) and
radiation-level-driven mode switching (Glein/Gantel) are the strongest evidence
that such an action space can return power, bandwidth, capacity, or throughput.

This is not yet direct evidence for the dissertation's external radiation SRAM.
The decisive missing bridge is whether the target SRAM/controller can maintain
per-region state and atomically recode or relocate data under the project error
model without erasing the apparent savings. A simpler region-priority scrubber
may be implementable sooner, but the executed routes produced patent/design-time
support rather than an independent radiation-SRAM system experiment.

### 5.4 Most dangerous competitors

1. **ARCC and DEMC/Stefani**: they already instantiate the chain local error
   evidence -> per-region ECC-strength change -> quantified energy/power effect.
2. **CARE**: it claims near-Chipkill protection from dynamic error tracking at
   low capacity/performance cost and therefore challenges any broad claim that
   adaptive memory protection itself is new.
3. **Glein/Gantel**: they place a radiation/fault sensor in the control loop and
   switch protection/performance modes, a close threat to an integrated
   evidence-to-action framing beyond scrub period.
4. **Intel ECS patent family**: it explicitly combines adaptive scrub rate,
   address priority, host hints, environmental conditions, and offlined-row
   handling. It is not experimental proof, but it narrows the architecture
   space available for a novelty claim.
5. **Chen plus PA-DOM-01-B** remain the strongest known period-only and simple
   control comparators in the canonical project domain.

### 5.5 Gaps and conflicts

- No executed source demonstrated runtime region- or bank-priority scrubbing on
  radiation-exposed external SRAM with an absolute DEC-001-compatible failure
  measure and a complete system-cost vector.
- No executed source demonstrated variable-strength ECC on external radiation
  SRAM while exposing physical-to-logical mapping, MCU/common-mode handling,
  recoding atomicity, estimator uncertainty, and switching overhead together.
- No independent flight/field deployment of adaptive SRAM protection was
  controlled; the evidence is dominated by prototypes, simulation/synthesis,
  patents, and server/GPU vendor mechanisms.
- The reported percentage improvements use incompatible baselines: unprotected
  memory, SEC-DED, SCCDCD, best static ECC/granularity, or vendor mechanisms.
  They must not be ranked until Paper Analyst normalizes the denominators.
- External warning plus local fallback has no new independent end-to-end source
  beyond the already controlled Chen family and the bounded cold-start result.
- Golden-copy evidence was found only where the content is genuinely
  reconstructible (FPGA configuration/identical modules), not for arbitrary
  mutable SRAM data.
- Russian public routes added no new primary source; NTRS/Gaisler, Scite, and
  the ResearchRabbit related pass have explicit access blockers. These are
  coverage gaps, not evidence of non-existence.

## 6. Bounded full-text queue — HANDOFF TO PAPER ANALYST

The five work units below are ordered by decision value, not citation count.
Each handoff prohibits inferring system benefit from metadata/abstract alone.

### PA-MPT-01 — direct SRAM/radiation implementation

- **Task-local label / RQs / gap:** `MPT-C02`; RQ-004/RQ-005/RQ-007; determine
  whether the closest direct SRAM/radiation source exposes a real adaptive
  action or only autonomous fixed self-scrubbing.
- **Identity:** Yufan Lu, Xiaojun Zhai, Sangeet Saha, Shoaib Ehsan, Klaus D.
  McDonald-Maier, “A Self-Adaptive SEU Mitigation Scheme for Embedded Systems
  in Extreme Radiation Environments,” *IEEE Systems Journal* 16(1), 1436–1447
  (2022), DOI `10.1109/JSYST.2022.3144019`.
- **Screening class / reason:** `CORE`; direct SRAM, ECC, fault injection, and
  neutron measurement.
- **Full text:** `AVAILABLE`; Southampton ePrints 473503 supplies the
  version-of-record PDF under a CC license.
- **Extraction questions:** What state is observed? Which parameter changes at
  runtime? What is the control cadence? What ECC, codeword, scrub/writeback,
  and functional-access arbitration semantics are implemented? What exact area,
  memory, latency, bandwidth, and energy costs were measured? What are the
  absolute exposure, sample size, confidence limits, and strongest fixed ECC+
  interleaving/self-scrub baseline? Are persistent faults handled separately?
- **Limits / prohibited inference:** the zero-versus-32 observation is not a
  bound on DEC-001 `F_A`; do not infer adaptive policy from the title.

### PA-MPT-02 — per-block multi-ECC source family

- **Task-local labels / RQs / gap:** `MPT-C09`, `MPT-C10`; RQ-004/RQ-005/RQ-007;
  test whether per-block error evidence can safely drive code-strength changes
  and return a measured resource.
- **Identities:** (a) César A. M. Marcon, Felipe Silva, Marco Stefani, Jarbas
  Aryel Nunes da Silveira, “Memory Controller with Adaptive ECC for Reliable
  System Operation,” SBCCI 2023, DOI
  `10.1109/SBCCI60457.2023.10261959`; (b) Marco Stefani, Felipe Silva, Jarbas
  Silveira, Giovanna Borba, Luthero Vargas, Edson Moreno, César Marcon, “DEMC:
  A Dynamic Multi-ECC Memory Controller with Per-Block Adaptation,”
  *Integration* 109, 102728 (2026), DOI `10.1016/j.vlsi.2026.102728`.
- **Screening class / reason:** `CORE`; explicit runtime per-block selection by
  local error rate, with energy/reliability evaluation.
- **Full text:** 2023 IEEE text `PENDING` (subscription or author copy); 2026
  ScienceDirect metadata/abstract accessible, PDF `PENDING` organizational
  access. A PUCRS 2023 thesis may be a related version but must not substitute
  without version comparison.
- **Extraction questions:** Is the 2026 paper an extension of the 2023 paper,
  and which results are new? Define block, metadata, estimator, window, trigger,
  hysteresis, recoding transaction, crash/radiation atomicity, and parity/
  Hamming/LPC code parameters. Which error mechanisms and spatial dependencies
  are injected? What is the exact 70% baseline and energy accounting? Define
  “99.956% application success,” sample count, uncertainty, and strongest
  static ECC. Quantify storage, decoder, latency, recoding bandwidth, and
  ongoing monitoring cost. Can the mechanism map to external SRAM and DEC-001
  without assuming independent single-bit errors?
- **Limits / prohibited inference:** do not transfer DDR results or aggregate
  “success” to radiation SRAM reliability; do not merge the source versions
  without checked evidence.

### PA-MPT-03 — radiation-informed protection-mode switching

- **Task-local label / RQs / gap:** `MPT-C04`; RQ-004/RQ-005/RQ-007; determine
  whether a measured runtime action beyond scrubbing rate trades performance or
  power against a stated safety objective.
- **Identity:** Laurent Gantel, Quentin Berthet, Emna Amri, Alexandre Karlov,
  Andres Upegui, “Fault-Tolerant FPGA-Based Nanosatellite Balancing
  High-Performance and Safety for Cryptography Application,” *Electronics*
  10(17):2148 (2021), DOI `10.3390/electronics10172148`.
- **Screening class / reason:** `CORE`; open full text, runtime modes, TMR,
  configuration scrubbing/DPR, and fault-injection evidence.
- **Full text:** `AVAILABLE` from the MDPI publisher page/PDF.
- **Extraction questions:** List modes and exact runtime transitions; separate
  memory, configuration, and processor/core protection. What observes faults
  or radiation, at what delay and uncertainty? What reliability objective and
  metric governs mode choice? Quantify throughput, latency, power, area,
  reconfiguration time, state recovery, and steady overhead versus static TMR,
  static unreplicated, and simple threshold policies. What was physically
  measured versus injected/modelled? Which parts, if any, transfer to SRAM data?
- **Limits / prohibited inference:** do not call a nanosatellite application a
  flight demonstration unless the full text establishes operation in orbit;
  do not equate configuration scrubbing with SRAM-data scrubbing.

### PA-MPT-04 — adaptive Chipkill comparator

- **Task-local label / RQs / gap:** `MPT-C11`; RQ-004/RQ-005/RQ-007; control the
  strongest early page-level dynamic-strength comparator and its true baseline.
- **Identity:** Xun Jian, Rakesh Kumar, “Adaptive Reliability Chipkill Correct
  (ARCC),” 19th IEEE HPCA, pp. 270–281 (2013), DOI
  `10.1109/HPCA.2013.6522325`.
- **Screening class / reason:** `CORE`; page-by-page increase of ECC strength
  and quantified memory-power effect against commercial SCCDCD.
- **Full text:** `AVAILABLE/PENDING INGEST`; an author-copy link is exposed on
  the University of Illinois publication page; publisher record is controlled.
- **Extraction questions:** What event causes a page to upgrade, and can it
  downgrade? What error taxonomy, field data, lifetime, and reliability model
  support “similar reliability”? Is the 36% result average/peak and against
  which exact SCCDCD organization? Quantify map/storage, access activation,
  switching, migration, latency, and capacity costs. Test whether the policy is
  principally responding to permanent/intermittent device faults rather than
  transient radiation accumulation. Compare to the strongest static scheme.
- **Limits / prohibited inference:** do not treat Chipkill field reliability or
  page independence as applicable to SRAM without a mapping/error argument.

### PA-MPT-05 — elastic data-center protection

- **Task-local label / RQs / gap:** `MPT-C12`; RQ-004/RQ-005/RQ-007; determine
  whether dynamic location evidence plus elastic augmentation dominates a
  simple static/controller baseline after complete overhead accounting.
- **Identity:** Jian Chen, Xiaowei Jiang, Ying Zhang, Li-Yin Liu, Huifeng Xu,
  Qiang Liu, “CARE: Coordinated Augmentation for Elastic Resilience on DRAM
  Errors in Data Centers,” HPCA 2021, DOI
  `10.1109/HPCA51647.2021.00052`.
- **Screening class / reason:** `CORE`; near-Chipkill-versus-SEC-DED claim,
  dynamic error tracking, and explicit controller-state/capacity claims.
- **Full text:** `PENDING`; IEEE metadata is controlled, subscription or an
  author/institutional copy is required.
- **Extraction questions:** Define the protected unit, tracked error types,
  observation source/window, false-positive/false-negative treatment, and exact
  elastic action. What field traces or injected distributions are used? Define
  “near-Chipkill reliability,” the 58 KB structure, no-capacity-penalty claim,
  and negligible-overhead baseline. Quantify latency, bandwidth, energy,
  metadata protection, recovery, and update cost. Test transfer to radiation
  SRAM, physical/logical mapping, MCU, and DEC-001 event semantics.
- **Limits / prohibited inference:** no abstract-level equivalence between its
  reliability metric and `F_A`; do not assume data-center error composition is
  radiation dominated.

### Identity refinement not yet PA-ready

`MPT-C03` (Glein et al.) warrants one future exact-identity/access task because
its abstract indicates an unusually close local-radiation-sensor -> DMR/TMR
runtime chain. It is **not** sent for scientific analysis until venue, stable
identifier, and a controlled full text replace the corrupt secondary record.

## 7. HANDOFF TO ZOTERO

**Operation status:** requested only; this report does not claim that Zotero
Desktop import has occurred.

- **Target collection:** `DISSERTATION / RQ / RQ-007`, with a saved-search or
  task note for `LS-MEMORY-PROTECTION-TRADEOFF-01`; cross-tag RQ-004 and RQ-005.
- **Common tags:** `rq/RQ-004`, `rq/RQ-005`, `rq/RQ-007`,
  `task/LS-MEMORY-PROTECTION-TRADEOFF-01`, `topic/adaptive-memory-protection`.
- **Mechanism/domain tags as applicable:** `action/scrub-rate`,
  `action/scrub-scope`, `action/ecc-strength`, `action/replication-mode`,
  `action/reallocation`, `memory/SRAM`, `memory/DRAM`, `memory/FPGA-config`,
  `error/radiation-transient`, `error/retention`, `error/persistent-defect`, and
  `class/CORE` or `class/RELATED`.
- **Priority ingest:** MPT-C02, C04, C09, C10, C11, C12, C13, C21; add C01,
  C14–C20 only if not already present or when Paper Analyst accepts a named
  comparison question. Do not duplicate controlled Chen/PAPER/PA-DOM records.
- **Identity/metadata checks:** resolve each DOI; preserve full author order,
  conference/journal, pages/article number, year, and version. Cross-link but do
  not merge C09/C10 until full-text comparison. Store the Intel disclosure as
  one patent family with preferred international identity `WO2022066178A1` and
  national-family links, not as independent scientific papers.
- **PDF expectation:** attach the Southampton version-of-record for C02 and the
  MDPI full text for C04; seek author/publisher copies for C09/C10/C11/C12/C13.
  Record access blockers rather than attaching a secondary summary. PDFs remain
  in Zotero and must not be committed to GitHub.
- **Duplicate policy:** match DOI first, then normalized title plus author/year;
  never accept the corrupt ResearchRabbit Glein metadata. C03 remains deferred
  until exact venue/identifier/full text are controlled.
- **Attachment notes:** label preprint, author accepted manuscript,
  version-of-record, vendor documentation, and patent disclosure distinctly.

## 8. Stopping disposition and Orchestrator handoff

### 8.1 Coverage and stopping test

| Required direction/comparator | Coverage disposition |
|---|---|
| Adaptive/patrol/demand scrub intensity | Covered by Chen/PA-DOM baseline, Lu implementation baseline, and Intel ECS disclosure; independent radiation-SRAM system-cost evidence beyond period reduction remains a gap |
| Bank/region priority and functional-access interaction | Architecture covered by Intel ECS patent and design-time FPGA critical-frame evidence; `NO RELEVANT INDEPENDENT RADIATION-SRAM EXPERIMENT FOUND IN EXECUTED ROUTES` |
| Runtime switchable/selective ECC | Covered by Stefani/DEMC, ARCC, CARE, MAGE; all controlled quantitative sources are DRAM/main-memory architecture studies |
| Runtime mirroring/replication | Covered by Glein/Gantel in FPGA logic/configuration domain; Glein identity remains blocked |
| Resource migration/spares/exclusion | Covered by Intel ADDDC and NVIDIA offlining/remapping as deployed DRAM features; different fault physics retained explicitly |
| Copy restoration | Covered only for reconstructible FPGA configurations/replicated modules; no general mutable-SRAM golden-copy mechanism admitted |
| Strong static ECC plus interleaving | Covered by canonical Baeg et al. and fixed Lu self-scrub baseline |
| Simple count regulator | Covered by canonical PA-DOM-01-B |
| External monitor/warning plus local fallback | Chen/current experiment plus Glein local-sensor analogy; `NO NEW INDEPENDENT END-TO-END VALIDATION FOUND` |

The general mapping stop condition is met: the requested action classes,
strong comparators, distinct memory/error domains, and architecture-changing
competitors are represented. The bounded ResearchRabbit expansion did not
yield a usable batch because of a service error, so it cannot support a
saturation claim. Nevertheless, further broad searching is unlikely to change
the present architectural fork before the five full-text questions above are
answered. Recommendation: **STOP GENERAL SEARCH AND HAND OFF TO PAPER ANALYST**.
Permit only the separately named Glein identity-resolution task or a PA-raised
single-gap refinement; do not begin another broad cycle.

### 8.2 Orchestrator decision note

- **Most supported candidates for further consideration:** per-block
  error-evidence-driven ECC strength (ARCC/DEMC/CARE), radiation/fault-driven
  protection-mode switching (Gantel; Glein after identity control), and a
  lower-complexity region-priority scrub action as an implementation candidate
  whose evidence gap is explicit.
- **Natural direction suggested, not selected:** compare a bounded action vector
  `{scrub scope/priority, protection strength/mode, local fallback}` against
  fixed strong ECC+interleaving, the PA-DOM count regulator, and the Chen-style
  warning/prediction controller. This is meaningfully broader than reducing the
  number of full scrub passes.
- **Specific gap blocking a first quantitative prototype:** the target external
  SRAM/controller's ability to store protected per-region metadata and perform
  atomic recoding or reallocation, plus a verified mapping from mixed protection
  modes to DEC-001 `E_cap`/`F_A`, is unknown. Until that is resolved, the apparent
  DRAM energy gains cannot be priced against SRAM bandwidth, capacity, latency,
  controller area, and switching risk.
- **No project decision created:** this report does not choose an architecture,
  revive RES-003/004, create a permanent source/claim/result ID, assign a
  numerical reliability threshold, or assert novelty/non-novelty.

### 8.3 Repository disposition

This report is the only intended task change. It must be reviewed by the
Research Orchestrator before any merge or permanent literature registration.
