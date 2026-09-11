# PA-MEMORY-PROTECTION-SELECTION-01 — адресное извлечение для ветвей А и Б

Версия отчёта: 1.0, 2026-09-11. Статус: DRAFT; передача Orchestrator, не научное принятие. Автор роли: Paper Analyst. Связь: RQ-003, RQ-004, RQ-005, RQ-007. Permanent identifiers не назначаются.

## 1. Область, входы и краткий результат

База инструкций: `59603d231b923ee7426056cb62779a5ad16c8413`; прочитаны global rules, Paper Analyst и HANDOFF_CONTRACTS, интерфейсы RQ-003/004/005. Приняты как точные входы:

- [Chen strategy, 261e2dafeb5360b7ebb55946906a1b16bb766c2f](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/261e2dafeb5360b7ebb55946906a1b16bb766c2f/docs/paper_cards/DRAFT-CHEN-THESIS-STRATEGY-01.md): повторное чтение диссертации не выполнялось; её выводы не переносятся на новые источники.
- [LS tradeoff, d0c3555a746b9e8db9d17b2a40fea8cfbacd849b](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/d0c3555a746b9e8db9d17b2a40fea8cfbacd849b/docs/literature_mapping/LS-MEMORY-PROTECTION-TRADEOFF-01.md): источник identity/discovery, не замена полного текста.
- Текущее решение Orchestrator: А — постоянный ECC, conditional-write scrubber и согласованное обслуживание приложения; Б — условный кандидат переключения ECC по областям. Остановленная практическая ветвь не возобновляется.

**INFERENCE — итог отбора.** Lu даёт предметный архитектурный baseline для А, но его прозрачность покупается временным резервом FPGA RAM и не доказывает бесплатное обслуживание внешней SRAM. ARCC и DFMC 2023 дают конкретные механизмы Б: состояние страницы/блока, событие усиления, изменение хранения и обслуживание перехода. Они не устанавливают выигрыш Б при одинаковом радиационном риске внешней SRAM. У ARCC меняются организация DRAM и обнаружение второго ошибочного символа; у DFMC сильный статический режим выдерживает сценарий, в котором динамический не успевает защитить данные. Обоснования перехода непосредственно к количественному RE внешней SRAM пока нет: отсутствуют перечисленные в §7 целевые входы, а не просто ещё один процент выигрыша.

**UNKNOWN — DEMC 2026.** Полный текст MPT-C10 отсутствует и по последнему указанию пользователя сейчас не разыскивается. Ни 70% energy saving, ни определения/переходы/метаданные версии 2026 здесь не подтверждаются. Третий блок — разрешённый адресный анализ MPT-C09 (2023), не реконструкция DEMC.

Метки: **SOURCE** — содержание прочитанного PDF; **INFERENCE** — наша ограниченная интерпретация/сопоставление; **UNKNOWN** — текст не устанавливает нужное свойство. Отрицательные сведения о полноте метода не означают отрицательный результат испытания. Ни application success, ни SDC rate, ни functional error count автоматически не являются DEC-001 `E_cap` или `F_A(t0,T;μ_t0)`.

## 2. Контроль фактически прочитанных текстов

| Кандидат | Полный текст и bibliographic identity | Контроль копии и чтение |
|---|---|---|
| MPT-C02 | Yufan Lu, Xiaojun Zhai, Sangeet Saha, Shoaib Ehsan, Klaus D. McDonald-Maier. **A Self-Adaptive SEU Mitigation Scheme for Embedded Systems in Extreme Radiation Environments**. IEEE Systems Journal 16(1), 1436–1447, March 2022. DOI `10.1109/JSYST.2022.3144019`. На первой странице: accepted 13 Jan 2022, publication 28 Jan 2022, current version 24 Mar 2022. | Supplied `A_Self-Adaptive_SEU_Mitigation_Scheme_for_Embedded_Systems_in_Extreme_Ra....pdf`, 12 PDF-страниц, 2,849,312 bytes. SHA-256 `7ad7499c4c187bd23765b903ad9dc314a8a6562335ad2a1b14c7166e369c6553`. Прочитан научный текст, формулы/таблицы сверены визуально. Ниже печатные страницы; PDF p.1 = 1436. Копия с журнальной вёрсткой; её побайтовая тождественность файлу Southampton отдельно не заявляется. |
| MPT-C11 | Xun Jian, Rakesh Kumar. **Adaptive Reliability Chipkill Correct (ARCC)**. HPCA 2013. DOI `10.1109/HPCA.2013.6522325` — identity принятого LS; заголовок/авторы сверены с PDF. | Supplied `xunjian2013.pdf`, 12 PDF-страниц, 654,074 bytes. SHA-256 `a3dae362b8c6f8ae942ada9f6b785e2e40386980a85f058097daba6d48ff1522`. Все разделы прочитаны. В данной копии используем **PDF-пагинацию**, не выдумываем отсутствующие печатные страницы. Конференционная полнотекстовая копия; побайтовая тождественность издательскому файлу UNKNOWN. |
| MPT-C09 | **Memory Controller with Adaptive ECC for Reliable System Operation**, SBCCI 2023. DOI `10.1109/SBCCI60457.2023.10261959` напечатан в PDF. Первая страница: левая группа авторов **Marco Stefani, César Marcon**, правая **Felipe Silva, Jarbas Silveira**. | Supplied `690c4ca5c90c3dd4a957368c6846b81e.pdf`, 6 PDF-страниц, 286,954 bytes. SHA-256 `c1843702b7fa461cb148bce119572f67d8fe78ca98d40b4d84850ca7e83df430`. IEEE download watermark: 11 Sep 2026, 09:03:22 UTC. Прочитаны §§I–VII; далее PDF-пагинация. Группированная byline сохранена буквально: порядок метаданных LS не используется для незаметной перестановки авторов; линейный издательский порядок требует metadata reconciliation. |
| MPT-C10 | **DEMC: A Dynamic Multi-ECC Memory Controller with Per-Block Adaptation**, Integration 2026, DOI `10.1016/j.vlsi.2026.102728` — идентичность из handoff, не из полного текста. | **UNKNOWN / FULL TEXT NOT SUPPLIED — DEFERRED BY USER.** Никакой PDF не прочитан. Контентное сопоставление 2023/2026 невозможно. |

