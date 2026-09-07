# RE-CY62167-PAPER-COMPLETION-01 — Phase B / FINAL

**Historical disposition: PASS-B-REFERENCE-BLOCKED.** Scientific acceptance remains governed by the later Scientific Reviewer disposition and the controlling semantic repair `RE-CY62167-SEMANTICS-REPAIR-01`; this historical engineering disposition is not a Scientific Review PASS.

Starting SHA: `10661887694c075fbb27786df72a7b85f5664a05`. Branch: `research/cy62167-paper-completion-01`. COSRAD was not run by Research Engineer.

## Controlling semantic qualification

The direct/residual split is a partition of the **registered-event population under the declared W**. The current interpretation does **not** assert that every direct-class physical toggle necessarily exceeds SEC capability from every safe pre-event state. For comparison to the corresponding toggle model, the absorbing-direct construction is adopted as a conservative surrogate coupled through identical registered events, initial state and restoration actions; under that fixed coupling, `F_toggle <= F_surrogate`. This inequality is scoped to the declared population/model and says nothing about unobserved physical parent events.

Three different statements must remain separate: (1) the coupling inequality above; (2) the product-survival expression, which additionally requires the declared independent thinned processes/fixed partition assumptions; and (3) the uniform-rate pair-count certificate `Q_U`, which is a sufficient certificate under its own assumptions. Failure of `Q_U`, `DIRECT-BOUND-EXHAUSTED`, or an empty passing set on the tested action grid is **not** proof of physical infeasibility. The exploratory `tau=1 s` grid minimum is not an architectural minimum. `theta` remains a sensitivity parameter, not a measured direct-event probability.

The synthetic values near `243.554 s` and `[315.224841, 315.744501] s` are retained only as frozen formula/arithmetic regression outputs. The external proof needed to treat the interval as a verified probabilistic reference bracket is unavailable; these numbers are not used for tightness, optimality, or reference-relative resource claims.

## 1. PI COSRAD package and scenario

`results.zip` SHA-256 is `84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb`; 38 expected members are present. Parsed scenario: apogee/perigee 36000/36000 km, inclination 0 deg, argument of perigee 0 deg, start year from solar cycle 1, flight time 10 years, mean solar cycle; GCR uses even solar-cycle number; SEP uses probability 0.100. Unit SEE runs use Thin sensitive volume, Bit=1, sigma_m=1 cm2. The declared L0=0.15 runs print 0.2 in COSRAD headers and are recorded as `OUTPUT_FORMAT_ROUNDING`.

GCR (`gl_x`, `gp_x`, `gw_x_*`) and SEP peak (`sl_x`, `sp_x`, `sw_x_*`) are kept separate. SEP is `PEAK-RATE-DIAGNOSTIC; NO-MISSION-INTEGRATION-WITHOUT-DURATION`; no 10-year stationary SEP calculation is released.

## 2. Operator closure and route decision

The LET conversion `L=X/1000`, `phi_L=1000 phi_X` is numerically invariant; maximum relative discrepancy is `5.62533852782552e-15`.

However, convolution of exported `gl_x/sl_x` with the declared COSRAD unit kernel `g(L;L0)=exp(-10 L0/L) H(L-L0)` does not reproduce ion SEE column 3 of `gw_x_*/sw_x_*`. Maximum absolute relative discrepancy is `0.9915724828643783` for GCR and `1.0` for SEP. Status: **SPECTRAL_OPERATOR_NOT_CLOSED**. This remains after bounded checks of units, column choice, interpolation and quadrature.

Therefore external spectrum convolution is retained as the reproducible **article-facing spectral construction**, not claimed equivalent to the internal COSRAD SEE operator. COSRAD basis-response reconstruction is retained as an independent diagnostic/stability comparator. The available basis represents accumulation well enough for a comparator but is inadequate/ill-conditioned for the sharp direct POINT/ACS targets. No route was selected because it happened to match the old manuscript.

Because operator closure fails, LET-resolved empirical event weights derived from exported spectra are diagnostic only. GEO reference periods receive **TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS**. The Phase-A synthetic reference code remains only a frozen arithmetic regression benchmark; its external probabilistic bound proof is not part of the controlled evidence.

## 3. Legacy article regression

Direct external integration of GCR `gl_x` with the old step at LET>=33 reproduces the old anchors without post-hoc tuning:

| shield g/cm2 | Phi(L>=33), cm-2 s-1 | ACS nu_D, s-1 | nu_C total, s-1 | tau_max^U |
|---:|---:|---:|---:|---:|
| 2.0 | 2.983423304620234e-9 | 3.253378046625673e-12 | 1.525969966717954e-4 | DIRECT-BOUND-EXHAUSTED |
| 2.5 | 2.56511182575943e-9 | 2.7972156978668894e-12 | 1.4016797829826655e-4 | 20.458626524826883 s |
| 3.0 | 2.2469017248686142e-9 | 2.450212389670736e-12 | 1.3045998107864148e-4 | 45.684928214485105 s |

