# Research Log

Журнал **значимых** действий, решений и изменений направления исследования. Не предназначен для записи каждого мелкого действия.

## 2026-08-26

### Infrastructure initialized

- Создан private GitHub repository `z3tm4n-x/phd-adaptive-memory-ecc`.
- Репозиторий назначен master-хранилищем собственного кода, моделей, экспериментов, результатов и provenance.
- Zotero назначен master-хранилищем внешней научной литературы.
- ChatGPT Project / Work используется как orchestration/analysis layer.
- Следующий milestone: `Research Specification v1.0`.

### Canonical state synchronized

- Infrastructure setup подтверждён как завершённый.
- Zotero setup подтверждён как завершённый.
- Текущая версия Research Specification — `v0.2-draft`.
- Текущая фаза изменена на подготовку Initial RQ Package.
- Следующий gate: утверждение 3–5 priority RQ и подготовка targeted literature mapping protocol.
- Окончательные `RQ-xxx` и гипотезы пока не зарегистрированы.

### AI-agent operating model established

- Создан canonical каталог `docs/agents/` с общими правилами и role cards для Orchestrator, Literature Scout, Paper Analyst, Evidence Auditor, Scientific Reviewer, Writing & Publications и Local Research Engineer/Codex.
- Зафиксирована иерархия источников истины: Zotero — внешняя литература; GitHub — собственное состояние исследования; primary sources + Scite — evidence layer; chat — временный рабочий контекст.
- Зафиксирована граница доступа: Cloud Work имеет прямой доступ к GitHub/Scite при подключённых коннекторах, но не к локальной Zotero Desktop library и локальному engineering toolchain.
- Для операций Zotero из Cloud Work введён structured handoff в локальный Codex/Zotero.
- Кандидатные Research Questions используют `C-RQ-xx`; постоянные `RQ-xxx` назначаются только после утверждения.

### Initial Research Questions registered

- Пользователь утвердил mapping: C-RQ-01 → RQ-001, C-RQ-02 → RQ-002, C-RQ-04 → RQ-003, C-RQ-06 → RQ-004, C-RQ-10 → RQ-005.
- Пять permanent RQ зарегистрированы в `docs/questions/` со scope, exclusions, dependencies, evidence requirements, decision criteria и next actions.
- Для RQ-001 numerical reliability threshold оставлен `TBD`, если отсутствует traceable source или system requirement.
- Для RQ-002 зафиксирован decision gate: существенность MCU/MBU или spatial correlation делает permanent RQ из C-RQ-05 обязательным до основной reliability model.
- Для RQ-005 первая стадия ограничена measurable resource-cost vector; scalar objective и optimization formulation оставлены C-RQ-11.
- Гипотезы не создавались.

### Targeted literature mapping protocols prepared

- Создан каталог `docs/literature_mapping/` и отдельные protocols для RQ-001…RQ-005.
- Protocols задают databases, concept blocks, reproducible search strings, screening, seed-paper и ResearchRabbit rules, Zotero tags/handoffs, evidence и stopping criteria.
- Литературный поиск намеренно не запускался.
- Dependency-aware order: RQ-001 → RQ-002 → RQ-003 → RQ-004 → RQ-005.
- RQ-001 выбран пилотом Literature Scout, поскольку его event/metric/horizon определяют evidence targets и decision semantics для последующих reliability и ECC questions.
- Новый active gate: принять воспроизводимый Literature Scout handoff по RQ-001 перед масштабированием mapping.

## 2026-08-27

### RQ-001 Literature Scout outputs registered

- Pilot report от 2026-08-26 и completion-delta report от 2026-08-27 сохранены в `docs/literature_mapping/` без редактирования содержания.
- После delta candidate register содержит 53 записи: 24 `CORE`, 16 `RELATED`, 3 `BACKGROUND`, 10 `REJECT`.
- Выполнены исходные IEEE Xplore queries, refinement queries, Scite bibliographic/editorial-signal checks и bounded ResearchRabbit expansion.
- Abstract-level mapping не интерпретируется как paper-level evidence и не отвечает на RQ-001.

### RQ-001 discovery disposition

- Пользователь решил пока не выполнять eLibrary search, поскольку eLibrary недоступна Literature Scout.
- eLibrary зафиксирована как `DEFERRED / UNKNOWN COVERAGE`, но не как нулевой результат и не как блокер текущего gate.
- Исходный protocol stopping criterion полностью не выполнен: eLibrary отсутствует, а refinement/expansion добавили новые категории.
- Orchestrator принял discovery как `SUFFICIENT FOR PAPER ANALYSIS — NOT EXHAUSTIVE`, поскольку все основные RQ-001 evidence dimensions имеют candidates, а оставшаяся неопределённость требует full-text extraction.
- Это явное stop-and-handoff decision, а не утверждение saturation, completeness, research gap или ответа на RQ.
- Numerical reliability threshold остаётся `TBD`; `HYP`, `CLM`, `EVD` и `RES` не создавались.

