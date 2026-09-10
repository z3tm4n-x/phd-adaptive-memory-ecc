# STAGE-A-INFORMATION-INTERFACE-01 — REPORT

## Executive answer

Within the accepted two-level Stage-A contract, imperfect information produces a
**finite stepwise map**, not a smooth latency/uncertainty curve.

There are exactly six timing-equivalence classes and two uncertainty classes,
hence **12 timing-by-eta parameter cells representing 11 distinct report-history
interfaces**.  The two `T000` cells have identical observation histories because
no report is available at either decision, so the eta class cannot affect the
controller history there.  The existing 12 region identifiers are retained as
parameter-cell identifiers.  The only uncertainty threshold is

\[
\boxed{\eta=\tfrac12}.
\]

For `eta < 1/2`, every delivered binary-level report identifies the true `L/H`
level.  For `eta >= 1/2`, an ambiguous `{L,H}` report is allowed; equality is
already ambiguous.

Across all five Stage-A cases certified at known `rho=0`:

1. The **complete selected Ideal Causal action tree** is implementable and
   selected only in `T111_E_EXACT`: current-level information is available at
   both action times and `eta < 1/2`.
2. For `eta >= 1/2`, the guaranteed worst-report path costs equal
   **Precomputed in every timing class**.  Singleton reports may still give
   lower report-conditioned costs, but that saving is not guaranteed.
3. Exact current information at `t=0` is **not necessary** to retain substantial
   pathwise savings.  Region `T011_E_EXACT`, with no report for the first action
   but both first- and current-second-block reports available at `t=300`, keeps
   positive guaranteed savings on `LL`, `LH`, and `HL` in every certified case.
   The minimum retained fraction across those three paths is 0.4286–0.6040.
4. In the aligned interface `s1=0, s2=300`, any positive latency
   `0 < ell <= 300 s` falls into `T010`: only the first-block report is available
   by the second action.  It retains LL/LH savings but **zero guaranteed HL
   saving**.  `ell > 300 s` gives the no-information `T000` endpoint.

Every latency statement above is conditional on the Stage-A contract with no
pre-window observations and fixed actions only at 0 and 300 s.  It is **not** a
maximum permissible latency for a real external radiation sensor.

## 1. Scope and reused scientific basis

This package changes only the declared information interface.  It retains:

- known `rho=0`;
- frozen Stage-A `L/H` levels and shielding cases;
- the four 300 s + 300 s paths `LL/LH/HL/HH`;
- the Stage-A action set `U`;
- the post-`W`, data-only SEC surrogate;
- R2-U sequential restoration, including carry through `t=300`;
- the reviewed sufficient whole-window certificate `Q`;
- the Stage-A resource contract and selection rule.

No estimator, scenario probability, report-error probability, new `rho`,
parity/ERR model, COSRAD/angular/mapping calculation, Monte Carlo, or literature
search is introduced.

The implementation decodes the retained Stage-A feasible causal roots and
second-action masks from `passing_sets.json.gz.b64`; it does not call the old
Stage-A `search()` production matrix.  Selected-path certificate values are
checked with the unchanged Stage-A production `cert()` function.

The five eligible `rho=0` cases are:

- `d=3 mm, epsilon=1e-2`;
- `d=3 mm, epsilon=1e-1`;
- `d=5 mm, epsilon=1e-3`;
- `d=5 mm, epsilon=1e-2`;
- `d=5 mm, epsilon=1e-1`.

Previously uncertified `rho=0` cases are not re-searched because restricting the
information class cannot create feasibility that was absent from the larger
Ideal Causal class.

## 2. Analytical information regions

Let

- `A0`: first measurement available before the action at 0 s;
- `A1`: first measurement available before the action at 300 s;
- `A2`: second measurement available before the action at 300 s.

The exact predicates are

\[
A_0=E_1\land(s_1=0)\land(\ell=0),
\]

\[
A_1=E_1\land(s_1+\ell\le300),
\]

\[
A_2=E_2\land(s_2=300)\land(\ell=0).
\]

Because `A0 => A1`, exactly six signatures are possible:

| Class | `(A0,A1,A2)` | Meaning |
|---|---|---|
| T000 | `(0,0,0)` | no useful report at either action |
| T001 | `(0,0,1)` | only current second-block report at 300 s |
| T010 | `(0,1,0)` | delayed first-block report by 300 s |
| T011 | `(0,1,1)` | both reports available at 300 s, none at 0 s |
| T110 | `(1,1,0)` | first report available at both actions, no current second report |
| T111 | `(1,1,1)` | current report at both actions |

The eta derivation gives two classes:

- `E_EXACT`: `0 <= eta < 1/2`;
- `E_AMBIG`: `eta >= 1/2`, including equality.

The Cartesian product therefore contains 12 timing-by-eta parameter cells, but
only 11 distinct report-history interfaces: `T000_E_EXACT` and
`T000_E_AMBIG` both contain the same no-report histories.  The identifiers and
numerical tables remain unchanged.

See `derivation.md`, `information_regions.csv`, and
`information_boundaries.json`.

## 3. Guaranteed policy map for eta < 1/2

Path order is `(LL,LH,HL,HH)`.

| Case | Precomputed | T001 | T010 | T011 | T110 | Ideal/T111 |
|---|---|---|---|---|---|---|
| 3 mm, `1e-2` | `(2100,2100,2100,2100)` | `(601,2100,601,2100)` | `(1200,1200,2100,2100)` | `(601,1200,601,2100)` | `(601,601,2100,2100)` | `(2,601,601,2100)` |
| 3 mm, `1e-1` | `(210,210,210,210)` | `(61,210,61,210)` | `(120,120,210,210)` | `(61,120,61,210)` | `(61,61,210,210)` | `(2,61,61,210)` |
| 5 mm, `1e-3` | `(900,900,900,900)` | `(301,900,301,900)` | `(600,600,900,900)` | `(301,600,301,900)` | `(301,301,900,900)` | `(2,301,301,900)` |
| 5 mm, `1e-2` | `(90,90,90,90)` | `(31,90,31,90)` | `(60,60,90,90)` | `(31,60,31,90)` | `(31,31,90,90)` | `(2,31,31,90)` |
| 5 mm, `1e-1` | `(10,10,10,10)` | `(6,10,6,10)` | `(7,7,10,10)` | `(6,7,6,10)` | `(3,3,10,10)` | `(2,3,6,10)` |

`T000` is exactly the Precomputed endpoint.

### 3.1 Retention with no information at the first action

`T011_E_EXACT` is the weakest timing region that preserves **positive guaranteed
saving simultaneously on LL, LH, and HL** in all five cases.

| Case | T011 `(LL,LH,HL,HH)` | Minimum retention across LL/LH/HL (approx.) |
|---|---|---:|
| 3 mm, `1e-2` | `(601,1200,601,2100)` | 0.600400266845 |
| 3 mm, `1e-1` | `(61,120,61,210)` | 0.604026845638 |
| 5 mm, `1e-3` | `(301,600,301,900)` | 0.500834724541 |
| 5 mm, `1e-2` | `(31,60,31,90)` | 0.508474576271 |
| 5 mm, `1e-1` | `(6,7,6,10)` | 0.428571428571 |

Thus the *full Ideal tree* needs current information at both decisions, but the
resource benefit does not: substantial savings survive when the first action is
chosen without a report, provided both old and current levels are distinguishable
at the second action.

### 3.2 What aligned positive latency loses

For aligned enabled samples `s1=0, s2=300`:

- `ell=0` -> `T111`;
- `0<ell<=300` -> `T010`;
- `ell>300` -> `T000`.

`T010_E_EXACT` retains LL and LH savings but its HL cost is the Precomputed cost
in all five cases.  The reason is informational, not a newly changed risk model:
at 300 s it knows only the first level.  On an `H` first block it cannot
distinguish `HL` from `HH`, so the second action must remain safe for `HH`.

## 4. Uncertainty result

For `eta >= 1/2`, every delivered measurement may be reported as `{L,H}`.
The all-ambiguous history is therefore an allowed adversarial history.

For every timing class and every eligible case:

\[
p_{\rm imperfect}^{\rm worst-report}(p)
=
p_{\rm Precomputed}(p)
\]

for all four paths.

