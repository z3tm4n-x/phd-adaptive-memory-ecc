# Current Status

**Updated:** 2026-08-31

## Current phase

EXP-001 has passed independent validation and Scientific Reviewer re-review.
The corrective and scientific-review gates are closed. After final PI `ACCEPT`,
the exact bounded statement is registered as
[`RES-001`](../results/RES-001-exp001-four-word-identified-set.md), and EXP-001
is complete/promoted only within that scope. The bounded Chen/IHP/Potsdam
Evidence Audit constrains the control-method target, and the Russian normative
baseline remains accepted with explicit unresolved interfaces.

The controlling [DEC-002](decisions/DEC-002-integrated-evidence-to-adaptive-control-roadmap.md)
architecture is unchanged:

`radiation-test evidence → identifiable device-error representation → W/ECC organization → ECC-level reliability → online risk assessment → adaptive restoration decision`.

Adaptive restoration control remains the final/core dissertation layer.

## Active scientific gate

The active gate is PI disposition of the
[`Next quantitative gate — Information-deficit price for restoration control`](research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md).
It proposes the bounded transition
`I → M(I) → F_A value/set/bound → admissible actions → T_scrub → measurable resource cost`
over a physically defensible event/`W` domain.

The gate is a directional draft, not an `RQ`, `DEC`, `HYP`, `EXP`, `RES` or
novelty claim. No new experiment, broad literature cycle or permanent integrated
adaptive-control RQ is authorized by its preparation. A new quantitative EXP
remains blocked until PI approves/revises the gate, the named minimum prior-art
closure is complete, the integrated control RQ is explicitly registered and a
reproducible experiment/derivation is preregistered.

## Active Research Questions

