# RE-CY62167-PHYSICAL-BRIDGE-01 — REPORT

**Role:** permanent Research Engineer, separate user-started session.  
**Task/handoff:** `9ea66664d37cb522d0d148ed63b06858de313d00`.  
**Scientific input base:** `69e92fe36b3b7933cebccbedd457cc0309dd4d1c`.  
**Pre-execution contract:** `4bac6ec1f017f98cd685fee79051dd972b8c8342`.  
**Issue:** #15.  
**Status:** OWN RESULT / substantial new claims require separate Scientific Review. No PASS/RES is assigned.

## 0. Result in one paragraph

The available CY62167 evidence is sufficient to establish a **structural policy-independent fatal-event criterion**, but not its physical frequency. For internal SEC `(32,38)`, an atomic parent event that toggles at least **three distinct cells of one actual internal codeword** causes first exceedance of SEC capability from every SEC-safe pre-state (zero or one pre-existing error), for any restoration policy that cannot act inside the atomic event. The corresponding event probability `q3(H)` is therefore a valid policy-independent risk lower term. However current CY62167 evidence does not identify a non-zero lower bound on `q3(H)`: physical parent identity is censored/split/merged by the observation path, proprietary `W`/parity placement is unknown, parity cells were not observed, internal ECC was disabled in the cluster tests, and absolute multiplicity cross sections cannot be reconstructed without file/segment-aligned fluence. Conversely, the reviewed registered data-only surrogate gives a valid **conditional upper** in its declared fixed-schedule model, but a full-device upper needs an additional coverage bound `delta_cov(H)` for hidden parent/parity/W paths. On the preregistered 10-mm/24-h/tau=1-s slice, `U_reg=0.0003098119451681036`; therefore a full-device certificate at the analysis line `epsilon=0.001` would require `delta_cov(24h) <= 0.0006901880548318964`. Current evidence supplies no such bound. Hence the full-device control-class decision is **NOT_ESTABLISHED**, while the conditional registered data-only tau=1-s action is sufficient inside its narrow model.

## 1. Physical bridge: objects are not interchangeable

The bridge is defined as

`environment -> parent event -> atomic toggle mark -> observation/cluster -> W/parity -> ECC state/outcome -> E_cap -> F_A -> system response`.

The following distinctions are mandatory.

### 1.1 Physical parent event

A parent event is the physical radiation interaction to which one atomic spatial mark belongs. Its mark is the set of physical codeword cells whose stored state is toggled an odd number of times by that interaction. Parent identity is not directly present in the controlled CY62167 cluster files.

### 1.2 Registered cluster

A registered cluster is the output of the experiment/tester/post-processing chain. Existing work establishes that clustering is spatial/transitive and that raw/pre-clustering records and the exact historical implementation are incomplete. Therefore:

- one registered cluster is **not proved to equal one physical parent**;
- one parent may be split into several registered clusters;
- several parents may be merged by the observation/post-processing rule;
- a cluster's `K` is registered multiplicity, not automatically physical-parent multiplicity.

### 1.3 Individual cell toggles

The external test files expose data-cell locations after the experiment's service/registration path. The empirical `(x,y)->A` mapping is recovered for ordinary rows, but `A` is an external byte address. It does not reveal the manufacturer mapping from external address/data position to actual internal `(32,38)` codeword or parity cells.

### 1.4 ECC outcome

The target internal architecture is Hamming SEC `(32,38)`: 32 data cells plus six parity cells. The irradiation cluster experiments used for the present physical interface had the internal ECC disabled, so they do not directly observe decoder outcomes or parity-cell marks. With ECC enabled, one erroneous codeword cell is within guaranteed correction; more than one exceeds the guaranteed capability.

`E_cap` is the first physical state with more than one erroneous cell in any actual codeword. It is not by definition DUE, SDC or system failure.

## 2. Policy-independent direct event: what is actually proved

Let a codeword's current error set immediately before an atomic parent event be `E`, with `|E|<=1`, and let the event toggle distinct-cell mark `M`.

For SEC, define `D3(W)` by `|M|>=3` in one actual internal codeword. The post-event error set is the symmetric difference `E Δ M`. Then

`|E Δ M| = |E| + |M| - 2|E intersection M| >= |M|-|E| >= 2`.

Therefore

`D3(W) subset E_cap^pi`

for **every** policy `pi in Pi_atomic` that leaves W/code fixed and cannot repair between toggles of one atomic parent event. This statement does not require a clean pre-state: it holds uniformly over all SEC-safe pre-states.

