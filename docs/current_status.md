# Текущее состояние исследования

Обновлено Orchestrator 2026-09-15 в ходе исполнения DEC-004. [DEC-004](decisions/DEC-004-dissertation-architecture-A.md) фиксирует **путь A как основную архитектуру диссертации**. Объект — ECC-защищённая память; центральный вклад — собственные методы адаптивного восстановления при ограничении риска и неполной информации. Поиск нового объекта завершён.

**Согласована [единая рабочая концепция](dissertation_concept.md).** Крупная цель —
связать достаточность данных, границы риска, потенциал управления и выбор
обоснованного класса с реальным исполнением. Fixed и simple — полноценные
результаты выбора; архитектуру меняют при доказанной недостаточности
рассматриваемого управления. Практическое следствие для документированной
подсистемы обязательно. Направления усиления — многомерные области применимости
и требования к данным радиационных испытаний; они пока не приняты как новые RES.
RES-003 — основной собственный метод, RES-004 — математическое развитие и граница
применимости. Рабочая [структура — четыре главы](../thesis/README.md).

## Текущий приоритет

**Физический мост CY62167 → W/interleaving → direct-границы → ECC outcome → E_cap/F_A.** Нужны проверяемая ограниченная область решений на доступных данных и конкретные сведения, без которых решение меняется или не устанавливается. XY→A уже восстановлено и повторно не исследуется.

**Локальное исправление conditional write завершено.** Постоянный RE поставил [repair-02 d3cd3e9385f62f047954ce3e54454eb5976ddcb8](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/d3cd3e9385f62f047954ce3e54454eb5976ddcb8/experiments/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02/). Отдельный Reviewer завершил [SR-03 52bb60e5](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/52bb60e516a85f5a0ba10a8b3935285a9c6c25d2/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_03.md): **PASS_WITH_MINOR**, MAJOR SR-02 закрыт для детерминированных окон записи. Две реализации дали 4096/60/0, независимое восстановление состояний совпало на 4105 случаях; различие counterexample JSON только в форматировании.

[Ограниченное принятие Orchestrator](research_gates/CY62167-PHYSICAL-BRIDGE-SR-03-DISPOSITION.md): **LOCAL CLOSED / DETERMINISTIC WINDOWS**. Принимаются enlarged-pair включение `E_CW ⊆ P ∪ B`, достаточная оценка и проверенный конечный исполнитель в области SR §8. MINOR учтён явно: past-known случайная D не разрешает снимать ожидание; допустима доказанная детерминированная потраекторная огибающая. Исходные REPORT/CONTRACT и review не переписаны; расширенное случайное прочтение их формулы не принято. Нового RES и общего PASS физического моста нет. Для этого локального исправления новый RE/SR цикл не требуется.

**Открыт физический вопрос, а не прежний proof/executor MAJOR.** Квалифицированные full-device coverage и задержка, ненулевая физическая D3 lower, полный actual-CY m0/m1 и связь с отказом системы не установлены. Структурный D3/2t+1 и условная coverage-лемма сохраняются в своих областях.

**RE-CY62167-COVERAGE-THRESHOLD-01: численная поставка и отдельный SR завершены; [ограниченное решение Orchestrator](research_gates/CY62167-COVERAGE-THRESHOLD-SR-DISPOSITION-01.md) принято.** Exact published target **a9d9b74b9ac03a4eb20b209eb14552d5b914e21a**, [REPORT](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a9d9b74b9ac03a4eb20b209eb14552d5b914e21a/experiments/RE-CY62167-COVERAGE-THRESHOLD-01/REPORT.md); source delivery **7d6d16c130f44f8d9210199498f326fc9e47b719** сохранён с 11 исходными commits в bundle. Отдельный Reviewer опубликовал [SR-01 d29b95f2](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/d29b95f2b913055cc54cd657b8f3f3d6195a02fc/docs/scientific_reviews/CY62167_COVERAGE_THRESHOLD_REVIEW_01.md): **PASS_WITH_MINOR**, без CRITICAL/MAJOR в ограниченной численной области. Поставка, Review и принятие — разные события; reviewer-пакет не переименован в канонический файл Orchestrator.

