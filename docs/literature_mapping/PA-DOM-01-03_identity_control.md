# PA-DOM-01...03 source identity and access control

## 1. Task control

| Field | Value |
|---|---|
| Task ID | `PA-DOM-01-03-SOURCE-CONTROL-01` |
| Related RQs | `RQ-002`, `RQ-004`, `RQ-006`, `RQ-007` |
| Canonical base | `83d4db20ce43ff238d58551610f487e7cf3c2c6e` |
| Execution date | 2026-09-01 (UTC) |
| Role boundary | Literature Scout; identity, version, and access control only |
| Excluded routes | eLibrary and ResearchRabbit, as required by the handoff |
| Output scope | This report only; no scientific, novelty, or claim-level adjudication |

This report controls the identity and access state of the three bounded
PA-DOM work units. A title, abstract, indexed excerpt, or visible publisher
page is not treated as evidence for a full scientific proposition. No
`PAPER-xxx`, `CLM-xxx`, `EVD-xxx`, `RQ`, `DEC`, `HYP`, `EXP`, or `RES` object is
created here.

## 2. Routes and exact queries executed

The search was deliberately limited to exact authors, exact titles, stable
identifiers, official publisher/institutional records, and access checks.
No citation-network expansion was performed.

| Route | Access | Exact query or operation | Purpose/result |
|---|---|---|---|
| Public web exact search | ACCESSIBLE | `"Мещанов" "Лушников" "Красников" память` | Locate the PA-DOM-01 source family. |
| Public web exact search | ACCESSIBLE | `"Мещанов" "периода регенерации" память` | Test the attributed regeneration-period chain without broadening by topic. |
| Public web exact search | ACCESSIBLE | `"интенсивност" "периода регенерации" СОЗУ Мещанов` | Test whether an intensity-estimation source could be identified exactly. |
| Public web exact-title search | ACCESSIBLE | `"Исследование сбоеустойчивости СОЗУ с функцией исправления одиночных сбоев при воздействии ТЗЧ" "68-76"` | Resolve the longer 2018 journal record. |
| Official NIIME author/publication page | ACCESSIBLE | Exact-title lookup on `niime.ru/education/nauchnye-publikatsii/` | Confirm the 2017 conference, 2018 journal, and 2018 Nanoindustry records as distinct bibliographic records. |
| Publisher record | ACCESSIBLE | DOI `10.22184/1993-8578.2018.82.327.329` | Control title, complete author order, venue, issue, pages, DOI, abstract, and public PDF link. |
| Direct full-text check | PARTIAL | `https://www.nanoindustry.su/files/article_pdf/6/article_6802_547.pdf` | Server returned HTTP 200 and `application/pdf`; transfer was slow, while the publisher article page exposes the full text and PDF link. |
| Public web exact-title search | ACCESSIBLE | `"Моделирование опасности одиночных сбоев от космических частиц для памяти с коррекцией ошибок" DOI` | Resolve PA-DOM-02 and its translation. |
| Official issue lookup | ACCESSIBLE | `site:vmu.phys.msu.ru "Моделирование опасности одиночных сбоев"` | Confirm Russian issue, pages, and official PDF route. |
| Publisher/DOI record | ACCESSIBLE | DOI `10.3103/S0027134917060133` | Control English version-of-record metadata and Russian-original relation. |
| Author-uploaded full text | ACCESSIBLE | Exact DOI/title on ResearchGate | Confirm an author-uploaded English full text is exposed for reading/download. |
| Direct Russian PDF check | PARTIAL | `https://vmu.phys.msu.ru/file/2017/6/17-6-099.pdf` | Endpoint begins a valid PDF transfer, but the transfer did not complete within 60 seconds. |
| Public web exact-title search | ACCESSIBLE | `"Методики экспериментальных исследований многократных сбоев" 2014 автореферат` | Locate the PA-DOM-03 dissertation abstract. |
| Public web exact-title search | ACCESSIBLE | `"Методики экспериментальных исследований многократных сбоев" 2015 автореферат` | Resolve the apparent year/defence-date discrepancy. |
| Official institutional repository | PARTIAL | `https://openrepository.mephi.ru/entities/publication/65a0372c-cced-43c8-805e-e268340f5327` | Official MEPhI entity is indexed, but did not render reliably during execution. |
| Official institutional PDF | UNAVAILABLE AT EXECUTION | `https://lib-repository.mephi.ru/abstracts_of_dissertations_mephi/Boruzdina_Metodiki_eksperimentalnykh_issledovaniy_mnogokratnykh_sboev_v_KMOP_2014.pdf` | Exact PDF route returned HTTP 502. |
| National Electronic Library catalogue | PARTIAL | NEL identifier `000200_000018_RU_NLR_BIBL_A_011098617` | Exact catalogue record was indexed; direct page returned HTTP 403. |
| Catalogue/file-number check | PARTIAL | `"01007928063" Боруздина` | Indexed copy exposed the defence date, but the route redirected to a secondary search page rather than a stable full-text object. |
| Publisher/DOI record | ACCESSIBLE | DOI `10.1134/S1063739714020036` | Control the PA-DOM-03 topology-paper identity and Russian/English version relation. |
| Scite public-index sanity check | PARTIAL | `site:scite.ai/reports 10.22184/1993-8578.2018.82.327.329` | No public Scite report surfaced. Correction/retraction status therefore remains unverified by Scite, not “absent.” |
| Scite public-index sanity check | PARTIAL | `site:scite.ai/reports 10.3103/S0027134917060133` | Same result. |
| Scite public-index sanity check | PARTIAL | `site:scite.ai/reports 10.1134/S1063739714020036` | Same result. |

