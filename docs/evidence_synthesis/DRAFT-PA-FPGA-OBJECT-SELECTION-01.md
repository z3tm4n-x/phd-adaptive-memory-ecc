# PA-FPGA-OBJECT-SELECTION-01 — адресный разбор FPGA configuration-memory candidates

Версия отчёта: 1.0, 2026-09-11. Статус: DRAFT; передача Research Orchestrator, не научное принятие. Роль: Paper Analyst. Связанные вопросы: RQ-001, RQ-004, RQ-005, RQ-007. Permanent `PAPER`, `CLM`, `EVD` или `RES` identifiers не назначаются.

## 1. Решаемый вопрос и итог

Задача — установить по двум полным текстам, показана ли существенная польза адаптивной защиты конфигурационной SRAM FPGA и относится ли она к:

- **случаю А:** управление проверкой/восстановлением конфигурации при неизменном резервировании вычислений;
- **случаю Б:** совместное использование постоянного configuration scrubbing и runtime-переключения вычислительного резервирования.

**INFERENCE — выбранный исход: 2. Основание относится только к более широкой системе переключения защиты.** Оба источника оставляют периодическую проверку/восстановление конфигурации постоянной или заданной средствами SEM и меняют число/назначение вычислительных копий. Glein даёт расчётный пример существенного обмена: три параллельных QPSK-канала при слабой радиации против TMR одного приоритетного канала при высокой. Gantel экспериментально показывает пользу постоянного scrubber, но отдельно не проверяет adaptive High-Performance↔Safe run; добавление TMR к scrubber в его campaign меняет заявленный multiplier с ×4 до ×4.4 относительно Basic. Ни одна работа не устанавливает, что runtime-изменение частоты configuration scrubbing при фиксированном резервировании даёт системный выигрыш относительно сильного постоянного SEM/scrub и простого управления.

**INFERENCE — остающийся проверяемый вопрос для нашей работы:** при фиксированной вычислительной избыточности существует ли на конкретной FPGA управляемый параметр configuration checking/restoration, изменение которого по причинно доступному observation действительно уменьшает стоимость полезной работы относительно сильнейшего допустимого постоянного SEM/scrub при одном и том же определении системного отказа и требовании? Этот вопрос сформулирован как decision gap, а не как литературная новизна. Если постоянный SEM уже укладывается в резерв интерфейса и его энергозатраты малы, простой постоянный режим может дать тот же практический эффект без адаптивного закона.

**INFERENCE — для случая Б обязательный простой comparator уже задан самими источниками:** пороговое переключение по счётчику ошибок. Более сложный predictor/controller нельзя обосновать названием `self-adaptive`; он должен превзойти причинный hysteresis threshold с учётом задержки наблюдения, реконфигурации и потери состояния.

## 2. Управление задачей и provenance

### 2.1. Проектные входы

- SOURCE — instruction base: `59603d231b923ee7426056cb62779a5ad16c8413`; прочитаны `docs/agents/00_GLOBAL_OPERATING_RULES.md`, `03_PAPER_ANALYST.md`, `HANDOFF_CONTRACTS.md`.
- SOURCE — LS input: `LS-MEMORY-PROTECTION-TRADEOFF-01`, commit `d0c3555a746b9e8db9d17b2a40fea8cfbacd849b`, blob `24a5eb9de4c018770d545cf121b1edda1056e468`. Использован только как discovery/identity context; abstract-level классификации повторно проверены по PDF.
- SOURCE — PA input: `DRAFT-PA-MEMORY-PROTECTION-SELECTION-01.md`, commit `71fad2de3eee10cbc02adfb7313155fbbcc14663`, blob `92511fcff6601670da1b35b4ec99b05d04c97365`. Повторный разбор Lu/ARCC/DFMC не выполнялся.
- SOURCE — новая сравнительная записка LS описана в handoff как пользовательская chat-delivery без commit SHA. **UNKNOWN — CONTENT NOT PRESENT IN CONTROLLED FILE SET:** отдельный текст/файл записки в текущем сообщении и приложениях отсутствует. Поэтому её происхождение сохранено как `user-transmitted chat input, non-canonical`, но научные утверждения из неё не извлекались и ей не приписывались.
- SOURCE — operational summaries о прежнем SRAM experiment не использованы как execution authorization. Расчёты, experiment, controller design и общий literature search не выполнялись.

### 2.2. Фактически прочитанные PDF

| Candidate | Exact identity from full text | Analyzed copy |
|---|---|---|
| MPT-C03 | **Robért Glein, Bernhard Schmidt, Florian Rittner, Jürgen Teich, Daniel Ziener**, “A Self-Adaptive SEU Mitigation System for FPGAs with an Internal Block RAM Radiation Particle Sensor,” *2014 IEEE 22nd Annual International Symposium on Field-Programmable Custom Computing Machines (FCCM)*, pp.251–258. DOI `10.1109/FCCM.2014.79`, visibly printed on p.251. The byline renders the first name as `Robért`; this is preserved as full-text provenance rather than silently normalized. | Supplied `A Self-Adaptive SEU Mitigation System for FPGAs.pdf`; 8 pages; 436,310 bytes; SHA-256 `b4edeeacf70896feb535e0bbef181e5c6c44049c9b750297bacbd524f04db25b`. IEEE-download footer: 2025-03-12 06:13:54 UTC. Full text read; equations/tables/figures below visually checked. The earlier LS identity blocker is resolved for title, venue, pages, author order and DOI. |
| MPT-C04 | **Laurent Gantel, Quentin Berthet, Emna Amri, Alexandre Karlov, Andres Upegui**, “Fault-Tolerant FPGA-Based Nanosatellite Balancing High-Performance and Safety for Cryptography Application,” *Electronics* 2021, 10(17), 2148. DOI `10.3390/electronics10172148`; received 13 Jul, accepted 27 Aug, published 3 Sep 2021. | Supplied publisher PDF `electronics-10-02148.pdf`; 12 pages; 658,301 bytes; SHA-256 `3045b64b8504d9bce368aa16c28fc3946451d0171dc7829b42e4dd074fba8343`. CC BY publisher layout. Full text read; figures/tables visually checked. |