SOURCE — название архитектуры в MPT-C09: **DFMC**, встроенный модуль **DFTM**. Нельзя переименовать её результаты в DEMC 2026. INFERENCE — это одна разрешённая линия источников, а не два независимых подтверждения. Lu 2020 не открывался: текущий текст достаточно описывает принцип обслуживания; недостающие точные параметры кода сохранены как named gap, а не основание для автоматического расширения корпуса. Общего поиска, моделирования и новых экспериментов не было.

## 3. MPT-C02 — Lu: что именно автономно и что действительно адаптируется

### 3.1. Метод, наблюдение и действие

| Поле | Извлечение и источник |
|---|---|
| Объект/порты | SOURCE — пользовательская FPGA block RAM, ECC/controller между пользовательским модулем и RAM. Пользователь и scrubber делят те же порты, не выделяется дополнительный порт scrubber. Controller и RAM работают на **2× user clock**, операции чередуются. III, p.1439, Figs.5–6. Нельзя переносить это утверждение на порты стенда инжекции, у которого другой интерфейс. |
| ECC и проверка | SOURCE — Hamming, комбинационные encoder/decoder; проверка и исправление по байтам, error flag запускает refresh. Дополнительный пользовательский цикл на кодирование не требуется при принятом timing. III, p.1439. UNKNOWN — формальная полная спецификация `(n,k,d)`, таблица всех decoder outcomes и защита самого контроллера/его состояния не даны как контракт. |
| Наблюдение | SOURCE — результат ECC decoder текущего прочитанного слова и адрес пользовательской операции, а не оценка текущего потока частиц по счётчику. III–IV, pp.1439–1441. INFERENCE — нет продемонстрированного radiation estimator, прогноза или закона выбора периода. |
| Исполнение | SOURCE — состояния scan/refresh: S0 чтение, S1 проверка/пользовательский слот; при ошибке S2 corrected write и S3 синхронизация. Чистое слово требует 2 RAM cycles, ошибочное — 4. IV.A–B, pp.1440–1441, Figs.8–10. |
| Conditional write и конфликт | SOURCE — scrub write выполняется при ошибке. Если пользователь пишет тот же адрес, scrubber отказывается от текущей операции и переходит дальше, не перезаписывая новые пользовательские данные старой «исправленной» копией. Обратный обход адресов противопоставлен последовательному прямому обходу приложения. IV.B, p.1441, Figs.10–11. INFERENCE — это конкретная локальная стратегия согласования, не доказательство отсутствия конфликтов/голодания для любого workload. |
| Прозрачность | SOURCE — buffer отделяет scrub-выходы от пользовательских; исходное ожидание ответа на следующем user cycle сохраняется благодаря 2× clock и чередованию. III.C–IV.A, pp.1439–1441, Figs.5–9. INFERENCE — прозрачность условна относительно временного резерва RAM/логики и предусмотренного интерфейса, не означает нулевую стоимость памяти, мощности или обслуживания. |
| Что меняется online | SOURCE — переход scan→refresh по error flag, дополнительные write cycles, вследствие этого фактическое время обхода. IV, Eqs.(1)–(3). INFERENCE — **автономное восстановление с фиксированным правилом обслуживания, постоянным ECC и номинальной частотой**, а не установленный адаптивный выбор `T_scrub`. Реальная длительность полного прохода не константа. |
| Внешняя интенсивность/параллелизм | SOURCE — число параллельных refresh controllers и размер участка можно выбрать под среду; RAM frequency обычно фиксирована runtime. IV.C, pp.1441–1442, Fig.12. INFERENCE — описанное sizing архитектуры не подтверждает runtime переключение числа контроллеров. |

SOURCE — Eq.(1), p.1441: `T=(2n1+4n2)/f=2(N+n2)/f`, где `N=n1+n2`, число проверяемых единиц; `f` — RAM/controller clock, `T` — время обхода. Eq.(3), p.1442: `T=2(N+n2)/(mf)` для `m` параллельных контроллеров. Это стоимость обхода в зависимости от проверяемых/исправляемых единиц, не вероятность отказа.

SOURCE — Eq.(2), p.1442: `T_max=1/(NR)`; автор связывает максимальное время сканирования со временем генерации последовательной ошибки. INFERENCE — это эвристическое условие сравнения времен, не оконная гарантия. Не заданы вероятность хвоста прихода, распределение ошибок по codewords, начало `μ_t0`, механизм одновременного превышения capability. Нотация единиц `R` в сопровождающем примере недостаточно однозначна для переноса без уточнения нормировки на bit/проверяемую единицу. Нельзя принять Eq.(2) как проектный threshold.

### 3.2. Ошибка, восстановление и уровень доказательства

SOURCE — в hardware injection функциональная ошибка устанавливается по отличию выхода injection RAM от reference RAM; это выходной observable, не родительское радиационное событие. Повторные обращения к одной неисправленной ячейке могут снова дать функциональную ошибку. V, pp.1442–1444. Инжектор управляет частотой и псевдослучайными интервалами вокруг среднего; такой стенд не подтверждает Poisson arrivals или physical MCU statistics.

SOURCE — neutron test: ChipIr, спектр для terrestrial neutron effects, `E_n>10 MeV`; Artix-7 XC7A15T/Cmod A7-15T; сравнение одинаковых доступных 32 kByte и пользовательской полосы. Unhardened RAM работает на 50 MHz, self-refresh — 100 MHz. VI.A–B, pp.1444–1445, Fig.17, Table III. Это испытание FPGA BRAM, не испытание внешней SRAM.

