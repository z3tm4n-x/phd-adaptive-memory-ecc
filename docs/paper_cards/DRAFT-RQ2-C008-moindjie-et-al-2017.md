# Draft Paper Card — RQ2-C008

**PAPER-ID:** `TBD until Orchestrator acceptance`  
**Candidate identity:** `RQ2-C008`  
**Related RQ:** `RQ-002`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommendation:** `CORE`  
**Exact full-text version:** Elsevier “Article in Press,” received 28 May 2017, accepted 8 July 2017, 5 pages  
**Full text used:** `moindjie2017.pdf`; SHA-256 `48efb6837b8c323f474247d33da6243fa9c4200b8d49a570e91f9e5cad887b3f0`

## Bibliographic identity

S. Moindjie, J.-L. Autran, D. Munteanu, G. Gasiot, and P. Roche, “Multi-Poisson process analysis of real-time soft-error rate measurements in bulk 65 nm and 40 nm SRAMs,” *Microelectronics Reliability*, 2017. DOI: `10.1016/j.microrel.2017.07.045`.

`[SOURCE]` The supplied complete text is explicitly an accepted “Article in Press” version and does not print final volume/page metadata. Those fields remain `UNKNOWN` here rather than reconstructed from secondary metadata.

## Common extraction summary

| Field | Extraction |
|---|---|
| Primitive arrival object | `[SOURCE]` One real-time detected “single event,” classified by multiplicity `i`, where multiplicity is the number of simultaneously upset cells attributed to one particle interaction; Sec. II, pp. 2–3. |
| Count/arrival process | `[SOURCE]` `M` independent homogeneous Poisson counting processes `N_i(t)`—one for each event multiplicity—whose superposition is Poisson with rate `λ=Σ_iλ_i`; Fig. 1 and Sec. II, p. 2. |
| Stationarity/intensity | `[SOURCE]` Fixed `λ_i` over each long aggregate experiment; estimator `λ_i=N_i/Σ`, where exposure `Σ` is Mbit·h (Eqs. (3)–(4)). No time-varying intensity. |
| Independence | `[SOURCE]` Temporal/spatial independence is assumed in deriving Poisson counts (Sec. II). `[UNKNOWN]` No independence test is reported. |
| Multiplicity/topology | `[SOURCE]` Full multiplicity count distribution is retained up to observed categories (65 nm: 1–7; 40 nm: 1–22, with reliable mechanism extraction only to 12). Spatial shape/coordinates are not retained. |
| Parent-event provenance | `[SOURCE]` The RT-SER data count online single events and their simultaneous multiplicity. `[UNKNOWN]` The supplied paper does not document the detector's detailed association-window algorithm. |
| Mapping `W` | `[UNKNOWN]` No codeword mapping or interleaving representation. |
| Accumulation/repair | `[SOURCE]` Errors are eliminated by rewriting new data after detection; a failing device is replaced immediately. The process measures event occurrence, not accumulated memory state (Sec. II, p. 2). |
| Direct/accumulation | `[SOURCE]` Multiplicity is defined as simultaneous cells from one particle; sequential accumulation is not modeled. |
| Mechanism partition | `[SOURCE]` Neutron and alpha rates are linearly separated for each multiplicity using altitude acceleration factor and underground/sea-level measurements (Eqs. (1), (5); Tables 2–5). |
| Uncertainty/validation | `[SOURCE]` Marseille event counts predicted from altitude/underground extraction are compared with measured counts; authors report agreement within about 10% of detected-count uncertainty (Table 4). No confidence intervals for all `λ_i` or formal Poisson GOF are given. |
| Relation to `E_cap`/`F_A` | `[INFERENCE]` Supplies candidate mechanism- and multiplicity-specific event intensities, but no mapping, accumulation, initial state, correction, or windowed capability event. |

## 1. Research problem

