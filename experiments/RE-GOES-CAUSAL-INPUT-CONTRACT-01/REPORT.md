# RE-GOES-CAUSAL-INPUT-CONTRACT-01 — REPORT

**Starting commit:** `19cb6c09c88f55cbcaf0af328cd6ef81cbff9f92`  
**Delivery branch:** `research/goes-causal-input-contract-01`  
**Scope:** input/code/metadata causality audit only; no reliability experiment, estimator, policy search, RADAR/COSRAD rerun, Monte Carlo, HYP or RES.

## Executive disposition

**PARTIAL / SUFFICIENT FOR A PARAMETERIZED DELAYED-DATA COMPARATOR; PRACTICAL OPERATIONAL CHANNEL NOT ESTABLISHED.**

The retained `RE-GOES19-PROTON-RATE-01` series is a valid pinned **retrospective environmental reference** under its existing physical/model limitations. It is not evidence of what a controller knew in real time.

The PI-controlled archive requested by the initial audit was subsequently supplied and checked in this closeout:

- `goes010226.zip`;
- SHA-256 `7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581` — **exact match** to the retained manifest;
- 59 daily NetCDF files, 16,992 timestamps at 300-s cadence.

This closes the raw-input blocker for source-time semantics and exact historical fallback identification. The only remaining input blocker is for a **practical operational-channel claim**: actual as-received L2 publication/delivery/version timing is still `UNKNOWN`.

## 1. Canonical evidence

Repository sources at the starting commit:

- `experiments/RE-GOES19-PROTON-RATE-01/goes19_adapter.py` — source identity, time conversion, E/W mapping, validity, calibration;
- `experiments/RE-GOES19-PROTON-RATE-01/rate_pipeline.py` — bridge, transport/rate construction and CSV writer;
- `experiments/RE-GOES19-PROTON-RATE-01/goes19_audit.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/rate_diagnostics.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/input_manifest.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/noaa_revision_semantic_patch.json`;
- `experiments/RE-GOES19-PROTON-RATE-01/REPORT.md`.

Additional controlled input used in this closeout: the exact PI archive above. `date_created` is retained only as archive/product metadata and is **not** interpreted as initial operational availability.

Status vocabulary:

- **KNOWN/RETAINED** — directly supported by pinned code/data/metadata;
- **DERIVED LOWER BOUND** — follows from the averaging interval;
- **UNKNOWN** — not established by current evidence;
- **RETROSPECTIVE ONLY** — uses future records or later archive state.

## 2. Temporal meaning of one record — source-level check closed

Inspection of all 59 controlled NetCDF files gives one uniform time contract:

- root `time_coverage_resolution = PT5M`;
- `time.long_name = "Time stamp at the start of the averaging period, in seconds since 2000-01-01 12:00:00 UTC"`;
- `time.units = "seconds since 2000-01-01 12:00:00 UTC"`;
- no `time.bounds` attribute and no separate time-bounds dataset were present;
- each daily file has `time_coverage_start` at 00:00 UTC and `time_coverage_end` at the next 00:00 UTC;
- first series timestamp: `2026-01-01T00:00:00Z`;
- last series timestamp: `2026-02-28T23:55:00Z`; its nominal averaging interval ends at `2026-03-01T00:00:00Z`.

Therefore, for a CSV/source timestamp `t`, the measurement interval is

`[t, t + 300 s)`.

The **complete** five-minute average cannot be available before `t + 300 s`. Any additional L2 processing, publication, communication, project-side transformation and controller-delivery delay remains `UNKNOWN`. For a future conditional comparator the admissible notation is therefore

`availability_time = t + 300 s + L`, with `L >= 0` explicit and not claimed as measured GOES latency.

## 3. Causality of the existing transformation

### 3.1 Same-record operations

Once the completed source record is available, these existing transformations do not require future timestamps:

- fill/nonfinite and yaw validity handling;
- E/W physical-direction reconstruction;
- fixed P1–P5 correction when legacy bounds are detected;
- keV-to-MeV unit conversion;
- fixed low-energy `gamma={0,2,4}` scenarios anchored to the same-row P1 value;
- pinned static transport and `sigma(E)` objects;
- P11 >500 MeV contribution;
- local P10/P11 390–500 MeV fit when both local values support the fit;
- arithmetic `(E+W)/2` after both same-row directional chains exist.

This establishes only absence of future-sample dependence. It does not establish real operational implementation or processing latency.

### 3.2 Global direction-median bridge fallback

