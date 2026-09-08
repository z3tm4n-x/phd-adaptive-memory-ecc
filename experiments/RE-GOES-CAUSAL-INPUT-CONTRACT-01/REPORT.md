# RE-GOES-CAUSAL-INPUT-CONTRACT-01 — REPORT

**Starting commit:** `19cb6c09c88f55cbcaf0af328cd6ef81cbff9f92`  
**Scope:** causal-input audit only; no new reliability/control experiment.

## Executive disposition

**PARTIAL / SUFFICIENT FOR A PARAMETERIZED DELAYED-DATA COMPARATOR; OPERATIONAL CHANNEL NOT ESTABLISHED.**

The existing `RE-GOES19-PROTON-RATE-01` series is a valid **pinned retrospective environmental reference** under its already declared physical/model limitations. It is not, as currently archived, evidence of what a controller could have known in real time.

For the present project contract, a source timestamp `t` is interpreted as the **start of a 5-minute averaging interval**. The historical adapter verifies `time_coverage_resolution=PT5M`, converts the source `time` coordinate without shifting it, explicitly records `timestamp_semantics='timestamp at start of averaging period'`, and writes that same value to `proton_rate_5min.csv`. Therefore the nominal measurement interval is `[t, t + 300 s)`, and the complete five-minute average cannot be available before `t + 300 s`. Any additional L2 processing, publication, communication, download, project-side transformation or controller-delivery latency is **UNKNOWN** from the retained evidence and must not be set to zero. `date_created` is not used as an operational-availability timestamp.

One existing transformation is not causal at the affected timestamps: `high_energy_gap_bridge()` first fits P10/P11 power-law indices over the **entire 59-day series**, then uses the direction-wide median fitted index where a local fit is unavailable. The retained diagnostics report **576 East and 920 West directional fallback rows**. The row-level `used_fallback` mask is not written to `proton_rate_5min.csv` or another committed row-level artefact; only aggregate counts are retained. Thus the exact affected timestamps cannot be recovered from the frozen derived CSV alone.

A small helper, `extract_causal_features.py`, is supplied to recover exactly that mask from the already-declared PI-controlled GOES NetCDF set, with hash verification and without running RADAR/transport/reliability/control. The exact controlled archive is not present in the Git checkout, so this helper could not be executed against the canonical raw bytes in this task.

The immediate input blocker for instantiating the existing derived series as a causal comparator is therefore the **PI-controlled `goes010226.zip`, SHA-256 `7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581` (59 declared daily NetCDF files)**. A separate blocker for any **practical operational guarantee** is evidence of actual L2 publication/delivery timing or an as-received operational feed/log; none is retained here.

## 1. Evidence and status discipline

Canonical repository sources at the starting commit:

- `experiments/RE-GOES19-PROTON-RATE-01/goes19_adapter.py`, especially `load_directory()`;
- `experiments/RE-GOES19-PROTON-RATE-01/rate_pipeline.py`, especially `high_energy_gap_bridge()`, `calculate()`, `write_rate_csv()`;
- `experiments/RE-GOES19-PROTON-RATE-01/goes19_audit.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/rate_diagnostics.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/input_manifest.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/REPORT.md`;
- `experiments/RE-GOES19-PROTON-RATE-01/noaa_revision_semantic_patch.json`.

The manifest also records the NOAA GOES-19 SGPS Provisional ReadMe URL. The currently reachable document is useful for product/calibration caveats, but it is not byte-pinned in the repository and it does not establish historical L2 delivery latency. It states that SGPS L1b is one-second cadence, that product improvements/reprocessing may occur, that gaps exist, and that the revised P1–P5 calibration had not been applied to operational L1b while corrected L2 one-/five-minute products were planned as replacements. Those facts support the archive-versus-operational distinction; they do not supply a controller-availability timestamp.

Statuses below use:

- **KNOWN/RETAINED** — directly preserved by the pinned code/artefacts;
- **DERIVED LOWER BOUND** — follows from the retained averaging/timestamp contract;
- **UNKNOWN** — not evidenced by the retained inputs;
- **RETROSPECTIVE ONLY** — depends on future records or later archive state and must not be presented as an online observation.

