# HANDOFF — RE-FIXED-ADAPTIVE-FEASIBILITY-01

From: постоянный Research Engineer, отдельная PI-started session  
To: Research Orchestrator  
Task: RE-FIXED-ADAPTIVE-FEASIBILITY-01  
Execution base: `59603d231b923ee7426056cb62779a5ad16c8413`  
Branch: `research/fixed-adaptive-feasibility-01`

## Статус

Эксперимент выполнен по зафиксированной двухуровневой постановке. Pre-verification commit программы/config/analysis contract: `e8713d187592c9b810ecf4194b6da7108d898e22`. Финальный delivery commit возвращается вместе с этой поставкой после публикации branch head.

Level I **OPENED Level II**. Level III / practical RES-004 **NOT EXECUTED**. Новый RES/PASS не присвоен. Новые существенные научные утверждения требуют отдельного Scientific Review.

## Центральный результат для проверки Orchestrator

Principal domain:
- protected data: 4 MiB;
- ECC: SEC-DED (39,32);
- H=43824 h;
- epsilon=0.001;
- B_avg=0.25%;
- B_peak scrub=25% in 1-s window;
- app load=10% or 50%, burst=8 words, research deadline=100 us;
- conditional write;
- one-hour delayed external scalar rate is a **conditional research information channel**, not established flight-feed latency.

Strong Fixed:
- resource-compatible Fixed needs tau >=25.165824 s even counting reads only;
- phase-independent lower bound at that tau gives F_A >=0.001571525;
- all tau from there to 3600 s are covered by the independent lower-bound argument;
- fixed risk/resource separator boundary corresponds to >=0.395040% read resource.

Simple causal witness:
- r=nu_hat/C, nu_hat=completed previous-hour rate, C=0.03560929816;
- risk upper=0.00095; 4x-RMW stress=0.000950000728;
- worst read+write average=0.142447%;
- peak=24.0458%;
- app delay bound at 50%=3.005 us;
- connected average-budget separator: [0.142447%, 0.395040%);
- 148 source-missing hours at peak fallback give average upper 0.223172% <0.25%.

Level II disposition:
1. Fixed — proven insufficient in principal domain.
2. Strong Precomputed — no distinct admissible witness established without future leakage; INCONCLUSIVE, not impossible.
3. Simple external delayed-rate + fallback — **minimal established causal witness**.
4. Counter-only simple — not established for this 39-bit/five-year/conditional-write domain; old seed sweeps remain diagnostic only.
5. RES-003 — not directly comparable without new scientific transfer: accepted domain is n=32 data-only, H=3600 s, epsilon=0.1, known symmetric two-state CTMC. No additional system benefit over the simple external witness is established here.
6. RES-004 — not executed; no practical revisit basis found.

Stronger ECC:
- separate shortened BCH candidate (44,32,d>=5), t=2;
- principal B_avg=0.25% gives tau=58.720256 s and analytic triple-event upper 5.57e-9;
- suggests adaptation need is not universal over ECC architecture;
- +12.82% protected storage relative to 39-bit codeword; decoder/timing/WCET not implemented.

## Что проверить Scientific Reviewer

Адресно:
1. validity and uniformity of the strong-Fixed lower bound across phase and continuous tau class;
2. Cauchy/union derivation of causal risk upper and lag-1 endpoint bound;
3. legitimacy of transferring normalized historical temporal shape to the ESA scalar rate and the exact scope of the resulting conditional claim;
4. conditional-write RMW bound and 4x robustness;
5. resource/peak/application-delay algebra and whether the stated residual controller-cost contract is sufficient;
6. stronger-ECC triple bound and architecture separation;
7. Level-II disposition: especially that Precomputed/simple/RES-003 are not scored negatively merely because a compatible certificate is absent.

## Файлы поставки

- `ANALYSIS_CONTRACT.md` — pre-registered rules;
- `config.json` — frozen ranges;
- `analyze.py` — frozen Level-I map;
- `verify.py` — frozen semantic checks;
- `independent_check.py` — post-result independent formula audit, does not import analyze.py;
- `INPUTS.json` — provenance/status;
- `REPORT.md` — complete report + five direct answers;
- `outputs/level1_map.csv.gz` (детерминированный gzip; `analyze.py` воспроизводит исходный CSV) — all preregistered grid combinations;
- `outputs/boundary_map.csv` — compact continuous boundaries;
- `outputs/causal_witnesses.csv` — causal trace witnesses;
- `outputs/hour_slice.json`;
- `outputs/stronger_ecc.json`;
- `outputs/level2_disposition.json`;
- `outputs/verification.json`;
- `outputs/independent_check.json`;
- `outputs/execution_record.json`;
- `MANIFEST.json`.

## Ограничения

E_cap != system failure. External operational data delivery is not established. Application deadline/load/peak are research contracts. No target WCET measurement. No new Monte Carlo, retuning, GOES/COSRAD rerun, RTL, Vivado or RES-004 practical work. First RES-003 publication stream is unchanged.
