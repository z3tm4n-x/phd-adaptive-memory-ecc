# Повтор T105

WSL Ubuntu 26.04, Python 3.14.4, GCC 15.2.0, ARM GCC 14.2.1,
binutils 2.45.50, QEMU 10.2.1; Vivado 2025.2 build 6299465.
Yosys/Icarus используются для малых формальных/AXI проверок.
Unicorn2.1.4 / pyelftools0.33 — полный ARM ELF с RTL MMIO;
закреплённые wheels в outputs/analysis-tools.json, установка только .tools.
Точные версии/хеши — outputs/manifest.json и tools.json.

Из корня checkout, без Vivado и без сети после подготовки:

```sh
python3 experiments/t105-arm-rule/reproduce.py --repeat-binary
```

Первый запуск на новом окружении: добавить --bootstrap (закреплённые
Ubuntu packages распаковываются только в .tools, без sudo).
Повтор проверяет прежние 20 165 C / 512 ARM переходов, 20 019 пакетов / 512 ARM,
RTL-collector, AXI, четыре SAT-композиции и их мутации, 20 019 driver vectors,
три успешных ARM-ISA/RTL трассы и две fault-трассы, драйвер/firmware,
11 unit tests, Python compilation и хеши пакета. Порядка 30–90 с хоста;
не время ARM. Для ELF проверяется повторная сборка прежнего теста,
firmware имеет отдельный детерминированный SHA.

Полный повтор трёх коротких vendor-XPM трасс, двух сервисных по4мс и post-route:

```sh
python3 experiments/t105-arm-rule/reproduce.py --integration --full
```

Обычно 8–12 минут и около 4 ГБ памяти хоста. --full создаёт свежую папку,
PS7/SmartConnect, address segment, выполняет synth/place/route и отдельную
read-only проверку внешних SRAM/FMC окон. Установка и лицензии Vivado
нужны; это не обращение к плате. Wrapper по умолчанию:
 /home/z3tm4n/bin/vivado-wsl; override через VIVADO.

Отдельно:

```sh
python3 experiments/t105-arm-rule/run_integration.py --phase 11 --stress 2
python3 experiments/t105-arm-rule/verify_isa.py
python3 experiments/t105-arm-rule/prove_compact.py
python3 experiments/t105-arm-rule/run_integration.py --stress 3 --cycles 1000000
python3 experiments/t105-arm-rule/run_integration.py --stress 4 --cycles 1000000
python3 experiments/t105-arm-rule/check_price.py --published
python3 experiments/t105-arm-rule/run_full.py
python3 experiments/t105-arm-rule/collect_full.py <напечатанный BUILD>
```

Трассы используют native C/DPI, не ARM timing model. NW/NH/NR 40/80/130
подставляются только в staged diagnostic header, production не меняется.
Исходные полные таймеры проверены verify/verify_batch и ARM ELF.
Стресс 3/1 выходит за договорные предложения/backpressure: 5930 нс
не выдаются за допустимый ответ приложения.

Stress3 и4 с phase0 — отдельные одинаковые offers через500,02мкс,
READY≤80нс, нет ERR/loss. Отчёт явно ограничен стационарным тихим сервисом;
не заменяет W524288 startup или миссионную цену. check_price --published
работает без .build/vendor logs по опубликованному компактному ledger
в check-evidence.zip и проверяет его hashes. Доказательство максимума
скользящего окна использует все узлы кусочно-линейного интеграла, не только bins.

## Проверяемые материалы

outputs/sta содержит полные первичные routed reports; outputs/io —
все 8 clocked min/max/corner reports. Их диагностические clocked slacks
не являются приёмкой: check_io.py составляет реальные SRAM windows.
Стандартный независимый фазовый checker и карта pins взяты из Б без правок.

outputs/check-evidence.zip содержит SAT logs/harness/counterexamples и
малые raw/packet AXI-трассы, actual-ISA MMIO/raw/cut/packet и компактный
сервисный ledger; hashes — check-evidence.json. Архив около1,1МБ.
Большие vendor traces, generated IP и checkpoints остаются в .build,
пути/хеши — integration-*.json и full-top.json. Не перепутать исторический
byte-CRC route с окончательным 7-word route.

`firmware.elf` — связанный образ для OCM 0xfffc0000, mailbox 0x40000000.
Он исполнялся в Unicorn с RTL mailbox, но не загружался в физический PS7; полный
BSP/OCM/MMU/GIC и верх времени остаются обязательствами.
QEMU-тестовые ELF используют loader и semihosting только в harness.

verify_isa не начисляет время инструкциям и не моделирует GP0/SmartConnect.
Три successful case: reference0, optimized0, optimized stalls0…7; seed10520261015,
по32 завершённых ответа, затем явная остановка. Две мутации: CRC и sequence.
Instruction counts, peripheral ticks и ARM WCET разведены в timing-residual.json.
firmware-reference.elf сохраняет алгоритм a477950; filename/comments другие,
он не является независимым oracle. Production rule/CRC/timers не менялись.

После a477950 production RTL/recipe/XDC не изменены: check_route_reuse
сверяет9 файлов с сохранённым routed manifest. Поэтому новый Vivado run
в этом продолжении не нужен; --full доступен для независимого повтора.

Обходы среды раскрыты: установленный iverilog-vpi передаёт ошибочный
литерал `0-3` в compiler flags. VPI bridge собирается напрямую GCC против
публичных VPI headers/libs, установка не исправлялась. Yosys assertions
понижаются через async2sync/chformal; это не ослабление свойства.
Vivado wrapper использует уже имевшийся LOCPATH.
