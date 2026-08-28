# RQ-002 — Initial cross-paper evidence synthesis

**Status:** `INITIAL EVIDENCE SYNTHESIS — ACCEPTED INPUTS / NOT A FINAL ANSWER`<br>
**Accepted:** 2026-08-28<br>
**Related RQ:** `RQ-002`<br>
**Accepted inputs:** [PAPER-004](../paper_cards/PAPER-004-clemente-rezaei-franco-2022.md), [PAPER-005](../paper_cards/PAPER-005-zebrev-2017-arxiv-v2.md), [PAPER-006](../paper_cards/PAPER-006-moindjie-et-al-2017.md), [PAPER-007](../paper_cards/PAPER-007-ogden-mascagni-2017.md), [PAPER-008](../paper_cards/PAPER-008-gomi-et-al-2026.md)<br>
**Companion version:** `RQ2-C006`, DOI `10.1109/RADECS.2017.8696217`, is controlled inside `PAPER-005` and does not receive a separate Paper Card<br>
**Model selection:** `NOT YET DECIDED`

Paper Card acceptance means that the analytical cards are complete, traceable and suitable for cross-paper reasoning. It does not adopt any paper's process, mapping, ECC, scrub, observation or validation assumptions as project assumptions. Statements explicitly marked as synthesis or inference remain candidate propositions until the required audit/decision gate.

## 1. Formal Paper Card disposition and task metadata

| Permanent ID | Candidate | Disposition | Decision-enabling contribution | Preserved caveat |
|---|---|---|---|---|
| `PAPER-004` | RQ2-C001 — Clemente, Rezaei, Franco, 2022 | `ACCEPTED — CORE` | Conditional independent-accumulation/occupancy model, repeat-hit cancellation and ideal scrub partition | Count horizon only; direct same-particle mechanism excluded; no explicit `W`, general initial state or first passage |
| `PAPER-005` | RQ2-C005 — Zebrev et al., arXiv v2, with RQ2-C006 comparison | `ACCEPTED — CORE` | Multiplicity-resolved physical-event partition, ECC vulnerability recombination and exact limits of the simple SEC-DED scrubbing example | No explicit `W`; Eq. (15) disjointness not proved; `β≪1`; companion C006 is a separate publication version but not a separate analytical card |
| `PAPER-006` | RQ2-C008 — Moindjie et al., 2017 | `ACCEPTED — CORE` | Empirical multiplicity-indexed event-rate representation and event-rate/bit-rate distinction | HPP/independence assumed; no topology, mapping, state or formal GOF |
| `PAPER-007` | RQ2-C011 — Ogden and Mascagni, 2017 | `ACCEPTED — CORE` | Parent-event topology, deterministic interleaving and event-driven accumulation/scrubbing in one simulator | One technology/organization; simplified ECC; synchronous scrub and stationary inputs |
| `PAPER-008` | RQ2-C020 — Gomi et al., 2026 | `ACCEPTED — CORE` | Quasi-event-wise topology, observation/classification trade-off and particle-provenance evidence | No ECC propagation, exact experimental particle identity or operational reset model |

No card is rejected. No `CLM`, `EVD`, `HYP`, `DEC`, `EXP` or `RES` is created by Paper Card acceptance.

| Field | Value |
|---|---|
| Task ID | `RQ-002-PA-BATCH-01` |
| Related RQ | `RQ-002` |
| Role | Paper Analyst |
| Canonical base used | `39f66ee359ba17b960d9382033b9a9f7c325ce93` |
| Provenance-correction task/base | `RQ-002-PA-BATCH-01-CORRECTION-01`; `ed2a938aa5cc733e1a311116d8bf7b79e7c01e4e` |
| Full-text gate | Passed for C005, C006, C001, C011, C008, and C020 |
| Scope | Five decision-enabling work units; no final model selection |
| Permanent identifiers | `PAPER-004…PAPER-008`; RQ2-C006 remains a controlled companion version inside `PAPER-005` |

`[SOURCE]` RQ2-C005 was verified against the versioned arXiv:1704.07271v2 record and official v2 PDF. The analyzed attachment is byte-different from the official PDF but has byte-identical raw extracted text and the same five-page/eight-figure/equation inventory. RQ2-C006 was read as a separate IEEE RADECS publication identity and compared field by field in `PAPER-005`. Because RQ2-C006 adds no independent analytical content beyond the common Eqs. (1)–(14), no separate full card was created.

## 2. Full-text identity and integrity

