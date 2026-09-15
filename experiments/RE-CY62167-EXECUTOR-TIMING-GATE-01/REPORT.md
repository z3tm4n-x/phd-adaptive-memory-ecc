# RE-CY62167-EXECUTOR-TIMING-GATE-01 — Stage 0

2026-09-15. Постоянный Research Engineer, локальная сессия Codex.
Issue №15. Это входной инженерный аудит, не Scientific Review.

## Решение

**BLOCKED_INPUT / NOT_ESTABLISHED. Stage 1 не начат.**

| Предмет | Вывод |
| --- | --- |
| Детерминированное окно check → confirmed commit | NOT_ESTABLISHED: квалифицированный абсолютный upper отсутствует |
| Точное условие Delta_upper <= Delta_star | NOT_ESTABLISHED; Delta_upper=null, сравнение не выполнено |
| Clean memory всего массива в начале H | NOT_ESTABLISHED |
| Отсутствие pending writes в начале H | NOT_ESTABLISHED, отдельно от clean memory |

Это не «доказана недостаточность исполнителя» и не «доказанный upper выше
порога»: нет ни квалифицированного upper, ни исключающего lower.
Прежние условные 180 нс не становятся доказанным upper; 360 нс кадра не
становятся необходимым lower для pending window.

Рабочая база: `be6b447e1c2ee7b70e68604fd135b379a800e62f`, обычный merge
с родителями `2c714c9e576ae4b48d316d26dde23d61a88f1c64` и
`0d5d0c97481980cf772234c6491a70bd93019b89`.
Документальная база handoff `a8b04eff258401233a1aa038862c71daa4f01072`
является её предком. Научные входы читались по exact commits, не branch heads.

## 1. Один рассматриваемый кандидат и граница источников

Сохранён прежний кандидат **Fixed / полный SEC-DED(39,32) / предложенный
48-bit параллельный порт с 9 padding bits**, без адаптивного банка.
Это только архитектурный кандидат S20–S21, не выбранная физическая плата.
Проверен его старый RTL-задел S22–S27 строго на
`cf7ab706224f7872fdafcf34febda70e3f6c8dd1`. Новый исполнитель не создан.

Идентификаторы S01–S27 раскрыты в `timing_input_gate.json`: repository,
commit, path, Git blob, размер и immutable URL. S10–S12 определяют принятую
область, S17–S19 — отдельные Review. Собственное чтение кода не присваивает
нам их тесты или научное авторство.

**SOURCE:** S20 §1 называет 48-bit порт, 180-нс резерв в 360-нс кадре
спецификацией малого прототипа, не квалифицированным устройством.
S19/S12 принимают только условные инженерные основания. Старый OOC
использует конкретный FPGA, но прямо исключает внешний массив памяти.

**UNKNOWN:** нет закреплённой связи этой спецификации с точными
CY62167 components/платой/backend и operating corner. Не установлены
число chips/доступов на 39-bit слово, data/parity pin/address packing,
одновременность частей слова и полный путь подтверждения записи.
48 логических бит порта не доказывают физической параллельности.
Внутреннее W CY62167 и полный data+parity physical transfer здесь не
восстанавливаются и не подменяются W32_seq.

## 2. Stage-0 таблица входов

