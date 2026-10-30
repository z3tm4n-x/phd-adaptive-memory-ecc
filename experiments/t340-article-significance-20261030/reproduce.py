"""Issue 340: exact rational bounds, no simulation or campaign dependencies.

Run from any directory: python experiments/t340-article-significance-20261030/reproduce.py
The accepted 16 Q enclosures are read, never regenerated or modified.
"""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from functools import lru_cache
from hashlib import sha256
from math import comb, factorial
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CFG = json.loads((HERE / 'inputs.json').read_text(encoding='utf-8'))
T = F(CFG['T_s'])
EPS = F(CFG['epsilon'])
N = CFG['n']
BW = F(N-1, 2*N)
ENV = CFG['environment']
B0 = F(ENV['background_reference_s_inv'])
BMAX = F(ENV['peak_reference_s_inv'])
FS = F(ENV['equivalent_peak_s']) * (BMAX-B0)
RMAX = BMAX/B0
NU0 = N*B0/ENV['reference_bits']
C = F(CFG['service']['reserved_block_s'])
RHO = F(CFG['service']['rho'])
TOL = F(CFG['arithmetic']['root_relative_tolerance'])
TERMS = CFG['arithmetic']['rational_exp_terms']
PREREG = 'fcf654e59d35a9ba98acbeb4f94c51f3a277bbf1'


def floor(x):
    return x.numerator // x.denominator


def ceil(x):
    return -floor(-x)


def outward(x, places=24, up=False):
    z = x * 10**places
    k = ceil(z) if up else floor(z)
    sign = '-' if k < 0 else ''
    a, b = divmod(abs(k), 10**places)
    return f'{sign}{a}.{b:0{places}d}'


def interval(lo, hi=None, places=24):
    hi = lo if hi is None else hi
    assert lo <= hi
    return dict(lower=outward(lo, places), upper=outward(hi, places, True),
                width_upper=outward(hi-lo+F(2, 10**places), places, True))


def dec(x):
    return Decimal(x.numerator) / Decimal(x.denominator)


def short(x, digits=9):
    if isinstance(x, dict):
        x = (F(x['lower'])+F(x['upper']))/2
    with localcontext() as ctx:
        ctx.prec = 40
        return f'{dec(F(x)):.{digits}g}'


def exp_minus(x):
    """Rational outward enclosure; scale to [0,1], then square intervals."""
    assert x >= 0
    squarings = 0
    while x > 1:
        x /= 2
        squarings += 1
    term = total = F(1)
    for k in range(1, TERMS+1):
        term *= x/k
        total += term
    tail = term*x/(TERMS+1)/(1-x/(TERMS+2))
    lo, hi = 1/(total+tail), 1/total
    # Bound denominator growth while retaining certified endpoints.
    lo, hi = F(outward(lo, 70)), F(outward(hi, 70, True))
    for _ in range(squarings):
        lo, hi = F(outward(lo*lo, 70)), F(outward(hi*hi, 70, True))
    return lo, hi


def probability_from_hazard(lo, hi=None):
    hi = lo if hi is None else hi
    return 1-exp_minus(lo)[1], 1-exp_minus(hi)[0]


def log_budget():
    # -log(1-eps), positive series with explicit geometric tail.
    m = 20
    s = sum((EPS**k/F(k) for k in range(1, m+1)), F(0))
    return s, s+EPS**(m+1)/((m+1)*(1-EPS))


HL, HU = log_budget()


def profile(d, r):
    assert F(10800) <= d <= F(864000)
    assert 1 <= r <= RMAX and B0*(r-1)*d <= FS
    a = (T-d)/2
    return [(F(0), a, NU0), (a, a+d, NU0*r), (a+d, T, NU0)]


def integrate(parts, a, b):
    return sum((max(F(0), min(b, y)-max(a, x))*v for x, y, v in parts), F(0))


def scalar_schedule(W, w, P, end, delta=F(0)):
    s = F(w, W)*P+delta
    out = []
    while s <= end:
        out.append(s)
        s += P
    return out


