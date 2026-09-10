# DRAFT — RQ-007 PA-DOM-01…04 common comparison matrix

**Task:** `PA-DOM-01-03-TARGETED-EXTRACTION-01`

**Related RQs:** `RQ-002`, `RQ-003`, `RQ-004`, `RQ-005`, `RQ-006`, `RQ-007`

**Repository baseline:** `83d4db20ce43ff238d58551610f487e7cf3c2c6e`

**Task starting commit:** `b82f146cabed5f92598834db4af78f7ea9b65d6a`

**Accepted identity-control report:** commit
`603fb4bff99a7d5c84f89030e2183bf41026fc15`,
`docs/literature_mapping/PA-DOM-01-03_identity_control.md`

**Lifecycle:** draft synthesis artefact; no permanent identifier assigned

## Scope and evidence discipline

This bounded extraction compares the controlled PA-DOM-01…03 full texts and
retains PA-DOM-04 from the accepted canonical-reuse matrix. It is neither a
general literature search nor a novelty conclusion. The labels mean:

- `SOURCE` — stated in, calculated by, or directly shown in the controlled
  source at the cited location;
- `INFERENCE` — project interpretation of the source-supported material;
- `UNKNOWN` — the controlled source set does not establish the proposition.

An author's assertion of agreement, accuracy, negligible cost, or control
performance remains a `SOURCE` statement about that assertion. It is not
silently promoted to an independently established guarantee. No paper-level
reliability object is identified with DEC-001 `E_cap` or
`F_A(t0,T;μ_t0)` without an explicit feature map.

## Controlled source and copy provenance

| Unit/source | Controlled identity and full text | Integrity/version note | Disposition |
|---|---|---|---|
| PA-DOM-01-A | G. Ya. Krasnikov, A. S. Lushnikov, V. D. Meshchanov, E. S. Rybalko, N. N. Fomicheva, N. A. Shelepin, “Исследование сбоеустойчивости СОЗУ с функцией исправления одиночных сбоев при воздействии ТЗЧ,” *Nanoindustry*, 2018, no. 9 (82), pp. 327–329, DOI `10.22184/1993-8578.2018.82.327.329`; primary publisher full text at the PI-specified URL. | `SOURCE` — identity and pagination agree with the accepted LS report and publisher record. The publisher HTML was read before PA-DOM-01-B. | **ANALYSED — PRIMARY SHORT VERSION; INSUFFICIENT FOR THE THREE-LINK CONTROL TEST ALONE** |
| PA-DOM-01-B | Same title and author order, *Электронная техника. Серия 3: Микроэлектроника*, 2018, no. 1 (169), pp. 68–76; PI-provided PDF. | SHA-256 `80e94fb58c1d79b6ff5ea5b74bdc283a0894f17a3e77f065672eb323a0828cbd`; nine PDF pages. | **ANALYSED — CONDITION TRIGGERED; DECISION-ENABLING EXTENDED TEXT** |
| PA-DOM-02-A | M. V. Podzolko, “Моделирование опасности одиночных сбоев от космических частиц для памяти с коррекцией ошибок,” *Вестник Московского университета. Серия 3. Физика. Астрономия*, 2017, no. 6, pp. 99–106; English publication identity “Modeling of the Risk of Single Event Upsets from Cosmic Particles for Memory with Error Correction,” *Moscow University Physics Bulletin* 72(6), 601–608, DOI `10.3103/S0027134917060133`. | PI-provided Russian original; SHA-256 `35133e369bca534bcc4ff1ce05ffb7e640e58c1671a088c81281ae3eeaf04e19`; eight PDF pages. `SOURCE` — Russian/English title and pagination differ as controlled by LS; extraction cites Russian pp. 99–106. | **ANALYSED — REPRODUCIBLE ANALYTICAL KERNEL; PARTIAL MISSION-NUMERICAL REPRODUCIBILITY** |
| PA-DOM-03-A | A. B. Boruzdina, “Методики экспериментальных исследований многократных сбоев в КМОП микросхемах статических оперативных запоминающих устройств при воздействии отдельных ядерных частиц,” dissertation abstract, НИЯУ МИФИ, 2014; PI-provided PDF. | SHA-256 `66a0903f9b59100e2804b0966206a1ebda1863f784c3ae75e879cf56ebd281ec`; supplied file has 24 PDF pages although the controlled bibliographic description says 25 pages. Title page says Moscow 2014; defence notice states 16 March 2015. | **ANALYSED — REQUIRED RECONSTRUCTION/METHOD SOURCE; COPY-PAGINATION DISCREPANCY RETAINED** |
| PA-DOM-03-B | A. B. Boruzdina, N. G. Grigor’ev, A. V. Ulanova, “Влияние топологического размещения ячеек в микросхемах памяти на кратность сбоев от ТЗЧ,” *Микроэлектроника* 43(2), 88–93, DOI `10.7868/S0544126914020033`; English translation DOI `10.1134/S1063739714020036`. | PI-provided Russian original; SHA-256 `a9e9def7e639bb396128128fc88a934df82abd6f49568dc0456c7ca9dc3cbc50`; six PDF pages. Extraction cites Russian pp. 88–93. | **ANALYSED — REQUIRED TOPOLOGY PAIR MEMBER** |
| PA-DOM-04 | PAPER-005 and `RQ-002_initial_evidence_synthesis.md`. | Accepted canonical artefacts only; the primary PDF was not opened or re-read in this task. | **CLOSED BY CANONICAL REUSE** |

### Conditional opening record for PA-DOM-01-B

> PA-DOM-01-B opened because PA-DOM-01-A does not establish proposition: an
> online rule maps an internally registered/corrected-error observation to a
> current error or radiation-intensity estimate and uses that estimate to
> change `T_scrub` or the regeneration frequency at a defined update time.

This trigger was recorded in the working notes after completing PA-DOM-01-A
and before scientific extraction from PA-DOM-01-B. Pre-trigger access to the
attached B file was limited to file identity and its first-page bibliographic
fields.

## Common comparison matrix