- `[SOURCE]` A single total SER obscures the different multiplicity profiles and relative neutron/alpha contributions needed to describe MCU occurrence in SRAMs (Introduction, pp. 1–2).

## 2. Objective

- `[SOURCE]` Analyze long real-time measurements as multiplicity-specific Poisson processes, separate atmospheric-neutron and alpha-emitter contributions, and use two environments to predict a third (Abstract; Secs. II–V).

## 3. System/model studied

- `[SOURCE]` Bulk single-port SRAM arrays: 3226 Mbit of 65-nm devices measured from 2008–2017 and 7168 Mbit of 40-nm devices measured from 2011–2017 (Sec. III, Table 1).
- `[SOURCE]` Test sites: ASTEP altitude platform (2255 m), Modane underground laboratory, and Marseille sea level; nominal voltages 1.2 V (65 nm) and 1.1 V (40 nm), checkerboard pattern (Sec. III).

## 4. Method

- `[SOURCE]` Count online single events per multiplicity and divide by integrated active-memory exposure `Σ=∫MEM(t)dt` to estimate `λ_i` in h⁻¹·Mbit⁻¹ (Eqs. (3)–(4)).
- `[SOURCE]` Model each multiplicity stream as an independent HPP and merge them by superposition (Fig. 1, Sec. II).
- `[SOURCE]` Solve the linear altitude/underground equations for neutron and alpha `λ_i`, then predict Marseille rates/counts using its acceleration factor (Eqs. (1), (5); Tables 2–4).

## 5. Assumptions

- `[SOURCE]` Soft errors are random in time and space, independent, and occur at fixed event rate `λ` (Sec. II, p. 2).
- `[SOURCE]` Multiplicity streams are independent Poisson processes (Fig. 1 and adjacent text).
- `[SOURCE]` Alpha SER is fixed by material contamination; neutron SER scales with environment-specific acceleration factor `AF` (Eq. (1), Introduction).
- `[SOURCE]` Event multiplicity represents simultaneous cells upset by a single particle interaction (Sec. II).
- `[INFERENCE]` Long-duration aggregation assumes rate stability within each experiment and hides shorter nonstationarity.

## 6. Input parameters

- `[SOURCE]` Detected counts `N_i`, integrated exposure `Σ` in Mbit·h, multiplicity `i`, acceleration factor `AF`, and site identity (Eqs. (1), (3)–(5); Tables 1–5).

## 7. Output parameters

- `[SOURCE]` Multiplicity-specific event rate `λ_i` in h⁻¹·Mbit⁻¹; separate neutron `n-λ_i` and alpha `α-λ_i`; predicted counts by multiplicity (Tables 2–5).
- `[SOURCE]` Event SER counts each physical/detected event once; total bit-flip SER weights multiplicity stream `i` by `i`. Both are rates normalized to memory exposure (Introduction; Sec. II).

## 8. Baselines/comparators

- `[SOURCE]` Measured Marseille counts/rates versus rates predicted from ASTEP plus Modane (Table 4).
- `[SOURCE]` 65-nm versus 40-nm multiplicity-specific neutron/alpha profiles (Figs. 4–5; Tables 3 and 5).

## 9. Main equations/models

- `[SOURCE]` Eq. (1): site total rate is `AF × n-SER_NYC + α-SER`.
- `[SOURCE]` Eq. (2): HPP count PMF `P(N(t)=n)=e^{-λt}(λt)^n/n!`.
- `[SOURCE]` Eqs. (3)–(4): maximum-likelihood exposure-normalized rate `λ=N/Σ`, `Σ=∫MEM(t)dt`.
- `[SOURCE]` Multiplicity construction: independent `N_i(t)` with rates `λ_i`; merged process `N(t)=Σ_iN_i(t)` has rate `Σ_iλ_i` (Fig. 1, p. 2).
- `[SOURCE]` Eq. (5): multiplicity-specific site equation `λ_i=AF×n-λ_i+α-λ_i`.