- RQ-001 — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`; DEC-001 unchanged.
- RQ-002 — `OPEN / RES-001 BOUNDED RESULT REGISTERED / NEXT GENERALIZATION GATE DRAFTED`.
- RQ-003 — `OPEN / ACTIVE NEXT INTERFACE`; owns parameterized ECC capability,
  state and decoder-outcome semantics and must keep `E_cap` distinct from
  DUE/SDC/miscorrection/system-visible outcomes.
- RQ-004 — `OPEN / REQUIRED NEXT-GATE INTERFACE`; must distinguish external exposure information
  from internal protected-memory state/history and propagate observation
  uncertainty to the risk interface.
- RQ-005 — `OPEN / REQUIRED NEXT-GATE INTERFACE`; retains the measurable multi-component resource
  vector without premature scalarization.
- RQ-006 — `OPEN / RES-001 BOUNDED RESULT REGISTERED / NEXT GENERALIZATION GATE DRAFTED`; owns `W`, topology, joint post-`W`
  impact and reduction-sufficiency/bound conditions.

The future integrated adaptive-control question is prepared as a candidate in
[`research_backlog.md`](research_backlog.md), but is not permanently registered.
It requires explicit PI acceptance of its final wording/ID before control-method
development. Because the proposed next stage maps risk information to a
restoration action, its registration is a prerequisite for executing that stage.

## EXP-001 disposition

### Accepted findings within the reviewed model class

Scientific Reviewer independently accepted:

- the pair-probability parameterization;
- `1/6 <= q <= 1/2`, with J-B and J-A attaining the two endpoints;
- `S(q,m)=exp(-m)[1+m+q m^2/2]` and the aligned reporting-window `F_A`;
- the identified-set interpretation within the complete fourteen-condition
  validity domain in review Section 7.4;
- the separation of representation/dependence uncertainty, Monte Carlo
  estimation uncertainty and CI-decision conservatism;
- exact endpoint decision differences at experimental `epsilon=0.15`, `0.25`
  and `0.35`, but not at `epsilon=0.55`.

These accepted findings are registered only as the bounded
[`RES-001`](../results/RES-001-exp001-four-word-identified-set.md). They do not
bound physical SRAM topology or establish universal insufficiency of marginal
models.

### Validation-repair disposition

The original 768,000 L0/L1 comparisons remain correctly labelled as
outcome/final-signature comparisons. The repair adds a bounded, independent
full-trace validation layer rather than relabelling the production run.
Scientific Review 02 confirms closure of the demonstrated shared-path weakness
without changing configurations, scientific outputs or the EXP-001 question.
EXP-001 is now `COMPLETE / SCIENTIFIC REVIEW PASS / PROMOTED TO RES-001`.

## Chen/IHP/Potsdam control-prior-art disposition

[CONTROL-PRIOR-ART Evidence Audit 01](evidence_audits/CONTROL-PRIOR-ART_EVIDENCE_AUDIT_01.md)
is `ACCEPTED WITH BOUNDED WORDING CORRECTION`.

- Candidates 1, 2, 4, 5, 6, 7, 8a and 8b are accepted only within the controlled
  S3/S4/S5 family.
- Candidate 3 is accepted only after correcting the claim: S5 newly specifies
  the six-hour input window and makes the already-present next-hour target
  explicit; it does not first add the `t+1` target.
- S5 is the strongest single architecture comparator; S3 remains necessary for
  feature provenance and S4 for the separate reactive HSIAO branch.
- No additional Chen-family Paper Card is required now.
- No permanent `CLM`/`EVD`, novelty or non-novelty conclusion is created.

The controlled family is genuine close prior art for online fault-count/rate
input, next-hour point prediction or reactive assessment, and adaptive
wash/scrub-frequency selection. Generic adaptive scrubbing, ML-to-frequency,
online fault counts and scrub-count reduction cannot be project novelty claims.

The accepted bounded differences become method-design axes only if the project
makes them operational and demonstrates a quantitative reliability, uncertainty,
decision, resource or implementation consequence.

## Russian normative baseline

[NORMATIVE-BASELINE-01](normative_baseline/NORMATIVE-BASELINE-01_extraction_matrix.md)
remains `ACCEPTED WITH LIMITATION / PARTIAL — NAMED INPUT NEEDED`.

Accepted practical chain:

`diagnostic observations → PMI/software classification → classified ORE counts → cross sections → sensitivity representation → environment convolution → scalar rate/probability`.

No normative deficiency or automatic equivalence to `W`, `E_cap` or `F_A` is
inferred. The STO controlled-edition status remains `AMBIGUOUS`.

## Additional domestic prior-art signals

PI-provided signals concerning the Meshchanov/Lushnikov/Krasnikov, Podzolko,
Boruzdina/Ulanova/Chumakov and Zebrev/Galimov lines remain `UNVERIFIED`. The
next-gate draft defines four bounded work units, common extraction columns and a
hard stop rule. They must become controlled comparison points before the next
quantitative experiment, but they do not authorize a broad literature cycle or
alter RES-001.

## Updated scientific roadmap

1. **Obtain PI disposition of the next quantitative gate.** No new EXP starts
   from the draft alone.
2. **Control the minimum prior-art boundary.** Before the next quantitative
   experiment, convert only the named domestic lines that
   can change the next method/gate into bounded full-text comparison points.
3. **Register the integrated control question and activate RQ-003.** After
   explicit PI approval, register the prepared integrated adaptive-control RQ;
   define the minimum parameterized ECC state/capability and
   decoder-outcome contract consumed by reliability and observation layers.
4. **Converge RQ-004 and RQ-005.** Bound at least one internal and one external
   observation channel with uncertainty/latency semantics, and a measurable
   resource vector containing scrub activity plus nonredundant service/hardware
   components.
5. **Generalize the own method.** Replace the single extremal discriminator with
   an information-state/model-set formulation
   `I -> M(I) -> F_A set/bound -> admissible actions -> T_scrub -> resource cost`,
   and quantify the control-resource price of information deficit.
6. **Move to a physically defensible domain.** Use plausible event/W classes and
   observable test outputs to determine effect magnitude, controlled error or a
   safe-reduction domain, then connect the result to adaptive `T_scrub` selection
   and resource cost.
7. **Only then broaden claims.** Run the separate classical
   inspection/maintenance prior-art pass before a literature-level integrated
   control novelty claim, not before the next bounded model work.

## Prepared next quantitative gate — PI approval required

The exact draft is stored in
[`docs/research_gates/`](research_gates/NEXT-QUANTITATIVE-GATE-information-deficit-control-price.md).
It must answer more than “dependence can matter.” For retained information `I`,
it defines an admissible model set and the induced value/set/bound for `F_A`,
then determines for every candidate `T_scrub`:

- exact/model feasibility at a specified model;
- estimated feasibility under a declared statistical rule;
- robust feasibility over representation/model/observation uncertainty;
- conditions under which the admissible or selected action is invariant;
- decision and resource consequences over a physically defensible domain.

The draft also fixes the minimum physically defensible domain, RQ-002/RQ-006 and
RQ-003/RQ-004/RQ-005 interface slices, the four-unit domestic prior-art closure,
its stop rule and the future experiment completion criterion. The next experiment
or derivation must be preregistered before execution and may use a prospective
hypothesis or an explicit decision/falsification criterion. It must not simply
create another synthetic pair with different `F_A`.

## Genuine blockers and PI inputs

The current blocking PI decisions are acceptance/revision/rejection of the next
quantitative gate and, before execution, explicit acceptance of the integrated
adaptive-control RQ wording/ID.

Before target-like calibration, useful but non-blocking material remains:

- controlled-edition or registry evidence for STO 04.01.0005–2022;
- one representative/de-identified SRAM private PMI and diagnostic/software log
  schema;
- target-like memory organization/interleaving information;
- applicable current normative documents named in the accepted extraction.

Permanent registration of the prepared integrated adaptive-control RQ will
require explicit PI acceptance of its exact wording and ID. A future genuine
branch decision is required only if evidence forces a choice between incompatible
observable channels, ECC semantics or target hardware domains.

## Active hypotheses and results

- No `HYP-xxx` is registered; none is created retroactively for EXP-001.
- EXP-001 is complete, independently validated and has `Scientific Review 02: PASS`.
- [`RES-001`](../results/RES-001-exp001-four-word-identified-set.md) is the first
  permanent own result; it is valid only under its complete fourteen-condition
  domain.
- The next quantitative gate is a PI-pending draft; no `EXP-002` or `RES-002`
  exists.

## Constraints

- Do not reopen RQ-001 or revise DEC-001 without a concrete contradiction.
- Do not identify `E_cap` with DUE/SDC/miscorrection/system failure.
- Do not assign a numerical reliability requirement without traceable provenance.
- Do not generalize EXP-001 to physical SRAM or universal marginal-model
  insufficiency.
- Do not infer normative deficiency or Chen-family novelty/non-novelty.
- Do not let representation/reliability work replace adaptive control as the
  dissertation core.
