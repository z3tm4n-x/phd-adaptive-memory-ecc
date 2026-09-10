# RE-CY62167-PROTON-01 — CY62167GE30-45ZXI proton experimental interface

## Scope and disposition

This bounded study uses the proton files of Zenodo DOI `10.5281/zenodo.8314389` and the controlled literature set for **CY62167GE30-45ZXI only**. It does not build an ECC failure model, infer the proprietary physical-to-logical mapping, run GOES/RADAR, interpolate multiplicity cross sections, or select a scrub period.

**Disposition: B — experimental `sigma_bit(E)` plus conditional multiplicity/geometry data are recoverable, but a complete absolute `sigma_k(E)` interface is not.**

The exact blocker is the absence of an independently reported **fluence aligned one-to-one with each Zenodo proton file/acquisition segment**, together with incomplete run-specific metadata (especially static/dynamic mode, package state for the 29-MeV/high-energy raw files, and the exact read/correction cadence). Fluence is therefore not reconstructed from `sigma_bit` or from the event counts.

## 1. Zenodo parser and data integrity

All 14 requested proton files pass strict parsing and `NUMBER OF EVENTS == number of parsed cell rows` for every record. The parser supports the two formats found in the dataset:

- timestamped records with a three-integer cell row; the leading integer is preserved as `field0_raw` and **no undocumented semantics are assigned**;
- non-timestamped records with two-integer cell rows.

In timestamped files a very specific all-zero `03:03:03` record is classified as a service/end-of-segment sentinel only when the otherwise-unknown leading integer also exceeds `2,097,151`; that threshold is used **only as part of the observed numerical signature**, not as an interpretation of `field0_raw`. Similar all-zero cluster-0 records in non-timestamped files are retained and flagged as ambiguous rather than deleted. Candidate acquisition segments are created only at cluster-ID resets; they are **not** promoted to fluence-normalized irradiation runs without independent metadata.

After excluding only strict service sentinels, the dataset contains **140,111 retained cluster records**, **162,910 recorded flipped cells**, of which **12,367 records have K>=2**.

### Multiplicity totals

| E, MeV | N_event | N_bit | N1 | N2 | N3 | max K | N2 dM>3 | N2 dInf>3 |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 0.9 | 7455 | 7507 | 7403 | 52 | 0 | 2 | 28 | 0 |
| 1 | 4690 | 4710 | 4670 | 20 | 0 | 2 | 8 | 0 |
| 1.1 | 14012 | 14090 | 13934 | 78 | 0 | 2 | 36 | 0 |
| 1.5 | 3214 | 3224 | 3204 | 10 | 0 | 2 | 3 | 0 |
| 2.5 | 28782 | 29008 | 28564 | 212 | 4 | 4 | 103 | 0 |
| 3 | 24703 | 25040 | 24383 | 309 | 9 | 8 | 140 | 0 |
| 4 | 4336 | 4406 | 4269 | 64 | 3 | 3 | 9 | 0 |
| 5 | 1994 | 2053 | 1936 | 57 | 1 | 3 | 5 | 0 |
| 29 | 1165 | 1183 | 1147 | 18 | 0 | 2 | 1 | 0 |
| 40 | 12442 | 16402 | 9972 | 1588 | 509 | 11 | 55 | 0 |
| 80 | 10890 | 15325 | 8489 | 1360 | 541 | 12 | 42 | 0 |
| 124 | 9404 | 13632 | 7177 | 1250 | 468 | 15 | 38 | 0 |
| 164 | 8668 | 13358 | 6446 | 1176 | 463 | 29 | 45 | 0 |
| 186 | 8356 | 12972 | 6150 | 1169 | 469 | 19 | 32 | 0 |

`multiplicity_by_energy.csv` reports descriptive whole-file energy totals. Candidate acquisition-segment boundaries/counts are reported separately in `zenodo_runs.csv`, and segment-level false-MCU diagnostics are in `false_mcu_estimates.csv`. Wherever a file contains cluster-ID resets, segment-aware interpretation is safer; the whole-file totals must **not** be interpreted as pooling verified identical runs, because run-specific voltage/mode/sample metadata are not available. `P(K=k|E)` is therefore an empirical distribution **conditional on the registered Zenodo cluster records**. Zenodo calls these raw MCU data, but it does not explicitly prove that every file is a complete sample of all physical particle impacts during a single fluence-normalized run; the output does not make that stronger claim.

## 2. Geometry and the clustering-criterion discrepancy

