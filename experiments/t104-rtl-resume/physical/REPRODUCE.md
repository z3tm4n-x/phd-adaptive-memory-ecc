# Повтор T104 physical

Все команды ниже — из корня checkout в Linux/WSL. Python3.14.4, Yosys0.52
`fee39a3284c90249e1d9684cf6944ffbbcbb8f90` с ABC, Icarus12.0,
Vivado2025.2 Build6299465, установленная поддержка Zynq-7000.
Прочитанные SHA, сохранённые входы и версии — [provenance](outputs/provenance.json).
Рабочая ветка `t104-rtl-resume`, parent99c0a414; все новые файлы в `physical/`.
Vendor PDF/XDC и объёмные DCP/сырые трассы не нужны для быстрой проверки.

## 1. Быстрая проверка опубликованного пакета

```sh
python3 experiments/t104-rtl-resume/physical/verify.py
```

Проверяются SHA-256 отчётов, точные compiled RTL/XDC/TCL inputs, побайтная
сохранность перечисленных базовых файлов, повтор внешней фазовой композиции,
pin-plan и рациональных верхов. Затем заново выполняются97 unit tests и
`compileall` исходников без старых `.build`. Около15 секунд на использованной
машине. Это **не новый запуск STA/формальных solver**; статус явно указан
в выходном `physical-verify-*/summary.json`.

Отдельные команды тестов:

```sh
python3 -m unittest discover -s experiments/t104-rtl-resume -p 'test_*.py'
python3 -m unittest discover -s experiments/t104-rtl-resume/integrated -p 'test_*.py'
python3 -m unittest discover -s experiments/t104-rtl-resume/physical -p 'test_*.py'
```

## 2. Свежие формальные прогоны и проверки

```sh
set -e
for proof in backend components candidate map chain join history transport progress; do
  python3 "experiments/t104-rtl-resume/physical/prove_${proof}.py"
done
python3 experiments/t104-rtl-resume/physical/check_crc.py
```

Сценарии сохраняют harness, фактические источники, полный solver log и
summary в новых каталогах `experiments/t104-rtl-resume/.build/`; ни один
исторический эксперимент не переписывается. `prove_components` также
запускает generation guard/admission; отдельно guard можно повторить:

```sh
python3 experiments/t104-rtl-resume/physical/guard_proof.py
```

Обычный miter:29/29 normal и29/29 prevalidated. Для мутантов ожидается
контрпример, а не успешное доказательство. Не путать `permit-reachable`
с ошибкой нормального RTL. Прогон backend около4 минут, components около2–3;
весь набор ориентировочно8–15 минут. Лимиты solver заданы в скриптах,
timeout не классифицируется как доказательство. Нужна запись в `.build`.

## 3. Vendor simulation и полный STA

На этой машине wrapper `/home/z3tm4n/bin/vivado-wsl` подхватывает settings64.sh
из `/home/z3tm4n/tools/Xilinx/2025.2/Vivado`. В другом окружении задать `VIVADO`
путём к доступному исполняемому Vivado (не строкой с аргументами).

```sh
set -e
python3 experiments/t104-rtl-resume/physical/run.py sim --phase 0 --stress 0
python3 experiments/t104-rtl-resume/physical/run.py sim --phase 3 --stress 2
python3 experiments/t104-rtl-resume/physical/run.py sim --phase 3 --stress 1
python3 experiments/t104-rtl-resume/physical/run.py pads
python3 experiments/t104-rtl-resume/physical/run.py sta
```

`stress1` намеренно вне временной огибающей: проверяется сохранность двух
запросов, а не3 мкс. Pad test использует W19 и production-width параметры;
долгие интервалы таймеров охватывает индукция, не длительность короткого xsim.
Каждый `run.py` до запуска копирует и хеширует зависимости. `completed` для
STA означает завершение инструмента; положительный slack дополнительно
проверяют `collect.py`/`verify.py`, а не этот флаг.

Финальный сохранённый run: `physical-sta-1791823709343438952`,
279,04 секунды, peak3342,574 MB. Это полный `board_top`, не OOC одного lane.
STA при ином tool/version/placement может дать другой запас; для новой
поставки требуются setup≥0,1 нс и hold>0 при неизменных uncertainty0,5/0,1.
Исходный `evidence_runs.json` точно выбирает проверенный run, не ищет лучший.

## 4. Проверка внешних окон нового routed checkpoint

Из строки `BUILD` последнего STA взять фактический каталог. Пример для
сохранённого run (каталог `io-review` должен ещё не существовать):

```sh
T104_BUILD=experiments/t104-rtl-resume/.build/physical-sta-1791823709343438952
/home/z3tm4n/bin/vivado-wsl -mode batch -nojournal -nolog \
  -source experiments/t104-rtl-resume/physical/inspect_io.tcl \
  -tclargs "$T104_BUILD/run/routed.dcp" experiments/t104-rtl-resume/.build/io-review
python3 experiments/t104-rtl-resume/physical/check_io.py \
  experiments/t104-rtl-resume/.build/io-review
python3 experiments/t104-rtl-resume/physical/check_pins.py "$T104_BUILD/run"
python3 experiments/t104-rtl-resume/physical/bounds.py
```

Для проверки загруженного оригинального Master XDC у `check_pins.py` есть
`--master-xdc PATH`; сверяется закреплённый hash. Без него проверяются
опубликованные pin-факты против actual routed pins. Исходник автоматически
не загружается и не кладётся в Git. Около20 секунд для I/O-инспекции.

## 5. Сборка компактного пакета и доступность

`collect.py` переупаковывает **существующие** именованные прогоны из
`evidence_runs.json`, не выполняет эксперимент заново. На исходной машине:

```sh
python3 experiments/t104-rtl-resume/physical/collect.py
python3 experiments/t104-rtl-resume/physical/verify.py
```

Для новых прогонов создать собственный JSON с их напечатанными именами и
передать `--runs PATH --output PATH` (не подменять исторические отчёты).
Следует также создать `final-pins.json` командой `check_pins --output`
в `.build` текущего checkout. `collect.py` отвергает несовпадение источников
выбранного STA и симуляций. Windows-worktree gitdir в WSL читается через
явное преобразование пути, без редактирования `.git`.

В Git входят ограниченные timing/I/O reports, машинные сводки и архив
формальных журналов; SHA каждого — `outputs/SHA256.json`. DCP, project cache,
полные event/pin traces остаются в игнорируемом `.build` по пути из provenance.
Их можно регенерировать приведёнными командами; для чтения доказательных
итогов доступ к Windows-пути не требуется. Для полного повторения достаточно
около3–5 GB свободного места; исходный checkout с историческими runs больше.
Эта оценка хранения и8–15 минут solver — ориентиры, не измеренный WCET.

Критические независимые контрпроверки и общие зависимости описаны в
[VALIDATION](VALIDATION.md). Рекомендуемая рецензия: граница generation/tag,
full-payload join, общий ACK-tail/огибающая, знаки и углы внешнего WE/hold
бюджета; не повторный литературный или радиационный аудит.
