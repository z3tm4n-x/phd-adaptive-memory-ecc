"""Independent checks of the new phase, cost and exclusion bounds from source inputs."""
import argparse
import json
from decimal import Decimal, ROUND_CEILING, localcontext
from fractions import Fraction as F
from functools import cache
from math import ceil, floor
from pathlib import Path


HERE = Path(__file__).resolve().parent
EXP = HERE.parent


def data(path):
    return json.loads(path.read_bytes(),parse_float=F)


def rounded(stored, exact, lower=False):
    digits = len(stored.partition(".")[2])
    assert F(stored) == F((floor if lower else ceil)(exact*10**digits),10**digits)


calendar = data(EXP/"t196-native-err-20261110/calendar.json")
env = data(EXP/"c1-common-geo-20261109/coverage.json")
geo = data(EXP/"c1-common-geo-20261109/six.json")
report = data(HERE/"result.json")
old = data(EXP/"t196-cluster-main-20261112/result.json")
b, B = F(env["b_s_inv"]), F(env["B_s_inv"])
T, S1, S2, delta = (F(geo[k]) for k in ("T","S1_max","S2_max","delta_exec"))
ns = F(1,10**9)
xm, xp = F(calendar["xi_min"]), F(calendar["xi_max"])
J = F(calendar["edge_jitter_ns"])*ns
F0 = calendar["frame_ns"]*ns
c = F(38,geo["D"])
operation = calendar["operation_ns"]
repair_end = operation["write_release"]*ns
read = operation["read_release_or_drive_write"]*ns
edge = xp*repair_end+3*J
cr, cw = xp*read+2*J, xp*(repair_end-read)+2*J
hard = 4*(ceil((T+2*J+edge)/(xm*F0))+2)
positions = calendar["visit_offsets_ns"]
span = F(geo["lower_witness_plateau_used_s"])
assert span+1 == F(geo["plateau_s"]) and T*b+(span+1)*(B-b) == S1


def word_witness(words, P, target, subset):
    # Direct sum of unordered-pair joint moments, separating edges and nonedges.
    blocks = ceil(span/F(target))
    t = span/blocks
    v = c*B
    mu = v*t
    n = words if subset == "all" else words//2
    neighbours = n if subset == "all" else 0
    pairs = n*(n-1)//2
    common = mu/6
    each = mu**4/4
    loss = (pairs-neighbours)*each + neighbours*(each+common*mu**2+common**2/2)
    visits_total = 2*n*(span/P+2)+blocks-1
    visits = visits_total/(n*blocks)
    free = max(0,t-visits*edge)
    z = max(0,blocks*(n*F(37,76)*(1-mu)*v**2*free**2/(1+visits)-loss))
    return max(0,z/(1+z)-delta)


def common_witness(words, L, K):
    second = floor((span+1)*B**2+(T-span-1)*b**2)
    blocked = xp*L+edge
    P = F(K,words)
    m = F(6,5)
    p = F(37,38)
    # Start coincidences for independent one/one, one/two, two/one, two/two.
    a = F(16,25)*p + 2*F(4,25)*2*p + F(1,25)*(2*p+1-F(1,38**2))
    free = (1-blocked/P)**2*second
    free -= blocked*(B**2+4*B*(B-b))+(1+4*P)*B**2+P*B*(B-b)
    z = (1-2*K*c*B/m)*c**2*K*a*free/(2*m*m)
    assert 0 < blocked < P and z > 0
    return max(0,z/(1+z)-delta)


def decimal(x):
    x = F(x)
    return Decimal(x.numerator)/x.denominator


