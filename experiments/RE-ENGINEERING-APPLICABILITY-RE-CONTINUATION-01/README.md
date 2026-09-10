# Ограниченное продолжение инженерной применимости

Начинать с REPORT.md и HANDOFF.md. Автор входного пакета — Orchestrator;
автор этой поставки — постоянный Research Engineer отдельной сессии PI.

```sh
cd experiments/RE-ENGINEERING-APPLICABILITY-RE-CONTINUATION-01
python run_checks.py
```

Требуется Python 3.10+; внешних библиотек нет. Выходы записываются только в
локальный outputs/. Новых миссий, настройки, повторной обработки старого
ряда и запуска принятых reproduce.py нет. `numerical_checks.py` проверяет
адресные формулы и альтернативные классы; `protocol_checks.py` — новую
абстрактную спецификацию интерфейса и конечные трассы. Это не RTL backend.
`outputs/execution_record.json` содержит реальные версии среды, пути инструментов,
хэши исполняемых файлов и результаты. Служебный delivery manifest хранится
отдельно от исторических манифестов Orchestrator и RES-004.