## 2. Temporal meaning of one record

### 2.1 Source timestamp and averaging interval

`goes19_adapter.load_directory()` checks `processing_level == 'Level 2'`, `time_coverage_resolution == 'PT5M'`, exactly 300 s between retained timestamps, and converts source `time` values directly to UTC datetimes. The same function records `timestamp_semantics = 'timestamp at start of averaging period'` in its audit object. `rate_pipeline.write_rate_csv()` writes `goes.times[t].isoformat()` directly as `timestamp_utc`; no later code shifts it to the interval centre or end.

Hence the current project interpretation is:

| Quantity | Contract |
|---|---|
| interval start | `t = timestamp_utc` |
| interval end | `t + 300 s` |
| CSV timestamp | source averaging-interval start |
| earliest possible availability of the **complete** five-minute average | not before `t + 300 s` |
| additional processing/publication/delivery latency | **UNKNOWN** |

This is adequate for a **conditional comparator** with an explicitly declared nonnegative latency `L`: `availability_time = t + 300 s + L`. It is not an operational-latency measurement.

### 2.2 Qualification: raw time attributes/bounds are not independently rechecked here

The Git checkout retains the adapter contract, hashes and audit summaries, but not the 59 controlled NetCDF files themselves. The committed audit does not preserve the raw `time` variable attributes or any raw time-bounds array. The historical adapter also does not consume a bounds variable; it uses the source `time` coordinate plus the checked `PT5M` resolution.

Therefore this task can verify the **existing project temporal contract**, but cannot independently re-open the original NetCDF `time` attributes/bounds from repository bytes. To close that provenance point at source-file level, provide the exact controlled archive named above. `extract_causal_features.py` intentionally requires the controlled hashes; with `--metadata-output` it also dumps the retained raw time attributes and discovers any bounds variable/dataset without interpreting `date_created` as operational availability.

`date_created` is read into historical in-memory file metadata by `goes19_adapter.py`, but it is not interpreted here as the time at which an operational controller first received a record. File creation/reprocessing time and network/controller availability are different objects.

## 3. Causality audit of the existing transformation

### 3.1 Per-record operations that do not use future timestamps

Subject to the source record itself being available, the following historical project operations use only the same timestamp plus fixed calibration/model objects:

- fill/nonfinite and yaw validity handling;
- E/W physical-direction reconstruction;
- fixed P1–P5 correction factors when legacy channel bounds are detected;
- unit conversion keV -> MeV;
- fixed low-energy `gamma={0,2,4}` scenario extension anchored to that row's P1 value;
- per-direction RADAR transport with pinned static matrices;
- static `sigma(E)` representation;
- P11 >500 MeV contribution;
- local P10/P11 390–500 MeV bridge when a positive finite local P10/P11 pair exists;
- E/W arithmetic central estimator after both same-timestamp directional chains exist.

These operations can still have **processing latency** and **model uncertainty**; absence of future-time dependence is not evidence that their real-time execution was implemented.

### 3.2 Direction-median high-energy fallback is retrospective

`rate_pipeline.high_energy_gap_bridge()` executes, per direction: (1) scan all timestamps and collect every locally fitted P10/P11 `gamma`; (2) compute `median(fitted)` over that complete population; (3) scan all timestamps again and fill any missing local `gamma` with that median.

Thus a fallback value at time `t_k` can depend on observations with timestamps `> t_k`. The exact frozen fallback value is therefore a retrospective reference quantity. If one insists on using that exact frozen value without changing the algorithm, it cannot be treated as available during the Jan–Feb record until the full median population has been observed and processed.

`rate_diagnostics.json` preserves direction median gamma E `1.179003304890439`, W `1.1705858862947358`, and fallback counts E `576`, W `920`. The local `used_fallback[T,2]` Boolean array is not returned from `high_energy_gap_bridge()`; only aggregate counts enter the diagnostic. `write_rate_csv()` does not contain a bridge/fallback flag or per-row `gap_bridge_gamma` column. Consequently **row-level fallback identity is not recoverable from `proton_rate_5min.csv` + committed diagnostics alone**.

