# RE-FPGA-PROTECTION-PREFEASIBILITY-01 — предпроектная оценка FPGA-направления

**Research Engineer.** Instruction base `59603d231b923ee7426056cb62779a5ad16c8413`; основной вход `4c65d946ca043b6383c2a70d4c09865bec44c550`, `docs/evidence_synthesis/DRAFT-PA-FPGA-OBJECT-SELECTION-01.md`. Это инженерная проверка возможности исследования: без разработки контроллера, инъекционной кампании, нового расчётного эксперимента и без возобновления RES-004.

## Решение

**Есть основание для ограниченного последующего эксперимента.** Основная платформа — **AMD ZCU102 / XCZU9EG**; запасная — **ZCU104 / XCZU7EV**. Предмет эксперимента — не период SEM, а переключение между продуктивным и защищённым вычислительными режимами при **постоянном SEM**.

ZCU102 выбран потому, что AMD отдельно аппаратно проверила на нём SEM integration (XAPP1298/XAPP1303) и DFX/PCAP flow (XAPP1361). Текущий PG187 v3.1 поддерживает SEM+Partial Reconfiguration на UltraScale+. ZCU104 сохраняет ту же архитектуру PS+PL/PCAP, но прямой SEM reference design здесь относится к ZCU102, поэтому ZCU104 потребует retargeting check.

**Фактически доступно сейчас:** GitHub, документация и текущая вычислительная среда. Не обнаружены `vivado`, `vitis`, `xsct`, `xsim`, `hw_server`, `iverilog`, `verilator`, `yosys`, `openocd`; не видны `/dev/ttyUSB*`/`ttyACM*`. Наличие физической ZCU102/ZCU104 у пользователя/организации — **UNKNOWN**. Следовательно, архитектурное основание есть, но запуск требует отдельного logistical gate: плата + совместимая Vivado/Vitis + SEM/DFX license.

## 1. Экспериментальная основа

**SOURCE.** PG187 v3.1 (2026-07-22) задаёт SEM для UltraScale/UltraScale+. Для Zynq UltraScale+ SEM нужен ICAP, а PS после boot владеет configuration logic через PCAP; владение необходимо явно передавать. SEM и PR совместимы на UltraScale+.

**SOURCE.** XAPP1298 v1.1 (2018-11-29) — hardware-verified SEM integration на ZCU102/ZU9EG. XAPP1361 v1.2 (2024-05-23) — hardware-verified IDF+DFX на ZCU102, с C/Tcl/HDL/Verilog исходниками; partial bitstreams хранятся в PS DDR и загружаются Cortex-A53 через PCAP. XAPP1361 проверена AMD на Vivado/Vitis 2021.1–2022.1; это не гарантия безусловной совместимости с любой более новой версией.

**SOURCE.** UG1137 2026.1 поддерживает runtime full/partial bitstream loading и configuration readback на Zynq UltraScale+.

**UNKNOWN.** Реальные PCAP/readback bandwidth, лицензия, build compatibility и аппаратная доступность должны быть подтверждены при bring-up; это не оценивается по паспортной частоте ICAP.

## 2. Нагрузка и одинаковый входной поток

Предлагается лабораторная нагрузка **трёх независимых очередей пакетной AES-256 обработки**, основанная на криптографической нагрузке Gantel и выбранная ради однозначного replay состояния.

- `P` — приоритетная очередь;
- `B1`, `B2` — фоновые полезные очереди;
- каждый пакет имеет sequence ID и хранится в PS DDR до подтверждённого commit результата.

**Productive RM:** три AES-256 линии параллельно обслуживают `P`, `B1`, `B2`.

**Protected RM:** три реплики обслуживают только `P`, результат проходит voter; `B1/B2` остаются в тех же очередях и временно не обслуживаются.

Входной task trace во всех режимах один и тот же. Полезная работа — только корректно committed пакет. Такое определение не позволяет получить «выигрыш» за счёт удаления фоновых задач из нагрузки.

## 3. Два режима и переход

Статическая часть ZCU102: PS+DDR queues/commit log, постоянный SEM, DFX/PCAP manager, RP decoupling/reset, SEM monitor/status collector, voter/watchdog и хранилище двух заранее подготовленных partial bitstreams.

Reconfigurable partition содержит только `RM-PROD` и `RM-PROT`.

Переход:

1. прекратить admission новых операций в RP и сохранить последний committed sequence ID;
2. по возможности дойти до packet boundary; иначе текущий пакет объявить uncommitted;
3. decouple/reset RP; все входы остаются в DDR;
4. остановить SEM scanning / передать configuration engine PS/PCAP;
5. загрузить выбранный partial bitstream;
6. выполнить **intended-image verification** readback'ом нужных RP frames против golden frame data/RBD с mask;
7. вернуть доступ SEM и выполнить требуемую re-initialization/golden-ECC/CRC recalculation после PR; дождаться healthy state;
8. release RM и replay последнего uncommitted `P`; фоновые очереди продолжаются только в Productive.

**INFERENCE.** SEM correction восстанавливает configuration memory, но не application state. В предлагаемом эксперименте состояние восстанавливается packet reset + replay + commit watermark. Незавершённая работа не засчитывается.

## 4. SEM/PR/readback: что документировано

Для выбранного семейства применяется **PG187**, не PG036 7-series.

