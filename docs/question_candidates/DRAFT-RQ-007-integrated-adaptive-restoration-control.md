# DRAFT-RQ-007 — Integrated adaptive restoration control

**Proposed permanent ID:** `RQ-007` — not allocated or registered<br>
**Status:** `PI DISPOSITION REQUIRED / NOT REGISTERED / NO EXP AUTHORIZED`<br>
**Prepared:** 2026-09-01<br>
**Candidate lineage:** integration of the former C-RQ-08, C-RQ-09 and C-RQ-11
control/action/optimization lines; no permanent identifier is consumed by this
draft<br>
**Accepted basis:** DEC-001…003; DEC-002 causal architecture; RQ-002…RQ-006;
RES-001; accepted information-deficit control-price gate; accepted bounded
Russian normative and Chen S3/S4/S5 analyses

This card is the exact candidate presented for PI `ACCEPT / REVISE / REJECT`.
It is not an accepted Research Question, project answer, method selection,
experiment authorization or novelty claim.

## Proposed title

**Integrated information-aware adaptive control of the restoration period for
ECC-protected SRAM**

## Proposed Research Question

Как построить и обосновать метод адаптивного выбора периода восстановления
`T_scrub` ECC-защищённой SRAM, который по доступной к моменту решения информации
`I` задаёт совместимое с ней множество моделей `M(I)`, преобразует его в точное
значение, идентифицированное множество либо проверяемую границу совместимой с
DEC-001 вероятности `F_A(t0,T;μ_t0)`, определяет допустимые и робастно допустимые
управляющие действия при явно заданном reliability constraint и выбирает
`T_scrub` по объявленному правилу с измеримым resource-cost vector; при каких
условиях дефицит или уточнение информации изменяет либо не изменяет множество
допустимых действий, выбранный `T_scrub` и ресурсное следствие решения?

## Why it matters

Цель диссертации требует не только корректной error/reliability model, но и
реального адаптивного решения о периоде восстановления. RQ-002 и RQ-006
определяют допустимые модели и информационные редукции, RQ-003 — ECC semantics,
RQ-004 — доступные online observations, RQ-005 — измеримые затраты. Без общего
risk-to-action interface эти результаты остаются разрозненными и не дают
проверяемого метода адаптивного управления.

Вопрос также нужен для точного определения **ресурсной цены дефицита
информации**: более широкое `M(I)` может вынудить более консервативное действие,
но само по себе отличие `F_A` ещё не означает отличие управления.

## Scope

1. Доступная к моменту решения внешняя и/или внутренняя информация `I`, включая
   provenance, разрешение, latency, uncertainty и отсутствующие компоненты.
2. Явное построение непустого множества совместимых моделей `M(I)` из
   RQ-002/RQ-006 interfaces без молчаливого смешения разных underlying physical
   domains.
3. Преобразование `M(I)` для каждого action в точное значение,
   идентифицированное множество, доказанную границу или контролируемую ошибку
   `F_A(t0,T;μ_t0)` с DEC-001 semantics.
4. Основной control variable — `T_scrub`; множество действий, update moments,
   feasibility semantics, selection rule и tie-break rule объявляются явно.
5. Exact/model, estimated и robust feasibility; uncertainty representation,
   model и observation отделяется от Monte Carlo/numerical error и
   conservatism принятого confidence/decision rule.
6. Области условной инвариантности и изменения допустимого/выбранного действия
   относительно объявленных `epsilon`, reporting window, initial state,
   action set, selection rule и resource criterion.
7. Покомпонентный resource-cost vector, достаточный для сравнения управляющих
   действий в analytical model, simulation и последующей RTL/FPGA evaluation.
8. Сопоставление с fixed conservative restoration и принятыми bounded
   adaptive-control baselines без автоматического novelty claim.
9. Computational tractability и явный interface к будущей controller
   architecture/implementation.

## Three resource objects that must remain separate

1. **Control-resource price of information deficit** — покомпонентное ресурсное
   следствие более консервативного управляющего действия, вызванного более
   широким `M(I)` при coarse information.
2. **Information-acquisition cost** — отдельные аппаратные, энергетические,
   вычислительные и коммуникационные затраты получения, хранения и обработки
   более богатой информации.
3. **Net information balance** — возможный последующий общий баланс первых двух
   объектов только при совместимых units и явно принятом aggregation/decision
   rule.

Разность затрат между двумя выбранными `T_scrub` не называется полной
«ценностью информации». До решения RQ-005 объекты сообщаются раздельно,
покомпонентно или как Pareto shift, без произвольной scalarization.

