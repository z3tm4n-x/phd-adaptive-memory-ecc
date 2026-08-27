# Targeted Literature Mapping Protocol — RQ-002

**Related RQ:** RQ-002<br>
**Status:** EXECUTION AUTHORIZED — LITERATURE SCOUT LAUNCHED — DEC-001 ALIGNED — CROSS-PUBLISHER SCOPE<br>
**Owner role:** Literature Scout<br>
**Prepared:** 2026-08-26<br>
**Pre-launch correction accepted:** 2026-08-27

## Research Question

Какая минимальная стохастическая модель радиационно-индуцированных ошибок SRAM одновременно физически обоснована и вычислительно пригодна для моделирования накопления ошибок и адаптивного scrubbing?

Обязательный representation sub-question:

> Какое минимальное представление одного radiation event необходимо сохранить после отображения на ECC architecture, чтобы корректно вычислять `E_cap` при accumulation и scrubbing?

## Search objective

Картировать эмпирически поддержанные model classes и допущения о arrival process, event marks, accumulation state, non-stationarity, MCU/MBU, spatial/temporal dependence, uncertainty and scrub/reset semantics, чтобы выбрать минимально достаточную error model, проверить decision gate по C-RQ-05 и разблокировать первый количественный prototype.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-002; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

IEEE Xplore is a mandatory anchor but not a sufficient sole source. The search must include an independent cross-publisher route and targeted non-IEEE publisher coverage to reduce publisher/database bias.

## External-review disposition

The pre-launch external-advisor review is classified `UNVERIFIED`. It supplies adversarial search targets and protocol corrections, not scientific evidence or project decisions. It does not reopen RQ-001 or revise DEC-001.

The radiation/reliability novelty-threat line belongs to RQ-002. The future inspection/maintenance/checking-policy line is recorded separately in [`research_backlog.md`](../research_backlog.md) and is not an RQ-002 blocker.

## Input contract from DEC-001

Every candidate model must be assessed against the accepted RQ-001 contract:

- primitive event `E_cap(A;t0,T)`;
- general metric `F_A(t0,T; μ_t0)`;
- explicit reporting window and initial state/distribution;
- explicitly declared controller-managed SRAM protection domain `A`;
- partitioning before aggregation when ECC, mapping `W`, arrival process, bank/block or scrubbing semantics differ;
- distinct upset-count, per-codeword exposure, reporting and mission layers;
- no automatic equivalence between `E_cap` and DUE/SDC/miscorrection/system-visible failure.
- explicit/parameterized post-`E_cap` correction, writeback, reset and scrub semantics rather than one fixed downstream consequence.

Literature Scout must identify which state variables and assumptions each model needs to calculate the accepted event/metric. Decoder-outcome semantics remain with RQ-003.

`E_cap` and `τ_A` refer to the underlying physical/codeword state. Future control can act only on observable information. Record, but do not resolve, the dependency `RQ-003 ECC outcome semantics ↔ RQ-004 observables/estimation`; do not assume that SEC is insufficient, DED is mandatory or a particular estimator is needed.


## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Target memory | SRAM; static random access memory; semiconductor memory; статическая память |
| Radiation errors | single-event upset; SEU; soft error; radiation-induced upset; одиночный сбой; радиационный сбой |
| Multiplicity | multiple-cell upset; MCU; multiple-bit upset; MBU; multi-cell upset; множественный сбой |
| Dependence | spatial correlation; temporal correlation; burst; clustering; common-mode; пространственная корреляция; временная корреляция |
| Stochastic model | Poisson process; stochastic process; probabilistic model; non-stationary; time-varying rate; intensity; стохастическая модель; интенсивность ошибок |
| Mechanism provenance | direct same-particle; single-particle multiple upset; sequential accumulation; independent arrivals; false/ambiguous multiple-event classification |
| Mapping | physical-to-logical mapping; physical-cell-to-codeword mapping; interleaving; interleaving distance; geometric factor; codeword impact |
| Event representation | event mark; marked point process; multiplicity mark; joint codeword-impact mark; topology; marginal multiplicity |
| State and repair | accumulated-error state; word age; exposure age; correction; writeback; reset; scrubbing phase; scan position |
| Uncertainty/observation | classification uncertainty; cross-section uncertainty; censored observation; imperfect observation; latent intensity; filtering; state estimation |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## Candidate model-class sensitivity block

The following are candidate mathematical classes to test, not project assumptions or a complexity wish list:

