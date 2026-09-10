# STAGE-A-INFORMATION-INTERFACE-REVIEW-01

## Scope and disposition

**Recommendation: PASS_WITH_MINOR.** No CRITICAL or MAJOR finding. The new finite information reduction, restricted shared-history optimization and reported bounded actuation conclusions are supported. The canonical retained-set reproduction qualification is resolved at the scientific-content level; the supplied shell command does not pass unchanged in the review environment because of gzip packaging.

Reviewed/base commit: `da03ab308989f76e9ae15043c83ce4c4b1f76821`, whose sole parent is accepted specification commit `8cde3f9ef079a34780caf4d07d339eadfa75ca9a`. Review branch: `reviewer/stage-a-information-interface-review-01`. Review date: 2026-09-08.

Scope: the information-interface preexecution gate, complete new experiment package, retained Stage A configuration/roots/trees/certificate implementation, prior Stage A review and relevant RQ-004/005/007, under the global/reviewer/handoff instructions. This is not renewed acceptance of physical calibration, radiation inputs, the old physical model, or an operational sensor. No old production matrix or radiation-input regeneration was performed. Only this review report is delivered.

| Candidate | Disposition and maximum supported conclusion |
|---|---|
| Timing/error reduction | Supported: six attainable timing signatures and two error regimes yield 12 parameter cells, but only 11 distinct report-history interfaces; both T000 cells carry no information. |
| Shared-history calculation | Supported for the declared deterministic, set-valued-report policy class and frozen feasible roots. Independent relational enumeration agrees with all 60 selected policies, including tie-breaks. |
| Full selected Ideal tree | Supported: implementable and selected only in T111_E_EXACT in these five cases. This is about the complete selected action tree, not uniqueness of scalar cost performance. |
| Ambiguous reports | Supported: every timing class admits a common all-ambiguous/no-report history; the optimal guaranteed pathwise pass vector collapses to the Precomputed vector. Singleton reports can still yield lower conditional costs. |
| T011 savings | Supported: all five cases retain strictly positive guaranteed LL/LH/HL savings, with unchanged HH cost. This signature requires zero common delivery latency for the second report. |
| Aligned positive latency | Supported: with both updates enabled, s1=0, s2=300 and 0<ell<=300, the signature is T010 and guaranteed HL saving is lost. For ell>300 it is T000. |
| Retention/resources | Supported from selected integer pass counts under R2-U; exported decimal breakpoints are rounded, not exact threshold representations. Acquisition/controller costs are excluded. |

## Actual reproduction and provenance

A detached canonical checkout was used. The new package and retained Stage A inputs were read at the reviewed commit, not from the development fixture. Unrelated checkout line-ending differences in older experiment CSVs were left untouched and were not calculation inputs.

Executed from `experiments/STAGE-A-INFORMATION-INTERFACE-01`:

```sh
./reproduce.sh
```

The new calculation returned `{"cases": 5, "regions": 12, "status": "PASS"}`. The shell helper then exited 1 at its first compressed-file `cmp`: `policy_region_map.csv.gz.b64` differed at byte 13. Its later unittest and syntax steps were therefore not reached. It would be incorrect to report this command as PASS.

To finish this narrowly scoped check, the committed ten-test suite was run using `unittest.TextTestRunner`, with a review-only wrapper around `InformationInterfaceTests.tearDownClass` that compared its temporary decoded outputs before calling the original cleanup. This necessarily executed the NEW calculation one additional time through the suite's existing `setUpClass`; it did not run the old matrix. All 10 tests passed. The syntax command also passed:

```sh
python -m py_compile information_interface.py test_information_interface.py
```

Review interpreter: Python 3.12.13, build Aug 7 2026, Clang 22.1.3. No claim is made that it duplicates the development environment.

Both regenerated decoded scientific CSVs were byte-identical to the committed decoded files:

| Decoded file | SHA-256 |
|---|---|
| policy_region_map.csv | `347b8688e4b37b4976233cd8668c051646576fa0ebe4a51b279f7dfd9491308d` |
| resource_summary.csv | `e74589392bf0bd7cd9b24a0741174b87ec70ed3e01eb0fe58c5d71e265d10101` |