## 10. Main results

- `[SOURCE]` For the 65-nm data, alpha contributions dominate SBU and MCU(2)–MCU(3), while neutron rates become comparable/dominant at higher multiplicities (Fig. 4; Table 3).
- `[SOURCE]` Predicted Marseille 65-nm counts total 57 versus 52 measured; multiplicity-level values are reported in Table 4 and described as within about 10% of detected-count uncertainty.
- `[SOURCE]` The 40-nm data contain higher observed multiplicities (up to 22), but insufficient statistics prevent reliable neutron/alpha extraction above multiplicity 12 (Fig. 5; Table 5).
- `[SOURCE]` The authors report different integration trends: alpha event rates generally decrease with scaling, while neutron sensitivity increases for SBU and MCU categories in the 40-nm data (Sec. IV.2).

## 11. Author-stated limitations

- `[SOURCE]` Large-multiplicity statistics are insufficient for reliable mechanism extraction, especially above MCU(12) in 40 nm (Fig. 5; Table 5).
- `[SOURCE]` Active memory under test varies because devices may be automatically disconnected; exposure normalization accounts for this (Sec. II, Eqs. (3)–(4)).

## 12. Methodological limitations inferred

- `[INFERENCE]` No formal goodness-of-fit/model comparison establishes HPP over the full 11,000–57,000 h windows; visual cumulative traces and one cross-site prediction are weaker evidence.
- `[INFERENCE]` Separate Poisson streams and linear neutron/alpha decomposition do not retain event coordinates, cluster shapes, parent-particle substructure, or logical codeword effects.
- `[INFERENCE]` Constant rates cannot capture solar/atmospheric/environmental nonstationarity or temporal bursts.
- `[INFERENCE]` Detection/classification uncertainty may bias rare multiplicity categories, but no explicit observation model is supplied.

## 13. Threats to validity

- `[INFERENCE]` Construct validity: “single event” relies on the RT-SER detector/association procedure, not fully specified here.
- `[INFERENCE]` Statistical validity: zero/small counts yield high relative uncertainty; rate CIs and GOF statistics are absent.
- `[INFERENCE]` External validity: results apply to the tested bulk 65-/40-nm products, voltages, patterns, and terrestrial sites.
- `[INFERENCE]` Mechanism validity: neutron and alpha separation relies on the acceleration-factor linear model and assumed environment invariance of alpha contamination.

## 14. What the paper actually demonstrates

- `[SOURCE]` The measured data can be parameterized as multiplicity-specific independent Poisson streams and linearly decomposed into neutron/alpha rates, with one successful 65-nm cross-site count prediction (Secs. II–V).
- `[SOURCE]` Event SER and bit-flip SER are distinct aggregations over the same multiplicity streams.
- `[INFERENCE]` It provides empirically estimated marginal mark rates `λ_i`, not a complete topographic mark distribution.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` The paper does not prove temporal independence, HPP validity at shorter windows, or time invariance outside the aggregate tests.
- `[INFERENCE]` It does not provide codeword mapping, scrubbing, initial memory state, or accumulated capability crossing.
- `[INFERENCE]` It does not distinguish direct one-neutron multi-secondary structure beyond detected multiplicity, nor model pseudo MCUs from sequential events.
- `[INFERENCE]` It does not supply reliable mechanism-specific rates for the sparse high-multiplicity tail.

## 16. Relevance to the dissertation

- `[INFERENCE]` Identifies a tractable candidate first quantitative prototype input: per-domain/per-mechanism multiplicity-specific intensities `λ_i`, with event rate kept distinct from bit-flip rate.
- `[INFERENCE]` Shows that exposure must be normalized by active tested memory and that rare-tail categories require explicit uncertainty/coverage status.
- `[INFERENCE]` Must be augmented with topology/post-`W` marks, state accumulation, repair, and `μ_t0` before use with `E_cap`/`F_A`.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` “Multi-Poisson” denotes independent homogeneous Poisson counting streams indexed by event multiplicity, with Poisson superposition (Fig. 1; Sec. II).
2. `[SOURCE-CANDIDATE]` Event SER counts physical/detected events, whereas total bit-flip SER weights events by multiplicity (Introduction; Sec. II).
3. `[SOURCE-CANDIDATE]` Multiplicity-specific neutron and alpha rates are separated using altitude factors and multi-site measurements (Eqs. (1), (5)).
4. `[SOURCE-CANDIDATE]` High-multiplicity 40-nm categories lack sufficient counts for reliable neutron/alpha extraction above multiplicity 12 (Fig. 5; Table 5).
5. `[INFERENCE-CANDIDATE]` Marginal `λ_i` values are insufficient to determine ECC-word capability events when spatial mapping matters.

