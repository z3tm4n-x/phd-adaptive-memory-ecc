# Research Specification

**Version:** 0.6-draft<br>
**Status:** WORKING DRAFT

> Документ фиксирует текущее состояние постановки исследования. Формулировки разделены по статусу: **SOURCE** — следует из утверждённого описания темы; **WORKING DEFINITION** — рабочая формализация проекта; **ASSUMPTION** — допущение, подлежащее проверке; **TBD** — вопрос сознательно оставлен открытым и должен быть разрешён последующим исследованием.

## 1. Идентификация исследования

- Специальность: 2.3.2 «Вычислительные системы и их элементы».
- Рабочая тема: «Разработка методов адаптивного управления системами коррекции ошибок в цифровой памяти вычислительных систем».

## 2. Исходная проблема

**SOURCE.** Непрерывность функционирования бортовых вычислительных систем зависит от сохранности информации в памяти. Радиационно-индуцированные искажения данных способны приводить к неисправимым ошибкам и отказам. Для противодействия используются помехоустойчивое кодирование, перемежение и периодическое восстановление памяти; период восстановления должен учитывать текущую радиационную обстановку.

**WORKING DEFINITION.** Исследование рассматривает задачу управления сбоеустойчивостью SRAM в части одиночных и связанных с ними многобитных ошибок памяти, при которой параметры восстановления/защиты должны адаптироваться к изменяющимся условиям и обеспечивать заданный уровень надёжности при приемлемых ресурсных затратах.

## 3. Объект исследования

**WORKING DEFINITION.** Подсистема SRAM вычислительной системы, защищённая средствами коррекции ошибок и периодического восстановления данных.

Границы объекта пока не привязаны к конкретной микросхеме SRAM или FPGA-платформе.

## 4. Предмет исследования

**WORKING DEFINITION.** Методы, модели и аппаратно-реализуемые алгоритмы адаптивного управления сбоеустойчивостью SRAM при возникновении ошибочных битов, включая управление периодическим восстановлением памяти и, при обоснованной необходимости, другими параметрами защиты.

**TBD.** Точный состав управляемых механизмов помимо периода scrubbing должен быть определён после анализа современного состояния области.

## 5. Цель

**SOURCE.** Разработка методов адаптивного управления периодом восстановления памяти, обеспечивающих непрерывность функционирования вычислительной системы при заданных требованиях к вероятности неисправимой ошибки и минимальных затратах ресурсов.

**WORKING DEFINITION.** В ходе исследования цель может быть уточнена от управления только периодом scrubbing к более общей задаче адаптивного проектирования/управления сбоеустойчивостью SRAM, если анализ литературы и результаты моделирования покажут обоснованность такого расширения.

### 5.1. Интегрированная архитектура метода

**WORKING DEFINITION / DEC-002.** Адаптивное управление остаётся центральным предметом диссертации. Радиационно-экспериментальная и стохастическая части формируют обоснованные входы для ECC-level reliability assessment, а не заменяют control layer.

Текущая причинно-расчётная архитектура:

`radiation tests → experimentally justified device-error representation → transformation through memory/ECC organization W → ECC-level reliability model → current/future risk assessment from online information → adaptive memory-restoration decision`.

Идентификация, ECC-aware reliability и adaptive control рассматриваются как три связанные слоя одного метода. Научная задача на их интерфейсе — установить, какая информация достаточна в принципе, какая реально идентифицируема из тестовых наблюдений и как её редукция изменяет reliability output и управляющее решение. Более богатое представление не считается автоматически необходимым или лучшим.

**TBD.** Эта архитектура является roadmap decision, а не утверждённым novelty claim. Её отличие от нормативной практики и closest prior art должно быть проверено отдельно.

## 6. Исследовательские вопросы

Зарегистрированы `RQ-001…RQ-006`; актуальные статусы фиксируются в `docs/current_status.md`.

