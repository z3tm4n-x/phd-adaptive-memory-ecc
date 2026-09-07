# CY62167-ANGULAR-FINDING-CONTROL-01

**Task:** bounded traceability control of the already-executed angular diagnostic.

**Exact base:** `619cb3538e296b3619f21301a176665f4611143f`

**Delivery branch:** `research/cy62167-angular-finding-control-01`

This task does **not** reopen `RE-CY62167-SEMANTICS-REPAIR-01`, does not rerun Phase A/B production calculations, does not implement a production angular operator, and does not promote the retained angular numbers to an accepted result.

## 1. Disposition

The finding is controlled as follows.

1. **Confirmed implementation fact:** the committed historical `cosrad_operator.py` performs a one-dimensional `phi(L) * target(L)` convolution and contains no incidence-angle integral.
2. **Confirmed normative scalar operator:** the controlled copy of СТО ГК Роскосмос 04.01.0010-2025 defines the scalar thin-sensitive-layer angular transformation, the flux/cross-section semantics, and fixed cutoff `theta_max = 60 deg`.
3. **Not established:** exact numerical reproduction of the internal COSRAD SEE operator from the printed `gl_x/sl_x` spectra. The retained angular diagnostic reduces the earlier discrepancy, but the residual cause remains `UNKNOWN_NO_DISCRIMINATING_TEST`.
4. **Comparator assumption only:** transferring the full registered-event mark law by `L_eff = L/cos(theta)` is not established by the scalar standard and is not validated by the identified CY62167 angular publication.

The retained `f_D` and angular-contribution values are classified only as **UNREVIEWED DIAGNOSTIC**. Under the controlling semantics repair, `f_D > 1` means exhaustion of the selected sufficient-surrogate certificate budget, not physical impossibility.

## 2. Historical diagnostic provenance

The angular calculations discussed in the preceding handoff were executed in ephemeral ChatGPT Python/Jupyter tool cells on 2026-09-07.

The exact historical cell source was not persisted and is therefore recorded as:

`UNKNOWN_NOT_PERSISTED`

No later reconstruction is presented as the original historical code. No shell command existed for the historical notebook-style execution. Historical Python/OS/NumPy/pandas/SciPy versions were not captured at execution time and remain `UNKNOWN_NOT_RECORDED_AT_EXECUTION`.

The task-local CSV files only transcribe retained outputs:

- `angular_diagnostic_shield_grid.csv`;
- `angular_diagnostic_contributions.csv`;
- `cosrad_closure_diagnostic_summary.csv`.

They were **not recomputed** in this control task.

Known retained configuration is limited to what is supported by the retained outputs/handoff: `theta_max = 60 deg`, scalar effective-LET relation `L_eff=L/cos(theta)`, angular weight `cos(theta) sin(theta)`, observed linear and log-log spectrum interpolation variants, no extra solid-angle multiplier, and `f_D=T*nu_D/Q_dop` with `T=315600000 s`, `Q_dop=1e-3`.

### Inputs tied to the retained diagnostic

- `results.zip`: SHA-256 `84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb`, 69464 bytes.
- `results/gl_x.txt`: SHA-256 `7e507a77a5b1d7e3ae7e0e0c0c87ed9d87dc6a3b220d7b72b762b5d21ae72c02`, 6335 bytes.
- `results/sl_x.txt`: SHA-256 `dbd44c3322293e9bb2238343af38ba08032e1a184da5cb2021942e86ac702350`, 7191 bytes.
- frozen Phase-A COSRAD input: `experiments/RE-CY62167-PAPER-COMPLETION-01/cosrad_input_cross_sections.csv`, SHA-256 `f59311fa1991c0db0dad2dfe3e7e88b1d1e5803de51b226bd82043b223f29bda`.
- frozen full heavy-ion cross-section output identity from the existing manifest: SHA-256 `2dd525cda6c19349990f340dc32e24c6a58d0717acbdcd6f36939358122afa4b`.
- historical no-angle implementation: `experiments/RE-CY62167-PAPER-COMPLETION-01/cosrad_operator.py`, Git blob `b7e21e01c381c630100ffbb19f74f398cbca27a7`.

