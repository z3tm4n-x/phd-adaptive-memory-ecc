# RE-CY62167-DISTANT-MCU-OBSERVABILITY-01

## Scientific semantic

The previous kill test established only the conservative inequality `p_D(E,W) <= P(K>=2|E)`: its result B meant that this coarse upper bound could not dismiss a direct term. It did **not** establish that the physical direct floor is large. This task asks how much geometry/observability can narrow that bound.

## 1. What Zenodo actually observes

Each file record is already a **registered post-processed cluster**, not a raw parent-particle record. The controlled parser preserves cluster id, bounding box, `xadd/yadd`, optional second-resolution timestamp and cell rows. `field0_raw` remains undocumented. The cited clustering lineage uses a ±3-cell window in both supplied XY axes, a temporal criterion, recursive growth, and later merge passes; the exact version that generated Zenodo is not fully published. Raw/pre-clustering bit records are absent.

Raw reproduction: every registered K=2 proton cluster has `d_inf<=3`. K>=3 clusters can span farther through recursive/transitive growth; some registered clusters also reflect merge semantics not reproducible from the public files alone.

## 2. Coordinate provenance

**Classification: TRANSFORMED physical-map coordinate representation; exact transformation proprietary.** Bosser describes manufacturer-provided scrambling/interleaving knowledge as necessary to convert logical addresses to physical bitmaps, and LELAPE states that the relevant Infineon campaigns used proprietary information to map logical bitflip addresses to XY bitcell locations. This supports treating the supplied XY values as a manufacturer-informed physical-map grid, but it does not publish the transform or establish which axis is a physical row versus column. Therefore this report uses only `axis_x/axis_y`. `xadd/yadd` are not given new semantics.

## 3. Mapping scenarios

|scenario|status|what is observable|
|---|---|---|
|W0|C|local registered K>=2 component observable; same-parent probability not point-identified|
|W16-reg|C|observed within-cluster exact16 candidates=1; conservative parent-level set remains broad because split clusters cannot be linked to one particle|
|W-unknown|D|no nontrivial device-specific p_D identified|

For **W16-reg**, the regular ID=16 relation is only a declared comparator consistent with interleaving-distance literature. It is not the proprietary CY62167 map. An isolated exact-16 same-axis pair cannot occur as one registered K=2 cluster under the reproduced `d_inf<=3` observation rule. It can enter one record only through a K>=3 bridge/merge, otherwise it appears as separate registered clusters. Thus the very topology relevant to W16 is censored by the clustering interface.

## 4. Cross-cluster temporal diagnostic

Timestamp-bearing files allow same-bin and adjacent-bin diagnostics. The largest raw observed/independent-uniform ratio for exact-16 cross-cluster cell pairs was `23.68`. This is **not** interpreted as a same-parent excess: timestamps are detection/readout-scale labels on already formed clusters, the exact merge chronology is unavailable, and the independent baseline assumes spatial exchangeability. Hence **cross-cluster distant excess = NOT IDENTIFIABLE**. Files without timestamps receive no reconstructed parent linkage.

## 5. Spectrum relevance

The previous GOES/RADAR and both sigma(E) responses are reused unchanged. `spectrum_observability_weight.csv` separates `<0.9 MeV` (no geometry data), `0.9-5 MeV` (timestamped measured envelope: partial distant diagnostic), `>5-186 MeV` (registered geometry exists at measured energies but cross-cluster distant inference is unobservable over the continuous envelope), and `>186 MeV` (no measured geometry; includes the high-energy closure terms). Fractions are reported separately for reconstructed parent-event, multi-upper, and bit-flip budgets.

## 6. Can p_D(E,W) be computed next?

- **W0:** only as an identified/registered-cluster set; parent truth is not point identified.
- **W16-reg:** only as a broad identified set / sensitivity model. Within-cluster bridge candidates are observable, but isolated distant same-parent pairs are censored.
- **W-unknown:** no. Exact W is an independent blocker in addition to event observability.

**Parity-cell status: UNKNOWN.** No 38/32 or pair-count multiplier is applied because parity placement is not exchangeable with data-cell placement.

**Zebrev 1/2 comparator: NOT TESTABLE** for the current CY62167 registered K=2 population under W16-reg. The K=2 observation process contains no pair beyond the ±3 window, while the declared ID16 same-word relation is distant; cross-cluster parent identity is unavailable.

**PHYSICAL-SPAN BOUND = NOT ESTABLISHED.** Literature on 65-nm bulk SRAM topology is useful context but does not provide a device-specific hard maximum span for this CY62167 dataset.

## Overall answer

Direct-term inference is limited by **both factors**: event observability/censoring and W. The current data are valuable for within-cluster geometry, but they do not identify the distant same-parent component needed to validate a regular-ID16 collision probability. The next quantitative p_D task should therefore be formulated as an identified-set/sensitivity study unless pre-clustering logs or manufacturer mapping information become available.