- `RQ-001` — reliability event, metric and horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; working contract recorded as `DEC-001`.
- `RQ-002` — minimum adequate radiation-induced SRAM error model — Evidence Audit accepted with limitation; bounded `RES-001` registered, general adequacy remains open.
- `RQ-003` — ECC abstraction and decoder outcomes.
- `RQ-004` — online observables for adaptation.
- `RQ-005` — measurable resource-cost vector without premature scalarization.
- `RQ-006` — physical-to-logical mapping `W`, interleaving and information-sufficiency conditions — permanently promoted from C-RQ-05; bounded `RES-001` registered, physically defensible generalization remains open.

RQ-001 is not closed: decoder/system outcomes, quantitative requirements and downstream model dependencies remain open.

The C-RQ-05 escalation is resolved by permanent RQ-006. RQ-002 and RQ-006 are coupled through EXP-001 but retain separate responsibilities. An integrated adaptive-control RQ must later consume the outputs of RQ-002…RQ-006 rather than duplicate or replace them.

## 7. Исходные допущения

### 7.1. Тип памяти

**WORKING DEFINITION.** Основной объект — SRAM.

### 7.2. Код коррекции ошибок

**WORKING DEFINITION.** Стартовый класс — коды с исправлением одиночной ошибки (SEC). SEC-DED рассматривается как естественное расширение, если детектирование двойной ошибки существенно для постановки задачи и метрик надёжности.

**TBD.** До анализа литературы не фиксировать конкретный код как окончательный. Необходимо установить, какие ECC-модели наиболее актуальны для современной SRAM и задач радиационной стойкости и насколько полезно обобщение результатов на различные коды.

### 7.3. Scrubbing

**WORKING DEFINITION.** Scrubbing понимается как периодический цикл чтения кодового слова из памяти, проверки/коррекции средствами ECC и обратной записи исправленного значения при необходимости.

### 7.4. Ошибки

**WORKING DEFINITION.** Центральный интерес — transient radiation-induced upsets, проявляющиеся как ошибочные биты в памяти. Accepted RQ-002 evidence requires same-parent multiplicity/topology and independent accumulation to remain distinguishable until their reduction through `W` is justified. Permanent faults, cumulative TID degradation and destructive/persistent mechanisms remain out of the base model unless separately reopened.

### 7.5. Стационарность и распределение ошибок

**TBD.** Не принимать заранее пуассоновскую, независимую или иную конкретную модель как установленную. DEC-003 authorizes an event-driven parent-event-preserving comparison reference and controlled HPP/time-varying scenarios for EXP-001, but this does not select a target stochastic family. Minimum adequacy remains an empirical/analytical result to be established over a declared validity domain.

### 7.6. Reliability event, aggregate and horizon contract

**WORKING DEFINITION / DEC-001.** Primitive event — `E_cap`: existence, within reporting window \(H(t_0,T)=[t_0,t_0+T]\), of at least one codeword in declared controller-managed SRAM protection domain \(A\) whose current distinct-error multiplicity exceeds the declared ECC correction capability.

**WORKING DEFINITION.** General metric — \(F_A(t_0,T;\mu_{t_0})\). The initial state/distribution \(\mu_{t_0}\) and nonstationary start-time semantics are mandatory parts of a quantitative model. \(F_A(T)\) is only a shorthand for an explicit origin and initial state.

**WORKING DEFINITION.** If ECC, mapping \(W\), arrival process, bank/block semantics or scrubbing semantics differ inside \(A\), partition \(A\) before aggregation and state the dependence model between partitions.

**WORKING DEFINITION / MODELING REQUIREMENT.** Upset-count, per-codeword exposure, reporting-window and mission horizons remain distinct. Sequential exposure semantics are not claimed as a literature-established fact; CAND-10 remains deferred.

**TBD.** `E_cap` is not automatically DUE, SDC, miscorrection or system-visible failure. Decoder outcomes belong to RQ-003. \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) require traceable system/mission provenance.