## 3. Controlled identity and access table

### 3.1 Mandatory and selected controlling records

| Local label | PA-DOM gap | Screening | Disposition | Exact identity | Version/family control | Full-text state |
|---|---|---|---|---|---|---|
| `PA-DOM-01-A` | Registered/corrected single-error count -> present error-intensity estimate -> restoration-period change | CORE | **IDENTITY AND FULL TEXT CONTROLLED** | G. Ya. Krasnikov; A. S. Lushnikov; V. D. Meshchanov; E. S. Rybalko; N. N. Fomicheva; N. A. Shelepin. **Исследование сбоеустойчивости СОЗУ с функцией исправления одиночных сбоев при воздействии ТЗЧ** [*Studying the Fault Tolerance of SRAM With the Function of Correcting Single Event Upsets Caused by Heavy Ions*]. *Наноиндустрия / Nanoindustry*, 2018, no. 9 (82), pp. 327-329. DOI: [`10.22184/1993-8578.2018.82.327.329`](https://doi.org/10.22184/1993-8578.2018.82.327.329). | Distinct record from the 2017 conference paper and the longer 2018 journal paper. Whether it is an abridgement/reissue is **UNKNOWN — REQUIRES FULL-TEXT COMPARISON**. | Publisher page and public PDF link are controlled: `https://www.nanoindustry.su/journal/article/6802`. The page exposes the article text. |
| `PA-DOM-01-B` | Same gap; candidate for the most complete treatment | CORE | **IDENTITY CONTROLLED / FULL TEXT PENDING** | G. Ya. Krasnikov; A. S. Lushnikov; V. D. Meshchanov; E. S. Rybalko; N. N. Fomicheva; N. A. Shelepin. **Исследование сбоеустойчивости СОЗУ с функцией исправления одиночных сбоев при воздействии ТЗЧ**. *Электронная техника. Серия 3: Микроэлектроника*, 2018, no. 1 (169), pp. 68-76. No DOI located in the bounded routes. | Same title and author order as `PA-DOM-01-A`, but identity as the same substantive work is not inferred. Relation to the 2017 conference and Nanoindustry records is **UNKNOWN — REQUIRES FULL-TEXT COMPARISON**. | Exact institutional bibliography is controlled; no stable public full text was located. |
| `PA-DOM-02-A` | ECC-protected memory, periodic background restoration, probability of ECC-uncorrectable state, restoration interval, and independent-error assumptions | CORE | **IDENTITY AND FULL TEXT CONTROLLED** | Mikhail V. Podzolko. **Modeling of the Risk of Single Event Upsets from Cosmic Particles for Memory with Error Correction**. *Moscow University Physics Bulletin*, vol. 72, no. 6, 2017, pp. 601-608. DOI: [`10.3103/S0027134917060133`](https://doi.org/10.3103/S0027134917060133). Affiliation: Skobeltsyn Institute of Nuclear Physics, Moscow State University, Moscow, Russia. | Author-translated version of the Russian original: M. V. Podzolko, **Моделирование опасности одиночных сбоев от космических частиц для памяти с коррекцией ошибок**, *Вестник Московского университета. Серия 3: Физика. Астрономия*, 2017, no. 6, pp. 99-106. The Springer note reports pp. 95-99, which conflicts with the official Russian issue and the translated PDF front matter; use 99-106 for the Russian record and preserve the discrepancy as a metadata note. English version of record published online 2018-04-03, issue year 2017. | Author-uploaded English full text is exposed at `https://www.researchgate.net/publication/324416174_Modeling_of_the_Risk_of_Single_Event_Upsets_from_Cosmic_Particles_for_Memory_with_Error_Correction`. The official Russian PDF endpoint responds as PDF but timed out during transfer. |
| `PA-DOM-03-A` | Mandatory dissertation-abstract source for experimental identification of physical/logical multiple upsets | CORE | **IDENTITY CONTROLLED / FULL TEXT PENDING** | Anna Borisovna Boruzdina. **Методики экспериментальных исследований многократных сбоев в КМОП микросхемах статических оперативных запоминающих устройств при воздействии отдельных ядерных частиц**. Dissertation abstract for Candidate of Technical Sciences, specialty 05.13.05, National Research Nuclear University MEPhI, Moscow, 25 pp. Stable NEL ID: `000200_000018_RU_NLR_BIBL_A_011098617`; catalogue/file number: `01007928063`. | The controlled catalogue tradition and official MEPhI filename assign publication year **2014**. The indexed abstract text states that the defence was scheduled for **16 March 2015**, and bears a February 2015 library/date stamp. These are treated as publication year versus defence/circulation dates, not as proof of two substantive versions. No second version identity was established. | Official MEPhI entity: `https://openrepository.mephi.ru/entities/publication/65a0372c-cced-43c8-805e-e268340f5327`. Exact official PDF route ends in `_2014.pdf`, but returned HTTP 502 during execution. Abstract-only secondary reproductions are not an acceptable substitute for the controlled PDF. |
| `PA-DOM-03-B` | Mandatory topology source | CORE | **IDENTITY CONTROLLED / FULL TEXT PENDING** | A. B. Boruzdina; N. G. Grigor'ev; A. V. Ulanova. **Effect of Topological Placement of Memory Cells in Memory Chips on Multiplicity of Cell Upsets from Heavy Charged Particles**. *Russian Microelectronics*, vol. 43, 2014, pp. 96-101. DOI: [`10.1134/S1063739714020036`](https://doi.org/10.1134/S1063739714020036). Published 2014-03-26; received 2013-05-22. Affiliations: National Research Nuclear University MEPhI (all authors) and JSC ENPO SPELS (Boruzdina and Ulanova). | English translation of the Russian original published as: *Микроэлектроника*, vol. 43, no. 2, 2014, pp. 88-93. The publisher controls this as one article/version relation. A. I. Chumakov is **not** an author of this mandatory DOI paper. | Springer/Pleiades metadata and abstract are accessible. Full text is subscription-only and no public author copy was located in the bounded routes: `https://link.springer.com/article/10.1134/S1063739714020036`. |

### 3.2 Abstract/metadata-level feature indications only

`UNKNOWN — PAPER ANALYST` means that the source identity is controlled but
the feature must not be inferred from a title, abstract, index snippet, or
unexamined full text.

| Record | Indicated inputs | Controlled variable | Decision rule | Reliability treatment | Resource-cost treatment | Implementation evidence |
|---|---|---|---|---|---|---|
| `PA-DOM-01-A` | Publisher page names SRAM parameters, temporal parameters, particle-flux parameters, registered single upsets, and correction-cycle duration. | Correction/restoration frequency or cycle is explicitly varied. | Whether a measured/corrected count is converted to a current intensity estimate and then to an online period update is **UNKNOWN — PAPER ANALYST**. | Publisher text indicates an uncorrectable multiple-upset frequency/probability motivation; exact event and guarantee relation are **UNKNOWN — PAPER ANALYST**. | **UNKNOWN — PAPER ANALYST**. | Publisher abstract reports model/experiment comparison on 4-Mbit pilot SRAM samples; exact hardware/control-loop realization is **UNKNOWN — PAPER ANALYST**. |
| `PA-DOM-01-B` | Same-title relation suggests overlapping scope, but features are not transferred from `PA-DOM-01-A`. | **UNKNOWN — PAPER ANALYST**. | **UNKNOWN — PAPER ANALYST**. | **UNKNOWN — PAPER ANALYST**. | **UNKNOWN — PAPER ANALYST**. | Bibliographic identity only; full text pending. |
| `PA-DOM-02-A` | Abstract names particle environment, spacecraft flight conditions, selected memory chips, ECC, and time. | No online controlled variable is established at metadata level; the restoration/scan interval is an extraction target. | **UNKNOWN — PAPER ANALYST**. | Abstract explicitly indicates probabilities of more than one/two errors in at least one memory block and probability of errors uncorrectable by ECC. Exact semantics and assumptions require extraction. | **UNKNOWN — PAPER ANALYST**. | Calculations for selected chips/flight conditions are indicated; no adaptive implementation is indicated. |
| `PA-DOM-03-A` | Title and controlled abstract identity indicate irradiation tests of CMOS SRAM multiple upsets. | None indicated. | None indicated. | Multiplicity/classification is indicated; exact physical-to-logical semantics and uncertainty are **UNKNOWN — PAPER ANALYST**. | Not indicated. | Dissertation abstract indicates experimental methods/apparatus, but proposition-level support requires the official text. |
| `PA-DOM-03-B` | Abstract indicates memory-cell topology and heavy charged particles. | Cell topology/configuration is compared, not an online scrub control. | None indicated. | MCU sensitivity/multiplicity is indicated; mapping and statistical semantics are **UNKNOWN — PAPER ANALYST**. | Not indicated. | Analysis of 6-transistor cell configurations is indicated; exact experimental/simulation support is **UNKNOWN — PAPER ANALYST**. |

## 4. Mismatch and rejection controls

These records are listed only to prevent silent substitution. They are not an
invitation to expand the task.

| Record | Disposition | Reason |
|---|---|---|
| Krasnikov et al., same title, proceedings of the 3rd International Scientific and Technical Conference *Микроэлектроника-2017*, Alushta, 2-7 Oct 2017, pp. 288-293 | **REJECT — WRONG OR ADJACENT SOURCE** for the present controlling target | It is a separate conference record. No evidence from the bounded routes establishes that it contains the most complete chain or that it is text-identical to either 2018 record. |
| V. D. Meshchanov; A. S. Lushnikov; E. S. Rybalko; N. N. Fomicheva, **Модель сбоеустойчивости СОЗУ с функцией исправления одиночных сбоев при воздействии тяжелых заряженных частиц**, *Электронная техника. Серия 3: Микроэлектроника*, 2016, no. 2 (162), pp. 71-76, EDN `WTIAHD` | **REJECT — WRONG OR ADJACENT SOURCE** for PA-DOM-01 identity control | It is an earlier model paper, lacks Krasnikov and Shelepin, and metadata does not establish the required online count-to-intensity-to-period chain. It may be a cited model predecessor, but that does not make it the controlling adaptive source. |
| Any secondary dissertation page reproducing parts of Boruzdina's abstract | **REJECT — WRONG OR ADJACENT SOURCE** as the controlled full text | Useful only as a locator. It must not replace the official MEPhI/NEL identity or support full-paper inference. |
| A. I. Chumakov as an author of DOI `10.1134/S1063739714020036` | **REJECT — IDENTITY MISMATCH** | Publisher metadata gives only Boruzdina, Grigor'ev, and Ulanova. Chumakov belongs to the wider PA-DOM-03 author/topic signal, not this paper's author list. |

## 5. HANDOFF TO PAPER ANALYST

The following source-specific contracts satisfy the Literature Scout to Paper
Analyst boundary. They authorize bounded extraction from the named full text,
not cross-paper adjudication or novelty conclusions.

### 5.1 PA-DOM-01-A — closest accessible source

**Identity and gap.** `PA-DOM-01-A`; RQ-004/RQ-007, with RQ-002/RQ-006
dependencies. It is the closest accessible primary source to the attributed
chain:

`registered/corrected single-error count -> current error-intensity estimate -> restoration-period change`.

**Selection reason.** Exact author group, exact SRAM/periodic-correction topic,
public full text, model/experiment indication, and explicit correction-frequency
dependence. It has higher decision value than the conference record, but its
three-page length makes comparison with `PA-DOM-01-B` important if the chain is
incomplete.

**Full-text location.** `https://www.nanoindustry.su/journal/article/6802` and
the publisher PDF link on that page.

**Extraction questions.** Extract with page/equation/figure anchors:

1. What exactly is counted: registered, detected, corrected, or residual single
   errors; at what word/device scope; with what reset/window semantics?
2. Is there an explicit estimator that maps the count to a current error/upset
   intensity? If yes, extract the equation, time window, update cadence, units,
   bias/variance or uncertainty treatment, and assumptions.
3. Is the restoration/regeneration period actually changed online? If yes,
   extract the admissible action set, trigger/update rule, timing, saturation,
   hysteresis, and initialization.
4. If no online rule exists, distinguish a parametric dependence or design-time
   sizing formula from adaptive control.
5. What reliability event and aggregation level are used, and how do they relate
   to uncorrectable multiple errors? Do not equate the event to DEC-001
   `E_cap`/`F_A` without a proved mapping.
6. What arrival, independence, spatial mapping, ECC, accumulation, writeback,
   and scrub/reset assumptions are made?
7. Is any reliability constraint/guarantee stated, or only a calculated
   frequency/probability?
8. Is resource cost, scrub traffic, energy, bandwidth, latency, or wear modeled
   or measured?
9. What constitutes the reported model/experiment agreement, and what hardware,
   irradiation, sample, and operating conditions delimit it?
10. Does this source alone contain the complete count-to-estimate-to-action chain?
    If not, name the exact missing proposition before requesting `PA-DOM-01-B`.

**Limits and prohibited inferences.** Do not infer a forecast-driven controller,
closed-loop optimality, a formal reliability guarantee, resource optimization,
or novelty from the title/abstract. Do not transfer content from the 2017
conference or 2018 longer journal record without direct comparison.

**Readiness.** **READY FOR PAPER ANALYST**.

### 5.2 PA-DOM-01-B — longer same-title journal record

**Identity and gap.** `PA-DOM-01-B`; same gap and RQs as `PA-DOM-01-A`.

**Selection reason.** It is the only bounded same-author, same-title primary
record with substantially greater page extent and is therefore the specific
candidate for a missing estimator or control rule. Similarity is not treated as
proof of content.

**Access blocker.** No stable public full text was located. Obtain the exact
2018 no. 1 (169), pp. 68-76 article; do not substitute the conference or
Nanoindustry file.

**Extraction questions.** After access, apply questions 1-10 from
`PA-DOM-01-A`, then compare the two full texts section-by-section and record
whether `PA-DOM-01-B` is an extension, duplicate/reissue, or substantively
different work.

**Limits and prohibited inferences.** Until full text is controlled, no feature
from `PA-DOM-01-A` may be imputed to this record and no family relation may be
asserted.

**Readiness.** **NOT READY — FULL TEXT PENDING**. Escalate only if analysis of
`PA-DOM-01-A` identifies a named missing proposition.

### 5.3 PA-DOM-02-A — Podzolko 2017

**Identity and gap.** `PA-DOM-02-A`; RQ-002/RQ-007, with RQ-004/RQ-006
dependencies. Exact primary text for ECC-protected memory risk under periodic
background restoration/scanning.

**Selection reason.** Exact title/year/topic match; DOI and Russian/English
version relation controlled; author-uploaded full text available.

**Full-text location.** Author-uploaded English version at
`https://www.researchgate.net/publication/324416174_Modeling_of_the_Risk_of_Single_Event_Upsets_from_Cosmic_Particles_for_Memory_with_Error_Correction`.
Official Russian issue record: `https://vmu.phys.msu.ru/ru/toc/2017/6`.

**Extraction questions.** Extract with page/equation/figure anchors:

1. Define the modeled failure event, ECC capability, memory-block/word/device
   aggregation, mission population, and time horizon.
2. Identify the arrival process and all independence assumptions: across time,
   bits, blocks/words, particle species, and physical events.
3. Determine whether a single particle can produce multiple affected bits or
   codewords and whether physical-to-logical mapping `W` is represented.
4. Extract initial-state assumptions and the state accumulated between
   restorations.
5. Define background scanning/restoration, correction/writeback, reset, coverage,
   scan order, and whether the quoted interval is a complete-memory cycle or a
   per-word exposure time.
6. Extract the exact probability formulas for ECC-uncorrectable states and their
   dependence on restoration interval; identify exact versus approximate steps
   and asymptotic regimes.
7. Explain how proton, ion, solar-flare, and radiation-belt components are
   combined and whether the environment is stationary or time varying.
8. Identify empirical inputs, chip-specific parameters, uncertainty treatment,
   and validation domain.
9. Determine whether the interval is optimized, merely swept, or sized against
   a requirement; extract any action/selection rule if present.
10. Identify any resource-cost, scan-traffic, power, latency, or implementation
    treatment.
11. Map the model to DEC-001 inputs only where the paper supplies explicit
    semantics; otherwise record the non-equivalence or missing mapping.
12. Record which assumptions are candidates for relaxation in RQ-002/RQ-006 and
    which observable quantities could be available for RQ-004.

**Limits and prohibited inferences.** The abstract establishes topic fit, not
the independent-error details or exact restoration semantics. Do not assign a
numerical reliability requirement, equate the paper's event with `E_cap`, or
interpret design-time interval dependence as adaptive control without textual
support.

**Readiness.** **READY FOR PAPER ANALYST**.

### 5.4 PA-DOM-03-A — Boruzdina dissertation abstract

**Identity and gap.** `PA-DOM-03-A`; primarily RQ-002/RQ-006, with downstream
RQ-004/RQ-007 relevance. Mandatory source for multiple-upset experimental and
physical/logical classification methods.

**Selection reason.** Exact PI-provided target, official institutional and
national-catalogue identities controlled. The 2014 publication year and 2015
scheduled defence date are recorded separately.

**Access blocker.** Exact official MEPhI PDF returned HTTP 502. Acquire that
25-page dissertation abstract, not the 121-page dissertation page or a
secondary excerpt.

**Extraction questions.** After access, extract with page/figure anchors:

1. Define physical MCU, logical MCU/MBU, event multiplicity, and the partition
   or logical-block level used.
2. Identify the experimental observables: physical position, logical address,
   time coincidence, irradiation condition, read pattern, and error signature.
3. Extract every method that groups observed cell upsets into one parent-particle
   event; give thresholds/windows and ambiguity rules.
4. Extract methods for distinguishing direct same-particle multiplicity from
   independent accumulation or false grouping.
5. Determine how physical-to-logical mapping/topology `W` is known, inferred, or
   reconstructed and what remains unidentifiable.
6. Extract treatment of classification error, missed events, censoring, false
   positives/negatives, uncertainty, and validation.
7. Identify the output representation: topology, joint codeword-impact mark,
   marginal multiplicity, cross section, or scalar rate.
8. State what parent-event provenance and spatial/inter-word dependence each
   reduction retains or loses.
9. Identify device, technology, particle, LET, pattern, and test-domain limits.
10. Determine which propositions are only announced in the abstract and require
    the full dissertation or another specifically authorized source.

**Limits and prohibited inferences.** Abstract-only material cannot support a
full-method conclusion. Do not infer universal mapping sufficiency, a complete
probabilistic event model, a DEC-001 failure law, or an adaptive control input.
Do not add a third PA-DOM-03 methods paper without Orchestrator authorization.

**Readiness.** **NOT READY — OFFICIAL FULL TEXT PENDING**.

### 5.5 PA-DOM-03-B — topology paper

**Identity and gap.** `PA-DOM-03-B`; primarily RQ-002/RQ-006. Mandatory primary
topology paper DOI `10.1134/S1063739714020036`.

**Selection reason.** Exact DOI-controlled article, exact Russian/English
version relation, and direct topology/multiplicity fit at abstract level.

**Access blocker.** Publisher abstract is accessible; full text is
subscription-only. Acquire either the English version of record or the exact
Russian original and preserve the relation.

**Extraction questions.** After access, extract with page/figure anchors:

1. Enumerate the compared 6T-cell topological configurations and the physical
   mechanisms/assumptions linking topology to MCU susceptibility.
2. Identify whether multiplicity is physical-cell, logical-address, codeword,
   or device level.
3. Determine whether and how physical-to-logical placement `W` is represented.
4. Extract the evidence type: analytical, simulation, layout analysis,
   irradiation experiment, or a combination; record samples and conditions.
5. Identify quantitative outputs, uncertainty/bounds, and validation domain.
6. State which inter-cell/inter-word dependencies and parent-event provenance
   are retained or lost by the reported representation.
7. Compare only documented overlap with `PA-DOM-03-A`; do not infer that the
   article contains the dissertation methods.
8. Record explicitly what this paper cannot establish about online observation,
   scrubbing, ECC decoder outcomes, or adaptive control.

**Limits and prohibited inferences.** Do not infer topology-independent
generality, codeword impact, an operational estimator, or a controller from the
abstract. Do not attribute the paper to A. I. Chumakov.

**Readiness.** **NOT READY — FULL TEXT PENDING**.

## 6. HANDOFF TO ZOTERO

**Status:** structured local handoff only. No import is claimed.

**Target:** place accepted records in the existing dissertation literature
library under the RQ-007/integrated-control prior-art area according to the
local collection convention. Preserve cross-tags for `RQ-002`, `RQ-004`, and
`RQ-006`; do not create new permanent research-object IDs from this handoff.

**Common tags:**

- `rq/RQ-002`, `rq/RQ-004`, `rq/RQ-006`, `rq/RQ-007` as applicable;
- `prior-art/PA-DOM-01`, `prior-art/PA-DOM-02`, or `prior-art/PA-DOM-03`;
- `topic/memory-scrubbing`, `memory/SRAM`;
- `status/identity-controlled`;
- `access/full-text-controlled` or `access/full-text-pending`.

**Records and attachment expectations:**

1. `PA-DOM-01-A`: import by DOI
   `10.22184/1993-8578.2018.82.327.329`; verify complete six-author order,
   Russian title, issue 9 (82), pp. 327-329; attach the publisher PDF from
   `https://www.nanoindustry.su/journal/article/6802`.
2. `PA-DOM-01-B`: create/import the exact *Электронная техника. Серия 3:
   Микроэлектроника* 2018, no. 1 (169), pp. 68-76 record; no DOI was found;
   require the exact journal PDF. Link it as a related item to `PA-DOM-01-A`
   but set relation note `UNKNOWN — REQUIRES FULL-TEXT COMPARISON`.
3. `PA-DOM-02-A`: import by DOI `10.3103/S0027134917060133`; attach the
   author-uploaded English full text. Preserve the Russian-original title,
   *Вестник МГУ* no. 6, pp. 99-106 as a version note/related record, and retain
   the Springer 95-99 discrepancy as a metadata note rather than overwriting
   the official issue pagination.
4. `PA-DOM-03-A`: create/import the exact dissertation-abstract record using
   NEL ID `000200_000018_RU_NLR_BIBL_A_011098617`; record publication year 2014
   and scheduled defence date 2015-03-16 as separate fields/notes; attach the
   exact official MEPhI `_2014.pdf` when retrievable. Do not attach a secondary
   dissertation-page excerpt as the controlled PDF.
5. `PA-DOM-03-B`: import by DOI `10.1134/S1063739714020036`; verify the exact
   three-author order and attach the English VOR or exact Russian original
   obtained through institutional access. Record Russian pp. 88-93 and English
   pp. 96-101 as version-specific pagination.

**Duplicate policy:** DOI first; otherwise exact title + complete author order +
venue/year/pages. Keep Russian originals and English translations related, not
silently duplicated or merged when version-specific fields differ. Do not add
the rejected 2017 conference or 2016 predecessor solely from this handoff.

**Metadata checks:** title script, author order/transliteration, year versus
online-publication date, venue, issue, pages, DOI/identifier, document type,
version relation, attachment provenance, and PDF completeness.

## 7. Unit stop-rule dispositions

### PA-DOM-01

**Selected controlling set:** `PA-DOM-01-A` is the closest accessible primary
source; `PA-DOM-01-B` is the one bounded longer same-title candidate. This is a
two-record controlling candidate set, not a verified version family.

**Why bounded:** the set is limited to the exact target author group and exact
title. The 2017 conference and 2016 model predecessor are excluded from the
active set.

**Unresolved:** whether one source contains the complete
count-to-intensity-to-period chain; whether the two 2018 records are
substantively related; full-text access to `PA-DOM-01-B`.

**Paper Analyst readiness:** `PA-DOM-01-A` ready; `PA-DOM-01-B` pending and
should be requested only if the first analysis names a missing proposition.

**Stop rule:** **MET AS BOUNDED UNRESOLVED IDENTITY/ACCESS RESULT**. The closest
full-text target is named, the only bounded longer candidate is controlled, and
the exact blockers are explicit. No broader search is justified before the
first Paper Analyst pass.

### PA-DOM-02

**Selected controlling source:** `PA-DOM-02-A`, with the Russian original and
English author-translated DOI record controlled as versions of the same work.

**Unresolved:** substantive assumptions and restoration semantics remain for
Paper Analyst. The Russian official PDF transfer is unreliable, but the
author-uploaded English full text is available.

**Paper Analyst readiness:** ready.

**Stop rule:** **MET**. Exact identity, translation relation, and a full-text
target are controlled.

### PA-DOM-03

**Selected controlling pair:** `PA-DOM-03-A` dissertation abstract and
`PA-DOM-03-B` topology paper, exactly as required.

**Unresolved:** successful retrieval of the official dissertation-abstract PDF;
subscription full text for the topology paper; proposition-level relation
between the pair. The 2014 publication year and 2015 defence date are controlled
as different bibliographic dates, not two proven versions.

**Paper Analyst readiness:** not ready until the exact full texts are acquired.

**Stop rule:** **MET AS IDENTITY-CONTROLLED / ACCESS-PENDING RESULT**. Both
mandatory identities and access blockers are named. No third methods paper is
authorized.

## 8. Completion boundary

The bounded identity task is complete. The next authorized action is:

1. Paper Analyst review of `PA-DOM-01-A` and `PA-DOM-02-A`;
2. Zotero acquisition of the exact pending files for `PA-DOM-01-B`,
   `PA-DOM-03-A`, and `PA-DOM-03-B`;
3. Paper Analyst review of a pending source only after its exact full text is
   controlled.

No novelty/non-novelty conclusion, scientific acceptance, or final RQ answer is
made by this report.
