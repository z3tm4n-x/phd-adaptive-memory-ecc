# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-001 claim-level evidence review — Evidence Auditor handoff preparation.

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

Выполнить claim-level Evidence Auditor review для двенадцати atomic candidate claims из `docs/evidence_synthesis/RQ-001_initial_evidence_synthesis.md`. До результата аудита не назначать `CLM-xxx`, не формулировать окончательный ответ на RQ-001 и не начинать RQ-002.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `INVESTIGATING`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / QUEUED`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.

RQ-001 Literature Scout discovery остаётся `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`. eLibrary coverage отложена и не блокирует текущий gate.

## Accepted RQ-001 Paper Cards

- `PAPER-001` — Tausch, 2009 — `CORE`.
- `PAPER-002` — Baeg, Wen, Wong, 2009 — `CORE`.
- `PAPER-003` — Lee, Baeg, Reviriego, 2011 — `CORE`.

Все три карты приняты как traceable full-text analyses. Это не означает принятие их stochastic, architecture, mapping или scrubbing assumptions как допущений проекта.

## Initial evidence synthesis

- Canonical matrix: `docs/evidence_synthesis/RQ-001_initial_evidence_synthesis.md`.
- Первичный synthesis возможен: три papers дают сопоставимые определения event/metric/aggregation/horizon и выявляют существенные несовместимости.
- Final answer на RQ-001 отсутствует.
- Дополнительные Paper Cards до Evidence Auditor stage не требуются.

## Active hypotheses and claims

- Постоянные `HYP-xxx` не заведены.
- Постоянные `CLM-xxx` не заведены.
- Для Evidence Auditor отобраны двенадцать atomic candidate claims `RQ001-EA-CAND-01…12`; это временные audit inputs, не утверждённые claims.

## Confirmed own results

Пока отсутствуют. Paper Cards и evidence synthesis являются literature-analysis artefacts, а не собственными `RES-xxx`.

## Current blockers / unknowns

- Project reliability event: physical codeword state vs DUE/SDC/miscorrection vs system-visible service loss — `UNKNOWN`.
- Exact aggregation boundary and codeword→bank/array/system rule — `UNKNOWN`.
- Operational sequential-scrubbing semantics and nonuniform word exposure age — `PARTIAL / UNRESOLVED`.
- Mission aggregation across scrub cycles and nonstationary conditions — `UNKNOWN`.
- Mutually exclusive direct-MCU vs independent-accumulation partition — `UNRESOLVED`.
- Numerical reliability threshold — `TBD` pending traceable system/mission requirement.
- eLibrary — `DEFERRED / UNKNOWN COVERAGE`.

## Next actions

1. Передать Evidence Auditor canonical synthesis, `PAPER-001…003`, `RQ-001` и exact atomic claims `RQ001-EA-CAND-01…12`.
2. Получить для каждого claim supporting, contrasting/limiting and contextual evidence, correction/editorial checks, scope match and status.
3. После аудита решить, какие claims принимаются и получают `CLM-xxx`, а какие уточняются или отклоняются.
4. Затем выбрать candidate project event/metric/aggregation/horizon либо заказать только gap-specific Paper Card.
5. Не запускать RQ-002 до review этого gate.

## Notes

Illustrative thresholds и scrub intervals из `PAPER-002`/`PAPER-003` не являются требованиями проекта. Upset-count horizon из `PAPER-001` не смешивается с elapsed-time, scrub-cycle или mission horizon.