Страницы Glein далее — печатные pp.251–258, совпадающие с PDF p.1–8 со сдвигом 250. Для Gantel используются printed/PDF pages 1–12.

## 3. MPT-C03 — Glein et al. 2014

### 3.1. Что наблюдается, что защищается, что управляется

| Объект | SOURCE — роль в работе | INFERENCE / UNKNOWN — граница |
|---|---|---|
| FPGA configuration SRAM | Внешний для показанной схемы blind configuration-memory scrubber периодически исправляет upsets через ICAP, предотвращая накопление; Fig.2/§II, p.252. В case study принят `t_s=60 s`; §VI/Table III, p.257. | **INFERENCE:** protection action configuration scrubbing не адаптируется. Это постоянный upstream mechanism, от которого зависит расчёт TMR reliability. UNKNOWN — scan order, SEM error classes, scrub bandwidth/arbitration и фактическое время correction. |
| BRAM sensor | Один или несколько BRAM Fault Detectors непрерывно читают BRAM; встроенный `(72,64)` Hamming исправляет single-bit output, различает `SBITERR/DBITERR`, scrubber переписывает повреждённое word. Fault Memory хранит counters, address, data word, ECC value; §§II,V.A/Fig.5, pp.252,255–256. BRAM может содержать deterministic pattern (standalone) или user data (integrated). | **INFERENCE:** BRAM одновременно наблюдается и локально защищается; это не protected application configuration. В integrated mode пользователь обязан обеспечить полный address sweep, поэтому observable зависит от user accesses. Фраза о sensor без дополнительного hardware означает отсутствие внешнего detector, но не нулевой FPGA overhead: реализация включает BFDs, Fault Memory, bus и MicroBlaze FMU. |
| Application modules | Partial region содержит 3 QPSK channels. Runtime action `l=0/1/2` assigns no redundancy/DMR/TMR для channel 1, inserts error detector or voter and removes other independent channels; §V.D–VI/Fig.7, p.257. | **INFERENCE:** адаптивно меняется вычислительное резервирование и состав полезной обработки, не scrub interval. DMR лишь detects output disagreement and, по автору, не improves PFH. |
| FMU/RCU/controller | MicroBlaze FMU polls Fault Memories, computes rates/level; its Fault Tolerance Option protects instruction/data memory and some CPU structures. RCU streams partial bitstreams from external radiation-hardened memory via 32-bit ICAP at 100 MHz; §V.B–C, p.256. | UNKNOWN — end-to-end protection FMU, GPIO, RCU, ICAP state, multiplexers and external bitstream integrity. Voter/multiplexer failure is explicitly future work (§VII, p.258). |
| Computation state | Duplicated/triplicated modules are reset to an initial state after each reconfiguration; §V.D, p.257. | **INFERENCE:** continuity of state is not preserved. Lost work, re-feed of input streams and state synchronization are not costed. |

SOURCE — article’s own contribution boundary: §III, p.253 calls the **BRAM radiation particle sensor** the primary contribution and says it may be combined with a suitable adaptive system similar to prior work. INFERENCE — the redundancy framework is not wholly claimed as new by this paper, and its analytical case study should not be presented as an independent experimental validation of every chain component.

### 3.2. Observation chain, window and delay

SOURCE — end-to-end described chain (§§II,IV,V, pp.252–256):

`SBITERR/DBITERR in selected BRAMs → counters/Fault Memory → periodic MicroBlaze polling → μ_BRAM → lookup f_CFG(μ_BRAM) → μ_CFG → module PFH/threshold → l → GPIO/RCU → partial bitstream/replicas`.

SOURCE — 298 BRAM primitives are available on Virtex-5QV. Table II, p.254 gives expected `μ_BRAM` (upsets/s) for 1, 32, 64 and 298 detector BRAMs. Authors choose **64 BFDs**; expected inter-upset time is about 28 h at Solar Minimum, 15 min at Worst Week and 1 min at Peak 5 Minutes. They average three measured mean-times-to-upset for a coarse estimate, assume a smooth transition between solar conditions, explicitly call confidence low due to Poisson-distributed SEUs, and defer a sophisticated estimator; §IV.A, p.254.

**INFERENCE — observability limit:** this is an event-count-defined estimator, not a fixed-length time window. At low rate, fresh information may arrive only on the cited inter-event scale; no decision-delay bound, confidence interval, false-alarm probability or missed-flare probability is supplied. The paper’s smooth-transition assumption is material to safe switching.

