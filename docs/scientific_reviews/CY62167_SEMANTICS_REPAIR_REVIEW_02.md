# CY62167 semantics repair — limited Scientific Review 02

Task: `CY62167-SEMANTICS-REPAIR-REVIEW-02`

Reviewer: independent Scientific Reviewer

Exact reviewed/base commit: `619cb3538e296b3619f21301a176665f4611143f`

Previous review commit: `1580a76def06aeaac450d0dbc37012715cc2e88c`

Delivery branch: `reviewer/cy62167-semantics-repair-review-02`

Related questions: RQ-002/003/005/006/007

Review date: 2026-09-07

**Recommendation: PASS_WITH_MINOR.** Both previous MAJOR findings are CLOSED within the deliberately narrowed scope. MINOR-01 and MINOR-03 are CLOSED as qualification/provenance repairs; MINOR-02 is PARTIALLY CLOSED because some legacy resource interfaces still lose or blur the distinction between necessary read time and sufficient full-pass time. No CRITICAL or remaining MAJOR blocker to preparing the bounded surrogate/certificate specification is identified. This report does not authorize Stage A execution or promote any result.

## 1. Scope and evidence boundary

Only closure of the five findings in `docs/scientific_reviews/CY62167_SCIENTIFIC_DISPOSITION_01.md` and repair-related regressions were reviewed. The global operating rules, Scientific Reviewer role and HANDOFF_CONTRACTS were read at the exact target. Primary repair evidence is `experiments/RE-CY62167-SEMANTICS-REPAIR-01/{REPORT.md,interpretation_map.json,resource_semantics_repair.csv}` and the complete changed-file inventory against the previous review. Changed source/report/test files were compared with their previous versions. Selected unchanged consumers were inspected solely to trace the repaired resource and benchmark interfaces.

GitHub comparison establishes one commit ahead, zero behind, with merge base equal to the previous review commit. The eleven changed paths are the three repair-package files; paper-completion REPORT, reference_solver.py, resource_model.py, run_phase_b.py, test_reference_solver.py, test_resource_model.py and new test_semantics_repair.py; and direct-decision-boundary boundary_contract.json. No historical numerical output, input/configuration file, previous Scientific Review, canonical decision or permanent result is changed. The numerical frozen fields in boundary_contract.json are unchanged despite JSON reformatting. Reference-solver changes are documentation/comment/error-message qualifications, not changed probability formulas or transition arithmetic. Resource changes add semantics and alter returned field representations, not the frozen timing constants.

This is source/history verification, not an independent regeneration of historical numerical files. The RE's 15/15 focused tests and syntax checks remain recorded engineering results; this reviewer did not repeat that suite or run production. Two tiny resource-interface checks, described below, resolve the named legacy-feasibility issue. They do not run a radiation, mapping, COSRAD, Monte Carlo or Phase A/B pipeline.

No new angular diagnosis is considered or incorporated into the corrective gate. This review accepts neither physical calibration nor an angular/COSRAD operator. All unchanged scientific limitations from the preceding review remain unless explicitly disposed below.

## 2. Finding disposition

| Previous finding | Disposition | Independent basis and remaining boundary |
|---|---|---|
| MAJOR-01: physical direct floor / exact-toggle interpretation | **CLOSED** | Pathwise first-passage inclusion is valid for the declared coupled processes. Repair REPORT §§2.1–2.3 and the paper REPORT explicitly separate coupling, independent-thinning product and Q_U certificate. Boundary metadata no longer equates certificate failure or NONE with physical infeasibility. No physical hazard calibration follows. |
| MAJOR-02: unverified synthetic probability bracket | **CLOSED BY CLAIM WITHDRAWAL** | Solver documentation, controlling reports, interpretation map and tests consistently retain the root pair as frozen arithmetic only. No proof was supplied or accepted. No retained reference-optimality or reference-relative resource claim may use it. |
| MINOR-01: incomplete provenance | **CLOSED AS DISCLOSURE REPAIR** | Historical missing versions/commands are explicitly UNKNOWN; repair environment and actual focused commands are separately recorded. This does not recover the missing historical environment or independently reproduce the recorded tests. |
| MINOR-02: ERR resource semantics | **PARTIALLY CLOSED** | Main Phase B export and resource model now expose necessary-read versus sufficient-full-pass fields. Historical CSVs are preserved with a controlling interpretation. However the legacy synthesis exporter drops qualifications, the expected-write API can still emit an overstrong architecture label, and an unchanged historical test conflicts with future qualified exports. These are limited interface/test issues, detailed in §5. |
| MINOR-03: phase/grid/support qualifications | **CLOSED** | Repair REPORT §6 and boundary_contract.json preserve the implemented 16-phase/tested-grid domain, distinguish sensitivity from uniform error bounds, and separate measured input support from interpolated/extrapolated values. No new full-word error guarantee was established. |

