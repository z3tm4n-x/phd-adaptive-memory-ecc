# RQ-001 — Reliability event, metric and evaluation horizon for ECC-protected SRAM

**Title:** Reliability event, metric and evaluation horizon for ECC-protected SRAM  
**Source candidate:** C-RQ-01  
**Status:** INVESTIGATING  
**Registered:** 2026-08-26

## Question

Как должны быть определены reliability event, соответствующая метрика, уровень агрегации и временной горизонт для SRAM, защищённой ECC и периодическим scrubbing, чтобы сформулировать проверяемое ограничение надёжности?

## Why it matters

Без явного события, метрики и горизонта нельзя однозначно построить reliability model, сравнить варианты ECC/scrubbing или проверить выполнение ограничения надёжности.

## Scope

- состояния исхода: исправимая ошибка, обнаруженная неисправимая ошибка и иные релевантные исходы;
- уровень агрегации: codeword, bank, memory array или system-visible memory service;
- накопление ошибок между scrub cycles;
- форма метрики: вероятность, частота, риск или иная проверяемая величина;
- временной горизонт: scrub interval, operating interval или mission horizon;
- правила агрегирования от codeword к целевому уровню системы.

## Exclusions

- произвольное назначение численного reliability requirement;
- выбор стохастической модели радиационно-индуцированных ошибок;
- окончательный выбор класса ECC;
- определение resource-cost vector или adaptive policy;
- привязка к конкретной платформе при отсутствии системных требований.

## Dependencies

- `docs/research_spec.md` версии `v0.2-draft`;
- утверждённая цель диссертационного проекта;
- системные или mission requirements, если они существуют и доступны.

## Evidence needed

- первичные публикации с reliability models для ECC-protected memory и scrubbing;
- определения failure/reliability events и временных горизонтов в сопоставимых исследованиях;
- системные или mission requirements с явным provenance;
- допущения, используемые при агрегировании codeword-level событий.

## Answer / decision criterion

RQ считается отвеченным, когда зафиксированы:

1. формальное reliability event;
2. измеримая метрика;
3. уровень агрегации;
4. временной горизонт;
5. необходимые допущения и provenance каждого ограничения.

Если конкретный численный threshold не задан источниками или системными требованиями, он остаётся `TBD`; численное значение не изобретается.

## Literature mapping status

Literature Scout discovery зафиксирован как `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`.

- [Pilot report](../literature_mapping/RQ-001_literature_mapping_pilot_2026-08-26.md)
- [Completion delta](../literature_mapping/RQ-001_literature_mapping_completion_delta_2026-08-27.md)
- Cumulative candidate register: 53 records — 24 `CORE`, 16 `RELATED`, 3 `BACKGROUND`, 10 `REJECT`.
- eLibrary coverage: `DEFERRED / UNKNOWN`; не блокирует текущий gate.
- Mapping не является ответом на RQ-001.

## Accepted Paper Cards

- [PAPER-001 — Tausch, 2009](../paper_cards/PAPER-001-tausch-2009.md), source candidate C45, `CORE`.
- [PAPER-002 — Baeg, Wen, Wong, 2009](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), source candidate C46, `CORE`.
- [PAPER-003 — Lee, Baeg, Reviriego, 2011](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md), source candidate C38, `CORE`.

Acceptance applies to the traceability and completeness of the Paper Cards. It does not promote paper assumptions, illustrative thresholds or fitted parameters to project requirements.

## Initial evidence synthesis

- [Canonical cross-paper extraction matrix](../evidence_synthesis/RQ-001_initial_evidence_synthesis.md).
- An initial evidence synthesis is possible, but it is explicitly `NOT A FINAL ANSWER`.
- Across the three papers, the primitive event is an existential word state beyond correction capability, while aggregation, horizon, scrubbing semantics and statistical assumptions differ materially.
- No additional Paper Card is required before claim-level Evidence Auditor review.

## Remaining evidence gaps

- physical multi-error word state vs DUE/SDC/miscorrection vs system-visible service loss;
- exact aggregate object and codeword→system rule;
- sequential scrub semantics and word exposure age;
- mission aggregation across scrub cycles;
- mutually exclusive direct-MCU and independent-accumulation partition;
- provenance for a numerical reliability threshold (`TBD`).

## Next action

Передать Evidence Auditor `PAPER-001…003`, canonical synthesis и exact atomic candidate claims `RQ001-EA-CAND-01…12`. Получить claim-level status, supporting/contrasting evidence, citation context, corrections/editorial checks and scope assessment. Не создавать `CLM-xxx` до отдельного acceptance.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-002, RQ-003.
- Related papers: `PAPER-001`, `PAPER-002`, `PAPER-003`.
- Candidate audit inputs: `RQ001-EA-CAND-01…12` — temporary, not permanent claims.
- CLM/EVD/HYP/EXP: не создавались.

## Answer

`PARTIAL — INITIAL EVIDENCE SYNTHESIS ONLY.`

The three-paper synthesis supports a candidate primitive codeword event and proves that aggregation and horizon must be explicit. The final project event, metric, aggregate object and horizon remain unresolved pending evidence audit and system-requirement provenance.

## Confidence

Medium for the bounded three-paper synthesis; not assessed for a final RQ-001 answer.