| Candidate | Exact text analyzed | File SHA-256 | Gate result |
|---|---|---|---|
| RQ2-C005 | G. I. Zebrev, A. M. Galimov, L. V. Mrozovskaya, M. S. Gorbunov, K. A. Petrov; arXiv:1704.07271v2, revised 15 Oct. 2017, 5 pp., 8 figs. | Analyzed attachment: `b02b5fb32d45f63b078cf11488283fe6fff5a012077edb3d37f14acd3157ba2e`; official v2 PDF: `03fc5bc397c68bfb613174f2fd7b5123a27cca0831530000ba3870206f7782ac` | PASS — byte-different PDFs; raw extracted text identical |
| RQ2-C006 | Same five-author order independently verified; “Multiple Cell Event Partitioning for Simulation of Soft Error Rates in Space Systems with Embedded Error Correcting Codes”; RADECS 2017, DOI `10.1109/RADECS.2017.8696217`, 4 pp. | `2cd3aa55ca715b8e3687fe411ad89b6ea01f6278c98423baa367fd38fc5bcc42` | PASS — separate identity; comparison only |
| RQ2-C001 | Juan A. Clemente, Mohammadreza Rezaei, Francisco J. Franco; IEEE TNS 69(2), 169–180, 2022 | `9b5caea4b2f97787389a1b08dc699ade7ea61a8116bf1ba7a196980dd11bfbf0` | PASS |
| RQ2-C011 | IEEE TR 66(4), 966–979, 2017 | `b5b8cb55ee16fe4d50c199b21eb9facfef9a9f70d9a6c68c2d503acee9ecec71` | PASS |
| RQ2-C008 | Elsevier Article in Press, accepted 8 July 2017, 5 pp. | `48efb6837b8c323f474247d33da6243fa9c4200b8d49a570e91f9e5cad887b3f` | PASS |
| RQ2-C020 | “Quasi Event-Wise Measurement and Simulation of Neutron-Induced Multiple-Cell Upsets in 22-nm and 55-nm SRAMs”; IEEE TNS 73(8), 2935–2947, 2026 | `9facf0f6086bc82557c7d18dbfa36ce7edcc2375e8cb63a49f6ec2576d586e2e` | PASS |

`[SOURCE]` Primary-record/full-text reconciliation corrected bibliographic provenance only: C001's second author is Mohammadreza Rezaei; C005 and C006 independently carry the five-author order shown above; and C020's exact bibliographic title uses “22-nm and 55-nm SRAMs,” while its analyzed PDF displays the abbreviated wording “22- and 55-nm SRAMs.” No scientific extraction, model-selection alternative, or comparison outcome was strengthened or changed.

## 3. Common extraction matrix — process and event representation

| Field | `PAPER-005` — C005 Zebrev | `PAPER-004` — C001 Clemente | `PAPER-007` — C011 Ogden | `PAPER-006` — C008 Moindjie | `PAPER-008` — C020 Gomi |
|---|---|---|---|---|---|
| Primitive arrival object | `[SOURCE]` Physical ion strike, marked by upset multiplicity `n`. | `[SOURCE]` Independent uniformly located cell hit/bit flip `(x,y)`. | `[SOURCE]` SEE with time, type, severity, location, and optional topology. | `[SOURCE]` RT-detected single-particle event, classified by simultaneous multiplicity. | `[SOURCE]` Quasi-event-wise macro upset record; physical direct event is neutron-induced SEU. |
| Count/arrival process | `[SOURCE]` Flux/cross-section rate integral; Poisson only for conditional multiplicity, not time. | `[SOURCE]` Conditional on total hits `m`; Poisson counts false MBUs, not arrivals. | `[SOURCE]` Constant-`λ` Bernoulli time steps plus compound-Poisson upset-count model. | `[SOURCE]` Independent HPP `N_i(t)` by multiplicity and Poisson superposition. | `[SOURCE]` Poisson arrivals only for within-scan false-grouping bound; no fitted mission process. |
| Stationarity | `[UNKNOWN]` No temporal process. | `[UNKNOWN]` No time axis. | `[SOURCE]` Stationary across one run. | `[SOURCE]` Stationary aggregate `λ_i` within each experiment. | `[SOURCE]` Constant beam in bound; operational stationarity untested. |
| Intensity type/units | `[SOURCE]` `R_n` per bit/cell-time from flux integral. | `[SOURCE]` No intensity; hit count. | `[SOURCE]` Mean arrival chance per simulation time unit. | `[SOURCE]` `λ_i` in h⁻¹·Mbit⁻¹. | `[SOURCE]` Beam flux `/cm²/s`, cross section `cm²/Mbit`; expected events per macro scan. |
| Event multiplicity | `[SOURCE]` Physical `n`-fold upset class. | `[SOURCE]` False word multiplicity after sequential hits. | `[SOURCE]` Empirical type/severity, including MBU cluster size. | `[SOURCE]` Simultaneous cells per detected event, `i=1…M`. | `[SOURCE]` Event-wise number of flipped cells plus MCU pattern groups. |
| Spatial topology | `[SOURCE]` Not retained beyond `n`. | `[SOURCE]` Only address/bit occupancy; physical topology excluded. | `[SOURCE]` 3×3 pattern for up to 4 flips; row-depth fallback for `≥5`. | `[SOURCE]` Not retained. | `[SOURCE]` Full observed row/column pattern, Chebyshev distances, rectangle diagonal. |
| Spatial correlation | `[SOURCE]` Implicit in physical multiplicity but not coordinate-resolved. | `[SOURCE]` Independent uniform hits. | `[SOURCE]` Explicit within-parent shape; mapping interaction simulated. | `[SOURCE]` Only through multiplicity marginal. | `[SOURCE]` Explicit within observed event; row/well-tap dependence reported. |
| Temporal clustering | `[UNKNOWN]` Not represented. | `[SOURCE]` Sequential hits accumulate; timing absent. | `[SOURCE]` iid Bernoulli arrivals; no burst component. | `[SOURCE]` HPP excludes clustering beyond chance. | `[SOURCE]` Multiple arrivals inside one scan are treated as rare false association; no burst model. |
| Parent-event provenance | `[SOURCE]` Preserved as `R_n` same-ion class. | `[SOURCE]` Independent-hit accumulation only; direct parent excluded. | `[SOURCE]` Preserved in simulated SEE mark; spatially reduced in S2P. | `[SOURCE]` Preserved as detected single event, subject to unspecified detector association. | `[SOURCE]` Exact in PHITS; probabilistic proxy in detector-less experiment. |
| Direct same-particle mechanism | `[SOURCE]` Yes, multiplicity-resolved. | `[SOURCE]` Excluded by interleaving assumption. | `[SOURCE]` Yes, one SEE may flip multiple cells. | `[SOURCE]` Yes, simultaneous single-particle event. | `[SOURCE]` Yes, true MCU/Distant MCU. |
| Sequential accumulation | `[SOURCE]` Low-`β` term in Eq. (15), reduced state. | `[SOURCE]` Main model. | `[SOURCE]` Explicit word-state accumulation between scrubs. | `[SOURCE]` Removed by rewrite/replacement; not modeled. | `[SOURCE]` False pseudo-MCU bounded; operational accumulation not modeled. |
| Ambiguous/false classification | `[INFERENCE]` Additive overlap possible in Eq. (15). | `[SOURCE]` Experimental final MBUs lack per-event provenance. | `[UNKNOWN]` Input empirical category error not modeled. | `[UNKNOWN]` Detector association uncertainty not modeled. | `[SOURCE]` Explicit pseudo-MCU and static grouping trade-off. |