## 3. Independent assessment of the repaired mathematics

### 3.1 Coupling

Let D be the first direct-class event time under the fixed registered-event partition. Couple the toggle process and surrogate using the same registered marks/times, mapping, initial state, restoration actions, residual transition rule and boundary ordering. The surrogate follows the same transitions before D and records absorbing failure at D. For each realization:

* if toggle first passage occurs before D, the surrogate has the same first passage;
* if toggle first passage occurs at or after D, the surrogate has already failed by that time;
* if D never occurs in the horizon, the trajectories coincide throughout it.

Thus the toggle failure indicator is bounded by the surrogate failure indicator, giving `F_toggle <= F_surrogate`. The equality-at-D case is included. First-passage failure must remain recorded after later restoration. This argument does not require a direct mark to be fatal in the toggle process, nor does it require Poisson arrivals or independent thinning. The repair's fixed-action/fixed-partition domain is conservative and sufficient; it does not claim an adaptive-policy theorem. Identical restoration actions and their effective state transitions are essential, not merely identical nominal periods.

The scope is the corresponding declared registered-event model. Calling it a physical-toggle model does not supply omitted physical parents, proprietary W, parity behavior or device calibration. No population-observation gap is repaired by coupling.

### 3.2 Product formula

For the surrogate, survival is the intersection of no direct arrival and survival of the residual trajectory. Under independent Poisson thinning with deterministic integrated direct intensity Lambda_D and fixed actions, the no-direct probability is `exp(-Lambda_D)` and independence justifies

`F_surrogate = 1 - exp(-Lambda_D) S_residual`.

Coupling alone does not imply this identity. Independence alone for an arbitrary non-Poisson direct process would instead give its actual no-arrival probability times residual survival; the exponential additionally requires the declared Poisson/intensity model. Read the repair's phrase “otherwise independent processes” subject to that no-arrival-law condition. This review does not endorse an exponential zero-count law from independence alone.

With a shared random environment, use the conditional expression and average afterwards. State-dependent partitioning, feedback-dependent actions or changes to the observation population require a separate argument. The revised `combined_reference_risk` docstring limits its exactness to the surrogate product model and does not claim exact toggle risk.

### 3.3 Sufficient certificate and decisions

The repair explicitly retains the uniform-rate pair-count assumptions: clean window start; data-only SEC; residual simple independently marked Poisson arrivals with at most one distinct residual bit per word/event; homogeneous per-bit marginal rates and independent increments; complete restoration with gaps bounded by tau. For a fixed reset interval of length L and distinct bits i,j in one word, no residual event hits both bits, and the expected cross-event hit-pair count is `r_i r_j L^2`. Residual first passage requires such a pair. Sum over same-word pairs and reset intervals, use `sum L^2 <= tau T`, and union-bound with occurrence of a direct event. This recovers

`F_toggle <= F_surrogate <= min(1,Q_U)`,

`Q_U = T nu_D + beta tau T nu_C^2`, with `beta = 31/(2*2^24)`.

This verifies the stated direction without relying on the product calculation or tests on constants. Uniform rates are an assumption, not an observed property recovered by this repair. Nonuniform/time-varying rates, random reset rules and non-clean carry-over states need their own pair-exposure treatment before reusing this particular scalar expression.

The corrected meaning is consistent across the controlling repair, paper REPORT and boundary metadata: `Q_U > epsilon`, direct-budget exhaustion and an empty tested passing set are not physical infeasibility proofs. A model probability above epsilon establishes only that model/action's infeasibility; failure of an upper certificate is weaker. The action grid is not all possible restoration periods. No physical floor can be recovered merely by using an upper direct-rate estimate or the mark classifier. Epsilon and theta remain study/sensitivity parameters, not assigned project requirements or measured direct probabilities.

### 3.4 Cancellation fixture and synthetic benchmark

Both repaired fixture tests implement `{}` → `{0}` → `{1}` through marks `{0}` and `{0,1}`. Each observed state is safe for SEC, while the surrogate is defined to absorb on the second mark. The fixture is a correct concrete distinction between processes. Its `surrogate_absorbed=True` is a stipulated branch outcome, not execution of an independent surrogate oracle, and it does not prove the general coupling. The analytical argument above supplies that proof; repeating the fixture is unnecessary.

