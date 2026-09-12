# Текущее состояние исследования

Обновлено Orchestrator 2026-09-12 в ходе исполнения DEC-004. [DEC-004](decisions/DEC-004-dissertation-architecture-A.md) фиксирует **путь A как основную архитектуру диссертации**. Объект — ECC-защищённая память; центральный вклад — собственные методы адаптивного восстановления при ограничении риска и неполной информации. Поиск нового объекта завершён.

## Текущий приоритет

**Физический мост CY62167 → W/interleaving → direct-границы → ECC outcome → E_cap/F_A.** Нужны проверяемая ограниченная область решений на доступных данных и конкретные сведения, без которых решение меняется или не устанавливается. XY→A уже восстановлено и повторно не исследуется.

**[RE-CY62167-PHYSICAL-BRIDGE-01](research_gates/RE-CY62167-PHYSICAL-BRIDGE-01.md), [Issue №15](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/15): поставка постоянного RE получена.** Exact delivery [0c979c34d537c9f328858010a8df6cdeab598735](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/0c979c34d537c9f328858010a8df6cdeab598735/experiments/RE-CY62167-PHYSICAL-BRIDGE-01/), pre-execution CONTRACT [4bac6ec1](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/4bac6ec1f017f98cd685fee79051dd972b8c8342). Отдельная сессия RE выполнила ограниченный пакет; Orchestrator прочитал документы/код и сверил происхождение, не запускал исследовательские проверки.

Получен [Scientific Review 18b78a647ac299290b5e2399b8af581e14240b88](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/18b78a647ac299290b5e2399b8af581e14240b88/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_01.md): **REVISE; 2 MAJOR, 3 MINOR, CRITICAL нет**. Отдельный Reviewer воспроизвёл оба скрипта с побайтным совпадением JSON и выполнил независимые адресные проверки. Проверяемость байтов не закрыла доказательные разрывы.

[Решение Orchestrator и RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01](research_gates/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01.md): ограниченно приняты структурный D3/2t+1, соответствующее per-model нижнее неравенство и условная coverage-лемма; порог старого среза — только арифметика. Полный m0/m1-свидетель и перенос исторического U_reg на conditional write не приняты. Численная калибровка q3/delta_cov для устройства отсутствует. Общий PASS, новый RES и закрытие Issue №15 не присваиваются.

Получен [repair c48ca29eb65fee96154d645819c4e533a1709037](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/c48ca29eb65fee96154d645819c4e533a1709037/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01/) отдельного постоянного RE. Commit доступен и проверен по файлам; RE-ref `research/cy62167-physical-bridge-repair-01` остаётся на pre-execution b386d8ff после сообщённой RE блокировки fast-forward. Orchestrator эту операцию не повторял и не обходил. Получение repair не зависит от использования старого branch HEAD: точный review target — c48ca29e.

Итог repair ограниченный: сильный actual-CY m0/m1 claim снят; численная upper на прежнем срезе не получена, старый запас снят как физический threshold. Предложены новая pair/RMW-оценка и set/bitmask проверки; их научная достаточность ещё не принята. Missing-rate описание содержит ошибку имени: SHA c10a68e… принадлежит `RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv`, а существующий `RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv` — другой вход. Численное восстановление Orchestrator не выполнял.

[CY62167-PHYSICAL-BRIDGE-SR-02](research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-02.md) подготовлен к передаче отдельному постоянному Reviewer через пользователя; приём не подтверждён. Он различает снятие завышенных claims, доказательство новых локальных границ и достижение исходной цели. Issue №15 открыт; общий REVISE и незавершённость моста сохраняются. Новый RE/LS/PA цикл, регенерация среды и контроллер не назначены.

После отдельного SR и решения Orchestrator по ограниченному завершению моста — формализация выбора наименее сложного из рассматриваемых классов управления, для которого получен достаточный сертификат выполнения требований, аппаратное подтверждение и публикационная сборка. [Условия завершения](research_backlog.md). Новая кампания или стенд не запущены. Технический исполнитель — постоянный RE в отдельной сессии через пользователя; Orchestrator не заменяет его внутренним субагентом.

## Принятое ядро и завершённые этапы