## 4. Common extraction matrix — mapping, state, and repair

| Field | `PAPER-005` | `PAPER-004` | `PAPER-007` | `PAPER-006` | `PAPER-008` |
|---|---|---|---|---|---|
| Physical-cell-to-codeword mapping | `[SOURCE]` No `W`; assumes half of 2-fold MCUs enter one word. | `[SOURCE]` Ideal statistical interleaving; `(address,bit)` only. | `[SOURCE]` Deterministic regular `ID` architecture. | `[UNKNOWN]` None. | `[SOURCE]` Physical macro coordinates, but no ECC mapping. |
| Representation after `W` | `[SOURCE]` Scalar `R_w(n≥1/2)` only. | `[SOURCE]` Final word occupancy/multiplicity. | `[SOURCE]` Explicit affected physical cells/logical words in simulator. | `[UNKNOWN]` None. | `[INFERENCE]` Can be derived externally from addresses if exact `W` is provided. |
| Information retained | Multiplicity rates and direct/sequential labels. | Word occupancy and hit/cancellation count. | Parent/time/topology plus mapped state for regular `ID`. | Mechanism- and multiplicity-specific event rates. | Event-wise physical pattern and simulated particle history. |
| Information lost | Coordinates, arbitrary mapping, word ages. | Physical parent/topology, time, direct mechanism. | Raw physics; `≥5` topology; decoder details. | Coordinates, topology, word state, mapping. | Experimental incident-particle identity, exact within-scan order, ECC state. |
| Accumulation state variables | `[SOURCE]` `R_1t_s`, `β`; no explicit occupancy. | `[SOURCE]` Total hits/observed flips and cell/word occupancy. | `[SOURCE]` Per-word bit-error state plus failed flag. | `[SOURCE]` None; event counters only. | `[SOURCE]` None for reliability; transient detected pattern only. |
| Initial state/distribution | `[INFERENCE]` Clean cycle implied; no `μ_t0`. | `[SOURCE]` Clean all-zero start. | `[INFERENCE]` Clean start implied; no distribution. | `[SOURCE]` Measurement rewrite prevents retained state; no reliability initial state. | `[SOURCE]` All-zero start; no distribution. |
| Correction/writeback/reset | `[SOURCE]` Simple SEC-DED correction abstracted by `t_s/β`; no scan. | `[SOURCE]` Equally spaced instantaneous global clean resets. | `[SOURCE]` Global instantaneous scrub of still-correctable words; failed words persist. | `[SOURCE]` Rewrite after detection; failed device replaced. | `[UNKNOWN]` Detection/FIFO stated; exact cell writeback/reset not stated. |
| Sequential word ages | `[SOURCE]` None. | `[SOURCE]` None. | `[SOURCE]` None; common STI. | Not applicable. | `[UNKNOWN]` Scan is sequential, but word exposure/reset age is not modeled. |
| Mechanism partition level | `[SOURCE]` Physical multiplicity first; approximate word conversion later. | `[SOURCE]` Logical accumulation only; direct mechanism removed. | `[SOURCE]` Event mark before deterministic mapping; state after mapping. | `[SOURCE]` Detected event multiplicity and neutron/alpha rate. | `[SOURCE]` Observation level in experiment; particle/event level in simulation. |
| Mechanism-specific rates | `[SOURCE]` `R_n` direct; sequential term derived from `R_1,t_s`. | `[SOURCE]` Accumulation probability conditional on hits; no direct rate. | `[SOURCE]` Common SEE rate/type distribution; direct/accumulated failure contributions not output separately. | `[SOURCE]` `n-λ_i`, `α-λ_i` by multiplicity where identifiable. | `[SOURCE]` Measured MCU/Distant ratios; pseudo is bounded, not separately measured. |
| Recombination rule | `[SOURCE]` Eq. (15) additive; Eqs. (13)–(14) vulnerability-weighted sums. | `[SOURCE]` No direct recombination. | `[SOURCE]` Event-driven state evolution naturally combines all events. | `[SOURCE]` Poisson superposition across multiplicities/mechanisms. | `[SOURCE]` No reliability recombination; compares direct observations with false-group bound. |
| Disjointness/approximation | `[INFERENCE]` Eq. (15) not proven disjoint; low-order approximation. | `[SOURCE]` Scope exclusion makes mechanisms separate, not empirically partitioned. | `[INFERENCE]` Parent events disjoint in simulation, but output does not decompose mechanisms. | `[SOURCE]` Independent-process superposition assumed. | `[SOURCE]` Pseudo/direct separation is probabilistic in experiment, exact in simulation. |

