# Targeted Literature Mapping Protocol — RQ-005

**Related RQ:** RQ-005  
**Status:** READY — SEARCH NOT STARTED  
**Owner role:** Literature Scout  
**Prepared:** 2026-08-26

## Research Question

Какие измеримые компоненты должны входить в первоначальный resource-cost vector adaptive SRAM scrubbing, чтобы их можно было последовательно оценивать в analytical model, simulation и RTL/FPGA evaluation?

## Search objective

Картировать измеримые resource/cost components, operational definitions, units/proxies и measurement stages, не выбирая scalar objective или произвольные weights.

Mapping должен уменьшить неопределённость, необходимую для принятия решения по RQ-005; он не должен превращаться в общий обзор темы и не считается ответом на RQ.

## Concepts and synonyms

| Concept | English/Russian synonyms and related terms |
|---|---|
| Scrubbing activity | memory scrubbing; scrub frequency; scrub interval; read-correct-rewrite; scrub operations; период скраббинга |
| Memory service cost | bandwidth; traffic; bus occupancy; access latency; interference; производительность; задержка; пропускная способность |
| Energy/power | energy per access; dynamic power; power overhead; energy proxy; энергопотребление; мощность |
| Hardware resources | FPGA; RTL; LUT; flip-flop; BRAM; area; timing; controller state; аппаратные ресурсы |
| Optimization representation | cost vector; resource vector; multi-objective; trade-off; metric; вектор затрат; критерии оптимизации |

Термины используются как concept blocks. Literature Scout может менять только синтаксис конкретной базы; смысловые блоки, фактически выполненная строка и причина изменения фиксируются в search log.

## IEEE Xplore search strings

Запускать строки отдельно, начиная с наиболее специфичной. Точный executed query, дата, filters и число результатов сохраняются в search log.

1. ("memory scrubbing" OR scrubber) AND (overhead OR bandwidth OR latency OR energy OR power OR performance)
2. (SRAM AND (ECC OR EDAC)) AND (scrub* OR "error correction") AND ("memory bandwidth" OR "access latency" OR energy OR power)
3. ("adaptive memory scrubbing" OR "dynamic scrubbing") AND (cost OR overhead OR resource OR FPGA OR hardware)
4. ("memory controller" OR "ECC controller") AND FPGA AND (area OR LUT OR timing OR power) AND (scrub* OR reliability)

Если интерфейс не поддерживает данную форму Boolean syntax, строка разбивается на эквивалентные запросы без смыслового расширения; все выполненные варианты документируются.

## eLibrary search concepts/strings

Искать по русским и английским терминам; при ограничениях интерфейса выполнять concept blocks отдельно и записывать точную фактическую строку.

1. (скраббинг ИЛИ «восстановление памяти») И (накладные расходы ИЛИ «пропускная способность» ИЛИ задержка ИЛИ энергия ИЛИ производительность)
2. (SRAM ИЛИ «статическая память») И (ECC ИЛИ EDAC) И (скраббинг ИЛИ «коррекция ошибок») И (трафик ИЛИ мощность ИЛИ ресурсы)
3. («адаптивный скраббинг» ИЛИ «динамический скраббинг») И (стоимость ИЛИ ресурсы ИЛИ FPGA ИЛИ RTL ИЛИ оптимизация)

## Scite usage

- Использовать после первичного IEEE Xplore/eLibrary screening как secondary discovery и sanity-check layer.
- Для каждого seed paper проверить bibliographic identity и наличие correction/retraction notice.
- Просмотреть supporting/contrasting citation signals только для выбора follow-up sources и обнаружения спорных допущений.
- Добавлять peer-reviewed related works в candidate list с пометкой discovery route = Scite.
- Не считать Scite заменой primary source, exhaustive search или отдельным evidence audit.

## Inclusion criteria

- Источник задаёт хотя бы одну измеримую component или proxy для scrubbing/ECC/controller overhead.
- Можно извлечь operational definition, unit, measurement method или hardware report field.
- Метрика применима хотя бы к одному из stages: analytical model, simulation, RTL или FPGA.
- Описан context, позволяющий понять нормализацию и границы сравнения.
- Источник позволяет связать хотя бы один извлекаемый элемент evidence с RQ-005.
- Для peer-reviewed работ доступны достаточные metadata и abstract; необходимость full text отмечается для Paper Analyst.
- Язык: английский или русский.

## Exclusion criteria