### Next gate: RQ-001 full-text extraction

- Выполнить Zotero handoffs из обоих Literature Scout reports.
- Получить verified full text для C45, C46 и C38.
- Paper Analyst создаёт отдельную Paper Card для каждого источника.
- Затем Orchestrator строит extraction matrix `event × metric × aggregation × horizon × assumptions` и определяет последующий evidence-review scope.
- RQ-002 не запускается до первичного evidence synthesis по RQ-001.
### RQ-001 Paper Cards formally accepted

- Research Orchestrator проверил три draft full-text Paper Cards по 19-section contract, source/inference discipline, page/equation provenance, scope limits и relevance to RQ-001.
- C45 принят как `PAPER-001` (`CORE`): Tausch, 2009.
- C46 принят как `PAPER-002` (`CORE`): Baeg, Wen, Wong, 2009.
- C38 принят как `PAPER-003` (`CORE`): Lee, Baeg, Reviriego, 2011.
- Внутренняя неоднозначность row-level wording в `PAPER-003` сохранена явно и не разрешена предположением.
- Acceptance относится к качеству аналитических карт; stochastic, architecture, mapping, illustrative-threshold и scrubbing assumptions публикаций не стали допущениями проекта.

### RQ-001 initial cross-paper evidence synthesis

- Создана canonical matrix `event × metric/units × aggregation × independent variable × horizon × ECC/decoder × scrubbing × statistics × mapping × mechanism × double-counting × limitations`.
- Зафиксировано согласие трёх papers относительно existential codeword event beyond correction capability, но выявлены несовместимые aggregate objects и horizons: upset count, elapsed time и deterministic scrub interval.
- Зафиксировано, что C45 исключает harmful direct MBU из основной формулы, а C46/C38 объединяют MCU-bearing arrivals и independent accumulation без сохранения causal provenance.
- Initial synthesis признан возможным, но final answer на RQ-001 не сформулирован; numerical reliability threshold остаётся `TBD`.
- До claim-level Evidence Auditor review дополнительные Paper Cards не требуются.

### Next gate: RQ-001 claim-level evidence audit

- Для Evidence Auditor отобраны 12 atomic candidate claims `RQ001-EA-CAND-01…12`; permanent `CLM-xxx` не создавались.
- Аудит должен проверить actual citation context, corrections/editorial concerns, scope match и strongest supporting/limiting evidence.
- RQ-001 переведён в `INVESTIGATING`; RQ-002 остаётся в очереди до review этого gate.

### RQ-001 Evidence Audit accepted with limitation

- Canonical Evidence Audit `RQ-001-EVIDENCE-AUDIT-01` принят после Orchestrator review.
- Поддержаны `RQ001-EA-CAND-01…09`, `11` и `12` в зафиксированных scope и confidence.
- `RQ001-EA-CAND-10` признан `PARTIALLY_SUPPORTED` и отложен: отсутствие word-specific exposure-age state подтверждено, но synchronous/effective global-reset interpretation не принято.
- Scite statement counts не использованы как evidence; contextual audit sources требуют Zotero reconciliation до цитирования в publication text.
- Опечатка `seven exact claims` в initial synthesis исправлена на `twelve exact claims`.
- Новые Paper Cards, literature search, `EVD`, `HYP` и `RES` не создавались.

### RQ-001 permanent claims registered

- `CLM-001` — count horizon requires arrival and repair semantics before time interpretation.
- `CLM-002` — harmful same-particle MBU is outside the main PAPER-001 equation.
- `CLM-003`/`CLM-004` — PAPER-002/PAPER-003 totals do not preserve failed-word mechanism provenance.
- `CLM-005`/`CLM-006` — adding an unpartitioned direct-MCU term overlaps those totals under matched event, scope, horizon and units.
- `CLM-007` — PAPER-002 upper-bound reading is conditional on MCU span relative to interleaving distance.
- `CLM-008` — the audited papers model multiplicity beyond ECC capability, not decoder or service outcome.
- Candidate facts 01–03 remain traceable through the Paper Cards and matrix rather than redundant permanent claims.

### Next gate: RQ-001 provisional definition approval

