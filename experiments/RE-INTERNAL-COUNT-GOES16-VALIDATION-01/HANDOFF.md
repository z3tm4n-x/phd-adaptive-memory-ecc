# HANDOFF — RE-INTERNAL-COUNT-GOES16-VALIDATION-01

From: Research Engineer
To: Research Orchestrator; отдельный Scientific Reviewer после решения Orchestrator
Date: 2026-09-16
Related RQ: RQ-003, RQ-004, RQ-005, RQ-007; принятое основание RES-003
Branch: research/internal-count-goes16-validation-01
Status: OWN RESULT, выполненная инженерная поставка; acceptance не назначен.

## Версии и что передаётся

- Canonical base: 7b83f643efb37541547d7d93a65ba2f43acd43fd.
- Опубликованный preregistration / весь production execution code:
  870a3c5d725793dd45ff2cc2feaf6e8885df0df9.
- Delivery: коммит, добавляющий этот HANDOFF; его точный SHA сообщён в ответе RE
  и проверяется как `git log -1 --format=%H -- experiments/RE-INTERNAL-COUNT-GOES16-VALIDATION-01/HANDOFF.md`.
  Его parent — указанный preregistration. Самоссылка на SHA собственного содержимого
  намеренно не вставляется. frozen prepare/experiment/check/config/inputs не изменены.
- Исходный RES-003 fb6415444d028526dfc41118b52688ffb83c03dd,
  SR 82117f8b2bea9d92ffcd807e3671ab3dd13e96db, RADAR
  b032505d4d1b15403b8ad06aef578339f6d1c6b4.
- Математическое основание — RES/derivation/принятый SR, не рукопись.
  Арифметический резерв использует принятый upper .000143018263177913 < .0002.
- [REPORT](REPORT.md), [REPRODUCE](REPRODUCE.md), [предварительная фиксация](PREREGISTRATION.md).
  Changed-file scope: только этот каталог; точный список — git diff --name-only base..delivery.
  Main, RES001–004, DEC004, Issue15 и MANUSCRIPT01/02 не изменялись.

## Ответ для решения о GOES-разделе статьи

Основной рост: 2024-10-10 13:00–14:00 UTC. Proposed E_cap=24/20000,
F_hat=.0012, family upper=.002085973800733317.
Count-disabled 3/20000, upper=.0006060289130362039.
G_J=.7517055611, family CI [.7447890379,.7585478686];
delta risk=.00105, family CI [.0001394294,.0019636777].
**Компромисс риск–ресурс при общем epsilon=.1**, не равный риск.

Пик 14:45–15:45: Proposed40/20000, F_hat=.002, upper=.0030862275742715613.
G_J=.7122060930 [.7050514497,.7192839043];
delta risk=.00185 [.0007098608,.0029895084].
Тот же исход: компромисс при общем требовании.

Типичный 2024-10-08 13:05–14:05: 0/20000 у всех политик,
family upper Proposed/disabled=.00030864166555360145, не нулевой риск.
G_J=.8933844992 [.8873740393,.8993305426];
delta risk CI [-.0003432877,.0003432877]. Подтверждённый ресурсный эффект,
но не установлено равенство рисков.

Обязательный Fixed300: достаточные uppers .03220400958, .06291257030,
6.833770852e-7 соответственно; все <=.1. 12 проходов/час.
Это исключает вывод о необходимости сложного управления на этих профилях.
Proposed затратнее выбранной PA-DOM на росте и пике; на пике имеет меньший риск.
Результат не заменять одним положительным сравнением с Fixed1/disabled.

## Вход и воспроизводимость

Вход замкнут для объявленной номинальной реконструкции: пять NOAA G16 L2
v3-0-2, 1440 пригодных bins, 1429 полных окон; основной рост существует.
3mm Al, main_loglog, scale1, native E/W/units/time/quality проверены.
G19 correction не переносилась. G16 P10 upper404 против retained numerical
cutoff390 раскрыт, high bridge включён один раз. Старые G16 calibration
caveats и PARTIAL_SIGMA_EXTRAPOLATION остаются; физическая калибровка не принята.
Исторический часовой ряд в расчётах не используется.

