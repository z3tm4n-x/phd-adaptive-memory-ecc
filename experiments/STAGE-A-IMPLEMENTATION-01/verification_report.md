# STAGE-A-IMPLEMENTATION-01 — verification report

## Result

The original implementation run recorded nine focused executable tests as PASS and used
exact `fractions.Fraction` arithmetic for decision classifications.  Scientific Review
01 later performed separate independent production-linked checks.  Those reviewer
checks are distinct evidence and must not be attributed to the original test suite or
run manifest.

## Validation-evidence distinction

**Original committed tests.** `test_stage_a.py` produced the nine PASS lines preserved
in `test_output.txt`.  As Scientific Review 01 notes, `test_phase_sum` and
`test_stationary_reduction` are algebraic checks written separately from production
`pair()`; the original executable record therefore does not by itself establish every
independent-production-link statement previously summarized here.

**Independent reviewer checks.** Scientific Review 01 independently compared an
explicit reset-timestamp/overlap-integration algorithm with production `stage_a.pair()`
and separately checked the stationary limit and artifact linkage.  The exact algorithm,
checked period/rate scope, and interpretation are preserved in
`docs/scientific_reviews/STAGE_A_SCIENTIFIC_REVIEW_01.md`, §6.  This corrective package
does not repeat the reviewer's larger check set and does not retroactively change the
original run record.

**Corrective input-gate regression.** `test_input_gate.py` is a new input-only test.
For a supplied file it requires the configured SHA-256 and then the paired-valid-row/L/H
contract, and it requires a one-byte-altered copy to fail at SHA-256.  Its code path was
exercised in this corrective environment on a controlled LF fixture: the matching
fixture was accepted and its one-byte mutation was rejected.  The exact 13,002,858-byte
upstream blob was not materialized in this correction runtime; exact-blob LF identity
and row/L/H evidence remain the independent Scientific Review 01 §6 record.  This test
does not execute the policy/science matrix.

## Input and scaling verification

The authenticated GitHub read of the frozen upstream implementation at commit
`619cb3538e296b3619f21301a176665f4611143f` shows `N_BITS = 16_777_216` in
`rate_pipeline.py`.  The accepted upstream validation defines the device/full-array rate
as `N_BITS * integral(F_sh(E)*sigma_bit(E)dE)`, with unit `s^-1`.  Stage A also uses
`N=16_777_216`; therefore the array scaling matches and no silent rescaling was made.

The frozen CSV identity is recorded as:

- git blob SHA: `5de108c6759bcf720073b3fbc6581389d46e63aa`;
- canonical LF Git-blob SHA-256:
  `9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`;
- historical CRLF serialization SHA-256 (provenance only):
  `713eceb0df3faa4ea0eb50f6381c5a26cfb77a969f82e059f58815e8469f1e09`;
- paired-valid rows: `16971`.

The original cloud execution did not materialize the complete private-repository file.
Scientific Review 01 subsequently established that the pinned Git blob is LF and has the
canonical SHA-256 above; the former value is the CRLF serialization hash.  The corrected
reproduction gate therefore uses the canonical LF bytes without newline normalization.
The original historical `run_manifest.json` is intentionally unchanged.

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
