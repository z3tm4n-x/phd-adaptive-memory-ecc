# Draft Paper Card — RQ2-C005

**PAPER-ID:** `TBD until Orchestrator acceptance`  
**Candidate identity:** `RQ2-C005`  
**Related RQ:** `RQ-002`  
**Status:** `DRAFT — FULL-TEXT DEEP READ COMPLETED`  
**Recommendation:** `CORE`  
**Exact primary version:** arXiv:1704.07271v2, 15 Oct. 2017, 5 pages  
**Companion identity:** `RQ2-C006`, DOI `10.1109/RADECS.2017.8696217`  
**Full text used:** `Multiple_Cell_Event_Partitioning_for_Sim(5).pdf`; SHA-256 `b02b5fb32d45f63b078cf11488283fe6fff5a012077edb3d37f14acd3157ba2e`  
**Companion full text used:** `Multiple_Cell_Event_Partitioning_for_Simulation_of_Soft_Error_Rates_in_Space_Systems_with_Embedded_Error_Correcting_Codes.pdf`; SHA-256 `2cd3aa55ca715b8e3687fe411ad89b6ea01f6278c98423baa367fd38fc5bcc42`

## Bibliographic identity

V. A. Zebrev, M. S. Gorbunov, P. A. Osipenko, S. V. Sheshin, and A. V. Balbekov, “Multiple Cell Upset Partitioning for Simulation of Soft Error Rates in Space Systems with Error Correcting Codes,” arXiv:1704.07271v2, 2017.

`[SOURCE]` The exact version is identified on the first page and by the versioned arXiv record; it contains five pages, eight figures, and Eqs. (1)–(19). The companion paper is the four-page RADECS 2017 publication “Multiple Cell Event Partitioning for Simulation of Soft Error Rates in Space Systems with Embedded Error Correcting Codes,” DOI `10.1109/RADECS.2017.8696217`.

## Common extraction summary

| Field | Extraction |
|---|---|
| Primitive arrival object | `[SOURCE]` Physical ion strike on a memory cell/IC, marked by physical upset multiplicity `n`; Eqs. (2)–(5), pp. 1–2. |
| Count/arrival process | `[SOURCE]` Rates are obtained by integrating multiplicity-conditioned cross sections over LET flux; Eqs. (1), (4)–(7). The Poisson law in Eqs. (8)–(11) is a conjecture for **multiplicity conditional on LET**, not a temporal Poisson arrival process. |
| Stationarity/intensity | `[UNKNOWN]` No time-varying or stationary temporal point-process model is specified. Flux spectra and orbit-averaged rates are inputs to rate integrals. |
| Event mark/topology | `[SOURCE]` Mark is physical multiplicity `n`; no spatial coordinates or shape are retained. |
| Parent-event provenance | `[SOURCE]` `R_n` preserves same-ion multiplicity class. Sequential accumulation is introduced separately in the scrubbing approximation, Sec. III.D. |
| Mapping `W` | `[SOURCE]` No explicit physical-cell-to-codeword map is defined. Eqs. (17)–(18) assume one half of two-fold MCUs falls within one word. |
| Accumulation state | `[SOURCE]` Reduced to `R_1 t_s` and `β`; no word-resolved state distribution. |
| Initial state | `[INFERENCE]` Eq. (15) assumes a corrected/clean cycle start, but no general `μ_t0` is defined. |
| Repair semantics | `[SOURCE]` `t_s` is the scrub interval in a simple SEC-DED procedure; correction is represented only through the low-`β` approximation, not an operational scan/writeback model. |
| Direct mechanism | `[SOURCE]` Multiplicity-resolved `R_n`, with codeword-harmful direct multi-bit contribution approximated by `R_w(n≥2)`. |
| Sequential mechanism | `[SOURCE]` First term of Eq. (15), using `β`, represents two successive errors in one word between scrubs. |
| Partition/recombination | `[SOURCE]` Physical multiplicity is partitioned before logical mapping. Direct and sequential contributions are then added in Eq. (15). `[INFERENCE]` The addends are not proved disjoint. |
| Uncertainty/validation | `[SOURCE]` Multiplicity partition is compared with published ground and on-orbit data (Figs. 4–5, 7–8). No parameter confidence intervals are propagated. |
| Exactness status | `[SOURCE]` Eqs. (2)–(7), (13)–(14) are general rate decompositions within stated definitions; Eqs. (8)–(12) are modeling approximations; Eqs. (15)–(19) are a simple low-`β` SEC-DED approximation. |
| Relation to `E_cap`/`F_A` | `[INFERENCE]` The paper supplies candidate direct-event marks/rates and a cycle-level approximation, but its `R_syst` is not automatically `E_cap` and it does not define `F_A(t0,T; μ_t0)`. |

