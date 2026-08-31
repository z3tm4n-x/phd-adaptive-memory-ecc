# NORMATIVE-BASELINE-01 — Radiation-test information-retention protocol

**Status:** `COMPLETED / ACCEPTED WITH LIMITATION`<br>
**Date:** 2026-08-28<br>
**Related:** DEC-002; RQ-002; RQ-006; EXP-001<br>
**Role handoff:** Paper Analyst, document-bounded normative extraction<br>
**Prohibited conclusion at this stage:** normative deficiency, target compliance or exact controlled-edition status beyond the evidence below

**Accepted output:** [NORMATIVE-BASELINE-01 clause-level extraction matrix](NORMATIVE-BASELINE-01_extraction_matrix.md), scientific-chain classification `PARTIAL — NAMED INPUT NEEDED`.

## 1. Objective

Reconstruct the supplied Russian normative chain from irradiation observations to reported ORE/SEE characteristics, environment-derived rate and probability indicator, and determine:

- what information exists during functional diagnosis and event classification;
- what is retained, transformed or aggregated when test observations become cross sections and sensitivity parameters;
- what is available downstream for physical-to-logical mapping `W`, ECC-aware `E_cap/F_A` and an adaptive restoration decision;
- which additional assumptions or data are required without presuming that address/topology information is absent or that the normative method is deficient.

## 2. Controlled source set and supplied-copy provenance

The labels below are task-local source labels, not `PAPER-xxx` identifiers.

| Label | Supplied source | SHA-256 / pages | Document-declared status | Supplied-copy caveat |
|---|---|---|---|---|
| `NORM-0174` | `РД 134-0174-2009`, methods for calculating charged-particle single-upset/failure resistance indicators from direct accelerator tests | `7de0db483fb6a912b0e8bcdbfff1b0cc46ff5216e0374e7cd4a05130584b8f37` / 27 pages | approved in the 2009 Q4 index; registered 07.12.2009 no. 19719; effective 2010-07-01 | PI-provided PDF; PDF metadata shows later Word/PDF regeneration in 2024, so metadata date is not an edition date and official controlled-copy identity is not independently established |
| `NORM-0175` | `РД 134-0175-2009`, accelerator test methods for digital VLSI under individual high-energy protons and heavy ions | `5cb73d6ac1c42aa8050d669d1e303898e528785c43c6ed7ec1e9a64adf4792dd` / 37 pages | approved in the 2009 Q4 index; registered 07.12.2009 no. 19720; the supplied copy states a 2012 reissue under notice no. 752-02-2012 with amendment 1 | PI-provided PDF; later 2024 PDF regeneration metadata does not prove the date or status of the normative edition |
| `NORM-STO0005` | `СТО ГК Роскосмос 04.01.0005–2022`, integrated order and typical methods for ionizing-radiation tests with facility-specific uncertainty | `80373578c8fc04349743f9d084ef831e329147f29d8d2e8c929d78d0bbab9ff5` / 248 pages | file states approval/enactment by Roscosmos order of 18.07.2022 no. LA-319-rsp, registration 25.07.2022 no. 22043 and effective date 2022-11-01 | the PDF text layer repeatedly contains `(Проект, окончательная редакция)` in white/hidden text while the visible preface states approval; exact controlled revision of this supplied file is therefore `AMBIGUOUS`, although the standard identity is independently listed by the developer/test institute |

