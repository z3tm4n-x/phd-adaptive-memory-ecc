# CONTRACT — RE-CY62167-PHYSICAL-BRIDGE-01

**Task:** `RE-CY62167-PHYSICAL-BRIDGE-01`  
**Task/handoff base:** `9ea66664d37cb522d0d148ed63b06858de313d00`  
**Scientific input base:** `69e92fe36b3b7933cebccbedd457cc0309dd4d1c`  
**Issue:** #15  
**Branch:** `research/cy62167-physical-bridge-01`

This contract is frozen **before any new task-specific calculation**. Reading already committed inputs/frozen outputs is not a new calculation. No later positive/negative outcome may change the model family, slice, direction of the bounds, or the deterministic slice selection below.

## 1. Fixed scientific question

How much of the available CY62167 physical/structural information is sufficient to obtain valid lower and upper bounds on first exceedance of SEC capability over a horizon and to make a determinate control-class decision, despite ambiguity of physical parent events, observation/clustering and internal ECC-word mapping?

The bridge must keep distinct:

`environment -> physical parent event -> atomic physical toggle mark -> observation/registered cluster -> actual internal W/parity -> ECC state/outcome -> E_cap -> F_A -> system response`.

The registered-cluster interface is not identified with the physical parent-event process.

## 2. Protected object and event

Target device architecture for the **full-device question**: CY62167 internal Hamming SEC organization reported as `(32,38)` (32 external data cells + 6 parity cells per internal codeword). The irradiation cluster experiments used for the physical data interface had internal ECC disabled; parity locations/outcomes were not observed.

Protected domain: all internal `(32,38)` codewords covering the 16-Mbit external data array. Actual internal mapping `W` is fixed inside one complete model but unknown to the analyst.

Capability event:

`E_cap = first time any actual internal codeword contains >1 erroneous physical codeword cells`.

This is a first-passage capability event. It is **not** automatically DUE, SDC, miscorrection or system failure.

Initial state for the primary theorem/slice: all protected codewords physically clean at `t0`. Initial-state uncertainty is not silently averaged; extension to unknown initial age/error state is outside this bounded task except where a theorem is stated uniformly over all SEC-safe pre-states (0 or 1 error).

## 3. Service/policy classes

Basic restoration transaction: read -> ECC check/correction of returned value -> write back only if corrected. A corrected read is not treated as automatic array repair before the write completes.

Two policy classes are separated:

- `Pi_atomic`: any causal restoration policy that leaves `W` and the SEC code fixed and cannot intervene inside one atomic physical parent event. This class is used only for policy-independent direct-floor statements.
- `Pi_fixed`: fixed cyclic/sequential restoration schedules satisfying the assumptions of the already reviewed registered-event surrogate/certificate. This class is used for the reused registered-process upper bound. No adaptive-policy theorem is inferred from it.

## 4. Observation/information object I

`I` consists only of controlled existing inputs:

1. registered post-processed CY62167 clusters, their supplied transformed `(x,y)` data-cell coordinates/multiplicity/timestamps where present, and frozen experimental `sigma_bit(E)` interface;
2. exact empirical `(x,y)->A` mapping for ordinary address-bearing records;
3. architecture fact `(32,38)` and source-stated 16-bit interleaving, but **not** proprietary `A->W/parity`;
4. documented observation limitations: parent identity can be split/merged/censored; pre-clustering records absent; exact clustering implementation incomplete; parity not observed; absolute `sigma_k(E)` for Zenodo files unavailable because file/segment-aligned fluence is missing;
5. frozen registered-event data-only risk constructions, including W32_seq/DREG and the semantics-repaired absorbing-surrogate upper direction.

No parity multiplier, random parity placement, pair factor or inferred manufacturer W may replace missing information.

## 5. Compatible-model family M(I)

A complete model `m in M(I)` must specify:

- physical parent-event point/marked process and absolute time law;
- atomic toggle mark on physical data+parity cells;
- observation/registration operator mapping physical events to the registered records, including possible miss/split/merge/censoring consistent with the controlled evidence;
- actual fixed `W` and data/parity placement consistent with known external organization and internal `(32,38)` SEC architecture;
- decoder/restoration semantics and the basic conditional-write transaction above;
- clean initial state for the selected slice;
- a policy from the declared class.

`M(I)` does **not** assume exchangeability of parity/data sensitivity, does not assert that the restricted 55/210 W families are complete, and does not force physical parents to equal registered clusters.

Two nested model sets will be reported explicitly:

- `M_full(I)`: all complete full-device descriptions above, including hidden/unobserved physical/parity processes not contradicted by I;
- `M_reg(W32_seq)`: conditional data-only registered-event model used only to reuse the already reviewed registered-process upper bound for the declared W32_seq scenario. It is not promoted to physical truth.

## 6. Predeclared lower-bound event D3

For SEC (`t=1`) define `D3(W)` as an **atomic physical parent event** whose toggle mark contains at least three distinct cells of one actual internal `(32,38)` codeword under `W`.

Claim to be tested analytically and by exhaustive finite-state enumeration:

> From every SEC-safe pre-event state containing at most one erroneous cell in that codeword, an atomic `D3(W)` event causes `E_cap` immediately, provided no restoration action can occur inside the atomic event.

Expected proof uses symmetric difference: for pre-error set `E`, mark `M`, `|E|<=1`, `|M|>=3`, then `|E Δ M| >= |M|-|E| >=2`.

