# RQ-003 — ECC abstraction and baseline code class for adaptive SRAM scrubbing

**Title:** ECC abstraction and baseline code class for adaptive SRAM scrubbing  
**Source candidate:** C-RQ-04  
**Status:** `OPEN / ACTIVE NEXT INTERFACE`<br>
**Registered:** 2026-08-26

## Question

Какая абстракция ECC и какой стартовый класс кодов — SEC, SEC-DED либо параметризованное обобщение — должны использоваться как baseline для исследования adaptive SRAM scrubbing, и какие состояния/исходы декодера должны быть представлены явно?

## Why it matters

Reliability model и сравнение adaptive policies зависят не только от nominal correction capability, но и от явной семантики correctable, detectable-uncorrectable, undetected и miscorrection outcomes.

## Scope

- SEC и SEC-DED как стартовые классы;
- параметризованные свойства кода, необходимые reliability model;
- codeword parameters;
- состояния и исходы decoder;
- связь decoder outcomes с reliability event из RQ-001;
- границы обобщения на более сильные коды.

## Exclusions

- детальная RTL-реализация encoder/decoder;
- окончательный выбор interleaving;
- adaptive switching между разными ECC;
- утверждение превосходства класса кодов без evidence;
- выбор adaptive policy.

## Dependencies

- RQ-001: reliability event и метрика;
- RQ-002: error model;
- RQ-006: physical-to-logical mapping, interleaving and retained post-`W` information.

## Evidence needed

- первичные публикации об ECC для SRAM и radiation environments;
- reliability models с явной семантикой decoder outcomes;
- архитектуры памяти, раскрывающие codeword parameters и обработку ошибок;
- evidence фактического применения SEC/SEC-DED и более общих кодов;
- ограничения и failure modes выбранных абстракций.

## Answer / decision criterion

RQ считается отвеченным, когда:

1. выбрана ECC abstraction и перечислены её параметры;
2. явно определены decoder states/outcomes, используемые в reliability model;
3. указан baseline code class и отделены обязательные расширения;
4. зафиксированы границы обобщения и неизвестные эффекты.

Допустимые решения: подтвердить SEC как достаточный baseline; потребовать SEC-DED; использовать параметризованную абстракцию; либо зафиксировать evidence gap, не делая произвольного выбора.

## Next action

After PA-DOM-01…04 closure, define the minimum parameterized ECC
state/capability and labelled decoder-outcome contract required by RQ-007 and
the proposed experiment/derivation. Launch a bounded RQ-003 evidence task only
for a named proposition that remains blocking; do not require eLibrary while it
is unavailable to Literature Scout.

## Related PAPER/CLM/HYP/EXP

- Related RQ: RQ-001, RQ-002, RQ-007.
- Required dependency: RQ-006.
- PAPER/CLM/EVD/HYP/EXP: TBD после targeted literature mapping.

## Answer

UNKNOWN.

## Confidence

Не оценивалась.
