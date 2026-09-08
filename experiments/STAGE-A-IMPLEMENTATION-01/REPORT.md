# STAGE-A-IMPLEMENTATION-01 — REPORT

## Executive answer

**Does knowledge of the current external intensity buy a resource advantage after the
best Precomputed mode in the accepted Stage A class?**

**Not in the primary minimax scalar, but yes pathwise.**  In every case in which all
three comparator classes are certified, the best Causal policy has exactly the same
**worst-case total pass count** as the best Precomputed policy.  The residual
`Precomputed -> Causal` worst-case gap is therefore **zero** on the accepted matrix.

This zero minimax gap is structural for this two-level robust scenario set, not evidence
that current information has no value.  `HH` is a required scenario and dominates the
certificate for any fixed action pair.  The action pair used by a certified causal
controller on its `HH` branch can be applied precomputed to all paths and remains
certified.  Hence current information cannot lower the minimax cost below the `HH`
branch cost.

At the same time, Causal uses current-level information to reduce resource consumption
strictly on `LL`, `LH`, and `HL` in every certified case.  Example: for `d=5 mm`,
`rho=0`, `epsilon=10^-2`, the best Precomputed policy uses 90 passes on every path,
whereas Causal uses `(2,31,31,90)` passes on `(LL,LH,HL,HH)`.  Thus the residual
pathwise savings are `(88,59,59,0)` passes.  Since Stage A assigns no probabilities to
paths, these componentwise savings are **not** converted to an expected mission gain.

The result is therefore:

> Current-level information has measurable conditional/pathwise resource value in the
> declared class, but no additional worst-case pass-count value beyond the best
> Precomputed schedule under the required `LL/LH/HL/HH` robust family.

This is a conditional surrogate/certificate result only; it is not a statement of
physical or mission-wide optimality.

## 1. Scope executed

Executed exactly the bounded Stage A package authorized by
`docs/research_gates/STAGE-A-PREEXECUTION-01.md`:

- frozen `d={1,3,5} mm` low/high rate extraction contract;
- declared post-`W`, 32-data-bit SEC model;
- `rho={0,10^-4,10^-2}` and finite ambiguity family `M_rho`;
- four two-block paths `LL,LH,HL,HH`, 300 s + 300 s;
- R2-U sequential full-pass word restoration phases;
- exact sufficient first-passage certificate;
- `Fixed -> Precomputed -> Causal current-information` finite comparator classes;
- accepted `U`, `epsilon` grid, resource contract and tie rule;
- direct-budget pruning before policy search;
- focused and independent verification checks.

No Stage B operation, COSRAD run, transport, mapping sweep, parity/ERR extension,
operational estimator, literature search, angular diagnostic, synthetic reference
bracket, parameter-grid change, HYP/RES creation, or Scientific Review disposition was
performed.

## 2. Input/config freeze and scaling audit

Frozen rate source:

- commit: `619cb3538e296b3619f21301a176665f4611143f`;
- path: `experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv`;
- git blob SHA: `5de108c6759bcf720073b3fbc6581389d46e63aa`;
- canonical LF Git-blob SHA-256:
  `9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`;
- historical CRLF serialization SHA-256 (provenance only, not the reproduction gate):
  `713eceb0df3faa4ea0eb50f6381c5a26cfb77a969f82e059f58815e8469f1e09`;
- paired-valid rows: `16971`.

The upstream implementation explicitly uses `N_BITS=16,777,216`, and its validated
rate contract is a full-array rate in `s^-1`.  Stage A uses the same `N=2^24`; the
array-scaling check therefore **PASS** and no rescaling was applied.

Because `16971` is odd, each median is one central order statistic.  Frozen CSV-text
levels are:

| Shield | L, s^-1 | median row UTC | H, s^-1 | max row UTC |
|---:|---:|---|---:|---|
| 1 mm | `1.0147076e-04` | 2026-02-19 11:10 | `5.8709784e+01` | 2026-01-19 19:20 |
| 3 mm | `2.8886786e-05` | 2026-01-28 15:15 | `6.1249308e+00` | 2026-01-19 19:20 |
| 5 mm | `7.1682448e-06` | 2026-01-05 07:05 | `1.5358618e+00` | 2026-01-19 19:15 |

`input_manifest.json` records the full provenance and the higher-precision upstream
summary cross-check.