- homogeneous Poisson process (HPP);
- nonhomogeneous Poisson process (NHPP);
- compound Poisson process;
- doubly stochastic / Cox process;
- marked point process / marked Poisson process;
- renewal process;
- semi-Markov process;
- piecewise-deterministic Markov process (PDMP);
- hidden-state / partially observed process;
- filtering / state estimation;
- censored / imperfect observations;
- stochastic ordering;
- positive dependence / association.

The objective is to determine which class is actually required by evidence and the DEC-001 computation, not to select the most elaborate formalism. Cox, PDMP, association, marked processes and every other class remain candidates until justified. An external-advisor suggestion about association or a conservative upper bound is only a candidate inference requiring proof and checked assumptions.

For every class found, record the empirical motivation, primitive arrival object, state/mark requirements, identifiable parameters, supported scrub/reset semantics, validity domain and computational cost. A class with no relevant SRAM/radiation evidence is recorded as `NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES`, not rejected as mathematically impossible.

## Minimal event-representation hierarchy

Screen evidence against this reduction hierarchy:

`full physical event topology + W → joint post-mapping codeword-impact mark → marginal per-word multiplicity distributions → scalar event/upset rate`.

For every supported level determine:

- which information is retained;
- which physical or statistical dependencies are lost;
- whether parent-event provenance survives;
- when the reduction is exact;
- when it supplies a proven bound;
- when it is only an approximation;
- when it can introduce systematic bias in `E_cap` under accumulation and scrubbing.

Do not assume that a marginal multiplicity distribution such as `q_k` is sufficient. Do not treat association or conservative-ordering arguments as established without a source or a separate derivation under explicit assumptions.

## Mandatory known candidates / anchors

RQ-002 mapping cannot be considered saturated until every record below has an explicit identity, access and screening disposition. Existing candidate labels are retained only as discovery identities; they are not permanent `PAPER` IDs.

| Candidate | Required identity | Mandatory disposition |
|---|---|---|
| C32 | Clemente et al. (2022), “Reliability of Error Correction Codes Against Multiple Events by Accumulation”, DOI `10.1109/TNS.2022.3143652` | verify metadata/access; classify; assess direct-versus-accumulation and mapping relevance |
| C51 | Franco et al. (2020), “Inherent Uncertainty in the Determination of Multiple Event Cross Sections in Radiation Tests” | verify exact bibliographic identity; classify; assess uncertainty and ambiguous multiple-event classification |
| C52 | Franco et al. (2019), “Influence of Randomness During the Interpretation of Results From Single-Event Experiments on SRAMs” | verify exact bibliographic identity; classify; assess randomness/classification uncertainty |
| mandatory anchor | Zebrev et al. (2015), “Statistics and methodology of multiple cell upset characterization under heavy ion irradiation”, `Nuclear Instruments and Methods in Physics Research A`, 775, 41–45, DOI `10.1016/j.nima.2014.11.106` | verify identity/access; classify; assess multiplicity partitioning and uncertainty |
| mandatory target source | Zebrev et al. (2017), “Multiple Cell Upset Partitioning for Simulation of Soft Error Rates in Space Systems with Error Correcting Codes”, exact `arXiv:1704.07271v2` | locate, preserve and hand to Paper Analyst as the required extended v2 source |
| related version identity | RADECS publication, DOI `10.1109/RADECS.2017.8696217` | cross-link as related peer-reviewed publication; keep separate until content comparison |

### Zebrev-2017 version-control rule

The mandatory target is exactly `arXiv:1704.07271v2`. Do not substitute an earlier arXiv version, a conference manuscript or the RADECS publication. Literature Scout must record:

- exact arXiv version and identifier;
- title and authors;
- submission/version date metadata;
- relationship to DOI `10.1109/RADECS.2017.8696217`;
- whether substantive content differences between arXiv v2 and the peer-reviewed version are verified, absent or `UNKNOWN — REQUIRES FULL-TEXT COMPARISON`.

Both records must be preserved as separate version identities until comparison is complete.

### Mandatory Paper Analyst handoff for Zebrev arXiv v2

Literature Scout must locate and preserve the exact v2 full text and pass these targets to Paper Analyst:

- Eqs. (2)–(11): MCU/event partitioning by multiplicity;
- Eqs. (13)–(14): transition from multiplicity-resolved event rates to ECC/system error rate;
- Section III.D, Eqs. (15)–(19): “Scrubbing efficiency for a simple SEC-DED procedure”.

