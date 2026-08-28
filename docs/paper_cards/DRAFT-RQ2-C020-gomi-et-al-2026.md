# Draft Paper Card — RQ2-C020

**PAPER-ID:** `TBD until Orchestrator acceptance`  
**Candidate identity:** `RQ2-C020`  
**Related RQ:** `RQ-002`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommendation:** `CORE`  
**Exact full-text identity:** IEEE Transactions on Nuclear Science, vol. 73, no. 8, pp. 2935–2947, Aug. 2026; current version dated 18 Aug. 2026  
**Full text used:** `1eaada2bae473033ae4e87dcffe3cecf.pdf`; SHA-256 `9facf0f6086bc82557c7d18dbfa36ce7edcc2375e8cb63a49f6ec2576d586e2e`

## Bibliographic identity

Y. Gomi, K. Takami, R. Yasuda, H. Kanda, M. Fukuda, and M. Hashimoto, “Quasi Event-Wise Measurement and Simulation of Neutron-Induced Multiple-Cell Upsets in 22- and 55-nm SRAMs,” *IEEE Transactions on Nuclear Science*, vol. 73, no. 8, pp. 2935–2947, Aug. 2026. DOI: `10.1109/TNS.2026.3675003`.

## Common extraction summary

| Field | Extraction |
|---|---|
| Primitive arrival object | `[SOURCE]` Experiment: an upset record from continuous self-scanning of one SRAM macro. Physical interpretation: one neutron-induced SEU may be SBU or MCU. Simulation: one primary-neutron event with complete secondary-particle history. |
| Count/arrival process | `[SOURCE]` A Poisson particle-arrival assumption is used only to upper-bound the chance of at least two independent SEUs in one macro during one full-scan window, Eqs. (1)–(4), pp. 2938–2939. No mission-time process is fitted. |
| Stationarity/intensity | `[SOURCE]` Constant beam flux is used in the pseudo-MCU calculation; no time-varying intensity model. |
| Multiplicity/topology | `[SOURCE]` Event-wise bit addresses, 2-D row/column pattern, multiplicity, Chebyshev separation, and cluster-size diagonal are reported (Secs. IV.B–IV.C, Figs. 6–11). |
| Parent-event provenance | `[SOURCE]` Quasi-event-wise experiment makes two independent arrivals in a scan window extremely unlikely but has no neutron detector; simulation has exact event/particle provenance. |
| Mapping `W` | `[SOURCE]` Physical macro organization (32 rows×288 columns, 128×72-bit words) is given. No ECC/codeword map is applied. `[INFERENCE]` External `W` can be applied only if address-to-protected-word mapping is supplied separately. |
| Accumulation/initial state | `[SOURCE]` SRAMs initialize to zero and are continuously checked. `[UNKNOWN]` Exact writeback/reset of a detected cell is not stated in this paper. |
| Direct mechanism | `[SOURCE]` True physical MCU is multiple cell flips from one neutron-induced event; Distant MCU contains at least one flipped-cell pair at Chebyshev distance `≥2` (Sec. IV.B). |
| Sequential/false mechanism | `[SOURCE]` Pseudo MCU is erroneous grouping of multiple independent SEUs; its probability ratio is estimated from `P(n≥2)/P(1)` within one macro scan window (Sec. IV.A). |
| Observation ambiguity | `[SOURCE]` Static bitmap grouping has a distance trade-off: large distance merges independent SEUs; small distance misses/splits true Distant MCUs (Sec. IV.D, Figs. 12–16). |
| Uncertainty | `[SOURCE]` Experimental/simulation error bars are standard errors. No full classification-error likelihood or confidence intervals are supplied. Model-form uncertainties include PBA omission and sensitive-volume/cell variation (Sec. V.B). |
| Validation | `[SOURCE]` PHITS event-wise simulation is calibrated to FIT, compared with SBU/MCU/Distant-MCU ratios and cluster-size distributions; Distant-MCU ratio agrees within a factor of two, with known PBA discrepancy (Figs. 18–22). |
| Relation to `E_cap`/`F_A` | `[INFERENCE]` Provides empirical/simulated direct-event spatial marks and a false-grouping bound, but stops at event/cross-section ratios; propagation through `W`, accumulation, repair, and capability crossing is `UNKNOWN`. |

## 1. Research problem

- `[SOURCE]` Static bitmap irradiation mixes independent accumulated upsets into pseudo MCUs and cannot simultaneously capture long-range Distant MCU patterns without increasing false merging (Introduction, pp. 2935–2936).

## 2. Objective

