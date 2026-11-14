# Воспроизведение одного пилота

Только Python3.12+ stdlib и Git для чтения девяти закреплённых blob.
Исторические PR271/272 не требуется сливать. SOURCE-хеши проверяются перед
расчётом; для обычных текстовых источников нормализуется только CRLF→LF,
а канонический inputs.json дополнительно проверяется byte-for-byte.

Из корня репозитория:

```text
python -B experiments/hybrid-p-r-20261026/single-pilot/run.py --check
python -B -m unittest discover -s experiments/hybrid-p-r-20261026/single-pilot -p test_pilot.py -v
```

Если закреплённые коммиты ещё отсутствуют локально:

```text
git fetch origin theory-hybrid-accumulated-20261026 hybrid-interface-price-20261026
```

Для сохранения нового JSON этой же конфигурации: run.py --write.
У программы нет входа для оптимизации параметров/подбора r. Здоровый канал,
полный префикс и ready вовремя — явные условные fixtures, не аппаратные данные.
Четыре ветви обрабатывают120000 действий каждая, цены вычисляются по8 фазам
календаря; миллиарды проходов по словам не материализуются.

Для повтора в чистом архиве сначала экспортировать закреплённые зависимости:

```text
python -B experiments/hybrid-p-r-20261026/single-pilot/run.py --export-dependencies PATH
```

В чистом снимке той же ревизии указать путь:

```text
python -B experiments/hybrid-p-r-20261026/single-pilot/run.py --historical-root PATH --check
```

Для unit-тестов без .git задать переменную PILOT_HISTORICAL_ROOT=PATH.
Экспорт не меняет закреплённые SHA; несовпадение любого входа останавливает
расчёт. Численная проверка и чистый повтор — [VALIDATION.md](VALIDATION.md).
Вывод и точный остаток — [REPORT.md](REPORT.md); полная цена — [COST.md](COST.md).
