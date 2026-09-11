# EXECUTION SEMANTICS REPAIR — RE-FIXED-ADAPTIVE-FEASIBILITY-01

This repair replaces the non-executable conditional-write fixtures in frozen `verify.py` with an executable small state model (`semantic_model.py`) and `repair_checks.py`.

## Conditional-write state semantics

A 39-bit SEC-DED word is represented by its current erroneous-bit set. Bit injections toggle physical cells. `E_cap` is recorded at the first instant when more than one distinct erroneous cell is present and is never erased by a later toggle or write.

At read completion: zero errors -> clean and no write; one error -> correctable and a corrected image is latched; two or more errors -> uncorrectable and `E_cap` has occurred. A correction write commits the latched corrected image. An upset arriving after a correcting read may therefore be physically cleared by that write, but a second distinct erroneous cell during the RMW interval still counts as first-passage `E_cap`.

Completed-pass count increments only when a correction write completes. The pass snapshot is published only after the final word transaction commits; partial passes have no completed snapshot.

`repair_checks.py` executes nine transitions: clean suppression; post-read error persistence; single-error correction; RMW second-error first passage; same-bit toggle; last-word snapshot; partial pass; deadline fallback; and application/scrub arbitration.

The eight dictionaries in frozen `verify.py` remain provenance only and are no longer treated as semantic evidence.

## Word-level executor and risk schedule

Principal 4 MiB timings are read=60 ns, write=80 ns. A worst-case scrub word therefore holds the interface for 140 ns. The declared application primitive is at most 80 ns.

The same causal scan phase used in the risk calculation releases scrub-word jobs. At the calibrated principal peak,

`p_min = 3600/(W*r_peak) = 582.221399 ns`.

Scrub has priority at a word boundary. If an application word is already active when scrub becomes due, that operation finishes and scrub starts immediately afterwards. Hence scrub-start lateness is <=80 ns and `140+80 < 582.221399 ns`, so blocked scrub releases cannot bunch.

The actual inter-check scan-phase integral is therefore at most

`1 + r_peak*80ns/3600 = 1.0000001310394042`.

Paying this factor on the pair term raises the principal risk upper bound only to

`0.0009500001244874023 < 0.001`.

Thus the executor used for the latency argument is explicitly connected to the schedule used for the risk witness.

## Delay bound

The 25%/1s constraint alone is not used to infer a microsecond delay. The phase-spaced release stream gives the deterministic scrub workload envelope

`A_scrub(T) <= g_scrub + rho_scrub*T`,

with `g_scrub=140 ns` and `rho_scrub=0.2404583551`. The leftover service to application traffic is therefore at least

`beta_app(T)=[(1-rho_scrub)T-g_scrub]^+`.

For an admitted burst of eight primitive application word operations, each <=80 ns, `sigma_app=640 ns`. With declared background load `rho_app=0.5`:

- leftover-service horizontal delay = `(sigma_app+g_scrub)/(1-rho_scrub) = 1.02694 us`;
- conservative whole-busy-period clearing bound = `(sigma_app+g_scrub)/(1-rho_app-rho_scrub) = 3.00530 us`.

The previously quoted 3.005 us therefore remains a valid conservative bound under this explicit executor/workload contract. If a logical application word requires multiple primitive memory operations, if 80 ns is exceeded, or if the arrival envelope is violated, the bound must be recomputed.