SOURCE — `μ_CFG=f_CFG(μ_BRAM)` is generated from CREME96/XRTC results for five predefined GEO solar conditions, using log-scale linear interpolation; Eq.(3), Figs.3–4, pp.254–255. Environment: Virtex-5QV behind 4.5 mm Al. Table I separately reports device rates for configuration controller, configuration memory, BRAM, FF/DSP resources.

**INFERENCE — sensor-to-hazard relation:** co-location and high BRAM sensitivity give an engineering rationale, but the relation is model-derived rather than established by a simultaneous physical irradiation/calibration of the implemented BRAM sensor and application failures. It is device/environment/shielding dependent. `μ_BRAM` is neither a direct readout of configuration upsets nor a forecast beyond the assumed smooth environmental evolution.

SOURCE — the authors define two-or-more corrupted bits **within one BRAM primitive during a scrub cycle** as MBU (§V.A, p.255). INFERENCE — this definition does not distinguish a same-parent physical MBU from sequential accumulation during the cycle. It therefore cannot be imported as a parent-event multiplicity definition for RQ-001.

### 3.3. Reliability object, formulas and requirements

SOURCE — environment rates are calculated as

- Eq.(1), p.253: `μ_HI = ∫ σ(L) P(L) F(L) dL`;
- Eq.(2), p.253: `μ_P = ∫ σ(E) f(E) dE`;
- overall device upset rate is their sum.

SOURCE — for a module using `n_e,m` essential configuration bits out of `n_FPGA`, every single essential-bit corruption is assumed capable of causing module failure when the module is not triplicated:

- Eq.(4), p.254: `λ_m = μ_CFG · n_e,m/n_FPGA`;
- Eq.(5): `R_m(t)=exp(-λ_m t)`;
- Eq.(6): `PFH_m=1-R_m(T_h)`, `T_h=3600 s`;
- Eq.(7): `R_m^TMR(t)=3R_m(t)^2-2R_m(t)^3`;
- Eqs.(8)–(10), p.255 replace TMR reliability over a scrub cycle by average rate `[1-R_m^TMR(t_s)]/t_s` and again report the one-hour probability.

SOURCE — voter reliability is excluded; p.255. State upset, faulty mux/RCU, common-mode placement and output corruption timing are not represented in the reported PFH. **INFERENCE:** `PFH_m` is the paper’s probability of module failure in a one-hour interval under an exponential model, not DEC-001 `F_A(t0,T;μ_t0)` and not direct evidence of system-visible incorrect output. There is no general initial distribution or mission aggregation.

SOURCE — threshold Eq.(11), p.256 derives `μ_CFG^l` from selected `PFH^l`; example uses `PFH^(l=1)=3×10^-6`, `PFH^(l=2)=1×10^-5`, `n_e,m=691,354`, `n_FPGA=34,087,072`. Policy: `l=0` below `4.11×10^-8`, `l=1` from `4.11×10^-8` to `1.37×10^-7`, `l=2` above `1.37×10^-7` upsets/(device·s). The claimed contract is **at least SIL 1**, whose footnote gives a band `10^-5...10^-6`; Fig.6/p.256.

**INFERENCE — comparator fairness:** modes are not maintained at one fixed numerical PFH target; two thresholds within a SIL band are used, and DMR does not lower modeled PFH. This can satisfy the paper’s categorical `at least SIL 1` rule but cannot be imported as a single project requirement or a continuous equal-risk comparison.

### 3.4. System benefit and resource price

SOURCE — Table III, p.257 gives each unreplicated demodulator as 4,176 LUT, 3,735 FF, 69 DSP48; `demod1` has 691,354 essential bits. DMR doubles and TMR triples these module counts; voter and error-detector resources are neglected. The table reports `PFH_m` across five modeled solar conditions; for `demod1` it ranges from `2.54×10^-7` (Solar Maximum) to `1.00×10^-3` (Peak 5 Minutes) without TMR, while TMR+60 s scrub reports `3.23×10^-15` to `5.01×10^-8`.

SOURCE — Table IV, p.258 defines the throughput denominator as the number of concurrently serviced module/channels: `l=0 → 3×`, `l=1 → 2×`, `l=2 → 1×`. At low radiation three channel-specific demodulators operate; DMR consumes channel 2 to duplicate channel 1; TMR consumes channels 2 and 3 to protect channel 1. Authors report at Peak 5 Minutes a PFH decrease by `2.00×10^4` (99.995%) from TMR and state that permanent TMR would reduce throughput to one third; §VI, p.257.

**INFERENCE — exact meaning of benefit:** the freed area performs other useful channel work in `l=0/1`, so this is genuine reuse rather than simply clock-gating replicas. However, `3×` is not throughput of the same single stream or measured jobs/s; it is three distinct frequency-band tasks versus one protected priority task under different radiation conditions. The paper does not integrate a mission profile, reconfiguration downtime or lost state into delivered useful work. The `2×10^4` reliability factor and `3×` throughput occur at different operating points and must not be multiplied into one benefit figure.

SOURCE — permanent sensor/control inputs include 64 BFDs, a Fault Memory/bus structure, MicroBlaze FMU and RCU; partial bitstreams reside in a proposed/available 1 Gbit radiation-hardened SDRAM; ICAP is 32 bit at 100 MHz; §§IV–V, pp.254–256. UNKNOWN — total LUT/FF/BRAM/power of sensor+FMU+RCU, partial-bitstream sizes, transition time/energy, external-memory bandwidth, output interruption and application restart cost. No energy result is reported.