No transport rerun is needed to recover it. The supplied helper identifies the historical fallback predicate directly from the controlled raw P10/P11/validity values and verifies the historical aggregate counts.

### 3.3 Other retrospective calculations are diagnostics, not causal inputs

Dataset-wide summary quantiles/maxima, `_raw_low_slope_diagnostic()` quantiles, and the version-boundary comparison inspect populations beyond a single timestamp, but they are not used to construct the released per-row reference rate except for the high-energy fallback described above. They remain retrospective reporting diagnostics and must not be injected into future controller information unless separately defined as causal history statistics.

## 4. Missing data, E/W aggregation, calibration and archive revision

### Missingness and quality

The frozen source has 16,992 timestamps and 16,971 paired-valid E/W intervals; 21 timestamps contain at least one missing/invalid direction. The adapter performs **no time interpolation or smoothing**. A central `lambda` is written only when both directional values are finite. This missingness must remain visible to a causal `M(I)`; a missing value is not permission to substitute a future neighbor.

DQF information is retained as warning metadata rather than an automatic rejection of an otherwise reported L2 average. Future `M(I)` may use it as an uncertainty/status input, but this task does not invent a rule that maps a DQF flag to a risk bound.

### E/W aggregation

East and West are reconstructed and propagated separately. The central series is `(E+W)/2` only after both complete chains are available. The historical report explicitly does **not** identify this arithmetic mean with a measured omnidirectional spectrum. A causal comparator may use the central value only as a declared estimator and must retain the E/W disagreement/status needed for uncertainty treatment.

### Calibration correction

The adapter applies the published GOES-19 P1–P5 factors once when legacy bounds are detected. The factors are fixed constants and do not depend on future Jan–Feb samples, so the mathematical transformation is causal once a source record is available. However the project has not demonstrated an operational L2 delivery/processing chain that applied those corrections at a known time. Therefore they are acceptable in the **conditional delayed-data comparator**, not proof of what an actual controller received.

### Late archive revisions

`goes19_audit.json` records that, when checked later, 7 public daily files (2026-01-14…20) were bytewise different from the PI-controlled copies; Jan 19 and Jan 20 contained scientific dataset values requiring the retained semantic patch. `input_manifest.json` explicitly freezes the scientific outputs to the PI-controlled copies rather than silently replacing them with current public files.

This is correct for retrospective reproducibility but prevents a historical-operational claim unless an **as-received version timeline** is available. A later archive value or correction is not evidence that the same value existed at the original decision time.

## 5. Three distinct information objects

| Object | Definition in this project | Permitted claim |
|---|---|---|
| **Archival retrospective reference** | pinned PI-controlled GOES source + historical adapter + frozen rate pipeline, including global direction-median fallback and declared model scenarios | Reproducible reconstruction of the selected archived environment under the existing model contract. May use future records for retrospective components. |
| **Conditional delayed-data comparator** | same source-period semantics, but a record may enter controller information no earlier than `t+300 s+L`, with `L>=0` explicit; future-dependent fallback-derived values are unavailable/masked unless a separately approved causal treatment is defined | Tests sensitivity to a declared hypothetical availability delay. `L` is a parameter, not measured operational latency. |
| **Practical operational channel** | a specific real feed/product whose acquisition, processing, publication and controller-delivery timing/version semantics are evidenced | **NOT ESTABLISHED** by current repository evidence. No practical latency/reliability guarantee may be claimed yet. |

The conditional comparator is scientifically useful even with actual `L` UNKNOWN, provided it is never relabelled as the operational GOES latency.

## 6. Minimal input contract for the next real-temporal gate

