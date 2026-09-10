# RE-CY62167-DIRECT-DECISION-BOUNDARY-01

**Disposition: PASS-B — BOUNDARY QUANTIFIED BUT ENERGY ATTRIBUTION REMAINS MATERIAL.**

## Scope and frozen model
This task inverts the frozen `RE-CY62167-ECC-RISK-BRIDGE-01` model; it does not estimate physical MCU probability and does not search proprietary `A -> W`. The sensitivity variable `theta in [0,1]` is the **DIRECT-REALIZATION SENSITIVITY PARAMETER**: the fraction of the declared DCLUSTER candidate `K>=2` parent-event population reassigned from accumulation to immediate direct failure.

The disjoint construction is
`r_D = theta r_evt p_M` and
`r_C,bit = r_evt[1-p_M+(1-theta)p_M Kbar_M]`.
Moved events are simultaneously removed from accumulation. The frozen GOES/RADAR, sigma models, multiplicity model, 32-bit SEC first-passage model, 16-phase CYCLIC-SEQUENTIAL scrub, windows, tau grid and epsilon grid were not changed.

The complete previous-bridge outputs were verified against their committed SHA-256 manifest before inversion. Endpoint reproduction passes: `theta=0 -> D0`; `theta=1 -> corresponding DCLUSTER`. Maximum endpoint relative error is `1.505e-16`; accounting conservation residual is <= `1.819e-12 s^-1` in floating-point arithmetic.

## Primary scalar boundary
Previous endpoint classification contains 798 FEASIBILITY-FLIP base cells, 783 shielded (`1,2,3,5,7,10 mm Al`). Production inversion is restricted to this domain; 0 mm is QA/reference.

Each shielded base cell is analysed for both sigma models, both risk semantics and both low-energy branches, giving 3,132 scalar rows. A finite loss-of-feasibility boundary exists in 3,116 rows. Sixteen `K1_only` rows remain feasible through `theta=1`; their paired low-energy-conservative rows have finite boundaries.

For the 3,116 finite scalar rows:
- median `theta_infeas = 0.00242624`;
- p90 `= 0.259989`;
- max `= 0.999676`;
- `theta<0.01`: 2,040 rows;
- `theta<0.1`: 2,624 rows;
- `theta>0.5`: 114 rows.

Collapsing each physical base cell to its smallest declared finite margin gives 783 cells: median `0.00201812`, p90 `0.229651`; 521/783 have margin <0.01, 663/783 <0.1, and 21/783 >0.5. Thus many previous endpoint flips are not upper-end phenomena: a small declared direct-realization fraction can already eliminate every exploratory scrub action.

Values <= the production absolute theta tolerance `1e-4` are labelled `NUMERICALLY_NEAR_BOUNDARY` instead of being over-resolved. `theta` remains a sensitivity normalization, not an inferred probability of physical MCU.

At the scalar boundary the median critical direct hazard is `Lambda_D,crit≈6.34e-4` (median `F_D,crit≈6.34e-4`); p90 `Lambda_D,crit≈0.1033` (`F_D,crit≈0.0981`).

## Intermediate action transitions
Continuous inversion exposes action shifts hidden by endpoint-only comparison. The shielded domain contains 9,626 transition boundaries: 6,510 transitions between finite tau actions plus 3,116 final transitions to `NONE` (all exploratory actions infeasible). Representative transition roots were recomputed directly with the frozen bridge and satisfy the expected ordering around epsilon.

## Low-energy branch sensitivity
`K1_only`: 1,550 finite scalar rows; median theta `0.00335157`, p90 `0.302761`, max `0.999676`.

`low_energy_conservative`: 1,566 finite rows; median `0.00201812`, p90 `0.230190`, max `0.970903`.

For paired finite rows, median absolute branch shift is `0.000774`, p90 `0.062646`, maximum `0.526067`. Therefore the `E<0.9 MeV` treatment materially changes interpretation in a substantial subset and cannot be collapsed into an invented single low-energy model.

