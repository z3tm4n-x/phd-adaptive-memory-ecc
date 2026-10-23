"""Bounded fixed-code long-lived calculation; no radiation input is changed.

New results require independent review. --compute writes new phase certificates;
--check only replays the small accounts from those certificates.
"""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(BASE))
import comparison as cmp
import informational as info

NS = cmp.NS
I = info.I
OUT = HERE / 'outputs'


def encoded(value):
    return (json.dumps(value, indent=2, sort_keys=True, default=str)+'\n').encode()


def numeric(value):
    if isinstance(value, dict):
        return {k:numeric(v) for k,v in value.items()}
    if isinstance(value, list):
        return [numeric(v) for v in value]
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            pass
    return value


def load():
    manifest = json.loads((HERE/'frozen-inputs.json').read_text('utf-8'))
    for name, digest in manifest['sha256'].items():
        data = (ROOT/name).read_bytes().replace(b'\r\n',b'\n')
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Frozen input changed: '+name)
    cfg = json.loads((BASE/'common-input.json').read_text('utf-8'))
    accepted = numeric(json.loads((ROOT/'experiments/mission-rise-rate-20261022/cfe-application/outputs/result.json').read_text('utf-8')))
    return cfg, accepted, manifest


def fixed(cfg, n, t, divisor=1):
    target = F(cfg['epsilon'])/divisor
    risk = lambda k: cmp.risk(cfg,n,t,cmp.period(cfg,k)['upper_ns'],cmp.service(cfg,n)['upper']['E'])
    lo,hi=0,1
    while risk(hi)['upper'] <= target:
        lo,hi=hi,2*hi
        if hi>cfg['fixed']['search_cap_k']:
            raise ValueError('Fixed search cap')
    if not lo:
        raise ValueError('No sufficient fixed candidate')
    while hi-lo>1:
        mid=(lo+hi)//2
        if risk(mid)['upper'] <= target:
            lo=mid
        else:
            hi=mid
    return dict(n=n,t=t,k=lo,target=target,risk=risk(lo),next_upper=risk(hi)['upper'],
                period=cmp.period(cfg,lo),optimality='largest certified integer k, not true optimum')


