# RE-CY62167-PHYSICAL-BRIDGE-REPAIR-02 — REPORT

**Role:** permanent Research Engineer, separate user-started session.  
**Task/handoff:** `ec6b1b3cd10ff1268979c60e08167279603f23d5`.  
**Reviewed repair input:** `c48ca29eb65fee96154d645819c4e533a1709037`.  
**Controlling SR-02:** `57021de76b45971ca2687e69c4a890f02647df8f` — `REVISE`.  
**Publication chronology:** the first authorized `create_branch` attempt was blocked by the OpenAI safety layer before execution; no alternate ref/API route was used. After the local proof/trace work was sealed, the exact same branch-creation request succeeded. The GitHub pre-execution mirror therefore was published retrospectively; the actual before-execution byte lock is the preserved local commit `0cab8b63fc7121422aec0a57a4c6f243bd7f3d5c` plus the saved failed frozen run. GitHub ancestry preserves the frozen checker bytes before the explicit checker-defect fixes.

## 1. Result

The repair closes the **bounded symbolic/executor defect** identified by SR-02. It does not close Issue #15 or the full physical bridge.

The invalid stronger inclusion from repair-01 is rejected:

`E_CW ⊄ E_ideal_at_read ∪ B_distinct`.

The required SR counterexample is executed and gives

- `physical_failure = true`;
- `ideal_failure = false`;
- `B = false`;
- `P = true`.

Across the frozen 4096-stream three-bit family, the old inclusion fails in **60** streams.

Under the explicit conditions in `CONTRACT.md`, the repaired inclusion is

`E_CW ⊆ P ∪ B`,

and both event-driven implementations report **0 violations in 4096 streams**. The main executor additionally passes the targeted clean/no-write, post-clean persistence, distinct-RMW, same-bit cancellation, pending-at-H, initial/final interval and sticky-first-passage checks.

No CY62167 numerical conditional-write upper is released. The physical slice remains `bound=null`, `NOT_ESTABLISHED`.

## 2. Executor and event semantics

The repaired executor keeps physical storage and ideal-at-read state on the same toggle stream. A clean check performs no write. A singleton check records the singleton bit, latches the corrected clean image and schedules one delayed correcting write. A commit overwrites physical storage with that latched clean image. First passage is sticky.

`P` is computed from **arrival labels** in the deterministic inter-check partition, independent of later cancellation/writeback. `B` is raised when an arrival during a pending correcting write hits a bit distinct from the singleton observed at its opening check.

Arrival/check or arrival/commit ties are excluded by the contract; under the simple NHPP model they have probability zero. The deterministic regression traces use distinct timestamps.

### Required negative regression

`traces/counterexample_input.json` is the exact SR §4.1 pattern. `outputs/counterexample_trace.json` records the full timeline. The same-bit RMW arrival cancels the physical singleton before commit and therefore does not raise B. Later arrivals `b,c` in the same inter-check interval make P true and physical first passage occurs while the ideal-at-read comparator remains safe.

The repair therefore **recognizes the counterexample**; it does not force it into the rejected inclusion.

## 3. Proof of `E_CW ⊆ P ∪ B`

Fix one word and consider the deterministic inter-check interval containing the first physical capability exceedance.

**Opening check clean.** There is no pending write. To reach two stored-error bits before the next check, arrivals with at least two distinct labels must occur in that interval. Hence P.

**Opening check singleton.** Let the observed singleton bit be `b`, and let its corrected clean image be pending.

- If any bit different from `b` is hit before correcting-write completion, B occurs.
- If B does not occur, the only pre-commit arrivals can be in `b`; the commit then installs the clean latched image.
- After that commit, reaching capability exceedance before the next check requires at least two distinct post-commit arrival labels. Those labels lie in the same deterministic inter-check interval, so P occurs.

If the horizon ends while a singleton write remains pending, any first passage caused by a different bit before H is already B. If no such different bit arrives, the pending interval cannot create a two-bit physical state from the singleton branch.

