# RE-CY62167-SEMANTICS-REPAIR-01

**Task:** bounded semantic/provenance repair after `CY62167_SCIENTIFIC_DISPOSITION_01`  
**Exact base:** `1580a76def06aeaac450d0dbc37012715cc2e88c`  
**Branch:** `research/cy62167-semantics-repair-01`  
**Review status:** ready for limited Scientific Reviewer re-review; this report does **not** assign Scientific Review PASS.

## 1. Scope and disposition

No raw input, mapping coefficient, registered-event population, numerical risk formula, action/epsilon grid, historical result value, historical execution manifest, decision record, question, permanent result, or Scientific Reviewer report is changed. No Phase A/B, GOES/RADAR, mapping, Monte Carlo, or COSRAD production run is performed. COSRAD operator closure and a new GEO reference calculation remain outside scope.

| SR finding | Repair disposition | Closure mechanism |
|---|---|---|
| MAJOR-01 direct/toggle semantics | REPAIRED FOR RE-REVIEW | Adopt absorbing-direct construction explicitly as a conservative surrogate; state coupling and `F_toggle <= F_surrogate`; separate coupling, product-survival assumptions and `Q_U`; add cancellation fixture; qualify decision/export language. |
| MAJOR-02 synthetic bracket provenance | REPAIRED FOR RE-REVIEW | Preserve `243.554...` and `[315.224841...,315.744501...]` only as frozen arithmetic regression outputs; legacy names retained with explicit non-bound status; no tightness/optimality/reference-resource conclusion depends on them. |
| MINOR-01 provenance | REPAIRED WITH UNKNOWN FIELDS | Preserve only commands/results actually present in saved reports/logs; historical environment versions not found are `UNKNOWN`; repair-test environment recorded separately. |
| MINOR-02 ERR resource semantics | REPAIRED FOR RE-REVIEW | Export path now carries read-only lower-bound, necessary read-time, worst-case full-pass sufficiency and unknown expected-write-cost fields; repair-derived four-row table added without production rerun. |
| MINOR-03 phase/grid/support qualification | REPAIRED FOR RE-REVIEW | Controlling report/metadata scope GOES decisions to implemented phase model and tested U; convergence is not a uniform error bound; measured support is distinguished from interpolation/extrapolation. |

## 2. Controlling interpretation for MAJOR-01

### 2.1 Registered-event partition versus physical toggle outcome

For a declared mapping `W`, direct/residual classification partitions the **registered events used by the declared model**. A direct-class mark contains at least two distinct data cells assigned to the same declared word. This classification alone does not establish that applying the mark as a physical XOR/toggle from every safe state causes capability exceedance: a mark can cancel a pre-existing erroneous bit.

Define the corresponding toggle process and the absorbing surrogate on the same probability space with identical registered events/marks, identical initial state and identical restoration actions. The two trajectories are identical until the first direct-class event. At that event the surrogate is killed/absorbed, while the toggle process applies the physical mark and may or may not fail. Any toggle failure occurring before that direct event is shared by both trajectories; any toggle failure after it occurs after the surrogate has already failed. Hence, for the declared fixed partition/population/model,

`F_toggle <= F_surrogate`.

This is a **model coupling upper-bound direction**, not a lower bound on physical direct risk and not a statement about unobserved/censored parent events.

### 2.2 Product-survival formula is a separate assumption layer

The expression

`F_surrogate = 1 - exp(-Lambda_D) * S_residual`

is exact only for the declared absorbing surrogate when the direct and residual streams are justified as independent thinnings (or otherwise independent processes) under the fixed, state-independent partition and fixed action. The coupling inequality above does not by itself prove this product form. With a shared random environment, multiplication must be conditional on that environment before averaging. State-dependent partitioning and adaptive policies require their own proof and are not covered here.

### 2.3 `Q_U` is a sufficient certificate, not the exact surrogate risk

For the registered-event population under the frozen uniform-rate pair-count assumptions used by the paper completion model—clean window start, data-only SEC word, residual simple independently marked Poisson arrivals, at most one distinct residual bit per word/event, homogeneous per-bit marginal rate, independent increments, and complete restoration with inter-restoration gap bounded by `tau`—the retained certificate is

`Q_U = T*nu_D + beta*tau*T*nu_C^2`, with `beta = 31/(2*2^24)`.

Under those assumptions `F_toggle <= F_surrogate <= min(1,Q_U)`. A result `Q_U > epsilon`, `T*nu_D >= epsilon`, `DIRECT-BOUND-EXHAUSTED`, `NONE`, or `NO_POSITIVE_PERIOD` means only that the selected sufficient rule does not certify the relevant action(s). It does not prove physical infeasibility. An empty passing set means **no action in the declared tested U passes that declared model/rule**. A physical direct floor would require a separately justified lower bound on physical direct hazard; no such lower bound is created by this repair.

