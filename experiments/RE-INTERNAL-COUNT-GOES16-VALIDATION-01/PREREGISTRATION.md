# Preregistration — RE-INTERNAL-COUNT-GOES16-VALIDATION-01

Frozen before the first GOES policy execution. Research Engineer implementation;
acceptance and scientific interpretation remain with Orchestrator and separate SR.

## Authority, scope and already inspected information

Base: `7b83f643efb37541547d7d93a65ba2f43acd43fd`, verified as origin/main
at preparation; branch `research/internal-count-goes16-validation-01`.
RES-003 source delivery fb6415444d028526dfc41118b52688ffb83c03dd and review
82117f8b2bea9d92ffcd807e3671ab3dd13e96db remain immutable.
Editorial requirements were inspected at 3fd5d792a0dd55ee9d46c0b7ca46c72d4eba5ea2,
PA-DOM synthesis at 4f96bb95189f0d385ea2077aa7b05d81ef8edf0d.
Those are context, not newly accepted mathematical inputs.
Known before freezing: original CTMC result tables, selected PA-DOM, certificate,
the old hourly-series context, all five days of GOES measurements, derived
intensities and the input-only window selection below. No GOES policy outcome,
production seed realization, illustration or pilot policy comparison has been
viewed. Debugging uses small artificial streams (seeds 314159, 8871).
Initial JIT-cache attempts failed on a long Windows path; a short external cache
resolves this without source changes. An input-check performance repair loads
compressed matrices once rather than repeatedly. These are technical changes,
not scientific selection.

Question: does the existing count channel change risk/resources under these
specific deterministic GOES-derived profiles? No parameter fitting or search.
An effect, tradeoff, no effect, requirement failure or quantified uncertainty
all finish this task. No hardware, mission, joint-coverage or theorem extension.

## Frozen input and quality contract