@cache
def ladder_check(scope, words, eta_str):
    """High-precision recomputation of the certified rational majorant and all costs."""
    with localcontext() as ctx:
        ctx.prec = 72
        source = old["profiles"][scope]
        peak,rise,s1,s2 = (decimal(source[k]) for k in ("B","U","S1","S2"))
        background, mission, pair = decimal(b),decimal(T),decimal(words*c**2/2)
        rate = decimal(words*c*F(eta_str))
        # Build the levels from slot counts again, without using calculate.py.
        L = decimal(2*words*F0/4)
        gap = [L]
        while decimal(xp)*gap[-1]*2+decimal(2*J)<=6:
            gap.append(gap[-1]*2)
        top = gap[-1]
        amplitude = [decimal(xp)*p/2 for p in gap[1:]]
        counts = [ceil(((p/Decimal(".00168")+decimal(2*J))/decimal(xm)+L)/top) for p in gap[1:]]
        h = [decimal(xm)*(n*top-L+decimal(300*ns))-decimal(2*J) for n in counts]
        fast = decimal(xp)*L+decimal(edge)

        def envelope(z):
            return (((1+z/64)**-64)*10**18).to_integral_value(rounding=ROUND_CEILING)/10**18

        def kernel(x):
            return fast+sum(a*envelope(rate*x*duration) for a,duration in zip(amplitude,h))

        left, high = background,Decimal(0)
        while left<peak:
            right = min(peak,2*left)
            dx = (right-left)/32
            for i in range(32):
                x = left+i*dx
                high = max(high,(background+x+dx)*kernel(x))
            left = right
        scalar = mission*background**2*kernel(background)+(s1-background*mission)*high

        def phase(p):
            return decimal(edge)*(s2/(decimal(xm)*p)+peak**2+4*peak*rise)

        overlap = fast*phase(L)+sum(a*phase(p) for a,p in zip(amplitude,gap[1:]))
        mass = peak*decimal(xp)*top
        ascent = (1+1/Decimal("2.71828")**2)*rise*sum(amplitude)*(
            mass/(1-envelope(rate*mass))+peak*decimal(xp)*(L-decimal(640*ns)))
        q = decimal(delta)+pair*(scalar+overlap+ascent)
        # Count required levels by adding their inverse-period rate differences.
        widths = [decimal(xm)*p-decimal(2*J) for p in gap]
        band = min(s1,(fast+decimal(2*J))*(s1/(decimal(xm)*top)+2*(peak+rise)))
        parent_mass = decimal(words*c)*(s1+band)
        hits = decimal((words+1)*c)*s1
        increments = [1/a-1/bb for a,bb in zip(widths,widths[1:])]
        start = 2+mission/widths[-1]+(decimal(xp)*L+decimal(J))*sum(increments)
        reset = (decimal(xp)*top+decimal(2*J))*sum(d*(1+n) for d,n in zip(increments,counts))
        lower = (1-q)*2*words*decimal(xm*read-2*J)*(mission/(decimal(xp)*top+decimal(2*J))-2)
        return q,lower,(start,reset,hits,parent_mass)


def validate_ladder(row):
    with localcontext() as ctx:
        ctx.prec = 72
        scope,words = row["scope"],row["words"]
        q,low,fees = ladder_check(scope,words,row["eta"])
        start,reset,hits,weighted_exposure = fees
        cells = min(hits,weighted_exposure/decimal(row["m"]))
        cost = decimal(2*words*cr)*(start+reset*(1+cells))+decimal(cw)*hits+decimal(hard*(cr+cw))*q
        stair = row["ladder"]
        rounded(stair["q"],F(q))
        rounded(stair["s_lower"],F(low),True)
        rounded(stair["s_upper"],F(cost))
        threshold = row["threshold"]
        qlo = ladder_check(scope,words,threshold["fail"])[0]
        assert qlo > decimal(row["epsilon"])
        rounded(threshold["q_at_fail_lower"],F(qlo),True)
        if threshold["pass"] is not None:
            qhi = ladder_check(scope,words,threshold["pass"])[0]
            assert qhi <= decimal(row["epsilon"])
            rounded(threshold["q_at_pass_upper"],F(qhi))
            assert F(threshold["pass"])-F(threshold["fail"])==F(1,16384)
        else:
            assert threshold["fail"]=="1"