`high_energy_gap_bridge()` is retrospective on fallback rows: it first collects fitted `gamma` over the full supplied time record, computes a direction-wide median, and then assigns that median where the local P10/P11 fit is unavailable. Hence a fallback at `t_k` can depend on samples with timestamps after `t_k`.

The raw-byte extraction exactly reproduces the retained diagnostics:

| Quantity | Result |
|---|---:|
| East fallback directional rows | 576 |
| West fallback directional rows | 920 |
| Total fallback directional rows | 1,496 |
| Unique timestamps with >=1 fallback direction | 1,449 |
| Timestamps with both directions in fallback | 47 |
| Timestamps with exactly one fallback direction | 1,402 |
| Fraction of all 16,992 timestamps whose central E/W rate inherits fallback | 8.53% |
| First affected timestamp | `2026-01-01T00:45:00Z` |
| Last affected timestamp | `2026-02-28T20:55:00Z` |

All 1,496 fallback directional rows have nonpositive/unusable P10 for the local fit. In 1,494 of them P11 remains positive/finite; two East rows also lack a positive/finite P11. This is exactly the predicate used by the historical implementation.

The row-level mask is stored as `fallback_rows.csv.gz` (CSV columns: timestamp, direction, algorithm version, P10/P11 positive-finite flags, fallback flag). It is a provenance table only; it does not alter the frozen historical rate series.

For causal use, any derived `lambda_E/W` using the global-median fallback is **RETROSPECTIVE ONLY**. The central `(E+W)/2` value inherits that status whenever either direction is affected.

## 4. Missing data, E/W aggregation, calibration and archive revisions

### Missingness / quality

Raw extraction confirms 16,971 valid rows per direction and 21 timestamps invalid in both E and W; there are no one-direction-only validity losses in this controlled set. The adapter performs no time interpolation or smoothing. Missing data must therefore remain explicit in later `M(I)` construction.

DQF fields are warning/status metadata, not a quantitative reliability penalty selected by this task.

### E/W aggregation

E and W are reconstructed and propagated separately. `(E+W)/2` is a declared central estimator, not a measured omnidirectional spectrum. Directional disagreement and validity/status must remain available alongside the central value.

### Calibration

The P1–P5 correction is a fixed same-record transformation once the correction constants are known; it has no future-time dependence within the Jan–Feb series. That does not prove when an operational feed first carried those corrected values.

### Late archive revision

The earlier audit established seven later public-file byte revisions for 2026-01-14…20 and scientific-value differences for Jan 19–20. The present closeout deliberately used the PI-controlled archive whose ZIP hash matches the pinned manifest. Later public replacements are valid retrospective provenance objects, not evidence of values available at the historical decision time.

## 5. Three information objects

| Object | Definition | Permitted use |
|---|---|---|
| **Archival retrospective reference** | exact PI-controlled GOES archive + historical adapter + frozen rate pipeline, including global-median fallback | Reproduce the selected archived environment; hindsight components remain labelled retrospective. |
| **Conditional delayed-data comparator** | completed-bin observations enter no earlier than `t+300s+L`; `L>=0` explicit; global-median-fallback-derived values are masked/unresolved unless a separately approved causal treatment is supplied | Future bounded real-temporal comparison with hypothetical/parameterized delay. |
| **Practical operational channel** | a real feed/product with evidenced acquisition, processing, publication, delivery and revision timing | **NOT ESTABLISHED**. No practical latency guarantee may be claimed. |

## 6. Minimal input contract for the next gate

| Field / signal | Measurement interval | Availability | Processing | Future dependence | Uncertainty / status | Permitted use |
|---|---|---|---|---|---|---|
| `timestamp_utc` | `[t,t+300s)` | complete average not before `t+300s` | source UTC stamp, no shift | none | source semantics directly verified on all 59 files | interval index / lower availability bound |
| E/W P1–P10 L2 average | same bin | `t+300s+L_source`, extra latency UNKNOWN | yaw, fill, units, fixed P1–P5 correction | none by itself | L2 uncertainty, DQF, calibration/background caveats | conditional external observation; not instantaneous flux |
| E/W P11 | same bin | same lower bound | yaw / validity | none by itself | L2 uncertainty | same-bin high-energy observation |
| validity + DQF | same bin | with associated L2 record | retained status | none | 21 jointly invalid timestamps; DQF not mapped to risk here | preserve missingness/status |
| local P10/P11 bridge | same bin | after same-bin inputs + processing | local power-law fit | none when fit exists | extrapolation/model limitation | conditional causal comparator component |
| global-median fallback bridge | nominally same bin | exact frozen value requires full-record population | whole-series median + same-row P11 | **YES** | 576 E / 920 W rows; exact row mask now retained | retrospective only; mask/unresolved in causal comparator pending approved treatment |
| `lambda_E/W_s-1` | same environmental bin | after all required causal inputs + processing | frozen transport/sigma/scenario chain | inherits bridge status | physical/model interface remains PARTIAL | retrospective reference; causal comparator only where all contributing information is causal |
| `(E+W)/2` central `lambda` | same bin | after both directions | arithmetic mean | inherits either direction | not measured omnidirectional flux | declared comparator estimator with E/W/status retained |
| `m5=300*lambda` | same bin | same as central `lambda` | algebraic interval expectation | inherits central status | not failure probability | bin exposure descriptor only |

