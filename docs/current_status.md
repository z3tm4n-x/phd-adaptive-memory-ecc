# Текущее состояние исследования

Обновлено Orchestrator 2026-09-11 по явному поручению пользователя. [DEC-004](decisions/DEC-004-dissertation-architecture-A.md) фиксирует **путь A как основную архитектуру диссертации**. Объект — ECC-защищённая память; центральный вклад — собственные методы адаптивного восстановления при ограничении риска и неполной информации. Поиск нового объекта завершён.

## Текущий приоритет

**Физический мост CY62167 → W/interleaving → direct-границы → ECC outcome → E_cap/F_A.** Нужны проверяемая ограниченная область решений на доступных данных и конкретные сведения, без которых решение меняется или не устанавливается. XY→A уже восстановлено и повторно не исследуется.

Затем — формализация выбора минимально достаточного сертифицированного класса, аппаратное подтверждение и публикационная сборка. [Условия завершения](research_backlog.md). Новая кампания или стенд не запущены. Технический исполнитель — постоянный RE в отдельной сессии через пользователя; Orchestrator не заменяет его внутренним субагентом.

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