## 1. Research problem

- `[SOURCE]` Mean device cross section loses the multiplicity information needed to evaluate ECC effectiveness; the paper seeks a multiplicity-resolved partition usable in system-rate calculations (Abstract; Secs. I–III, pp. 1–4).

## 2. Objective

- `[SOURCE]` Construct partial `n`-fold event rates from mean cross-section data, connect them to an ECC vulnerability vector, compare the partition with published data, and illustrate scrubbing efficiency for simple SEC-DED (Secs. III.A–III.D).

## 3. System/model studied

- `[SOURCE]` Spaceborne SRAM/IC soft-error rates under a heavy-ion LET spectrum, with physical multiple-cell upsets and an embedded ECC abstraction (Secs. II–III).
- `[SOURCE]` The scrubbing illustration uses a memory with `N_w` words, `N_BW` bits per word, total bits `M=N_wN_BW`, SEC-DED, and scrub interval `t_s` (Sec. III.D, p. 4).

## 4. Method

- `[SOURCE]` Decompose mean cross section into multiplicity probabilities/cross sections, integrate each component against the particle flux, and recombine using an ECC vulnerability vector (Eqs. (2)–(14), pp. 1–4).
- `[SOURCE]` Use a Poisson multiplicity conjecture parameterized by mean multiplicity `m(Λ)` when only mean cross-section information is available (Eqs. (8)–(11), pp. 2–3).
- `[SOURCE]` Compare predicted partial multiplicity rates/cross sections with published ground and in-flight results (Figs. 4–5 and 7–8).

## 5. Assumptions

- `[SOURCE]` The cell area `a_c` and mean cross section determine mean multiplicity; multiplicity at fixed LET is approximated by a Poisson distribution in Eqs. (8)–(11).
- `[SOURCE]` A linear cross-section approximation is used for illustration in Eq. (12), while the authors state arbitrary interpolation may be used (p. 3).
- `[SOURCE]` For Eqs. (17)–(18), rates with `n≥3` are neglected as small, and half of two-fold MCUs are assumed to fall in one word (p. 4).
- `[SOURCE]` Eq. (16) requires `β≪1`; no error bound or validity claim outside that regime is supplied.
- `[INFERENCE]` No explicit topology, interleaving distance, codeword address map, nonstationary flux process, or word-age distribution is represented.

## 6. Input parameters

- `[SOURCE]` LET-dependent mean cross section `σ(Λ)`, flux spectrum `φ(Λ)`, cell area `a_c`, mean multiplicity `m(Λ)`, partial probabilities `p_n(Λ)`, and ECC vulnerability coefficients `V_n` (Eqs. (1)–(14)).
- `[SOURCE]` Scrubbing inputs: `N_w`, `N_BW`, `M`, `R_1`, `R_2`, and `t_s` (Eqs. (15)–(19)).

## 7. Output parameters

- `[SOURCE]` Multiplicity-resolved event rates per bit `R_n`, total strike rate `R_tot`, total bit-flip rate `R_SBU`, and system error rate `R_syst` (Eqs. (3)–(5), (13)–(14)).
- `[SOURCE]` Approximate word-level rates `R_w(n≥1)`, `R_w(n≥2)`, and vulnerability vector `V_n` for the simple SEC-DED case (Eqs. (15)–(19)).

## 8. Baselines/comparators

- `[SOURCE]` Model-derived multiplicity partitions versus published experimental and on-orbit partial-event data (Figs. 4–5, 7–8).
- `[SOURCE]` Generic no-ECC/with-ECC recombination through choices of `V_n`; no decoder simulation baseline is provided.

## 9. Main equations/models

### 9.1 Physical multiplicity partition

