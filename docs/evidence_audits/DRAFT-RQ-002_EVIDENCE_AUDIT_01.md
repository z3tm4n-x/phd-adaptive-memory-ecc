# DRAFT — RQ-002 Evidence Audit 01

**Task:** `RQ-002-EVIDENCE-AUDIT-01`  
**Audit targets:** exactly `RQ002-EA-CAND-01` through `RQ002-EA-CAND-10`  
**Canonical base reviewed:** `c55ba6447e6b1104a5f7ae7af9d3b072c44a6c02`  
**Status:** draft for Research Orchestrator acceptance  
**Date:** 2026-08-28

## 1. Audit boundary and method

This audit is bounded to `PAPER-004`…`PAPER-008`, the accepted initial synthesis, `DEC-001`, `DEC-002`, and the named governance documents. It does not select the project stochastic model, set `H_req` or `epsilon_req`, reopen RQ-001, or make a literature-level novelty claim.

Each candidate was kept at its submitted wording. Where a sentence contains more than one testable component, the components are audited separately under the same candidate; no permanent claim or evidence identifiers are assigned. Assessments distinguish direct source statements from cross-source or mathematical inference.

`E_cap` is used only in the DEC-001 sense: a project-defined first-passage event. It is not identified with DUE, SDC, miscorrection, decoder failure, or system failure.

## 2. Scite and editorial-status check

Scite was used only for discovery of citation context and editorial flags. Citation counts and Scite classifications were not treated as evidence of validity.

| Source | Scite metadata observed | Material incoming citation context located | Correction/retraction/editorial result | Audit use |
|---|---|---|---|---|
| PAPER-004, Clemente et al. 2022, DOI `10.1109/TNS.2022.3143652` | 1 classified citation (mentioning) in the returned metadata | No material claim-level context was returned by the bounded DOI query | No indexed notice was returned. The targeted notice query also reported that queried DOIs were absent from its notice index, so this is **inconclusive**, not proof of absence | Primary text/card controls |
| PAPER-005, Zebrev 2017, arXiv `1704.07271v2`; companion DOI `10.1109/RADECS.2017.8696217` | 2 classified citations (mentioning) for the companion record | No material incoming context for Eq. (15) was returned | No indexed notice was returned; same index limitation. The companion paper is not a substitute for the exact arXiv-v2 equation scope | Exact arXiv v2 controls candidate 08 |
| PAPER-006, Moindjie et al. 2017, DOI `10.1016/j.microrel.2017.07.045` | 6 classified citations: 1 supporting, 0 contrasting, 5 mentioning | A 2022 TNS paper, DOI `10.1109/TNS.2022.3149160`, reuses the long-run Marseille neutron/alpha SER values and cites the prior tester/JESD89B setup. This is method/rate reuse, not independent validation of HPP adequacy at adaptive-window scale | No indexed notice was returned; same index limitation | Context limits candidate 10; it does not validate the temporal model |
| PAPER-007, Ogden and Mascagni 2017, DOI `10.1109/TR.2017.2765484` | 6 classified citations, all mentioning, in returned metadata | No material claim-level context was returned by the bounded DOI query | No indexed notice was returned; same index limitation | Primary text/card controls |
| PAPER-008, Gomi et al. 2026, DOI `10.1109/TNS.2026.3675003` | No classified incoming citations in returned metadata; very recent record | None returned | No indexed notice was returned; same index limitation and a short citation history | Primary text/card controls; low power for later-work checks |

No correction, retraction, or editorial concern was identified in the bounded checks. Because the notice-index response was internally limited and PAPER-008 is very recent, the defensible statement is “no indexed notice located,” not “none exists.”

## 3. Cross-source scope ledger used in every assessment