- Подготовлен `docs/evidence_synthesis/RQ-001_provisional_definition_package.md`.
- Package proposes `E_cap(A,H)`, `F_A(H)`, a controller-protected SRAM aggregate, layered horizon semantics and separation from DUE/SDC/system consequences.
- `H_req` and `ε_req` remain `TBD`; illustrative values from the papers are not project requirements.
- Until explicit approval, RQ-001 remains `INVESTIGATING` and RQ-002 remains queued.

### DEC-001 accepted — RQ-001 working reliability contract

- Пользователь утвердил все шесть решений RQ-001 с уточнениями notation and aggregation.
- `E_cap` принят как primitive ECC-capability-exceedance event; automatic equivalence to DUE, SDC, miscorrection or system-visible failure запрещена.
- General reporting window фиксируется как \(H(t_0,T)=[t_0,t_0+T]\); metric сохраняет start time и declared initial state/distribution: \(F_A(t_0,T;\mu_{t_0})\).
- `F_A(T)` разрешена только как сокращённая форма при явном time origin и initial state.
- Default aggregate — explicitly declared controller-managed protection domain \(A\); heterogeneous ECC, \(W\), arrival, bank/block or scrubbing semantics require partitioning before quantitative aggregation.
- Per-codeword/sequential exposure semantics classified as `WORKING DEFINITION / MODELING REQUIREMENT`, not literature fact; CAND-10 remains deferred.
- Decoder/system outcomes, \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) remain `OPEN/TBD`.
- Decision зарегистрирован как `DEC-001`; numerical reliability requirement, `HYP`, `EVD` and `RES` не создавались.

### RQ-001 partial disposition and RQ-002 gate opening

- RQ-001 переведён в `PARTIALLY ANSWERED / OPEN DEPENDENCIES` and remains open.
- Research Specification advanced to `v0.3-draft` to record the accepted working contract.
- RQ-002 gate открыт with DEC-001 as its event/metric/domain input contract.
- RQ-003 retains responsibility for decoder-outcome semantics.
- RQ-002 protocol aligned with DEC-001; eLibrary explicitly remains `DEFERRED / UNKNOWN COVERAGE` for Literature Scout.
- RQ-002 literature search was not started in this recording step.
- Next action: issue the exact Literature Scout handoff from `docs/literature_mapping/RQ-002_protocol.md` and apply the C-RQ-05 MCU/MBU/spatial-correlation escalation rule.

### RQ-002 protocol expanded before Literature Scout launch

- IEEE Xplore retained as mandatory anchor but rejected as the sole sufficient database route for RQ-002.
- Added a mandatory independent cross-publisher route: Scopus preferred; Web of Science or Compendex/Inspec accepted substitutes.
- Added public Crossref/OpenAlex fallback when all subscription indexes are inaccessible, with an explicit coverage limitation.
- Added targeted ScienceDirect and SpringerLink searches, including mandatory checks of non-IEEE reliability/radiation/testing venues.
- Added NASA NTRS as a supplemental technical-evidence route; report/presentation status must not be confused with peer review.
- Scite remains secondary discovery/context and ResearchRabbit remains bounded citation expansion.
- eLibrary remains `DEFERRED / UNKNOWN COVERAGE` and must not be queried by Literature Scout in this cycle.
- Stopping criterion now requires cross-publisher coverage, targeted publisher backfill, source-access reporting and the eight-category DEC-001 compatibility matrix.
- Exact Literature Scout launch handoff is ready against the expanded protocol.
- RQ-002 literature search had not started when this protocol update was recorded.

### Pre-RQ-002 external-review correction accepted

- External-advisor review classified as `UNVERIFIED`: it supplies adversarial search targets but is not `SOURCE`, project evidence or a research decision.
- DEC-001 was not revised and RQ-001 was not reopened.
- Mandatory RQ-002 anchors added: C32, C51, C52, Zebrev-2015, exact `arXiv:1704.07271v2`, and the separately controlled related RADECS DOI identity.
- Exact-version control and a 15-question Paper Analyst extraction target were added for the extended Zebrev arXiv v2 source.
- Direct same-particle, independent accumulation and ambiguous/false test classification must now be compared at physical, spatial, post-`W` and rate/recombination levels.
- Candidate model-class sensitivity and the minimum post-mapping event-representation hierarchy were added without preselecting Poisson, Cox, PDMP, marked processes, association or marginal `q_k`.
- The active failure domain remains transient radiation-induced upsets; permanent faults, cumulative TID degradation and destructive/persistent effects remain out of scope pending a separate decision.
- Canonical DEC-001 symbols were registered in `docs/terminology.md`; no new numerical requirement was assigned.