The initial interval opens from the declared clean start. The final partial interval is handled identically. First passage remains historical after any later writeback.

Therefore, under the frozen executor assumptions,

`E_CW ⊆ P ∪ B`.

This is a statement for the registered 32-data-bit submodel. It does not include simultaneous direct multibit parent marks, parity, decoder/controller failure or other full-device routes.

## 4. One-sided probability bounds

### 4.1 Enlarged pair-arrival event P

For one deterministic interval `I`, let `mu_I = integral_I r(t)dt`. For an unordered bit pair `(i,j)`, independent simple NHPP arrivals give

`Pr(N_i(I)>=1 and N_j(I)>=1) = (1-exp(-mu_I))^2 <= mu_I^2`.

A union bound over the `C(32,2)` pairs, all intervals and all words yields

`Pr(P) <= C(32,2) * sum_w sum_{I in Pi_w} mu_I^2`.

Cauchy-Schwarz and `|I|<=tau` give

`mu_I^2 <= |I| * integral_I r^2 <= tau * integral_I r^2`,

hence

`Pr(P) <= W*C(32,2)*tau*integral_H r(t)^2 dt`.

No independence across words is needed for this union bound. Event-dependent partitions do not inherit this formula automatically.

### 4.2 Pending-write event B

Let deterministic potential checks be `c_wk`; `J_wk` is the singleton indicator measurable at that check; `D_wk` is a deterministic or past-known upper bound on correcting-write completion delay. Conditional on the check-time history, future simple-NHPP increments are independent. Unioning over the 31 bits distinct from the observed singleton gives

`Pr(B) <= 31 * E[sum_wk J_wk * integral_[c_wk,min(c_wk+D_wk,H)] r(t)dt]`.

Dropping `J_wk<=1` gives the deterministic all-check envelope

`Pr(B) <= 31 * sum_wk integral_[c_wk,min(c_wk+D_wk,H)] r(t)dt`

`= 31 * integral_H K_D(t) r(t)dt`.

A realized random singleton sum is not itself an unconditional probability bound. A future-observed actual delay is not a valid predeclared window upper unless separately justified.

### 4.3 Periodic duty simplification

If `c_wk=phi_w+k*tau`, a common `D<tau` is valid, and `r` is constant on blocks containing an integer number of `tau` periods, integration of the periodic all-check window count on each complete block gives exactly the duty fraction `D/tau`. Removing pre-start windows and truncating at H can only reduce exposure. Thus

`Pr(B) <= 31*W*(D/tau)*integral_H r(t)dt`

under those conditions. Uniform staggering is unnecessary for this block integral identity. Average duty alone is insufficient for arbitrary `r(t)`.

The synthetic QA reproduces the SR-aligned example: all-check exposure `504.00` equals duty exposure `504.00` across two aligned 300-s constant-rate blocks. This is mathematical QA, not CY evidence.

### 4.4 Registered upper

The repaired registered-process sufficient form is

`U_CW = min(1, U_P + U_B)`.

For a full-device statement a separately qualified omitted-route term is still required, for example `U_CW + delta_cov` by a union bound.

## 5. Trace validation

### 5.1 Frozen pre-execution run and explicit test defect repair

The exact local pre-execution commit was `0cab8b63fc7121422aec0a57a4c6f243bd7f3d5c`. Its first run was preserved as a failed run. The matching frozen checker blobs were also published on the new GitHub branch before the post-run checker fixes; the final frozen GitHub snapshot before fixes ends at `ae208424274336f0bd0eb0fa923e1a974a3412bd`.

Two checker defects were exposed:

1. the clean/no-write targeted test inspected state **after** the next singleton check and correcting write rather than before that next check;
2. the independent checker concatenated arrivals and deterministic checks without sorting them into one chronological stream.

Neither changed the scientific contract. The frozen main exhaustive calculation had already produced `4096` streams, `60` old-inclusion violations and `0` repaired-inclusion violations. The defects and their exact observations are saved in `outputs/PREEXECUTION_FROZEN_RUN_FAILURE.json`.

