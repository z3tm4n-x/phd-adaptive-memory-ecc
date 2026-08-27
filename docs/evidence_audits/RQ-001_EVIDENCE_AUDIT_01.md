# RQ-001 — Evidence Audit of RQ001-EA-CAND-01…12

**Task:** `RQ-001-EVIDENCE-AUDIT-01`  
**Role:** Evidence Auditor  
**Date:** 2026-08-27  
**Disposition:** `AUDIT COMPLETE — ACCEPTED WITH CAND-10 DEFERRED`  
**Canonical recording:** accepted in `docs/evidence_audits/RQ-001_EVIDENCE_AUDIT_01.md`  
**RQ status:** remains `INVESTIGATING`

## 1. Audit basis and method

The audit preserves the twelve candidate wordings exactly and assesses each as a separate proposition. The canonical evidence base is:

- [PAPER-001 — Tausch (2009)](https://ieeexplore.ieee.org/document/4812293/), DOI `10.1109/TNS.2009.2012710`;
- [PAPER-002 — Baeg, Wen, and Wong (2009)](https://ieeexplore.ieee.org/document/5204525/), DOI `10.1109/TNS.2009.2015312`;
- [PAPER-003 — Lee, Baeg, and Reviriego (2011)](https://ieeexplore.ieee.org/document/6026934/), DOI `10.1109/TNS.2011.2164555`.

Judgments were made from the accepted full-text Paper Cards and their page/equation traces, not from abstracts or citation counts. The claims that depend on exact model structure were rechecked against the recorded equations and page-specific primary-text extractions. Scite full-text retrieval was unavailable for all three non-open-access articles in this session, so Scite was not used as a substitute for the primary text.

### Scite discovery result — no evidentiary weight

Exact-DOI discovery returned the following classified statement tallies: PAPER-001: 23 mentioning, 0 supporting, 0 contrasting; PAPER-002: 47 mentioning, 1 supporting, 0 contrasting; PAPER-003: 4 mentioning, 0 supporting, 0 contrasting. The underlying citation statements were not returned because content access was denied. These counts establish neither validity nor absence of criticism and do not affect any status below.

### Editorial-notice checks

| Code | Source | Result as of 2026-08-27 |
|---|---|---|
| `ED-1` | PAPER-001 | No correction, erratum, retraction, expression of concern, or other editorial notice was located in exact-title/DOI searches, the IEEE record, or Scite notice filters. This is “no notice found,” not proof that none exists. |
| `ED-2` | PAPER-002 | Same result and limitation. |
| `ED-3` | PAPER-003 | Same result and limitation. |

Confidence in the notice check is **medium**, because no explicit Crossmark history was available and Scite’s full-text/notice context was incomplete.

## 2. Decision matrix

| Candidate | Assessment | Confidence | Later permanent-claim recommendation |
|---|---|---|---|
| `RQ001-EA-CAND-01` | `SUPPORTED` | High | Suitable |
| `RQ001-EA-CAND-02` | `SUPPORTED` | High | Suitable |
| `RQ001-EA-CAND-03` | `SUPPORTED` | High | Suitable with the row-prose caveat retained |
| `RQ001-EA-CAND-04` | `SUPPORTED` | High | Suitable as an inference |
| `RQ001-EA-CAND-05` | `SUPPORTED` | High | Suitable |
| `RQ001-EA-CAND-06` | `SUPPORTED` | High | Suitable as an inference |
| `RQ001-EA-CAND-07` | `SUPPORTED` | Medium-high | Suitable as an inference |
| `RQ001-EA-CAND-08` | `SUPPORTED` | Medium-high | Suitable only with the sample-space/horizon limitation retained |
| `RQ001-EA-CAND-09` | `SUPPORTED` | Medium-high | Suitable only with the sample-space/horizon limitation retained |
| `RQ001-EA-CAND-10` | `PARTIALLY_SUPPORTED` | Medium | Defer |
| `RQ001-EA-CAND-11` | `SUPPORTED` | High | Suitable |
| `RQ001-EA-CAND-12` | `SUPPORTED` | High | Suitable as source synthesis |

## 3. Atomic claim audits

### RQ001-EA-CAND-01 — PAPER-001 event

**Claim:** `[SOURCE] PAPER-001 defines the modeled array event as the existence of at least one Hamming-protected word containing at least two distinct upset bits after p accumulated random upsets.`

**Primary supporting evidence.** Sections II–III and Eqs. 17–18 define a birthday-collision probability over the full bit population. In the memory specialization, a collision means two distinct upset locations in one protected word, and “some word” is existential over the complete array. The worked example contains 524,288 protected words; `p` is the total accumulated random-upset count. The irradiation protocol also accumulates a prescribed count with EDAC disabled and then tests whether any non-correctable word exists (pp. 474–477).

**Strongest contrasting or limiting evidence.** The collision-range and first-order birthday approximation simplify exact word boundaries; direct same-particle MBU is excluded; experimental repetitions are small. These limit accuracy and external validity but do not alter the event definition.

**Actual citation context.** Tausch’s later paper explicitly describes the 2009 result as predicting the cumulative probability of a single uncorrectable double-bit word as the number of random upsets increases, then extends it to the number of failing addresses. That is a development/extension context, not independent validation: [Tausch (2015)](https://ieeexplore.ieee.org/document/7182796/).

**Editorial concerns.** `ED-1`.

**Scope match.** Memory: Hamming-EDAC semiconductor memory/SRAM example; ECC: 39-bit protected word, single-bit correction and double-bit detection; aggregation: word → complete array/device; horizon: accumulated count `p`; arrival process: none in Eq. 18, only isolated uniformly random persistent locations; metric: cumulative array-event probability conditional on `p`; units: probability dimensionless, `p` a count. **Match is exact within this model.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** This verifies the modeled array event, not an elapsed-time, decoder-outcome, service-loss, or arbitrary-mapping event.

**Evidence that could change the assessment.** A primary-text correction showing that Eq. 18 is per-word rather than array-wide, or that repeated hits to one physical cell count as the modeled double-bit event.

### RQ001-EA-CAND-02 — PAPER-002 event

**Claim:** `[SOURCE] PAPER-002 defines leaf-block failure as the existence of at least one SEC-protected word containing at least two distinct upset cells by elapsed time t.`

**Primary supporting evidence.** Eq. 1 defines `F(t)=Σ_X P(X,t)P_f(X)`. Eqs. 4–6 define `P_f(X)` by counting assignments with at least two occupied cells in one SEC word; multiple instances that occupy only one physical cell do not constitute failure. The authors explicitly restrict the modeled aggregate to one leaf block (pp. 2114–2116).

**Strongest contrasting or limiting evidence.** The conditional location model is independent and uniform, the true 45 nm hierarchy was unavailable, and multi-block aggregation is excluded. No scan/repair process or decoder-output classes are represented.

**Actual citation context.** PAPER-003 treats this as the earlier interleaving-selection/total-upset-count model, reuses its compound-Poisson time layer in Eq. 7, and limits it by arguing that the earlier row-depth representation is unsuitable for accumulated-error clustering (PAPER-003, Introduction and pp. 2485–2488). This is use plus model-form limitation, not a contradiction of the leaf-block event.

**Editorial concerns.** `ED-2`.

**Scope match.** Memory: SRAM leaf block; ECC: SEC; aggregation: word → one leaf block; horizon: elapsed `t`; arrival process: constant-rate Poisson grouped arrivals, iid geometric multiplicity, then independent uniform placement conditional on total `X`; metric: cumulative `F(t)` and `R(t)`; units: probabilities dimensionless, with derived MTTF in the time unit of `t` and FIT per `10^9` h/Mbit when hours are used. **Match is exact for `F(t)` at leaf-block level.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** “Failure” means a multiplicity state in one modeled leaf block, not bank/device/system failure and not a measured decoder consequence.

**Evidence that could change the assessment.** Primary text or an erratum redefining `P_f(X)` as per-word rather than leaf-block existential probability, or changing the distinct-cell threshold.

### RQ001-EA-CAND-03 — PAPER-003 event

**Claim:** `[SOURCE] PAPER-003 defines modeled-memory failure as the existence of at least one ECC word whose upset multiplicity exceeds the modeled correction capability.`

**Primary supporting evidence.** The word rule is “upsets exceed correctable bits” (p. 2484). Eqs. 4–6 aggregate word failure through a row to `F_mem(X,ID)`, whose memory-level event is one or more failing words. The main model is SEC; a DEC-TED case is illustrative.

**Strongest contrasting or limiting evidence.** Row-level prose is internally inconsistent (“more than one” and then “one or more” failing words), but the word rule and memory-level event are clear. The actual 45 nm hierarchy is replaced by an assumed architecture, and decoder outcomes are not modeled.

**Actual citation context.** A later same-line study moves from the single modeled-memory representation to multiple blocks and the number of accessed blocks, showing that cross-block combinations alter word-failure rates. This limits aggregation transfer but does not contradict the event definition: [Lee et al. (2013)](https://ieeexplore.ieee.org/document/6496324/). A later multi-error-ECC model cites PAPER-003 while extending the correction capability beyond SEC: [Jahanirad (2017)](https://link.springer.com/article/10.1007/s10836-017-5649-x).

**Editorial concerns.** `ED-3`.

**Scope match.** Memory: modeled 45 nm SRAM representation; ECC: main SEC, DEC-TED illustrative; aggregation: word → physical row → modeled memory; horizon: accumulated `X` and elapsed `t` since effective refresh/reset within deterministic `T_scr`; arrival process: fitted row grouping plus compound-Poisson total count, with a richer MCU/SBU simulator; metric: `F_mem(X,ID)`, `F(t,ID)`, and `R(t,ID)` dimensionless; units: probabilities dimensionless, reported word MTBF in seconds. **Match is exact at memory level.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** The row-prose ambiguity must remain attached, and the statement must not be generalized to real decoder behavior or an arbitrary physical architecture.

**Evidence that could change the assessment.** An erratum resolving the memory event differently, or primary equations that separately define decoder outcomes rather than multiplicity beyond capability.

### RQ001-EA-CAND-04 — PAPER-001 horizon

**Claim:** `[INFERENCE] The probability in PAPER-001, being conditioned on accumulated upset count p, cannot be interpreted as elapsed-time, scrub-cycle or mission reliability without an additional upset-count arrival model and repair/reset semantics.`

**Primary supporting evidence.** Eq. 18 has inputs `n`, `k`, and `p`, with no time, flux, repair, or reset state. A time probability requires an additional mixture over an arrival-count process, for example `Σ_p P_collision(n,k,p) Pr{N(t)=p}`. A scrub-cycle or mission quantity additionally requires an exposure/repair state and a cross-cycle aggregation rule.

**Strongest contrasting or limiting evidence.** The experiment reports flux, cross section, and an observed accumulation rate, so a scenario-specific time mapping can be constructed. That information is external to Eq. 18 and was obtained with EDAC disabled during irradiation; it does not supply operational scrub or mission semantics.

**Actual citation context.** The 2015 extension still characterizes and extends the model as a function of random-upset count, confirming the count-domain context rather than supplying a general time/mission transformation: [Tausch (2015)](https://ieeexplore.ieee.org/document/7182796/). A later independent accumulation paper likewise gives reliability as a function of accumulated bit-flip count, memory size, and word size: [Clemente, Rezaei, and Franco (2022)](https://ieeexplore.ieee.org/document/9682731/).

**Editorial concerns.** `ED-1`.

**Scope match.** Memory/ECC/aggregation: same as CAND-01; horizon: exactly count-conditioned `p`; arrival process: absent from the equation; metric: conditional cumulative array probability; units: dimensionless probability versus count. **The dimensional and stochastic-layer mismatch is exact.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** The claim does not say conversion is impossible; it says conversion is not justified without additional, scenario-specific arrival and repair semantics.

**Evidence that could change the assessment.** A primary, validated derivation in PAPER-001 that already embeds `p` in a stochastic time process and specifies operational reset/cycle aggregation.

### RQ001-EA-CAND-05 — PAPER-001 mechanism boundary

**Claim:** `[SOURCE] Harmful same-particle MBU is outside the main equation of PAPER-001 and is identified by the author as requiring a separate mapping-dependent probability component.`

**Primary supporting evidence.** Section V calls the isolated-upset equation a theoretical best case. It states that when one MBU can cross physical tile boundaries and place multiple affected cells in the same Hamming word, the main equation must be enhanced with a separate probability component governed by physical/logical mapping (p. 477).

**Strongest contrasting or limiting evidence.** The statement applies to *harmful* MBU configurations. An MBU confined to a mapping that places its cells in different logical words may remain SEC-correctable. PAPER-001 supplies no quantitative MBU component or explicit map.

**Actual citation context.** Later work distinguishes exactly these mechanisms: interleaving can prevent one particle from flipping several cells in one word, while independent events can still accumulate in that word. This supports the boundary concept but does not validate PAPER-001’s missing term: [Clemente et al. (2022)](https://docta.ucm.es/entities/publication/e52a4bb5-be00-4c1a-9c4e-4bf89b0c9e26).

**Editorial concerns.** `ED-1`.

**Scope match.** Memory: Hamming-EDAC array; ECC: single correction; aggregation: array event; horizon: accumulated `p`; arrival process: isolated random upsets only in the main equation; mapping: qualitative tile/logical-word dependence; metric: dimensionless cumulative collision probability. **Match is exact for the stated mechanism boundary.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** The source identifies the need for a separate mapping-dependent component but neither derives it nor proves how to combine it without overlap.

**Evidence that could change the assessment.** A corrected main equation that explicitly integrates same-particle MBU topology, or primary text showing that the proposed separate component is only optional commentary rather than a model boundary.

### RQ001-EA-CAND-06 — PAPER-002 provenance loss

**Claim:** `[INFERENCE] The final failure probability in PAPER-002 does not retain whether the multiple erroneous cells in a failed word originated from one grouped particle arrival or from multiple arrivals.`

**Primary supporting evidence.** `P(X,t)` retains grouped-arrival statistics through Poisson `Y` and geometric multiplicity, but `P_f(X)` is conditioned only on total `X` and maps every upset instance independently over physical cells. The final sum over `X` therefore has no variable that identifies the parent arrival(s) of the occupied cells in a failed word (Eqs. 1–6, pp. 2114–2116).

**Strongest contrasting or limiting evidence.** Grouping is not absent from the total: `λ` and `r` influence the distribution of `X`. The loss is attribution/provenance at the failed-word level, not loss of all statistical influence of MCU-bearing arrivals.

**Actual citation context.** PAPER-003 reuses the compound-Poisson total-count layer from PAPER-002 but introduces accumulated row grouping because the earlier row-depth approach does not describe continued accumulation adequately. This is a direct developmental citation context and is consistent with provenance compression rather than a mechanism-separated decomposition.

**Editorial concerns.** `ED-2`.

**Scope match.** Memory: one SRAM leaf block; ECC: SEC; aggregation: word → leaf block; horizon: elapsed `t`; arrival process: grouped Poisson/geometric upstream, independent uniform placement downstream; metric: total `F(t)`; units: dimensionless. **Match is exact for the published final probability.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** The claim applies to the final analytical probability, not to the upstream generative distribution, whose multiplicity parameter still reflects grouped arrivals.

**Evidence that could change the assessment.** A published conditional decomposition such as `F_direct(t)` and `F_accum(t)` based on retained parent-event identifiers or topology.

### RQ001-EA-CAND-07 — PAPER-003 provenance loss

**Claim:** `[INFERENCE] The analytical failure probability in PAPER-003 does not retain whether the multiple erroneous cells in a failed word originated from one MCU or from independent arrivals accumulated between repairs.`

**Primary supporting evidence.** The row-group analysis explicitly uses accumulated upset locations without MCU/SBU distinctions (p. 2485). `F_mem(X,ID)` and `F(t,ID)` aggregate through total count and row grouping (Eqs. 5–9). The separate Monte Carlo generator labels MCU/SBU arrivals, but those labels are not output as separate analytical failure probabilities (pp. 2490–2491).

**Strongest contrasting or limiting evidence.** The simulator does retain event labels internally and uses an MCU ratio and test-derived shapes. Thus the paper as a whole can vary MCU influence; the claim is valid only for the analytical failure output, not every computational state in the study.

**Actual citation context.** Later accumulation work explicitly separates the conceptual case of one-particle multi-cell effects from multiple independent events while still calculating a total accumulated-bit-flip reliability quantity. That shows why provenance is a distinct modeling dimension, but it does not independently validate the exact internals of PAPER-003: [Clemente et al. (2022)](https://ieeexplore.ieee.org/document/9682731/).

**Editorial concerns.** `ED-3`.

**Scope match.** Memory: assumed 45 nm SRAM representation; ECC: main SEC; aggregation: word → row → modeled memory; horizon: `X` and `t` within `T_scr`; arrival process: row-group/compound-Poisson analytical model, richer labeled simulator; metric: analytical `F_mem`/`F(t,ID)`; units: dimensionless. **Match is exact only for the analytical output.**

**Assessment:** `SUPPORTED`. **Confidence:** Medium-high.

**Exact limitation.** Provenance is removed from the analytical probability, but MCU/SBU labels and parameters exist in the separate simulator.

**Evidence that could change the assessment.** A primary equation or published output that analytically conditions failure on the causal mechanism of the word’s erroneous cells.

### RQ001-EA-CAND-08 — overlap consequence for PAPER-002

**Claim:** `[INFERENCE] Adding a separate direct-MCU probability or rate to the total failure metric of PAPER-002 without partitioning its upstream event population would overlap events already contained in that total.`

**Primary supporting evidence.** The upstream compound-Poisson process already contains multi-upset grouped arrivals, and the total event `F(t)` includes every modeled history in which the resulting occupied cells produce a failed word. A harmful one-arrival subset is therefore inside the total event. Adding its unconditional probability again duplicates the intersection unless the source population or event algebra is made disjoint.

**Strongest contrasting or limiting evidence.** PAPER-002 does not explicitly perform this addition. Its spatial approximation does not preserve real MCU topology, so the *amount* of physical overlap cannot be recovered from the published total. A separately defined term would not overlap if the original process were first restricted to an explicitly disjoint population or if a complete competing-risk/union model were derived. The paper also supplies no mechanism-specific rate directly comparable to `F(t)`.

**Actual citation context.** The 2022 accumulation paper’s explicit separation of one-particle and independent-event mechanisms shows why the populations must be defined before recombination; it is contextual support for the set-partition requirement, not proof of a numerical overlap fraction: [Clemente et al. (2022)](https://docta.ucm.es/entities/publication/e52a4bb5-be00-4c1a-9c4e-4bf89b0c9e26).

**Editorial concerns.** `ED-2`.

**Scope match.** Memory/ECC/aggregation/horizon/arrival: exactly PAPER-002’s SEC leaf-block compound process over `t`; metric: total `F(t)` or a consistently defined same-scope failure rate; units: probability is dimensionless, rate is per time and may only be combined with a like quantity. **Match requires the same sample space, aggregate, horizon, event definition, and units.**

**Assessment:** `SUPPORTED`. **Confidence:** Medium-high.

**Exact limitation.** This is a conditional event-algebra conclusion, not an author-reported result and not a quantified double-counting estimate.

**Evidence that could change the assessment.** A derivation showing that a proposed direct-MCU term is built from events explicitly excluded from the original `P(X,t)`/`F(t)`, or a mutually exclusive marked-process decomposition.

### RQ001-EA-CAND-09 — overlap consequence for PAPER-003

**Claim:** `[INFERENCE] Adding a separate direct-MCU probability or rate to the total failure metric of PAPER-003 without partitioning its upstream event population would overlap events already contained in that total.`

**Primary supporting evidence.** PAPER-003’s data-derived row groups and compound-Poisson total count merge MCU and SBU contributions before `F_mem` and `F(t,ID)` are formed; its simulator also includes MCU arrivals. Harmful direct-MCU histories therefore contribute to the total modeled event even though their label is not retained. Adding an unconditional direct component to that total repeats those histories unless the upstream population is partitioned.

**Strongest contrasting or limiting evidence.** No explicit arithmetic double counting occurs inside the published model, and the exact overlap fraction is unidentifiable from the analytical output. A disjoint simulator experiment or recalibrated analytical model could separate mechanisms. As in CAND-08, probabilities and rates require like units and matched horizons.

**Actual citation context.** Later work on accumulated events treats direct one-particle effects and independent-event accumulation as distinguishable mechanisms, reinforcing the need for explicit partitioning before recombination: [Clemente et al. (2022)](https://ieeexplore.ieee.org/document/9682731/).

**Editorial concerns.** `ED-3`.

**Scope match.** Memory: modeled SRAM; ECC: main SEC; aggregation: word → row → memory; horizon: count/time within `T_scr`; arrival process: merged row-group/compound-Poisson population with a labeled simulator; metric: total `F_mem` or `F(t,ID)`, or a same-scope rate; units: dimensionless probability or per-time rate, never mixed directly. **Match requires identical event, horizon, aggregate, and units.**

**Assessment:** `SUPPORTED`. **Confidence:** Medium-high.

**Exact limitation.** This establishes overlap in event membership, not its magnitude, and only when the added term is drawn from the same unpartitioned event population.

**Evidence that could change the assessment.** A mechanism-conditioned analytical derivation proving that direct-MCU events are excluded from `F_mem`/`F(t,ID)` before the external term is added.

### RQ001-EA-CAND-10 — PAPER-003 scrub abstraction

**Claim:** `[INFERENCE] The periodic-maintenance equations in PAPER-003 treat completion of a deterministic full-memory scrub as an effective reset of correctable accumulated errors and do not represent different word exposure ages during a sequential scan.`

**Primary supporting evidence.** The prose describes periodic scanning, ECC correction, and writeback; accumulated errors remain until scrub/reset. Eq. 10 uses one deterministic `T_scr`, integrates one common `R(t,ID)` from 0 to `T_scr`, and applies a renewal-style denominator `1-R(T_scr,ID)`. No scan-position state, word-specific last-correction time, scan duration, or arrivals during scan appear in Eqs. 7–10.

**Strongest contrasting or limiting evidence.** The paper does describe a physical scan rather than an instantaneous repair action. The effective synchronous-reset interpretation is inferred from the renewal equation, and the cited periodic-maintenance derivation behind Eq. 10 was not independently audited in the accepted card. Separately, the same research line shows that when multibit errors matter, the order in which memory is scrubbed can affect reliability: [Reviriego, Maestro, and Baeg (2010)](https://ieeexplore.ieee.org/document/5361330/). That limits the abstraction but does not prove PAPER-003 contains word ages.

**Actual citation context.** The 2010 scrubbing-sequence paper treats scrub order as a substantive design variable. PAPER-003’s Eq. 10 cites a generic periodic-maintenance approximation instead and contains no equivalent sequence variable. This is contrasting model-scope context, not a retraction of PAPER-003.

**Editorial concerns.** `ED-3`.

**Scope match.** Memory: modeled SRAM; ECC: main SEC; aggregation: memory reliability converted to word MTBF; horizon: repeated deterministic full-memory intervals `T_scr`; arrival process: compound-Poisson accumulation between maintenance boundaries; metric: `R(t,ID)` dimensionless and word MTBF; units: `T_scr`/MTBF in seconds in the reported examples. **The missing sequential-age state matches exactly; the effective-reset-at-completion wording is inferential.**

**Assessment:** `PARTIALLY_SUPPORTED`. **Confidence:** Medium.

**Exact limitation.** The equations omit word-specific exposure ages, but the stronger characterization of scrub completion as a synchronous global reset depends on the unaudited periodic-maintenance derivation and is not stated explicitly in the source.

**Evidence that could change the assessment.** The primary derivation cited for Eq. 10; an implementation section defining when correction takes effect; or equations with scan position, per-word ages, scan duration, concurrent arrivals, or imperfect coverage.

### RQ001-EA-CAND-11 — PAPER-002 conditional upper bound

**Claim:** `[SOURCE] The independent-location failure calculation in PAPER-002 is an upper bound only when MCU row spans greater than the modeled interleaving distance are absent or negligible.`

**Primary supporting evidence.** Section IV states the conservative relation for independent uniform placement under the condition that MCU row depth/span does not exceed `ID`, or longer spans have negligible probability. It also explains that when span exceeds `ID`, one MCU can directly place multiple errors in one word and the upper-bound relation may fail (p. 2115).

**Strongest contrasting or limiting evidence.** The paper’s 45 nm comparison used an unknown real hierarchy and arbitrary pseudo-partitioning; observed conservatism in that sample does not establish a universal upper bound. Technology-specific topology is required.

**Actual citation context.** A later same-line study says the ideal `ID` is at least the maximum expected MCU size, while exploring smaller IDs only as a cost/reliability tradeoff. This independently matches the span/ID boundary: [Reviriego et al. (2010)](https://ieeexplore.ieee.org/document/5550430/).

**Editorial concerns.** `ED-2`.

**Scope match.** Memory: SRAM leaf block; ECC: SEC; aggregation: word → leaf block; horizon: conditional `X` and elapsed `t`; arrival process: compound-Poisson multiplicity with independent location approximation; metric: conditional `P_f(X)` and total `F(t)`; units: dimensionless. **Match is exact only under the stated MCU-span condition.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** This is not a universal bound over arbitrary layouts, mappings, or MCU size distributions.

**Evidence that could change the assessment.** An erratum changing the inequality/condition, or topology-resolved evidence showing the independent-location model remains an upper bound even with non-negligible spans above `ID`.

### RQ001-EA-CAND-12 — modeled outcome class

**Claim:** `[SOURCE SYNTHESIS] PAPER-001, PAPER-002 and PAPER-003 define failure through erroneous-bit multiplicity beyond modeled correction capability rather than through an observed decoder output or system-visible loss-of-service event.`

**Primary supporting evidence.** PAPER-001 labels the first two-distinct-bit Hamming word non-correctable; PAPER-002 labels at least two distinct erroneous cells in one SEC word unrepairable; PAPER-003 defines word failure as upset count beyond correction capability and aggregates it to memory. None has separate state equations for detected-uncorrectable error, silent data corruption, miscorrection, decoder syndrome/output, or service loss.

**Strongest contrasting or limiting evidence.** PAPER-001’s experiment uses EDAC/readout to observe whether a non-correctable word exists, and the papers mention detection/SDC/DUE concepts narratively. Those observations do not change the mathematical failure state. PAPER-003 also includes an illustrative DEC-TED comparison, but still labels failure by multiplicity beyond capability.

**Actual citation context.** Later accumulation work remains in the same multiplicity/correction-capability class, computing error probability from accumulated bit flips, memory size, word size, and ECC capability rather than a system service event: [Clemente et al. (2022)](https://ieeexplore.ieee.org/document/9682731/). The 2013 multiple-block extension changes aggregation but still discusses word-failure rates, not system-visible service loss: [Lee et al. (2013)](https://ieeexplore.ieee.org/document/6496324/).

**Editorial concerns.** `ED-1`, `ED-2`, and `ED-3`.

**Scope match.** Memory: PAPER-001 Hamming-EDAC array and PAPER-002/003 SRAM models; ECC: Hamming/SEC, with DEC-TED illustrative in PAPER-003; aggregation: array, leaf block, and modeled memory respectively; horizons: `p`, `t`, and `X/t` within `T_scr`; arrival processes: isolated random locations, compound Poisson/geometric, and fitted row grouping plus compound Poisson; metrics: cumulative failure/reliability probabilities, with derived MTTF/FIT/MTBF; units: core probabilities dimensionless, derived time/rate metrics in their declared units. **Match is exact for the mathematical outcome class, not for all narrative or experimental instrumentation.**

**Assessment:** `SUPPORTED`. **Confidence:** High.

**Exact limitation.** The synthesis cannot establish how a real decoder maps multi-error states to DUE, SDC, miscorrection, or system-visible loss of service.

**Evidence that could change the assessment.** Primary equations in any of the three papers that separately model decoder outputs or propagate them to an explicit service-loss event.

## 4. Recommendation to the Research Orchestrator

Suitable for later permanent acceptance, without changing the audited wording:

- `RQ001-EA-CAND-01`, `02`, `04`, `05`, `06`, `07`, `11`, and `12`;
- `RQ001-EA-CAND-03`, only if its permanent record retains the internal row-level prose ambiguity and makes clear that the audited event is the memory-level event;
- `RQ001-EA-CAND-08` and `09`, only as explicit inferences with the exact condition that the added and existing terms share the same event definition, upstream sample space, aggregate, horizon, and units.

Defer `RQ001-EA-CAND-10`. Its “different word exposure ages are not represented” component is well supported, but its “completion as effective reset” component should not receive permanent acceptance until the periodic-maintenance derivation cited by PAPER-003 or an equivalent primary scrub-state derivation is audited.

No candidate is `DISPUTED`, `INSUFFICIENT`, or `NOT_VERIFIED` on the current evidence. No numerical project reliability threshold is inferred. No work on RQ-002 was started.

## 5. Internal synthesis erratum

Section 9 of the initial synthesis says that the next step is checking “seven exact claims.” Section 8 and the handoff contain twelve. This is an internal document-count typo; it does not affect the evidence judgments above.

## 6. Research Orchestrator disposition

**Accepted:** 2026-08-27  
**Disposition:** `ACCEPTED WITH LIMITATION`

- Audit assessments for CAND-01…09, 11 and 12 are accepted within their stated scope and confidence.
- CAND-10 is not accepted as a permanent claim. Its missing word-specific exposure-age component is supported; the stronger effective-global-reset interpretation remains deferred.
- CAND-01…03 remain source facts in the accepted Paper Cards and cross-paper matrix; separate permanent claim records would be redundant.
- Permanent claim mapping: CAND-04→CLM-001, CAND-05→CLM-002, CAND-06→CLM-003, CAND-07→CLM-004, CAND-08→CLM-005, CAND-09→CLM-006, CAND-11→CLM-007, CAND-12→CLM-008.
- No `EVD-xxx` records are created at this gate; the accepted audit report is the direct trace for the registered claims.

### Contextual-source Zotero reconciliation

Before later contextual/limiting sources are used in publication text, check/import these stable identities in Zotero:

- Tausch (2015), IEEE document `7182796`;
- Lee et al. (2013), IEEE document `6496324`;
- Jahanirad (2017), DOI `10.1007/s10836-017-5649-x`;
- Clemente, Rezaei, and Franco (2022), IEEE document `9682731`;
- Reviriego, Maestro, and Baeg (2010), IEEE document `5361330`;
- Reviriego et al. (2010), IEEE document `5550430`.

This reconciliation is not an order for new Paper Cards or a broad literature search.
