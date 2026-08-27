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
- **Research Specification:** `v0.3-draft`.
- **RQ-001:** `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- **Accepted decision:** `DEC-001` — ECC-capability event, start-time-aware metric, declared/partitioned protection domain and layered horizon semantics.
- **Numerical reliability requirement:** `TBD`.
- **Current phase:** RQ-002 targeted literature mapping; corrected handoff issued and Literature Scout launched.
- **Active gate:** receive and assess the bounded Scout report against `docs/literature_mapping/RQ-002_protocol.md`, including mandatory anchors, exact Zebrev arXiv-v2 control, model-class sensitivity and the C-RQ-05 gate.
- **Constraint:** RQ-003 retains decoder-outcome semantics; RQ-001 remains open.