## 5. Common extraction matrix — evidence, validity, and contract fit

| Field | `PAPER-005` | `PAPER-004` | `PAPER-007` | `PAPER-006` | `PAPER-008` |
|---|---|---|---|---|---|
| Uncertainty treatment | `[SOURCE]` No full propagation. | `[SOURCE]` Monte Carlo 95% standard-error bars; sparse experiments. | `[SOURCE]` Kruskal–Wallis tests; no input-parameter uncertainty propagation. | `[SOURCE]` Count uncertainty discussed; sparse-tail insufficiency; no full CIs/GOF. | `[SOURCE]` Standard errors; no full classification/model uncertainty propagation. |
| Empirical validation | `[SOURCE]` Ground/on-orbit multiplicity comparisons; scrub example not validated. | `[SOURCE]` Monte Carlo plus sparse irradiation-count comparisons. | `[SOURCE]` S2P vs related WRCSER; T2P vs S2P controlled simulation. | `[SOURCE]` Long real-time field tests; one cross-site prediction. | `[SOURCE]` Beam experiment plus PHITS comparisons. |
| Domain of validity | Heavy-ion/space-rate examples; low-`β` SEC-DED illustration. | Uniform independent hits in ideally interleaved memory; count horizon. | Simulated 45-nm regular-ID SRAM under fixed parameters. | Tested bulk 65-/40-nm SRAMs/sites/voltages; aggregate HPP. | Tested bulk 22-/55-nm fast-scan SRAMs/beam/voltages; PHITS assumptions. |
| Computational tractability | `[SOURCE]` Closed-form rate sums; very low cost. | `[SOURCE]` Closed forms over multiplicity/word width; MC validation only. | `[SOURCE]` Event-driven MATLAB Monte Carlo; qualitative efficiency claim only. | `[SOURCE]` Closed-form MLE and linear decomposition. | `[SOURCE]` Measurement processing tractable; PHITS with `10^10` primaries/configuration is computationally heavy. |
| Relation to `E_cap` | `[INFERENCE]` Vulnerability/system rate is related but not identical; no explicit `A/W` or first passage. | `[INFERENCE]` ECC-exceeding final pattern is related; toggling can break first-passage equivalence. | `[INFERENCE]` Explicit word-state crossing can approximate capability event for one clean-start simulated domain. | `[INFERENCE]` Supplies arrival marks/rates only. | `[INFERENCE]` Supplies direct physical marks/observation error only. |
| Relation to `F_A(t0,T;μ_t0)` | `[INFERENCE]` No general window/initial state; only rate/low-`β` cycle approximation. | `[INFERENCE]` Conditional kernel only; no `t0,T,μ_t0`. | `[INFERENCE]` Has clean-start `F(t)` for one homogeneous simulation, not arbitrary `μ_t0`/domain partitions. | `[INFERENCE]` No accumulation/repair/window capability calculation. | `[UNKNOWN]` Propagation stops at cross-section/event/topology. |
| Exact/bound/approximation/bias | Physical partition definition + modeled multiplicity; scrub is approximation with possible overlap. | Conditional occupancy approximation/Poisson occurrence layer; final-state bias relative to first passage. | Monte Carlo under explicit assumptions; topology input reduced/fallback; ECC abstraction bias. | HPP/independence assumed; sparse-tail estimation bias/uncertainty. | Pseudo bound under HPP; quasi-parent bias; static grouping bias; PHITS model-form bias. |
| Key limitation | No explicit `W`/disjoint recombination. | No time/direct mechanism/general initial state. | One technology/organization; simplified ECC/synchronous scrub. | No topology/state/mapping/formal GOF. | No ECC propagation/exact experimental particle provenance/full uncertainty model. |

