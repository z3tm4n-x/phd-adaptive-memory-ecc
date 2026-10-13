# C0: закреплённый запуск ARM и остаток времени

13.10.2026, продолжение0871ef5, контрольный выход к16.10. **Стартовый
профиль реализован и функционально проверен; полный временной верх пока
не установлен.** Прежняя запись «CP15/startup не реализован» заменяется
этим пакетом, но не заявлением об аппаратном запуске. В остаётся открытым.

Выбран один вариант: `C0-OCM-cold-r3p0`, xc7z020clg484-1, выделенный CPU0,
600МГц nominal, OCM, один GP0/50МГц; PL250/50 и принятый Б неизменны.
`startup_profile.json` — машинная конфигурация. Это условная демонстрационная
платформа, не паспорт конкретной платы. Cold POR/JTAG — условие входа;
ни платы, ни JTAG в этой работе не запускались.

## 1. Исполнение до начала опыта

1. `startup_host.tcl::t105_cold_prepare` исполняется внешним загрузчиком
   при остановленных CPU после POR, уже загруженной через JTAG PL и
   **низком qualified_switch**. Callback read32/write32 обязан завершать
   операции по порядку. Процедура не подключается к устройству сама.
   Cold provenance нельзя установить одним чтением SCTLR после чужой ОС.
2. CPU1 удерживается в reset/clock-stop; DMAC, USB, GEM, SDIO — в reset;
   APER clocks выключаются. В принятом HWH все S_AXI GP/HP/ACP отключены;
   PCAP не используется после JTAG-загрузки. Нельзя останавливать активный
   DMA этой процедурой: отсутствие ранее начатой периферийной работы —
   cold-условие, а не следствие одного reset-bit. DAP/PCAP/отладчик после
   квалифицированного старта молчат; ни DVFS, ни runtime reset, ни OS.
3. ARM PLL программируется bypass→reset→FDIV36/CFG→release→lock→выход
   из bypass. Делитель2, CPU6:2:1; все OCM-банки переводятся наверх, SCU
   filter0…FFE00000. **В это время CPU не исполняет OCM**: UG585 запрещает
   OCM-доступ при смене CLK_621_TRUE. Маски/значения сверены с generated
   ps7_init и UG585; порядок FDIV взят из требования регистра, а не слепо
   скопирован. PLL poll ограничен числом попыток, не обещанием boot-WCET;
   неуспех прекращает запуск. Время подготовки не входит в миссию/B.
4. Загружаются два разных ELF: закреплённый `firmware.elf` в FFFC0000 и
   новый `startup.elf` в FFFE0000. PC=t105_boot, secure ARM SVC CPU0.
   Программа проверяет MIDR r3p0, PSv3.0, clocks/reset/OCM/SCU/L2/DevC и
   незапущенный mailbox. Эти значения **наблюдались только в тестовой модели**.
   Неверное чтение ведёт к trap без перехода в правило. Тёплый handoff
   с включённым MMU/I/D cache отклоняется; очистка dirty cache не имитируется.
5. Устанавливаются VBAR с терминальными exception-ветвями, IRQ/abort masks
   и выключенный GIC с запрещённым bypass. CPSID запрашивает также FIQ mask,
   но при Zynq NMFI=1 исключение FIQ нельзя основывать только на CPSR.F:
   оно опирается на GIC/routing, отсутствие внешней FIQ-активности и cold-вход.
   Физическое поведение NMFI эмулятор не подтверждает. L1 I/D и L2 остаются
   выключенными, SCTLR.Z=0, ACTLR D-prefetch/L2-hints=0, L2 prefetch=0.
   Это не утверждение об отключении всей внутренней спекуляции A9.
   TTBR/TTBCR/DACR, таблицы и MMU задаются явно; DSB/ISB и TLB/I/branch
   invalidation включены. Caches никогда не включаются, POR-clean — условие.
6. Запись C0RD в FFFED000 означает **только** успешное завершение startup,
   не начало опыта и не подтверждённый deadline. Переход в неизменный ELF,
   его BSS/driver init, затем phase0 непрерывно читает STATUS. Qualification
   разрешается только после достижения этого состояния и выполнения
   прежних условий чистой памяти Б. Инициализацию памяти ARM не доказывает.
   В действующей PL нет автоматического boot-ready interlock; удержание
   qualified_switch до polling — явное условие запуска, не скрытая связь.

Все действия загрузчика — **реализуемая последовательность плюс проверка
регистровой модели**, не выполненный физический запуск. Политика не может
обнулить mission budget: повторная загрузка после начала исключена.

## 2. Адреса, ресурсы и проверка

