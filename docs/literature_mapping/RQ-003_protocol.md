# Targeted Literature Mapping Protocol — RQ-003

**Related RQ:** RQ-003  
**Status:** `ACTIVE NEXT / PRE-LAUNCH REVISION REQUIRED / SEARCH NOT STARTED`<br>
**Owner role:** Literature Scout  
**Prepared:** 2026-08-26
**Gate update:** 2026-08-31 after EXP-001 Scientific Review 01 and the bounded Chen Evidence Audit

## Research Question

Какая абстракция ECC и какой стартовый класс кодов — SEC, SEC-DED либо параметризованное обобщение — должны использоваться как baseline для исследования adaptive SRAM scrubbing, и какие состояния/исходы декодера должны быть представлены явно?

## Search objective

Картировать ECC abstractions, code classes, codeword parameters и decoder outcome semantics, используемые в radiation-tolerant SRAM и scrubbing models, чтобы обоснованно выбрать baseline.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-003; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

Before launch, the Orchestrator must align the database routes and extraction
contract with DEC-001/DEC-002, accepted RQ-002/RQ-006 evidence and the Chen
comparison. eLibrary is `DEFERRED / UNAVAILABLE TO LITERATURE SCOUT`; the Russian
query concepts below are retained for a later authorized actor and are not a
completion requirement for this Scout cycle.

## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Target memory | SRAM; static random access memory; radiation-tolerant memory; космическая память |
| Code class | SEC; SEC-DED; SECDED; Hamming code; BCH; EDAC; код Хэмминга; коррекция одиночной ошибки |
| Decoder outcome | correctable; detected uncorrectable; undetected error; miscorrection; syndrome; исправимая; обнаруженная неисправимая; необнаруженная ошибка |
| Organization | codeword; data bits; parity bits; check bits; word width; кодовое слово; проверочные разряды |
| Maintenance context | memory scrubbing; scrubber; read-correct-rewrite; скраббинг памяти |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. SRAM AND (radiation OR "single event upset") AND (SEC OR SEC-DED OR SECDED OR "single error correction")
2. ("radiation tolerant memory" OR "spaceborne memory") AND ("error correcting code" OR ECC OR EDAC) AND (scrub* OR "memory scrubbing")
3. SRAM AND (ECC OR "error correction") AND (codeword OR decoder OR syndrome) AND ("uncorrectable error" OR miscorrection OR "undetected error")
4. (SEC-DED OR SECDED OR "Hamming code") AND memory AND (reliability OR radiation OR scrubbing) AND (decoder OR codeword)

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## eLibrary search concepts/strings — deferred

Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (SRAM ИЛИ «статическая память») И (SEC ИЛИ SEC-DED ИЛИ «код Хэмминга» ИЛИ EDAC) И (радиация ИЛИ «одиночный сбой»)
2. («радиационно-стойкая память» ИЛИ «космическая память») И («коррекция ошибок» ИЛИ ECC) И (скраббинг ИЛИ «восстановление памяти»)
3. («кодовое слово» ИЛИ декодер ИЛИ синдром) И (SRAM ИЛИ память) И («неисправимая ошибка» ИЛИ «необнаруженная ошибка» ИЛИ «ошибка коррекции»)

## Scite usage

- Использовать после первичного IEEE Xplore/eLibrary screening как secondary discovery и sanity-check layer.
- Для каждого seed paper проверить bibliographic identity и наличие correction/retraction notice.
- Просмотреть supporting/contrasting citation signals только для выбора follow-up sources и обнаружения спорных допущений.
- Добавлять peer-reviewed related works в candidate list с пометкой discovery route = Scite.
- Не считать Scite заменой primary source, exhaustive search или отдельным evidence audit.

## Inclusion criteria

- ECC применяется или моделируется для SRAM/radiation-tolerant memory.
- Можно извлечь correction/detection capability, codeword parameters и/или decoder outcomes.
- Работа связывает ECC semantics с reliability, scrubbing или error accumulation.
- Ограничения, miscorrection/undetected behavior или generalization boundaries описаны явно.
- Источник позволяет связать хотя бы один извлекаемый элемент evidence с RQ-003.
- Для peer-reviewed работ доступны достаточные metadata и abstract; необходимость full text отмечается для Paper Analyst.
- Язык: английский или русский.

## Exclusion criteria

- Работа только о generic channel coding без memory context.
- Только gate-level encoder/decoder optimization без доступной semantics для reliability model.
- ECC class назван, но параметры и outcomes не извлекаются.
- Claims о superior code без сопоставимого error model или resource context.
- Secondary summary без traceable primary source, если он используется как доказательство.
- Публикация, не позволяющая определить объект памяти, error-protection context или релевантный measurement/model.
- Дубликат; сохраняется одна canonical record, а варианты metadata связываются в screening log.

## Target publication types

- Peer-reviewed fault-tolerant memory and radiation-effects papers.
- Peer-reviewed ECC/reliability modeling papers.
- Memory-controller or scrubber architecture papers с явными decoder semantics.
- Authoritative standards/architecture documents как BACKGROUND.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Жёсткой нижней границы нет. Первый проход: 2000–present; более ранние foundational SEC/SEC-DED works включаются, если на них опираются современные memory models.

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

- Источник явно связывает code capability и decoder outcomes с reliability event.
- Параметры codeword и assumptions доступны для извлечения.
- Seeds в совокупности сравнивают SEC, SEC-DED или parameterized abstraction.
- Предпочтение работам, отличающим detected-uncorrectable, undetected и miscorrection outcomes.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-003, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-003`.
- Required logical tags: `rq/RQ-003`, `topic/ECC`, `topic/SEC-DED`, `topic/decoder-outcomes`, `topic/memory-scrubbing`, `memory/SRAM`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- ECC abstractions и минимальный набор code parameters для reliability model.
- Decoder states/outcomes и их связь с reliability event RQ-001.
- Фактическое применение и ограничения SEC и SEC-DED в radiation-tolerant SRAM.
- Evidence за необходимость parameterized/generalized code abstraction.
- Влияние error multiplicity/correlation из RQ-002 на допустимый baseline.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## Stopping criterion

Mapping для RQ-003 может быть остановлен, когда одновременно выполнены условия:

- все authorized pre-launch database/search routes выполнены и воспроизводимо записаны; eLibrary is not a completion requirement while unavailable to Literature Scout;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены candidate table, gaps и handoffs.

RQ-006 is now permanently registered. Mapping must preserve its `W`, interleaving
and joint post-`W` dependencies rather than treating the former escalation as
unresolved.

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

- Не выбирать ECC baseline по привычке или одной implementation paper.
- Отделять abstract code capability от конкретной RTL architecture и от adaptive ECC switching.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-003 только по результатам mapping.