| Source | Mechanism and primitive | Device / mapping | ECC | Aggregation and horizon | Arrival model | Metric and units |
|---|---|---|---|---|---|---|
| PAPER-004 | Independent random cell-address hits; repeated hits toggle/cancel; direct same-particle MBU excluded by the ideal-interleaving setup | SRAM bitmap/address model; uniform addresses and idealized interleaving | Analytic SEC/SEC-DED pattern treatment | Final occupancy/pattern after fixed hit count `m`; equal instantaneous global clean scrubs | No temporal arrival family for hits; Poisson is used for false-MBU **counts**, not as a validated arrival process | Expected counts and probabilities (dimensionless); not DEC-001 first passage |
| PAPER-005 | Ion strike marked by physical multiplicity `n`; direct multi-cell contribution plus sequential accumulation approximation | Generic memory words; assumes one half of two-fold MCUs map to the same word; no coordinate-level `W` | SEC-DED approximation | Word rates aggregated over `M` words and scrub interval `t_s`; clean/low-occupancy approximation | Environment-integrated event rates; Poisson expression in Eqs. (8)–(11) concerns multiplicity conditional on LET, not temporal validation | `R_n`, `R_w`, `R_syst` are rates (inverse time in the model); `beta` is dimensionless |
| PAPER-006 | One detected particle event with simultaneous cell multiplicity `i`; neutron/alpha classes | Tested SRAMs; no physical-to-logical mapping | None | Event rates per device capacity; errors rewritten after detection and failed devices replaced, so no retained accumulation state | Independent fixed-rate HPPs `N_i(t)` assumed by multiplicity; rates estimated from long exposures, without short-window goodness-of-fit | `lambda_i` in `h^-1 Mbit^-1`; reported SER also in `FIT/Mbit`; event SER is distinct from bit-flip SER |
| PAPER-007 | Parent SEE with time/type/severity/location/topography; event effects accumulate in word state | Simulated SRAM, including a selected 45 nm case; deterministic interleaving; S2P versus sampled 3×3 T2P | Simplified correction capacity represented by number of ECC bits | Word states aggregated to array reliability over scheduled scrub intervals; correctable words reset, failed words persist | Constant-rate parent-event process; compound-Poisson upset count | Reliability/failure probability (dimensionless) over simulated time; not the exact DEC-001 event semantics |
| PAPER-008 | Direct neutron event with row/column pattern versus independent-event pseudo MCU; exact provenance only in PHITS simulation | SRAM macro coordinates; no logical ECC-word `W` | None | Static or quasi-event grouping over a full-macro scan window; no mission accumulation model | Constant-beam Poisson bound for two independent SEUs inside scan time `T`; no validated time-varying mission intensity | Collision/grouping probability (dimensionless); multiplicity and Chebyshev distance in cell-coordinate units |

The ledger prevents cross-paper numerical transfer: mechanisms, devices, mappings, ECC semantics, horizons, and output metrics are not aligned. It is used only to test structural propositions and to identify which interfaces a project comparison must declare.

## 4. Candidate-by-candidate audit matrix

