# RQ-001 — Initial cross-paper evidence synthesis

**Status:** `INITIAL EVIDENCE SYNTHESIS — NOT A FINAL ANSWER`  
**Date:** 2026-08-27  
**Related RQ:** `RQ-001`  
**Accepted inputs:** [PAPER-001](../paper_cards/PAPER-001-tausch-2009.md), [PAPER-002](../paper_cards/PAPER-002-baeg-wen-wong-2009.md), [PAPER-003](../paper_cards/PAPER-003-lee-baeg-reviriego-2011.md)  
**Numerical reliability threshold:** `TBD`

This document separates paper-supported definitions from cross-paper inference. Acceptance of a Paper Card means that the analytical card is complete and traceable enough for the current workflow; it does not adopt the paper's model assumptions as project assumptions and does not establish a final answer to `RQ-001`.

## 1. Formal Paper Card disposition

| Permanent ID | Candidate | Disposition | Basis for acceptance | Preserved caveat |
|---|---|---|---|---|
| `PAPER-001` | C45 — Tausch, 2009 | `ACCEPTED — CORE` | Complete full-text card; all 19 required sections; equation/page provenance; clear separation of source and inference | The model horizon is accumulated upset count, not elapsed or mission time; harmful direct MBU is outside the main equation |
| `PAPER-002` | C46 — Baeg, Wen, Wong, 2009 | `ACCEPTED — CORE` | Complete full-text card; explicit event, metrics, leaf-block boundary, stochastic model and bound condition | The final metric loses direct-MCU versus independent-accumulation provenance; the upper-bound interpretation is conditional |
| `PAPER-003` | C38 — Lee, Baeg, Reviriego, 2011 | `ACCEPTED — CORE` | Complete full-text card; explicit word→row→memory aggregation, time layer and periodic-maintenance model | Row-level prose contains a flagged internal ambiguity; architecture and fitted parameters are not independently transferable |

No card is rejected. `PAPER-003` is accepted with the row-level wording ambiguity retained as an evidence limitation rather than silently resolved.

## 2. Canonical cross-paper extraction matrix

| Field | `PAPER-001` — C45 | `PAPER-002` — C46 | `PAPER-003` — C38 |
|---|---|---|---|
| Reliability/failure event | `[SOURCE]` At least two distinct upset bits in at least one Hamming-protected word anywhere in the complete worked memory | `[SOURCE]` At least one SEC word in one leaf block contains at least two distinct upset cells | `[SOURCE]` At least one word in the modeled memory exceeds ECC correction capability; main model is SEC. Row-level prose is internally ambiguous, but the memory-level event is explicit |
| Metric and units | `[SOURCE]` Cumulative array-event probability conditional on `p` accumulated random upsets; dimensionless | `[SOURCE]` `F(t)` and `R(t)` dimensionless; MTTF in the time unit of `t`; FIT in failures per `10^9` operating hours per Mbit when hours are used | `[SOURCE]` Conditional row/memory failure probabilities, `F(t,ID)` and `R(t,ID)`, all dimensionless; reported word MTBF in seconds |
| Aggregation level | `[SOURCE]` ECC word → complete array/device (`524,288` protected words in the example) | `[SOURCE]` ECC word → one leaf block; multi-block aggregation excluded | `[SOURCE]` ECC word → physical row → assumed modeled memory; experimental blocks are folded into one representation; no system-service event |
| Independent variable | `[SOURCE]` `p`, total accumulated random upset count | `[SOURCE]` elapsed time `t`, with intermediate grouped-arrival count `Y`, total upset count `X`, event rate `λ` and multiplicity parameter `r` | `[SOURCE]` accumulated upset count `X`, row-group number `g`, elapsed time `t`, `ID`, and fitted statistical parameters |
| Evaluation horizon | `[SOURCE]` Upset-count horizon only; not time, fluence, scrub interval or mission duration | `[SOURCE]` Elapsed time under a constant-rate compound-Poisson process; examples use consistent hour or second units. No mission aggregation | `[SOURCE]` Time since effective refresh/reset, bounded by deterministic full-memory scrub interval `T_scr`; examples use accelerated-test seconds up to 3,000 s. No mission aggregation |
| ECC capability / decoder outcome | `[SOURCE]` Hamming EDAC corrects one bit and detects a double-bit state; the model labels the first double-bit word non-correctable/unusable | `[SOURCE]` SEC; one distinct error is repairable, two or more are unrepairable | `[SOURCE]` Main model SEC; a DEC-TED comparison is illustrative. Failure is multiplicity beyond correction capability | 
| Scrubbing semantics | `[SOURCE]` No operational scrubbing; EDAC is disabled during irradiation and enabled after beam stop in the experiment | `[SOURCE]` No scan/repair state process; an illustrative scrub interval is read from threshold crossing of `F(t)` | `[SOURCE]` Periodic scan, ECC correction and writeback; deterministic full-memory interval. `[INFERENCE]` Equations treat completion as an effective reset of correctable accumulated errors and omit sequential exposure ages |
| Error-arrival/statistical assumptions | `[SOURCE]` Isolated uniformly random upset locations; persistent errors; first-order birthday approximation with an effective collision range | `[SOURCE]` Constant-rate Poisson grouped arrivals; iid geometric multiplicity; uniform independent placement of upset instances conditional on total `X` | `[SOURCE]` Count-dependent geometric row grouping; Weibull row-failure fit; compound-Poisson total count; simulator uses Poisson arrivals, MCU/SBU classification, geometric MCU size and test-derived shapes |
| Interleaving / mapping assumptions | `[SOURCE]` No explicit mapping function; regular protected words and qualitative dependence of harmful MBU on physical/logical mapping | `[SOURCE]` Regular scalar interleaving distance `ID` in a structured leaf block; actual 45 nm hierarchy is unavailable and replaced by pseudo-partitioning | `[SOURCE]` Regular scalar `ID` through column multiplexing; unknown 45 nm hierarchy replaced by an assumed `8×16` block structure with `256×64` cells per block |
| Direct MCU vs independent accumulation | `[SOURCE]` Main equation quantifies isolated-upset accumulation; harmful same-particle MBU is excluded and said to require a separate component | `[SOURCE]` MCU multiplicity enters total-count generation, but the final failure metric does not retain whether a failed word arose from one arrival or multiple arrivals | `[SOURCE]` Simulator labels MCU/SBU arrivals, while the analytical row-group and final failure metrics intentionally remove that provenance and combine both temporal and spatial contributions |
| Double-counting risk | `[INFERENCE]` None inside the published equation. A combined model must partition harmful direct MBU from accumulation-eligible events before adding a direct term | `[INFERENCE]` None internally because one generative process is used. Adding an external direct-MCU term to total `F(t)` without repartitioning would overlap events | `[INFERENCE]` No explicit arithmetic double counting internally; mechanisms are conflated. Adding a separate direct-MCU term without upstream repartition would overlap the existing total |
| Key limitations | Count horizon only; no time/repair model; no explicit `W`; small experimental samples; no DUE/SDC/miscorrection states | One leaf block; constant-rate Poisson and geometric multiplicity; independent-location approximation; conditional upper bound; no operational scrub; no arbitrary `W` | Assumed architecture; mixed/in-sample calibration data; several fitted layers; idealized periodic maintenance; row prose ambiguity; no uncertainty propagation or decoder outcomes |

