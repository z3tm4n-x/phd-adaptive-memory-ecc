# RE-CY62167-EXECUTOR-TIMING-GATE-01

HANDOFF

From: Research Orchestrator.

To: **постоянный Research Engineer в отдельной сессии через пользователя**.

Task ID: RE-CY62167-EXECUTOR-TIMING-GATE-01.

Related: Issue №15; DEC-001, DEC-002, DEC-004; RQ-001, RQ-003, RQ-006.

Дата постановки: 2026-09-15.

Статус при постановке: **PREPARED FOR TRANSFER / NOT STARTED**.
Точная выданная версия сохранена на be6b447e1c2ee7b70e68604fd135b379a800e62f.

**Актуализация 2026-09-15:** Stage 0 выполнен в поставке
003c2346c4135b3d2f24dac0981e60cb2f179384 и [принят Orchestrator как входной аудит](CY62167-EXECUTOR-TIMING-STAGE0-DISPOSITION-01.md).
Итог **BLOCKED_INPUT / NOT_ESTABLISHED**; Stage 1 не начат. Продолжение требует
конкретных новых входов T1–T3/S1–S2 и решения по ним. Технические условия
исходного задания ниже сохранены; прежние формулировки NOT STARTED внутри
исторического уточнения не обозначают состояние Stage 0 после этой поставки.

**Действующее дополнение после Stage 0:** [CY62167-REFERENCE-SUBSYSTEM-01](CY62167-REFERENCE-SUBSYSTEM-01.md)
фиксирует один проект AC701 + 3×CY62167GE30, packing/слоты/подготовку и явно
разрешает reference-continuation-01. Оно меняет локальные start/read/clock/ERR
условия и допускает минимальную реализацию/новый условный upper; это не объявление
прохождения прежнего gate. Исторические запреты/условия ниже действуют с указанными
в дополнении исключениями только для этого продолжения.

**Итог 2026-09-16:** reference-продолжение RE 3dc58a5f и отдельный SR 4b8aa6ae
выполнены. [Disposition](CY62167-EXECUTOR-REFERENCE-SR-DISPOSITION-01.md)
ограниченно принимает условный сертификат с поправками B_H и 48-pin TSOP I;
reference-subgate закрыт. Физическая квалификация остаётся NOT_ESTABLISHED.
Текст ниже сохраняет исходную постановку, не назначает повторное исполнение.

Каноническая документальная база:
**a8b04eff258401233a1aa038862c71daa4f01072**. Рабочую ветку начать от
этого commit либо от его обычного merge-потомка в `main`; записать фактический
base SHA и отношение ancestry. Научные входы ниже всегда использовать по
точным SHA, а не по подвижным branch heads.

## 1. Один decision-changing вопрос

**Можно ли для одного конкретного минимального Fixed executor доказать полный
детерминированный upper pending correcting-write window, явно сопоставив
модельный check instant аппаратным read/latch/SEC-DED decode/conditional-write/
commit событиям, вместе с обоснованным clean/no-pending start, так чтобы этот
предел проходил принятую численную границу `Delta <= Delta_star`? Если нет,
является ли результатом непрохождение конкретного executor или точный
отсутствующий backend/platform input?**

Это ранний gate физического переноса. Он не принимает устройство и не строит
coverage upper. Его ценность — отделить проверяемую timing/start осуществимость
от дорогого joint coverage этапа: при `Delta > Delta_star` текущая sufficient
upper не имеет неотрицательного остатка даже при условном нулевом coverage.

**Связь с диссертацией — уточнение 2026-09-15:** это предварительная прикладная
проверка для положений 1 и 4 DEC-004, а не отдельное фундаментальное положение.
Она решает, имеет ли смысл продолжать физический перенос этой Fixed с данной
достаточной оценкой, и даёт исполнительное основание либо точный препятствующий
вход. Основной научный пробел после неё — совместный количественный контракт
physical parents → registration → W → data+parity → E_cap, включая смешанные
неохваченные пути. [Рабочая концепция](../dissertation_concept.md) объясняет связь
с требованиями к данным испытаний и методикой выбора класса. При положительном
ответе следующим предметом становится joint coverage; иные ответы требуют
решения об исполнителе/оценке/входе по классификации задания. Уточнение не меняет
научные входы, критерии, объём работ и статус NOT STARTED.

