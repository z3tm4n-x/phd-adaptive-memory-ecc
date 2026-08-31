# Scientific Re-review — EXP-001

**Task:** `EXP-001-SCIENTIFIC-REREVIEW-02`  
**Reviewer role:** independent Scientific Reviewer  
**Exact review commit:** `222e9303724c1e0f8f0986c1d4e53c754c47cf23`  
**Repair commit:** `072b70adabb9827ee59c94b2b3d5cf044b25cdf9`  
**Original canonical base:** `0ca6f13481ea0818c59395ead26db2f58cb6188e`  
**Related:** `RQ-002`; `RQ-006`; `DEC-001…003`  
**Review date:** 2026-08-31  
**Recommendation:** `PASS`  
**Result status:** this review creates no `RES-xxx`

## 1. Review scope

This is a bounded repair re-review. It checks only closure of `MAJOR-01` and
`MINOR-01…04` from Scientific Review 01 and whether the repair introduced a
regression. The accepted J-A/J-B analytical derivation is not reopened because
no contradictory evidence or analytical regression was found.

The review covers the independent test oracle, separate L0/L1-to-oracle paths,
complete-trace coverage, the mutation/sentinel, analytical-domain and
statistical qualifications, precondition enforcement, deterministic analytical
tests, and Git/hash regression evidence. It does not review physical SRAM
topology, target devices, new prior-art signals, a numerical project
requirement, or any later experiment.

## 2. Independent verification

### 2.1 Commit ancestry and change boundary

Git history gives the exact linear chain:

```text
0ca6f13481ea0818c59395ead26db2f58cb6188e
  -> 072b70adabb9827ee59c94b2b3d5cf044b25cdf9
  -> 222e9303724c1e0f8f0986c1d4e53c754c47cf23
```

Thus the repair has the required original parent, and the review branch starts
at the required review commit. The second edge changes only project/status
documentation and the Orchestrator disposition; it does not change production
code, tests, fixed configurations, or the seven scientific files.

### 2.2 Required commands

Executed at the exact review commit:

```text
python -m unittest discover -s simulation/tests -v
python -m compileall -q simulation/src simulation/tests simulation/run_exp001.py
```

Result: 32 tests run; 32 passed; zero failures/errors/skips. `compileall`
completed with exit code 0.

### 2.3 Oracle independence and path separation

Manual source inspection confirms that
`simulation/tests/independent_l0_oracle.py` imports only Python standard-library
modules. It does not import the production `exp001` package and does not call or
copy a production helper through an alias. It independently implements both
fixed mappings, initialization, toggle and `set_error` transitions, complete
simultaneous marks, full scrub reset, `scrub_then_event` ordering, state
snapshots, capability evaluation, and first passage.

The production imports occur only in the test harness. For every physical
stream, the harness evaluates three paths:

1. the direct physical oracle;
2. production L0 through `simulate_physical_events`;
3. production L1 through `convert_l0_to_l1` followed by
   `simulate_joint_events`.

Production L0 and production L1 are each compared separately with the oracle
for `E_cap`, first-passage time, final state, and every transition record. This
is not merely an L0-versus-L1 comparison.

The bounded validation contains 267 physical streams and therefore 534
separate production-path-to-oracle full-trace comparisons. Inspection confirms
coverage of both declared `W` variants; all 64 cells of the fixed 8x8 domain
under each `W`; clean and non-clean starts; toggle and `set_error`; single- and
multi-cell marks; repeat hits and toggle clearing; immediate, sequential, and
initial exceedance; scrub-boundary ordering; deterministic cases; and 128
bounded randomized streams.

The sentinel is probative for the original failure class. It deliberately uses
the contiguous conversion for physical cell 8 while declaring round-robin
mapping. The resulting joint mark is structurally valid and is accepted by the
production joint simulator. Given the chosen non-clean initial state, the
mutant returns `E_cap=false`, while the direct physical oracle returns
`E_cap=true`; the complete traces also differ. A shared mapping/conversion error
that could survive the old L0/L1 comparison is therefore detected by the new
gate.

**Verdict:** the oracle is implementation-independent for the failure class
identified in `MAJOR-01`; the coverage and sentinel are sufficient to close
that finding. This does not convert the original 768,000 production checks into
independent full-trace checks: they remain correctly described as
outcome/final-signature comparisons, while the new 534 comparisons are the
independent full-trace validation layer.

