"""PR261 reviewer arithmetic; no imports of author calculation modules.

Reuse accepted PR260 constants. Independently count eight frame residues over
the whole horizon and evaluate the new eta/cost/service inequalities exactly.
This is arithmetic evidence; scientific scope is in REVIEW_20261025.md.
"""
import json
from fractions import Fraction as F
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def read(path):
    def numbers(x):
        if isinstance(x, dict):
            return {k: numbers(v) for k, v in x.items()}
        if isinstance(x, list):
            return [numbers(v) for v in x]
        if isinstance(x, str):
            try:
                return F(x)
            except ValueError:
                pass
        return x
    return numbers(json.loads(path.read_text(encoding="utf-8")))


def ceil(x):
    return -(-x.numerator // x.denominator)


r = read(HERE / "outputs/result.json")
a = read(ROOT / "experiments/comparison-foundations-20261018/predictable-windows-20261025/result.json")
m = a["model"]
W, T, ns = 131072, 315576000, 10**9
xm, xp, J = F(99999, 100000), F(100001, 100000), F(1, 2*ns)
period = lambda k: k*W*196*xm/ns-J
rb, cb = 48*xp/ns+J, 56*xp/ns+J
delta = F(7, 10**6)
hard = W*(T/period(1)+2)
U = a["adaptive"]["Q_upper"]
repair = 2*a["adaptive"]["parent_count_upper"]+U*hard
common = a["common_cost"]["ECC_and_initial_bus_upper"]
lower = a["fixed"]["pure_bus_class_lower"]+a["common_cost"]["ECC_and_initial_bus_lower"]
C = m["price_padding_s"]
slope = rb*2*W*58440/period(20)/T
assert slope == r["affine_bus"]["slope_per_second"]
assert m["windows"] == 58440 and T == 5400*58440


def by_frame_residues(k, left_ns, right_ns):
    """Count frame indices separately for each of the eight physical offsets."""
    block, repeat = W//8, k*(W//8)
    total = 0
    for offset in range(0, 8*164, 164):
        lo = max(0, -((offset-left_ns)//1568))
        hi = max(0, -((offset-right_ns)//1568))
        nlo, remlo = divmod(lo, repeat)
        nhi, remhi = divmod(hi, repeat)
        total += (nhi-nlo)*block+min(remhi, block)-min(remlo, block)
    return total


for row in r["rows"]:
    eta = row["eta_s"]
    length = 58440*(600+2*eta+2*C)+m["loss_time_upper_s"]+2*C*(m["loss_episodes_upper"]+m["false_count_expected_upper"])
    bands = 58440+m["loss_episodes_upper"]+m["false_count_expected_upper"]
    reads = W*(T/period(1780)+2)+W*(length/period(20)+2*bands)+W+2*W*(C/period(20)+2)+delta*hard
    assert repair < reads < hard
    bus = (reads*rb+repair*cb)/T
    assert reads == row["reads_upper"] and bus == row["pure_bus_upper"]
    for g in (1, 2, 4, 5):
        assert lower/g-bus-common == row["u_limits"][str(g)]
    # The model's integer-second polls, zero time error, latest allowed readiness.
    first = ceil(1800-eta-m["poll_step_upper_s"]-m["command_delay_s"]-(320*xp/ns+J)-m["complete_fast_cover_s"]-m["time_error_s"])
    last = (2400+eta+m["complete_fast_cover_s"]+m["time_error_s"])//1
    left = first*ns+10000000+320
    right = (last+1)*ns+10000000+320
    total = by_frame_residues(1780, 0, T*ns)
    intervals = [(left+i*5400*ns, right+i*5400*ns) for i in range(58440)]
    intervals += [(0, r["geometry"]["recovery_hold_nominal_s"]*ns+20000000+320), ((T-C)*ns, T*ns)]
    for l, h in intervals:
        total += by_frame_residues(20, l, h)-by_frame_residues(1780, l, h)
    assert total == row["nominal_schedule_count"]["total_reads_exact"], eta
    print(f"eta={eta}: exact starts={total}; bus upper={float(bus)*100:.12f}%")

P = T/m["poll_step_lower_s"]+2
R = 1+m["loss_episodes_upper"]+m["false_count_expected_upper"]+delta*P
counts = [P, P+R+1, P+2*R+2, P]
rates = [x/T for x in counts]
assert counts == list(r["management"]["expected_count_upper"][k] for k in ("check", "command", "timer", "extra_bundle"))
v, atom = 64*xm/ns-J, F(32, ns)
q, frame = v-atom, 1568*xp/ns+J
chunks = (F(9, 1000)//frame)-20
universal = rates[0]*chunks*q/5
assert universal == r["management"]["composition_independent_u_upper"]
assert F(3601, 10**8) < universal
for example, coeff in zip(r["management"]["examples"], ([8, 4, 2, 2], [10, 20, 10, 20])):
    costs = [F(v, 10**6) for v in coeff]
    u = sum(c*b for c, b in zip(rates, costs))
    burst = sum(weight*b for weight, b in zip([1, 3, 5, 1], costs))
    latency = (ceil(burst/q)+20)*frame
    assert u == example["mean_bus_upper"] and latency == example["bus_response_upper_s"]
    assert latency+F(1, 1000) < F(1, 100)
    print(f"service {example['id']}: u={float(u)*1e6:.9f} us/s, bus delay={float(latency)*1e3:.9f} ms")
for box in r["boxes_with_margin"]:
    eta, u = box["eta_range_s"][1], box["management_range"][1]
    row = next(x for x in r["rows"] if x["eta_s"] == eta)
    gain = lower/(row["pure_bus_upper"]+common+u)
    assert gain > box["gain_at_least"] and u < universal
    assert row["u_limits"][str(box["gain_at_least"]) ]-u == box["management_slack_at_worst_corner"]
    print(f"box {box['gain_at_least']}x: worst-corner gain >= {float(gain):.9f}")
print("PR261 independent rational arithmetic and full-horizon frame-residue counts agree.")
