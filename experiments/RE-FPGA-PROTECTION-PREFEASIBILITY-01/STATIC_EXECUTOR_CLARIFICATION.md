# RE-FPGA-STATIC-EXECUTOR-CHECK-01 — STATIC EXECUTOR CLARIFICATION

**Research Engineer.**  
**Task base / handoff:** `b45f77106d79f12ebc7b0ba1c642659a7e4a2e27`.  
**Input prefeasibility:** `08e7838eeb15f117774fa1b838c1d4264dd13d36`, `experiments/RE-FPGA-PROTECTION-PREFEASIBILITY-01/REPORT.md`.  
**Literature input:** `4c65d946ca043b6383c2a70d4c09865bec44c550`, `docs/evidence_synthesis/DRAFT-PA-FPGA-OBJECT-SELECTION-01.md`.  
**Scope:** documentary/constructive clarification only; no RTL, synthesis, hardware bring-up, injection campaign, hysteresis tuning, new probability model, RES-004 execution, PR or merge.

## 1. Direct answer

**The static variant is constructively sufficient for the defined Productive ↔ Protected switching. DFX is not required for any functional property named in the present workload contract.**

The same three AES-256 cores can remain resident in one configuration:

- **Productive:** core 0 serves `P`, core 1 serves `B1`, core 2 serves `B2`;
- **Protected:** all three cores receive the same `P` packet and a 2-of-3 result quorum is used; `B1/B2` remain queued.

A mode transition therefore requires changes only in run-time state/registers/multiplexers and core reset/load/start control. It does **not** require configuration-frame modification. Consequently the normal Productive ↔ Protected transition does not require SEM to enter Idle, does not require ICAP/PCAP ownership hand-off, partial-bitstream loading, readback image verification, or SEM re-initialization.

DFX remains relevant only for a **different named property** not required here: reclaiming/replacing fabric, using alternative placement/implementation, or system-level recovery from configuration state that cannot be safely restored by normal SEM correction. Those are recovery/reallocation functions, not ordinary mode switching.

This conclusion is architectural/semantic. The exact AES IP has not been selected and no synthesis has been run; resource fit, timing and actual physical separation of the three instances remain unverified.

## 2. Static one-bitstream structure

The minimal static structure is:

```text
                    +---------------- PS / trusted lab infrastructure ----------------+
P queue ---------->| packet descriptors / payload / commit log / mode request         |
B1 queue ----------|                                                               |
B2 queue ----------|                                                               |
                    +-------------------------------+-------------------------------+
                                                    |
                                                    v
                                         +--------------------+
                                         | dispatcher/router  |
                                         | mode, epoch, seq_id |
                                         +---+-----------+----+
                                             |           |
                       Productive: P --------+           +-------- B1/B2
                       Protected: broadcast P to all three cores
                                             |
                 +---------------------------+---------------------------+
                 v                           v                           v
           +-----------+               +-----------+               +-----------+
           | AES core0 |               | AES core1 |               | AES core2 |
           +-----+-----+               +-----+-----+               +-----+-----+
                 |                           |                           |
                 +---------------------------+---------------------------+
                                             |
                                  +-------------------------+
                                  | result capture + quorum |
                                  | / direct-output select  |
                                  +------------+------------+
                                               |
                                               v
                                         commit interface
```

The voter/result selector is always present in the static configuration. In Productive it is bypassed for independent queue results; in Protected it accepts only results belonging to the same `mode_epoch` and `seq_id` and commits a result only when at least two complete results agree. If no 2-of-3 equality quorum exists, no priority result is committed.

No fourth AES core and no run-time software AES oracle is introduced.

## 3. Minimum packet/core interface contract

No concrete open AES core is selected in this task. Integration is therefore **UNKNOWN** until a core satisfying the following contract is chosen.

### 3.1 Core-facing signals/semantics

Each of the three instances must provide, directly or through a thin wrapper:

- deterministic `start` / input acceptance handshake;
- `busy` or equivalent in-flight indication;
- `done/result_valid` and stable result until acknowledged;
- synchronous or otherwise well-defined reset/clear that discards in-flight internal state;
- deterministic key load / key-valid semantics;
- load of all packet-dependent cryptographic state required before `start`;
- no hidden cross-packet state after reset unless that state is externally checkpointed;
- ability to associate the returned result with an externally held `seq_id` and `mode_epoch`.