They were repaired in separate local commit `43ebefecefd6ab440811d3a9638aa334d2d15a87` and explicit GitHub commits before the successful rerun.

### 5.2 Successful rerun

Main event executor:

- mandatory SR counterexample: PASS;
- clean/no-write post-error persistence: PASS;
- distinct RMW hit: PASS;
- same-bit RMW cancellation: PASS;
- pending write at H: PASS;
- initial interval P: PASS;
- final interval P: PASS;
- sticky first passage after writeback: PASS;
- exhaustive count: 4096;
- old inclusion violations: **60**;
- repaired inclusion violations: **0**.

Independent bitmask executor imports neither `executor_model.py` nor `check_executor.py` and reproduces:

- streams: 4096;
- old inclusion violated: YES;
- repaired inclusion violations: 0.

The independent implementation is not an independent physical data source. It shares the same scientific contract, fixed slot family and required SR counterexample.

## 6. MINOR dispositions

1. **Optional numerical interface removed from acceptance.** The new checkers have no `--rate-summary` option. No supplied summary can emit a positive scientific status. Physical slice output is fixed to `bound=null`, `NOT_ESTABLISHED`.
2. **Synthetic terminology corrected.** The historical value formerly called `exact_pair_first_passage` is represented here as `distinct_arrival_event_probability`. Independent deterministic arithmetic gives `0.000590007300664385... <= 0.0006`. This is an enlarged arrival-label event, not exact toggle first passage and not a physical input.
3. **Opposite-decision claim narrowed.** This package does not claim a complete actual-CY opposite-decision pair. Without an explicit admissible full passing `m0` and policy, only the conditional observation-invariant extension lemma changing an excluding lower bound is retained.
4. **Certificate wording corrected.** `upper>epsilon` means this sufficient certificate fails; it does not prove physical impossibility. `upper==epsilon` satisfies an inclusive `<=epsilon` condition. Exclusion requires a qualified lower `>epsilon`.
5. **Missing input identity corrected.** The absent full artifact is `experiments/RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv`, historical SHA-256 `c10a68e721716c8c9b96bf99a9e2d1de0bd3b179ebcc747b3fd149ff0741ff83`, 237888 rows, 53420841 bytes. For the selected registered process the intended rate field is `nu_C_bit_DREG_s-1 / 2^24`; no other proton-rate table is substituted.
6. **ECC-disabled campaign linkage not overclaimed.** Archive/source identity does not itself prove every run/segment was acquired under the same ECC-disabled protocol. In this repair that linkage remains `ASSUMPTION/UNKNOWN` where not separately anchored.

## 7. Scientific boundary after repair

The repair establishes the symbolic conditional-write lemma and its trace implementation under the declared registered-process assumptions. It does **not** establish:

- qualified `I1/I2` for the frozen physical slice;
- a correcting-write WCET `D` for the real executor;
- a numerical CY62167 `U_CW`;
- full-device `delta_cov`;
- a nonzero full-word D3 occurrence floor;
- a complete actual-CY passing `m0` / excluding indistinguishable `m1` pair;
- DUE, SDC or system-failure probabilities.

Issue #15 therefore remains open. A later Orchestrator decision may pursue one of the already named physical closure routes; this repair does not select it.

## 8. Reproduction

Environment used:

- Python 3.13.5;
- Linux x86_64;
- standard library only for event/probability checks.

Commands:

```bash
python3 -m py_compile executor_model.py check_executor.py independent_check.py probability_qa.py
python3 check_executor.py --config config.json --counterexample traces/counterexample_input.json --out outputs/executor_check.json --trace-out outputs/counterexample_trace.json
python3 independent_check.py --config config.json --out outputs/independent_check.json
python3 probability_qa.py
```

No rate/environment regeneration, mapping fit, Monte Carlo, controller design, Phase A/B or RES execution was performed.
