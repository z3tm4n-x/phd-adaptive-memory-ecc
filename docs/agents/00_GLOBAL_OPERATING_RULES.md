# Global Operating Rules for AI Agents

## 1. Purpose

These rules govern all AI roles used in the dissertation research project. Role-specific instructions in this directory supplement this file; they do not override it unless explicitly stated.

## 2. Canonical sources of truth

1. **External literature identity, metadata, PDFs, notes, and bibliography:** Zotero.
2. **Own research state, decisions, RQ/HYP/DEC/EXP/RES artefacts, code, experiment definitions, approved results, RTL, and provenance:** this GitHub repository.
3. **Current orchestration state:** `docs/current_status.md`, `docs/research_spec.md`, and open GitHub Issues.
4. **Scientific evidence:** primary scientific sources, with Scite used as an evidence/citation-context layer where appropriate.
5. **Chat messages:** temporary working context only. A statement existing only in chat is not a canonical research result.

When chat history conflicts with canonical GitHub state, agents must surface the conflict and prefer the canonical state unless the user explicitly updates it.

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

## 10. Completion discipline

For substantial tasks, report:

1. conclusion/output;
2. basis/evidence;
3. confidence or uncertainty;
4. unresolved questions;
5. next recommended action;
6. what must be saved outside chat.

The primary optimization criterion is reduction of scientific uncertainty with reproducible, traceable outputs — not number of papers, pages, commits, or generated text.