| Field / signal | Measurement interval | Earliest availability under current evidence | Processing | Future dependence | Uncertainty / status | Permitted use |
|---|---|---|---|---|---|---|
| `timestamp_utc` | identifies nominal `[t,t+300s)` L2 average | timestamp itself is metadata; complete average not before `t+300s` | source time -> UTC; no shift | none | raw bounds not independently rechecked without controlled NetCDF | index the retrospective interval and define lower bound on observation availability |
| `AvgDiffProtonFlux` E/W, P1–P10 | L2 five-minute average over nominal bin | `t+300s + L_source`, `L_source` UNKNOWN | yaw mapping, fill handling, units, fixed P1–P5 correction | no project future sample except downstream bridge | L2 uncertainty, DQF, background/calibration caveats | external observation component for conditional `M(I)`; not instantaneous flux |
| P11 E/W | same nominal bin | `t+300s + L_source`, UNKNOWN extra latency | yaw mapping / validity | none by itself | L2 uncertainty | same-bin integral high-energy observation |
| validity + DQF status | pertains to samples contributing to same L2 bin | no earlier than associated L2 record under current evidence | retained by adapter | none | DQF semantics are warning/status, not a chosen risk penalty | preserve missingness/status; do not silently interpolate |
| corrected P1–P5 project spectrum | same source bin | after L2 availability + project-processing latency (UNKNOWN) | deterministic published correction on legacy signature | no time-future dependence | corrected calibration remains provisional/qualified | hypothetical processed external input; not proof of historical operational feed |
| local P10/P11 390–500 bridge | same source bin | after both local values + processing latency | local power-law fit | none when local fit exists | extrapolation/model limitation | may participate in conditional causal comparator |
| direction-median fallback bridge | nominally assigned to same bin | exact frozen value only after full fitted-median population exists + processing | whole-series direction median + P11 normalization | **YES** | 576 E / 920 W directional rows; row-level mask absent from committed derived outputs | **RETROSPECTIVE ONLY** until row mask and a separately approved causal treatment/M(I) are defined |
| `lambda_E/W_s-1` | derived from same five-minute environmental bin | after all causal source inputs for that row + processing latency | fixed transport/sigma/scenario chain | inherits fallback status | physical/model interface remains PARTIAL | retrospective reference; conditional causal input only on rows/components not using future-dependent fallback, with uncertainties carried separately |
| `lambda_central_s-1=(E+W)/2` | same bin | after both E and W directional chains are causally available | arithmetic mean after complete chains | inherits either direction's fallback status | not measured omnidirectional flux; E/W discrepancy material | declared comparator estimator only; retain E/W/status alongside it |
| `m5_central_bits=300*lambda` | summarizes same bin | same as central lambda | algebraic interval expectation | inherits central status | expected flips under existing rate model; **not** failure probability | retrospective/bin exposure descriptor only; not an instantaneous rate, within-bin maximum, or next-bin guarantee |

`L_source` above intentionally remains a parameter. A future gate may split it into source processing/publication, communications and controller processing if evidence justifies those components.

## 7. What a five-minute average does **not** establish

The current input does not establish that: (1) `lambda(t)` at every instant inside the bin equals the reported average; (2) the five-minute average upper-bounds sub-bin intensity; (3) the current average bounds or predicts the next bin; (4) a value stamped `t` was available to a controller at `t`; (5) the present archive value is the value historically available in real time; (6) `(E+W)/2` is a physically measured omnidirectional flux; or (7) a DQF-warning bin has a known quantitative bias suitable for a reliability inequality.

Before constructing causal `M(I)` or a future exposure bound, the next approved specification must explicitly state, without silently importing them:

- a within-bin state/exposure representation consistent with a five-minute average;
- an uncertainty set or controlled relation from L2 E/W/uncertainty/status to the latent rate used by the reliability model;
- a rule/bound for exposure after the latest completed bin and before the next observation arrives;
- the delayed-data latency parameter/evidence;
- treatment of missing bins and direction disagreement;
- a causal replacement, masking rule, or widened uncertainty set for high-gap fallback rows;
- whether the comparator uses the pinned retrospective archive or a versioned as-received operational feed;
- processing-time accounting for conversion to `lambda_bit`.

