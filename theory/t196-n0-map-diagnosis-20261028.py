"""Check only the three fixed N0 rules from accepted PR298; no search.

New formula/proof: t196-n0-map-diagnosis-20261028.md, sections 2-3.
Default checks the saved result; --write creates only its new result file.
All scientific arithmetic is rational. Decimal is an independent check.
"""
import argparse
from decimal import Decimal, localcontext
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
BASE = ROOT / 'experiments/regime-map-methodology-20261019/predictability-volume-20261028'
OUT = HERE / 't196-n0-map-diagnosis-20261028-result.json'
EXPECTED = {'c01': (1048576, F(1, 1000), [15, 120]),
            'c02': (1048576, F(1, 10000), [1, 16]),
            'c07': (131072, F(1, 1000), [727, 11632])}


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def upper_decimal(x, places=15):
    scale = 10 ** places
    v = -(-(x.numerator * scale) // x.denominator)
    return f'{v // scale}.{v % scale:0{places}d}'


def decimal(x):
    x = F(x)
    return Decimal(x.numerator) / Decimal(x.denominator)


def independent_decimal(c, cell, kh, kl):
    """Recompute from raw inputs, using cubic primitives, not edge expansion."""
    with localcontext() as ctx:
        ctx.prec = 85
        e, s, ch = (c[k] for k in ('environment', 'service', 'information'))
        n = Decimal(e['template']['count'])
        width = Decimal(e['template']['width_s'])
        rise = Decimal(e['template']['rise_s'])
        T, W = Decimal(c['bank']['mission_s']), Decimal(cell['words'])
        b, B, fs = (Decimal(e[k]) for k in ('b', 'B', 'Fs'))
        a = 2 * fs / (n * width)
        xp, jitter = Decimal(s['xi_plus']), Decimal(s['J_ns']) / 10**9
        ph = 196 * kh * W * xp / 10**9 + jitter
        pl = 196 * kl * W * xp / 10**9 + jitter
        de = 124 * xp / 10**9 + 3 * jitter
        pad = xp + jitter + Decimal(ch['command_delay_upper_s'])
        pad += 320 * xp / 10**9 + jitter + 2 * Decimal(ch['mission_time_error_upper_s'])
        strip = ph + de + 2 * pad
        slope = a / rise
        ih = 2 * n * ((b + a)**3 - b**3) / (3 * slope)
        il = (T - n * width) * b**2
        edge = 2 * n * ((b + slope * strip)**3 - b**3) / (3 * slope)
        K = W * 39 * 38 / (2 * Decimal(e['reference_positions'])**2)
        delta = Decimal(ch['lifetime_delta_exec']) + Decimal(ch['lifetime_delta_calendar'])
        xe = 2 * B * de * (b * T + fs)
        return delta + K * ((ph + de) * ih + (pl + de) * il + (pl - ph) * edge + xe)


def calculate():
    c = json.loads((BASE / 'inputs.json').read_text('utf-8'))
    m = json.loads((BASE / 'map-14/inputs.json').read_text('utf-8'))
    accepted = json.loads((BASE / 'map-14/result.json').read_text('utf-8'))
    pinned = {
        BASE / 'map-14/inputs.json': 'bbd6e84d1ab646e16577b01519d21d339100ced74cda34f6c503a77a590bafd4',
        BASE / 'map-14/result.json': 'ef8b56daf67fbc3b48804129ba7ddde27dab33346aee9c24254f8c20584274e0',
    }
    for path, expected in pinned.items():
        assert digest(path) == expected, path
    for path, expected in m['source_sha256_LF'].items():
        assert digest(ROOT / path) == expected, path
    assert c['bank']['code'] == [39, 32, 1]
    assert c['bank']['clean_initial_conditional'] and not c['bank']['pending_initial']
    e, s, ch = (c[k] for k in ('environment', 'service', 'information'))
    T, n, width, rise = (F(c['bank']['mission_s']), F(e['template']['count']),
                         F(e['template']['width_s']), F(e['template']['rise_s']))
    b, B, fs = (F(e[k]) for k in ('b', 'B', 'Fs'))
    a = 2 * fs / (n * width)
    xp, xm, jitter = F(s['xi_plus']), F(s['xi_minus']), F(s['J_ns']) / 10**9
    de = 124 * xp / 10**9 + 3 * jitter
    pad = xp + jitter + F(ch['command_delay_upper_s'])
    pad += 320 * xp / 10**9 + jitter + 2 * F(ch['mission_time_error_upper_s'])
    delta = F(ch['lifetime_delta_exec']) + F(ch['lifetime_delta_calendar'])
    ih = n * width * (b*b + b*a + a*a/3)
    il = (T - n * width) * b*b
    box = n * width * (b+a)**2
    xe = 2 * B * de * (b*T + fs)
    rows = {}
    for key, (W, eps, pair) in EXPECTED.items():
        cell = next(x for x in m['cells'] if x['id'] == key)
        old = accepted['cells'][key]['methods']['N0']
        assert (cell['words'], F(cell['alpha']), F(cell['epsilon'])) == (W, 0, eps)
        assert old['pair'] == pair and old['Q_status'] == 'unresolved'
        kh, kl = pair
        assert kl % kh == 0 and W % 8 == 0 and W & (W-1) == 0
        ph, pl = (196 * k * W * xp / 10**9 + jitter for k in pair)
        ah, al = ph + de, pl + de
        strip = ah + 2 * pad
        assert 0 < strip < rise and 2 * strip < width
        assert 196 * W * xp / 10**9 + jitter + de < F(e['template']['left_s'])
        assert F(e['template']['left_s']) - al - 2 * pad > 0
        assert n * F(e['template']['cycle_s']) == T
        edge = 2 * n * (b*b*strip + b*a*strip**2/rise + a*a*strip**3/(3*rise**2))
        assert 0 < edge < ih
        K = F(W * 39 * 38, 2 * e['reference_positions']**2)
        v0 = delta + K * (ph * box + pl * il)
        assert v0 == F(old['V0'])
        peak_margin = K * ph * (box - ih)
        weak_extension = K * de * (ih + il)
        mixed = K * xe
        boundary = K * (al - ah) * edge
        q = delta + K * (ah * ih + al * il + (al-ah) * edge + xe)
        assert q == v0 - peak_margin + weak_extension + mixed + boundary
        assert q < eps < F(old['Q_upper'])
        assert F(old['Q_lower']) <= q
        with localcontext() as ctx:
            ctx.prec = 80
            independent_error = abs(decimal(q) - independent_decimal(c, cell, kh, kl))
            assert independent_error < Decimal('1e-75')
        rounded = upper_decimal(q)
        assert q <= F(rounded) < eps
        rows[key] = dict(words=W, alpha=0, epsilon=eps, pair=pair,
            period_high_upper_s=ph, period_low_upper_s=pl, strip_s=strip,
            inherited_Q_lower=F(old['Q_lower']), inherited_Q_upper=F(old['Q_upper']),
            V0=v0, peak_margin=peak_margin, weak_E_extension=weak_extension,
            E_mixed=mixed, boundary_penalty=boundary, edge_integral=edge,
            Q_upper=q, Q_upper_decimal=rounded, epsilon_minus_upper=eps-q,
            result='N0 sufficient in the accepted conditional model',
            independent_decimal_agrees_to_absolute='1e-75')
    paths = [BASE/'inputs.json', BASE/'THEORY.md', BASE/'first_point.py',
             BASE/'map-14/inputs.json', BASE/'map-14/result.json',
             ROOT/'theory/t196-three-variant-foundations-20261022.md',
             ROOT/'theory/t196-predictable-windows-20261025.md', Path(__file__)]
    return dict(schema=1, status='OWN RESULT; independent review pending',
        base_main='30dd56ca97a0553fb8c9900325eaebfcc84ba4c8',
        accepted_map_head='d278fdf9991b2be78ce4ad4063c74f24cf2cb589',
        sources_sha256_LF={p.relative_to(ROOT).as_posix(): digest(p) for p in paths},
        mission_s=T, calendar_pad_s=pad, delta=delta, dE_s=de,
        squared_integral_high=ih, squared_integral_low=il, rows=rows,
        accepted_files_written=False, candidate_search=False, physical_alpha_assigned=False)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = calculate()
    raw = (json.dumps(result, default=str, ensure_ascii=False, indent=2, sort_keys=True) + '\n').encode('utf-8')
    if args.write:
        OUT.write_bytes(raw)
    else:
        assert OUT.read_bytes().replace(b'\r\n', b'\n') == raw, 'Result replay mismatch'
    for key, row in result['rows'].items():
        print(key, 'Q <=', row['Q_upper_decimal'], '<', row['epsilon'])
    print('Exact rational inequalities and independent 85-digit primitive check: PASS')


if __name__ == '__main__':
    main()
