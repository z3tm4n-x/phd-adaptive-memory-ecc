# Targeted Literature Mapping Protocol — RQ-001

**Related RQ:** RQ-001  
**Status:** EXECUTED — SUFFICIENT FOR PAPER ANALYSIS; NOT EXHAUSTIVE  
**Owner role:** Literature Scout  
**Prepared:** 2026-08-26  
**Disposition reviewed:** 2026-08-27

## Research Question

Как должны быть определены reliability event, соответствующая метрика, уровень агрегации и временной горизонт для SRAM, защищённой ECC и периодическим scrubbing, чтобы сформулировать проверяемое ограничение надёжности?

## Search objective

Найти первичные модели и определения, позволяющие формально выбрать reliability event, metric, aggregation level и evaluation horizon без изобретения численного requirement.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-001; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Target memory | SRAM; static random access memory; semiconductor memory; статическая оперативная память; статическая память |
| Protection | error-correcting code; ECC; EDAC; error correction; помехоустойчивое кодирование; коррекция ошибок |
| Maintenance | memory scrubbing; scrub cycle; periodic scrubbing; read-correct-rewrite; скраббинг; периодическое восстановление памяти |
| Reliability event | uncorrectable error; uncorrectable word; detected uncorrectable error; failure event; data loss; неисправимая ошибка; отказ |
| Metric/horizon | failure probability; reliability; risk; event rate; mission time; time interval; codeword; bank; array; вероятность отказа; время миссии |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. "SRAM" AND ("error correcting code" OR ECC OR EDAC) AND (scrub* OR "memory scrubbing") AND ("uncorrectable error" OR failure OR reliability)
2. ("radiation tolerant memory" OR "spaceborne memory") AND (ECC OR "error correction") AND (scrub* OR "memory scrubbing") AND ("failure probability" OR "error probability" OR reliability)
3. ("memory reliability model" OR "reliability modeling") AND (ECC OR "error correcting code") AND (codeword OR bank OR "memory array") AND ("mission time" OR "time interval" OR horizon)
4. (SRAM OR "semiconductor memory") AND (scrub* OR "error correction") AND ("data loss probability" OR "uncorrectable word" OR "reliability event")

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## eLibrary search concepts/strings

Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (SRAM ИЛИ «статическая оперативная память») И («коррекция ошибок» ИЛИ ECC ИЛИ EDAC) И (скраббинг ИЛИ «восстановление памяти») И («неисправимая ошибка» ИЛИ «вероятность отказа» ИЛИ надежность)
2. («радиационно-стойкая память» ИЛИ «космическая память») И («помехоустойчивое кодирование» ИЛИ «коррекция ошибок») И (скраббинг ИЛИ регенерация) И (отказ ИЛИ надежность)
3. («модель надежности памяти» ИЛИ «вероятность потери данных») И (кодовое слово ИЛИ банк ИЛИ массив) И («время миссии» ИЛИ «временной интервал»)

## Scite usage

- Использовать после первичного IEEE Xplore/eLibrary screening как secondary discovery и sanity-check layer.
- Для каждого seed paper проверить bibliographic identity и наличие correction/retraction notice.
- Просмотреть supporting/contrasting citation signals только для выбора follow-up sources и обнаружения спорных допущений.
- Добавлять peer-reviewed related works в candidate list с пометкой discovery route = Scite.
- Не считать Scite заменой primary source, exhaustive search или отдельным evidence audit.

## Inclusion criteria

- Модель или архитектура относится к SRAM либо переносимость на SRAM сформулирована явно.
- ECC и/или scrubbing входят в исследуемый protection mechanism.
- Явно определены failure/reliability event, metric, aggregation level или time horizon.
- Допущения и уровень анализа можно извлечь из primary source.
- Источник позволяет связать хотя бы один извлекаемый элемент evidence с RQ-001.
- Для peer-reviewed работ доступны достаточные metadata и abstract; необходимость full text отмечается для Paper Analyst.
- Язык: английский или русский.

## Exclusion criteria

- Работа сообщает только raw bit error rate без связи с system/codeword-level reliability event.
- Численный threshold приведён без traceable system/mission requirement.
- Объектом является исключительно storage/DRAM/flash, а переносимость на SRAM не обоснована.
- Только implementation result без определения reliability outcome.
- Secondary summary без traceable primary source, если он используется как доказательство.
- Публикация, не позволяющая определить объект памяти, error-protection context или релевантный measurement/model.
- Дубликат; сохраняется одна canonical record, а варианты metadata связываются в screening log.