## 3. Where the papers agree

- `[SOURCE SYNTHESIS]` Each paper uses an existential memory event: at least one protected word enters a state beyond the modeled guaranteed correction capability. For the main SEC abstractions, this is at least two distinct erroneous cells in one word.
- `[SOURCE SYNTHESIS]` Their main reliability quantities are cumulative probabilities; none supplies a project numerical reliability requirement.
- `[SOURCE SYNTHESIS]` Error multiplicity is used as the failure label. DUE, SDC, miscorrection and system-visible loss of memory service are not separate mathematical outcomes.
- `[SOURCE SYNTHESIS]` Logical-to-physical organization matters, but none validates an arbitrary target mapping `W` for this project.
- `[SOURCE/INFERENCE SYNTHESIS]` None provides both a mutually exclusive direct same-particle mechanism and an independent-event accumulation mechanism with separate rates and a proven recombination rule.

## 4. Different definitions, aggregation levels and horizons

| Dimension | Difference | Consequence for RQ-001 |
|---|---|---|
| Horizon | `PAPER-001`: upset count; `PAPER-002`: elapsed time; `PAPER-003`: upset count plus elapsed time bounded by a deterministic scrub interval | These curves are not interchangeable. A count-conditioned probability becomes a time-domain probability only after specifying an arrival process; mission aggregation needs another layer |
| Aggregate object | Complete array/device vs one leaf block vs an assumed row/block/memory representation | The symbol “memory failure probability” is insufficient unless the modeled object and aggregation rule are named |
| Scrubbing | Absent vs threshold-crossing illustration vs idealized periodic full-memory reset | A scrub interval cannot be inferred consistently until operational repair/reset semantics and word exposure age are fixed |
| Spatial model | Uniform isolated placement vs compound count plus uniform placement vs fitted row grouping and assumed ID | Relative reliability results cannot be transferred to a different layout or `W` without new evidence |
| Decoder semantics | All reduce outcomes to correction capability, with only illustrative detection wording | A physical multi-error word state must not be silently equated with DUE, SDC or system failure |

## 5. Assumptions that are incompatible or non-transferable