| Required fact | Проверенный источник / revision / corner | Тип свидетельства | Использование / незакрытый вход |
| --- | --- | --- | --- |
| Численный порог, tau и область | S14–S17; accepted S10 | SOURCE: условный численный результат | Порог фиксирован; actual delay не является входом этих файлов |
| 2^19 слов ×32 data, полный executor 39 bits | S09, S14, S21 | Модель + архитектурный кандидат | Не физический packing |
| Шина 48 bits, 9 padding | S20 §1, S21; S19 §8 | ASSUMPTION/specification | Нужна привязка каждого разряда к backend/компоненту |
| FPGA, clock, tools/corner | S26: xc7a200tfbg484-2; S27: Vivado 2025.2, routed, speed file -2 PRODUCTION 1.23, Slow/Fast | Исторический core-level timing report | Не выбранная целевая плата и не full-system corner |
| Исторические clock/service числа | S25: 100 MHz и 256 Mbit/s; S26: 100000000 words/s assumption | Сервисные допущения и OOC constraints | Не WCET отдельной RMW; старые 1935832 слова не заменяют 524288 |
| Read/data-valid, setup/hold, turnaround, IO/CDC | S22 интерфейс; S27 check_timing | UNKNOWN upper; 41 input и 187 output ports без delay constraints | Нужны полные corner-qualified max задержки и согласованные минимальные требования |
| 45-нс transfer, 180-нс guard, 360-нс frame | S20–S21; S19 §6, S12 | Условная транзакционная модель; 45-нс datasheet minimum в S09 — не upper | Ни одну величину не подставляем как физический Delta |
| Arbitration/stalls | S19 §6: условные FIFO/4 из 8 slots/token bucket; S22 без ready/ack | Условная сервисная теорема, не binding backend | Нужны список мастеров, максимальное ожидание, stalls/retry/timeout и отсутствие starvation |
| Latch/check instant | S22 decoder.codeword_in(mem_read_data), combinational mem_write_data | SOURCE: код; стабильный полный latch не установлен | Нужны граница выборки и неизменный clean image после singleton |
| Confirmed commit | S22: S_WRITE увеличивает write_count и переходит в S_ADVANCE | SOURCE: локальный state advance, не подтверждение памяти | Нужна семантика конца физической записи, включая все части слова и hold |
| Фиксированные check phases | S17 §4; S22–S23 | Требование модели; старый scan не доказывает его | Нужен полный word schedule, независимый от результатов ECC и stalls |
| Clean start | S14, S18 §3; S20 §3 | ASSUMPTION математической модели | Нужен физический протокол для всего массива в одном t0 |
| No-pending start | S22 reset сбрасывает локальную FSM; S23 стартует при нулевом wait | Локальный reset, не drain backend | Нужны fence/drain completion и условия reset/failed commit |

Это инвентаризация перечисленных exact sources, а не утверждение об отсутствии
любого возможного внешнего документа. Никакой неподтверждённый datasheet
вариант не выбран. Для target-specific чисел сначала нужны точный component
SKU/speed grade/voltage/temperature/load и плата; одно название CY62167 этого
не задаёт. Исторические отчёты прочитаны, Vivado заново не запускался.

## 3. Хронология: что известно и чего не хватает

| Этап полного цикла | Старый witness | Требуемое сопоставление с моделью |
| --- | --- | --- |
| Планирование/арбитраж/read request | S_READ активирует mem_read_en | Максимум ожидания и чтения обязан оставаться в scheduler/inter-check contract |
| Data valid и фиксация полного слова | mem_read_data напрямую идёт в decoder | Возможный c_wk — доказанный момент согласованной выборки полного образа; сейчас не установлен |
| SEC-DED decode/decision | S_DECODE проверяет decoded_corrected | Если выборка уже произошла, все последующие стадии входят в Delta; decode нельзя скрыть переносом c_wk вперёд |
| Conditional write | S_WRITE только при corrected; write data комбинаторная | После singleton нужен сохранённый исправленный образ и безусловное завершение принятой записи; clean check не пишет |
| Physical commit/hold/ack | Нет входа ready/ack; затем S_ADVANCE | Нужен необратимый конец записи всех частей слова; выдача enable и write_count не являются commit |
| Следующее слово/следующая проверка | S_ADVANCE; S23 period scheduler | Фиксированные c_wk=phi_w+k*1s, отсутствие extra checks и commit до следующего check |

При выборе c_wk раньше read/data-valid соответствующие этапы войдут в Delta.
При выборе c_wk на согласованной выборке предыдущие этапы не исчезают:
нужны bounded precheck service и гарантированные фазы. При последовательном
чтении частей слова сначала требуется обоснование единого модельного снимка.
Здесь это не объявляется установленным timeline.

**INFERENCE из S22:** clean и singleton маршруты различаются состоянием
S_WRITE, поэтому время достижения последующих адресов может зависеть от
предыдущих исправлений. S23 компенсирует длительность завершённого прохода
в coarse ticks; это не свидетельство фиксированной фазы каждого слова.
Один max-gap или средняя полоса не закрывают duty-условие S17.
Это адресный входной пробел, не новое общее опровержение прежнего executor.

## 4. Отдельное основание начала

**No pending:** reset_n в S22 обнуляет FSM/счётчики, но не подтверждает,
что внешний backend завершил все принятые записи. Нет переданного сюда
протокола drain/fence, treatment частичной записи, перезапуска и failed commit.

