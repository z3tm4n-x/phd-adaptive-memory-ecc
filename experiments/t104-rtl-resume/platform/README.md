# ZedBoard: проверенный вход и конкретная остановка STA

08.10.2026. Продолжение #104 от `6320707`, не завершение Б.
[Решение автора](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/134#issuecomment-6062039542):
основной XC7Z020-1CLG484C/250 МГц, сравнение -2/250 на том же RTL.
**Результат preflight: BLOCKED_DEVICE_SUPPORT.** Vivado запускается, но
`get_parts` не находит ни `xc7z020clg484-1`, ни `xc7z020clg484-2`.
429 доступных variants, ни одного `*7z*`. Это не неудачный синтез,
не недостаточность -1/250 и не проверка лицензии для выбранного устройства.

## Что проверено и что остаётся входом

| Поле | Основание / статус |
|---|---|
| Программа | Фактический запуск Vivado2025.2, SW build6299465; `outputs/platform.json` |
| Установка | `/home/z3tm4n/tools/Xilinx/2025.2/Vivado`, wrapper `~/bin/vivado-wsl` |
| Device support | Оба точных parts отсутствуют; запрос выполнен Tcl, не только поиск каталога |
| Коммерческий диапазон | SOURCE: DS187 v1.21, табл.2, с.3: Tj 0…85°C; PL VCCINT 0.95…1.05V. Это не измерение платы и не выбранные timing corners |
| Частота ядра | ASSUMPTION/цель проекта:250МГц; 4нс. PLL/MMCM и generated clocks ещё не реализованы |
| Опорные часы платы | SOURCE: ZedBoard HW UG v2.2 §2.5, с.18:100МГц IC17/Fox767-100-136; master XDC:GCLK/Y9 |
| Точность/джиттер | UNKNOWN для конкретного генератора/MMCM. ξ=1±10⁻⁵нс и фронт±0.25нс остаются условием T104, не свойством ZedBoard |
| FMC | SOURCE: HW UG §2.9.1/§3.1: банки34/35 питаются от VADJ. ASSUMPTION: выбранные3.3V через J18; фактическая ревизия/перемычка не осмотрены |
| SRAM | CY62167GE30-45ZXI, x16,002-20054 Rev.*F; прежний E и observed-write32 неизменны |
| SRAM/FPGA pins и нагрузка | UNKNOWN: рабочий адаптер, min/max трасс, ёмкость и turnaround. Master XDC даёт FPGA↔FMC, но не существующую разводку SRAM |
| STA/ресурсы | NOT RUN: WNS/TNS/WHS/THS, unconstrained paths, LUT/FF/BRAM/DSP и longest paths — null, не ноль |

Отдельно сверены таблица переключений SRAM (с.10) и диаграммы записи (с.14).
Сохраняется OE HIGH при записи; конец задаётся первым снятым разрешающим
сигналом. Сведение только к `tPWE=35нс` не заменяет полного цикла.
Для -45: read45нс, tWC45нс, tPWE/tAW/tSCE/tBW35нс, tSD25нс;
полные E148ξ/observed-write216ξ и резервы164/240 остаются прежними.
Физическое E/ERR под облучением этим чтением datasheet не квалифицировано.

## Повтор и снятие блокера

В Ubuntu/WSL, из корня checkout:

```sh
vivado-wsl -version
python3 -B experiments/t104-rtl-resume/platform_probe.py --write
```

Можно задать `--vivado <executable>`. Probe только запрашивает версию и parts;
ожидаемый exit Vivado=2 при зафиксированном блокере. Не трактовать этот exit
как провал timing. Лог/журнал остаются в `.build/platform-probe`; компактный
отчёт включает их происхождение. Обёртка выдаёт предупреждение en_US.UTF-8,
но Tcl исполнился и оба запроса вернули определённый результат.

Найден локальный установщик
`/home/z3tm4n/tools/Xilinx/.xinstall/2025.2/xsetup`; прочитана только `--help`.
Он поддерживает добавление устройств через Add. EULA не приняты, установка
и загрузки не запускались. Два пути: добавить Zynq-7000 support в2025.2
или предоставить другую установленную Vivado с обоими exact parts. После
этого повторить probe; наличие Kintex/Artix не повод заменять выбранную FPGA.

Устройство само по себе не закрывает все входы. Следом нужны проверенные
clock/generated-clock constraints, declared uncertainty/reset, OOC-контракт
всех портов, SRAM/FMC wrapper и конкретные min/max/load-допущения.
`vivado_ooc.tcl` пока лишь guarded flow; он ещё не выполнен до post-route.
Полный XDC не объявлен готовым. Нельзя blanket false-path скрывать Gray
или stable bundled buses. Отчёты должны отдельно проверять внутренние3нс,
выход4нс/возврат2нс, corners setup/hold и 10% полного E/write/CDC/очереди.
Положительный внутренний WNS на4нс этого не заменяет.

Если последующая проверка -1/250 не пройдёт, остаются две разрешённые
ветви:200МГц **с новым полным календарным расчётом**, либо локальный pipeline/
упрощение при250МГц и семантическая регрессия. Сейчас оснований выбирать
между ними ещё нет: аппаратный timing не измерен. PS/ARM и этапы В/Г не начаты.

## Происхождение

Первичные документы прочитаны 08.10.2026; локальные копии/кэш вне Git.

- [ZedBoard HW User Guide v2.2, 27.01.2014](https://files.digilent.com/resources/programmable-logic/zedboard/ZedBoard_HW_UG_v2_2.pdf), §2.5,2.9.1,3.1. Прочитан доступный текст; прямое скачивание PDF вернуло JS challenge и не обходилось.
- [Digilent master XDC](https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Zedboard-Master.xdc), SHA256 `4c3ae9d40dce0cb0ca86fdd381a3ec05e0cc099c6f17f8299e270690b2b58b5c`. Закреплён именно hash содержимого, не приписан неизвестный commit.
- [AMD DS187 v1.21,01.12.2020](https://docs.amd.com/api/khub/documents/uaBd8Qxmf_K1~~tiVnOxrw/content), табл.2 с.3. Диапазоны спецификации не заменяют фактических Vivado corners.
- [AMD UG973,2025.2](https://docs.amd.com/r/2025.2-English/ug973-vivado-release-notes-install-license/Supported-Devices): поддержка семейства продуктом не означает установку его файлов на машине.
- [Infineon002-20054 Rev.*F](https://www.infineon.com/assets/row/public/documents/10/49/infineon-cy62167g30-cy62167ge30-16-mbit-1m-words-x-16-bit-2m-words-x-8-bit-static-ram-with-error-correcting-code-ecc-datasheet-en.pdf?fileId=8ac78c8c7d0d8da4017d0ee9e49f72cf), SHA256 `a7d9faf23208b6c0f3b2be402feb8653ff0c6f649306fc246605189018a9ed1f`, совпадает с ранее закреплённым T104.

Научные входы T104/T110/T114 и старые пакеты не изменялись. Эти сведения
подготовлены для инженерного продолжения, не присваивают новое принятие.