Five official files 2024-10-08 through 2024-10-12, G16 SGPS L2 avg5m v3-0-2:
[archive](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l2/data/sgps-l2-avg5m/2024/10/).
Exact URLs, SHA256, native attributes, energy bounds, retrieval time and pipeline
hashes are in input_manifest.json. It also pins RADAR
b032505d4d1b15403b8ad06aef578339f6d1c6b4 and its 192-node matrices (48 depth,
128 survival integration steps). Raw data/matrices remain outside Git.
The external [NOAA event catalogue](https://www.ngdc.noaa.gov/stp/space-weather/interplanetary-data/solar-proton-events/SEP%20page%20code.html)
records the event beginning October 9 and maximum October 10; this is an
event-selected example, not a random sample of operational conditions.

Assert g16, Level 2, PT5M, algorithm [3,2], 288 rows/day, uninterrupted 300 s
start-of-averaging-period timestamps in UTC. These metadata are directly
checked, not assumed from the filename. A bin is usable only when both
directions have all 13 finite nonnegative differential channels and integral
P11 within native valid_max, positive valid sample counts (<=301), and matching
LUT indicator. Its misleading variable name is interpreted from its long_name:
1 means LUTs match. Nonzero ignored-DQF masks are retained warnings, not
unrecorded deletions. In these data all such masks are zero. Incomplete sampling
is retained as a valid archived mean and explicitly tabulated; not asserted to
be 300 independent valid measurements. No invalid flux becomes zero exposure,
no timestamp fill, no hourly interpolation or compression. Unsupported energy
support is handled only by the declared spectral model, not missing-time fill.

Native yaw is zero throughout: sensor 0=-X/West, sensor 1=+X/East; each direction
uses its own native energy metadata. Native keV differential units are converted
by x1000 to per-MeV. P11 is integral >500 MeV. Use archived temperature-corrected
Avg*Flux, not Avg*FluxObserved; no GOES-19 channel correction is applied.
[NOAA product](https://www.ncei.noaa.gov/products/goes-r-space-environment-in-situ)
and [G16 provisional readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/docs/GOES-16_SEISS_SGPS_L1b_Provisional_Maturity_ReadMe.pdf)
supply identity/direction and calibration caveats. The older readme warns about
P5/P7, background and geometric factors. Their physical resolution in v3.2 is
NOT inferred; this task uses the as-archived nominal spectrum conditionally.

Response: inherited main_loglog per-bit sigma from the fixed experimental CSV,
3 mm Al-equivalent, gamma=2 below P1, the inherited P10/P11 high bridge and
constant sigma above 186 MeV. Transport cutoff remains 390 MeV although G16
P10 upper support is 404 MeV: the inherited 390--500 bridge models this range
once, without adding it again to transport. It is a model cutoff, not a G16
detector boundary. Above TENDL support the inherited adapter does not extrapolate
nuclear cross-sections; this physical limitation remains. Below/above measured
sigma support the original extrapolations remain PARTIAL_SIGMA_EXTRAPOLATION.
Retrospective direction-median bridge fallback is flagged (E34, W135 bins);
the controller never receives these values. This is not a physical calibration.

Exactly one 4pi isotropy-equivalent factor enters each spectral component,
including the analytic high tail. First calculate per-bit rates in s^-1,
then central=(E+W)/2, then nu=16777216*central. Scale=1.
The old GOES19 pipeline variable names do not authorize an extra array factor.
Five-minute means define constant intensities on [timestamp,timestamp+300).

All 1440 bins usable; 1429 eligible complete hours, no excluded interval.
Selection only uses exposure: largest second-half minus first-half integral,
largest total integral, then lower median of (integral,UTC). Maxima ties earliest;
median index floor((m-1)/2); duplicates calculated once, no replacements.

| Case | UTC start (H=3600 s) | Expected arrivals | Half-hour difference |
|---|---|---:|---:|
| growth (primary) | 2024-10-10 13:00 | 636.9701529394009 | 105.68192515124348 |
| peak | 2024-10-10 14:45 | 884.2977049876768 | 79.95754767343297 |
| typical | 2024-10-08 13:05 | 2.9712659356663162 | -0.15721251812779274 |

Exact arrays/UTC bounds: selected_windows.json. Derived-rate SHA256:
e3a1ce8f2a33cd9a60b22039c86ae8f1f7214458850d5a0b609042eace1bc3ac.

## Method, stream and observation contract

config.json fixes all handoff parameters. Load original core/simulate unchanged,
D=300, epsilon=.1; q0V=.07645559141483578, delta=.0002196041093111929,
floor=.07667519552414697, positive s0=.023324804475853028. Use the accepted
SR arithmetic allowance .000143018263177913 inside .0002, not the superseded
historical tally. Its conditional numerical guarantee is still only CTMC.
The executed JIT runtime is recorded; independent physical checks and finite
trace audits are not a new machine-arithmetic proof.

Five frozen policies in original index representation:
Proposed [0,2,2,0,0,0,0]; disabled [1,2,2,0,0,0,0];
Fixed [2,2,2,0,0,0,0] (1 s);
Precomputed [3,3,2,0,0,0,0] (2 s then 1 s);
PA-DOM [4,2,2,.15,20,3,1].
Precomputed chooses its block at action start, t<1800-1e-10.
PA-DOM is the selected adaptation, not a claim about the original algorithm.

Each unique profile: 20000 trials, clean independent starts, no continuation
between windows. PCG64 SeedSequence([2026091601, Unix_start_seconds//300, i])
for zero-based i. In each of 12 bins: Poisson(300*nu), sorted independent uniform
times; then independent uniform word int32 and bit int8 marks. Generate the
entire stream before executing any policy; identical bytes and event hashes
for all five, checked before/after. Batch/order changes cannot alter a stream.
Illustration uses seed2026091602, index0, once; never search for a prettier trace.
Seed2026091603 is reserved, unused (no resampling). No optional stopping.

Full original R2-U chronology: an action tau ends its pass at t+tau; scan begins
at t+tau-P, word j checks at scan_start+(j+1)P/W. Arrivals continue during scans;
repeat same-bit toggles can clear, two distinct erroneous bits cause immediate
absorbing E_cap. Individual checks clear the word, not a pass-end global reset.
Checks precede arrivals at exact equality. Legacy endpoint tolerance 1e-12 s
is retained; continuous draws have probability-zero exact ties. Terminal partial
actions retain events and individual checks but produce no completed count/update.
No physical state, survival signal, profile/date, nu, event stream or mode label
enters _choose/_observe. The harness observes first failure to stop measurement;
that censoring is not a controller observation.

Stop cost counts completed passes plus completed alternating read/write
operations in the partial final/failing pass, as original R2-U: four reads and
four writes per full word. A full pass gives 2097152 reads and writes each.
Busy time and partial operations are reported. Not processor/energy/economic cost.
Conditional pass costs use no-Ecap on H; stop costs over all trials are separate.
The shared-survivor J estimand never treats early failure as savings.

## Statistics fixed before production

Risks: exact Clopper-Pearson two-sided 95% and one-sided 95% upper; zero failures
retain nonzero upper. Nominal intervals are pointwise.
Primary family: four metrics in each of three cases, alpha=.05/12 each:
Proposed risk interval (hence upper), disabled risk interval, risk difference,
G_J. Two-sided risk intervals are conservative for the requested one-sided
upper and also permit family-protected lower>epsilon classification.
No family claim is made for extra PA-DOM and individual cost summaries.

Paired difference = p(Proposed fails,other survives)-p(reverse).
Use two two-sided CP intervals each at alpha/2, then [Lplus-Uminus,Uplus-Lminus].
Nominal alpha=.05, primary alpha=.05/12. Counts in all four paired cells retained.

Conditional means: on surviving/J samples, independent identically distributed
bounded observations conditional on the observed survivor count. Complete passes
are bounded by 12 and 18000 (H/actions, including possible terminal partial).
Use two-sided empirical Bernstein:
r=sqrt(2*s^2*log(4/alpha)/n)+7*(b-a)*log(4/alpha)/(3*(n-1)),
intersect [mean-r,mean+r] with [a,b].
This is the union of two applications of Maurer & Pontil (2009), Theorem 4,
[primary text](https://arxiv.org/html/0907.3740v1).
It remains nondegenerate at zero observed variance. For n<2 use full bounds.
For G=1-muP/muC on J, each mean interval receives alpha/2, then
[1-UP/LC,1-LP/UC]; LC>=12. Pairing is retained in the estimand but this conservative
ratio bound does not claim an efficient paired bootstrap.
Also report saved-pass mean E[NC-NP|J] with bounds [-17988,17988].
Different individual survivor populations never replace J.
Monte Carlo uncertainty is conditional on the declared profile/model, not
instrument, response, solar-event or mission uncertainty.

Classification per case: confirmed >=10% effect when both family risk uppers
<=.1 and family G lower>=.10. If also family risk-difference lower>0, label the
risk/resource tradeoff explicitly. A difference interval containing zero does
not establish equal risks. Family G upper<.10 establishes effect below threshold;
upper<0 establishes higher costs. Family Proposed risk lower>.1 establishes
requirement violation. All unresolved thresholds remain quantitatively uncertain.
No survivor sample/any numerical failure suppresses unqualified inference.

## Mandatory simple-regime bound and validation

Fixed300 is retrospective, not a sixth fitted controller. For each word and
each actual interval between checks, couple failures to the existence of a pair
of different-bit arrivals. If interval array exposure is L, expected distinct-bit
pairs in that word are (31/64)*(L/W)^2. Union over words/intervals upper-bounds
first E_cap, even though toggles can cancel. Checks at 300k-d_j,
d_j=P*(W-1-j)/W; include first and terminal gaps. With piecewise constant bins,
first L=r0*(300-d), interiors L=rprev*d+rnext*(300-d), last L=r11*d.
Use exact rational sums via E[d], E[d^2] over all W words; ceiling decimal output.
This supplies a deterministic sufficient bound, not estimated actual risk.
If >.1, status NOT_ESTABLISHED, not infeasible. Independently enumerate all
word gaps on test profiles.

Checks: independent explicit word-set oracle vs production, fixed and random
small streams for all policies; mutation sentinel; raw units and direction;
independent scalar convolution of ten direction/rows; independent window
enumeration; seed/batch invariance; Poisson and uniform marks; count-disabled qP;
zero-likelihood and lost-backup exceptions; finite trace audits on every adaptive
production trial. Shared controller functions/tables and transport matrices
are explicitly not independently reimplemented. Computational failures retain
trial/seed/hash/error and suppress complete-sample summary; no silent deletion
or fallback. Preserve upstream file hashes and record environment/resources.
Only this package is committed. Raw trials and downloaded files stay outside Git.