def intervals_from(points, end):
    p = sorted(set([F(0), end] + [s for s in points if 0 <= s <= end]))
    return list(zip(p, p[1:]))


def saleh_product(masses, n):
    lo = hi = F(1)
    for mu in masses:
        # r_S = n exp(-(n-1)mu/n) - (n-1) exp(-mu).
        a, b = exp_minus(F(n-1, n)*mu), exp_minus(mu)
        rlo, rhi = max(F(0), n*a[0]-(n-1)*b[1]), min(F(1), n*a[1]-(n-1)*b[0])
        assert rlo <= rhi
        lo *= rlo
        hi *= rhi
        lo, hi = F(outward(lo, 65)), F(outward(hi, 65, True))
    return 1-hi, 1-lo


def saleh_decimal(masses, n, precision):
    with localcontext() as ctx:
        ctx.prec = precision
        v = Decimal(1)
        for m in masses:
            mu = dec(m)
            v *= (-mu).exp()+n*(1-(-mu/n).exp())*(-mu*(n-1)/n).exp()
        return F(1-v)


def small_validation():
    out = []
    for folder, rule in [('sequential-small-validation-20261014', 'B'),
                         ('sequential-err-small-validation-20261015', 'I38')]:
        directory = ROOT/'experiments'/folder
        cfg = json.loads((directory/'inputs.json').read_text(encoding='utf-8'))
        accepted = json.loads((directory/'outputs/results.json').read_text(encoding='utf-8'))
        end, P, n = F(cfg['T_s']), F(cfg['period_s']), cfg['n']
        for row in accepted['cases']:
            W, delta, name = row['W'], F(row['D_s']), row['profile']
            parts = [(F(p['start']), F(p['end']), F(p['lambda_array_s_inv'])/W)
                     for p in cfg['profiles'][name]]
            mean = integrate(parts, F(0), end)/end
            masses, averaged = [], []
            pair = cross = F(0)
            for w in range(W):
                reads = scalar_schedule(W, w, P, end)
                points = [s+delta for s in reads if s+delta <= end] if rule == 'B' else reads
                for a, b in intervals_from(points, end):
                    m = integrate(parts, a, b)
                    masses.append(m)
                    averaged.append(mean*(b-a))
                    pair += F(n-1, 2*n)*m*m
                if rule != 'B':
                    for e in reads:
                        cross += F(n-1, n)*integrate(parts, max(F(0), e-P), e)*integrate(parts, e, min(e+delta, end))
            computed_U = min(F(1), pair+cross)
            old = row['exact']
            ql, qh = F(old['Q_exact']['lower']), F(old['Q_exact']['upper'])
            ll, lh = F(old['L']['lower']), F(old['L']['upper'])
            uk = 'U' if rule == 'B' else 'U_E'
            ul, uh = F(old[uk]['lower']), F(old[uk]['upper'])
            assert ul <= computed_U <= uh and lh <= ql <= qh <= computed_U
            assert qh-ql <= F('1e-36')
            cl, ch = saleh_product(masses, n)
            ml, mh = saleh_product(averaged, n)
            for precision in CFG['arithmetic']['decimal_source_precisions']:
                assert cl <= saleh_decimal(masses, n, precision) <= ch
            assert ch-cl < F('1e-50')
            if rule == 'B' or delta == 0:
                assert qh <= cl  # Here the source event contains physical XOR failure.
                assert ch <= computed_U
            out.append(dict(id=f'{rule}_{row["id"]}', n=n, W=W, profile=name,
                            delta_s=str(delta), Q=old['Q_exact'], L=old['L'], U=old[uk],
                            U_reproduced_rational=str(computed_U),
                            C_profile=interval(cl, ch, 60), C_mean=interval(ml, mh, 60),
                            C_minus_Q=interval(cl-qh, ch-ql),
                            bounds_width=interval(computed_U-ll),
                            source_scope='valid_upper' if rule == 'B' or delta == 0 else 'fictitious_clean_reset_outside_source_guarantee',
                            C_below_Q=ch < ql, C_below_L=ch < ll))
    assert len(out) == 16
    return out


