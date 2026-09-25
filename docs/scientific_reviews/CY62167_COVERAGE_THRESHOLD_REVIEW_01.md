# CY62167 Coverage Threshold — Scientific Review 01

Дата: 2026-09-15. Роль: независимый Scientific Reviewer. Задание: CY62167-COVERAGE-THRESHOLD-SR-01; Issue #15; RQ-001/002/003/006, DEC-001/002/004.

## 1. Объект, область и вердикт

**PASS_WITH_MINOR — для новой достаточной численной CW-огибающей и coverage-требования в явно объявленной registered data-only модели. Блокирующих CRITICAL/MAJOR в этой области не обнаружено. Ограниченное принятие научно допустимо. Принятие конкретной физической Fixed остаётся NOT_ESTABLISHED.**

Единственный проверенный опубликованный target и parent review-ветки: **`a9d9b74b9ac03a4eb20b209eb14552d5b914e21a`**, пакет `experiments/RE-CY62167-COVERAGE-THRESHOLD-01/`. Handoff: `99ee43551f06f52f5a4156f4b7b27865a5f45b5f`. Исходный local delivery: `7d6d16c130f44f8d9210199498f326fc9e47b719`, не переименованный SHA публикации.

Рассмотрены GLOBAL, роль SR, HANDOFF_CONTRACTS, постановка `64a7a1f436b2abd6997d37d14e6ce571e3a480c8`, разрешение input recovery `7971484c4d054f521cc0086e2df6d4d0f63ed7b7`, действующий disposition `408134431d46e8efeae6ebb3223fee91b550c0cf` и SR-03 `52bb60e516a85f5a0ba10a8b3935285a9c6c25d2`. Доказательство/executor REPAIR-02 не переоткрывались; 4096 трасс, транспорт, прежние risk/MC grids и новый эксперимент не запускались. Текущий REPORT/HANDOFF/INPUTS и CALCULATION_PREREGISTRATION с явными amendments управляют численным результатом; историческая отозванная upstream=DREG подстановка в CONTRACT не принята заново.

**Предел независимого воспроизведения:** точный GOES ZIP найден и проверен вместе со всеми 59 NetCDF members, однако сырой NetCDF→спектры→selected CSV путь в этой SR-среде не завершён: `upstream_regression.py` остановился на отсутствующем `h5py` до вычислений. Независимо проверены исходники и происхождение восстановления, сохранённые transport/contributions, их связь с 288 CSV-значениями и frozen upstream reference, затем точная арифметика CW. Это не полная независимая регенерация из NetCDF. Verdict допускает принятие **условного результата для опубликованного численного r**, а не утверждения о полном SR end-to-end rerun или физически квалифицированной интенсивности.

| Предмет | Disposition | Что поддержано / что не установлено |
|---|---|---|
| Source-based recovery / численный r | **Достаточно для ограниченного использования frozen numerical input** | Источники, энергетическое преобразование и сохранённые компоненты согласованы; новая собственная идентичность CSV. Полный NetCDF rerun этой SR-сессией не установлен; историческое побайтовое тождество не заявляется. |
| CW upper и нулевой coverage-порог | **Достаточно в §4** | Точная арифметика, применение принятого включения и направленное округление подтверждены. Это не точное F_CW. |
| Условие физического покрытия | **Достаточно как условная теорема/требование** | При отдельном сопряжении вне V и доказанном P(V)≤δ_cov^U≤s перенос достаточен. Вычитание само не оценивает P(V). |
| Существующее физическое обоснование coverage | **Недостаточно** | Нет совместного количественного контракта полного physical-parent/data+parity процесса с этой моделью. |
| Конкретная физическая Fixed | **NOT_ESTABLISHED** | Не установлены coverage upper, executor WCET и требуемые физические предпосылки, включая clean start. Это ожидаемая граница задания, не новый дефект вычисления. |

## 2. Происхождение, предварительная фиксация и восстановление

Все **54 entries MANIFEST** совпали по размеру, SHA-256 и Git blob до исполнения. Все 10 source entries сопоставлены с байтами указанных frozen Git commits; две распакованные Python-копии независимо сверены с zlib/base85 оригиналами. Проверены реальные NPZ, CSV, bundle, а не только записанные в манифесте флаги.