Short-descriptor MMU: domain0 **client**, все остальные no-access; TTBR0
в OCM, table walks non-cacheable/shareable, TTBCR.N=0. Отображены только
15 страниц:14 OCM и1 mailbox. DDR/SLCR/прочая периферия после запуска
не отображены. OCM Normal-NC/shareable; mailbox40000000…40000FFF —
Device/shareable/privileged-RW/**XN**. Не считаем время TLB miss нулём.

Две страницы прежнего ELF остаются RWX: код/rodata и BSS делят вторую
страницу. Это раскрытое ограничение сохранённого бинарного образа, не W^X
доказательство. Startup-код RO/X; таблицы, report и оба стека RW/XN.
Независимый decoder проверяет все4096 L1 и512 L2 entries, атрибуты,
тождество физических адресов, отсутствие лишних окон и запрет user-доступа.
Он не вызывает production builder; Unicorn CP15 **перехватывается** и
эмулируется отдельно, поэтому это не проверка реализации MMU/SCU в PS7.

| Величина | Значение и тип |
|---|---|
| Правило | Прежние4244B code/rodata,208B static; ELF SHA2562daf3308…09 — побайтно сохранён |
| Новый startup | 1268B загружаемых bytes,64B сумма static frames — результат компилятора |
| Таблицы | 18432B, резерв5страниц=20480B — конструкция |
| OCM резерв всего | 14страниц=57344B из262144B; включает2+2 code-pages,5 tables,1 report,2+2 stacks |
| Стеки | По8192B startup/правило; прежние240B frames правила не включают startup |
| CPU | 100% одного ядра зарезервировано; полезные CPU% и время неизвестны |
| PL/транспорт | Прежние2476LUT/5516FF/4,5BRAM36, bank96B/reply32B; дополнительной PL нет |
| STA | Прежний+0,225/+0,044нс,9source hashes совпали; новый route не выполнялся |

Tcl8.6.17 исполняет **саму** host-процедуру на mock-registers:5 исходов
(штатный, L2-on, нет PLL lock, не записался OCM, другая silicon version).
Её конечные регистры подаются фактическому startup ELF.28 ISA-сценариев:
штатный и27 отклонённых входов/сбоев readback; ещё3 независимые мутации
(кэшируемый MMIO, физический alias, manager-domain) отвергнуты decoder.
После startup прежний ELF доходит до4 вызовов phase0 без начала опыта.
Это не coverage всех microstates и не bound времени инструкций.

Функциональная проверка использует общие ABI/адреса/ISA emulator. Первичные
регистровые значения сверены человеком; модель не является независимой
моделью кремния. Записанные CASE/readbacks явно помечены emulated.
Ранняя отладочная сборка отличалась случайным STT_FILE; исправлено .file,
повторная сборка сравнивается по SHA. Tcl требовал explicit UTF-8 для пути;
эти неудачные запуски не заявляются успешными.

## 3. Почему полный сервис всё ещё не подписан

Конкретная команда `0xfffc09ec: ldr r3,[r1]`, r1=40000000, затем
`dmb sy` и зависимое ветвление по STATUS. Для **этого** C0-профиля не найден
документированный верх от принятия load ядром через SCU/PS interconnect,
GP0/SmartConnect/mailbox и обратную доставку до использования результата.
Readback правильного PLL и отсутствие конкурента не задают этот срок.
Даже гарантированные RVALID после AR-фронта на нашем slave не ограничивают
предшествующую доставку запроса и окончательное принятие ответа A9.

Минимальная недостающая строка: **C0-DEP-LOAD**, применимый односторонний
верх полной зависимой операции, включая miss/page-walk/ordering/drain,
для всех разрешённых состояний fixed A9r3p0/OCM/GP0. Чтобы закрыть весь d,
нужен также верх fetch/data/write/barrier или одно проверяемое утверждение
о целом `driver_step+loop`. Старые5 неизвестных не заменены удобными CPI.
Зависимое чтение — конкретный достаточный blocker, не единственный gap.

`B≤5d+662,006600нс` сохраняется; 1мс требует
**d≤199867,598680нс**. Это рассчитанное выделение, не measured maximum/WCET.
Работа startup не добавляется в каждый B, но page walks runtime входят
в d. После уже polling-начала первый cut≤2d+61,500600нс при том же
неустановленном d; конечность boot не подменяет конечность healthy service.

Адресно проверены UG585 Memory Access Sequence, TLB Match Process,
Interconnect Register Overview и CPU→GP: задаются пути, атрибуты,
ограничение outstanding/QoS, но не требуемый end-to-end bound. ARM/BSP
задаёт команды настройки и r3p0, не временную модель PS7. Нет доказательства
«нигде такой модели нет» или «A9 не укладывается» — **её нет в проверенных
входах**. Штатная функциональная эмуляция и протокольные backpressure
контрпримеры не доказывают достижимость бесконечного stall в реальном PS7.

## 4. Решение и три пути

| Путь | Проверенный смысл / цена | Рекомендация |
|---|---|---|
| Изолировать нынешний A9/OCM/GP0 | Реализовано; снимает неопределённость startup, оставляет C0-DEP-LOAD и другие временные члены | **Сохранить этот профиль и прототип к23.10.** Для временной приёмки нужен независимый envelope/model именно этой конфигурации, не новый подсчёт операций |
| Burst/DMA/ACP, перенос части в PL | Может уменьшить обмен; A9 fetch/OCM/completion всё равно остаются. Новые ownership/STA проверки, ориентир2–4дня | Не менять транспорт без основания, что проблемен его численный срок; полного возврата правила в PL не выдавать за этап В |
| Конечное extra FAST, T146(3) | Нужны конечные суммарное опоздание и число новых полос; watchdog запрета LOW этого не доказывает | Не назначать бесплатный FAST и не ослаблять Q/цену. Только с отдельным конечным основанием времени и согласованием |

**Передать Orchestrator точный недостающий вход**, сохранив функциональную
поставку; временную приёмку не присваивать. Самостоятельные дальнейшие
scalar-MMIO правки или широкий WCET-поиск не рекомендуются. Практический
запрос к поставщику timed-model/документации: C0-DEP-LOAD и полный d с данным
ELF, ревизией, картой, cache-off и single-owner assumptions; допускается
другой обоснованный миллисекундный B в T146. Если такой источник недоступен,
полная временная приёмка В остаётся незавершённой; выбор иной доказательной
платформы/объёма — оркестратору с этим остатком. Новое поручение на physical
tests, WCET-покупку или новый научный режим отсюда не следует.

## 5. Источники и происхождение

Issue105 прочитан в редакции2026-10-13T17:57:40Z; main при чтении
**a69fe3df97eac5a509f65446395891e71a8e9553**, инструкции совпали с веткой.
Прочитана окончательная T146 **c31017517fa81667b58ab4929f7db55ff383bd0f**:
оба loss CDC,6675,537049025нс и условия1–7 сохранены. Новая full-U теорема
не переносится на нашу E/r4. Снимок происхождения — inputs/issue105-startup.json.

Первичные источники, проверены13.10.2026:

- [UG5851.15, состояние после BootROM](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/APU-and-OCM-State-after-BootROM): cold caches/MMU disabled, SVC, прежнее размещение OCM/CPU1.
- [SCU/OCM](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/SCU-Address-Filtering), [Changing Address Mapping](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Changing-Address-Mapping), [CLK_621_TRUE](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-CLK_621_TRUE-Details): карта/порядок, запрет OCM во время ratio-change.
- [ARM_CLK_CTRL](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-ARM_CLK_CTRL-Details), [ARM_PLL_CTRL](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-ARM_PLL_CTRL-Details), [APER_CLK_CTRL](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Register-APER_CLK_CTRL-Details): источник/делитель/гейты.33⅓МГц — проектный clock input; фактический oscillator не проверен.
- UG585 System Level Control Register Summary и A9_CPU_RST_CTRL/USB/GEM/SDIO: offsets/reset masks. Числа ARM_PLL_CFG взяты из собственного Vivado2025.2 ps7_init, SHA в манифесте; это tool-derived settings, не измерения.
- [AMD BSP boot.S](https://github.com/Xilinx/embeddedsw/blob/145cea8fcf98268c8b163f732c181f008e887e53/lib/bsp/standalone/src/arm/cortexa9/gcc/boot.S), [xil_mmu.h](https://github.com/Xilinx/embeddedsw/blob/145cea8fcf98268c8b163f732c181f008e887e53/lib/bsp/standalone/src/arm/cortexa9/xil_mmu.h), [DevC](https://github.com/Xilinx/embeddedsw/blob/145cea8fcf98268c8b163f732c181f008e887e53/XilinxProcessorIPLib/drivers/devcfg/src/xdevcfg_hw.h): r3p0, CP15/L2 и DevC STATUS **offset0x14**. BSP не включён слепо: он по умолчанию включает caches, наш профиль этого не делает.
- [UG585 Memory Access Sequence](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/Memory-Access-Sequence), [TLB Match](https://docs.amd.com/r/en-US/ug585-zynq-7000-SoC-TRM/TLB-Match-Process): дополнительные обращения page walker остаются частью неизвестного срока.

Повтор — REPRODUCE.md. `startup-check.json`/`startup-host.json` — новые
свидетельства; прежний service-budget.json остаётся UNKNOWN-safe. Источники
правила и STA не изменялись; main/принятые results/другие задачи не менялись.
