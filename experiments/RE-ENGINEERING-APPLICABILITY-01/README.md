# RE-ENGINEERING-APPLICABILITY-01

Предварительный инженерный анализ по принятому заданию. [REPORT](REPORT.md)
содержит вывод и один рекомендуемый вариант; [DERIVATION](DERIVATION.md) —
адресные основания. Старые методы и результаты не изменяются.

Исходное разрешение/config commit: c9132b1a262eca283fb04ad5877f7c3e611778b2.
`config.json` сохраняет первоначальный кандидат 16-bit порта. Выбранный после
анализа 48-bit вариант и причины выбора отражены в REPORT и outputs/summary.json;
это инженерный выбор среди вариантов, не retuning held-out контроллера.

В checkout основного репозитория и старого repo на
cf7ab706224f7872fdafcf34febda70e3f6c8dd1 выполнить:

```sh
cd experiments/RE-ENGINEERING-APPLICABILITY-01
OPENBLAS_NUM_THREADS=1 python analyze.py --old-repo /absolute/path/chapter4-risk-limited-scrubber
OPENBLAS_NUM_THREADS=1 python verify.py
```

Зависимости: Python 3.12, NumPy, SciPy. Исполненная среда — outputs/summary.json.
Новых миссий, pilot, retune, синтеза или полной симуляции RTL нет. Короткие
проверки исполнителя — явно обозначенные cycle/event модели. Не запускать
reproduce.py принятых экспериментов для этой задачи.

Основные выходы:

- accepted_budget_screen.csv: пределы сохранённого сертификата;
- scan_backup_screen.csv: аналитический выбор временного профиля;
- information_screen.csv: доступное число поступлений и временной масштаб;
- target_conditional_risk.csv / target_precomputed_screen.csv: условная
  предварительная оценка, не откалиброванная физическая гарантия;
- application_service_screen.csv: сервисный контракт и его граница;
- retained_resource_comparison.csv: прежнее согласованное сравнение без новых миссий;
- summary.json / verification.json: источники, результаты и границы проверки.

Первоначальная постановка: docs/research_gates/DISSERTATION-COMPLETION-POSITION-01.md
§6 в основном repo. Доставка не создаёт RES и не меняет состав первой статьи.
