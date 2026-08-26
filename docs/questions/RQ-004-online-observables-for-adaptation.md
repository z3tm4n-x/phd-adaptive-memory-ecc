# RQ-004 — Online observables for estimating SRAM error risk

**Title:** Online observables for estimating SRAM error risk  
**Source candidate:** C-RQ-06  
**Status:** OPEN  
**Registered:** 2026-08-26

## Question

Какие online observables доступны для оценки текущей интенсивности ошибок или риска для ECC-protected SRAM, и какую информацию, с какой задержкой и неопределённостью, даёт каждый наблюдаемый сигнал?

## Why it matters

Adaptive controller может использовать только сигналы, которые реально доступны online и имеют определённую связь с latent error/radiation state; без этого нельзя обоснованно формировать estimator или adaptive policy.

## Scope

- corrected-error counters;
- syndrome и scrub-result statistics;
- detected-uncorrectable events;
- external radiation sensors и dosimetry;
- forecast/model outputs;
- комбинации внутренних и внешних каналов;
- availability, update rate, latency, provenance и uncertainty;
- связь observable с latent error/radiation variable.

## Exclusions

- выбор конкретного estimator algorithm и оценка его точности;
- выбор adaptive policy;
- предположение о прямой online-доступности COSRAD без evidence;
- выбор конкретного sensor без evidence;
- детальная RTL-реализация интерфейсов.

## Dependencies

- RQ-002: структура error model и latent variables;
- RQ-003: ECC abstraction и доступные decoder outcomes.

## Evidence needed

- первичные описания memory controller и scrubber architectures;
- механизмы corrected-error/syndrome counters и telemetry;
- radiation-monitoring instruments и интерфейсы;
- исследования online error-rate/risk estimation;
- evidence о latency, noise, update rate и observability limits.

## Answer / decision criterion

RQ считается отвеченным, когда для каждого candidate channel зафиксированы:

1. измеряемая величина;
2. место и способ получения;
3. availability и update rate;
4. latency и основные uncertainty/limitations;
5. необходимый интерфейс к controller;
6. связь с latent variable из error model.

Каждый канал классифицирован как feasible, unproven или out of scope. Также принято решение, достаточны ли внутренние ECC/scrub observables или требуется внешний канал. При недостатке evidence фиксируется partial answer и конкретный gap.

## Next action

Выполнить `docs/literature_mapping/RQ-004_protocol.md` после первичного определения модели RQ-002 и ECC abstraction RQ-003.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-002, RQ-003, RQ-005.
- PAPER/CLM/EVD/HYP/EXP: TBD после targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Не оценивалась.
