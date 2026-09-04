# RE-CY62167-PAPER-COMPLETION-01 — Phase B / FINAL

**Disposition: PASS-B-REFERENCE-BLOCKED**

Starting SHA: `10661887694c075fbb27786df72a7b85f5664a05`. Branch: `research/cy62167-paper-completion-01`. COSRAD was not run by Research Engineer.

## 1. PI COSRAD package and scenario

`results.zip` SHA-256 is `84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb`; 38 expected members are present. Parsed scenario: apogee/perigee 36000/36000 km, inclination 0 deg, argument of perigee 0 deg, start year from solar cycle 1, flight time 10 years, mean solar cycle; GCR uses even solar-cycle number; SEP uses probability 0.100. Unit SEE runs use Thin sensitive volume, Bit=1, sigma_m=1 cm2. The declared L0=0.15 runs print 0.2 in COSRAD headers and are recorded as `OUTPUT_FORMAT_ROUNDING`.

GCR (`gl_x`, `gp_x`, `gw_x_*`) and SEP peak (`sl_x`, `sp_x`, `sw_x_*`) are kept separate. SEP is `PEAK-RATE-DIAGNOSTIC; NO-MISSION-INTEGRATION-WITHOUT-DURATION`; no 10-year stationary SEP calculation is released.

## 2. Operator closure and route decision

The LET conversion `L=X/1000`, `phi_L=1000 phi_X` is numerically invariant; maximum relative discrepancy is `5.62533852782552e-15`.

However, convolution of exported `gl_x/sl_x` with the declared COSRAD unit kernel `g(L;L0)=exp(-10 L0/L) H(L-L0)` does not reproduce ion SEE column 3 of `gw_x_*/sw_x_*`. Maximum absolute relative discrepancy is `0.9915724828643783` for GCR and `1.0` for SEP. Status: **SPECTRAL_OPERATOR_NOT_CLOSED**. This remains after bounded checks of units, column choice, interpolation and quadrature.

Therefore external spectrum convolution is retained as the reproducible **article-facing spectral construction**, not claimed equivalent to the internal COSRAD SEE operator. COSRAD basis-response reconstruction is retained as an independent diagnostic/stability comparator. The available basis represents accumulation well enough for a comparator but is inadequate/ill-conditioned for the sharp direct POINT/ACS targets. No route was selected because it happened to match the old manuscript.

Because operator closure fails, LET-resolved empirical event weights derived from exported spectra are diagnostic only. GEO reference periods receive **TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS**. The Phase-A synthetic reference benchmark remains valid and `reference_solver.py` was not changed.

## 3. Legacy article regression

Direct external integration of GCR `gl_x` with the old step at LET>=33 reproduces the old anchors without post-hoc tuning:

| shield g/cm2 | Phi(L>=33), cm-2 s-1 | ACS nu_D, s-1 | nu_C total, s-1 | tau_max^U |
|---:|---:|---:|---:|---:|
| 2.0 | 2.983423304620234e-9 | 3.253378046625673e-12 | 1.525969966717954e-4 | DIRECT-BOUND-EXHAUSTED |
| 2.5 | 2.56511182575943e-9 | 2.7972156978668894e-12 | 1.4016797829826655e-4 | 20.458626524826883 s |
| 3.0 | 2.2469017248686142e-9 | 2.450212389670736e-12 | 1.3045998107864148e-4 | 45.684928214485105 s |

Thus the manuscript 20.5/45.7 s numbers are reproduced specifically under the external-spectrum article construction. Old 0.9437184% at 20 s and 0.4194304% at 45 s remain reproduced for R2 mapping-agnostic full-address scan + unconditional writeback + serial 45 ns read and 45 ns write.

## 4. Updated GCR results

Primary data-only accumulation is `nu_C=nu_C,HI+nu_C,p` with no parity multiplier. Proton accumulation is a separate article comparator process using E0=10 MeV, sigma_p,bit=8e-14 cm2/bit and factor 1/2, labelled **DECLARED PROTON COMPARATOR ASSUMPTION**. COSRAD proton SEE columns are not substituted for this object. Primary registered direct proton rate for the baseline is zero only as `REGISTERED-CLUSTER POINT ONLY; PHYSICAL DIRECT PROTON FLOOR NOT ESTABLISHED`.