### 3.5. What is and is not demonstrated

**SOURCE — actually supported:** the paper specifies and tool-implements a Virtex-5QV/GoAhead/PlanAhead 13.2 architecture; provides environment convolution, BRAM/configuration rate mapping, PFH formulas, fixed thresholds and a QPSK resource case. It explicitly leaves fault-injection verification, voter/mux reliability, other resource upset rates and improved estimation to future work (§VII, p.258).

**INFERENCE — evidence level:** architecture + synthesis/place/reconfiguration tool flow + analytical case study. No neutron/proton test of the closed loop, no reported injected adaptive transition trace, and no measured end-to-end throughput/availability. Consequently the paper demonstrates feasibility and a conditional analytical opportunity, not an experimentally verified autonomous reliability guarantee.

**UNKNOWN — reproducibility package:** exact family Virtex-5QV, 4.5 mm Al scenario, 64 BFD choice, GoAhead, PlanAhead 13.2, ICAP parameters and QPSK module/resource counts are reported. Source/bitstream, exact board, complete configuration scrubber implementation, fault logs, thresholds’ update code and experiment scripts are not supplied or declared available in the article. GoAhead’s cited existence does not provide this application’s artifact.

**Recommendation:** `CORE` for **case B** as a sensor→threshold→redundancy architecture comparator; `BACKGROUND` for case A because `t_s` is exogenous and fixed.

**Concrete unresolved question created by the paper:** can a configuration-SRAM system use a causal observable with quantified delay/error to select a protection action while maintaining the *same* system failure requirement, once controller/voter/common-mode and transition loss are included? For case A specifically, the source supplies no evidence that varying `t_s` is preferable to fixed 60 s scrubbing.

## 4. MPT-C04 — Gantel et al. 2021

### 4.1. Protected objects, observed objects and runtime actions

| Object | SOURCE — treatment | INFERENCE / UNKNOWN — boundary |
|---|---|---|
| Configuration SRAM | Xilinx UltraScale+ SEM IP scans, detects/classifies and corrects configuration faults; wrapper exposes commands/reports to Cortex-R5. Correctable/uncorrectable and essential/non-essential classes are counted; §§2.2–2.4/Figs.2–6, pp.4–6. | **INFERENCE:** scan/restoration rate is not selected by the controller. Mean full verification is about 50 ms in the tested setup (§3.2, p.8). This is a fixed SEM baseline, not adaptive scrubbing. |
| Essential-bit information | Vivado-generated ASCII EBD indicates every design bit. An optional hardware fetch compresses this to one flag per frame (“frame contains an essential bit”) in BRAM; correctable essential bits are repaired, non-essential faults discarded; §2.3/Figs.3–4, pp.4–5. | **INFERENCE:** frame-level compression can cause extra checks/repairs relative to exact bit classification but paper does not quantify classifier error. It is design-time information, not radiation observation. |
| Uncorrectable configuration fault | Original frame images are extracted with RapidWright and stored in DDR4 at boot. Custom flow reads back the faulty frame and restores via PCAP/DPR; §2.3/Fig.4, p.5. | UNKNOWN — atomicity, integrity of DDR4 frame database, concurrent application behavior and exact recovery latency. Golden-copy validity applies to reconstructible configuration, not arbitrary user data. |
| Reconfigurable application | High-Performance mode gives RPs to distinct accelerators; Safe mode reconfigures flexible partitions for TMR. Low-Power disables RPs via DPR. Cortex-A53 controls deployment/registers; Cortex-R5 monitors; §§1,2.2,2.6, pp.2–4,7–8. | **INFERENCE:** runtime-controlled variable is application placement/redundancy, not SEM frequency. Low-Power entry/exit law is not specified as part of radiation loop. |
| Computation/system state | Watchdog and deterministic-result check detect freeze/wrong result; on mode switch application is stopped, platform reconfigured, application resumed; on run failure testbench stops and PMU resets system; §§2.4,3.2/Fig.6, pp.6–9. | UNKNOWN — application-state checkpoint/restore, lost work, I/O quiescence, in-flight AXI/DDR transactions and whether resume continues or restarts semantic work. |
| SEM/controller | SEM is implemented in FPGA logic; R5 reads it. Authors explicitly identify protection of SEM and FPGA internal memory as future work; §4, p.10. | **INFERENCE:** the observer/repair agent lies in the radiation domain and is not covered by the reported reliability result as an independently hardened controller. |

SOURCE — exact platform class: Zynq UltraScale+ MPSoC, quad Cortex-A53, dual Cortex-R5, 2 GB DDR4, AXI-Stream interconnect, ICAP for SEM and PCAP for processor-driven configuration; §2.2/Fig.2, pp.3–4. **UNKNOWN:** exact device part number and development board are not stated in this article. The cited vendor document is **PG187 UltraScale Architecture SEM Controller v3.1 (2019)**, not PG036 for 7-series; no vendor guide was opened or generalized in this task.

### 4.2. Observation, threshold and unsafe transition boundary

