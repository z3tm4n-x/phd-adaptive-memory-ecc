# Chen 2023 — архитектура доказательств self-adaptive resilience

PAPER-ID: TBD until Orchestrator acceptance

Task: PA-CHEN-THESIS-STRATEGY-01. Related: RQ-004, RQ-005, RQ-007.
Версия отчёта: **1.0, 2026-09-11, DRAFT / NOT SCIENTIFICALLY ACCEPTED**.
Рекомендация: **CORE** как целевой архитектурный comparator; не доказательство необходимости прогнозирования или управления периодом восстановления SRAM.

## 0. Идентичность, контроль источника и границы работы

**SOURCE.** Junchao Chen, *A Self-adaptive Resilient Method for Implementing and Managing the High-reliability Processing System*, doctoral dissertation, Universität Potsdam, 2023. DOI: [10.25932/publishup-58313](https://doi.org/10.25932/publishup-58313). На титуле: Potsdam, 03.02.2023; университетский URN: `urn:nbn:de:kobv:517-opus4-583139`.

Фактически прочитан предоставленный `thesis-chen-junchao-2023-03-14.pdf`: 192 PDF-страницы, 10 452 584 bytes; SHA-256 `15485850b9d2f01c85110c0e65e65385b4c4791da99be4d6df604fa2eaf86949`. Первая PDF-страница — ResearchGate cover с DOI и указанием загрузки Junchao Chen 19 March 2023; титул — PDF p. 2. Метаданные файла: создание/изменение 14 March 2023, producer iLovePDF. **Это supplied author-uploaded copy, не вновь сверенная побайтно официальная университетская копия.** Дата в имени файла не объявляется датой защиты или новой редакцией научного текста.

Все `с.` ниже — напечатанные арабские страницы диссертации; в проверенных основных главах соответствующая PDF-страница = с. + 25. Например, с. 96 = PDF 121; с. 132 = PDF 157; с. 143 = PDF 168. Полностью прочитаны главы 1, 4, 6, 7; в главе 5 — концепция, методы прогноза/реализации/оценки и адресные части построения среды (§§5.1, 5.3–5.6; необходимые §§5.2.1–5.2.3). Основные формулы и результаты на с. 96, 107–108, 124, 132, 137–138, 143 дополнительно сверены по изображению PDF. Это целевое чтение, не постраничный аудит всей библиографии.

Каноническая база инструкций/задела: `59603d231b923ee7426056cb62779a5ad16c8413`. Прочитаны GLOBAL OPERATING RULES, PAPER ANALYST, HANDOFF CONTRACTS, research_spec, DEC-002, RQ-004/005/007, research_lifecycle, PAPER-009/010/011 и CONTROL-PRIOR-ART-01 comparison. Оперативный контекст берётся отдельно из SCIENTIFIC_REVIEW_DISPOSITION на `a88d6a26c54c193e3d518fb16f43ffd19511202b` и FIXED_ADAPTIVE_FEASIBILITY_REVIEW_01 на `619492db33cb8793710fb4e454616f543993c982`: полная поставка REVISE, ограниченное cold-start принятие. Этот отчёт не расширяет RES-001…004, не возобновляет практическую ветвь RES-004 и не устанавливает дополнительную пользу RES-003.

`SOURCE` — содержание фактически прочитанного источника, включая явно названные авторские предположения; это не автоматическое подтверждение их истинности. `INFERENCE` — наш ограниченный вывод из метода. `UNKNOWN` — не установлено прочитанным текстом. Ссылки на другие работы в диссертации обозначают заимствованный автором материал, а не выполненный здесь анализ тех работ.

## 1. Research problem

**SOURCE — §§1.1–1.2, с. 2–5.** Статическая worst-case защита многопроцессора расходует ресурсы и в спокойной среде; SPE резко меняют радиационную обстановку. Инженерный вопрос автора: как обнаруживать/прогнозировать среду и менять защиту, сохраняя приемлемый баланс надёжности, производительности и мощности. Mixed-criticality даёт дополнительный мотив: требования задач могут различаться.

**INFERENCE.** Связность работы создаёт не само наличие ML, а физически понятная альтернативная роль одного ресурса: ядро может выполнять полезную независимую задачу, дублировать критическую задачу либо быть выключено. У переменной управления заранее виден сильный архитектурный эффект. Для `T_scrub` такой эффект нельзя считать уже установленным по аналогии.

## 2. Objective и карта вкладов

**SOURCE — §1.3, с. 5–6; §7.1, с. 147–148.** Автор выделяет три вклада: встроенный SRAM SEU-monitor; прогноз следующего часового SEU count с онлайн-подстройкой; SAFR — выбор режима многопроцессора по среде и требованиям.

| Звено общей цепочки | Собственный заявленный вклад и результат | Заимствованный аппарат/данные | Доказательная граница |
|---|---|---|---|
| Проблема → требования | **SOURCE:** разделение design-time hardening и runtime adaptation; режимные reliability LUT, пример SIL (§1.2, рис. 1.1; §6.3) | **SOURCE:** IEC 61508 используется как пример численного ориентира; готовые классы hardening | **INFERENCE:** не получены требования конкретной миссии и safety function |
| Мониторинг | **SOURCE:** EDAC + scrub + re-scrub + ODRF + counters + management stack (§4.2, рис. 4.3–4.7) | **SOURCE:** HSIAO(39,32); MCM SSRAM [SSC+19]; PULPissimo/RI5CY и TCMI (§4.3) | **SOURCE:** random-fault simulation и synthesis; ≥3 ошибки в слове ограничивают достоверность (§4.4.1) |
| Среда → обучающие SEU | **SOURCE:** обработка 36 SPE solar cycle 24, спектральная реконструкция и почасовые rates (§5.2) | **SOURCE:** GOES/ACE, CREME96, 65-nm Cypress cross sections из [VGU17] (§4.1; рис. 5.3, 5.6) | **INFERENCE:** исторические измерения частиц не являются измеренным in-flight SEU trace защищаемого прототипа |
| Прогноз | **SOURCE:** выбор линейной регрессии, fixed-point accelerator, SGD (§§5.3–5.5) | **SOURCE:** известные regression/SGD algorithms, Scikit-learn/Keras | **SOURCE:** прогнозные ошибки и синтез; **UNKNOWN:** отдельный системный выигрыш ML против measurement-only |
| Выбор и исполнение | **SOURCE:** SAFR LUT/threshold selection, controller registers, QMR voter integration (§6.1–6.3, рис. 6.4–6.8) | **SOURCE:** core-level NMR [ASI14], programmable voter [SHK+12], DVFS reliability model [FSW+11] | **SOURCE:** DVFS прямо назван theoretical evaluation (§6.3.2, с. 135) |
| Системный итог | **SOURCE:** расчёт времени в режимах и нормированных годовых ресурсов (§6.4, табл. 6.2–6.5) | **SOURCE:** историческая среда + принятые mode functions | **INFERENCE:** расчётная композиция компонентов, не продемонстрированный end-to-end hardware safety loop |

**INFERENCE.** Вклад следует приписывать Chen как представленный в диссертации, не объявляя единоличным создание всего SoC, SRAM, voters, ML или среды. Публикации команды перечислены в §1.5, с. 7–8; исключительное индивидуальное авторство каждого интеграционного блока из этого перечня не устанавливается.

## 3. System/model: три разных объекта

| Объект | Что защищается/наблюдается | Что действительно показано | Что не следует переносить |
|---|---|---|---|
| SRAM как память приложения | **SOURCE:** data + parity, исправление одиночных ошибок, обнаружение двойных, чтение/запись (§§4.2–4.3) | **SOURCE:** функциональная схема и fault-injection classification | **UNKNOWN:** memory mission failure probability, DEC-001 `F_A`, выигрыш adaptive `T_scrub` |
| SRAM как радиационный монитор | **SOURCE:** ошибки памяти → периодические counters/history → proxy среды (§4.2.4, с. 60) | **SOURCE:** чувствительность/разрешение, resource overhead, прогноз SEU | **INFERENCE:** fault count не равен parent-particle count; режим записи и ECC меняют наблюдаемость |
| Quad-core как объект управления | **SOURCE:** core grouping, gating, voltage/frequency → правильность выходов, parallel task capacity, power (§6.2) | **SOURCE:** режимные модели и среднегодовой расчёт | **INFERENCE:** освобождение 2–3 ядер не эквивалентно сокращению scrub traffic памяти |

**SOURCE.** Три технологических/масштабных случая также различаются: 65-nm Cypress для cross-section/rate; IHP 130-nm для SPICE/synthesis; внутренний SoC с 8 × 8192 × 40-bit L2 banks, внешний 20-Mbit MCM и модельный 2-Gbit монитор (§§4.1, 4.3–4.4, 5.3.1). **INFERENCE:** это не один физически квалифицированный 2-Gbit SAFR-чип.

## 4. Method и модальность доказательств

| Доказательство | Фактическая модальность | Достаточный и недопустимый вывод |
|---|---|---|
| Fe irradiation / ECC ON–OFF, табл. 4.6, с. 56 | **SOURCE:** воспроизведённые результаты [VGU17], не новые испытания Chen monitor | **INFERENCE:** показывает мотив ECC; не испытание всей предлагаемой системы |
| HSIAO/ODRF, §4.4.1, с. 66–67 | **SOURCE:** симуляции random soft/hard bit injection | **INFERENCE:** ограниченная функциональная проверка; не физическая MCU/parent-event калибровка |
| Cell/gate sensitivity, §4.4.2 | **SOURCE:** SPICE double-exponential current injection, rise 10 ps, fall 100 ps | **INFERENCE:** circuit sensitivity, не measured space reliability |
| Monitor/accelerator resources, §§4.4.3, 5.5.3 | **SOURCE:** synthesis estimates, IHP 130 nm, 1.2 V, 50 MHz | **INFERENCE:** не измеренная энергия годовой миссии |
| Predictor, §§5.3–5.5 | **SOURCE:** reconstructed hourly rates, train/test/CV, fixed-point function results, online-learning tests | **INFERENCE:** “Actual Upsets” на графиках — target reconstruction, не live monitor telemetry |
| Quad-core/controller, §§4.3.2, 6.2.1 | **SOURCE:** описана реализованная архитектура, маршрутизация, registers, voting | **UNKNOWN:** физическая демонстрация полного переходного процесса с workload/irradiation |
| SAFR benefit, §6.4 | **SOURCE:** analytic functions + historical mode occupancy + normalized annual sums | **INFERENCE:** интегрированная методическая цепочка есть; экспериментально замкнутый аппаратный контур со всеми uncertainties не установлен |

**INFERENCE.** Нельзя свести работу к «только концепции»: есть детальная реализационная часть и synthesis. Но нельзя и прочитать слова “implemented”/“100% reliability” как доказательство непрерывного монитор→forecast→decision→actuation→mission результата на изготовленном изделии.

## 5. Assumptions и reliability semantics

**SOURCE — с. 124–125, формулы (6.5)–(6.8).** Для одинаковых cores используется экспоненциальная reliability; далее perfect majority voter. DMR обеспечивает detection, но его correct-output reliability ниже одиночного ядра. QMR зависит от `P_d` — вероятности различия ошибочных выходов; в иллюстрации рис. 6.9 принято `P_d=1`, для предела 10120 на с. 132 — `P_d=0.99`.

**INFERENCE.** Биномиальные режимные формулы предполагают независимость модульных исходов; общая причина отказа нескольких cores не представлена отдельным измеренным членом. Возможность оценить `P_d` fault injection указана, но фактическая калибровка `P_d=0.99` для целевого workload не предъявлена. Правильный выход одного task/group не автоматически означает отсутствие отказа всей совокупности параллельных задач.

**SOURCE — §6.3, с. 129–132.** Счётчик за `T=1 hour` преобразуется через cross section в flux и далее номинальную system failure rate. Автор определяет `PFH_s=1−R_s(t), t=1 h` (6.29), таблицу SIL1 `10^-5…10^-6` и т.д. Принимаются: минимум SIL1; single core в background имеет `1−exp(−K_c)=10^-6`; промежуточный trigger `3×10^-6` — пример автора.

**INFERENCE.** Это условный one-hour probability proxy и модельный SIL-inspired threshold, а не проверенная IEC conformity/certification. Здесь не выполнен отдельный анализ действующих стандартов: вывод ограничен тем, что диссертация не определяет safety function/dangerous-failure coverage и не демонстрирует полный safety case. Не следует переносить численные SIL-границы в `H_req/epsilon_req` проекта.

**SOURCE — §6.4, с. 143–144.** “Reliability” табл. 6.5 — процент времени среднего года, когда mode model удовлетворяет принятому требованию. **INFERENCE:** не `P(no failure over year)`, не вероятность сохранности всех битов/слов, не `E_cap`, DUE, SDC или DEC-001 `F_A(t0,T;μ_t0)`. General initial memory distribution, word ages и mission accumulation этой метрики не определены.

### Одинаковы ли требования при сравнении?

**SOURCE.** Возможность relaxed image-transmission tasks обсуждается на с. 117, user-defined protection vs self-NMR — с. 122–123. Но численный пример §§6.3–6.4 применяет один минимальный SIL1 ко всем сравниваемым режимам. **INFERENCE:** основной эффект табл. 6.5 нельзя объяснить просто ослаблением SIL для SAFR. Одновременно требования к объёму полезной работы различаются между SAFR1 (один активный core в фоне) и SAFR2 (четыре): их нельзя считать двумя способами выполнить один и тот же фиксированный workload с одинаковыми deadlines. Межрежимное “optimal” — объявленная приоритетная policy, не доказанный глобальный оптимум всех feasible task schedules.

## 6. Inputs, observation и persistent state

**SOURCE — §§4.2–4.3.** Read-back scan, immediate re-scrub, три counters (single, double, permanent), ODRF addresses. Повторная single после re-scrub классифицируется как permanent; double/permanent address записывается, чтобы не считать повторно. Rewrite очищает соответствующую ODRF запись. Внешний вариант: 32 × 21-bit ODRF, три 8-bit counters; overflow oldest record eviction/status flag; management block не реализован и делегирован host. Внутренний вариант имеет bank-local EDAC и общий management history.

**SOURCE — с. 53, 59–60, 62, 64–65.** До overwrite требуется проверять старые данные для сохранения статистики; периодическая проверка, например раз в час; история хранит почасовые totals. User-configurable scrub word spacing ограничен частотой. Внутренний bank недоступен cores при detection; misaligned write требует read/merge/encode, дополнительный цикл. **INFERENCE:** наблюдения не бесплатны и зависят от execution semantics, а не только размера SRAM.

**SOURCE — §§5.3.1, 5.4.1.** Offline inputs: cross sections, reconstructed environment, SRAM size, shield assumption; online — история hourly counts. 17-sample regression начинает работать после первых 17 часов. Две 32 × 21-bit register files для history/coefficients; fixed-point arithmetic. Есть четырёхчасовой вариант (§5.5.1).

**UNKNOWN.** Единое правило перевода single/double/permanent counters в radiative bit-flip-only target обучающей выборки, parent-event association, физическая `W`, остаточные ≥3 ошибки, точная фаза общего collection/update/actuation, missing-data fallback и защита cold start целого контура. ODRF не восстанавливает физический parent event. TCMI address interleaving (с. 63) не является доказанной физической MCU→ECC mapping.

## 7. Outputs и точные количественные результаты

### 7.1 Память/монитор/вычислитель

| Величина | SOURCE: значение и условия | Знаменатель/граница |
|---|---|---|
| External full scan | ≈42 ms; 20-Mbit MCM, 50 MHz, 4 clocks/word, 2^19 addresses (§4.3.1, с. 61–62) | Полный проход; не measured service cost адаптивной policy |
| Internal write cost | +1 cycle для misaligned writing (§4.3.2, с. 65) | Событие такого доступа; “dozens” для Dhrystone без общего denominator не даёт slowdown % |
| Cell critical charge | SRAM 9.7 fC для “1”, 13.9 fC для “0”; DFF 24.9 fC (табл. 4.7, с. 69) | SPICE, IHP130nm, 1.2 V; не Cypress65nm irradiation |
| Digital controller without/with monitor | 18 706 / 95 739 µm²; 0.054 / 0.211 mW; 253 / 947 flip-flops (табл. 4.8–4.9, с. 70) | Именно digital baseline; “<1% overhead” использует существенно больший host SRAM denominator |
| Accelerator | 0.6363 mm², 3.629 mW; monitor 0.0957 mm², 0.211 mW; SRAM 14 mm², 384 mW (табл. 5.4, с. 113) | Synthesis130nm,1.2V,50MHz; авторские 4.55% area и0.95% power относительно SRAM; не относительно controller |
| Prediction compute | 262 cycles, 5.24 µs at50MHz для (5.7) (с. 104) | Раз в час, 17-term fixed-point predictor |
| Online parameter update | <3M cycles /0.06s at50MHz, при всех `x_j≤118122` (с. 106) | Заданный исторический max count, не universal WCET |
| Размер монитора | 4Mbit недостаточно для малого SPE; 20Mbit улучшает; около35Mbit рекомендовано для hourly background detection (с. 107–109) | Размеры масштабированы из65nm model; не гарантированный минимум для любого SRAM |

**INFERENCE.** Авторское условие “at least one SEU each hour” для≈35Mbit основано на расчётном rate; в тексте нет вероятностной гарантии ненулевого наблюдения каждого часа. Power-saving clock gating accelerator обсуждён на с. 113, но годовые Joules, duty-cycle trace и энергия переходов не измерены. Добавление отдельной чувствительной SRAM ради разрешения меняет acquisition-cost denominator и тезис reuse/no-overhead.

### 7.2 Прогноз: числа, а не обещание заранее обнаружить любой SPE

**SOURCE — с. 93–96.** 60/40 train/test; 10-fold CV; выбор history3…24h и hyperparameters. На рис. 5.15–5.16 есть R²/RMSE curves; точные агрегатные значения из графика здесь не оцифровываются. Автор выбирает17h linear regression,14h RNN optimum; не импортируем R²=0.94/0.95 из позднейших статей.

**SOURCE — рис. 5.23, с. 107 (визуально сверено):** Jan19–31,2012,2Gbit: (5.7) R²=0.9769, (5.11) R²=0.9741. **SOURCE — рис. 5.24, с. 108:** Mar7–15,2011,2Gbit:0.9745/0.9673;4Mbit:0.7495/0.8763. Это качество hourly-count prediction в указанных reconstructed episodes, не detection probability и не control benefit. RMSE на этих рисунках, согласно с.106, масштабирован по размеру SRAM; графики и текст не дают достаточно однозначного соглашения для превращения всех показанных RMSE в один физический rate unit. **UNKNOWN:** единая точная нормировка RMSE между рис.5.16 и5.23–5.25; поэтому raw R² приведён без произвольной конверсии RMSE.

**SOURCE — с. 101,110–112.** Online SGD: random50/30/20 split для initial/online/validation; learning rate0.02. В отдельном learning-rate анализе с.110 используется50/50. Scratch learning starts zero coefficients,≈1000 instances для относительно хорошего результата; автор предупреждает, что редкость SPE растягивает обучение. Смена shield100mils→10mm(394mils) — пример улучшения после online update, не испытание всех будущих сред.

### 7.3 Режимы и системные знаменатели

**SOURCE — с. 119–125,126–128.** В простом de-stress один core выполняет task; high-performance — четыре независимые tasks; DMR/TMR/QMR занимают2/3/4 cores для защищённой работы. Производительность пропорциональна parallel tasks и частоте, power — active cores и dynamic `V²f`. Sleep leakage и точная power variation упрощены. **INFERENCE:** “performance” здесь capacity proxy, не измеренный полезный throughput приложения при memory contention.

**SOURCE — §6.3.3, с. 138:** при `r=SEU_T/SEU_0`: `r<3` default;3…12 frequency reduction;12…24 voltage increase;24…1830 TMR;≥1830 QMR. Пример: `fmax/fmin=4`, `vmin=0.7V`, `vmax=1.4V`; DMR исключён из joint strategy. В NMR-only policy пороги3,5,1830 (с.132). **UNKNOWN:** физически проверенная допустимость всего voltage/frequency range и numeric device coefficient для его воспроизведения; автор называет DVFS теоретическим.

**SOURCE — табл.6.2–6.4, с.140–142.** Модель2Gbit,65nm; background25th/median/75th count34/41/51upsets/hour, min23,max64. Выбран baseline25upsets/hour (2.80×10^-7upsets/bit/day). Historical peak118122upsets/hour. Средний год8760h: default8540h,DVFS142h,TMR74h,QMR4h. Автор прямо предупреждает: average-year не реальная временная последовательность SPE (с.141).

Ниже **SOURCE — табл.6.5, с.143–144**, числа сохранены в авторском обозначении. `P=1` и `Pe=1` — single-core reference за час при `(fmax,vmin)`; годовые суммы фактически energy/work proxies, не watts и не throughput в секунду.

| Режим | Годовая сумма “Power Consumption” | Годовая сумма “Performance” | Доля времени удовлетворения SIL1 |
|---|---:|---:|---:|
| SAFR1: default de-stress | 8849 P | 8689 Pe | 100% |
| SAFR2: default high-performance | 34682 P | 34522 Pe | 100% |
| Static de-stress | 8760 P | 8760 Pe | 98.6% |
| Static DMR | 17520 P | 8760 Pe | 97.9% |
| Static TMR | 26280 P | 8760 Pe | 99.95% |
| Static QMR | 35040 P | 8760 Pe | 100% |
| Static high-performance | 35040 P | 35040 Pe | 98.6% |

**SOURCE — с.144.** SAFR2 вычислен как `4×8540+2×142+3×74+4×4=34682` для P и `4×8540+2×142+1×74+1×4=34522` для Pe. DVFS часы заменены средними величинами. **INFERENCE:** это не замер power по траектории controller; нет explicit затрат monitor/predictor/switches в этой сумме. QMR — сильный статический comparator, также100% по тому же proxy. SAFR1 экономит energy proxy против QMR, но имеет немного меньший work proxy; SAFR2 даёт почти четырёхкратный work proxy против QMR при близкой energy proxy. Нельзя заключать, что один SAFR вариант доминирует все статические варианты сразу по всем метрикам или выполняет тот же fixed workload дешевле.

## 8. Baselines и дополнительная ценность прогнозирования

| Проверка | Что есть в диссертации | Disposition |
|---|---|---|
| Regression vs regression | **SOURCE:** пять ML models, varying history, fixed-point и SGD (§5.3–5.5) | Качество estimator сравнивается |
| Forecast vs current count / persistence | **UNKNOWN:** нет парного итогового risk/resource comparison с одинаковым observation delay и требованиями | **INFERENCE:** added decision value не установлена |
| Forecast vs простой порог | **SOURCE:** сам mode selector пороговый/LUT; measurement может немедленно trigger mode (с.99,138) | **INFERENCE:** ML не противопоставлен порогам как отдельная доказанно лучшая policy |
| Adaptive vs strong static | **SOURCE:** QMR и другие static modes в табл.6.5 | Условный архитектурный эффект mode switching показан; вклад именно prediction не изолирован |
| Forecast uncertainty → action | **UNKNOWN:** нет calibrated intervals, false-alarm/miss confusion matrix, error-to-risk/resource curve | R² не заменяет decision-safety metric |

**SOURCE — с.74,98–99.** Мотив прогноза — measurement collection занимает время. Но первый отсчёт после взрывного начала SPE из background точно предсказать нельзя. Автор сообщает типичные first-instance1.5…6 background и возможность немедленной защиты по measurement, не ожидая forecast. Критические clock/reset trees и critical memory должны иметь постоянную локальную защиту.

**INFERENCE.** Фраза “one hour in advance” защищаема как следующий час после доступной истории, но не универсальное предсказание onset до первого сигнала. Диапазон1.5…6 пересекает иллюстративные triggers3 и5; “обычно ниже порога” не доказывает безопасность каждого пропущенного onset. Статическая защита здесь часть условия, а не ненужный baseline.

**SOURCE — с.138.** Concurrent policy должна удовлетворять actual detected и predicted future reliability одновременно. **INFERENCE:** замысел гибридный reactive/forecast-assisted, не чистый forecast-only controller. **UNKNOWN:** точный оператор объединения двух оценок, clipping отрицательного linear forecast, saturation, hysteresis, invalid-input fallback; длительность и потери при reconfiguration, synchronized state transfer, recovery after failed transition. Context-switch restoration описана на с.122, но не дана как измеренный переходный контракт.

## 9. Main equations и воспроизводимость

**SOURCE.** Для targeted reproduction важны:

1. Cross sections/static bit choice: (4.1), (4.3)–(4.4), табл.4.2–4.3; CREME96/proton+heavy-ion sum, shield и RPP assumptions (§5.2.3, с.87–91).
2. Predictor17h (5.6), integer/32 version (5.7), SGD (5.8)–(5.9),4h versions (5.10)–(5.11). На с.104 опубликованы все17 coefficients; на с.106 — все4. Это существенно полнее описания поздних S3/S5.
3. При `p=exp(−λ_ct)`: single `p`,DMR `p²`,TMR `3p²−2p³`,QMR `6P_d p²(1−p)²+4p³−3p⁴`, (6.5)–(6.8). Voter в дальнейшем идеализирован.
4. Mode resource functions (6.9)–(6.20); наблюдение→failure (6.21)–(6.24); PFH и thresholds (6.25)–(6.33); DVFS (6.34)–(6.37); yearly arithmetic с.144.

**INFERENCE.** Можно воспроизвести выбранные published linear functions и явную арифметику таблицы. Полный численный SAFR reliability/control experiment из PDF не воспроизводится однозначно: нужны исходные splits/traces, target calibration, mode transitions и непротиворечивые equations. Здесь новые расчётные эксперименты не выполнялись.

### Конкретные текстовые/формульные несогласованности

| Место | SOURCE: что напечатано | INFERENCE: почему важно |
|---|---|---|
| (6.4),с.124, визуально проверено | В binomial failure factor стоит `(1−exp(−i λ_c t))^(N−i)` | Не совпадает с подстановкой `p=exp(−λ_c t)` в (6.3). Не исправлялось молча; последующие explicit mode formulas рассмотрены отдельно |
| (6.33),с.132, визуально проверено | `3exp(−2K_cr)−2exp(−3K_cr)=10^-5` | Левая часть — TMR reliability из (6.27), а требуется failure threshold по (6.29). Пропущенный `1−` выглядит источником дефекта;1830 сохранено как заявленное число, не заново проверенный вывод |
| с.139 | Проза ссылается на (6.38), displayed TMR+DVFS equation помечено (6.36) | Воспроизводить по содержанию/странице, не одной нумерации |
| (6.21),с.129 | `φ=SEU_T/(σ T)`, но flux units названы particles/cm² | При явном времени нужен time denominator; сохранять count/rate различие |
| с.59 vs62 vs64 | Общая detection запрещает доступ; внешний scrub назван transparent с доступом; internal bank блокируется | Разные execution cases, нельзя выбирать наиболее выгодную фразу для общего service guarantee |
| §7.1 vs§4.4.1 | Общее “accurately detected and counted” для MCU; отдельно ограничение ≥3bit/word | Summary нельзя читать сильнее code-specific validation |

## 10. Main results: что действительно демонстрирует работа

**SOURCE.** Разработана связная monitor/predictor/mode-selection методика с реализационными деталями, конкретными synthesized blocks, регрессионными тестами и расчётным trade-off на solar-cycle24 (§§4.2–4.4,5.3–5.5,6.2–6.4).

**INFERENCE.** Наиболее сильный практический элемент — не universal guarantee, а последовательное закрепление каждого вклада за интерфейсом и проверяемым выходом: monitor даёт counts, predictor даёт следующий count, LUT даёт operating mode, cores дают понятный capacity/power trade-off. Слабейшее место — переход от компонентных validation к замкнутому системному выигрышу с фактическими ошибками наблюдения/прогноза и switching costs.

## 11. Limitations stated by author

**SOURCE:** ≥3 errors/word и необходимость иных ECC/interleaving (§4.4.1); зависимость записи от сохранения fault observations (с.53); inaccurate first SPE instance и постоянная защита critical elements (с.98–99); orbit/shield/solar-cycle mismatch (с.99–100); inadequate small-monitor resolution (с.106–109); долгое scratch learning и нестабильность большого learning rate (с.110–112); DVFS только theory, параметры и practical range требуют анализа (с.135); средний год не реальная SPE хронология (с.141); LET measurement, дополнительные среды/модели и иные processing units — future work (§7.2).

## 12. Limitations inferred from methodology

**INFERENCE.** Нет end-to-end propagation cross-section/spectral/observation/prediction uncertainty; нет task-level calibration условной связи monitor→processor failures; mean-count scaling не демонстрирует noisy finite-count detector; reusable SRAM и35Mbit minimum не согласованы для любого embedded target; power denominators меняются между host SRAM/digital controller/normalized core; operational mode selection не включает явно стоимость собственного controller. Нельзя автоматически зачесть все аппаратные проценты к годовой экономии SAFR.

## 13. Threats to validity

**INFERENCE.** Random online split и unspecified event-wise separation offline60/40/CV допускают optimistic temporal validation; это риск leakage, не доказательство фактической утечки. Хороший R² может сосуществовать с опасным underprediction на onset. Unknown cross-core common-cause, `P_d`, task mix и perfect-voter assumption ограничивают QMR guarantee. Упрощённые DVFS/power/task models не доказывают полезный throughput или thermal/timing feasibility. Reconstructed episode не равен будущей непредвиденной среде; total counted fault objects не гарантированно равны физическим radiative marks.

## 14. What the thesis actually demonstrates — bounded verdict

**INFERENCE:** **связный и практически мотивированный design flow с компонентными реализациями и условной системной оценкой**. **UNKNOWN:** единый аппаратный закрытый цикл с совместно измеренными правильностью, prediction failures, переходами, energy и workload service. **UNKNOWN:** дополнительная системная ценность predictor сверх корректно реализованного current-measurement threshold. Эти UNKNOWN не обесценивают monitor/accelerator results, но запрещают сильную attribution “ML дал весь системный выигрыш”.

## 15. What cannot legitimately be claimed

**INFERENCE.** Из этой диссертации нельзя утверждать: необходимость ML для адаптивной памяти; достаточность/недостаточность нашего `T_scrub`; гарантированное обнаружение SPE до первого опасного события; memory `F_A` или SIL certification; превосходство над любым сильным fixed/scheduled controller; экспериментально измеренное снижение годового энергопотребления всего SAFR; универсальную пользу richer information или адаптации; литературную novelty/non-novelty Chen либо нашей работы. Не следует заимствовать расширение action vector до NMR/DVFS только потому, что здесь оно даёт большой эффект.

## 16. Relevance: что перенять для нашей диссертации

| Принцип | INFERENCE: полезный перенос | Граница переноса |
|---|---|---|
| Начинать с физически значимого trade-off | Обосновать, какой именно полезный service resource меняет период восстановления и при каком неизменном требовании | Не подменять traffic/cost SRAM числом освобождённых cores |
| Единая цепочка вкладов | Каждый результат должен закрывать следующий интерфейс; вспомогательные оценки должны менять decision или доказывать границу его изменения | Не включать predictor только ради полноты блок-схемы |
| Известный сильный baseline | Сохранять лучший admissible fixed/simple causal comparator; отдельно проверять добавочную ценность сложного information layer | QMR не memory fixed-scrub baseline |
| Hardware-facing outputs | Явно считать acquisition, decision compute и execution costs с правильными denominators | Synthesis блока не end-to-end service measurement |
| Слабые/нулевые результаты как граница | Разрешение малого монитора и onset limit — содержательная часть метода; аналогично принимать область отсутствия преимущества `T_scrub` | Не спасать выбранную ветвь сменой requirement или скрытым workload |
| Разделение требований и режима | Сравнивать действия при одном memory reliability/service contract, отдельно показывать изменение класса задач | SIL-inspired proxy не заменяет DEC-001 |

**INFERENCE — стратегический вывод.** Перенять следует **способ связывать инженерную проблему, действие и измеримый ресурс**, а не многослойность как самоцель. Chen показывает, почему смена режима может иметь большой эффект именно при пространственной избыточности ядер. Он не даёт основания заранее ни сохранять любой ценой период восстановления как достаточный actuator, ни немедленно отказываться от него. Для текущего проекта limited cold-start separation и отсутствие установленной added value RES-003 остаются ровно теми, чем признаны review; тезис Chen их не расширяет. Обоснованная смена постановки требует собственного architecture-constrained основания и решения PI, не аналогии с процессором.

## 17. Атомарные candidates для Evidence Auditor

Без permanent claim/evidence IDs; восемь statements на адресную проверку, не принятые claims.

| № | Label и statement | Exact source location | Граница audit |
|---|---|---|---|
| 1 | **SOURCE-CANDIDATE:** монитор HSIAO(39,32) подтверждён simulations для single/double soft и single hard errors, но не обеспечивает общий accurate count для≥3bits/word | §4.4.1,с.66–67;рис.4.5,с.58 | Не переносить на все MCU и parent particles |
| 2 | **SOURCE-CANDIDATE:**17h predictor требует17 начальных hourly samples; первый SPE instance не может точно предсказываться из background alone | §5.4.1,с.104;§5.3.3,с.98–99 | Next-hour forecasting≠universal onset warning |
| 3 | **SOURCE-CANDIDATE:** при small SPE Mar2011 масштабированный4Mbit monitor даёт недостаточное разрешение; улучшение при20Mbit и рекомендация≈35Mbit относятся к принятой65nm модели | §5.5.1,с.106–109;рис.5.24–5.25 | Не universal minimum size/guaranteed count |
| 4 | **SOURCE-CANDIDATE:** табл.6.5 Reliability есть доля времени удовлетворения model SIL1 requirement, а не годовая survival probability | Табл.6.5,с.143;разъяснение с.143–144;формула6.29,с.130 | Не `F_A` и не safety certification |
| 5 | **SOURCE-CANDIDATE:** годовые SAFR2 ресурсы вычислены из mode-hours с усреднённым DVFS, а не получены аппаратным power/workload измерением | Табл.6.4–6.5,с.142–144,явные суммы с.144 | Preserve P/Pe reference и общий horizon |
| 6 | **SOURCE-CANDIDATE:** joint selection использует actual и predicted reliability, тогда как measurement может запускать защиту без ожидания forecast | §6.3.3,с.138;§5.3.3,с.99 | Hybrid design intent; точный fusion operator не определён |
| 7 | **INFERENCE-CANDIDATE:** добавочная системная ценность prediction против current-count-only controller не изолирована в опубликованной оценке | Predictor comparisons§5.3–5.5;mode comparison§6.4,табл.6.5 | Проверка отсутствия matched ablation в целевом scope; не доказательство нулевой ценности |
| 8 | **INFERENCE-CANDIDATE:** диссертация не устанавливает end-to-end hardware reliability guarantee, хотя содержит monitor/controller implementation и synthesis evidence | §§4.3–4.4,5.4–5.5;§6.3.2,с.135;§6.4 | Не отрицать реализованные компоненты; отделить DVFS theory и historical calculation |

## 18. Tensions с принятыми PAPER-009…011

**SOURCE (канонические cards, не автоматическая attribution thesis).** S3/S5 позднейшей семьи используют PBD и wash-frequency selection; S4 — HSIAO evaluation branch. **SOURCE (диссертация):** monitor здесь HSIAO/ODRF; основное adaptive action в главе6 — NMR/DVFS. **INFERENCE:** нельзя переносить PBD collision equation, wash thresholds, scrub totals и R² из статей в thesis. В thesis явно опубликованы17h/4h functions, SGD и cold-start limitations; six-hour history S5 не переименовывает их задним числом. Chronological priority за пределами прочитанного набора не устанавливается.

## 19. Named gaps и передача Orchestrator

| Неразрешённое звено | Точный недостающий input/evidence | Значение для решения |
|---|---|---|
| Monitoring→training target | Правило weighting/filtering single/double/permanent counters и accounting до overwrite, с missed-error statistics | Идентичность online observation и learned target |
| Monitor→processor risk | Device/task-specific nominal failure calibration, correlation/common-cause и `P_d` evidence | Обоснование LUT/SIL-inspired thresholds |
| Predictor→added system benefit | Matched forecast/current-measurement/persistence policies при одинаковом delay, static hardening, requirements и cost accounting | Нельзя приписать annual gain прогнозированию |
| Cold start/onset/transitions | Начальная safe policy, missed-sample/negative forecast handling, switching/recovery timing и fault exposure | Нельзя утверждать universal timely protection |
| Reproducibility | Event-separated dataset/splits, consistent (6.4)/(6.33), DVFS calibration, dynamic resource traces | Пока доступна лишь частичная numerical reproduction |
| Our memory strategy | Собственное target-memory service/cost/applicability evidence при неизменном контракте | Thesis не решает, достаточен ли `T_scrub` в нашем practical domain |

**HANDOFF TO RESEARCH ORCHESTRATOR.** Поставка: одна draft analytical card v1.0 по указанному SHA-256 PDF; рекомендация CORE. Архитектурный урок: заранее обосновать сильную связь actuator→полезный ресурс и довести каждый вклад до отдельной проверяемой роли. Основное ограничение сравнения: условная многопроцессорная mode-capacity выгода Chen не переносится на память; системная added value прогноза и полный closed-loop hardware result не установлены. Не предлагается ни пересмотр accepted RES, ни новый controller/experiment, ни расширение action vector. Восемь candidates требуют отдельного EA review; публикация карточки — не научное принятие.

Проверка repository на точной исходной базе уже даёт **1 error /44 warnings**: pre-existing `BROKEN_LINK` в `docs/scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md` (inline Python воспринят как link), legacy/draft warnings. Этот отчёт не исправляет чужие артефакты. Итоговый delta validation и commit identity передаются в completion message, чтобы не создавать самоссылочный SHA.