An explicit `abort` input is not required if reset safely invalidates the operation. If the chosen IP cannot be reset while busy, transition must wait for `done`; this affects transition latency but not the static architectural conclusion.

### 3.2 Packet record

AES-256 alone does not define packet state. The queue record must therefore contain enough information to restart the exact same operation, for example:

`{queue_id, seq_id, key_id, cryptographic_mode, IV/nonce/counter-or-chaining-start-state, payload pointer/data, length, auxiliary mode fields}`.

The same record is used in all compared modes. State shared across packets is not allowed unless it is explicitly externalized/checkpointed. Thus AES-CTR/GCM/CBC-like processing is admissible only if the selected wrapper can restore all required per-packet IV/nonce/counter/chaining state from the descriptor. A mode with unrecoverable cross-packet state would violate this executor contract and would have to be changed or checkpointed before the experiment.

### 3.3 Result/commit record

Each core result is captured as at least

`{core_id, queue_id, seq_id, mode_epoch, result, status}`.

A late result from an old epoch is discarded. `seq_id` prevents an old/background result from being mistaken for the currently protected priority packet.

The offline known-good AES implementation used to score experimental correctness is **not** available to the run-time executor. In Productive mode the single selected core result is committed according to normal protocol; if it is wrong, that wrong result remains a measured baseline outcome. In Protected mode the run-time rule is the declared hardware quorum, not comparison against an offline oracle.

## 4. State machine and safe transition semantics

Minimal control states:

- `PROD_ACTIVE`;
- `QUIESCE_TO_PROTECTED`;
- `PROTECTED_ARM`;
- `PROTECTED_ACTIVE`;
- `QUIESCE_TO_PRODUCTIVE`;
- `PRODUCTIVE_ARM`;
- `FAULT_HOLD`.

`mode_epoch` increments on every accepted mode change or fault-induced restart. New work is admitted only in an `*_ACTIVE` state.

### 4.1 Productive → Protected

1. Stop admission of new work to all three AES wrappers.
2. For each in-flight `P/B1/B2` packet either:
   - allow it to complete and commit before the boundary; or
   - mark it uncommitted, retain its queue record, reset the corresponding core, and replay it later.
3. Enter `PROTECTED_ARM`; increment `mode_epoch`.
4. Reset/clear **all three** AES instances. Do not attempt to align their pre-existing internal states.
5. Load the same key and the same next `P` packet descriptor/state into all three wrappers.
6. Change the run-time input route to broadcast `P`; enable the protected quorum path.
7. Start all three instances for the same `seq_id`; enter `PROTECTED_ACTIVE` only after the arm sequence has completed.
8. `B1/B2` arrivals and uncommitted packets remain queued; they are not discarded and are not counted as processed.

### 4.2 Protected → Productive

1. Stop admission of a new protected `P` packet.
2. Complete the current protected packet if a valid quorum can be committed, otherwise invalidate it and retain/replay its input.
3. Increment `mode_epoch`; reset/clear all three AES instances.
4. Route `P`, `B1`, `B2` to cores 0,1,2 respectively.
5. Load the required per-queue key/state descriptors and start the oldest pending eligible packets.
6. Resume three independent queues.

No internal AES state is migrated between replicas or modes. Transition correctness relies on reset + replay from externally retained packet state.

## 5. Addressed transition cases

| Case | Static executor disposition | DFX implication |
|---|---|---|
| Packet already completed before transition | Commit under old `mode_epoch`; then arm new mode. | None. |
| Packet unfinished at transition | Either drain before boundary or invalidate, reset and replay from retained descriptor. Never count partial work. | None. |
| Three cores have unequal internal state before Protected | Ignore old state. Reset all three and reload same key/packet state. Equality after reset is synchronization only, not proof of configuration integrity. | None for normal switch. |
| Two Protected results agree, one differs | Commit only the matching 2-of-3 result for the same epoch/seq; raise mismatch/fault evidence. | None automatically; later recovery policy may act. |
| No 2-of-3 result quorum / timeout | Do not commit; enter retry/fault path and preserve input. | DFX/full reconfiguration is a possible recovery action only if configuration integrity cannot be restored/established otherwise. |
| SEM reports a corrected configuration event while work is in flight | Configuration correction does not repair application state. Conservatively invalidate affected in-flight epoch, reset relevant/all cores and replay before new commit if association is uncertain. Already emitted output is not retroactively repaired. | Normal mode switch still static. |
| Known uncorrected / uncorrectable configuration error in a line or common logic | Enter `FAULT_HOLD`; do not claim that reset makes the replica healthy and do not enter Protected merely because three states now match. Require configuration recovery/system action before resuming. | DFX/full reconfiguration can be justified here as recovery, not as Productive↔Protected switching. |
| No SEM report | Not proof of clean configuration. It only means no report has been delivered under the assumed SEM observation contract. | None. |
| Return to Productive with B1/B2 backlog | Reset/re-arm, then process preserved backlog with original sequence IDs. | None. |