SOURCE — SEM reports feed counters for injected, corrected and uncorrectable faults plus SEM state; essential/non-essential classification comes from EBD. Cortex-R5 particularly monitors the number of soft errors detected by the configuration scrubber. Count is periodically reset to form an error rate. If rate exceeds a threshold, application stops, platform switches High-Performance→Safe, then resumes; below threshold it returns; §2.3–2.4, pp.4–7.

**UNKNOWN:** numerical threshold, reset/observation period, hysteresis equality, minimum residence, update latency, mapping from count to probability of application failure, and confidence/uncertainty. The text says the threshold “should be defined” by the number of soft errors able to cause failure but provides no calibration. **INFERENCE:** this is a reactive simple threshold switch; no forecast of the next window is implemented. Neural-network prediction appears only as future possibility (§4, p.10).

SOURCE — the discussion states that High-Performance→Safe cannot necessarily be performed at any time. At high measured radiation, dynamic reconfiguration is considered hazardous; additional mitigation such as DPR readback/check of the reconfigured partition is needed. In Safe mode the two filters are not dynamically reconfigured and AES is kept in place for this reason; §4, p.10.

**INFERENCE — internal method gap:** the trigger requests reconfiguration precisely when the observed rate becomes high, while the safety procedure and its time are not closed. This does not invalidate the static-mode fault-injection result, but it prevents treating the described controller as a verified safe closed loop. The work itself requires a post-reconfiguration check; no transition-failure probability or delay is reported.

### 4.3. Failure event and fixed-mode injection evidence

SOURCE — monitor periodically receives deterministic processing result and resets watchdog. Wrong signature/result or watchdog expiry is a computation/system failure; current run stops, elapsed time and number injected are returned, system reset through PMU; §2.4/Fig.6, p.6. Section 3.2, p.8 states failure occurs when scrubber does not repair before the faulty bit is used, causing computation error or freeze. Thus a configuration error can affect output/state before detection and repair.

SOURCE — fault injection uses SEM’s LFSR pseudo-random linear frame address or a software-fed FIFO for constrained regions. Authors inject only into protected regions when evaluating a mechanism so failures in unprotected areas do not confound it; §2.5, p.7. Addresses vary by PC-provided random seed; injection **time is deterministic**, one fault each 100 ms, not a random process. Mean SEM full scan is about 50 ms; §§2.5,3.2, pp.7–8.

SOURCE — four configurations, same 100 ms injection period/startup, 400 runs each until computation/system failure (§3.2/Fig.9, pp.8–9):

| Tested mode | Scrubber | TMR | Meaning |
|---|---:|---:|---|
| B_MODE | no | no | Basic baseline |
| P_MODE | yes | no | Fixed High-Performance / scrubber-only baseline |
| T_MODE | no | yes | Fixed TMR-only baseline |
| S_MODE | yes | yes | Fixed Safe / combined baseline |

SOURCE — Fig.9 plots empirical “Reliability” against number of injected faults, not mission hours; every injected interval is 100 ms. The paper states P_MODE improves reliability by ×4 and S_MODE by ×4.4 relative to Basic (§4, p.10). It does not define these multipliers as mean, median, quantile or a specific survival point; confidence intervals are absent. Curves show S_MODE best, P_MODE second; T_MODE loses notable benefit beyond roughly 100 injected faults (§3.2, p.9).

**INFERENCE — what the experiment establishes:** under this accelerated configuration-bit injection and deterministic cryptographic workload, constant SEM/scrubbing is the dominant measured protection component; adding TMR gives a smaller additional stated multiplier. The campaign compares fixed modes; it does **not** execute the error-rate threshold transition, changing radiation regimes, reconfiguration under injection, or Low-Power mode. Therefore it does not measure benefit, stability or availability of the adaptive controller.

**INFERENCE — RQ-001 relation:** the failure object is system-visible wrong result/freeze before repair, while x-axis is injected configuration faults. It is closer to a system outcome than raw configuration corruption, but remains conditioned on targeted regions, deterministic interval, workload and monitor. It is not automatically `E_cap` for a controller-managed memory domain, nor `F_A(t0,T;μ_t0)`.

### 4.4. Performance, power and transition price

SOURCE — application: image Grayscale→Sobel, AES-256, storage, SPHINCS+ signature. In Safe mode filters move to software, one flexible TMR partition hosts TMR AES, another hosts three SPHINCS+ instances; §2.6/Fig.7, pp.7–8. High-Performance mode uses separate hardware accelerators.

SOURCE — Table 1/Fig.8, p.8 report **estimated**, not measured, resources and power:

| Module/mode | Raw denominator | Reported value |
|---|---|---:|
| Static partition | 20,568 FF; 17,140 LUT; 2,382 LUTRAM; 7 BRAM; 1 DSP | 2,901 mW |
| Grayscale / Sobel / AES-256 / SPHINCS+ | Per module counts in Table 1 | 1 / 7 / 12 / 21 mW |
| Low-Power / High-Performance / Safe | Whole shown platform estimate in Fig.8 | 2,901 / 2,984 / 3,000 mW |

SOURCE — static partition, particularly processing system, accounts for >90% power; authors say DPR’s impact on overall power is minimal and processor power management would be needed to make Low-Power more useful (§3.1, p.8; §4, pp.9–10). They state no extra power budget is needed depending on High-Performance versus Safe residence, based on close estimates.

