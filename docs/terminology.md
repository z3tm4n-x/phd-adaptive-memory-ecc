# Terminology and Notation

Единый словарь терминов, сокращений, математических обозначений и единиц. Заполняется по мере стабилизации модели.

## Terms

| Term | Russian / meaning | Status | Source / note |
|---|---|---|---|
| ECC | Error-Correcting Code | working | TBD |
| scrubbing | периодическое чтение/коррекция/перезапись содержимого памяти | working | уточнить терминологию по литературе |
| SEU | Single-Event Upset | working | TBD |
| MCU / MBU | Multiple-Cell / Multiple-Bit Upset | working | уточнить используемое обозначение |
| protection domain | explicitly declared controller-managed SRAM domain aggregated under one reliability contract | accepted working definition | DEC-001 |
| reporting window | interval over which occurrence of the declared event is reported | accepted working definition | DEC-001; distinct from upset-count, word-exposure and mission horizons |
| parent radiation event | one declared physical radiation interaction/event whose affected cells retain common provenance before and after `W` | accepted modeling object | RQ-002 Evidence Audit; DEC-003 |
| physical event topology | multiplicity plus the declared spatial/coordinate arrangement of cells affected by one parent event before `W` | working definition | RQ-006; coordinates may be unavailable or only indirectly observed in a test |
| joint post-`W` codeword-impact mark | one parent event represented by its simultaneous impacts across all affected ECC codewords after applying declared `W` | accepted comparison interface | DEC-003; losslessness for the declared state update must be verified in EXP-001 |
| representation reduction | declared transformation from a richer event representation to a joint, marginal or scalar representation, with recorded information loss and validity condition | working definition | RQ-006 / DEC-003 |
| information state | explicitly declared set `I` of retained observations/summaries, provenance, resolution, uncertainty and missing components available for a stated decision | accepted gate-level working object | accepted information-deficit control-price gate; exact online semantics remain RQ-004/RQ-007 candidate |
| control-resource price of information deficit | component-wise resource consequence of the action made necessary by a coarser information state and wider compatible model set, relative to a richer information state under the same physical domain, horizon, constraint, action set and selection rule | accepted gate-level distinction | does not include the cost of acquiring richer information |
| information-acquisition cost | separately measured hardware, energy, computation and communication cost of obtaining, storing and processing richer information | accepted gate-level distinction | RQ-004/RQ-005 interface; not silently included in control-resource price |
| net information balance | a later, explicitly justified comparison of control-resource consequence and information-acquisition cost in compatible units and under a declared aggregation/decision rule | deferred object | not an automatic scalar “value of information” |
| conditional action invariance | equality of the admissible or selected restoration action only over a declared domain of reliability threshold, horizon, initial state, action set, feasibility semantics, selection rule and resource criterion | accepted gate-level working object | a point equality does not imply that information is generally unnecessary |
| `J-A` / `J-B` controlled pair | EXP-001-local pair of post-`W` models with identical one-event per-word impact probabilities, fixed two-distinct-word cardinality and different joint pair association | accepted bounded construct | EXP-001 / RES-001; endpoint role applies only under the complete fourteen-condition domain |
| `L3-U` | EXP-001 scalar comparator whose primitive objects are ungrouped individual bit/upset arrivals over `A`; parent-event grouping is discarded | accepted Phase-1 comparator | EXP-001 |
| `L3-E` | scalar parent-event-arrival comparator without an impact mark; distinct from `L3-U` and requiring an explicit event-to-state reconstruction | deferred comparator | EXP-001 Phase 1 |
| normative reported characteristic | test/calculation output such as a classified ORE count, cross section, fitted sensitivity parameter, rate or probability indicator; not automatically a raw-event record or ECC-level reliability metric | working distinction | NORMATIVE-BASELINE-01 |

## Symbols

