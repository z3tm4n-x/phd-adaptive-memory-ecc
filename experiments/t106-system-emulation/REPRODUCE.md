# Повтор цифрового пакета Г / #106

Все команды — из корня checkout. Для **проверки поставленных результатов**
нужен Python ≥3.11 и стандартная библиотека, без Vivado, NumPy и доступа
к машине инженера:

Проверенная среда — Linux/WSL с UTF-8. При переносе в Windows задайте
PYTHONUTF8=1 для процесса и его дочерних проверок; отдельное выполнение
всего пакета под Windows здесь не заявляется.

```sh
python3 experiments/t106-system-emulation/reproduce.py
```

Пока оба полных прогона сценария 2 не прошли независимую проверку, команда
возвращает ненулевой код и INCOMPLETE. Для предварительного повторения
только имеющихся данных предусмотрен явный --allow-incomplete; он не
является проверкой окончательного пакета. Пилот не подставляется вместо полного результата.
Исторические сообщения вложенных checker сохраняют прежний статус своей
поставки; актуальный итог — последнее сообщение и five-scenarios.json.

Команда проверяет 244 закреплённых входных хеша, unit tests и компиляцию
Python, старые холодные трассы, 1/3/5, буквальные/ускоренные свидетели,
инъекции, память, историю/разрешения, цену и все новые адресные регрессии.
Для полного 2 дополнительно проверяется каждая сохранённая запись CT3 и
SHA исходного текста. Отдельная арифметика FAST не вызывает расчёт шины
симулятора. Read-only повтор не меняет научные выходы.
Два полных журнала проверяются отдельными процессами параллельно;
оба должны завершиться успешно до проверки общей таблицы. Это только
организация повторного чтения: checker, исходные трассы и критерии те же.
При ограниченных ресурсах их можно проверить последовательно командой
`python3 experiments/t106-system-emulation/verify_burst_v3.py`.

## Адресная проверка

В текущей проверенной Linux-среде выполнены все 69 unit tests без пропусков.
При отсутствии GCC пропускается один тест C-моста; на другой ОС также
может пропускаться Linux-FIFO тест. Независимое чтение поставленных трасс
не требует GCC. Число пропусков нужно сохранять, а не называть таким запуском
повтор всех 69 выполнений. Копия опубликованного 518fd5a без локальных .build
и .tools прошла весь доступный --allow-incomplete повтор в Linux/WSL:
в том зафиксированном снимке было 66 тестов. Следующий commit добавил тест
выбора полного V3-пути в replay CLI, не меняя исполняемые источники V3.
Ещё два теста проверяют параллельный read-only повтор: ожидание обоих
проверяющих процессов и обязательный отказ при ошибке любого из них.

```sh
python3 experiments/t106-system-emulation/verify_burst_repair.py
python3 experiments/t106-system-emulation/verify_burst_upgrade.py
python3 experiments/t106-system-emulation/verify_trace_upgrade.py
python3 experiments/t106-system-emulation/replay_burst.py --case cold-envelope
# После появления обоих полных результатов:
python3 experiments/t106-system-emulation/verify_burst_v3.py
python3 experiments/t106-system-emulation/five_scenarios.py
python3 experiments/t106-system-emulation/final_price_check.py
```

`verify_burst_repair` проверяет сохранённые отрицательный/положительный
same-edge примеры и точность длинных временных меток XSim.
`verify_burst_upgrade` подтверждает побайтовое совпадение обеих новых
20-событийных трасс со старыми. Это технические проверки, не сценарий 2.

## Новое исполнение ARM ISA / vendor XPM / RTL

Нужны Linux/WSL Ubuntu, GCC, Vivado 2025.2 с Zynq-7000, закреплённые
Unicorn 2.1.4 / pyelftools 0.33 (Capstone 5.0.6 входит в исходный комплект).
Используются **принятые ELF**, новая сборка контроллера не требуется.
В выполненной среде: Ubuntu 26.04/WSL2, Python 3.14.4, GCC 15.2,
Vivado 2025.2 build6299465. VIVADO можно задать путём к совместимому wrapper.
В исходной среде wrapper — /home/z3tm4n/bin/vivado-wsl.