**INFERENCE:** this source does not show a substantial energy benefit from adaptation. Low-Power merely disables reconfigurable activity; no released fabric performs other useful work there. In High-Performance, fabric does perform other distinct accelerators, but no tasks/s, latency, throughput, deadline success or energy per completed cryptographic job is reported. Safe and High-Performance do not have an explicitly demonstrated equal useful-service rate.

SOURCE — switching workflow stops application, reconfigures and resumes; p.7/Fig.6. UNKNOWN — stop duration, DPR/PCAP bandwidth used, frame count/bitstream size, verification time, transition energy, state synchronization, lost work and availability. No result shows whether work already computed by replicas is discarded or reconciled. Configuration recovery time and whole-mode transition time must not be conflated.

### 4.5. Strong baselines, reproducibility and validity

SOURCE — fixed B/P/T/S modes isolate no protection, permanent SEM, permanent TMR and permanent combined protection under a common injection period/startup. This is a useful component ablation. However no always-Safe workload performance result and no simple-threshold adaptive baseline are reported. **INFERENCE:** the described controller itself is already a simple threshold method; any more complex scheme must compare against it, not merely against Basic.

SOURCE — the experiment targets mitigation-covered address regions. The interval 100 ms is intentionally pessimistic to accelerate tests; authors cite much lower on-orbit daily counts and plan a random temporal distribution in future (§4, p.10). UltraScale+ 16 nm is discussed as less sensitive than earlier families. INFERENCE — magnitude/direction of x4/x4.4 cannot be transferred to natural particle flux, other placement, another SEM scan period or a different FPGA family without evidence.

SOURCE — reproduction inputs stated: Zynq UltraScale+ MPSoC class, Cortex-A53/R5/FreeRTOS split, 2 GB DDR4, AXI/ICAP/PCAP architecture, SEM and EBD/RapidWright flow, LFSR/FIFO address injection, PC seed, 100 ms period, 400 runs/mode and watchdog/result termination. Data Availability p.11 declares reliability data at a SwitchDrive URL (accessed 2 Sep 2021).

**UNKNOWN — reproducibility blocker:** current accessibility/content/hash of that external dataset was not checked because this bounded task is not an access-completion cycle. No source repository, bitstreams, seed list, exact part/board, Vivado/SEM build settings, application input corpus, threshold/reset period or raw mode-switch logs are supplied in the PDF. Hence the four fixed-mode campaign is partially reproducible in concept, not bit-for-bit controlled from the article alone.

**Recommendation:** `CORE` for fixed SEM/TMR component ablation and `RELATED` as **case B** controller comparator. It is not evidence for case A adaptive scrub-frequency control.

**Concrete unresolved question created by the paper:** after a strong fixed SEM baseline, does runtime switching of redundancy produce more useful work at the same failure requirement once unsafe-transition verification, stoppage and state loss are included? The present x4/x4.4 result does not answer it because the adaptive transition was not exercised.

## 5. Direct comparison

| Comparison field | Glein 2014 | Gantel 2021 |
|---|---|---|
| Object | SOURCE — Virtex-5QV configuration SRAM + BRAM sensor + QPSK modules | SOURCE — Zynq UltraScale+ configuration SRAM + cryptographic/image pipeline |
| Error | SOURCE — CREME96/XRTC modeled device SEU rates; every essential configuration upset treated as module-failure opportunity; BRAM SBIT/DBIT observed | SOURCE — SEM-injected configuration-bit fault; result/freeze before repair terminates run |
| Observation | SOURCE — 64 BRAM detectors, three-event coarse rate, lookup `μ_BRAM→μ_CFG` | SOURCE — SEM detected-error count periodically reset; essential/error class available |
| Observation delay/uncertainty | SOURCE — expected event spacing 28 h/15 min/1 min by condition; low confidence explicitly stated; smooth transition assumed | UNKNOWN — window, threshold, latency and uncertainty not stated; 50 ms is SEM full-scan mean, not controller estimation window |
| Configuration restoration | SOURCE — independent blind periodic scrub, case-study `t_s=60 s` | SOURCE — SEM scan/correct; custom golden-frame restoration for uncorrectable faults |
| Adaptive action | SOURCE — no redundancy / DMR / TMR via partial reconfiguration | SOURCE — High-Performance↔Safe redundancy/placement; Low-Power separately available |
| Transition | SOURCE — ICAP partial bitstream; module reset to initial state | SOURCE — stop application, DPR, resume; high-radiation transition needs added verification |
| Requirement/metric | SOURCE — modeled one-hour `PFH_m`, “at least SIL 1” band | SOURCE — empirical survival-like curve vs injected faults; wrong output/freeze event |
| Strong fixed comparator | SOURCE — permanent TMR is conceptual throughput baseline; fixed scrub assumed | SOURCE — B, permanent SEM-only, TMR-only, SEM+TMR tested separately |
| System/resource result | SOURCE — 3/2/1 simultaneous channels; analytical PFH reduction; no energy/transition result | SOURCE — x4 SEM, x4.4 SEM+TMR claim; estimated 2901/2984/3000 mW; no useful-throughput result |
| Evidence level | SOURCE — architecture/tool flow + environment/reliability calculation; no closed-loop injection | SOURCE — implemented platform + fixed-mode configuration fault injection + power estimate; adaptive loop not tested |
| Case A support | INFERENCE — no; `t_s` fixed/exogenous | INFERENCE — only fixed SEM efficacy, no adjustable restoration policy |
| Case B support | INFERENCE — conditional analytical feasibility and real reuse of channels | INFERENCE — architecture and component ablation, but adaptive benefit remains unmeasured |
| Transfer constraint | INFERENCE — Virtex-5QV BRAM/config sensitivity map and ICAP flow device-specific | INFERENCE — UltraScale+ SEM/PCAP/EBD flow device-specific; do not apply 7-series PG036 semantics |

