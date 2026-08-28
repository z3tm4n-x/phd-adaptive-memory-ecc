# DEC-002 — Integrated evidence-to-adaptive-control research architecture

**Decision:** Preserve adaptive control as the dissertation core and organize the research as one traceable chain from radiation-test evidence to an ECC-level risk assessment and an actual adaptive memory-restoration decision.<br>
**Date:** 2026-08-28<br>
**Status:** `ACCEPTED — PI DIRECTION / ROADMAP DECISION`<br>
**Related RQ:** `RQ-002`, `RQ-003`, `RQ-004`, `RQ-005`; C-RQ-05 escalation and a future integrated adaptive-control RQ remain pending explicit registration<br>
**Does not revise:** `DEC-001` or the `PARTIALLY ANSWERED / OPEN DEPENDENCIES` disposition of `RQ-001`

## Context

The approved dissertation topic and SOURCE-level objective concern adaptive control of the memory-restoration period under a declared reliability requirement and resource-cost considerations. RQ-002 evidence has exposed a potentially load-bearing information interface between radiation-test observations, physical event representation, mapping `W`, ECC-level reliability and the downstream control decision.

The PI directed that this event-representation problem strengthen the foundation of the adaptive method rather than replace it. This decision records that roadmap constraint. It is a project-scope decision, not external scientific evidence and not an accepted novelty claim.

## Decision

### 1. One connected method

The current working architecture is:

`radiation tests → experimentally justified device-error representation → transformation through memory/ECC organization W → ECC-level reliability model → current/future risk assessment from online information → adaptive memory-restoration decision`.

The three scientific layers are:

1. identification from radiation-test evidence;
2. ECC-aware reliability;
3. adaptive control.

They are treated as one causal method whose layer outputs are the next layer's inputs. They are not automatically three independent novelty claims.

### 2. Central approximation question

The project must determine:

- what radiation-test information is sufficient in principle for the required ECC-level reliability calculation;
- what information is actually identifiable from realistic test observations;
- what information is lost by candidate reductions before or after `W`;
- how that reduction changes, bounds or leaves invariant both `F_A(t0,T; μ_t0)` and the eventual adaptive restoration decision.

Richer information is not presumed superior. A reduced representation is acceptable when its adequacy or bound is demonstrated for a declared applicability domain. The internal compass is the **quantitative price of information loss**, not a prior commitment to one representation.

### 3. Physical, logical and observational layers remain distinct

The model must distinguish:

- physical radiation-event information before `W`;
- logical codeword impact after `W`;
- reconstruction/classification uncertainty in observed test data;
- additional assumptions used when physical information was reduced before logical impact was calculated.

An ideal event representation is not treated as automatically observable in an irradiation test.

### 4. Russian normative practice is a primary baseline

Applicable Russian normative documentation is a primary engineering baseline for the identification-to-rate chain, not background and not merely a final compliance check. The initial bounded target includes РД 134-0175-2009 and РД 134-0174-2009 after the PI supplies the exact documents.

The normative extraction must identify what the chain

`radiation testing → experimental SEE/ORE cross section → environment convolution → SEE/ORE rate → probability indicator`

retains, aggregates and assumes, and whether those outputs are sufficient for the declared ECC-aware reliability and adaptive-control problem. No normative deficiency is claimed before the relevant documents are examined.

### 5. Prior-art threats are layered

- Zebrev, Ogden, Gomi, Franco and related work primarily threaten identification, event representation, mechanism partition and mapping claims.
- Chen/IHP/Potsdam and related adaptive-scrubbing work threaten the adaptive-control layer.
- Classical inspection/maintenance/checking literature remains a separate future control-layer threat.

These threat layers must not be conflated. Novelty requires a feature-by-feature comparison over the actual load-bearing interfaces, decision logic and guarantees.

### 6. Adaptivity requires an actual decision

A time-varying or forecast input alone is not sufficient to establish an adaptive-control contribution. The eventual method must map observable information and an ECC-level reliability assessment to a selected restoration regime or control action.

External exposure information and internal memory state/history are distinct observation channels. Their equivalence, sufficiency or fusion is not assumed. RQ-004 retains responsibility for observables/estimation; RQ-005 retains responsibility for measurable resource costs without premature scalarization.

### 7. Parameterized own work may precede final requirements