The same logic generalizes structurally: for a `t`-error-correcting code, an atomic mark of `2t+1` distinct cells is sufficient for first capability exceedance from every state with at most `t` errors.

### 2.1 Address check

`checks.py` exhaustively enumerated all 39 SEC-safe states (clean plus each one-error state) and all 3-distinct-cell marks in an actual 38-cell word: **329,004 cases, zero counterexamples**. The analytic inequality covers every larger distinct-cell mark.

An independent bitmask implementation repeated the property on a separate small explicit word.

### 2.2 Why two toggles are not a universal floor

For a safe pre-state `E={0}` and atomic mark `M={0,1}`,

`E Δ M={1}`,

so the word remains within SEC capability. Thus an observed/reconstructed event with two same-word toggles is not universally fatal. The prior semantics-repair conclusion that the absorbing registered-direct construction is an **upper surrogate** is therefore preserved; it is not reinterpreted as a physical lower bound.

## 3. Risk bounds and their quantifiers

Let

`q3_m(H)=P_m(at least one D3(W) parent event on [t0,t0+H])`.

For every compatible complete model `m` and every `pi in Pi_atomic`, the theorem gives

`F_A^pi(m;H) >= q3_m(H)`.

This is the correct policy-independent direct-floor form. `1-exp(-Lambda3)` is **not** used unless a Poisson no-event law is separately assumed for the D3 process.

### 3.1 Current lower bound

Current controlled evidence does not provide a positive lower bound on `q3_m(H)` common to the full compatible family. The strongest universally justified direct lower term from present information is therefore the trivial

`q3_lower(H)=0`.

This is not evidence of safety. It says only that the data do not establish a non-zero policy-independent physical direct floor.

The reasons are concrete:

1. registered clusters are not identified physical parents;
2. proprietary internal `W` is unknown;
3. parity-cell placement/marks are not observed;
4. the irradiation cluster tests used ECC disabled;
5. absolute `sigma_k(E)` for the Zenodo proton cluster populations is not computable because aligned file/segment fluence is missing.

`P_registered(K>=2|E)` is therefore neither a lower bound on `q3` nor a substitute for it.

### 3.2 Conditional registered-process upper

For the narrow registered data-only process, fixed W32_seq scenario and fixed cyclic scheduling, the semantics repair and Scientific Review allow the absorbing construction only as an upper coupling/certificate under its declared premises.

Define `U_reg^pi(H)` as that registered-process upper. To extend it to the full device, define `B_cov` as the union of all capability-exceedance routes omitted from the registered model: hidden/split/censored parents, parity paths, actual-W mismatch and other unrepresented physical marks. Let

`delta_cov(H)=P(B_cov on H)`.

If `B_cov` really covers every omitted full-device `E_cap` route for the same initial/service semantics, then without any independence assumption

`F_A^pi(H) <= min(1, U_reg^pi(H) + delta_cov(H))`.

This union-bound direction was independently checked. It is deliberately different from multiplying by a parity factor or treating a candidate event rate as a floor.

### 3.3 Robust full-device interval under current information

For current `M_full(I)`:

- no non-trivial positive direct lower floor is established;
- no non-trivial upper `<1` is established because `delta_cov` is unconstrained by the controlled data interface.

Thus the only current full-device bounds that are valid without adding physical assumptions are the trivial probability bounds `[0,1]`. These bounds are **uninformative**, but correctly expose the missing information rather than hiding it inside one W or one cluster interpretation.

## 4. Constructive non-identifiability witness

Two complete descriptions can be compatible with exactly the same registered data interface while changing the control decision.

### Model m0

Use the frozen registered data process and declared W32_seq conditional model; assign no additional hidden parity/direct parent process. On the selected fixed tau=1-s slice, the frozen registered upper is below the analysis requirement line.

### Model m1(p)

Keep the **same** registered data process and observation. Add an unobserved atomic physical parent component which, with horizon probability `p`, toggles three parity cells of one actual internal codeword. The current experiment does not expose parity locations/outcomes and used ECC disabled, so this added component has zero projection into the controlled registered data interface. It is a `D3(W)` event and therefore causes `E_cap` for every `Pi_atomic` policy.

A toy projection checker confirms the logical observation property: adding a parity-only triple changes no data-only registered mark while creating D3.

