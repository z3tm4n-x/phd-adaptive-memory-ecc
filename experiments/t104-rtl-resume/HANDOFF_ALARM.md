# Research Engineer → Orchestrator: #104, alarm-short-01

**Контрольная поставка ограниченного цикла, не завершение Б.**
[Короткий отчёт/решение](platform/ALARM_SHORT.md).
Ветка`t104-rtl-resume`, существующий draft[PR134](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/134).
Parent/base`3a3656bdf09b7e99fd5f1de2baabb1b55e6a905d`;
main`e63964c2b9ddf6a53fe9c76bd5942f458f167f8e` проверен отдельно, не изменён.
Точный SHA поставки — commit, содержащий эту версию документа; он опубликован
в PR и финальном сообщении после push/сверки remote. Из checkout:
`git log -1 --format='%H%n%P' -- experiments/t104-rtl-resume/HANDOFF_ALARM.md`.
Так не создаётся невозможная самоссылка SHA внутри собственного commit.

## Что установлено и что нет

**OWN RESULT:** gate-equivalence относительно точного3a3656b, k1,455входных
бит кромеclock,520бит FF и pre-edge permit. Инициализация RTL, двоичные
синхронные входы, без требований монотонности now, без иных assumptions.
Отношение состояний asserted, не assumed. На шаге индукции проверяются также
большие счётчики/overflow. Полные reachable traces следуют по индукции;
6384симуляционных случая с инъекцией равных состояний сами по себе не
утверждают достижимость каждого состояния. Предыдущие5000reachable gate
steps и integrated traces повторены отдельно.

Алгебра: A=alarm,U=usable_channel,P=payload_good,V=cmd_valid.
Прежнее C=U∧¬A; A∨(V∧¬(P∧C)) тождественно
A∨(V∧¬P)∨(V∧¬U). В разрешении при V внешний¬bad_payload уже устанавливаетP;
в успешной sequential ветви V устанавливаетP,U,¬A. Поэтому вложенные
проверки исключены без сдвига приоритета. Cold-init/ack и overflow сохранены.
Мутанты: снятый финальный veto — pre case12; deadline< вместо≤ — pre case1;
recover выигрывает alarm для состояния — post case207.

**STA OWN RESULT:** оба новых OOC−1/−2 имеют одинаковые24source hashes;
относительно3a изменён только`rtl/permission_gate.sv`, не XDC/flow. Оба не
проходят250МГц. Извлечение покрывает все4182/3407setup и934/944hold endpoints,
124dynamicGrayD; полные группы/округление сумм проверяет`compare_alarm.py`.
Runtime478.874/427.934с; peak главного Vivado процесса3523.664/3625.270MB
(не сумма параллельных процессов). Полный regression236.841с; поздние три
parser-tests повторены общим82-test unit run, production после регрессии не менялся.

**Физический договор:** новые components1MMCM/5BUFG/16IOBUF и42FMCpin proposal;
их реальный синтез и4096digital tests выполнены. Не полный board-top/STAIO.
Отсутствующие alias grouping, адаптер/load/minmax, источник virtual IO,
clock containment/точность, pin hazards и qualified start — [явно](board/README.md).