For W_00_01 POINT-DATA-INTERPOLATED, `(f_D, S_D, tau_max^U)` over the nine shields is:

| d | f_D | S_D | tau_max^U, s |
|---:|---:|---:|---:|
|1.50|0.0435905|-0.0455773|112.9935|
|1.75|0.0399457|-0.0416078|127.81395|
|2.00|0.0369617|-0.0383803|141.84133|
|2.25|0.0342850|-0.0355022|155.75724|
|2.50|0.0320004|-0.0330583|168.97745|
|2.75|0.0299464|-0.0308709|182.53088|
|3.00|0.0281397|-0.0289545|195.83956|
|3.50|0.0249885|-0.0256289|223.49998|
|4.00|0.0223826|-0.0228951|251.54904|

For ARTICLE-CONFIDENCE-STYLE, direct budget is exhausted at 1.50, 1.75 and 2.00 g/cm2. Positive certified periods start at 2.25 g/cm2: 8.48705, 20.45863, 32.90235, 45.68493, 71.15913 and 96.82286 s at 2.25, 2.5, 2.75, 3.0, 3.5 and 4.0 g/cm2 respectively. The sufficient-model direct-controllability boundary is **GRID BRACKET [2.00, 2.25] g/cm2** with linear interpolated estimate `2.084290039155888 g/cm2`; the latter is not a COSRAD run.

W_01_02 has zero observed heavy-ion direct POINT component on the registered-cluster support and is not treated as a physical upper bound. W_00_01 and W_00_11 have identical observed heavy-ion direct populations; W_00_11 differs only through the 164 MeV proton registered cluster in the full P_MAP sweep, so it is not assigned a larger heavy-ion orbital direct term.

## 5. Reference, architecture and resource

`tau_max^ref` is **REFERENCE-NOT-AVAILABLE** for GEO because exported LET spectra fail the operator gate; diagnostic `cosrad_event_weights.csv` is generated but must not be used as validated reference input. This blocker prevents a scientifically valid numerical eta_tau/Delta_R release. It does not invalidate the sufficient bound.

Frozen architecture anchors are unchanged: R1+U `tau_min_arch=0.04718592 s`, R2+U `0.18874368 s`; ERR-assisted deterministic read floors are 0.02359296 and 0.09437184 s, with write cost `MODEL_DEPENDENT`. Every positive article-facing sufficient period on the calculated grid is `ARCHITECTURALLY-FEASIBLE` for both R1+U and R2+U. Therefore the observed ACS transition near 2.0–2.25 g/cm2 is a direct-budget boundary, not an interface-speed boundary. The R2/R1 read-count ratio remains 4 and is only the resource consequence of grouping knowledge for this declared full-scan implementation.

## 6. What moves to the revised article

Recommended: frozen Phase-A 210->55 and 45/9/1 results with their restricted/registered-cluster qualifications; data-only 32-bit model; disjoint direct/residual populations; the nine-shield GCR POINT and ARTICLE-CONFIDENCE-STYLE rates/bounds; direct-budget boundary; architecture floors and exact R1/R2 semantics; explicit SEP peak diagnostic separation; exact legacy-regression route.

Revise/remove: manuscript total 299206; claims that 55 mappings are all possible W or that proprietary W was recovered; any equivalence of registered clusters to complete same-parent MCU population; `F_art` as measured fluence; confidence-style value as a normative experimental 95% bound; parity multipliers 38/32, 1.1875 or 1.42 in the primary result; use of SEP peak as a ten-year stationary rate; claim that failure of Q_U proves physical impossibility; any numerical GEO `tau_max^ref` until COSRAD operator semantics are resolved.

## 7. Reproducibility

Primary command:

`python run_phase_b.py --cosrad-results /path/to/results.zip`

Phase-B tests: **30/30 PASS**. `compileall`: PASS. Two complete runs produced byte-identical commit-facing outputs: **DETERMINISM PASS**. Accepted Phase-A suite remains **33/33 PASS** and Phase-A source files were not modified.

Large event/spectral intermediate outputs and Figure B1-B6 may be regenerated rather than committed; hashes, sizes, row counts, generator command and input fingerprint are recorded in manifests. Final scientific disposition: **PASS-B-REFERENCE-BLOCKED**.
