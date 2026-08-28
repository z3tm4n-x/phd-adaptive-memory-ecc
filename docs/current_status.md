# Current Status

**Updated:** 2026-08-28

## Current phase

First own quantitative prototype: implementation and validation of `EXP-001` while bounded normative and close-prior-art extractions run in parallel.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.5-draft`.

## Active scientific gate

Implement the DEC-003 event-representation ladder under common `A/W/ECC/initial-state/scrub` semantics and determine whether full physical topology, joint post-`W` marks, marginal word statistics and the Phase-1 scalar upset-arrival comparator produce equivalent, bounded or decision-changing `F_A` estimates.

The gate output is a reproducible `EXP-001` run suitable for adversarial Scientific Reviewer inspection. No second general RQ-002 literature cycle is authorized without a named gap that blocks model adequacy, validation or interpretation.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / EVIDENCE AUDIT ACCEPTED / PROTOTYPE GATE`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`; retains decoder-outcome semantics.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`; must distinguish external exposure from internal memory-state/history information.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.
- RQ-006 — physical-to-logical mapping and information sufficiency — `OPEN / REGISTERED / PROTOTYPE-COUPLED`.
- An integrated adaptive-control RQ remains required after RQ-002/RQ-006 prototype results and RQ-003…RQ-005 interfaces are bounded. It must preserve the SOURCE objective rather than become a dynamic-input-only question.

## Controlling decisions

- [DEC-001](decisions/DEC-001-rq001-reliability-contract.md) remains unchanged: `E_cap` is ECC capability exceedance, general metric is `F_A(t0,T;μ_t0)`, `A` is declared/partitioned, horizons remain distinct, and `H_req/ε_req` remain `TBD`.
- [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md) keeps one causal architecture from radiation-test evidence through `W` and ECC reliability to an actual adaptive restoration decision.
- [DEC-003](decisions/DEC-003-rq002-bounded-model-family-and-exp001.md) accepts the bounded RQ-002 evidence constraints, retains an event-driven comparison reference and authorizes the representation-reduction experiment without selecting a universal process family.

## Orchestrator review dispositions

### RQ-002 Evidence Audit 01

[Accepted with limitation](evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md):

- candidates 01–03 and 05–10 are accepted only in their precise scoped wording;
- candidate 04 is partially supported: marginal per-word sufficiency cannot be presumed, but universal insufficiency is not established;
- no permanent `CLM`/`EVD` was created;
- no additional Paper Card is required before EXP-001.

### Chen/IHP/Potsdam identity report

[Accepted as identity/discovery only](literature_mapping/CONTROL-PRIOR-ART-IDENTITY-01.md):

- the publication family and DOI/version chain are resolved;
- the 2025 JETTA paper is the consolidated target;
- the 2023 DFT controller disclosure and 2024 LATS evaluation branch remain separate mandatory full-text comparators;
- discovery-level feature statements are not paper evidence or novelty conclusions.

## RQ-006 registration

PI approval permanently promoted C-RQ-05 → [RQ-006](questions/RQ-006-physical-logical-mapping-information-sufficiency.md). RQ-006 owns physical topology, `W`, interleaving, joint post-`W` impact and the exactness/bound/error of representation reduction. RQ-002 continues to own arrival/event/state and restoration-process representation; RQ-003 retains ECC/decoder outcomes.

## Russian normative baseline

The bounded [NORMATIVE-BASELINE-01 protocol](normative_baseline/NORMATIVE-BASELINE-01_protocol.md) covers:

- `РД 134-0174-2009` — calculation from experimental cross sections and space-environment spectra to rate/probability;
- `РД 134-0175-2009` — digital VLSI irradiation testing and event/cross-section processing; supplied copy states a 2012 reissue with amendment 1;
- `СТО ГК Роскосмос 04.01.0005–2022` — integrated modern test-method framework including SEU/MBU/MCU/SMU and PMI/software-dependent identification.

The STO identity and practical listing are corroborated, but the supplied file's exact controlled revision is `AMBIGUOUS`: it contains approval/registration/effective-date statements and also repeated hidden white-text `Проект, окончательная редакция` markers. No stronger edition or compliance claim is accepted.

