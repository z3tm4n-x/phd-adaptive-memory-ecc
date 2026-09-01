# Research Artefact Lifecycle

This document defines the normative lifecycle semantics of permanent research artefacts. It defines **how state is represented**, not the scientific state of any particular current artefact.

Formatting examples live in [`artefact_templates.md`](artefact_templates.md). Current project state lives in object-specific canonical artefacts plus [`current_status.md`](current_status.md).

## 1. Core rules

1. **Lifecycle and scientific/evidence assessment are different dimensions.** Do not overload one `Status` field to mean both.
2. **Object-specific state belongs to the object.** `current_status.md` summarizes project state but does not override an accepted RQ, DEC, EXP disposition, scientific review, or RES.
3. **Historical execution provenance is not current lifecycle state.** A run manifest records what was executed; later validation, review, and promotion are separate records.
4. **Reproducibility is not independent validation.** A reproduced run can still lack an independent falsification path.
5. **Review is not promotion.** `PASS` or `PASS_WITH_MINOR` may make a result eligible for promotion, but does not itself create a `RES-xxx`.
6. **No generic newer-wins rule.** Replacement of an accepted artefact requires an explicit `Supersedes` / `Superseded by` relation or a separate accepted disposition/decision.
7. **Candidates are not permanent artefacts.** Draft/candidate objects do not acquire permanent epistemic status merely because they exist in Git.

## 2. Research Question (`RQ`)

The RQ lifecycle describes whether the question remains part of the active research contract; activity/gate details belong in `current_status.md` or the RQ body.

- `OPEN` — registered question not yet closed.
- `ANSWERED` — answer criterion has been met and an accepted answer/disposition exists.
- `CLOSED_NO_ANSWER` — intentionally closed without an accepted answer.
- `SUPERSEDED` — replaced by an explicitly related RQ/decision.

Terms such as `ACTIVE`, `QUEUED`, `OPEN DEPENDENCIES`, or a named gate are orchestration qualifiers, not replacements for the RQ lifecycle state.

## 3. Claim (`CLM`)

A claim has two separate dimensions.

**Artefact lifecycle:**

- `ACTIVE`
- `SUPERSEDED`
- `WITHDRAWN`

**Evidence assessment:**

- `SUPPORTED`
- `PARTIALLY_SUPPORTED`
- `DISPUTED`
- `INSUFFICIENT`
- `NOT_VERIFIED`

`WITHDRAWN` or `SUPERSEDED` describes project use of the claim; it does not mean the underlying proposition was scientifically refuted.

## 4. Hypothesis (`HYP`)

A permanent hypothesis is registered only through the authorized workflow. Its project lifecycle and test assessment should not be collapsed into one field.

**Lifecycle:** `ACTIVE | SUPERSEDED | RETIRED`

**Assessment:** `UNTESTED | TESTING | SUPPORTED | REJECTED | INCONCLUSIVE`

A result produced before a hypothesis was registered must not be retroactively relabelled as a prospective hypothesis test.

## 5. Research Decision (`DEC`)

**Lifecycle:** `ACTIVE | SUPERSEDED | REVOKED`

A later decision does not silently replace an earlier accepted decision. Supersession/revocation must be explicit and traceable, with rationale and revisit conditions.

## 6. Experiment (`EXP`)

A nontrivial experiment uses independent lifecycle axes. One compound free-text status may be shown for readability, but it must not erase these distinctions.

### 6.1 Implementation

`PLANNED | IMPLEMENTED | INVALIDATED`

Describes whether the declared experiment has a usable implementation. `INVALIDATED` means the implementation/experiment definition cannot support its intended interpretation without a new disposition.

### 6.2 Reproduction

`NOT_RUN | REPRODUCED | MISMATCH | NOT_APPLICABLE`

Describes whether the declared run/result can be reproduced under the recorded execution contract.

### 6.3 Independent validation

`NOT_RUN | PARTIAL | PASS | FAIL | NOT_APPLICABLE`

Describes whether an independent path capable of falsifying relevant implementation failures has been exercised. Independence is relative to the stated failure class and must be explained; shared production helpers must not be presented as independent merely because two entry points agree.

For a nontrivial computational EXP, record an **Independent falsification path** as `YES | PARTIAL | NO | NOT_APPLICABLE` with a short rationale. `NO` is not automatically invalid, but it must be visible before scientific review.