| Уровень/условие | Исходные результаты и baseline | Ограничение |
|---|---|---|
| SOURCE — hardware fault injection, V, pp.1442–1444, Figs.13–16 | Virtex-5 XC5VLX110T; пользовательские операции 25 MHz, refresh 50 MHz, отдельная инжекция 100 MHz. При среднем интервале инжекции 100 μs (`10^4 bit/s`) заявлено 99.9% устранения ошибок; при 160 μs — 99.97%. Сравнивается выход с reference RAM. | INFERENCE — эффективность относительно этих операций/инжекций, не гарантированная доля устранённых физических MCU и не `F_A`. В тексте имеется несогласованная запись `6.25×10^4` для интервала 160 μs: не использовать её как независимо проверенную интенсивность. |
| SOURCE — neutron comparison A, VI.D, pp.1445–1446 | Первые 1.5 h: 32 ошибки unhardened против 0 зарегистрированных в self-refresh. | INFERENCE — ноль наблюдений не означает нулевую вероятность. Размер выборки не подтверждает универсальную верхнюю границу риска. |
| SOURCE — neutron comparison B, VI.E, p.1446, Fig.21/Table IV | За 360 min conventional Xilinx ECC RAM — 5 ошибок, self-refresh — 1. Автор сообщает `8.7×10^-5 bit/(kB·h)` и `1.16×10^-16 cm²/bit` для self-refresh. | UNKNOWN — из этого сравнения не получается полный одинаковый ECC/scrub/mapping контракт двух систем. Exposure accounting для независимого воспроизведения нормированных показателей и статистическая неопределённость не даны достаточно подробно. Числа оставлены авторскими, не пересчитаны. |

SOURCE — PC периодически читает память (интервал 5 s); повторяемость/локальность ошибок используется для различения BRAM, коммуникации и controller malfunction. VI.C, pp.1445–1446. INFERENCE — такая диагностика не восстанавливает автоматически parent-event provenance, физическую топологию и joint post-W mark. Публикация не даёт измерительной модели ошибки такой классификации.

SOURCE — при неисправимой ошибке данные оставляются, а check bits переписываются, чтобы не повторять её обнаружение; VI.C–D, pp.1445–1446. INFERENCE — эту операцию нельзя назвать восстановлением правильного содержимого. Для RQ-003 существенно, что дальнейшее отсутствие syndrome не эквивалентно отсутствию повреждённых данных.

### 3.3. Постоянные затраты и цена обслуживания

SOURCE — Table III, p.1444, одинаковые 32 kByte usable:

| Ресурс | Unhardened | Self-refresh |
|---|---:|---:|
| BRAM units (сноска PDF: «36-kB BRAM») | 16.0 | 21.50 |
| LUT | 562 (5.4%) | 681 (6.5%) |
| LUTRAM | 8 | 8 |
| FF | 467 | 575 |

SOURCE — p.1445: Vivado power estimates для RAM 8 kB — 0.001/0.003 W, 256 kB — 0.020/0.038 W; для конфигурации с 256 kB сообщается +1.4% полной мощности FPGA. INFERENCE — это расчёт мощности, не прямое измерение энергии на полезную задачу. Малый процент на знаменателе всего FPGA не означает малой относительной цены самой RAM. Сноска «36-kB», подпись внутренней ёмкости и наименование единиц BRAM требуют сверки перед reuse; приведены literally, не заменены предположением. Проза о дополнительных 121 LUT не совпадает с табличными 562→681; для воспроизведения использовать исходные counts и отметить расхождение.

SOURCE — непрерывные дополнительные reads даже без ошибок; при исправлении добавляются writes; §§III–IV. INFERENCE — нет опубликованного workload-wide вектора interface occupancy, worst-case service latency и measured energy с переносом на внешнюю SRAM. Сохранение user bandwidth достигается большей внутренней скоростью, а не устранением этих операций.

### 3.4. Решение по А/Б и named gaps

**INFERENCE — пригодность А: CORE comparator внутри данного отбора**, для инженерного рассмотрения fixed ECC + conditional write + предотвращение stale-write конфликта. Не выбирает окончательный проект и не подтверждает практическую пользу изменения `T_scrub`. Для Б — BACKGROUND: ECC strength не переключается.

**UNKNOWN — до RE нужны**: А1 — интерфейс/частоты/turnaround/read-write timing целевой SRAM и доступный резерв между пользовательскими обращениями; А2 — точный код, check-bit layout и outcome неисправимых ошибок; А3 — атомарность user-write/scrub-write для конкретной шины и допустимые задержки приложения; А4 — физический mapping, direct-MCU sensitivity и измерение ресурсов целевой реализации. Это target-architecture inputs, не недоказанная «недостаточность» Lu. Исходный full text не требует подключения Lu 2020 ради общего принципа.

## 4. MPT-C11 — ARCC: реактивная смена организации защиты DRAM

### 4.1. Режимы, переход и ошибки

| Поле | SOURCE / ограничение |
|---|---|
| Основная пара режимов | SOURCE — обычный SCCDCD гарантирует single-chip correction и double-chip detection; relaxed ARCC сохраняет single-symbol correction, но не гарантирует одновременное double-symbol detection до upgrade. Strong codeword: 32 data + 4 check symbols; relaxed: 16 + 2. 12.5% check/data storage в обоих. §§2,4.1,6, PDF pp.2–5,7–8. Не путать symbol/chip с одиночным битом SRAM. |
| Granularity и layout | SOURCE — 4 kB page, 64-byte relaxed cache lines; соседние линии размещены в разных каналах. После upgrade две соседние 64 B объединяются в 128 B с четырьмя check symbols на расширенный codeword. Для 64 B relaxed приводятся четыре codewords. §4.1, PDF pp.4–5. |
| Событие усиления | SOURCE — обнаруженный memory fault в странице; переход к upgraded page. Чтение страницы, пересчёт ECC, запись. §4.1–4.2, PDF pp.4–6. Это реактивная защита по обнаруженному дефекту, не прогноз radiation intensity. |
| Начало и возврат | SOURCE — startup: все страницы upgraded, затем scrub, fault-free pages переводятся в relaxed; page-mode bit обновляется в конце scrub. §4.2.1–2, PDF pp.5–6. UNKNOWN — последующий runtime downgrade после периода без ошибок или доказательство безопасности такого возврата не представлены. Нельзя приписать схеме двусторонний онлайн-регулятор. |
| Что обнаруживает scrub | SOURCE — сохранить исходные данные; записать/прочитать all-0, записать/прочитать all-1, восстановить исправленные исходные данные. Это выявляет в том числе stuck-at, замаскированные текущим содержимым. §4.2.2, PDF pp.5–6. |
| Fault population | SOURCE — field-DRAM rates; lane, device, bank, column, row faults; reliability model/детали Monte Carlo отнесены к техническому отчёту [6], входные rates к field study [12]. §6.2–7, PDF pp.8–9. UNKNOWN — замкнутый отдельно параметризованный набор transient/intermittent/permanent rates и likelihood для радиационных инверсий в этом PDF не приведён. INFERENCE — модель нельзя объявить чисто transient-SEU; тест all-0/all-1 и накопление faulty pages существенно ориентированы на дефекты/деградацию. |
| First error / второй до наблюдения | SOURCE — первый bad symbol исправим; второй в том же codeword до обнаружения первого может пройти необнаруженным в relaxed. §6.2, PDF pp.7–8. INFERENCE — первая double-symbol ошибка не получает ретроактивной защиты после upgrade. Same-parent radiation mechanism и его отдельная частота не установлены. |