The deep read must answer:

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

Do not characterize Zebrev as having “exactly the project method” or “not the project method” before a feature-by-feature full-text comparison.

## Direct-versus-accumulation extraction contract

For C32, C51, C52, both Zebrev identities and every analogous new candidate, record at discovery level where possible and mark full-text-only fields `UNKNOWN — PAPER ANALYST`:

1. whether the source distinguishes direct same-particle multi-error codeword mechanisms, accumulation from independent arrivals, and false/ambiguous multiple-event classification in radiation tests;
2. whether partitioning occurs at physical-cell multiplicity, spatial topology, after mapping to ECC codewords, or another level;
3. how `W` is represented: explicit physical-cell-to-codeword mapping, interleaving distance, geometric factor, statistical abstraction or absent;
4. whether separate cross sections, probabilities or rates are used;
5. how mechanism-specific quantities are recombined;
6. whether disjoint sample spaces are demonstrated or only an additive approximation is used;
7. which small-parameter or asymptotic assumptions apply;
8. how partition/classification uncertainty is represented;
9. whether that uncertainty propagates into reliability results or remains at cross-section level.

## Required per-paper/model extraction fields

For every `CORE` model paper and any `RELATED` source decisive for a model-class choice, the Scout report must create fields for:

- primitive arrival object: particle event, upset, group or other;
- count/arrival process;
- stationarity/nonstationarity;
- intensity: fixed, deterministic time-varying or latent-random;
- event multiplicity;
- spatial topology and spatial correlation;
- temporal clustering/burst behavior;
- retention of parent-event provenance;
- physical-cell-to-ECC-word mapping treatment;
- representation of one event after mapping;
- state variables required for accumulation;
- initial state / initial distribution requirements;
- correction/writeback/reset/scrub semantics;
- sequential word-age representation;
- uncertainty treatment;
- empirical validation;
- domain of validity;
- computational tractability for adaptive scrubbing;
- connection to DEC-001 `E_cap` and `F_A(t0,T; μ_t0)`.

At Scout stage these fields are screening/triage observations, not claim-level full-text conclusions. Unknown fields remain explicit and become targeted Paper Analyst questions.

## Search-source coverage and access rules

### Mandatory routes

1. **IEEE Xplore** — primary anchor for IEEE TNS, IEEE reliability/device journals and IEEE-hosted conference proceedings.
2. **Independent cross-publisher index** — execute at least one of:
   - Scopus — preferred when accessible;
   - Web of Science Core Collection — accepted equivalent;
   - Engineering Village Compendex/Inspec — accepted engineering/physics equivalent.
3. **Targeted publisher backfill**:
   - ScienceDirect;
   - SpringerLink.
4. **Secondary discovery and citation expansion**:
   - Scite;
   - ResearchRabbit after seed selection.

### Supplemental route

- NASA NTRS/NEPP-related public records for test reports, mission context and technical evidence. A technical report remains `RELATED` or `BACKGROUND` unless a peer-reviewed publication identity is verified.

### Access fallback

At the start of execution, record `ACCESSIBLE`, `PARTIAL` or `UNAVAILABLE` for every route.

If Scopus, Web of Science and Compendex/Inspec are all unavailable:

- do not claim that a cross-publisher index was searched;
- execute public metadata fallback through Crossref and/or OpenAlex;
- execute the targeted ScienceDirect and SpringerLink searches below;
- record the resulting coverage limitation explicitly;
- use public web/Google Scholar only as a locator or sensitivity check, not as a reproducible primary database and not as a stopping-criterion substitute.

Publisher search, metadata discovery, citation expansion and full-text evidence are distinct layers. Discovery inclusion never implies that full text was checked.

### Targeted non-IEEE venues

At minimum, search/filter for relevant records in:

- `Microelectronics Reliability`;
- `Nuclear Instruments and Methods in Physics Research Section A`;
- `Nuclear Instruments and Methods in Physics Research Section B`;
- `Radiation Physics and Chemistry`;
- `Journal of Electronic Testing`;
- `Science China Technological Sciences`.