`information_regions.csv`, `information_boundaries.json`, `retention_breakpoints.csv` and `summary.json` also matched byte-for-byte. Recompressing the committed decoded CSVs with local `gzip.compress(..., mtime=0)` isolated the discrepancy: both committed headers end `02ff`, local headers end `0203`; compressed payloads and trailers after the ten-byte header are identical. Thus this observed failure is packaging, not scientific output divergence.

The historical disclosure that development used a reconstructed fixture remains true. This review supplies the missing canonical retained-set comparison; it does not retroactively alter that history or independently rederive the retained Stage A sets.

## Independent checks and their limits

A temporary reviewer script was executed as:

```sh
python /workspace/scratch/24e1723b7ed9/ii-review-checks.6foy0C/check.py
```

This scratch script is not an experiment artefact. Its independent procedure, sufficient to reconstruct the check, was:

1. Decode canonical `passing_sets.json.gz.b64` directly; read `U_s` as exact fractions. For each C root, expand each hexadecimal path mask into a relation of triples `(path, preceding period, second period)`. Do not call production `parse_case_encoding`, `realizations`, `mask_intersection`, or `solve_policy`.
2. Generate compatible report records directly from each binary path: the true singleton, plus A when overlap is allowed, or absence when the update is unavailable. Reuse the same first-report variable at both decisions. Form first and second decision histories and group identical histories.
3. Enumerate assignments of U to distinct first histories. For every second history retain a candidate second action only when its triple belongs to the relation for EVERY compatible path and its actual preceding action. Choose the candidate minimizing its second-block pass count.
4. Rank assignments by maximum path/report cost, then the LL/LH/HL/HH worst-report vector, then negative periods in path/time/canonical-history order. Compare actions, candidate counts, primary/secondary tie counts and worst-report values with the decoded committed tables.
5. Independently reconstruct reads, writes and occupied seconds from integer pass counts. For the d5/epsilon=0.1 T111 ambiguous case, additionally enumerate ALL second-history assignments on the bounded action subset {60,300}; compare the full brute-force optimum with second-action elimination.

Outcome: **60 policy cells, 420 selected report/path rows and 324 canonical C roots checked; all actions, counts, tie counts and checked resource identities matched.** The reduced full-second-action enumeration also matched. This is independently expressed constraint validation against canonical feasible data, not a second invocation of the production solver. It is not independent validation of the old certificate or radiation model.

An additional direct-delivery-time oracle compared `availability` with enabled timestamps satisfying `sample+latency<=decision`, across 288 combinations: s1 in {0,1,100,299}, s2 in {300,301,599}, ell in {0,0.000001,1,200,300,301}, both enable flags independently false/true. All matched. A geometric interval-overlap oracle at eta in {0,0.499999,0.5,0.500001,2} matched the error classification, including equality.

Evidence classification:

- Mathematical arguments below establish reduction, class completeness and elimination direction.
- The reviewer relation/enumeration and delivery-time checks link independent expressions to production outputs/functions.
- Committed selected-row Q checks reuse the accepted Stage A production certificate; they are consistency checks, not new independent certificate proofs.
- The committed endpoint/resource assertions and repeated output comparison are useful regression checks, not independent scientific proofs. In particular, a test named `class_inclusion_cost_order` cannot prove a pathwise order merely by that name.

## Analytical assessment

### Timing, uncertainty and history

With no pre-window observation and nonnegative common latency, report 1 can be available at t=0 only if enabled, s1=0 and ell=0. It is available at t=300 exactly when enabled and s1+ell<=300. Report 2 is available at that decision only if enabled, s2=300 and ell=0. Hence A0 implies A1 and exactly the six listed signatures occur. Missing updates are known exogenous suppression, not observations of a hidden level. Boundary equality is included before the decision.