## 8. Входные параметры и наблюдаемые величины

**SOURCE / WORKING DEFINITION:**

- параметры радиационной обстановки или производная от них оценка интенсивности ошибок;
- параметры организации SRAM;
- параметры ECC;
- состояние/статистика ошибок памяти;
- параметры режима восстановления.

**TBD — ключевой исследовательский вопрос.** Как именно контроллер получает оперативную информацию для адаптации:

- внешний источник/датчик радиационной обстановки;
- модель/прогноз радиационной среды;
- счётчики исправленных ошибок памяти;
- комбинация физических и внутренних наблюдений;
- иной механизм.

COSRAD рассматривается как источник предметно обоснованных сценариев и данных для исследования, но его роль как прямого источника информации для реального контроллера не предполагается без дополнительного обоснования.

## 9. Управляемые параметры

**SOURCE.** Основной управляемый параметр — период восстановления памяти (`T_scrub`).

**WORKING DEFINITION.** Исследование допускает расширение набора управляемых параметров в рамках проектирования сбоеустойчивости SRAM, если это даст самостоятельный обоснованный результат.

**TBD.** Определить по литературе и моделированию, имеет ли смысл адаптация:

- периода scrubbing;
- режима/параметров ECC;
- interleaving;
- порогов или режимов работы контроллера;
- иных механизмов.

## 10. Критерии и ограничения

**SOURCE.** Базовое ограничение — заданное требование к вероятности неисправимой ошибки. Базовая цель оптимизации — минимизация затрат ресурсов на восстановление.

**WORKING DEFINITION / DEC-001.** Пока decoder/system semantics не определены, quantitative reliability contract uses `E_cap` and \(F_A(t_0,T;\mu_{t_0})\). A future constraint may use \(F_A(t_{0,\mathrm{req}},T_{\mathrm{req}};\mu_{t_{0,\mathrm{req}}})\le\varepsilon_{\mathrm{req}}\), but the reporting window, initial state and numerical bound remain `TBD` until traceable requirements are available.

**TBD — ключевой исследовательский вопрос.** Функция затрат пока не фиксируется. Необходимо определить, какие компоненты являются существенными и измеримыми:

- число/частота операций scrubbing;
- дополнительный трафик и использование пропускной способности памяти;
- latency/занятость интерфейса памяти;
- энергопотребление;
- аппаратные ресурсы контроллера;
- производительность вычислительной системы;
- комбинация перечисленных показателей.

Предпочтительно рассматривать многокритериальную картину до тех пор, пока не будет обоснован основной скалярный критерий или набор ограничений.

## 11. Базовые методы для сравнения

**TBD.** Baselines должны быть выбраны после обзора литературы. Минимально предполагается наличие fixed/non-adaptive strategy для сравнения с предлагаемым adaptive approach.

**WORKING DEFINITION / DEC-002.** Applicable Russian normative practice is a primary engineering baseline for the radiation-test → cross-section → environment convolution → event-rate/probability chain. The received bounded set is РД 134-0174-2009, РД 134-0175-2009 and СТО ГК Роскосмос 04.01.0005–2022. The STO explicitly raises a pre-aggregation functional-diagnosis/event-classification layer; whether address/topology/provenance information is retained or usable downstream remains open and PMI/software dependent. No deficiency is presumed before accepted extraction.

**PROVENANCE LIMIT.** The supplied STO file contains approval/registration/effective-date statements and also hidden `Проект, окончательная редакция` text. Its exact controlled revision remains ambiguous until official copy/registry evidence is provided.

The Chen/IHP/Potsdam S3/S4/S5 family has a bounded accepted full-text comparison and Evidence Audit. It is close prior art for fault-count/rate observation or prediction followed by adaptive restoration-frequency selection; the audit is not a novelty decision. Zebrev/Ogden/Gomi/Franco and related sources address a different identification/event-representation/mapping threat layer. The layers must be compared separately.