### 2.4 Deterministic cancellation fixture

Focused regression fixture:

`clean {} -> one erroneous bit {0} -> two-bit direct-class toggle {0,1} -> physical state {1}`.

The physical toggle path therefore remains below the SEC capability-exceedance condition after the second event, whereas the declared absorbing surrogate is absorbed at that same direct-class event. The fixture deliberately demonstrates `toggle != surrogate` while preserving the upper-bound direction.

## 3. MAJOR-02 frozen synthetic arithmetic benchmark

The following numerical outputs are preserved exactly as regression constants/functions:

- `synthetic_tau_upper() = 243.55401798... s`;
- legacy-named `synthetic_reference_tau_bracket() = [315.224841226..., 315.744500579...] s`.

The external Stage-5 proof was not requested or reconstructed. The legacy function names remain for compatibility, but code documentation and the controlling interpretation map state that these are **frozen arithmetic/formula outputs only**. They are not retained as a verified probabilistic reference bracket, proof of tightness, accepted optimal period, or basis for reference-relative resource savings. GEO `tau_max_ref`, `eta_tau`, and reference-relative resource penalties remain unavailable for their already recorded COSRAD/operator reason.

## 4. MINOR-01 provenance

### Historical records actually available

- Phase A production command recorded in the historical package: `CY62167_RAW_ARCHIVE=<controlled.zip> python run_phase_a.py`.
- Phase A test command recorded in the historical package: `CY62167_RAW_ARCHIVE=<controlled.zip> python -m unittest discover -v -p 'test_*.py'`; saved result: 33 tests, PASS.
- Phase B production command recorded in the historical report: `python run_phase_b.py --cosrad-results /path/to/results.zip`; saved result package reports 30 tests PASS and compileall PASS.

### Historical environment values not recovered from saved records inspected by the SR/repair

- Python version: `UNKNOWN`.
- OS/build: `UNKNOWN`.
- NumPy version: `UNKNOWN`.
- SciPy version: `UNKNOWN`.
- pandas version: `UNKNOWN`.
- COSRAD build/version string: `UNKNOWN`.
- Exact historical Phase-B test-selection command and exact compileall command: `UNKNOWN`.

No current environment value is substituted for any historical `UNKNOWN`.

### Repair-test environment (new repair only)

- Python: `3.13.5` (GCC 14.2.0).
- OS: `Linux 6.18.35 x86_64, glibc 2.41`.
- NumPy: `2.3.5`.
- pandas: `2.2.3`.
- SciPy: not required by the focused repair tests.
- COSRAD: not invoked.

## 5. MINOR-02 ERR-assisted resource interpretation

The unchanged frozen serial timing quantities are:

| mode | reads/pass | read-only time | declared worst-case full pass (read + at most one write/read) |
|---|---:|---:|---:|
| R1 | 524288 | 0.02359296 s | 0.04718592 s |
| R2 | 2097152 | 0.09437184 s | 0.18874368 s |

For U (unconditional writeback), the full-pass quantities are totals of the declared serial model. For E (ERR-assisted), `0.02359296/0.09437184 s` are only **read-only lower bounds / necessary read-time conditions**. Expected write count and expected total interface cost remain unknown without an ERR/write model. A sufficient full-pass feasibility statement may use the declared worst case of at most one write per read, equal to the corresponding U full-pass bound.

Future `run_phase_b.py` exports now attach explicit semantic fields. Historical `resource_results.csv` is left byte-for-byte unchanged; `resource_semantics_repair.csv` is a repair-derived semantic table from the already committed timing constants, not a Phase A/B rerun.

## 6. MINOR-03 phase/grid/energy-support scope

GOES decision/boundary statements are conditional on the implemented cyclic phase model, the frozen reporting windows and the tested action grid `U`. The 16-phase comparison/convergence diagnostics are numerical sensitivity checks; they are not a rigorous uniform discretization-error bound over all phases or model uncertainty. The `tau=1 s` action-grid minimum is exploratory and is not an architectural lower limit.

Energy labels retain the distinction between measured support and values produced by declared interpolation/extrapolation models. A `MEASURED-SUPPORT-*` classification describes where measured-support inputs enter the frozen sensitivity decomposition; it does not convert interpolated/extrapolated values into measurements or calibrated tails.

## 7. Changed locations and SR closure criteria

