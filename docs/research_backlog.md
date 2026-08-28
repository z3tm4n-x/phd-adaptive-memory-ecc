# Research Backlog

This file records bounded future tasks that must not be mixed into the active RQ unless their trigger is reached. Entries are orchestration tasks, not accepted `RQ`, `HYP`, `DEC` or `RES` artefacts.

## Awaiting PI decision — promote C-RQ-05

**Status:** `PROPOSED / NOT REGISTERED`<br>
**Recommended mapping:** C-RQ-05 → `RQ-006`<br>
**Trigger:** full-text RQ-002 synthesis confirmed that topology, interleaving and physical-to-logical mapping cannot be excluded or safely reduced without an explicit validity argument.

Proposed Research Question:

> Какое минимальное представление физической топологии радиационного события и отображения памяти `W` необходимо сохранять, чтобы корректно преобразовывать события в совместное воздействие на ECC-кодовые слова и вычислять `E_cap`; при каких условиях редуцированное представление или исключение interleaving является точным, даёт проверяемую границу либо приемлемую аппроксимацию?

Proposed boundary:

- RQ-002 selects or bounds the stochastic arrival/event/state representation;
- proposed RQ-006 owns physical-cell → codeword mapping, interleaving, joint post-`W` impact and reduction-validity conditions;
- RQ-003 retains ECC capability and decoder-outcome semantics;
- no permanent ID or answer is created until explicit PI acceptance.

## Waiting for PI material — Russian normative baseline

**Status:** `WAITING FOR EXACT DOCUMENTS / PRIMARY BASELINE`<br>
**Trigger:** PI provides the applicable exact editions/files, initially РД 134-0175-2009 and РД 134-0174-2009<br>
**Purpose:** reconstruct the existing normative chain from irradiation evidence to probability indicator and test its interface with ECC-aware reliability and adaptive control without presuming a deficiency.

Required extraction fields:

- normative scope, object and applicability conditions;
- primitive test observation and experimental quantity;
- cross-section definition, units and aggregation;
- radiation-environment convolution and rate definition;
- probability/reliability indicator and horizon;
- retained multiplicity, topology, parent-event and uncertainty information;
- treatment of memory organization, ECC, interleaving, scrubbing and initial state;
- required input provenance and validation;
- exact information available to the downstream ECC/reliability/control layers;
- compatible use, required augmentation and genuine incompatibility with DEC-001/DEC-002.

Expected output: a bounded normative-baseline matrix and traceable list of assumptions/gaps. No normative-deficiency or novelty claim is permitted before the document set is examined.

## Pending — closest adaptive-control prior art

**Status:** `PENDING / BOUNDED / MAY RUN IN PARALLEL WITH THE RQ-002 PROTOTYPE`<br>
**Trigger:** exact Chen/IHP/Potsdam source identity and full text are available; mandatory before an adaptive-control novelty claim<br>
**Purpose:** determine what is already disclosed by the closest radiation-variation/prediction → adaptive scrub-frequency work and which distinctions remain load-bearing for the integrated method.

Required comparison fields:

- radiation/current/future input and provenance;
- internal memory-state/history input;
- ECC-level reliability or risk model;
- observation/estimation uncertainty;
- controlled variable and available restoration regimes;
- decision law, update timing and state;
- reliability constraint or guarantee;
- resource-cost treatment;
- radiation-test traceability and `W`/event-representation assumptions;
- validation, controller architecture and implementation evidence;
- effect, if any, of information reduction on the decision.

Expected output: one bounded closest-prior-art card/matrix. Do not broaden automatically into general control literature.

## Pending — future control prior-art threat

**Status:** `PENDING / NON-BLOCKING FOR RQ-002`<br>
**Trigger:** before any literature-level novelty claim for the future adaptive-control layer<br>
**Purpose:** determine how adaptive SRAM scrubbing differs from classical inspection, checking and maintenance scheduling.

Bounded search concepts:

- inspection scheduling;
- optimal checking schedules;
- checking policy;
- inspection density;
- maintenance optimization;
- minimax inspection;
- adaptive maintenance;
- condition-based maintenance;
- partially observed maintenance/control.

Mandatory prior-art line and venues:

- classical Barlow / Proschan / Keller line;
- `Management Science`;
- `Operations Research`;
- `IEEE Transactions on Reliability`;
- `Reliability Engineering & System Safety`;
- `European Journal of Operational Research`.

Expected output: a bounded control-prior-art matrix comparing state/observation assumptions, inspection or maintenance action, objective/constraint, adaptation mechanism, guarantee, and domain with the future SRAM controller formulation. This task must remain separate from RQ-002 radiation/error-model mapping.

## Gate after RQ-002 mapping — own-result throughput

**Status:** `ACTIVE — INITIAL MAPPING, DECISIVE DEEP READS AND CROSS-PAPER SYNTHESIS ACCEPTED`

Before authorizing another broad RQ-002 literature cycle, the Orchestrator must decide:

1. which 2–5 sources are decisive for selecting or rejecting competing error-model classes;
2. which bounded model alternatives remain, such as HPP, NHPP, compound/marked, Cox or another evidence-supported class;
3. which minimal quantitative prototype can be built directly from RQ-002 results;
4. which first computational experiment can discriminate between the remaining models or test a validity domain;
5. which verifiable own result should become the first `RES-xxx`.

Expected transition:

`literature mapping → decisive deep reads → model-selection decision / bounded alternatives → computational prototype → EXP-xxx → RES-xxx`.

A new discovery/deep-read cycle is allowed only for a named evidence gap that blocks model selection, adequacy, validation or the first own-result experiment. Unread `CORE` papers alone are not a reason to continue searching.

Current bounded target after `PAPER-004…008`:

- audit only the synthesis propositions that will carry model selection;
- retain a small alternative set for arrival process, post-`W` event mark, accumulation state, repair and observation error;
- compare representation levels under common `W`, ECC and scrub semantics;
- quantify their effect on `F_A(t0,T; μ_t0)` and a parameterized adaptive restoration decision;
- define `EXP-001` only after the model alternatives, inputs and falsifiable comparison metric are explicit.

## Future specialty and implementation alignment

**Status:** `PENDING / NOT AN RQ-002 SCOPE CHANGE`

Future major contributions must preserve the specialty 2.3.2 chain:

`physical/error model → reliability model → adaptive-control method → controller architecture → RTL implementation → hardware/resource/timing validation`.

RTL alone is not presumed to be scientific novelty. Controller architecture and implementation are nevertheless required to demonstrate computational-system relevance and hardware feasibility rather than becoming optional appendices.

## Publication trigger

**Status:** `PENDING / NON-BLOCKING`

Do not open a standalone publication solely from the RQ-001 literature synthesis. After the first independent `RES-xxx`, evaluate whether the combination of the RQ-001 evidence basis, an RQ-002 own model/result and validation is sufficient to register the first `ART` candidate. Do not wait for the entire dissertation if that traceable package is already complete.