## 2. Canonical sources

Прочитать global rules, роль Research Engineer, HANDOFF_CONTRACTS, DEC-004,
current status, research spec и [Orchestrator disposition](CY62167-COVERAGE-THRESHOLD-SR-DISPOSITION-01.md).

Контролирующие версии:

- published numerical target
  **a9d9b74b9ac03a4eb20b209eb14552d5b914e21a**,
  `experiments/RE-CY62167-COVERAGE-THRESHOLD-01/`;
- [coverage-threshold Review](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/d29b95f2b913055cc54cd657b8f3f3d6195a02fc/docs/scientific_reviews/CY62167_COVERAGE_THRESHOLD_REVIEW_01.md),
  **d29b95f2b913055cc54cd657b8f3f3d6195a02fc**, особенно §§4, 7, 8;
- [SR-03 disposition](CY62167-PHYSICAL-BRIDGE-SR-03-DISPOSITION.md) и
  [SR-03 52bb60e5](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/52bb60e516a85f5a0ba10a8b3935285a9c6c25d2/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_03.md);
- локальная инженерная основа:
  [ENGINEERING-APPLICABILITY-SR-DISPOSITION-01](ENGINEERING-APPLICABILITY-SR-DISPOSITION-01.md)
  и её exact RE/SR versions;
