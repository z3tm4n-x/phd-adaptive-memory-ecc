# Specialized Handoff Contracts

This file supplements the standard handoff format in `00_GLOBAL_OPERATING_RULES.md` for recurring role-to-role transitions. It defines the **minimum information that must cross the boundary**; it does not change role authority, scientific state, or acceptance rules.

Do not duplicate these contracts across role cards. Role-specific instructions may add task-specific requirements, but conflicting local copies must not be created.

## ORCHESTRATOR → research roles — scientific purpose of the next task

For each new research handoff, state briefly:

- **Dissertation contribution:** which numbered task in the agreed research
  passport (`docs/dissertation_concept.md`) and which major proposition or
  scientific assertion will become stronger or be completed; distinguish a
  supporting feasibility check from a new fundamental result.
- **Decision and practical purpose:** what concrete choice the output enables,
  why it matters for the target application, and which input gap currently prevents it.
- **Expected evidence:** the verifiable derivation, data requirement, bound,
  comparison or implementation evidence that changes that choice.
- **Completion and next disposition:** what ends the task for a positive,
  negative or unresolved result, including the decision about stopping, changing
  the approach or requesting a specific missing input.

Use the [dissertation concept and research program](../dissertation_concept.md) and DEC-004
for this connection. Integrate these fields into the existing handoff; do not
create a separate artefact merely to repeat them. A local repair can be necessary,
but its role in the larger result must be explicit. These requirements do not
silently amend already accepted in-flight tasks or authorize their execution.

## LS → PA — Literature Scout to Paper Analyst

Required minimum:

- candidate identity (`Cxx` or exact bibliographic identity);
- related `RQ` and concrete evidence gap/question;
- title / authors / year / DOI or other stable source identity;
- screening class and why the source was selected;
- full-text status and accessible location/source;
- exact extraction questions for the Paper Analyst;
- known scope/access limitations;
- explicit prohibited inference where relevant (for example, abstract-only material must not be treated as a full-paper conclusion).

The handoff does not create a permanent `PAPER-xxx` or accepted claim.

## PA → EA — Paper Analyst to Evidence Auditor

Required minimum:

- candidate/Paper Card identity and related `RQ`;
- one or more **atomic** propositions proposed for audit;
- whether each proposition is `SOURCE-CANDIDATE` or `INFERENCE-CANDIDATE`;
- exact source provenance, including pages/sections/equations when available;
- system/population/model scope and material assumptions;
- strongest limiting or contrasting evidence already visible in the source;
- unresolved ambiguity or missing full-text material that can affect the audit.

The handoff does not assign `CLM-xxx`, `EVD-xxx`, or an evidence assessment.

## RE → SR — Research Engineer to Scientific Reviewer

Required minimum:

- task ID and related `EXP/RQ/DEC`;
- canonical base and implementation/repair commit SHA;
- configuration identities and input-data provenance;
- exact reproduction/test commands and relevant tool/environment versions;
- reproduction result;
- independent-validation status and independent falsification path;
- known shared code/helpers or other common-mode failure paths;
- tests/oracles/mutation or sentinel checks used where applicable;
- output locations and hashes/identities of reviewed outputs where material;
- deviations, failed checks, known limitations, and expected falsification criterion.

A successful engineering handoff establishes technical provenance only. It does not assign Scientific Review `PASS` or promote an `EXP` to `RES`.

## SR → ORCHESTRATOR — Scientific Reviewer to Research Orchestrator

Required minimum:

- review target and exact reviewed commit/state;
- related `EXP/RES/RQ/CLM` as applicable;
- recommendation: `PASS | PASS_WITH_MINOR | REVISE | BLOCK`;
- findings grouped by severity with required corrective action for `CRITICAL/MAJOR`;
- disposition of earlier findings when this is a re-review;
- residual risks and unresolved scientific boundaries;
- maximum admissible wording or explicit statement that none is yet admissible;
- validity domain / conditions that must accompany any accepted wording;
- whether bounded result promotion is scientifically eligible, without performing that promotion.

The Orchestrator/PI retains authority over canonical disposition and promotion.
