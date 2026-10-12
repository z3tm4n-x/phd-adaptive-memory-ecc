# Повтор checkpoint разделения доменов

Из корня клона ветки `t104-rtl-resume`, Linux/WSL:

```sh
python3 -B experiments/t104-rtl-resume/split/checkpoint.py --full \
  --vivado /home/z3tm4n/bin/vivado-wsl
```

Нужны Python3, Icarus/VVP, Yosys/ABC и Vivado2025.2 с Zynq7000.
Версии и hashes реально использованных XPM записывает `manifest.json`.
Путь исполняемого Vivado передаётся аргументом. Полный сборщик hashes
в этой версии привязан к установленному XPM в
`/home/z3tm4n/tools/Xilinx/2025.2/Vivado/data/ip/xpm`: на ином хосте
этот путь надо обеспечить либо явно изменить только путь сбора provenance,
раскрыв отличие. Сами RTL/Tcl и отдельные проверки ниже от этого пути
не зависят. Это известное ограничение переносимости convenience runner,
не скрытая подмена версии IP. Скрипт `checkpoint.py`
фиксирует источники до/после; расхождение останавливает проверку.
Вложенные tools должны быть доступны в PATH. Запускать не из PowerShell
Python, а внутри WSL/Linux. При Windows-created worktree прежний runner
сам разрешает `.git` pointer через `/mnt/<drive>`; указатель не редактируется.

Команда повторяет расчёт баланса; PDR обвязки/ошибочного варианта;
Icarus-проверки календаря/guard;6 запусков настоящего XPM в xsim;
compileall; полный прежний `run.py --rtl --formal --regression-A` без
`--write`; затем маршрутизацию одного RTL на−1 и справочном−2.
В старые outputs не записывает. Локальные сборки/DCP и полные PIN logs —
`experiments/t104-rtl-resume/.build/`, исключённый изGit. Ничего не удаляется.

В новый каталог записываются только `checks.json`, `lane_proof.json`,
`timing_balance.json`, `manifest.json` и компактный `evidence.zip`.
Архив содержит все финальные STA/XDC reports, журнал синтеза/маршрутизации,
результаты функциональных/formal шагов и регрессию. Детальные симуляционные
PIN traces воспроизводятся и остаются в `.build`; их hashes — `checks.json`.
Вендорский исходный код и DCP в архив не включаются.

Ошибки функциональных/формальных проверок завершают команду ненулевым
кодом. Отрицательный STA сохраняется как результат, **не** выдаётся за
PASS по коду возврата Vivado/runner. См. `STA.*.component_timing_target_met`
и поля WNS/TNS/WHS/THS; `B_closed` намеренно false для этого компонентного
checkpoint независимо от STA. Актуальные длительности шагов, путь сборки,
платформа и версия находятся в манифесте. Планировать примерно10–20мин,
4 потока Vivado и до4ГБ RAM на один route; это ориентир, не WCET.

Для более короткой проверки можно отдельно выполнить:

```sh
python3 -B experiments/t104-rtl-resume/split/timing_balance.py
python3 -B experiments/t104-rtl-resume/split/prove_lane.py
python3 -B experiments/t104-rtl-resume/split/check.py --vendor --write
```

SHA поставки извлекается из commit, содержащего этот пакет:

```sh
git log -1 --format='%H %P' -- experiments/t104-rtl-resume/split
```

Самоссылка на SHA внутри того же commit не используется. Exact SHA также
сообщается в #135 и PR134 после push и проверки remote. `manifest.json`
хеширует именно код/XDC исполнения; timestamps, длительности и абсолютные
пути могут отличаться при повторе. Формальный статус, транзакции/фронты,
арифметика и семантика проверок должны воспроизводиться. Иные версии
Vivado могут менять placement/STA и требуют отдельной записи результата.
