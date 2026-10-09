# #104: проверка конфигурации при загрузке, −1/250 МГц

**08.10.2026, OWN RESULT: упрощение эквивалентно прежнему RTL, но не закрывает
250 МГц. Б остаётся незавершённым; PR134 — draft.** Продолжение от
`cd68afd309cc00a152dca51dd557b76991afdb13` по [поручению](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/pull/134#issuecomment-6065477339).
База/main при проверке: `e63964c2b9ddf6a53fe9c76bd5942f458f167f8e`.
Это контрольная поставка адресной правки, не новый научный результат или SR.

## Результат до/после

В `service_config` двенадцать широких сравнений перенесены на разрешённый
фронт записи поля. Хранятся результаты **последней** записи, а не sticky-success.
Arm не получил дополнительного такта; параметры, периоды, квоты и весь E неизменны.
Основной `xc7z020clg484-1`, 250 МГц, Vivado2025.2 build6299465; те же XDC,
IO/CDC constraints, synthesis/place/route flow. Перебора directives не было.

| Расчётный показатель | cd68afd | config-load-01 |
|---|---:|---:|
| WNS / TNS, нс | −6.439 / −11244.293 | **−5.706 / −9734.453** |
| WHS / THS, нс | −1.338 / −1413.252 | −1.336 / −977.085 |
| Нарушенные setup / hold endpoints | 4393 / 1329 | 4280 / 937 |
| LUT / FF | 5248 / 4500 | 5073 / 4122 |
| BRAM / DSP | 0 / 0 | 0 / 0 |
| Худший memory path: cell + route, нс | 2.006 + 7.790 | 3.105 + 6.032 |
| Gray union skew, цель 2 нс | 2.034 | 1.892 |

Улучшение WNS **0.733 нс**, экономия175LUT/378FF. Новый критический путь:
`core/now_reg[13] → core/calendar/decisions_reg[3]/D`,9.137нс,16уровней.
SOURCE внутри собственного STA: путь проходит через `error_reply` compare,
`gate/loss`, `permit_at_edge`, `decide_execute`.
INFERENCE по RTL: следующим узким местом стала same-edge проверка временной
метки входящей заявки → alarm → разрешение LOW → freeze календаря.
Перенос её на более поздний фронт без нового доказательства меняет приоритет
ошибки. При неизменной цепи добавление1нс оставило бы −4.706нс; это **не**
прогон200МГц и не Fmax. Доказательства невозможности платформы нет.

## Проверки и точный остаток

- Конфигурация: 16assertions, индукция k=1 для всех17ширин WORD_BITS3…19
  с правильным inverse и трёх неправильных параметризаций; все двоичные
  входные истории из RTL initialization. Четыре внешних выхода и12отношений
  представления **доказаны**, не приняты как assumptions. Golden — точный blob
  cd68afd. Отдельная словарная модель проверила31 640фронтов pre/post;
  два дефекта (`wr+commit`, сохранение match после плохой перезаписи) отвергнуты.
  Неполный банк, start_ok, sticky fault, запись после lock и повторный commit
  включены; fault не получил нового права запрещать позднейший правильный arm.
- Полная регрессия:72unit tests,49testsА; прежние E24/k43, RPC PDR рабочих
  ширин и352010интеграционных фронтов. `integration.json` и `rtl.json` совпадают
  с cd68afd побайтно. Windows/WSL compileall. Общие Yosys/Icarus и константы
  раскрыты; это не независимый решатель и не proof всего executor.
- Gray: все124динамических D покрыты max4нс, худший slack+1.749нс,
  max data2.025нс; union skew slack+0.108нс. `Invalid endpoint` объяснён
  четырьмя D старших62/63бит CPU/X, подключёнными к GND; это **проверено по
  DCP**, а не предположено. Они не несут меняющийся Gray. Исключения не менялись.
- Все937hold-нарушений в отдельной полной выборке начинаются на виртуальных
  **ports**, не на внутренних FF: command417,CPU249,memory15,X256. Худший
  `app_kind[0] → ports[0].frontend/held[0]/D`. Это несовместимость выбранного
  виртуального min0.1нс с моделью clock insertion, не измерение внешней SRAM.
  Нельзя закрыть её произвольным увеличением input delay или blanket cut.
- CDC unwaived:1042CDC-1,14CDC-3,2CDC-6,1164CDC-15. По521CDC-1 идут от
  CPU/X к очереди, gate и decisions; по374CDC-15 — к данным/ID/threshold;
  ещё416CDC-15 — command→receiver. Handshake-обоснование должно покрыть
  **реальный** endpoint и same-edge управляющие конусы, не только RPC.
  `check_timing`:12категорий0; ignored exceptions0; routing errors0.

**Следующее адресное действие:** укоротить найденную цепь валидности заявки /
same-edge alarm без изменения фронта freeze; вместе с этим закрыть машинную
композицию реальной очереди с RPC/календарём/E. Она здесь не продвинута до нового
proof: сохраняются компонентные индукции и точный остаток [INTEGRATION §3](../INTEGRATION.md).
Другой путь —200МГц **только с полным пересчётом**; он не запускался и успех
не обещан. Новый -2 не запускался: справочные результаты cd68afd относятся
к старому RTL, не выдаются за проверку этой правки.

Clock/SRAM/FMC wrapper, исключение hazards CE/OE/WE/drive, pad/load/turnaround,
ξ/edge допуски и начало остаются открыты. Требуются согласованный адаптер/pin
map и условия нагрузки/трасс, а не только имя ZedBoard. Нельзя заменить пару
alias одного internal32+6 произвольным `2*word` без основания группировки.
Полные logic3нс/output4нс/return2нс и10% для E/observed-write не подтверждены.
Прежние условные79.76551260464%/1мс и2.148320350мкс не стали FPGA-измерениями.
Main, А, T104-budget/T110/T114 и научные параметры не изменены; В/Г не начаты.

## Повтор, происхождение и границы проверки

Из корня Git checkout (не source ZIP: golden требует историю cd68afd):

```sh
python3 -B experiments/t104-rtl-resume/run.py --rtl --formal --regression-A
python3 -m compileall -q experiments/t104-rtl-resume
python3 -B experiments/t104-rtl-resume/audit_sta.py --source-ref cd68afd309cc00a152dca51dd557b76991afdb13
python3 -B experiments/t104-rtl-resume/audit_sta.py --series config-load-01 --parts xc7z020clg484-1
python3 -B experiments/t104-rtl-resume/compare_sta.py
python3 -B experiments/t104-rtl-resume/platform_run.py --vivado /home/z3tm4n/bin/vivado-wsl --parts xc7z020clg484-1 --series reproduce-config-load-01 --write
```

Последняя команда создаёт **новую** серию; runner отказывается перезаписывать
готовую. Для ещё одного повтора нужно новое имя серии. Отчёты cd68afd сохранены.
Репродукция Vivado не обязана дать byte-identical даты/логи/ZIP.
Read-only детализация: `vivado-wsl -mode batch -source
experiments/t104-rtl-resume/sta_detail.tcl -tclargs <routed.dcp> <new-directory>`.
Это чтение checkpoint, без новых constraints или повторной трассировки.

[Сопоставление и группы](../outputs/sta/config-load-01/comparison.json),
[summary/исходные hashes](../outputs/sta/config-load-01/xc7z020clg484-1/summary.json),
[18отчётов](../outputs/sta/config-load-01/xc7z020clg484-1/reports.zip),
[7детальных файлов](../outputs/sta/config-load-01/detail.zip),
[доказательство конфигурации](../outputs/config_equivalence.json).
Archive hashes: STA `bf739ecb584b63b9d2f0ad50f5962ce007087afb7964f278c6a401af6e3d0597`;
detail `fb2abc79a769ddde25c77fa55598d847a96a833ec21c064fa0be27b6377b2cb4`.
Все отчёты дословные. DCP/log остаются в `.build`; exact path/hash есть в summary.
Detail получен из того же DCP; его hash проверен до упаковки. Извлечение и
проверка целостности не являются независимой STA или waiver CDC.
Сумма округлённых hold slacks −977.130нс отличается от THS−977.085нс на0.045нс
в пределах округления937строк; знак/endpoint count не изменены.

Vivado run414.756с, peak главного процесса3730.691MB (не сумма дочерних).
Ubuntu26.04/WSL, Python3.14.4, Icarus12.0, Yosys0.52
`fee39a3284c90249e1d9684cf6944ffbbcbb8f90`, bundledABC;
Windows Python3.12.14. Полный заключительный прогон с72tests:229.911с;
предыдущий с66tests:266.352с. Ориентир регрессии4–5мин, STA7–10мин, предел7200с.
Первый proof probe потребовал `memory_map` для `$mem_v2`; первый detail probe
остановился на неподдержанном свойстве `PATH_GROUP` (правильное `GROUP`).
Это исправленные технические ошибки проверяющего кода, не RTL-контрпримеры;
успех им не присваивался. Мутанты и сырые диагностические прогоны вне Git.
