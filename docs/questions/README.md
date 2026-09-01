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

## Registered Research Questions

| Permanent ID | Source candidate | Short title | Status | Mapping protocol |
|---|---|---|---|---|
| [RQ-001](RQ-001-reliability-event-metric-horizon.md) | C-RQ-01 | Reliability event, metric and horizon | PARTIALLY ANSWERED / OPEN DEPENDENCIES | [Protocol](../literature_mapping/RQ-001_protocol.md) |
| [RQ-002](RQ-002-sram-radiation-error-model.md) | C-RQ-02 | SRAM radiation error model | OPEN / RES-001 REGISTERED / NEXT GATE ACCEPTED | [Protocol](../literature_mapping/RQ-002_protocol.md) |
| [RQ-003](RQ-003-ecc-abstraction-baseline-class.md) | C-RQ-04 | ECC abstraction and baseline class | OPEN / ACTIVE NEXT INTERFACE | [Protocol](../literature_mapping/RQ-003_protocol.md) |
| [RQ-004](RQ-004-online-observables-for-adaptation.md) | C-RQ-06 | Online observables for adaptation | OPEN | [Protocol](../literature_mapping/RQ-004_protocol.md) |
| [RQ-005](RQ-005-resource-cost-vector.md) | C-RQ-10 | Measurable resource-cost vector | OPEN | [Protocol](../literature_mapping/RQ-005_protocol.md) |
| [RQ-006](RQ-006-physical-logical-mapping-information-sufficiency.md) | C-RQ-05 | Physical-to-logical mapping and information sufficiency | OPEN / RES-001 REGISTERED / NEXT GATE ACCEPTED | [Normative protocol](../normative_baseline/NORMATIVE-BASELINE-01_protocol.md) + [RES-001](../../results/RES-001-exp001-four-word-identified-set.md) |

## Dependency-aware execution order

1. RQ-001 — определить reliability event/metric/horizon.
2. RQ-002 — bound the arrival/event/state model family and supply the reference representation.
3. RQ-006 — use RES-001 as a bounded base and generalize information-sufficiency/bound conditions over a physically defensible `W`/event domain.
4. RQ-003 — active interface: обосновать parameterized ECC state/capability and decoder outcomes before observation/control integration.
5. RQ-004 — define external/internal information channels and observation uncertainty needed by the next control-price gate.
6. RQ-005 — define the measurable resource-cost vector used to price information deficit without arbitrary scalarization.

RQ-005 literature mapping может получить предварительный parallel pass, но окончательное решение зависит от RQ-001, RQ-003 и RQ-004.

## RQ-001 disposition and RQ-002 gate

RQ-001 discovery was accepted as `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`; eLibrary remains deferred/unknown coverage.

Accepted evidence:

- [PAPER-001…003](../paper_cards/README.md);
- [initial cross-paper synthesis](../evidence_synthesis/RQ-001_initial_evidence_synthesis.md);
- [Evidence Audit 01](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md);
- [CLM-001…008](../claims/README.md).

[DEC-001](../decisions/DEC-001-rq001-reliability-contract.md) records the accepted event, metric, protection-domain/partition and horizon contract. RQ-001 is `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; it is not closed, and the numerical reliability requirement remains `TBD`.

RQ-002 mapping, decisive deep reads, synthesis and Evidence Audit 01 are accepted with recorded limitations. The C-RQ-05 escalation condition was confirmed and the PI explicitly approved C-RQ-05 → RQ-006 on 2026-08-28.

EXP-001 passed independent validation and Scientific Review 02 and is complete.
Its PI-approved bounded result is registered as
[`RES-001`](../../results/RES-001-exp001-four-word-identified-set.md). The active
gate is PI disposition of the
[exact proposed RQ-007 wording](../question_candidates/DRAFT-RQ-007-integrated-adaptive-restoration-control.md)
under the accepted
[next quantitative gate](../research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md).
RQ-003 is the next ECC interface; RQ-002 and RQ-006 remain open, and no final
minimum model or target-specific answer is asserted.