The existing Phase-B manifest independently records the same `results.zip` fingerprint and Thin sensitive volume / `sigma_m=1 cm2` COSRAD configuration. No raw inputs are committed by this task.

### Control-task verification environment

This is recorded separately from the historical diagnostic runtime:

- Python `3.13.5` (GCC 14.2.0);
- Linux `6.18.35` x86_64, glibc 2.41;
- NumPy `2.3.5`;
- pandas `2.2.3`.

Lightweight provenance checks used in this task included SHA-256 verification of the controlled STO PDF and COSRAD archive/member identities and JSON/CSV structural checks. No numerical sweep or production model run was authorized or performed.

## 3. Controlled normative source

### Identity

`СТО ГК Роскосмос 04.01.0010-2025` — «Типовые методики расчетно-экспериментальной оценки стойкости комплектующих изделий электронной компонентной базы бортовой радиоэлектронной аппаратуры автоматических космических аппаратов к воздействию ионизирующего излучения космического пространства по одиночным радиационным эффектам».

Controlled PDF:

- file: `СТО ГК Роскосмос 04.01.0010-2025.pdf`;
- SHA-256: `cbda322df345fd39146c4772d429b3f741dabd8343573b387cbd2b95750f0f7e`;
- size: 2168729 bytes;
- 93 PDF pages;
- PDF is **not committed**.

Copy status: the cover contains Roscosmos approval disposition dated 03.09.2025, No. `ЦА-362-рсп`, and states entry into force on 2026-01-01. The embedded foreword page still contains blank template approval/registration fields. External registry status was not independently audited because it is outside the two-source stop rule.

### Scalar flux and cross-section semantics

Section 7.2, formula (7.1), defines

`nu_TZCh = integral phi_z(L_z) * sigma_is(L_z) dL_z`.

The same section defines:

- `phi_z(L_z)` as the **total differential LET spectrum of particle flux density**, with units `particles cm^-2 s^-1 (MeV cm^2 mg^-1)^-1`;
- `sigma_is(L_z)` as the SEE cross section for an **isotropic** heavy-ion flux, in `cm^2`.

Thus the normative `phi_z` is not specified per steradian. In the controlled formula set there is no separate `pi`, `2pi`, or `4pi` multiplier to append to (7.5).

### Thin-sensitive-layer transformation

Section 7.8 states that when approximating functions (7.2)/(7.3) are used, the calculation uses a thin sensitive layer model. For function (7.2), the standard explicitly notes that this model is implemented in COSRAD.

Formula (7.5) is

`nu_TZCh = integral_[L_z0 cos(theta_max)]^[L_zmax] phi_z(L_z) * integral_0^[theta_max] sigma(L_z/cos(theta)) cos(theta) sin(theta) dtheta dL_z`.

The accompanying definitions state:

- `theta` is the ion incidence angle relative to the IC surface normal;
- `sigma(L_z)` is the SEE cross section at **normal incidence**;
- `theta_max` is the cutoff angle;
- for calculations under (7.5), `theta_max = 60 deg`.

Therefore the scalar thin-layer operator and cutoff are source-supported and do not require fitting to COSRAD.

### Important alternative in the same standard

Section 7.12 describes a different conservative procedure in which the isotropic-flux cross-section dependence is taken equal to the normal-incidence dependence for the stated worst-case treatment. This is a separate normative route and must not be silently combined with (7.5).

### What the standard does not prove

The standard establishes a scalar SEE cross-section angular transformation. It does not establish that a full registered MCU/event mark obeys

`K(m | L, theta, W) = K(m | L/cos(theta), 0, W)`.

It therefore does not by itself validate angular transport of multiplicity, coordinates, parent-event identity, or the post-`W` direct/residual classification.

It also does not prove that a printed COSRAD `gl_x/sl_x` export is numerically identical to whatever internal quadrature representation a specific COSRAD build uses. Unit compatibility is necessary but not sufficient for exact rate reproduction.

## 4. CY62167 angular publication — targeted extraction only

### Identity and full text

