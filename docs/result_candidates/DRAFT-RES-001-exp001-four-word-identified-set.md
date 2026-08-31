# DRAFT RES-001 — Identified set for `F_A` in the EXP-001 four-word class

**Status:** `PI FINAL ACCEPT REQUIRED / WORDING REVISED / NOT REGISTERED AS RES-xxx`<br>
**Proposed permanent ID:** `RES-001`<br>
**Related:** `EXP-001`; `RQ-002`; `RQ-006`; `DEC-001`; `DEC-003`<br>
**Reviewer disposition:** `SCIENTIFIC REVIEW 02 — PASS`<br>
**PI scientific-content disposition:** `ACCEPTED`<br>
**PI wording disposition:** `REVISE — TWO EDITORIAL CORRECTIONS INCORPORATED`

This file is a bounded result candidate for PI wording approval. It is not an
approved result and must not be cited as `RES-001` until the PI explicitly
accepts the statement and permanent registration is completed.

## Proposed central result statement

В заявленном синтетическом четырёхсловном классе одинаковые однословные
маргинальные вероятности воздействия одного родительского события при
фиксированной кратности два не определяют единственное значение вероятности
первого превышения корректирующей способности `F_A`.

Допустимый класс совместных распределений воздействий порождает точное
идентифицированное множество значений `F_A`, границы которого достигаются
моделями `J-A` и `J-B`.

При исследованных экспериментальных значениях `epsilon` различие между
границами этого множества имеет разные управляющие последствия: при
`epsilon=0.15` оно изменяет само множество допустимых действий — для `J-A`
период `T_scrub=0.5` допустим, тогда как для `J-B` ни один исследованный период
не допустим; при `epsilon=0.25` и `0.35` оно изменяет максимальный допустимый и
выбранный `T_scrub`; при `epsilon=0.55` точное выбранное действие для `J-A` и
`J-B` совпадает.

Результат действителен только при совместном выполнении всех четырнадцати
условий применимости, зафиксированных ниже. Использованные значения `epsilon`
являются параметрами эксперимента и не являются требованиями проекта.

## Analytical form and exact decision table

В центральной формулировке фиксированная кратность два означает обязательное
условие: каждое родительское событие воздействует ровно на два различных слова.

Для допустимого класса совместных распределений пар затронутых слов

`p01=p23=a`, `p02=p13=c`, `p03=p12=e`, `a,c,e>=0`, `a+c+e=1/2`,

вероятность того, что две последовательные пары не пересекаются, равна

`q=2(a^2+c^2+e^2)`,

причём `1/6 <= q <= 1/2`. При среднем числе родительских событий за один
интервал восстановления `m=lambda*T_scrub` вероятность не превысить
корректирующую способность в этом интервале имеет вид

`S(q,m)=exp(-m)*[1+m+q*m^2/2]`.

Для отчётного окна, состоящего из `k` полных одинаковых интервалов
восстановления, точное значение метрики DEC-001 составляет

`F_A(t0,T;delta_0)=1-S(q,m)^k`, где `T=k*T_scrub` и `t0` совмещено с фазой
восстановления. Поэтому указанная сокращённая информация задаёт не точечное
значение, а точное идентифицированное множество

`F_A in [F_A(q=1/2), F_A(q=1/6)]`.

Границы достигаются проверенными моделями `J-A` (`q=1/2`) и `J-B` (`q=1/6`).
При фиксированных экспериментальных параметрах `lambda=0.5`, `T=4` и множестве
кандидатных периодов `{0.5, 1, 2, 4}` применяется экспериментальное правило:
выбрать максимальный период, для которого точное `F_A<=epsilon`; если такого
периода нет, действие считается недопустимым. Точные выбранные периоды имеют
вид:

| `epsilon` | `J-A` | `J-B` | Точное действие |
|---:|---:|---:|---|
| 0.15 | 0.5 | допустимого периода нет | различается |
| 0.25 | 1.0 | 0.5 | различается |
| 0.35 | 2.0 | 1.0 | различается |
| 0.55 | 4.0 | 4.0 | совпадает |

Указанное правило является экспериментальным правилом выбора и не заменяет
будущий многокомпонентный ресурсный критерий RQ-005.

## Complete validity domain

Результат действителен только при одновременном выполнении всех условий:

1. объявленная область содержит ровно четыре логических слова с общей
   корректирующей способностью `t_c=1`;
