# Research Backlog

This file records bounded future tasks that must not be mixed into the active RQ unless their trigger is reached. Entries are orchestration tasks, not accepted `RQ`, `HYP`, `DEC` or `RES` artefacts.

## Registered — RQ-006 mapping/information sufficiency

**Status:** `PROMOTED / ACTIVE WITH EXP-001`<br>
**Decision:** PI approved C-RQ-05 → [RQ-006](questions/RQ-006-physical-logical-mapping-information-sufficiency.md) on 2026-08-28.

The former escalation backlog item is resolved. RQ-006 owns `W`, interleaving, joint post-`W` impact and representation-reduction validity. RQ-002 retains arrival/event/state modelling and RQ-003 retains decoder-outcome semantics.

## Active parallel branch — Russian normative baseline

**Status:** `ACCEPTED WITH LIMITATION / PARTIAL — NAMED INPUT NEEDED`<br>
**Protocol:** [NORMATIVE-BASELINE-01](normative_baseline/NORMATIVE-BASELINE-01_protocol.md)
**Extraction:** [canonical matrix](normative_baseline/NORMATIVE-BASELINE-01_extraction_matrix.md)

Source set:

- РД 134-0174-2009;
- РД 134-0175-2009, supplied 2012 reissue with amendment 1;
- СТО ГК Роскосмос 04.01.0005–2022.

Purpose: reconstruct the information-retention chain from functional diagnosis and event classification through cross section, environment convolution, rate and probability, then determine which outputs are directly usable or require augmentation by `W`/ECC/observation assumptions.

The accepted extraction reconstructs the chain through classified counts, cross sections, sensitivity representation, environment convolution and scalar rate/probability. It does not infer normative deficiency and leaves named PMI/software/`W`/ECC interfaces open. The supplied STO file's controlled-revision status remains ambiguous because approval/registration statements coexist with hidden `Проект, окончательная редакция` text.

Exact PI follow-up material requested:

1. controlled-edition/registry evidence for STO 04.01.0005–2022;
2. ГОСТ РВ 0020–57.415–2020;
3. STO 04.01.0008–2024;
4. STO 04.01.0010–2025;
5. a representative SRAM private PMI or de-identified template and diagnostic/software output schema.

Do not launch a broad standards search. Request another source only when one matrix link remains unresolved.

## Accepted bounded branch — closest adaptive-control prior art

**Status:** `EVIDENCE AUDIT ACCEPTED / BOUNDED FAMILY ONLY`<br>
**Identity record:** [CONTROL-PRIOR-ART-IDENTITY-01](literature_mapping/CONTROL-PRIOR-ART-IDENTITY-01.md)
**Comparison:** [CONTROL-PRIOR-ART-01](evidence_synthesis/CONTROL-PRIOR-ART-01_comparison_matrix.md)
**Audit:** [CONTROL-PRIOR-ART-EVIDENCE-AUDIT-01](evidence_audits/CONTROL-PRIOR-ART_EVIDENCE_AUDIT_01.md)

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

`PAPER-009`/`PAPER-011` are accepted as CORE and `PAPER-010` as RELATED. The
bounded audit confirms genuine close prior art for fault-count/rate observation,
next-hour prediction or reactive assessment and adaptive restoration-frequency
selection. It does not establish literature-level novelty or non-novelty.

No additional Chen-family Paper Card is authorized now. The named gaps
`G-CHEN-OBS`, `G-CHEN-HW`, `G-CHEN-COST` and `G-CHEN-NUM` may trigger a single
bounded task only when an RQ-004/RQ-005/implementation decision depends on the
missing proposition.

## Pending bounded branch — domestic prior-art signals

**Status:** `BOUNDED CLOSURE DEFINED / PI GATE APPROVAL REQUIRED / NOT A BROAD SEARCH`<br>
**Protocol location:** [next quantitative gate](research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md)<br>
**Trigger:** PI approval of the gate, then identity-controlled verification before
the next quantitative EXP or any corresponding method distinction.

PI reported four potentially load-bearing domestic lines:

1. Meshchanov/Lushnikov/Krasnikov and co-authors — corrected-error counts,
   current-rate estimation and restoration-period adaptation;
2. Podzolko (2017) — ECC-uncorrectable-state probability, periodic background
   scanning and restoration-interval dependence under independent errors;
3. Boruzdina/Ulanova/Chumakov and related work — physical/logical multiple
   upsets, topology, accumulation, false grouping and event-form/multiplicity
   measurement or reconstruction;
4. Zebrev/Galimov and related work — recovery of multiplicity distributions or
   partial rates from reduced observations under additional assumptions.

None of these statements is accepted evidence until exact source identities and
the relevant primary text are checked. The bounded verification questions are:

- what information is observed, retained, reconstructed or assumed;
- whether the output is before or after physical-to-logical mapping `W`;
- what uncertainty/error or applicability domain is provided;
- whether the output is sufficient for DEC-001-compatible `F_A` and a restoration
  decision, rather than only for cross section, multiplicity or rate;
- which generic adaptive-scrubbing or reconstruction claims are already occupied.