## 6. What each paper proves, where the gain comes from, and what remains open

### 6.1. Glein

- **SOURCE — demonstrated in accepted source scope:** a specified BRAM-sensor/threshold/reconfiguration architecture and analytical QPSK case based on Virtex-5QV environment/device rates.
- **INFERENCE — system gain:** opportunistic use of fabric for two additional independent channels when TMR is not selected; high-radiation reliability gain comes from TMR plus fixed scrubbing, not from changing scrubbing.
- **UNKNOWN / cannot claim:** measured adaptive closed-loop benefit, mission-integrated work, energy saving, safe state-preserving transitions, calibrated prediction, reliability including voter/controller/common-mode failures.
- **INFERENCE — project question:** whether any configuration-restoration actuator at fixed redundancy has enough controllable cost/risk range to beat fixed scrub. Glein does not supply a positive answer; its stronger occupied approach is redundancy switching by a simple threshold.

### 6.2. Gantel

- **SOURCE — demonstrated:** relative survival behavior of four fixed mitigation configurations under one fault/100 ms for 400 runs/mode; resource counts and estimated mode power; recovery architecture for SEM error classes.
- **INFERENCE — system gain:** reliable operation mainly improves from constant SEM; safe TMR provides additional masking. Fabric-mode flexibility changes which accelerators execute, but a quantitative useful-performance gain of adaptive switching is not established.
- **UNKNOWN / cannot claim:** adaptive-loop reliability, forecast value, energy saving per useful result, transition safety/latency, equivalence of payload service, natural-radiation effectiveness and complete controller protection.
- **INFERENCE — project question:** whether redundancy switching remains beneficial over permanent SEM and permanent Safe after including transition verification/state loss. A simple threshold may be sufficient; this source provides no evidence that a more complex controller is better.

## 7. Design implications without selecting an architecture

### 7.1. Mandatory baselines if Orchestrator later authorizes engineering evaluation

1. **INFERENCE — case A:** strongest admissible constant SEM/scrub setting at fixed redundancy; same essential-bit/static classification; same application load and failure event.
2. **INFERENCE — case B:** permanent Safe/TMR + fixed scrub; High-Performance + fixed scrub; and causal two-threshold/hysteresis switching using the same local count. An adaptive method that only reproduces this threshold effect adds no demonstrated contribution.
3. **INFERENCE — failure accounting:** separate configuration corruption, detected/corrected fault, uncorrectable frame, wrong application output, watchdog freeze, reset, lost state and recovery completion.
4. **INFERENCE — resource accounting:** useful completed work, interface/SEM occupancy, reconfiguration and verification delay, lost work, availability, energy/task, standing sensor/controller/fabric area and protected bitstream/database storage.

### 7.2. Named inputs absent from the two sources

| Missing input | Link it blocks |
|---|---|
| Target FPGA/board, exact SEM version and exposed scan/control interface | Whether case A has a runtime actuator at all, and its admissible range |
| Constant-SEM timing, bandwidth and power measured with target workload | Whether there is a material resource to recover relative to fixed protection |
| Causal relation between observable count and near-future *essential* configuration risk, with delay/error | Whether either A or B can act before dangerous configuration use |
| Safe partial-reconfiguration protocol under elevated radiation | Whether B’s protective transition can complete without increasing failure risk |
| State checkpoint/restart and input replay semantics | Lost work and application-equivalent comparison between modes |
| Equal system reliability requirement and full outcome mapping | Fair fixed-versus-adaptive comparison under RQ-001/RQ-007 |
| Controller/SEM/voter/bitstream-database protection | End-to-end rather than component-only reliability |
| Raw code/bitstreams, exact seeds, injection logs and platform build files | Exact reproduction of both implementations/results |

**INFERENCE — stopping judgment:** the two reads are sufficient to reject a mistaken attribution (“adaptive scrubbing produced the published throughput/reliability gain”) and to classify the occupied case B architecture. They are not sufficient to start controller development or promise a positive case A result. The next decision is an Orchestrator/engineering feasibility gate on the named target FPGA and SEM control/cost interface, not another general literature search.

## 8. Candidate propositions for possible Evidence Auditor review

These are atomic candidates only; no `CLM`/`EVD` record or audit disposition is created.

