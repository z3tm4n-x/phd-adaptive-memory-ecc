#!/usr/bin/env python3
"""T367: one frozen point after the word-phase lemma (commit e5b610d).

Reuse the accepted scalar E3 search and C3 accounting without changing its
source. Its old 'weak' field is only an adapter for the total pair-bound
constant, now justified by R2-R5 for the SAME auxiliary break. Neither
P_obs in the observation test nor P_obs in the parent window is replaced.
No call to the old six-point calculate(), no rival optimization.
"""
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
import importlib.util
import json
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OLD = ROOT / 'theory/observation-volume-20261101'
spec = importlib.util.spec_from_file_location('accepted_volume', OLD/'check.py')
v = importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)
EPS, W = F('0.01'), 1048576


def fixed_k(b, k):
    """Boundary verification at this same point, using the registered rule."""
    threshold = F(v.I(F(b.n)/(EPS/20)).ln().hi)
    low, high = F(0), b.R-b.g*b.hhi
    if v.SCORE*b.exposure(high,k)-v.ETA*b.c <= threshold+F(1,10**6):
        return None
    for _ in range(66):
        mid=(low+high)/2
        if v.SCORE*b.exposure(mid,k)-v.ETA*b.c > threshold+F(1,10**6):
            high=mid
        else:
            low=mid
    u=F(v.ceil(high*10**12),10**12)
    U=u+b.g*b.hhi
    ab=b.duration(k)
    ks=b.round_k(min(b.kcell-2,int((ab*b.R/U-v.J)/b.bhi)))
    if ks<k or U>=b.R:
        return None
    ar=b.duration(ks)
    qp=(ar*b.cp+ab*b.R*b.Fr)/(2*b.w)
    return dict(k_base=k,k_rare=ks,u=u,U=U,Q_upper=v.DELTA0+v.DELTAC+EPS/20+b.weak+qp)


def calculate():
    b=v.Bank(W)
    old_carry=b.weak
    q_ap=b.B*b.dE*b.mass/W
    # Local adapter to the unchanged accepted scalar routine; R2-R5 are essential.
    b.weak=q_ap
    a=b.tune(EPS)
    saved=json.loads((OLD/'result.json').read_text(encoding='utf-8'))
    old_row=saved['banks'][1]['rows'][1]
    assert F(old_row['epsilon'])==EPS
    assert old_row['adaptive']['status']=='E5_UNRESOLVED'
    assert old_carry==F(old_row['adaptive']['residual_upper'])
    geom=saved['banks'][1]['geometry']
    assert b.p==F(geom['P_obs']) and b.c==32 and b.kcell==3001
    assert b.llo==F(geom['history_lower_s']) and b.lhi==F(geom['history_upper_s'])
    result=dict(task=367,scientific_base='75fc66711fffeea30dd79d902f12c2b58600e57c',
                base_main='e15708b51e6d32460af8202b48d2c25fae5029c8',
                pre_application_lemma_commit='e5b610d',
                frozen=dict(words=W,alpha=F(1,2),epsilon=EPS,mission_s=v.T,
                            m=v.M,K=b.kcell,c=b.c,eta=v.ETA,
                            delta0=v.DELTA0,deltaC_design=v.DELTAC,alpha_total=EPS/20),
                geometry=dict(P_obs=b.p,operation_aperture_s=b.dE,block_s=b.block,
                              H_lower=b.hlo,H_upper=b.hhi,history_lower_s=b.llo,
                              history_upper_s=b.lhi,attempts_upper=b.n,
                              completed_cells_lower=b.nfull,
                              gate_budget_after_10us_s=b.gate_budget),
                refinement=dict(old_action_carry_upper=old_carry,new_aperture_pairs_upper=q_ap,
                                old_over_new=old_carry/q_ap,
                                parent_mass_upper=b.mass,known_p_squared=b.ip,
                                known_parent_window_upper=b.mu_p),
                old_rival_bounds_used_verbatim=old_row['rivals'])
    # Remove the legacy diagnostic asking how small P_obs would have to be.
    a.pop('P_obs_needed_from_residual_budget',None)
    a['aperture_pair_upper']=a.pop('residual_upper')
    if 'Q_upper' in a:
        a['word_interval_pair_upper']=a.pop('pair_within_upper')
        a['q0_for_break_observation_and_cost']=EPS/20+q_ap+a['word_interval_pair_upper']
        a['semantic_status']='conditional bound on the same auxiliary break; not physical-only'
        k=a['k_base']
        local=fixed_k(b,k)
        assert local is not None
        for key in ('k_base','k_rare','u','U','Q_upper'):
            assert local[key]==a[key],key
        next_k=next((x for x in range(k+1,b.kcell-1) if b.legal_k(x)),None)
        next_row=fixed_k(b,next_k) if next_k is not None else None
        assert next_row is None or next_row['Q_upper']>EPS
        result['scalar_boundary_check']=dict(selected=local,next_legal=next_row)
        for x,c in a['costs'].items():
            c['strict_full_cost_budget']={}
            for j in ('schedule','constant'):
                lower=F(old_row['rivals']['costs'][x][j]['with_common_lower'])
                c['strict_full_cost_budget'][j]=lower-c['with_common_upper']
    else:
        assert 'costs' not in a  # No economics without a full sufficient Q test.
    result['application']=a
    paths=list(v.SOURCES)+[
        'theory/observation-volume-20261101.md',
        'theory/observation-volume-20261101/check.py',
        'theory/observation-volume-20261101/result.json',
        'docs/scientific_reviews/OBSERVATION_VOLUME_20261101.md',
        'experiments/t186-method-comparison/code-strength/SERVICE.md']
    result['sources_sha256_LF']={p:v.digest(p) for p in paths}
    result['checker_sha256_LF']=sha256(Path(__file__).read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    return result


def summarize(result):
    a=result['application']
    print('ONE POINT: W=1048576, alpha=1/2, epsilon=1/100;',a['status'])
    print('q_ap <=',v.decimal(a['aperture_pair_upper']))
    if 'Q_upper' in a:
        for name in ('k_base','k_rare','u','U','U_over_R','Q_upper','risk_margin',
                     'q0_for_break_observation_and_cost','D0_upper',
                     'rare_fraction_lower_before_extra_z'):
            print(name,v.decimal(a[name],up=name not in ('risk_margin','rare_fraction_lower_before_extra_z')))
        for x,c in a['costs'].items():
            print(x,'V us/s',v.decimal(10**6*c['V_at_deltaC_design']),
                  'budget S/F us/s',{j:v.decimal(10**6*y,False) for j,y in c['strict_full_cost_budget'].items()})
            print(x,'extras per second', {n:v.decimal(10**6*c[n]) for n in ('A_z','A_G_rate','C_escape')})


if __name__=='__main__':
    result=calculate()
    encoded=json.dumps(result,default=str,ensure_ascii=False,sort_keys=True,indent=2)+'\n'
    dest=HERE/'result.json'
    if '--write' in sys.argv:
        dest.write_text(encoded,encoding='utf-8',newline='\n')
    else:
        assert dest.read_text(encoding='utf-8')==encoded,'saved result differs'
    summarize(result)
    print('PASS: one registered application; accepted source files remain read-only.')