| Candidate | Atomicity disposition | Assessment | Confidence | Precise admissible wording | Consequence for RQ-002 model selection | First parameterized prototype blocker? |
|---|---|---|---|---|---|---|
| 01 | Decompose into (a) object distinction and (b) declared transformations | **SUPPORTED** | High | Within PAPER-004…008 and DEC-001, parent event, affected physical cells/bits, post-mapping codeword pattern, and `E_cap` must be represented as distinct layers; every reduction between layers must declare its mapping or aggregation rule | Require explicit primitive, mapping, state, and outcome interfaces in every candidate representation | No |
| 02 | Decompose into (a) provenance distinction and (b) recombination condition | **SUPPORTED** | High | Direct same-parent multi-cell impact and multi-arrival accumulation are distinct causal routes. A combined calculation must prevent duplicate attribution or state and bound an overlap approximation | Reject an unexplained sum of direct and accumulated failure terms as an exact model | No, if an event-driven reference preserves provenance |
| 03 | Atomic conditional insufficiency statement | **SUPPORTED** | High | Physical-event multiplicity must not be assumed to determine codeword multiplicity for an arbitrary `W`; topology/mapping may be compressed only with an exactness argument, a bound, or an explicitly tested approximation | Keep `W` or a validated post-`W` statistic in the representation ladder; preserve C-RQ-05 gate | No for synthetic declared `W`; yes for target-specific calibration if `W` is unavailable |
| 04 | Decompose into (a) non-sufficiency assertion and (b) three sufficiency conditions | **PARTIALLY_SUPPORTED** | Medium | Marginal per-word multiplicities **cannot be assumed sufficient** for domain-level `F_A` when one parent event can affect several words; sufficiency must be demonstrated by retained dependence, irrelevance to the queried union/first-passage event, or a valid bound | Include a joint-versus-marginal comparison; do not accept marginal marks as the minimum sufficient statistic yet | No; it is a prototype comparison target |
| 05 | One semantics claim with three documented transition variants | **SUPPORTED** | High | Reliability/accumulation output is conditional on the declared correction, writeback, replacement, and reset transitions. The three source-level policies are not interchangeable state updates; their numerical effect remains target-specific | Repair semantics must be an explicit model input, not an implicit property of the arrival process | No if parameterized explicitly |
| 06 | Decompose into (a) metric non-equivalence and (b) required conditions | **SUPPORTED** | High | A clean-start terminal-state or count-conditioned probability is not, by itself, DEC-001 `F_A(t0,T;mu_t0)`. Equivalence requires stated trajectory monotonicity/absorption, initial-state, and repair assumptions | Candidate models must expose path, initial state, and restoration transitions, or prove a valid reduction to terminal state | No |
| 07 | Atomic regime-conditional adequacy claim | **SUPPORTED** | High | An unmarked scalar bit/upset HPP is inadequate for `E_cap` whenever same-parent clustering or post-`W` topology materially changes word-level multiplicity. It may remain a candidate only in a stated regime where those marks are irrelevant or conservatively bounded | Keep marked/structured alternatives on the ladder; do not rule HPP in or out globally | No |
| 08 | Decompose into (a) low-`beta` scope and (b) absence of disjointness proof/beyond-regime validation | **SUPPORTED** | Medium-high | In PAPER-005 arXiv v2, Eq. (15) is a low-`beta` additive SEC-DED approximation using Eqs. (16)–(18). The source neither proves disjoint sample spaces for its two addends nor validates Eq. (15) outside `beta << 1` | Use Eq. (15) only as a scoped low-`beta` comparator, not an exact recombination identity | No, if not used as exact ground truth |
| 09 | Decompose into (a) static grouping error, (b) residual quasi-event association error, and (c) observation-model requirement | **SUPPORTED** | Medium-high | When physical-event provenance is not directly observed, bitmap grouping can merge independent arrivals or split/miss a direct event. Any inference from grouped observations to latent events must state the grouping rule and its false-merge/false-split model or bound | Separate latent-event dynamics from the observation/classification layer | No if the reference simulator retains ground truth; target calibration needs the observation rule |
| 10 | Atomic absence-of-validation claim bounded to five sources | **SUPPORTED** | High | PAPER-004…008 do not validate a time-varying intensity model at the adaptive restoration decision-window scale. This leaves stationarity versus nonstationarity unresolved; it does not establish that NHPP is required | Keep HPP/NHPP/other temporal families open and test value of temporal enrichment at the decision layer | No for a comparative parameterized prototype |

## 5. Detailed reasoning and scope limits

### RQ002-EA-CAND-01

**Submitted proposition.** Physical parent event, cell upset/bit flip, logical codeword-error pattern and `E_cap` are distinct objects; moving between them requires declared mapping and aggregation operations.

**Atomicity.** The sentence contains two linked propositions: (01a) the objects are distinct; (01b) transitions between them require declared operations. Both are supported, but by different parts of the evidence chain.

**Primary supporting evidence.** PAPER-006 defines detected single-particle events stratified by simultaneous cell multiplicity `i` and distinguishes event SER from bit-flip SER. PAPER-007 explicitly samples an SEE with time, type, severity, location and topography, maps affected cells through a deterministic interleaver to logical words, updates word state, and then computes an ECC-oriented reliability output. PAPER-008 records physical row/column event patterns and explicitly distinguishes one-neutron MCU provenance from pseudo-MCU grouping. PAPER-004 starts from cell-address hits and derives final logical pattern classes under an idealized interleaving assumption. DEC-001 separately defines `E_cap` as a trajectory-level first-passage event over the protected partition.

**Strongest limit/contrast.** No paper implements the complete DEC-001 chain. PAPER-006 stops at physical events, PAPER-008 at physical macro patterns, and PAPER-004/007 use source-specific outcome metrics. Therefore the support is for layer separation and explicit interfaces, not for one particular mapping or aggregation.