Mario Sacristán Barbero; Ivan Slipukhin; Matteo Cecchetto; Daniel Prelipcean; Ygor Aguiar; Kacper Bilko; Natalia Emriskova; Andreas Waets; Andrea Coronetti; Maria Kastriotou; Carlo Cazzaniga; Torran Dodd; Frédéric Saigné; Vincent Pouget; Rubén García Alía,

**“Characterization of Fragmented Ultrahigh-Energy Heavy Ion Beam and Its Effects on Electronics Single-Event Effect Testing,”**

IEEE Transactions on Nuclear Science, vol. 71, no. 8, pp. 1557-1564, 2024.

DOI: `10.1109/TNS.2024.3396737`.

Controlled final full-text location for this task: CERN Document Server record `2913173`, `https://cds.cern.ch/record/2913173`, final PDF `https://cds.cern.ch/record/2913173/files/document.pdf`.

The preliminary chat diagnostic had initially consulted an author accepted version under the same DOI. This control task checked the final published text exposed by CERN CDS; the PDF itself is not copied into the repository.

### Device and test extraction

The source identifies Cypress `CY62167GE30-45ZXI`, 65-nm, date code 1731.

For the UHE campaign described in Section VI-A:

- primary beam: `208Pb`, 150 GeV/n;
- the described UHE irradiation took place at **normal incidence**;
- device bias: 3.3 V;
- room temperature;
- read/write operation every minute;
- checkerboard pattern.

Figure 11 nevertheless compares aggregate SEU cross sections for Cypress and explicitly states Cypress tilt angles `0 deg`, `45 deg`, and `60 deg`; effective LETs and fluences are corrected with the cosine rule. The figure combines the UHE measurements with comparison measurements from other facilities. Under the stop rule, this task does **not** follow the off-normal points into additional cited sources.

Azimuth for the Cypress angular points is not reported in the targeted text inspected.

The source does not establish a Cypress embedded-ECC/ERR observation contract for these angular data. It reports the memory test operation and aggregate SEU cross sections, but not whether an event-level ECC correction/indicator stream was retained for the plotted points.

### What is measured and what is absent

Available for Cypress:

- aggregate SEU cross-section response;
- angle labels including 0/45/60 deg in Fig. 11;
- cosine-rule effective-LET/fluence correction used for the comparison.

Not available in the final article for the Cypress angular points:

- event multiplicity records;
- upset address lists;
- parent-particle/event grouping;
- cluster geometry;
- event-local marks suitable for reclassification;
- post-`W` direct/residual labels.

Therefore this source can test or constrain a **scalar total-SEU angular response comparator**, but it cannot directly test the angular transformation of the registered event law after the frozen mapping `W`.

## 5. Four claims that must remain separate

| Question | Controlled disposition |
|---|---|
| Did the old committed spectral code omit angular integration? | **YES — CONFIRMED IMPLEMENTATION FACT.** |
| Is the scalar 60-deg thin-layer operator source-supported? | **YES — CONFIRMED for the stated scalar model/domain of §7.8 and eq. (7.5).** |
| Does adding that operator numerically reproduce COSRAD from printed spectra? | **NOT ESTABLISHED.** Retained diagnostics improve agreement, but residual mismatch remains and its cause is `UNKNOWN_NO_DISCRIMINATING_TEST`. |
| Is effective-LET transport physically valid for the full registered direct/residual event law? | **NOT ESTABLISHED — COMPARATOR ASSUMPTION ONLY.** |

No item in this table is used as automatic proof of the next item.

## 6. Retained angular numbers — status only

No new sweep was run. The retained tables preserve the previously generated values solely for traceability.

### Scalar COSRAD-comparison diagnostic

The retained closure summary shows that adding the 60-deg thin-layer transform reduced the earlier no-angle discrepancy, but the outcome remains interpolation-dependent. Examples retained from the prior diagnostic are:

- GCR no-angle maximum absolute relative difference about `0.99157`;
- GCR 60-deg linear mean/max about `0.2040 / 0.4699`;
- GCR 60-deg log-log mean/max about `0.3350 / 0.7257`;
- SEP 60-deg linear mean/max about `0.2134 / 0.4657`;
- SEP 60-deg log-log mean/max about `0.3215 / 0.6214`.