### 4.2. Неравенство требований и источник экономии

SOURCE — §6.1 заявляет неизменность DUE rate относительно SCCDCD из сохранения correction capability; §6.2 отдельно признаёт деградацию detection/SDC и оценивает её как малую в исследованной модели. Fig.4, PDF p.8: SDC на **1000 machine-years**, lifespans 5–7 years, 1×/2×/4× field fault rates; scrub period 4 h. При первом undetectable error предполагается замена всех DIMM машины, чтобы одна faulty machine не давала повторные SDC. INFERENCE — это не тождественная надёжность во всех outcome-классах и не одинаковое ограничение `F_A`. Не следует заменять авторское «малое изменение SDC» утверждением «то же требование выполнено» без отдельного requirement.

SOURCE — сравнение памяти (Table 1, PDF p.8): baseline DDR2 x4, 2 channels, 1 rank/channel, rank size 36; ARCC DDR2 x8, 2 channels, 2 ranks/channel, rank size 18. Текст на той же странице описывает baseline как один logical channel с двумя ranks, тогда как §4.2.4 объясняет lockstep двух физических каналов. INFERENCE — необходимо сохранять различие physical/logical channel conventions; не исправлять таблицу догадкой. Всего по рассматриваемой организации 72 devices; check/data storage 12.5%, но организация доступа **не одинакова**.

SOURCE — для fault-free pages активируется меньше chips/rank, допускаются более широкие x8 вместо x4 устройства и больше rank-level parallelism; §§2,4,7–8, PDF pp.2–6,8–10. INFERENCE — экономия не сводится к мощности более простого decoder или уменьшению числа исправлений. Изменение гранулярности и количества активируемых DRAM-чипов — ключевая часть baseline comparison.

### 4.3. Расходы и evidence

| Объект стоимости | SOURCE: что включено / показано | UNKNOWN / INFERENCE |
|---|---|---|
| Mode metadata | PTE/TLB +1 bit/page; LLC tag +1 bit/line, сопряжённые линии и изменение replacement policy. §4.2.1,4.2.3, PDF pp.5–6. | UNKNOWN — fault protection этих метаданных, полная hardware area/power стоимость OS/cache/controller изменений. |
| Переход | Page read/recode/write; для upgraded lines оба 64 B sub-lines должны считываться/записываться совместно. §4.1–4.2.4, PDF pp.4–6. | UNKNOWN — завершённый concurrency/atomic-commit protocol относительно всех кэшей, прерываний и ошибки в момент перехода. Из архитектурного эскиза нельзя вывести crash-safe recoding. |
| Доступ | Дополнительный tag lookup; paired memory queues либо cross-queue pointers и ожидание второго sub-line. Дополнительный relaxed EDAC controller на memory controller сверх strong EDAC пары. §4.2.3–4, PDF p.6. | SOURCE — doubling cache replacement time в оценке не дало заметного performance effect. Это не измерение нулевой аппаратной цены. |
| Scrub | Пример: 4 GB, 128-bit, DDR2 667 MHz; проход 0.4 s, шесть обращений/проходов дают 2.4 s; один scrub в 4 h → 0.0167% максимальной effective memory bandwidth. §4.2.2, PDF pp.5–6. | INFERENCE — авторский идеализированный bandwidth calculation, не измеренный верхний предел задержки полезного запроса при арбитраже. Write/test/read/restoration существенно сложнее conditional write А. |
| Upgraded-page access | При плохой locality объединение линий может требовать вдвое больше данных/активных устройств; lane fault может вынудить upgrade всей памяти; worst-case bandwidth penalty обсуждается до 50%. §§7–8, PDF pp.9–10. | INFERENCE — доля faulty pages, locality и fault granularity необходимы для воспроизведения выигрыша. |
| Мощность/производительность | §8, PDF pp.9–10: fault-free average memory-power saving **36.7%**, performance **+5.9%** относительно SCCDCD; lifetime headline около **36%**; при 7 years и 4× field fault rate остаётся ≥30% power saving. | SOURCE — DRAMSim/Micron datasheet power model + M5/12 SPEC mixes, не измерения изготовленной ARCC памяти. Нет полной системы в абсолютных W или energy/useful job. Не смешивать power saving и energy saving. |

SOURCE — reliability: аналитический model plus Monte Carlo; performance/power: simulator, четырёхъядерная модель, workload mixes; progression: 10,000-channel Monte Carlo over seven years. §§6–8, PDF pp.8–10. INFERENCE — «field-informed» не значит ARCC испытан в neutron/space environment. Существенная модель воспроизведения вынесена в technical report [6]; в этом bounded task он не подключён.

### 4.4. Пригодность для внешней SRAM