`git bundle verify` прошёл; bundle имеет 1,135,129 bytes и SHA-256 `b0424696e51b0252a2947b7cc348943921cb5f9de5368218bfc5f13a02dcd9d5`. В отдельной reproduction-копии восстановлены исходные 11 commits с prerequisite `64a7a1f…` и head `7d6d16c…`. Diff source delivery→published target добавляет только `PUBLISHED_DELIVERY.json` и `delivery.bundle`: научные файлы побайтно сохранены. Bundle сохраняет исходные родителей/авторство, включая ошибку и её отзыв; review не заменяет эту историю.

Проверенная последовательность: transport lock `037b9c91…` → восстановление CRLF `64d3d7cb…` → запись environment failure / execution HEAD `63fbe46c…` → numerical lock `9945f320…` → дополнительные threshold probes `a50952c8…` → serialization/validate-only repair `38ae8a7b…` → результаты `28b2b8e2…` → source delivery `7d6d16c…`. Между numerical lock и delivery `cw_calculate.py`, `selected_recovery.py`, `upstream_regression.py`, `input_contract.py`, calculation config и scientific historical sources не менялись. Изменения checker добавляют реальные CLI equality/above-threshold проверки; wrapper repair переводит NumPy bool в builtin bool и разрешает проверку уже готового NPZ. Это не перенастройка модели или допусков после результата. Между transport lock и execution HEAD scientific Python sources не менялись; CSV восстановлен в точных historical CRLF bytes.

Git-последовательность согласуется с заявленным исполнением, но **не даёт независимой временной аттестации локальных запусков**. Сохранённые failure JSON и журналы — исторические свидетельства RE, не наши исполнения. Первое падение было на metadata pytest до scientific functions; второе — сериализация qualification после создания матрицы. Неуспешная qualification не выдаётся за успешный rate run.

Новая матрица имеет SHA-256 `7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e`, 296,715 bytes. Historical `af35f22e…` не совпал; старых массивов нет для содержательного сравнения. Это разрешённое **source-based reproduction**, не восстановление старых байтов. Отсутствие старого NPZ не превращено в новый блокер условного результата.

Инспекция pinned historical entry point подтверждает 192 energy points, production depth=48/survival=128, прежние grid/depth gates и RADAR `b032505d4d1b15403b8ad06aef578339f6d1c6b4`. Сохранены прежние compatibility normalizations: R=0 endpoint, обработка повторных координат, MT5 zero-threshold extension, отсутствие nuclear correction выше 200 MeV при CSDA до 390 MeV. Это численная/модельная область, не квалифицированная ошибка физического transport.

`--validate-only` повторно даёт 13 passing checks. Но grid/depth convergence, параметры построения и monoenergetic residuals он **читает из сохранённого validation JSON**. Это не независимый пересчёт сходимости. Собственный SR checker дополнительно обращается непосредственно к NPZ: форма 7×192×192, оси, конечность, неотрицательность и zero-shield residual. Получены primary max abs `2.7755575615628914e-15`, secondary `0`, внутри исходного допуска `1e-14`. Ни структурные проверки, ни совпадение SHA не доказывают физическую корректность матрицы.

## 3. DREG, время и нормировка

Активный selected recovery использует энергетические вклады и **mreg(E)/kbar(E)**; суммарную upstream-колонку не подставляет. Собственный checker извлекает только буквальные upstream MULT_POINTS, независимо строит mreg из целочисленных зарегистрированных counts и выполняет скалярную log-E интерполяцию двух величин по отдельности. Он не импортирует `dreg_grid`, selected recovery или RE checker.

Различия популяций подтверждены на шести узлах **29, 40, 80, 124, 164, 186 MeV**. На 186 MeV отношение равно **4323/4324**, оно же применяется к high bucket. Даже общий знак отклонения нельзя выводить из одного узла: на 29 и 124 MeV отношение больше единицы. Интерполяция самого отношения вместо двух отдельных функций не является frozen алгоритмом. Ни нулевая registered direct-доля, ни равенство accumulation_bits=registered_bitflips не устанавливают mreg=kbar.

