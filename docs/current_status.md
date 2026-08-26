# Current Status

**Updated:** 2026-08-26

## Current phase

Targeted literature mapping — pilot preparation.

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

Выполнить пилотный targeted literature mapping для RQ-001 и принять воспроизводимый Literature Scout handoff до запуска mapping остальных RQ.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — OPEN.
- RQ-002 — minimum adequate SRAM radiation error model — OPEN.
- RQ-003 — ECC abstraction and baseline code class — OPEN.
- RQ-004 — online observables for adaptation — OPEN.
- RQ-005 — measurable resource-cost vector — OPEN.

Canonical cards находятся в `docs/questions/`; утверждённые protocols — в `docs/literature_mapping/`. Литературный поиск ещё не запускался.

## Active hypotheses

Пока не заведены. Гипотезы формируются только после initial literature mapping и evidence review.

## Confirmed own results

Пока отсутствуют.

## Current blockers

Инфраструктурных блокеров нет. Научные неизвестные зафиксированы в RQ-001…RQ-005. Для RQ-002 действует decision gate: если MCU/MBU или spatial correlation существенны либо их исключение не обосновано, C-RQ-05 должен быть зарегистрирован как обязательный RQ до основной reliability model.

## Next actions

1. Передать RQ-001 и `docs/literature_mapping/RQ-001_protocol.md` Literature Scout как pilot task.
2. Выполнить только discovery/screening, не формируя HYP и не объявляя ответ на RQ.
3. Получить reproducible search log, screened candidate table, 2–5 seed papers, gaps и structured Zotero/Paper Analyst handoffs.
4. Проверить качество пилотного handoff и при необходимости скорректировать protocol pattern.
5. Затем выполнять mapping в порядке RQ-002 → RQ-003 → RQ-004 → RQ-005.

## Notes

Этот файл должен оставаться коротким. Он отражает текущее canonical state, а не историю проекта.