Не фиксировать конкретные baseline algorithms до подтверждения их распространённости и корректности для выбранной модели памяти.

## 12. Проверяемые гипотезы

Пока не заведены.

Гипотезы должны появляться только после первичного literature mapping. Каждая `HYP-xxx` должна иметь заранее заданный критерий опровержения и связь с `RQ-xxx` и будущими `EXP-xxx`.

## 13. Планируемые классы экспериментов

**WORKING DEFINITION.** На текущем этапе предполагаются следующие классы, без фиксации конкретных моделей:

1. аналитическое/численное моделирование вероятности исправимых и неисправимых ошибок;
2. Monte Carlo или иная вычислительная верификация аналитической модели;
3. controlled synthetic scenarios для отладки и проверки модели;
4. сценарии радиационной обстановки на основе COSRAD;
5. сравнительное исследование adaptive и baseline strategies;
6. sensitivity/robustness analysis;
7. аппаратная RTL-реализация выбранного метода;
8. функциональная верификация SystemVerilog/iVerilog;
9. синтез и оценка аппаратных затрат/временных характеристик в Vivado.

**REGISTERED / DEC-003.** [EXP-001](../experiments/EXP-001-event-representation-reduction-sensitivity.md) compares a declared hierarchy of device-error representations through the same `W`, ECC state and scrub semantics, then measures change in `F_A` and a parameterized restoration decision. Its `L0 → L1` full-topology-to-joint-post-`W` interface must be lossless for the declared state update; marginal/scalar reductions have no pre-assigned result direction. Unknown numerical reliability requirements are swept and not invented.

**COMPLETED / REGISTERED RESULT.** Scientific Review 02 returns `PASS` after
the independent-oracle repair and confirms closure of `MAJOR-01` and
`MINOR-01…04` without scientific-output regression. The PI accepts the exact
bounded wording, and
[`RES-001`](../results/RES-001-exp001-four-word-identified-set.md) is permanently
registered with its complete fourteen-condition validity domain. EXP-001 is
complete and promoted only within that result. No retrospective `HYP-xxx` is
created, and DEC-001…003 and the experiment question remain unchanged.

**NEXT GATE / NOT YET AUTHORIZED FOR EXECUTION.** The draft
[information-deficit control-price gate](research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md)
proposes the progression `I → M(I) → F_A value/set/bound → admissible actions →
T_scrub → measurable resource cost`. It requires a physically defensible
event/`W` domain, bounded domestic prior-art closure, minimum RQ-003/RQ-004/RQ-005
interfaces and permanent integrated-control RQ registration before a new EXP.

## 14. Критерии воспроизводимости

**WORKING DEFINITION.** Для каждого существенного `EXP-xxx` должны фиксироваться:

- commit SHA кода;
- конфигурация эксперимента;
- версии инструментов;
- происхождение входных данных;
- версия/параметры COSRAD для соответствующих сценариев;
- random seeds при стохастическом моделировании;
- используемые baselines и метрики;
- выходные данные и связь с `RES-xxx`/`FIG-xxx`.

## 15. Ожидаемые классы научных результатов

**SOURCE:**

- вероятностная аналитическая модель возникновения неисправимых ошибок;
- условия достижимости заданных требований;
- методы адаптивного управления периодом восстановления памяти;
- архитектура контроллера адаптивного восстановления памяти.

**WORKING DEFINITION.** Конкретные формулировки научной новизны не фиксируются до анализа состояния области и получения собственных результатов.

**WORKING DEFINITION / DEC-002.** Expected results must remain connected across the full chain. A candidate result on information reduction is scientifically useful only if it quantifies an effect, bound or invariance relevant to ECC-level reliability and the downstream adaptive decision.