Повторять в отдельном checkout либо заранее сохранить уже поставленные
выходы. Не запускать вторую копию поверх работающего полного прогона.
Отдельный checkout тоже содержит опубликованные результаты: перед новым
--execute сохраните его outputs/burst3-* вне outputs (например, в отдельной
папке .build/published-v3). Это исходные результаты для сравнения, не мусор.
V3 намеренно запрещает перезапись имеющихся metadata/CT3. Для обычной
проверки поставки ничего перемещать не нужно; используйте команду без --execute.
В текущем workspace закреплённые wheels доступны так:

```sh
export T106_ANALYSIS="$PWD/../t105-arm-rule/experiments/t105-arm-rule/.tools/analysis"
python3 experiments/t106-system-emulation/verify_burst_repair.py --execute --record
python3 experiments/t106-system-emulation/verify_burst_v2.py --pilot-events 20 --execute --record
python3 experiments/t106-system-emulation/verify_burst_upgrade.py --record
python3 experiments/t106-system-emulation/run_burst_v3.py --case short --mode adaptive
python3 experiments/t106-system-emulation/verify_burst_v3.py --pilot-events 20 --execute --record
python3 experiments/t106-system-emulation/verify_trace_upgrade.py --record
python3 experiments/t106-system-emulation/run_full_profile_v3.py
python3 experiments/t106-system-emulation/five_scenarios.py --record
python3 experiments/t106-system-emulation/reproduce.py
```

В другой среде задайте свой каталог **тех же версий и хешей**.
Опциональная первоначальная установка task-local wheels и повтор исходного
холодного опыта: `reproduce.py --execute --bootstrap`; хеши сверяются с
t105-arm-rule/outputs/analysis-tools.json, глобальная среда не изменяется.
Повтор остальных actual прогонов:
`reproduce.py --execute-empty --execute-accel --execute-sparse`.
Новый согласованный холодный опыт:
`cold_envelope.py --execute --record`.

Полный supervisor запускает два режима, прекращает парный путь при отказе
одного и сохраняет состояние в .build/full-profile-v3/state.json.
Статус verified_both включает независимый checker, а не только exit0
симулятора. Финальная таблица не публикуется без обоих полных результатов.
Изменение уже проверенного результата/trace отклоняется; обновление только
проверочной provenance хранит предыдущие хеши. Tuple/list нормализуются
без округления чисел.

## Хранение, стоимость повторения и пределы

CT3 — обратимое колонночное сжатие всех исходных токенов, не генерация
PIN-строк эталоном. Временные CT2/vendor-build/частичные неудавшиеся журналы
остаются в игнорируемой .build; для независимого повтора нужны опубликованные
CT3, metadata и исходники. Они не зависят от Windows-пути инженера.
При свежем Vivado-исполнении служебные WDB могут занимать десятки гигабайт:
место для .build нужно отдельно от компактного поставляемого журнала.
Первая неудачная полная попытка не используется как результат:
outputs/failed-full-attempt.json содержит её происхождение и локальные хеши.
Вторая попытка отклонена из-за таймаута постобработки; её факты/хеши —
outputs/failed-postprocessing-attempt.json. V3 сохраняет исходный ASCII SHA
и metadata до длительной проверки, затем подтверждает тот же SHA/число строк
при транскодировании и полном независимом replay. Подробности — POSTPROCESSING.md.

Измерено на хосте в V3: пилот adaptive 107,93 с / FAST 57,97 с;
полное исполнение/capture — 12719,202 / 8833,225 с. Эти времена не включают
последующее транскодирование и независимый replay; точные значения — поле
host_elapsed_s в metadata каждого режима. Независимая проверка полного
FAST заняла ещё 2295,429 с, adaptive —2836,238 с.
Согласованный cold — 74,22 / 72,75 с.
Это времена хоста, не ARM. Переносимый replay также читает весь журнал,
поэтому существенно дольше коротких unit tests.
Исходные большие данные NOAA не нужны: выбранные 6065 строк и инъекции
уже закреплены, BURST.md объясняет временную форму и условную нормировку.

Принятый PL route переиспользован по 9 хешам; нового route нет.
Доступность платы не подтверждена, аппаратные измерения не выполнялись.
Аппаратные CPU-время/WCET неизвестны. **Q(T) за срок эмуляцией не доказывается.**