| Location | Change | SR closure criterion addressed |
|---|---|---|
| `experiments/RE-CY62167-SEMANTICS-REPAIR-01/REPORT.md` | controlling coupling/product/certificate interpretation; provenance; resource and phase/grid qualifications | all five findings |
| `.../interpretation_map.json` | explicit mapping from legacy field/function names to current bounded meaning | MAJOR-01, MAJOR-02, MINOR-02 |
| `.../resource_semantics_repair.csv` | repair-derived resource semantics, no historical value replacement | MINOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/REPORT.md` | current report no longer calls synthetic pair valid reference; direct budget and ERR resource statements qualified | MAJOR-01, MAJOR-02, MINOR-02, MINOR-03 |
| `RE-CY62167-PAPER-COMPLETION-01/reference_solver.py` | legacy benchmark/docstrings demoted; product formula explicitly surrogate-only | MAJOR-01, MAJOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/resource_model.py` | explicit ERR read-only / worst-case / unknown expected-write semantics | MINOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/run_phase_b.py` | future export rows retain semantic qualifications | MINOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/test_reference_solver.py` | frozen benchmark status + cancellation distinction regression | MAJOR-01, MAJOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/test_resource_model.py` | frozen numbers + ERR semantic tests | MINOR-02 |
| `RE-CY62167-PAPER-COMPLETION-01/test_semantics_repair.py` | compact cross-cutting repair regression | MAJOR-01, MAJOR-02, MINOR-02 |
| `RE-CY62167-DIRECT-DECISION-BOUNDARY-01/boundary_contract.json` | `theta`, NONE, tau=1, phase and energy-support interpretation fields corrected | MAJOR-01, MINOR-03 |

## 8. Maximum retained scientific statements

1. The 45/9/1 and related direct/residual counts remain statements about the controlled **registered-cluster population** and restricted declared mapping family; they do not establish the complete physical parent-event direct population.
2. For the declared fixed registered-event toggle model and its coupled absorbing surrogate, the surrogate gives an upper bound on first-passage probability: `F_toggle <= F_surrogate`.
3. Under the additional independent-thinning assumptions, the product-survival expression is exact for that surrogate only.
4. Under the additional frozen uniform-rate pair-count assumptions, `Q_U` is a sufficient upper certificate. Positive `tau_max^U` values remain certified periods for that rule; certificate failure is inconclusive about physical feasibility.
5. `theta` boundaries remain sensitivity results conditional on the frozen model, phase implementation and tested action grid, not inferred physical direct probabilities.
6. U resource totals remain exact for the declared serial bus-occupancy model. E read-only values remain lower bounds; worst-case full-pass sufficiency can be checked with the U bound; expected E cost is unknown.
7. The synthetic 243.554 / 315.224841–315.744501 values remain arithmetic regression outputs only.

## 9. Focused verification

Executed only focused repair tests and syntax checks; no production simulation/data pipeline was invoked.

Commands:

`python -m unittest -v test_reference_solver.py test_resource_model.py test_semantics_repair.py`

Result: **15/15 PASS**. This includes the cancellation fixture, frozen arithmetic values, frozen legacy R2 percentages/floors, ERR resource qualification, and a direct check that `_qualify_resource_rows` preserves ERR read-only/write-unknown export semantics.

`python -m py_compile reference_solver.py resource_model.py run_phase_b.py`

Result: **PASS**.

`python -m json.tool boundary_contract.json`

Result: **PASS**.

## 10. Proof that historical numerical outputs are unchanged

The repair intentionally does not edit historical numerical CSV/JSON result files such as `geo_bound_results.csv`, `geo_reference_results.csv`, `resource_results.csv`, mapping/event-population outputs, direct-boundary numerical tables, or historical validation/manifests. The only CSV added is `resource_semantics_repair.csv`, explicitly labelled repair-derived. Focused tests also reproduce the frozen numerical anchors `243.55401798`, `315.224841226...`, `315.744500579...`, R1/R2 U/E timing numbers, and old R2 U interface percentages `0.9437184%` and `0.4194304%`.

Final Git comparison against the exact base is the controlling repository proof: changed paths are limited to the semantic/report/code/test locations listed above plus the new repair-derived table; no historical numerical result path is modified.

## 11. Known unresolved limitations

- Complete physical parent-event population remains unobserved/censored; the coupling inequality does not repair that observational gap.
- Parity/device-level `(32,38)` reliability remains outside the data-only primary result.
- COSRAD spectral-operator semantics remain unresolved; no new GEO reference is produced.
- The external Stage-5 proof for the synthetic arithmetic pair remains unavailable by design.
- Product-survival and fixed-action coupling are not generalized to state-dependent partitioning, shared random environments without conditioning, or adaptive policies.
- Expected ERR-assisted write count/resource cost remains unknown.
- Historical software/OS/COSRAD build versions listed above remain `UNKNOWN` because no controlled saved record was found; none was inferred.

**Readiness:** bounded repair complete and ready for the requested limited Scientific Reviewer re-review. No Scientific Review disposition is assigned here.