Additional venues may be added only when a candidate or citation chain exposes a relevant model/evidence category; the exact reason is logged.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. SRAM AND ("single event upset" OR SEU OR "soft error") AND ("stochastic model" OR "statistical model" OR probability OR "upset rate")
2. SRAM AND ("multiple cell upset" OR MCU OR "multiple bit upset" OR MBU) AND (spatial OR correlation OR distribution OR model*)
3. (SRAM OR "semiconductor memory") AND radiation AND (nonstationary OR "non-stationary" OR "time-varying" OR intensity) AND (error OR upset)
4. ("radiation induced errors" OR "single event effects") AND SRAM AND (clustering OR burst OR correlation OR independence) AND (model OR measurement)
5. SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "independent arrivals" OR "same particle") AND (ECC OR codeword OR interleaving)
6. SRAM AND radiation AND ("compound Poisson" OR "marked Poisson" OR "marked point process" OR NHPP OR Cox OR renewal OR "hidden state")
7. SRAM AND radiation AND ("semi-Markov" OR PDMP OR "piecewise deterministic Markov" OR "renewal process")
8. SRAM AND radiation AND (filtering OR "state estimation" OR "partially observed" OR censored OR "imperfect observation")
9. SRAM AND radiation AND ("stochastic ordering" OR association OR "positive dependence")

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## Independent cross-publisher index search strings

### Scopus — preferred syntax

Run separately and preserve exact executed syntax, filters, hit counts and export date.

1. `SCOPUS-Q1: TITLE-ABS-KEY(SRAM AND ("single event upset" OR SEU OR "soft error") AND ("stochastic model" OR "statistical model" OR "Poisson process" OR "upset rate"))`
2. `SCOPUS-Q2: TITLE-ABS-KEY(SRAM AND ("multiple cell upset" OR MCU OR "multiple bit upset" OR MBU) AND ("spatial correlation" OR topology OR cluster* OR multiplicity OR distribution))`
3. `SCOPUS-Q3: TITLE-ABS-KEY((SRAM OR "static random access memory") AND (radiation OR neutron OR proton OR "heavy ion") AND (nonstationary OR "non-stationary" OR "time-varying" OR burst OR clustering))`
4. `SCOPUS-Q4: TITLE-ABS-KEY(SRAM AND (scrub* OR repair OR accumulation) AND ("error process" OR "arrival process" OR reliability) AND (ECC OR "error correction"))`
5. `SCOPUS-Q5: TITLE-ABS-KEY(SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "independent arrival*" OR "same particle") AND (ECC OR codeword OR interleav*))`
6. `SCOPUS-Q6: TITLE-ABS-KEY(SRAM AND radiation AND ("compound Poisson" OR "marked Poisson" OR "marked point process" OR NHPP OR "Cox process" OR renewal OR "hidden state"))`
7. `SCOPUS-Q7: TITLE-ABS-KEY(SRAM AND radiation AND ("semi-Markov" OR PDMP OR "piecewise deterministic Markov" OR "renewal process"))`
8. `SCOPUS-Q8: TITLE-ABS-KEY(SRAM AND radiation AND (filtering OR "state estimation" OR "partially observed" OR censored OR "imperfect observation"))`
9. `SCOPUS-Q9: TITLE-ABS-KEY(SRAM AND radiation AND ("stochastic ordering" OR association OR "positive dependence"))`

### Web of Science / Compendex / Inspec substitute

If Scopus is unavailable, translate SCOPUS-Q1…Q9 without semantic expansion:

- Web of Science: use `TS=(...)` with the same concept blocks;
- Compendex/Inspec: search title/abstract/controlled terms with the same concept blocks.

Record the exact platform-specific executed query. Interface-driven syntax changes are allowed; silent concept changes are not.

### Public metadata fallback

Only when all three subscription indexes are unavailable, execute these concept queries through Crossref and/or OpenAlex:

1. `SRAM "single event upset" stochastic model`
2. `SRAM "multiple cell upset" spatial correlation topology`
3. `SRAM radiation nonstationary time-varying upset rate`
4. `SRAM error accumulation scrubbing ECC reliability`
5. `SRAM multiple event direct accumulation codeword interleaving`
6. `SRAM radiation compound Poisson marked process NHPP Cox renewal`
7. `SRAM radiation semi-Markov PDMP renewal process`
8. `SRAM radiation filtering state estimation partially observed censored`
9. `SRAM radiation stochastic ordering association positive dependence`

The fallback does not establish equivalence to Scopus/WoS/Compendex coverage.

## Targeted ScienceDirect search strings

Run across ScienceDirect, then repeat with relevant journal filters where supported:

1. `SRAM AND "single event upset" AND ("stochastic model" OR "statistical model" OR "upset rate")`
2. `SRAM AND ("multiple cell upset" OR MCU OR MBU) AND ("spatial correlation" OR topology OR multiplicity)`
3. `SRAM AND radiation AND (nonstationary OR "time-varying" OR clustering OR burst)`
4. `SRAM AND ("Poisson process" OR "arrival process") AND ("soft error" OR upset)`
5. `SRAM AND ("multiple event" OR MCU OR MBU) AND (accumulation OR "same particle") AND (ECC OR codeword OR interleaving)`
6. `SRAM AND radiation AND ("compound Poisson" OR "marked point process" OR NHPP OR Cox OR renewal)`

Mandatory journal-filter checks:

- `Microelectronics Reliability`;
- `Nuclear Instruments and Methods in Physics Research Section A`;
- `Nuclear Instruments and Methods in Physics Research Section B`;
- `Radiation Physics and Chemistry`.

## Targeted SpringerLink search strings

1. `SRAM "multiple cell upset" spatial correlation`
2. `SRAM "single event upset" stochastic model`
3. `SRAM radiation upset multiplicity topology`
4. `SRAM soft error accumulation scrubbing ECC`
5. `SRAM multiple event direct accumulation codeword mapping`
6. `SRAM radiation marked process nonhomogeneous Poisson hidden state`

Mandatory journal-filter/title checks:

- `Journal of Electronic Testing`;
- `Science China Technological Sciences`.

## NASA NTRS supplemental search strings

1. `SRAM "multiple cell upset" radiation`
2. `SRAM SEU test heavy ion proton neutron`
3. `SRAM "soft error rate" model`
4. `SRAM scrubbing reliability radiation`
5. `SRAM multiple event accumulation ECC interleaving`

Record document type and peer-review status. Do not promote a presentation/report to peer-reviewed evidence by implication.

## eLibrary search concepts/strings

**Current execution disposition:** `DEFERRED / UNKNOWN COVERAGE`. eLibrary is unavailable to Literature Scout and must not be queried in this cycle. The strings below are retained for a future local/authorized handoff; lack of access is not a zero-result finding and does not block the bounded IEEE Xplore/Scite/ResearchRabbit mapping.


Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (SRAM ИЛИ «статическая память») И («одиночный сбой» ИЛИ SEU ИЛИ «радиационный сбой») И («стохастическая модель» ИЛИ «вероятностная модель» ИЛИ «интенсивность сбоев»)
2. (SRAM ИЛИ «статическая оперативная память») И («множественный сбой» ИЛИ MCU ИЛИ MBU ИЛИ «многократный сбой») И («пространственная корреляция» ИЛИ кластеризация ИЛИ распределение)
3. («радиационно-индуцированные ошибки» ИЛИ «одиночные эффекты») И (память ИЛИ SRAM) И (нестационарность ИЛИ «изменяющаяся интенсивность» ИЛИ корреляция)

## Scite usage

- Использовать после первичного IEEE/cross-publisher screening как secondary discovery и sanity-check layer.
- Для каждого seed paper проверить bibliographic identity и наличие correction/retraction notice.
- Просмотреть supporting/contrasting citation signals только для выбора follow-up sources и обнаружения спорных допущений.
- Добавлять peer-reviewed related works в candidate list с пометкой discovery route = Scite.
- Не считать Scite заменой primary source, exhaustive search или отдельным evidence audit.

## Inclusion criteria

- Primary empirical irradiation/field study для SRAM или явно сопоставимой semiconductor memory.
- Публикация определяет stochastic/statistical model либо предоставляет данные для проверки её assumptions.
- Можно извлечь upset multiplicity, spatial/temporal structure, arrival process или rate variability.
- Условия устройства, технологии и radiation environment описаны достаточно для domain-of-validity assessment.
- Источник позволяет связать хотя бы один извлекаемый элемент evidence с RQ-002.
- Источник characterizes direct-event/accumulation partitioning, physical-to-codeword mapping, classification uncertainty or a candidate stochastic class relevant to `E_cap`.
- Для peer-reviewed работ доступны достаточные metadata и abstract; необходимость full text отмечается для Paper Analyst.
- Язык: английский или русский.

## Exclusion criteria

