# Targeted Literature Mapping Protocol — RQ-002

**Related RQ:** RQ-002  
**Status:** READY — SEARCH NOT STARTED — DEC-001 ALIGNED  
**Owner role:** Literature Scout  
**Prepared:** 2026-08-26

## Research Question

Какая минимальная стохастическая модель радиационно-индуцированных ошибок SRAM одновременно физически обоснована и вычислительно пригодна для моделирования накопления ошибок и адаптивного scrubbing?

## Search objective

Картировать эмпирически поддержанные model classes и допущения о arrival process, accumulation, non-stationarity, MCU/MBU и correlations, чтобы выбрать минимально достаточную error model и проверить decision gate по C-RQ-05.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-002; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

## Input contract from DEC-001

Every candidate model must be assessed against the accepted RQ-001 contract:

- primitive event `E_cap(A;t0,T)`;
- general metric `F_A(t0,T; μ_t0)`;
- explicit reporting window and initial state/distribution;
- explicitly declared controller-managed SRAM protection domain `A`;
- partitioning before aggregation when ECC, mapping `W`, arrival process, bank/block or scrubbing semantics differ;
- distinct upset-count, per-codeword exposure, reporting and mission layers;
- no automatic equivalence between `E_cap` and DUE/SDC/miscorrection/system-visible failure.

Literature Scout must identify which state variables and assumptions each model needs to calculate the accepted event/metric. Decoder-outcome semantics remain with RQ-003.


## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Target memory | SRAM; static random access memory; semiconductor memory; статическая память |
| Radiation errors | single-event upset; SEU; soft error; radiation-induced upset; одиночный сбой; радиационный сбой |
| Multiplicity | multiple-cell upset; MCU; multiple-bit upset; MBU; multi-cell upset; множественный сбой |
| Dependence | spatial correlation; temporal correlation; burst; clustering; common-mode; пространственная корреляция; временная корреляция |
| Stochastic model | Poisson process; stochastic process; probabilistic model; non-stationary; time-varying rate; intensity; стохастическая модель; интенсивность ошибок |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. SRAM AND ("single event upset" OR SEU OR "soft error") AND ("stochastic model" OR "statistical model" OR probability OR "upset rate")
2. SRAM AND ("multiple cell upset" OR MCU OR "multiple bit upset" OR MBU) AND (spatial OR correlation OR distribution OR model*)
3. (SRAM OR "semiconductor memory") AND radiation AND (nonstationary OR "non-stationary" OR "time-varying" OR intensity) AND (error OR upset)
4. ("radiation induced errors" OR "single event effects") AND SRAM AND (clustering OR burst OR correlation OR independence) AND (model OR measurement)

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## eLibrary search concepts/strings

**Current execution disposition:** `DEFERRED / UNKNOWN COVERAGE`. eLibrary is unavailable to Literature Scout and must not be queried in this cycle. The strings below are retained for a future local/authorized handoff; lack of access is not a zero-result finding and does not block the bounded IEEE Xplore/Scite/ResearchRabbit mapping.


Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (SRAM ИЛИ «статическая память») И («одиночный сбой» ИЛИ SEU ИЛИ «радиационный сбой») И («стохастическая модель» ИЛИ «вероятностная модель» ИЛИ «интенсивность сбоев»)
2. (SRAM ИЛИ «статическая оперативная память») И («множественный сбой» ИЛИ MCU ИЛИ MBU ИЛИ «многократный сбой») И («пространственная корреляция» ИЛИ кластеризация ИЛИ распределение)
3. («радиационно-индуцированные ошибки» ИЛИ «одиночные эффекты») И (память ИЛИ SRAM) И (нестационарность ИЛИ «изменяющаяся интенсивность» ИЛИ корреляция)

## Scite usage

- Использовать после первичного IEEE Xplore/eLibrary screening как secondary discovery и sanity-check layer.
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

## Target publication types

- Peer-reviewed irradiation and field-observation studies.
- Peer-reviewed reliability/radiation-effects modeling papers.
- Device- and architecture-level conference papers с данными SEU/MCU/MBU.
- Authoritative radiation test reports с traceable methods, как RELATED/BACKGROUND.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Жёсткой нижней границы нет. Первый проход: 2000–present; более ранние seminal SEU/MCU models включаются через citation chaining.

