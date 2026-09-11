# FINAL DELIVERY — RE-FIXED-ADAPTIVE-FEASIBILITY-01

**Исполнитель:** постоянный Research Engineer в отдельной PI-started session.  
**Execution base:** `59603d231b923ee7426056cb62779a5ad16c8413`.  
**Pre-verification commit:** `e8713d187592c9b810ecf4194b6da7108d898e22`.  
**Branch:** `research/fixed-adaptive-feasibility-01`.  
**Статус:** OWN RESULT; существенные новые научные утверждения требуют отдельного Scientific Review. Новый RES/PASS не присвоен. Практическая ветвь RES-004 не запускалась.

Этот файл является финальным RE delivery/disposition и имеет приоритет над двумя устаревшими числами fallback sensitivity в промежуточных `REPORT.md`/`HANDOFF.md`. Основные Level-I/II результаты этих файлов не изменены.

## Level I

Principal slice: 4 MiB data, SEC-DED (39,32), `H=43824 h`, `epsilon=0.001`, `B_avg=0.25%`, scrub peak `25%/1 s`, conditional write, application load 10% или 50%, burst 8 слов, research deadline 100 us.

**Strong Fixed:** даже при учёте только чтений ресурс требует `tau >= 25.165824 s`; фазонезависимая exactly-two lower bound при этом периоде даёт `F_A >= 0.001571525 > 0.001`. Независимый post-result audit закрывает весь непрерывный resource-compatible класс до 3600 s: `[25.165824,900] s` покрыт exactly-two lower bound, `[900,3600] s` — отдельной Cauchy lower bound. Read-resource boundary, ниже которой Fixed не может удовлетворить риск, равна `0.3950398%`.

**Causal witness:** `r(t)=nu_hat(t)/C`, где `nu_hat` — только завершённое значение предыдущего часа, `C=0.03560929816`. Достаточная risk upper = `0.00095`; при stress с четырёхкратным RMW-слагаемым = `0.000950000728`. Консервативная средняя занятость, резервирующая read+write для каждого посещения, = `0.1424470%`; peak = `24.0458%`; delay bound при 50% application load = `3.005 us`.

Связный separator:

`0.142447% <= B_avg < 0.395040%`.

Контрольный срез `0.25%` лежит внутри него. На отдельном peak-hour срезе Fixed требует лишь около `0.032605%` read resource, поэтому необходимость адаптации на часовом горизонте не установлена; положительный separator относится к пятилетнему накоплению риска без ежечасного reset budget.

## Corrected missing-input fallback

Исторический source summary содержит 148 missing proton hours. Строгая ресурсная верхняя оценка после исправления:

`B_fallback <= B_normal + (148/H) * B_peak = 0.2236533% < 0.25%`.

Соответствующая ёмкость среднего ресурсного запаса — `196.017 h` peak-fallback. Ранее записанные `0.223172%` и `197.19 h` считать superseded только для этой вспомогательной sensitivity. Level-I separator и Level-II disposition от исправления не меняются.

## Level II disposition

1. **Fixed:** доказанно недостаточен в principal domain.
2. **Strong Precomputed:** отдельный допустимый свидетель без future leakage не установлен; статус `INCONCLUSIVE`, не `impossible`.
3. **Simple external delayed-rate + local peak fallback:** минимальный **установленный** причинный full-contract witness в этой постановке.
4. **Counter-only simple:** совместимый 39-bit/five-year/conditional-write сертификат не построен; старые seed sweeps остаются диагностикой и не считаются поражением метода.
5. **RES-003:** принятая область (32 data bits, H=3600 s, epsilon=0.1, known symmetric two-state CTMC) не переносится автоматически. Дополнительная системная польза RES-003 сверх simple external contour здесь не установлена.
6. **RES-004:** practical execution не запускался; основания для возврата практической ветви не получено.

## Stronger ECC boundary

Отдельный аналитический shortened BCH candidate `(44,32,d>=5)`, `t=2`, при principal `B_avg=0.25%` даёт `tau=58.720256 s` и triple-event upper `5.5713e-9`. Это не drop-in claim для документированного 39-bit SRAM: storage +12.82% относительно 39-bit codeword, decoder/timing/WCET не реализованы. Следовательно, необходимость адаптации установлена только условно на фиксированную SEC-DED архитектуру.

## Проверки

- frozen `verify.py`: `78/78 PASS`;
- post-result `independent_check.py`: `13/13 PASS`, не импортирует `analyze.py`;
- pre-verification Git blobs повторно сверены для `ANALYSIS_CONTRACT.md`, `config.json`, `analyze.py`, `verify.py`;
- RES-004 practical execution = false;
- новые Monte Carlo, retuning, GOES/COSRAD rerun, RTL/Vivado не выполнялись.

## Пять прямых ответов

1. **Где Fixed недостаточен?** В principal SEC-DED области выше и в соответствующей связной полосе среднего бюджета; недостаточность доказана нижними границами для всего постоянного класса, а не непрохождением верхней оценки.
2. **Какой минимальный метод достаточен?** Из проверенных и научно допустимых вариантов — simple external one-hour-delayed scalar controller + local peak fallback. Абсолютная минимальность среди всех Precomputed не доказана, поскольку Strong Precomputed остаётся inconclusive.
3. **Что даёт RES-003 сверх simple?** В этой системной постановке дополнительная практическая польза не установлена; для честного сравнения нужен новый научный transfer.
4. **Возвращать ли RES-004?** Нет, оснований нет.
5. **Что обосновано для диссертации?** При фиксированной SEC-DED архитектуре и объявленном информационно-ресурсном контракте существует параметрическая область внешней SRAM, где причинное перераспределение по доступной прошлой информации выполняет совместные ограничения риска и ресурса, а любой постоянный период — нет. Это не универсальная необходимость адаптации по всем ECC/архитектурам.

## Ограничения

`E_cap` не тождествен системному отказу. Operational latency внешнего environmental feed не установлена; one-hour information age является исследовательским conditional contract. Mission-specific `epsilon/H`, реальная workload envelope и controller WCET остаются UNKNOWN. Все существенные новые утверждения перед научным принятием подлежат отдельному Scientific Review.