- Только aggregate SER value без описания multiplicity, process assumptions или measurement context.
- Модель независимых Poisson events принята без обоснования и без данных для проверки.
- Исследование относится только к логике/регистрам без аргументированной переносимости на SRAM.
- Simulation-only error injection без физического или empirical basis для radiation error process.
- Secondary summary без traceable primary source, если он используется как доказательство.
- Публикация, не позволяющая определить объект памяти, error-protection context или релевантный measurement/model.
- Дубликат; сохраняется одна canonical record, а варианты metadata связываются в screening log.
- Work focused only on permanent faults, cumulative TID degradation, destructive SEE/SEFI or another persistent mechanism without separable transient-upset evidence.
- General inspection/maintenance/control scheduling without an explicit radiation-error-model contribution; route it to the future bounded backlog task rather than RQ-002.

## Target publication types

- Peer-reviewed irradiation and field-observation studies.
- Peer-reviewed reliability/radiation-effects modeling papers.
- Device- and architecture-level conference papers с данными SEU/MCU/MBU.
- Authoritative radiation test reports с traceable methods, как RELATED/BACKGROUND.
- Version-controlled preprints when they are mandatory extended sources or expose methods/equations not available in the peer-reviewed version; version identity and review status must remain explicit.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Жёсткой нижней границы нет. Первый проход: 2000–present; более ранние seminal SEU/MCU models включаются через citation chaining.

Любое изменение временного фильтра документируется; публикации не исключаются только по возрасту, если backward chaining показывает их фундаментальную роль.

The mandatory known candidates are included regardless of the first-pass date filter.

## Failure-domain boundary

The base RQ-002 model is the transient radiation-induced upset process. Permanent faults, cumulative TID degradation, destructive SEE/SEFI and other persistent mechanisms are explicit out-of-scope/revisit conditions unless later evidence motivates a separate scope decision. They must not be silently folded into the active model or used to expand this cycle.

## Screening procedure

1. Выполнить access test и создать source-coverage table: route, platform, access status, limitation.
2. Resolve every mandatory known candidate before general saturation assessment: exact identity, version, access, duplicate/version relation, classification and next action.
3. For `arXiv:1704.07271v2`, verify the exact v2 metadata and keep DOI `10.1109/RADECS.2017.8696217` as a separate related identity until content comparison.
4. Создать search-log entry для каждой database/query pair: database, дата, exact executed query, filters, hits and export/screening route.
5. Дедуплицировать across all routes по DOI; при отсутствии DOI — по normalized title + year + first author. Related versions are cross-linked, not collapsed before comparison.
6. Выполнить title/metadata screening по inclusion/exclusion criteria.
7. Выполнить abstract screening без глубокого claim-level анализа.
8. Для каждого record сохранить discovery route, publisher/platform, document type и verified/unverified peer-review status.
9. Классифицировать каждый screened item как `CORE`, `RELATED`, `BACKGROUND` или `REJECT`; для `REJECT` и пограничных случаев записать reason.
10. Populate the required per-paper/model fields. Use `UNKNOWN — PAPER ANALYST` wherever discovery metadata/abstract does not support the entry.
11. Построить coverage matrix «evidence category → candidate papers» по категориям:
   - arrival/count process;
   - stationarity/nonstationarity;
   - MCU/MBU multiplicity distribution;
   - spatial topology/correlation;
   - direct-event vs independent-accumulation provenance;
   - mapping/partition implications for `E_cap`;
   - initial state, exposure age and scrub-state variables;
   - empirical validation and domain of validity.
12. Build the event-representation hierarchy matrix and state, for each reduction, what is retained/lost and whether exactness, a bound, approximation or possible bias is supported.
13. Build the direct-versus-accumulation matrix and the RQ-002 subset of the [novelty-threat matrix](../novelty_workflow.md). At Scout stage, unresolved feature cells remain explicit rather than inferred.
14. Map candidate mathematical classes to evidence, required state/marks, identifiability, validation and computational feasibility; do not choose a project model.
15. Выбрать 2–5 seed papers по правилам ниже.
16. Выполнить ограниченное expansion через ResearchRabbit, затем повторить deduplication и screening.
17. Для принятых records подготовить structured `HANDOFF TO ZOTERO`; глубокое чтение передать Paper Analyst with named feature/extraction gaps.
18. Return one of the C-RQ-05 dispositions: `GATE LIKELY TRIGGERED`, `GATE NOT YET TRIGGERED`, or `UNKNOWN — INSUFFICIENT DISCOVERY EVIDENCE`, with a bounded rationale.

## Seed-paper selection criteria