1. `[INFERENCE]` The isolated-uniform upset population in `PAPER-001` is incompatible with treating harmful same-particle MCU as already included; the populations must be partitioned before combination.
2. `[SOURCE/INFERENCE]` `PAPER-002` retains grouped multiplicity in `P(X,t)` but remaps members independently in `P_f(X)`. This is not a topology-preserving MCU model and is conservative only under its stated MCU-span condition.
3. `[INFERENCE]` `PAPER-003` row-group, Weibull and compound-Poisson parameters are fitted to a specific, architecture-assumed data representation and are not transferable constants for another SRAM or mission.
4. `[INFERENCE]` A leaf-block rate `λ` from `PAPER-002` cannot be used as an array/device rate without an explicit block aggregation model.
5. `[INFERENCE]` The idealized full-memory reset in `PAPER-003` is not equivalent to sequential scrubbing when words have different exposure ages or errors can arrive during the scan.
6. `[INFERENCE]` Accelerated-test seconds in `PAPER-003` and illustrative hours in `PAPER-002` are not mission requirements and must not be copied as project thresholds or admissible intervals.

## 6. Evidence gaps after the three-paper synthesis

| Gap | Status after synthesis | Dependency / likely owner |
|---|---|---|
| Exact project event: physical state beyond correction capability vs DUE/SDC/miscorrection vs system-visible service loss | `UNKNOWN` | RQ-001, with decoder semantics from RQ-003 |
| Exact aggregate object and rule from codeword to bank/array/system | `UNKNOWN` | RQ-001; requires explicit target system boundary or system requirements |
| Operational scrubbing semantics, including sequential scan and nonuniform word exposure age | `PARTIAL` | RQ-001 model choice; no new paper requested before audit |
| Mission aggregation across scrub cycles, especially for nonstationary conditions | `UNKNOWN` | RQ-001 plus later RQ-002 arrival model |
| Mutually exclusive direct-MCU and accumulation-eligible event populations | `UNRESOLVED` | RQ-001 boundary; detailed adequacy belongs to RQ-002/C-RQ-05 gate |
| Provenance for a numerical reliability threshold | `TBD` | System/mission requirement, not illustrative paper examples |
| Valid physical-cell-to-codeword mapping for a target SRAM | `UNKNOWN` | RQ-003 and conditional C-RQ-05; none of the three papers supplies it |

## 7. Initial evidence synthesis for RQ-001

### Known from these papers

- `[SOURCE SYNTHESIS]` A tractable primitive event used across all three sources is the existence of at least one ECC word whose distinct erroneous-bit count exceeds the guaranteed correction capability.
- `[SOURCE SYNTHESIS]` The reported probability is meaningful only together with its aggregate object and horizon.
- `[SOURCE SYNTHESIS]` Count horizon, elapsed-time horizon, scrub-cycle horizon and mission horizon are distinct layers.

### Candidate interpretation, not yet accepted as the project answer

- `[INFERENCE]` The project can provisionally use a codeword state beyond guaranteed correction capability as the primitive physical reliability event, then separately define decoder-visible and system-visible consequences.
- `[INFERENCE]` A first project metric could be cumulative probability of that event over one explicitly defined repair/exposure interval for an explicitly named aggregate memory object. Mission-level risk would require a separate cross-cycle aggregation rule.
- `[INFERENCE]` This candidate is preferable to copying any one paper's “memory failure” definition because it exposes the aggregation and horizon rather than hiding them.

### Still unknown

- Whether the accepted project event should terminate at the physical codeword state or require DUE, SDC, miscorrection or service-loss semantics.
- Whether the target aggregate is a leaf block, bank, entire SRAM, memory service or system.
- How sequential scrubbing and a nonstationary environment alter the per-cycle and mission horizons.
- What traceable numerical requirement, if any, applies. It remains `TBD`.

Therefore an initial synthesis is possible, but a final answer to `RQ-001` is not.

## 8. Exact candidate claims for Evidence Auditor

These are audit inputs only. No `CLM-xxx` is created or accepted by this document.

1. **RQ001-EA-CAND-01 — PAPER-001 event.**  
   `[SOURCE]` `PAPER-001` defines the modeled array event as the existence of at least one Hamming-protected word containing at least two distinct upset bits after `p` accumulated random upsets.

2. **RQ001-EA-CAND-02 — PAPER-002 event.**  
   `[SOURCE]` `PAPER-002` defines leaf-block failure as the existence of at least one SEC-protected word containing at least two distinct upset cells by elapsed time `t`.

3. **RQ001-EA-CAND-03 — PAPER-003 event.**  
   `[SOURCE]` `PAPER-003` defines modeled-memory failure as the existence of at least one ECC word whose upset multiplicity exceeds the modeled correction capability.