### Novelty and post-mapping throughput gates registered

- Created `docs/novelty_workflow.md`: claims used for novelty assessment require a separate adversarial gap-closure pass, and scope-limited claims cannot become general literature claims by downstream use.
- `CLM-002…006` remain valid only over `PAPER-001…003`; a mandatory RQ-002 novelty-threat matrix must cover the strongest mechanism-partition threats before any general novelty statement.
- Created `docs/research_backlog.md` with a separate, non-blocking future inspection/maintenance/control prior-art task covering the Barlow/Proschan/Keller line and specified reliability/OR venues.
- Registered the post-RQ-002 throughput gate: select decisive deep reads, bound model alternatives, build a minimal quantitative prototype, define the first discriminating `EXP` and target the first verifiable `RES` before another broad discovery cycle.
- Registered future specialty/implementation alignment and the non-blocking publication trigger after the first independent `RES`.

### RQ-002 Literature Scout launched

- Task `RQ-002-LITERATURE-MAPPING-01` was issued against the corrected protocol.
- eLibrary remains `DEFERRED / UNKNOWN COVERAGE` and is not part of this Scout cycle.
- The next Orchestrator gate is acceptance of the reproducible mapping report, mandatory-anchor/version dispositions, C-RQ-05 assessment, novelty-threat matrix and bounded Paper Analyst handoff.
- No new `RQ`, `HYP`, `CLM`, `EVD`, `DEC`, `EXP` or `RES` was created by this launch.

### RQ-002 initial literature mapping accepted with access limitations

- The Literature Scout report was stored canonically as `docs/literature_mapping/RQ-002_literature_mapping_initial_2026-08-27.md` and accepted as sufficient for bounded decisive full-text reads.
- The report is not treated as proof of saturation or as an answer to RQ-002: ResearchRabbit was unavailable and OpenAlex F4–F9 were not completed.
- All mandatory anchors received explicit dispositions, including exact `arXiv:1704.07271v2` and the separately controlled RADECS DOI identity.
- Discovery evidence operationally triggers the C-RQ-05 escalation condition because topology, interleaving and mapping `W` cannot yet be safely excluded or bounded. No permanent RQ was created; explicit user acceptance remains required.
- Five decision-enabling Paper Analyst work units were selected: C001; C005 with C006 version comparison; C008; C011; and C020.
- No second general literature cycle, model selection, numerical reliability requirement, `PAPER`, `CLM`, `HYP`, `DEC`, `EXP` or `RES` was created by this disposition.
- Next gate: `RQ-002-PA-BATCH-01`, followed by Orchestrator acceptance and a bounded cross-paper model-selection matrix.

## 2026-08-28

### RQ-002 Paper Analyst Batch 01 formally accepted

- Provenance corrections in base commit `314b040de3bd8096ba1114edf1dc165da06e2360` were verified; no blocking identity issue remains.
- Five complete, traceable full-text cards were accepted: RQ2-C001 → `PAPER-004`, RQ2-C005 → `PAPER-005`, RQ2-C008 → `PAPER-006`, RQ2-C011 → `PAPER-007`, and RQ2-C020 → `PAPER-008`.
- RQ2-C006 remains a controlled peer-reviewed companion identity inside `PAPER-005`; it did not receive a separate `PAPER` ID because the accepted work unit is the exact arXiv-v2/RADECS version comparison rather than two independent analytical cards.
- Acceptance covers analytical-card quality, identity control, extraction completeness and fitness for synthesis. It does not adopt source assumptions, accept candidate claims, select an error-process family or establish novelty.
- The cross-paper matrix was accepted as `docs/evidence_synthesis/RQ-002_initial_evidence_synthesis.md`. It preserves differences in primitive event, arrival law, topology, mapping `W`, accumulation state, repair, observation error, aggregation and horizon.
- The batch narrows but does not resolve the alternatives: marked HPP/NHPP, compound/event-driven models, direct-plus-accumulation constructions, scan/repair state models and observation-aware latent-event models remain conditional.
- C-RQ-05 escalation is confirmed by full-text evidence; permanent promotion remains an explicit PI decision.
- No additional Paper Card or broad discovery cycle is authorized without a named gap that blocks model selection, adequacy, validation or the first own-result experiment.

### PI scientific-direction update accepted as DEC-002