- **PCAP/ICAP.** На Zynq UltraScale+ PS/PCAP и PL/ICAP конкурируют за configuration logic. Нужна явная передача владения.
- **Arbitration.** PG187: безопасная передача ICAP от SEM и обратно может вызвать reboot/re-initialization. Manual Idle→foreign access→Observation без re-init допустим только если configuration memory не изменялась; для DFX это условие не выполняется.
- **После PR.** UG570/XAPP1261: SEM должен пересчитать golden frame ECC/device CRC до Observation.
- **Проверка образа.** UG570 задаёт readback comparison с original frame data или RBD с MSK/MSD. SEM reset сам по себе не подтверждает, что загружен именно ожидаемый RM: без внешнего сравнения текущее содержимое просто становится новой golden basis.
- **Компонентные времена.** PG187 указывает для XCZU9 при ICAP Fmax максимум boot 127 ms + initialization 71 ms. Это не WCET всего перехода. Аналогично опубликованные correction/classification latencies для других UltraScale+ устройств — только ориентиры компонентов.
- **Наблюдение.** Monitor throttling увеличивает mitigation latency; logging path не должен создавать backpressure.
- **Hardware requirement.** PG187 прямо указывает, что поведение SEM не наблюдается полноценно в обычной simulation: оценка SEM требует hardware.
- **Граница применимости.** AMD отдельно отмечает, что SEM IP не разрабатывался/не тестировался специально для space-radiation environments; лабораторный результат нельзя превращать в космическую квалификацию IP.

## 5. Границы защиты

- **RM configuration:** constant SEM; Protected дополнительно использует TMR `P`.
- **Application state:** не считается восстановленным SEM; хранится/replay через PS DDR и commit log.
- **Observer:** SEM status/Monitor/heartbeat контролируются PS supervisor; сам SEM имеет ненулевую вероятность отказа, поэтому его health также наблюдается.
- **PS supervisor:** в первом эксперименте — trusted experiment infrastructure; его радиационная стойкость не является результатом эксперимента.
- **Voter/static shell:** не считать идеальными; будущая fault coverage должна включать их configuration bits/common-mode paths.
- **Reference configurations:** partial bitstreams + hashes и readback reference files защищают целостность лабораторного эксперимента; это не квалификация их storage для полёта.

## 6. Исход ошибки

Нужна системная цепочка:

`configuration upset → SEM detection/report → correction/classification → возможный wrong output до correction → voter/checker/watchdog → stop/decouple → known-RM reconfiguration → intended-image readback/check → SEM re-init → RP reset → replay → return to useful service`.

Отдельно регистрируются: corrected/uncorrectable configuration event; wrong/timeout priority result; replay/drop/duplicate; transition downtime; корректно committed `P/B1/B2` work. Исправление configuration frame не аннулирует ошибочный результат, уже вышедший наружу.

## 7. Наблюдения и своевременность

На ZCU102 доступны причинные SEM status/Monitor/heartbeat, correctable/uncorrectable status, optional essential classification, адрес/error reports и, в Mitigation and Testing, controlled injection/Query. Приложение даёт completion, mismatch/watchdog и backlog.

Но это преимущественно **реактивные** наблюдения. Для выбранной платформы сейчас нет проверенного sensor→near-future-hazard contract. SEM error count не доказан как predictor следующего опасного интервала.

Поэтому можно проверять системную механику causal hysteresis под заранее заданным fault-injection profile, но нельзя заранее утверждать своевременное переключение при естественном росте радиации. В будущем обязательно измеряется полный путь `SEM report→decision→quiesce→DFX→readback→SEM re-init→priority service restored`.

## 8. Обязательные сравнения

Один task trace и один будущий fault trace для всех режимов:

1. **Permanent Productive + constant SEM** — `RM-PROD`, три полезных потока.
2. **Permanent Protected + constant SEM** — `RM-PROT`, TMR `P`, фоновые очереди копятся.
3. **Simple causal hysteresis + constant SEM** — только те же два RM и заранее заданный простой threshold/hysteresis по доступным SEM observations.

Отсутствие теоремы не считается недостатком simple. Если после transition/replay cost hysteresis не даёт преимущества над сильными постоянными режимами, усложнение управления не обосновано.

## 9. Только следующий эксперимент — не исполнение сейчас

**Центральный проверяемый тезис:**

> На одной ZCU102, при постоянном SEM и одном идентичном packet workload, двухрежимное causal переключение `3×productive ↔ TMR-priority` по простому hysteresis может дать больше корректно committed фоновой работы, чем Permanent Protected, при не худшем заранее выбранном показателе корректности/доступности `P`, после оплаты quiescence, DFX, readback verification, SEM re-initialization, replay и lost work.

Минимальные измерения:

- correctly committed `P/B1/B2` packets и deadlines;
- wrong/duplicate/dropped/replayed `P`;
- SEM event/state timestamps;
- времена quiesce, PR, readback/check, SEM re-init, replay и полный downtime;
- intended-image verification и возврат SEM в healthy Observation;
- backlog/lost work/mode residence;
- Vivado resource utilization static + двух RM.

Не нужны на первом шаге: энергетическая кампания, irradiation, сложный predictor или оптимизация threshold.

## Итог

**Есть основание для ограниченного последующего эксперимента.** Инженерная осуществимость двух режимов, постоянного SEM и DFX на ZCU102 имеет прямую документационную и hardware-reference опору. Предпроект не доказывает практическую полезность адаптации, своевременность естественного переключения или окончательный выбор объекта диссертации.

До запуска подтвердить: физическую ZCU102 (или формально перейти на ZCU104), рабочую Vivado/Vitis+SEM/DFX toolchain/license и базовые измеримые времена SEM/DFX/readback. До этого закон управления не разрабатывать.
