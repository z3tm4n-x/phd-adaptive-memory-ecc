# Повтор первого сквозного выхода Г

Из корня checkout, Python≥3.11, только стандартная библиотека:

```sh
python3 experiments/t106-system-emulation/reproduce.py
```

Проверяет закреплённые хеши, семь unit tests, обе опубликованные полные
сжатые трассы (~2,4МБ вместе), пять отрицательных мутаций и раздельную цену.
Это **независимая обработка записанной трассы**, не повтор ARM/RTL.
Распаковка получается автоматически; отдельного Windows-пути для SR нет.

Новый actual-ISA/vendor-RTL запуск обоих режимов плюс тот же checker:

```sh
python3 experiments/t106-system-emulation/reproduce.py --execute --bootstrap
```

Linux/WSL, GCC, Vivado2025.2 с Zynq7000 нужны заранее. Wrapper по умолчанию
`/home/z3tm4n/bin/vivado-wsl`; другой путь задаётся `VIVADO`.
`--bootstrap` скачивает только три закреплённых wheels из принятого
analysis-tools.json, проверяет SHA256, ставит в локальный `.tools/analysis`.
После подготовки флаг не нужен. Вместо установки можно задать
`T106_ANALYSIS=/absolute/path/to/existing/pinned/analysis` — именно так
первый запуск переиспользовал ранее установленные пакеты В.
Ни sudo, ни подключение платы, ни изменение accepted outputs не нужны.

Среда первого запуска: Ubuntu26.04/WSL2, Python3.14.4, GCC15.2,
Vivado2025.2 build6299465, Unicorn2.1.4, pyelftools0.33. Используются
принятые ELF, новой пересборки ARM в Г пока нет. CP15/GIC/table модель
переиспользована явно из В; она не тактовая модель hard PS7.
Actual-запуск занимал~28с хоста на режим, память xsim peak~346МБ,
Vivado peak~1650МБ. Дополнительно checker обрабатывает~180тыс строк на
режим. `.build/` содержит большие сырые trace/vendor logs и generated IP,
в Git их нет; сжатые trace и run.json поставлены в outputs.

Каждый режим начинает отдельную миссию из одного и того же clean state;
runtime reset не выполняется. Входы генерируются из config и сверяются
между режимами по хешам. Общие начальные данные/инъекции не означают
общие наблюдения: каждое ERR получено собственным посещением памяти.

При новом запуске поля host_elapsed/build/environment могут различаться.
Детерминированные traces/check должны совпасть. Профиль ARM-доставки
синтетический; время хоста, инструкции, HDL-время и неизвестное время
платы не взаимозаменяемы. **Q(T) за срок этой командой не доказывается.**

## Результаты этого выхода

- 7/7 unit tests, Python compile: успешно.
- Actual startup→firmware→AXI→vendor XPM/full executor→memory/application:
  adaptive/fixed прошли,149428 E-фронтов каждый.
- 5/5 trace mutations отвергнуты с локатором.
- 244 inherited hashes и9 STA source hashes совпали.
- Свежий full route/плата/WCET: не выполнялись.
- Сценарии1/2/3/5: ещё не исполнены. Не запускать их с сокращёнными
  hold или неполным профилем под видом окончательного пакета.