- `[SOURCE]` Use sub-microsecond self-scan to obtain quasi-event-wise neutron upset patterns in 22-/55-nm SRAMs, quantify the limitations of static grouping, characterize Distant MCUs, and validate event-wise PHITS simulations (Secs. I, III–VI).

## 3. System/model studied

- `[SOURCE]` Bulk planar 22- and 55-nm SRAM chips, 0.7/0.9 V, irradiated by the RCNP white neutron beam approximating terrestrial spectra (Sec. III).
- `[SOURCE]` Each macro has 128 words×72 bits organized as 32 rows×288 columns, with well taps at both BL ends (Fig. 3, p. 2938).
- `[SOURCE]` Four scanning chips were active because of heat dissipation; total per-chip capacities were 1.84 Mbit (22 nm) and 0.33 Mbit (55 nm) (Sec. III.B).

## 4. Method

- `[SOURCE]` Initialize all SRAMs to zero; scan 128 words continuously at several hundred MHz; forward each detected bit-flip event to FIFO for asynchronous readout (Sec. III.A–B, pp. 2937–2938).
- `[SOURCE]` Scan intervals: 181 ns (22 nm, 0.9 V), 313 ns (22 nm, 0.7 V), 270 ns (55 nm, 0.9 V), and 371 ns (55 nm, 0.7 V) (Sec. III.B; Table I).
- `[SOURCE]` Estimate pseudo-MCU probability from flux, cross section, macro size, and scan interval under Poisson arrivals (Eqs. (1)–(4)).
- `[SOURCE]` Reconstruct conventional bitmap outputs by accumulating true quasi-event-wise records and regrouping them with Chebyshev distance thresholds; compare counts and patterns against event-wise ground truth (Sec. IV.D).
- `[SOURCE]` Simulate primary neutrons and secondary particles event by event with PHITS, tune critical charge to FIT, and compare event ratios/topology; analyze particle-level causes (Sec. V).

## 5. Assumptions

- `[SOURCE]` Independent particle arrivals in one macro/full-scan interval follow a Poisson distribution for the pseudo-MCU calculation (Sec. IV.A).
- `[SOURCE]` The short-window method cannot distinguish successive neutron arrivals individually, but their estimated probability is negligible relative to observed Distant MCUs (Secs. III.A, IV.A).
- `[SOURCE]` Simulation uses rectangular-parallelepiped sensitive volumes, selected critical charges, an extended neutron spectrum, and excludes multi-macro events not observed experimentally (Sec. V.A).
- `[SOURCE]` PHITS model lacks parasitic bipolar amplification (PBA); BL-aligned experimental flips are clustered to compare with the direct-charge simulation (Sec. V.B, Figs. 21–22).

## 6. Input parameters

- `[SOURCE]` Beam flux/spectrum, SEU cross section per Mbit, macro size `B`, scan interval `T`, technology/supply voltage, observed bit addresses, Chebyshev grouping distance, and PHITS geometry/material/critical-charge parameters (Secs. III–V).

## 7. Output parameters

- `[SOURCE]` SEU counts/cross sections; SBU/MCU/Distant-MCU ratios; pseudo-MCU probability ratio; MCU bit cross section by row; spatial patterns; multiplicity/pattern group; cluster-size distribution; particle-species attribution (Tables I; Figs. 5–24).
- `[SOURCE]` Distant-MCU cluster size is the diagonal of the smallest rectangle containing all flipped cells (Sec. IV.C.1, p. 2939).

## 8. Baselines/comparators

- `[SOURCE]` Quasi-event-wise data versus reconstructed conventional static bitmap grouping across Chebyshev distances (Secs. IV.D, Figs. 12–16).
- `[SOURCE]` PHITS simulation versus experiment for FIT, event ratios, Distant-MCU ratio, and cluster-size distributions (Figs. 18–22).

## 9. Main equations/models

- `[SOURCE]` Eq. (1): expected independent SEUs in one macro scan window `λ=ΦσBT`.
- `[SOURCE]` Eqs. (2)–(4): `P(0)=e^{-λ}`, `P(1)=λe^{-λ}`, `P(n≥2)=1−(1+λ)e^{-λ}`. Table I reports the ratio `P(n≥2)/P(1)` as pseudo-MCU likelihood relative to one SEU.
- `[SOURCE]` Static-method observation model is empirical: accumulated event-wise records are grouped when cell Chebyshev distances fall within a selected threshold (Sec. IV.D).
- `[SOURCE]` PHITS provides event-by-event primary/secondary histories; upset occurs when deposited charge in a sensitive volume exceeds tuned critical charge (Sec. V.A).