**Scope match.** Devices range from SRAM test chips to simulated SRAM arrays; mappings range from absent (PAPER-006) through idealized (PAPER-004), explicit regular `W` (PAPER-007), and physical macro coordinates without ECC `W` (PAPER-008). ECC is absent in PAPER-006/008, analytic SEC/SEC-DED in PAPER-004/005, and simplified capacity-based ECC in PAPER-007. Horizons and metrics differ. This heterogeneity strengthens the need for declared interfaces but prevents numerical transfer.

**Assessment rationale.** Direct definitions in the sources establish distinct primitives. DEC-001 supplies the project outcome definition. The need to declare transitions is a traceability requirement forced by the observed non-equivalent mappings.

**Evidence that could change the assessment.** A formally defined source in which all four labels are proven identical under one restricted experiment would only narrow the scope; it would not overturn the general interface requirement. A counterexample to a particular reduction would change that reduction, not this layered proposition.

### RQ002-EA-CAND-02

**Submitted proposition.** Same-particle multi-cell impact and sequential accumulation from independent arrivals are represented by different mechanisms; recombination requires explicit non-overlap rule or quantified overlap approximation.

**Atomicity.** (02a) causal routes differ; (02b) recombination needs a non-overlap rule or bounded approximation.

**Primary supporting evidence.** PAPER-004 explicitly excludes direct same-particle MBU under ideal interleaving and models independent random hits with repeat-hit cancellation. PAPER-005 Eq. (15) adds a sequential term, `beta M R_w(n>=1)`, and a direct multi-cell term, `M R_w(n>=2)`. PAPER-007 represents each parent SEE and then accumulates its mapped effects in word state, so the two routes coexist in one trajectory without discarding provenance. PAPER-008 distinguishes direct one-neutron MCU from pseudo-MCU formed by independent SEUs.

**Strongest limit/contrast.** The routes are causally distinct but need not be disjoint failure attributions: a direct multi-cell event can also leave state that later participates in accumulation. PAPER-005 does not state a partition of histories proving its two Eq. (15) addends disjoint. PAPER-007 avoids formula-level overlap through event-by-event state evolution, but does not provide a closed-form decomposition.

**Scope match.** The evidence covers independent bit hits, multiplicity-marked particle events, explicit topological SEE simulation, and observation grouping. It does not establish one universal decomposition across mappings, ECC policies, or restoration horizons.

**Assessment rationale.** The provenance distinction is direct. The recombination condition follows from ordinary probability accounting and is exposed by the source mismatch. It does not prescribe the required project mechanism.

**Evidence that could change the assessment.** A derivation that defines mutually exclusive history sets for direct and accumulated failure, or a uniform error bound on a deliberately overlapping approximation, would resolve the current recombination condition for that model.

### RQ002-EA-CAND-03

**Submitted proposition.** Physical upset multiplicity alone does not determine ECC-word impact for arbitrary `W`; topology/mapping may be reduced only under stated exactness/bound/approximation condition.

**Atomicity.** Atomic as a conditional insufficiency proposition.

**Primary supporting evidence.** PAPER-005 must introduce a mapping assumption—one half of two-fold MCUs affect the same word—to convert physical multiplicity to SEC-DED word vulnerability (Eqs. (17)–(18)). PAPER-007 holds event time/type/severity/location fixed and changes only S2P versus T2P topography; in the selected 45 nm scenario Tables IV–V and Figs. 6–7 report statistically different reliability (`p=10^-6`). PAPER-008 shows that direct neutron events have spatial patterns including distant pairs, so equal multiplicity does not imply equal geometry.

**Strongest limit/contrast.** Under a specified ideal interleaver, symmetry, or a mapping that makes all placements equivalent for the queried ECC event, a reduced multiplicity statistic can be exact or adequate. PAPER-007 demonstrates a selected simulated scenario, not every device or `W`.

**Scope match.** Direct evidence spans physical multiplicity, physical geometry, explicit cell-to-word mapping, and simplified ECC. It does not validate the project target `W` or decoder semantics.

**Assessment rationale.** PAPER-005's extra mapping assumption and PAPER-007's controlled topography comparison directly refute unconditional sufficiency of physical multiplicity for arbitrary `W`.

**Evidence that could change the assessment.** A proof that a particular target `W` makes the post-`W` multiplicity distribution invariant to all retained topologies, or a validated conservative bound, would permit a reduced representation for that target.

### RQ002-EA-CAND-04