## 7. What the five-minute average still does not establish

The current evidence does **not** establish that the reported average is:

- the instantaneous intensity anywhere inside the bin;
- an upper bound on within-bin intensity;
- a bound or predictor for the next bin;
- available at its start timestamp;
- the same version/value historically available in an operational feed;
- sufficient by itself to bound exposure between the latest completed bin and a future decision.

The next separately approved real-temporal specification must therefore declare, rather than inherit silently:

- within-bin exposure/state representation;
- relation/uncertainty set from E/W L2 observations to the latent rate used by reliability;
- future-exposure rule/bound after the latest completed bin;
- value or sweep for delayed-data latency;
- missing-bin and E/W-disagreement treatment;
- causal treatment for global-median-fallback rows (masking, widened model set, or another separately justified rule);
- processing-time accounting from L2 observation to the controller-facing `lambda_bit` object.

No choice among those alternatives is made here.

## 8. Reproducible real-section selection rule

To avoid selecting windows on later control success:

1. Freeze the source/reference series, window length and one input-only stratification rule before reliability/policy computation.
2. Partition Jan–Feb 2026 into non-overlapping windows anchored at `2026-01-01T00:00:00Z`.
3. Apply only predeclared input-quality eligibility rules, including explicit use of `fallback_rows.csv.gz` and the 21 invalid timestamps.
4. If only a bounded subset is needed, select using predeclared environmental/input descriptors (for example level or change), with earliest-UTC tie-break.
5. Do not inspect `F_A`, feasibility, selected `T_scrub`, resource cost or savings during window selection.
6. Freeze selected UTC intervals before the real-temporal reliability/control calculation.

Offline case selection may inspect the retrospective input series; controller information inside each case must still obey the causal availability contract.

## 9. Remaining blocker

### Required only for a practical operational-channel claim

Need a traceable artefact that establishes **as-received SGPS L2 five-minute availability and version/revision timing**, for example:

- timestamped NOAA/NCEI publication/download logs for the relevant records;
- an authoritative interface/product specification defining production/publication latency and revision semantics for this exact L2 product; or
- a preserved as-received operational stream/archive with acquisition timestamps and version identity.

Absent such evidence, real processing/delivery latency remains `UNKNOWN`. A future experiment may parameterize `L`; it must not call the chosen value measured GOES operational latency.

There is **no remaining raw-data blocker** for the row-exact fallback mask or source timestamp semantics.

## 10. Verification actually performed

- Verified the supplied archive SHA-256 against the pinned manifest: exact match.
- Confirmed 59 controlled NetCDF files and 16,992 timestamps at exactly 300-s cadence.
- Inspected raw `time` attributes in every file; confirmed start-of-averaging-period semantics and absence of explicit bounds variable/dataset.
- Recomputed historical E/W validity and the exact fallback predicate from raw P10/P11 values without transport.
- Reproduced historical fallback counts exactly: E=576, W=920.
- Materialized the exact row-level fallback mask and compact statistics; no frozen rate value was changed.
- No RADAR/COSRAD, transport regeneration, policy search, reliability calculation, Monte Carlo, estimator training or control optimization was executed.

## Final answer to the gate

The stop rule is satisfied:

- **retrospective reference:** fully identified and reproducible from the pinned archive;
- **admissible causal delayed-data input:** completed five-minute bins with availability no earlier than `t+300s+L`, explicit missing/status information, and future-dependent fallback rows masked/unresolved unless a future approved causal treatment is supplied;
- **remaining assumptions:** within-bin representation, future-exposure bound, uncertainty mapping and latency parameter are explicitly left for the next preexecution specification;
- **operational channel:** remains **UNPROVEN** solely because actual publication/delivery/version timing is not evidenced.

Orchestrator can now prepare the exact real-temporal EXP/derivation specification for separate PI approval. This task does not authorize its execution.
