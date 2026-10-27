# Повтор инженерного клеточного среза

Python3.12+ stdlib; Matplotlib3.11.2 для научного PNG/SVG. Из корня:

```text
python -B experiments/regime-map-methodology-20261019/epsilon-slice-20261027/cell-service/run.py --check
python -B -m unittest discover -s experiments/regime-map-methodology-20261019/epsilon-slice-20261027/cell-service -p test_cell.py -v
python -B experiments/regime-map-methodology-20261019/epsilon-slice-20261027/cell-service/plot.py
```

`run.py --write` записывает JSON/Markdown. Никаких tune/MC/архива событий;
принимается готовый result PR281, проверяются неизменность входов и
коэффициенты C3 по закреплённому reference-C3.json. Старый A11 не импортируется
и не рассчитывается. Все математические операции — точные Fraction;
десятичные таблицы направленно округлены, float только для графика.

`prepare.py` сохранён как одноразовая регистрация исходников из GitHub-
репозитория; при существующем SOURCES.json отказывается перезаписывать.
Обычный replay не требует `.git`, сети или исторических веток. Достаточно
этой папки и13 текущих путей SOURCES.json, сохраняя структуру репозитория.
Хеши текста нормализуют CRLF→LF; научные inputs и настройки не меняются.

Карта файлов: REPORT — вывод; TABLE — общий срез; CONTRACT — исполнение
и границы переноса; COST — полная цена и параметры; VALIDATION — проверка.
CellSelector — малый эталон управления для проверки соответствия, не новый
аппаратный исполнитель/транспорт и не доказательство физической вероятности.