def check_grid(row, scan_ns, w):
    L = scan_ns*ns
    eps = F(row["epsilon"])
    prefactor = w*F(38*37,2*geo["D"]**2)
    def q(paired_gap):
        return delta+prefactor*((xp*paired_gap+2*J+edge)*S2+2*B*edge*S1)

    rounded(row["u_upper"],q(L)/eps)
    rounded(row["continuous_Q_upper"],q(L))
    rounded(row["paired_continuous_Q_upper"],q(L/2))
    assert F(row["eta"]) == (1-F(4,5*w))/F(6,5)
    fixed = row["fixed"]
    fast = fixed["fast_witness"]
    f_q = word_witness(w,xp*L,fast["max_block_s"],fast["subset"])
    rounded(fast["Q_lower"],f_q,True)
    assert fixed["class_empty"] == (f_q > eps)
    if not fixed["class_empty"]:
        wtn = fixed["witness"]
        p0 = F(fixed["cutoff_physical_s"])
        if wtn["method"] == "word_blocks":
            lower = word_witness(w,p0,wtn["max_block_s"],wtn["subset"])
        else:
            assert p0*w == wtn["K_word_s"]
            lower = common_witness(w,L,wtn["K_word_s"])
        assert lower > eps
        rounded(fixed["exclusion_Q_lower"],lower,True)
        rounded(fixed["s_lower"],(1-delta)*2*w*(xm*read-2*J)*(T/(p0+2*J)-2),True)
    quote = fixed["candidate"] or fixed["continuous_tariff"]
    p = F(quote["period_s"])
    assert (p/F0).denominator == 1 and p >= L
    rounded(quote["physical_Q_upper"],q(p-L/2))
    if fixed["candidate"]:
        assert q(p-L/2) <= eps < q(p+F0-L/2)
    else:
        assert q(L/2) > eps and fixed["class_empty"]
    nr = min(hard,2*w*(T/(xm*p-2*J)+2))
    qstop = delta + w*c**2/2*(xp*p+edge)*(S2+edge*(S2/(xm*p)+B**2+4*B*F("28.855")))
    rounded(quote["stop_upper"],qstop)
    exceptions = delta*(hard-nr)
    repairs = min(nr+exceptions,(w+1)*c*S1+min(qstop*hard,qstop*nr+exceptions))
    rounded(quote["s_upper"],cr*(nr+exceptions)+cw*repairs)
    if row["ladder_pass"]:
        assert F(row["ladder"]["q"]) <= eps
    else:
        assert F(row["ladder"]["q"])-F(1,10**12) > eps
    if row["choice"] == "fixed":
        assert F(quote["s_upper"]) < F(row["ladder"]["s_lower"])
    if row["choice"] == "ERR":
        assert F(fixed["s_lower"]) > F(row["ladder"]["s_upper"])


def printed(value, digits, lower=False, trim=True):
    scaled = (floor if lower else ceil)(F(value)*10**digits)
    whole, tail = divmod(scaled,10**digits)
    if not digits:
        return f"{whole:,}".replace(","," ")
    result = f"{whole},{tail:0{digits}d}"
    return result.rstrip("0").rstrip(",") if trim else result


def price_cell(lower, upper, percent_lower, percent_upper):
    seconds = f"{printed(lower,0,True)}–{printed(upper,0)}"
    percent = f"{printed(percent_lower,3,True,False)}–{printed(percent_upper,3,False,False)}"
    return f"{seconds} ({percent}%)"


