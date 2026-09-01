# Next quantitative gate — Information-deficit price for restoration control

**Status:** `ACCEPTED / PRE-EXECUTION / NO NEW EXP AUTHORIZED`<br>
**Artefact class:** directional research gate; not `RQ`, `DEC`, `HYP`, `EXP`,
`RES` or novelty claim<br>
**Prepared:** 2026-08-31<br>
**PI accepted:** 2026-09-01<br>
**Accepted basis:** `DEC-001…003`; `RES-001`; RQ-002; RQ-006; accepted Russian
normative extraction; accepted Chen S3/S4/S5 Evidence Audit<br>
**Downstream interfaces:** RQ-003; RQ-004; RQ-005; permanently registered
[RQ-007](../questions/RQ-007-integrated-adaptive-restoration-control.md)

## Accepted gate statement

Следующий количественный этап должен построить и проверить единый интерфейс

`available information I → admissible model set M(I) → exact value / identified set / bound for F_A → admissible restoration actions → selected T_scrub → measurable resource-cost vector`.

Цель — не повторно показать, что зависимость «может иметь значение», а
количественно определить **ресурсную цену дефицита информации для
управляющего решения** в физически обоснованном классе событий и отображений
`W`.

Этап должен установить области параметров, в которых переход от более богатого
информационного состояния к редуцированному:

1. сохраняет `F_A` точно;
2. даёт доказанную границу или контролируемую ошибку;
3. изменяет `F_A`, но не изменяет управляющее действие;
4. сужает множество робастно допустимых действий или вынуждает более частое
   восстановление;
5. имеет измеримое покомпонентное ресурсное следствие для управления.

Ни знак, ни наличие эффекта заранее не предполагаются.

## Scientific object

### Accepted gate-level notation

Обозначения этого раздела являются принятыми working objects данного gate и
зарегистрированы в `docs/terminology.md`. Они не выбирают конкретную модель,
источник наблюдений, численный reliability requirement или scalar objective.

- `I` — явно объявленный информационный набор: сохранённые наблюдения/сводки,
  provenance, разрешение, uncertainty и отсутствующие компоненты.
- `M(I)` — непустое множество процессов, event marks, отображений `W`,
  начальных состояний и transition semantics, совместимых с `I` и всеми
  объявленными ограничениями.
- `U` — конечное или параметризованное множество допустимых режимов
  восстановления; в первом исполнении основной action — `T_scrub`.
- `R_I(u)` — множество значений `F_A(t0,T;mu_t0)` при действии `u` по всем
  моделям из `M(I)`.
- `F_I^-(u)` и `F_I^+(u)` — нижняя и верхняя границы `R_I(u)`, если они
  установлены.
- `U_rob(I,epsilon)` — действия, для которых `F_I^+(u) <= epsilon`.
- `C(u)` — измеримый resource-cost vector; scalar weights не вводятся без
  отдельного решения RQ-005.

Если `M(I)` содержит estimation uncertainty, representation uncertainty и
observation uncertainty, они должны быть представлены раздельно. Monte Carlo
error вычисления не входит в `M(I)` и отчётно отделяется от этих объектов.

### Action-invariance object

Для двух информационных состояний `I_coarse` и `I_rich` инвариантность действия
может утверждаться только относительно полного объявленного контракта:

- `epsilon` или sweep его экспериментальных значений;
- reporting window `H(t0,T)` и initial state/distribution;
- candidate action set `U`;
- exact/estimated/robust feasibility semantics;
- selection/tie-break rule;
- resource vector или явно объявленный experiment-local proxy.

Из равенства выбранных действий в одной точке не следует общая ненужность
информации. Допустимый результат — только область условной инвариантности.

### Three distinct resource objects

**Control-resource price of information deficit** — разность или множество
разностей между затратами действия, допустимого робастно при `I_coarse`, и
действия при `I_rich`, при одном и том же underlying physical model/domain,
action set, horizon, reliability constraint и selection rule. Это прежде всего
ресурсное следствие более консервативного режима восстановления, вызванного
более широким `M(I_coarse)`.

**Information-acquisition cost** — отдельные аппаратные, энергетические,
вычислительные и коммуникационные затраты получения, хранения и обработки
более богатого `I`. Они относятся к RQ-004/RQ-005 interface и не включаются
молча в control-resource price.

**Net information balance** — возможное последующее сопоставление первых двух
объектов при совместимых единицах, области применения и явно принятом правиле
агрегирования. До такого решения разность затрат на `T_scrub` не называется
полной «ценностью информации».