The numerical synthetic roots and sufficient-formula value remain callable under legacy names, but comments/docstrings explicitly withdraw their probabilistic and optimality status. Tests check frozen values and documentation, not the unavailable Stage 5 proof. The inspected Phase A generator does not consume the roots; the Phase B reference path emits unavailable-reference fields, and the resource path uses sufficient-period outputs, not the synthetic bracket. The retained numerical pair must not be promoted through old names or historical validation wording. Closure here is by removal of the stronger claim, not validation of the old bound.

## 4. Provenance and phase qualifications

Repair REPORT records Python 3.13.5 (GCC 14.2.0), Linux 6.18.35 x86_64/glibc 2.41, NumPy 2.3.5 and pandas 2.2.3; SciPy is not required by the focused tests and COSRAD was not invoked. Recorded commands are:

```sh
# Paper-completion directory
python -m unittest -v test_reference_solver.py test_resource_model.py test_semantics_repair.py
python -m py_compile reference_solver.py resource_model.py run_phase_b.py
# Direct-decision-boundary directory
python -m json.tool boundary_contract.json
```

The test definitions contain 5 + 6 + 4 = 15 tests, consistent with the RE report. This count is not a new execution. Historical A/B versions and exact unavailable B invocations remain UNKNOWN, rather than being filled with these repair versions. MINOR-01 requested honest disclosure when recovery was unavailable; that requirement is met.

The 16-phase representation, clean per-window state and tested grid remain frozen. The recorded convergence checks are not simultaneous/uniform error guarantees over all phases or uncertainty models. The 1 s action minimum is exploratory, not an architectural floor. “Measured-support” categorizes support used by the sensitivity model; it does not measure interpolated/extrapolated rates. These qualifications close MINOR-03 without any production rerun.

## 5. ERR feasibility: exact consumer audit and residual MINOR

The repaired main route is `phase_b_core.resource_rows -> run_phase_b._qualify_resource_rows -> full/subset CSV export`. The qualifier retains both `necessary_read_time_feasible` and `sufficient_full_pass_feasible`, the expected-write UNKNOWN status and lower-bound cost labels. It deliberately retains legacy `period_feasible` as the necessary-read predicate for E. Therefore that Boolean alone is not a full-pass admission rule.

The following source-level consumer findings matter:

1. Main Phase B CSV column selection now keeps the semantic fields. Its figure/reporting resource plot selects unconditional U, and architecture lines use U bounds; the inspected main route does not turn E `period_feasible` into a sufficient full-pass decision. The controlling paper REPORT supports existing periods by comparison against the larger U worst-case pass time, not the read floor.
2. Unchanged `post_cosrad_synthesis.py` still selects only legacy resource fields. It drops `sufficient_full_pass_feasible`, `write_cost_status` and interface-value qualifications. After the repaired API changes E cost from textual markers to numbers, this legacy export loses the explicit lower-bound marker. Its architecture status now says necessary-read only, so the row is not entirely unqualified, but it remains an unsafe standalone consumer interface. This exporter is not accepted as a qualified Stage A input path.
3. With supplied expected writes, `resource_at_period` still bases legacy `period_feasible` and `ARCHITECTURALLY-FEASIBLE` on expected pass time. Expected occupancy is not a deterministic completion guarantee. The separate worst-case field is correct and must govern the declared worst-case rule. The current main export uses the no-write-model branch, so this residual API behavior does not invalidate its corrected sufficient field.
4. `test_geo_phase_b.py::test_architecture_and_old_resource` still demands `ARCHITECTURALLY-FEASIBLE` for every historical resource row. It is compatible with the preserved historical CSV, but contradicts E rows generated by the corrected export. Passing this historical test would not validate repaired semantics; its assertion needs separation into historical regression versus qualified-export tests before any future rerun. No production run was made to demonstrate this statically evident mismatch.

### Minimal focused checks

Purpose: distinguish necessary-read and sufficient-full-pass predicates at periods between their thresholds, rather than repeating already passing large-period constants. Exact target source files were fetched through GitHub into `after/`; no production driver was imported or executed. Only the qualifier function AST was evaluated with `resource_semantics` supplied. Working directory: `/workspace/scratch/24e1723b7ed9/semantics-review-02`; local Python 3.12.13, standard library only.