## Target publication types

- Peer-reviewed journal articles по reliability modeling и fault-tolerant memories.
- Peer-reviewed conference papers по ECC-protected memory, scrubbing и space/radiation systems.
- Primary system/mission requirement documents или standards с явными reliability definitions.
- Seminal methods papers, определяющие используемую reliability metric.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Жёсткой нижней границы нет. Первый проход: 2000–present для современных SRAM/ECC/scrubbing; более ранние seminal models включаются через backward chaining.

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

- Источник формально задаёт событие и хотя бы одну из осей: metric, aggregation или horizon.
- Модель явно связывает ECC/scrubbing с вероятностью либо частотой failure outcome.
- Предпочтение работам, позволяющим сравнить разные определения, а не только подставить параметры.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-001, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-001`.
- Required logical tags: `rq/RQ-001`, `topic/reliability-event`, `topic/reliability-metric`, `topic/memory-scrubbing`, `memory/SRAM`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- Альтернативные формальные определения reliability/failure event.
- Метрики и правила агрегирования от bit/codeword к bank/array/system.
- Выбор и обоснование scrub, operating или mission horizon.
- Связь correctable/detectable-uncorrectable/other outcomes с событием.
- Traceable system/mission requirements, если они задают numerical threshold.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## Stopping criterion

Mapping для RQ-001 может быть остановлен, когда одновременно выполнены условия:

- все заранее определённые IEEE Xplore и eLibrary strings выполнены и воспроизводимо записаны;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены candidate table, gaps и handoffs.

Если numerical threshold не найден в traceable requirements, результатом mapping должен быть явный `TBD`, а не придуманное значение.

Количество найденных работ само по себе не является stopping criterion.

## Expected handoff from Literature Scout

Literature Scout возвращает:

1. `Task ID`, `Related RQ`, дату и использованные databases.
2. Search log: exact strings, filters, hits, screened и included counts.
3. Candidate table: title, authors, year, venue, DOI/identifier, discovery route, classification и reason.
4. Список 2–5 seed papers и обоснование выбора.
5. Coverage matrix по требуемым evidence categories.
6. Термины/синонимы, обнаруженные в источниках, и предложения по корректировке queries.
7. Явные gaps, conflicts и пограничные exclusions без объявления окончательного ответа на RQ.
8. Structured `HANDOFF TO ZOTERO` для принятых records.
9. `HANDOFF TO PAPER ANALYST`: приоритетные papers и конкретные extraction questions.
10. Рекомендацию: stop, refine protocol либо выполнить ещё один ограниченный search cycle.

## Execution constraints

- Не назначать numerical reliability threshold без traceable source или system requirement.
- Разделять SOURCE definitions и INFERENCE о пригодности для проекта.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-001 только по результатам mapping.


## Execution record and orchestration disposition

Canonical Literature Scout outputs:

- [Pilot report](RQ-001_literature_mapping_pilot_2026-08-26.md) — executed 2026-08-26;
- [Completion delta](RQ-001_literature_mapping_completion_delta_2026-08-27.md) — executed 2026-08-27.

Cumulative screened register after the completion delta:

- `CORE`: 24;
- `RELATED`: 16;
- `BACKGROUND`: 3;
- `REJECT`: 10;
- total candidates: 53.

**Discovery disposition:** `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`.

The original stopping criterion was not fully met: eLibrary queries were not executed and the completed refinement/expansion batches added new categories. On 2026-08-27 the user explicitly deferred eLibrary because it is unavailable to Literature Scout. The Orchestrator therefore accepted the current mapping as sufficient for full-text extraction, while preserving the following limitations:

- no claim of search saturation or exhaustiveness is made;
- Russian/eLibrary coverage remains unknown;
- the mapping does not answer RQ-001;
- event, metric, aggregation and horizon remain `UNKNOWN`;
- numerical reliability threshold remains `TBD`;
- no `HYP`, `CLM` or `EVD` is created from abstract-level screening.

This is an explicit orchestration stop-and-handoff decision, not evidence that no additional literature exists. Discovery may be reopened only when Paper Analyst identifies a specific missing definition/model, or when eLibrary access becomes available.

**Next handoff:** after Zotero reconciliation and full-text acquisition, Paper Analyst creates separate Paper Cards for C45, C46 and C38.