До решения RQ-005 все три объекта сообщаются раздельно и покомпонентно либо как
Pareto shift. Они не сворачиваются в произвольную weighted sum. Для
control-resource price отдельно сообщаются случаи:

- оба информационных состояния дают одно действие;
- coarse information требует более консервативного действия;
- coarse information не допускает ни одного действия из `U`;
- richer information не улучшает действие в объявленной области;
- выбор меняется только из-за численной/статистической decision rule, а не из-за
  model-set uncertainty.

## Minimum physically defensible execution domain

Будущий execution design должен одновременно удовлетворять следующим условиям:

1. Используется хотя бы один source-constrained event/topology family и хотя бы
   один source- or architecture-constrained class of `W`; это не должна быть
   только новая экстремальная синтетическая пара.
2. Сравниваемые информационные состояния получаются как контролируемые
   проекции/редукции одного underlying model family. Нельзя смешивать эффект
   потери информации с заменой marginal distributions, arrival intensity,
   initial state, ECC capability или scrub semantics.
3. Полная physical topology не считается автоматически наблюдаемой или
   необходимой. Допускаются reconstructed statistics и uncertainty sets,
   основанные на реально доступных test/diagnostic outputs.
4. Как минимум один coarse information state должен соответствовать реально
   встречающемуся output class: classified event/multiplicity statistics,
   cross-section/rate summary, corrected-error statistic или иной проверенный
   интерфейс.
5. `E_cap` и `F_A` сохраняют DEC-001 semantics; decoder/service outcomes не
   подменяются ими.
6. Restoration/reset semantics остаются explicit/parameterized; одна
   post-`E_cap` semantics не зашивается как универсальная.
7. Результаты сообщаются как parameter-domain map, а не как одна выбранная
   точка или один численный threshold.

Target-device calibration полезна, но не блокирует первый bounded execution,
если все параметры помечены как source-constrained range или declared sweep.

## Required RQ/interface slices

Полное закрытие RQ-002…RQ-006 не требуется до следующего количественного этапа.
Нужны только следующие минимальные интерфейсные срезы:

| Interface | Required before execution | Not required yet |
|---|---|---|
| RQ-002 | Declared arrival/event/state family, initial state, accumulation and reset semantics; explicit uncertainty set | Universal minimum stochastic family |
| RQ-006 | Declared `W` family, information projections and exact/bound/approximation relation to post-`W` impact | Proof that full topology is always necessary or unnecessary |
| RQ-003 | Parameterized ECC state/capability contract sufficient to compute `E_cap`; decoder outcomes remain separately labelled | Final code or complete DUE/SDC/miscorrection model |
| RQ-004 | At least one external/test-derived and one internal-memory information channel represented with latency/uncertainty semantics, or an explicit reason one is deferred | Final estimator or sensor choice |
| RQ-005 | Experiment-local measurable cost vector with units/proxies and measurement stage | Scalar objective, arbitrary weights or final platform limits |

The permanently registered
[RQ-007](../questions/RQ-007-integrated-adaptive-restoration-control.md)
consumes these interfaces. It does not close the upstream RQ and does not
authorize an experiment by itself.

## Minimum bounded prior-art closure before a new EXP

This closure is a design-boundary check, not a new broad mapping. It has four
work units and a hard stop rule.

| Work unit | Minimum controlled source set | Exact extraction needed | Stop condition |
|---|---|---|---|
| PA-DOM-01 — Meshchanov/Lushnikov/Krasnikov | Identity-resolve the most complete primary source for corrected-error count → intensity estimate → regeneration-period adaptation; add one companion only if needed to recover the full method | observable, estimator, update timing, action set/rule, reliability guarantee, cost, `W`/event assumptions | One source or controlled family fully specifies the occupied method chain |
| PA-DOM-02 — Podzolko 2017 | Exact primary 2017 text | failure event/metric/horizon, independence and arrival assumptions, ECC model, scan/reset semantics, `T_scrub` relation, decision/optimization rule | The independent-error periodic-restoration baseline can be reproduced or its missing inputs are named |
| PA-DOM-03 — Boruzdina/Ulanova/Chumakov | 2014 dissertation abstract plus the already identified primary topology paper DOI `10.1134/S1063739714020036`; at most one additional primary methods paper if the reconstruction/error claim is absent | physical vs logical multiplicity, topology/address observables, false grouping, reconstruction assumptions/error, level before/after `W`, downstream output | The strongest controlled statement about retained/reconstructed event information and its error is known |
| PA-DOM-04 — Zebrev/Galimov | Reuse `PAPER-005` first; request another full text only if the specific reduced-data reconstruction claim is not present there | reduced inputs, reconstructed statistics, assumptions, uncertainty, mapping level, suitability for DEC-001 `F_A` | Existing accepted card either closes the comparator or exposes one exact missing source proposition |