**INFERENCE — Б: RELATED engineering comparator**, достаточно конкретный для списка механизмов, не достаточный для переноса численного эффекта. Переносимы как идеи: page-mode state, усиление после исправимого наблюдения, явное recoding, учёт цены доступа к расширенному codeword. Непереносимы без нового обоснования: chip-symbol failure mapping, x4→x8 DRAM activation/rank benefit, field-derived rarity и persistence faulty pages, эффективность all-0/all-1 diagnostics для transient radiation. Для А — не прямой conditional-write baseline.

**UNKNOWN — gaps**: Б-AR1 — проверяемая модель transient/intermittent/permanent и отдельный direct-MCU компонент; Б-AR2 — target SRAM data/check-bit layout и физическая цена доступа слабого/сильного кодов; Б-AR3 — metadata protection и атомарность перехода; Б-AR4 — что считать равным требованием DUE/SDC/capability и допустима ли потеря detection; Б-AR5 — параметры полной reliability model, вынесенные в [6], если требуется точное воспроизведение самого ARCC. Подключение [6] требует отдельного решения Orchestrator, не выполнено автоматически.

## 5. MPT-C09 — DFMC 2023, разрешённый fallback без DEMC 2026

### 5.1. Режимы, наблюдение, окно и переход

| Поле | Извлечение |
|---|---|
| Кодовый набор | SOURCE — none, Parity, Hamming SECDED, LPC (modified product code с Hamming/Parity по строкам/столбцам). §§III–IV, PDF pp.2–3. Fig.3 показывает 64-bit data path и 72-bit RAM paths, вторую RAM для ECC, требующего дополнительного слова. UNKNOWN — полные `(n,k,d)`, матрицы кодов, точная LPC correction/detection область и размещение всех check bits из этого текста не восстанавливаются. Нельзя приписывать LPC параметры из DEMC. |
| Гранулярность/метаданные | SOURCE — 2048-bit internal configuration memory, 256 blocks, 8 bit/block: static/dynamic 1 bit, code 2, error counter 5. §IV, PDF p.3. В оценке block=32,000 addresses; §VI.B, PDF pp.4–5. UNKNOWN — защита этих метаданных, saturation/overflow counter и поведение при повреждённом code selector не указаны. |
| Наблюдение | SOURCE — ECC evaluator получает результат decoder при чтениях; block finder обновляет относящийся к блоку error state. §III, PDF p.2, Fig.2. INFERENCE — observable зависит от обращений и текущей способности ECC обнаруживать ошибки; это не наблюдение всех injected faults и не unbiased physical error intensity. В none нет обычного ECC error channel, Parity не исправляет. |
| Окно | SOURCE — configurable cycle; на цикле threshold process смотрит count и уменьшает его по заданному decrement. Три списка: thresholds increase/decrease и decrement per cycle. §III.A, PDF p.2. В оценке каждые **10,000 cycles**, **800 evaluations**, parallel operation, §VI.B, PDF p.5. INFERENCE — затухающий счётчик, а не определённое скользящее time window/arrival estimator; не дан перевод периода в seconds для любой целевой памяти. |
| Пороги/выбор | SOURCE — compare с upper/lower thresholds; пример диапазонов Parity 0–1, Hamming 2–3, LPC ≥4. Рядом описан переход above 3 / below 2. §III.A, PDF p.2. UNKNOWN — исчерпывающая спецификация равенства границ, порядка decrement/compare и всех конкурирующих запросов к переходу; перед кодированием нужна проверка точной семантики, а не догадка о hysteresis. |
| Направление адаптации | SOURCE — общий метод допускает up/down; параметры threshold не меняются runtime. Но фактическая оценка: initial Hamming, после первой ошибки LPC, **без возврата в Hamming**. §VI.B, PDF pp.4–5. INFERENCE — доказательства двустороннего устойчивого переключения из этой оценки нет. |
| Recoding | SOURCE — за цикл recode одного блока; OS уведомляется о диапазоне, чтение/перекодирование/запись; memory requests ждут завершения, затем уведомление OS. §III.B, PDF p.2. UNKNOWN — точный linearization point mode metadata, rollback, error-during-recode handling, fault-safe buffering и область блокировки block/module описаны недостаточно для готового внешнего SRAM протокола. |
| Хранение/модули | SOURCE — R+W manager проверяет, нужен ли хотя бы одному блоку ECC с двумя memory words, и управляет второй RAM; §§III–V, PDF pp.2–3, Figs.2–4. INFERENCE — per-block code choice не равнозначен независимому per-block power gating; внешний SRAM может не иметь соответствующей второй отключаемой памяти. |

SOURCE — static/dynamic configuration может учитывать критичность приложения (например OS против video), §§I–II, PDF p.1. INFERENCE — это разрешение разных требований, не доказательство экономии при едином фиксированном reliability constraint.

### 5.2. Первая ошибка, физика и 99.956%

SOURCE — Absimth, RISC-V 32F, DDR4, synthetic applications/read-write patterns; модель hardware описана на MyHDL, с memory-controller infrastructure; §§IV–V, PDF p.3. Инжекция bitflips в data area, пять сценариев; оценка Hamming→LPC с 32,000-address block. §§V–VI, PDF pp.3–5.

| Сценарий (SOURCE, Table VI, PDF p.5) | Static Hamming | Static LPC | DFMC Hamming→LPC |
|---|---|---|---|
| i — без ошибок | OK | OK | OK |
| ii — одиночный bitflip | OK, correction | OK, correction | OK, correction |
| iii — сначала одиночный, затем multiple | ERR | OK | OK |
| iv — multiple без промежуточного обращения | ERR | OK | **ERR** |
| v — повторное использование проблемной области двумя приложениями | ERR | OK | OK |

SOURCE — текст поясняет: несколько bitflips в одном слове возникают в интервалах, не допускающих доступа к нему для Hamming correction. Это контролируемый сценарий отсутствия раннего исправимого наблюдения, не экспериментальная классификация одного neutron parent event. INFERENCE — усиление помогает после достаточно раннего исправимого предупреждения; оно не восстанавливает автоматически данные, уже недоступные слабому decoder. Для radiation SRAM first same-parent capability exceedance может не иметь предупреждения. Утверждать соответствующую частоту или risk floor из этого сценария нельзя.