def price(cfg, n, k, upper, calendar=None):
    """Protection work only; useful app work and common ECC shown separately."""
    adaptive = calendar is not None
    c = cmp.cost_result(cfg,n,1 if n==39 else 2,k,upper,adaptive,calendar)
    T=F(cfg['mission_s']); s=cmp.service(cfg,n); W=cfg['words']
    N=c['read_count_upper']; terms=None
    if adaptive:
        cal=calendar; a=cfg['adaptive']; e=cfg['environment']
        fresh=F(a['source_to_fresh_rule_upper_ns'],NS)
        S=lambda length:F(2+cmp.ceil((length*NS+s['J'])/(cfg['calendar']['c_ticks']*s['xminus'])))
        tau=cal['tau']+fresh; wp=cal['w_upper']+fresh; hp=cal['h_upper']+fresh
        pair=cal['source_PAIR']['upper']+2*cal['J']
        d,V,H,L=pair+tau,wp+tau,hp+tau,hp+pair+2*tau
        factor=F(W*n,e['reference_words']*e['reference_bits'])
        b=factor*F(e['reference_background_per_s']); fs=factor*F(e['reference_solar_mass'])
        parents=b*T+fs
        terms=dict(background_first=S(V)*b*T,background_pairs=S(H)*b*b*d*T,
            solar_and_cross=S(H)*(1+b*d)*fs,
            false=S(L)*F(a['ordinary_false_expected_per_s'])*T,
            weak_E_repeat=S(L)*parents/W,
            startup_and_recovery=(a['recoveries_upper']+1)*S(cal['recovery']['upper']+fresh),
            loss=F(a['ordinary_outage_fraction'])*T*NS/(cfg['calendar']['c_ticks']*s['xminus'])+2*a['ordinary_loss_episodes_upper'],
            support=cmp.read_bounds(cfg,k)['upper'],bad=upper*c['adaptive']['reads_hard_upper'])
        N=min(N,c['adaptive']['reads_hard_upper'],sum(terms.values(),F(0)))
    repairs=min(N,c['repair_count_upper'])
    reads_lower=cmp.read_bounds(cfg,k)['lower']
    core=(s['upper']['R']*N+(s['upper']['E']-s['upper']['R'])*repairs)/(T*NS)
    lower=s['lower']['R']*reads_lower/(T*NS)
    hardN=cmp.read_bounds(cfg,1 if adaptive else k)['upper']
    hard=s['upper']['E']*hardN/(T*NS)
    # Pure bus upper: one endpoint span for read and one for repair segment.
    bus_read=3*cfg['service']['read_beat_ns']*s['xplus']+s['J']
    bus_write=(3*cfg['service']['write_beat_ns']+cfg['service']['turnaround_ns'])*s['xplus']+s['J']
    bus=(bus_read*N+bus_write*repairs)/(T*NS)
    bus_lower=max(F(0),3*cfg['service']['read_beat_ns']*s['xminus']-s['J'])*reads_lower/(T*NS)
    rates=dict(scrub_reads=N/T,scrub_corrections=repairs/T,decodes=N/T,
        read_beats=3*N/T,write_beats=3*repairs/T,turnarounds=repairs/T)
    for key in ('cuts','captures','records','decisions','timer_events'):
        rates[key]=c['full_cost_rates'][key]
    rates['observation_record_transfers']=rates['records']
    rates['observation_cut_transfers']=rates['cuts']
    cpu={key+'_ns':rates[key]/NS for key in ('cuts','captures','records','decisions','timer_events')}
    result=dict(core_lower=lower,core_upper=core,pure_bus_lower=bus_lower,pure_bus_upper=bus,
        rates_per_s=rates,CPU_fraction_coefficients=cpu,
        energy='T*sum(rate_a*incremental_nonoverlapping_J_a)+T*protection_idle_W',
        unknown_controller_bus=None,CPU_value=None,energy_value=None,
        initialization_common_core_upper=s['upper']['initial']*W/(T*NS),
        reads_upper=N,repairs_upper=repairs,all_history_core_upper=hard,
        read_count_terms=terms,after_A_paid=True,tail_paid=True,
        hardware_winner=None,physical_Q=None)
    if adaptive:
        result.update(veto_slice_per_s=F(0),extra_veto_core_slope=c['veto_core_fraction_slope_per_notification_per_s'],
                      extra_veto_actions=c['extra_veto_action_rates_per_unit_v'],
                      adaptive_state_bytes=131136,
                      scope='v=0 conditional slice; for unknown v use hard upper and retain controller costs')
    return result


