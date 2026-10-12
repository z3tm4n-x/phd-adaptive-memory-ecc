# Воспроизведение интегрированной связки

Из корня checkout в Linux/WSL, Python3.14.4, Vivado2025.2
(SW6299465/IP6300035), установлен Zynq-7000; Yosys0.52 с `yosys-abc`,
Icarus12. Python-код использует только стандартную библиотеку. Tool versions
и platform зафиксированы в `outputs/verification.json` и `manifest.json`.

```bash
VIVADO=/home/z3tm4n/bin/vivado-wsl python3 -B experiments/t104-rtl-resume/integrated/reproduce.py --sta
```

`VIVADO` можно заменить своим корректным исполняемым wrapper/executable.
Он должен загрузить установленную среду Vivado; полный путь установки здесь
`/home/z3tm4n/tools/Xilinx/2025.2/Vivado`. Местный wrapper задаёт en_US.UTF-8,
подключает settings64.sh и добавляет каталог совместимых системных библиотек
`/home/z3tm4n/vivado_compat_libs` в LD_LIBRARY_PATH. Это часть местной среды,
не переносимый научный вход. Нативный поддерживаемый Linux не обязан иметь
такой каталог. Использование пользовательских compiler variables отмечено
самой XSim в сохранённом логе.

Контрольные SHA256 внешних инструментальных источников:

| Источник | SHA256 |
|---|---|
| vivado-wsl |231897138a8e259d9b1753d1a400c4298bd93de3f2546127e466b67b35bbb6e0|
| XPM FIFO HDL |60f6087dbfbe0602796fefef3231963247559fd3eac4641241ccf6397bd91b9d|
| XPM CDC HDL |27592359d8363d7e6575298f9d0faa7c9f9258ea77f19c9a38946fbaf3783f09|

Команда создаёт **новый** `.build/integrated-reproduce-<id>/`; опубликованные
и исторические файлы не перезаписывает. Отдельно сохраняются stdout/stderr,
реальные XSim-трассы, инструментированные proof harnesses, STA и routed DCP.
Последний локальный полный прогон: **596.245с**; routed STA174.972с.
Это измерено на данной машине; не WCET контроллера. Пик памяти Vivado — по
`run/sta.log` в архиве, относится к процессу инструмента, не FPGA.

Воспроизведение включает82старых+7новых unit tests, compileall, три режима
полных трасс, MMCM/full-top test, три trace-mutants, counter/frame/warmup/rule,
guard/admission induction и два formal-mutants. Нормальные инварианты обязаны
быть proved. Статус мутанта хранится явно; отсутствие доказательства не считается
его отвержением. В финальном прогоне оба имеют найденные контрпримеры, хотя
оставшиеся свойства за срок PDR могут остаться undecided.

STA **ожидаемо показывает незакрытый проект**, что сохраняется как результат.
Успешный exit воспроизведения означает полученные проверяемые артефакты,
**не** `setup/hold PASS` либо завершение Б. Результат с virtual I/O нельзя
подменять только положительным internal hold. Только стандартные XPM-исключения;
setup/hold uncertainty .5/.1нс. `check_timing=0` не отменяет отрицательные slack.

## Быстрые отдельные проверки

```bash
python3 -B -m unittest discover -s experiments/t104-rtl-resume/integrated -p 'test_*.py'
python3 -B experiments/t104-rtl-resume/integrated/bounds.py
python3 -B experiments/t104-rtl-resume/integrated/physical_audit.py
python3 -B experiments/t104-rtl-resume/integrated/check.py --clocked
python3 -B experiments/t104-rtl-resume/integrated/prove.py --case frame
python3 -B experiments/t104-rtl-resume/integrated/guard_proof.py
python3 -B experiments/t104-rtl-resume/integrated/admission_proof.py
```

`check.py --phase {0,1,3} --stress {0,1,2}` не образует полный декартов sweep:
основные пары0/0,1/1,3/2 объявлены в reproduce.py. STRESS1 вне огибающей
T135, STRESS2 проверяет допустимое количество loss-переходов плотным пакетом;
его непрерывные ERR — directed verification, не выборка радиационной среды.

## Независимое прочтение сохранённых трасс без Vivado

```bash
T104_EVIDENCE=$(mktemp -d)
python3 -m zipfile -e experiments/t104-rtl-resume/integrated/evidence.zip "$T104_EVIDENCE"
python3 -B experiments/t104-rtl-resume/integrated/check.py --log "$T104_EVIDENCE/simulation/0.log"
python3 -B experiments/t104-rtl-resume/integrated/check.py --log "$T104_EVIDENCE/simulation/1.log"
python3 -B experiments/t104-rtl-resume/integrated/check.py --log "$T104_EVIDENCE/simulation/2.log"
```

`simulation/3.log` — отдельный production clocked top; его CLOCKED_PASS и
контроль10ID проверяются в tb_clocked. SHA каждого файла/членаZIP дан в manifest.
Три отрицательные трассы лежат в `mutation/`; обычный checker должен отвергнуть
их, поэтому ненулевой выход там ожидаем и не считается положительной трассой.

Даты/пути/время инструментальных логов при повторе изменяются; требуются те же
семантические результаты, параметры и доказательства, а не побайтное равенство
stdout другой установки. Главные арифметические JSON используют Fraction и
должны совпасть точно. Перегенерация proof/STA — **воспроизведение**, независимые
формулы/checker/source audit — отдельные проверки с границами из PROOF.md.

Только авторская упаковка уже проверенного прогона (не нужна рецензенту):

```bash
python3 -B experiments/t104-rtl-resume/integrated/reproduce.py --collect experiments/t104-rtl-resume/.build/integrated-reproduce-1791537081689537980
```

Она сверяет tested-source hashes и обновляет только этот `integrated/outputs`,
ZIP и manifest. DCP, XSim binaries, исходные datasheets и большие рабочие
каталоги в Git не входят. Известные предупреждения XSim о позднем объявлении
TB-reg, timescale, generic glbl и vendor `$fatal` сохранены; runtime assertion
ошибок в положительных трассах нет. Стандартный тест не скрывает `Fatal:`.

Исторический `registered/prove_equivalence.py` без адаптации **не запускать**
для этой поставки: он записывает свой старый JSON. Здесь reused backend проверен
по закреплённым hashes, его прежний29-property результат остаётся по старому SHA.