1. **SOURCE-CANDIDATE:** Glein’s runtime actuator is the redundancy level `l∈{0,1,2}`; the configuration scrub period remains an assumed `t_s=60 s` in the case study. Glein §§V.D–VI, p.257, Table III/Fig.7.
2. **SOURCE-CANDIDATE:** Glein’s BRAM-rate estimator averages three measured inter-upset times, is explicitly low-confidence, and assumes smooth transitions between solar conditions. Glein §IV.A, p.254.
3. **SOURCE-CANDIDATE:** Glein’s 3×/2×/1× throughput is the number of simultaneously used processing channels as two channels are reassigned to DMR/TMR of channel 1. Glein §VI, pp.257–258, Fig.7/Table IV.
4. **INFERENCE-CANDIDATE:** Glein’s reported adaptive benefit is conditional analytical resource reallocation, not a measured mission-level gain at one fixed numerical reliability requirement. Basis: Eqs.(4)–(11), Tables III–IV and future-work statement, pp.254–258.
5. **SOURCE-CANDIDATE:** Gantel’s fault campaign tests four fixed configurations, 400 runs each, with one pseudo-random-address injection every 100 ms and mean SEM scan around 50 ms. Gantel §3.2, pp.8–9, Fig.9.
6. **SOURCE-CANDIDATE:** Gantel reports ×4 for permanent scrubber and ×4.4 for scrubber+TMR relative to Basic, while no adaptive-switch campaign is reported. Gantel §§3.2–4, pp.8–10, Fig.9.
7. **SOURCE-CANDIDATE:** Gantel’s described high-error transition is incomplete as a safety argument: authors warn DPR under high radiation is hazardous and require additional readback/check. Gantel §4, p.10.
8. **INFERENCE-CANDIDATE:** neither source establishes substantial benefit from runtime management of configuration-restoration rate at fixed computational redundancy; both support only case B or a fixed-scrub baseline. Scope: exact two PDFs above; this is not a literature-wide absence claim.

## 9. HANDOFF TO ORCHESTRATOR

Task `PA-FPGA-OBJECT-SELECTION-01`; report v1.0. Both requested full texts were available and read. MPT-C03 identity blocker is closed by the supplied full text: FCCM 2014, pp.251–258, DOI `10.1109/FCCM.2014.79`; MPT-C04 publisher identity is confirmed. Checksums and copy details are in §2.2.

- **Outcome:** `2 — основание относится только к более широкой системе переключения защиты`.
- **Glein disposition:** `CORE` for case B comparator; `BACKGROUND` for case A.
- **Gantel disposition:** `CORE` for fixed SEM/TMR component evidence, `RELATED` for case B adaptive controller, not case A.
- **Strongest evidence:** Glein’s analytically quantified channel-reuse/TMR exchange; Gantel’s 400-run-per-mode ablation showing fixed SEM as the main measured mitigation component.
- **Strongest limitation:** neither source tests an adaptive configuration-scrub rate; Gantel does not test its adaptive mode transition, and Glein has no physical closed-loop campaign.
- **Named next gate:** establish on one target configuration-SRAM FPGA whether SEM exposes a materially useful, safe runtime restoration actuator and measure the fixed baseline’s actual cost. If no material controllable cost exists, case A has no engineering basis from these sources.
- **No transfer:** configuration-scrubbing benefit was not credited with redundancy-switch throughput; no PG036 7-series semantics were transferred to UltraScale+; no RES-003/004, ARCC or new candidate analysis was performed.

## 10. Repository validation note

The instruction-base repository produces a pre-existing validator result of **1 error / 44 warnings**: `BROKEN_LINK` in `docs/scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md` plus legacy/draft metadata warnings. This task does not modify those files. Required acceptance for this draft is: identical diagnostics at task head, no new warning, and `git diff --check` clean. PDF files are not added to Git.

## 11. HANDOFF TO ZOTERO

No Zotero operation is claimed as completed.

| Field | MPT-C03 | MPT-C04 |
|---|---|---|
| Action | Reconcile/import full peer-reviewed FCCM record and attach controlled PDF | Verify/import publisher record and attach controlled PDF |
| Target collection | `DISSERTATION / RQ / RQ-007` | `DISSERTATION / RQ / RQ-007` |
| Identity | DOI `10.1109/FCCM.2014.79`; exact title and author order in §2.2 | DOI `10.3390/electronics10172148`; *Electronics* 10(17):2148 (2021) |
| Duplicate policy | DOI first, then exact title/year; merge, do not create a second record. Remove/reject corrupt secondary DOI `10.1109/.77` if present. | DOI first, then exact title/year; merge, do not create a second record. |
| Metadata check | Reconcile primary IEEE metadata spelling `Robert`/PDF-visible `Robért`; preserve the supplied PDF byline in a provenance note; verify FCCM pages 251–258. | Verify five-author order, publication date, volume/issue/article number and CC BY publisher version. |
| Required tags | `RQ-007`, `FPGA`, `configuration-SRAM`, `BRAM-sensor`, `adaptive-redundancy`, `CORE-case-B`, `PA-FPGA-OBJECT-SELECTION-01` | `RQ-007`, `FPGA`, `configuration-SRAM`, `SEM`, `TMR`, `DPR`, `CORE-fixed-baseline`, `RELATED-case-B`, `PA-FPGA-OBJECT-SELECTION-01` |
| Attachment expectation | Supplied PDF, SHA-256 `b4edeeacf70896feb535e0bbef181e5c6c44049c9b750297bacbd524f04db25b`; do not commit to Git | Supplied publisher PDF, SHA-256 `3045b64b8504d9bce368aa16c28fc3946451d0171dc7829b42e4dd074fba8343`; do not commit to Git |
| Expected result | One deduplicated primary record, corrected DOI/venue/pages, checksum-controlled attachment, provenance note on name rendering | One deduplicated publisher record with checksum-controlled attachment |