Thus the manuscript 20.5/45.7 s numbers are reproduced specifically under the external-spectrum article construction. They are periods certified by the declared sufficient rule, not established physical optima. Old 0.9437184% at 20 s and 0.4194304% at 45 s remain reproduced for R2 mapping-agnostic full-address scan + unconditional writeback + serial 45 ns read and 45 ns write.

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

For ARTICLE-CONFIDENCE-STYLE, the selected sufficient certificate's direct budget is exhausted at 1.50, 1.75 and 2.00 g/cm2. Positive certified periods start at 2.25 g/cm2: 8.48705, 20.45863, 32.90235, 45.68493, 71.15913 and 96.82286 s at 2.25, 2.5, 2.75, 3.0, 3.5 and 4.0 g/cm2 respectively. The **tested sufficient-certificate transition** is GRID BRACKET `[2.00, 2.25] g/cm2`, with linear interpolated estimate `2.084290039155888 g/cm2`; the latter is not a COSRAD run and is not a physical controllability threshold.

W_01_02 has zero observed heavy-ion direct POINT component on the registered-cluster support and is not treated as a physical upper or lower bound. W_00_01 and W_00_11 have identical observed heavy-ion direct populations; W_00_11 differs only through the 164 MeV proton registered cluster in the full P_MAP sweep, so it is not assigned a larger heavy-ion orbital direct term.

## 5. Reference, architecture and resource

`tau_max^ref` is **REFERENCE-NOT-AVAILABLE** for GEO because exported LET spectra fail the operator gate; diagnostic `cosrad_event_weights.csv` is generated but must not be used as validated reference input. This blocker prevents a scientifically valid numerical eta_tau or reference-relative resource-penalty release. It does not invalidate the sufficient certificate.

Frozen unconditional full-pass bounds are R1+U `0.04718592 s` and R2+U `0.18874368 s`. ERR-assisted values `0.02359296 s` and `0.09437184 s` are **read-only lower bounds / necessary read-time conditions**, not architectural minima and not exact total ERR-assisted costs. Expected ERR-assisted write cost remains `UNKNOWN / MODEL_DEPENDENT`. A sufficient full-pass feasibility check may use the declared worst-case bound of at most one write per read, numerically equal to the corresponding U full-pass bound. Every positive article-facing sufficient period on the calculated grid exceeds both U worst-case full-pass bounds; therefore full-pass feasibility is certified for that declared serial worst case, while expected E resource cost remains unknown.

The observed ACS certificate transition near 2.0–2.25 g/cm2 is therefore not an interface-speed boundary. The R2/R1 read-count ratio remains 4 and is only the resource consequence of grouping knowledge for this declared full-scan implementation.

## 6. What moves to the revised article

Recommended with the stated qualifications: frozen Phase-A 210->55 and 45/9/1 registered-cluster results; data-only 32-bit model; disjoint registered-event direct/residual populations; the nine-shield GCR POINT and ARTICLE-CONFIDENCE-STYLE rates and sufficient certificates; the certificate transition; unconditional architecture bounds and exact R1/R2 semantics; explicit SEP peak diagnostic separation; exact legacy-regression route.

Revise/remove: manuscript total 299206; claims that 55 mappings are all possible W or that proprietary W was recovered; any equivalence of registered clusters to complete same-parent MCU population; `F_art` as measured fluence; confidence-style value as a normative experimental 95% bound; parity multipliers 38/32, 1.1875 or 1.42 in the primary result; use of SEP peak as a ten-year stationary rate; claim that failure of Q_U proves physical impossibility; use of `NONE`/`NO_POSITIVE_PERIOD` as global physical infeasibility; any numerical GEO `tau_max^ref`, tightness, optimality, or reference-relative resource saving based on the frozen synthetic arithmetic pair.

GOES/decision statements remain conditional on the implemented phase model and tested action grid. Recorded phase-convergence checks are numerical sensitivity checks, not rigorous uniform error bounds. Measured energy support must remain distinct from values obtained by interpolation/extrapolation of the declared models.

## 7. Reproducibility

Historical production command recorded for Phase B:

`python run_phase_b.py --cosrad-results /path/to/results.zip`

Historical Phase-B tests: **30/30 PASS**; compileall: PASS; two complete runs were reported byte-identical. Accepted Phase-A suite remains **33/33 PASS**. Historical Python/OS/library/COSRAD build versions are not reconstructed by the semantic repair when no saved record is available; the repair environment is recorded separately in `RE-CY62167-SEMANTICS-REPAIR-01/REPORT.md`.

Large event/spectral intermediate outputs and Figure B1-B6 may be regenerated rather than committed; hashes, sizes, row counts, generator command and input fingerprint remain in the historical manifests. This semantic repair does not rerun Phase A/B and does not alter historical numerical result files.
