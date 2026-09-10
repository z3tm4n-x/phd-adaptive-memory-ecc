# RE-INTERNAL-COUNT-UNKNOWN-D-01

Полная исполнявшаяся инженерная поставка по PI-authorized заданию на base
`529709f1b98d12a5f5a2c7b71ee1ff9f53210c97`.

Начинать с `REPORT.md`; математическое основание — `derivation.md`;
условия независимой проверки — `HANDOFF.md`.

## Статус передачи

Расчёты и зафиксированное сравнение завершены. Полный пакет передан архивом
`RE-INTERNAL-COUNT-UNKNOWN-D-01.zip`. Запись полного обновлённого model.py через
GitHub была отклонена шлюзом. Поэтому старый прототип в ветке
`research/internal-count-unknown-d-01` **не является byte-identical исходником
этого исполнения**. Не смешивать его отдельные файлы с данным архивом.
`outputs/execution_record.json` и `outputs/manifest.json` содержат фактические
идентичности исполнявшихся исходников и результатов. Отсутствующий Git commit
исполнявшейся версии не выдумывается.

## Воспроизведение

Из распакованного каталога:

```sh
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python reproduce.py --retune --full --workers 4
```

Без `--full` выполняются резерв, направленная проверка коэффициентов,
непрерывный сертификат Fixed/Precomputed, независимые тесты и трассы.
С `--full` воспроизводится 20000 миссий на каждый из пяти D; без `--retune`
используется сохранённая единая настройка аналога.

Исполнено на Linux x86_64, Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0,
Numba 0.65.1. Построение ожидания использует extended-precision longdouble;
на платформе с другим longdouble направленная проверка может не пройти.
Это проверяемая граница численного контракта, не повод пропускать проверку.
Времена выполнения при воспроизведении измеряются заново и не должны
побайтно совпасть с исходными.

## Состав

- `model.py`: 33 фиксированных закона, бинарный собственный счётчик,
  шесть статистик, тестовое исключение ячеек и перенос отдельных бюджетов.
- `numeric_witness.py`: направленные Decimal-интервалы всех коэффициентов
  и непрерывных ячеек; `feasibility.py`: 12/144 общих baseline-класса.
- `simulate.py`: реальные word/bit инверсии и собственные сканы;
  `small_reference.py`: независимая поглощающая физическая модель.
- `known_reference.py`: раскрытый адаптер known-D RES-003;
  `tests.py`: 17 проверок; `diagnostics.py`: полные трассы и ресурсы.
- `experiment.py`: отдельный пилот, lock исходников, пять held-out запусков,
  marginal/common-survivor/stop статистика без усреднения по D.
- `outputs/`: отчёты, полные bracket-таблицы, тесты, интервальные witnesses,
  исходные и сокращённые трассы, lock и manifest.
- `cache/heldout_*.npz`: полные парные результаты по каждой миссии.
  Шесть политик: learning, frozen, Fixed, Precomputed, PA-DOM, known-D.
  Поля: failure, complete_passes, busy_seconds, reads, writes, stop_time,
  updates, final_cell_mask, first_shrink_time, empty_set_time.

Параметрические точки Монте-Карло не заменяют доказательство континуума.
Малый эталон не заменяет целевой масштаб. Никаких PASS, RES, main merge,
общей оптимальности, physical identification или net-energy результата
эта инженерная поставка самостоятельно не назначает.