def powers(m, degree):
    """S[k] = sum j**k for j=0,...,m-1; integer Faulhaber recurrence."""
    s = [F(m)]
    for k in range(1, degree+1):
        s.append((F(m**(k+1))-sum(F(comb(k+1,j))*s[j] for j in range(k)))/(k+1))
    return s


def affine_power(a, b, m, k):
    s = powers(m, k)
    return sum((F(comb(k,j))*a**(k-j)*b**j*s[j] for j in range(k+1)), F(0))


def time_moments(W, P, end, degree=8):
    """Exact moments of all start/end/complete cells of uniformly phased words."""
    assert 0 < P <= end
    h = P/W
    cycles = floor(end/P)
    remainder = end-cycles*P
    count = min(W, floor(remainder/h)+1)
    full = W*(cycles-1)+count
    out = {}
    for k in range(2, degree+1):
        initial = affine_power(F(0), h, W, k)
        terminal = (affine_power(remainder, -h, count, k) +
                    affine_power(remainder+P-count*h, -h, W-count, k))
        out[k] = full*P**k+initial+terminal
    return out


def poly_square(poly):
    out = {}
    for i, a in poly.items():
        for j, b in poly.items():
            out[i+j] = out.get(i+j, F(0))+a*b
    return out


def source_hazard(W, P, nu):
    """Enclose the exact Saleh formula, not its quadratic approximation."""
    mu_max = nu*P
    assert mu_max <= 1
    moments = {k: v*nu**k for k,v in time_moments(W, P, T).items()}
    coef = {k: F((-1)**k, factorial(k))*((N-1)-N*F(N-1, N)**k)
            for k in (2,3,4)}
    low = {k:coef[k] for k in (2,3)}
    high = coef
    def total(poly):
        return sum((a*moments[k] for k,a in poly.items()), F(0))
    qmax = BW*mu_max**2
    lo = total(low)+total(poly_square(low))/2
    hi = total(high)+total(poly_square(high))/(2*(1-qmax))
    assert 0 <= lo <= hi
    return lo, hi


