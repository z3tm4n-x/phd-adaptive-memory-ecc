# Повтор T105

WSL Ubuntu 26.04, Python 3.14.4, GCC 15.2.0, ARM GCC 14.2.1,
binutils 2.45.50, QEMU 10.2.1; Vivado 2025.2 build 6299465.
Yosys/Icarus используются для малых формальных/AXI проверок.
Точные версии/хеши — outputs/manifest.json и tools.json.

Из корня checkout, без Vivado и без сети после подготовки:

```sh
python3 experiments/t105-arm-rule/reproduce.py --repeat-binary
```

Первый запуск на новом окружении: добавить --bootstrap (закреплённые
Ubuntu packages распаковываются только в .tools, без sudo).
Повтор проверяет прежние 20 165 C / 512 ARM переходов, 20 019 пакетов / 512 ARM,
RTL-collector, AXI, две SAT-композиции и их мутации, драйвер/firmware,
8 unit tests, Python compilation и хеши пакета. Порядка 10–20 с хоста;
не время ARM. Для ELF проверяется повторная сборка прежнего теста,
firmware имеет отдельный детерминированный SHA.

Полный повтор трёх коротких vendor-XPM трасс и нового post-route:

```sh
python3 experiments/t105-arm-rule/reproduce.py --integration --full
```

Обычно 5–8 минут и около 4 ГБ памяти хоста. --full создаёт свежую папку,
PS7/SmartConnect, address segment, выполняет synth/place/route и отдельную
read-only проверку внешних SRAM/FMC окон. Установка и лицензии Vivado
нужны; это не обращение к плате. Wrapper по умолчанию:
 /home/z3tm4n/bin/vivado-wsl; override через VIVADO.

Отдельно:

```sh
python3 experiments/t105-arm-rule/run_integration.py --phase 11 --stress 2
python3 experiments/t105-arm-rule/run_full.py
python3 experiments/t105-arm-rule/collect_full.py <напечатанный BUILD>
```

Трассы используют native C/DPI, не ARM timing model. NW/NH/NR 40/80/130
подставляются только в staged diagnostic header, production не меняется.
Исходные полные таймеры проверены verify/verify_batch и ARM ELF.
Стресс 3/1 выходит за договорные предложения/backpressure: 5930 нс
не выдаются за допустимый ответ приложения.

## Проверяемые материалы

outputs/sta содержит полные первичные routed reports; outputs/io —
все 8 clocked min/max/corner reports. Их диагностические clocked slacks
не являются приёмкой: check_io.py составляет реальные SRAM windows.
Стандартный независимый фазовый checker и карта pins взяты из Б без правок.

outputs/check-evidence.zip содержит SAT logs/harness/counterexamples и
малые raw/packet AXI-трассы; hashes — check-evidence.json.
Большие vendor traces, generated IP и checkpoints остаются в .build,
пути/хеши — integration-*.json и full-top.json. Не перепутать исторический
byte-CRC route с окончательным 7-word route.

`firmware.elf` — связанный образ для OCM 0xfffc0000, mailbox 0x40000000.
Он не загружался в физический PS7; драйвер проверен отдельно, полный
BSP/OCM/MMU/GIC и верх времени остаются обязательствами.
QEMU-тестовые ELF используют loader и semihosting только в harness.

Обходы среды раскрыты: установленный iverilog-vpi передаёт ошибочный
литерал `0-3` в compiler flags. VPI bridge собирается напрямую GCC против
публичных VPI headers/libs, установка не исправлялась. Yosys assertions
понижаются через async2sync/chformal; это не ослабление свойства.
Vivado wrapper использует уже имевшийся LOCPATH.