def fixed_class_lower(cfg, P0):
    """Candidate consequence of T196(8), arbitrary phases and all P>=P0.

    Peak plateau from t=0 is allowed by the one-sided growth restriction.
    Remove the initial fast pass and bound all possible E windows. Jensen
    bounds sum of squared free-gap lengths without choosing a phase.
    """
    e=cfg['environment']; s=cmp.service(cfg,39); W=cfg['words']; T=F(cfg['mission_s'])
    b,B,fs=(F(e[x]) for x in ('reference_background_per_s','reference_peak_per_s','reference_solar_mass'))
    plateau=fs/(B-b)
    prefix=F(cmp.period(cfg,1)['upper_ns'],NS)
    length=plateau-prefix
    lam=F(39)*B/(e['reference_words']*e['reference_bits'])
    aperture=(s['upper']['E']+2*s['J'])/NS
    windows=length/F(P0)+2
    free=max(F(0),length-windows*aperture)
    sq=free*free/(windows+1)
    exponent=I(W*F(38,39)*lam*lam*sq/2)*(I(-lam*length)).exp()
    q=I(1)-(I(0)-exponent).exp()-I(F(cfg['lifetime_other_budget']))
    # Exclude policies at the allowed upper clock scale and zero jitter.
    # At any allowed execution their cycle has at most one endpoint span more.
    period_limit=F(P0)+s['J']/NS
    core=s['lower']['R']*W*max(F(0),1/period_limit-2/T)/NS
    bus=max(F(0),3*cfg['service']['read_beat_ns']*s['xminus']-s['J'])*W*max(F(0),1/period_limit-2/T)/NS
    return dict(P0=F(P0),plateau_s=plateau,prefix_s=prefix,window_count_upper=windows,
        aperture_s=aperture,free_length_lower=free,gap_squares_lower=sq,
        admitted_period_upper_limit=period_limit,
        Q_lower=max(F(0),F(q.lo)),Q_upper_numeric_enclosure=min(F(1),F(q.hi)),
        core_class_lower_if_reviewed=core,pure_bus_class_lower_if_reviewed=bus,
        status='candidate lemma and numbers; independent theory review required')


def class_threshold(cfg):
    lo,hi=1,1000000
    while fixed_class_lower(cfg,F(hi,10**6))['Q_lower'] <= F(cfg['epsilon']):
        hi*=2
    while hi-lo>1:
        mid=(lo+hi)//2
        if fixed_class_lower(cfg,F(mid,10**6))['Q_lower'] > F(cfg['epsilon']):
            hi=mid
        else:
            lo=mid
    return dict(last_not_excluded=fixed_class_lower(cfg,F(lo,10**6)),
                excluded_from=fixed_class_lower(cfg,F(hi,10**6)))


