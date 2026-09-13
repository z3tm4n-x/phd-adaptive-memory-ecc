# RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02 — pre-execution contract

Task handoff: `ec6b1b3cd10ff1268979c60e08167279603f23d5`.
Reviewed target: `c48ca29eb65fee96154d645819c4e533a1709037`.
Controlling Scientific Review: `57021de76b45971ca2687e69c4a890f02647df8f`.

This contract is frozen before any new trace/exhaustive execution. It is a bounded symbolic/executor repair only. No CY62167 rate regeneration, no physical parameter fitting, no controller design, no RES change.

## Scientific question

Under what explicit conditions on the registered 32-data-bit arrival process and the conditional-write executor does

`E_CW subset P union B`

hold, how does it induce a one-sided unconditional upper bound, and does an event-driven executor implement exactly those conditions?

Definitions:

- `E_CW`: sticky first occurrence of at least two physical stored-error bits in a word under the declared conditional-write executor.
- `P`: at least two distinct arrival labels in one deterministic inter-check interval of a word. `P` is an enlarged arrival event, not exact toggle first passage.
- `B`: during a pending correcting write created by a singleton check, at least one arrival hits a bit distinct from the singleton observed at that check.

## Frozen model conditions

1. Clean start and no pending write at `t=0`.
2. Each word has deterministic potential check times. Initial, complete and final inter-check intervals have length at most `tau`.
3. Atomic single-bit toggles only in the registered submodel; no simultaneous direct multibit parent event.
4. Clean read causes no write.
5. Singleton read latches a clean corrected image, records the original singleton bit and schedules one correcting write. Its completion occurs before the next check of that word.
6. No other writes, decoder failures or controller failures in this submodel.
7. First passage is sticky even if later writeback clears physical storage.
8. Arrival times do not coincide with deterministic check/commit instants. Under continuous NHPP this has probability zero; deterministic regression inputs must obey it.
9. Main probability model: independent simple NHPPs for 32 data bits within a word, common deterministic intensity `r(t)`. Future increments after a check are independent of the check-time sigma-field. No word-independence is required for union bounds.
10. Full-device parity/hidden routes are outside this registered submodel and require a separate `delta_cov` term.

## Frozen probability statements to prove/check

For word `w` with deterministic inter-check partition `Pi_w`,

`Pr(P) <= C(32,2) * sum_w sum_{I in Pi_w} (integral_I r)^2`

and, because `|I|<=tau`,

`Pr(P) <= W*C(32,2)*tau*integral_H r(t)^2 dt`.

For deterministic potential checks `c_wk`, check-measurable singleton indicators `J_wk`, and deterministic or past-known delay upper bounds `D_wk`,

`Pr(B) <= 31*E[sum_wk J_wk * integral_[c_wk,min(c_wk+D_wk,H)] r]`

`<= 31*sum_wk integral_[c_wk,min(c_wk+D_wk,H)] r`.

With `K_D(t)` the number of all-check windows covering `t`, the deterministic envelope is

`Pr(B) <= 31*integral_H K_D(t) r(t) dt`.

The periodic simplification

`31*W*(D/tau)*integral_H r`

is accepted only when checks are `phi_w+k*tau`, `D<tau`, and `r` is constant on blocks containing an integer number of periods; initial/final truncation may only reduce the all-check exposure. For arbitrary `r`, average duty alone is not a valid upper bound.

The registered-process result is

`U_CW = min(1, U_P + U_B)`.

No numerical CY62167 `U_CW` is released by this repair; physical-slice `bound=null`, `NOT_ESTABLISHED` is frozen.

## Executor/event order

All deterministic traces use distinct timestamps. Event order for implemented traces is therefore chronological without ties. A singleton check creates a pending latch; a commit occurs only if such a pending write exists. `P` is computed from arrival labels grouped by deterministic inter-check intervals independently of writeback. `B` is raised only by a distinct-from-origin arrival while pending.

## Mandatory regression

Input trace (scaled exactly as given in `traces/counterexample_input.json`):

- 0.5 toggle b
- 1.0 singleton check; latch clean; ideal-at-read reset
- 1.1 toggle b while pending
- 1.2 commit clean latch
- 1.3 toggle b
- 1.4 toggle c

Required final indicators:

`physical_failure=true`, `ideal_failure=false`, `B=false`, `P=true`.

The old inclusion `E_CW subset E_ideal union B` must fail on this trace; the repaired inclusion `E_CW subset P union B` must hold.

## Exhaustive acceptance criteria

Use the six fixed arrival slots `[0.5,1.1,1.3,1.4,2.1,2.3]`, three bits and an optional no-arrival symbol: `4^6 = 4096` short streams. Checks at `1.0` and `2.0`; correcting delay `0.2`; horizon `3.0`.

Required:

- all 4096 streams executed by the event model;
- zero violations of `physical_failure => P or B`;
- at least one violation of the old `physical_failure => ideal_failure or B` (the mandated trace itself is one);
- preserve clean/no-write, post-clean persistence, distinct-RMW, same-bit cancellation, pending-at-H, initial/final interval and sticky-first-passage cases;
- a second implementation-independent bitmask checker must reproduce the new invariant on the same frozen input family without importing the main executor.

## MINOR dispositions frozen before execution

- No `--rate-summary` acceptance path will exist in the new checker. Physical selected-slice status remains `bound=null`, `NOT_ESTABLISHED`.
- Historical synthetic label `exact_pair_first_passage` is superseded only in this package by `distinct_arrival_event_probability`; historical bytes are not rewritten.
- Any opposite-decision theorem requires an explicit admissible passing complete `m0` policy plus an observation-invariant excluding `m1`; otherwise only the weaker lower-bound-change lemma is allowed.
- `upper > epsilon` means failure of that sufficient certificate, not physical impossibility; `upper == epsilon` passes an inclusive `<=epsilon` requirement. Exclusion requires a qualified lower `>epsilon`.
- Missing full rate input path is `experiments/RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv`; historical full SHA-256 `c10a68e721716c8c9b96bf99a9e2d1de0bd3b179ebcc747b3fd149ff0741ff83`, 237888 rows, 53420841 bytes. The required field is `nu_C_bit_DREG_s-1 / 2^24`. No search/regeneration is performed here.
- Run/segment to ECC-disabled linkage remains `ASSUMPTION/UNKNOWN` unless already explicitly qualified; archive identity does not prove per-segment protocol.
