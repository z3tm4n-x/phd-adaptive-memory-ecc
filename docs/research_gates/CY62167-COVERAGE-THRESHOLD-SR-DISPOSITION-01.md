# Orchestrator disposition — CY62167 coverage threshold, SR-01

Дата: 2026-09-15. Автор: Research Orchestrator.

Основание: Issue №15; DEC-001, DEC-002, DEC-004; RQ-001, RQ-002,
RQ-003, RQ-006; поставка постоянного Research Engineer и завершённый
Scientific Review отдельной роли.

Статус: **LIMITED NUMERICAL ACCEPTANCE / NUMERICAL SUBGATE CLOSED /
PHYSICAL DEVICE NOT_ESTABLISHED / ISSUE OPEN**.

Вердикт Reviewer сохраняется **PASS_WITH_MINOR**; он не переименован в PASS.
Новый RES, общий PASS физического моста и принятие конкретной Fixed не
присваиваются.

## 1. Проверенные идентичности и решение

- Reviewed published target:
  **a9d9b74b9ac03a4eb20b209eb14552d5b914e21a**,
  `experiments/RE-CY62167-COVERAGE-THRESHOLD-01/`.
- Source delivery постоянного RE:
  **7d6d16c130f44f8d9210199498f326fc9e47b719**; его 11 commits,
  родители и авторство сохранены в опубликованном `delivery.bundle`.
- Orchestrator handoff на SR:
  **99ee43551f06f52f5a4156f4b7b27865a5f45b5f**.
- Scientific Review:
  **d29b95f2b913055cc54cd657b8f3f3d6195a02fc**,
  [CY62167_COVERAGE_THRESHOLD_REVIEW_01.md](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/d29b95f2b913055cc54cd657b8f3f3d6195a02fc/docs/scientific_reviews/CY62167_COVERAGE_THRESHOLD_REVIEW_01.md).

Orchestrator принимает ровно ограниченный численный результат и максимальную
формулировку Review §8 с условиями ниже. Reviewer независимо проверил
происхождение опубликованных файлов, связь сохранённых energy contributions с
288 значениями DREG, применение локально принятого включения SR-03 и точную
арифметику. Orchestrator прочитал отчёт и принимает его disposition; численные
команды Reviewer или RE в этой сессии не повторялись и их авторство
Orchestrator не присваивается.

Публикация RE, Review и это решение остаются разными событиями. Пакет
Reviewer не импортируется в каноническое дерево как собственный файл
Orchestrator: действующее состояние ссылается на его точный неизменяемый
commit. Исходные RE/SR-пакеты, манифесты и результаты не переписываются.

## 2. Что принято

Для опубликованного source-based численного среза
`H=[2026-01-19 04:00 UTC, 2026-01-20 04:00 UTC)`, 10 mm Al,
`main_loglog`, `central_mean`, DREG, W32_seq, в объявленной registered
data-only SEC-модели с `2^19` словами по 32 data bits, независимыми внутри
слова простыми per-bit NHPP, атомарными одиночными toggle, ступенчатым
300-секундным rate, clean/no-pending start и фиксированными периодическими
проверками `tau=1 s`, принимается достаточная оценка

`F_CW <= U(Delta) = min(1, a_upper + b_upper*Delta)`, где

- `a_upper = 0.0003098157772336203819978391463469440873`;
- `b_upper = 2528.1037181797039690725 s^-1`;
- `0 <= Delta < tau` — **доказанная общая детерминированная верхняя
  задержка**, а не наблюдённое среднее или datasheet minimum.

При `epsilon_analysis=0.001` — исследовательской линии, не проектном
требовании — условный нулевой coverage-риск допускает точную границу

```text
Delta_star = 6901842227663796180021608536530559127 /
             25281037181797039690725000000000000000000000 seconds.
```

Безопасное десятичное округление вниз:
`0.0000002730047101324343639986193957750873 s`, то есть приблизительно
`273.004710132434364 ns`. Равенство проходит только при нулевой upper
вероятности нарушения coverage. При условном `Delta=100 ns` остаётся не более
`0.0004373738509484092210949108536530559127` на отдельно доказанную
вероятность нарушения полного physical-transfer контракта. При `Delta=1 us`
эта достаточная upper не проходит; физическая невозможность или исключение
всех Fixed из этого не следует.

`U` — достаточная upper в объявленной модели, не точное `F_CW`. Exact
arithmetic начинается с опубликованных десятичных значений CSV; она не
ограждает upstream floating-point, статистическую и физическую неопределённость
`central_mean`.

## 3. Область source-based recovery

Принимается использование frozen numerical input с собственной новой
идентичностью: 288 строк, 300-секундные блоки, DREG через раздельные
`mreg(E)`/`kbar(E)` и нормировка per-bit делением на `2^24` ровно один раз.
Историческое побайтовое тождество transport не принимается: новый NPZ имеет
SHA-256 `7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e`,
а старый `af35f22e...` не воспроизведён.

Reviewer проверил точный GOES ZIP и hashes всех 59 members, но сырой
NetCDF → spectra → selected CSV rerun в его среде не завершился из-за
отсутствующего `h5py`. Поэтому принятое основание — опубликованный численный
`r` и проверенные сохранённые промежуточные слои, а не полный независимый
raw-input rerun и не физически квалифицированная upper intensity.