## 6. Agreements supported by the batch

These are synthesis statements, not permanent claims.

1. `[INFERENCE]` **Physical-event count, bit-flip count, and codeword-capability event are distinct aggregation levels.** C005 and C008 explicitly separate event and bit-flip rates; C001/C011 show additional logical-state aggregation.
2. `[INFERENCE]` **Direct same-particle multi-cell effects and sequential accumulation require separate provenance.** C005 makes two terms, C001 isolates accumulation, C020 measures/bounds the classification boundary.
3. `[INFERENCE]` **Physical multiplicity alone is not always sufficient after ECC mapping.** C005 replaces mapping with a one-half assumption, while C011/C020 show that topology can materially alter logical consequences.
4. `[INFERENCE]` **Repair semantics determine the accumulation state.** C001 and C011 obtain different state trajectories from ideal global resets; C008 intentionally removes accumulation after detection.
5. `[INFERENCE]` **Observed bitmap clusters are not automatically physical events.** C001 irradiation comparisons lack provenance; C020 directly quantifies the static-grouping trade-off.
6. `[INFERENCE]` **A clean-start probability is not a general `F_A(t0,T;μ_t0)`.** None of the five sources supplies arbitrary mid-cycle initial distributions and heterogeneous sequential word ages.

## 7. Different definitions that must not be merged

| Term | Source-specific meaning |
|---|---|
| “Poisson” in C005 | Conditional physical upset multiplicity at fixed LET, Eqs. (8)–(11). |
| “Poisson” in C001 | Distribution of the number of false MBU occurrences with analytically supplied mean, Sec. III. |
| “Compound Poisson” in C011 | Time distribution of total upsets from clustered SEE events, Eq. (5). |
| “Multi-Poisson” in C008 | Independent HPP streams indexed by detected event multiplicity, Fig. 1. |
| “Poisson” in C020 | Probability of two or more independent arrivals in one macro/full-scan observation window, Eqs. (1)–(4). |
| MCU in C001 | Multi-bit error in one logical word; “false” if produced by independent events. |
| MCU in C008 | Simultaneous multiple upset cells from one detected particle event; no codeword notion. |
| Distant MCU in C020 | Direct MCU with at least one cell pair at Chebyshev distance `≥2`; a subset of physical MCU. |
| Failure in C011 | Word errors exceeding the number of ECC bits, propagated to model-derived memory `F(t)`. |
| Loss of integrity in C001 | At least one false word pattern outside the chosen code's correction pattern, conditional on hits. |

## 8. Incompatible assumptions

| Dimension | Incompatibility |
|---|---|
| Direct MCU | C001 excludes it by ideal interleaving; C005/C011/C008/C020 retain it. |
| Temporal arrivals | C008 assumes independent HPP; C011 uses constant Bernoulli/compound-Poisson; C001 has no time law; C005's Poisson is not temporal; C020 uses HPP only as a short-window bound. |
| Spatial dependence | C001/C008 discard physical topology; C011/C020 retain it at different resolutions; C005 retains only multiplicity. |
| Mapping | C011 fixes regular deterministic `ID`; C005 uses a scalar one-half allocation; C001 assumes ideal interleaving; C008/C020 do not apply ECC `W`. |
| Repair | C001 uses equal global clean resets; C011 resets only still-correctable words; C008 rewrites each detected event/replaces failed devices; C020 reset behavior is unstated. |
| Initial state | C001/C020 explicitly start clean; C011/C005 imply clean cycles; no source supports arbitrary `μ_t0`. |
| Failure semantics | C001 pattern capability, C011 errors-versus-ECC-bit count, C005 abstract vulnerability rate; C008/C020 stop before ECC failure. |

## 9. Incompatible aggregation levels