### 2.4 Configuration and scientific-output regression

`git diff --exit-code` confirms no change from the original canonical base to
the exact review commit in either fixed configuration or any of the seven
scientific files. Independently computed current hashes are:

| File | SHA-256 |
|---|---|
| `simulation/configs/EXP-001/bounded-phase1.json` | `77f78ea988e1ee9106d4f414556fb76a0b6eefec0a2724a04484252c75eb0112` |
| `simulation/configs/EXP-001/joint-discriminator.json` | `e79b9f8914cea2a5a616f1ba0b26c38fe4d09fef4969dc39148ad051502e58c0` |
| `bounded-aggregate.csv` | `84e3f031da8ed0cb70209b10e9f8f8c06a08f00add8cb7c440db1d92be94804c` |
| `bounded-decisions.csv` | `530f37e2f4cc5232a872fa7a96ce28bde2560bd4192866574ae11c7b2ae70ae9` |
| `bounded-invariants.json` | `cc316d1892d0aaf181d04c001acf51b02e93f18ac4d64e18aa22fb5fb380ea0f` |
| `joint-discriminator-aggregate.csv` | `9aec0a6638cc9a53627558abc67d4a6e54232641b5d188f2656620e739377a53` |
| `joint-discriminator-decisions.csv` | `f689c3a008653fc461c8f04f95cb1b411004393ac1e84fb7ed71483386921d79` |
| `joint-discriminator-delta.csv` | `acc677f17a9e4a9408dd1d423b69e78c719bf193853dd8ead0ae04e39f1abdbc` |
| `joint-discriminator-invariants.json` | `255afd28c55e08b8190b203b1b1e130a2f9167eb9737ef6912f0ab32a2907e65` |

These equal the registered before/after values in
`validation-repair-regression.json`. No configuration or scientific-output
regression is present.

## 3. Original-finding dispositions

| Finding | Disposition | Basis |
|---|---|---|
| `MAJOR-01` | **CLOSED** | Independent physical oracle; separate L0- and L1-to-oracle full-trace checks; complete bounded coverage; mapping mutation/sentinel detects the former shared-path failure class. |
| `MINOR-01` | **CLOSED** | All fourteen conditions are stated together in the EXP specification, repair report, Orchestrator disposition and machine-readable analytical validation; exact claims are explicitly conditioned on the complete domain. |
| `MINOR-02` | **CLOSED** | Wilson and paired-normal intervals are labelled pointwise 95%; CI-based selection is explicitly not simultaneous or selection-valid. The seven legacy tables remain byte-identical and are qualified by their companion validation/manifests. |
| `MINOR-03` | **CLOSED** | Validation enforces four words, common `t_c=1`, clean start, valid two-word marks, fresh `set_error`, simultaneous complete marks, full synchronous reset, boundary order, phase/full-window alignment, positive HPP rate, and declared-versus-derived trial totals. Runtime validation enforces finite-stream fresh-bit capacity before analytical output. Mutation tests cover these gates. |
| `MINOR-04` | **CLOSED** | Deterministic tests cover both `q` endpoints, `S`, all fixed exact `F_A` endpoint values and the exact/robust decision table. The active statistical gate is linked to the predeclared 0.007 Wilson half-width; eight checks pass, and all eight exact values lie inside their pointwise Wilson intervals. The legacy 0.02 field is retained only as inert byte-compatibility metadata. |

No finding is partially closed, open, or regressed.

## 4. New issues

- **CRITICAL:** none.
- **MAJOR:** none.
- **MINOR:** none.
- **OPTIONAL:** none required for this bounded gate.

The source-text independence guard alone would not prove independence against
arbitrary obfuscation or dynamic imports. Here that theoretical limitation does
not create an issue because manual source inspection confirms the oracle's
actual imports and implementation, and the behavioral sentinel demonstrates
detection of the concrete shared-mapping failure class.

## 5. Analytical and statistical closure

No repair change contradicts the accepted derivation, endpoint attainment,
identified interval, or exact decision table. The machine-readable validation
records both the closed form and all fourteen conditions, while deterministic
tests bind the implementation to the previously reviewed analytical values.