```sh
python -B - <<'PY'
import ast, pathlib, sys
sys.path.insert(0, 'after')
from resource_model import resource_at_period, resource_semantics
src=ast.parse(pathlib.Path('after/run_phase_b.py').read_text())
fn=next(n for n in src.body if isinstance(n,ast.FunctionDef) and n.name=='_qualify_resource_rows')
ns={'resource_semantics':resource_semantics}
exec(compile(ast.Module(body=[fn],type_ignores=[]),'qualifier-only','exec'),ns)
for mode,tau in [('R1',.03),('R2',.1)]:
    r=resource_at_period(tau,mode,'E')
    q=ns['_qualify_resource_rows']([dict(r,tau_s=tau,scan_mode=mode,write_policy='E')])[0]
    print(mode,tau,{k:q[k] for k in ['period_feasible','necessary_read_time_feasible','sufficient_full_pass_feasible','architecture_status','interface_value_semantics']})
    assert q['period_feasible'] and not q['sufficient_full_pass_feasible']
r=resource_at_period(.1,'R2','E',0)
print('R2 supplied expected writes=0:',{k:r[k] for k in ['period_feasible','architecture_status','sufficient_full_pass_feasible','expected_total_cost_status']})
print(sys.version.split()[0])
PY
python -B - <<'PY'
import sys
sys.path.insert(0, 'after')
from resource_model import resource_at_period
r=resource_at_period(.1,'R2','E',1000)
print({k:r[k] for k in ['tau_min_arch_s','period_feasible','architecture_status','sufficient_full_pass_feasible','expected_total_cost_status']})
PY
```

Both commands exited 0. R1/.03 s and R2/.1 s give legacy/necessary `True`, sufficient `False`, `NECESSARY-READ-TIME-FEASIBLE` and `READ-ONLY-LOWER-BOUND`. This confirms the distinction, not universal model validity. The supplied-zero case demonstrates separate fields; it is not by itself a counterexample to deterministic feasibility because exactly zero expected nonnegative writes forces zero writes. The additional supplied-1000 case gives expected time .09441684 s, legacy `True`/`ARCHITECTURALLY-FEASIBLE`, and sufficient `False`. A write-count distribution with mean 1000 can still sometimes require the full .18874368 s, so the expected-time label cannot certify a .1 s worst-case deadline.

**Remaining severity: MINOR, associated with prior MINOR-02.** Minimum correction is to preserve the qualification fields in every supported exporter, or explicitly retire/exclude the legacy exporter; label expected-time feasibility as such; and update the historical test's scope. Include one between-threshold case for each R mode and one nonzero expected-write case in focused interface tests. No radiation or Phase A/B production run is needed. Closure means that no supported consumer admits an E full pass solely from read time or expected time, and that qualified future exports are not rejected by an obsolete all-rows status assertion.

Until then, Stage A preparation must use U or the explicit E `sufficient_full_pass_feasible` worst-case predicate with its assumptions. It must not ingest historical `period_feasible`, the legacy exporter or the supplied-mean architecture label as a full-pass certificate. This containment makes the remaining issue nonblocking for specification preparation, not fully repaired software acceptance.

## 6. Maximum scientifically admissible wording and limits

> For a fixed declared registered-event population, mapping, initial state and restoration actions, with matched residual transitions and boundary ordering, replacing each direct-class event by absorbing failure gives a surrogate whose first-passage probability upper-bounds that of the corresponding toggle model. Under the additional declared independent Poisson thinning assumptions the product-survival expression is exact for the surrogate. Under the separate clean-start, data-only SEC, uniform residual-rate Poisson pair-count and bounded reset-gap assumptions, Q_U is a sufficient upper certificate. Certificate failure is inconclusive about physical feasibility. Full-pass resource sufficiency is conditional on the declared serial timing and at most one write per read; ERR expected cost remains unknown without a write model.

The wording does not establish actual physical parent-event completeness, proprietary W, parity/device reliability, physical direct hazard, calibration, angular or COSRAD operator closure, guaranteed confidence coverage, or adaptation/resource benefit. Experimental epsilon and theta retain their existing conditional roles. The synthetic bracket remains arithmetic only. Expected information-acquisition/controller cost is not obtained from actuation counts.

**Stage A preparation: sufficient within these boundaries.** The specification must define common horizon/state carry-over, model/action set, observation and causal-information contract, and the risk/resource decision rules. The fixed-action scalar certificate is not automatically a theorem for time-varying/adaptive schedules; any intended extension must be an explicit proof obligation in that specification. The residual MINOR does not require reopening the general CY62167 review, obtaining proprietary topology or resolving an unrelated operator to prepare this bounded specification.

**Stage A execution: not authorized. Physical/angle calibration: not accepted. Result promotion: not performed.** The conditional coupling/certificate content is scientifically eligible for later bounded consideration by the Orchestrator/PI; this re-review creates no RES/HYP and does not extend earlier result domains.

Final disposition: **PASS_WITH_MINOR**; both MAJOR gates closed by the scoped repair, no remaining CRITICAL/MAJOR block to preparation, and the residual resource-interface correction specified above remains open.
