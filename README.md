# PhD Research — Adaptive Memory ECC

Репозиторий исследовательской части кандидатской диссертации по специальности **2.3.2 «Вычислительные системы и их элементы»**.

**Рабочая тема:** «Разработка методов адаптивного управления системами коррекции ошибок в цифровой памяти вычислительных систем».

## Назначение репозитория

Этот репозиторий — master-хранилище **собственных исследовательских артефактов**: моделей, кода, конфигураций экспериментов, результатов, графиков, RTL и технической документации.

Он **не является** библиотекой научных публикаций. Внешняя литература и библиографические метаданные хранятся в Zotero.

## Canonical systems

- **Литература и библиография:** Zotero
- **Оркестрация исследования и анализ:** ChatGPT Project / Work
- **Код, модели, эксперименты, результаты и provenance:** этот Git-репозиторий
- **Радиационная обстановка:** COSRAD; здесь фиксируются сценарии, параметры и происхождение данных
- **RTL/FPGA:** SystemVerilog + iVerilog + Vivado

## Tool access boundary

- **Cloud ChatGPT Work:** прямой доступ к GitHub и Scite при подключённых коннекторах; нет прямого доступа к локальной Zotero Desktop library, локальным COSRAD/Vivado/Python данным и файловой системе рабочего ПК.
- **Local Codex / local research environment:** локальный Git clone, Zotero Desktop + local API, Python/Jupyter, COSRAD, SystemVerilog/iVerilog, Vivado и локальные datasets.
- `literature/zotero_exports/references.bib` используется как cloud-visible snapshot библиографии и не заменяет Zotero master library.

## AI-agent governance

Canonical инструкции ИИ-ролей находятся в `docs/agents/`:

- `00_GLOBAL_OPERATING_RULES.md` — общие правила;
- `01_ORCHESTRATOR.md` — Research Orchestrator;
- `02_LITERATURE_SCOUT.md` — Literature Scout;
- `03_PAPER_ANALYST.md` — Paper Analyst;
- `04_EVIDENCE_AUDITOR.md` — Evidence Auditor;
- `05_SCIENTIFIC_REVIEWER.md` — Scientific Reviewer;
- `06_WRITING_PUBLICATIONS.md` — Writing & Publications;
- `07_RESEARCH_ENGINEER_LOCAL.md` — локальный Research Engineer / Codex.

Перед существенной работой агент должен читать общие правила и свою role card. Инструкции в GitHub являются canonical; DOCX в ChatGPT Project — удобный snapshot.

## Исследовательские сущности

Используются стабильные идентификаторы:

- `RQ-xxx` — Research Question
- `PAPER-xxx` — карточка публикации
- `CLM-xxx` — Claim
- `EVD-xxx` — Evidence record
- `HYP-xxx` — Hypothesis
- `DEC-xxx` — Research decision
- `EXP-xxx` — Experiment
- `RES-xxx` — Research result
- `FIG-xxx` — Figure
- `ART-xxx` — Article/publication

Кандидатные Research Questions до утверждения используют временные идентификаторы `C-RQ-xx`.

## Структура

- `docs/` — research specification, Research Questions, журнал исследования, решения, гипотезы, claims и инструкции ИИ-агентов
- `literature/` — только экспорты/мосты из Zotero; не PDF-библиотека
- `model/` — аналитические и символические модели
- `simulation/` — вычислительные модели и тесты
- `cosrad/` — обработка и provenance COSRAD-сценариев
- `experiments/` — спецификации и manifests экспериментов
- `results/` — утверждённые таблицы, данные малого объёма и графики
- `rtl/` — RTL, testbench, constraints и scripts
- `papers/` — материалы публикаций
- `thesis/` — материалы диссертации

## Правила

1. Не коммитить большие raw datasets, waveforms, generated Vivado projects и Zotero database.
2. Любой существенный эксперимент должен иметь `EXP-ID`, конфигурацию и связь с commit SHA.
3. Любой утверждённый собственный вывод должен иметь `RES-ID` и ссылаться на воспроизводимый эксперимент/вывод.
4. Значимые научные решения фиксируются как `DEC-ID`.
5. Непроверенные утверждения не помещаются в `results/` как установленные результаты.
6. `main` содержит только согласованное текущее состояние; рискованные изменения выполняются в отдельных ветках.
7. Chat history не является canonical research storage.

## Текущая стадия

- **Infrastructure setup:** завершён.
- **Zotero setup:** завершён; Zotero является master-хранилищем внешней литературы.
- **AI-agent operating model:** настроен в `docs/agents/`.
- **Research Specification:** `v0.7-draft`.
- **RQ-001:** `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- **Accepted decision:** `DEC-001` — ECC-capability event, start-time-aware metric, declared/partitioned protection domain and layered horizon semantics.
- **Integrated roadmap:** `DEC-002` — radiation-test evidence, mapping `W`, ECC-level reliability and adaptive restoration control are one causal method; representation loss and observability are evaluated explicitly.
- **Numerical reliability requirement:** `TBD`.
- **Accepted model decision:** `DEC-003` — event-driven comparison reference, `L0…L3` representation ladder and authorization of the first own experiment.
- **RQ-006:** permanently registered for physical-to-logical mapping `W`, interleaving and information-sufficiency conditions.
- **First own result:** [`RES-001`](results/RES-001-exp001-four-word-identified-set.md) — permanent, PI-approved and limited to the reviewed synthetic four-word/fixed-cardinality class.
- **EXP-001:** complete; independent validation and Scientific Review 02 passed; promoted only within `RES-001`.
- **Accepted next gate:** [`Information-deficit price for restoration control`](docs/research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md) — pre-execution; it separates control-resource price, information-acquisition cost and any later net balance.
- **Active PI gate:** disposition of the [exact proposed RQ-007 wording and boundaries](docs/question_candidates/DRAFT-RQ-007-integrated-adaptive-restoration-control.md); no permanent ID is consumed yet.
- **Next scientific interfaces:** RQ-003 parameterized ECC state/capability, RQ-004 observation/uncertainty and RQ-005 measurable resource vector.
- **Constraint:** no new experiment before RQ-007 registration, bounded domestic prior-art closure, preregistration and separate PI approval of the experiment/derivation; no retroactive hypothesis or broad literature cycle without a named blocker.