## Two-region energy decomposition
For the low-energy-conservative branch, `theta_L` controls `E<0.9 MeV` and `theta_M` controls `E>=0.9 MeV`. For `theta_L={0,0.25,0.5,0.75,1}`, `theta_M,crit` is solved using exact frozen `tau=1 s` evaluation. A coarse bilinear shortcut was explicitly rejected after off-grid validation showed equivalent theta errors up to about `6.5e-3`; final roots use exact correction.

Base-cell attribution:
- **MIXED:** 702 / 783;
- **MEASURED-SUPPORT-DOMINATED:** 81 / 783;
- **LOW-ENERGY-DOMINATED:** 0;
- **NOT-SEPARABLE:** 0.

The classification uses structural boundary-axis behaviour and continuous movement of `theta_M,crit` across `theta_L=0 -> 1`, not an arbitrary percentage cutoff. Measured-support realization matters in every sensitive cell, but low-energy uncertainty also materially moves the boundary in the large majority.

## Sigma, dependence and direction sensitivity
Between `main_loglog` and `published_rpp_fluka_digitized`, paired scalar boundaries have median absolute shift `0.000110`, p90 `0.017325`, max `0.137521`.

Between `product_estimate` and `dependence_upper`, paired finite scalar boundaries have median absolute shift `1.66e-14`, p90 `1.97e-8`, max `6.53e-5`. The four previous `DEPENDENCE/MODEL BOUND TOO WIDE` cells are not assigned artificial theta thresholds and remain **DEPENDENCE-UNRESOLVED**.

East/West sensitivity was bounded to six representative cases. Eleven directional roots are finite; median absolute shift from central E/W mean is `2.83e-4`, maximum `0.15976`. Direction can therefore matter near the high-margin edge but does not justify a full 783-cell direction campaign here.

## Numerical validation
- previous bridge hash contract: PASS;
- endpoint reproduction / no double counting: PASS;
- theta monotonicity: PASS in the decision domain; worst all-domain negative anchor delta is `-5.17e-12` at saturated `F≈1` and treated as floating-point noise;
- tau monotonicity: PASS, zero negative anchor deltas;
- exact scalar root validation: equivalent theta error < `3.5e-5`;
- root tolerance study at `1e-3`, `1e-4`, `1e-5`: stable non-near-boundary representatives converge within production `1e-4`;
- invariant regression: PASS for >=10 feasible-invariant and >=10 all-infeasible-invariant shielded base cells;
- deterministic row-order test: PASS;
- address mapping refit: NO;
- previous experiment files modified: NO;
- test suite: 16/16 PASS (3 optional full-output integration checks skip unless their environment variables are supplied).

## Interpretation and information value
A statement such as `theta_crit=0.03` means only: assigning 3% of the **declared DCLUSTER candidate multi-event population** to the direct class is sufficient to cross that selected data-only feasibility boundary. It is not an estimate that physical direct-MCU probability is 3%.

Further exact direct/topology information has no demonstrated decision value in the invariant domains tested continuously. It is needed only in the named previous FEASIBILITY-FLIP subdomain. Within that domain, 81 measured-support-dominated cells directly motivate better measured-support parent/topology or proprietary-W information; 702 mixed cells additionally require narrowing the low-energy direct-realization/observability component. Do not reopen `(x,y)->A` globally.

Parity remains **UNRESOLVED / OUTSIDE PRIMARY DATA-ONLY BOUNDARY**. No `38/32`, `1.42`, random parity mapping or parity-location hypothesis is introduced. These theta boundaries cannot by themselves certify full `(32,38)` device-level feasibility.

## Next step
The scalar decision boundary is sufficiently quantified to rule out dependence-model refinement as the general blocker. The remaining blocker is energy/topology attribution in the named mixed subdomain. Stage-A robust model sets may be opened only if the Orchestrator accepts the resolved `(theta_L,theta_M)` boundary envelope as the uncertainty set; otherwise the next bounded task should target low-energy/measured-support parent-event observability/topology only in that named subdomain.

Large derived tables are committed as deterministic bounded audit subsets; complete outputs are identified by exact SHA-256, byte size and row count in `full_output_manifest.json` and can be regenerated by `run_boundary_analysis.py` from frozen inputs.
