# CY62167-COVERAGE-THRESHOLD-SR-01

From: Research Orchestrator.
To: **постоянный Scientific Reviewer в отдельной сессии через пользователя**.
Related: Issue №15; DEC-001, DEC-002, DEC-004; RQ-001, RQ-002, RQ-003, RQ-006.
Дата: 2026-09-15.
**Статус: выполнено отдельным Reviewer.** [Review d29b95f2](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/d29b95f2b913055cc54cd657b8f3f3d6195a02fc/docs/scientific_reviews/CY62167_COVERAGE_THRESHOLD_REVIEW_01.md): **PASS_WITH_MINOR**. [Disposition Orchestrator](CY62167-COVERAGE-THRESHOLD-SR-DISPOSITION-01.md): ограниченное численное принятие; physical device NOT_ESTABLISHED; Issue №15 открыт.

## 1. Решение и один вопрос

Численная поставка RE-CY62167-COVERAGE-THRESHOLD-01 получена. Прежний вычислительный BLOCKED_INPUT больше не является текущим состоянием. Научное принятие новых чисел ещё не выполнено.

Проверить, обоснованы ли для неизменного среза восстановленный DREG-вход, достаточная conditional-write огибающая U(Delta) и вычисленная граница delta_cov_upper; какую максимальную формулировку они допускают при неизвестных физическом покрытии и WCET?

Это отдельный Review новых численных утверждений и их связи с принятым локальным основанием SR-03. Полный физический мост заранее не объявляется закрытым. Поиск нового объекта, следующий эксперимент и пересмотр DEC-004 не назначены.

## 2. Exact target, история и канонические входы

**Единственный опубликованный target: a9d9b74b9ac03a4eb20b209eb14552d5b914e21a.**
[Пакет](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/a9d9b74b9ac03a4eb20b209eb14552d5b914e21a/experiments/RE-CY62167-COVERAGE-THRESHOLD-01/) · [REPORT](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a9d9b74b9ac03a4eb20b209eb14552d5b914e21a/experiments/RE-CY62167-COVERAGE-THRESHOLD-01/REPORT.md) · [HANDOFF RE](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a9d9b74b9ac03a4eb20b209eb14552d5b914e21a/experiments/RE-CY62167-COVERAGE-THRESHOLD-01/HANDOFF.md) · [REPRODUCE](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a9d9b74b9ac03a4eb20b209eb14552d5b914e21a/experiments/RE-CY62167-COVERAGE-THRESHOLD-01/REPRODUCE.md).

Ветка research/cy62167-coverage-threshold-01 — навигация; подвижный HEAD не заменяет exact target.

- Исходный local delivery: **7d6d16c130f44f8d9210199498f326fc9e47b719**.
- Исходная постановка: **64a7a1f436b2abd6997d37d14e6ce571e3a480c8**, docs/research_gates/RE-CY62167-COVERAGE-THRESHOLD-01.md.
- Научная база: **408134431d46e8efeae6ebb3223fee91b550c0cf**.
- Разрешённое восстановление: **7971484c4d054f521cc0086e2df6d4d0f63ed7b7**, docs/research_gates/RE-CY62167-COVERAGE-THRESHOLD-01-INPUT-RECOVERY.md; точная копия recovery/ORCHESTRATOR_INPUT_RECOVERY.md.
- REPAIR-02: **d3cd3e9385f62f047954ce3e54454eb5976ddcb8**.
- [SR-03](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/52bb60e516a85f5a0ba10a8b3935285a9c6c25d2/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_03.md): **52bb60e516a85f5a0ba10a8b3935285a9c6c25d2**, PASS_WITH_MINOR. Действующее ограниченное принятие — [SR-03 disposition](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/408134431d46e8efeae6ebb3223fee91b550c0cf/docs/research_gates/CY62167-PHYSICAL-BRIDGE-SR-03-DISPOSITION.md).
- Документальная база этого handoff: main **ee174ccd2df1176d73b8f5d05dac55e50ca963d9**. Это не execution base RE.

