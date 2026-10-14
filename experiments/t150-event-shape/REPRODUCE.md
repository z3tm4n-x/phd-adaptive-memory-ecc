# T150 — повтор

Python 3.12.14, NumPy 2.3.5, SciPy 1.18.1, pandas 3.0.1, Windows.
Зависимости совпадают с `../t141-radiation-chain/requirements.txt`.
Полный повтор из корня checkout:

```sh
python -B experiments/t150-event-shape/reproduce.py --raw "/path/to/SEPEM_H_reference.txt" --cache "/path/outside/git/t141-cache" --verify-again
```

Кеш должен быть создан принятым T141 и содержать `manifest.json`,
`bands.npy`, `flux30.npy`. Проверяются raw SHA, fingerprint и SHA массивов.
Если кеша нет, его можно один раз получить штатным `profiles.py` T141,
задав его `--out` во внешний временный каталог; принятые outputs не переписывать.
Ни raw, ни полный кеш в Git не добавляются. Без кеша можно выполнить только
модульные проверки, явно не называя их повтором архивного расчёта:

```sh
python -B -m unittest discover -s experiments/t150-event-shape -p "test_*.py" -v
```

`reproduce.py` проверяет Git-содержимое закреплённых зависимостей, запускает
новые радиационные и контроллерные расчёты в отдельных процессах, затем
тесты и скалярную проверку восьми малых реальных эпизодов. `--verify-again`
повторяет пакет в отдельном каталоге `.cache/` и сравнивает SHA; каталог
удаляется только после проверки его принадлежности этому пакету.
Raw-свёртка при этом не повторяется, используется проверенный кеш.

Основные выходы:

- `shape-transfer.csv` — одинаковые b,p,F, изменяется форма;
- `mission-model.csv` — полные совместные реализации и статистика;
- `event-shapes.csv`, `window-shapes.csv`, `window-all-starts.csv` — архив;
- `square-decomposition.csv` — фон, диагональные и перекрёстные члены;
- `overflow.csv`, `statistics.json` — полный закон упаковки и границы;
- `tail-and-bin-sensitivity.csv`, `segmentation.csv` — условия модели;
- `controller-requirements.csv`, `controller-comparison.csv`, `potentials.csv`
  — достаточные требования, согласованные сравнения и оба потенциала;
- `controller-contract.json` — область/пробелы, без автоматического G_cert;
- `*provenance.json`, `validation.json` — версии, SHA и выполненная проверка.

Битовая повторяемость проверяется в одной закреплённой среде. Иная версия
библиотек/платформа требует численного сопоставления; SHA не объявляется
переносимым между ними. Численная проверка не заменяет научную рецензию.