## Exclusions

- общий тезис «более богатая информация всегда необходима/лучше»;
- предположение, что полная physical topology или полный `W` всегда наблюдаемы;
- повторное решение arrival/event/state и mapping-sufficiency задач RQ-002 и
  RQ-006 внутри control RQ;
- отождествление `E_cap` с DUE, SDC, miscorrection или system-visible failure;
  эти outcomes остаются ответственностью RQ-003;
- выбор конкретного sensor, estimator или predictor без RQ-004 evidence;
- generic chain `fault/radiation estimate → dynamic scrub frequency` как
  научный результат или novelty claim;
- заранее выбранная stochastic model, control law, scalar objective или
  arbitrary weights;
- назначение численных `H_req` или `epsilon_req` без traceable provenance;
- автоматическое расширение action vector за пределы `T_scrub`; такое
  расширение требует отдельного обоснования;
- включение permanent faults, cumulative TID degradation, destructive SEE/SEFI
  или других persistent mechanisms без отдельного scope decision;
- представление RTL само по себе как scientific novelty;
- literature-level novelty/non-novelty conclusion по одному bounded prior-art
  family.

## Dependencies and owned interfaces

| Input | What RQ-007 consumes | What remains owned elsewhere |
|---|---|---|
| DEC-001 / RQ-001 | `E_cap`, `A`, `F_A(t0,T;μ_t0)`, horizon and initial-state contract | DUE/SDC/system consequence and numerical project requirement remain open |
| DEC-002 | Single evidence → reliability → adaptive-decision architecture | Novelty is not implied |
| RQ-002 | Declared arrival/event/state family, accumulation, reset and uncertainty semantics | Universal minimum stochastic family |
| RQ-006 | `W` family, information projections and exact/bound/approximation relations | Universal need for full topology or a target-specific sufficiency claim |
| RQ-003 | Parameterized ECC state/capability and labelled decoder outcomes | Final code and full service-outcome model |
| RQ-004 | Observable channels, timing, latency, identifiability and uncertainty | Final sensor/estimator selection |
| RQ-005 | Operational resource components, units/proxies and measurement stage | Arbitrary scalarization or final platform limits |
| RES-001 | Bounded proof that a model set can induce a non-singleton `F_A` set and conditional action consequences | General physical-SRAM conclusion |
| Accepted next gate | `I → M(I) → F_A → actions → T_scrub → costs` contract and completion rules | New EXP authorization |
| Bounded prior art | Controlled occupied method/reconstruction features and baselines | Literature-level novelty decision |

RQ-007 owns the **integration and adaptive decision law/interface**. It consumes
the upstream RQ outputs but does not absorb or close them.

## Accepted basis, working assumptions and unknowns

### Accepted basis

- adaptive restoration-period control remains the central dissertation layer;
- `F_A` uses DEC-001 event, aggregate, start-time, horizon and initial-state
  semantics;
- the Chen S3/S4/S5 family occupies generic fault-count/prediction or reactive
  assessment → adaptive restoration-frequency selection;
- RES-001 is a bounded foundational result, not a physical-domain answer;
- resource components remain a vector until RQ-005 supports anything stronger.

### Working assumptions to test, not conclusions

- at least one physically defensible event/`W` family can support nested
  information states and nonempty `M(I)` sets;
- risk sets/bounds can be evaluated with sufficient accuracy to separate model
  uncertainty from numerical error;
- at least one declared decision rule can map reliability information to an
  implementable `T_scrub` action without inventing a project requirement.

### Unknown / TBD

- numerical `H_req` and `epsilon_req`;
- final ECC and decoder/service outcomes;
- final external/internal observable channels and estimator;
- target SRAM/FPGA organization and interleaving;
- whether information refinement materially changes action in a physically
  plausible domain;
- whether a guaranteed bound, controlled approximation or only an identified
  set is attainable for each reduction;
- final resource objective, any scalarization and acquisition-cost model;
- literature-level novelty and the final dissertation proposition.

## Evidence required

1. Completion of only PA-DOM-01…04 under the accepted hard stop rule.
2. Accepted bounded Russian normative and Chen comparison artefacts as practical
   and closest-control baselines, without claims beyond their scope.
3. At least one source-constrained event/topology family and one source- or
   architecture-constrained `W` family.
4. Controlled information states derived as reductions of common underlying
   models, including realistic test/diagnostic or memory-controller outputs.
5. An explicit RQ-003 parameterized ECC capability/state slice.
6. At least one external/test-derived and one internal-memory observation
   interface with uncertainty/latency semantics, or a recorded reason one is
   deferred from the first bounded execution.
