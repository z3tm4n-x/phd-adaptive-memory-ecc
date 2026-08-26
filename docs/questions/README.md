# Research Questions

Этот каталог является canonical Git-реестром утверждённых Research Questions диссертационного проекта.

## File convention

Каждый утверждённый вопрос хранится в отдельном файле:

```text
RQ-xxx-short-title.md
```

Карточка должна соответствовать RQ-шаблону из `docs/artefact_templates.md`.

## Registration rules

1. Вопрос должен быть достаточно узким, чтобы им можно было управлять через targeted literature mapping и/или определённый эксперимент.
2. Для вопроса должны быть явно указаны scope, exclusions, dependencies, требуемый evidence и критерий ответа/решения.
3. Каждый открытый RQ должен иметь один конкретный next action.
4. Окончательный `RQ-xxx` назначается только после утверждения приоритетного пакета.
5. Кандидатные обозначения `C-RQ-xx` являются временными и не резервируют окончательные RQ-ID.
6. Гипотезы не создаются автоматически из RQ; они регистрируются отдельно после появления достаточного литературного основания.

## Registered initial RQ package

| Permanent ID | Source candidate | Short title | Status | Mapping protocol |
|---|---|---|---|---|
| [RQ-001](RQ-001-reliability-event-metric-horizon.md) | C-RQ-01 | Reliability event, metric and horizon | OPEN | [Protocol](../literature_mapping/RQ-001_protocol.md) |
| [RQ-002](RQ-002-sram-radiation-error-model.md) | C-RQ-02 | SRAM radiation error model | OPEN | [Protocol](../literature_mapping/RQ-002_protocol.md) |
| [RQ-003](RQ-003-ecc-abstraction-baseline-class.md) | C-RQ-04 | ECC abstraction and baseline class | OPEN | [Protocol](../literature_mapping/RQ-003_protocol.md) |
| [RQ-004](RQ-004-online-observables-for-adaptation.md) | C-RQ-06 | Online observables for adaptation | OPEN | [Protocol](../literature_mapping/RQ-004_protocol.md) |
| [RQ-005](RQ-005-resource-cost-vector.md) | C-RQ-10 | Measurable resource-cost vector | OPEN | [Protocol](../literature_mapping/RQ-005_protocol.md) |

## Dependency-aware execution order

1. RQ-001 — определить reliability event/metric/horizon.
2. RQ-002 — выбрать минимально достаточную radiation error model и проверить gate C-RQ-05.
3. RQ-003 — обосновать ECC abstraction и baseline.
4. RQ-004 — определить online observables.
5. RQ-005 — зафиксировать measurable resource-cost vector.

RQ-005 literature mapping может получить предварительный parallel pass после пилота, но окончательное решение зависит от RQ-001, RQ-003 и RQ-004. Пилотный Literature Scout запускается для RQ-001.