Institutional corroboration for the standard identity and practical use: [АО «НИИ КП» / НТЦ-1 applicable-document listing](https://tlniikp.ru/services/ntc1/). This does not by itself resolve the supplied PDF's hidden draft label or prove that it is the controlled master copy.

## 3. Preliminary routing — not an accepted extraction result

- `NORM-0175` is the test-method branch: functional diagnosis, event-type registration, fluence, test conditions, cross-section estimation and uncertainty.
- `NORM-0174` is the calculation branch: experimental cross-section parameterization, convolution with declared space-radiation spectra, event/failure rate and probability over time.
- `NORM-STO0005` integrates and updates test procedures, explicitly covers SEU/MBU/MCU/SMU, delegates some identification criteria and diagnostic/software details to a private PMI, and separates direct registration from later processing.

These are routing observations for the handoff. The Paper Analyst must trace exact clauses, definitions, formulas and applicability before they become accepted evidence.

## 4. Required extraction matrix

For each stage below, record the exact document/clause, object, unit, provenance, uncertainty and whether the information is mandatory, optional, PMI-defined or absent:

| Stage | Required extraction |
|---|---|
| Irradiation input | particle class, energy/LET, flux/fluence, angle, sample/device conditions and facility uncertainty |
| Functional diagnosis | test patterns, read/write/scan sequence, temporal resolution, raw bit/address records, device state, recovery action and specialized software |
| Event reconstruction | parent-event association, time/grouping rule, physical versus logical address, topology, multiplicity, MBU/MCU/SMU criteria, false merge/split handling |
| Classified counts | what constitutes one ORE/SEE of each type, whether mechanism-specific counts remain separate, and how ambiguous events are disposed |
| Cross section | numerator/denominator, units, aggregation over samples/types/multiplicity, confidence interval and uncertainty sources |
| Sensitivity parameterization | fitted thresholds/saturation/shape parameters, model assumptions and information discarded by fitting |
| Environment convolution | radiation-environment input, angular/energy/LET integration, geometry/device scaling, stationary/nonstationary semantics |
| Rate and probability | event/failure rate definition, aggregation level, Poisson/exponential assumptions, horizon/initial state and relation to DEC-001 `F_A` |
| ECC/downstream interface | ECC, codewords, `W`, interleaving, scrubbing/reset, joint word impact and any unrepresented assumptions needed to reach `E_cap` |
| Traceability | what must remain in protocol/report/PMI/software output and whether raw data are retained after the normative reported characteristic is produced |

## 5. Mandatory questions

1. Does an observed upset address correspond to a physical cell coordinate, logical address, tested pattern location or another object?
2. What evidence permits several upset addresses to be assigned to one parent radiation event?
3. Are MBU, MCU and SMU definitions mutually consistent across the three documents and with the private PMI?
4. At what stage are topology, address, parent-event identity and multiplicity available, and at what stage are they aggregated?
5. Are separate cross sections required or permitted by multiplicity/type/mechanism, and how are they later recombined?
6. Which statistical assumptions apply only to event-count uncertainty and which are used to extrapolate mission-time arrivals?
7. Does the test protocol include correction, rewrite or reset during irradiation, and how does that affect accumulation observability?
8. What exactly is the aggregation object in `NORM-0174`: device, bit, sensitive region, failure type or another declared unit?
9. Which input spectra/environment documents and applicability conditions are required for the convolution step?
10. What probability indicator is produced, over which time origin/horizon and initial state, and under what assumptions is it comparable with DEC-001 `F_A`?
11. Which normative outputs can be used directly by RQ-002/RQ-006, which require augmentation by `W`/ECC information, and which are incompatible only for a stated target problem?
12. Is the apparently richer diagnostic/address information a mandatory retained artefact, a transient implementation detail, or a PMI-dependent option?

## 6. Relationship to RQ-002, RQ-006 and EXP-001

- **RQ-002:** identifies which event/rate/uncertainty parameters are empirically available and what observation model is needed.
- **RQ-006:** identifies whether topology/address/provenance sufficient for `W` is retained, reconstructible, PMI-dependent or lost before downstream use.
- **EXP-001:** remains synthetic and may run immediately. The normative matrix later determines which representation levels are realistically identifiable and which synthetic reductions correspond to actual engineering interfaces.
- **DEC-002:** requires the output to remain connected to ECC reliability and adaptive control; a stand-alone compliance summary is insufficient.

## 7. Accepted handoff

The draft artefact passed Orchestrator review and is canonical at:

`docs/normative_baseline/NORMATIVE-BASELINE-01_extraction_matrix.md`

It must include:

1. source/copy provenance and status table;
2. clause-level stage matrix from section 4;
3. exact formulas/variables for cross section → rate → probability, without importing numerical project requirements;
4. an information-retention graph/table from raw observation to normative output;
5. terminology conflicts across the three documents;
6. compatibility/augmentation/incompatibility matrix against DEC-001, RQ-002 and RQ-006;
7. list of source facts, project inferences and unknowns kept separate;
8. an exact list of additional normative documents or PMI fields required, each tied to one unresolved link;
9. recommendation: `SUFFICIENT FOR BASELINE SYNTHESIS`, `PARTIAL — NAMED INPUT NEEDED`, or `BLOCKED`.

Do not create `CLM`, `EVD`, `DEC`, `RES` or a normative-deficiency/novelty claim.

## 8. Exact PI material request already identifiable

The three supplied documents are sufficient to start the bounded extraction and do not block EXP-001. To close the **current/applicable** normative chain rather than only the 2009/2022 chain, request from the PI if available:

1. a controlled copy or registry extract resolving the exact approved edition of `СТО ГК Роскосмос 04.01.0005–2022`;
2. `ГОСТ РВ 0020–57.415–2020`, because the STO states that it supplements and is applied jointly with this standard for current developments;
3. `СТО ГК Роскосмос 04.01.0008–2024`, on setting and confirming radiation-resistance requirements for space EEE;
4. `СТО ГК Роскосмос 04.01.0010–2025`, on calculation/experimental evaluation of space EEE resistance to single-event effects;
5. one representative SRAM-specific private PMI, or a de-identified template plus the functional-diagnostic/software output schema, because MBU/MCU/SMU identification and the retained address/event fields are explicitly delegated to it.

The 2024/2025 standard identities are listed by the same institutional source linked above. Do not infer their content or replacement relationships until the exact documents are provided. Additional older references such as `ОСТ 134-1044-2007` should be requested only if the clause-level extraction shows that their unresolved input semantics block the chain.

## 9. Stopping criterion

Stop after all three supplied sources have an explicit disposition in every matrix row and every remaining unknown is tied to one exact missing document, PMI field or target-architecture input. Do not broaden into a general standards search.