The parser preserves each retained cluster's coordinates, timestamp (when present), `xadd/yadd`, header bounds, and the undocumented leading integer without assigning new semantics. `geometry_by_energy.csv` is the compact analysis interface derived from those records: it reports per-`(E,K)` bounding/pairwise-distance/connectivity summaries and the complete K=2 distance/orientation distribution with `P(geometry | E,K)`. Signed coordinates and timestamps remain preserved in the source records/parser rather than duplicated in this compact repository table. This keeps the repository output auditable without duplicating the ~1 MB event-detail table already reproducible from the Zenodo files and parser.

A material consistency finding is that the raw files do **not** obey a literal Manhattan-diamond cutoff `dM<=3` for all two-cell clusters: **545 K=2 records have dM>3**. In contrast, **all K=2 records satisfy `dInf<=3`** (`0` violations). Examples therefore exist with `|dx|=|dy|=3`, giving `dM=6` while remaining within a ±3-cell-per-axis window.

This reconciles the source wording only partially. Rezaei 2020 and the later same-SRAM paper use the label “Manhattan distance 3”, whereas the original Bosser clustering paper describes a detection window extending **three cells in every direction** and recursive cluster growth. The Zenodo two-cell geometry is exactly consistent with that square/infinite-norm window, not with a literal MD3 diamond. The study consequently reports both metrics instead of silently rewriting the dataset. For K>=3, only **9** retained clusters are not connected under a simple transitive `dInf<=3` graph, indicating that a few records likely reflect additional merge/temporal logic not fully reconstructible from the published algorithm.

At high proton energies, K=2 events are strongly dominated by same-x (“vertical” in the dataset coordinate convention) pairs, qualitatively supporting the published observation that 65-nm two-cell MCUs preferentially follow the vertical/column direction. This is kept as a geometry statement only; no MCU is promoted to an MBU.

## 3. False-MCU estimates

`false_mcu_estimates.csv` implements the formulas of Franco et al. 2020 and keeps two spatial interpretations in parallel:

- literal published MD3: cell influence area `S1=24`;
- raw-coordinate-consistent square/IND3: `S1=48`.

For false 2-bit events the primary estimate uses the observed singleton count as the SBU proxy, as required by the paper. A deliberately pessimistic all-bitflip diagnostic is also reported. For timestamped segments, an additional approximate temporal estimate counts only same and adjacent observed timestamp bins, corresponding to the published rule that continuous-beam clustering can span consecutive readouts. This is explicitly marked reconstructed, because the dataset is already clustered and does not expose the original pre-clustering readout population.

For false 3-bit events the CSV gives Franco-2020 optimistic/pessimistic pooled bounds: three independent SBUs (their factor M=1...3) plus an SBU falling in the influence area of an observed 2-bit MCU. Observed N1/N2 are proxies for the unknown true SBU/MCU populations, so these are diagnostic expectations, not corrections to individual clusters. No cluster is labeled “false”.

The implementation is independently sanity-checked against the Rezaei 2020 worst static case: using their 1003 total affected cells and literal MD3 gives about 0.719 expected false pairs, reproducing the paper's stated ~0.71. The same paper also demonstrates why pooling over many dynamic read cycles is too pessimistic; this is why temporal and pooled diagnostics remain separate.

There are **14 timestamp-bearing segment(s)** for which the reconstructed same/adjacent-bin estimate can be reported and **5 segment(s)** without timestamps, for which no exact temporal false-MCU estimate is claimed.

## 4. Experimental `sigma_bit(E)`

`sigma_bit_experimental.csv` contains experimental points only. Low-energy CNA points (0.9–5 MeV) and high-energy KVI points are controlled marker-centre digitizations from the cited experimental figures; FLUKA and Weibull curves are not copied into the table. Experimental source error bars are 95% intervals combining event-count statistics and about 10% fluence uncertainty; the digitization itself is separately flagged and no invented numerical “digitization uncertainty” is substituted for the source CI.

The low-energy response is strongly non-monotonic: the published Cypress peak lies near 0.8–1 MeV and reaches about `1.2e-9 cm2/bit`; at high energy the response is of order `8e-14 cm2/bit`. A separate exact literature anchor at 184 MeV is `7.73e-14 cm2/bit`; the Zenodo file is labelled 186 MeV, so the two energy labels are not silently equated.

The 29-MeV point is left unresolved in the raw-aligned table. Open literature confirms a 29.0-MeV TOP-IMPLART campaign on the same part and shows packaged and delidded measurements, but the Zenodo file does not identify which configuration it represents and the controlled source set did not yield a uniquely alignable numerical point/fluence for that raw file.

## 5. Why absolute `sigma_k(E)` is not produced

The event numerators `N_k` are available at every requested energy, but the denominator `Phi` is not independently aligned to the corresponding Zenodo file/segment. Therefore `sigma_k_experimental.csv` records the numerators and status `NOT_COMPUTABLE_MISSING_ALIGNED_FLUENCE`, with the cross-section field empty.