**Clean memory:** reset контроллера не записывает все адреса. Даже завершённый
последовательный initialization/scrub pass не доказывает clean всего массива
в одном t0: ранее очищенные слова имеют ненулевую предысторию экспозиции
до конца прохода. Отсутствие pending само по себе не исключает этих ошибок.
Это логическое следствие последовательной очистки, не оценка её вероятности.

Нужно отдельно обосновать заявленное начальное состояние относительно
экспозиции, всех 524288 слов и соответствующих полных кодовых образов.
Возможное новое основание должно квалифицировать начальную подготовку и
интервал до t0 либо потребовать отдельного Orchestrator решения о другой
предыстории/модели. Здесь не вводятся exposure-free допущение, бесплатный
atomic reset или ненулевое начальное распределение взамен принятого clean start.

## 5. Минимальные decision-changing inputs для Orchestrator

| ID | Что предоставить | Почему меняет решение / критерий продолжения |
| --- | --- | --- |
| T1 | Закреплённый platform/backend binding: board/revision, controller part/clock bounds, CY components/SKU/corner, полный pin/address/data/parity mapping и параллельность транзакций | Определяет состав и последовательную/параллельную композицию пути. После выбора нужны точные полные datasheet/board/constraint источники |
| T2 | Контракт bound каждой транзакции и stalls: max read-valid/IO/CDC, контролируемые cycles, setup/hold/write/turnaround, bounded arbitration/retries; связь observable completion с физическим commit | Определяет конечность и величину Delta. Верхние значения должны позволять сравнить полный путь с exact Delta_star; отсутствие fairness bound не разрешает конечный WCET |
| T3 | Полный Fixed schedule и sampling/commit protocol для 524288 слов: c_wk, phi_w, precheck reservation, latch, singleton-only irrevocable write, clean/no-write, failed commit/reset, commit-before-next-check | Быстрый интерфейс без этих свойств не позволяет применять неизменную численную формулу. Нельзя заменить fixed phases одним max-gap |
| S1 | Процедура подготовки всего массива с подтверждённым clean state в точном t0 и квалифицированной экспозицией ранее подготовленных слов | Clean start влияет на начальные интервалы и принятую upper. Serial pass или reset не являются таким доказательством |
| S2 | Backend drain/fence/start interlock с доказанной полнотой: все ранее принятые/частичные записи завершены, новые до разрешённого старта исключены; reset/ошибка не означают success | Позволяет установить no-pending независимо от clean memory; иначе остаются неучтённые pre-start окна |

Не требуется сначала строить joint coverage, менять контроллер или запускать
стенд. Достаточен конкретный проверяемый контракт с источниками для одного
кандидата. T1–T3 и S1–S2 совместно закрывают Stage 0; ни один произвольный
добавленный timing scalar не закрывает все эти пробелы.

## 6. Неизменная научная область и проверки

Унаследован, не пересчитан порог в секундах:

```text
6901842227663796180021608536530559127 /
25281037181797039690725000000000000000000000
```

Это приблизительно 273.0047101324 нс; равенство допустимо только при условном
нулевом coverage upper. Численный источник — S15, ограниченное принятие S10/S17.
Полная область: H=[2026-01-19 04:00 UTC, 2026-01-20 04:00 UTC), 10 mm Al,
main_loglog/central_mean/DREG/W32_seq, 2^19 ×32 data bits, независимые внутри
слова простые per-bit NHPP с общей ступенчатой 300-секундной r, атомарные
одиночные toggle, clean/no-pending start, фиксированные периодические
проверки tau=1s и singleton-only clean-latch write с доказанным общим
0<=Delta<tau. E_CW, enlarged-pair и pending-window область S18 сохраняется.
Полный 39-bit исполнитель не расширяет численную data-only область на parity.

delta_upper, lower, comparison и coverage slack оставлены null.
Ни U, ни rate slice, ни coverage заново не вычислялись. epsilon_analysis=.001
не проектное требование. По этому блокеру нельзя исключить Fixed, пересмотреть
DEC-004 или диссертацию, присвоить RES/PASS либо закрыть Issue №15.

Проведены source/identity/ancestry и документальные проверки; воспроизводимые
команды и фактические результаты — EXECUTION.md, hashes поставки — MANIFEST.json.
Тесты RTL, синтез, моделирование timing, independent bound checker относятся
к Stage 1 и **NOT_RUN_STAGE0_BLOCKED**, а не PASS.
Пакет передаётся Orchestrator для предоставления входов; отдельный SR только
для подтверждения отсутствующего входа не требуется.