RES-001…004 — **ACCEPTED / PERMANENT** в областях [карточек и SR](../results/README.md). Их этапы завершены. Четыре итоговых положения: информационная достаточность/мост; внешний метод; собственные наблюдения с RES-004 как развитием; методика выбора. Завершённость всех положений не объявляется.

RES-002: 600 с, один пересмотр, Q — достаточная оценка. RES-003/004: data-only SEC / CTMC / 3600 с / epsilon=0.1 и арифметический контракт. Перенос на полный код, conditional write, задержки и иной вычислитель не автоматический.

RE-ENGINEERING-APPLICABILITY-01: **LOCAL CLOSED** в области [SR и Endpoint-поправки](research_gates/ENGINEERING-APPLICABILITY-SR-DISPOSITION-01.md). Пакет bcc774c1 принадлежит Orchestrator, выбранное продолжение 8229668e — постоянному RE. Изменённый банк/полное устройство/WCET не приняты.

RE-FIXED-ADAPTIVE-FEASIBILITY-01: исполнение 80737bdc → repair 03e6c4ad → [SR 619492db](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/619492db33cb8793710fb4e454616f543993c982) → [disposition a88d6a26](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a88d6a26c54c193e3d518fb16f43ffd19511202b/experiments/RE-FIXED-ADAPTIVE-FEASIBILITY-01/SCIENTIFIC_REVIEW_DISPOSITION.md). Общая поставка **REVISE**; выбранный principal **LIMITED ACCEPTANCE — COLD START ONLY**. Этап завершён в этой области; warm start не принят.

Ограниченный principal: 4 MiB / SEC-DED(39,32) / 43824 h / epsilon=0.001 / B_avg=0.25%; clean memory, первый час peak fallback и до 148 дополнительных fallback-часов. F_A<0.000951, occupancy<0.224203% до вычислителя, peak<25%, delay<3.006 мкс при заданной 50%-ной нагрузке. Fixed исключён в объявленном непрерывном классе; простой внешний causal-свидетель достаточен условно на ретроспективно перенесённую форму. Нового RES и установленной пользы RES-003 сверх simple нет.

## Альтернативы

**FPGA — сохранённая альтернатива смены предмета.** [PA 4c65d946](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/4c65d946ca043b6383c2a70d4c09865bec44c550/docs/evidence_synthesis/DRAFT-PA-FPGA-OBJECT-SELECTION-01.md) и [prefeasibility 08e7838e](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/08e7838eeb15f117774fa1b838c1d4264dd13d36/experiments/RE-FPGA-PROTECTION-PREFEASIBILITY-01/REPORT.md) сохранены. Резервирование AES при постоянном SEM — управление вычислительными копиями.

[Статическое уточнение b45f7710](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/b45f77106d79f12ebc7b0ba1c642659a7e4a2e27/docs/research_gates/RE-FPGA-STATIC-EXECUTOR-CHECK-01.md) подготовлено; подтверждения приёма/поставки здесь нет. При уже принятом отдельным RE поручении допускается завершить только записку. Она не блокирует A и не разрешает стенд. Новый поиск NAND/DRAM/FPGA и практическая ветвь RES-004 остановлены.

## Публикация и ограничения

Первая статья RES-003 продолжается в [согласованном составе](publication_plans/RES-003-PUBLICATION-HANDOFF.md). Будущая новая выборка RES-004 не восстанавливает историческую независимость прежней и не возобновляет разработку.

Для CY62167 [семантический SR](scientific_reviews/CY62167_SEMANTICS_REPAIR_REVIEW_02.md) принял верхнее сопряжение; физический direct-floor и старый синтетический вероятностный bracket не восстановлены. ERR consumer MINOR не закрыт U-ветвью. E_cap, DUE/SDC и отказ системы различаются; состояние/бюджет не обнуляются каждый час.

[Критерии пересмотра A](decisions/DEC-004-dissertation-architecture-A.md): невозможное положение, незамыкаемый мост, описательная методика либо явно более сильный самостоятельный FPGA-результат. Ни одно основание сейчас не установлено.

[Сводка до решения](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/59603d231b923ee7426056cb62779a5ad16c8413/docs/current_status.md) и [карта истории](research_map.md) сохраняют прежние этапы; их старые ACTIVE/UNTESTED не являются поручениями.
