# Current Status

**Updated:** 2026-08-26

## Current phase

Подготовка Initial RQ Package.

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

Утвердить 3–5 priority Research Questions и подготовить для них targeted literature mapping protocol.

## Active Research Questions

Окончательные `RQ-xxx` пока не зарегистрированы. Готовится кандидатный пакет `C-RQ-xx`.

## Active hypotheses

Пока не заведены. Гипотезы формируются только после initial literature mapping.

## Confirmed own results

Пока отсутствуют.

## Current blockers

Инфраструктурных блокеров нет. Источник оперативной информации для адаптации, состав управляемых параметров и функция ресурсных затрат остаются осознанными открытыми исследовательскими вопросами.

## Next actions

1. В `00 ORCHESTRATOR` сформировать 12–15 кандидатных Research Questions без запуска литературного поиска.
2. Построить dependency graph и выбрать 3–5 priority RQ.
3. После пользовательского утверждения зарегистрировать priority RQ в `docs/questions/`.
4. Подготовить targeted literature mapping protocol для каждого priority RQ.
5. Передать первый утверждённый RQ в `01 LITERATURE SCOUT`.
6. Только после этого начать targeted literature discovery.

## Notes

Этот файл должен оставаться коротким. Он отражает текущее canonical state, а не историю проекта.