Отдельный повтор с `h5py 3.14.0` допустим, если позднее понадобится заявить
полную независимую регенерацию selected slice. Он не является условием
текущего ограниченного принятия и сам по себе не закроет physical transfer.

## 4. MINOR-01

Статус: **ACCEPTED AS NON-BLOCKING / SEMANTICS FIXED FOR CANONICAL USE /
CODE CHANGE DEFERRED UNTIL WRAPPER REUSE**.

Поле `elapsed_s`, записываемое существующим `run_transport.py --validate-only`,
равно времени от исторического `start_unix` до текущей проверки. Оно не
является ни длительностью исходного transport, ни длительностью validation
stage и не используется как такое в принятом результате.

Старые outputs не переписываются. При любом будущем повторном использовании
wrapper обязательны отдельные timestamps/duration текущей validation stage и
неизменяемая длительность исходного transport либо явное переименование в
`elapsed_since_original_start_s`. До такого изменения новое значение
`elapsed_s` нельзя использовать как временное свидетельство. MINOR не требует
нового численного цикла и не блокирует принятую upper, но его реализационное
условие считается закрытым только при следующем изменении wrapper.

## 5. Что не принято

Не установлены:

- событие нарушения transfer `V`, включение
  `E_cap,physical ∩ V^c ⊆ E_CW,model` на общем вероятностном
  пространстве и совместная upper `Pr(V) <= delta_cov_upper`;
- parent association, полнота регистрации, split/merge/censoring, истинное
  внутреннее W, data+parity и mixed paths, абсолютная нормировка/отклик и
  отклонения от объявленных вероятностных предпосылок как единый coverage
  контракт;
- физическая upper intensity, ненулевой direct floor, actual-CY пара
  противоположных решений и связь `E_cap` с DUE/SDC/отказом системы;
- детерминированный WCET всей read/latch/decode/conditional-write/commit цепи,
  bus/arbitration semantics, завершение до следующей проверки и процедура
  clean/no-pending start;
- конкретная физическая Fixed, преимущество адаптации, полный CY62167 bridge
  и готовность диссертации.

Произвольный процент coverage, вероятность одного omitted mechanism,
datasheet `tWC >= 45 ns`, OOC timing ядра или среднее host/CPU time не заменяют
эти основания.

## 6. Decision policy и следующий gate

**KNOWN:** численная достаточная область теперь проверена; при
`Delta > Delta_star` именно эта upper не проходит даже при нулевом coverage
риске. Старый `cf7ab706` содержит полезный 39-битный RTL-задел и OOC timing,
но внешний memory subsystem не входит в OOC, а действующее инженерное
основание требует latch, подтверждённого write и явного start-контракта.

**ASSUMED:** для следующего gate не предполагаются конкретная частота,
арбитраж, верхние времена CY62167 или чистое состояние памяти; они должны быть
входами либо явно остаться UNKNOWN.

**UNKNOWN:** существует ли для одного конкретного минимального Fixed executor
полный детерминированный путь с `Delta <= Delta_star` и обоснованный
clean/no-pending start. Даже положительный ответ не даст coverage upper.

Рассмотрены альтернативы:

1. принять physical Fixed сейчас — отклонено из-за отсутствующих timing и
   transfer оснований;
2. отвергнуть численный результат из-за неполного raw rerun — отклонено как
   несоответствующее проверенной frozen-input области;
3. сначала строить joint coverage upper — отложено: при недопустимой Delta
   такой дорогой этап не сможет спасти текущий достаточный сертификат;
4. сначала проверить точный executor timing/start contract — выбрано как
   наиболее ранний decision-changing gate.

Подготовлен
[RE-CY62167-EXECUTOR-TIMING-GATE-01](RE-CY62167-EXECUTOR-TIMING-GATE-01.md).
Он должен раздельно классифицировать timing и start: **SUFFICIENT FOR THIS
TIMING GATE**, если полный детерминированный bound/start доказан и проходит
численную границу; **CANDIDATE NOT CERTIFIED BY THIS UPPER**, если доказанный
upper выше порога без исключающего lower; **INSUFFICIENT FOR THIS EXECUTOR**
только при доказанном необходимом lower либо невозможном обязательном
контракте; **NOT_ESTABLISHED / BLOCKED_INPUT**, если нет точного
backend/platform timing контракта, с перечислением минимальных входов,
способных изменить решение. Handoff подготовлен, но исполнение Research
Engineer этим disposition не объявляется начатым.

После положительного timing gate следующий самостоятельный предмет — joint
physical-transfer coverage upper. При отрицательном результате пересматривается
не DEC-004 автоматически, а выбранный physical executor/достаточная upper.
При неизвестности сначала предоставляется конкретный backend/platform
контракт; общий новый data или hardware sweep не запускается.

DEC-004 и области RES-001…004 сохраняются. Issue №15 остаётся открытым.
Решение пересматривается при новом accepted SR, доказанном executor bound,
совместном coverage контракте либо выполнении критерия пересмотра пути A из
DEC-004.
