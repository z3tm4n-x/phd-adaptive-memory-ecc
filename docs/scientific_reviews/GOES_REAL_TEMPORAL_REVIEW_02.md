# SR-GOES-REAL-TEMPORAL-REVIEW-02

## 1. Verdict and scope

**PASS_WITH_MINOR. MAJOR-01 and original MINOR-01…03 are CLOSED in the acceptance domain stated below. No remaining CRITICAL or MAJOR issue blocks acceptance of the repaired package in that domain.** One new, nonblocking diagnostic-summary issue is identified: replay-domain boundary widths are classified by the midpoint instead of clipped at the exact replay threshold. It does not change policies, certificate validity, savings or existence conclusions.

- Review starting commit: `b08c651c7694f17e725f27c9520b2e9aadcf0344`.
- Repair reviewed: `65d640d7c988d83b97daa839e35a3abb358b3c7d`, direct parent `77f299bdc3f5abaac36e5d8ef79359f557e56065`.
- Previous review: `bf34676d7842e6f843a716941178c695855bbf75`, `GOES_REAL_TEMPORAL_REVIEW_01.md`.
- Delivery branch: `reviewer/goes-real-temporal-review-02`.
- Date: 2026-09-09.

This is a repair-only review. Read the role/global/handoff rules, previous review, effective preexecution specification, REPAIR_REPORT, derivation repair appendix, current report, changed numerical solver, tests, resource alignment, summaries, wrapper, configuration and provenance. The review start differs from the repair only in current-status documentation. Accepted physics, the envelope theorem, Q/exposure semantics and the input contract were reused, not reopened.

Git/content checks confirm unchanged preexecution specification, original low-level core, frozen window selection and selection manifest. Configuration input, memory, restoration and experiment sections match the reviewed original; changed fields concern numerical precision/jobs and task provenance. No upstream GOES/RADAR/COSRAD, old Stage A matrix, transport, Monte Carlo or new experiment was executed. Only this review report is delivered.

## 2. Disposition of previous findings

| Previous finding | Disposition | Basis and acceptance qualification |
|---|---|---|
| MAJOR-01: wrong certified map near close roots, defective serialized brackets | **CLOSED** | Seven witnesses now map to the correct exported regions. Independent endpoint/rank checks support constancy on every resolved region. All serialized certificate brackets sign-enclose their roots under exact rational recomputation. Bands remain explicitly outside resolved action/saving guarantees. |
| MINOR-01: complete replay mixed with missing-reference completion | **CLOSED** | Complete-reference and stress denominators are separate; factual Ideal costs and retention are blank for EARLIEST_INVALID; compatible-completion costs have a separate field. |
| MINOR-02: destructive fixed temporary directory/container comparison | **CLOSED** | Wrapper uses mktemp with scoped cleanup and decoded scientific CSV comparison. Historical execution remains historical; the review used one staged regeneration to retain maps for targeted checks. |
| MINOR-03: overstated verification independence | **CLOSED** | Repair tests now contain a production-linked reset-time Q oracle and independent competitor enumeration, with shared dependencies disclosed. Their remaining representative/witness limitations are covered by the additional checks below, not ignored. |

There is no finding that the repaired action selection changes the accepted physical model or substantive benchmark conclusions.

## 3. Actual reproduction

A fresh output directory was created once. From `experiments/RE-GOES-REAL-TEMPORAL-01` in the exact review checkout, the following stages were executed on that same output:

```sh
mktemp -d /workspace/scratch/24e1723b7ed9/goes-r2-run.XXXXXX
# Returned /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w
python numerical_repair.py --config config.json --output-dir /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w
python resource_map.py --config config.json --dir /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w
python summarize_results.py --dir /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w
python test_numerical_repair.py --config config.json --dir /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w --rate-csv ../RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv --fallback ../RE-GOES-CAUSAL-INPUT-CONTRACT-01/fallback_rows.csv.gz
```

All stages exited successfully; the suite reported `ALL 8 NUMERICAL-REPAIR TEST GROUPS PASS`. This is a staged reproduction, not a claim that the reviewer ran the wrapper end-to-end. Its temporary-directory and decode/compare logic were inspected separately.

Environment: Python 3.12.14, Clang 22.1.3, NumPy 2.3.5, Pandas 2.2.3. Repair provenance records Python 3.13.5 and the same NumPy/Pandas versions. Input and decoded-source integrity checks passed.