This branch must not reopen EXP-001 or assert that complete physical topology is
always necessary. The gate limits it to four work units (`PA-DOM-01…04`), common
comparison columns and a hard stop after the required method boundaries are
controlled. A new source requires one named proposition blocking model-set
definition, physical plausibility, baseline reproduction, validity/bound
interpretation or an exact comparison used in the next EXP specification.

## Prepared candidate — integrated adaptive-control RQ

**Status:** `PREPARED / PROPOSED RQ-007 / NOT REGISTERED / PI ACCEPTANCE REQUIRED`<br>
**Inputs:** DEC-001; DEC-002; RQ-002…RQ-006; accepted Chen Evidence Audit<br>
**Candidate lineage:** integrates the former C-RQ-08, C-RQ-09 and C-RQ-11
control/action/optimization lines without consuming a permanent RQ identifier.

**Proposed question:**

> Как построить метод адаптивного выбора периода или режима восстановления
> ECC-защищённой SRAM, который по доступной online-информации формирует
> DEC-001-compatible оценку или множество допустимых значений
> `F_A(t0,T;μ_t0)`, явно распространяет неопределённость представления событий,
> `W`, модели и наблюдений, и выбирает реализуемое управляющее действие при
> заданном reliability constraint с отдельным измеримым resource-cost vector;
> при каких условиях выбранное действие является инвариантным или робастным к
> этой неопределённости?

The candidate consumes rather than duplicates:

- RQ-002 arrival/event/state representation;
- RQ-006 mapping and information-sufficiency/bound conditions;
- RQ-003 ECC capability/state/outcome semantics;
- RQ-004 observable information, latency and estimation uncertainty;
- RQ-005 measurable resource vector.

It excludes generic “radiation prediction → dynamic scrub frequency,” arbitrary
scalarization, an invented numerical reliability threshold, and a novelty claim.
Permanent registration is required before the next risk-to-action quantitative
execution because that work is control-method development. The gate draft does
not consume `RQ-007`; PI must explicitly accept its exact wording and ID.

## Pending — future classical control prior-art threat

**Status:** `PENDING / NON-BLOCKING FOR THE NEXT BOUNDED QUANTITATIVE GATE`<br>
**Trigger:** before any literature-level novelty claim for the integrated adaptive-control method.

Purpose: compare adaptive SRAM restoration with classical inspection/checking/maintenance scheduling, including the Barlow/Proschan/Keller line and relevant reliability/operations-research venues. Keep this task separate from radiation-test/event-representation mapping and do not launch it merely because the Chen identity is resolved.

## Active — post-RES-001 throughput gate

**Status:** `RES-001 REGISTERED / NEXT QUANTITATIVE GATE AWAITING PI APPROVAL`

[DEC-003](decisions/DEC-003-rq002-bounded-model-family-and-exp001.md) selected a bounded comparison architecture rather than a universal stochastic family. [EXP-001](../experiments/EXP-001-event-representation-reduction-sensitivity.md) is complete and promoted only within [RES-001](../results/RES-001-exp001-four-word-identified-set.md).

Current transition:

`DEC-003 → EXP-001 implementation → Scientific Review 01 REVISE → accepted independent-oracle repair → Scientific Review 02 PASS → PI ACCEPT → RES-001`.

No second general RQ-002 literature cycle or automatic Paper Card batch is allowed. A new evidence task requires a named gap blocking:

- lossless reference construction;
- model adequacy/bounds;
- target validation;
- interpretation of the first own result.

[`RES-001`](../results/RES-001-exp001-four-word-identified-set.md) states the
exact four-word identified set only with the complete validity domain accepted
by the Reviewer and PI. It separates representation uncertainty, Monte Carlo
uncertainty and confidence-rule conservatism and is not a source summary.

The prepared
[next quantitative gate](research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md)
maps available information `I` to an admissible model class `M(I)`, then to an
exact value/set/bound for `F_A`, admissible restoration actions, selected
`T_scrub` and resource cost. It must quantify controlled error, a safe-reduction
domain or the resource price of robust conservatism over physically defensible
`W`/topology/event/observation inputs rather than repeat the synthetic existence
discriminator.

No new experiment may start before PI approval of that gate, permanent
integrated-control RQ registration, completion of its four-unit prior-art stop
rule and preregistration of the experiment/derivation.

## Future specialty and implementation alignment

**Status:** `PENDING / NOT AN EXP-001 SCOPE CHANGE`

Future major contributions must preserve the specialty 2.3.2 chain:

`physical/error model → reliability model → adaptive-control method → controller architecture → RTL implementation → hardware/resource/timing validation`.

RTL alone is not presumed novelty, but architecture/implementation cannot become an optional appendix after the adaptive method stabilizes.

## Publication trigger

**Status:** `TRIGGER REACHED / NO ART LAUNCH AUTHORIZED`

The first independently reviewed result now exists. RES-001 is a narrow
foundational result and does not by itself establish the physically defensible
or integrated adaptive-control contribution targeted by the project. No ART is
launched at this gate. Re-evaluate after the next gate produces either a
physically bounded sufficiency/error result or a control-resource consequence;
do not wait for the entire dissertation if that package becomes independently
publishable.