**Submitted proposition.** Marginal per-word multiplicity distributions are not generally sufficient for domain-level `F_A` when one parent event may jointly affect multiple codewords; sufficiency requires retained joint dependence, proof of irrelevance or valid bound.

**Atomicity.** (04a) general non-sufficiency; (04b) acceptable routes to sufficiency. The exact submitted wording is stronger than the direct experimental evidence.

**Primary supporting evidence.** PAPER-007 retains a parent event, mapped affected cells, and simultaneous updates across logical words; thus joint multiword outcomes exist in the modeled state rather than only marginal word counts. PAPER-005 converts event multiplicity into word-level rates using an assumed mapping fraction, but does not represent the joint distribution across multiple words. DEC-001 defines `F_A` as a union/first-passage probability over partition `A`; such a probability is not generally determined by one-dimensional marginals when same-parent marks couple words.

**Strongest limit/contrast.** None of PAPER-004…008 performs a controlled comparison between two post-`W` models with identical per-word marginals but different cross-word dependence and then measures the change in domain-level `F_A`. PAPER-007's topography comparison changes more than a formally isolated dependence statistic. Therefore the exact general sufficiency boundary is inferred from probability structure, not demonstrated by a source-level theorem or target experiment.

**Scope match.** The concern applies to aggregation over multiple codewords and a first-passage union metric. It may be irrelevant for a single-word domain, for an outcome additive in independent word marginals, or when a verified bound replaces exact joint dependence.

**Assessment rationale.** The evidence is sufficient to reject an unexamined sufficiency assumption, but not to assert that a particular joint mark is the minimum adequate post-`W` representation. Hence **PARTIALLY_SUPPORTED**, not SUPPORTED.

**Evidence that could change the assessment.** A counterexample with fixed marginals and materially different `F_A`, a theorem giving necessary/sufficient conditions, or a target-specific irrelevance/bounding proof would raise confidence and settle the admissible reduction.

### RQ002-EA-CAND-05

**Submitted proposition.** Accumulation state/reliability output depend on correction/writeback/reset semantics; global clean reset, correctable-word-only reset, event-wise rewrite not interchangeable.

**Atomicity.** One state-transition claim illustrated by three distinct policies.

**Primary supporting evidence.** PAPER-004 applies equal, instantaneous global clean scrubs to an all-zero state. PAPER-007 globally schedules scrubs but resets only still-correctable words, while failed words persist. PAPER-006 rewrites detected errors after each event and replaces failed devices, so the experiment does not accumulate errors across events in the PAPER-004/007 sense.

**Strongest limit/contrast.** The papers use different devices, arrivals, ECC abstractions, and outputs; they do not provide a controlled numerical experiment varying only repair semantics. The supported conclusion is non-equivalence of state transitions and conditionality of output, not a quantitative ranking of policies.

**Scope match.** The distinction is most important over horizons spanning multiple arrivals or restoration actions. Under a one-event horizon, zero rate, or an absorbing failure definition reached before restoration, some policies may coincide for the queried event.

**Assessment rationale.** The transition rules are explicitly different, and different transition kernels generally induce different path probabilities. The sources establish the semantics; the project must still parameterize the target behavior.

**Evidence that could change the assessment.** Target firmware/controller documentation and a controlled trace replay under alternative policies would determine which distinctions materially affect the first prototype and eventual target model.

### RQ002-EA-CAND-06

**Submitted proposition.** Clean-start final-state or count-conditioned failure probability is not generally equivalent to DEC-001 first-passage `F_A(t0,T;mu_t0)` without trajectory, initial-state, repair assumptions.

**Atomicity.** (06a) non-equivalence; (06b) conditions needed for equivalence.

**Primary supporting evidence.** DEC-001 defines `F_A` as the probability that `E_cap` is reached at some time in the horizon from initial distribution `mu_t0`. PAPER-004 computes final occupancy/pattern probabilities conditional on hit count; because repeated hits toggle and can cancel, a terminal pattern can be below a threshold after an earlier crossing. PAPER-005 derives a clean-memory, low-`beta` system rate approximation rather than DEC-001 first-passage risk. PAPER-007 simulates clean-start reliability trajectories with scheduled repair semantics, which are closer to but still not identical to the DEC-001 contract.

