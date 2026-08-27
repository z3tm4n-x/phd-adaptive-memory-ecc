# Novelty Assessment Workflow

**Status:** `CANONICAL PROCESS RULE`<br>
**Accepted:** 2026-08-27<br>
**Applies to:** every claim, synthesis or publication statement used to assess scientific novelty

## Purpose

Prevent a source-bounded observation from being promoted into a literature-level novelty claim without an explicit adversarial search for the most likely prior art that could invalidate it.

External-advisor statements may identify threats and search targets, but remain `UNVERIFIED` until checked against primary sources. They are not `SOURCE`, project evidence or research decisions by themselves.

## Intended-use gate

If a `CLM` or candidate claim has `Intended use` / `Used in = novelty assessment`, it cannot support a literature-level novelty statement until a separate adversarial gap-closure pass has been completed.

The pass must:

1. state the exact proposed novelty feature;
2. name the strongest known or likely novelty-destroying sources and search routes;
3. compare the feature paper by paper at the same abstraction, mapping, mechanism and validity-domain levels;
4. preserve `UNKNOWN` when full text or a decisive feature is unavailable;
5. record whether the searched evidence supports, narrows or defeats the proposed novelty;
6. undergo Orchestrator acceptance before use in an article, dissertation claim or contribution statement.

Using a claim in a novelty assessment does not widen its evidential scope. Scope must be preserved unchanged in every role handoff and downstream artefact unless a separately checked source supports the broader statement.

## RQ-002 mechanism-partition novelty protection gate

`CLM-002…006` remain valid only in their accepted scope over `PAPER-001…003`. They must not be used to assert that the literature generally fails to separate direct same-particle codeword errors from independent accumulation, that the project mechanism partition is novel, or that existing models necessarily double count.

Before any such literature-level statement, the adversarial pass must explicitly disposition at least:

- C32 — Clemente et al., 2022, DOI `10.1109/TNS.2022.3143652`;
- C51 — Franco et al., 2020;
- C52 — Franco et al., 2019;
- Zebrev et al., 2015, DOI `10.1016/j.nima.2014.11.106`;
- Zebrev et al., 2017, exact `arXiv:1704.07271v2`;
- the related peer-reviewed RADECS identity, DOI `10.1109/RADECS.2017.8696217`, treated as a separate version until content comparison;
- any additional source found by RQ-002 discovery that directly addresses this mechanism.

## Required novelty-threat matrix

| Column | Required comparison |
|---|---|
| Mechanism partition | direct same-particle versus sequential accumulation versus ambiguous/false multiple-event classification |
| Partition after mapping `W` | whether partition occurs after physical-cell-to-codeword mapping |
| Mechanism-specific quantities | separate cross sections, probabilities or rates |
| Non-overlap rule | explicit disjoint sample spaces or only an additive approximation |
| Beyond-small-parameter validity | validity outside any small-parameter/asymptotic regime |
| Joint inter-word dependence | retained, reduced, bounded or discarded |
| Observation/estimation layer | what is observable and how latent mechanisms are inferred |
| Control law/guarantee | whether adaptation and a verifiable guarantee are actually present |
| Domain of validity | device, radiation environment, architecture, mapping and operating regime |

## Acceptance rule

A novelty statement may be advanced only when:

- the matrix covers all mandatory threats or records a named blocking gap;
- version identities and peer-review status are controlled;
- comparisons use checked full text for decisive features;
- absence of evidence is not represented as evidence of absence;
- the final wording is no broader than the completed adversarial pass.

No permanent `CLM`, `DEC`, `HYP`, `RES` or novelty statement is created automatically by this workflow.

## Related pending task

The separate future control-layer prior-art threat is recorded in [`research_backlog.md`](research_backlog.md). It is not part of RQ-002 and does not block the RQ-002 Literature Scout cycle.