Normalize the separated binary levels to 0 and 1. Their possible numeric report intervals are [-eta,eta] and [1-eta,1+eta]. They overlap iff eta>=1/2, with the midpoint already ambiguous at equality. Below that boundary all valid delivered reports identify the level. At and above it, singleton and ambiguous reports remain attainable for either true level because numeric reports are not artificially clipped. This reduction applies to the declared compatible-set interface, not a richer policy using the numerical report itself. An incompatible empty report lies outside the bounded-error contract; no selected policy relies on silently discarding one.

The implementation persists the same report-1 value: it does not independently draw a new report about the first block at t=300. A later history determines its earlier history when A0=1. Arbitrarily correlated report errors are allowed; exogeneity to realized upsets is essential for reusing conditional scenario certificates. There is no future-level/event observation, free reset or changed action epoch.

### Completeness of root projection and second-action elimination

Root masks encode feasible continuations conditional on both the actual first period and full environmental path. Projection does not replace this by a second-block-only test. An admissible policy under a reduced interface is also implementable with Ideal information by ignoring excess information and choosing compatible report histories. Any first action used for a given first level must admit continuations for both second levels. It therefore occurs in a complete Ideal root, paired with some feasible opposite-first-level branch. Conversely, arbitrary mask unions without preserving the first action would be unsound; the current calculation preserves it. Repeated root entries must and do give the same continuation set for each path/first-action pair.

For a fixed first-history assignment, the largest FEASIBLE second period minimizes the second-block count 300/tau2. It lowers no feasibility standard: it is selected only after intersecting all compatible-path continuation sets. Increasing that period cannot increase any path's worst-report cost. If primary and secondary objectives tie, it is also preferred by the tertiary period order at its first affected occurrence. Report histories are exogenous and not changed by actions. Thus eliminating smaller second periods preserves the specified optimum, without assuming monotonicity of exact physical risk or that all intermediate periods are feasible. This proof and the independent enumeration cover the full declared selection rule, not only minimax.

### Ambiguity and pathwise interpretation

Scalar class inclusion bounds optimal minimax values, not the components of separately selected pathwise vectors in general. Here a stronger, model-specific argument closes the gap. The all-ambiguous (or absent) report sequence is available on every path. The actions on that sequence form one common, all-path-feasible Precomputed pair. Its action-independent total pass cost is at least the optimal Precomputed count P. Consequently every path's worst-report cost is at least P. Ignoring reports supplies a policy with cost P on every path, so an optimal minimax policy has every component at most P. Both inequalities force every component to equal P. This proves the reported guaranteed collapse without invoking any scenario probabilities.

For exact interfaces the particular selected pathwise ordering and savings were independently checked, not inferred from inclusion. There are primary/secondary ties; published actions depend on the declared period tie-break. The guaranteed vector is already fixed by primary/secondary selection; report-conditioned best cases and selected actions need not be invariant to an unspecified replacement selection rule.

## Quantitative bounded conclusions

Counts are worst over allowed reports, ordered (LL,LH,HL,HH):

| Frozen case | Precomputed count on each path | T011_E_EXACT vector | Minimum LL/LH/HL retention, exact |
|---|---:|---|---|
| d3, epsilon=0.01 | 2100 | (601,1200,601,2100) | 900/1499 |
| d3, epsilon=0.1 | 210 | (61,120,61,210) | 90/149 |
| d5, epsilon=0.001 | 900 | (301,600,301,900) | 300/599 |
| d5, epsilon=0.01 | 90 | (31,60,31,90) | 30/59 |
| d5, epsilon=0.1 | 10 | (6,7,6,10) | 3/7 |

Retention is `(Precomputed - imperfect worst)/(Precomputed - Ideal)`; HH has zero denominator and is NA. Threshold comparisons can be made exactly by cross-multiplying these integer savings, without a new optimization or a gamma grid.

Under R2-U, each pass reads and writes 2^21 words and occupies 0.18874368 seconds; the window is 600 seconds. For example, d5/epsilon=0.01 T011 saves (59,30,59,0) passes, or (11.13587712,5.6623104,11.13587712,0) occupied seconds. Absolute occupancy follows from the SAME pass counts, not from an added information-acquisition model. The full selected Ideal tree was verified to agree only at T111_E_EXACT. T010's HL worst cost equals Precomputed in all five cases.