- The approved dissertation core remains adaptive control of the memory-restoration period under a declared/parameterized reliability requirement and measurable restoration-resource cost.
- `DEC-002` records one integrated causal architecture: radiation-test evidence → identifiable device-error representation → mapping `W`/ECC → ECC-level reliability → observable risk → adaptive restoration decision.
- The working scientific problem is to establish the sufficiency, observability and quantitative price of information reduction between radiation testing and the adaptive decision; richer event information is not presumed superior.
- Applicable Russian normative practice is elevated to a primary practical baseline. No normative deficiency may be claimed before controlled document extraction.
- Identification/mapping, normative-practice and adaptive-control prior-art threats remain separate. Chen/IHP/Potsdam stays an active close threat for the control layer; Franco/Zebrev/Ogden/Gomi and related sources cover different layers.
- Missing numerical `H_req`/`ε_req`, final observables, final cost scalarization or hardware selection do not block a parameterized representation-sensitivity prototype.
- `DEC-001` and RQ-001 remain unchanged. No new `RQ`, `CLM`, `HYP`, `EXP` or `RES` was created automatically.

### RQ-002 Evidence Audit 01 accepted with limitation

- Draft audit commit `1961ec77d11b3d0ee56009d41b1cb361cfb1f369` was reviewed against the Evidence Auditor role contract and accepted canonically as `docs/evidence_audits/RQ-002_EVIDENCE_AUDIT_01.md`.
- `RQ002-EA-CAND-01…03` and `05…10` are accepted only in the report's precise scoped wording.
- `RQ002-EA-CAND-04` remains `PARTIALLY_SUPPORTED`: marginal per-word statistics cannot be assumed sufficient, but universal insufficiency is not established. Joint-versus-marginal sufficiency becomes an experiment target.
- No permanent `CLM`/`EVD` was created. No additional Paper Card or general RQ-002 literature cycle is required before the first prototype.

### Chen/IHP/Potsdam identity output accepted at discovery level

- Identity-resolution commit `0b8864155c47bd8cb28fa0bd96be9fe23f6b96cb` was accepted as an identity/discovery record, not paper evidence or novelty adjudication.
- The closest family is controlled as a 2025 JETTA consolidated source, a separate 2023 DFT controller disclosure and a separate 2024 LATS evaluation branch.
- A bounded three-source full-text Paper Analyst comparison is authorized in parallel with EXP-001. The 2020/2022 prediction sources remain upstream context unless a named gap requires them.

### C-RQ-05 permanently promoted to RQ-006

- Explicit PI approval registered C-RQ-05 → `RQ-006`.
- RQ-006 owns physical event topology, `W`, interleaving, joint post-`W` impact and exactness/bounds/error of representation reduction.
- RQ-002 retains arrival/event/state modelling; RQ-003 retains concrete ECC/decoder outcomes.
- RQ-006 remains `OPEN`; no answer, hypothesis, result or novelty claim was created by registration.

### DEC-003 and EXP-001 registered

- `DEC-003` passed the bounded literature/model-selection gate for prototype work without selecting HPP, NHPP, Cox, PDMP or another universal target family.
- The comparison reference preserves parent-event provenance, physical topology, explicit `W`, joint codeword impact, initial state, repair transitions and DEC-001 first-passage semantics.
- `EXP-001` was registered to compare `L0` full topology + `W`, `L1` joint post-`W` marks, `L2` marginal word statistics and `L3` scalar rates.
- `L0 → L1` must be lossless for the declared state update. `L2/L3` have no pre-assigned direction; both invariance and material decision change are admissible results.
- Numerical reliability requirements remain swept parameters. EXP-001 does not validate a target SRAM model or establish a normative deficiency/novelty claim.

### Three-document Russian normative source set registered

- PI-provided `РД 134-0174-2009`, `РД 134-0175-2009` and `СТО ГК Роскосмос 04.01.0005–2022` were fingerprinted and routed into `NORMATIVE-BASELINE-01`; PDFs were not committed.
- The supplied RD 0175 copy states a 2012 reissue with amendment 1. Both RD PDFs contain later 2024 regeneration metadata, which is not treated as an edition date.
- The supplied STO file states approval, registration and a 2022 effective date, but its text layer also contains repeated hidden white-text `Проект, окончательная редакция` labels. Standard identity/use is externally corroborated, while exact controlled-copy status remains `AMBIGUOUS`.
- Preliminary inspection confirms that functional diagnosis and later processing can be separate stages and that MBU/MCU/SMU criteria and diagnostic software are PMI-dependent. No conclusion about normative information sufficiency or deficiency was accepted.
- A bounded clause-level Paper Analyst handoff was defined. It runs in parallel and does not block the synthetic EXP-001.

### Current gate and PI material request

