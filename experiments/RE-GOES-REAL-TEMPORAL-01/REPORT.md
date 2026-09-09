# RE-GOES-REAL-TEMPORAL-01 — report

## Disposition

**Research Engineer delivery: COMPLETE FOR ORCHESTRATOR DISPOSITION AND ONE SCIENTIFIC REVIEW.**

The accepted `GOES-REAL-TEMPORAL-PREEXECUTION-01` contract was executed without changing the Stage-A memory/ECC/restoration slice, `U`, `B_d`, known `rho=0`, latency grid, window-selection rule, or conservative open-loop plus one-replan rule. No RADAR/transport/COSRAD, estimator, literature search, PR/merge, main change, HYP or RES promotion was performed.

This delivery does **not** assign Scientific Review PASS.

GOES-19 SGPS is not interpreted as an operational input to the target-spacecraft memory controller. The series is used only as a real chronological environmental reference and as signal content for a hypothetical delayed external-information comparator. Feasibility, latency, cost and spatial/environmental representativeness of any operational channel remain unestablished under RQ-004.

## Frozen inputs and pre-control selection

The accepted five-minute rate input has 16,992 rows and 16,971 paired-valid rows; canonical LF SHA-256 is `9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`. The exact fallback artifact has Git blob `a78c8a2ff51c0213b5cd85c3ecd50f448ed0332f`, 1,496 directional rows, 1,449 unique timestamps, E=576 and W=920.

The six 600-s windows were committed before any reliability/control calculation in `selected_windows.csv` and `selection_manifest.json`:

- `LOWER_MEDIAN`: 2026-01-15 00:30 UTC;
- `MAX_MEAN`: 2026-01-19 19:20 UTC;
- `MAX_INCREASE`: 2026-01-19 19:10 UTC;
- `MAX_DECREASE`: 2026-01-19 19:40 UTC;
- `MAX_FALLBACK`: 2026-01-20 19:00 UTC;
- `EARLIEST_INVALID`: 2026-01-13 17:20 UTC.

Re-execution reconstructs the same starts in `selection_recomputed.csv`; the frozen provenance file is not overwritten.

## Compatible family and worst-case reduction

For shielding-specific benchmark ceiling `B_d`, the retained family is

`0 <= x_j <= B_d`, `|x_(j+1)-x_j| <= g B_d`, `0 <= g <= 1`.

For delivered anchors `(i,y_i)`, non-emptiness is characterized by the pairwise Lipschitz constraints, with minimum compatible variation parameter

`g_min = max |y_i-y_k| / (B_d |i-k|)`.

The componentwise upper sequence is

`u_j = min(B_d, min_i[y_i + g B_d |j-i|])`.

The derivation shows that this whole upper sequence is itself in `M(I)`: it matches all anchors, stays in `[0,B_d]`, and is `g B_d`-Lipschitz. Every compatible sequence is componentwise below it. At `rho=0`, the retained Stage-A certificate is nondecreasing in both five-minute window rates for every deterministic R2-U schedule. Therefore

`sup_{x in M(I)} Q(x;tau1,tau2) = Q(u0,u1;tau1,tau2)`

with no envelope-relaxation gap. The reviewed sequential-reset expression is retained, including exposure crossing `t=300 s`; there is no free reset at the block boundary.

## Causal availability and masking

A source value stamped `t_j` can constrain the delayed comparator no earlier than `t_j + 300 s + L`, for `L={0,300,900,1800} s`; equality-time delivery is admitted before the action. Fallback-derived and invalid central values are suppressed from the controller and are not replaced by zero, interpolation, forward fill, one-direction substitution, or the retrospective global-median fallback. Their retrospective exposure/reference role is unchanged.

The Ideal current-rate comparator is an information benchmark: it receives exact frozen reference rates through the current bin at the decision. When a required reference bin is missing (`EARLIEST_INVALID`), exact Ideal replay cost and retention are marked unavailable rather than imputed.

## Section-independent baseline

Only five `(shield,epsilon)` Precomputed cells are certified on the accepted action grid:

| shield | epsilon | Fixed passes | Precomputed passes | Precomputed `(tau1,tau2)`, s |
|---|---:|---:|---:|---:|
| d3 | 1e-2 | 3000 | 2100 | (0.5,0.2) |
| d3 | 1e-1 | 300 | 210 | (5,2) |
| d5 | 1e-3 | 1200 | 900 | (1,0.5) |
| d5 | 1e-2 | 120 | 90 | (10,5) |
| d5 | 1e-1 | 10 | 10 | (60,60) |

All d1 baseline cells and smaller d3/d5 epsilon cells are `UN-CERTIFIED` under this sufficient certificate/action grid. That is not a physical infeasibility statement.

## Main resource findings

### No useful variation restriction: `g=1`

Across the five exact-reference windows and 25 baseline-certified `(window,shield,epsilon)` cells:

| latency | positive Precomputed-to-Delayed saving |
|---:|---:|
| 0 s | 13/25 |
| 300 s | 0/25 |
| 900 s | 0/25 |
| 1800 s | 0/25 |

At `L=0,g=1`, all five baseline cells save on `LOWER_MEDIAN` and `MAX_INCREASE`, three save on `MAX_DECREASE`, while `MAX_MEAN` and `MAX_FALLBACK` have no positive saving. Thus one additional 300-s latency eliminates all tested `g=1` savings; this is a property of the declared comparator/timing contract, not a measured sensor-latency requirement.