| Source | Native unit/aggregation |
|---|---|
| `PAPER-005` | Per-bit/per-cell physical event rate → multiplicity → abstract ECC/system rate. |
| `PAPER-004` | Cell hits → final logical-word pattern → at least one word in memory. |
| `PAPER-007` | Parent SEE → physical cells under regular `ID` → logical words/rows → modeled device `F(t)`. |
| `PAPER-006` | Detected physical event → multiplicity-specific rate per Mbit exposure; no word/array capability event. |
| `PAPER-008` | Detected/simulated physical event → cell pattern/cross section; no logical-word/domain reliability. |

`[INFERENCE]` Numerical values from these levels cannot be pooled until the target domain `A`, mapping `W`, mechanism partition, and event definition are aligned.

## 10. Incompatible horizons

| Source | Horizon |
|---|---|
| `PAPER-005` | Rate integral plus one ideal scrub interval `t_s` under `β≪1`. |
| `PAPER-004` | Total accumulated hit/upset count, optionally partitioned into equal scrub segments. |
| `PAPER-007` | Discrete simulation time `0…T` with global STI phase. |
| `PAPER-006` | Long calendar/exposure windows normalized in Mbit·h; rate assumed constant. |
| `PAPER-008` | Nanosecond full-scan observation window for false association; irradiation fluence/cross section for event statistics. |

`[INFERENCE]` None may be treated as the DEC-001 reporting window without an explicit conversion and state/repair semantics.

## 11. Work-unit decision results

| Work unit | Result | Decision-enabling contribution | Remaining blocker/gap |
|---|---|---|---|
| WU1 `PAPER-005` / C006 | COMPLETE | Physical multiplicity partition; exact interpretation/limits of Eqs. (15)–(19); verified version differences. | No explicit `W`; Eq. (15) non-overlap not proven; no validation outside `β≪1`. |
| WU2 `PAPER-004` | COMPLETE | Conditional independent-accumulation state/count model; repeat-hit cancellation; ideal scrub partition. | No temporal process, direct MCU, arbitrary `μ_t0`, first passage, or realistic word age. |
| WU3 `PAPER-007` | COMPLETE | Parent-mark/topography versus row-depth reduction under deterministic `ID`; explicit event-driven accumulation/scrub. | One simulated technology/organization; simplified ECC; no nonstationarity/uncertainty cost study. |
| WU4 `PAPER-006` | COMPLETE | Empirical multiplicity-indexed HPP construction and neutron/alpha rates; event-rate/bit-rate separation. | No formal GOF/independence test, topology, mapping, state, or tail precision. |
| WU5 `PAPER-008` | COMPLETE | Observation/classification model evidence; event-wise topology; pseudo-MCU bound; PHITS provenance. | No ECC propagation, exact experimental particle identity, operational reset semantics, or full uncertainty model. |

## 12. Unresolved model-selection gaps

1. `[UNKNOWN]` Minimal post-`W` joint mark: full cell coordinates, logical-word multiplicity vector, or a smaller sufficient statistic for the declared `A`.
2. `[UNKNOWN]` Temporal process on scrub-window scales: HPP, NHPP/time-dependent intensity, compound marked process, burst/Cox alternative, or bounded empirical schedule.
3. `[UNKNOWN]` General initial-state representation `μ_t0`, including mid-cycle entry, residual errors, and partition-specific word ages.
4. `[UNKNOWN]` Target correction/writeback/reset timing: synchronous global, sequential scan, on-access repair, partial coverage, or mixed policy.
5. `[UNKNOWN]` Exact disjoint recombination of direct same-particle marks and independent accumulation without the Eq. (15) overlap risk.
6. `[UNKNOWN]` Observation model connecting static bitmap/scan data to latent physical events, including false merges and splits.
7. `[UNKNOWN]` Decoder capability interface that remains compatible with RQ-003 responsibility and does not identify `E_cap` with DUE/SDC.
8. `[UNKNOWN]` Parameter/model uncertainty propagation into `F_A`, particularly sparse high-multiplicity tails and topology/classification error.
9. `[UNKNOWN]` Computational cost at target domain scale for adaptive-scrub policy evaluation.
10. `[UNKNOWN]` Evidence for stationarity/nonstationarity under the target field environment and reporting horizon.

## 13. Model alternatives still admissible after the deep reads

No alternative is selected here.

