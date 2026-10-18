"""T186 sparse integer-time pilot. No random law or probability is inferred.

Optimization sees input marks only to identify words requiring explicit service.
The rule receives only publication/source times of its own ERR. Every clean
operation is counted analytically, including after A_T and at the final edge.
"""
from bisect import bisect_right
from dataclasses import dataclass, field
from fractions import Fraction
import heapq
import math


def ceildiv(a, b):
    return -(-a // b)


@dataclass
class Grid:
    words: int = 524288

    def start(self, j):
        return (j // 8) * 1568 + (j % 8) * 164

    def address(self, j):
        return (pow(3, -1, self.words) * j) % self.words

    def first(self, t):
        """First j with start(j)>=t; unbounded integer, not float."""
        if t <= 0:
            return 0
        j = (t // 1568) * 8
        while self.start(j) < t:
            j += 1
        return j

    def eligible(self, j, low):
        return not low or j < self.words or j % 3 == 0

    def count(self, a, b, low):
        if b <= a:
            return 0
        if not low:
            return b - a
        warm = max(0, min(b, self.words) - a)
        a = max(a, self.words)
        return warm + max(0, ceildiv(b, 3) - ceildiv(a, 3))

    def work(self, a, b, low, t, duration=92):
        """Integral before t of eligible disjoint pulses for slots [a,b)."""
        if b <= a or t <= self.start(a):
            return 0
        full = min(b, self.first(t - duration + 1))
        result = self.count(a, max(a, full), low) * duration
        # duration<=148<164; at most one partial pulse.
        j = max(a, full)
        if j < b and self.start(j) < t and self.eligible(j, low):
            result += min(duration, t - self.start(j))
        return result


@dataclass
class Rule:
    cfg: dict
    last_source: int | None = None
    short: int = 0
    long: int = 0
    recovery: int = 0
    pending: int = 0
    generation: int = 0
    processed: int = 0
    history: list = field(default_factory=list)

    def __post_init__(self):
        self.recovery = self.cfg["NR"] * self.cfg["timer_tick_ns"]

    def publish(self):
        self.pending += 1
        self.generation += 1

    def process(self, now, source):
        tick = self.cfg["timer_tick_ns"]
        pair = self.cfg["pair_source_ticks"] * self.cfg["source_tick_ns"]
        self.short = max(self.short, now + self.cfg["NW"] * tick)
        if self.last_source is not None and source - self.last_source <= pair:
            self.long = max(self.long, now + self.cfg["NH"] * tick)
        self.last_source = source
        self.pending -= 1
        self.processed += 1
        self.history.append(dict(processed_ns=now, source_ns=source,
                                 generation=self.processed,
                                 short_deadline_ns=self.short,
                                 long_deadline_ns=self.long))

    def low(self, now):
        return self.pending == 0 and now > max(self.short, self.long, self.recovery)

    def next_expiry_cut(self, now):
        deadline = max(self.short, self.long, self.recovery)
        return max(now + self.cfg["cut_ns"],
                   (deadline // self.cfg["cut_ns"] + 1) * self.cfg["cut_ns"])


def run(config, method, literal=False):
    if method not in ("constant_fast", "our_err_r4"):
        raise ValueError("unregistered method")
    for k, v in dict(frame_ns=1568, batch=8, c_ns=164, g_ns=196,
                     freeze_ns=320, ka=3).items():
        if config["calendar"][k] != v:
            raise ValueError("unregistered calendar")
    if config["bits"] != 38:
        raise ValueError("not full38")
    horizon = config["horizon_ns"]
    grid = Grid(config["words"])
    rule = Rule(config["policy"])
    adaptive = method == "our_err_r4"
    marks = config["injections"]
    apps = config["application_reads"]
    watch = set(x["word"] for x in marks)
    if literal:
        watch = set(range(grid.words))
    errors = {}
    first_hit = None
    heap, serial = [], 0
    trace, txs, correction, app_work = [], [], [], []
    mode_history = [(0, False)]
    state_low = False
    event_counts = {}
    # Priority at ties: injection, publication/processing, freeze, begin,
    # snapshot, commit, release. A tie is explicitly part of this model.
    def push(t, priority, kind, item):
        nonlocal serial
        if 0 <= t <= horizon:
            serial += 1
            heapq.heappush(heap, (t, priority, serial, kind, item))

    def decision_at(t):
        ix = bisect_right([x[0] for x in mode_history], max(0, t)) - 1
        return mode_history[ix][1] if t >= 0 else False

    def record_mode(t, low):
        nonlocal state_low
        if low != state_low:
            mode_history.append((t, low))
            trace.append(dict(t=t, event="permission", low=low))
            state_low = low

    for x in marks:
        if not 0 <= x["word"] < grid.words or not 0 <= x["bit"] < 38:
            raise ValueError("invalid mark")
        push(x["t"], 0, "injection", x)
    for w in sorted(watch):
        j = (3 * w) % grid.words
        push(grid.start(j), 4, "control_start", j)
    for i, x in enumerate(apps):
        ac = config["app"]
        start = ceildiv(x["arrival_ns"] + ac["inbound_ns"] -
                        ac["slot_offset_ns"], 1568) * 1568 + ac["slot_offset_ns"]
        push(start, 4, "app_start", (i, x))
    if adaptive:
        push(rule.next_expiry_cut(0), 2, "expiry", None)

    while heap:
        t, _, _, kind, x = heapq.heappop(heap)
        event_counts[kind] = event_counts.get(kind, 0) + 1
        if kind == "injection":
            w, bit = x["word"], x["bit"]
            e = errors.setdefault(w, {})
            if bit in e:
                del e[bit]
            else:
                e[bit] = t
            if len(e) > 1 and first_hit is None:
                first_hit = dict(t=t, word=w, bits=sorted(e))
            trace.append(dict(t=t, event=kind, word=w, bit=bit, weight=len(e)))
        elif kind in ("control_start", "app_start"):
            if t >= horizon:
                continue
            if kind == "control_start":
                j = x
                push(grid.start(j + grid.words), 4, kind, j + grid.words)
                low = decision_at(grid.start(j) - 320)
                if not grid.eligible(j, low):
                    continue
                w, arrival, tx_kind = grid.address(j), None, "control"
            else:
                i, req = x
                w, arrival, tx_kind = req["word"], req["arrival_ns"], "read32"
                j = None
                app_work.append((t, t + 184))
            tx = dict(start=t, word=w, kind=tx_kind, slot=j,
                      arrival=arrival, err=False, snapshot=None, end=None)
            txs.append(tx)
            push(t + 60, 5, "snapshot", tx)
        elif kind == "snapshot":
            tx = x
            tx["snapshot"] = t
            tx["err"] = bool(errors.get(tx["word"]))
            control = tx["kind"] == "control"
            duration = (148 if tx["err"] else 92) if control else 184
            tx["end"] = tx["start"] + duration
            if control and tx["err"]:
                push(tx["start"] + 64, 1, "publish", tx)
                push(tx["start"] + 132, 6, "commit", tx)
                correction.append((tx["start"] + 92, tx["start"] + 148))
            push(tx["end"], 7, "release", tx)
        elif kind == "publish":
            trace.append(dict(t=t, event="ERR", word=x["word"], slot=x["slot"]))
            if adaptive:
                rule.publish()
                record_mode(t, False)
                cut = (t // config["policy"]["cut_ns"] + 1) * config["policy"]["cut_ns"]
                push(cut, 2, "process", t)
        elif kind == "process":
            rule.process(t, x)
            record_mode(t, rule.low(t))
            push(rule.next_expiry_cut(t), 2, "expiry", None)
        elif kind == "expiry":
            record_mode(t, rule.low(t))
        elif kind == "commit":
            tx = x
            errors[tx["word"]] = {b: born for b, born in errors.get(tx["word"], {}).items()
                                  if born >= tx["start"]}
            trace.append(dict(t=t, event="commit", word=tx["word"],
                              remaining=sorted(errors[tx["word"]])))
        elif kind == "release":
            pass
        else:
            raise AssertionError(kind)

    total_slots = grid.first(horizon)
    # Marks at T count, but zero-duration starts at T do not.
    cuts = [(0, False)]
    for t, low in mode_history[1:]:
        j = grid.first(t + 320)
        if j < total_slots:
            cuts.append((j, low))
    cuts.append((total_slots, False))
    segments = [(a, b, low) for (a, low), (b, _) in zip(cuts, cuts[1:]) if b > a]
    def pulse_integral(intervals, a, b):
        return sum(max(0, min(b, y) - max(a, x)) for x, y in intervals)
    def base_prefix(t):
        return sum(grid.work(a, b, low, t) for a, b, low in segments)
    def price(a, b):
        return dict(control_base_ns=base_prefix(b)-base_prefix(a),
                    correction_extra_ns=pulse_integral(correction, a, b),
                    application_read_ns=pulse_integral(app_work, a, b))
    bus = price(0, horizon)
    bus["total_ns"] = sum(bus.values())
    started = sum(grid.count(a, b, low) for a, b, low in segments)
    if literal:
        controls = [q for q in txs if q["kind"] == "control" and q["start"] < horizon]
        assert started == len(controls), "literal operation count"
        literal_control_work = sum(min(horizon, q["end"] or q["start"]+92)-q["start"]
                                   for q in controls)
        assert literal_control_work == bus["control_base_ns"] + bus["correction_extra_ns"], "literal cost"
    unfinished = []
    # Any partial operation is in the last slot (or a sparse application).
    if total_slots:
        j = total_slots - 1
        if grid.eligible(j, decision_at(grid.start(j)-320)):
            tx = next((q for q in reversed(txs) if q["slot"] == j), None)
            end = tx["end"] if tx else (grid.start(j)+92 if grid.start(j)+60<=horizon else None)
            if end is None or end > horizon:
                unfinished.append(dict(kind="control", start_ns=grid.start(j),
                                       end_ns=end, charged_ns=horizon-grid.start(j),
                                       end_status="snapshot known" if end is not None else "snapshot after horizon; end unknown"))
    for tx in txs:
        if tx["kind"] == "read32" and tx["start"] < horizon and (tx["end"] or tx["start"]+184) > horizon:
            unfinished.append(dict(kind="read32", start_ns=tx["start"],
                                   end_ns=tx["start"]+184, charged_ns=horizon-tx["start"]))
    app_delays = []
    for tx in txs:
        if tx["kind"] == "read32":
            response = tx["start"]+184+config["app"]["outbound_ns"]+config["app"]["ready_ns"]
            app_delays.append(dict(arrival_ns=tx["arrival"], grant_ns=tx["start"],
                                   response_ns=response, delay_ns=response-tx["arrival"],
                                   response_within_horizon=response <= horizon))
    errors = {str(w): {str(b): born for b, born in sorted(e.items())}
              for w, e in sorted(errors.items()) if e}
    after = price(first_hit["t"], horizon) if first_hit else None
    if after is not None:
        after["total_ns"] = sum(after.values())
    err_events = [x for x in trace if x["event"] == "ERR"]
    explicit = [dict(start_ns=q["start"], word=q["word"], kind=q["kind"], slot=q["slot"],
                     err=q["err"], end_ns=q["end"])
                for q in txs if q["err"] or q["kind"] == "read32"]
    return dict(method=method, horizon_ns=horizon, words=grid.words, bits=38,
                Q=None, probability_status="not estimated; deterministic implementation pilot",
                first_exceedance=first_hit, err_events=err_events,
                started_control_operations=started,
                completed_control_operations=started-sum(x["kind"]=="control" for x in unfinished),
                started_application_operations=len(app_delays),
                unfinished_operations=unfinished,
                bus=bus, mean_bus_fraction_exact=str(Fraction(bus["total_ns"], horizon)),
                mean_bus_percent=100*bus["total_ns"]/horizon,
                bus_after_first_exceedance=after,
                mode_history=[dict(t_ns=t, low=low) for t, low in mode_history],
                effective_segments=[dict(first_slot=a, end_slot=b, low=low) for a,b,low in segments],
                processed_ERR_history=rule.history if adaptive else [],
                nominal_driver_services=horizon//config["policy"]["cut_ns"] if adaptive else 0,
                allocated_CPU_cores=1 if adaptive else 0,
                CPU_use_percent=None, CPU_time_ns=None,
                max_application_delay_ns=max((r["delay_ns"] for r in app_delays), default=0),
                application=app_delays, residual_errors=errors,
                trace=trace, explicit_nonempty_operations=explicit,
                simulator_work=dict(event_counts=event_counts, explicit_transactions=len(txs),
                                    watched_words=len(watch)))


def resource_checks(config):
    """Conservative all-history bounds, not sampled peaks or measured WCET."""
    F = Fraction
    # A 1ms window can meet at most ceil(width/frame)+2 frames. Count EVERY
    # control as long E, irrespective of policy, plus all pilot app requests.
    frames = ceildiv(1000000, 1568)+2
    e, r, read = F("148.501480"), F("92.500920"), F("185.001840")
    app_count = len(config["application_reads"])  # conservative for any window
    peak_ns = frames*8*e+app_count*read
    arrivals = sorted(x["arrival_ns"] for x in config["application_reads"])
    min_spacing = min((b-a for a,b in zip(arrivals,arrivals[1:])), default=None)
    app_response_upper = F(320+1568+320+80)+read
    return dict(
        peak_any_1ms_bus_upper_fraction=str(peak_ns/1000000),
        peak_any_1ms_bus_upper_percent=float(peak_ns/10000),
        peak_is_upper_not_observed_max=True,
        control_E_with_10pct_ns=str(e*F(11,10)),
        control_slot_ns=164,
        application_read_with_10pct_ns=str(read*F(11,10)),
        application_reservation_ns=240,
        response_with_10pct_ns=str(app_response_upper*F(11,10)),
        response_limit_ns=3000,
        minimum_application_arrival_spacing_ns=min_spacing,
        mean_read_rate_per_s=len(arrivals)*1e9/config["horizon_ns"],
        pass_peak=peak_ns <= 800000,
        pass_service_reserve=e*F(11,10) <= 164 and read*F(11,10) <= 240,
        pass_response=app_response_upper*F(11,10) <= 3000,
        pass_app_envelope=(min_spacing is None or min_spacing >= 100000)
            and len(arrivals)*1e9/config["horizon_ns"] <= 1000,
        scope="r4 conditional scalar bounds; nominal grid; no physical WCET qualification")