This is a **guaranteed-cost collapse**, not a claim that reports are useless.
The selected policy may exploit singleton reports, and `policy_region_map.csv.gz.b64` (decoded CSV)
records those lower report-conditioned outcomes separately.  No probability is
assigned to singleton versus ambiguous reports, so they cannot be averaged.

## 5. Absolute resource scale

Each R2-U pass has

- `2^21` reads;
- `2^21` writes;
- `0.18874368 s` of serial occupied interface time.

The Precomputed interface occupancy over the 600 s window is:

| Case | Precomputed passes | occupied s | occupied fraction |
|---|---:|---:|---:|
| 3 mm, `1e-2` | 2100 | 396.361728 | 66.060288% |
| 3 mm, `1e-1` | 210 | 39.6361728 | 6.6060288% |
| 5 mm, `1e-3` | 900 | 169.869312 | 28.311552% |
| 5 mm, `1e-2` | 90 | 16.9869312 | 2.8311552% |
| 5 mm, `1e-1` | 10 | 1.8874368 | 0.3145728% |

The absolute headroom therefore varies by more than two orders of magnitude
across the accepted sensitivity cases.  A large *relative* saving does not have
one fixed engineering meaning.

Representative `T011_E_EXACT` guaranteed savings relative to Precomputed:

| Case | Path | pass saving | occupied-s saving | occupancy saving, percentage points |
|---|---|---:|---:|---:|
| 3 mm, `1e-2` | LL | 1499 | 282.92677632 | 47.15446272 |
| 3 mm, `1e-2` | LH | 900 | 169.869312 | 28.31155200 |
| 3 mm, `1e-2` | HL | 1499 | 282.92677632 | 47.15446272 |
| 5 mm, `1e-2` | LL | 59 | 11.13587712 | 1.85597952 |
| 5 mm, `1e-2` | LH | 30 | 5.6623104 | 0.94371840 |
| 5 mm, `1e-2` | HL | 59 | 11.13587712 | 1.85597952 |
| 5 mm, `1e-1` | LL | 4 | 0.75497472 | 0.12582912 |
| 5 mm, `1e-1` | LH | 3 | 0.56623104 | 0.09437184 |
| 5 mm, `1e-1` | HL | 4 | 0.75497472 | 0.12582912 |

These are scrub-service occupancy quantities only.  They are not measured
application latency, net bandwidth loss under arbitration, energy, sensor cost,
or controller cost.

## 6. Action equality, tie rule, grid and certificate

The report records separately:

- whether the complete Stage-A Ideal selected tree is representable;
- whether the common selection rule actually selects that tree;
- whether the guaranteed cost equals Precomputed;
- whether the selected policy is literally Precomputed for every report.

No case was found where the Ideal tree was representable but the common rule
selected a different tree: the two notions coincide only at `T111_E_EXACT`.

Several regions contain multiple policies tied on the primary/secondary pass
criteria; the inherited tertiary period-maximization rule selects the committed
action map.  These tie choices do not create the information loss itself.

`U` and `Q` are frozen Stage-A objects.  This task does not claim to separate
general grid conservatism or certificate conservatism from the Stage-A result.
Observed degradation relative to Ideal is caused by shared-history information
constraints *within that frozen action/certificate model*.

## 7. Retention breakpoints

No arbitrary gamma grid was evaluated.  `retention_breakpoints.csv` exports
rounded decimal **display values** of

\[
R=\frac{p_P-p_D^{worst}}{p_P-p_I}.
\]

Those decimals are approximate and must not be used to decide exact equality at
a breakpoint.  The exact query uses the already exported integer pass counts:

\[
G=p_P-p_D^{worst}=\texttt{guaranteed\_pass\_saving},\qquad
D=p_P-p_I=\texttt{ideal\_pass\_saving}.
\]

For `D>0` and a rational reporting target `gamma=a/b` with `b>0`,

\[
R\ge\gamma\quad\Longleftrightarrow\quad bG\ge aD.
\]

Decimal targets must therefore be parsed as exact decimal rationals (for example
with `Decimal`/`Fraction` semantics), not as binary floating-point values.  For
`D=0`, including `HH`, retention remains `NOT APPLICABLE`.  No rerun or gamma
grid is needed to answer an exact threshold query.

## 8. Verification

### New-information checks

The focused test suite contains 10 tests covering:

1. exhaustiveness of the six timing signatures;
2. aligned latency boundaries;
3. timestamp equality and missing-update cases;
4. the exact `eta=1/2` boundary;
5. Ideal endpoint recovery;
6. Precomputed endpoint recovery;
7. guaranteed ambiguous-report collapse;
8. bounded selected-policy pathwise cost ordering (`Ideal <= selected imperfect <= Precomputed` for the committed cells);
9. whole-window certificate margin for every selected report history;
10. resource identities.

Timing predicates and the `eta=1/2` overlap result are analytical checks
independent of the Stage-A certificate implementation.

Endpoint, selected-Q and resource checks intentionally reuse Stage-A code/data;
they are shared-code consistency tests, not an independent revalidation of the
old physical model.  Stage-A Scientific Review 01 remains the independent
production-linked validation of the old sequential-reset certificate.

### Execution-environment qualification

The cloud execution used for preparing this delivery does not mount the private
Git repository as a local filesystem.  The new solver and 10 focused tests were
executed against an equivalent reconstructed Stage-A `rho=0` fixture generated
from the exact accepted Stage-A constants/formula.  Its five feasible-root counts
`(24,60,36,72,132)`, Precomputed counts `(3,24,8,35,105)`, and all five selected
Precomputed/Ideal endpoint trees agree with the canonical Stage-A artefacts.

The committed solver itself **does not use that development fixture**: on a
repository checkout it reads the canonical retained
`STAGE-A-IMPLEMENTATION-01/passing_sets.json.gz.b64`,
`passing_sets.csv`, `selected_policy_trees.json`, and `stage_a.py`.
`reproduce.sh` regenerates the outputs from those canonical files.  For the two
gzip/base64 artefacts it compares the **decoded scientific CSV bytes**; a gzip
container/header difference is reported but does not fail scientific
reproduction or prevent the focused tests from running.  An actual decoded CSV
difference still fails.  The remaining uncompressed maps are compared
byte-for-byte.

Scientific Review 01 historically ran the original helper in Python 3.12.13: the
new calculation completed, but the command exited at the first compressed-file
`cmp` because the gzip OS-header byte differed (`02ff` versus `0203`).  The
review then established that both decoded scientific CSVs were byte-identical.
This closeout does not rewrite that historical failure; it corrects the helper's
scientific comparison criterion.

A focused Scientific Review should therefore execute `reproduce.sh` in the
pinned repository checkout and review the new observation reduction and
shared-history policy logic.  No old physics matrix rerun is required.

## 9. Minimum next interface worth testing

The next real-temporal study should not repeat the two-level map.

The load-bearing information feature exposed here is **availability of a
sufficiently discriminating current-level observation at an action update**.
A delayed report of only the preceding level preserves some savings but cannot
guarantee the `HL` saving against `HH`.

Therefore the minimum next external interface should specify, on real temporal
segments:

1. a timestamped observable actually available online;
2. its update cadence and delivery latency relative to controller action times;
3. an uncertainty/identified-set relation to the latent rate used by the risk
   model;
4. separate acquisition/controller cost.

An internal scrub-correction channel remains a separate next question because
its observations depend on the random upset process and on previous scrub
actions.  The candidate `T_rel` versus `T_obs` distinction should be derived only
after its count/reset/detection semantics are defined.

## 10. Files

- `derivation.md` — analytical timing/eta and shared-history derivation;
- `config.json` — frozen new-interface contract/provenance;
- `information_interface.py` — finite policy calculation reusing Stage-A roots;
- `test_information_interface.py` — 10 focused tests;
- `information_regions.csv` — 12 timing-by-eta parameter cells representing 11 distinct report-history interfaces;
- `information_boundaries.json` — exact boundary predicates;
- `policy_region_map.csv.gz.b64` — deterministic gzip+base64 of the report-conditioned CSV action/Q/resource map;
- `resource_summary.csv.gz.b64` — deterministic gzip+base64 of the guaranteed/best-report resource/retention CSV;
- `retention_breakpoints.csv` — rounded display values of attained retention, no gamma grid; exact threshold queries use integer `G,D`;
- `summary.json` — compact machine-readable conclusions;
- `reproduce.sh` — canonical regeneration/comparison/test command.

No HYP/RES is created and no Scientific Review status is assigned.