These values do **not** justify assigning the residual to interpolation or any other numerical convention. The residual mismatch cause remains `UNKNOWN_NO_DISCRIMINATING_TEST`.

### Event-law effective-LET comparator

The retained `W_00_01` diagnostic using the unaccepted scalar effective-LET transfer gives `f_D` values above one across the retained shielding grid. These values remain `UNREVIEWED_DIAGNOSTIC` and are not a physical feasibility result.

The retained contribution decomposition is the more important finding: for the representative 2.0-4.0 g/cm2 shielding points, approximately 93.5-93.9% of the comparator direct integral comes from the 45-60 deg angular band, and approximately 98.1-98.4% comes from incident LET 16.5-33 MeV cm2/mg. Thus the qualitative comparator behavior is controlled by the very angular/mark-law extrapolation that is not validated by the scalar source.

The post-hoc `theta` values retained in `angular_diagnostic_shield_grid.csv` are sensitivity markers only. They are **not** fitted or admissible replacement cutoff angles; the normative scalar cutoff remains 60 deg.

## 7. What is source-confirmed versus assumed

### Source-confirmed

- historical committed code lacks the angular integral;
- СТО eq. (7.5) defines a scalar normal-incidence-to-angular thin-layer transformation;
- `theta_max = 60 deg` for that calculation;
- `phi_z` is a total differential LET flux-density spectrum without an `sr^-1` unit in the standard;
- the standard says the thin-layer model for function (7.2) is implemented in COSRAD;
- the identified Cypress source provides aggregate angular SEU comparison data including 0/45/60-deg labels and cosine-rule correction.

### Comparator assumptions / unresolved

- that the printed COSRAD LET spectrum is numerically identical to the internal object used by the relevant COSRAD SEE calculation;
- the cause of the retained residual COSRAD mismatch;
- that a scalar effective-LET substitution transports MCU multiplicity/topology/event marks;
- that the Cypress 45/60-deg aggregate points contain recoverable event-address/parent-event records;
- azimuth dependence for the Cypress angular response;
- the exact embedded-ECC/ERR observation semantics of the angular Cypress points.

## 8. Can the identified publication constrain the post-W event law?

**Not by itself.**

It can constrain scalar total-SEU angular response. It cannot evaluate the frozen post-`W` statistic

`D_W(Z) = 1{two or more distinct cells of a registered event fall in one declared word}`

because the required event-level cell/address and parent-event information is absent from the published angular result.

The publication therefore cannot validate or falsify the proposed angular direct/residual transformation at the event-law level from the information currently controlled.

## 9. Exact residual gap and one minimal next check

### Residual gap

**Scalar angular normalization is controlled. Topology-resolved angular transport of the CY62167 registered-event law remains unvalidated because the identified CY62167 angular source provides aggregate SEU response but not the event multiplicity/address/parent-event information required to reapply the frozen mapping `W`. Separately, the cause of the residual COSRAD numerical mismatch remains UNKNOWN because no discriminating test was performed.**

### One minimal next check

Do **not** start a new literature search automatically.

If an underlying machine-readable error/event log for the Cypress `0/45/60 deg` points already exists or can be supplied by PI/source provenance, obtain that exact identified dataset and test only whether it contains:

1. event-local upset addresses/cells;
2. parent-event grouping;
3. angle label and beam/LET provenance.

If present, apply the already-frozen `W` without refitting and compare by angle:

- `P[D_W=1]`;
- residual event multiplicity/mark distribution.

That is the minimum discriminating test of the event-law transformation. If those event-level fields do not exist and only scalar totals are available, record the angular publication as scalar-only evidence and stop rather than expanding the search automatically.

## 10. Task completion statement

This control task changes no frozen population, mapping, cross-section node, historical result, or production model. It records provenance and bounded source interpretation only. The appropriate next decision belongs to the Research Orchestrator; no result promotion or Scientific Review disposition is assigned here.
