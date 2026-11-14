"""A second substitution from the calendar and the independent #481 verifier."""
import json
from decimal import Decimal as D, ROUND_CEILING, localcontext
from fractions import Fraction as F
from math import ceil, floor
from pathlib import Path
from runpy import run_path

HERE = Path(__file__).resolve().parent
EXP = HERE.parent
base = run_path(str(EXP / "t186-native-cost-map/check.py"))
ledger = json.loads((HERE / "result.json").read_bytes())
prior = json.loads((EXP / "t504-large-bank/result.json").read_bytes())
cal = base["calendar"]
dec, rounded = base["decimal"], base["rounded"]
W = ledger["words_closed"]
A = 2*W
ns = F(1, 10**9)
frame, offsets = cal["frame_ns"], cal["visit_offsets_ns"]
starts = [j//len(offsets)*frame+offsets[j % len(offsets)] for j in range(A)]
L = ns*(A//len(offsets)*frame)
xi, xm, edge, jitter = (base[k] for k in ("xp","xm","edge","J"))


def check_phase_threshold():
    assert {starts[a ^ (1 << 16)]-starts[a] for a in range(W)} == {L/(2*ns)}
    assert {starts[a+1]-starts[a] for a in range(0,A,2)} == {ledger["tight_separation_ns"]}
    periods = [L]
    while 2*xi*periods[-1]+2*jitter <= 6:
        periods.append(2*periods[-1])
    counts = [ceil(((p/F(".00168")+2*jitter)/xm+L)/periods[-1]) for p in periods[1:]]
    assert counts == [10,19,38,75,149,298,596]
    cut = L-cal["report_cut_ns_before_next_pass"]*ns
    H = [xm*(n*periods[-1]-cut)-2*jitter for n in [counts[0],*counts]]
    a = [dec(xi*p/2) for p in periods]
    s = dec(base["c"]*(5*W-4)/6)
    b, peak, t, exposure, second, delta = (dec(base[k]) for k in ("b","B","T","S1","S2","delta"))
    rise = dec(prior["GEO"]["rise_s-1"])
    pair = dec(W*base["c"]**2/2)

    def weight(z):
        return ((1+z/64)**-64*10**18).to_integral_value(rounding=ROUND_CEILING)/10**18

    def remainder(x):
        return sum(amp*weight(s*dec(h)*x) for amp,h in zip(a,H,strict=True))

    def mask(p):
        return dec(edge)*(second/dec(xm*p)+peak**2+4*peak*rise)

    left, strips = b, []
    while left < peak:
        right = min(peak,2*left)
        step = (right-left)/32
        for i in range(32):
            x = left+i*step
            strips.append((x+b+step, remainder(x)))
        left = right
    mass = peak*dec(xi*periods[-1])
    kernel = mass/(1-weight(s*mass)) + peak*dec(xi*starts[-1]*ns)
    rises = (1+D("2.71828")**-2)*sum(a)*rise*kernel
    other = sum(amp*mask(p) for amp,p in zip(a,periods,strict=True))
    def q(gap, half_mask=False):
        h = dec(xi*(L-gap)+edge)
        scalar = t*b*b*(h+remainder(b))+(exposure-t*b)*max(k*(h+tail) for k,tail in strips)
        masks = h*(mask(L/2) if half_mask else 2*mask(L)) + other
        return delta+pair*(scalar+masks+rises)

    n = ledger["common_separation_ns_ceiling"]
    high, low = q(n*ns), q((n-1)*ns)
    assert high <= D(".001") < low and n*ns < L/2
    rounded(ledger["stop_upper_at_issued_ns"],F(high))
    rounded(ledger["certificate_at_previous_ns_lower"],F(low),True)
    rounded(ledger["stop_upper_at_3ms"],F(q(F(3,1000))))
    rounded(ledger["stop_upper_at_L_over_2_exact_masks"],F(q(L/2,True)))
    rounded(ledger["tight_two_phase_upper"],F(q(ledger["tight_separation_ns"]*ns)))
    # Independent 80-digit recovery of the new one-phase rise allowance.
    issued = ledger["one_phase_growth"]
    old_q, _, _ = base["ladder_check"]("geo",W,str(F(5*W-4,6*W)))
    step, width = dec(xi*periods[-1]), dec(xm*periods[-1])
    phi = dec(xi*starts[-1]*ns)
    speed = dec(prior["GEO"]["growth_s-2"])
    bottom = peak/2-speed*(2*step+phi+dec(edge))
    discount = min(1-1/(1+s*bottom*width), 1-s*peak*width)
    low_mass = peak/2*(peak/(4*speed)-step)
    def fee(top):
        mass = top*step
        return mass/(1-weight(s*mass))
    expensive, cheap = fee(peak),fee(3*peak/4)
    high = (1-discount)*(expensive+peak*phi)
    low = cheap+(expensive-cheap)*weight(s*low_mass)+peak*phi
    old_rise = pair*rise*sum(a[1:])*(expensive+peak*phi)*(1+D("2.71828")**-2)
    new_rise = pair*rise*sum(a[1:])*max(high,low)
    closed = old_q-old_rise+new_rise
    rounded(issued["rise_term_upper"],F(new_rise))
    rounded(issued["closed_one_phase_stop_upper"],F(closed))
    rounded(issued["epsilon_room_lower"],F(D(".001")-closed),True)
    rounded(issued["high_rise_fee_upper"],F(high))
    rounded(issued["low_rise_fee_upper"],F(low))
    quoted_old_price = dec(prior["rows"][0]["ladder"]["s_upper"])
    bus = quoted_old_price-(old_q-closed)*dec((base["cr"]+base["cw"])*base["hard"])
    rounded(issued["closed_bus_s_upper_I0_X0"], F(bus))
    rounded(issued["closed_bus_percent_upper"], F(100*bus/t))
    assert closed < D(".001")
    # Taking y later than x, including births during a weak write and clipping by T.
    # A pair elsewhere in a parent node must straddle the entire middle aperture.
    for d in (240*ns,n*ns,L/2,L-n*ns):
        k, end = xi*d, xi*L+edge
        points = sorted({F(0),edge/2,k-edge/2,k,k+edge/2,k+edge,(end+k+edge)/2,end})
        for u in points:
            for v in (v for v in points if v >= u):
                assert (v <= k+edge or u >= k) != (u < k and v > k+edge)
    return len(strips)


def check_plateau(words, band):
    t_plat, B, c = (base[k] for k in ("span","B","c"))
    n = ceil(4*t_plat)
    t = t_plat/n
    g = xi*L
    visits = floor((t+band)/g)+1
    sq = (g-band)*(t-visits*band)-(g-band)**2/2
    mu = c*B*t
    # The ring has W adjacent and W(W-1)/2 total unordered word pairs.
    loss = (words*(words-1)//2)*mu**4/4 + words*((mu/6)*mu**2+(mu/6)**2/2)
    z = n*(words*F(37,76)*(1-mu)*(c*B)**2*sq-loss)
    return 1-1/(1+z)-base["delta"]


def check_archive():
    receipt = ledger["archive_fixed"]
    k = receipt["K_word_s"]
    p, mean = F(k,W), F(6,5)
    B, U, second = F(525,1000), F(24), F(15624)
    c, T, delta = (base[key] for key in ("c","T","delta"))
    blocked = xi*L+edge
    x = 2*k*c*B/mean
    mark = F(37,38)
    same = F(16,25)*mark + F(8,25)*2*mark + F(1,25)*(2*mark+1-F(1,38**2))
    exposure = (1-blocked/p)**2*second-blocked*(B**2+4*B*U)-(1+4*p)*B**2-p*B*U
    z = (1-x*(1-x*(F(1,2)-x/6)))*c*c*k*same*exposure/(2*mean**2)
    q = 1-1/(1+z)-delta
    assert q > F(1,1000)
    rounded(receipt["exclusion_Q_lower"],q,True)
    cost = (1-delta)*A*(xm*base["read"]-2*jitter)*(T/(p+2*jitter)-2)
    rounded(receipt["compulsory_reads_s_lower"],cost,True)
    rounded(receipt["percent_lower"],100*cost/T,True)


def check_closed_fixed():
    r = ledger["closed_fixed_class"]
    k = r["K_word_s"]
    q_witness = base["common_witness"](W,L,k)
    rounded(r["exclusion_Q_lower"],q_witness,True)
    assert q_witness > F(1,1000)
    c,T,delta = (base[key] for key in ("c","T","delta"))
    cost = (1-delta)*A*(xm*base["read"]-2*jitter)*(T/(F(k,W)+2*jitter)-2)
    rounded(r["per_map_constant_reads_s_lower"],cost,True)
    for period, key in ((F(r["one_phase_candidate_s"]),"candidate_Q_upper"),(L,"continuous_Q_upper")):
        width = xi*period+2*jitter+edge
        exposure = width*base["S2"]+2*base["B"]*edge*base["S1"]
        q = delta+W*c**2*F(37,76)*exposure
        assert period >= L and q <= F(1,1000)
        rounded(r[key],q)
    assert F(r["one_phase_candidate_s"]) == r["candidate_frames"]*frame*ns
    quoted = F(ledger["one_phase_growth"]["closed_bus_s_upper_I0_X0"])
    floor_cost = F(r["per_map_constant_reads_s_lower"])
    rounded(r["per_map_saving_s_lower"],floor_cost-quoted,True)
    rounded(r["per_map_ratio_lower"],floor_cost/quoted,True)


if __name__ == "__main__":
    with localcontext() as ctx:
        ctx.prec = 80
        bins = check_phase_threshold()
    rounded(ledger["tight_physical_lower"], check_plateau(W,edge+xi*240*ns), True)
    rounded(ledger["all_external_physical_lower"], check_plateau(A,edge), True)
    assert ledger["all_external_physical_lower"] == prior["rows"][1]["fixed"]["common_Q_lower"]
    check_archive()
    check_closed_fixed()
    print(f"{W} address pairs, {bins} intensity strips, both plateau tests and the SEPEM price agree.")
