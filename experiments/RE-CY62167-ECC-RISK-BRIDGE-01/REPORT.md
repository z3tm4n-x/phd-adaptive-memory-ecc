# RE-CY62167-ECC-RISK-BRIDGE-01

**Disposition: PASS-B — BRIDGE ESTABLISHED / DIRECT INFORMATION DECISION-CRITICAL.**

## Result

The frozen GOES-19/RADAR device-rate interface is connected to a data-only SEC first-passage model with CYCLIC-SEQUENTIAL restoration. The primary object is `F_A,data`: DEC-001 capability exceedance in the 32 observed data cells of each declared analysis word. Parity remains unknown, so this is not complete device-level `F_A`.

`A=f(x,y)` and `W32_seq=floor(A/4)` are imported from starting commit `365eaee5906505ff7bfccd8766ca8cb1d6729486`; address mapping was **not refitted**.

## DREG versus DCLUSTER

Across 140106 evaluable registered proton clusters and 162891 retained observed data-cell flips, `N_direct_W32seq=0` at all 14 measured proton energies and ordinary mapping failures are 0. Therefore DREG has zero registered-cluster direct hazard in this declared scenario. This is not a physical lower bound because registered clusters are post-processed and same-parent topology can be split/censored.

DCLUSTER reuses the previous `P_registered(K>=2|E)` construction and remains nonzero. Thus D0/DREG and DCLUSTER bracket materially different scrub-independent direct hazards without inventing arbitrary manufacturer mappings.

## SEC / scrub model

For one clean 32-data-bit word, `Q0=[[-32,32],[1,-32]]` and the exact clean survival is evaluated from integrated per-bit exposure `mu`; a Taylor branch preserves the `C(32,2) mu^2` small-exposure limit. Matrix-exponential/ODE QA, pair asymptotic QA, cyclic phase convergence, synchronous-global comparator, monotonicity, and log-space survival checks pass. Product aggregation is explicitly assumption-labelled; union upper and max-word lower reductions are reported. Reduced marked-event Monte Carlo remains below the union upper bound.

## Decision result

Exploratory grid: tau = 1,2,5,10,20,30,60,120,300,600,1200,1800,3600 s; epsilon = 1e-6...1e-1; windows 5 min, 1 h, 6 h, 24 h, 7 d; both sigma models; 0,1,2,3,5,7,10 mm Al.

Central-mean decision counts:

- ACTION-INVARIANT, feasible: 140
- ACTION-INVARIANT, all actions infeasible: 738
- FEASIBILITY FLIP: 798
- DEPENDENCE/MODEL BOUND TOO WIDE: 4
- pure QUANTITATIVE ACTION SHIFT: 0

Therefore direct-information uncertainty is decision-critical in a large named part of the exploratory domain, but decision-irrelevant in explicit action-invariant subdomains. Exact proprietary W/censored topology work is required **ONLY IN NAMED DOMAIN**, not globally. The `(x,y)->A` layer should not be revisited.

## Parity

`UNRESOLVED / NON-BLOCKING FOR DATA-ONLY BRIDGE`. No 38/32 factor, random parity mapping, or parity-location search is introduced.

## Reproducibility / repository-size deviation

Raw CY, GOES NetCDF/ZIP and RADAR transport are not committed. The complete generated tables were computed and are identified by exact SHA-256, byte size and row count in `full_output_manifest.json`. To keep this bounded experiment commit small and avoid duplicating a 53.4-MB derived trace, Git stores representative audit subsets in `risk_curves.csv`, `window_risk_summary.csv`, and `decision_sensitivity.csv`; `direct_rate_5min.csv` is a schema-preserving generation manifest. `risk_bridge.py` deterministically regenerates the complete tables from the frozen inputs. This is the sole output-packaging deviation; the scientific sweep and decision counts are not reduced.

## Validation

- upstream rate reproduction: PASS, max rel error 2.891e-16
- prior DCLUSTER reproduction: PASS
- W32_seq imported: YES; refitted: NO
- registered W32_seq direct events: 0
- matrix exponential / ODE: PASS
- pair asymptotic: PASS
- cyclic phase convergence: PASS (<0.5%)
- union upper >= product: PASS
- marked-event Monte Carlo below union: PASS
- production monotonicity: PASS
- tests: 12/12 PASS

## Next scientific task

Freeze this bridge. Refine post-W marked-event/cross-word dependence and censored direct topology only in the decision-boundary subset where D0/DREG versus DCLUSTER changes feasibility; do not search `A(x,y)` again and do not start Stage-A resource/adaptive-controller optimization until that bounded blocker is resolved.