Choosing `p>epsilon` gives a model compatible with the same data interface in which every restoration-timing policy is insufficient, while `m0` retains the conditional registered fixed-policy certificate. `p` is **not an estimate** of CY62167 physics; it is a constructive identifiability witness.

Therefore the present observations do not identify the full-device decision.

## 5. Traceable frozen numerical slice and decisive threshold

The slice was fixed in `CONTRACT.md` before new arithmetic:

- 10 mm Al;
- 24 h horizon/window;
- frozen timestamp `2026-01-19T04:00:00+00:00`;
- `main_loglog`, `central_mean`;
- DREG registered data-only scenario;
- fixed tau=1 s;
- `epsilon_analysis=1e-3` only as an analysis line, not a mission allocation.

From the already committed `risk_curves.csv`:

- registered data-only lower: `5.90925197663239e-10`;
- registered data-only upper: `U_reg=0.0003098119451681036`.

No environment/rate calculation was rerun.

The maximum uncovered full-device probability that still preserves the simple union certificate is

`delta_cov,crit = 0.001 - U_reg = 0.0006901880548318964`.

Therefore:

- if a qualified physical argument gives `delta_cov(24h) <= 6.901880548318964e-4`, the same fixed tau=1-s action remains sufficient for the **full-device risk line** under the other registered-surrogate premises;
- if a qualified physical lower bound gives `q3_lower(24h)>1e-3`, **every** policy in `Pi_atomic` is insufficient, independent of scrub timing;
- with neither quantity bounded, the full-device decision remains `NOT_ESTABLISHED`.

For scale only, if the relevant hidden process were additionally assumed Poisson, the D3 exclusion threshold would correspond to `lambda3 > 1.1579865e-8 s^-1` (`0.0010005003 day^-1`), and the coverage-certificate threshold to `lambda_cov <= 7.9910457e-9 s^-1` (`0.0006904263 day^-1`). These are conditional translations, not measured rates.

## 6. What the existing W results do and do not tell us

The restricted 55 mapping family is diagnostic, not complete. Its frozen `mapping_sweep_summary.csv` already shows strong mapping sensitivity in the **registered >=2-same-word classifier**:

- 45 of 55 retained mappings have `N_direct_all_series=0`;
- nine have `N_direct_all_series=4`;
- one (`W_00_11`) has 5;
- the baseline `W_00_01` has 4;
- only `W_00_11` has one registered proton direct mark in that summary; the others have zero proton direct marks.

This demonstrates that structural mapping information can change even the registered surrogate classification. It does **not** identify actual proprietary W, and those >=2 registered marks are not D3 floors.

The full linear candidate family was previously shown to be vastly larger than 55/210, so robustness across the restricted families is not robustness to all physically compatible W.

## 7. Information sufficiency: exact W is not the real end goal

The task asks what information is actually sufficient for choosing the control class. The answer is more compact than full topology reconstruction.

### 7.1 Sufficient for policy-independent exclusion

A defensible scalar lower bound

`q3_lower(H) > epsilon`

is sufficient to reject **all** restoration-timing policies in `Pi_atomic` for that requirement. Exact proprietary W is unnecessary if a parent-resolved experiment or device-level measurement directly supplies this bound for full codewords including parity.

Current status: **NOT_ESTABLISHED**.

### 7.2 Sufficient for a policy upper certificate

For the selected fixed action, a defensible full-device coverage bound

`delta_cov_upper(H) <= epsilon-U_reg^pi(H)`

is sufficient to lift the registered conditional upper to a full-device upper by the union bound. On the selected slice the numerical threshold is `6.901880548318964e-4`.

Current status: **NOT_ESTABLISHED**.

### 7.3 Is full W sufficient by itself?

No. Knowing `A->W` alone would still not identify parent-event splitting/merging, parity event marks, absolute parent multiplicity rates or missing exposure normalization. Conversely, full W is not strictly necessary if `q3` and `delta_cov` are measured/bounded directly at the complete-codeword level.

Hence the information target should be **decision summaries over complete physical events**, not topology for its own sake.

## 8. The exact missing physical/structural fact that can change the decision

For the currently passing registered tau=1-s slice, the weakest directly decision-capable missing fact is:

> a qualified upper bound on the 24-h probability `delta_cov` of any full-device `E_cap` route not covered by the registered data-only W32_seq model, including parity and hidden/split/censored parent-event routes.

If that upper bound is <=`0.0006901880548318964`, the full-device upper certificate passes the analysis line. If it is larger, this certificate no longer decides safety.