2. отчётное окно начинается из чистого состояния;
3. каждое родительское событие воздействует ровно на два различных слова;
4. каждое выбранное слово получает ровно один новый ошибочный бит; отсутствуют
   повторное попадание в тот же бит, toggle-clear и восстановление внутри
   интервала;
5. вероятность воздействия одного события на каждое слово равна ровно `1/2`;
6. используется один фиксированный вектор вероятностей пар, а метки пар
   независимы и одинаково распределены между родительскими событиями;
7. метки пар независимы от времён и количества событий однородного
   пуассоновского потока;
8. родительские события образуют простой однородный пуассоновский процесс с
   пуассоновским числом событий и независимыми приращениями;
9. воздействия одного родительского события одновременны, а `E_cap`
   проверяется после применения полной метки события;
10. восстановление мгновенное, периодическое, синхронное и полностью очищает
    состояние ошибочных битов;
11. `t0` совмещено с фазой восстановления, а длительность отчётного окна равна
    ровно `k*T_scrub` без неполных начального или конечного интервалов;
12. события точно на детерминированной границе имеют нулевую вероятность, а в
    реализации используется порядок `scrub_then_event`;
13. `F_A` является вероятностью первого появления события DEC-001 в отчётном
    окне, поэтому состоявшееся превышение учитывается даже после последующего
    очищения состояния;
14. каждое логическое слово содержит достаточно ещё не использованных битовых
    позиций для конечной реализации конструкции с новыми ошибочными битами.

## Evidence and provenance

- experiment specification:
  [`EXP-001`](../../experiments/EXP-001-event-representation-reduction-sensitivity.md);
- implementation commit: `84728d1b5768e7c91c508495d696c5980943ae57`;
- validation-repair commit: `072b70adabb9827ee59c94b2b3d5cf044b25cdf9`;
- accepted Orchestrator repair disposition commit:
  `222e9303724c1e0f8f0986c1d4e53c754c47cf23`;
- [Scientific Review 01](../scientific_reviews/EXP-001_SCIENTIFIC_REVIEW_01.md):
  analytical result accepted, validation repair required;
- [Scientific Review 02](../scientific_reviews/EXP-001_SCIENTIFIC_REREVIEW_02.md):
  `PASS`; all original findings closed and no new issue found;
- fixed configurations, manifests, aggregate tables and analytical validation:
  [`experiments/manifests/EXP-001`](../../experiments/manifests/EXP-001/).

The analytical identified set is exact within the complete validity domain.
Monte Carlo estimates reproduce the endpoint probabilities within the reported
pointwise 95% Wilson intervals; those intervals are not simultaneous or
selection-valid guarantees over the period/model grid.

## Required uncertainty separation

1. **Representation/dependence uncertainty:** the exact interval induced by the
   admissible joint pair distributions at fixed one-event per-word impact
   probabilities and fixed two-word parent-event cardinality.
2. **Monte Carlo estimation uncertainty:** uncertainty of finite-run numerical
   estimates, represented by pointwise intervals.
3. **Decision-rule conservatism:** the additional restriction produced by using
   the pointwise Wilson upper endpoint instead of exact `F_A`.

The `epsilon=0.55` Wilson-rule difference is attributable to the third object;
it is not an exact structural difference between the endpoint models.

## Limitations and explicit non-claims

This candidate does not establish:

- universal insufficiency of marginal per-word distributions;
- necessity of retaining complete physical event topology or complete `W`;
- that real SRAM event dependence reaches either synthetic endpoint;
- a physically calibrated SRAM radiation model;
- validity outside the fourteen-condition domain;
- a numerical reliability requirement;
- DUE, SDC, miscorrection or system-visible failure semantics;
- an optimal restoration period or final resource objective;
- novelty of the integrated adaptive-control method.

The result states non-identification only for the declared model class. Any
future invariance statement must remain conditional on the declared
`epsilon`, candidate action set, decision rule, reporting horizon and resource
criterion.

## PI approval gate

After the wording-only revision, PI must explicitly choose one final
disposition:

- `ACCEPT` — approve this wording and authorize permanent `RES-001`
  registration;
- `REVISE` — return exact wording or scope corrections;
- `REJECT` — do not register the result.

Until `ACCEPT`, `results/` remains unchanged and no publication or thesis claim
may cite this candidate as an approved own result.