### Replay-compatible variation contracts

Requiring the real section itself to satisfy the assumed variation family, the number of section/case cells with some nonempty replay-compatible positive-saving interval is:

| latency | cells with some compatible saving | total |
|---:|---:|---:|
| 0 s | 23 | 30 |
| 300 s | 18 | 30 |
| 900 s | 15 | 30 |
| 1800 s | 15 | 30 |

`MAX_MEAN` is a genuine negative result: no baseline-certified cell has positive replay-compatible delayed-information saving at any declared latency. `MAX_INCREASE` retains five useful cells at `L=0`, three at `L=300`, and none at 900/1800. `MAX_DECREASE` retains three only at `L=0`. `LOWER_MEDIAN` and `MAX_FALLBACK` can retain value at long latency only under sufficiently restrictive prior/history variation bounds; this remains conditional on independent justification of those bounds.

### Concrete verified boundary

For `MAX_INCREASE`, d3, `epsilon=0.01`, retrospective compatibility requires

`g >= 0.3274298543911712`.

At `L=300 s`, positive saving survives only to the independently bracketed action-transition root

`0.4004020241222228 < g* < 0.4004020241222305`,

bracket width `7.62939453125e-15`.

At representative compatible `g=0.35`:

- Precomputed: 2100 passes;
- Delayed comparator: 1200 passes;
- Ideal comparator: 900 passes;
- saving vs Precomputed: 900 passes;
- reads avoided = writes avoided = 1,887,436,800;
- R2-U occupied-time saving = `169.869312 s`;
- occupancy saving = `28.311552` percentage points of the 600-s window;
- retention of the Precomputed-to-Ideal gap = `0.75`.

At `g=1` the delayed cost returns to 2100 passes. At `L=900` and 1800, no replay-compatible `g` gives positive saving for this case.

A long-latency example is d5, `epsilon=0.01`, `L=1800`, `g=0.1`: `LOWER_MEDIAN` gives Precomputed 90, Delayed 45, Ideal 2 passes, i.e. 45 passes / `8.4934656 s` / `1.4155776` occupancy points saved. `MAX_FALLBACK` also gives 90 -> 45 passes at `g=0.1`; its useful interval exists despite the masked fallback because the value comes from the declared compatible prior/history structure, not hindsight use of the fallback-derived current observation.

## Certifiability gain is not resource saving

For d1 no certified Precomputed baseline exists, but some quiet-window/`g` regions become certified after external information is admitted. These rows are reported as **certifiability gain**, never as resource saving, because there is no certified baseline cost to subtract.

## Generated map and checks

The full transient calculation produced:

- 14,667 policy regions;
- 13,947 decision boundaries;
- 20,341 aligned resource regions;
- 12,857 selected certificate/selection boundaries independently bracketed with Decimal evaluation to the accepted `<=1e-14` width target.

Focused checks reproduce the frozen selection; causal delivery and fallback/missing masking; compatible-set non-emptiness and attainable envelope; an independent sequential-reset exposure sum with explicit no-free-reset falsification; hidden-future invariance; recursive continuation preservation and resource identities; interval-verified selected boundaries; the limiting `g=1` contract; and missing-window Ideal-NA semantics. The stored test output ends with `ALL 8 FOCUSED TEST GROUPS PASS`.

The larger `policy_regions.csv`, `decision_boundaries.csv` and `resource_comparison.csv` are regenerated rather than committed; authoritative SHA-256 values and row counts are in `run_manifest.json`. The compact committed map is `applicability_resource_summary.csv.gz.b64`, with exact `g=1` endpoint projection in `g1_endpoint_summary.csv`.

The executable calculation and focused-test source are stored losslessly as deterministic gzip/base64 text plus small integrity-checking loaders. The solver loader verifies decoded SHA-256 `6ffb2bbedd971b01201109aab94c3616a7ec6b39e3bc8549864d42716fcb2d79`; the test loader verifies `af9580c5f81be153f547b4891af59fb46745398c8301c507e9a26b7303357a9a`. Packaged execution on the completed transient maps produced byte-identical focused-test output.

## Reproduction

From the repository root, with Python, NumPy and Pandas and the canonical frozen upstream files present:

```bash
cd experiments/RE-GOES-REAL-TEMPORAL-01
./reproduce.sh
```

The wrapper regenerates the selection audit, full policy/boundary/resource maps and compact summaries, runs focused tests, byte-compares compact release tables, and checks transient-map hashes.

In the ChatGPT execution harness, the single wrapper shell reached completed core generation (`14,667` policy regions; `13,947` boundaries) before the outer 300-s harness timeout. The remaining stages were then executed immediately on the same temporary output: `20,341` resource regions, focused tests, compact byte comparisons and all transient hashes passed. This is recorded as an execution-harness limitation, not a scientific/reproduction mismatch.

## Maximum defensible interpretation

The result establishes a conditional control-resource value map for a hypothetical external environmental information channel with the declared temporal structure, availability and uncertainty/prior contract. It does not establish a GOES-fed controller, GOES-to-target spatial equivalence, measured operational latency, a physical `B_d` or `g` bound, an operational sensor choice, acquisition/communication/controller cost, weighted mission benefit, exact `F_A`, physical infeasibility from certificate failure, or global optimality of the conservative one-replan rule.