A practical way to obtain such a bound would require **parent-resolved, exposure-normalized full-codeword evidence with internal mapping/parity observable or otherwise bounded**. The currently missing aligned fluence manifest is necessary if absolute multiplicity cross sections are to be reconstructed from the existing Zenodo proton files, but fluence alone is not sufficient: parent identity and W/parity coverage would still remain.

For policy-independent impossibility, the corresponding decisive missing fact is a lower bound on `q3(24h)`; if it exceeds `1e-3`, restoration timing cannot rescue the requirement.

## 9. E_cap versus decoder and system outcomes

The bridge stops at a precise point.

| State/outcome | What is established |
|---|---|
| <=1 erroneous physical cell at read | Within SEC guarantee. Read output may be corrected, but the source documentation says corrected read output is not automatically written back; physical state persists until explicit correction write. |
| `E_cap`: >1 erroneous physical cells | Guaranteed SEC capability is exceeded. This is a physical first-passage risk event. |
| DUE | **NOT ESTABLISHED** from E_cap. `(32,38)` is SEC, not a demonstrated SEC-DED outcome contract here. |
| SDC/miscorrection | **NOT ESTABLISHED quantitatively**. It is possible once the guaranteed correction radius is exceeded, but the cluster irradiation tests had ECC disabled and do not calibrate decoder outcome probabilities. |
| System failure/recovery | **NOT ESTABLISHED**. Depends on application checking, retry/reset, state restoration and response architecture. |

Therefore no report line equates the new direct-floor theorem with DUE/SDC or mission failure.

## 10. Address checks actually executed

Environment: Python 3.13.5, Linux 6.18.35 x86_64, glibc 2.41, standard library only.

Executed:

```text
python3 checks.py
python3 independent_check.py
```

Results:

1. **D3 first passage:** 329,004 actual-38-cell minimal D3 combinations over all SEC-safe pre-states; zero counterexamples. Analytic proof covers larger marks.
2. **Cancellation:** explicit two-toggle counterexample leaves one error and therefore disproves universal fatality of `t+1=2` toggles.
3. **Upper/lower direction:** Decimal arithmetic independently verifies `U_reg + delta_crit = epsilon`; increasing the uncovered probability beyond the threshold breaks the union certificate.
4. **Non-identifiability:** independent bitmask/projection fixture preserves the registered data observation while adding an invisible parity D3 mark.
5. **No hidden recomputation:** GOES/COSRAD, raw cluster parsing, mapping search, Phase A/B/C, controller simulation and Monte Carlo were not run.

Outputs: `outputs/checks.json`, `outputs/independent_check.json`, with captured stdout.

## 11. Decision table summary

`decision_table.csv` is the machine-readable disposition. Main conclusions:

- conditional registered data-only W32_seq, tau=1 s: **SUFFICIENT** for the selected analysis line inside that model;
- full device, same tau=1 s under current information: **NOT_ESTABLISHED**;
- nonzero policy-independent physical direct floor from current data: **NOT_ESTABLISHED**;
- full-device fixed action becomes **SUFFICIENT conditionally** if `delta_cov` is below the stated threshold;
- all restoration policies become **INSUFFICIENT conditionally** if `q3_lower>epsilon`;
- current information is **INSUFFICIENT for selecting a full-device restoration-control class**, because physically hidden direct/coverage uncertainty can dominate and is not resolvable by controller complexity.

## 12. Maximum wording for later Scientific Review

The maximum new statement proposed for review is:

> For a memory protected by SEC with fixed internal word mapping, any atomic physical event that toggles at least three distinct cells of one codeword causes first exceedance of correction capability from every SEC-safe pre-event state, independently of restoration timing, provided no restoration can act inside the event. For CY62167 the currently controlled data establish neither a non-zero occurrence lower bound for such full-codeword parent events nor a full-device coverage upper bound, because the registered clusters do not identify physical parents, proprietary W/parity is unresolved and the proton cluster files lack aligned exposure normalization. Consequently the current full-device admissibility decision is not established. A complete proprietary W is not intrinsically required: a direct lower bound on the D3-event probability can exclude all timing policies, while an upper bound on the probability of all paths omitted from the registered data-only model can lift the existing registered upper certificate. On the preregistered 10-mm/24-h/tau=1-s diagnostic slice, the latter coverage bound must be no larger than `6.901880548318964e-4` to preserve the analysis line `F_A<=10^-3`.

This is an engineering/scientific delivery, not an accepted RES. All substantial new claims above are intended for separate Scientific Review.