- `[SOURCE]` Eq. (2): `σ(Λ)=Σ_n nσ_n(Λ)=a_cΣ_n n p_n(Λ)=a_c m(Λ)`.
- `[SOURCE]` Eqs. (3)–(5): bit-flip rate is `Σ_n nR_n`, whereas `Σ_nR_n=R_tot` is the physical strike/event rate per cell.
- `[SOURCE]` Eq. (4): `R_n=a_c∫p_n(Λ)φ(Λ)dΛ`.
- `[SOURCE]` Eqs. (8)–(11): Poisson multiplicity conjecture `p_n(Λ)=m(Λ)^n e^{-m(Λ)}/n!` and its reduced forms.

### 9.2 ECC/system recombination

- `[SOURCE]` Eqs. (13)–(14): `R_syst=Σ_n V_nR_n` or `R_syst=Σ_n nV_nR_n`, depending on whether an error-event or bit-error quantity is required (p. 4).

### 9.3 Simple SEC-DED scrubbing approximation

- `[SOURCE]` Eq. (15): `R_syst=βMR_w(n≥1)+MR_w(n≥2)`.
- `[SOURCE]` Eq. (16): `β=(1/2)(N_BW−1)(R_1t_s)`, for `β≪1`.
- `[SOURCE]` Eqs. (17)–(18): `R_w(n≥1)≈R_1+(1/2)R_2`; `R_w(n≥2)≈(1/2)R_2`.
- `[SOURCE]` Eq. (19): `V_n≈{β,(1/2)(1+β),1,1,…}`.

## 10. Main results

- `[SOURCE]` The reduced-Poisson partition reproduces the qualitative/quantitative multiplicity dependence of cited ground and in-flight examples (Figs. 4–5, 7–8; Sec. III.C).
- `[SOURCE]` The SEC-DED example yields a compact vulnerability vector in Eq. (19) only after the low-`β`, `n≤2` mapping approximation used in Eqs. (15)–(18).
- `[INFERENCE]` Experimental/on-orbit comparison supports the physical multiplicity partition, not the specific additive scrubbing approximation.

## 11. Author-stated limitations

- `[SOURCE]` Poisson multiplicity is called a conjecture; linear cross-section behavior is an approximation (Secs. III.B–III.C).
- `[SOURCE]` Rates for `n≥3` are neglected in Eqs. (17)–(18), and `β≪1` is required (Sec. III.D).
- `[SOURCE]` The factor one half in Eqs. (17)–(18) rests on the explicit assumption that only half of two-fold MCUs affect one word (p. 4).

## 12. Methodological limitations inferred

- `[INFERENCE]` A scalar physical multiplicity is insufficient to determine codeword multiplicity under an arbitrary mapping `W`; coordinates or a joint post-mapping mark would be needed.
- `[INFERENCE]` Eq. (15) is an approximate additive construction, not a derivation over mutually exclusive sample spaces. Its first term allows the second successive error to be “any soft error,” while the second term also counts a direct multi-bit word event; overlap is therefore possible unless higher-order overlap is neglected under `β≪1`.
- `[INFERENCE]` The first factor `1/2` in Eq. (16) is not derived in this paper. It should not be attributed to the explicit interleaving assumption used for the separate factors `1/2` in Eqs. (17)–(18).

## 13. Threats to validity

- `[INFERENCE]` Construct validity: `R_syst` depends on an abstract vulnerability vector and is not a decoder-outcome-specific DUE/SDC metric.
- `[INFERENCE]` Mapping validity: the one-half allocation for two-fold events may be wrong for another physical layout or interleaving.
- `[INFERENCE]` Temporal validity: the source supplies no nonstationary arrival process or general initial-state distribution.
- `[INFERENCE]` Statistical validity: uncertainty in cross sections, flux, multiplicity fit, and validation data is not propagated to `R_syst`.

## 14. What the paper actually demonstrates

- `[SOURCE]` Mean cross-section information can be expanded into a multiplicity-resolved rate representation under an explicit multiplicity model, then combined with ECC vulnerability coefficients (Eqs. (2)–(14)).
- `[SOURCE]` It gives an illustrative low-occupancy SEC-DED expression separating a sequential accumulation term from a direct multi-bit word term (Eqs. (15)–(19)).
- `[INFERENCE]` For RQ-002, it supports retaining physical-event multiplicity and mechanism provenance before logical aggregation.

## 15. What cannot legitimately be claimed