A simple conservative implementation can increment a `config_event_epoch` on relevant SEM correction/uncorrectable reports. A result dispatched before such an event is not committed after the event unless the experiment has an explicitly justified narrower association rule. This is bookkeeping on available SEM reports, not a claim that all configuration faults are observable before use.

## 6. SEM behavior in the static variant

The normal static mode transition performs no ICAP/PCAP operation and changes no configuration frame. Therefore there is no technical reason to suspend SEM merely to change `mode`.

Primary-source check:

- AMD **PG187 v3.1**, `Observation (Mitigation Modes Only)`: Observation is the normal state in which SEM observes the configuration system and transitions to correction when an error is detected.  
  https://docs.amd.com/r/en-US/pg187-ultrascale-sem/Observation-Mitigation-Modes-Only
- PG187 `Idle`: entering Idle disables built-in configuration-memory scan/check; errors are then not detected/corrected by SEM.  
  https://docs.amd.com/r/en-US/pg187-ultrascale-sem/Idle
- PG187 `ICAP Arbitration Interface`: ICAP arbitration is needed when another function takes the ICAP; returning ownership normally causes SEM reboot/reinitialization, while the manual Idle path is safe only if configuration memory/settings were not manipulated. If ICAP sharing is unused, the arbitration inputs are tied to permanent SEM access.  
  https://docs.amd.com/r/en-US/pg187-ultrascale-sem/ICAP-Arbitration-Interface
- PG187 `Partial Reconfiguration Support`: SEM + PR is supported on UltraScale+, but that compatibility does not make PR necessary for a run-time logic-mode change.  
  https://docs.amd.com/r/en-US/pg187-ultrascale-sem/Partial-Reconfiguration-Support

**INFERENCE:** with one static bitstream the Productive↔Protected executor should leave SEM in its ordinary mitigation/Observation path. Stopping SEM during a pure register/mux mode change would only create an unnecessary observation gap.

If a system-level recovery later uses DFX/full reconfiguration, the previous prefeasibility requirements again apply: quiesce, configuration ownership hand-off, intended-image verification where required, SEM re-initialization and application replay.

## 7. Common points of failure and independence limits

The three AES instances do not make the complete executor triplicated. Important common points are:

- mode register / mode-request path;
- P/B1/B2 input router and broadcast network;
- result selector / protected quorum voter;
- shared clock and reset distribution;
- key/configuration distribution into the three cores;
- PS/DDR queue and commit infrastructure;
- SEM and its monitor/health path;
- any common static-shell interconnect used by all replicas.

PS/DDR remains trusted laboratory infrastructure in the same limited sense as the prefeasibility report. This task does not convert it into a radiation-tolerant flight supervisor.

The voter/router are configuration-sensitive logic. A configuration fault there can defeat replica independence. Constant SEM reduces configuration-error residence time but does not guarantee that a wrong result cannot be emitted before correction.

### 7.1 Preserving three actual core instances

Three copies written in RTL are not by themselves proof of three independent implementation domains. Vivado can flatten hierarchy and optimize logic.

Targeted AMD synthesis documentation:

- **UG901 2026.1, `KEEP_HIERARCHY`**: `TRUE` prevents cross-hierarchy optimizations; hierarchy preservation is explicitly a synthesis control, not a reliability property.  
  https://docs.amd.com/r/en-US/ug901-vivado-synthesis/KEEP_HIERARCHY
- **UG901 2026.1, `DONT_TOUCH`**: `DONT_TOUCH` can be applied to a module/entity/component and is forward-annotated to implementation to prevent logic optimization; AMD cautions that it can constrain optimization.  
  https://docs.amd.com/r/en-US/ug901-vivado-synthesis/DONT_TOUCH