The required uncertainty separation remains intact:

1. representation/joint-dependence uncertainty is the exact interval over the
   admissible `q` set;
2. Monte Carlo estimation uncertainty is represented by pointwise intervals;
3. CI-decision conservatism is the additional restriction caused by selecting
   with a pointwise Wilson upper endpoint.

In particular, the exact endpoint decisions differ at experimental
`epsilon=0.15`, `0.25`, and `0.35`. At `epsilon=0.55`, exact J-A and J-B both
select `T_scrub=4`; only the Wilson-upper-bound rule produces 4 versus 2. The
latter is not a purely structural effect.

## 6. Complete validity domain

The accepted analytical and maximum result wording remain valid only when all
of the following conditions hold together:

1. one declared domain contains exactly four logical words with common
   correction capability `t_c=1`;
2. the reporting window starts from a clean state;
3. every parent event impacts exactly two distinct words;
4. every selected word receives exactly one fresh erroneous bit, with no repeat
   hit, toggle-clear, or within-interval repair;
5. every word has one-event impact probability exactly `1/2`;
6. one fixed pair-probability vector is used, and pair marks are i.i.d. across
   parent events;
7. pair marks are independent of HPP event times and counts;
8. parent arrivals form a simple homogeneous Poisson process, giving Poisson
   counts and independent increments;
9. parent impacts are simultaneous and `E_cap` is evaluated after the complete
   mark;
10. scrubbing is instantaneous, periodic, synchronous, and clears the entire
    erroneous-bit state;
11. `t0` is aligned with the scrub phase and the reporting duration is exactly
    `k*T_scrub`, with no partial leading or trailing interval;
12. deterministic-boundary events have probability zero under the HPP, and the
    implementation ordering is `scrub_then_event`;
13. `F_A` is the DEC-001 reporting-window first-passage event, so an exceedance
    remains counted even if a later scrub clears the state;
14. each logical word has sufficient unused bit positions for the generated
    fresh-bit construction over the finite run.

## 7. Residual risks

The repair closes validation defects; it does not expand the scientific domain.
No evidence here shows that real radiation-event dependence is i.i.d., has the
fixed marginals, or reaches the synthetic endpoints. No real SRAM topology,
decoder/system failure semantics, non-Poisson dependence, asynchronous or
partial scrub, repeat-hit process, target requirement, adaptive-control law,
resource optimum, or novelty claim is established. L2 and L3-U findings remain
descriptive only for their declared reconstructions and domains; one failed L2
reconstruction is not universal marginal insufficiency.

## 8. Recommendation and RES-001 gate

**Recommendation: `PASS`.**

All five original findings are closed, the required commands pass, and no
repair-induced scientific regression or new issue is found. A narrowly bounded
`RES-001` candidate is now scientifically admissible for Orchestrator/PI
promotion. This review does not create or canonically accept it, and no
retrospective `HYP-xxx` is warranted.

The maximum wording from Scientific Review 01 remains valid without expansion:

> In a synthetic four-word `t_c=1` model with clean starts, HPP parent arrivals,
> i.i.d. exactly-two-word fresh-error marks independent of those arrivals,
> per-word one-event impact probability 1/2, and aligned synchronous full-reset
> scrubbing, the one-event per-word marginal impact distributions and fixed
> event cardinality do not point-identify the DEC-001 reporting-window
> probability `F_A`. The admissible pair distributions yield
> `q∈[1/6,1/2]` and the exact identified interval
> `[F_A(q=1/2), F_A(q=1/6)]`, whose endpoints are attained by J-A and J-B.
> For the fixed rate 0.5, four-time-unit window and candidate periods
> `{0.5,1,2,4}`, endpoint-specific exact maximal feasible periods differ at the
> experiment parameters `epsilon=0.15,0.25,0.35`, but not at `epsilon=0.55`.
> Monte Carlo estimates reproduce the exact endpoint probabilities within the
> reported pointwise Wilson intervals.

This wording must be accompanied by the complete fourteen-condition validity
domain above. It does not support the shorter claims “marginals are
insufficient,” “inter-word dependence always matters,” “J-A/J-B bound real
SRAM,” or “the optimal scrub period differs.” Experimental epsilon values remain
experiment parameters, not project requirements.