This task does **not** choose any of these modelling assumptions and does not derive a control law.

## 8. Reproducible real-section selection rule for the next gate

To prevent selection on a later reliability/control outcome:

1. Before any reliability or policy calculation, freeze the source/reference series, a window length `W`, and one declared **input-only** stratification signal from the contract above.
2. Partition the Jan–Feb time axis into non-overlapping windows of length `W`, anchored at `2026-01-01T00:00:00Z`.
3. Apply only input-quality eligibility rules fixed in advance (for example a minimum paired-valid fraction and explicit treatment of fallback-affected records once the row mask exists).
4. If a bounded subset is required, select windows using only predeclared environmental/input descriptors (e.g. low level, high level, strongest positive change, strongest negative change), with earliest-UTC tie-break. Do **not** inspect `F_A`, chosen `T_scrub`, feasibility, resource saving or any control result during selection.
5. Freeze the selected UTC intervals and their input descriptors before running the real-temporal reliability/control study.

Case selection is an offline experimental-design operation and may inspect the retrospective input series; controller information *within* each selected case must still obey the causal availability contract. No windows are selected by this task.

## 9. Exact remaining inputs / blockers

### Immediate blocker for a row-exact causal mask of the existing frozen rate series

Provide the exact PI-controlled GOES archive:

- **file:** `goes010226.zip`
- **SHA-256:** `7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581`
- **contents:** the 59 daily NetCDF files listed/hashes pinned in `input_manifest.json`.

With those bytes, `extract_causal_features.py` can, without transport, verify the source hashes, dump raw time metadata/bounds discovery, and emit the exact timestamps/directions that trigger the historical global-median fallback. Public revised substitutes must not be used silently because the project has already demonstrated archive drift.

### Additional blocker for an operational-channel claim (not required for a parameterized comparator)

Need a traceable product/feed artefact that establishes **as-received L2 availability**, preferably one of:

- timestamped NCEI/NOAA publication/download logs for the relevant 5-minute L2 records;
- an authoritative interface/product specification that defines production/publication latency and revision semantics for this exact SGPS L2 five-minute product;
- a preserved as-received operational stream/archive with acquisition timestamps and version identity.

Absent that evidence, real processing/delivery latency remains `UNKNOWN`; the next experiment may sweep a declared delay, but cannot call it measured GOES operational latency.

## 10. Verification actually performed

- Read the pinned adapter and rate-pipeline source; no historical production matrix was run.
- Confirmed from code that `timestamp_utc` is copied from `goes.times` without shift and that the adapter asserts 300-s cadence / `PT5M` and start-of-average semantics.
- Confirmed from code that the direction median is computed over all fitted timestamps before fallback assignment.
- Confirmed from the writer schema that no row-level bridge-fallback flag is exported to `proton_rate_5min.csv`.
- Confirmed retained aggregate fallback counts (E=576, W=920) from `rate_diagnostics.json`.
- Confirmed 16,992 source timestamps, 16,971 paired-valid intervals, calibration policy and 7-file archive drift from the retained audit/manifest.
- `extract_causal_features.py` passed `python -m py_compile` and CLI parsing locally. It was **not** run on raw GOES data because the controlled archive is not present in the connected repository/runtime.
- No RADAR/COSRAD, transport regeneration, policy search, reliability calculation, Monte Carlo, estimator or control optimization was executed.

## Final answer to the gate

The next real-temporal gate can now distinguish the required objects unambiguously:

- **retrospective reference:** the existing frozen Jan–Feb 2026 series, including documented retrospective components;
- **admissible delayed comparator:** a completed-bin observation available no earlier than `t+300s+L`, with `L` explicit/UNKNOWN and future-dependent fallback values excluded or represented as unresolved until a causal treatment is separately approved;
- **operational channel:** currently **UNPROVEN** because actual L2 delivery/version timing is not evidenced.

This is sufficient for Orchestrator to draft a bounded real-temporal EXP/derivation specification. A practical latency guarantee is not yet supportable.