7. Exact derivation, verified bounds or independently validated computation of
   the induced `F_A` object for every tested action.
8. Reproducible decision and component-wise resource comparison against a fixed
   conservative baseline and the relevant controlled prior-art baseline.
9. Adversarial Scientific Reviewer disposition before any permanent result.

## Answer / decision criterion

RQ-007 may be considered answered only when a declared applicability domain has
all of the following:

1. `I` and every `M(I)` are operationally defined, nonempty and traceable to
   observations, assumptions and uncertainty.
2. For every candidate action, the method returns an exact `F_A`, an identified
   set, a proven bound or a controlled-error approximation with a stated
   validity domain.
3. Exact/model, estimated and robust feasible-action sets are distinguished.
4. The adaptive update and selection rule produces an implementable `T_scrub`
   and preserves the declared reliability semantics.
5. Conditional action-invariance and action-change regions are reported over
   `epsilon`, horizon, initial state, action set, decision rule and resource
   criterion; no point result is generalized beyond that contract.
6. The control-resource price of information deficit is reported separately
   from information-acquisition cost; any net balance is explicitly justified.
7. Negative, zero, infeasible and unresolved outcomes are retained rather than
   forcing a benefit from richer information or adaptivity.
8. The result is compared with fixed and controlled close-prior-art baselines,
   reproduced from registered artefacts and accepted by Scientific Reviewer.
9. The method exposes the interfaces needed for controller architecture and
   future RTL/resource/timing validation.

A partial answer is permitted when an exact named dependency remains open, but
it must identify the blocked interface and cannot be promoted to a general
adaptive-control claim.

## Expected outputs

- a formal information-state/model-set-to-action method;
- exactness, bound, approximation-error or non-identification conditions;
- maps of robust feasibility and conditional action invariance/change;
- a component-wise control-resource-price result;
- a separate information-acquisition-cost interface and, only if justified,
  net balance;
- reproducible quantitative evidence over a physically defensible domain;
- an implementation-facing controller contract;
- bounded `RES-xxx` candidates, not automatic novelty claims.

## Alternatives considered

1. **Point-estimate controller only.** Rejected as the RQ definition because it
   suppresses the accepted model/observation uncertainty object; it may remain
   a baseline.
2. **Require full physical topology and complete `W`.** Rejected as an a priori
   requirement because observability and sufficiency are open RQ-006 questions.
3. **Make cost optimization a separate immediate RQ.** Deferred: RQ-005 first
   defines measurable components; RQ-007 may use an explicit bounded selection
   rule without claiming a final scalar objective.
4. **Broaden the action vector now.** Deferred to avoid splitting the project;
   `T_scrub` remains the primary source-controlled decision variable.

## Revisit or split conditions

Revisit the wording, rather than silently expanding it, if accepted evidence
shows that:

- no common risk-to-action method can support the required external and
  internal information channels without incompatible state definitions;
- an additional control variable is essential to answer the source-level goal;
- decoder/service outcome semantics make `E_cap` inadequate for the selected
  control decision;
- the resource components cannot be compared without a new, separately
  justified optimization decision;
- the physically defensible domain cannot be defined without a specific target
  device/PMI/architecture supplied by PI.

## Next action after PI disposition

- `ACCEPT`: register the question as
  `docs/questions/RQ-007-integrated-adaptive-restoration-control.md`, update the
  Research Questions registry, then execute only the accepted PA-DOM-01…04
  closure. After closure, present the exact next experiment/derivation for
  separate PI approval before execution.
- `REVISE`: change only the named scope, dependency or criterion and resubmit;
  do not register RQ-007 or launch a new EXP.
- `REJECT`: retain no permanent RQ identifier and return to the accepted gate
  for an alternative decomposition.

## Related artefacts

- Decisions: DEC-001, DEC-002, DEC-003.
- Questions: RQ-001…RQ-006.
- Result: RES-001.
- Gate: `NEXT-QUANTITATIVE-GATE-information-deficit-control-price` — accepted.
- Prior art: Russian normative baseline; Chen S3/S4/S5 Evidence Audit;
  PA-DOM-01…04 pending.
- HYP/EXP/RES: no new identifier created by this candidate.

## Candidate answer

`UNKNOWN`.

## Confidence

Not assessed; this is a question formulation, not an evidence conclusion.

## PI decision requested

Choose one: `ACCEPT / REVISE / REJECT` for the exact proposed wording,
boundaries and permanent ID `RQ-007`.