This is intentional. Computing `Phi = N_bit/(N_bits*sigma_bit)` from the digitized `sigma_bit` curve would be circular and would violate the task contract. Fluences from the separate Rezaei 15.6-MeV low-VDD campaign are retained only as methodological evidence and are not transferred to the Zenodo energies.

Consequently, `consistency_check.csv` evaluates the left side `N_bits*sigma_bit` where an experimental point exists but leaves `sum_k k*sigma_k` empty. No artificial normalization is applied.

## 6. Architecture facts recorded, not modeled

The device is a 16-Mbit SRAM with embedded ECC. The experiment disables the ECC. AN88889 documents an internal `(32,38)` Hamming organization (32 data + 6 parity bits) and 16-bit interleaving. The datasheet states that an error detected/corrected on read is **not automatically written back** to the array. These facts are retained only as architecture metadata; no ECC capability event, MBU mapping, or unknown `W` is inferred from the Zenodo MCU coordinates.

## 7. Citation-trail and supplementary-material audit

A targeted backward/forward citation audit was performed after the controlled-PDF extraction, including Scite and public repository searches. It produced useful **context**, but did not close the run-fluence denominator. In particular:

- Cazzaniga et al., `10.1109/TNS.2021.3123814`, describes the same CNA low-energy-proton dosimetry campaign and explicitly says that the SRAM results are in its refs. [26] and [31]. Following those references closes back to the already-controlled PDI 2021 and REDW 2020 sources; it does **not** expose a separate run manifest or per-file fluence table.
- Cecchetto's thesis (`CERN-THESIS-2021-330`, `tel-03391539`) adds the most useful missing protocol context: the tester used a checkerboard pattern, read the memory every few seconds/minutes depending on facility flux, counted mismatches and subsequently corrected them, with Cypress-65 ECC disabled and nominal 3.3-V supply unless otherwise stated. It also explicitly places 29 MeV at TOP-IMPLART and 40/50/80/124/164/184 MeV at KVI. This strengthens facility attribution but still does not provide a one-to-one mapping from Zenodo cluster files/segments to fluence.
- Cecchetto et al., `10.1109/TNS.2021.3064666`, provides an exact `7.73e-14 cm2/bit` 184-MeV KVI anchor for the same Cypress-65 family. Because the Zenodo raw file is labelled 186 MeV, this is retained as an adjacent exact literature anchor rather than relabelling the raw data.
- Rezaei et al., `10.1109/RADECS50773.2020.9857721`, provides same-device 15-MeV high-flux experiments and demonstrates that measured cross section can depend strongly on flux. It is therefore important methodological evidence against borrowing fluence or pooling unrelated runs, but it is a separate campaign.
- Public RADSAGA/CORDIS deliverables on dosimetry, test setups, and the SRAM monitor were also checked as potential supplementary sources. They document the project/facility infrastructure, but no publicly indexed one-to-one `Zenodo file/segment -> fluence` mapping was found.

No ResearchRabbit integration is exposed in this session, so its private graph could not be queried directly. The citation-graph role was covered with Scite plus backward/forward public citation searches. This negative result is recorded so that the same source trail does not need to be repeated later.

## Answers to the four required questions

1. **Can `sigma_bit(E)` be reliably recovered? — PARTIAL.** Yes for a useful experimental low-/high-energy response using published points and controlled digitization, with an exact 184-MeV anchor; 29-MeV raw alignment and pointwise numerical uncertainties remain incomplete.
2. **Can absolute `sigma_k(E)` be recovered? — NO for the target Zenodo proton files.** `N_k` is known, but independently aligned fluence is missing.
3. **Can `P(K, geometry | E)` be recovered? — PARTIAL.** The complete registered-cluster multiplicity and event geometry in each supplied file are available, but the files do not prove a complete fluence-normalized physical-event population and the exact proprietary/post-processing implementation is not fully published.
4. **What is missing for the next step?** A run manifest linking each Zenodo file/segment to exact fluence (and preferably flux), sample/package state, static/dynamic mode, read/correction cadence, and the exact clustering-tool interpretation of the ±3 spatial rule. A one-to-one run identifier linking raw cluster files to facility logs would close the main blocker.

## Reproducibility

Parser/data-integrity validation:

```bash
CY62167_ZENODO_DIR=<zenodo-dir> python3 -m unittest -v test_parser.py test_dataset.py
```

The repository CSV/JSON tables are frozen outputs derived from the checked raw files. The source manifest records supplied input hashes, and the parser/tests provide the auditable raw-data interface. No publication PDFs are committed to Git.
