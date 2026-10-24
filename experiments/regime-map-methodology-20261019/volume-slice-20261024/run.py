"""Bounded volume slice reusing PR250. All new results require review."""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASE = ROOT / 'experiments/fixed-code-long-lived-20261023'
spec = importlib.util.spec_from_file_location('accepted_pr250', BASE / 'calculate.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
OUT = HERE / 'outputs'


def cfg_for(kib):
    original, _, _ = base.load()
    cfg = deepcopy(original)
    cfg['words'] = kib * 1024 // 4
    cfg['useful_bytes'] = kib * 1024
    return cfg


def read(path):
    return base.numeric(json.loads(path.read_text('utf-8')))


def verify_inputs():
    manifest = json.loads((HERE / 'frozen-inputs.json').read_text('utf-8'))
    for name, digest in manifest['sha256'].items():
        raw = (ROOT / name).read_bytes().replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Frozen dependency changed: ' + name)
    return manifest


def certificate(cfg, kib, k, compute, force=False):
    target = OUT / f'certificate-{kib}KiB-k{k}.json'
    if compute and (force or not target.exists()):
        print(json.dumps(dict(start_kib=kib, k=k)), flush=True)
        start = time.perf_counter()
        cert = base.info.compute(cfg, k)
        target.write_bytes(base.encoded(cert))
        print(json.dumps(dict(done_kib=kib, k=k, seconds=time.perf_counter()-start,
                              Q_upper=float(cert['risk']['upper']))), flush=True)
    cert = read(target)
    if cert['calendar']['W'] != cfg['words'] or cert['k'] != k:
        raise ValueError('Wrong certificate volume or k')
    return cert


def odd_at_least(k):
    return k if k % 2 else k + 1


def price_gate(cfg):
    """A lower bound on the COMPUTED upper-price certificate, not real cost."""
    s=base.cmp.service(cfg,39)
    a,e=cfg['adaptive'],cfg['environment']
    T=F(cfg['mission_s']); W=cfg['words']
    factor=F(39*W,e['reference_words']*e['reference_bits'])
    b=factor*F(e['reference_background_per_s'])
    fs=factor*F(e['reference_solar_mass'])
    S=lambda x: F(2+base.cmp.ceil((F(x)*base.NS+s['J'])/(cfg['calendar']['c_ticks']*s['xminus'])))
    hard=base.cmp.read_bounds(cfg,1)['upper']
    terms=dict(background=S(a['short_hold_s'])*b*T,
               solar=S(a['long_hold_s'])*fs,
               false=S(a['long_hold_s'])*F(a['ordinary_false_expected_per_s'])*T,
               recovery=(a['recoveries_upper']+1)*S(a['long_hold_s']),
               loss=F(a['ordinary_outage_fraction'])*T*base.NS/(cfg['calendar']['c_ticks']*s['xminus'])+2*a['ordinary_loss_episodes_upper'],
               bad=F(cfg['lifetime_other_budget'])*hard)
    Rbus=3*cfg['service']['read_beat_ns']*s['xplus']+s['J']
    floor=Rbus*min(hard,sum(terms.values(),F(0)))/(T*base.NS)
    return dict(certificate_bus_floor=floor,terms=terms,
                terms_bus_fraction={k:Rbus*v/(T*base.NS) for k,v in terms.items()},
                NOT_a_lower_bound_on_real_cost=True,
                proves_no_positive_gap_with_this_price_and_class_bound_only=True)


def mandatory_row(cfg,kib,kf):
    k=kf if kf%2 else kf-1
    risk=base.cmp.risk(cfg,39,1,base.cmp.period(cfg,k)['upper_ns'],base.cmp.service(cfg,39)['upper']['E'])
    cal=base.info.calendar(cfg,k)
    return dict(k=k,Q_upper=risk['upper'],sufficient=risk['upper']<=F(cfg['epsilon']),
                price=base.price(cfg,39,k,risk['upper'],cal),calendar=cal,risk=risk,
                certificate='accepted mandatory-only T196(5), recomputed for this W/k',
                selection_reason='price-certificate floor blocks positive sufficient gap for every k')


def probe_sequence(cfg, kib, kf, compute, pilot=False, force=False):
    rows = []
    k = 2*kf+1
    for i in range(3):
        cert = certificate(cfg, kib, k, compute, force)
        sufficient = cert['risk']['upper'] <= F(cfg['epsilon'])
        price = base.price(cfg, 39, k, cert['risk']['upper'], cert['calendar'])
        rows.append(dict(k=k, Q_upper=cert['risk']['upper'], sufficient=sufficient,
                         price=price, certificate=f'outputs/certificate-{kib}KiB-k{k}.json'))
        if pilot:
            break
        if i == 0:
            k = 4*kf+1 if sufficient else odd_at_least(kf)
            if k == rows[0]['k']:
                k = 1
        elif i == 1:
            ok = [r['k'] for r in rows if r['sufficient']]
            bad = [r['k'] for r in rows if not r['sufficient']]
            if not ok or not bad:
                break
            lo, hi = min(ok[0], bad[0]), max(ok[0], bad[0])
            k = odd_at_least((lo+hi)//2)
            if not lo < k < hi:
                break
    return rows


def summarize(cfg, kib, fixed, lower, rows):
    eligible = [r for r in rows if r['sufficient']]
    selected = min(eligible, key=lambda r: r['price']['pure_bus_upper']) if eligible else None
    F_lower = lower['pure_bus_class_lower_if_reviewed']
    fixed_price = base.price(cfg, 39, fixed['k'], fixed['risk']['upper'])
    F_upper = fixed_price['pure_bus_upper']
    comparison = None
    if selected:
        cost = selected['price']
        A_up, A_lo = cost['pure_bus_upper'], cost['pure_bus_lower']
        # Optional veto occupies a complete worst-case E, in pure bus units.
        svc = base.cmp.service(cfg, 39)
        er = cost['extra_veto_actions']['scrub_reads']
        bus_E = (3*cfg['service']['read_beat_ns']+3*cfg['service']['write_beat_ns']+cfg['service']['turnaround_ns'])*svc['xplus']+2*svc['J']
        comparison = dict(adaptive_bus_upper=A_up, adaptive_support_bus_lower=A_lo,
                          fixed_class_bus_lower=F_lower, fixed_witness_bus_upper=F_upper,
                          control_bus_sufficient_strict_below=F_lower-A_up,
                          necessary_limit_offset_requires_fixed_control_upper=F_upper-A_lo,
                          fixed_extra_control_upper=None,
                          gain_lower_at_zero_extra=F_lower/A_up,
                          core_only_gain_upper_from_fixed_witness=F_upper/A_lo,
                          extra_veto_bus_slope=bus_E*er/base.NS,
                          meaning='sufficient upper on adaptive control u; necessary limit adds unknown fixed-control upper',
                          all_adaptive_policies_optimality_claim=False)
    svc=base.cmp.service(cfg,39)
    app_rate=base.cmp.count_apps(cfg)['read']/F(cfg['mission_s'])
    return dict(kib=kib, words=cfg['words'], fraction_of_reference=F(kib,512),
                mission_s=cfg['mission_s'], epsilon=F(cfg['epsilon']),
                delta_common=F(cfg['lifetime_other_budget']),
                separate_bank=True, whole_reference_memory_Q=None,
                fixed=fixed, fixed_price=fixed_price, fixed_class=lower,
                adaptive_rows=rows, selected_k=selected['k'] if selected else None,
                comparison=comparison,price_gate=price_gate(cfg), timing=base.cmp.timing(cfg,39,selected['k'] if selected else 1),
                common_code=dict(active_bits=39*cfg['words'], check_bits=7*cfg['words'],
                                 padding_bits=9*cfg['words'], physical_bytes=6*cfg['words'],
                                 initialization_encodes=cfg['words']),
                probability_margin=F(cfg['epsilon'])-selected['Q_upper'] if selected else None,
                probability_target_margin=F(cfg['epsilon'])/2-selected['Q_upper'] if selected else None,
                unknown_resource_margin=None,
                common_application=dict(read_only=True,
                    serialized_service_upper=app_rate*svc['upper']['app_read']/base.NS,
                    pure_bus_upper=app_rate*(3*cfg['service']['read_beat_ns']*svc['xplus']+svc['J'])/base.NS,
                    ECC_nominal_part_already_in_service=app_rate*(cfg['service']['read_beat_ns']+svc['decode'])/base.NS),
                application_read_rate=app_rate,
                application_write_rate=F(0), app_repair=False, app_ERR=False)


def run(compute=False, pilot=False, force=False):
    manifest = verify_inputs()
    OUT.mkdir(exist_ok=True)
    accepted = read(BASE / 'outputs/result.json')
    rows = []
    for kib in ([256] if pilot else [512,256,128,64]):
        cfg = cfg_for(kib)
        if kib == 512:
            fixed = next(x for x in accepted['fixed_candidates'] if x['n']==39 and x['target']==F(cfg['epsilon']))
            lower = accepted['fixed_class_candidate']['excluded_from']
            adaptive = [deepcopy(next(x for x in accepted['adaptive_rows'] if x['k']==accepted['selected_k']))]
            adaptive[0]['certificate'] = 'accepted PR250 outputs/certificate-k53.json'
        else:
            fixed = base.fixed(cfg,39,1)
            lower = base.class_threshold(cfg)['excluded_from']
            gate=price_gate(cfg)
            if not pilot and lower['pure_bus_class_lower_if_reviewed'] <= gate['certificate_bus_floor']:
                adaptive=[mandatory_row(cfg,kib,fixed['k'])]
            else:
                adaptive = probe_sequence(cfg,kib,fixed['k'],compute,pilot,force)
        row = summarize(cfg,kib,fixed,lower,adaptive)
        rows.append(row)
        print(json.dumps(dict(kib=kib,fixed_k=fixed['k'],selected_k=row['selected_k'],
                              comparison={k:float(v) if isinstance(v,F) else v for k,v in (row['comparison'] or {}).items()})),flush=True)
    return dict(status='NEW_VOLUME_SLICE_FOR_INDEPENDENT_REVIEW',
                plan_commit='c2da6522285038a10380051476c217550ae2cec3',
                frozen_dependencies=len(manifest['sha256']),rows=rows,
                physical_Q=None, interpolated_boundary=None, total_partial_memory_Q=None,
                observation_veto_slice=0, unknown_CPU=None, unknown_energy=None)


if __name__ == '__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    group=ap.add_mutually_exclusive_group(required=True)
    group.add_argument('--compute',action='store_true')
    group.add_argument('--recompute',action='store_true',help='replace all three new phase certificates, ignoring cache')
    group.add_argument('--check',action='store_true')
    group.add_argument('--assemble',action='store_true')
    ap.add_argument('--pilot',action='store_true')
    args=ap.parse_args()
    value=run(args.compute or args.recompute,args.pilot,args.recompute)
    if not args.pilot:
        target=OUT/'result.json'
        payload=base.encoded(value)
        if args.check:
            if target.read_bytes()!=payload:raise AssertionError('Exact replay mismatch')
        else:
            target.write_bytes(payload)
        print('SHA256',hashlib.sha256(payload).hexdigest(),flush=True)