- Используется только неопределённое слово cost/overhead без измеримой величины.
- Scalar objective или weights предложены без разложения на измеримые components.
- Platform-specific number без architecture, unit или measurement method.
- Reliability metric выдана за resource cost без явного разделения constraint и cost.
- Secondary summary без traceable primary source, если он используется как доказательство.
- Публикация, не позволяющая определить объект памяти, error-protection context или релевантный measurement/model.
- Дубликат; сохраняется одна canonical record, а варианты metadata связываются в screening log.

## Target publication types

- Peer-reviewed memory-scrubbing/ECC performance and architecture papers.
- Peer-reviewed energy, bandwidth, latency and interference modeling papers.
- Peer-reviewed RTL/FPGA implementation and evaluation reports.
- Authoritative FPGA/tool measurement documentation как BACKGROUND для definitions.

Патенты, theses, technical reports и standards допускаются как BACKGROUND или источник требований/архитектуры, но не заменяют peer-reviewed primary evidence без явного обоснования.

## Target time range

Первый проход: 2000–present для современных SRAM/FPGA measurement practices. Более ранние seminal cost models включаются через citations, если их definitions сохраняются.

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

- Источник предоставляет хотя бы одну operationally defined component с unit/proxy.
- Seeds в совокупности покрывают runtime service costs и hardware implementation resources.
- Есть достаточный context для переноса между analytical, simulation и RTL/FPGA stages.
- Предпочтение работам, сохраняющим vector/trade-off representation без преждевременной scalarization.
- Peer-reviewed primary or methods paper с устойчивой bibliographic identity.
- Прямое соответствие RQ-005, а не только общая тематическая близость.
- Достаточная прозрачность assumptions, methods или measured quantities.
- Совокупность 2–5 seeds должна покрывать разные релевантные подходы, а не дублировать один cluster.

## ResearchRabbit expansion rule

ResearchRabbit используется только после выбора 2–5 strong seeds. Для каждого seed выполнить один ограниченный проход по backward citations, forward citations и closely related works. Candidate добавляется, только если проходит inclusion criteria и добавляет новую model class, definition, observable, metric, method или контрастирующее допущение. Discovery route и parent seed фиксируются. Expansion прекращается, когда два последовательных seed/expansion batches дают только duplicates, уже покрытые подходы либо out-of-scope records.

## Zotero destination/tags

- Target collection: `DISSERTATION / RQ / RQ-005`.
- Required logical tags: `rq/RQ-005`, `topic/resource-cost-vector`, `topic/scrubbing-overhead`, `topic/memory-bandwidth`, `topic/energy-power`, `topic/RTL-FPGA`, а также одна screening classification: `class/CORE`, `class/RELATED` или `class/BACKGROUND`.
- Local Zotero actor должен сначала сопоставить этот destination с существующей canonical collection/tag taxonomy и не создавать параллельные дублирующие деревья.
- Перед импортом выполнить deduplication; сохранить DOI, полные metadata, abstract и PDF/link при доступности.
- Cloud Literature Scout не утверждает, что запись уже находится в Zotero: он формирует structured `HANDOFF TO ZOTERO`.

## Evidence required to answer RQ

- Candidate components: scrub activity, traffic/bandwidth, latency/interference, energy/power, performance, hardware resources и controller-state overhead.
- Operational definition, unit либо proxy и measurement stage для каждой component.
- Нормализация, platform dependency и uncertainty.
- Evidence о компонентах, необходимых для честного сравнения baselines и adaptive strategies.
- Разделение reliability constraint и resource-cost vector.

Literature Scout только находит и классифицирует источники. Claim extraction выполняет Paper Analyst; достаточность и конфликты evidence проверяет Evidence Auditor.

## Stopping criterion

Mapping для RQ-005 может быть остановлен, когда одновременно выполнены условия:

- все заранее определённые IEEE Xplore и eLibrary strings выполнены и воспроизводимо записаны;
- каждая evidence category имеет хотя бы один plausible candidate либо явно зарегистрированный gap;
- выбраны 2–5 strong seeds либо документировано, почему это невозможно;
- выполнен предусмотренный ResearchRabbit expansion;
- два последовательных search/expansion batches не добавили новую model/definition/measurement category;
- подготовлены candidate table, gaps и handoffs.

Mapping не должен завершаться scalar objective. Если scalarization встречается в literature, фиксируются только исходные components и assumptions; форма optimization передаётся C-RQ-11.

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

- Не назначать weights и не выбирать scalar objective function.
- Не исключать component только ради удобства измерения; отсутствие method регистрировать как gap.
- Не создавать HYP, CLM или EVD на стадии discovery.
- Не изменять `docs/research_spec.md`.
- Не объявлять novelty/gap или ответ на RQ-005 только по результатам mapping.
