# RE → Scientific Reviewer

From: Research Engineer
To: Scientific Reviewer / Research Orchestrator
Task: RE-INTERNAL-COUNT-CONTROL-01
Related: RQ-007; interfaces RQ-001...006; DEC-001; accepted PI task.
Disposition: ENGINEERING_EXECUTION_COMPLETED / READY_FOR_SCIENTIFIC_REVIEW.
No Scientific Review PASS, RES promotion or main merge is assigned.

## Identity and scope

Canonical base: `a44355e38a5434fa69d7c343e456ddd944315d46`.
Implementation commit: `ec8f95b24733d854c9e343f5077f313ee886e178`.
Delivery branch: `research/internal-count-control-01`.
All implementation/doc/output changes are under `experiments/RE-INTERNAL-COUNT-CONTROL-01/`.
The source tree assembled from local Git blob hashes exactly matched the
uploaded Git tree `aeed0b306b8cf1ef10f7ba4df8d4055f001fd8c5`.
The execution used those same source bytes in a local package, not a fabricated
claim of a complete local clone of the private repository.

`config.json` records model, scan/action/initial-state contract and provenance:
Stage-A blob `654c50105390904ae62d114998d7369a7f4adb27`, task blob
`f20f0b5041bfed62d6cda880d09d3636860dc046`, DEC-001 blob
`f24f8a6b041e00d2f2c381c6f6118288f745087f`.
PA-DOM controlled source: synthesis on `4f96bb95189f0d385ea2077aa7b05d81ef8edf0d`,
blob `8cdd41f2914203df0e130fa9863a73864a3e14a1`, reproduction sheet equations
(7)-(10) of PA-DOM-01-B as extracted there. No claim of a new direct
PDF inspection is made in this task. Source cross-reference ambiguity is explicit.

## Reproduction

```
cd experiments/RE-INTERNAL-COUNT-CONTROL-01
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python reproduce.py
OPENBLAS_NUM_THREADS=1 python reproduce.py --full
# Include the independent pilot selection as well:
OPENBLAS_NUM_THREADS=1 python reproduce.py --retune --full
```

Executed environment: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0,
Numba 0.65.1, mpmath 1.3.0; full platform identity and SHA256 in manifest.
The source is not a shell call to a missing external solver and not encoded.

Reproduction result: all engineering checks in `outputs/tests.json` completed;
all 12 Fixed/144 Precomputed evaluated at each D; 20000 final held-out missions
per D for five policies. Proposed/disabled use a horizon certificate, Fixed/
Precomputed deterministic probability brackets, PA-DOM binomial evidence only.
The original production inputs and epsilon grid were not changed. Pilot
refinement of PA-DOM used no final-validation samples; final seed 91842031 is
separate from the exploratory coarse-grid seed 7143801 and pilot 943771.
Wall-clock timings are machine dependent; numerical outcomes and source/input
identities, rather than the bytes of timing-containing CSVs, are reproduction targets.

## What to falsify independently

1. `derivation.md` §§2,5: the real/auxiliary coupling and first-repeat bound;
   verify that normalized auxiliary q does not secretly condition on survival,
   and that kernel-TV errors enter the event bound without an invalid
   unbounded-cost TV argument.
2. §§3-4: the action-dependent joint likelihood and residual K. Verify the
   finite-word primitive error, two-switch quadrature derivative bound,
   pending overflow and adaptive whole-horizon union bound.
3. §4: independently audit the explicit arithmetic ledger, especially
   projective filtering error and value-recursion/selection reserve. This is
   conditional on the declared IEEE-754/4-ulp contract, not interval-arithmetic
   hardware certification. Observed row residuals are not offered as its proof.
4. §5: verify the complete observation-branch identity, preserved backup,
   nonnegative terminal slack, partial final interval and the no-count ablation.
5. §6: independently verify the lower bracket and exclusion of every cheaper
   Fixed/Precomputed candidate. Do not turn these exogenous-schedule results
   into a theorem for all adaptive schedules.
6. §7 and the code: verify PA-DOM adaptation/tuning fairness, per-policy own
   counts, actual-bit simulation, stop resources and the D=3000 risk/cost caveat.

A single admissible witness breaking the coupling/budget/error bound, an
absorbed-probability deletion, a foreign-counter input, a cheaper admissible
baseline in its declared class, or a systematic independently confirmed
F>epsilon falsifies the corresponding assertion. Monte Carlo alone is not
sufficient to validate a rare-event guarantee.

## Independence and common-mode paths

The small oracle has a separately constructed killed generator on (Z,mask),
exact chronological word-reset/counter maps and unnormalized real mass.
It does not call the auxiliary scan kernel or pair-reward helper. A separate
explicit all-word event scanner cross-checks the lazy full-scale simulator.
Sentinels cover same-bit cancellation, irreversible first passage and the
nonzero post-pass dirty state. The small oracle is a benchmark, not the
production controller.

Shared elements remain: declared configuration, controller implementation and
its action grid, Python numerical environment; the actual simulator and
compiled controller share the same process. Small Oracle evaluation must
invoke the candidate policy to inspect it, so it is independent in its
physical probability/observation law, not an independent reimplementation
of the policy. The event generator is common across policy comparisons as
paired external random numbers, never as a common counter observation.

## Outputs and limitations

Read `REPORT.md`; main machine tables in `outputs/`. `manifest.json` records
source/output hashes. Complete trace/event-summary files and exhaustive pilot/
open-loop tables are regenerated by the commands; compact excerpts/optima are
versioned, and the delivered archive includes the complete generated CSVs.

Six strict-epsilon cases remain UNRESOLVED for general adaptive feasibility;
all Fixed there are ruled out. There is no global policy optimum or universal
advantage claim. At D=3000 the selected PA-DOM adaptation has lower estimated
risk but higher cost; the report does not describe that as equal-risk
Pareto dominance. No MCU, unknown generator, real orbital identification,
parity-cell extension, physical W, energy or flight-hardware result is claimed.
The exact IEEE-754 implementation bound and scientific significance/novelty
are review objects, not self-approved dispositions.

Initial engineering issues repaired before delivery: Numba rejected float(bool),
and unnecessary per-pass allocations slowed tuning. These were implementation
issues, not discarded physical failures. Unsafe pilot candidates were retained;
no full-array trajectory was removed because it failed. The coarse-grid
benchmark was superseded by a separately held-out refined-analogue comparison,
with both seed identities retained in configuration.
