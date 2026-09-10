# RE-ENGINEERING-APPLICABILITY-01 — continuation 01

2026-09-10. Собственная поставка постоянного Research Engineer из отдельной
пользовательской сессии. Приём handoff подтверждён в этой сессии после чтения.
Автор входного пакета bcc774c1 — Research Orchestrator; его файлы не изменяются.

Начать с [REPORT.md](REPORT.md). Локальные основания — [TRANSFER.md](TRANSFER.md),
обмен и обслуживание — [INTERFACE.md](INTERFACE.md), передача — [HANDOFF.md](HANDOFF.md).
Это адресное инженерное продолжение, не Scientific Review и не новый RES.

В checkout поставленного commit:

```sh
cd experiments/RE-ENGINEERING-APPLICABILITY-01/continuation-01
OPENBLAS_NUM_THREADS=1 python run_checks.py --out /tmp/re-applicability-check
```

Проверяются точные Git blob SHA исходных model.py/config.json из соседнего
RE-INTERNAL-COUNT-UNKNOWN-D-01. Другой путь задаётся `--reference-root`.
Зависимости фактически исполненной среды указаны в outputs/execution.json.
Не запускать reproduce.py прежних экспериментов; новый MC и retuning не нужны.
Исполняемые .py/config и входные два файла идентифицированы до и после проверок.
`outputs/repeat_check.json` подтверждает повтор только этого ограниченного пакета.

`outputs/manifest.json` — манифест данной инженерной поставки, а не старого запуска.
Он исключает собственный файл. SHA финального commit сообщается с поставкой;
его не вставляют внутрь хэшируемого дерева задним числом. Новые outputs — только
проверочные расчёты/трассы. Старые NPZ, результаты RES и пакет Orchestrator не копируются.