| Symbol | Meaning | Unit | Status |
|---|---|---|---|
| \(E_{\mathrm{cap}}(A;t_0,T)\) | Event that at least one codeword in \(A\) exceeds its declared ECC correction capability at some time in \(H(t_0,T)\) | event / dimensionless | accepted working definition, DEC-001 |
| \(A\) | Explicitly declared controller-managed SRAM protection domain | set of codewords | accepted working definition, DEC-001 |
| \(A_j\) | Homogeneous member of the explicit disjoint partition \(A=\biguplus_j A_j\) used before quantitative aggregation when ECC, \(W\), arrival, bank/block or scrubbing semantics differ | set of codewords | accepted working definition, DEC-001 |
| \(W\) | Declared physical-cell-to-ECC-codeword mapping, including any interleaving semantics required by the model | mapping | `TBD` target; required model input |
| \(N_w(t)\) | Current number of distinct erroneous bit cells in codeword \(w\) at time \(t\), under the declared correction/writeback semantics | count | accepted working definition, DEC-001 |
| \(t_c(w)\) | Number of distinct erroneous bits the declared ECC configuration guarantees to correct in codeword \(w\) | count | accepted working definition; concrete semantics remain RQ-003 |
| \(\tau_A(t_0)\) | First time at or after \(t_0\) when any codeword in \(A\) satisfies \(N_w(t)>t_c(w)\) | declared time unit | accepted working definition, DEC-001 |
| \(t_0\) | Start time / origin of a reporting window | declared time unit | accepted notation, DEC-001 |
| \(T\) | Non-negative duration of a reporting window | declared time unit | accepted notation, DEC-001 |
| \(H(t_0,T)\) | Reporting window \([t_0,t_0+T]\) | time interval | accepted working definition, DEC-001 |
| \(F_A(t_0,T;\mu_{t_0})\) | Probability that \(\tau_A(t_0)\le t_0+T\), conditional on the declared initial state/distribution | probability / dimensionless | accepted general metric, DEC-001 |
| \(F_A(t_0,T)\) | Restricted abbreviation of \(F_A(t_0,T;\mu_{t_0})\) when \(\mu_{t_0}\) is fixed explicitly elsewhere in the quantitative model | probability / dimensionless | accepted shorthand restriction, DEC-001 |
| \(\mu_{t_0}\) | Declared initial state or state distribution at \(t_0\), covering every state variable required by the quantitative model | state or probability distribution | mandatory model specification, DEC-001 |
| \(H_{\mathrm{req}}\) | Required reporting window, including its origin and duration | time interval | `TBD`; requires traceable system/mission provenance |
| \(\varepsilon_{\mathrm{req}}\) | Required upper bound for the declared reliability metric | probability / dimensionless | `TBD`; no numerical value assigned |
| \(q\) | Probability that two consecutive two-word parent-event marks are disjoint in the RES-001 four-word class; \(q=2(a^2+c^2+e^2)\) | probability / dimensionless | accepted local symbol, RES-001 only; \(1/6\le q\le1/2\) under all fourteen conditions |
| \(m\) | Mean number of parent events in one restoration interval, \(m=\lambda T_{\mathrm{scrub}}\), in the RES-001 HPP construction | expected count / dimensionless | accepted local symbol, RES-001 only |
| \(k\) | Number of complete equal restoration intervals in the aligned RES-001 reporting window, \(T=kT_{\mathrm{scrub}}\) | count | accepted local symbol, RES-001 only |
| \(S(q,m)\) | One-interval probability of not exceeding ECC capability in the RES-001 class, \(e^{-m}(1+m+qm^2/2)\) | probability / dimensionless | accepted local symbol, RES-001 only |
| \(I\) | Declared information state available for a stated reliability/control decision | structured information set | accepted gate-level symbol; concrete channels and timing remain RQ-004/RQ-007 candidate |
| \(M(I)\) | Nonempty set of processes, event marks, mappings `W`, initial states and transition semantics compatible with `I` and all declared constraints | model set | accepted gate-level symbol; not a selected stochastic family |
| \(U\) | Declared finite or parameterized set of admissible restoration actions; the primary first-stage action is `T_scrub` | action set | accepted gate-level symbol; extensions require separate justification |
| \(R_I(u)\) | Set of values of \(F_A(t_0,T;\mu_{t_0})\) induced by all models in \(M(I)\) under action \(u\) | set of probabilities | accepted gate-level symbol |
| \(F_I^-(u), F_I^+(u)\) | Established lower and upper bounds of \(R_I(u)\) when available | probability / dimensionless | accepted gate-level symbols; exactness/validity must be stated |
| \(U_{\mathrm{rob}}(I,\varepsilon)\) | Actions whose declared upper risk bound satisfies \(F_I^+(u)\le\varepsilon\) | action set | accepted gate-level symbol; \(\varepsilon\) may be an experimental sweep and is not automatically \(\varepsilon_{\mathrm{req}}\) |
| \(C(u)\) | Measurable component-wise resource-cost vector for action \(u\) | declared vector of units/proxies | accepted gate-level symbol; components and units remain RQ-005 responsibility; no arbitrary scalarization |

## Rule

Новый термин или обозначение, используемое в нескольких документах/моделях, должно сначала быть согласовано здесь. RQ-002 may add notation only after the corresponding model concept is accepted; parallel symbols must not be introduced silently.
