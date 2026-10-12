# Повтор контрольного результата

Из корня ветки, в Ubuntu/WSL с Icarus12, Yosys0.52 + yosys-abc и Vivado2025.2
с установленным xc7z020:

```sh
python3 -B experiments/t104-rtl-resume/registered/reproduce.py --run
```

Путь по умолчанию `/home/z3tm4n/bin/vivado-wsl`; другой исполняемый wrapper:
`--vivado /absolute/path/to/vivado`. Wrapper должен подключать settings64.sh.
09.10 повторно сверены SHA-256 установленных vendor-файлов, совпадающие с
`installed_vendor_sources` в [предыдущем manifest](../split/manifest.json):
CDC HDL `27592359d8363d7e6575298f9d0faa7c9f9258ea77f19c9a38946fbaf3783f09`,
handshake Tcl `c524b464dff2e91e30389fa624522c37bd1585068041e303918218ac66625c1c`,
FIFO HDL `60f6087dbfbe0602796fefef3231963247559fd3eac4641241ccf6397bd91b9d`.
Python использует только стандартную библиотеку. Вся генерация — в `.build`;
опубликованные файлы исторических пакетов не перезаписываются. Новые JSON/ZIP
контрольного результата обновляются. Примерный ресурс повтора:10–20 минут,
3–4 ГБ на один Vivado-процесс; точные версии, длительности и логи в manifest.
Это ориентир, не WCET аппаратуры. Большие DCP/сборки локальные и не входят в git.

Отдельные команды (порядок важен для зависимости lane proof от miter):

```sh
python3 -B experiments/t104-rtl-resume/registered/contract_check.py
python3 -B experiments/t104-rtl-resume/registered/prove_equivalence.py
python3 -B experiments/t104-rtl-resume/registered/prove_lane.py
python3 -B experiments/t104-rtl-resume/registered/prove_guard.py
python3 -B experiments/t104-rtl-resume/registered/verify.py --vendor
python3 -B experiments/t104-rtl-resume/run.py --rtl --formal --regression-A
```

Точный STA top — `clocked_lane`, новый operation_lane/registered E, старые
проверенные clock_250_50/slow_queue/async_queue. Сценарий `lane_sta.tcl`
принимает part и **новый** каталог результата; `inspect_routed.tcl` проверяет
все внутренние пути отдельно от общего отчёта. Основные результаты обязаны
различать положительные внутренние slack и отрицательный полный OOC.
Vivado не должен скрывать отсутствующие XPM clocks через fallback1000/3003 нс.
Финальные стандартные data exceptions12/60 нс и общие uncertainty.5/.1 сохранены.

Эталон `reference.py`, старая testbench и parser `split/check.py` — общие
зависимости. Новая bench меняет только получение тестового ID по порядку
grant: внутри fast DUT ID больше нет. Возвращаемый **реальный** slow-ID
проверяется относительно принятого. Source/data/capture внутри DUT не
подменяются моделями. Для formal vendor boundary наоборот объявлена
абстракция; её нельзя выдавать за формальное доказательство XPM.

`evidence.zip` содержит открываемые обычным ZIP-инструментом тексты STA,
effective XDC, формальные и simulation-логи и полную старую регрессию.
Их SHA-256 закреплены в manifest. Vendor HDL/IP, netlists/DCP и секретов нет.
Повтор может изменить elapsed/path/date/log hashes; критерии — те же свойства,
пин-трассы, функциональные результаты и заявленные timing margins, а не
побайтовое равенство строк с датами. Указанный в передаче commit определяет
научный/инженерный вход; новый запуск не объявляется независимой рецензией.