Любое изменение временного фильтра документируется; публикации не исключаются только по возрасту, если backward chaining показывает их фундаментальную роль.

## Screening procedure

1. Создать search-log entry для каждой database/query pair: database, дата, exact query, filters, hits.
2. Дедуплицировать по DOI; при отсутствии DOI — по нормализованным title + year + first author.
3. Выполнить title/metadata screening по inclusion/exclusion criteria.
4. Выполнить abstract screening без глубокого claim-level анализа.
5. Классифицировать каждый screened item как `CORE`, `RELATED`, `BACKGROUND` или `REJECT`; для `REJECT` и пограничных случаев записать reason.
6. Построить coverage matrix «evidence category → candidate papers».
7. Выбрать 2–5 seed papers по правилам ниже.
8. Выполнить ограниченное expansion через ResearchRabbit, затем повторить deduplication и screening.
9. Для принятых records подготовить structured `HANDOFF TO ZOTERO`; глубокое чтение передать Paper Analyst.

## Seed-paper selection criteria

- Источник предоставляет эмпирические distributions/rates или явно валидирует stochastic assumptions.
- Хотя бы один seed должен покрывать MCU/MBU и spatial correlation, если доступен.
- Хотя бы один seed должен рассматривать time variability/non-stationarity либо обосновывать stationarity.
- Device technology и radiation conditions позволяют оценить переносимость.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-002, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-002`.
- Required logical tags: `rq/RQ-002`, `topic/radiation-error-model`, `topic/SEU`, `topic/MCU-MBU`, `topic/spatial-correlation`, `memory/SRAM`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- Model classes для arrival, accumulation и time-varying intensity.
- Empirical basis для independence/Poisson/stationarity assumptions либо evidence против них.
- Frequency/distribution и spatial structure MCU/MBU.
- Domain of validity по device technology, geometry и radiation environment.
- Evidence, достаточный для decision gate: материально ли MCU/MBU или spatial correlation меняют структуру/вероятность reliability event RQ-001.
- State variables needed to specify `μ_t0`, including accumulated errors, word exposure ages and scrubber state where relevant.
- Evidence on when a controller-managed domain must be partitioned and how dependence across partitions is represented.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## Stopping criterion

Mapping для RQ-002 может быть остановлен, когда одновременно выполнены условия:

- все заранее определённые IEEE Xplore strings выполнены и воспроизводимо записаны; eLibrary explicitly recorded as `DEFERRED / UNKNOWN COVERAGE` under the current access constraint;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены candidate table, gaps и handoffs.

Decision-gate coverage обязательна: нельзя завершить mapping, не указав, найдено ли evidence за/против существенности MCU/MBU/spatial correlation или остаётся ли этот вопрос UNKNOWN.

Количество найденных работ само по себе не является stopping criterion.

## Expected handoff from Literature Scout

Literature Scout возвращает:

1. `Task ID`, `Related RQ`, дату и использованные databases.
2. Search log: exact strings, filters, hits, screened и included counts.
3. Candidate table: title, authors, year, venue, DOI/identifier, discovery route, classification и reason.
4. Список 2–5 seed papers и обоснование выбора.
5. Coverage matrix по требуемым evidence categories, including compatibility with the DEC-001 event/window/initial-state/domain contract.
6. Термины/синонимы, обнаруженные в источниках, и предложения по корректировке queries.
7. Явные gaps, conflicts и пограничные exclusions без объявления окончательного ответа на RQ.
8. Structured `HANDOFF TO ZOTERO` для принятых records.
9. `HANDOFF TO PAPER ANALYST`: приоритетные papers и конкретные extraction questions.
10. Рекомендацию: stop, refine protocol либо выполнить ещё один ограниченный search cycle.

## Execution constraints

- Не принимать Poisson process, independence или stationarity как факт без evidence.
- Не запускать eLibrary в текущем Literature Scout cycle; фиксировать `DEFERRED / UNKNOWN COVERAGE`.
- Если decision gate срабатывает либо исключение MCU/MBU/correlation нельзя обосновать, явно рекомендовать регистрацию permanent RQ из C-RQ-05 до основной reliability model.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-002 только по результатам mapping.
