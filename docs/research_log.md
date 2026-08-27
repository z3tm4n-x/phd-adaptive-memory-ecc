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
### RQ-001 Paper Cards formally accepted

- Research Orchestrator проверил три draft full-text Paper Cards по 19-section contract, source/inference discipline, page/equation provenance, scope limits и relevance to RQ-001.
- C45 принят как `PAPER-001` (`CORE`): Tausch, 2009.
- C46 принят как `PAPER-002` (`CORE`): Baeg, Wen, Wong, 2009.
- C38 принят как `PAPER-003` (`CORE`): Lee, Baeg, Reviriego, 2011.
- Внутренняя неоднозначность row-level wording в `PAPER-003` сохранена явно и не разрешена предположением.
- Acceptance относится к качеству аналитических карт; stochastic, architecture, mapping, illustrative-threshold и scrubbing assumptions публикаций не стали допущениями проекта.

### RQ-001 initial cross-paper evidence synthesis

- Создана canonical matrix `event × metric/units × aggregation × independent variable × horizon × ECC/decoder × scrubbing × statistics × mapping × mechanism × double-counting × limitations`.
- Зафиксировано согласие трёх papers относительно existential codeword event beyond correction capability, но выявлены несовместимые aggregate objects и horizons: upset count, elapsed time и deterministic scrub interval.
- Зафиксировано, что C45 исключает harmful direct MBU из основной формулы, а C46/C38 объединяют MCU-bearing arrivals и independent accumulation без сохранения causal provenance.
- Initial synthesis признан возможным, но final answer на RQ-001 не сформулирован; numerical reliability threshold остаётся `TBD`.
- До claim-level Evidence Auditor review дополнительные Paper Cards не требуются.

### Next gate: RQ-001 claim-level evidence audit

- Для Evidence Auditor отобраны 12 atomic candidate claims `RQ001-EA-CAND-01…12`; permanent `CLM-xxx` не создавались.
- Аудит должен проверить actual citation context, corrections/editorial concerns, scope match и strongest supporting/limiting evidence.
- RQ-001 переведён в `INVESTIGATING`; RQ-002 остаётся в очереди до review этого gate.

### RQ-001 Evidence Audit accepted with limitation

- Canonical Evidence Audit `RQ-001-EVIDENCE-AUDIT-01` принят после Orchestrator review.
- Поддержаны `RQ001-EA-CAND-01…09`, `11` и `12` в зафиксированных scope и confidence.
- `RQ001-EA-CAND-10` признан `PARTIALLY_SUPPORTED` и отложен: отсутствие word-specific exposure-age state подтверждено, но synchronous/effective global-reset interpretation не принято.
- Scite statement counts не использованы как evidence; contextual audit sources требуют Zotero reconciliation до цитирования в publication text.
- Опечатка `seven exact claims` в initial synthesis исправлена на `twelve exact claims`.
- Новые Paper Cards, literature search, `EVD`, `HYP` и `RES` не создавались.

### RQ-001 permanent claims registered

- `CLM-001` — count horizon requires arrival and repair semantics before time interpretation.
- `CLM-002` — harmful same-particle MBU is outside the main PAPER-001 equation.
- `CLM-003`/`CLM-004` — PAPER-002/PAPER-003 totals do not preserve failed-word mechanism provenance.
- `CLM-005`/`CLM-006` — adding an unpartitioned direct-MCU term overlaps those totals under matched event, scope, horizon and units.
- `CLM-007` — PAPER-002 upper-bound reading is conditional on MCU span relative to interleaving distance.
- `CLM-008` — the audited papers model multiplicity beyond ECC capability, not decoder or service outcome.
- Candidate facts 01–03 remain traceable through the Paper Cards and matrix rather than redundant permanent claims.

### Next gate: RQ-001 provisional definition approval

- Подготовлен `docs/evidence_synthesis/RQ-001_provisional_definition_package.md`.
- Package proposes `E_cap(A,H)`, `F_A(H)`, a controller-protected SRAM aggregate, layered horizon semantics and separation from DUE/SDC/system consequences.
- `H_req` and `ε_req` remain `TBD`; illustrative values from the papers are not project requirements.
- Until explicit approval, RQ-001 remains `INVESTIGATING` and RQ-002 remains queued.

### DEC-001 accepted — RQ-001 working reliability contract

- Пользователь утвердил все шесть решений RQ-001 с уточнениями notation and aggregation.
- `E_cap` принят как primitive ECC-capability-exceedance event; automatic equivalence to DUE, SDC, miscorrection or system-visible failure запрещена.
- General reporting window фиксируется как \(H(t_0,T)=[t_0,t_0+T]\); metric сохраняет start time и declared initial state/distribution: \(F_A(t_0,T;\mu_{t_0})\).
- `F_A(T)` разрешена только как сокращённая форма при явном time origin и initial state.
- Default aggregate — explicitly declared controller-managed protection domain \(A\); heterogeneous ECC, \(W\), arrival, bank/block or scrubbing semantics require partitioning before quantitative aggregation.
- Per-codeword/sequential exposure semantics classified as `WORKING DEFINITION / MODELING REQUIREMENT`, not literature fact; CAND-10 remains deferred.
- Decoder/system outcomes, \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) remain `OPEN/TBD`.
- Decision зарегистрирован как `DEC-001`; numerical reliability requirement, `HYP`, `EVD` and `RES` не создавались.

### RQ-001 partial disposition and RQ-002 gate opening

- RQ-001 переведён в `PARTIALLY ANSWERED / OPEN DEPENDENCIES` and remains open.
- Research Specification advanced to `v0.3-draft` to record the accepted working contract.
- RQ-002 gate открыт with DEC-001 as its event/metric/domain input contract.
- RQ-003 retains responsibility for decoder-outcome semantics.
- RQ-002 protocol aligned with DEC-001; eLibrary explicitly remains `DEFERRED / UNKNOWN COVERAGE` for Literature Scout.
- RQ-002 literature search was not started in this recording step.
- Next action: issue the exact Literature Scout handoff from `docs/literature_mapping/RQ-002_protocol.md` and apply the C-RQ-05 MCU/MBU/spatial-correlation escalation rule.

### RQ-002 protocol expanded before Literature Scout launch

- IEEE Xplore retained as mandatory anchor but rejected as the sole sufficient database route for RQ-002.
- Added a mandatory independent cross-publisher route: Scopus preferred; Web of Science or Compendex/Inspec accepted substitutes.
- Added public Crossref/OpenAlex fallback when all subscription indexes are inaccessible, with an explicit coverage limitation.
- Added targeted ScienceDirect and SpringerLink searches, including mandatory checks of non-IEEE reliability/radiation/testing venues.
- Added NASA NTRS as a supplemental technical-evidence route; report/presentation status must not be confused with peer review.
- Scite remains secondary discovery/context and ResearchRabbit remains bounded citation expansion.
- eLibrary remains `DEFERRED / UNKNOWN COVERAGE` and must not be queried by Literature Scout in this cycle.
- Stopping criterion now requires cross-publisher coverage, targeted publisher backfill, source-access reporting and the eight-category DEC-001 compatibility matrix.
- Exact Literature Scout launch handoff is ready against the expanded protocol.
- RQ-002 literature search had not started when this protocol update was recorded.