- Источник предоставляет эмпирические distributions/rates или явно валидирует stochastic assumptions.
- Хотя бы один seed должен покрывать MCU/MBU и spatial correlation, если доступен.
- Хотя бы один seed должен рассматривать time variability/non-stationarity либо обосновывать stationarity.
- Device technology и radiation conditions позволяют оценить переносимость.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-002, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.
- Если найден сильный non-IEEE source, как минимум один seed должен представлять cross-publisher evidence; отсутствие такого seed требует явного объяснения.
- Prefer sources capable of discriminating competing model/event-representation classes or defining a first quantitative prototype.
- Mandatory-anchor status does not automatically make a source a seed; seed selection still requires a stated decision-enabling role.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, event/mark representation, mechanism partition, mapping treatment, uncertainty treatment, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records. Do not open a second general RQ-002 expansion cycle automatically.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-002`.
- Required logical tags: `rq/RQ-002`, `topic/radiation-error-model`, `topic/SEU`, `topic/MCU-MBU`, `topic/spatial-correlation`, `topic/direct-vs-accumulation`, `memory/SRAM`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Preserve exact version metadata for `arXiv:1704.07271v2`; cross-link but do not merge it with the RADECS DOI record before content comparison.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- Model classes for arrival, accumulation, marks/dependence and time-varying or latent-random intensity.
- Empirical basis для independence/Poisson/stationarity assumptions либо evidence против них.
- Frequency/distribution и spatial structure MCU/MBU.
- Domain of validity по device technology, geometry и radiation environment.
- Evidence, достаточный для decision gate: материально ли MCU/MBU или spatial correlation меняют структуру/вероятность reliability event RQ-001.
- State variables needed to specify `μ_t0`, including accumulated errors, word exposure ages and scrubber state where relevant.
- Evidence on when a controller-managed domain must be partitioned and how dependence across partitions is represented.
- Minimum arrival-process and event/mark representations needed to calculate `E_cap` after mapping `W`.
- Exact, bounded or approximate reductions across the event-representation hierarchy and any systematic-bias risk.
- Distinction among direct same-particle, independent accumulation and ambiguous radiation-test classification, including recombination/non-overlap semantics.
- Uncertainty in multiplicity/cross-section classification and whether it propagates into the reliability result.
- Correction/writeback/reset/scrub semantics and the ability to represent sequential word ages without fixing one post-`E_cap` consequence.
- Experimentally identifiable parameters, validation requirements and computational feasibility for adaptive scrubbing.
- Inputs/outputs required by RQ-003, RQ-004 and the first quantitative model prototype.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## RQ-002 output contract

The accepted RQ-002 synthesis must eventually determine, or preserve as a bounded alternative/gap:

1. minimal arrival-process representation;
2. minimal event/mark representation after `W`;
3. spatial and inter-word dependencies that must be retained;
4. information that can be aggregated without losing required reliability information;
5. minimal accumulation state and initial-state/distribution requirements;
6. treatment of nonstationary/time-varying or latent-random intensity;
7. reset/correction/writeback/scrub semantics the model can support;
8. experimentally identifiable parameters and unresolved uncertainties;
9. validation requirements and computational feasibility;
10. outputs required by RQ-003, RQ-004 and future adaptive-control studies.

The model must not hard-code one post-`E_cap` repair/reset or decoder/system consequence. Those semantics remain explicit or parameterized.

## Stopping criterion

Mapping для RQ-002 может быть остановлен, когда одновременно выполнены условия:

- все заранее определённые IEEE Xplore strings выполнены и воспроизводимо записаны;
- выполнен минимум один independent cross-publisher index route; если все subscription indexes unavailable, выполнен и явно ограничен Crossref/OpenAlex fallback;
- выполнены targeted ScienceDirect and SpringerLink searches, включая mandatory journal checks;
- NASA NTRS supplemental route выполнен либо документирована техническая недоступность;
- eLibrary explicitly recorded as `DEFERRED / UNKNOWN COVERAGE` under the current access constraint;
- every mandatory known candidate has an explicit identity, access, version relation, screening class and next-action disposition;
- exact `arXiv:1704.07271v2` has been located and preserved for Paper Analyst, or a named access blocker has been returned; an earlier/preprint/conference/RADECS version is not an acceptable silent substitute;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- every candidate model class has relevant evidence or an explicit `NO RELEVANT EVIDENCE FOUND IN EXECUTED ROUTES` disposition;
- the minimal-representation hierarchy and direct-versus-accumulation fields have been populated to discovery depth, with full-text gaps named;
- the RQ-002 novelty-threat matrix covers all mandatory anchors at discovery depth and identifies the exact cells requiring deep read;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены source-coverage table, candidate table, gaps and handoffs.

Decision-gate coverage обязательна: нельзя завершить mapping, не указав, найдено ли evidence за/против существенности MCU/MBU/spatial correlation или остаётся ли этот вопрос UNKNOWN.

Количество найденных работ само по себе не является stopping criterion.

## Expected handoff from Literature Scout

Literature Scout возвращает:

1. `Task ID`, `Related RQ`, дату и использованные databases.
2. Source-access/coverage table and search log: exact strings, filters, hits, screened and included counts for every route.
3. Candidate table: RQ2 candidate ID, title, authors, year, venue, DOI/identifier, discovery route, publisher/platform, document type, peer-review status, classification and reason.
4. Список 2–5 seed papers и обоснование выбора.
5. Mandatory-anchor disposition table, including exact Zebrev arXiv-v2/RADECS version control.
6. Coverage matrix по восьми predefined evidence categories, including compatibility with the DEC-001 event/window/initial-state/domain contract and the C-RQ-05 escalation gate.
7. Candidate model-class sensitivity matrix and per-paper/model extraction fields.
8. Minimal event-representation hierarchy matrix: retained/lost dependencies, exact/bound/approximation/bias status.
9. Direct-versus-accumulation matrix and the RQ-002 [novelty-threat matrix](../novelty_workflow.md), with unknown full-text features explicit.
10. Термины/синонимы, обнаруженные в источниках, и предложения по корректировке queries/notation; no new canonical symbol is introduced without terminology registration.
11. Явные gaps, conflicts и пограничные exclusions без объявления окончательного ответа на RQ.
12. Structured `HANDOFF TO ZOTERO` для принятых records.
13. `HANDOFF TO PAPER ANALYST`: only decision-enabling papers and concrete extraction questions, including the full Zebrev-v2 target list.
14. Recommendation: stop and hand off, or one named-gap refinement. Do not request a second general cycle.
15. A bounded post-mapping note identifying the 2–5 potentially decisive sources, remaining model alternatives and the evidence gap—if any—that blocks the first quantitative prototype. This is input to the Orchestrator throughput gate, not a model-selection decision by Literature Scout.

## Post-RQ-002 throughput gate

After the mapping report is accepted, the Orchestrator applies the gate in [`research_backlog.md`](../research_backlog.md): select 2–5 decisive deep reads, bound the remaining model alternatives, define a minimal quantitative prototype and first discriminating `EXP`, and identify the intended first verifiable `RES`. Another broad search/deep-read cycle is prohibited unless a named gap blocks model selection, adequacy, validation or that first experiment.

## Execution constraints

- Не принимать Poisson process, independence или stationarity как факт без evidence.
- Do not preselect Cox, PDMP, marked processes, association, filtering or any other candidate class.
- Do not assume that marginal `q_k` is a sufficient post-mapping representation.
- Do not treat an association/conservative-bound argument as established without proof and checked assumptions.
- Не запускать eLibrary в текущем Literature Scout cycle; фиксировать `DEFERRED / UNKNOWN COVERAGE`.
- Не считать IEEE Xplore единственным достаточным source route.
- Не утверждать, что Scopus/WoS/Compendex был searched, если доступ отсутствовал; use explicit fallback labeling.
- Do not substitute another Zebrev version for exact `arXiv:1704.07271v2`; cross-link the RADECS DOI as a separate related identity pending comparison.
- Do not describe Zebrev as identical to or different from the project method before feature-by-feature full-text comparison.
- Do not generalize `CLM-002…006` beyond `PAPER-001…003` or make a mechanism-partition novelty claim before the adversarial gate.
- Do not mix inspection/maintenance/control prior art into RQ-002; the pending task is separate and non-blocking.
- Do not expand the base model to permanent faults, cumulative TID degradation, destructive SEE/SEFI or other persistent mechanisms without a separate decision.
- Do not modify DEC-001 or reopen RQ-001 from this mapping.
- Do not assign `H_req`, `ε_req`, decoder outcomes or system-visible consequences.
- Do not convert external-advisor statements into `SOURCE` evidence.
- Если decision gate срабатывает либо исключение MCU/MBU/correlation нельзя обосновать, явно рекомендовать регистрацию permanent RQ из C-RQ-05 до основной reliability model.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-002 только по результатам mapping.
- Do not create future defense propositions or publication claims as if they were obtained results.
- Do not start a second general RQ-002 cycle automatically; return a named blocking evidence gap or stop and hand off.
