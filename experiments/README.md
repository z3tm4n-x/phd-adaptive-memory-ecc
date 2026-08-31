# Experiments

Каждый значимый эксперимент получает стабильный `EXP-xxx`.

Минимально должны быть воспроизводимы:

- цель и связанная гипотеза;
- commit SHA кода;
- configuration;
- input data provenance;
- seeds;
- baselines;
- metrics;
- процедура;
- location outputs;
- статус валидности эксперимента.

Сырые большие outputs не коммитятся; в Git остаются manifests, агрегированные данные разумного объёма и утверждённые figures/tables.

## Registry

| EXP-ID | Objective | Related RQ | Status |
|---|---|---|---|
| [EXP-001](EXP-001-event-representation-reduction-sensitivity.md) | Quantify the reliability and restoration-decision effect of reducing full physical event information through `W` to joint, marginal and scalar representations | RQ-001 / RQ-002 / RQ-006 | IMPLEMENTED / SCIENTIFIC REVIEW REVISE / VALIDATION REPAIR REQUIRED |
