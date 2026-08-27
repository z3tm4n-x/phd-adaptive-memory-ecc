# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-001 evidence extraction — Paper Analyst preparation.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.2-draft`.

## Tool access boundary

- Cloud ChatGPT Work: GitHub + Scite via connectors; no direct access to local Zotero Desktop or local research toolchain.
- Local Codex / research environment: local Git, Zotero Desktop/local API, Python/Jupyter, COSRAD, SystemVerilog/iVerilog, Vivado, local datasets.
- Zotero operations requested from Cloud Work are transferred through structured handoffs.

## Active gate

Завершить Zotero handoff для принятых RQ-001 candidates, получить full-text Paper Cards по C45, C46 и C38 и построить extraction matrix `event × metric × aggregation × horizon × assumptions`.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — OPEN.
- RQ-002 — minimum adequate SRAM radiation error model — OPEN.
- RQ-003 — ECC abstraction and baseline code class — OPEN.
- RQ-004 — online observables for adaptation — OPEN.
- RQ-005 — measurable resource-cost vector — OPEN.

RQ-001 Literature Scout discovery принят как `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`. Pilot и completion-delta reports находятся в `docs/literature_mapping/`. Это не является ответом на RQ-001.

## Active hypotheses

Пока не заведены. Гипотезы формируются только после paper-level extraction и evidence review.

## Confirmed own results

Пока отсутствуют. Literature mapping является discovery artefact, а не подтверждённым собственным научным результатом.

## Current blockers

- Формальные reliability event, metric, aggregation level и horizon для проекта остаются `UNKNOWN` до анализа полных текстов.
- Numerical reliability threshold остаётся `TBD` до появления traceable system/mission requirement.
- eLibrary недоступна Literature Scout и по решению пользователя отложена как coverage limitation; она не блокирует текущий gate.
- Для Paper Analyst необходимы проверенные полные тексты C45, C46 и C38 в Zotero или через иной законный доступ.

## Next actions

1. Выполнить Zotero handoffs из pilot и completion-delta reports с duplicate/metadata/PDF checks.
2. Получить verified full text для C45, C46 и C38.
3. Передать эту тройку Paper Analyst и получить отдельную Paper Card на каждый источник.
4. Построить сравнительную extraction matrix `event × metric × aggregation × horizon × assumptions`.
5. После matrix решить, нужны ли дополнительные Paper Cards и какие конкретные claims передавать Evidence Auditor.
6. Не запускать RQ-002 до первичного evidence synthesis по RQ-001.

## Notes

Этот файл отражает текущее canonical state. RQ-001 discovery может быть переоткрыт только при конкретном paper-level evidence gap либо после восстановления доступа к eLibrary.