60k независимых marked NHPP trials x5 политик, общие внешние потоки;
вычислительных сбоев/скрытых fallback/отброшенных trials нет.
11 тестов и compileall успешны. Все 60k stream hashes восстановлены,
60 policy-trial результатов повторены точно, агрегатные CSV — побайтно.
Повторная сборка входа из свежих RADAR matrices даёт ту же derived-rate SHA:
e3a1ce8f2a33cd9a60b22039c86ae8f1f7214458850d5a0b609042eace1bc3ac.
Это **воспроизведение**, не независимая физическая калибровка.

Независимая проверка:
явный word-set oracle сам вычисляет проверки/ошибки/counts/first passage;
80 randomized streams x5 плюс детерминированные границы/terminal.
Sentinel ошибочно объединяет адреса в production и обнаруживается oracle.
Oracle разделяет controller _choose/_observe/_analog_next и kernel tables;
фильтр/теорема им независимо не доказаны.
Свёртка десяти строк проверена отдельной scalar quadrature, но использует
общие reconstructed spectra/sigma/transport matrices. Fixed300 проверен
отдельным перечислением всех word offsets на тестовых профилях.
Область независимости намеренно не завышена.

## Артефакты, hashes, ошибки и ограничения

- outputs/policy_summary.csv, paired_summary.csv, journal_table.csv.
- outputs/growth_profile.png/.svg и полная фиксированная трасса.
- outputs/output_hashes.json, raw_results_manifest.json, environment.json,
  reproduction_checks.json, preservation.json; final_checks.json.
- Raw trial NPZ вне Git, paths/hashes в raw_results_manifest.json; воспроизводимы
  по seeds/UTC/trial. Ресурсы: около 48–59 с и 201–202 MB на case process.
- Первые запуски были остановлены Git long-path ошибкой до trials; устранено
  только настройкой среды. JIT-кэш перенесён на короткий временный путь.
  Дважды исправлялась неэффективная распаковка NPZ в validation/postprocessing,
  без изменения модели/выборки/статистики.
- 576 файлов базы проверены: 551 raw-byte equal, 25 checkout-EOL-only,
  содержательных различий нет. Отдельные 10 legacy CSV дают false-positive
  modified в git status и raw-byte равны базе; они не staged. Не заявляется
  буквальный пустой git status этой Windows worktree. Git-история вне задачи
  должна остаться побайтно той же.
- Remaining scientific limitations: response/calibration and within-bin structure,
  не вся миссия; CTMC theorem не перенесена; интервалы только MC условной модели;
  полная экономическая/аппаратная эффективность не оценена.
  Исполнительных BLOCKED_INPUT/неразрешённых numerical failures нет.

## Максимальная формулировка и попытка опровержения

Допустима после принятия только формулировка REPORT §7: собственный count даёт
существенное сокращение проходов относительно count-disabled на этих трёх
профилях; в двух — с установленным ростом риска, при .1; Fixed300 уже достаточен.
Не заявлять универсального превосходства, оптимальности, физической гарантии
или необходимости адаптивности.

SR предлагается попытаться опровергнуть: (1) unit/direction/4pi/bit normalization;
(2) включение события E_cap в distinct-bit pair bound с фактическими краями;
(3) отсутствие скрытых входов в controller; (4) независимость oracle от physical
path; (5) одновременно защищённые CI, conditioning на J и трактовку риска;
(6) неизменность frozen code и повторение input/trial/aggregate hashes.
Любое расхождение, меняющее эти выводы, требует disposition, не подгонки.
Reviewer не запускался; сообщений участникам и изменений Issue15 не было.