**Strongest limit/contrast.** Terminal-state and first-passage probabilities can coincide under absorbing/monotone failure, fixed clean initial state, and compatible repair rules. The candidate says “not generally equivalent,” not “never equivalent.”

**Scope match.** The distinction is metric- and horizon-specific and survives any arrival-family choice. It is especially material when toggling, repair, or non-clean initial state permits leaving a terminal hazard set.

**Assessment rationale.** PAPER-004 supplies a concrete non-monotone state mechanism; DEC-001 supplies the required project metric. This directly establishes the stated non-equivalence unless additional conditions are proved.

**Evidence that could change the assessment.** A proof that the chosen project state has an absorbing `E_cap` set before intervention and a fixed `mu_t0`, or an exact reduction theorem for the selected repair process, would allow a terminal-state calculation.

### RQ002-EA-CAND-07

**Submitted proposition.** Unmarked scalar bit/upset HPP is inadequate for `E_cap` in regimes where parent-event clustering or post-`W` topology changes codeword multiplicity.

**Atomicity.** Atomic and explicitly regime-conditional.

**Primary supporting evidence.** PAPER-006 uses independent homogeneous Poisson processes `N_i(t)` by event multiplicity, showing that multiplicity marks are distinct from a scalar bit rate even in its source model. PAPER-007 uses a constant-rate parent SEE process but obtains different reliability when topography changes under the same sampled events. PAPER-008 documents direct spatial MCU patterns and pseudo-MCU grouping, which a scalar unmarked arrival count cannot distinguish.

**Strongest limit/contrast.** PAPER-006 does not formally validate independence or HPP fit at short decision windows, and PAPER-007's result is one selected simulation setting. Conversely, an unmarked scalar HPP may be adequate in an SBU-only regime, under a mapping that makes clustering irrelevant, or as a verified conservative bound.

**Scope match.** The claim concerns representation adequacy for the DEC-001 word/domain event, not the mere ability to fit aggregate SER. It does not choose marked HPP, NHPP, compound Poisson, or event-driven simulation.

**Assessment rationale.** A scalar process erases exactly the marks shown by PAPER-007 to change a word-level reliability output. The conditional “in regimes where … changes” prevents overgeneralization.

**Evidence that could change the assessment.** A target-specific sufficiency or error-bound result showing `F_A` insensitive to retained marks would rehabilitate the scalar HPP for that regime.

### RQ002-EA-CAND-08

**Submitted proposition.** PAPER-005 Eq. (15) SEC-DED result is a low-`beta` additive approximation; the source does not prove disjoint sample spaces for the two terms and does not establish validity beyond `beta << 1`.

**Atomicity.** (08a) low-`beta` approximation scope; (08b) no disjointness proof; (08c) no beyond-regime validation.

**Primary supporting evidence.** In the exact arXiv v2, Eq. (15) states

`R_syst = beta M R_w(n>=1) + M R_w(n>=2)`.

Eq. (16) defines `beta = (1/2)(N_BW-1)(R_1 t_s)` and explicitly requires `beta << 1`. Eqs. (17)–(18) approximate the word rates by retaining one- and two-fold contributions and neglecting higher multiplicities. The surrounding derivation adds sequential-accumulation and direct-multiple terms but does not define mutually exclusive sample spaces or give an overlap correction/bound. No derivation or validation is provided for `beta` outside the small-parameter regime.

**Strongest limit/contrast.** The lack of an explicit proof does not itself establish that the overlap is numerically important. Under `beta << 1`, any overlap may be higher order and practically negligible, but PAPER-005 does not quantify that remainder. The companion RADECS record does not carry the exact Eq. (15) scope and cannot expand it.

**Scope match.** The result is for the source's SEC-DED word model, mapping approximation, clean/scrub assumptions, and low-`beta` regime. It is not a general identity for arbitrary `W`, ECC, initial state, or DEC-001 first passage.

**Assessment rationale.** The positive scope statement and the two absence statements are directly verifiable in the exact source. Confidence is below High only because the materiality of possible overlap is not quantified.

**Evidence that could change the assessment.** A source derivation partitioning histories, an explicit inclusion-exclusion term, or a uniform remainder bound in `beta` would make Eq. (15)'s admissible role more precise.

### RQ002-EA-CAND-09

