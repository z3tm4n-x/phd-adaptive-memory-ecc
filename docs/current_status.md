# Current Status

**Updated:** 2026-08-27

## Current phase

RQ-002 targeted literature mapping — handoff preparation.

## Infrastructure status

- GitHub repository setup: complete.
- Zotero setup: complete.
- AI-agent operating model: complete; canonical role instructions are in `docs/agents/`.
- Research Specification: `v0.3-draft`.

## Active gate

Prepare and run the targeted Literature Scout handoff defined by `docs/literature_mapping/RQ-002_protocol.md`. The gate is open, but no RQ-002 literature search has been started by the DEC-001 recording commit.

## Active Research Questions

- RQ-001 — reliability event, metric and evaluation horizon — `PARTIALLY ANSWERED / OPEN DEPENDENCIES`.
- RQ-002 — minimum adequate SRAM radiation error model — `OPEN / ACTIVE GATE / MAPPING NOT STARTED`.
- RQ-003 — ECC abstraction and baseline code class — `OPEN / QUEUED`.
- RQ-004 — online observables for adaptation — `OPEN / QUEUED`.
- RQ-005 — measurable resource-cost vector — `OPEN / QUEUED`.

## Accepted RQ-001 decision

[DEC-001](decisions/DEC-001-rq001-reliability-contract.md) records:

- primitive event `E_cap` as ECC capability exceedance, not an automatic DUE/SDC/miscorrection/system-failure label;
- reporting window \(H(t_0,T)=[t_0,t_0+T]\);
- general metric \(F_A(t_0,T;\mu_{t_0})\), with the initial state/distribution required by every quantitative model;
- an explicitly declared controller-managed SRAM protection domain \(A\);
- mandatory partitioning of \(A\) when ECC, mapping \(W\), arrival, bank/block or scrubbing semantics differ;
- distinct upset-count, per-codeword exposure, reporting and mission horizons;
- sequential exposure as a working modeling requirement, not a literature-established fact.

## RQ-001 open dependencies

- concrete ECC/decoder outcomes — RQ-003;
- adequate error-arrival/correlation model — RQ-002;
- target physical mapping \(W\);
- nonstationary mission aggregation;
- system-visible consequence model;
- \(H_{\mathrm{req}}\) and \(\varepsilon_{\mathrm{req}}\) — `TBD` pending traceable requirements;
- CAND-10 remains deferred.

## RQ-002 input contract

RQ-002 must evaluate candidate error models by whether they can produce the declared `E_cap` metric for:

- a stated reporting window and initial state/distribution;
- an explicitly declared or partitioned protection domain;
- direct same-particle and independent-accumulation mechanisms without untracked overlap;
- stationary and nonstationary scenarios within stated validity domains.

The C-RQ-05 escalation gate remains mandatory if MCU/MBU or spatial correlation is material or cannot be safely excluded/bounded.

## Active hypotheses and own results

- No `HYP-xxx` has been registered.
- No `RES-xxx` has been registered.
- `DEC-001` is a research decision, not an own experimental result.

## Next actions

1. Issue the exact RQ-002 Literature Scout handoff using `docs/literature_mapping/RQ-002_protocol.md` and DEC-001 as its input contract.
2. Do not assume Poisson arrivals, independence, stationarity or negligible MCU/MBU before evidence screening.
3. Apply the C-RQ-05 escalation rule during screening.
4. Keep RQ-001 open and revisit DEC-001 only under its explicit revisit conditions.
5. Do not assign a numerical reliability requirement without traceable provenance.

## Notes

- eLibrary remains deferred where Literature Scout lacks access; an unavailable database is recorded as unknown coverage, not as zero results.
- No new literature search is active at the end of this commit.