Независимая сборка 288 DREG значений из сохранённых energy contributions через скалярный `math.fsum` и заново полученные веса дала max relative difference **`4.39049622815852e-16`** с CSV. Отдельная не взвешенная DREG-весами сборка upstream дала `2.9505678449913086e-16` с сохранённой upstream-колонкой и **`4.551567838617994e-8`** с exact frozen upstream reference, ниже неизменного `1e-6`. Последняя проверка использует сохранённые contributions, **не заново восстановленные из raw flux**. Она подтверждает согласованность сохранённого слоя и reference, не независимость исходной радиационной модели.

Нулевой `r_D_DREG` обоснован только эмпирической классификацией зарегистрированных marks при declared W32_seq плюс явно заданными low/high extensions. Полные physical parent events, split/merge/censoring, истинное внутреннее W и parity этими нулями не квалифицированы. Наличие общего энергетического происхождения также не доказывает независимость bit arrivals: NHPP/атомарные одиночные toggle и пространственная однородность — отдельные ASSUMPTIONS модели.

CSV: **288** строк, SHA-256 **`13daa667dcdf0931a477ba6994f3213b345c582b4d6b472031a9454705a60cf8`**, 44,436 bytes. Проверены точные метаданные и последовательность начал блоков от 2026-01-19 04:00 UTC до 2026-01-20 03:55 UTC, каждое duration=300 s; конец H исключён. По frozen input interpretation timestamp — начало усреднения; применение этой семантики в коде согласовано. Пятиминутное среднее **не доказывает** физическое постоянство интенсивности внутри блока; ступенчатое r — объявленное представление.

Деление на **2^24 ровно один раз** подтверждено точно для каждой строки. `nu` — весь data-bit accumulation stream, r — per-bit s^-1; 2^19 слов ×32 bits=2^24. `central_mean` — среднее E/W, не confidence upper. Инспекция двух frozen upstream путей подтверждает прежние keV→MeV, 4π, sigma, measured/low/high и full-archive gap-median правила; последние не заявлены причинным estimator. Общие GOES, sigma, transport, conventions и floating-point libraries ограничивают независимость RE двух upstream маршрутов.

## 4. Применение SR-03 и точные числа

Используется принятое **E_CW ⊆ P ∪ B**, не ошибочное включение через точное ideal-at-read failure. P означает наличие двух различных arrival labels в inter-check интервале; B — distinct-bit hit во время pending correcting write после singleton.

Для каждого слова реальные начальный, полные и конечный интервалы имеют длину ≤τ. При μ_I=∫_I r и независимых внутри слова простых NHPP вероятность пары ≤μ_I². Cauchy–Schwarz отдельно на каждом интервале даёт Σμ_I²≤τ∫_H r²; union over words/pairs даёт **a=N_w C(32,2)τ I2**. Межсловная независимость не нужна. Разные фиксированные фазы не заменены общей фазой либо квадратурой.

Для B все фактические correcting windows доминируются потенциальными окнами [φ_w+kτ,φ_w+kτ+Δ). Периодически продолженная оконная функция имеет меру Δ на каждый период. На каждом полном постоянном 300-s rate block при τ=1 её взвешенный интеграл равен 300rΔ независимо от фазы. Удаление pre-start windows при clean/no-pending start и обрезание при H только уменьшают exposure. Поэтому **Pr(B)≤31N_w(Δ/τ)I1=bΔ**. Здесь не требуется равномерное распределение фаз, но требуются фиксированный период, целочисленное 300/τ и H из полных rate blocks. Произвольные дополнительные checks или только maximum-gap contract не дают эту duty-формулу.

Δ — детерминированная верхняя граница, **0≤Δ<1 s**, commit до следующей проверки слова. Случайное фактическое время допускается только при доказанном доминировании этими детерминированными окнами. Одной прошлой измеримости или подстановки наблюдённой задержки вместо ожидания недостаточно. При Δ=0 B исчезает как допустимый предельный/мгновенный model executor, не как утверждение о hardware.

Собственный integer-scaled oracle сначала приводит `nu` к общей целочисленной шкале 10^19, суммирует значения и квадраты и лишь затем вводит per-bit и временную нормировки. Он независимо от RE-calculator восстанавливает:

| Величина | Проверенное значение |
|---|---|
| I1, безразмерная | 0.00015554758614445987634181976318359375, точно |
| I2, s^-1 | 1.1913844740529997963976058127… ×10^-12 |
| a_upper | 0.0003098157772336203819978391463469440873 |
| b_upper, s^-1 | 2528.1037181797039690725, точно |

