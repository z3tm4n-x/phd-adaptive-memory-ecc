"""Independent Decimal-90 checks; does not import T72/T58 or timing.py."""
from decimal import Decimal as D, localcontext, ROUND_CEILING, ROUND_FLOOR


def dec(x):
    if hasattr(x, 'numerator') and hasattr(x, 'denominator'):
        return D(x.numerator)/D(x.denominator)
    return D(str(x))


def check(cfg, env, reference):
    with localcontext() as ctx:
        ctx.prec = 90
        s, m, r, q = [cfg[k] for k in ['service', 'monitor', 'resources', 'whole_mission_quotas']]
        W, n = cfg['scenario']['W'], cfg['scenario']['n']
        T, eps = D(cfg['scenario']['T_s']), D(cfg['scenario']['epsilon'])
        tm = D(s['tick_nominal_s'])*D(s['constant_clock_scale_min'])
        tp = D(s['tick_nominal_s'])*D(s['constant_clock_scale_max'])
        c, g = D(s['c_ticks'])*tp, D(s['g_ticks'])*tm
        ps = D(W*s['g_ticks'])*tp
        pl = D(s['long_multiplier'])*ps
        b, solar = D(env['bbar_per_s']), D(env['solar_peak_per_s'])
        B, fs = b+solar, D(115776)*solar
        beta = D(n-1)/D(2*n*W)
        vc = D(m['v_c_per_s'])
        V = min(vc*vc*T, b*b*T+(vc+b)*fs) if vc >= b else vc*vc*T
        ds = D(cfg['mark_contract']['D_star_full38_direct_exposure_upper'])
        err = sum(D(q[k]) for k in ['rho0', 'delta_exec', 'delta_svc', 'delta_E', 'delta_M', 'alpha_M'])
        risk = err+ds+D(q['K0'])*B*ps/W+beta*(ps*D(env['S2_rational_upper_per_s'])+pl*V)
        square = min(B*B*T, B*(b*T+fs), b*b*T+(B+b)*fs)
        intercept = ds+sum(D(q[k]) for k in ['rho0', 'delta_exec', 'delta_svc'])
        slope = beta*square+D(q['K0'])*B/W
        M = int(((eps-intercept)/(slope*tp)).to_integral_value(rounding=ROUND_FLOOR))
        assert M == reference['fixed_strong_M']
        assert intercept+D(M)*tp*slope <= eps < intercept+D(M+1)*tp*slope
        h = D(r['peak_window_s'])
        periods = (h/(2*g)).to_integral_value(rounding=ROUND_FLOOR)
        work = h if c >= g else periods*2*c+min(2*c, h-periods*2*g)
        cm, sm = D(r['extra_monitor_control_rate']), D(r['extra_monitor_control_sigma_s'])
        peak = (work+sm+cm*h)/h
        block = 2*c+D(r['application_max_request_s'])
        rate = 1-block/(2*g)
        delay = block+(D(r['application_sigma_s'])+sm)/rate if rate > 0 else D(10**9)
        wm, wp = D(m['window_ticks'])*tm, D(m['window_ticks'])*tp
        J = (T/wm).to_integral_value(rounding=ROUND_CEILING)
        mu = wp*(D(m['A_M'])*b+D(m['eta_M_per_s']))
        x = max(D(0), D(m['k'])-mu)
        exponent = x*x/(2*(mu+x/3)) if x else D(0)
        tail = (-exponent).exp()
        cf, cs = c/g, c/(g*s['long_multiplier'])
        strip = D(s['price_strip_physical_s'])
        # Parse rational strings added to the ERR budget without importing Fraction.
        def rational_text(text):
            a, sep, bden = str(text).partition('/')
            return D(a)/D(bden) if sep else D(a)
        de = rational_text(cfg['own_ERR']['max_delivery_s'])
        rf, bad = D(cfg['own_ERR']['false_flag_rate_upper_per_s']), D(m['recognized_bad_window_probability'])
        pq = min(D(1), err-D(q['alpha_M'])+ds+D(q['K0'])*b*ps/W+beta*pl*b*b*T)
        quiet = cs+cf*min(D(1), strip*(1+q['K0'])/T+strip*(b+rf)+J*strip/T*(tail+bad)+pq)+2*c/T+cm+sm/T
        tq, kq = D('.9')*T, D(1000)
        ret = cs+cf*min(D(1), strip*(b+rf)+strip*(kq+q['K0']+kq*B*(pl+de))/tq
                        +strip*(1/wm+2*kq/tq)*(tail+bad)+risk)+2*c*kq/tq+cm+sm*kq/tq
        computed = dict(risk_upper=risk, peak_upper=peak, app_delay_upper_s=delay,
                        quiet_mission_upper=quiet, quiet_returns_upper=ret)
        for key, value in computed.items():
            assert abs(dec(reference[key])-value) < D('1e-47'), (key, value, dec(reference[key]))
        return dict(metrics_checked=len(computed)+2, precision=90,
                    max_absolute_difference=str(max(abs(dec(reference[k])-v) for k, v in computed.items())))