## 10. Main results

- `[SOURCE]` Pseudo-MCU/single-SEU probability ratios are `10^-12–10^-11` (22 nm) and about `10^-11` (55 nm), giving an expected pseudo/Distant-MCU ratio below `10^-8` under test conditions (Sec. IV.A; Table I).
- `[SOURCE]` Distant MCU is about 2% of all SEUs; among MCU events it is 13% for the 22-nm 0.7-V configuration. At 0.7 V, maximum cluster sizes were 7.0 µm (22 nm) and 15 µm (55 nm); the 22-nm 0.9-V dataset additionally contained a 37.15-µm event (Abstract; Sec. IV.C.4, pp. 2940–2941).
- `[SOURCE]` At Chebyshev distance 11, about 80% of Distant MCUs are captured for 22 nm at 0.7 V, while independent-event merging grows; no single distance recovers both true counts and patterns across conditions (Figs. 12–16).
- `[SOURCE]` PHITS Distant-MCU ratios agree with experiment within a factor of two, but MCU ratios—especially 55 nm—are underestimated because PBA is not modeled (Sec. V.B, Figs. 19–20).
- `[SOURCE]` After clustering BL-aligned flips to reduce PBA mismatch, simulated and experimental cluster-size distributions agree more closely (Fig. 22).
- `[SOURCE]` Particle-level simulation attributes approximately 78% of observed Distant MCUs to alpha particles; about 80% of Distant MCUs involve one secondary particle and about 20% two, with `≥3` rare (Secs. V.B–VI).

## 11. Author-stated limitations

- `[SOURCE]` Quasi-event-wise neutron measurement has no particle detector and cannot individually distinguish successive neutron arrivals within short intervals; the paper bounds their probability instead (Secs. III.A, IV.A).
- `[SOURCE]` Limited Distant-MCU counts restrict statistics, particularly for 55 nm (Sec. IV.C.4).
- `[SOURCE]` PHITS omits PBA and uses approximate sensitive volumes/critical charge; remaining discrepancies may arise from geometry and cell variation (Sec. V.B).
- `[SOURCE]` Events spanning multiple macros are theoretically possible but were not observed and are excluded from simulation analysis (Secs. III.A, V.A).

## 12. Methodological limitations inferred

- `[INFERENCE]` The pseudo-MCU bound depends on HPP/constant-flux assumptions and a macro-wide full-scan association window; it is not a general operational false-classification model.
- `[INFERENCE]` Event grouping within the quasi-event-wise hardware is not specified as a formal timestamp/association algorithm beyond scan-window reasoning, so exact temporal resolution within one scan is unobservable.
- `[INFERENCE]` Standard errors do not provide a complete uncertainty model for sparse tail topology, classification error, or simulation calibration.
- `[INFERENCE]` No ECC mapping or capability calculation connects measured physical patterns to logical failure.

## 13. Threats to validity

- `[INFERENCE]` Construct validity: experimental parent-event identity is probabilistic, not detector-confirmed for each neutron.
- `[INFERENCE]` Observation validity: exact flip time/order inside a sequential scan and exact detection/reset behavior are not reported.
- `[INFERENCE]` External validity: two bulk planar nodes, two voltages, one beam spectrum, and bespoke scanning chips may not transfer to other SRAMs/environments.
- `[INFERENCE]` Simulation validity: fitted critical charge and omitted PBA permit compensating errors; factor-two agreement is not exact mechanism validation.

## 14. What the paper actually demonstrates

