"""Two C3 rows only at 0.25 MiB, conditional on the published C2 check."""
import argparse
from fractions import Fraction as F
import json
from math import ceil
from pathlib import Path
import numpy as np
from observations import HERE,T,WIDTH,setup
from strict import G_MAIN,G_STRICT,START
from datetime import datetime

C2_HANDOFF='https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/186#issuecomment-6744394993'
NS=10**9


def c3(args):
    common,_=setup(args.common,args.previous)
    from fixed_six import calculate
    from coverage import environment
    from sepem import empirical
    old=json.loads((common/'six.json').read_text(encoding='utf-8'))
    reproduced=calculate(args.previous)
    assert json.loads(json.dumps(reproduced,default=str))==old
    U=F(json.loads((HERE/'variation.json').read_text(encoding='utf-8'))['quota_exact'])
    env,mission,Fsun=environment();R=env['B']-env['b'];B=env['B'];tau=Fsun/R
    assert U>R and tau==F(old['plateau_s']) and (mission-tau)*env['b']**2+tau*B*B==F(old['S2_max'])
    row=next(r for r in reproduced['rows'] if r['W']==65536 and r['epsilon']==F(1,1000))
    w=row['W'];eps=row['epsilon'];L=F(196*w,NS);D=old['D'];c=F(39,D);lam=c*B
    xp=F(100001,100000);xm=F(99999,100000);j=F(1,2*NS);E=124*xp/NS+3*j;delta=F(old['delta_exec'])

    def physical_floor(block,free):
        assert w*lam*block<1
        z=(tau//block)*(1-w*lam*block)*F(38,78)*lam**2*free
        return z/(1+z)
    h1floor=physical_floor(32*L,5*w*(4*L-E)**2)
    at_h={str(h):physical_floor(64*h*L,13*w*(4*h*L-E)**2) for h in range(2,7)}
    block=128*L;k=ceil((block+E)/(7*L))
    assert k==19
    at_h['>=7']=physical_floor(block,w*(block-k*E)**2/(k+1))
    assert min(at_h.values())>eps and F('0.000502197')<h1floor<eps
    # h=1 requires D_o + I_o <= L. Use the outer D_o=L in both bounds.
    H=4*xp*L+2*j;fast=xp*L+2*j;fast_min=xm*L-2*j;slow_min=4*xm*L-2*j
    peak_scan=xp*L+j;dstar=xm*L
    M=H//dstar+1;Nstar=ceil((mission+2*j)/dstar)+2
    accum=w*c**2*((H+M*fast/2)*reproduced['S2_max']+2*j*Nstar*H*B**2)
    q=min(F(1),delta+accum)  # (6), stop probability used consistently below
    Do_min=L-F(420,NS)
    edges=(tau-3*L)//(4*L)-1
    Vfloor=edges*w*lam**2*(F(1,2)*(4*L)**2+Do_min*4*L)
    early=1-3*w*lam*L
    assert Vfloor>F('0.001305143') and early>F('0.98') and q>eps
    const=row['candidate']['price']['bus']
    lowread=(1-eps-delta)*w*(mission/H-2)*(48*xm/NS-j)
    opportunity=const['upper_s']-lowread
    assert opportunity>0 and opportunity/const['upper_s']<F('0.025544')
    # Formula (10); eta is the expected count of invalid/late/false restarts.
    nt=2*w*c*reproduced['S1_max']
    max_commands=2+ceil(mission/fast_min); all_reads=row['necessary']['maximum_reads_upper']
    coeff_sec=2*fast
    Tbase=peak_scan+2*fast*(1+nt)+mission*q
    Sbase=1+2*nt+max_commands*q
    def prices(time_fast):
        visits=min(all_reads,w*(2+mission/slow_min+(1/fast_min-1/slow_min)*time_fast))
        repairs=min(visits,nt+q*all_reads)
        bus=visits*(48*xp/NS+j)+repairs*(56*xp/NS+j)
        serial=visits*(68*xp/NS+j)+repairs*(56*xp/NS+j)
        return {'reads_upper':visits,'repairs_upper':repairs,'bus_upper_s':bus,'bus_upper_percent':100*bus/mission,
                'serial_upper_s':serial,'serial_upper_percent':100*serial/mission}
    strict=json.loads((HERE/'strict.json').read_text(encoding='utf-8'))
    with np.load(args.windows) as f:s1=f['S1']
    r=T*float(reproduced['S2_max'])/s1**2
    keep=np.zeros(len(s1),dtype=bool)
    for x,_,n in strict['SEPEM']['strict5']['ranges_valid_starts_inclusive']:
        start=int((datetime.fromisoformat(x)-START).total_seconds())//300
        keep[start:start+n]=True
    outputs=[]
    for label,quota in [('main_positive_variation',U),('A',None)]:
        outputs.append({'class':label,'volume_MiB':F(1,4),'epsilon':eps,'g_s_inv2':G_MAIN,'J_quota_s_inv':quota,
            'psi':{'baseline_direct_lifetime_upper':0,'direct_sensitivity':[F(1,100000),F(1,10000)],
                   'coordinate_marginals':'bounded by nu/D; full singleton law included for witness',
                   'K_overlap_registration_and_burst':'physical joint tail, subset visibility and queue budgets conditional'},
            'plateau_in_class':True,'S2_max':reproduced['S2_max'],'k_class':mission*reproduced['S2_max']/reproduced['S1_max']**2,
            'R_on_all_SEPEM_window_S1':empirical(r),
            'fixed_lower_bus_s':row['necessary']['bus_lower_s'],'fixed_candidate_bus_upper_s':const['upper_s'],
            'fixed_candidate_Q_upper':row['candidate']['risk']['total'],
            'policy_h1':{'early_false_slow_lower':early,'V_without_stop_lower':Vfloor,'Q_upper_eq6':q,
                         'Q_physical_sup_lower':h1floor,'admissibility':'open; both tests fail',
                         'conditional_mandatory_bus_lower_s':lowread,'savings_upper_s_if_admissible':opportunity,
                         'savings_upper_pp_if_admissible':100*opportunity/mission,
                         'relative_savings_upper_percent':100*opportunity/const['upper_s'],
                         'E_fast_time_upper_intercept_s':Tbase,'E_fast_time_s_per_eta':coeff_sec,
                         'fast_fraction_upper_at_eta_zero':Tbase/mission,'switch_upper_intercept':Sbase,
                         'switch_upper_per_eta':2,'hard_maximum_commands':max_commands,
                         'restart_bound_before_stops_without_eta':nt,'charge_post_stop_q':q,
                         'prices_at_eta_zero':prices(min(mission,Tbase)),'prices_at_unbounded_eta':prices(mission),
                         'empty_valid_nominal_history':{'switches':1,'fast_until':'D_o+2L','Tfast_upper_s':3*L},
                         'persistent_invalid_history':{'switches':0,'Tfast_s':mission},
                         'peak_1ms':row['peak'],'Tfast_fraction_cap':1},
            'other_h_physical_floors':at_h,'strict_sensitivity':{'g_s_inv2':G_STRICT,'same_plateau_bounds':True,
               'joint_SEPEM_windows':int(keep.sum()),'R_on_passing_windows':empirical(r[keep])}})
    return {'freeze':'d8eb9e4192cfaa7e37182ab87a4794dd2e2708cf','C2_path':C2_HANDOFF,'source_formulae':'PR420 (6),(9),(10), PR424 (B)–(E), PR424 acceptance',
          'inputs':{'T':mission,'L_s':L,'F':Fsun,'tau_s':tau,'R':R,'delta_exec':delta,'direct_default':0},
          'transferred_fixed_rows':[{'MiB':r['MiB'],'epsilon':r['epsilon'],'k':r['candidate']['k'] if r['candidate'] else None,
                'necessary_bus_s':r['necessary']['bus_lower_s'],'sufficient_bus_s':r['candidate']['price']['bus']['upper_s'] if r['candidate'] else None,
                'status':r['status']} for r in reproduced['rows']],
          'rows':outputs}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for k in ('common','previous','windows'):p.add_argument('--'+k,required=True,type=Path)
    p.add_argument('--check',action='store_true');args=p.parse_args();result=c3(args)
    data=json.dumps(result,default=str,indent=2,ensure_ascii=False,allow_nan=False)+'\n'
    path=HERE/'comparison.json'
    if args.check:
        if data!=path.read_text(encoding='utf-8'):raise SystemExit('Mismatch: '+path.name)
    else:path.write_text(data,encoding='utf-8',newline='\n')
    print('PASS: six fixed rows transfer; exactly two C3 rows at W=65536')
