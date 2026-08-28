# Research Backlog

This file records bounded future tasks that must not be mixed into the active RQ unless their trigger is reached. Entries are orchestration tasks, not accepted `RQ`, `HYP`, `DEC` or `RES` artefacts.

## Registered — RQ-006 mapping/information sufficiency

**Status:** `PROMOTED / ACTIVE WITH EXP-001`<br>
**Decision:** PI approved C-RQ-05 → [RQ-006](questions/RQ-006-physical-logical-mapping-information-sufficiency.md) on 2026-08-28.

The former escalation backlog item is resolved. RQ-006 owns `W`, interleaving, joint post-`W` impact and representation-reduction validity. RQ-002 retains arrival/event/state modelling and RQ-003 retains decoder-outcome semantics.

## Active parallel branch — Russian normative baseline

**Status:** `SOURCE SET RECEIVED / BOUNDED EXTRACTION READY / NON-BLOCKING FOR SYNTHETIC EXP-001`<br>
**Protocol:** [NORMATIVE-BASELINE-01](normative_baseline/NORMATIVE-BASELINE-01_protocol.md)

Source set:

- РД 134-0174-2009;
- РД 134-0175-2009, supplied 2012 reissue with amendment 1;
- СТО ГК Роскосмос 04.01.0005–2022.

Purpose: reconstruct the information-retention chain from functional diagnosis and event classification through cross section, environment convolution, rate and probability, then determine which outputs are directly usable or require augmentation by `W`/ECC/observation assumptions.

The supplied STO file's controlled-revision status remains ambiguous because approval/registration statements coexist with hidden `Проект, окончательная редакция` text. The bounded extraction must preserve that provenance issue without treating the content as nonexistent.

Exact PI follow-up material requested:

1. controlled-edition/registry evidence for STO 04.01.0005–2022;
2. ГОСТ РВ 0020–57.415–2020;
3. STO 04.01.0008–2024;
4. STO 04.01.0010–2025;
5. a representative SRAM private PMI or de-identified template and diagnostic/software output schema.

Do not launch a broad standards search. Request another source only when one matrix link remains unresolved.

## Active parallel branch — closest adaptive-control prior art

**Status:** `IDENTITY RESOLVED / BOUNDED FULL-TEXT COMPARISON READY / NON-BLOCKING FOR EXP-001`<br>
**Identity record:** [CONTROL-PRIOR-ART-IDENTITY-01](literature_mapping/CONTROL-PRIOR-ART-IDENTITY-01.md)

Mandatory full-text targets:

1. 2025 JETTA consolidated article, DOI `10.1007/s10836-025-06183-5`;
2. 2023 IEEE DFT controller disclosure, DOI `10.1109/DFT59622.2023.10313560`;
3. 2024 IEEE LATS dynamic-fault-injection/evaluation branch, DOI `10.1109/LATS62223.2024.10534594`.

Required comparison fields:

- external radiation/current/future input and provenance;
- internal memory-state/history input;
- ECC-level reliability/risk assessment;
- observation/prediction uncertainty;
- action variable, available regimes and decision law;
- update timing/controller state;
- reliability constraint/guarantee;
- resource cost;
- test evidence, `W` and event-representation assumptions;
- validation, architecture and implementation;
- actual publication-family differences.

No discovery-level statement may become paper evidence or a novelty conclusion. The 2020/2022 prediction papers become additional deep-read targets only if the three-source comparison leaves a named upstream gap.

## Pending — future classical control prior-art threat

**Status:** `PENDING / NON-BLOCKING FOR RQ-002, RQ-006 AND EXP-001`<br>
**Trigger:** before any literature-level novelty claim for the integrated adaptive-control method.

Purpose: compare adaptive SRAM restoration with classical inspection/checking/maintenance scheduling, including the Barlow/Proschan/Keller line and relevant reliability/operations-research venues. Keep this task separate from radiation-test/event-representation mapping and do not launch it merely because the Chen identity is resolved.

## Active — own-result throughput gate

**Status:** `MODEL-SELECTION LITERATURE GATE PASSED / EXP-001 REGISTERED`

[DEC-003](decisions/DEC-003-rq002-bounded-model-family-and-exp001.md) selected a bounded comparison architecture rather than a universal stochastic family. [EXP-001](../experiments/EXP-001-event-representation-reduction-sensitivity.md) is the active own-work target.

Expected transition:

`DEC-003 → EXP-001 implementation/tests → fixed configs/seeds → aggregate comparison → Scientific Reviewer → first RES candidate`.

No second general RQ-002 literature cycle or automatic Paper Card batch is allowed. A new evidence task requires a named gap blocking:

- lossless reference construction;
- model adequacy/bounds;
- target validation;
- interpretation of the first own result.

The first `RES-xxx` should state a tested exactness/bound/error/decision-sensitivity result over a declared representation, mapping and parameter domain. It must not be a source summary.

## Future specialty and implementation alignment

**Status:** `PENDING / NOT AN EXP-001 SCOPE CHANGE`

Future major contributions must preserve the specialty 2.3.2 chain:

`physical/error model → reliability model → adaptive-control method → controller architecture → RTL implementation → hardware/resource/timing validation`.

RTL alone is not presumed novelty, but architecture/implementation cannot become an optional appendix after the adaptive method stabilizes.

## Publication trigger

**Status:** `PENDING / NON-BLOCKING`

After the first independently reviewed `RES-xxx`, evaluate whether the RQ-001 evidence basis + RQ-002/RQ-006 own result + validation supports an `ART` candidate. Do not start a paper from literature synthesis alone and do not wait for the entire dissertation if a bounded publishable result is already complete.