Для I1/I2/a/b проверены exact fractions, enclosure и минимальная внешняя сетка 10^-40. `b` представимо точно; `a_upper` округлено вверх. Exact arithmetic начинается с **объявленных десятичных чисел CSV** и не ограждает ошибку всех предшествующих BLAS/libm операций либо физическую ошибку central_mean.

При ε_analysis=0.001 (не project requirement):

`U(Δ)=min(1,a_upper+b_upper Δ)`, `s(Δ)=0.001−U(Δ)`.

Точная граница достаточного сертификата при условном δ_cov=0:

```text
Δ_star = 6901842227663796180021608536530559127 /
         25281037181797039690725000000000000000000000 seconds
```

Безопасное десятичное округление вниз: **0.0000002730047101324343639986193957750873 s**. Приблизительно **273.004710132434364 ns**; округлённое отображение не заменяет exact fraction. Равенство Δ=Δ_star проходит, s=0 и допустим только нулевой coverage upper. Верхний конец десятичного enclosure уже не проходит — это отдельно проверено через production CLI.

| Условная Δ | U, сокращённо | s, сокращённо | Значение решения |
|---|---:|---:|---|
| 0 | 0.000309815777234 | +0.000690184222766 | Сертификат проходит при coverage≤s |
| 100 ns | 0.000562626149052 | +0.000437373850948 | Сертификат проходит при coverage≤s |
| exact Δ_star | 0.001 | 0 | Равенство проходит только при coverage upper=0 |
| 1 μs | 0.002837919495413 | −0.001837919495413 | Эта достаточная оценка не проходит |
| 0.999 s | 1 | −0.999 | Насыщенная тривиальная upper; сертификат не проходит |

При 100 ns точный допустимый coverage upper: **0.0004373738509484092210949108536530559127**. Отрицательный slack не обрезается. U>ε не является lower-risk доказательством, физической невозможностью или исключением всех Fixed. b=0, равенство, Δ=0, Δ=τ, насыщение и избыточный coverage отдельно проверены; Δ=τ отклоняется даже при нулевой интенсивности, поскольку это вне executor domain.

## 5. Фактически выполненные проверки и независимость

Публикационные bytes оставлены в review checkout; запускавшие перезапись RE команды исполнены в отдельном checkout `coverage-reproduction`. Выходной каталог создан отдельно. SR runtime: **Python 3.12.14 / Clang 22.1.3 / Linux 6.18.44 x86_64 / glibc 2.39; NumPy 2.3.5**, доступные SciPy 1.17.0, pandas 2.2.3, pydantic 2.13.5. RE task-specific h5py 3.14.0/pytest 8.4.2 в этой среде отсутствуют; историческая среда не заявлена идентичной.

Выполненные команды (P=`experiments/RE-CY62167-COVERAGE-THRESHOLD-01`; пути ниже — фактические scratch paths):

```sh
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/cw_calculate.py calculate --input experiments/RE-CY62167-COVERAGE-THRESHOLD-01/selected_rate.csv --output /workspace/scratch/24e1723b7ed9/coverage-recheck-output/cw_bounds_recheck.json
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/independent_validation.py
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/run_transport.py --radar-root /workspace/scratch/24e1723b7ed9/coverage-radar --validate-only
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/upstream_regression.py --archive /workspace/scratch/24e1723b7ed9/coverage-inputs/goes010226.zip --repo .
```

Первые три завершены успешно. `cw_bounds_recheck.json` и `independent_validation.json` **побайтно идентичны** опубликованным; 38 RE checks проходят, но остаются RE QA, а не самостоятельным SR доказательством. Qualification отличается только `elapsed_s`, см. MINOR-01. Четвёртая команда завершилась `ModuleNotFoundError: No module named 'h5py'` до scientific computation. `selected_recovery.py` не запускался после установления того же missing-reader prerequisite. ZIP SHA `7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581` и все 59 member hashes независимо проверены без NetCDF reader; это **не** проверка декодированных flux arrays. Никакой новый transport не выполнялся. 21 historical shielding test и полные transport convergence runs — только сохранённый RE результат, не повторённый SR.