**OWN RESULT / RES-001.** In its complete fourteen-condition synthetic
four-word domain, fixed two-distinct-word parent-event cardinality and identical
one-event per-word impact probabilities induce a nontrivial exact identified set
for `F_A` through admissible joint pair distributions. The endpoint difference
changes the exact admissible-action set at experimental `epsilon=0.15`, changes
the maximal feasible selected period at `0.25` and `0.35`, and leaves the exact
selected action unchanged at `0.55`. This is not a statement about arbitrary marginal
models, physical SRAM topology, a project reliability requirement or integrated
method novelty.

## 16. Связь результатов с публикациями и диссертацией

Планируется 3–5 научных статей, однако статьи не рассматриваются как независимые от исследования задачи. Каждая публикация должна соответствовать завершённому и проверенному исследовательскому результату (`RES-xxx`) либо связанной группе результатов.

Точная карта `RES → ART → thesis section` будет сформирована после появления первых результатов.

## 17. Открытые вопросы

### Высокий приоритет

1. Какой класс ECC является наиболее актуальным и научно оправданным baseline для SRAM в рассматриваемой задаче: SEC, SEC-DED или более общий класс кодов?
2. Какие модели радиационно-индуцированных ошибок SRAM применяются в современной литературе и каковы их границы применимости?
3. Как в реальной вычислительной системе получать оценку текущей интенсивности/риска ошибок, пригодную для adaptive control?
4. Какие параметры системы защиты, кроме `T_scrub`, целесообразно рассматривать как управляемые?
5. Как определить функцию/вектор ресурсных затрат так, чтобы он отражал реальную цену adaptive scrubbing и был измерим в моделировании и RTL/FPGA-реализации?
6. При каких условиях full topology, joint post-`W` marks, marginal word statistics или scalar rates достаточны для `E_cap/F_A`, и какова цена редукции для управляющего решения?
7. Какие fixed/adaptive approaches являются корректными baselines для сравнения?
8. Какая информация о physical radiation event достаточна после `W`, какая реально идентифицируема из тестовых наблюдений и как её редукция влияет на `F_A` и adaptive decision?
9. Что сохраняет и агрегирует применимая российская нормативная цепочка расчёта, и достаточны ли её выходы для ECC-aware reliability/adaptive control?

### Средний приоритет

10. Какие метрики аппаратной реализации необходимы для доказательства практической реализуемости метода?
11. Как связать COSRAD-сценарии с параметрами модели ошибок памяти без необоснованных преобразований?
12. Какой уровень обобщения результатов между различными организациями SRAM и ECC-кодами достижим без потери строгости?

## Change log

- `0.1-draft` — создан каркас документа.
- `0.2-draft` — зафиксированы рабочие границы: SRAM, стартовый класс SEC/SEC-DED, определение scrubbing, обязательная RTL/FPGA-верификация; источник управляющей информации, расширенный набор механизмов защиты и функция затрат оставлены как осознанные открытые вопросы исследования.
- `0.3-draft` — зарегистрирован DEC-001: primitive ECC-capability event, start-time-aware metric, declared/partitioned protection domain and layered horizon semantics; RQ-001 переведён в PARTIALLY ANSWERED, открыт gate RQ-002.
- `0.4-draft` — зарегистрирован DEC-002: сохранён adaptive-control core и введена единая evidence-to-decision architecture; information sufficiency отделена от experimental identifiability; Russian normative practice and layered closest-prior-art threats made explicit baselines; RQ-002 advanced to bounded model-selection after accepted Paper Cards and synthesis.
- `0.5-draft` — принят RQ-002 Evidence Audit with CAND-04 limitation; C-RQ-05 permanently promoted to RQ-006; DEC-003 registered the comparison reference/representation ladder and authorized EXP-001; three-document Russian normative source set and Chen identity record received bounded follow-up protocols without a broad search or novelty claim.
- `0.6-draft` — EXP-001 independent validation and Scientific Review 02 passed; PI-approved `RES-001` registered with its complete fourteen-condition domain; Chen S3/S4/S5 bounded audit incorporated; the next information-deficit control-price gate prepared without authorizing a new EXP, RQ, HYP or novelty claim.
