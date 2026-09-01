# Research Artefact Templates

These are **formatting templates**, not the normative source of lifecycle semantics. Lifecycle definitions and allowed meanings are defined in [`research_lifecycle.md`](research_lifecycle.md). New permanent artefacts should also use the minimal YAML metadata block defined there; existing untouched legacy artefacts do not require immediate migration. Templates may omit fields that are not applicable, but must not invent alternative meanings for controlled lifecycle/evidence terms.

## RQ — Research Question

```text
RQ-xxx
Title:
Question:
Why it matters:
Scope:
Exclusions:
Dependencies:
Lifecycle: OPEN | ANSWERED | CLOSED_NO_ANSWER | SUPERSEDED
Current activity / gate:
Evidence needed:
Answer / decision criterion:
Next action:
Related PAPER/CLM/HYP/EXP:
Answer:
Confidence:
Supersedes:
Superseded by:
```

## CLM — Claim

```text
CLM-xxx
Claim:
Type: SOURCE | INFERENCE | ASSUMPTION | OWN RESULT
Lifecycle: ACTIVE | SUPERSEDED | WITHDRAWN
Evidence assessment: SUPPORTED | PARTIALLY_SUPPORTED | DISPUTED | INSUFFICIENT | NOT_VERIFIED
Evidence:
Contrasting evidence:
Used in:
Last checked:
Supersedes:
Superseded by:
```

## HYP — Hypothesis

```text
HYP-xxx
Hypothesis:
Rationale:
Falsification criterion:
Required experiment(s):
Lifecycle: ACTIVE | SUPERSEDED | RETIRED
Assessment: UNTESTED | TESTING | SUPPORTED | REJECTED | INCONCLUSIVE
Related RQ:
Supersedes:
Superseded by:
```

## DEC — Research Decision

```text
DEC-xxx
Decision:
Date:
Lifecycle: ACTIVE | SUPERSEDED | REVOKED
Context:
Alternatives considered:
Rationale:
Evidence:
Consequences:
Revisit when:
Supersedes:
Superseded by:
```

## EXP — Experiment

```text
EXP-xxx
Objective:
Related RQ/HYP:
Authorization:
Code commit:
Configuration:
Input data / provenance:
Random seed(s):
Baselines:
Metrics:
Procedure:
Expected falsification/acceptance criterion:
Independent falsification path: YES | PARTIAL | NO | NOT_APPLICABLE
Independent falsification rationale:
Output locations:
Implementation: PLANNED | IMPLEMENTED | INVALIDATED
Reproduction: NOT_RUN | REPRODUCED | MISMATCH | NOT_APPLICABLE
Independent validation: NOT_RUN | PARTIAL | PASS | FAIL | NOT_APPLICABLE
Scientific review: NOT_REVIEWED | PASS | PASS_WITH_MINOR | REVISE | BLOCK
Promotion: NOT_ELIGIBLE | RES_ELIGIBLE | PROMOTED
```

## RES — Result

```text
RES-xxx
Lifecycle: ACCEPTED | SUPERSEDED | INVALIDATED
Maximum admissible statement:
Derived from:
Code / derivation provenance:
Scientific review / disposition:
Evidence / statistics:
Validity domain:
Explicit non-claims / forbidden generalizations:
Evidence dependencies:
Relevant uncertainty classes:
Revisit / invalidation conditions:
Used in ART / thesis:
Supersedes:
Superseded by:
```
