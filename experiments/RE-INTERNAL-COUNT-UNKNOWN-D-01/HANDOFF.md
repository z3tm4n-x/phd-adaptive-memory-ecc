# RE → Scientific Reviewer / Research Orchestrator

Task: **RE-INTERNAL-COUNT-UNKNOWN-D-01**.
Related: RQ-004/RQ-007, RQ-003/RQ-005 interfaces; DEC-001; accepted RES-003.

**Engineering disposition:** computation, derivation, independent checks and
held-out experiment completed. Scientific Review disposition NOT assigned.
**Delivery limitation:** full source-package upload to GitHub was not completed:
the gateway rejected the full updated model.py write. The supplied ZIP is the
complete executed package. The existing branch prototype must not be described
as that source. This is a delivery limitation, not an unresolved calculation.

## Identity and permitted scope

Canonical PI task base: `529709f1b98d12a5f5a2c7b71ee1ff9f53210c97`.
Task blob: `d9cd726b95072c48a732aa435e5d8990c620d59f`.
Intended branch: `research/internal-count-unknown-d-01`.
Allowed subtree: `experiments/RE-INTERNAL-COUNT-UNKNOWN-D-01/`.
Pre-existing engineering branch head before this delivery:
`e4ffac70d0a94ba9424e93b1591b098cd8f705b3`.
It is provenance of the earlier prototype/configuration, NOT the executed
implementation commit. A nonexistent implementation commit is not assigned.

The source set actually executed is recorded by SHA-256 in
`outputs/validation_lock.json`, checked again in `outputs/execution_record.json`.
`outputs/manifest.json` additionally records Git blob identities of archive files.
The source was assembled into a working package; no complete private-repository
local clone or access to the user's desktop tools is claimed.

Read-only upstream identities:
- core.py: `7873e28e126ea02e03fc6c429ac0b4275e243cfb`;
- simulate.py: `ee55c6bf57b034b0efc0b41936a549d6a14b53dd`;
- feasibility.py: `d9417313ad406c2fa7a5e54ad9751d7a82903b97`;
- config.json: `5ca1b8cda0a19315684c34423cadafa2cf544e6e`.

Known-D is an explicitly labelled readable target-interface adapter, not a
byte-identical copy. Its extra true-D input is confined to that diagnostic.
Three accepted trace/action witnesses were reproduced. Upstream numerical
results, accepted RES-003, main and canonical documents were not modified.

## Reproduction and actual completion

```sh
python -m pip install -r requirements.txt
OPENBLAS_NUM_THREADS=1 python -u reproduce.py --retune --full --workers 4
```

Executed environment: Python 3.13.5, NumPy 2.3.5, SciPy 1.17.0, Numba 0.65.1;
platform recorded in execution_record. Extended-precision longdouble is used
offline and checked by independent directed coefficient enclosures.
All 17 engineering checks passed; no Scientific Review PASS is inferred.
All five production cases completed 20000 held-out missions with six policies.
All 5148 finite-grid Fixed/Precomputed brackets and their continuous transfer
were calculated. Full raw paired arrays and traces accompany the ZIP.

Beta=.005, G=1.064, bank33, coarsening, controller and numerical allowances
were not tuned to held-out savings. Initial PA-DOM grid was refined in its
favor only on pilot data; the exact reason/inserted settings are retained in
config. One setting Ms=.105, cap5, growth3, zero-mode1 serves all D.
Final seeds differ from pilot; source hashes were unchanged during final workers.

## Proposed statement and its boundaries

Within the declared symmetric fixed-D, known-level, accumulation-only SEC
model, a finite own-count controller safely removes parameter cells while
carrying separate whole-horizon budgets. Event-level positive-Poisson-series
interpolation converts endpoint guarantees into F(D)<=.1 over the continuum.
The own-count effect of learning D is isolated from within-D hidden-state
filtering by a frozen-set controller with otherwise identical mechanism.