Прочитать global rules, свою роль, HANDOFF_CONTRACTS и перечисленные предметные основания. Применяется authority by information type; поздняя навигация не меняет исходные предпосылки.

Published target — отдельный контейнер файлов и **delivery.bundle**, а не переименование исходного SHA. PUBLISHED_DELIVERY.json связывает обе идентичности. Bundle: 1135129 bytes, SHA-256 b0424696e51b0252a2947b7cc348943921cb5f9de5368218bfc5f13a02dcd9d5; prerequisite 64a7a1f…; contained head 7d6d16c…. Он сохраняет исходные 11 commits, включая c8ee76b / fa3a550 / e7a4c727, отозванную подстановку и фактическое авторство.

Локальная предварительная фиксация transport: 037b9c91f939962a4ca5bb363cda485e89c86b20; execution HEAD 63fbe46c10c41dce24477ab43f7916eb93aa448e. Numerical preregistration: 9945f3205f6d13b9b378a4e24b8a1efa2c057e94, дополнительные probes до расчёта a50952c801901341e0af7f45cf3d652dd1167e68; первый rate-run HEAD 38ae8a7bcfbc8ee4b1f4b8fb36daf5b4f899cecd. Проверить эту последовательность и соответствие фактически исполненных blobs. Ретроспективная публикация не является независимой временной аттестацией.

Orchestrator прочитал документы и адресные исходники, сопоставил 54 manifest entries с Git blobs/размерами опубликованного дерева (расхождений нет), подтвердил наличие всего 57 файлов, parent публикации c8ee76b и bundle verify/список 11 commits. Исследовательские команды Orchestrator не запускал. Это приёмка происхождения, не независимая проверка чисел.

## 3. Неизменный контракт и кандидаты на принятие

H=[2026-01-19 04:00 UTC, 2026-01-20 04:00 UTC); 288 блоков по 300 s; 10 mm Al; main_loglog; central_mean; DREG; W32_seq; N_w=2^19, n=32 data bits; Fixed tau=1 s; epsilon_analysis=0.001.

Чистая память, без pending write, детерминированные периодические проверки с фиксированными фазами. Чистое слово не записывается; singleton исправляется через latched clean image. Delta — доказанный детерминированный верхний предел задержки, 0<=Delta<tau, запись завершена до следующей проверки слова. Начальный/конечный неполные интервалы учитываются.

r(t)=nu_C_bit_DREG/2^24 — общий детерминированный per-bit rate; независимые простые NHPP внутри слова, атомарные одиночные toggle и постоянство r на 300-s блоке — предпосылки. W32_seq не является установленным внутренним W. Data-only n=32 не заменяет полное внутреннее (32,38) слово.

RE сообщает:

| Величина | Кандидатный результат |
|---|---|
| I1=integral r dt | 0.00015554758614445987634181976318359375 |
| I2=integral r^2 dt | приблизительно 1.1913844740529997964e-12 s^-1 |
| a_upper | приблизительно 0.000309815777233620382 |
| b_upper | 2528.1037181797039690725 s^-1 |
| U(Delta) | min(1,a_upper+b_upper*Delta) |
| s(Delta) | 0.001-U(Delta), со знаком |
| Delta_star при условном delta_cov=0 | приблизительно 273.0047101324 ns; определяет точная дробь, равенство допустимо |
| При условном Delta=100 ns | delta_cov_upper<=0.0004373738509484092210949108536530559127 |
| При Delta=1 microsecond | отрицательный запас; только непрохождение этой достаточной оценки |

Фактические WCET, qualified coverage upper и принятие физической Fixed — NOT_ESTABLISHED. Это ожидаемая граница задания, сама по себе не дефект исполнения.

## 4. Предмет адресной проверки

