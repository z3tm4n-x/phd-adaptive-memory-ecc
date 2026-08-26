# RQ-005 — Measurable resource-cost vector for adaptive SRAM scrubbing

**Title:** Measurable resource-cost vector for adaptive SRAM scrubbing  
**Source candidate:** C-RQ-10  
**Status:** OPEN  
**Registered:** 2026-08-26

## Question

Какие измеримые компоненты должны входить в первоначальный resource-cost vector adaptive SRAM scrubbing, чтобы их можно было последовательно оценивать в analytical model, simulation и RTL/FPGA evaluation?

## Why it matters

Без operationally defined cost/resource components невозможно сравнивать baselines и adaptive strategies на общей доказательной основе или переносить модельные результаты в hardware evaluation.

## Scope

- scrub operations/frequency;
- memory traffic и bandwidth occupancy;
- access latency и interface occupancy;
- energy либо обоснованный proxy;
- performance impact;
- hardware resources;
- controller state и update overhead;
- единицы, proxies и этап измерения каждой компоненты.

## Exclusions

- произвольные веса;
- scalar objective function;
- форма оптимизации;
- исключение существенной компоненты без evidence;
- platform-specific limits до выбора и обоснования платформы;
- сравнение adaptive policies.

## Dependencies

- RQ-001: reliability event и evaluation horizon;
- RQ-003: ECC abstraction;
- RQ-004: online observables и необходимые интерфейсы.

Targeted mapping может начаться параллельно, но окончательный vector зависит от результатов этих RQ.

## Evidence needed

- performance/resource models для memory scrubbing;
- ECC overhead models;
- bandwidth, latency, energy/power и performance measurements;
- RTL/FPGA implementation reports;
- методы измерения hardware resources и runtime overhead;
- сопоставимые definitions и units.

## Answer / decision criterion

RQ считается отвеченным, когда:

1. определён измеримый cost/resource vector;
2. для каждой компоненты заданы operational definition, unit или proxy и этап измерения;
3. зафиксированы platform dependencies и uncertainty;
4. исключения обоснованы evidence.

На этой стадии scalar objective function не выбирается. Форма оптимизации и возможная scalarization относятся к C-RQ-11.

## Next action

Выполнить `docs/literature_mapping/RQ-005_protocol.md` после первичного mapping RQ-003 и RQ-004; до этого допускается только предварительная карта метрик.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-003, RQ-004.
- Deferred candidate: C-RQ-11 — optimization formulation.
- PAPER/CLM/EVD/HYP/EXP: TBD после targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Не оценивалась.
