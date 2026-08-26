# RQ-001 — Reliability event, metric and evaluation horizon for ECC-protected SRAM

**Title:** Reliability event, metric and evaluation horizon for ECC-protected SRAM  
**Source candidate:** C-RQ-01  
**Status:** OPEN  
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

## Next action

Передать `docs/literature_mapping/RQ-001_protocol.md` Literature Scout для пилотного targeted literature mapping.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-002, RQ-003.
- PAPER/CLM/EVD/HYP/EXP: TBD после targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Не оценивалась.
