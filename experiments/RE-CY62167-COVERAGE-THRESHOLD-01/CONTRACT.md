# RE-CY62167-COVERAGE-THRESHOLD-01 — pre-execution contract

This file freezes the numerical question before `I1`, `I2`, `a`, `b`, any slack, or any coverage threshold is inspected.

## Fixed slice

- `t0=2026-01-19T04:00:00+00:00`, `H=86400 s`;
- `10 mm Al`, `main_loglog`, `central_mean`, `DREG`;
- `W32_seq` analysis mapping only;
- `W=2^19`, `n=32`, `N_data=2^24`;
- Fixed `tau=1 s`, deterministic periodic fixed-phase checks;
- clean initial state, no pending write;
- conditional write after singleton only; deterministic common upper `0<=Delta<tau`, completion before the next check;
- `epsilon_analysis=0.001`, an analysis line, not a device requirement.

The proof/executor result accepted after SR-03 is immutable input and is not re-tested here.

## Input recovery rule

The historical 53.4-MB `RE-CY62167-ECC-RISK-BRIDGE-01/direct_rate_5min.csv` is not available as full bytes. A full frozen upstream `RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv` is available with SHA-256 `9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d`, 16992 rows and Git blob `5de108c6759bcf720073b3fbc6581389d46e63aa`.

For DREG the frozen registered-direct table has `N_direct_W32seq=0` and `p_registered_direct_W32seq=0` at every measured proton energy, while `accumulation_bits_W32seq=N_registered_bitflips`. The source-equivalent selected slice therefore uses the upstream 10-mm whole-device bit-upset rate unchanged:

`nu_C_bit_DREG_s-1 = d10_lambda_central_s-1`,

then

`r(t)=nu_C_bit_DREG_s-1 / 2^24`.

This identity is confined to the declared registered DREG model. It is not a full-device physical coverage statement.

## Required validation before arithmetic

The extractor must reject: wrong upstream SHA, wrong row count/header, missing/duplicate selected timestamps, timestamps not exactly 300 s apart, negative/nonfinite rates, wrong selected row count, and a selected interval not exactly `[t0,t0+H)`.

The selected-rate output must contain all 288 five-minute bins, each with its actual duration and both whole-device and per-bit rate.

## Frozen arithmetic

Using exact decimal input strings and actual durations:

`I1 = sum r_i*dt_i`,

`I2 = sum r_i^2*dt_i`,

`a = W*C(32,2)*tau*I2`,

`b = 31*W*I1/tau`,

`U_model(Delta) <= min(1,a+b*Delta)`.

Signed slack is `s(Delta)=epsilon_analysis-U_model_upper(Delta)`. Negative slack is preserved. The model-level sufficient region is `delta_cov_upper <= s(Delta)` only when `s(Delta)>=0`, with equality accepted.

If `b>0` and `a<=epsilon`, the conditional zero-coverage delay boundary is `(epsilon-a)/b`; otherwise it is absent. `Delta<tau` remains a separate executor condition.

The reporting Delta values are frozen in `config.json`. `45 ns` is a formula-only diagnostic because the datasheet minimum write-cycle time is not an executor WCET.

## Physical conclusion rule

The subtraction `epsilon-U_model` is a requirement, not measured physical coverage. A device-level sufficient statement additionally requires a separately justified event/contract `C` such that the full physical process agrees with the registered reference model on `C` and `Pr(C^c)<=delta_cov_upper` for the same environment/horizon. Existing sources will be checked only for such a quantitative upper; qualitative uncertainty is not converted into a number.

Statuses are exactly `SUFFICIENT`, `INSUFFICIENT`, `NOT_ESTABLISHED` and always name their object.
