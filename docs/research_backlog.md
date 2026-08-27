# Research Backlog

This file records bounded future tasks that must not be mixed into the active RQ unless their trigger is reached. Entries are orchestration tasks, not accepted `RQ`, `HYP`, `DEC` or `RES` artefacts.

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

**Status:** `PENDING / ACTIVATES WHEN THE INITIAL RQ-002 MAPPING IS ACCEPTED`

Before authorizing another broad RQ-002 literature cycle, the Orchestrator must decide:

1. which 2–5 sources are decisive for selecting or rejecting competing error-model classes;
2. which bounded model alternatives remain, such as HPP, NHPP, compound/marked, Cox or another evidence-supported class;
3. which minimal quantitative prototype can be built directly from RQ-002 results;
4. which first computational experiment can discriminate between the remaining models or test a validity domain;
5. which verifiable own result should become the first `RES-xxx`.

Expected transition:

`literature mapping → decisive deep reads → model-selection decision / bounded alternatives → computational prototype → EXP-xxx → RES-xxx`.

A new discovery/deep-read cycle is allowed only for a named evidence gap that blocks model selection, adequacy, validation or the first own-result experiment. Unread `CORE` papers alone are not a reason to continue searching.

## Future specialty and implementation alignment

**Status:** `PENDING / NOT AN RQ-002 SCOPE CHANGE`

Future major contributions must preserve the specialty 2.3.2 chain:

`physical/error model → reliability model → adaptive-control method → controller architecture → RTL implementation → hardware/resource/timing validation`.

RTL alone is not presumed to be scientific novelty. Controller architecture and implementation are nevertheless required to demonstrate computational-system relevance and hardware feasibility rather than becoming optional appendices.

## Publication trigger

**Status:** `PENDING / NON-BLOCKING`

Do not open a standalone publication solely from the RQ-001 literature synthesis. After the first independent `RES-xxx`, evaluate whether the combination of the RQ-001 evidence basis, an RQ-002 own model/result and validation is sufficient to register the first `ART` candidate. Do not wait for the entire dissertation if that traceable package is already complete.