def markdown_table():
    lines = ["| Обстановка, МиБ, закон | ε | u⁺ | m | η гарант. / достат. | P кандидата, с | F⋆, с (% срока) | Q⁺ лестницы | Лестница, с (% срока) | Выбор |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|"]
    names = {"compact_1p2":"смесь","two_uniform":"пара","compact_4":"4 сосед.",
             "compact_5":"5 сосед.","compact_8":"8 сосед."}
    eps_names = {F(1,10):"10⁻¹",F(1,100):"10⁻²",F(1,1000):"10⁻³",F(1,10000):"10⁻⁴"}
    choices = {"ERR":"**лестница**","fixed":"**постоянный**","excluded":"**оба исключены**"}
    for row in report["rows"]:
        scope = "ГСО" if row["scope"]=="geo" else "Архив"
        volume = printed(F(4*row["words"],2**20),4)
        fixed, stair = row["fixed"],row["ladder"]
        cand = fixed["candidate"] or fixed["continuous_tariff"]
        lo = fixed if fixed["candidate"] else cand
        fixed_cost = price_cell(lo["s_lower"],cand["s_upper"],lo["pct_lower"],cand["pct_upper"])
        period = printed(cand["period_s"],7)
        if not fixed["candidate"]:
            fixed_cost = "класс пуст<br>L† "+fixed_cost
            period += "†"
        need = row["threshold"]["pass"]
        visibility = printed(row["eta"],6,True)+" / "+(printed(need,6) if need else "нет")
        choice = choices.get(row["choice"],"цены пересекаются" if row["ladder_pass"] else "подтверждён постоянный")
        cols = [f"{scope} {volume}, {names[row['law']]}",eps_names[F(row["epsilon"])],
                printed(row["u_upper"],6),printed(row["m"],1),visibility,period,fixed_cost,
                printed(stair["q"],9),price_cell(stair["s_lower"],stair["s_upper"],
                                               stair["pct_lower"],stair["pct_upper"]),choice]
        lines.append("| "+" | ".join(cols)+" |")
    return "\n".join(lines)


def main():
    rows = report["rows"]
    assert len(rows) == len({(r["scope"],r["law"],r["words"],r["epsilon"]) for r in rows}) == 21
    for row in rows:
        validate_ladder(row)
    slots_checked = 0
    for w in (16384,32768,65536):
        m = report["maps"][str(w)]
        starts = [j//4*calendar["frame_ns"]+positions[j%4] for j in range(2*w)]
        scan_ns = (2*w//4)*calendar["frame_ns"]
        assert all(y-x == scan_ns//2 for x,y in zip(starts[:w],starts[w:]))
        assert starts[-1] == scan_ns-640 and F(m["L_s"]) == scan_ns*ns
        slots_checked += len(starts)
        anchor = F(m["anchor_s"])
        assert xp*anchor+2*J <= 6 < xp*2*anchor+2*J
        thresholds = [ceil(((F(m["L_s"])*2**i/F("0.00168")+2*J)/xm+F(m["L_s"]))/anchor)
                      for i in range(1,m["top_stride"].bit_length())]
        assert m["zero_cells"] == thresholds
        for row in (r for r in rows[:12] if r["words"]==w):
            check_grid(row,scan_ns,w)
    for row in (r for r in rows if r["words"]==32768 and r["epsilon"]=="1/1000"):
        ref = old["laws"][row["law"]][row["scope"]]
        assert row["ladder"]["q"]==ref["stop_Q_upper"]
        assert row["ladder"]["s_lower"]==ref["ladder_s_lower"]
        assert row["ladder"]["s_upper"]==ref["ladder_s_upper_I0_X0"]
        fixed = row.get("prior_fixed_473",row["fixed"])
        assert fixed["s_lower"]==ref["fixed_s_lower"]
        assert fixed["candidate"]["s_upper"]==ref["fixed_candidate_s_upper"]
        assert row["threshold"]["pass"]==old["thresholds"][row["scope"]]["eta_sufficient"]
    table = "\n".join(s for s in (HERE/"README.md").read_text(encoding="utf-8").splitlines() if s.startswith("|"))
    assert table == markdown_table()
    print(f"{slots_checked} x16 phases, 12 fixed bounds, all ladder costs/thresholds, 10 accepted comparisons and the printed table verified.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table",action="store_true",help="emit the complete Markdown table")
    if parser.parse_args().table:
        print(markdown_table())
    else:
        main()