Reproduced counts: 14,781 resolved policy regions; 14,061 boundary records (12,869 certificate/selection and 1,192 model/replay); 2,632 point records; zero unresolved clusters; 46,336 resource rows, including 22,880 boundary rows; 576 compact summary rows; 100 complete-reference g=1 rows.

All eight transient hashes matched `run_manifest.json`. Principal identities:

| File | SHA-256 |
|---|---|
| policy_regions.csv | `7f0236f11d46e680865bf2045eddc6858869a9a2ece19cd36fec2f29c61bfeea` |
| decision_boundaries.csv | `ae7148b35bcb0b20de20295dea4d34203ad251de8b6f41a3613c175ebde2a359` |
| policy_points.csv | `730a9f437dd8df46a383353002287ea6994d686a14609f7953fdb651ec217138` |
| resource_comparison.csv | `e92cdf8b4f055df29f8bd7d32cdc549d300c0340ac410eb9a7e24b9bee8bf3d8` |

Decoded applicability and compatibility tables matched committed scientific bytes. `selection_recomputed.csv`, `g1_endpoint_summary.csv` and `repair_regression_witnesses.csv` matched byte-for-byte. Hash equality establishes reproduction/provenance, not scientific validity; the independent checks below supply the latter within scope.

## 4. Independent path and completeness of resolved regions

The reviewer reused the prior review's independently expressed reset-timestamp oracle, not the new production root solver or the repair test's expected-value selector. Integer-tick integration of the two unit-rate basis functions at three word phases and exact rational phase quadrature reconstructs all 144 Q coefficient triples. The physical/configuration objects are intentionally shared and unchanged. Pinned source loading/section objects are shared; expected Q, compatibility thresholds and selected decisions are independently expressed.

Review-only scripts were run outside the repository:

```sh
python /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w/independent_r2.py
python /workspace/scratch/24e1723b7ed9/goes-r2-run.rt4o9w/downstream_r2.py
```

Additional inline checks recomputed every certificate enclosure's competing transitions and checked historical summary identities. These scripts are review scratch checks, not new experiment artefacts.

### Why this establishes constancy, rather than only representative agreement

For each of the **14,781 resolved open regions**, the reviewer independently enumerated all initial competitors and fixed-first-action continuations at **both serialized interval endpoints**: 29,562 endpoint selections, with zero signature mismatches. Signatures include status, actual first action, planned second action, executed second action and total passes where available. Selection arithmetic used the independently reconstructed coefficients at 85-digit working precision, not saved residuals or production threshold tables.

The interval-wide argument is important. For a fixed information set, every action's Q is nondecreasing in g. The initial feasible set can therefore only lose actions as g increases. Under a fixed total ordering `(passes,-tau1,-tau2)`, an optimal initial pair that is the same at both ends cannot disappear and reappear inside. It remains feasible at the upper end; every higher-ranked competitor is already infeasible at the lower end. Once that same first action is fixed, the identical argument applies to the continuation ranking. Model nonemptiness has a single monotone rational threshold, protected by its band/point semantics. Thus endpoint/rank verification plus these properties establishes constant selection on the **whole open region**, without assuming that midpoints alone detect all changes.

This also addresses harmless omission of nonselected feasibility transitions: not every change in the full feasible set must split a selected-policy map. It is legitimate to join cells across a nonselected single event when the complete selected signature remains unchanged. It is not legitimate to infer an invariant full feasible set from that joined row.

Source inspection confirms that all 144 pairs at both decisions are classified by endpoint feasibility and, where needed, a root of the continuous monotone piecewise-quadratic certificate. Fast estimates do not control certification. Distinct events are not distance-averaged; identical action/anchor equations may be deduplicated. Overlapping unproved events become unresolved clusters. Resolved selection is checked against Q<=epsilon before export. Actual input cases have no unresolved root/threshold overlap.

Independently checking the ordered union of resolved cells and boundary enclosures gave exact adjacency across [0,1] for all **720 policy maps**, with no interval overlap or silent interval gap. This is interval coverage; it is not a claim that every real-number query receives an action directly from the open-cell CSV.

## 5. Seven witnesses checked through regenerated map lookup

For each original g, the reviewer first located its unique containing row in the regenerated `policy_regions.csv`, then compared that row with independent **exact rational all-competitor selection**. All seven are inside resolved cells, not hidden in an enclosure or reported only through a standalone calculation.

All rows below are LOWER_MEDIAN, Delayed, L=0:

| Shield / epsilon | g | tau1 | Planned tau2 | Executed tau2 | Map and independent passes |
|---|---|---:|---:|---:|---:|
| d3 / 0.1 | 0.6936659869408 | 5 | 5 | 10 | **90** |
| d3 / 0.01 | 0.6936536239361873553 | 0.5 | 0.5 | 1 | 900 |
| d3 / 0.1 | 0.40048695890843278108 | 10 | 10 | 30 | 40 |
| d3 / 0.1 | 0.6936659869395377387 | 5 | 5 | 10 | 90 |
| d3 / 0.1 | 0.69366598694086486387 | 5 | 5 | 10 | 90 |
| d5 / 0.001 | 0.5532557245343374802 | 1 | 1 | 2 | 450 |
| d5 / 0.1 | 0.7142569798627903833 | 100 | 100 | 150 | 5 |

For the mandatory control, the containing cell starts at `0.693665986938542395833234...` and ends at `0.961298342983086743585790...`; the witness is strictly interior. Those shortened displays are identifiers for this explanation, not substitutes for the full serialized bounds in an exact query.

The committed regression test calculates expected answers but does not itself perform this witness-to-map lookup. Its separate representative tests do not make that missing step implicit. The reviewer explicitly performed it here.

## 6. Serialized boundaries and equality semantics

### Certificate/selection boundaries

For **12,869/12,869** records, the reviewer read the actual serialized lo/hi and independently recomputed `Q(lo)-epsilon` and `Q(hi)-epsilon` using **exact Fraction arithmetic**, exact finite-decimal anchors and the timestamp-derived rational coefficients. Every pair has strict negative/positive signs. No production residual column supplied the expected signs.

Certificate equality metadata in `decision_boundaries.csv` was checked separately from point records: equality status, tau1/tau2 and passes agree with independent selection on the feasible side. At each enclosure, all competing action equations were inspected for a transition. There is exactly one distinct **model-valid** equation event after identical action/anchor equations are identified. Thirty additional algebraic crossings occurred at the other decision while its information model was empty; excluding them is required, not a lost valid transition.

With a single valid loss-of-feasibility event, all predicates at the exact root retain their left-side values under Q<=epsilon. This justifies the left-side equality metadata. Where the equality status is `MODEL/INPUT-CONTRACT-VIOLATION`, the owner label `LEFT-FEASIBLE-BY-<=` describes the certificate event only; it must not override the overall violation status.

### Rational model/replay thresholds and domain endpoints

For all **1,192** model/replay records, the exact numerator/denominator was reconstructed independently from the appropriate anchors. The rational value lies inside its serialized enclosure. All **2,632** `policy_points.csv` records were checked by exact rational all-competitor selection, including g=0/1 and model/replay threshold equalities. There were no mismatches. This is stronger than selecting at the upper endpoint and assuming the exact rational point has the same action.

These are different information objects:

- `policy_points.csv` contains g=0/1 and rational model/replay equalities.
- `decision_boundaries.csv` supplies certificate-root enclosures, their witness equation and equality metadata; it does **not** make its midpoint an exact root.
- A displayed rounded root or displayed g_min is neither an exact query coordinate nor a compatibility test.

## 7. Downstream map and exact acceptance domain

The reviewer checked **full-interval containment**, not just midpoint alignment, for all **46,336** resource rows. Each resolved resource interval lies within both source policy intervals and crosses no retained source band. All **22,880** BOUNDARY-ENCLOSURE rows leave joint pass differences, occupied-time differences, occupancy differences and retention blank. When a component pass count remains available because only the *other* comparator has a boundary band, its own policy interval covers the full resource interval. This is a justified component value, not a joint certified saving.

The map is accepted with the following exact limitations:

1. An action/resource claim from an open resolved row applies only to g strictly inside its full-precision serialized endpoints, with the row's certification and replay/completion qualifications.
2. Enclosures are exclusion/protection bands for direct table lookup. Do not interpolate across them, fill them from a neighboring row, use their midpoint as the root or infer savings merely because the band is narrow. Conservatively include the enclosure endpoints in this lookup exclusion unless an explicit point record or independent query calculation resolves them.
3. Exact rational endpoint/model-threshold queries use the matching point records. Certificate-root equality uses the exact root identified by its witness equation/enclosure and its equality metadata, not an arbitrary decimal inside that enclosure. The root's printed approximation is not proof that an input equals it.
4. For an ordinary exact decimal/rational query inside a band that is not an identified equality point, the tables alone do not answer the action question. A separate verified all-competitor query calculation or additional refinement is needed; no such total-query API is established by this review.
5. `UNRESOLVED=0` means no unproved ordering/coincidence cluster remained. It does **not** remove BOUNDARY-ENCLOSURE or imply a certified action for every point in it.
6. Within a boundary row, `replay_compatible` is a representative classification, not a universal statement about all g in a band that straddles the replay threshold. The exact rational replay threshold governs membership.
7. EARLIEST_INVALID is compatible-completion stress only. Its factual Ideal cost and retention remain NA; numerical stress costs are separately named. Existence of a completion does not identify the unknown realized bin.

