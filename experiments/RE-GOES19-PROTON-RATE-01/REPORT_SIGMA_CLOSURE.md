# RE-GOES19-PROTON-RATE-01-SIGMA-CLOSURE

## Scope

Only sigma(E) is varied. GOES, 4pi, E/W handling, RADAR, shielding grid and calibration are unchanged from `e2370c1ad2bb5e640efe5af549e0944ac1a16aa0`.

## Comparator provenance

`published_rpp_fluka_digitized` is digitized from Coronetti et al., DOI `10.1109/TNS.2021.3061209`, Fig. 3, printed p. 939 (PDF p. 3). It is the published FLUKA/nested-RPP simulated Cypress response, not experimental data.

Table III Cypress parameters: 10 um SiO2-equivalent BEOL; Qcrit=0.86 fC; nested volumes (side x thickness nm, alpha): 360x360/1, 984x360/0.057, 1612x360/0.037, 3160x360/0.007. No FLUKA/RPP model was rebuilt.

Publication model uncertainty is about +/-35% on average. Separate digitization allowance: typical +/-3 px = ~1.62% E and ~6.24% sigma; two overlapping peak markers +/-5 px = ~2.72% E and ~10.62% sigma. Pixel calibration/centres are reproducible in `digitize_published_physics.py`.

Comparator boundary policy: log-log interpolation of digitized FLUKA points inside plotted support; below the first point retain the Task-2 main_loglog boundary response; above the last point hold the published endpoint constant.

## Rate comparison

| Al mm | median diff | mean diff | p99 diff | max diff | temporal r | log10 r | peak changed |
|---:|---:|---:|---:|---:|---:|---:|:---:|
| 0 | +12.61% | +11.51% | +11.63% | +11.36% | 0.999999 | 0.999998 | NO |
| 1 | +7.83% | +9.45% | +9.26% | +9.54% | 1.000000 | 0.999994 | NO |
| 2 | +7.39% | +8.89% | +8.71% | +8.93% | 1.000000 | 0.999979 | NO |
| 3 | +5.57% | +8.80% | +8.78% | +8.87% | 1.000000 | 0.999956 | NO |
| 5 | -6.44% | +8.02% | +8.01% | +8.07% | 1.000000 | 0.999462 | NO |
| 7 | -6.95% | +8.16% | +8.14% | +8.26% | 1.000000 | 0.999601 | NO |
| 10 | -8.15% | +8.50% | +8.60% | +8.75% | 1.000000 | 0.999577 | NO |

Shielding ranking changed: **NO**.
Any peak timestamp changed: **NO**.
Worst change in p99/median or max/median excursion metric: **18.41%**.

## Energy decomposition

Fractions are fractions of total expected flips over common valid 5-minute intervals.

| Al mm | model | 0-3 MeV | 3-20 MeV | >20 MeV |
|---:|---|---:|---:|---:|
| 0 | main_loglog | 99.962% | 0.036% | 0.002% |
| 0 | published_rpp_fluka_digitized | 99.994% | 0.005% | 0.001% |
| 1 | main_loglog | 99.071% | 0.678% | 0.252% |
| 1 | published_rpp_fluka_digitized | 99.710% | 0.128% | 0.162% |
| 2 | main_loglog | 98.261% | 1.083% | 0.655% |
| 2 | published_rpp_fluka_digitized | 99.340% | 0.223% | 0.437% |
| 3 | main_loglog | 98.000% | 1.062% | 0.938% |
| 3 | published_rpp_fluka_digitized | 99.157% | 0.219% | 0.624% |
| 5 | main_loglog | 96.636% | 1.550% | 1.814% |
| 5 | published_rpp_fluka_digitized | 98.457% | 0.355% | 1.188% |
| 7 | main_loglog | 96.922% | 1.507% | 1.571% |
| 7 | published_rpp_fluka_digitized | 98.620% | 0.345% | 1.035% |
| 10 | main_loglog | 97.061% | 1.268% | 1.671% |
| 10 | published_rpp_fluka_digitized | 98.466% | 0.270% | 1.263% |

Paper Table IV sanity context only (ISS + 100 mil Al, Cypress): Exp/RPP = 1.89e-6/2.11e-6 (0-3), 2.34e-8/7.64e-9 (3-20), 2.22e-7/2.08e-7 (>20), total 2.14e-6/2.33e-6 SEU/bit/day.

## Validation

Reference reconstruction max rel error: `9.869e-16`
Band closure ref: `8.653e-16`
Band closure physics: `9.843e-16`

## Disposition

**B**

A <=10% key/excursion and log10 corr>=0.995; C ranking/peak change, corr<0.95, >=2x ratio factor, or >50% excursion; otherwise B

No T_scrub, sigma_k, ECC/MCU/W or F_A calculation is performed.