| Alternative family | Supported element(s) | Required augmentation / reason it remains conditional |
|---|---|---|
| Multiplicity-indexed marked HPP | `PAPER-006` empirical `λ_i`; `PAPER-005` multiplicity partition. | Must add post-`W` joint mark, nonstationarity test, state/repair, and uncertainty. |
| Time-varying marked Poisson/NHPP | Compatible with `PAPER-005` rate integrals and DEC-001 windows. | No batch source validates time-varying intensity on target scales. |
| Compound marked Poisson | `PAPER-007` represents clustered event sizes and parent marks. | Marginal cluster-size law alone is insufficient when topology/`W` matters. |
| Event-driven Monte Carlo with physical/post-`W` marks | `PAPER-007` and `PAPER-008` support topology/provenance and explicit state updates. | Needs target mapping, calibrated event distribution, computational study, and general initial state. |
| Analytic occupancy model for independent accumulation plus a separate direct-event layer | `PAPER-004` supplies an accumulation kernel; `PAPER-005`, `PAPER-006` and `PAPER-008` supply candidate direct layers. | Must define disjoint recombination, first-passage state, realistic scrubbing, and mapping. |
| Discrete-time scan/repair state model | `PAPER-008` provides scan windows; `PAPER-004` and `PAPER-007` show reset effects. | Exact target scan/writeback semantics and word-age distribution are absent. |
| Observation-aware latent-event model | `PAPER-008` provides false-merge/split evidence; `PAPER-004` and `PAPER-006` expose provenance limitations. | Requires identifiable classification-error parameters and validation data. |

## 14. Alternatives narrowed or ruled insufficient as stand-alone models

- `[INFERENCE]` **Unmarked bit-level HPP alone is insufficient** when one parent can upset multiple mapped codewords or topology affects codeword multiplicity.
- `[INFERENCE]` **Marginal multiplicity probabilities `q_k` alone are insufficient** unless the target `W` makes topology irrelevant or a conservative bound is separately justified.
- `[INFERENCE]` **`PAPER-004`'s clean count-conditioned occupancy model alone is insufficient** for general `F_A(t0,T;μ_t0)` because it has no time law/direct events/general initial state.
- `[INFERENCE]` **`PAPER-005` Eq. (15) alone is insufficient as an exact direct-plus-accumulation partition** because disjointness is not established and validity is restricted to `β≪1`.
- `[INFERENCE]` **Static bitmap clusters alone are insufficient as physical-event observations** without an association/error model, as shown by `PAPER-008`.
- `[INFERENCE]` **A clean-start, synchronous-scrub `F(t)` alone is insufficient** for heterogeneous sequential word ages required by a general controller-managed domain.

## 15. Evidence gaps requiring later named work

These are gaps only; no new RQ/HYP/EXP is created.

- Target-specific physical-to-logical mapping `W` and partition of `A`.
- Field/environment time-series evidence at adaptive-scrub window scales.
- Sequential correction/writeback/reset trace for the target controller.
- Initial-state/word-age distribution at arbitrary `t0`.
- Joint direct-event topology/multiplicity distribution after `W`, with uncertainty.
- Disjoint direct-versus-independent-accumulation recombination proof or validated algorithm.
- Decoder-capability interface compatible with, but not replacing, RQ-003.
- Observation-error model for bitmap/scan datasets.
- End-to-end uncertainty propagation and computational benchmark.

## 16. HANDOFF TO ZOTERO

No Zotero operation was performed. The following structured handoff is prepared because version identity and metadata provenance matter for later acceptance.

| Accepted card / candidate(s) | Target collection | Required action | Duplicate policy / expected result |
|---|---|---|---|
| `PAPER-005` / RQ2-C005 and companion RQ2-C006 | `DISSERTATION / RQ / RQ-002` | Preserve exact arXiv v2 and the RADECS DOI publication as separate related items; attach the exact analyzed PDFs and version/checksum notes. | Do not merge by title/authors. Match C005 by versioned arXiv ID and C006 by DOI; record their verified content relationship. |
| `PAPER-004` / RQ2-C001 | `DISSERTATION / RQ / RQ-002` | Verify DOI, volume/issue/pages, and attach the analyzed publisher PDF. | DOI-first deduplication; one item with exact attachment/version note. |
| `PAPER-007` / RQ2-C011 | `DISSERTATION / RQ / RQ-002` | Verify DOI, volume/issue/pages, and attach the analyzed publisher PDF. | DOI-first deduplication; one item with exact attachment/version note. |
| `PAPER-006` / RQ2-C008 | `DISSERTATION / RQ / RQ-002` | Reconcile final volume/issue/pages from publisher metadata while retaining the analyzed Article-in-Press PDF as a versioned attachment. | DOI-first deduplication; do not replace or relabel the analyzed PDF without preserving its accepted-version identity. |
| `PAPER-008` / RQ2-C020 | `DISSERTATION / RQ / RQ-002` | Verify DOI/current-version date and attach the analyzed publisher PDF. | DOI-first deduplication; one item with exact attachment/version note. |

**Required tags:** `RQ-002`, permanent `PAPER-xxx`, candidate ID, `paper-card-accepted`, and `full-text-verified`.
**Metadata checks:** exact title, author order, year, venue, DOI/arXiv version, pagination/version, and attachment checksum.
**PDF expectation:** PDFs remain Zotero attachments only; none are committed to GitHub.

## 17. Orchestrator disposition and downstream gate

The five Paper Cards and this initial synthesis are accepted for the RQ-002 model-selection gate.

