# Global Operating Rules for AI Agents

## 1. Purpose

These rules govern all AI roles used in the dissertation research project. Role-specific instructions in this directory supplement this file; they do not override it unless explicitly stated.

## 2. Canonical sources and authority by information type

Canonical authority is determined by **what information is being asserted**, not by one global document hierarchy.

- **External literature identity, metadata, PDFs, notes, and bibliography:** Zotero.
- **A specific research object's accepted scientific content or disposition:** that object's own accepted canonical artefact and any explicit accepted disposition/review that governs it (`RQ`, `DEC`, `CLM`, `EXP`, `RES`, etc.).
- **Current project phase, active gate, and cross-object summary:** `docs/current_status.md`. It is a summary of canonical state; it does not override object-specific accepted artefacts.
- **Integrated working research contract:** `docs/research_spec.md`. It coordinates the project but does not silently supersede an accepted object-specific artefact.
- **What was actually executed in a particular experiment run:** the corresponding run manifest and recorded code/config/input provenance. Execution provenance is historical; it must not be repurposed as the current lifecycle status of the experiment.
- **Task ownership, coordination, and bounded work requests:** GitHub Issues and explicit handoffs.
- **Historical project context:** `docs/research_log.md`.
- **Scientific evidence:** checked primary scientific sources, with Scite used as an evidence/citation-context layer where appropriate.
- **Chat messages:** temporary working context only. A statement existing only in chat is not a canonical research result.

When chat history conflicts with canonical GitHub state, agents must surface the conflict and prefer canonical state unless the user explicitly updates it.

When a summary file conflicts with an accepted object-specific artefact, agents must surface the inconsistency; the object-specific artefact governs that object's scientific content until an authorized correction or disposition is recorded.

Two accepted scientific artefacts must **not** be resolved by a generic "newer file wins" rule. Replacement requires an explicit `Supersedes` / `Superseded by` relation or a separate accepted decision/disposition that explains the relationship. Historical artefacts remain part of provenance.

A run manifest is authoritative for the execution it records, not for later review or promotion state. Later review, repair, or promotion must be recorded in their own artefacts/dispositions rather than by reinterpreting historical execution facts.

An in-flight agent task remains bound to the explicit handoff, canonical base, and role rules under which it was issued. Later governance changes do not silently rewrite an active task; if they materially affect it, the task must be explicitly reissued, rebased, or amended.

Lifecycle semantics for research artefacts are defined in [`docs/research_lifecycle.md`](../research_lifecycle.md).

## 3. Tool access boundaries

### Cloud ChatGPT Work

- GitHub: direct connector access when authorized.
- Scite: direct connector access when authorized.
- Web/public academic sources: available when appropriate.
- Zotero Desktop local library: **no direct cloud access**.
- Local repository, Python environment, COSRAD, SystemVerilog/iVerilog, Vivado, and local datasets: no direct cloud filesystem/tool access unless a local execution environment is explicitly being used.

### Local Codex / local research environment

Intended for:
- local Git repository operations;
- Zotero Desktop through the local Zotero API;
- Python/Jupyter modelling and simulation;
- COSRAD processing;
- SystemVerilog/iVerilog;
- Vivado;
- local and large datasets.

## 4. Zotero handoff rule

Zotero is the master literature library, but cloud agents must not pretend they can directly inspect or modify Zotero Desktop.

When a Zotero operation is needed, create a structured `HANDOFF TO ZOTERO` containing:

- action;
- target collection;
- DOI/title/other record identity;
- required tags;
- duplicate policy;
- metadata checks;
- PDF/attachment expectations;
- expected result.

The user/local agent returns a `ZOTERO HANDOFF RESULT`.

`literature/zotero_exports/references.bib` may be used as a cloud-visible snapshot, but it is not the Zotero master database.

## 5. Evidence discipline

Always distinguish:

- `SOURCE` — directly supported by a checked source;
- `INFERENCE` — interpretation derived from evidence;
- `ASSUMPTION` — working assumption;
- `OWN RESULT` — result produced by this research with traceable provenance;
- `UNKNOWN` — unresolved.

Never fabricate papers, DOI, authors, data, quotations, formulae, experimental results, or tool outputs.

Do not turn plausibility into evidence. Do not treat citation counts as proof.

## 6. Research artefact IDs

Use stable identifiers after acceptance:

- `RQ-xxx` — Research Question
- `PAPER-xxx` — Publication analysis card
- `CLM-xxx` — Claim
- `EVD-xxx` — Evidence record
- `HYP-xxx` — Hypothesis
- `DEC-xxx` — Research decision
- `EXP-xxx` — Experiment
- `RES-xxx` — Research result
- `FIG-xxx` — Figure
- `ART-xxx` — Publication/article

Candidate Research Questions must use temporary `C-RQ-xx` identifiers until accepted. Do not consume permanent IDs for disposable candidates.

### Paper Card lifecycle

Literature Scout candidate IDs such as `C38` identify discovery records; they are not permanent Paper IDs.

The normal lifecycle is:

`Cxx → full-text analysis → DRAFT Paper Card → Orchestrator acceptance → PAPER-xxx`.

Paper Analyst must not assign a permanent `PAPER-xxx` identifier. A draft Paper Card is an analytical artefact, not accepted evidence. Candidate statements inside a draft card remain candidate claims until they are explicitly accepted for Evidence Auditor review.

No agent may silently upgrade a candidate RQ, Paper Card, Claim, Evidence record, Hypothesis, Decision, or Result to accepted canonical state outside the active workflow.

## 7. GitHub write policy

Agents may read canonical state whenever needed.

Agents may propose changes freely.

Write to GitHub only when:
- the user explicitly requests the write; or
- the active task explicitly includes recording the accepted result.

Do not silently convert suggestions into `DEC`, `HYP`, `RQ`, or `RES` records.

A `RES-xxx` may only represent a traceable result backed by an experiment, derivation, or verified analysis.

## 8. Scientific decision policy

Before recording a material scientific decision, state:

- what is known;
- what is assumed;
- what remains unknown;
- alternatives considered;
- what evidence or constraint motivated the decision;
- when the decision should be revisited.

If the evidence is insufficient, record the uncertainty rather than forcing a choice.

## 9. Standard handoff format

```text
HANDOFF

From:
To:
Task ID:
Related RQ:

Context:

Canonical sources:

Known:

Assumed:

Unknown:

Required action:

Expected output:

Do not:

Where result belongs:
GitHub / Zotero / Scite / local files / chat only
```

Handoffs should transfer structured state, not long chat transcripts.

For recurring specialized transitions, the minimum boundary-specific fields are centralized in [`HANDOFF_CONTRACTS.md`](HANDOFF_CONTRACTS.md). Those contracts supplement this base format and must not be copied into multiple role cards; task-specific handoffs may add requirements without changing role authority.

## 10. Artefact proportionality rule

Do not create a research artefact merely because a template exists.

Before requesting or creating an artefact, ask:

1. Will it close a defined evidence gap?
2. Will it change or enable a research decision?
3. Is it required for reproducibility or traceability?

If the answer to all three is no, do not create the artefact.

The depth of documentation must be proportional to scientific importance. Typical default:

- `CORE` source selected for evidence extraction → full Paper Card;
- `RELATED` source → targeted extraction only when needed;
- `BACKGROUND` source → Zotero metadata/notes are normally sufficient;
- `REJECT` → screening record only.

Do not optimize for number of artefacts, papers, pages, commits, or generated text.

## 11. Completion discipline

For substantial tasks, report:

1. conclusion/output;
2. basis/evidence;
3. confidence or uncertainty;
4. unresolved questions;
5. next recommended action;
6. what must be saved outside chat.

The primary optimization criterion is reduction of scientific uncertainty with reproducible, traceable outputs — not number of papers, pages, commits, or generated text.
