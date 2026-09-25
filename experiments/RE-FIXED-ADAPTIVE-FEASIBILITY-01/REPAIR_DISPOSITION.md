# REPAIR DISPOSITION 01 — RE-FIXED-ADAPTIVE-FEASIBILITY-01

**Repair base:** `80737bdcc37dff1eb597a20e603c61a6a5af3a1f`.  
**Scope:** four addressable review findings only; no new environment, retuning, Monte Carlo, RTL or RES-004 work.

## 1. Conditional-write semantic checks

Accepted finding. Frozen `verify.py` stored expected outcomes in dictionaries and then checked those stored values. Those checks remain provenance but are not semantic evidence after this repair.

Repair: `semantic_model.py` + `repair_checks.py` execute nine state transitions covering clean suppression, post-read upset persistence, single-error correction, RMW first passage, same-bit toggle, last-word snapshot, partial pass, deadline fallback and word-boundary arbitration. All nine pass.

## 2. Executor schedule and the 3.005 us delay

Accepted finding. The 25%/1s limit alone is insufficient for a microsecond latency claim.

Repair: the executor is explicitly tied to the causal scan phase used by the risk witness. At the principal peak, scrub-word releases are spaced by `582.221399 ns`. Scrub has priority at a word boundary; one already-running application primitive may delay it by at most `80 ns`; one worst-case scrub word occupies `140 ns`. Since `220 ns < 582.221399 ns`, blocked releases do not bunch.

The corresponding phase lateness raises the risk upper bound only to `0.0009500001245 < 0.001`.

The release stream gives `A_scrub(T)<=140ns+rho_scrub*T`. For an eight-word application burst (`sigma=640ns`) and `rho_app=0.5`, the leftover-service delay is `1.02694 us`; the previously quoted whole-busy-period bound is the looser `3.00530 us`. Thus 3.005 us remains conservative, now under a concrete word-level executor/workload contract rather than the 1-second peak percentage alone.

## 3. Nominal versus fallback-reserved resource regions

Accepted finding. The original connected interval cannot be described as if all of it also reserves the published 148 fallback hours.

For the principal 4 MiB, epsilon=0.001 case, the Fixed separator remains `0.3950398%`, but the lower edge depends on the information-availability case:

| Case | Established lower edge for average interface service | Reserve at B_avg=0.25% for additional same-interface controller cost |
|---|---:|---:|
| nominal warm start | 0.1424470% | 0.1075530 percentage point |
| warm start + strict 148 h fallback reservation | 0.2236533% | 0.0263467 percentage point |
| cold start + the same 148 h fallback reservation | 0.2242020% | 0.0257980 percentage point |

Therefore:

- nominal warm-start region: `[0.142447%, 0.395040%)`;
- 148-hour fallback-reserved warm-start region: `[0.223653%, 0.395040%)`;
- cold-start + 148-hour fallback-reserved region: `[0.224202%, 0.395040%)`.

At the tested 0.25% slice both fallback-reserved cases still fit before unmeasured controller overhead is charged.

Controller computation/WCET remains unmeasured. If it consumes the same interface budget, it must fit in the corresponding reserve above; if it consumes another resource, that resource requires a separate contract.

## 4. Information/calibration contract

Accepted finding. The runtime rule is causal, but `mean_old_per_hour`, `max_old_per_hour`, `lag1_eta` and `C` are retrospective offline calibration constants from the transferred 2021--2025 shape. Their out-of-sample transfer is not independently established.

Warm start requires a valid pre-t0 completed-hour scalar. Without one, the first hour uses calibrated peak fallback. Additional operational delivery latency is not established. The historical maximum is a calibration envelope, not a qualified future physical ceiling.

The corrected scientific scope is therefore an **existence/feasibility result conditional on a retrospectively calibrated transferred-shape assumption**, not a prospective qualification of the tuning for an unseen mission.

## Effect on the five top-level answers

1. Fixed insufficiency in the principal SEC-DED slice remains supported.
2. Simple external delayed-rate + fallback remains the minimal **established** causal witness, conditional on the clarified information contract.
3. No additional practical benefit of RES-003 over that simple witness is established.
4. No basis to restart the practical RES-004 branch is created.
5. The dissertation-level statement must distinguish nominal and fallback-reserved resource domains and state the calibration-transfer condition explicitly.

Substantial claims remain subject to separate Scientific Review.
