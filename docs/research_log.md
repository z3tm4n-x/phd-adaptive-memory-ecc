# Research Log

Журнал **значимых** действий, решений и изменений направления исследования. Не предназначен для записи каждого мелкого действия.

## 2026-08-26

### Infrastructure initialized

- Создан private GitHub repository `z3tm4n-x/phd-adaptive-memory-ecc`.
- Репозиторий назначен master-хранилищем собственного кода, моделей, экспериментов, результатов и provenance.
- Zotero назначен master-хранилищем внешней научной литературы.
- ChatGPT Project / Work используется как orchestration/analysis layer.
- Следующий milestone: `Research Specification v1.0`.

### Canonical state synchronized

- Infrastructure setup подтверждён как завершённый.
- Zotero setup подтверждён как завершённый.
- Текущая версия Research Specification — `v0.2-draft`.
- Текущая фаза изменена на подготовку Initial RQ Package.
- Следующий gate: утверждение 3–5 priority RQ и подготовка targeted literature mapping protocol.
- Окончательные `RQ-xxx` и гипотезы пока не зарегистрированы.

### AI-agent operating model established

- Создан canonical каталог `docs/agents/` с общими правилами и role cards для Orchestrator, Literature Scout, Paper Analyst, Evidence Auditor, Scientific Reviewer, Writing & Publications и Local Research Engineer/Codex.
- Зафиксирована иерархия источников истины: Zotero — внешняя литература; GitHub — собственное состояние исследования; primary sources + Scite — evidence layer; chat — временный рабочий контекст.
- Зафиксирована граница доступа: Cloud Work имеет прямой доступ к GitHub/Scite при подключённых коннекторах, но не к локальной Zotero Desktop library и локальному engineering toolchain.
- Для операций Zotero из Cloud Work введён structured handoff в локальный Codex/Zotero.
- Кандидатные Research Questions используют `C-RQ-xx`; постоянные `RQ-xxx` назначаются только после утверждения.

### Initial Research Questions registered

- Пользователь утвердил mapping: C-RQ-01 → RQ-001, C-RQ-02 → RQ-002, C-RQ-04 → RQ-003, C-RQ-06 → RQ-004, C-RQ-10 → RQ-005.
- Пять permanent RQ зарегистрированы в `docs/questions/` со scope, exclusions, dependencies, evidence requirements, decision criteria и next actions.
- Для RQ-001 numerical reliability threshold оставлен `TBD`, если отсутствует traceable source или system requirement.
- Для RQ-002 зафиксирован decision gate: существенность MCU/MBU или spatial correlation делает permanent RQ из C-RQ-05 обязательным до основной reliability model.
- Для RQ-005 первая стадия ограничена measurable resource-cost vector; scalar objective и optimization formulation оставлены C-RQ-11.
- Гипотезы не создавались.

### Targeted literature mapping protocols prepared

- Создан каталог `docs/literature_mapping/` и отдельные protocols для RQ-001…RQ-005.
- Protocols задают databases, concept blocks, reproducible search strings, screening, seed-paper и ResearchRabbit rules, Zotero tags/handoffs, evidence и stopping criteria.
- Литературный поиск намеренно не запускался.
- Dependency-aware order: RQ-001 → RQ-002 → RQ-003 → RQ-004 → RQ-005.
- RQ-001 выбран пилотом Literature Scout, поскольку его event/metric/horizon определяют evidence targets и decision semantics для последующих reliability и ECC questions.
- Новый active gate: принять воспроизводимый Literature Scout handoff по RQ-001 перед масштабированием mapping.

## 2026-08-27

### RQ-001 Literature Scout outputs registered

- Pilot report от 2026-08-26 и completion-delta report от 2026-08-27 сохранены в `docs/literature_mapping/` без редактирования содержания.
- После delta candidate register содержит 53 записи: 24 `CORE`, 16 `RELATED`, 3 `BACKGROUND`, 10 `REJECT`.
- Выполнены исходные IEEE Xplore queries, refinement queries, Scite bibliographic/editorial-signal checks и bounded ResearchRabbit expansion.
- Abstract-level mapping не интерпретируется как paper-level evidence и не отвечает на RQ-001.

### RQ-001 discovery disposition

- Пользователь решил пока не выполнять eLibrary search, поскольку eLibrary недоступна Literature Scout.
- eLibrary зафиксирована как `DEFERRED / UNKNOWN COVERAGE`, но не как нулевой результат и не как блокер текущего gate.
- Исходный protocol stopping criterion полностью не выполнен: eLibrary отсутствует, а refinement/expansion добавили новые категории.
- Orchestrator принял discovery как `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`, поскольку все основные RQ-001 evidence dimensions имеют candidates, а оставшаяся неопределённость требует full-text extraction.
- Это явное stop-and-handoff decision, а не утверждение saturation, completeness, research gap или ответа на RQ.
- Numerical reliability threshold остаётся `TBD`; `HYP`, `CLM`, `EVD` и `RES` не создавались.

### Next gate: RQ-001 full-text extraction

- Выполнить Zotero handoffs из обоих Literature Scout reports.
- Получить verified full text для C45, C46 и C38.
- Paper Analyst создаёт отдельную Paper Card для каждого источника.
- Затем Orchestrator строит extraction matrix `event × metric × aggregation × horizon × assumptions` и определяет последующий evidence-review scope.
- RQ-002 не запускается до первичного evidence synthesis по RQ-001.