@lru_cache(maxsize=None)
def reference_period(W, d, r):
    nu = NU0*(1+(r-1)*d/T)
    cap = min(T/6, 1/nu)
    x = min(nu*cap/2, F(1))
    tail_hazard_lower = (W//2)*BW*x*x*exp_minus(x)[0]
    # Initial cells of at least floor(W/2) words exclude every P >= cap.
    assert tail_hazard_lower > HU
    assert source_hazard(W, cap, nu)[0] > HU
    lo, hi = F(0), cap
    for _ in range(160):
        mid = (lo+hi)/2
        a, b = source_hazard(W, mid, nu)
        if b <= HL:
            lo = mid
        elif a > HU:
            hi = mid
        else:
            # May occur only below the requested resolution: keep rigorous bracket.
            radius = mid*TOL/4
            l, h = max(lo, mid-radius), min(hi, mid+radius)
            if source_hazard(W, l, nu)[1] <= HL and source_hazard(W, h, nu)[0] > HU:
                lo, hi = l, h
            else:
                raise AssertionError('source enclosure needs refinement')
        if lo > 0 and hi-lo <= lo*TOL:
            break
    else:
        raise AssertionError('root search did not converge')
    assert source_hazard(W, lo, nu)[1] <= HL
    assert source_hazard(W, hi, nu)[0] > HU
    return lo, hi, tail_hazard_lower


def lower_free_cells(W, P, delta, parts):
    """T45: only full free cells wholly inside a constant-intensity segment."""
    assert 0 <= delta < P
    h = P/W
    hazard_lo = hazard_hi = F(0)
    counts = []
    for a, b, nu in parts:
        j0 = max(W, ceil((a+P-delta)/h))
        j1 = floor(b/h)
        count = max(0, j1-j0+1)
        mu = nu*(P-delta)
        el, eh = exp_minus(mu)
        hazard_lo += count*BW*mu**2*el
        hazard_hi += count*BW*mu**2*eh
        counts.append(count)
    ql, qh = probability_from_hazard(hazard_lo, hazard_hi)
    return interval(ql, qh), counts


def shift_class(lo, hi):
    # All shifts here are signed reductions; preserve interval ambiguity at thresholds.
    maglo, maghi = -hi, -lo
    if maghi <= 10:
        return '<=10%'
    if maglo > 10 and maghi <= 20:
        return '(10%,20%]'
    if maglo > 20:
        return '>20%'
    return 'threshold_interval'


def sensitivity_row(label, W, d, r, c=C, delta=C, rule='C', lower=False):
    parts = profile(d,r)
    a = BW*W*sum((nu*nu*(b-a) for a,b,nu in parts), F(0))
    mean = integrate(parts, F(0), T)/T
    amean = BW*W*T*mean*mean
    pmean, pprofile = EPS/amean, EPS/a
    pcorr = pprofile if rule == 'B' or delta == 0 else (pprofile-delta)/(1+F(1,W))
    floor_resource = W*c/RHO
    pl, ph, tail = reference_period(W,d,r)
    ref_feasible = pl >= floor_resource
    assert ref_feasible or ph < floor_resource  # Otherwise report unresolved resource intersection.
    corr_feasible = pcorr >= floor_resource
    signed = interval(100*(pcorr/ph-1), 100*(pcorr/pl-1)) if corr_feasible and ref_feasible else None
    u = a*pcorr if rule == 'B' or delta == 0 else a*((1+F(1,W))*pcorr+delta)
    if corr_feasible:
        assert u == EPS and delta <= c <= pcorr*RHO/W
    source_q = probability_from_hazard(*source_hazard(W,pl,mean))
    assert source_q[1] <= EPS
    out = dict(label=label,W=W,useful_MiB=str(F(W,262144)),rule=rule,
               peak_ratio=str(r),duration_s=str(d),excess_reference=str(B0*(r-1)*d),
               c_s=str(c),delta_s=str(delta),resource_floor_s=interval(floor_resource),
               P_ref_s=interval(pl,ph),reference_feasible=ref_feasible,
               P_mean_s=interval(pmean),P_profile_s=interval(pprofile),
               P_corr_s=interval(pcorr) if corr_feasible else None,
               unconstrained_corrected_root_s=interval(pcorr),
               corrected_feasible=corr_feasible,signed_shift_percent=signed,
               shift_class=shift_class(F(signed['lower']),F(signed['upper'])) if signed else 'empty_corrected_set',
               source_to_pair_percent=interval(100*(pmean/ph-1),100*(pmean/pl-1)),
               profile_only_percent=interval(100*(pprofile/pmean-1)),
               operation_only_percent=interval(100*(pcorr/pprofile-1)),
               profile_same_finite_service_percent=interval(100*((pprofile-delta)/(pmean-delta)-1)) if rule!='B' and delta>0 else interval(100*(pprofile/pmean-1)),
               reserved_bus_fraction_at_corrected=interval(W*c/pcorr) if corr_feasible else None,
               U_at_corrected_root=interval(u),C_at_reference_passing_endpoint=interval(*source_q),
               reference_passing_endpoint_rational=str(pl),corrected_root_rational=str(pcorr),
               reference_tail_hazard_lower=interval(tail),
               peak_word_mass_at_reference=interval(max(v for _,_,v in parts)*pl))
    if lower:
        out['L_at_reference'],out['free_cell_counts_at_reference']=lower_free_cells(W,pl,delta,parts)
        out['U_at_reference']=interval(a*pl if rule=='B' or delta==0 else a*((1+F(1,W))*pl+delta))
        out['false_permission_proved']=ref_feasible and F(out['L_at_reference']['lower']) > EPS
        if corr_feasible:
            out['L_at_corrected'],out['free_cell_counts_at_corrected']=lower_free_cells(W,pcorr,delta,parts)
    return out


def cv2(r,d):
    f=d/T
    return (r-1)**2*f*(1-f)/(1+(r-1)*f)**2


def global_source_gap():
    """Uniform localization, independent of which sensitivity rows happened to pass."""
    wmin=min(CFG['W'])
    amin=BW*wmin*NU0**2*T
    guard=2*EPS/amin
    nu_max=N*(B0+FS/T)/ENV['reference_bits']
    assert guard < min(T/6,1/nu_max)
    # sum cell lengths squared >= W*P*(T-P/2), and q_S >= BW*mu^2*exp(-mu).
    exclusion=amin*guard*(1-guard/(2*T))*exp_minus(nu_max*guard)[0]
    assert exclusion>HU
    x0=min(NU0*T/12,F(1,2))
    uniform_tail=(wmin//2)*BW*x0*x0*exp_minus(x0)[0]
    assert uniform_tail>HU
    gamma_min=EPS/HU*(1-guard/(2*T))*exp_minus(nu_max*guard)[0]
    operation_min=F(wmin,wmin+2)
    return gamma_min,operation_min,dict(reference_guard_s=interval(guard),
        gamma_min=interval(gamma_min),source_gap_upper_percent=interval(100*(1-gamma_min)),
        finite_operation_factor_min=interval(operation_min),guard_hazard_lower=interval(exclusion),
        uniform_tail_hazard_lower=interval(uniform_tail))


def ratio_threshold(d,target,cap):
    lo,hi=F(1),cap
    assert 0<target<cv2(cap,d)
    for _ in range(70):
        mid=(lo+hi)/2
        if cv2(mid,d)<=target: lo=mid
        else: hi=mid
    return lo,hi


def thresholds():
    out=[]
    gamma_min,operation_min,_=global_source_gap()
    for ds in ENV['duration_slices_s']:
        d=F(ds)
        cap=min(RMAX,1+FS/(B0*d))
        for percent in CFG['thresholds_percent']:
            target=F(percent,100-percent)
            if cv2(cap,d)<=target:
                out.append(dict(d_s=ds,percent=percent,status='not_reached_inside_quota'))
                continue
            lo,hi=ratio_threshold(d,target,cap)
            safe_cv=gamma_min*operation_min/(1-F(percent,100))-1
            safe_lo,safe_hi=ratio_threshold(d,safe_cv,cap)
            # Resource checked at the upper threshold endpoint for each volume.
            checks=[]
            for W in CFG['W']:
                a=BW*W*NU0**2*(T+(hi*hi-1)*d)
                pc=(EPS/a-C)/(1+F(1,W))
                checks.append(dict(W=W,feasible=pc>=W*C/RHO,P_corr_s=interval(pc)))
            out.append(dict(d_s=ds,percent=percent,status='unique_ratio_threshold',
                            r=interval(lo,hi),quota_cap=interval(cap),volumes=checks,
                            total_shift_transition_uniform_bracket=interval(safe_lo,hi),
                            total_shift_at_most_threshold_if_r_le=outward(safe_lo),
                            total_shift_exceeds_threshold_if_r_gt=outward(hi,24,True)))
    return out


def algebra_checks():
    # Independent explicit small calendars vs aggregate power sums (including exact T fence).
    for W in (4,8):
        for p in (F(1),F(7,10),F(17,10)):
            end=F(17,5)
            cells=[b-a for w in range(W) for a,b in intervals_from(scalar_schedule(W,w,p,end),end)]
            for k,v in time_moments(W,p,end).items():
                assert v==sum(x**k for x in cells)
    # Original (4.13): synchronous full cycles plus last remainder.
    n,W,p,end,nu=39,4,F(1),F(17,5),F(1,5)
    mu=[nu*p]*3+[nu*F(2,5)]
    lo,hi=saleh_product(mu*W,n)
    with localcontext() as ctx:
        ctx.prec=100
        def rs(t):
            x=dec(nu*t)
            return (-x).exp()+n*(1-(-x/n).exp())*(-x*(n-1)/n).exp()
        original=F(1-(rs(p)**3*rs(F(2,5)))**W)
    assert lo<=original<=hi
    # Polynomial source enclosure contains direct primary formula on a non-tiny exposure.
    oldT=globals()['T']
    try:
        globals()['T']=end
        hazard=source_hazard(W,p,nu)
        masses=[nu*(b-a) for w in range(W) for a,b in intervals_from(scalar_schedule(W,w,p,end),end)]
        direct=saleh_product(masses,n)
        bounded=probability_from_hazard(*hazard)
        assert bounded[0]<=direct[0]<=direct[1]<=bounded[1]
    finally:
        globals()['T']=oldT


def sources():
    paths=['thesis/ch2/chapter2.md','thesis/ch2/SOURCE_MAP.md',
           'theory/fixed-period-resource-contract.md','theory/fixed-period-resource-contract-appendix.md',
           'theory/t45-lambda-rarity.md','theory/t110-err-write-service.md',
           'experiments/t186-method-comparison/code-strength/common-input.json',
           'experiments/t186-method-comparison/code-strength/comparison.py']
    for f in ('sequential-small-validation-20261014','sequential-err-small-validation-20261015'):
        paths += [f'experiments/{f}/{p}' for p in ('inputs.json','METHOD.md','exact.py','outputs/results.json')]
    for p in ('PLAN.md','inputs.json','reproduce.py'):
        paths.append(str((HERE/p).relative_to(ROOT)).replace('\\','/'))
    # LF-normalized hashes permit Windows/Linux replay without touching source files.
    return {p:sha256((ROOT/p).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in paths}


def write_tables(result):
    lines=['# #340 — основной результат','',
           'Условный ГСО-срез; SEC(39,32), упаковка 48, T=10 лет, epsilon=0.001.',
           'Все времена — секунды. Значения округлены для чтения; строгие интервалы и статусы — results.json.',
           'В пустой строке P_corr не определён внутри общего ресурса; это отказ сертификата, не доказанное нарушение.',
           'Источник всех строк: глава 2, таблица 2.2 (условный ГСО, 3 г/см²); модель сервиса code-strength плюс явно назначенный резерв c (PLAN).',
           '', '| Срез | МиБ | r | d, s | Правило | P_ref | P_corr | Сдвиг, % | Класс | Вывод / причина |',
           '|---|---:|---:|---:|---|---:|---:|---:|---|---|']
    for row in result['sensitivity']:
        status=('P_corr достаточен' if row['corrected_feasible'] else 'сертификат несовместим с ресурсом')
        if row.get('false_permission_proved'): status+='; P_ref исключён нижней'
        status+=' / '+('запас оценки' if F(row['peak_ratio'])==1 else 'переменный профиль')
        if not row['corrected_feasible']: status+=' и ресурс'
        lines.append('| '+ ' | '.join([row['label'],row['useful_MiB'],short(F(row['peak_ratio'])),row['duration_s'],row['rule'],
                                      short(row['P_ref_s']),short(row['P_corr_s']) if row['P_corr_s'] else '∅',
                                      short(row['signed_shift_percent']) if row['signed_shift_percent'] else '—',row['shift_class'],status])+' |')
    lines += ['', '## Разложение и физическая нижняя оценка (4 МиБ, сутки, C)', '',
              '| r | Запас пары против Saleh, % | Только профиль, % | Только операция, % | L(P_ref) | U(P_ref) | L(P_corr) | C<=epsilon<L? |',
              '|---:|---:|---:|---:|---:|---:|---:|---|']
    for row in result['sensitivity']:
        if row['label']=='main' and row['rule']=='C':
            lines.append('| '+' | '.join([short(F(row['peak_ratio'])),short(row['source_to_pair_percent']),
                                          short(row['profile_only_percent']),short(row['operation_only_percent']),
                                          short(row['L_at_reference']),short(row['U_at_reference']),
                                          short(row['L_at_corrected']) if 'L_at_corrected' in row else '—',
                                          'да' if row['false_permission_proved'] else 'нет'])+' |')
    lines += ['', '## Границы отдельного профильного эффекта', '',
              '| Длительность, s | Сдвиг, % | Порог r только профиля | Полоса перехода полного сдвига для всех W/правил | Ресурс при пороге для всех четырёх W |',
              '|---:|---:|---:|---|---|']
    for row in result['thresholds']:
        band=row['total_shift_transition_uniform_bracket']
        text=f"[{short(F(band['lower']))}; {short(F(band['upper']))}]"
        lines.append(f"| {row['d_s']} | {row['percent']} | {short(row['r'])} | {text} | {'проходит' if all(v['feasible'] for v in row['volumes']) else 'см. JSON'} |")
    lines+=['','Ниже левого конца полосы полный |s| не больше порога; выше правого — больше. Это аналитическая полоса запаса, не ошибка арифметики. Внутри используется точный интервальный тест P_corr/P_ref.']
    (HERE/'outputs/TABLE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    lines=['# #340 — 16 готовых случаев: проверка формул','',
           'C_profile использует действительные интегралы профиля; C_mean заменяет профиль его средним.',
           'B: чистые границы на окончаниях. I38: фиктивные чистые границы на снимках; при Delta>0 гарантия Saleh неприменима.',
           'n=38 и n=39 не сравниваются разностью как эффект сервиса.', '',
           '| Случай | L | Q (принятый эталон) | C_profile | C_mean | U | C_profile-Q | Область C_profile |',
           '|---|---:|---:|---:|---:|---:|---:|---|']
    for row in result['small16']:
        lines.append('| '+' | '.join([row['id'],short(row['L']),short(row['Q']),short(row['C_profile']),
                                      short(row['C_mean']),short(row['U']),short(row['C_minus_Q']),row['source_scope']])+' |')
    lines+=['','Численные ошибки C — строгие рациональные интервалы шириной <1e-50 до вывода; Q взят из принятых интервалов шириной <=1e-36.',
             'Интервал L..U — запас оценок, а не вычислительная погрешность. Все 16 U независимо воспроизведены точно.']
    (HERE/'outputs/SMALL16.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


def main():
    algebra_checks()
    small=small_validation()
    rows=[]
    ratios=[RMAX if s=='cap' else F(s) for s in ENV['ratio_slices']]
    for r in ratios:
        for rule in CFG['service']['rules']:
            rows.append(sensitivity_row('main',1048576,F(86400),r,rule=rule,lower=True))
    for W in CFG['W'][:-1]:
        for rule in CFG['service']['rules']:
            rows.append(sensitivity_row('volume',W,F(86400),F(1000),rule=rule))
    for ds in ENV['duration_slices_s']:
        if ds=='86400': continue
        for rule in CFG['service']['rules']:
            rows.append(sensitivity_row('duration',1048576,F(ds),F(100),rule=rule))
    for fraction in CFG['service']['delta_fractions']:
        rows.append(sensitivity_row(f'operation Delta/c={fraction}',1048576,F(86400),F(1000),delta=C*F(fraction)))
    slow=F(CFG['service']['slow_block_s'])
    rows.append(sensitivity_row('operation c=1us',1048576,F(86400),F(1000),c=slow,delta=slow))
    out=dict(task=340,base=CFG['base'],preregistration_commit=PREREG,
             status='OWN_RESULT; awaiting review; conditional singleton/service model',
             source_sha256_lf=sources(),primary_source=dict(doi='10.1109/24.52622',page=118,equations=['4.12','4.13'],
                 pdf_sha256='514a3857f40c30f49233d658da2dd04afa35f3640c3ae6d7e7ecfef4fa635015'),
             small16=small,sensitivity=rows,thresholds=thresholds(),
             whole_region_source_gap=global_source_gap()[2],
             whole_region_operation_bound_percent={str(w):interval(F(200,w+2)) for w in CFG['W']},
             checks=dict(accepted_cases=16,accepted_Q_recomputed=False,independent_U_reproduction=True,
                         source_ideal_limit=True,aggregated_moments=True,source_enclosure=True,
                         all_quotas=True,all_reported_corrected_periods_pass=True,
                         all_reference_roots_bracketed=True,large_reference_monotonicity_scope='P<=min(T/6,1/nu_mean); tail excluded by initial cells'))
    (HERE/'outputs').mkdir(exist_ok=True)
    (HERE/'outputs/results.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    write_tables(out)
    print(f'PASS: 16 accepted-case checks; {len(rows)} preregistered sensitivity rows; {len(out["thresholds"])} analytic thresholds.')


if __name__=='__main__':
    main()
