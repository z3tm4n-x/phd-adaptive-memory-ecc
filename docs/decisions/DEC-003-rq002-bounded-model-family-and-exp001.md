# DEC-003 — Bounded RQ-002 model family and EXP-001 authorization

**Decision:** Accept the RQ-002 Evidence Audit with its stated limitation, retain an event-driven parent-event-preserving reference representation plus a declared reduction ladder, and authorize EXP-001 to determine which reductions preserve or alter ECC-level reliability and a parameterized restoration decision.<br>
**Date:** 2026-08-28<br>
**Status:** `ACCEPTED — MODEL-SELECTION LITERATURE GATE PASSED / EXP-001 AUTHORIZED`<br>
**Related RQ:** RQ-001, RQ-002, RQ-006; interfaces to RQ-003/RQ-004<br>
**Does not revise:** DEC-001 or DEC-002

## Context

The accepted RQ-002 mapping, `PAPER-004…008`, cross-paper synthesis and [Evidence Audit 01](../evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md) establish constraints on primitive events, mechanism provenance, mapping `W`, state transitions, observation ambiguity and DEC-001 metric compatibility. They do not establish one universally minimal stochastic process.

The audit explicitly finds no literature gap that blocks a parameterized prototype if the system, mapping, ECC capability, initial state, restoration semantics and horizon are declared and no target-specific validity claim is made. PI approval also permanently promoted C-RQ-05 to RQ-006.

## Alternatives considered

1. **Select a scalar bit/upset HPP as the project model now.** Rejected: it can discard same-parent clustering, mapping and joint word impact without a validity argument.
2. **Select a richer process family such as Cox/PDMP as the project model now.** Rejected: current evidence does not establish that the added temporal state is required or identifiable.
3. **Continue general literature/deep-read work before modelling.** Rejected: no named gap blocks the first controlled comparison.
4. **Use an event-driven reference and test successive reductions.** Accepted: it preserves the information needed to expose approximation loss without pre-judging which reduced model will prove adequate.

## Decision

### 1. Reference representation

The first prototype uses an event-driven reference representation with:

- parent radiation-event identity and event time;
- a declared physical-cell impact/topology mark;
- deterministic declared `W` mapping cells into codewords;
- joint post-`W` codeword impacts from each parent event;
- trajectory state sufficient to update distinct erroneous bits under declared write/toggle semantics;
- declared `A`, ECC capability `t_c(w)`, initial state/distribution and scrub/reset transitions;
- first-passage evaluation of DEC-001 `E_cap` and `F_A(t0,T;μ_t0)`.

This is a **comparison reference**, not an accepted universal or target-calibrated physical model.

### 2. Representation ladder

EXP-001 compares, under common event times and parameters:

| Level | Representation | Intended role |
|---|---|---|
| `L0` | full physical event topology plus explicit `W` | reference input |
| `L1` | joint post-`W` codeword-impact mark retaining parent-event dependence | candidate lossless interface for `E_cap` state evolution |
| `L2` | marginal per-word multiplicity distributions with an explicit reconstruction rule | tested reduction; sufficiency remains unknown |
| `L3` | scalar/unmarked event or upset rate | tested coarse reduction; permitted only in demonstrated regimes |

`L0 → L1` must be verified as lossless for the declared state update. No direction or conservatism is presumed for `L2` or `L3`.

### 3. Temporal alternatives

The initial prototype may use a constant-rate marked HPP and one declared deterministic time-varying intensity profile/NHPP as controlled scenarios. These are synthetic comparison conditions, not evidence that either family is the target process. Cox, renewal, PDMP and latent-state families remain deferred until a named inadequacy or identifiability need appears.

### 4. Mechanism and restoration semantics

Direct same-parent impact and sequential accumulation are represented in the same event trajectory rather than added as unexplained failure-rate terms. The model must expose correction/writeback/reset schedules as configuration. Phase 1 may use one explicitly declared periodic scrub policy, but the implementation interface must not hard-code it as the only possible semantics.

### 5. Decision-level output

No numerical `H_req` or `ε_req` is assigned. EXP-001 sweeps a parameterized `ε` and candidate scrub periods, reports the feasible set under each representation and records false-safe, false-conservative and selected-period discrepancies relative to `L0/L1`. Any scrub-operation count used is an experiment-local resource proxy, not the final RQ-005 cost objective.

## Rationale and evidence

- Evidence Audit candidates 01–03 and 05–10 support the reference interfaces and explicit-state constraints in bounded scope.
- Candidate 04 supports only the rule that marginal sufficiency cannot be presumed; EXP-001 supplies the missing controlled comparison.
- PAPER-007 demonstrates the relevance of parent-event topology and mapping in a selected simulated case; PAPER-005 exposes a mapping-factor approximation; PAPER-008 exposes observation/grouping ambiguity; PAPER-004 and PAPER-006 supply contrasting reduced representations.
- DEC-001 provides the common outcome metric; DEC-002 requires the effect of information reduction to be tested at both reliability and control-decision interfaces.

## Consequences

- RQ-002 remains `OPEN`, but its literature/model-selection gate is passed for the first prototype.
- RQ-006 is registered and owns mapping/reduction sufficiency.
- [EXP-001](../../experiments/EXP-001-event-representation-reduction-sensitivity.md) is registered as `PLANNED` and may proceed immediately in the local research environment.
- Russian normative extraction and Chen prior-art deep reads run in parallel and do not block the synthetic prototype.
- No additional RQ-002 Paper Card or broad search is authorized without a named gap blocking model adequacy, validation or interpretation of EXP-001.
- No `HYP-xxx`, `RES-xxx` or novelty claim is created by this decision.

## Revisit when

- EXP-001 falsifies the assumed `L0 → L1` losslessness or reveals a missing state variable;
- the normative extraction changes what test information is realistically available or identifiable;
- RQ-003 changes the required ECC state/outcome semantics;
- target SRAM `W`, irradiation logs or a representative private PMI become available;
- a named temporal/observation gap requires an additional process family;
- an adaptive-control claim requires a different decision interface after the Chen full-text comparison.
