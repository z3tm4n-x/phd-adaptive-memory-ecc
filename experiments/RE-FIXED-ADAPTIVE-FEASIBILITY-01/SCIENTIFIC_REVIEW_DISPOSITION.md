# SCIENTIFIC REVIEW DISPOSITION — COLD-START LIMITED RESULT

**Task:** `RE-FIXED-ADAPTIVE-FEASIBILITY-01`  
**Reviewed delivery:** `03e6c4ad8570fa3351378c9c77b1f9c2fe943f15`  
**Scientific Review:** `619492db33cb8793710fb4e454616f543993c982`  
**Orchestrator decision:** select the cold-start limited result from review §9; do not investigate warm start further.

## 1. Review verdict versus selected limited acceptance

The Scientific Review verdict for the **full delivery remains `REVISE`**. This documentary disposition does not change that verdict and does not claim a new general Scientific Review.

Separately, Orchestrator accepts the reviewer's explicitly permitted **limited cold-start result**. The two statuses are therefore:

- full delivery: **REVISE**;
- selected restricted scientific statement: **LIMITED ACCEPTANCE — COLD START ONLY**, under the conditions below.

No new RES is created and no accepted RES is changed.

## 2. Selected cold-start domain

The limited accepted statement is restricted to the principal slice reviewed in §9:

- protected data: **4 MiB**;
- ECC: **SEC-DED(39,32)**;
- event/metric: `E_cap` / `F_A` in the existing DEC-001 sense;
- horizon: **43824 h**;
- probability requirement parameter: **epsilon=0.001**;
- average interface-service budget: **0.25%** over the whole horizon;
- initialization: **cold start**, with calibrated peak fallback in the first hour;
- later missing previous-hour information: at most **148 additional fallback hours**;
- application load for the reviewed latency statement: **50%** with the declared FIFO/primitive-transaction contract;
- continuous scan phase and the reviewed read/write/jitter/arbitration conditions are retained.

Conservative Scientific Review bounds, which supersede tighter RE arithmetic for accepted wording, are:

- causal risk: **`F_A < 0.000951`**;
- average interface occupancy before controller-computation cost: **`< 0.224203%`**;
- scrub peak in the declared window: **`< 25%`**;
- application delay under the declared 50% workload envelope: **`< 3.006 us`**.

At the 0.25% average budget, the review therefore leaves **more than 0.025798 percentage point** for additional same-interface controller cost. Actual controller computation/WCET remains unmeasured and must fit this reserve if charged to the same interface budget.

The reviewer independently retained the result that, at this principal 0.25% slice, the declared continuous Fixed class through 3600 s is excluded by lower risk bounds even when Fixed pays only reads.

## 3. Conditions retained from review §9

The limited acceptance is conditional on all of the following:

- clean ECC state at the beginning of the horizon;
- long-lived protected data without additional application writes/restorations that change the declared state model;
- the same memory/ECC architecture for Fixed and causal comparison;
- uniform single Poisson inversions with the declared word/bit marking model; no direct MCU population is added;
- the deterministic transferred temporal profile and its reviewed integral/peak constants;
- cold-start peak fallback in hour 0 and peak fallback when a later previous-hour scalar is missing;
- no more than 148 such additional missing-input hours;
- continuous scan phase, without hourly reset of risk or phase;
- the read/write/jitter/FIFO primitive-transaction contract reviewed in §§4–5;
- no address/latch/controller faults outside the modeled error process;
- acquisition/computation costs fit the stated residual resources or receive a separate resource contract;
- `E_cap` is not identified with total system failure;
- `epsilon` and `H` remain research parameters, not mission allocations.

The transferred historical maximum is not promoted to a qualified future physical ceiling; the entire result remains conditional on the retrospective transferred-shape assumption.

## 4. Warm-start disposition — not selected

The following historical rows remain in the package but are **not certified for an arbitrary pre-t0 scalar** and are not part of limited acceptance:

- nominal warm start, historical lower edge `0.142447%`;
- warm start plus 148 h fallback, historical lower edge `0.223653%`.

Their numerical arithmetic is retained as provenance. No additional warm-start search, interval for the initial scalar, or re-tuning is performed.

## 5. Source correction for lag1_eta

The current source of `lag1_eta=1.04935369403` is:

- `z3tm4n-x/chapter4-risk-limited-scrubber@cf7ab706224f7872fdafcf34febda70e3f6c8dd1`;
- `results/schedules/ch3_five_year_summary.csv`, blob `7f64b1f6a7ba544c610325588ee26f7b10d03bb4`, `delayed_1h.eta_shape`.

The corresponding code is `scripts/run_ch3_five_year_schedule.py`, blob `10ea6f0911bf5782f5034a39d95e647f181480fc`, specifically `delayed_estimate()` and `eta_shape()`.

The previous pointer to `ch3_lag_sweep_summary.csv` is superseded as the source citation for this value. Git history is unchanged.

## 6. Review findings disposition

### MAJOR-01

**Addressed by Orchestrator selection of review option 1.** The accepted statement is cold-start only. Warm-start rows remain explicitly uncertified for arbitrary initial estimates. No warm-start calculation is added.

### MINOR-01

**Addressed documentarily for the selected limited statement.** Accepted wording uses the reviewer's conservative bounds `F_A<0.000951`, average occupancy `<0.224203%`, peak `<25%`, and delay `<3.006 us`, rather than promoting tighter RE numbers to production-linked physical bounds. Stronger BCH remains only an analytical architecture variant under its own timing/transfer contract.

No repeat review is claimed; the full-delivery verdict remains REVISE.

### MINOR-02

**Addressed by `EXPORT_RULE.md` and machine metadata.** The export projections, renamed files, omitted trace, manual textual annotations, current `independent_check.py` bytes and verification records are identified explicitly. Historical `outputs/execution_record.json` is intentionally not rewritten.

## 7. No additional execution

This disposition performs no new scientific calculation, retuning, Monte Carlo, warm-start development, GOES/COSRAD processing, RTL/Vivado work, or general Scientific Review. It changes only documentary scope/provenance inside this experiment directory.