Unknown numerical `H_req`, `ε_req`, final observables, resource weights or hardware platform do not block all quantitative work. Parameterized model studies may proceed when they:

- preserve DEC-001 semantics;
- state `A`, `W`, initial state and scrub/reset semantics;
- sweep unresolved requirements or parameters instead of inventing values;
- report sensitivity, approximation error or decision changes rather than claiming satisfaction of an unspecified requirement.

## Known

- The approved topic and SOURCE-level objective retain adaptive control as the core subject.
- DEC-001 supplies the current event, metric, domain and horizon contract.
- The accepted RQ-002 synthesis shows that the five decisive sources use materially different primitive objects, aggregation levels, mappings, horizons, reset semantics and observation models.
- The C-RQ-05 escalation condition is confirmed at full-text synthesis depth because topology and `W` cannot be safely discarded without a validity argument.

## Working definitions / roadmap requirements

- The contribution is evaluated over the complete evidence-to-decision chain.
- Information sufficiency and experimental identifiability are separate questions.
- The effect of representation reduction must be measured at both the reliability-output and control-decision levels.
- Normative practice and closest prior art are explicit baselines.
- Prototype work should target a verifiable approximation/sensitivity result before another broad literature cycle.

These are project decisions and internal roadmap requirements; they are not universal literature facts.

## Unknown / TBD

- the minimum adequate arrival/event/state representation — RQ-002;
- the accepted physical-to-codeword mapping question and permanent RQ identity for C-RQ-05;
- concrete ECC and decoder outcomes — RQ-003;
- feasible external/internal observation channels and estimator requirements — RQ-004;
- measurable cost vector and later optimization form — RQ-005 and the deferred C-RQ-11 line;
- the exact adaptive-control RQ/policy class and guarantee;
- what the applicable Russian normative document set retains and assumes;
- the verified feature boundary relative to Chen/IHP/Potsdam;
- device-specific `W`, event-resolved data availability, `H_req`, `ε_req` and hardware target.

## Alternatives considered

| Alternative | Disposition | Rationale |
|---|---|---|
| Replace the adaptive-control problem with radiation-test/event representation | Rejected | Conflicts with the approved topic and SOURCE-level objective |
| Treat identification, reliability and control as independent dissertations/contributions | Rejected | Breaks the causal interface and encourages unbounded scope |
| Assume full event topology is always required | Rejected | Sufficiency and approximation domain must be demonstrated quantitatively |
| Assume scalar rate or marginal multiplicity is always sufficient | Rejected | Accepted evidence exposes mapping/topology and observation cases where that reduction may lose relevant dependence |
| Delay all own modelling until final numerical requirements and hardware are fixed | Rejected | Parameterized studies can produce valid sensitivity and approximation results without inventing requirements |
| Claim novelty for forecast-driven scrub-frequency change alone | Prohibited pending verification | Chen/IHP/Potsdam is an active close prior-art threat |
| Treat Russian normative practice as background only | Rejected | It is a primary practical baseline for the existing test-to-probability chain |

## Consequences

- RQ-002 model selection must include representation sufficiency, experimental identifiability and uncertainty propagation to the DEC-001 metric.
- C-RQ-05 should be promoted to a permanent mapping/information-reduction RQ after explicit PI acceptance and before the main quantitative reliability model is fixed.
- An integrated adaptive-control RQ must be registered before control-method development; it should consume outputs from RQ-002…RQ-005 rather than duplicate them.
- A bounded normative-baseline extraction task is activated when the PI supplies exact documents.
- The close Chen/IHP/Potsdam control-prior-art pass is required before an adaptive-control novelty claim but does not block the first parameterized representation/reliability prototype.
- No new general literature cycle is authorized by this decision.
- No numerical requirement, `CLM`, `EVD`, `HYP`, `EXP` or `RES` is created.

## Revisit when

Revisit this roadmap if:

- normative analysis or verified closest prior art removes the load-bearing distinction;
- RQ-002 evidence shows that representation reduction has no decision-relevant effect over the intended domain;
- realistic test data cannot identify the parameters required by the selected model;
- the integrated contribution cannot remain quantitatively testable and substantial without exceeding the approved dissertation scope;
- a concrete contradiction requires revising DEC-001 or the RQ-001 disposition.