- `[SOURCE]` Under the stated beam, device, and scan conditions, independent multi-arrival contamination is orders of magnitude below observed direct Distant MCU frequency (Sec. IV.A).
- `[SOURCE]` Static bitmap distance grouping has an empirical false-merge/true-split trade-off when long-range direct events coexist with accumulated independent upsets (Sec. IV.D).
- `[SOURCE]` Quasi-event-wise measurements preserve physical address patterns that support event-level topology characterization and simulation comparison.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` The source does not prove true parent-neutron identity for each experimental event or a universal pseudo-MCU bound outside its flux/scan conditions.
- `[INFERENCE]` It does not define a category of “Distant MCU missed because the observation window is short.” The demonstrated miss mechanism is primarily a **spatial grouping cutoff** in static bitmap analysis; short windows reduce false accumulation.
- `[INFERENCE]` It does not provide codeword failure, scrubbing, `E_cap`, or `F_A` probabilities.
- `[INFERENCE]` It does not supply a separately measured pseudo-MCU cross section; pseudo frequency is a model-based bound.

## 16. Relevance to the dissertation

- `[INFERENCE]` Supplies high-value empirical direct-event marks `(parent proxy, physical addresses, multiplicity, topology)` and an explicit observation/classification-bias example.
- `[INFERENCE]` Supports keeping direct same-particle and sequential accumulation provenance separate and adding an observation model when ingesting bitmap data.
- `[INFERENCE]` Physical addresses can be transformed through an external `W`, but the paper itself does not provide the controller/ECC map.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` A sub-microsecond scan window makes independent-event pseudo MCUs negligible relative to observed Distant MCUs under the tested beam/device conditions (Eqs. (1)–(4); Table I).
2. `[SOURCE-CANDIDATE]` Distant MCU is defined by at least one pair of flipped cells with Chebyshev distance `≥2` (Sec. IV.B).
3. `[SOURCE-CANDIDATE]` Static bitmap grouping cannot simultaneously avoid pseudo-MCU merging and recover all long-range Distant MCUs for the tested datasets (Sec. IV.D, Figs. 12–16).
4. `[SOURCE-CANDIDATE]` Event-wise PHITS preserves primary/secondary provenance unavailable in the neutron measurement (Sec. V).
5. `[INFERENCE-CANDIDATE]` Observation/classification uncertainty must be modeled separately from the physical marked-event process before using static bitmap data for `E_cap`.

## 18. Tensions/conflicts

- `[SOURCE]` Experimental “ground truth” is quasi-event-wise, whereas exact particle provenance exists only in simulation; these are different evidence levels.
- `[INFERENCE]` A marginal MCU cross section loses the spatial mark needed to apply an external `W`, despite the measurement retaining that information.

## 19. Open questions/evidence gaps

1. `[UNKNOWN]` What exact writeback/reset occurs after FIFO detection, and can a cell remain upset across scans?
2. `[UNKNOWN]` What formal hardware grouping/timestamp rule associates multiple detected cells with one event?
3. `[UNKNOWN]` How stable is the pseudo-MCU bound under field flux nonstationarity or burst exposure?
4. `[UNKNOWN]` What codeword-multiplicity distribution results after the target `W`?
5. `[UNKNOWN]` How should standard errors, false-grouping probability, PBA model error, and critical-charge uncertainty be propagated into `E_cap/F_A`?

## Direct answers to mandatory measurement questions

- **True MCU:** `[SOURCE]` Multiple cell flips caused by one physical neutron-induced event; exact event provenance is available in simulation and probabilistically supported, not detector-confirmed, in the experiment.
- **Pseudo MCU:** `[SOURCE]` Multiple independent SEUs erroneously grouped as one MCU; bounded over one macro/full-scan time by `P(n≥2)/P(1)`.
- **Distant MCU:** `[SOURCE]` An MCU containing at least one flipped-cell pair with Chebyshev distance at least two.
- **“Distant MCU missed by short observation window”:** `[UNKNOWN]` No such formal category is defined. Static spatial cutoff misses Distant MCUs; shortening the temporal window suppresses pseudo MCUs.
- **Unobservable quantities:** `[INFERENCE]` Exact incident neutron/secondary identity in experiment, exact ordering within a scan, and multi-arrival separation within the same scan.
- **Separate rates:** `[SOURCE]` SEU/MCU/Distant-MCU ratios and cross sections are measured; pseudo-MCU is a Poisson-based probability bound, not a separately observed cross section.
- **Propagation:** `[UNKNOWN]` The source ends at cross-section/event/topology and simulation-validation levels; it does not propagate to `E_cap` or `F_A`.

## Equations and assumptions requiring reproduction

- Reproduce Eqs. (1)–(4) per macro and per exact full-scan interval, and compute the reported pseudo/single ratio as `P(n≥2)/P(1)`.
- Preserve the four configuration-specific scan intervals and the all-zero initial pattern.
- Reconstruct static bitmap results from event-wise records with the same Chebyshev-distance rule before comparing false merges/splits.
- Keep experimental quasi-parent provenance distinct from PHITS exact event/particle provenance.
- Reproduce PHITS geometry, spectrum, tuned critical charges, PBA omission, and BL-clustering adjustment before using the simulation comparisons.

## Final disposition

- **Recommendation:** `CORE` for measurement/classification uncertainty and direct-event topology.
- **Confidence:** high for procedure/definitions and static-grouping trade-off; medium for experimental parent-event provenance; medium-low for simulation mechanism attribution beyond validated conditions.
- **Evidence gaps:** exact detection/reset/grouping semantics, field nonstationarity, explicit `W`, codeword effects, full uncertainty model, and propagation to capability-window reliability.