SOURCE — **99.956%** (Table VII, PDF p.5) получено рассуждением на основе внешней Google server field study: около 8% memories/errors annually и 0.22% multiple; 70–80% multiple имели предшествующий bitflip в том же адресе; берётся возможность предотвратить примерно 80% таких случаев. Таблица: WE 91.780%, SH 99.780%, DFMC 99.956%, SL ~99.999%; fail DFMC 0.044%. INFERENCE — это **экстраполяционный application-fail indicator**, не доля успешных прогонов из сообщённого количества испытаний, не измерение радиационной стойкости и не `F_A` с известными `A,H,μ`. Данные field study и предположение о предотвратимости не означают, что всякий предшествующий fault обнаружится вовремя.

SOURCE — проза у Table VII даёт «0.170% more» и «0.043% less»; табличные значения следует сохранять отдельно от округлённого/несогласованного первого выражения. INFERENCE — одинаковая надёжность с static LPC не установлена: отличается и Table VII, и исход сценария iv.

SOURCE — spatial heterogeneity вводится выбранными областями/сценариями инжекции и мотивируется коррелированными field-DRAM errors; §§I,V–VI, PDF pp.1,3–5. UNKNOWN — физическая SRAM cell topology, particle-to-cell mark, `W`, отдельные neutron/alpha/device-defect mechanisms и classification uncertainty не определены. Логическая близость адресов не является измеренной близостью ячеек.

### 5.3. Стоимость: что учтено, какой baseline, какие пределы

SOURCE — Genus для controller logic и CACTI для RAM, **28 nm, 1 V, 25°C**, §VI.A, PDF pp.3–4. Это synthesis/model estimates, не измерение мощности изготовленного контроллера. Areas Table I (μm²): WE 1446.53; SH 2224.57; SL 5124.51; DFMC 8205.67. WE — минимальная реализация, не полнофункциональный коммерческий контроллер.

SOURCE — Tables II–V, PDF p.4, учитывают internal-memory R/W, block finder, ECC evaluator, threshold, recoding и command generator. Поэтому нельзя писать, что статья вообще игнорирует monitor/recode overhead. Но UNKNOWN — fault protection metadata, leakage, полная OS/cache interaction и worst-case queued-service latency не доведены до end-to-end accounting.

| Операция/система | SOURCE: исходные величины | Знаменатель/граница |
|---|---|---|
| Static read | SH 447.891 pJ; SL 895.777 pJ; Table III | ECC + controller + DDR4, один read; SL использует вторую RAM. Не только decoder energy. |
| DFMC read | Hamming 447.983 pJ; LPC 895.869 pJ; 2.650 ns, Table V | ECC + proposed modules + DDR4, один read. |
| DFMC write | Hamming 458.797 pJ; LPC 917.501 pJ; 6.785 ns, Table V | Один write. |
| Recode Hamming→LPC | 1367.024 pJ, 10.764 ns, Table V | Описанная цепочка read/recoding/write **одного адреса**, не время полного 32,000-address block и не bound пользовательской остановки. |
| Полный сценарий i | SH 3592 μJ; SL 7184 μJ; DFMC 3593 μJ, Table IX | Controller + RAM, simulation scenario. |
| Сценарии ii–iv | SH 3592 μJ; SL 7184 μJ; DFMC 4272 μJ, Table IX | В DFMC включён recode 44 μJ. Сценарий iv у DFMC завершает симуляцию, но имеет ERR. |
| Сценарий v | SH 7184 μJ; SL 14368 μJ; DFMC 9137 μJ, Table IX | Два приложения; нельзя сравнивать с энергией одного приложения сценария i. |
| Controller only | i: SH 0.60, SL 1.17, DFMC 1.40 μJ; ii–iv DFMC 1.56; v DFMC 3.15 μJ | Table IX: контроллер динамической схемы сам дороже; итоговый выигрыш формируется преимущественно RAM organization/activity. |

SOURCE — paper reports saving versus SL: **49.99%**, **41.35%**, **36.85%** для i, ii–iv, v. PDF p.5, Table IX. UNKNOWN — **70% energy saving DEMC 2026**: baseline, boundary и включённые overheads нельзя получить из этого PDF. Указанное 99.956% встречается уже в 2023, но это не делает его определение в 2026 автоматически идентичным.

SOURCE — все сценарии выполнялись до конца и при ошибке, чтобы получать сопоставимые energy counts, §VI.B, PDF p.5. INFERENCE — энергия ошибочного выполнения не является энергией одной успешно решённой полезной задачи; нельзя выдавать снижение 41.35% в iv за reliability-preserving выигрыш.

SOURCE — Table III печатает energy ECC+MC в fJ, но значения 0.079 и компоненты Hamming decoder 55.108 fJ + MMCG 23.148 fJ в Table II не согласуются по масштабу; Table V использует pJ. INFERENCE — присутствует unit/provenance defect: перед reproduction нужно сверить исходные component units, а не тихо нормализовать таблицы. Table X, PDF p.6, — отдельная 4 GB экстраполяция (15,625 blocks по 32,000 адресов, 30%/4687 требующих воздействия), не та же 256-block internal metadata configuration; её W-values без leakage не принимаются как hardware measurement или готовый SRAM sizing.

### 5.4. Решение по Б и отсутствующая версия

**INFERENCE — Б: CORE targeted comparator внутри данного отбора** для per-block mode/count state, decaying threshold mechanism, recode queue, conservative one-way experimental configuration и обязательного сценария ошибки до усиления. Не достаточно как готовый воспроизводимый radiation-SRAM controller. Для А — RELATED лишь как контраст: здесь меняются ECC/доступы и останавливается обслуживание при recoding, а не реализуется Lu-подобная прозрачность.

**UNKNOWN — gaps**: Б-DF1 — точные code matrices/capability/check-bit storage; Б-DF2 — protected metadata и counter overflow; Б-DF3 — exact threshold ordering/equality/window и наблюдаемость слабых режимов; Б-DF4 — safe recode, точка commit, handling неисправимого исходного слова и ошибка при переходе; Б-DF5 — hardware/cost model внешней SRAM вместо дополнительного DDR4-модуля; Б-DF6 — controlled DEMC PDF для заявлений 2026 и content version comparison. Только Б-DF6 — отсутствующий названный full text; остальные — методические/архитектурные входы, которые нельзя автоматически заполнить его аннотацией.