Savings estimates are positive at all five D. Distribution-free simultaneous
positive conditional-resource statements are supported for D=100/300/1000/3000;
the small D=30 effect is not supported by the chosen loose family bound.
Actual risks are not equal; Monte Carlo is not the proof of coverage or risk.
No general prior-art novelty, globally optimal adaptation, useful-information
limit, real radiation identification, hardware WCET or energy result is claimed.

## Mandatory falsification questions

1. Verify the six-statistic closure for zero/positive own counts. In particular,
   preserve pending arrivals and their mode-correlated first moments, and do
   not interpret normalized auxiliary q as physical mass conditioned on survival.
2. Verify the positive-series/Hölder continuum argument for ONE fixed policy
   program and ONE immutable D over H. The argument must not assume that the
   worst case occurs at endpoints, nor apply silently to a true-D-fed family.
3. Verify anytime likelihood-ratio exclusion with adaptive own actions, the
   closed-cell endpoint rule, and beta/G allocated once. The test mixture is
   not a physical prior. Check the explicit empty-set continuation/no reset.
4. Verify the stopped risk proof. Kernel-TV errors act on bounded continuation
   probabilities before using the pair-reward bound. Do not use an invalid
   TV estimate for an unbounded accumulated cost. Audit how rejection, repeat
   hits, exact/approximate channel and arithmetic are jointly paid.
5. Audit the directed coefficient support/enclosures and the separate analytic
   scan approximation and rounding ledger. The stated numeric version is
   conditional on its IEEE/transcendental/compiler contract, not certified
   merely because row sums or observed risk are small.
6. Verify frozen-set invariance and per-generator slack: posterior reweighting
   must not bypass the full-set requirement; no new physical D at each step.
7. Verify baseline class optimality, single-setting analogue pilot separation,
   no foreign-counter input, first-passage/terminal scan and resource semantics.
8. Verify interpretation: individual survivor means differ in conditioning;
   check common-survivor/stop results and the separate statistical families.
   The known-D gap also includes coarsening and reserve differences.

A valid witness breaking the likelihood identity, closure, stopped bound,
continuum inequality, arithmetic reserve, frozen invariance or cheaper-baseline
exclusion falsifies the corresponding claim. Systematically established F>.1
under a declared fixed D also falsifies it; absence of observed failures cannot
prove the guarantee.

## Independence and shared failure paths

The small killed model builds its own physical generator on (mode,dirty mask),
uses actual chronological word resets to generate counts, and retains lost
mass. It does not call the production auxiliary observation helper. An explicit
all-word event merger independently checks the lazy scanner on 400 paths.
Integrated moments are checked by a separate block exponential. Coefficients
are enclosed with directed Decimal arithmetic; a second dense grid is not
used as a continuum certificate.

The candidate controller is still the same code called by the oracle;
configuration and Python numerical stack are shared. The small auxiliary
builder and production controller interface are not independent reimplementations
of the decision rule. The actual-bit lazy scanner follows the accepted RES-003
algorithm and is a common path across competitors. Pairing shares external
random events, never realized count observations. Small-H natural parameter
exclusion did not occur, so this test is not presented as a learning-effect
validation. Formal and full-scale checks have distinct functions.

## Engineering repairs and remaining limitations

A purely binary64 offline idle-kernel build did not meet the frozen relative
coefficient allowance. Extended precision was introduced before held-out and
all coefficients re-enclosed. No physical or optimization settings changed.
Pilot refinement history is retained; unsuccessful pilot configurations were
not removed from the result table. No failing production mission was discarded.

Remaining boundaries: sufficiency/conservatism rather than global optimum;
unknown fixed D only; actual physical counter after a coupling break lacks an
unconditional auxiliary-coverage interpretation; coarsening versus reserve
contributions not fully separated; no onboard hardware measurements. Full
GitHub source publication remains incomplete due the recorded gateway refusal;
use the supplied complete archive for review/reproduction until that delivery
limitation is resolved through an authorized repository write.

Orchestrator/PI retains responsibility for acceptance, publication planning and
canonical registration. RES-003 publication handoff was not executed here.
