# Simulation

Вычислительные модели, Monte Carlo и тесты.

Будущая структура создаётся по мере появления кода, например:

- `src/`
- `tests/`
- `configs/`

Не хранить результаты без привязки к `EXP-ID` и commit SHA.

## EXP-001 Phase 1

Config-driven implementation is under `src/exp001/`; fixed synthetic inputs are
under `configs/EXP-001/`.  The implementation uses only the Python standard
library and deliberately does not implement the deferred `L3-E` comparator.

From the repository root:

```powershell
python -m unittest discover -s simulation/tests -v
python simulation/run_exp001.py --bounded-config simulation/configs/EXP-001/bounded-phase1.json --joint-config simulation/configs/EXP-001/joint-discriminator.json --output-dir experiments/manifests/EXP-001 --repo-root .
```

On the recorded local Codex runtime, replace `python` with the exact executable
stored in `experiments/manifests/EXP-001/environment.json`.

The fixed run streams Bernoulli/paired counts into bounded aggregate tables; it
does not persist raw trajectories.  `L0 → L1` disagreement, a failed mandatory
joint invariant, or a failed predeclared precision rule terminates the run.