**Submitted proposition.** Static/quasi-event bitmap grouping can misassociate independent arrivals/direct events; latent physical-event inference requires explicit classification/observation-error model.

**Atomicity.** (09a) static grouping error; (09b) residual quasi-event association error; (09c) observation-model requirement.

**Primary supporting evidence.** PAPER-008 explicitly defines pseudo MCU as independent SEUs incorrectly grouped and reports the distance-threshold tradeoff: a large threshold can merge independent events, while a small threshold can miss or split distant direct MCU patterns (Figs. 12–16). Its Poisson calculation in Eqs. (1)–(4) bounds the chance of two independent SEUs within one full-macro scan under the constant-beam test. PAPER-004 notes that final irradiated bitmaps do not reveal parent-event provenance. PAPER-006 detects events in real time but does not fully specify association/classification error.

**Strongest limit/contrast.** PAPER-008 argues that the residual independent-double-hit probability is negligible in its tested quasi-event beam conditions (reported order `10^-12`–`10^-11`), and its PHITS simulation retains exact primary/secondary provenance. Thus the claim does not license treating every quasi-event data set as materially contaminated. Exact provenance simulation does not need latent-event inference.

**Scope match.** The issue is an observation/classification layer, not a physical arrival mechanism. Error rates depend on scan time, flux, macro size, threshold, detector timing, and grouping algorithm; they do not transfer directly to a mission or target memory.

**Assessment rationale.** Static false merge/split behavior is direct evidence. The quasi-event component is supported as a residual bounded possibility, with source-specific negligible probability. Any likelihood or calibration that treats grouped clusters as latent events must therefore expose the rule or bound.

**Evidence that could change the assessment.** Detector-confirmed one-to-one event labels, a validated confusion matrix, or an exact zero-error association proof for a specified acquisition system would remove or bound the observation layer for that system.

### RQ002-EA-CAND-10

**Submitted proposition.** None of PAPER-004…008 validates time-varying arrival intensity at adaptive-window scale; stationarity/nonstationarity remains a named gap, not a settled choice.

**Atomicity.** Atomic and explicitly bounded to the five-paper set.

**Primary supporting evidence.** PAPER-004 conditions on total random hits and does not specify a temporal arrival family. PAPER-005 integrates environment/cross-section information into event rates but does not validate a time-varying point process at the control decision scale. PAPER-006 assumes fixed-rate multiplicity-specific HPPs estimated from long aggregate experiments; no short-window fit or independence test is reported. PAPER-007 uses a constant parent-event rate. PAPER-008 uses a constant-beam Poisson bound only for independent SEUs within a scan window.

**Strongest limit/contrast.** Constant-rate models may still be adequate for a declared stationary regime, and PAPER-008 does analyze a short acquisition interval; however, that calculation is a collision bound under constant flux, not validation of mission-scale time variation or adaptive-window nonstationarity. The bounded source set cannot establish what the wider literature contains.

**Scope match.** The source rates cover beam tests, long terrestrial measurements, environment-integrated rates, and stationary simulation. None is matched to a specified project decision window because that target window and mission trace are not yet fixed.

**Assessment rationale.** This is a supported absence claim over an exhaustively inspected, fixed set. It keeps temporal family selection open rather than implying NHPP superiority.

**Evidence that could change the assessment.** Timestamped target-relevant event traces across the proposed decision/restoration horizon, with a stated model-checking protocol comparing stationary and time-varying families, would settle whether temporal enrichment matters.

## 6. Propositions safe for a later model-selection DEC

The following may be used, with the precise admissible wording and source boundary in the matrix:

1. Candidate 01: enforce physical-event, physical-error, logical-pattern, and DEC-001 outcome separation.
2. Candidate 02: keep direct and accumulated provenance distinct and require non-overlapping or bounded recombination.
3. Candidate 03: do not reduce physical multiplicity across arbitrary `W` without an exactness/bound/approximation statement.
4. Candidate 05: expose repair/writeback/reset semantics as model inputs.
5. Candidate 06: require path/initial-state/repair compatibility before substituting terminal-state probability for `F_A`.
6. Candidate 07: retain marked/structured alternatives whenever clustering or topology is material; do not globally reject HPP.
7. Candidate 08: use PAPER-005 Eq. (15) only as a low-`beta`, source-scoped comparator.
8. Candidate 09: separate observation/classification error from latent physical-event dynamics when provenance is inferred.
9. Candidate 10: keep stationarity versus nonstationarity open because this evidence set does not validate time-varying intensity at the decision scale.