def run(compute=False):
    cfg,accepted,manifest=load(); original=encoded(cfg)
    fixeds=[fixed(cfg,39,1),fixed(cfg,39,1,2),fixed(cfg,44,2)]
    for row in fixeds:
        row['price']=price(cfg,row['n'],row['k'],row['risk']['upper'])
    threshold=class_threshold(cfg)
    rows=[]
    for k in (27,53,107,215,431):
        if k==27:
            cert=accepted['informational']
            U=max(cert['risk']['upper'],accepted['accepted_risk_upper_retained_in_price'])
        else:
            file=OUT/f'certificate-k{k}.json'
            if compute:
                print(json.dumps(dict(computing_k=k)),flush=True)
                cert=info.compute(cfg,k); file.write_bytes(encoded(cert))
            else:
                cert=numeric(json.loads(file.read_text('utf-8')))
            U=cert['risk']['upper']
        cost=price(cfg,39,k,U,cert['calendar'])
        rows.append(dict(k=k,period_s=cmp.period(cfg,k)['upper_ns']/NS,
            Q_upper=cert['risk']['upper'],price_bad_probability_used=U,
            sufficient=cert['risk']['upper']<=F(cfg['epsilon']),price=cost))
        print(json.dumps(dict(k=k,Q=float(cert['risk']['upper']),protection_core_upper=float(cost['core_upper']))),flush=True)
        if cert['risk']['upper']>F(cfg['epsilon']):
            break
    eligible=[r for r in rows if r['sufficient']]
    selected=min(eligible,key=lambda r:r['price']['core_upper'])
    c=selected['price']; fc=fixeds[0]['price']; lower=threshold['excluded_from']
    delta=lower['core_class_lower_if_reviewed']-c['core_upper']
    bus_delta=lower['pure_bus_class_lower_if_reviewed']-c['pure_bus_upper']
    old_period=F(cfg['words']*cfg['application']['epoch_ns'],NS)
    off={str(n):cmp.risk(cfg,n,t,old_period*NS,cfg['constraints']['application_deadline_ns']) for n,t in ((39,1),(44,2))}
    app_reads=cmp.count_apps(cfg)['read']/cfg['mission_s']
    s=cmp.service(cfg,39)
    result=dict(status='AUTHOR_CALCULATION_READY_FOR_INDEPENDENT_REVIEW',
        plan_commit='24636b542a2ea746d1de969bd9549d6b7254e7b6',
        scope=dict(long_lived_fraction=1,words=cfg['words'],mission_s=cfg['mission_s'],epsilon=F(cfg['epsilon']),
            code=[39,32,1],useful_writes=0,ordinary_reads_repair=False,ordinary_reads_publish_ERR=False,
            fixed_class='one constant periodic scan per word, arbitrary phases, first fast pass; all histories to T',
            input='accepted conditional singleton model; not a newly qualified GEO/LEO input'),
        fixed_candidates=fixeds,adaptive_rows=rows,selected_k=selected['k'],fixed_class_candidate=threshold,
        comparison=dict(candidate_fixed_lower_over_adaptive_upper=fc['core_lower']/c['core_upper'],
            candidate_upper_ratio=fc['core_upper']/c['core_upper'],
            class_gain_lower_if_lemma_accepted=lower['core_class_lower_if_reviewed']/c['core_upper'],
            pure_bus_class_gain_lower_if_lemma_accepted=lower['pure_bus_class_lower_if_reviewed']/c['pure_bus_upper'],
            gain_upper_from_fixed_witness_and_adaptive_support=fc['core_upper']/c['core_lower'],
            extra_adaptive_core_budget_if_lemma_accepted=delta,
            extra_adaptive_pure_bus_budget_if_lemma_accepted=bus_delta,
            veto_threshold_if_lemma_accepted=max(F(0),delta)/c['extra_veto_core_slope'],
            whole_hardware_gain=None,independently_accepted=False),
        application_separate=dict(reads_per_s=app_reads,writes_per_s=F(0),
            full_read_core_upper=app_reads*s['upper']['app_read']/NS,
            payload_two_beats_nominal_fraction=app_reads*2*cfg['service']['read_beat_ns']/NS,
            common_ECC_extra_read_beat_plus_decode_nominal_fraction=app_reads*(cfg['service']['read_beat_ns']+s['decode'])/NS,
            meaning='last two nominal parts sum to nominal external39 read; clock/jitter retained in full upper'),
        common_fixed_code=dict(active_check_bits=7*cfg['words'],padding_bits=9*cfg['words'],
            allocated_word_bits=48,allocated_memory_bytes=6*cfg['words'],
            initialization_encodes=cfg['words'],initialization_write_beats=3*cfg['words'],
            initialization_turnarounds=cfg['words'],
            initialization_CPU_ns=None,initialization_energy_J=None),
        timing=cmp.timing(cfg,39,selected['k']),
        old_131s_case=dict(period_s=old_period,OFF_by_code=off,
            meaning='rewriting alone does not prove OFF for fixed t1; sufficient upper above epsilon is not exclusion'),
        physical_Q=None,new_hardware=False,
        provenance=dict(frozen_files=len(manifest['sha256']),input_unchanged=encoded(cfg)==original))
    if encoded(cfg)!=original:
        raise AssertionError('Accepted configuration mutated')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--compute',action='store_true'); group.add_argument('--check',action='store_true')
    group.add_argument('--assemble',action='store_true',help='rewrite accounts from existing certificates, without reintegration')
    args=parser.parse_args(); OUT.mkdir(exist_ok=True)
    result=run(args.compute); payload=encoded(result); target=OUT/'result.json'
    if args.compute or args.assemble:
        target.write_bytes(payload)
    elif target.read_bytes()!=payload:
        raise AssertionError('Exact replay mismatch')
    print(json.dumps(dict(selected_k=result['selected_k'],
        comparison={k:float(v) if isinstance(v,F) else v for k,v in result['comparison'].items()},
        sha256=hashlib.sha256(payload).hexdigest()),indent=2),flush=True)
