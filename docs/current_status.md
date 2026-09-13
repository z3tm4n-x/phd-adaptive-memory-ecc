# Текущее состояние исследования

Обновлено Orchestrator 2026-09-13 в ходе исполнения DEC-004. [DEC-004](decisions/DEC-004-dissertation-architecture-A.md) фиксирует **путь A как основную архитектуру диссертации**. Объект — ECC-защищённая память; центральный вклад — собственные методы адаптивного восстановления при ограничении риска и неполной информации. Поиск нового объекта завершён.

## Текущий приоритет

**Физический мост CY62167 → W/interleaving → direct-границы → ECC outcome → E_cap/F_A.** Нужны проверяемая ограниченная область решений на доступных данных и конкретные сведения, без которых решение меняется или не устанавливается. XY→A уже восстановлено и повторно не исследуется.

**[RE-CY62167-PHYSICAL-BRIDGE-01](research_gates/RE-CY62167-PHYSICAL-BRIDGE-01.md), [Issue №15](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/15): поставка постоянного RE получена.** Exact delivery [0c979c34d537c9f328858010a8df6cdeab598735](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/0c979c34d537c9f328858010a8df6cdeab598735/experiments/RE-CY62167-PHYSICAL-BRIDGE-01/), pre-execution CONTRACT [4bac6ec1](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/4bac6ec1f017f98cd685fee79051dd972b8c8342). Отдельная сессия RE выполнила ограниченный пакет; Orchestrator прочитал документы/код и сверил происхождение, не запускал исследовательские проверки.

Получен [Scientific Review 18b78a647ac299290b5e2399b8af581e14240b88](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/18b78a647ac299290b5e2399b8af581e14240b88/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_01.md): **REVISE; 2 MAJOR, 3 MINOR, CRITICAL нет**. Отдельный Reviewer воспроизвёл оба скрипта с побайтным совпадением JSON и выполнил независимые адресные проверки. Проверяемость байтов не закрыла доказательные разрывы.

[Решение Orchestrator и RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01](research_gates/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01.md): ограниченно приняты структурный D3/2t+1, соответствующее per-model нижнее неравенство и условная coverage-лемма; порог старого среза — только арифметика. Полный m0/m1-свидетель и перенос исторического U_reg на conditional write не приняты. Численная калибровка q3/delta_cov для устройства отсутствует. Общий PASS, новый RES и закрытие Issue №15 не присваиваются.

Получен [repair c48ca29eb65fee96154d645819c4e533a1709037](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/c48ca29eb65fee96154d645819c4e533a1709037/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01/) отдельного постоянного RE. Commit доступен и проверен по файлам; RE-ref `research/cy62167-physical-bridge-repair-01` остаётся на pre-execution b386d8ff после сообщённой RE блокировки fast-forward. Orchestrator эту операцию не повторял и не обходил. Получение repair не зависит от использования старого branch HEAD: точный review target — c48ca29e.

Итог repair c48ca29e ограниченный: сильный actual-CY m0/m1 claim снят; численная upper на прежнем срезе не получена, старый запас снят как физический threshold. [SR-02 57021de7](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/57021de76b45971ca2687e69c4a890f02647df8f/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_02.md) независимо воспроизвёл оба выхода байт-в-байт с `bound=null`. Вердикт **REVISE**, один новый MAJOR и локальные MINOR, CRITICAL нет. Статические set/bitmask fixtures не подтвердили заявленную семантику исполнителя. Missing-rate SHA c10a68e… принадлежит `RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv`; имеющийся upstream proton_rate — другой вход.

[CY62167-PHYSICAL-BRIDGE-SR-02](research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-02.md) **выполнен отдельным постоянным Reviewer**. Его контрпример: same-bit toggle во время отложенной записи, затем новые b/c arrivals дают physical first passage без ideal first passage и без distinct-hit RMW. Ошибочное включение не принимается. Квалифицированный enlarged-pair аргумент SR §§4.2–4.4 принят как ограниченное аналитическое основание с атрибуцией Reviewer; численная/физическая допустимость из него не следует.

[RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02](research_gates/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02.md) **выполнен постоянным RE в отдельной сессии; поставка получена 2026-09-13**: [repair-02 d3cd3e93](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/d3cd3e9385f62f047954ce3e54454eb5976ddcb8/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02/). Ветка `research/cy62167-physical-bridge-repair-02` указывает на d3cd3e93. От ec6b1b3c — 18 линейных commits / 16 добавленных файлов только нового каталога; c48ca29e и чужой SR не входят в ancestry. Orchestrator прочитал пакет, сверил 15 manifest blobs и два test-fix diff, исследовательские команды не запускал.

RE поставил доказательство `E_CW ⊆ P ∪ B`, исполнение SR-контрпримера и две реализации с заявленными 4096/60/0. Неудачный frozen run сохранён; исправлены момент targeted проверки и порядок событий independent checker. Git mirror опубликован ретроспективно; заявленная локальная фиксация до вычислений и её независимая временная проверка различаются. Старое включение остаётся false, физический selected-slice bound — null, full-device/m0/m1 не установлены.

[CY62167-PHYSICAL-BRIDGE-SR-03](research_gates/CY62167-PHYSICAL-BRIDGE-SR-HANDOFF-03.md) подготовлен к передаче отдельному постоянному Reviewer через пользователя, приём не подтверждён. Цель — закрытие локального proof/executor MAJOR и связанных MINOR, включая область RMW при случайной или детерминированной D и сопоставление raw/compact JSON. Отсутствие физического числа исключено из цели repair и само по себе не является его дефектом. Для d3cd3e93 новый научный вердикт ещё не присвоен; прежний REVISE сохраняется для рассмотренного им c48ca29e. Issue №15 открыт: локальный Done/SR не равен завершению моста. Регенерация среды, новый RE/PA/LS пакет, методика и аппаратура автоматически не запускаются.

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