## 3. Direct-term triviality audit

The required 36 `d x rho x path` combinations were evaluated before policy search with

\[
\Lambda_D=\frac{\rho}{2}(300b_1+300b_2).
\]

There are no equality/ambiguous direct comparisons on the accepted epsilon grid.
Representative/full-family-determining values are:

| d | rho | Lambda_D(LL) | Lambda_D(LH=HL) | Lambda_D(HH) | Full-family consequence up to eps=0.1 |
|---:|---:|---:|---:|---:|---|
| 1 mm | `0` | 0 | 0 | 0 | direct budget remains |
| 3 mm | `0` | 0 | 0 | 0 | direct budget remains |
| 5 mm | `0` | 0 | 0 | 0 | direct budget remains |
| 1 mm | `1e-4` | `3.044e-6` | `8.806e-1` | `1.7613` | exhausted for every epsilon |
| 3 mm | `1e-4` | `8.666e-7` | `9.187e-2` | `1.837e-1` | exhausted for every epsilon (HH at 0.1) |
| 5 mm | `1e-4` | `2.150e-7` | `2.304e-2` | `4.608e-2` | remains only at `epsilon=0.1` |
| 1 mm | `1e-2` | `3.044e-4` | `8.806e+1` | `1.761e+2` | exhausted for every epsilon |
| 3 mm | `1e-2` | `8.666e-5` | `9.187` | `1.837e+1` | exhausted for every epsilon |
| 5 mm | `1e-2` | `2.150e-5` | `2.304` | `4.608` | exhausted for every epsilon |

The detailed epsilon-by-epsilon classifications are in `direct_budget_audit.csv`.
Cases whose required robust family was already exhausted were not subjected to
pointless policy search.

Consequences:

- all `rho=10^-2` known-rho full families are direct-certificate-exhausted;
- `rho=10^-4` is direct-certificate-exhausted everywhere except `d=5 mm,
  epsilon=0.1`;
- every `M_rho={0,10^-4,10^-2}` robust family is direct-certificate-exhausted because
  it must retain the `rho=10^-2` member and all required paths.

These are certificate-budget statements, **not physical infeasibility** and not evidence
of zero information value.

## 4. Derivation result

For each word `w`, R2-U credits the reset at the end of its four-address group.  If
`a_w=P(N_w-w-1)/N_w`, the interval crossing `t=300 s` has exposure

\[
r_1 a_w+r_2(\tau_2-a_w),
\]

so state is explicitly carried through the boundary and no free reset is introduced.
The exact closed-form phase sum, first-passage union certificate, causal conditioning
argument, and stationary reduction are given in `derivation.md`.

The implementation uses exact rational arithmetic for all classifications after parsing
the frozen decimal inputs.

## 5. Certification map after the direct audit

For `rho=0`, lack of certification at small epsilon is accumulation/U limited rather
than direct-term limited.  The HH certificate at the smallest available pair
`(tau1,tau2)=(0.2,0.2) s` is:

- 1 mm: `Q=3.8208795e-1`;
- 3 mm: `Q=4.1585771e-3`;
- 5 mm: `Q=2.6148493e-4`.

Thus, within the accepted finite `U`:

| d | rho | Certified epsilon values for all three comparator classes |
|---:|---:|---|
| 1 mm | 0 | none |
| 3 mm | 0 | `1e-2`, `1e-1` |
| 5 mm | 0 | `1e-3`, `1e-2`, `1e-1` |
| 5 mm | `1e-4` | `1e-1` |
| all other known-rho combinations | — | direct-certificate-budget exhausted on required family |
| all `M_rho` combinations | finite ambiguity | direct-certificate-budget exhausted |

`NO-CERTIFIED-POLICY-IN-U` is intentionally not called physical impossibility.

## 6. Fixed -> Precomputed -> Causal resource result

Worst-case total pass counts in every certified case are:

| d | rho | epsilon | Fixed | Precomputed | Causal | Fixed -> Causal | Precomputed -> Causal |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 mm | 0 | `1e-2` | 3000 | 2100 | 2100 | 900 | **0** |
| 3 mm | 0 | `1e-1` | 300 | 210 | 210 | 90 | **0** |
| 5 mm | 0 | `1e-3` | 1200 | 900 | 900 | 300 | **0** |
| 5 mm | 0 | `1e-2` | 120 | 90 | 90 | 30 | **0** |
| 5 mm | 0 | `1e-1` | 10 | 10 | 10 | 0 | **0** |
| 5 mm | `1e-4` | `1e-1` | 20 | 20 | 20 | 0 | **0** |