The omission of other Stage A cases is bounded by the retained Ideal class: reducing information cannot manufacture a feasible policy where that dominating class has none under the same Q/grid. This is not evidence of physical impossibility, nor a robust known/unknown-rho equivalence.

## Findings and minimum corrections

**CRITICAL: none. MAJOR: none.**

**MINOR-01 — Parameter cells are not distinct interfaces.** REPORT opening/output inventory and derivation call all 12 cells distinct information-equivalence regions. The two T000 cells have identical histories. Correct the terminology to 12 timing-by-eta parameter cells, representing 11 distinct report-history interfaces. Preserve table identifiers; no numerical rerun is needed.

**MINOR-02 — Cross-environment reproduction fails on packaging.** The helper compares base64 gzip bytes before tests, although this review establishes equality of decoded scientific content and isolates a header OS-byte difference. Compare decoded CSV bytes for scientific reproduction, separately report container differences, and allow tests to complete. Alternatively pin and document the compression environment. Closure is a successful helper-level check with decoded equality and tests; no old production run is needed. Do not rewrite the historical assertion into a claim that the original command passed here.

**MINOR-03 — State the pathwise proof, not just class inclusion.** Supplement derivation section 6.2 with the common ambiguous-history lower bound and ignoring-reports upper bound given above. Label the committed per-path inequality test as a bounded selected-policy check, not a generic consequence of class inclusion. This is a local proof/wording correction; independent enumeration found no wrong selected result.

**MINOR-04 — Rounded retention exports cannot define exact equality thresholds.** REPORT suggests directly testing exported R>=gamma; the CSV uses 12-significant-digit decimals. Near a true rational breakpoint that can change equality classification. Specify exact comparison from the already exported integer guaranteed/Ideal savings (or export numerator/denominator); label displayed decimals approximate. No new threshold, experiment or optimization is required.

**OPTIONAL — Retain an independent constraint test.** A small relational/brute-force test of this kind would improve future regression resistance. The current review supplies independent evidence; this is not a new blocking gate.

## Maximum defensible wording and next-gate relevance

Within the frozen Stage A four-path, two-decision, known-rho=0 model and its five certified cases, restricting exogenous binary-level reports by the declared sampling, common-latency and bounded-error contract induces a finite shared-history policy problem. Exact enumeration under the specified minimax/pathwise-lexicographic/period ordering reproduces the canonical results. The selected full Ideal action tree requires T111_E_EXACT; T011_E_EXACT retains positive guaranteed LL/LH/HL actuation savings with unchanged HH cost. An admissible all-ambiguous history removes guaranteed pathwise savings for eta>=1/2, without excluding savings on particular singleton-report histories.

Validity additionally requires the unchanged U, whole-window Q certificate with actual preceding actions and sequential restoration, clean-start/reset/exposure conventions inherited from accepted Stage A, LL/LH/HL/HH scenario set, decision times 0/300, 600-second window, deterministic compatible-set policies, known update suppression, persistence of reports, unrestricted joint bounded report errors exogenous to realized upsets, and action-independent R2-U pass costs. T011 requires zero common latency; all latency boundaries exclude pre-window observations.

This is a conditional information benefit without scenario weights, not a scenario-weighted average, engineering-significance threshold, real-sensor latency requirement or net economic benefit. Q certification is sufficient and is not exact F_A; certificate exhaustion is not physical infeasibility. No acquisition cost, controller overhead, new physical calibration or unknown-rho robust comparison is established. Zero minimax improvement does not imply universal uselessness of current information.

Bounded result promotion is scientifically eligible with the corrected wording above, subject to Orchestrator/PI acceptance; no RES/HYP is created. No remaining scientific defect blocks the next scientific decision about an operational-information study. The four local corrections do not warrant a new broad scientific cycle. This review neither designs nor authorizes execution of that next study.