## 18. Tensions/conflicts

- `[INFERENCE]` C008's HPP/multiplicity representation is computationally compact but discards the spatial dependencies highlighted by topology-sensitive models.
- `[INFERENCE]` Continuous rewrite/replacement measurement semantics prevent accumulation, whereas adaptive scrubbing specifically requires between-repair state evolution.

## 19. Open questions/evidence gaps

1. `[UNKNOWN]` Does HPP fit hold on operational scrub-window scales rather than only multi-year aggregate exposure?
2. `[UNKNOWN]` What joint spatial mark accompanies each `λ_i` after mapping `W`?
3. `[UNKNOWN]` What detector association window and classification errors affect multiplicity counts?
4. `[UNKNOWN]` How should uncertainty in sparse `λ_i` estimates propagate into `F_A`?
5. `[UNKNOWN]` How do event rates vary with voltage, data pattern, environment, and time for the target domain?

## Identifiable parameters for a first prototype

- `[SOURCE]` Directly estimable from this dataset: total event rate; total bit-flip rate; `λ_i` by observed multiplicity; neutron/alpha `λ_i` where counts are sufficient; active-memory exposure.
- `[INFERENCE]` Not identifiable from this source alone: spatial/topographic mark, codeword multiplicity after `W`, accumulation state, initial distribution, scrub-reset process, decoder outcome, and short-window nonstationarity.

## HANDOFF TO ZOTERO — metadata reconciliation only

- **Target collection:** `DISSERTATION / RQ / RQ-002`.
- **Identifier:** DOI `10.1016/j.microrel.2017.07.045`.
- **Required action:** retain the analyzed accepted Article-in-Press PDF as a versioned attachment; reconcile final journal volume, issue, and pagination against publisher metadata; record that the Paper Card's page references use the five-page accepted version.
- **Duplicate policy:** match by DOI first; do not create a second bibliographic item if an existing DOI item is present; do not silently replace the analyzed attachment.
- **Expected result:** one reconciled item with the exact analyzed attachment and explicit version note.
- **Status:** handoff prepared; no Zotero operation claimed.

## Equations and assumptions requiring reproduction

- Reproduce Eqs. (2)–(4) with integrated active-memory exposure `Σ`; do not substitute nominal installed capacity for `MEM(t)`.
- Reproduce the independent `N_i(t)` HPP streams and their superposition exactly as Fig. 1 defines “multi-Poisson.”
- Reproduce Eq. (5) separately for every multiplicity and use the stated acceleration factors/sites for neutron/alpha decomposition.
- Preserve event-count and bit-flip-rate outputs as separate quantities; flag multiplicities with insufficient counts rather than extrapolating rates.

## Final disposition

- **Recommendation:** `CORE` for arrival-process assumptions and empirical multiplicity/mechanism rates.
- **Confidence:** high for definitions/equations; medium for 65-nm rate decomposition; low for sparse high-multiplicity tail and universal HPP validity.
- **Evidence gaps:** formal GOF, independence tests, association/classification model, spatial marks, mapping, state/repair semantics, and uncertainty propagation.