The repaired package is a map of selected policies on resolved regions, with explicit boundary information and certain exact points, not a total exact-g oracle and not a table of all feasible actions.

## 8. Substantive regressions and remaining minor issue

Both existence booleans match the historical table in **all 576** keyed summary cells. All five integer cost/difference fields match in **all 100** complete-reference g=1 rows. Exact endpoint selection was independently checked through the point records, so this is not merely comparison of two exported projections.

- g=1: positive saving remains 13/25 at L=0, and 0/25 at L=300/900/1800.
- Complete-reference “some compatible saving” counts remain 18/25, 13/25, 10/25, 10/25. Missing-reference stress remains separately 5/5 at each L.
- MAX_MEAN has no baseline-certified positive-saving existence flag. Its prior accepted relaxed-all-pair argument remains applicable because the physical/data/rule interfaces are unchanged.
- MAX_INCREASE/d3/epsilon=0.01/L=300/g=0.35 retains 2100/1200/900 passes and the previously verified transition near 0.400402024122230256. The repair suite independently rechecks the representative and prior transition sides; the new interval and bracket checks cover their map semantics.
- Baseline-absent certifiability gain is still separate from resource saving. No factual Ideal replay is inferred for missing-reference cases.

### New MINOR-R2-01 — Replay-domain enclosure-width metadata uses midpoint classification

`summarize_results.py` first filters rows by `replay_compatible`, then sums each retained band's entire width. A band straddling the exact replay threshold is therefore either fully included or fully omitted. This does not equal its geometric intersection with the replay domain.

Independent rational clipping found a width discrepancy in all **576** summary rows, at approximately one half-band, 1e-18 in g per row. Example: EARLIEST_INVALID/d1/epsilon=0.1/L=0 exports `verified_boundary_enclosure_total_g_width_in_replay_domain = 7.2e-17`; clipping each band at the exact rational replay threshold gives approximately `7.3e-17`. These are diagnostic widths, not probability mass or scenario weights.

**Minimum correction:** compute each contribution as `max(0, hi-max(lo,g_min_exact))` using the rational threshold, and form any domain-component counts from the clipped intervals. Alternatively relabel these fields explicitly as widths/counts selected by representative compatibility, not actual intersection widths/counts. This affects summary metadata only. No numerical-map regeneration, new experiment or scientific re-review cycle is needed; the summary can be corrected from the retained maps.

**Impact:** no false action, certificate, saving or retention claim is introduced; all bands are still excluded from joint resource guarantees. The issue is nonblocking for acceptance in section 7's domain. Original MAJOR-01 and MINOR-01…03 are not reopened by it.

## 9. Maximum admissible result and next disposition

Within the unchanged bounded Stage A model and the declared hypothetical external-information contract, the repaired numerical package reproduces the selected conservative one-replan policies on its resolved open g-regions, preserves close selected-policy transitions, and explicitly withholds joint resource claims within verified boundary enclosures. Exact rational model/replay thresholds and endpoint decisions are controlled separately from certificate-root equality metadata. The seven prior map counterexamples are corrected, and the principal bounded saving/certifiability conclusions are unchanged.

This wording must retain the counterfactual B_d/g prior, known rho=0, imposed per-window clean start, accepted Q rather than exact F_A, actual sequential reset/exposure semantics, fixed U and epsilon/L/window families, exogenous eligible reports, fallback/missing masking, and the distinction between complete reference and compatible completion. It establishes neither a GOES-fed spacecraft architecture nor measured operational latency, spatial equivalence, physical B_d/g calibration, a full acquisition/controller resource balance, global policy optimality or novelty.

**Orchestrator may complete scientific acceptance of the repair in the explicit domain above.** No blocking scientific correction remains. The diagnostic-width MINOR can be closed locally without a new map study. Bounded promotion remains an Orchestrator/PI decision; this review creates no HYP/RES, changes no canonical decision, and authorizes no next experiment.
