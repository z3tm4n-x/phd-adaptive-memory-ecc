# Targeted Literature Mapping Protocol — RQ-004

**Related RQ:** RQ-004  
**Status:** READY — SEARCH NOT STARTED  
**Owner role:** Literature Scout  
**Prepared:** 2026-08-26

## Research Question

Какие online observables доступны для оценки текущей интенсивности ошибок или риска для ECC-protected SRAM, и какую информацию, с какой задержкой и неопределённостью, даёт каждый наблюдаемый сигнал?

## Search objective

Найти реализуемые internal и external observation channels и описать measured quantity, availability, update rate, latency, uncertainty и связь с latent error/radiation state.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-004; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Internal ECC signals | corrected error counter; syndrome counter; ECC telemetry; EDAC counter; scrub result; счётчик исправленных ошибок; синдром |
| Memory control | memory scrubber; memory controller; fault management; health monitoring; контроллер памяти; скраббинг |
| External radiation signals | radiation monitor; dosimeter; particle detector; space weather; radiation telemetry; дозиметр; датчик радиации |
| Estimation target | error rate; upset rate; soft error rate; radiation intensity; risk estimate; интенсивность ошибок; оценка риска |
| Signal quality | latency; update rate; noise; uncertainty; observability; availability; задержка; частота обновления; наблюдаемость |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. ("memory scrubbing" OR scrubber) AND (adaptive OR dynamic) AND ("error rate" OR monitor OR counter OR telemetry)
2. SRAM AND (ECC OR EDAC) AND ("corrected error counter" OR syndrome OR "error counter" OR telemetry)
3. (radiation OR "space systems") AND ("memory controller" OR "fault management") AND (monitor OR sensor OR dosimeter OR "error rate estimation")
4. ("radiation monitor" OR dosimeter OR "particle detector") AND (onboard OR "real time" OR telemetry) AND (memory OR "soft error" OR upset)

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## eLibrary search concepts/strings

Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (скраббинг ИЛИ «контроллер памяти») И (адаптивный ИЛИ динамический) И («счётчик ошибок» ИЛИ синдром ИЛИ телеметрия ИЛИ «интенсивность ошибок»)
2. (SRAM ИЛИ «статическая память») И (ECC ИЛИ EDAC ИЛИ «коррекция ошибок») И («исправленные ошибки» ИЛИ «счётчик синдромов» ИЛИ мониторинг)
3. («радиационный монитор» ИЛИ дозиметр ИЛИ «детектор частиц») И (бортовой ИЛИ «реальное время» ИЛИ телеметрия) И (память ИЛИ сбои)

## Scite usage

- Использовать после первичного IEEE Xplore/eLibrary screening как secondary discovery и sanity-check layer.
- Для каждого seed paper проверить bibliographic identity и наличие correction/retraction notice.
- Просмотреть supporting/contrasting citation signals только для выбора follow-up sources и обнаружения спорных допущений.
- Добавлять peer-reviewed related works в candidate list с пометкой discovery route = Scite.
- Не считать Scite заменой primary source, exhaustive search или отдельным evidence audit.

## Inclusion criteria

- Источник описывает online- или near-online signal, доступный контроллеру/системе.
- Можно определить measured quantity, interface/location и хотя бы одну temporal/quality characteristic.
- Связь с memory error rate, radiation intensity или risk сформулирована явно либо проверяема.
- Архитектурная реализуемость канала показана или достаточно описана.
- Источник позволяет связать хотя бы один извлекаемый элемент evidence с RQ-004.
- Для peer-reviewed работ доступны достаточные metadata и abstract; необходимость full text отмечается для Paper Analyst.
- Язык: английский или русский.

## Exclusion criteria

- Только post-mission/offline radiation reconstruction без online interface.
- Предположение о доступности сигнала без описания sensor/controller path.
- Работа только об estimator algorithm без определения исходных observables.
- COSRAD или иная dataset названа как прямая online telemetry без evidence.
- Secondary summary без traceable primary source, если он используется как доказательство.
- Публикация, не позволяющая определить объект памяти, error-protection context или релевантный measurement/model.
- Дубликат; сохраняется одна canonical record, а варианты metadata связываются в screening log.

## Target publication types

- Peer-reviewed memory-controller, scrubber and fault-management architecture papers.
- Peer-reviewed radiation-monitoring and onboard dosimetry papers.
- Peer-reviewed online error-rate/risk estimation studies.
- Authoritative instrument/interface documents как RELATED/BACKGROUND.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Первый проход: 2000–present для современных controller/telemetry interfaces. Более ранние работы включаются только как foundational architecture или measurement method.

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

- Источник раскрывает реальный observable и путь его получения, а не только предлагает latent variable.
- Можно извлечь update rate/latency/noise/availability либо явно отметить отсутствие этих данных.
- Seeds в совокупности покрывают internal ECC/scrub telemetry и external radiation sensing.
- Предпочтение sources с system interface или экспериментальной validation.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-004, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-004`.
- Required logical tags: `rq/RQ-004`, `topic/online-observation`, `topic/error-counters`, `topic/radiation-monitoring`, `topic/error-rate-estimation`, `memory/SRAM`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- Перечень internal и external channels.
- Measured quantity, availability, update rate, latency, noise/uncertainty и interface для каждого channel.
- Связь observable с latent variable error model RQ-002.
- Evidence о достаточности internal ECC/scrub signals либо необходимости external sensor/model.
- Ограничения portability и реализуемости для последующей RTL/FPGA architecture.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## Stopping criterion

Mapping для RQ-004 может быть остановлен, когда одновременно выполнены условия:

- все заранее определённые IEEE Xplore и eLibrary strings выполнены и воспроизводимо записаны;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены candidate table, gaps и handoffs.

Mapping должен завершиться channel matrix с классификацией feasible/unproven/out of scope; отсутствие данных о latency или uncertainty регистрируется как gap, а не заполняется предположением.

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

- Не выбирать estimator algorithm или adaptive policy.
- Не считать forecast/model output измерением и не считать external dataset online source без interface evidence.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-004 только по результатам mapping.