Собственный checker и его компактный JSON опубликованы рядом с отчётом:

```sh
python3 -B docs/scientific_reviews/checks/cy62167_coverage_threshold_review_01.py . --archive /workspace/scratch/24e1723b7ed9/coverage-inputs/goes010226.zip --output docs/scientific_reviews/checks/cy62167_coverage_threshold_review_01.json
```

**171 проверка прошла**, включая provenance entries; это не 171 независимый научный опыт. Checker не импортирует RE-calculator/checker/scientific modules. Помимо integer arithmetic и заново интерполированных weights он вызывает реальный calculator CLI для сравнения решений с собственным oracle, а не только повторяет формулу в локальном тесте. Есть 12 CLI queries и два rejection checks. **48** рациональных window-sweep проверок используют фактические first/last и наиболее rising/falling соседние rates, 3 фазы и 4 Δ. Явно построенные check timestamps, интервальные пересечения и реальные начальные/конечные обрезания сопоставлены с duty bound; отдельно проверена pair inequality. Эти конечные случаи поддерживают реализацию/применение; общность результата даёт аргумент §4, не число тестов.

Два первоначальных сбоя собственного SR checker не являются RE findings: требование точного float-равенства zero-shield identity оказалось сильнее заданного допуска (фактический residual 2.78e-15); чтение всех reference rows встретило пустые rates вне выбранного H. Исправлены только SR проверки: применён исходный допуск 1e-14 и reference ограничен точными выбранными timestamps. RE файлы и научные критерии не менялись.

Общие зависимости остаются: определение модели, frozen counts/sigma, сохранённые energy contributions, NumPy/Python и interpretation timestamps. Независимый finite oracle проверяет алгоритмическую арифметику и связи артефактов; не даёт новых физических наблюдений и не устраняет common-mode upstream model error.

## 6. Findings и минимальные действия

### CRITICAL / MAJOR

**Нет в области ограниченного численного принятия.** Неизвестные физические coverage/WCET — оговорённые условия переноса, а не скрытый дефект, требующий нового облучения внутри данного SR. Полная независимая регенерация сырого входа не заявляется; её отсутствие ограничивает воспроизводимый слой, но не опровергает independently checkable условный результат по frozen r.

### MINOR-01 — `--validate-only` неверно интерпретируемый elapsed time

Доказанный дефект metadata: wrapper читает `start_unix` старого transport run и пишет `elapsed_s=time.time()-start_unix`. В SR запуске поле стало **7204.784690618515** вместо опубликованных **743.044055223465**, хотя transport не запускался. Это возраст старого запуска на момент проверки, не длительность transport или validate-only; остальные JSON поля совпадают.

Минимальное исправление для будущего wrapper/provenance: отдельные timestamps/duration текущей validation stage и неизменяемая длительность исходного transport, либо явное имя/описание elapsed-since-original-start. Closure: validate-only не выдаёт время с исторического старта за stage runtime; scientific arrays/checks не меняются. Старые outputs не переписывать задним числом. Это не основание для нового numerical cycle и не блокер conditional upper.

### Остаточное ограничение воспроизведения, не demonstrated scientific defect

Точный архив доступен, но не выполнен current-session raw NetCDF rerun из-за отсутствующего reader. Чтобы позднее заявить **полное независимое selected-slice reproduction**, достаточно в среде с уже указанным h5py 3.14.0 исполнить два существующих recovery commands в отдельной копии, используя тот же сохранённый NPZ, и сравнить selected CSV и regression. Транспорт или новые входы для этого не нужны. Здесь такое исполнение не аттестуется и не объявляется обязательным новым научным циклом для принятия frozen-input арифметики.

OPTIONAL: переносимый environment lock/recipe вместо одного старого task-specific PYTHONPATH упростит этот повтор. Отсутствие такой упаковки не приравнивается к научной ошибке.

## 7. Физическая сила результата и следующий decision

SOURCE: существующие proton REPORT, distant-MCU REPORT/observation_contract и paper-completion REPORT различают registered clusters и parents, отражают неизвестные pre-clustering chronology/merge, W и parity; они не содержат нужного joint coverage upper. INFERENCE: достаточный device-transfer пока не обоснован. Это не утверждение, что физическое покрытие обязательно плохо или вероятность direct events обязательно положительна.

