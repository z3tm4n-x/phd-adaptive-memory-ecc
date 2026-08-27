# RQ-001 — Reliability event, metric and evaluation horizon for ECC-protected SRAM

**Title:** Reliability event, metric and evaluation horizon for ECC-protected SRAM  
**Source candidate:** C-RQ-01  
**Status:** INVESTIGATING — PROVISIONAL DEFINITION PENDING  
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
- системные или mission requirements, если они существуют и доступны;
- RQ-003 for concrete ECC/decoder outcomes.

## Answer / decision criterion

RQ считается отвеченным, когда зафиксированы:

1. формальное reliability event;
2. измеримая метрика;
3. уровень агрегации;
4. временной горизонт;
5. необходимые допущения и provenance каждого ограничения.

Если конкретный numerical threshold не задан источниками или системными требованиями, он остаётся `TBD`.

## Evidence workflow

- Literature Scout discovery: `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`.
- eLibrary: `DEFERRED / UNKNOWN COVERAGE`.
- Accepted Paper Cards: [PAPER-001](../paper_cards/PAPER-001-tausch-2009.md), [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md).
- [Initial cross-paper synthesis](../evidence_synthesis/RQ-001_initial_evidence_synthesis.md).
- [Accepted Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md): 11 candidates supported; CAND-10 partially supported/deferred.

## Accepted claims

- [CLM-001](../claims/CLM-001-upset-count-horizon-requires-time-model.md)
- [CLM-002](../claims/CLM-002-harmful-mbu-outside-paper001-model.md)
- [CLM-003](../claims/CLM-003-paper002-loses-mechanism-provenance.md)
- [CLM-004](../claims/CLM-004-paper003-loses-mechanism-provenance.md)
- [CLM-005](../claims/CLM-005-paper002-direct-term-overlap.md)
- [CLM-006](../claims/CLM-006-paper003-direct-term-overlap.md)
- [CLM-007](../claims/CLM-007-paper002-upper-bound-condition.md)
- [CLM-008](../claims/CLM-008-multiplicity-not-decoder-service-outcome.md)

Candidate source facts 01–03 remain in their Paper Cards; CAND-10 is deferred and has no permanent `CLM-ID`.

## Provisional definition package

[Review package](../evidence_synthesis/RQ-001_provisional_definition_package.md) — `PROPOSED / PENDING USER APPROVAL`.

It proposes:

- primitive event: ECC capability exceedance in at least one codeword;
- primary metric: cumulative first-passage probability `F_A(H)`;
- default aggregate: complete SRAM region protected by the modeled controller;
- separate upset-count, per-codeword exposure and reporting/mission horizons;
- no automatic equivalence between capability exceedance and DUE/SDC/system failure;
- numerical requirement remains `TBD`.

None of these proposed project choices is accepted until the approval gate is completed.

## Next action

Approve, amend or reject the six explicit decisions in `RQ-001_provisional_definition_package.md`. If approved, record RQ-001 as `PARTIALLY ANSWERED / OPEN DEPENDENCIES` and release RQ-002 from the queue.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-002, RQ-003.
- PAPER: `PAPER-001…003`.
- CLM: `CLM-001…008`.
- HYP/EXP: none.

## Answer

`PARTIAL — PROVISIONAL DEFINITION PENDING APPROVAL.`

## Confidence

High for the audited bounded statements; medium for the proposed project definition until its assumptions and open dependencies are accepted explicitly.