После [разрешённого восстановления](research_gates/RE-CY62167-COVERAGE-THRESHOLD-01-INPUT-RECOVERY.md) полный выбранный 288-строчный DREG-срез и оба NPZ находятся в Git. Новый transport имеет собственную воспроизводимую идентичность, исторический SHA не совпал; причина без старых байтов не установлена. Upstream-регрессия не означает тождества upstream/DREG. [Прежний BLOCKED_INPUT и решение восстановления](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/ee174ccd2df1176d73b8f5d05dac55e50ca963d9/docs/current_status.md) — история, не действующий блокер.

На неизменном 24-h / 10-mm / DREG / tau=1-s / epsilon_analysis=0.001 срезе теперь ограниченно принята достаточная upper `U(Delta)=min(1,a_upper+b_upper*Delta)`, `a_upper=0.0003098157772336203819978391463469440873`, `b_upper=2528.1037181797039690725 s^-1`, только в declared registered data-only модели Review §8. При условном нулевом coverage-риске exact `Delta_star` приблизительно 273.0047101324 ns и допускает равенство; при условном `Delta=100 ns` требуется `delta_cov_upper<=0.0004373738509484092210949108536530559127`. При 1 microsecond эта upper не проходит; физическая невозможность не следует.

Reviewer проверил точный GOES ZIP и 59 member hashes, сохранённые transport/contributions, их связь с 288 CSV-строками и exact arithmetic; 171 адресная проверка прошла. Полный raw NetCDF→spectra→selected CSV rerun в SR-среде не выполнен из-за отсутствующего `h5py`, поэтому принят frozen numerical `r`, а не полный независимый raw-input rerun или physical upper intensity. MINOR-01 не блокирует upper: `run_transport.py --validate-only` записывает возраст от исходного `start_unix`, а не длительность validation; старые outputs не переписываются, при следующем использовании wrapper metadata должна быть разведена.

Реальные deterministic WCET и clean/no-pending start, joint physical-transfer coverage upper, внутреннее W/data+parity, parent/registration/split/merge/censoring, E_cap→system outcome и принятие физической Fixed не установлены. [Issue №15](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/15) открыт; новый RES и общий PASS отсутствуют.

**RE-CY62167-EXECUTOR-TIMING-GATE-01: Stage 0 завершён, входной аудит принят Orchestrator.** [Поставка 003c2346](../experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/REPORT.md), parent be6b447e1c2ee7b70e68604fd135b379a800e62f, содержит пять собственных файлов RE. [Disposition](research_gates/CY62167-EXECUTOR-TIMING-STAGE0-DISPOSITION-01.md): **BLOCKED_INPUT / NOT_ESTABLISHED; Stage 1 не начат**. Раздельно не установлены полная задержка, clean start и no-pending start; Delta_upper, lower, comparison и coverage slack равны null. Недостаточность исполнителя не доказана. Сохранены точные bytes/история RE; Orchestrator сопоставил 27 source hashes, четыре manifest payload и ancestry, прочитал ключевой RTL, не запускал аппаратные или исследовательские расчёты.

Следующий проектный вход определяет **Orchestrator**: одна конкретная подсистема/packing (T1) и подготовка/начало памяти (S1), с совместимыми верхними временами и ожиданиями (T2), фиксированными фазами/latch/commit (T3) и завершением предшествующих записей (S2). Старые условные 180 нс и 360 нс не заменяют bound; переменная длина маршрута старого RTL не доказывает фиксированные фазы слов. Повторный аудит тех же материалов и SR входного блокера не назначаются. Stage 1 возобновляется только по конкретным новым входам или явному изменению постановки.

Только после положительного timing gate адресно строится joint coverage contract; затем — формализация выбора наименее сложного сертифицированного класса и аппаратное подтверждение. [Условия завершения](research_backlog.md). Первая статья RES-003 идёт параллельно. Orchestrator исследовательские проверки RE/SR не присваивал себе.

Timing/start gate — предварительная проверка осуществимости конкретного примера,
не следующий фундаментальный результат диссертации. Основной научный пробел —
совместный количественный переход physical parents → registration → W → data+parity
→ E_cap. Действующее численное принятие уже входит в `main` через [PR #25](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/25);
нового disposition по тому же SR не требуется. Это решение по Stage 0 не выдаёт нового поручения на исполнение.

[Подробная история SR-01 → repair → SR-02 → repair-02 → handoff SR-03](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/e8ee2302032afbc7019e0b3fb612b6261c83a095/docs/current_status.md) сохранена вместе с исходными пакетами, failed frozen run, test-fixes и фактическим авторством; её старые текущие статусы больше не являются поручениями.

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