- `[INFERENCE]` The source does not establish a temporal Poisson arrival law, an arbitrary mapping `W`, or a universal factor one half.
- `[INFERENCE]` It does not prove Eq. (15) exact, disjoint, or valid outside `β≪1`.
- `[INFERENCE]` It does not provide separately measured direct-MCU and accumulation cross sections/rates.
- `[INFERENCE]` It does not identify `R_syst` with `E_cap`, DUE, SDC, miscorrection, or system-visible failure.

## 16. Relevance to the dissertation

- `[INFERENCE]` Supplies one candidate marked-event layer `(physical strike, n)` and a mechanism-aware decomposition that can be mapped into `A` only after `W` is declared.
- `[INFERENCE]` Shows why bit-flip rate, physical event rate, and ECC/system error rate must remain distinct.
- `[INFERENCE]` Leaves `μ_t0`, nonstationarity, exact repair semantics, decoder outcomes, and uncertainty propagation unresolved.

## 17. Candidate claims

No `CLM-xxx` is created.

1. `[SOURCE-CANDIDATE]` Physical strike rates can be partitioned by upset multiplicity before ECC vulnerability is applied (Eqs. (2)–(14), pp. 1–4).
2. `[SOURCE-CANDIDATE]` In this source, the Poisson distribution describes multiplicity conditional on LET, not temporal arrivals (Eqs. (8)–(11), pp. 2–3).
3. `[SOURCE-CANDIDATE]` Eq. (15) contains a sequential two-arrival term and a direct multiple-bit word-event term (Sec. III.D, p. 4).
4. `[SOURCE-CANDIDATE]` The simple SEC-DED expression is explicitly restricted by `β≪1` and an assumed one-half mapping of two-fold MCUs into one word (Eqs. (16)–(18), p. 4).
5. `[INFERENCE-CANDIDATE]` Multiplicity-only partition cannot determine codeword harm under arbitrary `W` without additional spatial/post-mapping information.

## 18. Tensions/conflicts

- `[INFERENCE]` The general event partition in Eqs. (2)–(14) is mechanism-preserving, but the later `R_w` conversion discards topology and replaces mapping with a scalar one-half assumption.
- `[INFERENCE]` The additive Eq. (15) is useful as a low-order approximation but is not a source-established non-overlap rule for direct and accumulated mechanisms.

## 19. Open questions/evidence gaps

1. `[UNKNOWN]` What spatial mark and target mapping `W` replace the one-half assumption for the controller-managed domain `A`?
2. `[UNKNOWN]` What is the error order of Eq. (15) as `β` grows, and where does the Eq. (16) factor `1/2` originate?
3. `[UNKNOWN]` How should direct and sequential terms be made mutually exclusive in a windowed first-passage model?
4. `[UNKNOWN]` What temporal arrival law and initial state `μ_t0` should drive accumulation?
5. `[UNKNOWN]` How should cross-section/flux uncertainty be propagated into `F_A(t0,T; μ_t0)`?

## Mandatory questions on Eqs. (15)–(19)

