# RQ-002 — Minimum adequate model of radiation-induced errors in SRAM

**Title:** Minimum adequate model of radiation-induced errors in SRAM  
**Source candidate:** C-RQ-02  
**Status:** OPEN  
**Registered:** 2026-08-26

## Question

Какая минимальная стохастическая модель радиационно-индуцированных ошибок SRAM одновременно физически обоснована и вычислительно пригодна для моделирования накопления ошибок и адаптивного scrubbing?

## Why it matters

Структура error model определяет вероятность выбранного reliability event, допустимость упрощающих допущений и необходимость учитывать MCU/MBU и корреляции до построения основной reliability model.

## Scope

- single-bit upsets и накопление ошибок между scrub cycles;
- stationary и non-stationary intensity;
- MCU/MBU;
- spatial и temporal correlation;
- уровни bit/cell, codeword, region и memory array;
- допущения модели и границы их применимости.

## Exclusions

- априорное принятие Poisson process или независимости ошибок без evidence;
- численные параметры без provenance;
- окончательный выбор codeword organization или interleaving;
- преобразование конкретных данных COSRAD в online signal;
- выбор adaptive policy.

## Dependencies

- RQ-001: reliability event, метрика, уровень агрегации и временной горизонт.

## Evidence needed

- первичные irradiation studies для SRAM;
- эмпирические исследования SEU, MCU и MBU;
- опубликованные stochastic/probabilistic error models;
- данные или анализ, позволяющие проверить independence, stationarity и correlation assumptions;
- валидация моделей в сопоставимых условиях.

## Answer / decision criterion

RQ считается отвеченным, когда:

1. перечислены релевантные классы моделей;
2. для каждого класса зафиксированы допущения, параметры, наблюдаемый уровень и domain of validity;
3. выбран минимально достаточный класс либо небольшой набор обоснованных альтернатив;
4. явно зафиксированы исключённые эффекты и границы применимости.

**Decision gate:** если evidence показывает, что MCU/MBU или spatial correlation существенно изменяют структуру либо вероятность reliability event, или их исключение нельзя обосновать/ограничить, кандидат C-RQ-05 должен быть повышен до обязательного permanent RQ и отвечен до построения основной reliability model.

## Next action

Выполнить `docs/literature_mapping/RQ-002_protocol.md`; при screening отдельно собирать evidence для decision gate по C-RQ-05.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-003.
- Conditional dependency: C-RQ-05 при срабатывании decision gate.
- PAPER/CLM/EVD/HYP/EXP: TBD после targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Не оценивалась.