## 6. Общая сравнительная таблица

Все SOURCE в таблице отсылают к подробным локаторам §§3–5; переносимость/границы помечены INFERENCE. DEMC 2026 отсутствует, поэтому научный столбец о нём не имитируется.

| Поле | Lu 2022 (MPT-C02) | ARCC 2013 (MPT-C11) | DFMC 2023 (MPT-C09; не DEMC) |
|---|---|---|---|
| Объект | SOURCE — FPGA BRAM + fixed Hamming + controller | SOURCE — DRAM pages/chips, caches, OS, channels/ranks | SOURCE — DDR4 blocks, ECC/controller/configuration RAM |
| Ошибка | SOURCE — injected bitflips и neutron functional errors; INFERENCE — физический parent mark не извлечён | SOURCE — field-derived lane/device/bank/row/column faults, bad symbols; UNKNOWN — radiative mechanism partition | SOURCE — injected single/multiple in data words; UNKNOWN — radiation parent provenance |
| Наблюдение | SOURCE — ECC syndrome/error flag + user address | SOURCE — detected page fault, including periodic pattern scrub | SOURCE — decoder-reported count/block при обращениях + decay |
| Действие | SOURCE — scan, conditional corrected write, conflict skip; INFERENCE — fixed-policy autonomous restoration | SOURCE — reactive page upgrade, line/codeword combination | SOURCE — block ECC selection; общий up/down, проверено Hamming→LPC без возврата |
| Переход | SOURCE — scan/refresh FSM, user write имеет приоритет при конфликте | SOURCE — page read/recode/write, mode bit, coupled cache/queue state; UNKNOWN — complete atomicity | SOURCE — queued/blocking recode и OS notice; UNKNOWN — fault-safe atomic commit |
| Требование | SOURCE — scan-time heuristic и functional output errors; INFERENCE — не DEC-001 probability guarantee | SOURCE — single-symbol correction retained, detection reduced before upgrade; INFERENCE — не одинаковые все reliability outcomes | SOURCE — application success в сценариях и field extrapolation; INFERENCE — не равная static LPC гарантия |
| Ресурс | SOURCE — 2× memory clock, extra BRAM/LUT/FF, continuous reads/conditional writes, Vivado power | SOURCE — activated chips/rank parallelism, metadata/cache/controller overhead, periodic six-pass scrub | SOURCE — ECC/metadata/monitor/recode logic, second RAM access, synthesis+simulation energy |
| Baseline | SOURCE — unhardened и conventional Xilinx ECC; одинаковые usable memory/user bandwidth в neutron comparison | SOURCE — SCCDCD, 36-device rank против relaxed 18-device rank; check/data ratio сохранён | SOURCE — WE, static Hamming, static LPC; LPC strongest comparator; iv только LPC проходит |
| Уровень evidence | SOURCE — hardware injection + neutron exposure + estimated power | SOURCE — model/Monte Carlo + workload/power simulation с field inputs | SOURCE — logic synthesis/RAM model + injected scenarios + external field-statistic extrapolation |
| Переносимость | INFERENCE — А: принцип обслуживания переносим, timing transparency зависит от target SRAM | INFERENCE — Б: protocol ideas переносимы, DRAM energy result и fault prognosis нет | INFERENCE — Б: per-block state/threshold/recode pattern переносимы, код/безопасность/радиационная применимость не закрыты |

## 7. Что в Б уже описано и что стало бы собственным проектированием

### 7.1. Достаточно описано для предметного архитектурного сравнения, но не для численной гарантии SRAM

- SOURCE — ARCC: конкретный relaxed/upgraded symbol layout, 4 kB granularity, trigger, startup, page/TLB/cache/queue participation и тестовый scrub (§4.1–4.2, PDF pp.4–6). INFERENCE — это воспроизводимые структурные варианты, а не только слово adaptive.
- SOURCE — DFMC: перечень режимов, 8-bit block state, read-derived count, fixed threshold/decrement settings, recode queue/OS interaction; фактическая conservative Hamming→LPC конфигурация (§§III–VI, PDF pp.2–5). INFERENCE — можно сравнивать логику решения и состав overheads без предположения, что полные code/transition details уже заданы.
- SOURCE — ARCC explicitly weakens early double-error detection; DFMC Table VI имеет режим multiple-before-access, где усиление не спасает. INFERENCE — first-error safety и одинаковое требование являются обязательными границами, а не деталями будущего retuning.
- SOURCE — сильные статические baseline присутствуют в обеих работах. INFERENCE — сравнение Б только со слабым ECC не ответит на вопрос о его инженерной ценности.

### 7.2. Что нельзя «заимствовать»: пришлось бы самостоятельно задать и затем проверить

| Нужное звено | Почему выбранные тексты не закрывают его | Что вернуть Orchestrator |
|---|---|---|
| Radiation observation → прогноз опасности региона | INFERENCE — ARCC опирается на DRAM fault persistence, DFMC — на предшествующие decoder-visible errors. Same-parent SRAM MCU может не иметь предупреждения; слабый ECC цензурирует наблюдение. | Named input: target radiation event/mapping model и проверяемая связь past observed errors с future risk. Без этого выбор count thresholds был бы собственным предположением. |
| ECC modes → одинаковое требование | INFERENCE — источники считают разные outcome objects; нет общего SRAM `F_A`/decoder map и численного проектного requirement. | RQ-003 outcome/capability contracts для каждого кода, включая metadata faults и переход. Не назначать requirement здесь. |
| Mode selection → безопасная перекодировка | UNKNOWN — complete atomicity, recoverability исходных данных, режим чтения в переходе и fault during transition. | Target architecture/implementation input: buffer, concurrency, code-version metadata, commit и unrecoverable-word policy. Их изобретение — разработка, не extraction. |
| Region count → корректный online observable | UNKNOWN — точный count update, saturation, access bias, false/missed detection и denominator exposure для SRAM. | RQ-004: доступные события и ошибки наблюдения, не oracle injected-fault stream. |
| Stronger code → физическая цена | INFERENCE — экономия источников определяется DRAM ranks/second module; внешний SRAM layout может дать другой знак и величину. | RQ-005: целевые read/write/check-bit transactions, bus occupancy, latency, storage, energy и controller costs раздельно; не scalarize заранее. |
| Выигрыш → полезная задача при равном риске | INFERENCE — в DFMC энергия считается даже для ERR; ARCC допускает дополнительный SDC. | Named input: workload/service contract и accepted risk comparison. Отсутствие этого входа нельзя закрыть процентом power saving. |
| DEMC 2026 → улучшенные детали/70% | UNKNOWN — PDF не предоставлен; версия 2023 не удостоверяет 2026. | Только точный полный текст `10.1016/j.vlsi.2026.102728`, когда пользователь/Orchestrator разрешит продолжение. Сейчас defer, не поиск. |