- Active gate: Research Engineer implementation/tests/configuration for EXP-001, followed by Scientific Reviewer inspection before any `RES-xxx`.
- Parallel non-blockers: three-document normative extraction and three-source Chen full-text comparison.
- Exact requested material for the current/applicable normative chain: controlled-copy/registry evidence for STO 04.01.0005–2022; ГОСТ РВ 0020–57.415–2020; STO 04.01.0008–2024; STO 04.01.0010–2025; and a representative/de-identified SRAM private PMI plus diagnostic/software output schema.
- No additional PI decision is required to start EXP-001.

### PI clarification incorporated into EXP-001

- `DEC-003` and the experiment roadmap remain unchanged.
- EXP-001 now requires a machine-checked `J-A`/`J-B` post-`W` discriminator with identical per-word marginal multiplicity distributions and different joint inter-word dependence / parent-event association.
- The discriminator compares both `F_A` and the parameterized restoration decision without assuming the sign or existence of an effect.
- Failure of one `L2` reconstruction is explicitly limited to that rule and tested domain; it cannot establish universal insufficiency of marginal per-word statistics.
- Phase 1 selects `L3-U`, an ungrouped scalar bit/upset-arrival primitive. The distinct scalar parent-event-rate primitive `L3-E` is deferred and may not be substituted silently for `L3-U`.
- The Research Engineer implementation handoff is ready against the corrected EXP-001 specification.

## 2026-08-31

### EXP-001 implementation technically accepted for Scientific Reviewer

- Research Engineer commit `84728d1b5768e7c91c508495d696c5980943ae57` was reviewed against DEC-003, the registered EXP-001 specification and the fixed manifests.
- All 17 tests pass; `L0/L1` has zero mismatches over 768,000 trajectory checks and 288,302 converted event marks; all J-A/J-B invariants and statistical precision rules pass.
- An independent Linux execution reproduced the scientific aggregate, decision, delta and invariant outputs byte-for-byte from the committed Windows run. Only platform-dependent runtime and peak-memory values changed.
- Implementation and reproducibility are accepted; scientific interpretation remains pending adversarial Scientific Reviewer review. No `HYP-xxx` or `RES-xxx` was created.
- An Orchestrator algebra precheck supports, but does not yet accept, the proposed four-word identified-set derivation with `1/6 <= q <= 1/2` and `F_A=1-S(q,m)^k`.
- A mandatory interpretation correction was recorded: at experimental `epsilon=0.55`, exact J-A and J-B both select `T_scrub=4`; the reported Wilson-rule 4-versus-2 difference is confidence-bound conservatism, not a purely structural decision discrepancy.

### Russian normative baseline accepted with limitation

- The three-document clause-level extraction was accepted as `NORMATIVE-BASELINE-01` with scientific-chain status `PARTIAL — NAMED INPUT NEEDED`.
- The practical chain from diagnostic observations and PMI/software classification through counts, cross sections, sensitivity representation, environment convolution and scalar probability is accepted as a bounded source extraction.
- No normative deficiency, compliance conclusion or automatic equivalence to `W`/`E_cap`/`F_A` was inferred.
- The two RD hash pairs were normalized administratively as canonical PI-supplied copy versus Paper Analyst processed copy; the difference is not a scientific blocker absent a material content difference.
- The STO controlled-edition ambiguity remains explicit. PMI/log/address semantics, target `W`/ECC, initial state, restoration and current-applicability documents remain named downstream inputs.

### Chen S3/S4/S5 Paper Cards and comparison accepted

- CONTROL-S3 → `PAPER-009` (`CORE`), CONTROL-S4 → `PAPER-010` (`RELATED`) and CONTROL-S5 → `PAPER-011` (`CORE`) were formally accepted after full-text provenance, source/inference discipline and version-relation review.
- The canonical S3/S4/S5 matrix is accepted with limitation and is ready for a bounded Evidence Auditor comparison against DEC-002.
- S3 is the controller-disclosure source within the controlled family, S4 is a separate reactive HSIAO evaluation branch, and S5 is a real but bounded consolidation/extension. Their metrics, assumptions and numerical inconsistencies remain version-specific.
- Eight exact candidate statements were selected for audit. No `CLM-xxx`, novelty conclusion, broad control search or project control model was created.

### Next canonical gate

- Scientific Reviewer: verify EXP-001 implementation fairness, statistics, the analytical identified-set claim and exact/estimated/robust feasibility separation.
- Evidence Auditor: verify the eight scoped Chen-family feature/limitation statements.
- After both returns, the Orchestrator will accept/reject a narrowly bounded `RES-001` and, if justified, preregister the next hypothesis/experiment over physically plausible `W`/topology/event statistics.
- No additional PI decision is required at this gate.

