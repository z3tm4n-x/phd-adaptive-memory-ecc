# Scientific Reviews — действующие основания

Актуальный указатель 2026-09-11. Вердикты и тексты рецензий сохраняются без изменений. [DEC-004](../decisions/DEC-004-dissertation-architecture-A.md) выбирает путь A и не является новым Scientific Review. Области принятия задают [карточки RES](../../results/README.md) и явные dispositions.

| Объект | Действующая рецензия | Применение и закрытие |
|---|---|---|
| EXP-001 / RES-001 | [Review 02](EXP-001_SCIENTIFIC_REREVIEW_02.md), PASS | Исправление независимого эталона принято; 14 условий RES-001 сохраняются. [Review 01](EXP-001_SCIENTIFIC_REVIEW_01.md) остаётся историей замечаний. |
| CY62167 | [Scientific disposition](CY62167_SCIENTIFIC_DISPOSITION_01.md), [semantics repair Review 02](CY62167_SEMANTICS_REPAIR_REVIEW_02.md) | Registered-event и W-ограничения сохраняются. Остаточный ERR consumer MINOR не закрыт U-ветвью, а обходится ею. |
| Stage A | [Scientific Review](STAGE_A_SCIENTIFIC_REVIEW_01.md) | Применяется с последующими исправлениями воспроизводимости; не физическая калибровка среды. |
| Информационный интерфейс | [Review](STAGE_A_INFORMATION_INTERFACE_REVIEW_01.md) | Локальное закрытие — [REPORT пакета](../../experiments/STAGE-A-INFORMATION-INTERFACE-01/REPORT.md). |
| RES-002 | [Review 02](GOES_REAL_TEMPORAL_REVIEW_02.md), PASS_WITH_MINOR | [Closeout 43cfad8f](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/43cfad8f8b411f1abfa625fae4117f93d07c27f4). [Review 01](GOES_REAL_TEMPORAL_REVIEW_01.md) и дефектная карта — история, не действующая полная карта. |
| RES-003 | [Review 01](INTERNAL_COUNT_CONTROL_REVIEW_01.md), PASS_WITH_MINOR | Арифметическое закрытие MINOR — §5 [RES-003](../../results/RES-003-internal-count-control.md); условный численный контракт сохраняется. |
| RES-004 | [Review 01](INTERNAL_COUNT_UNKNOWN_D_REVIEW_01.md), PASS_WITH_MINOR | [Поправка 8b865cbb](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/8b865cbbbec2406a7eccd033bb3c2ff150f4c995), [RES-004](../../results/RES-004-internal-count-unknown-d.md). Историческая независимость held-out не установлена. [Сохранённый проверочный код](checks/internal_count_unknown_d_review_01.py) перенесён без исполнения. |
| Инженерное продолжение | [Review 01](ENGINEERING_APPLICABILITY_REVIEW_01.md), PASS_WITH_MINOR | [Disposition и Endpoint-поправка](../research_gates/ENGINEERING-APPLICABILITY-SR-DISPOSITION-01.md): LOCAL CLOSED, без изменения вердикта и без сертификата изменённого банка. |

Полная цепочка версий, авторство и отвергнутые интерпретации — в [карте исследования](../research_map.md). Рецензии на ограниченные пакеты не являются общим PASS проекта, устройства или диссертации.

**RE-FIXED-ADAPTIVE-FEASIBILITY-01:** [SR на 619492db](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/619492db33cb8793710fb4e454616f543993c982), объект 03e6c4ad, общий вердикт **REVISE**; [документальный довыпуск a88d6a26](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a88d6a26c54c193e3d518fb16f43ffd19511202b/experiments/RE-FIXED-ADAPTIVE-FEASIBILITY-01/SCIENTIFIC_REVIEW_DISPOSITION.md) фиксирует только разрешённое ограниченное cold-start принятие. Он не является общим повторным SR. Warm-start строки не сертифицированы для произвольного начального scalar. Новый RES не присвоен.

В текущем физическом приоритете не восстанавливать отозванный lower-floor смысл direct-суррогата CY62167 и старого синтетического bracket. Новые существенные утверждения о floor, полном ECC outcome и формальной методике потребуют собственных адресных проверок.

**RE-CY62167-PHYSICAL-BRIDGE-01:** [SR 18b78a64](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/18b78a647ac299290b5e2399b8af581e14240b88/docs/scientific_reviews/CY62167_PHYSICAL_BRIDGE_REVIEW_01.md), exact target 0c979c34; **REVISE, 2 MAJOR / 3 MINOR, без CRITICAL**. [Disposition Orchestrator и repair](../research_gates/RE-CY62167-PHYSICAL-BRIDGE-REPAIR-01.md) принимают ограниченно D3/2t+1 и условные вероятностные компоненты, не CY62167-свидетель или физический численный сертификат. Issue №15 открыт, новый RES не присвоен. Отчёт и его проверочный скрипт сохранены на ветке отдельного Reviewer без переписывания; дальнейшая проверка — адресный re-review нового repair SHA.
