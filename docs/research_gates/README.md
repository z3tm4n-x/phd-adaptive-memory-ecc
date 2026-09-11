# Исследовательские этапы и решения

Актуальный указатель 2026-09-11. Действующее направление — [DEC-004: путь A](../decisions/DEC-004-dissertation-architecture-A.md). Физический мост → формальная методика выбора → аппаратное подтверждение. Поиск нового объекта завершён. Это навигация, не новый регламент или запуск исследования. Исторические задания сохраняются с исходными статусами; применимость определяется явными последующими решениями, [состоянием](../current_status.md) и [историей](../research_map.md).

## Консолидация принятого состояния

[RE-REPOSITORY-CONSOLIDATION-01](REPOSITORY-CONSOLIDATION-01.md) и [selection.json](REPOSITORY-CONSOLIDATION-01.selection.json) фиксируют научный состав Orchestrator и разрешение PI на интеграционный PR и merge. Исполнитель — постоянный Research Engineer в отдельной сессии. Проверяются комплектность, Git-объекты, исходные байты, авторство, ссылки и Issues; новые расчёты, общий SR и рефакторинг научного кода исключены. Итог и точные SHA публикуются в интеграционном PR и квитанции RE.

## Закрытые исследовательские этапы

| Этап | Действующее основание закрытия |
|---|---|
| EXP-001 | [RES-001](../../results/RES-001-exp001-four-word-identified-set.md) и [Review 02](../scientific_reviews/EXP-001_SCIENTIFIC_REREVIEW_02.md). |
| Ограниченный PA-DOM-01…04 | [Полная адресная матрица](../evidence_synthesis/DRAFT-RQ-007_PA-DOM-01-04_comparison_matrix.md) и [контроль идентичностей](../literature_mapping/PA-DOM-01-03_identity_control.md); DRAFT и эпистемические метки сохранены. |
| Внешняя информация / real-temporal | [RES-002](../../results/RES-002-external-information-restoration.md), [Review 02](../scientific_reviews/GOES_REAL_TEMPORAL_REVIEW_02.md), [closeout 43cfad8f](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/43cfad8f8b411f1abfa625fae4117f93d07c27f4). |
| Собственный счётчик, известный закон | [Принятое задание](INTERNAL-COUNT-CONTROL-PROPOSAL-01.md) → [RES-003](../../results/RES-003-internal-count-control.md), арифметическое закрытие MINOR в §5. |
| Неизвестный постоянный D | [Принятое задание](INTERNAL-COUNT-UNKNOWN-D-PROPOSAL-01.md) → [RES-004](../../results/RES-004-internal-count-unknown-d.md), [SR](../scientific_reviews/INTERNAL_COUNT_UNKNOWN_D_REVIEW_01.md) и [поправка 8b865cbb](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/commit/8b865cbbbec2406a7eccd033bb3c2ff150f4c995). |
| Локальная инженерная основа | [Исправление авторства](ENGINEERING-APPLICABILITY-ROLE-CORRECTION-01.md), [handoff постоянному RE](ENGINEERING-APPLICABILITY-RE-CONTINUATION-01.md), [согласование редакций](ENGINEERING-APPLICABILITY-DELIVERY-RECONCILIATION-01.md), [SR](../scientific_reviews/ENGINEERING_APPLICABILITY_REVIEW_01.md), [disposition с Endpoint-поправкой](ENGINEERING-APPLICABILITY-SR-DISPOSITION-01.md). LOCAL CLOSED в области SR, без нового RES. |

## Действующий этап и сохранённые последующие поставки

[Прежняя позиция](DISSERTATION-COMPLETION-POSITION-01.md) сохраняется исторически; новый выбор и критерии завершения полностью заданы DEC-004. Первый приоритет — физический мост CY62167 → W/ECC и корректные границы риска; [backlog](../research_backlog.md).

[Задание Fixed/Adaptive](RE-FIXED-ADAPTIVE-FEASIBILITY-01.md), [Issue №12](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/12), исполнение/repair и [cold-start disposition a88d6a26](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/a88d6a26c54c193e3d518fb16f43ffd19511202b/experiments/RE-FIXED-ADAPTIVE-FEASIBILITY-01/SCIENTIFIC_REVIEW_DISPOSITION.md) — завершённый этап в ограниченной области, общий SR остаётся REVISE. Старое «подготовлено к передаче» больше не действует для этого исполнения.

[FPGA-prefeasibility 08e7838e](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/tree/08e7838eeb15f117774fa1b838c1d4264dd13d36/experiments/RE-FPGA-PROTECTION-PREFEASIBILITY-01/) и [подготовленное статическое уточнение b45f7710](https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/b45f77106d79f12ebc7b0ba1c642659a7e4a2e27/docs/research_gates/RE-FPGA-STATIC-EXECUTOR-CHECK-01.md) сохранены как альтернативная ветвь. Их наличие не разрешает стенд и не блокирует A; подтверждения приёма/исполнения последнего уточнения здесь нет.

[Первая статья RES-003](../publication_plans/RES-003-PUBLICATION-HANDOFF.md) продолжается отдельно; подтверждающая выборка RES-004 является отдельной будущей публикационной проверкой. Старые NOT EXECUTED или ACTIVE в исторических документах не являются текущими поручениями.