The Fixed-to-Causal minimax reduction in the first four rows is entirely already
available to Precomputed.  It comes from the larger precomputed action class, including
its ability to use different predetermined periods in the two blocks and to exploit the
discrete `U` grid.

### Residual pathwise value of current information

Precomputed and Causal path pass vectors are:

| d, rho, epsilon | Precomputed `(LL,LH,HL,HH)` | Causal `(LL,LH,HL,HH)` | Residual savings |
|---|---|---|---|
| 3 mm, 0, `1e-2` | `(2100,2100,2100,2100)` | `(2,601,601,2100)` | `(2098,1499,1499,0)` |
| 3 mm, 0, `1e-1` | `(210,210,210,210)` | `(2,61,61,210)` | `(208,149,149,0)` |
| 5 mm, 0, `1e-3` | `(900,900,900,900)` | `(2,301,301,900)` | `(898,599,599,0)` |
| 5 mm, 0, `1e-2` | `(90,90,90,90)` | `(2,31,31,90)` | `(88,59,59,0)` |
| 5 mm, 0, `1e-1` | `(10,10,10,10)` | `(2,3,6,10)` | `(8,7,4,0)` |
| 5 mm, `1e-4`, `1e-1` | `(20,20,20,20)` | `(2,4,6,20)` | `(18,16,14,0)` |

Every pass has exactly `2^21` reads, `2^21` writes and `P=0.18874368 s` of serial
occupied time.  Therefore every pass saving maps linearly and identically into all three
resource components.  Exact component savings are tabulated in `resource_gaps.csv`.

No path averaging is reported.

## 7. Selected policy behavior, U saturation and tie rule

The complete selected trees are in `selected_policy_trees.json`.

Two bounded effects are visible:

1. **U ceiling.** In every certified Causal case, the `LL` branch selects
   `(300 s,300 s)`, the maximum accepted periods, giving only two passes over 600 s.
   This action is saturated by `U`; no larger period is available in Stage A.

2. **Tie rule.** The third-stage period-maximization tie-break is actually exercised for
   the selected Precomputed policy in five cases:
   - 3 mm, `rho=0`, `epsilon=1e-2`: `(0.5,0.2) s`;
   - 3 mm, `rho=0`, `epsilon=1e-1`: `(5,2) s`;
   - 5 mm, `rho=0`, `epsilon=1e-3`: `(1,0.5) s`;
   - 5 mm, `rho=0`, `epsilon=1e-2`: `(10,5) s`;
   - 5 mm, `rho=1e-4`, `epsilon=1e-1`: `(60,20) s`.

These choices are not post-hoc optimization criteria; they follow the accepted
selection order after identical worst-case and path pass-count vectors.

## 8. Known-rho versus finite ambiguous-rho consequence

Known `rho=0` is the useful information-headroom slice: it yields five certified
`d,epsilon` cases.  The one nonzero known-rho case surviving the direct audit is
`d=5 mm, rho=10^-4, epsilon=0.1`, and it is also certifiable.

The finite ambiguity family `M_rho` yields no certified Stage A family because its
`rho=10^-2` member already exhausts the direct certificate budget on a required
high-level scenario for every shield and epsilon.  Therefore Stage A **cannot** use
`M_rho` to quantify a robust information-value gap on this accepted grid.  This result
says that the declared structural uncertainty dominates the certificate; it does not
justify changing the rho grid post hoc and does not establish physical impossibility.

## 9. Numerical status and validation evidence

The original implementation run recorded **9 focused tests PASS** in `test_output.txt`.
Those tests are not identical to the later independent production-linked checks.  In
particular, Scientific Review 01 independently linked explicit reset-timestamp/overlap
integration to production `pair()` and separately checked the stationary limit; the
preserved algorithm and scope are in
`docs/scientific_reviews/STAGE_A_SCIENTIFIC_REVIEW_01.md`, §6.  Those reviewer checks
remain reviewer evidence and are not retroactively attributed to `test_stage_a.py` or
to the original run manifest.