4. **RQ001-EA-CAND-04 — PAPER-001 horizon.**  
   `[INFERENCE]` The probability in `PAPER-001`, being conditioned on accumulated upset count `p`, cannot be interpreted as elapsed-time, scrub-cycle or mission reliability without an additional upset-count arrival model and repair/reset semantics.

5. **RQ001-EA-CAND-05 — PAPER-001 mechanism boundary.**  
   `[SOURCE]` Harmful same-particle MBU is outside the main equation of `PAPER-001` and is identified by the author as requiring a separate mapping-dependent probability component.

6. **RQ001-EA-CAND-06 — PAPER-002 provenance loss.**  
   `[INFERENCE]` The final failure probability in `PAPER-002` does not retain whether the multiple erroneous cells in a failed word originated from one grouped particle arrival or from multiple arrivals.

7. **RQ001-EA-CAND-07 — PAPER-003 provenance loss.**  
   `[INFERENCE]` The analytical failure probability in `PAPER-003` does not retain whether the multiple erroneous cells in a failed word originated from one MCU or from independent arrivals accumulated between repairs.

8. **RQ001-EA-CAND-08 — overlap consequence for PAPER-002.**  
   `[INFERENCE]` Adding a separate direct-MCU probability or rate to the total failure metric of `PAPER-002` without partitioning its upstream event population would overlap events already contained in that total.

9. **RQ001-EA-CAND-09 — overlap consequence for PAPER-003.**  
   `[INFERENCE]` Adding a separate direct-MCU probability or rate to the total failure metric of `PAPER-003` without partitioning its upstream event population would overlap events already contained in that total.

10. **RQ001-EA-CAND-10 — PAPER-003 scrub abstraction.**  
    `[INFERENCE]` The periodic-maintenance equations in `PAPER-003` treat completion of a deterministic full-memory scrub as an effective reset of correctable accumulated errors and do not represent different word exposure ages during a sequential scan.

11. **RQ001-EA-CAND-11 — PAPER-002 conditional upper bound.**  
    `[SOURCE]` The independent-location failure calculation in `PAPER-002` is an upper bound only when MCU row spans greater than the modeled interleaving distance are absent or negligible.

12. **RQ001-EA-CAND-12 — modeled outcome class.**  
    `[SOURCE SYNTHESIS]` `PAPER-001`, `PAPER-002` and `PAPER-003` define failure through erroneous-bit multiplicity beyond modeled correction capability rather than through an observed decoder output or system-visible loss-of-service event.

## 8.1 Orchestrator disposition after Evidence Audit

The canonical [Evidence Audit](../evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md) is accepted with a limitation:

- `RQ001-EA-CAND-01…03` remain source facts in the accepted Paper Cards and this matrix; separate permanent claim records would be redundant.
- `RQ001-EA-CAND-04…09`, `11` and `12` are registered as [`CLM-001…008`](../claims/README.md).
- `RQ001-EA-CAND-10` is partially supported and deferred: omission of word-specific exposure age is supported, while the stronger effective-global-reset interpretation is not accepted.
- No numerical reliability threshold, hypothesis, evidence record or project result is created by this disposition.
- No additional Paper Card or new literature search is ordered at this gate.

## 9. Additional Paper Card decision

**Decision:** no additional Paper Cards are required before the Evidence Auditor stage.

**Rationale:** the three accepted cards cover the minimum comparative dimensions needed for an initial synthesis and expose the remaining disagreements. The next uncertainty reduction comes from checking the twelve exact claims and their citation context, not from broadening the paper batch.

Additional full-text cards may be requested only after audit if a named gap remains material. The permitted gap-specific categories are:

- a primary source that explicitly aggregates a codeword event to bank/array/system or mission-level service loss;
- a primary source with operational sequential-scrubbing exposure-age semantics;
- a primary source that distinguishes decoder outcomes such as DUE, SDC and miscorrection for the relevant ECC abstraction.

This is not an active search order.

## 10. Next gate

`RQ-001 PROVISIONAL DEFINITION — USER APPROVAL`.

The [provisional definition package](RQ-001_provisional_definition_package.md) asks for explicit approval or amendment of:

1. the primitive ECC capability-exceedance event `E_cap(A,H)`;
2. the cumulative first-passage metric `F_A(H)`;
3. the complete controller-protected SRAM region as the default aggregate;
4. separate upset-count, per-codeword exposure and reporting/mission horizons;
5. separation of the physical capability-exceedance event from DUE, SDC and system-visible consequences;
6. the post-approval status `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.

The numerical requirement `F_A(H_req) ≤ ε_req` retains both `H_req` and `ε_req` as `TBD` until traceable system or mission requirements exist. `RQ-001` remains `INVESTIGATING` and `RQ-002` remains queued until this approval gate is completed.