### EXP-001 Scientific Review 01 accepted with REVISE disposition

- Scientific Reviewer commit `8f03ece7cda635c10413d404a02f44d8be0bca11`
  was accepted canonically as
  `docs/scientific_reviews/EXP-001_SCIENTIFIC_REVIEW_01.md`.
- The review found no `CRITICAL` issue and accepted the bounded J-A/J-B
  parameterization, `1/6 <= q <= 1/2`, exact `S(q,m)`/`F_A`, endpoint attainment
  and identified-set interpretation under the complete fourteen-condition
  validity domain.
- Exact endpoint decisions differ at experimental `epsilon=0.15`, `0.25` and
  `0.35`; the `epsilon=0.55` Wilson-rule discrepancy is not structural.
- `MAJOR-01` is accepted as demonstrated: production L0 and L1 reuse mapping and
  state-transition code, so the 768,000 zero-mismatch checks are
  outcome/final-signature comparisons rather than independent full-trajectory
  validation.
- EXP-001 status is `REVISE / VALIDATION REPAIR REQUIRED`; no `RES-xxx` or
  retroactive `HYP-xxx` was created.

### Chen control-prior-art Evidence Audit accepted

- Evidence Auditor commit `1798a2c677fa3003c91e120dfd99d0557b9c0477`
  was accepted canonically as
  `docs/evidence_audits/CONTROL-PRIOR-ART_EVIDENCE_AUDIT_01.md`.
- Candidates 1, 2, 4, 5, 6, 7, 8a and 8b are accepted only within the controlled
  S3/S4/S5 family. Candidate 3 is accepted after correcting the claim that S5
  first adds `t+1`: S5 newly specifies the six-hour input and makes S3's
  already-present next-hour target explicit.
- The family is confirmed as close prior art for observation/fault-count input,
  forecast or reactive assessment and adaptive scrub-frequency selection.
- The bounded absence of explicit `W`, DEC-001 first-passage risk, propagated
  uncertainty, a measured multi-component resource vector or a complete deployed
  loop is not a novelty claim. No `CLM-xxx`/`EVD-xxx` was created and no new
  Chen-family Paper Card is authorized without a named blocker.

### Roadmap advanced to validation repair and RQ-003 interface

- The immediate gate is `EXP-001-VALIDATION-REPAIR-01`, followed by a bounded
  Scientific Reviewer re-review. A passing disposition makes a narrow
  `RES-001` admissible but does not create it automatically.
- RQ-003 is now the active next scientific interface; its protocol requires a
  current-gate revision and eLibrary remains deferred for Literature Scout.
- A candidate integrated adaptive-control RQ was prepared in
  `docs/research_backlog.md` without consuming a permanent ID. It combines
  uncertainty-aware ECC first-passage assessment, adaptive restoration action and
  a separate measurable resource vector, and requires explicit PI acceptance
  before permanent registration.
- The next quantitative target is a general information-set/model-set to
  `F_A`-bound to robust-restoration-decision interface over a physically
  defensible domain, not another isolated dependence counterexample.

## 2026-08-31

### EXP-001 validation repair accepted for bounded re-review

- Research Engineer repair commit
  `072b70adabb9827ee59c94b2b3d5cf044b25cdf9` is exactly one commit over canonical
  base `0ca6f13481ea0818c59395ead26db2f58cb6188e`.
- Orchestrator inspection accepts the independent test-only L0 oracle, separate
  full-trace comparison of production L0 and L1, exhaustive 8x8 mapping checks,
  mutation/sentinel evidence and all four Scientific Review MINOR corrections.
- Independent verification passed 32/32 tests and `compileall`. A clean fixed
  rerun satisfied all precision and analytical-precondition rules and reproduced
  the seven scientific files and `analytical-validation.json` byte-for-byte.
- EXP-001 status advances to `VALIDATION REPAIR ACCEPTED / SCIENTIFIC RE-REVIEW
  PENDING / NOT RES-xxx`. Scientific Review 01 remains `REVISE`; no retrospective
  `HYP-xxx` or `RES-001` was created.
- PI-provided Meshchanov/Lushnikov/Krasnikov, Podzolko,
  Boruzdina/Ulanova/Chumakov and Zebrev/Galimov prior-art signals are recorded as
  `UNVERIFIED` bounded backlog only. They do not alter EXP-001 or authorize a
  broad literature campaign.
