"""Independent arithmetic audit of the existing PR296 cell, no new map cells."""
from decimal import Decimal as D, localcontext
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
c = json.loads((HERE / "inputs.json").read_text(encoding="utf-8"))
raw = (HERE / "first-point-result.json").read_bytes().replace(b"\r\n", b"\n")
assert hashlib.sha256(raw).hexdigest() == "0f727a6bd458c15baf7e46e48ba78d88e161afa8b77e5941a1ea78db12aa4952"
r = json.loads(raw)
e, s, info = (c[k] for k in ("environment", "service", "information"))
W, T = c["first_probe"]["words"], F(c["bank"]["mission_s"])
b, B, Fs = (F(e[k]) for k in ("b", "B", "Fs"))
alpha = F(c["first_probe"]["alpha"])
n, positions = c["bank"]["code"][0], e["reference_positions"]
count, width = e["template"]["count"], F(e["template"]["width_s"])
a = (1-alpha)*2*Fs/(count*width)
cap, mass = B-b-a, alpha*Fs

# Integrate the two linear ramps and the constant part directly.
inside = count*width*(b*b+b*(b+a)+(b+a)**2)/3
outside = (T-count*width)*b*b
moment = inside+outside
assert moment == F(r["environment"]["Ip"])
K = W*F(n-1,2*n)*F(n,positions)**2
xm, xp, J = F(s["xi_minus"]), F(s["xi_plus"]), F(s["J_ns"])/10**9
dE = 124*xp/10**9+3*J
delta = F(info["lifetime_delta_exec"])
def period(k, upper):
    return 196*k*W*(xp if upper else xm)/10**9+(J if upper else -J)

row = next(x for x in r["candidates"]["rows"] if x["pair"] == [3,3])
Q = delta+K*((period(3,True)+dE)*(moment+(2*(b+a)+cap)*mass)+2*B*dE*(b*T+Fs))
assert Q == F(row["risks"]["F"]["upper"]) < F(c["first_probe"]["epsilon"])
Nmax = W*(T/period(1,False)+2)
reads = W*(T/period(3,False)+2)+delta*Nmax
repairs = min(reads,2*F(n*W,positions)*(b*T+Fs)+Q*Nmax)
assert reads == F(row["prices"]["M"]["reads_upper"])
assert repairs == F(row["prices"]["M"]["repairs_upper"])
for name,ticks in (("bus",48),("serial",68)):
    upper=(ticks*xp/10**9+J)*reads+(56*xp/10**9+J)*repairs
    assert upper == F(row["prices"]["M"]["coordinates"][name]["protection_upper_s"])

# Re-evaluate the lower expression at 80 digits without the author's
# interval implementation; check containment in its published 48-digit box.
def dec(value):
    value=F(value)
    return D(value.numerator)/D(value.denominator)

with localcontext() as ctx:
    ctx.prec=80
    for entry in (r["fixed_class"]["last_not_excluded"],r["fixed_class"]["excluded_from"]):
        P0=F(entry["P0_s"])
        values=[]
        specifications=(
            (mass/cap-period(1,True),1,F(n,positions)*(b+cap),F(n,positions)*B),
            (F(300),count,F(n,positions)*(b+a/2),F(n,positions)*(b+a)),
        )
        for saved,(length,mult,lo,hi) in zip(entry["witnesses"],specifications):
            apertures=length/P0+2
            free=max(F(0),length-apertures*dE)
            z=dec(mult*W*F(n-1,2*n)*lo**2*free**2/(apertures+1))*(-dec(hi*length)).exp()
            q=max(D(0),1-(-z).exp()-dec(delta))
            values.append(q)
            assert dec(saved["Q_lower"]) <= q <= dec(saved["Q_lower_expression_enclosure_upper"])
        if entry is r["fixed_class"]["excluded_from"]:
            assert max(values) > dec(c["first_probe"]["epsilon"])
            lower_reads=(1-delta)*W*max(F(0),T/(P0+J)-2)
            for name,ticks in (("bus",48),("serial",68)):
                lower=lower_reads*(ticks*xm/10**9-J)
                assert lower == F(entry["cost"][name]["lower_s"])
        else:
            assert max(values) < dec(c["first_probe"]["epsilon"])

assert all(pair == [3,3] for pair in r["candidates"]["selected"].values())
residual = K*(period(3,True)+dE)*(2*(b+a)+cap)*mass/(Q-delta)
assert residual == F(r["diagnostic"]["residual_fraction_of_fixed_physical_Q"])
print("Independent moment, fixed Q and full known price: OK")
print("Independent 80-digit lower expressions inside directed bounds: OK")
print("Constant lower price and residual share: OK")
print("No other map cell, policy search or old campaign executed.")