Every work unit must populate the same comparison columns:

1. available input/observation;
2. reconstructed or assumed information;
3. uncertainty/error and validity domain;
4. position relative to `W`;
5. ECC reliability object and horizon;
6. restoration action and decision law;
7. reliability guarantee/constraint;
8. resource-cost treatment;
9. exact distinction that can change the next execution design.

### Prior-art stop rule

Stop after the four work units are identity-controlled and the matrix can state
which baseline, reconstruction and control features the next design must not
reclaim generically. Do not continue merely because more related sources exist.

A new source is permitted only for a named proposition that blocks one of:

- definition of `M(I)`;
- physical plausibility of the event/`W` domain;
- a required baseline implementation;
- validity/bound interpretation;
- an exact comparison statement used in the next experiment specification.

The classical inspection/maintenance pass and a broad Chen/control search are
not blockers for this bounded execution. They become mandatory before a
literature-level integrated-control novelty claim, or earlier only if the
chosen decision law directly instantiates that literature.

## Candidate quantitative work package after prior-art and interface gates

No `EXP-002` is registered by this document. After prior-art closure and the
minimum interface decisions, a proposed experiment/derivation must include:

1. a nested information-state lattice derived from common underlying models;
2. explicit construction of each `M(I)`;
3. exact, bounded or independently validated numerical evaluation of `R_I(u)`;
4. a candidate `T_scrub` set and declared exact/robust decision rule;
5. an experiment-local RQ-005-compatible resource vector;
6. a parameter-domain map of action invariance/change and control-resource
   price, with information-acquisition cost reported separately when present;
7. a fixed/non-adaptive conservative baseline;
8. falsification criteria and a Scientific Reviewer gate before any `RES-002`.

No directional hypothesis is forced. If the bounded prior-art closure supports
a genuinely falsifiable magnitude statement, register `HYP-001` before
execution; otherwise use an explicit decision/falsification criterion in the
future `EXP` specification.

## Required outputs and completion criterion

The next quantitative gate is complete only when all of the following exist:

- traceable information states and compatible model sets;
- a justified physical/event/`W` applicability domain;
- `F_A` values, identified sets, bounds or controlled errors for every tested
  action;
- exact separation of representation/model/observation uncertainty from
  numerical estimation error and decision-rule conservatism;
- robust and non-robust feasible action sets;
- conditional action-invariance/change regions;
- component-wise control-resource-price results;
- separately reported information-acquisition cost and, only if justified, net
  information balance;
- explicit null/infeasible outcomes rather than a forced positive effect;
- reproducible code/configuration/manifests and adversarial scientific review.

Only then may an independently reviewed bounded `RES-002` be proposed. No
novelty claim follows automatically.

## Genuine blockers and non-blockers

### Blockers before execution

1. Completion of PA-DOM-01…04 to the stop rule above.
2. Minimum RQ-003/RQ-004/RQ-005 interface decisions required by RQ-007.
3. A preregistered experiment/derivation with declared interface slices,
   uncertainty objects, action rule, resource vector and falsification criteria.
4. Separate PI `ACCEPT` of that experiment/derivation before execution.

### Not blockers for the first bounded execution

- numerical `H_req` or `epsilon_req`;
- a final target SRAM/FPGA platform;
- proof that one stochastic family is universally minimal;
- full closure of RQ-003/RQ-004/RQ-005;
- a second general RQ-002 literature cycle;
- broad inspection/maintenance literature mapping;
- a novelty decision.

## PI disposition and next approval gate

PI disposition: `ACCEPT` on 2026-09-01. This accepts the scientific direction,
the four-unit prior-art closure and its stop rule. It does **not** authorize a
new `EXP`.

PI issued `ACCEPT` for the exact RQ-007 wording, boundaries and permanent ID on
2026-09-01. The active gate is completion of PA-DOM-01…04 under the hard stop
rule, followed by baseline/interface synthesis. The proposed
experiment/derivation must then be presented for separate PI approval before
execution.