| Comparison field | PA-DOM-01 | PA-DOM-02 | PA-DOM-03 | PA-DOM-04 |
|---|---|---|---|---|
| 1. available input/observation | `SOURCE` — A uses device parameters `N, σ`, fluence `V`, flux density `G`, and selected full-memory regeneration period `T_r`; it does not disclose the complete online observation-to-action chain. B additionally provides a readable single-upset counter and uses the actual count `m_1` collected during the current regeneration cycle. `INFERENCE` — B's operational observation is a corrected-error count over an endogenous window of length `T_r`, not a direct radiation-state measurement. [Trace D1](#trace-d1) | `SOURCE` — total accumulated error count `x(t)`, number of ECC blocks `m`, reporting duration `t`, fixed scan period `t_scan`, device upset cross sections, and modeled particle spectra/fluence. `UNKNOWN` — no online estimator or controller observation is supplied. [Trace D4](#trace-d4) | `SOURCE` — A observes test patterns, error signatures/logical addresses sufficient to form a memory error map, multiplicity and cluster form; irradiation conditions include LET, angle, temperature and mode. B uses physical layout/sensitive-region geometry plus multiplicity and spatial column distributions. `UNKNOWN` — neither source supplies a runtime controller observation. [Trace D7](#trace-d7) | `SOURCE` — available reduced inputs include the LET-dependent mean cross section `σ(Λ)`, particle-flux spectrum `φ(Λ)`, cell area `a_c`, mean multiplicity `m(Λ)` or partial multiplicity probabilities when supplied, and ECC vulnerability coefficients `V_n`. `UNKNOWN` — no online controller observation is established in the accepted scope. [Trace T1](#trace-t1) |
| 2. reconstructed or assumed information | `SOURCE` — Eqs. (4)–(6) reconstruct expected sequential multiple-error words from uniformly and independently accumulated single upsets; B Eqs. (7)–(10) infer a count compatible with the target `M_s` and update `T_r` without a live `G` or `σ` measurement after initialization. `INFERENCE` — the estimate is model-mediated and cycle-aggregated; direct same-parent multiplicity is not separately reconstructed. [Trace D2](#trace-d2) | `SOURCE` — exact occupancy expressions and asymptotic birthday-type formulas reconstruct the probability that at least one block contains more than one, two, or three errors under independent uniform placement. `INFERENCE` — the block occupancy is postulated rather than reconstructed from physical topology or parent-event marks. [Trace D5](#trace-d5) | `SOURCE` — A reconstructs physical parent-event clusters from error-map adjacency while allowing several particle impacts per read cycle; Eqs. (3)–(5) bound false joining using array size and admissible cluster form. B relates sensitive-region arrangement/orientation to physical multiplicity. `UNKNOWN` — a general physical-coordinate-to-logical-address transformation is not disclosed. [Trace D8](#trace-d8) | `SOURCE` — a conditional-on-LET multiplicity conjecture may reconstruct `p_n(Λ)` and hence partial cross sections/rates `R_n`; `V_n` then recombines multiplicity classes into an abstract ECC/system rate. The physical parent-event rate `Σ_n R_n` remains distinct from the bit/upset rate `Σ_n nR_n`. `INFERENCE` — this conditional multiplicity model must not be re-described as a temporal Poisson-arrival model. [Trace T2](#trace-t2) |
| 3. uncertainty/error and validity domain | `SOURCE` — Eq. (5) assumes `m≪N`; for the 4-Mbit example the authors state about 1% formula error for `m<1000`. A reports a slightly different “less than 0.5%” summary. B reports a 50%-confidence cross-section interval whose bounds differ by 1.2 and hence a factor 1.44 in `M_s`, plus statistical and flux-nonuniformity errors. `INFERENCE` — this uncertainty is not propagated through the online update law; the validation covers the tested 0.24-µm SOI SRAM and heavy-ion conditions, not arbitrary targets. [Trace D3](#trace-d3) | `SOURCE` — `1≪x≪m`, independent uniform placement, approximately uniform accumulation inside a mission interval, and repeated equivalent scan intervals are required. The paper notes that its triple-independence approximation is not exact but numerically close. `UNKNOWN` — parameter confidence intervals and end-to-end uncertainty propagation are not supplied. [Trace D6](#trace-d6) | `SOURCE` — A bounds false joining, conditional on a specified maximum multiplicity/form and uniform position reasoning, by Eqs. (3)–(5); it reports up to 20-fold test-time reduction. B's domain is the analyzed layouts/technologies and irradiation evidence. `UNKNOWN` — false separation of one parent event, a complete classification confusion model, and confidence intervals are not quantified. [Trace D9](#trace-d9) | `SOURCE` — the Poisson multiplicity law is a conjecture; the illustrated cross-section interpolation is approximate; the simple SEC-DED conversion requires `β≪1`, neglects `n≥3` contributions in Eqs. (17)–(18), and assumes that one half of two-fold MCUs enters one word. No parameter confidence intervals are propagated end to end. `INFERENCE` — Eq. (15) is an approximate additive construction, and its direct and sequential addends are not proved to be disjoint. `UNKNOWN` — no numerical validity boundary or error bound outside `β≪1` is established. [Trace T3](#trace-t3) |
| 4. position relative to `W` | `SOURCE` — the model works with `N` ECC words and assumes uniform placement of single errors among them; no physical-cell-to-codeword map, topology, or interleaving is specified. `INFERENCE` — this is an implicit statistical post-`W` occupancy model, not a controlled explicit `W`. [Trace D2](#trace-d2) | `SOURCE` — errors are assigned uniformly to `m` ECC blocks. The paper later identifies same-particle neighboring-bit MBU as a limitation and mentions interleaving/stronger codes, but does not map measured physical events through an explicit `W`. [Trace D5](#trace-d5) | `SOURCE` — A distinguishes physical neighboring-cell MC from logical MC in one block and treats spatial separation/interleaving as the transformation between them; B explains why layout and mutual orientation affect physical multiplicity. `INFERENCE` — outputs are upstream of target `W`; the pair motivates testing information sufficiency but does not prove that full topology is always necessary. [Trace D8](#trace-d8) | `SOURCE` — physical multiplicity is partitioned before logical mapping. No explicit physical-cell-to-codeword map or topology is supplied; the later word-level conversion uses a statistical one-half allocation for two-fold events rather than an explicit `W`. `INFERENCE` — the scalar allocation is not a universal mapping and is insufficient for arbitrary target organizations without additional post-mapping information. [Trace T4](#trace-t4) |
| 5. ECC reliability object and horizon | `SOURCE` — the 4-Mbit device uses a 39-bit Hsiao SEC-DED word (32 data plus seven check bits): one error is corrected; two or more in the read word assert `MERR`. The model's object is expected/allowed multiple-error-word count `M_s` over `T_s`, or frequency `f_0`, under periodic sequential regeneration. `INFERENCE` — this is neither a complete decoder-outcome distribution nor DEC-001 `F_A`; the formula collapses word-age phase and implies corrected cycles rather than arbitrary `μ_t0`. [Trace D1](#trace-d1) | `SOURCE` — the object is the probability of more than `c` errors in at least one block over `t`, with examples for SEC-DED and stronger thresholds. Under scanning, singles are corrected; detected doubles cause reboot and memory rewrite in the described SEC-DED scenario. `INFERENCE` — “uncorrectable or undetectable” threshold events are not a complete DUE/SDC/miscorrection semantics and are not automatically `E_cap`/`F_A`. [Trace D4](#trace-d4) | `SOURCE` — the pair characterizes physical and logical multiple upsets and discusses interleaving/correction qualitatively. `UNKNOWN` — no ECC reliability probability, decoder outcome, mission horizon, `μ_t0`, or DEC-001-compatible aggregate is calculated. [Trace D7](#trace-d7) | `SOURCE` — Eqs. (13)–(14) define an abstract `R_syst` rate through multiplicity vulnerabilities, while Eqs. (15)–(19) give one simple SEC-DED illustration over an exogenous scrub interval `t_s` in the low-`β` regime. `INFERENCE` — the illustration implies a corrected/clean cycle start rather than a general `μ_t0`; neither `R_syst` nor the one-interval expression is DEC-001 `F_A(t0,T;μ_t0)` or automatically `E_cap`, DUE, SDC, miscorrection, or system-visible failure. [Trace T5](#trace-t5) |
| 6. restoration action and decision law | `SOURCE` — A sizes/sweeps regeneration frequency and describes MASTER/SLAVE control but does not give the complete online rule. B initializes from estimated `G,σ,M_s,T_s`, counts `m_1` in each full regeneration cycle, and if it changes computes `m_2` and `T_r2` using Eqs. (7)–(10), then applies the new period. `INFERENCE` — B is reactive online adaptation at one-complete-cycle updates, not forecast-driven control; update latency is at least the completed observation cycle. `UNKNOWN` — saturation, hysteresis, hard min/max periods, counter reset details, and delayed/noisy-decision logic are not specified. [Trace D1](#trace-d1) | `SOURCE` — `t_scan` is fixed externally; background scans read all memory, repair singles, and a detected double initiates restart/rewrite. Formulas sweep or size risk as a function of `t_scan`. `INFERENCE` — this is a fixed periodic-restoration baseline, not an optimized or adaptive period law; scan order and sequential word-age phase are collapsed. [Trace D4](#trace-d4) | `UNKNOWN` — no operational scrub/writeback controller or `T_scrub` decision law is present. The experimentally varied read-cycle/fluence conditions concern event reconstruction, not runtime restoration control. [Trace D7](#trace-d7) | `SOURCE` — `t_s` is an exogenous scrub interval in a simple SEC-DED approximation; operational scan, correction/writeback, and sequential word-age semantics are not modeled. `UNKNOWN` — the accepted scope provides no adaptive action set, update rule, online estimator, or law selecting `T_scrub`. [Trace T6](#trace-t6) |
| 7. reliability guarantee/constraint | `SOURCE` — B takes allowable `M_s` over `T_s` as an input and claims its loop maintains that level within the model; testing compares measured and calculated `M_s`. `INFERENCE` — this is not a confidence-qualified DEC-001 chance constraint or formal guarantee, especially with unpartitioned direct MCU, uncertain `σ`, and endogenous observation windows. [Trace D3](#trace-d3) | `SOURCE` — the formulas return probabilities for occupancy thresholds under stated assumptions; no numerical target requirement is optimized or enforced. `UNKNOWN` — no DEC-001-compatible guarantee under model/parameter uncertainty is supplied. [Trace D6](#trace-d6) | `UNKNOWN` — no windowed ECC reliability constraint or control guarantee is supplied. `INFERENCE` — bounds on false event joining constrain experimental classification, not operational `F_A`. [Trace D9](#trace-d9) | `SOURCE` — `β≪1` is a validity condition for the illustrative approximation. `INFERENCE` — it is not a project reliability requirement and must not be interpreted as `H_req` or `ε_req`. `UNKNOWN` — no DEC-001-compatible windowed reliability constraint or guarantee is provided in the accepted scope. [Trace T7](#trace-t7) |
| 8. resource-cost treatment | `SOURCE` — sequential regeneration makes the SRAM unavailable for read/write at the addressed word; B defines relative unavailability `t_r/(T_r/N)` and Eq. (11), reporting 0.003% for one example. `INFERENCE` — this is a service-interruption/interface-occupancy proxy, not a complete RQ-005 vector. `UNKNOWN` — energy, bandwidth, controller/area overhead, and information-acquisition cost are not quantified. [Trace D3](#trace-d3) | `SOURCE` — the paper cites peak/average SDRAM bandwidth and asserts that a scan lasting tens of minutes has negligible performance impact; SEC-DED storage overhead is described qualitatively. `UNKNOWN` — scan operations, occupancy, energy, latency distribution, and controller cost are not measured. [Trace D6](#trace-d6) | `SOURCE` — A reports experimental acquisition-time reduction (fourfold to twentyfold in examples). `INFERENCE` — that is an information-acquisition/test cost, not an operational scrub-resource benefit. `UNKNOWN` — operational bandwidth, energy, latency, and controller hardware cost are absent. [Trace D9](#trace-d9) | `SOURCE` — the accepted synthesis characterizes the rate sums as closed-form and computationally inexpensive. `INFERENCE` — compact analytical form or computational simplicity is not a measured resource benefit. `UNKNOWN` — no RQ-005 resource-cost vector, controller overhead, bandwidth, energy, latency, or disturbance measurement is provided. [Trace T8](#trace-t8) |
| 9. exact distinction affecting the next RQ-007 method or experiment | `INFERENCE` — PA-DOM-01-B occupies a concrete reactive `internal corrected-error count → model-mediated period update` comparator and a narrow unavailability metric, but it does not separate direct same-parent exceedance, propagate uncertainty, or establish best-fixed/full-information/robust comparators. A alone is only a model/test and configurable-restoration source. [Trace D3](#trace-d3) | `INFERENCE` — PA-DOM-02 supplies the mandatory independent-error, uniform-occupancy, fixed-period restoration baseline; its direct-MBU exclusion makes it unsuitable as the sole applicability-domain model. [Trace D6](#trace-d6) | `INFERENCE` — PA-DOM-03 is an upstream event-reconstruction/topology comparator: it shows which parent-event and spatial information may be retained before `W` and bounds one false-joining mechanism, but does not determine `F_A` or select restoration. [Trace D9](#trace-d9) | `INFERENCE` — PAPER-005 is an upstream reconstruction/rate comparator occupying a conditional multiplicity-reconstruction approach from reduced physical inputs. It is not an integrated `information → F_A → adaptive T_scrub` baseline. Whether its recovered information is sufficient for target `W`, DEC-001 `F_A`, and restoration selection remains a downstream open question. [Trace T9](#trace-t9) |

## PA-DOM-01 targeted extraction

### Three-link control test and A/B relationship

| Proposition | PA-DOM-01-A | PA-DOM-01-B | Disposition |
|---|---|---|---|
| a. Periodically registered/corrected-error observation | `UNKNOWN` — the short article establishes periodic correction and test measurements but does not disclose the internal per-cycle observation used by an online law (pp. 327–329). | `SOURCE` — the architecture includes a single-upset counter; step 2 of the algorithm counts actual `m_1` in the current regeneration cycle (Table 1, pp. 70, 74). | Established only by B for the control chain. |
| b. Current error/radiation-intensity estimate from that observation | `UNKNOWN` — `G` is an external irradiation/environment parameter; no internal count-to-state estimator is given (pp. 327–329, Eq. (3)). | `SOURCE` — Eqs. (7)–(10) use `m_1`, the preceding model state, target `M_s,T_s`, and initialized `σ,G` to compute a compatible `m_2` and new period; the authors emphasize that operational use avoids direct determination of effective cross section and particle flux (pp. 74–75). `INFERENCE` — the latent object is a model-compatible error-count/intensity surrogate, not an independently calibrated radiation-state estimate. | Established as model-mediated reactive estimation by B; no forecast. |
| c. Online rule changing `T_r` | `UNKNOWN` — MASTER/SLAVE programmability and dependence on flux do not by themselves establish an online update rule (pp. 327–329). | `SOURCE` — if `m_1≠m`, steps 3–5 compute `m_2,T_r2`, assign them as the new state, and repeat; Fig. 4 shows the feedback loop (pp. 74–75, Eqs. (7)–(10), Fig. 4). | Established by B; update occurs after a complete regeneration/observation cycle. |

`INFERENCE` — B is a substantive extension for the RQ-007 comparison: it
contains the full feedback algorithm, exact equations, architecture tables,
uncertainty discussion, and the unavailability calculation absent from A.
The two texts share title, author group, device, core model, and test family,
so A is consistent with a condensed version of B. `UNKNOWN` — neither source
explicitly declares the formal publication relationship as reissue,
translation, or derivative version; “duplicate” must not be asserted from
feature overlap alone.

### Reproduction sheet

`SOURCE` — the analytical and controller core is:

\[
M_r=\frac{m(m-1)}{2N}, \tag{4}
\]

\[
M_s=\frac{VG\sigma^2}{2N}T_r\left(1-\frac{T_1}{T_r}\right),
\qquad T_1=\frac{1}{G\sigma}, \tag{5}
\]

\[
f_0=\frac{1}{2}\left(1-\frac{T_1}{T_r}\right)
f_{OC}^{2}\frac{T_r}{N}, \tag{6}
\]

\[
m=1+\frac{2N}{\sigma T_s}\frac{M_s}{G},\qquad
G=\frac{m}{\sigma T_r},\qquad
T_r=\frac{T_s}{2M_sN}m(m-1), \tag{7–9}
\]

\[
m_2=1+\frac{2NM_sT_r}{m_1T_s}, \tag{10}
\]

\[
t_r=\frac{2M_s}{G^2\sigma^2T_s}. \tag{11}
\]

Locations: PA-DOM-01-B pp. 68–69 (Eqs. (1)–(6)), pp. 74–75
(Eqs. (7)–(11), Fig. 4). Inputs needed for the model/controller reproduction
are `N`, `σ`, target `M_s` over `T_s`, initialization `G`, current `T_r`, and
per-cycle count `m_1`; implementation also needs the regeneration address
counter, period generator/control register, single-upset counter, ECC, and
`MERR` interface (Table 1, p. 70).

- `SOURCE` — correction is sequential, one address at a time, and interrupts
  ordinary read/write for the address operation; the tested address operation
  is 100 ns (pp. 70, 75).
- `UNKNOWN` — the scan order, precise single-upset-counter reset boundary,
  saturation/rounding of `T_r`, minimum/maximum period, and handling of
  delayed/noisy counts are not specified.
- `SOURCE` — step 4 says that `T_r2` is calculated “in (7),” although Eq. (9),
  not Eq. (7), explicitly gives `T_r` as a function of `m`. Fig. 4 groups
  calculation of `m_2` and `T_r2` without resolving the cross-reference
  (pp. 74–75). This internal reference ambiguity must be resolved before a
  literal implementation.
- `SOURCE` — the demonstrated irradiation comparison is for a 0.24-µm CMOS
  SOI 4-Mbit SRAM with internal 131072×39 Hsiao SEC-DED organization under
  specified Xe/Kr tests (pp. 69–73, Tables 1 and 4, Figs. 1–3).
- `INFERENCE` — the model represents sequential independent accumulation of
  single-cell errors into an ECC word. It does not supply a separate rate for
  one-parent physical MCU and therefore does not expose a `T_r`-independent
  direct-event floor. Any direct/accumulation recombination is absent rather
  than proved exact or disjoint.

## PA-DOM-02 targeted extraction

### Reproducible independent-error periodic-restoration kernel

`SOURCE` — for `x` independent errors placed uniformly among `m` memory
blocks, the paper gives exact occupancy expressions and the following
approximations for at least one block exceeding capability thresholds
(pp. 102–103, Eqs. (1)–(3a)):

\[
P_m^x(>1)=1-\frac{A_m^x}{m^x}, \tag{1}
\]

\[
P_m^x(>2)=1-\frac{1}{m^x}
\sum_{j=0}^{\lfloor x/2\rfloor}
\frac{A_m^{x-j}A_x^{2j}}{2^j j!}, \tag{2}
\]

\[
P_m^x(>3)=1-\frac{1}{m^x}
\sum_{j=0}^{\lfloor x/3\rfloor}
\frac{A_m^jA_x^{3j}}{(3!)^j j!}
N_{m-j}^{x-3j}(\le 2), \tag{3}
\]

where `A_m^x=m(m-1)…(m-x+1)` and
`N_{m-j}^{x-3j}(≤2)` is the previously constructed count of allocations with
at most two errors per remaining block. The corresponding approximations are:

\[
P_m^x(>1)\approx 1-\exp\!\left(-\frac{x^2}{2m}\right),
\]

\[
P_m^x(>2)\approx 1-\exp\!\left(-\frac{x^3}{3!m^2}\right),
\]

\[
P_m^x(>3)\approx 1-\exp\!\left(-\frac{x^4}{4!m^3}\right).
\]

For fixed periodic scanning, the paper sets approximately uniform
accumulation `x(t')≈x(t_scan)t'/t_scan` inside each interval and obtains
(p. 103):

\[
P_m^x(>1,t)\approx
1-\exp\!\left[-\frac{x(t)^2(t_{scan}/t)}{2m}\right],
\]

\[
P_m^x(>2,t)\approx
1-\exp\!\left[-\frac{x(t)^3(t_{scan}/t)^2}{3!m^2}\right].
\]

`SOURCE` — the exact formulas count occupancy arrangements; the approximations
assume `1≪x≪m`. The paper explicitly notes that the product-of-triples
argument is not fully independent, while reporting close numerical agreement
with the exact expression (pp. 102–103).

| Reproduction feature | Extraction |
|---|---|
| Event/metric | `SOURCE` — probability that at least one ECC block contains more than one, two, or three accumulated errors over `t`; dimensionless, array-level aggregate over `m` blocks (pp. 102–104). |
| Initial state and repair | `SOURCE` — background SEC-DED scanning corrects singles; a double-error indication causes restart and memory rewrite in the described scenario (p. 103). `INFERENCE` — repeated identical intervals imply a clean post-repair cycle state. `UNKNOWN` — arbitrary `μ_t0`, partial repairs, scan order, and per-word phase are not represented. |
| Arrival/statistics | `SOURCE` — independent, uniformly distributed error placement; approximately uniform accumulation over the selected time interval; repeated scan intervals are combined by `1-[1-P(t_scan)]^{t/t_scan}` (pp. 102–103). `INFERENCE` — no explicit continuous-time HPP/NHPP is estimated. |
| Direct MCU/MBU | `SOURCE` — same-particle neighboring-bit MBU is discussed as a practical limitation and a reason for interleaving/stronger codes, but is outside the independent uniform-occupancy formulas (pp. 104–105). `INFERENCE` — the baseline has no direct-event floor and no direct/accumulation recombination. |
| Mapping/ECC | `SOURCE` — logical blocks receive errors uniformly; the principal numerical example uses 64 data bits plus SEC-DED check bits and `m=2^24` blocks, while stronger correction thresholds are also analyzed (pp. 100–104). `UNKNOWN` — explicit physical `W`, interleaving, decoder miscorrection and service outcomes are absent. |
| Environment inputs | `SOURCE` — device cross-section parameterizations are convolved/integrated with modeled proton/heavy-ion energy/LET, time, angle and shielding environments using COSRAD-related calculations; flare fluence is distributed over a day and trapped-particle exposure over a month in the examples (pp. 99–101, 103–105, Figs. 1–4, Tables 1–2). |
| Period selection | `SOURCE` — numerical calculations use a fixed two-hour scan and cite a 20-minute RAD750 practice point; probability depends explicitly on `t_scan` (pp. 103–105). `INFERENCE` — the paper sizes/sweeps a fixed parameter but provides no optimizer, estimator, or adaptive update. |
| Validation/uncertainty | `SOURCE` — approximations are numerically compared with exact combinatorics; mission examples are calculated scenarios. `UNKNOWN` — no end-to-end empirical validation or propagated input confidence intervals are provided. |
| Resource treatment | `SOURCE` — peak/average SDRAM bandwidth is cited and the performance impact of scans lasting tens of minutes is asserted negligible; ECC storage overhead is described (pp. 100–101, 104). `UNKNOWN` — no measured operational cost vector. |

**Reproducibility disposition.** `INFERENCE` — the independent-error
periodic-restoration analytical kernel is reproducible when `m`, `x(t)`, ECC
threshold and `t_scan` are supplied. Reproducing every mission number is
`PARTIAL`: exact software configuration, all spectra/transport settings and
all device-fit inputs required to recreate Tables 1–2 are not fully specified
in the paper. This does not block use of the equations as a mandatory fixed
baseline.

## PA-DOM-03 mandatory-pair extraction

### Definitions, reconstruction, and topology

| Proposition | PA-DOM-03-A dissertation abstract | PA-DOM-03-B topology article |
|---|---|---|
| Physical versus logical MC | `SOURCE` — an MC is upset of two or more logical elements by one nuclear particle; physical MC affects physically neighboring cells, whereas logical MC affects cells in one logical block (pp. 3–4). | `SOURCE` — spatial separation of cells from one logical word can turn one physical neighboring-cell MC into single errors in different logical words (pp. 88, 90–91). |
| Parent-event reconstruction | `SOURCE` — one impact per read cycle gives unambiguous association; the accelerated method permits `k` errors per cycle and groups neighboring positions by the admissible multiplicity/form, with a false-MC bound (pp. 11–13, Eqs. (3)–(5), Figs. 5–7). | `UNKNOWN` — no read-window grouping rule or classification-error model is given. |
| Observed information | `SOURCE` — test pattern, error signature/logical address, memory error map, multiplicity and shape; test conditions include LET, angle, temperature, pattern and dynamic/static mode (pp. 10–20). | `SOURCE` — physical sensitive-region layout/orientation and experimental multiplicity/spatial-column distributions are analyzed (pp. 88–93, Figs. 3–6). |
| False joining/separation | `SOURCE` — Eqs. (3)–(5) bound false joining of independent impacts into a neighboring-cell cluster. `UNKNOWN` — false separation of one physical event, within-window timing and a full confusion matrix are not quantified. | `UNKNOWN` — neither error is quantified. |
| `W` and retained dependence | `SOURCE` — physical versus logical MC and the role of separation are explicit, but the complete map from reported address to physical coordinate and target codeword is not supplied. | `SOURCE` — topology controls physical multiplicity and interleaving changes logical consequences; no target `W` is instantiated. `INFERENCE` — both outputs are upstream of `W`. |
| Operational risk/control | `UNKNOWN` — no `F_A`, decoder-outcome model, scrub law, or operational cost is supplied. | `UNKNOWN` — no `F_A`, decoder-outcome model, scrub law, or operational cost is supplied. |

`SOURCE` — the registered experimental identifier in A is a test-access
address/error position used to construct an information map (pp. 10–13,
Figs. 5–7). `INFERENCE` — it is therefore not automatically a physical-cell
coordinate or a target ECC-codeword identifier. Converting it to either object
requires the array organization/layout map that the abstract does not specify.
The read-cycle boundary is retained, but `UNKNOWN` — individual impact times
inside a cycle are not observed or reported.

`SOURCE` — PA-DOM-03-A controls the accelerated false-joining condition as
(pp. 12–13):

\[
k\le \frac{e(MN)}{x}+1, \tag{3}
\]

where `k` is the number of upset cells per read cycle, `M` bits per word, `N`
addresses, `e` the admissible fraction of false MC, and `x` a quantity set by
maximum multiplicity and cluster form. For a candidate neighboring position:

\[
p_{false}(n_{max})\le\frac{z}{MN}, \tag{4}
\]

and for the `i`-th upset:

\[
p_{false}^{\,i}(n_{max})\le\frac{z(i-1)}{MN}. \tag{5}
\]

Here `z` is the number of positions able to complete an allowed false cluster;
it depends on maximum multiplicity and form. `INFERENCE` — these are
classification-control bounds under the stated spatial occupancy construction,
not confidence intervals for radiation cross sections and not an operational
reliability guarantee.

`SOURCE` — B compares four 0.13-µm 6T-cell layouts and shows that sensitive
region area alone is insufficient: orientation and separation can make compact
layouts more MCU-sensitive (pp. 90–91, Figs. 3–4). Its 256-Kbit SRAM example
relates measured two-/threefold multiplicity and error-column periodicity to
physical regions and power-bus placement (pp. 91–93, Figs. 5–6).
`INFERENCE` — the strongest controlled pair proposition is that an error map
plus admissible cluster shape/multiplicity can retain a bounded reconstruction
of physical parent-event multiplicity before `W`, while the layout paper shows
that the resulting multiplicity/form is topology-dependent. The pair does not
show that full physical topology is always required, nor that those upstream
outputs alone determine DEC-001 `F_A`.

## PA-DOM-04 canonical-reuse guard

PA-DOM-04 remains **CLOSED BY CANONICAL REUSE**. Its nine matrix entries and
Trace T1–T9 below are retained from the accepted matrix. The source PDF and
PAPER-005 were not re-read in this task; only cross-unit synthesis links were
added.

## Traceability ledger — PA-DOM-01…03

### Trace D1

- PA-DOM-01-A: *Nanoindustry* pp. 327–329, model Eqs. (1)–(3), device and
  MASTER/SLAVE regeneration descriptions, Fig. 1.
- PA-DOM-01-B: pp. 68–70, Eqs. (1)–(6), Table 1; pp. 74–75, Eqs. (7)–(11),
  Fig. 4 and algorithm steps 1–5.

### Trace D2

- PA-DOM-01-B: pp. 68–69, Eqs. (4)–(6), definitions of `N,σ,V,G,T_r,T_s`;
  pp. 74–75, Eqs. (7)–(10).
- PA-DOM-01-A: pp. 327–329, condensed Eq. (3) and model assumptions.

### Trace D3

- PA-DOM-01-B: pp. 69–73, device/test domain, Tables 1 and 4, Figs. 1–3;
  pp. 73–74, uncertainty discussion; p. 75, Eq. (11), unavailability example
  and conclusion.
- PA-DOM-01-A: pp. 328–329, validation and formula-error statement.

### Trace D4

- PA-DOM-02-A: Russian pp. 100–103, ECC descriptions and Eqs. (1)–(3a);
  p. 103, fixed-scan combination and scan semantics.

### Trace D5

- PA-DOM-02-A: Russian pp. 102–103, occupancy derivations and approximations;
  pp. 104–105, numerical memory organization and MBU/interleaving limitation.

### Trace D6

- PA-DOM-02-A: Russian pp. 99–101 and 103–105, environment/device inputs,
  Figs. 1–4 and Tables 1–2; p. 104, bandwidth/performance statement; p. 105,
  domain limitations and conclusion.

### Trace D7

- PA-DOM-03-A: supplied-PDF pp. 3–6, definitions/objectives; pp. 10–20,
  experimental conditions, apparatus, test modes, maps and outputs.
- PA-DOM-03-B: Russian pp. 88–93, physical/logical discussion, Figs. 3–6.

### Trace D8

- PA-DOM-03-A: supplied-PDF pp. 11–13, Eqs. (3)–(5), Figs. 5–7; pp. 14–20,
  logical-MC method and experimental outputs.
- PA-DOM-03-B: Russian pp. 88, 90–93, interleaving discussion, layout analysis,
  Figs. 3–6.

### Trace D9

- PA-DOM-03-A: supplied-PDF pp. 11–13, false-joining bound and reported test
  acceleration; pp. 18–20, technology/irradiation results.
- PA-DOM-03-B: Russian pp. 89–93, model/technology domain and experimental
  example; no reported confidence interval or grouping-error model.

## Traceability ledger — retained PA-DOM-04

### Trace T1

- PAPER-005: Common extraction summary (`Count/arrival process`,
  `Stationarity/intensity`); §6 `Input parameters`; §§9.1–9.2, Eqs. (1)–(14),
  source pp. 1–4 as already controlled.
- RQ-002 synthesis: §3 `Common extraction matrix — process and event
  representation`; §9 `Incompatible aggregation levels`.

### Trace T2

- PAPER-005: §4 `Method`; §7 `Output parameters`; §§9.1–9.2, especially Eqs.
  (3)–(5), (8)–(11), and (13)–(14), source pp. 1–4 as already controlled; §15
  `What cannot legitimately be claimed`.
- RQ-002 synthesis: §3; §7 `Different definitions that must not be merged`; §9.

### Trace T3

- PAPER-005: §5 `Assumptions`; §§11–13; Mandatory questions 3, 7–11, and
  14–15 on Eqs. (15)–(19), source p. 4 as already controlled.
- RQ-002 synthesis: §5 `Common extraction matrix — evidence, validity, and
  contract fit`; §8 `Incompatible assumptions`; §11 work-unit WU1; §14
  `Alternatives narrowed or ruled insufficient as stand-alone models`.

### Trace T4

- PAPER-005: Common extraction summary (`Mapping W`); §§9.1 and 9.3; §§12 and
  18; Mandatory questions 6, 8, and 13, Eqs. (17)–(18), source p. 4 as already
  controlled.
- RQ-002 synthesis: §4 `Common extraction matrix — mapping, state, and repair`;
  §8; §12 `Unresolved model-selection gaps`.

### Trace T5

- PAPER-005: §7; §§9.2–9.3, Eqs. (13)–(19), source p. 4 as already controlled;
  §§13–16; Mandatory questions 1–2 and 10–11.
- RQ-002 synthesis: §5; §§9–10; §14.

### Trace T6

- PAPER-005: Common extraction summary (`Repair semantics`); §§3 and 6; §9.3,
  Eqs. (15)–(19), source p. 4 as already controlled; §§16 and 19.
- RQ-002 synthesis: §4; §10 `Incompatible horizons`; §12.

### Trace T7

- PAPER-005: §§5, 11, and 15; Mandatory questions 10–11, Eqs. (16)–(19), source
  p. 4 as already controlled.
- RQ-002 synthesis: §5; §14.

### Trace T8

- PAPER-005: §4; §9; §16.
- RQ-002 synthesis: §5 (`Computational tractability`); §12, gap 9.

### Trace T9

- PAPER-005: §§14–16; §§18–19.
- RQ-002 synthesis: §§12–15; §17 `Orchestrator disposition and downstream
  gate`.

## 1. Occupied method chains

- `SOURCE`/`INFERENCE` — PA-DOM-01-B occupies
  `internal per-cycle corrected-single count m_1 → model-compatible count update
  → reactive T_r update`, initialized from external `G,σ` and constrained by an
  allowed expected multiple-error count `M_s` over `T_s` (B pp. 74–75,
  Eqs. (7)–(10), Fig. 4). It is a control-layer comparator, not a complete
  DEC-001 reliability controller.
- `SOURCE`/`INFERENCE` — PA-DOM-02 occupies
  `environment/device upset total x(t) → independent uniform ECC-block
  occupancy → fixed periodic global restoration → threshold-exceedance
  probability` (pp. 99–105, Eqs. (1)–(3a) and scan formulas). It is the fixed
  independent-accumulation baseline.
- `SOURCE`/`INFERENCE` — PA-DOM-03 occupies
  `irradiation error map → bounded spatial parent-event reconstruction →
  physical multiplicity/form`, while B adds
  `layout/sensitive-region geometry → physical multiplicity/topology` (A
  pp. 11–20, Eqs. (3)–(5); B pp. 88–93). This is upstream of target `W`.
- `SOURCE`/`INFERENCE` — PA-DOM-04 occupies
  `reduced LET-dependent physical inputs → conditional multiplicity
  reconstruction → partial rates → abstract ECC vulnerability recombination`,
  plus a separately qualified low-`β` scrub illustration (Trace T1–T9).
- `INFERENCE` — no unit occupies the complete common chain
  `controlled direct+accumulation model → explicit W/ECC → general F_A with
  μ_t0 → uncertainty-aware comparison of best fixed, full-information adaptive,
  and information-limited robust restoration → separated resource costs`.

## 2. Mandatory baselines for the next quantitative work

| Baseline/comparator | Required retained scope |
|---|---|
| PA-DOM-02 fixed baseline | `INFERENCE` — reproduce the exact/approximated independent uniform-occupancy kernel and fixed `t_scan` repair semantics; make its exclusion of same-parent MCU explicit. Do not import its numerical two-hour setting as a requirement. |
| PA-DOM-01-B reactive comparator | `INFERENCE` — reproduce the internal corrected-count observation, one-cycle update cadence, Eqs. (7)–(10), sequential regeneration, and Eq. (11) unavailability proxy; test the Eq. (7)/(9) cross-reference and add explicit bounds/uncertainty rather than silently repairing them. |
| PA-DOM-03 reconstruction/topology comparator | `INFERENCE` — preserve the false-joining bound and at least one representation retaining parent-event multiplicity/form before `W`; compare reductions without claiming that full topology is universally required. |
| PA-DOM-04 reduced-input comparator | `INFERENCE` — preserve physical-event versus bit-rate distinction and Eqs. (2)–(14); use Eqs. (15)–(19) only with their low-`β`, scalar-mapping and additivity qualifications. |

## 3. Mandatory design boundaries and prohibited generic claims

- `INFERENCE` — changing flux, selectable hardware frequency, a parametric
  `T_scrub` sweep, and online adaptation are different propositions; only
  PA-DOM-01-B discloses a feedback update among these sources.
- `INFERENCE` — do not claim shorter `T_scrub` removes a direct same-parent
  capability exceedance; PA-DOM-01/02 do not model that floor, PA-DOM-03
  measures/reconstructs its upstream cause, and PA-DOM-04 only approximates
  recombination.
- `INFERENCE` — do not equate `M_s`, `f_0`, Podzolko's threshold probability,
  physical MCU cross section, or `R_syst` with DEC-001 `F_A` without domain,
  horizon, initial-state, mapping and decoder-outcome reconciliation.
- `INFERENCE` — do not treat uniform logical occupancy, an interleaving
  statement, or PA-DOM-04's scalar one-half as a universal `W`.
- `INFERENCE` — do not infer a full RQ-005 benefit vector from fewer scrub
  operations, one unavailability fraction, a qualitative bandwidth claim, or
  analytical compactness.
- `INFERENCE` — do not claim richer information, adaptation, or shorter
  `T_scrub` is always beneficial; the future comparison must include its
  acquisition and controller cost and its domain of usefulness.

## 4. Assumptions to reproduce, parameterize, or test

- PA-DOM-01: `SOURCE` — `m≪N`, uniform/independent accumulation, constant or
  piecewise interpreted flux during a cycle, cycle-aggregated observation,
  sequential address repair, and the stated cross-section uncertainty
  (B pp. 68–75). `UNKNOWN` — direct-MCU rate, counter reset, period bounds and
  decision latency/noise policy require target parameters.
- PA-DOM-02: `SOURCE` — `1≪x≪m`, uniform independent placement, approximately
  uniform time accumulation, equivalent fixed scan intervals and clean repair
  (pp. 102–103). `UNKNOWN` — direct-event contribution, explicit `W`, arbitrary
  initial state and mission-input uncertainty require tests/parameters.
- PA-DOM-03: `SOURCE` — admissible cluster form/max multiplicity, array size,
  spatial occupancy model and read-cycle grouping determine the false-join
  bound (A pp. 11–13). `UNKNOWN` — false splitting, address-to-physical mapping,
  timing inside the observation window and transfer to target technology.
- PA-DOM-04: retain the accepted conditional multiplicity, interpolation,
  scalar one-half, `n≥3` omission and low-`β` assumptions (Trace T3–T4).

## 5. Minimum RQ-003 interface

- `INFERENCE` — supply a target-declared codeword/block, correction capability
  `c`, and decoder outcomes that distinguish corrected operation, detected
  uncorrectable events, miscorrection and silent corruption. PA-DOM-01's Hsiao
  SEC-DED `MERR`, PA-DOM-02's occupancy threshold, and PA-DOM-04's vulnerability
  coefficients are not interchangeable outcome semantics.
- `INFERENCE` — the interface must accept both a one-parent post-`W` joint mark
  and accumulated per-codeword state so that controllable and
  `T_scrub`-independent risk components are not conflated.

## 6. Minimum RQ-004 interface

- `SOURCE`/`INFERENCE` — PA-DOM-01-B establishes a minimum observable candidate:
  corrected single-error count per completed regeneration cycle, together with
  the current cycle length and controller state (pp. 70, 74–75). Because the
  window length changes with `T_r`, exposure normalization and update latency
  must be explicit.
- `INFERENCE` — external/test-derived `G,σ`, physical event/multiplicity
  information from PA-DOM-03/04, and internal corrected-error counts are
  distinct information channels; their timestamps, uncertainty and loss under
  aggregation must not be merged.
- `UNKNOWN` — none of the units provides a validated forecast, observation
  confusion model covering both false join and false split, or uncertainty
  propagation from observation to action.

### Information retained and lost before downstream reliability

| Unit | Retained information | Aggregated or discarded information |
|---|---|---|
| PA-DOM-01 | `SOURCE` — total corrected-single count for the current regeneration cycle and persistent model/controller state `m,T_r`. | `INFERENCE` — address, syndrome/topology, within-cycle timing and parent-event provenance are collapsed into `m_1`; direct multiplicity cannot be recovered from the controller input. |
| PA-DOM-02 | `SOURCE` — total error count `x(t)`, logical block count `m`, threshold and fixed scan interval. | `INFERENCE` — physical address/topology, parent event, joint mark and within-interval word age are discarded by the uniform occupancy reduction. |
| PA-DOM-03 | `SOURCE` — during diagnosis A retains an error map, address/pattern, multiplicity/form and read-cycle grouping; B retains analyzed layout and spatial/multiplicity distributions. | `INFERENCE` — reducing these observations to marginal multiplicity/cross section loses raw event-map and joint spatial detail. `UNKNOWN` — target `W` and within-cycle event times cannot be recovered from the supplied pair. |
| PA-DOM-04 | `SOURCE` — reduced mean cross section, multiplicity-related inputs and partial rates are retained. | `INFERENCE` — explicit topology, physical-cell-to-codeword association and the full post-`W` joint mark are not retained in the accepted reduced-input representation. |

## 7. Minimum RQ-005 interface

- `INFERENCE` — retain a vector containing at least scrub reads/writes,
  memory-interface occupancy/service interruption, bandwidth/latency,
  energy/power and controller/hardware overhead. PA-DOM-01 Eq. (11) supplies
  only a service-unavailability component; PA-DOM-02 supplies only a qualitative
  bandwidth/performance statement.
- `INFERENCE` — retain information-acquisition cost separately: PA-DOM-03-A's
  reduced irradiation/test time is an acquisition-cost result, not an
  operational scrub benefit. Controller-layer cost remains separately
  unmeasured.
- `UNKNOWN` — no controlled source supplies a complete vector or authorizes
  scalarization.

## 8. Direct-versus-accumulation treatment across all units

| Unit | Direct same-parent mechanism | Sequential accumulation | Recombination and `T_scrub` floor |
|---|---|---|---|
| PA-DOM-01 | `UNKNOWN`/`INFERENCE` — not separately parameterized; irradiation `MERR` observations are not partitioned by parent event. | `SOURCE` — Eqs. (4)–(10) model independent single upsets accumulating in a word. | `INFERENCE` — no recombination; the modeled term is `T_r`-controllable, while any direct floor is unmodeled. |
| PA-DOM-02 | `SOURCE` — recognized as neighboring-bit MBU limitation but excluded from the main formulas. | `SOURCE` — independent uniform occupancy with periodic reset/repair. | `INFERENCE` — no recombination or direct floor; only accumulation risk changes with `t_scan`. |
| PA-DOM-03 | `SOURCE` — central measured/reconstructed physical MCU object with parent association. | `UNKNOWN` — no operational accumulation reliability model. | `UNKNOWN` — no reliability recombination or `T_scrub` dependence. |
| PA-DOM-04 | `SOURCE` — multiplicity-partitioned direct term is represented. | `SOURCE` — a sequential scrub-interval term is represented in the simple SEC-DED illustration. | `INFERENCE` — additive approximation is not proved disjoint; low-`β` scope and scalar mapping apply. |

## 9. Fixed-versus-adaptive treatment across all units

| Unit | Classification | Controlled evidence |
|---|---|---|
| PA-DOM-01-A | **CONFIGURABLE/PARAMETRIC, NOT ESTABLISHED ONLINE ADAPTIVE** | `SOURCE` — model/test dependence on regeneration frequency and MASTER/SLAVE programmability; `UNKNOWN` — closed observation-estimation-update chain. |
| PA-DOM-01-B | **REACTIVE ONLINE ADAPTIVE** | `SOURCE` — internal per-cycle `m_1` and feedback update of `T_r` (pp. 74–75, Eqs. (7)–(10), Fig. 4). `INFERENCE` — not forecast-driven; no ideal/full-information or robust comparator. |
| PA-DOM-02 | **FIXED PERIODIC / PARAMETRIC** | `SOURCE` — exogenous `t_scan`; no online update. |
| PA-DOM-03 | **NO OPERATIONAL RESTORATION CONTROL** | `SOURCE` — experimental acquisition/reconstruction only. |
| PA-DOM-04 | **EXOGENOUS SCRUB INTERVAL** | `SOURCE` — illustrative `t_s`; no selection law. |

## 10. Resource-cost treatment across all units

- PA-DOM-01: `SOURCE` — per-address service interruption and example relative
  unavailability via Eq. (11); `UNKNOWN` — energy, bandwidth, and controller
  hardware cost.
- PA-DOM-02: `SOURCE` — qualitative bandwidth/performance and ECC-overhead
  discussion; `UNKNOWN` — measured scrub/controller costs.
- PA-DOM-03: `SOURCE` — acquisition/test-time reduction; `INFERENCE` — not an
  operational control-resource result.
- PA-DOM-04: `UNKNOWN` — no RQ-005 resource vector; analytical simplicity is
  not a resource measurement.
- `INFERENCE` — no source evaluates information-acquisition cost,
  controller-layer cost and control-resource price together.

## 11. Exact remaining blockers

The bounded PA-DOM comparison has no missing controlled publication that
requires another source read. The following are named downstream
architecture/model inputs, not reasons to extend this literature task:

1. `UNKNOWN` — target physical-cell-to-codeword map `W`, bank/domain partition,
   interleaving and post-`W` joint event mark; unresolved link: PA-DOM-03/04
   physical reconstruction → target codeword harm.
2. `UNKNOWN` — target RQ-003 decoder outcome map for direct and accumulated
   marks; unresolved link: multiplicity/occupancy threshold → `E_cap` and
   service-visible outcomes.
3. `UNKNOWN` — target initial distribution `μ_t0`, sequential word ages, exact
   scan order and correction/writeback/reset timing; unresolved link: cyclic
   source models → DEC-001 `F_A(t0,T;μ_t0)`.
4. `UNKNOWN` — mechanism-specific direct-event rate and a controlled disjoint
   or explicitly bounded recombination with sequential accumulation; unresolved
   link: physical direct MCU → `T_scrub`-independent risk floor.
5. `UNKNOWN` — observation latency, counter-reset semantics, period bounds,
   noise/confusion model and uncertainty-to-decision propagation; unresolved
   link: PA-DOM-01-B feedback signal → information-limited robust action.
6. `UNKNOWN` — target RQ-005 vector measurements for scrub operations,
   bandwidth/latency, energy, hardware/controller overhead and acquisition
   cost; unresolved link: action policy → comparable resource price.
7. `UNKNOWN` — numerical reliability requirement `H_req,ε_req`; unresolved
   link: computed `F_A` → feasibility/constraint classification. It must not be
   assigned by this task.

## 12. Stop-rule disposition for every PA-DOM unit

| Work unit | Disposition | Reason |
|---|---|---|
| PA-DOM-01 | **CLOSED — A READ; B OPENED BY NAMED TRIGGER AND READ** | B establishes the missing online observation/estimation/update chain and adds the decision-enabling control/resource detail; no further PA-DOM-01 source is authorized or needed. |
| PA-DOM-02 | **CLOSED — BASELINE EXTRACTED** | The independent-error fixed-period analytical kernel is reproducible; the mission numerical layer is explicitly partial rather than silently reconstructed. |
| PA-DOM-03 | **CLOSED — MANDATORY PAIR READ** | A supplies controlled parent-event reconstruction/false-join bounds; B supplies topology/multiplicity evidence. No third source is authorized or needed. |
| PA-DOM-04 | **CLOSED BY CANONICAL REUSE** | Accepted PAPER-005 and RQ-002 synthesis already cover the unit; no primary PDF was opened. |

## 13. Overall recommendation

**CLOSED** — all four PA-DOM work units have a controlled disposition and the
nine common comparison fields are populated. This means the bounded domestic
prior-art comparison is closed, not that RQ-007, novelty, a reliability
requirement, or the next quantitative gate is closed.

The extracted prior-art components are classified as follows:

- **mandatory reproducible baselines:** PA-DOM-02 independent uniform
  accumulation with fixed periodic restoration; PA-DOM-01-B reactive
  count-to-period controller, including its narrow unavailability measure;
- **upstream input/reconstruction comparators:** PA-DOM-03 bounded physical
  parent-event reconstruction/topology and PA-DOM-04 reduced-input conditional
  multiplicity reconstruction;
- **control-layer comparator:** PA-DOM-01-B only; PA-DOM-01-A is insufficient
  alone, and PA-DOM-02/03/04 do not disclose online adaptation;
- **mandatory non-claims:** no universal `W`, no automatic equality with
  DEC-001 `F_A`, no claim that direct risk is scrub-controllable, no complete
  uncertainty guarantee, and no scalar resource benefit;
- **still-unoccupied project design targets:** an integrated direct-plus-
  accumulation, explicit-`W`/ECC, general-`μ_t0` risk calculation comparing
  best fixed, ideal full-information adaptive, and information-limited robust
  restoration with separate information, controller and control-resource
  costs.