**Общий proof:** новый actual-system PDR harness,22/26свойств и120с на
попытку; оба inconclusive,0proved/0disproved. Не считать их PASS или bounded
proof. [Предмет свойств/технические ошибки](INTEGRATION.md#6-actual-endpoint-композиция-ограниченная-попытка-после3a3656b).
Нужны интерфейсные леммы lifetime/ID/release/retire с отдельным доказательством
предпосылок actual calendar/E, не произвольные assumptions. Возвращаем этот
остаток, а не запускаем бесконечный поиск.

## Бюджет следующего решения — не уже выполненная оптимизация

Из первого−1path, ns с округлением Vivado:

| Участок от source C до destination D | Cell / route | Сумма |
|---|---:|---:|
| FF saved CRC и integrity compare, до входа gate | 1.439 / 1.483 | 2.922 |
| Проверка gate и доставка skip_permitted | 0.806 / 3.397 | 4.203 |
| Решение/доставка calendar | 0.248 / 0.794 | 1.042 |
| Всего | 2.493 / 5.674 | 8.167 |

Для этой цепи3нс означают уменьшение5.167нс; для setup требуется4.840нс.
Соседний next_offer→gateCE имеет7.949нс; fanout самого широкого gate control
net512sinkpins, shadow-enable254. Имена/все пути — detail.zip. Нельзя
оптимизировать одну CRC equality и считать соседние конусы закрытыми.

**Рекомендуемая развилка:** разрешить структурное предвычисление статической
валидности полей/CRC/заявки в существующих стадиях, отделив динамические
now/sequence/revocation и короткий прямой veto, с новым miter и бюджетом
композиционных границ. Просто pipeline alarm запрещён. Пока не доказано,
что всё это помещается в прежнюю задержку: это следующий адресный дизайн,
не обещание закрытия250МГц. Альтернатива200МГц требует заново согласовать
календарь/ERR/наблюдаемую запись/загрузку≤80%/ответ≤3мкс; добавка1нс сама
оставляет−3.840нс для неизменной цепи. Это не STA200/Fmax.
Обе ветви требуют отдельного решения по данному существенному дефициту.

## Воспроизведение и проверка передачи

Нужен Git checkout с историей3a3656b/cd68afd. Среда: Ubuntu26.04WSL,
Python3.14.4, Icarus12.0, Yosys0.52
`fee39a3284c90249e1d9684cf6944ffbbcbb8f90`, bundledABC;
Vivado2025.2SW6299465, IP6300035, SharedData6298862, Zynq7000device files.
Отдельно WindowsPython3.12.14unit/compileall. Intel i3-12100F, WSL16GB;
установка`/home/z3tm4n/tools/Xilinx/2025.2/Vivado`, wrapper`~/bin/vivado-wsl`.

Из корня репозитория (без`--write` опубликованные результаты не меняются):

```sh
python3 -B experiments/t104-rtl-resume/run.py --rtl --formal --regression-A
python3 -m compileall -q experiments/t104-rtl-resume
python3 -B experiments/t104-rtl-resume/audit_sta.py --series alarm-short-01
python3 -B experiments/t104-rtl-resume/compare_alarm.py
python3 -B experiments/t104-rtl-resume/compare_sta.py
python3 -B experiments/t104-rtl-resume/delivery_check.py
python3 -B experiments/t104-rtl-resume/composition_check.py
python3 -B experiments/t104-rtl-resume/composition_check.py --ownership-invariants
python3 -B experiments/t104-rtl-resume/board_check.py --vivado /home/z3tm4n/bin/vivado-wsl
python3 -B experiments/t104-rtl-resume/platform_run.py --vivado /home/z3tm4n/bin/vivado-wsl --series reproduce-alarm-short-01 --write
```

Runner отказывается перезаписывать STA-series; для следующего повтора выбрать
свежий label. Новое значение runtime/hash даты отчёта не обязано совпасть.
Последние две команды:~1мин компоненты/~16мин два route, запас7200с на part.
`board_check` проверяет SHA masterXDC; для offline передать`--master-xdc PATH`.
PDR ожидаемо может остаться inconclusive по120с; exit0 не означает proof.

Для detail нового DCP:

```sh
vivado-wsl -mode batch -source experiments/t104-rtl-resume/alarm_detail.tcl -tclargs /absolute/routed.dcp /absolute/new-detail-directory
```

Проверка hashes/извлечение отчётов не является независимым STA; gate miter
использует исторический actualRTL, но общий Yosys/SAT/Icarus. Primitive digital
stub не UNISIM/аналоговый oracle. Эти общие зависимости раскрыты.

В Git только компактные отчёты и`outputs/alarm-evidence.zip`: точные proof
мониторы/buildcopies/logs двух корректных попыток и регрессии. DCP/AIG/full
Vivado projects вне Git в.build; точные paths/hashes — summary JSON.
До/после integration/rtl, preserved42inputs и evidence member hashes —
`outputs/alarm-evidence.json`. Старые STA-архивы сохранены побайтно.
Список файлов: `git show --name-status <delivery-SHA>`; все изменения в
собственном`experiments/t104-rtl-resume/`. Семь исторических COSRAD CSV с
EOL-диагностикой не staged/не исправлены, raw равны исходнойHEAD.

Ограниченный alarm-цикл завершён; дальнейшая разработка Б остаётся открыта.
Принятые параметры/пакеты, main, очередь задач, RES/DEC,PS/ARM,В/Г,Reviewer
не менялись/не запускались. Следующий шаг — решение Orchestrator по бюджету
цепей; физическое замыкание и общий proof не подменяются выигрышем WNS.