### 6.4 Scientific review

`NOT_REVIEWED | PASS | PASS_WITH_MINOR | REVISE | BLOCK`

This is the accepted Scientific Reviewer recommendation for the relevant reviewed state. Earlier review records remain historical provenance; a later re-review closes or supersedes findings through an explicit review/disposition rather than rewriting the earlier record.

### 6.5 Promotion

`NOT_ELIGIBLE | RES_ELIGIBLE | PROMOTED`

- `NOT_ELIGIBLE` — no accepted basis for promotion.
- `RES_ELIGIBLE` — scientific review/disposition permits a bounded result proposal.
- `PROMOTED` — an accepted `RES-xxx` explicitly records the promoted result.

`PASS` / `PASS_WITH_MINOR` does not automatically imply `PROMOTED`.

## 7. Scientific Review

A scientific review is an accepted review record over a declared target and reviewed state/commit. Its recommendation is:

`PASS | PASS_WITH_MINOR | REVISE | BLOCK`

A review should identify its target, reviewed commit/state, findings, and relationship to earlier reviews when applicable. Review records are provenance and are not rewritten merely because a later review reaches a different recommendation.

## 8. Result (`RES`)

A permanent result exists only after explicit authorized promotion.

**Lifecycle:** `ACCEPTED | SUPERSEDED | INVALIDATED`

Every `RES` must remain bounded by its provenance. At minimum it should make clear:

- maximum admissible result statement;
- source experiment/derivation/verified analysis;
- scientific review/disposition;
- validity domain;
- explicit non-claims / forbidden generalizations;
- evidence dependencies;
- relevant uncertainty classes when they materially affect interpretation;
- revisit or invalidation conditions.

A later broader result does not silently widen an earlier `RES`; it requires its own accepted artefact or explicit supersession.

## 9. Paper Cards and external literature

The existing Paper Card gate remains:

`Cxx → full-text analysis → DRAFT Paper Card → Orchestrator acceptance → PAPER-xxx`.

Acceptance of a Paper Card means the analysis is accepted for project use; it does not automatically adopt every assumption or conclusion of the source as a project claim.

## 10. Transition discipline

Lifecycle transitions are recorded only by the role/PI authority defined by the active workflow. Infrastructure, templates, validators, or future procedural skills may detect inconsistencies or check transition preconditions, but they do not themselves promote, reject, supersede, or scientifically reinterpret artefacts.

## 11. Minimal machine-readable metadata

New permanent artefacts should begin with a small YAML front-matter block so repository checks can read identity, relations, and controlled lifecycle fields without parsing arbitrary prose. Existing untouched artefacts are legacy-compatible and do **not** require immediate migration. When a permanent artefact is materially revised, adding metadata is expected when practical.

Metadata v1 deliberately uses only a small YAML-compatible subset: top-level `key: scalar` fields and top-level scalar lists. Nested mappings, anchors, tags, multiline scalar syntax, and other general YAML features are outside v1; keep structured scientific detail in the Markdown body rather than expanding the metadata grammar.

Metadata **mirrors an already authorized state; it does not create that state**. A validator or editor must not change scientific disposition merely to make metadata pass. If metadata conflicts with the accepted body/disposition, surface the inconsistency for the responsible role rather than applying a generic precedence rule.

Common minimum form:

```yaml
---
schema_version: 1
artifact_type: EXP
id: EXP-xxx
related:
  - RQ-xxx
supersedes: []
superseded_by: []
---
```

Use only fields applicable to the artefact type. Empty relationship lists are permitted. `related` is traceability, not authority or supersession.

For an `EXP`, the machine-readable block should carry the controlled axes when they are known:

```yaml
implementation: IMPLEMENTED
reproduction: REPRODUCED
independent_validation: PASS
independent_falsification: YES
scientific_review: PASS
promotion: RES_ELIGIBLE
```

For a `RES`, it should at minimum identify lifecycle and provenance links, for example:

```yaml
lifecycle: ACCEPTED
derived_from:
  - EXP-xxx
scientific_review:
  - EXP-xxx-SCIENTIFIC-REVIEW-yy
```

Long scientific statements, validity domains, evidence reasoning, review findings, and limitations remain in human-readable Markdown. Metadata is intentionally small and should not become a second research database.
