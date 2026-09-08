# STAGE-A-IMPLEMENTATION-01 — verification report

## Result

All mandatory focused checks passed.  Decision classifications use exact
`fractions.Fraction` arithmetic on the frozen decimal inputs; binary floating point is
used only to render CSV values.  No numerically unresolved case was found.

## Checks performed

| Check | Result | Method |
|---|---:|---|
| `nu_C + 2 nu_D = b` | PASS | exact algebra over all frozen `d`, levels and accepted `rho` values |
| R2-U minimum period and 300 s divisibility | PASS | all `tau in U` satisfy `tau >= P` and `300/tau` integral |
| word reset phase / cross-boundary exposure | PASS | independent explicit interval construction on small memories (`N_w=3,4,5,7,8`) compared with production closed form |
| stationary reduction | PASS | exact equality to `beta tau T nu_C^2`, `beta=31/(2*2^24)`, in collapsed-phase limit |
| zero direct limit (`rho=0`) | PASS | `Lambda_D=0` exactly |
| zero residual limit (`rho=1`, algebraic diagnostic only) | PASS | accumulation term exactly zero; `rho=1` is not added to the execution grid |
| pass/read/write/occupied-time identities | PASS | `reads=writes=passes*2^21`, occupied time `passes*P` |
| common first action for identical prefixes | PASS | every selected causal policy has `LL.tau1=LH.tau1` and `HL.tau1=HH.tau1` |
| no future-level knowledge | PASS | causal root enumeration parameterizes first action only by current `L/H` |
| `Fixed subset Precomputed subset Causal` | PASS | constructive feasible-set checks in every non-direct-pruned execution case |
| row-storage-order invariance | PASS | frozen-level extraction is order-statistic based; production consumes only frozen `L/H` |
| tie rule | PASS | focused unit check plus actual precomputed selections where the period-maximization tie-break is exercised |
| numerical boundary audit | PASS | exact rational `Q-epsilon` / `Lambda_D-epsilon`; no tolerance classification |

`verification.json` is the machine-readable check record.  `numerical_boundary_summary.csv`
contains the closest exact direct/certificate boundary for every known-rho `d x rho x epsilon` case.
The smallest reported absolute certificate gap is still classified exactly; no equality
or arithmetic ambiguity was delegated to binary float.

## Input and scaling verification

The authenticated GitHub read of the frozen upstream implementation at commit
`619cb3538e296b3619f21301a176665f4611143f` shows `N_BITS = 16_777_216` in
`rate_pipeline.py`.  The accepted upstream validation defines the device/full-array rate
as `N_BITS * integral(F_sh(E)*sigma_bit(E)dE)`, with unit `s^-1`.  Stage A also uses
`N=16_777_216`; therefore the array scaling matches and no silent rescaling was made.

The frozen CSV identity is recorded as:

- git blob SHA: `5de108c6759bcf720073b3fbc6581389d46e63aa`;
- accepted upstream SHA-256:
  `713eceb0df3faa4ea0eb50f6381c5a26cfb77a969f82e059f58815e8469f1e09`;
- paired-valid rows: `16971`.

In this cloud execution the connector exposed the frozen text and exact source rows but
did not materialize the complete private-repository file as local bytes.  Thus the
SHA-256 was not independently recomputed in the execution container.  This is an
execution-environment verification limitation, not a change of scientific input.  The
reproduction command uses `git show` to materialize the exact commit blob and
`stage_a.py --frozen-csv ...` then hard-fails on SHA-256, row-count, or `L/H` mismatch.

## Focused tests

Executed command:

```bash
python3 experiments/STAGE-A-IMPLEMENTATION-01/test_stage_a.py
```

Observed result in the implementation environment:

```text
PASS test_causal_prefixes
PASS test_class_inclusion
PASS test_config_architecture
PASS test_conservation
PASS test_limits
PASS test_phase_sum
PASS test_resources
PASS test_stationary_reduction
PASS test_tie_rule
9 tests passed
```

Implementation environment: Python 3.13.5, Linux 6.18.35 x86_64, glibc 2.41.  The Stage
A implementation itself uses only the Python standard library.

## Remaining validity limits

The checks validate the accepted finite surrogate/certificate implementation.  They do
not validate proprietary physical-to-ECC mapping, parity-bit behavior, real estimator or
control acquisition cost, COSRAD/transport physics, mission scenario probabilities, or
physical calibration of `rho`.  Certificate failure is not interpreted as physical
infeasibility, and the finite causal comparator is not an absolute bound on all adaptive
methods.