Preliminary routing shows that richer address/event information may exist before reported cross-section aggregation; its actual availability, physical meaning and retention are PMI/software dependent. No normative deficiency or sufficiency conclusion has been made.

## First own experiment

[EXP-001](../experiments/EXP-001-event-representation-reduction-sensitivity.md) is `PLANNED / IMPLEMENTATION HANDOFF READY`.

It compares:

1. `L0` full physical topology + `W`;
2. `L1` joint post-`W` parent-event mark;
3. `L2` marginal per-word multiplicities with explicit reconstruction;
4. `L3-U` scalar ungrouped bit/upset-arrival intensity.

`L3-E`, the scalar parent-event-rate primitive, is explicitly distinct and deferred from Phase 1 because it requires a separate event-to-state reconstruction. EXP-001 must also run a controlled `J-A`/`J-B` post-`W` pair with identical per-word marginals and different joint inter-word dependence, comparing both `F_A` and the parameterized restoration decision. An error of one `L2` reconstruction cannot be generalized to all marginal-statistics models.

Outputs include `F_A` error, the controlled-pair `ΔF_A`, false-safe/false-conservative classification over a swept parameterized `ε`, feasible scrub-period sets, decision discrepancy and computational cost. `L0 → L1` must be lossless for the declared state update; otherwise the implementation/model interface is invalid.

## Actual blockers

### Not blocking the synthetic EXP-001 implementation

- numerical `H_req` and `ε_req`;
- final target SRAM, `W` or irradiation data;
- final RQ-003 decoder outcomes;
- final RQ-004 estimator/observation channel;
- final RQ-005 resource vector/scalarization;
- final FPGA/RTL platform;
- completion of normative or Chen deep reads.

### Blocking only stronger downstream claims

1. **Target/device validity:** target `A/W`, irradiation/test-log provenance and repair trace.
2. **Normative applicability/identifiability:** accepted three-document extraction plus representative PMI/software-output semantics; current standard hierarchy remains incomplete.
3. **Adaptive-control novelty:** full-text comparison of the 2025 JETTA, 2023 DFT and 2024 LATS Chen-family sources.
4. **System requirement claim:** traceable `H_req` and `ε_req`.
5. **First RES:** completed EXP-001 with fixed code/config/seeds, uncertainty and Scientific Reviewer pass.

## Next bounded handoffs

1. **Research Engineer (priority):** implement and run EXP-001 deterministic checks and Monte Carlo comparison from the registered specification.
2. **Paper Analyst — normative branch (parallel):** perform only the three-document NORMATIVE-BASELINE-01 clause-level extraction; no broad standards search.
3. **Paper Analyst — control prior art (parallel, non-blocking for EXP-001):** full-text compare the 2025 JETTA, 2023 DFT and 2024 LATS sources; create draft Paper Cards/matrix and no novelty conclusion.
4. **Scientific Reviewer:** review EXP-001 only after implementation/tests/config/aggregate results exist.

## PI materials requested

The current three documents are sufficient to start extraction. To close the current/applicable normative chain, request exact copies/status for:

- controlled edition or registry extract for `СТО ГК Роскосмос 04.01.0005–2022`;
- `ГОСТ РВ 0020–57.415–2020`;
- `СТО ГК Роскосмос 04.01.0008–2024`;
- `СТО ГК Роскосмос 04.01.0010–2025`;
- one representative SRAM private PMI or de-identified PMI template plus diagnostic/software output schema.

No PI decision is required to begin EXP-001.

## Active hypotheses and results

- No `HYP-xxx` has been registered.
- `EXP-001` is registered but has no accepted result.
- No `RES-xxx` has been registered.
- DEC-001…003 are research decisions, not own experimental results.

## Constraints

- Do not reopen RQ-001 or revise DEC-001 without a concrete contradiction.
- Do not identify `E_cap` with DUE/SDC/miscorrection/system failure.
- Do not claim that richer event information is always necessary or observable.
- Do not claim normative deficiency before accepted extraction and applicability resolution.
- Do not claim adaptive-control novelty before the bounded Chen full-text comparison.
- Do not assign a numerical reliability requirement without traceable provenance.
- Do not let the identification/mapping layer replace adaptive control as the dissertation core.