Expected falsifier: any enumerated safe pre-state and >=3-distinct-cell atomic mark whose post-toggle state has <=1 erroneous cell.

A separate two-toggle cancellation case must be exhibited to show why `t+1=2` is not universally fatal.

## 7. Risk-bound form fixed before calculation

Let

`q3_m(H) = P_m{at least one D3(W) event in [t0,t0+H]}`.

For every `pi in Pi_atomic`, if the D3 claim survives the checks,

`F_A^pi(m;H) >= q3_m(H)`.

No expression `1-exp(-Lambda3)` is used unless a Poisson/no-event law for D3 is explicitly part of the model. Otherwise `q3` remains a probability functional.

For the registered conditional model, let `U_reg^pi(H)` denote an already valid semantics-repaired upper bound for the registered data-only process. Define coverage event `B_cov` to include any full-device capability exceedance route not represented by that registered model: hidden/split/censored parents, parity-cell paths, W mismatch, observation incompleteness and other excluded physical marks. Let

`delta_cov(H) = P(B_cov on H)`.

Then the intended full-device upper certificate is the union-bound form

`F_A^pi(H) <= min(1, U_reg^pi(H) + delta_cov(H))`,

only when `U_reg` and `B_cov` together cover every full-device `E_cap` path for the same initial state/action semantics. No independence is required for this union bound.

Common robust bounds over `M_full(I)` are

`L*(H)=inf_m inf_pi F_A^pi(m;H)` and `U*(H)=sup_m sup_pi F_A^pi(m;H)`

with policy quantifiers restated per reported decision. If current I allows `L*=0` or `U*=1`, that value is reported rather than replaced by a surrogate.

## 8. Traceable frozen numerical slice

No new environment/COSRAD/GOES calculation is permitted. The deterministic traceable slice is selected now from existing committed `RE-CY62167-ECC-RISK-BRIDGE-01/risk_curves.csv`:

- shield: `10 mm Al`;
- window/horizon: `24 h`;
- window statistic/timestamp: the frozen DREG audit row at `2026-01-19T04:00:00+00:00`;
- sigma model: `main_loglog`;
- direction: `central_mean`;
- registered direct scenario: `DREG`;
- fixed scrub action: `tau=1 s`;
- registered data-only upper value reused from frozen output, not recomputed;
- diagnostic decision line: `epsilon_analysis=1e-3`.

`epsilon_analysis=1e-3` is an **analysis line**, not a mission allocation. The only new arithmetic allowed on this slice is algebraic thresholding of the already committed upper value, e.g. `delta_cov,crit = epsilon_analysis - U_reg`, with direction/sign checked independently.

## 9. Constructive non-identifiability test

A required falsification path is to construct two complete descriptions in `M_full(I)` that generate the same controlled registered data interface but lead to different full-device risk/control decisions. Preferred construction, fixed now:

- Model `m0`: no hidden parity/direct parent process beyond the registered data model.
- Model `m1(lambda)`: identical registered data process/observation, plus an unobserved atomic parity-cell `D3` process within actual internal codewords. Because irradiation data expose data cells with ECC disabled and parity placement/outcomes are absent, this hidden component is not constrained by the current registered data interface unless a controlled source provides such a bound.

The construction must be rejected if any controlled source already imposes a quantitative upper bound that makes `m1` incompatible.

The point is not to assert that parity events are large; it is to test identifiability. A compatible model pair with different decisions proves that the missing physical quantity is decision-capable.

## 10. Information-sufficiency decision rule

For each material statement output one status: `SUFFICIENT`, `INSUFFICIENT`, or `NOT_ESTABLISHED`.

Minimum sufficient summaries to be tested:

- for **policy-independent exclusion** at requirement epsilon: a justified lower bound `q3_lower(H)>epsilon` is sufficient; full proprietary W is unnecessary if this lower bound is obtained directly by another physical/architectural measurement;
- for **policy sufficiency** using the registered upper: a justified `delta_cov_upper(H) <= epsilon-U_reg^pi(H)` is sufficient, provided the registered surrogate assumptions and service semantics hold;
- if neither bound is available, full W reconstruction is not automatically requested. The output must name the weakest physical/structural measurement that would bound `q3` or `delta_cov` tightly enough to change the decision.

## 11. Address checks allowed after this commit

1. Exhaustive D3/two-toggle state check on a small explicit SEC word, plus direct analytic proof for `(32,38)`.
2. Independent arithmetic check of lower/upper inequality direction and union coverage logic.
3. Constructive `m0/m1` compatibility witness using only the controlled observation boundary.
4. One threshold calculation on the frozen 10-mm/24-h/tau=1-s slice.
5. Existing W-family/registered direct counts may be summarized; no broad new W search, raw reparse, COSRAD or GOES rerun.

## 12. Stop/falsification criteria

Stop and return `NOT_ESTABLISHED` rather than expanding scope if:

- D3 is not uniformly first-passage fatal over safe pre-states;
- current evidence already constrains hidden parity/parent processes so the predeclared compatible-model pair is invalid and no equally bounded witness follows from existing inputs;
- the registered upper cannot be placed in a valid full-device coverage union without a new experiment;
- the decisive threshold requires new environment normalization or unrelated epsilon/H.

No RES-004, Stage A, controller optimization, new environment class, full Phase A/B/COSRAD/GOES replay, hardware experiment, irradiation campaign, or broad literature cycle is authorized.