1. **First term of Eq. (15):** `[SOURCE]` `βMR_w(n≥1)` models two successive errors in one word between scrubs: the first is a single-bit upset and the second may be any soft error (Sec. III.D, p. 4).
2. **Second term:** `[SOURCE]` `MR_w(n≥2)` is the rate of a direct multiple-bit error within a word (p. 4).
3. **Disjoint sample spaces?:** `[INFERENCE]` No. The source presents a standard approximation/additive construction and does not prove disjointness.
4. **Direct versus sequential separation:** `[SOURCE]` They are the second and first addends of Eq. (15), respectively; physical multiplicity was previously partitioned in Eqs. (2)–(11).
5. **Meaning of `R_w(n≥1)` / `R_w(n≥2)`:** `[SOURCE]` Word-level rates for at least one and at least two upset bits from an event, approximated by Eqs. (17)–(18).
6. **Physical-to-word translation:** `[SOURCE]` Only by the statistical one-half allocation of two-fold MCUs in Eqs. (17)–(18); no explicit `W`.
7. **Factor `1/2`:** `[SOURCE]` In Eqs. (17)–(18), it is the assumed half of two-fold MCUs in one word. `[UNKNOWN]` Eq. (16)'s separate factor one half is not derived.
8. **Mapping assumption:** `[SOURCE]` Exactly half of two-fold MCUs affect one word; no physical organization/interleaving distance is specified.
9. **Dropped `n≥3`:** `[SOURCE]` Their contributions are omitted from Eqs. (17)–(18) because the rates are assumed small. Eq. (19) nevertheless assigns `V_n=1` for `n≥3` if their `R_n` are retained in the general sum.
10. **Meaning of `β≪1`:** `[SOURCE]` The dimensionless accumulation parameter in Eq. (16) must be small. `[INFERENCE]` It is a low-collision/low-occupancy regime; no numerical boundary is supplied.
11. **Validity outside:** `[UNKNOWN]` Not claimed.
12. **Separate experimental rates?:** `[SOURCE]` No; direct `R_n` are model-derived/compared with data, while accumulation is analytic through `β`.
13. **Partition level:** `[SOURCE]` Physical multiplicity is partitioned before logical mapping; the word conversion occurs later and approximately.
14. **Overlap/double counting:** `[INFERENCE]` Possible in Eq. (15), because the second error in the first addend may itself be multi-bit and the second addend also represents multi-bit word events; likely higher-order under `β≪1`, but no proof is given.
15. **Validation boundary:** `[SOURCE]` Ground/on-orbit comparisons validate the multiplicity partition examples; the SEC-DED scrubbing formula is illustrative and is not separately experimentally/on-orbit validated.

## C005/C006 version comparison

| Comparison field | Status | Verified result |
|---|---|---|
| Bibliographic identity | `VERIFIED DIFFERENCE` | C005 is arXiv:1704.07271v2, revised 15 Oct. 2017, five pages; C006 is RADECS 2017, DOI `10.1109/RADECS.2017.8696217`, four pages. Titles and received dates differ. |
| Equations (1)–(14) | `VERIFIED NO SUBSTANTIVE DIFFERENCE` | Same multiplicity decomposition, Poisson conjecture, linear illustration, and vulnerability-vector recombination; minor layout/wording changes only. |
| Equations (15)–(19) | `VERIFIED DIFFERENCE` | Present only in C005 as Sec. III.D; absent from C006. |
| Definitions | `VERIFIED NO SUBSTANTIVE DIFFERENCE` | Core `σ_n`, `p_n`, `R_n`, multiplicity, and `V_n` definitions are substantively the same through Eq. (14). |
| Scrubbing assumptions/derivation | `VERIFIED DIFFERENCE` | Low-`β` SEC-DED assumptions, `t_s`, `R_w`, factor one half, and Eq. (19) occur only in C005. |
| Validation data | `VERIFIED DIFFERENCE` | C005 adds SAC-C simulated-versus-in-flight partial-event plots (Figs. 4–5). Shared reduced-Poisson comparisons are C005 Figs. 7–8 / C006 Figs. 5–6. |
| Figures/tables | `VERIFIED DIFFERENCE` | C005 has eight figures; C006 has six. Neither version contains tables. |
| Omitted material | `VERIFIED DIFFERENCE` | C006 omits the complete scrubbing subsection and the two SAC-C comparison figures present in C005. |
| General conclusions | `VERIFIED NO SUBSTANTIVE DIFFERENCE` | Both conclude that multiplicity partition can support system-rate simulation; C005 additionally has the scrub-specific result. |
| Validity statements | `VERIFIED DIFFERENCE` | `β≪1`, neglected `n≥3`, and one-half codeword mapping are stated only in C005. |
| References | `VERIFIED DIFFERENCE` | C005 has 15 references and adds material supporting the scrubbing section; C006 has 13. |

`[INFERENCE]` C006 has independent publication identity but no analytical content beyond the common Eqs. (1)–(14) that changes this batch's model-selection conclusions. Therefore no separate full Draft Paper Card is created; C006 remains explicitly versioned and compared here.

## Final disposition

- **Recommendation:** `CORE` for event/mechanism partitioning; C006 retained as a separate version identity but not a separate analytical card.
- **Confidence:** high for equations/definitions/version differences; medium for interpreting Eq. (15) overlap because the paper does not formalize sample spaces.
- **Evidence gaps:** exact `W`, disjoint recombination, Eq. (16) derivation, nonstationary arrivals, initial-state distribution, uncertainty propagation, and operational scrub semantics.