Нужны явное событие V нарушения связи и включение `E_cap,physical ∩ V^c ⊆ E_CW,model` на общем вероятностном пространстве (либо доказанная достаточная доминирующая связь), с отдельным P(V)≤δ_cov^U. Тогда union bound даёт physical risk≤U+δ_cov^U. V/его обоснование должны охватывать все релевантные неучтённые пути: parent association, полноту регистрации, split/merge/censoring, post-W полный data+parity состав, mixed paths, абсолютную нормировку/отклик и отклонения от вероятностных предпосылок. Произвольный «процент coverage» или отдельная вероятность одного omitted mechanism не заменяют их совместного контракта. Если bound статистически оценён, уровень уверенности и вероятность его нарушения требуют отдельного учёта; измеренного/нормативного 95% обещания здесь нет.

WCET, bus/arbitration/commit semantics, clean-start procedure и завершение до следующей проверки нуждаются в отдельном physical/executor основании. Datasheet minimum write-cycle 45 ns не upper и не WCET. E_cap data-only не равен DUE/SDC либо отказу всей системы. Данные не устанавливают actual-CY opposite-decision pair, physical direct floor, превосходство адаптации или невозможность Fixed. DEC-004/RES-004 не пересматриваются.

**Что можно принять сейчас:** conditional numerical U/s/Δ_star для точного опубликованного r, корректное преобразование сохранённых энергетических компонентов в DREG, и вытекающее требование к coverage при заданном deterministic delay upper. MINOR-01 требует только локального уточнения будущей metadata. **Что не принято:** полностью независимое raw-input recovery в этой SR-сессии, physical upper intensity, actual coverage/WCET и конкретная device policy.

Нет блокера для Orchestrator принять эту ограниченную численную составляющую и решить, какое физическое звено исследовать далее. Для device acceptance конкретно отсутствуют доказанные executor delay/clean-start условия и совместный количественный transfer contract. Один дополнительный замер не объявляется закрытием всех пробелов; ни hardware, ни следующая кампания этим review не назначаются. Issue #15 остаётся открытым; научная регистрация и promotion принадлежат Orchestrator/PI.

## 8. Максимально допустимая формулировка и состав передачи

> Для опубликованного source-based численного среза H=[2026-01-19 04:00 UTC, 2026-01-20 04:00 UTC), 10 mm Al/main_loglog/central_mean/DREG/W32_seq, в declared homogeneous data-only SEC модели с 2^19 словами по 32 bits, независимыми внутри слова простыми per-bit NHPP, атомарными одиночными toggle и ступенчатым 300-s rate, clean/no-pending start и фиксированными периодическими проверками τ=1 s, conditional clean-latch write только после singleton с доказанным общим deterministic delay upper 0≤Δ<τ допускает sufficient bound F_CW≤min(1,a_upper+b_upperΔ), где a_upper=0.0003098157772336203819978391463469440873 и b_upper=2528.1037181797039690725 s^-1. При условном нулевом coverage violation сертификат ε_analysis=0.001 проходит до exact Δ_star≈273.0047101324 ns включительно. При условном Δ=100 ns он оставляет не более 0.0004373738509484092210949108536530559127 на отдельно доказанную вероятность нарушения полного physical-transfer контракта. Это требование к покрытию, не его оценка; конкретный CY62167 physical risk certificate и WCET не установлены. Числа проверены точно относительно объявленного CSV; физическая и полная upstream numerical uncertainty этим округлением не ограждаются.

Ветка передачи: **`reviewer/cy62167-coverage-threshold-review-01`**, один новый report commit непосредственно над `a9d9b74…`. Его exact SHA передаётся в итоговом handoff и определяется Git-объектом, содержащим этот отчёт (самохеш внутрь файла не вставляется). Собственный local source commit с отличающимся SHA не пересоздаётся: единственная публикационная версия создаётся непосредственно как review commit.

Разрешённый diff — только три новых SR файла: этот отчёт, `checks/cy62167_coverage_threshold_review_01.py`, `checks/cy62167_coverage_threshold_review_01.json`. Ни RE-пакет, ни прежние SR, main, decisions, results или manifests не изменены. Новый RES/HYP/CLM, PR, merge, закрытие Issue и canonical acceptance не выполняются.