These propositions constrain interfaces and comparisons. They do not select the stochastic model.

## 7. Propositions that must remain UNKNOWN or conditional

- Candidate 04's exact general assertion remains conditional. The safe conclusion is that marginal per-word marks cannot be **assumed** sufficient; the minimum sufficient post-`W` representation is UNKNOWN.
- The numerical importance and exact correction for overlap between PAPER-005 Eq. (15) addends are UNKNOWN.
- Adequacy of HPP, NHPP, another temporal family, or a non-point-process representation for the target is UNKNOWN.
- Target-specific observation false-merge/false-split parameters are UNKNOWN.
- Target repair/writeback/reset semantics and their quantitative effect are UNKNOWN.
- The target `A`, `W`, decoder/outcome semantics, event/topology distributions, and initial-state distribution remain conditional inputs where not already fixed by DEC-001.
- C-RQ-05's escalation condition is supported, but this audit does not register the proposed RQ-006 or change governance state.

## 8. Exact evidence gaps and prototype impact

| Named gap | What it prevents | Does it block the first parameterized prototype? |
|---|---|---|
| `G-JOINT-SUFFICIENCY`: no same-marginals/different-dependence test or theorem for domain-level `F_A` | Acceptance of a marginal post-`W` representation as sufficient | **No.** Make this a comparison axis against a provenance-retaining reference |
| `G-RECOMBINATION`: no exact disjointness or remainder bound for the PAPER-005 additive split | Treating Eq. (15) as exact combined ground truth | **No.** Use event-wise state evolution as reference and Eq. (15) only as a low-`beta` comparator |
| `G-TARGET-MAPPING`: target physical-to-logical mapping/topology and partition `A` not fixed | Target-specific calibration or final model choice | **No** for declared synthetic `A/W`; **yes** for a target-specific conclusion |
| `G-REPAIR-TRACE`: target correction/writeback/reset behavior not fixed | Target-specific accumulation and first-passage calibration | **No** if policies are explicit parameters; **yes** for a target-specific conclusion |
| `G-OBSERVATION`: no target acquisition/grouping confusion model | Inference of physical event marks from grouped bitmap data | **No** for simulated latent ground truth; **yes** for empirical calibration from grouped data |
| `G-TEMPORAL-WINDOW`: no target-relevant timestamped validation at the adaptive decision horizon | Selection/calibration of stationary versus time-varying intensity | **No** for a representation comparison; **yes** for a validated target temporal family |
| `G-EQ15-REMAINDER`: no quantified valid range beyond `beta << 1` | Extrapolation of PAPER-005 Eq. (15) | **No** if restricted to its stated regime |

Accordingly, **no literature-evidence gap in PAPER-004…008 blocks a first parameterized, comparative prototype** provided that it:

- declares synthetic or provisional `A`, `W`, ECC abstraction, restoration semantics, horizon, and initial state;
- preserves parent-event provenance in the reference implementation;
- evaluates all reduced representations through the same DEC-001 `F_A` interface;
- reports sensitivity/price of information loss rather than target validity;
- does not treat PAPER-005 Eq. (15) as exact ground truth.

The C-RQ-05 promotion remains a governance dependency before fixing the main project model, not a reason to delay the bounded comparison prototype.

## 9. Recommendation

**Further Paper Cards are not required before the first model-selection decision.** The current evidence is sufficient to define a representation ladder, exclude several silent reductions, and design the comparison that will reveal whether richer marks change `F_A` or the adaptive decision.

Do not request broad new literature at this stage. A new Paper Card should be commissioned only through a structured, narrow handoff if the first comparison shows that a decision turns on one of the named gaps—for example, a theorem/bound for joint-to-marginal reduction, target-relevant timestamped arrival traces, or a validated observation confusion model. CORE sources should be processed through the existing workflow before treating their unread status as an evidence gap.

**Acceptance recommendation:** candidates 01, 02, 03, 05, 06, 07, 08, 09, and 10 are suitable for later permanent claim consideration only with the admissible wording above. Candidate 04 should not be accepted at its submitted strength; retain it as conditional and test it in the first representation comparison.
