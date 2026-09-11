# HANDOFF — RE-CY62167-PHYSICAL-BRIDGE-01

**From:** permanent Research Engineer  
**To:** Research Orchestrator / subsequent Scientific Reviewer  
**Task:** `RE-CY62167-PHYSICAL-BRIDGE-01`  
**Task base:** `9ea66664d37cb522d0d148ed63b06858de313d00`  
**Scientific input base:** `69e92fe36b3b7933cebccbedd457cc0309dd4d1c`  
**Pre-execution contract:** `4bac6ec1f017f98cd685fee79051dd972b8c8342`

## Conclusion

A structural physical bridge is obtained, but current CY62167 information is not sufficient for a full-device control-class decision.

1. For internal SEC `(32,38)`, an atomic parent event toggling >=3 distinct cells of one actual internal word is universally first-passage fatal from every SEC-safe pre-state for every timing policy unable to act inside the atomic event.
2. Current evidence does not establish a nonzero occurrence lower bound for that event (`q3`): parent identity, actual W/parity and absolute multiplicity normalization are incomplete.
3. The reviewed registered data-only upper remains useful only conditionally. Full-device lifting requires a coverage probability `delta_cov` for omitted physical/parity/W paths.
4. On the preregistered 10-mm/24-h/DREG/tau=1-s slice, the frozen registered upper is `0.0003098119451681036`; at the diagnostic `epsilon=0.001`, the missing full-device coverage must satisfy `delta_cov<=0.0006901880548318964` to preserve the certificate.
5. Exact proprietary W is not intrinsically necessary if complete-codeword measurements directly bound `q3` and `delta_cov`. W alone is also not sufficient because parent/exposure/parity uncertainties remain.

## Material new claims requiring Scientific Review

- the `D3(W)` policy-independent first-passage theorem and its quantifiers;
- the full-device coverage-union formulation `F_A <= U_reg + delta_cov` as the bridge from the reviewed registered surrogate;
- the constructive compatible-model non-identifiability witness using an observation-invisible parity D3 component;
- the information-sufficiency conclusion that direct bounds on `q3`/`delta_cov` can replace full W reconstruction for the control decision;
- the numerical `delta_cov` threshold on the frozen slice.

## Reproduction

From the delivery directory:

```sh
python3 checks.py
python3 independent_check.py
```

Expected: both exit 0; `outputs/checks.json` and `outputs/independent_check.json` have `passed=true`.

Environment used: Python 3.13.5; Linux 6.18.35 x86_64; glibc 2.41; stdlib only.

## Limits

- no new GOES/COSRAD/radiation calculation;
- no raw cluster reparse;
- no broad W search;
- no new environment class;
- no controller optimization or RES-004;
- no hardware/irradiation experiment;
- `epsilon=1e-3` is an analysis line, not a mission requirement;
- `E_cap` is not identified with DUE/SDC/system failure;
- parity/direct hidden hazard rates remain unmeasured.

No PASS/RES is assigned by this handoff.