For a future implementation the three AES instances must be preserved intentionally (for example instance/module `DONT_TOUCH`, `KEEP_HIERARCHY`, or equivalent controlled out-of-context implementation as appropriate) and then **verified in the post-synthesis/post-implementation netlist**. These attributes do not establish physical separation, independent configuration frames, absence of shared routing, or independence of radiation faults. Any later TMR reliability claim needs placement/configuration-frame evidence and the common-point accounting above.

No resource, timing, power or placement result is claimed here because synthesis was not run.

## 8. Static versus DFX — mandatory operations and costs

| Operation / property | One static configuration | DFX mode switch |
|---|---|---|
| Stop new packet admission | Required | Required |
| Drain or invalidate/replay in-flight packets | Required | Required |
| Reset/reload AES state | Required | Required after RM replacement |
| Change P/B1/B2 routing | Register/mux selection | Encoded by selected RM/static shell |
| Quorum voter | Permanently present; enabled in Protected | Can differ by RM, depending architecture |
| SEM scan during ordinary mode switch | Remains active | Must coordinate with configuration access |
| ICAP/PCAP ownership transfer | Not required | Required |
| Partial bitstream load | Not required | Required |
| Intended-image readback/check after mode switch | Not required because image is unchanged | Required by the earlier safety protocol if using DFX transition |
| SEM re-initialization after altered configuration | Not required | Required/safest path per SEM/PR ownership contract |
| Replay after transition | Only packets not safely committed | Required for invalidated state/work |
| Permanent fabric cost | Three AES + router + voter/control always resident | May permit different RM resource layouts |
| Transition time/resource | Logic quiesce/reset/load only; **not measured** | Adds configuration transfer, verification and SEM re-init; **not measured** |
| Can physically reclaim/replace fabric | No | Yes |
| Can by itself prove configuration is healthy | No | No; image verification/SEM/system health still needed |

The static design therefore removes an entire class of transition operations without changing the task semantics. This is an engineering simplification, not evidence that adaptive switching is scientifically useful.

## 9. What would force DFX back into the design

DFX becomes necessary only if a later requirement establishes at least one of the following:

1. all required Productive and Protected logic cannot coexist within the target resource/timing budget;
2. Productive mode must physically reuse the replica/voter fabric for different useful accelerators rather than merely route three AES tasks;
3. Protected mode requires placement/routing or an implementation image that cannot coexist statically with Productive;
4. recovery requires replacing/relocating logic after an unresolved configuration fault or known bad region.

None of these properties is currently part of the accepted workload requirement. Their presence is **UNKNOWN**, not assumed.

## 10. Residual concrete integration obstacle

The static architecture itself is not blocked by one missing scientific fact. The first concrete engineering gate is narrower:

> select one AES-256 core/wrapper and verify that its reset, done/valid, key-load and packet-state semantics satisfy §3, and that three preserved instances plus the static router/voter fit the chosen device after synthesis/implementation.

No broad IP search was performed. If the selected AES core has non-replayable internal state, lacks a safe reset/packet boundary, or the three instances cannot be preserved/fitted, that becomes a specific implementation blocker. Until then, integration is **UNKNOWN**, not evidence for DFX.

The current RE environment still has no detected `vivado`, `vitis`, `xsct`, `xsim`, `hw_server`, `iverilog`, `verilator`, `yosys` or attached `/dev/ttyUSB*`/`ttyACM*`; this was rechecked for the present task. The handoff explicitly states that lack of a board does not block this documentary conclusion.

## 11. Final disposition

**OWN ENGINEERING CONCLUSION:** for the exact three-core AES workload fixed in `RE-FPGA-PROTECTION-PREFEASIBILITY-01`, one static FPGA configuration is constructively sufficient for Productive ↔ Protected execution. The candidate next executor is therefore the static router/reset/replay/quorum design above, not the earlier DFX mode-change path.

The historical DFX scheme remains valid provenance and remains a possible system-recovery or future fabric-reallocation mechanism. It is not required for the ordinary mode switch unless a later synthesis/architecture requirement identifies one of the concrete properties in §9.

This result establishes only a minimal executor architecture and its safety boundaries. It does **not** establish performance benefit, risk reduction, fault-prediction value, scientific novelty, a reason to change the dissertation topic, a new RES, or a Scientific Review PASS. Per the handoff, work stops here for the Orchestrator/user strategic gate.