1. **Восстановление и область численной идентичности.** Проверить замороженные исходники, нормализацию, сетку 192/depth48/survival128 и использование именно исторического entry point. Новый NPZ имеет собственный SHA 7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e; исторический af35f22e… не воспроизведён побайтно. Проверки и regression не доказывают полного тождества недоступной матрице либо физической верхней интенсивности. Оценить достаточность ограниченного восстановления для заявленного результата, а не требовать недоступной старой byte identity.

2. **Upstream → DREG → per-bit r.** Проверить энергетически зависимое mreg/kbar, включая high bucket и шесть несовпадающих узлов; суммарный upstream не является DREG. Проверить выбранные временные границы, смысл timestamp, 288 блоков и деление на 2^24 ровно один раз. Установить, почему зарегистрированный direct-компонент равен нулю в этой declared W32_seq подмодели; не перенести это на физические родительские события. Выделить общие зависимости двух upstream-путей и checker: сохранённые sigma/GOES/transport/model не становятся независимым физическим подтверждением.

3. **Применение SR-03.** Проверить, что E_CW subset P union B используется в своей области; P не переименовано в точное физическое first-passage. Для pair-части и RMW duty-огибающей проверить начальные/конечные интервалы, фиксированные фазы, целочисленное 300/tau и завершение write. Формулы a=N_w*C(32,2)*tau*I2, b=31*N_w*I1/tau должны следовать из этих условий. Прошлая измеримость случайной задержки не снимает ожидание; допустима только доказанная детерминированная огибающая. Закрытые 4096 трасс и всю SR-03 кампанию автоматически не повторять.

4. **Арифметика и границы.** Независимо получить I1/I2 и a/b из опубликованных decimal rates, проверить outward upper, точную дробь Delta_star и округление вниз, единицы, равенство, Delta=0, b=0, Delta=tau, насыщение и отрицательный остаток. Не заменять отрицательное s нулём. Exact arithmetic относится к объявленному численному r; не заявляет строгую погрешность всех BLAS/libm действий upstream или статистическую квалификацию central_mean.

5. **Физическая сила утверждения.** Для device-transfer нужны отдельное событие V, доказанная связь физического E_cap с моделью вне V и P(V)<=delta_cov_upper<=s(Delta). Вычитание не оценивает P(V). Проверить, охватывает ли формулировка parent/registration/W/data+parity, mixed paths, censoring, абсолютную нормировку и отклонения от вероятностных предпосылок. Отдельно сохранить clean-start, WCET, E_cap vs DUE/SDC/system failure. Ни ненулевой physical direct floor, ни actual-CY opposite-decision pair не заявляются. Upper>epsilon не исключает физическое устройство или все Fixed.

Эти вопросы — предмет проверки, не заранее присвоенные findings. Простой недостаток физических данных не должен превращаться в требование нового облучения внутри данного SR.

## 5. Воспроизведение и независимая попытка опровержения

Работать в отдельной копии exact target; outputs исполнителей могут перезаписываться, поэтому исходные bytes сохранить. Сначала проверить MANIFEST, PUBLISHED_DELIVERY и bundle по REPRODUCE.md; восстановление исходной истории выполнять в другой временной копии, не заменяя review target.

Активны cw_calculate.py, independent_validation.py, input_contract.py, upstream_regression.py и selected_recovery.py. Старые compute_bounds.py / extract_selected_rate.py / independent_check.py — отключённая история отозванной подстановки.

Минимальное воспроизведение чисел из корня reviewer-копии:

```bash
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/cw_calculate.py calculate --input experiments/RE-CY62167-COVERAGE-THRESHOLD-01/selected_rate.csv --output /absolute/reviewer/output/cw_bounds_recheck.json
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/independent_validation.py
```

Каталог выхода создать заранее. Дополнительно построить собственный небольшой checker без импорта RE-calculator/RE-checker: арифметический oracle, знак/равенство границы и адресная проверка окон. Не считать 38 RE checks назначенным SR.

Проверка сохранённого transport без его регенерации:

```bash
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/run_transport.py --radar-root /absolute/path/RADAR --validate-only
```