`[INFERENCE]` The batch narrows the admissible structure: a quantitative RQ-002 candidate must distinguish physical parent events from sequential state accumulation, declare or apply `W`, carry enough post-mapping dependence for capability evaluation, expose the repair/initial-state semantics, and treat observation uncertainty explicitly when using bitmap data. It does **not** determine which admissible process family should become the project model and does not answer RQ-002.

- No additional Paper Card or general literature cycle is authorized merely because other `CORE` sources remain unread.
- No process family, event representation, mapping reduction or observation model is selected by this synthesis.
- Candidate synthesis propositions that will carry a model-selection decision must pass a bounded Evidence Auditor gate.
- The C-RQ-05 escalation condition remains triggered; permanent promotion still requires explicit PI acceptance before the main quantitative reliability model is fixed.
- Parameterized prototype work may proceed before numerical `H_req` or `ε_req` exists, but it must report sensitivity rather than claim satisfaction of an unstated requirement.

## 18. Candidate propositions for bounded Evidence Auditor review

These identifiers are audit handles, not permanent `CLM` or `EVD` IDs. Intended use is **RQ-002 model selection and first-prototype specification only**, not a general literature-level novelty statement.

| Candidate | Atomic proposition to audit | Accepted-source scope | Decision enabled |
|---|---|---|---|
| `RQ002-EA-CAND-01` | Physical parent event, cell upset/bit flip, logical codeword-error pattern and `E_cap` are distinct objects; moving between them requires declared mapping and aggregation operations. | `PAPER-004…008` | Define primitive arrival and state interfaces. |
| `RQ002-EA-CAND-02` | Same-particle multi-cell impact and sequential accumulation from independent arrivals are represented by different mechanisms; recombination requires an explicit non-overlap rule or a quantified overlap approximation. | `PAPER-004`, `PAPER-005`, `PAPER-007`, `PAPER-008` | Require mechanism provenance in the model. |
| `RQ002-EA-CAND-03` | Physical upset multiplicity alone does not determine ECC-word impact for an arbitrary mapping `W`; topology/mapping may be reduced only under a stated exactness, bound or approximation condition. | `PAPER-005`, `PAPER-007`, `PAPER-008` | Trigger C-RQ-05 and representation ladder. |
| `RQ002-EA-CAND-04` | Marginal per-word multiplicity distributions are not generally sufficient for domain-level `F_A` when one parent event may jointly affect multiple codewords; sufficiency requires retained joint dependence, a proof of irrelevance or a valid bound. | `PAPER-005`, `PAPER-007`, with DEC-001 contract | Decide minimum post-`W` mark. |
| `RQ002-EA-CAND-05` | Accumulation state and reliability output depend on correction/writeback/reset semantics; global clean reset, correctable-word-only reset and event-wise rewrite are not interchangeable model operations. | `PAPER-004`, `PAPER-006`, `PAPER-007` | Parameterize restoration semantics and state. |
| `RQ002-EA-CAND-06` | A clean-start final-state or count-conditioned failure probability is not generally equivalent to the DEC-001 first-passage metric `F_A(t0,T; μ_t0)` without additional trajectory, initial-state and repair assumptions. | `PAPER-004`, `PAPER-005`, `PAPER-007`, DEC-001 | Prevent invalid metric substitution. |
| `RQ002-EA-CAND-07` | An unmarked scalar bit/upset HPP is inadequate for `E_cap` in regimes where parent-event clustering or post-`W` topology changes codeword multiplicity. | `PAPER-006`, `PAPER-007`, `PAPER-008` | Reject scalar-rate-only model in the stated regime. |
| `RQ002-EA-CAND-08` | The `PAPER-005` Eq. (15) SEC-DED result is a low-`β` additive approximation; the source does not prove disjoint sample spaces for its two terms and does not establish validity beyond `β≪1`. | `PAPER-005` exact arXiv v2 | Prevent adoption as an exact mechanism partition. |
| `RQ002-EA-CAND-09` | Static or quasi-event bitmap grouping can misassociate independent arrivals and direct events; latent physical-event inference from such observations requires an explicit classification/observation-error model. | `PAPER-004`, `PAPER-006`, `PAPER-008` | Require an observable-to-latent interface. |
| `RQ002-EA-CAND-10` | None of `PAPER-004…008` validates a time-varying arrival intensity at the adaptive-restoration decision-window scale; stationarity versus nonstationarity remains a named evidence/model-validation gap rather than a settled model choice. | `PAPER-004…008` only | Keep HPP/NHPP alternatives bounded and explicit. |

For every candidate, the auditor must preserve the source scope, identify the strongest limitation or counterexample, and return `SUPPORTED`, `PARTIALLY_SUPPORTED`, `DISPUTED`, `INSUFFICIENT` or `NOT_VERIFIED`. No permanent claim or evidence ID is assigned automatically.