The original exact-decision results still report numerically unresolved cases: **0**.
See `verification_report.md`, `verification.json`, and
`numerical_boundary_summary.csv` for the historical implementation record, qualified by
the Scientific Review 01 distinction above.

## 10. Execution environment and one limitation of this cloud run

Implementation environment:

- Python 3.13.5;
- Linux 6.18.35 x86_64;
- glibc 2.41;
- Python standard library only.

The original implementation run did not materialize the complete private CSV bytes and
therefore did not independently recompute its SHA-256.  Scientific Review 01 later
identified that the old value was the hash of a CRLF serialization, while the pinned Git
blob and `git show` output are LF.  The reproduction gate is corrected here to the
canonical LF SHA-256.  This correction changes provenance/packaging only; no input
value, L/H level, scale, formula, policy, or scientific table is changed.

## 11. Reproduction

From a clone containing the repository objects:

```bash
git checkout research/stage-a-reproduction-fix
bash experiments/STAGE-A-IMPLEMENTATION-01/reproduce.sh
```

The helper creates a fresh `mktemp -d` workspace, materializes the pinned file there via
`git show`, runs the dedicated input-gate regression, then runs the historical focused
tests and the science-table reproduction.  Cleanup is explicit through an EXIT trap; no
fixed temporary path is deleted.

The input gate fails closed on canonical LF SHA-256, paired-valid-row count, or
recomputed `L/H` mismatch.  The historical committed `run_manifest.json` is not
rewritten or promised as a generated reproduction artifact.

## 12. Files

- `derivation.md` — certificate and exact R2-U phase derivation;
- `config.json` — frozen Stage A configuration;
- `input_manifest.json` / `run_manifest.json` — provenance and execution environment;
- `direct_budget_audit.csv` — required 36-combination pre-search direct audit;
- `selected_policies.csv.gz.b64` / `resource_table.csv` — base64-wrapped deterministic gzip of selected certificate margins/resources and the exact 12x12 per-action resource table;
- `passing_sets.csv` — comparator passing-set counts;
- `passing_sets.json.gz.b64` — base64-wrapped deterministic gzip of feasible causal roots and allowed second actions;
- `selected_policy_trees.json` — selected policy trees;
- `resource_gaps.csv` — componentwise Fixed/Causal and Precomputed/Causal gaps;
- `numerical_boundary_summary.csv` — nearest exact certificate/direct boundary per known-rho case;
- `stage_a.py` / `test_stage_a.py` — implementation and original focused tests;
- `test_input_gate.py` — input-only canonical/altered-byte regression;
- `verification_report.md` / `verification.json` — independent checks and validity limits.

## 13. Scientific limitations retained

This package does not calibrate `rho`, does not infer proprietary `W`, does not include
parity, ERR, estimator/acquisition cost, or a real mission distribution, and does not
run Stage B.  The sufficient certificate remains an upper bound for the accepted
surrogate.  A certificate failure is not a proof of physical infeasibility.  The finite
Causal comparator is not an absolute upper bound on all adaptive control methods.


## 14. Reproduction correction after Scientific Review 01

Corrective scope is limited to findings in
`docs/scientific_reviews/STAGE_A_SCIENTIFIC_REVIEW_01.md` at review commit
`12d461aad112f22c37a365a38501143aaf2c3ee8`.  The exact Git blob remains
`5de108c6759bcf720073b3fbc6581389d46e63aa`; the canonical LF SHA-256 is
`9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`.
The former `713ece...` value is retained only as the historical CRLF serialization hash.

The dedicated input-only regression calls `stage_a.frozen()` on a supplied file and on
a one-byte-altered copy; it does not call `search()`, `main()`, or regenerate the
scientific matrix.  In this corrective engineering environment the input-gate code path
was exercised on a controlled LF fixture whose temporary config matched its SHA-256,
paired-valid-row count and L/H contract: the fixture was accepted and a one-byte
mutation was rejected at SHA-256.  The 13,002,858-byte private upstream blob was not
materialized in this runtime, so no second direct execution on that blob is claimed
here.  Exact-blob LF identity and row/L/H validation are the independent Scientific
Review 01 §6 record; the corrected config now uses that canonical LF hash.  No
production matrix was executed for this correction.  The original `run_manifest.json`
remains unchanged.  Scientific Review 01's independent production-linked timestamp
algorithm remains preserved in its §6 and is not repeated or re-labelled as an original
implementation test.