**INFERENCE — ответ о готовности.** Б описана достаточно, чтобы определить состав системы, сильные статические comparators и риски первого события/перехода. Б не описана достаточно, чтобы без собственного инженерного задания запустить fair quantitative RE радиационной внешней SRAM. Нельзя утверждать, что её нужно отвергнуть: условная полезность остаётся вопросом. Нельзя и объявить её готовым расширением stopped branch. А имеет более непосредственный контролируемый пример обслуживания памяти; но перенос её timing/energy также требует А1–А4.

## 8. Атомарные candidate statements для возможной дальнейшей проверки

Ниже только содержательные кандидаты, не создаваемые Claims/Evidence records и не автоматическое поручение Evidence Auditor.

1. **SOURCE-CANDIDATE:** прозрачность Lu относительно user cycles обеспечивается 2× RAM/controller clock и чередованием scrub/user операций. Lu III–IV, pp.1439–1441, Figs.5–9.
2. **INFERENCE-CANDIDATE:** Lu устанавливает autonomous fixed-policy scrub с conditional write, но не закон runtime выбора `T_scrub` по оценённой интенсивности. Основание: Lu IV.C, pp.1441–1442, Eqs.(1)–(3), фиксированная частота и параметр `m`.
3. **SOURCE-CANDIDATE:** ARCC сохраняет single-bad-symbol correction, но до обнаружения первого дефекта ослабляет double-symbol detection относительно SCCDCD. ARCC §6.1–6.2, PDF pp.7–8, Fig.4.
4. **SOURCE-CANDIDATE:** основной performance/power comparison ARCC меняет DRAM organization x4/36-device ranks на x8/18-device ranks, а не только ECC decoder. ARCC §4.2.4, §7, PDF pp.6,8–9, Table 1.
5. **SOURCE-CANDIDATE:** в оценке DFMC 2023 initial Hamming повышается до LPC после первой ошибки без downgrade; multiple-before-access scenario даёт ERR у DFMC и OK у static LPC. PDF pp.4–5, §VI.B, Table VI.
6. **SOURCE-CANDIDATE:** 99.956% DFMC 2023 — indicator, экстраполированный из внешних field-error statistics, а не сообщённая эмпирическая доля успешных инжекционных прогонов. PDF p.5, Table VII и непосредственно предшествующее рассуждение.
7. **SOURCE-CANDIDATE:** DFMC 2023 включает monitor/recode затраты в свои estimates; reported total energy saving относительно static LPC связано с RAM contribution, хотя standalone controller дороже. PDF pp.4–5, Tables II–V,IX.
8. **INFERENCE-CANDIDATE:** перечисленные результаты не подтверждают energy saving per successful task внешней radiation SRAM при одном и том же reliability constraint. Основание: ARCC §6–8; DFMC Tables VI–IX; в Lu и DFMC отсутствует target SRAM physical/cost contract. Это ограничение переноса, не литературный вывод о невозможности адаптации.

## 9. Краткий HANDOFF TO ORCHESTRATOR

Task PA-MEMORY-PROTECTION-SELECTION-01; report v1.0. Фактически прочитаны Lu 2022, ARCC 2013, SBCCI DFMC 2023; exact PDF identities/checksums — §2. DEMC 2026 отсутствует и отложен по указанию пользователя. Lu 2020 и другие кандидаты не подключались.

- **А:** пригоден Lu как архитектурный comparator fixed ECC + conditional write + coordinated user service; quantitative SRAM RE требует А1–А4.
- **Б:** ARCC — RELATED; DFMC 2023 — CORE targeted comparator, но не selected controller. Оба показывают занятые механизмы; перенос численных выигрышей и равенства требований не обоснован. Нужны named inputs §7.2, а не общий повторный SR.
- **RQ-003:** точно задать outcome/capability в слабом/сильном/переходном состоянии; early multi-error safety не подменять способностью исправить первый одиночный fault.
- **RQ-004:** считать только доступные decoder/service observations с exposure/access bias; latency усиления и отсутствие предупреждения сохранить явно.
- **RQ-005:** отдельно standing hardware/storage, reads/writes/bandwidth, transition interruption, RAM activation и controller energy; power/energy и whole-system/memory/controller denominators не смешивать.
- **Disposition:** bounded extraction **COMPLETED WITH NAMED GAPS**; готовность к quantitative RE внешней SRAM **NOT ESTABLISHED BY THESE TEXTS**. Полного выбора А/Б, изменения принятого задела, нового контроллера или научного принятия не выполнялось.

## 10. Контроль поставки

Один новый draft report; исходные пакеты, main, статусы и permanent registries не изменяются. PDF в Git не добавляются. На instruction base repository validator уже выдаёт **1 error / 44 warnings**: существующий `BROKEN_LINK` в `docs/scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md` (парсер ссылки на выражение `dict(...)`) и существующие metadata/draft warnings. Повторная проверка с новым отчётом дала тот же набор: новых diagnostics нет. Existing defects не исправляются в данной задаче. Whitespace check нового файла не выявил замечаний. Публикация отдельной аналитической ветки не означает acceptance.