RADAR HEAD b032505d4d1b15403b8ad06aef578339f6d1c6b4. Для восстановления selected slice из уже сохранённого NPZ — upstream_regression.py и selected_recovery.py с --archive /absolute/path/goes010226.zip --repo . согласно REPRODUCE.md. Exact archive SHA: 7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581; исходный reference proton_rate находится в RE-GOES19-PROTON-RATE-01. Архив имеет внешнее хранение: сначала проверить его доступность, не считать старый scratch path гарантированным входом новой сессии. Если недоступен, явно ограничить воспроизводимый слой сохранёнными NPZ/contributions/CSV и назвать влияние на verdict. Не подменять вход и не запускать полный transport/GOES/risk/MC цикл автоматически.

Зафиксированная RE-среда: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, pandas 2.2.3, pydantic 2.13.5, h5py 3.14.0, pytest 8.4.2, Linux x86_64/glibc 2.39. Совпадение с исторической средой не заявлялось. RE результаты: 21 historical shielding / 13 transport / 38 собственных независимых checks; upstream288 max relative 4.55157e-8 при допуске 1e-6. Повторять только нужные для конкретного нового утверждения проверки. Failed environment/serialization attempts сохранены; различать содержательные расхождения, окружение и сериализацию.

Ключевые Git blobs exact target:

| Артефакт внутри пакета | Git blob |
|---|---|
| MANIFEST.json | 363c651a9d238fe28acb685b32867a540c103ace |
| calculation_config.json | fe1a1510cb8e083bd7aefcf91b1e475f1965bbad |
| selected_rate.csv | f44648d3bdbe7b44f2a03cded74d768d3cebbac4 |
| recovery/outputs/radar_transport.npz | 43348224fa55f8888211fa29da25212177b94108 |
| recovery/outputs/selected_energy_contributions.npz | 9585244d66cbe3e8e4bad390ae8e084a4ab20b95 |
| recovery/outputs/cw_bounds.json | 89d6a7042877f1377c91e02a64f0fd5aaf7419bd |
| recovery/outputs/independent_validation.json | 308934d21ff8bb109322c35c6f1a79c706298691 |

Полный набор размеров/SHA-256 — в MANIFEST, wrapper/bundle — в PUBLISHED_DELIVERY. Проверки не используют старый U_reg как oracle.

## 6. Выход, критерий завершения и публикация

Вернуть verdict PASS / PASS_WITH_MINOR / REVISE / BLOCK **именно для новых численных утверждений**, с областями отдельно для: восстановления/численного r; CW-огибающей/порога; условия физического покрытия; принятия конкретной физической политики.

Для CRITICAL/MAJOR — конкретная демонстрация либо точная проверяемая угроза и минимальное исправление. Для каждого существенного вывода — достаточно / недостаточно / не установлено с указанием, что именно классифицируется. При неизвестности — конкретное отсутствующее сведение, способное изменить решение. Дать максимальную допустимую формулировку и остаточные ограничения; возможность ограниченного принятия не равна закрытию Issue.

Публиковать только собственные отчёт и независимый checker/его необходимые компактные outputs в новой ветке **reviewer/cy62167-coverage-threshold-review-01** от exact target. Отчёт: **docs/scientific_reviews/CY62167_COVERAGE_THRESHOLD_REVIEW_01.md**. Указать target, свои команды/среду/результаты, точный review commit и фактический состав diff. Комментарий передачи в Issue №15 разрешён; Issue оставить открытым. При отличающемся SHA публикации сохранить исходные объекты/авторство и явно описать отношение версий.

Не менять main, RE-пакет, старые SR/манифесты/RES; не присваивать новый RES и не регистрировать научное принятие за Orchestrator. Новая настройка, модель, контроллер, hardware, RES-004, PA/LS цикл и внутреннее замещение постоянной роли не назначены.

После отчёта Orchestrator принимает решение о доступной области результата и конкретном оставшемся физическом звене. Формализация методики следует после этого решения; заранее не запущена.