- The post-EXP direction is retained as
  `I -> M(I) -> F_A value/set/bound -> admissible actions -> T_scrub -> resource
  cost`, with the quantitative target of the control-resource price of
  information deficit.

### EXP-001 Scientific Review 02 accepted; bounded result candidate prepared

- Scientific Reviewer commit
  `d76850f47826cc5c9cf693fae8b581b3dcc2542e` was reviewed as the direct child
  of accepted Orchestrator disposition
  `222e9303724c1e0f8f0986c1d4e53c754c47cf23`.
- `EXP-001-SCIENTIFIC-REREVIEW-02` returns `PASS`: `MAJOR-01` and
  `MINOR-01…04` are closed, no new issue or scientific-output regression is
  reported, and the complete fourteen-condition validity domain is preserved.
- PI accepts the Orchestrator disposition and closes the EXP-001 corrective
  gate.
- A bounded first-result candidate is stored as
  `docs/result_candidates/DRAFT-RES-001-exp001-four-word-identified-set.md`.
  It is not registered as `RES-001` and requires explicit PI wording approval.
- The candidate states only the exact identified set for the reviewed synthetic
  four-word class and the conditional action change/invariance observed on the
  declared experimental grid. It preserves the separation of representation,
  Monte Carlo and decision-rule uncertainty and creates no retrospective
  `HYP-xxx`.
- No new experiment is authorized before PI disposition of the candidate.

### DRAFT-RES-001 wording-only revision incorporated

- PI accepted the scientific content of `DRAFT-RES-001` and returned
  `REVISE — wording only`; EXP-001, its calculations and Scientific Review 02
  remain closed and unchanged.
- The central statement now uses the proved object: identical one-event
  per-word marginal impact probabilities with mandatory parent-event
  cardinality of exactly two distinct words.
- The control consequence is separated correctly: at experimental
  `epsilon=0.15`, J-A admits `T_scrub=0.5` while J-B admits no period in the
  tested action set; at `0.25` and `0.35`, the maximal feasible selected period
  differs; at `0.55`, the exact selected action is identical.
- All formulas, the exact decision table, fourteen validity conditions,
  uncertainty separation and explicit non-claims remain unchanged.
- The candidate is resubmitted for final PI `ACCEPT`; no permanent `RES-001`,
  new experiment, calculation, hypothesis or review is created by this edit.

### RES-001 permanently registered after final PI ACCEPT

- PI issued final `ACCEPT` for the wording-revised first-result candidate and
  explicitly authorized permanent registration.
- The candidate was promoted without scientific expansion to
  `results/RES-001-exp001-four-word-identified-set.md`; formulas, exact decision
  table, all fourteen validity conditions, three uncertainty objects and every
  explicit non-claim are preserved.
- EXP-001 is now `COMPLETE / INDEPENDENT VALIDATION PASS / SCIENTIFIC REVIEW
  PASS / PROMOTED TO RES-001` only within that exact scope.
- At experimental `epsilon=0.15`, RES-001 records different admissible-action
  sets; at `0.25` and `0.35`, different maximal feasible selected periods; at
  `0.55`, identical exact selected actions. The `epsilon` values are not project
  requirements.
- No retrospective `HYP-xxx`, physical-SRAM generalization, numerical
  reliability requirement or novelty claim was created.

### Next information-deficit control-price gate prepared for PI disposition

- A directional draft was created in `docs/research_gates/`; it is not an `RQ`,
  `DEC`, `HYP`, `EXP`, `RES` or novelty claim and does not authorize execution.
- The proposed chain is `I → M(I) → F_A value/set/bound → admissible actions →
  T_scrub → measurable resource-cost vector`, with explicit conditional
  action-invariance and robust-feasibility objects.
- The draft requires a physically defensible event/`W` domain, controlled
  projection of common underlying models, separate model/observation/numerical
  uncertainties and a component-wise cost result without arbitrary
  scalarization.
- Minimum interfaces are assigned to RQ-002/RQ-006 and bounded slices of
  RQ-003/RQ-004/RQ-005. The prepared integrated adaptive-control question is
  proposed as future `RQ-007` but remains unregistered pending explicit PI
  acceptance.
- The domestic prior-art boundary is limited to four work units over the
  Meshchanov/Lushnikov/Krasnikov, Podzolko, Boruzdina/Ulanova/Chumakov and
  Zebrev/Galimov lines, with common extraction columns and a hard stop rule.
- No new EXP may start until PI approves/revises this gate, the bounded prior-art
  closure is complete, the integrated RQ is registered and a reproducible
  experiment/derivation is preregistered.
