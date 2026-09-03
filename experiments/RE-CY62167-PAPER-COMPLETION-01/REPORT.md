# RE-CY62167-PAPER-COMPLETION-01 — Phase A

**Disposition: PASS-A-WITH-DISCREPANCY**

## Controlled population and frozen map

Raw archive SHA-256: `16ab27789329adbbccdf9a7e5d0e15e855440d3f52b8dd93a384317a4635770a`. The frozen `A=f(x,y)` coefficients from `RE-CY62167-ADDRESS-MAPPING-01` are imported without refit; 148731 address-bearing ordinary records reproduce with zero mismatches.

Population accounting is RAW `173835 clusters / 299154 cell rows`, ORDINARY `173802 / 299121`, EVENT_LOCAL_DEDUPLICATED `173802 / 299026`; service records = 15, ambiguous records = 18, event-local duplicate rows removed = 95. The manuscript event total 173802 is reproduced, but its global total 299206 cells is **NOT REPRODUCED** because it exceeds even the raw 299154 rows in the controlled archive. P_HI reproduces exactly 9 series, 8240 events and 91284 deduplicated cells.

## Restricted mapping family

All `C(21,2)=210` coordinate-subspace mappings are constructed. The manuscript-compatible spacing rule is recovered without post-hoc metric choice: spacing distribution is `1:74, 2:31, 4:27, 8:23, 16:55`; exactly 55 mappings satisfy minimum spacing >=16. Baseline `W_00_01` satisfies `W(A)=floor(A/4)`. The complete four-address linear class has `[21 choose 2]_2 = 733006703275` partitions, independently reproduced by the q-binomial recurrence. Therefore `55 subset 210 subset 733006703275`; the retained 55 are a **RESTRICTED MANUSCRIPT-COMPATIBILITY DIAGNOSTIC FAMILY**, not all possible proprietary layouts.

## Direct/residual partition

P_MAP uses all 28 controlled heavy-ion and proton series after event-local deduplication. The manuscript distribution is exactly **REPRODUCED**: 45 mappings have 0 registered direct events, 9 have 4, and 1 has 5. Baseline `W_00_01` has 4. The fifth event is proton series `clust_p164MeV.txt`, segment 1, cluster 5480, K=29, direct only for `W_00_11` among the retained family. Direct results are **REGISTERED-CLUSTER DIRECT EVENTS**, not proof of the complete parent-particle same-parent MCU population.

For P_HI (LET 5.2, 15, 17, 22, 27, 29, 33, 42, 57 MeV cm^2/mg), baseline direct counts are zero through 33, one at 42 and three at 57. Every LET/mapping construction uses the disjoint conservation contract `S_D^cells + S_C = S_used`.

## Article normalization

`sigma_b(L)=2.6e-7[1-exp(-((L-0.15)/70)^1.2)]` for `L>0.15`, otherwise zero. `F_art=S/(2^24 sigma_b)` is an **ARTICLE-NORMALIZED EFFECTIVE FLUENCE**, **not measured fluence**. Baseline reconstructed values include `sigma_C(42)=1.8139804054 cm^2`, `sigma_C(57)=2.3463996153 cm^2`, `sigma_D(57)=3.342767046e-4 cm^2`.

For N_D=3 at LET 57 the manuscript construction gives `sigma_hat*2.4*(3+0.67)/(3*(1-0.10)) = 1.090484894e-3 cm^2`. Its status is **ARTICLE-CONFIDENCE-STYLE EFFECTIVE-FLUENCE NORMALIZATION** and **NOT ESTABLISHED AS NORMATIVE CONFIDENCE BOUND WITHOUT INDEPENDENT FLUENCE PROVENANCE**. It is not generalized to other N_D without PI decision.

## Reference and resource regressions

Synthetic regression passes: `tau_max^U=243.554017980 s` and model-conditional reference bracket `[315.224841226,315.744500579] s`. Registered direct events are separate absorbing hazards; residual events use bit toggles and cyclic sequential scrub phases.

Datasheet timing audit treats tRC=45 ns and tWC=45 ns independently and records relevant write constraints. In the **DECLARED SERIAL BUS-OCCUPANCY MODEL**, R1 uses `2^19` reads/pass and R2 `2^21`, a read-count ratio of 4. Unconditional full-pass floors are R1 `0.04718592 s`, R2 `0.18874368 s`; ERR-assisted deterministic read floors are `0.02359296 s` and `0.09437184 s`, with write cost model-dependent. The old 0.94% and 0.42% values are reproduced only for R2 + unconditional writeback + serial 45 ns read and 45 ns write at tau=20 s and 45 s: 0.9437184% and 0.4194304%.

## Phase-B gate

COSRAD was **not run**. `cosrad_input_cross_sections.csv` and `cosrad_contract.md` are the PI package. Required PI return for bounds: `shield_g_cm2,mapping_id,estimate_type,nu_direct_s-1,nu_accumulation_bit_s-1` for 2.0, 2.5 and 3.0 g/cm^2, with estimate type POINT or ARTICLE_CONFIDENCE_STYLE. `tau_max^ref` additionally requires LET-resolved registered-event weights; otherwise use `TAU_MAX_REFERENCE_BLOCKED_BY_MISSING_EVENT_RATE_WEIGHTS`.

## Claims that must be revised in the manuscript

Qualify/remove the unreproduced 299206 total; do not call the 55 mappings all possible W; do not claim recovery of proprietary W; do not equate registered clusters with the complete physical same-parent population; do not call `F_art` measured fluence; do not call the confidence-style construction a normative 95% bound; do not convert failure of the sufficient `Q_U` certificate into physical impossibility; state the exact R2/unconditional serial semantics behind 0.94%/0.42%.

Tests: `CY62167_RAW_ARCHIVE=<controlled.zip> python -m unittest discover -v -p 'test_*.py'`. Phase-A suite: **33/33 PASS**.