- старый implementation только на
  [cf7ab706224f7872fdafcf34febda70e3f6c8dd1](https://github.com/z3tm4n-x/chapter4-risk-limited-scrubber/tree/cf7ab706224f7872fdafcf34febda70e3f6c8dd1),
  прежде всего `rtl/scrubber/scrub_pass_engine.sv`,
  `docs/model_rtl_contract.md`, `configs/ch4_hardware_timing.json` и
  `results/vivado_ooc/`;
- применяемые datasheet/board/tool reports — только с точной identity,
  revision, operating corner и source location. Если требуемого полного текста
  нет в доступных источниках, вернуть input gap, а не реконструировать числа.

## 3. Known, assumed, unknown

### KNOWN

- В принятой frozen-input registered data-only модели `2^19` model words по
  32 data bits; полный 39-bit codeword executor нужен как implementation
  candidate, но его physical parity/W packing численной моделью не установлен.
  В этой модели
  `a_upper=0.0003098157772336203819978391463469440873` и
  `b_upper=2528.1037181797039690725 s^-1`.
- При `epsilon_analysis=0.001` exact boundary:

```text
Delta_star = 6901842227663796180021608536530559127 /
             25281037181797039690725000000000000000000000 seconds.
```

  Безопасное decimal-down значение —
  `0.0000002730047101324343639986193957750873 s`.
- `Delta` — общий **детерминированный upper** pending correcting-write window
  в смысле SR-03/coverage Review. Среднее, percentile, один trace, warmed CPU
  timing или наблюдённое значение его не заменяют.
- `cf7ab706` содержит 39-bit SEC-DED scrub RTL и OOC timing для controller
  cores. Его внешний memory subsystem не входит в OOC implementation.
  `scrub_pass_engine.sv` использует текущий `mem_read_data` без принятого
  стабильного latch/confirmed-commit контракта; поэтому его существующие cycle
  counts сами по себе не являются нужным proof.
- Datasheet minimum write-cycle порядка 45 ns — нижнее требование к
  формированию цикла, не измеренный end-to-end WCET.

### ASSUMED ONLY FOR THIS TASK

- Неизменны `tau=1 s`, check phases и численная формула принятого disposition.
  Их не оптимизировать ради положительного ответа.
- Рассматривается минимальный Fixed baseline; adaptive bank, RES-003/004
  вычислитель и новый policy не входят.
- Любое параметрическое timing выражение допустимо как инженерный промежуточный
  результат, но абсолютный `Delta` нельзя объявлять доказанным до подстановки
  квалифицированных upper inputs.

### UNKNOWN AT HANDOFF

- точный controller device/clock/tool corner, board и физический memory backend;
- packing полного 39-bit codeword по CY62167 components и число/параллельность
  bus transactions;
- максимальные read/data-valid, setup/hold/write/turnaround и IO/CDC задержки,
  arbitration/stall bound, commit/ack semantics;
- процедура, которая устанавливает clean memory для всего моделируемого
  массива в один объявленный `H` start, и доказательство отсутствия pending
  transaction. Controller reset либо завершение последовательной инициализации
  не считать автоматически глобальным clean start;
- проходит ли полный bound exact `Delta_star`.

## 4. Required action

### Stage 0 — input gate до реализации

1. Инвентаризировать exact sources одного candidate executor и построить
   таблицу `required timing fact → source/revision/corner → upper/minimum/
   measurement/unknown → decision use`.
2. Зафиксировать физическую границу интерфейса: какие компоненты образуют один
   39-bit codeword, какие операции последовательны/параллельны, где начинается
   model check instant и какой observable event означает completed commit.
3. Проверить, достаточно ли источников для абсолютного bound. При отсутствии
   хотя бы одного decision-critical upper, arbitration bound, platform identity
   или start premise остановиться с **BLOCKED_INPUT / NOT_ESTABLISHED**.
   Указать минимальный конкретный input, допустимые значения которого меняют
   решение. Не писать RTL, не выполнять synthesis и не подставлять удобное
   число после такого stop.

### Stage 1 — timing/start contract, только если Stage 0 проходит

4. До вычисления результата зафиксировать config, exact source identities,
   definition of `Delta`, критерии и scripts отдельным pre-execution commit.
5. Построить полный worst-case transaction timeline и явное отображение на
   `c_wk` SR-03. В `Delta` включить все аппаратные этапы после выбранного
   check instant до commit: стабильный latch полного codeword,
   combinational/sequential SEC-DED, decision, bus turnaround, conditional
   write pulse/data hold, controller/bus stalls и событие необратимого
   завершения записи. Если read request/data-valid предшествуют `c_wk`, их
   bound должен оставаться в inter-check/scheduler contract и не может быть
   скрыт; если hardware check instant определён раньше, они входят в `Delta`.
   Каждая слагаемая получает доказанный upper либо controlled cycle count;
   minimum requirements не суммируются как WCET.
6. Показать, что singleton записывается из защёлкнутого clean image, чистое
   слово не записывается, запись безусловно завершается после принятия, а
   следующий check того же слова не начинается раньше commit. Проверить
   boundary/equality и худший арбитраж, не только nominal trace.
7. Задать start protocol. Отдельно доказать `no pending write` и основание
   `clean memory` для всего объявленного массива в model-H start. Если
   последовательная initialization оставляет ранние слова под экспозицией,
   оплатить/смоделировать эту предысторию либо вернуть clean-start
   NOT_ESTABLISHED; запрещён бесплатный одновременный reset всего массива.
8. Вычислить exact/rational `Delta_upper`, безопасное округление вверх и
   сравнение с exact `Delta_star`. Если `Delta_upper <= Delta_star`, вычислить
   `s(Delta_upper)=0.001-a_upper-b_upper*Delta_upper` через отдельный маленький
   checker. Это только remaining coverage requirement, не оценка coverage.
9. Провести независимую адресную проверку без импорта основного calculator:
   units, cycle-to-time, sequential/parallel composition, corner selection,
   equality/one-tick-above, injected maximum stall, pending-at-reset и failed
   commit. Конечные tests поддерживают implementation; общность bound должна
   следовать из контракта.

Минимальное изменение старого executor допустимо только если оно необходимо
для latch/commit witness и все Stage-0 inputs уже достаточны. Его выполнять в
новом каталоге/ветке, не переписывая `cf7ab706` или прежние PhD packages.

## 5. Обязательная классификация результата

Вернуть раздельно:

- **SUFFICIENT FOR THIS TIMING GATE** — только если полный deterministic
  `Delta_upper <= Delta_star`, start contract и все boundary conditions
  установлены;
- **CANDIDATE NOT CERTIFIED BY THIS UPPER** — если доказанный upper больше
  порога, но нет lower bound, исключающего более быструю реализацию;
- **INSUFFICIENT FOR THIS EXECUTOR** — только если доказанный необходимый lower
  bound уже больше `Delta_star` либо иной обязательный контракт невозможен;
- **NOT_ESTABLISHED / BLOCKED_INPUT** — если отсутствует exact platform,
  backend, timing upper, arbitration/commit или clean-start evidence.

Не объединять timing и start в один общий PASS: каждый получает отдельный
статус. Положительный timing результат не принимает physical Fixed без joint
coverage upper. Непрохождение текущей sufficient upper не доказывает
физическую невозможность защиты или невозможность всех Fixed.

## 6. Expected output и проверка

Если Stage 0 блокирован, достаточно пропорционального пакета:

- `REPORT.md` и короткий `HANDOFF.md`;
- `timing_input_gate.json` с exact identities, статусами и минимальными
  decision-changing inputs;
- `MANIFEST.json` и execution/provenance record без фиктивных PASS.

Если Stage 0 проходит, дополнительно нужны:

- `executor_timing_contract.md` и machine-readable config;
- timeline/component table с units, upper provenance и composition rule;
- минимальный неизменяемый implementation witness, если он действительно нужен;
- основной bound calculator, независимый checker, tests и компактные outputs;
- exact `Delta_upper`, safe upward decimal, comparison with exact fraction,
  signed coverage slack и отдельный clean-start disposition;
- failures, tool/environment versions, commands, hashes и factual diff.

Перед передачей проверить published bytes, Git ancestry и отсутствие изменений
чужих packages/SR/RES. Собственные PASS counters RE остаются инженерной QA и не
являются Scientific Review.

## 7. Do not

- не менять `tau`, H, shielding, DREG, W32_seq, epsilon или rate slice;
- не повторять coverage-threshold calculation как новый научный результат;
- не начинать joint coverage, irradiation, new transport/GOES, Monte Carlo,
  новый W/mapping sweep или общий physical-bridge inventory;
- не выдавать OOC controller timing, nominal simulation, host benchmark,
  datasheet minimum, mean/percentile или отсутствие observed stalls за WCET;
- не предполагать atomic clean memory reset, confirmed commit, bus fairness,
  parity packing, platform clock/corner или physical W;
- не модифицировать main, RE/SR packages, DEC-004, RES-001…004 или старый
  `chapter4` repository; не присваивать PASS/RES и не закрывать Issue №15;
- не строить hardware stand и не расширять задачу до adaptive executor.

## 8. Where result belongs and closure

Публикация разрешена только в новой ветке
`research/cy62167-executor-timing-gate-01` и новом каталоге
`experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/`. В Issue №15 после готовности
оставить exact delivery SHA, base/ancestry, статус каждой части, команды,
артефакты и ограничения; Issue не закрывать.

Gate завершён, когда Orchestrator получает один воспроизводимый статус из §5
с точным основанием. Новый существенный timing/start claim после поставки
передаётся отдельному Scientific Reviewer. Чистый `BLOCKED_INPUT` сначала
разбирает Orchestrator; создавать SR только для подтверждения отсутствующего
файла не требуется.

При **SUFFICIENT** следующим отдельным научным звеном становится joint
physical-transfer coverage contract `Pr(V) <= s(Delta_upper)`. При иных исходах
сначала решается названный executor/input blocker; formal methodology,
аппаратура и новый общий цикл автоматически не запускаются.
