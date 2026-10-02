"""Independent Decimal90 equations and addressed B5--B7 diagnostics."""
from decimal import Decimal as D,localcontext
from fractions import Fraction as F
import copy
import itertools
from types import SimpleNamespace

import t80_joint as j
import t80_engine as old
from timing import minimum_resource_g,min_ticks


def dec(x):
    x=F(x);return D(x.numerator)/D(x.denominator)


def context_for(r,ps):
    return dict(next(p for p in ps if p['set']==r['set_representative'] and p['architecture']==r['architecture']
                     and p['shield']==r['shield'] and p['margin']==r['margin']),mode=r['mode'])


def validate(ev,ps):
    counts=dict(risk=0,LOW=0,price=0,resource=0);max_error=D(0)
    with localcontext() as ctx:
        ctx.prec=90
        def primitive(x,bU,t):
            l=D('.001');rho=D('.048')
            if x<=bU:return D(0)
            H=lambda y:y/l if y<=l else 1+(y/l).ln()
            v=min(t,(H(x)-H(bU))/rho)
            if x<=l:return (x-bU)*v-rho*l*v*v/2
            te=(x/l).ln()/rho
            v1=min(v,te);v2=min(max(D(0),v-te),1/rho)
            return x/rho*(1-(-rho*v1).exp())+l*(v2-rho*v2*v2/2)-bU*v
        for r in ev.records:
            if r['status']!='certified_conditional':continue
            p=context_for(r,ps)
            b,B,T,Ps,S2,FS=(dec(p[k]) for k in ('b','B','T','Ps','S2','FS'))
            vc=dec(r['vc']);ka=D(r['ka']);Pl=ka*Ps
            beta=D(p['n']-1)/(2*p['n']*p['W'])
            u=(Ps+Pl)*b*b
            v=max((Ps+Pl)*(vc+b),(Ps*B*B-u)/(B-b),D(0))
            V=min(vc*vc*T,b*b*T+(vc+b)*FS)
            Q=min(Ps*S2+Pl*V,Pl*S2,u*T+v*FS)
            risk=dec(old.errors(p['q'],p['mode']))+dec(p['Dstar'])+p['K']*B*Ps/p['W']+beta*Q
            assert abs(risk-dec(r['risk_upper']))<D('1e-75')
            assert risk<=dec(p['eps']);counts['risk']+=1
            wm,wp=dec(r['wm']),dec(r['wp']);bU=D(0) if r['kind']=='total_load' else b
            if r['low_type']=='direct-fast':
                hf=dec(r['hF_max'])
                mass=max(D(0),primitive(vc,bU,hf)-primitive(vc,bU,hf-wm))
            else:
                qr=dec(r['qratio'])*b;h0=wm*(1-1/D(r['divisor']))
                t=min(h0,max(D(0),(qr-bU)/D('.000048')))
                mass=max(D(0),(qr-bU)*t-D('.000048')*t*t/2)
            assert dec(r['mass_lower'])<=mass+D('1e-80')
            assert dec(r['mass_upper'])>=mass-D('1e-80')
            z=dec(r['z']);am=dec(r['aM']);H=D(r['H']);k=D(r['k'])
            assert am*(1-(-z).exp())*mass-z*k>=H
            assert D(r['J'])*(-H).exp()<=dec(p['q']['alpha_M'])
            counts['LOW']+=1
            # Independent full price: exact same declared tail upper is input.
            cf=dec(p['cp'])/dec(p['gm']);cs=cf/ka
            DE,DM=dec(r['DE']),dec(r['DM']);CX=dec(r['channel_rate']);sig=dec(r['sigmaX'])
            pq=min(D(1),dec(old.errors(p['q'],p['mode'],False))+dec(p['Dstar'])+
                   p['K']*b*Ps/p['W']+beta*Pl*b*b*T)
            flags=DE*(b+dec(p['rF'])+dec(p['rloss']))
            bad=dec(r['pM_upper'])+D('1e-9')
            whole=(DM+DE*p['K'])/T+flags+D(r['J'])*DM/T*bad+pq
            ex=(2*dec(p['cp'])+sig)/T+CX
            quiet=min(cf+ex,cs+cf*min(D(1),whole)+ex)
            TQ=D('.9')*T;KQ=D(1000)
            bound=(DM*KQ+DE*(p['K']+KQ*B*(Pl+dec(p['dE']))))/TQ
            freq=1/dec(r['Delta_m'])+2*KQ*wp/(dec(r['Delta_m'])*TQ)+2*KQ/TQ
            exq=(2*dec(p['cp'])+sig)*KQ/TQ+CX
            ret=min(cf+exq,cs+cf*min(D(1),bound+flags+DM*freq*bad+min(D(1),risk))+exq)
            for actual,key in ((quiet,'quiet_upper'),(ret,'returns_upper')):
                err=abs(actual-dec(r[key]));max_error=max(max_error,err)
                assert err<D('1e-70'),(r['id'],key,err)
            counts['price']+=1
            assert dec(r['peak_upper'])<=D('.8')
            assert (1+dec(r['margin']))*dec(r['delay_upper_s'])<=D('3e-6')
            counts['resource']+=1
    return dict(precision=90,points=sum(counts.values()),rows=counts['risk'],counts=counts,
                maximum_price_difference=str(max_error),comparison_tolerance='1e-70',
                independent_formulas=True,physical_qualification=False)


def repair_service(p,joint_upper):
    """One separately labelled sufficient requirement, never a changed baseline."""
    q=copy.deepcopy(p)
    c=min_ticks(joint_upper,p['margin'],p['tm'])
    q['cfg']['service']['c_ticks']=q['cfg']['service']['fence_ticks']=c
    g=minimum_resource_g(q['cfg'],p['margin']);q['cfg']['service']['g_ticks']=g
    q.update(c=c,g=g,cp=c*p['tp'],cm=c*p['tm'],gm=g*p['tm'],gp=g*p['tp'],f=c*p['tp'],
             gap=(2*g-c)*p['tp'],Ps=p['W']*g*p['tp'])
    return j.cadence_context(q,2)


def diagnostics(out,ev,ps,selected,csv_write,json_write):
    ids=sorted({r[tag+'_id'] for r in selected for tag in ('joint_reset','direct','reset_addressed','direct_addressed')
                if r[tag+'_id'] is not None})
    # B6 requirements at the addressed fractions must not disappear just
    # because their unchanged-aM cost is worse than the half-window cap.
    ids=sorted(set(ids)|{r['id'] for r in ev.records if r['status']=='certified_conditional'
        and r['low_type']=='reset-slow' and r['divisor'] in (8,32) and r['aM']==10**6
        and r['w']==r['d']==1 and r['qratio']==2 and r['rho_e']==F('1e-6') and r['DQ']==300})
    rows=[];quantiles={};changes=[]
    for rid in ids:
        r=ev.records[rid];p=j.cadence_context(context_for(r,ps),r['divisor'])
        m=j.window(p,r['aM'],r['w'],r['d'],r['qratio'],r['kind'],r['divisor']);m['b_nom']=p['b']
        target=r['pstar']
        row=dict(calculation_id=rid,low_type=r['low_type'],divisor=r['divisor'],
                 pstar_whole=r['pstar_whole'],pstar_return=r['pstar_return'],
                 mu_upper=r['mu_upper'],k_safe=r['k'],target=target,
                 base_tax=r['base_tax'],return_boundary=r['return_boundary'],
                 return_global_component=r['return_global_component'],channel_rate=r['channel_rate'])
        if 0<target<1:
            key=(m['mu'],target)
            if key not in quantiles:quantiles[key]=j.k_price_exact(*key)
            kp=quantiles[key]
            tail=j.poisson_tail_exact(m['mu'],kp);prev=j.poisson_tail_exact(m['mu'],kp-1)
            row.update(k_price=kp,tail_at_price_lower=F(tail.lo),tail_at_price_upper=F(tail.hi),
                       tail_previous_lower=F(prev.lo),exact_price_compatible=kp<=r['k'])
            trials=[j.requirement_B7(m,r['mass_lower'],target,z,y) for z,y in
                    itertools.product(map(F,old.FAMILY['z']),repeat=2)]
            good=[v for v in trials if v['status']=='sufficient']
            if good:
                req=min(good,key=lambda v:v['a_suff_upper'])
                anew=F(j.t58.ceil(req['a_suff_upper']))
                nm=j.window(p,anew,r['w'],r['d'],r['qratio'],r['kind'],r['divisor'])
                tested=j.evaluate(p,nm,r['ka'],r['vc'],r['low_type'],F(r['DQ'] or 0),
                                  theta=r['theta'],rho_e=r['rho_e'],vc_kind=r['vc_kind'])
                row.update(req,a_tested=anew,changed_channel_is_requirement=True,
                           retested_risk=tested.get('risk_upper'),retested_whole=tested.get('quiet_upper'),
                           retested_return=tested.get('returns_upper'),retested_goal=tested.get('full_goal_pass'),
                           retested_k=tested.get('k'),retested_mu=nm['mu'],
                           retested_counter_bits=(tested['k']+1).bit_length())
                assert tested.get('full_goal_pass'),(rid,anew,tested)
                checked=dict(r)|tested|{'aM':anew}
                changes.append(dict(kind='B7_channel',calculation_id=rid,
                    **validate(SimpleNamespace(records=[checked]),[p])))
            else:row['status']='nonpositive_contrast_for_registered_z_y'
        else:row['status']='price_ceiling_before_false_alerts' if target<=0 else 'no_tail_restriction'
        rows.append(row)
    csv_write(out/'threshold_requirements.csv',rows)
    # Localize failed short gates and check ONE explicit service requirement
    # for each. No cadence/environment/direct tuning accompanies the change.
    repairs=[]
    failures={(r['context_id'],r['mode']) for r in selected if not r['direct_addressed_goal']}
    for ci,p0 in enumerate(ps):
        for mode in ('combined','monitor-only'):
            if (ci,mode) not in failures:continue
            p=dict(p0,mode=mode)
            gate=old.short_gate(p,mode)
            required=F('80e-9')
            q=repair_service(p,required)
            m=j.window(q,F(10**6),F(1),F(1),F(2),'total_load',2)
            r=j.best_direct(q,m)
            from run_t80 import fixed_row
            fixed=fixed_row(q)
            checked=dict(set_representative=q['set'],architecture=q['architecture'],shield=q['shield'],
                         margin=q['margin'],mode=mode,kind='total_load',qratio=F(2),
                         divisor=2,aM=F(10**6),wm=m['wm'],wp=m['wp'],Delta_m=m['Delta_m'],
                         hF_max=m['hF_max'],peak_upper=q['resource']['peak'],delay_upper_s=q['resource']['delay'])|r
            assert r['full_goal_pass'] and q['cadence_pass']
            changes.append(dict(kind='U_80ns',context_id=ci,mode=mode,**validate(SimpleNamespace(records=[checked]),[q])))
            original=[r for r in selected if r['context_id']==ci and r['mode']==mode and r['kind']=='total_load'][0]
            br=None if original['direct_addressed_id'] is None else ev.records[original['direct_addressed_id']]
            repairs.append(dict(context_id=ci,**old.ident(p),mode=mode,original_short_risk=gate['short_risk_upper'],
                obstruction='short_risk' if not gate['short_pass'] else 'price',
                original_price=None if br is None else br['objective'],
                original_base_tax=None if br is None else br['base_tax'],
                required_joint_upper_s=required,required_c=q['c'],required_g=q['g'],
                fixed_M=fixed['fixed_strong_M'],fixed_cost_lower=fixed['fixed_cost_lower'],
                fixed_resource_ok=fixed['fixed_resource_ok'],
                source_upper_s=F('90e-9') if p['architecture']=='internal38' else F('240.5120006e-9'),
                Dstar_unchanged=p['Dstar'],quotas_unchanged=True,physics_qualified=False,
                aM=10**6,w=1,d=1,qratio=2,kind='total_load',
                resulting_peak=q['resource']['peak'],resulting_delay=q['resource']['delay'],
                service_margin=q['cm']/required-1,**r))
    csv_write(out/'service_requirements.csv',repairs)
    # Coefficient constraints for actual interface cost are not measurements.
    interface=[]
    for ci,p in enumerate(ps):
        for div in (2,8,32):
            q=j.cadence_context(dict(p,mode='combined'),div)
            interface.append(dict(context_id=ci,**old.ident(p),divisor=div,CX_required_upper=q['CX'],
                sigmaX_required_upper=q['sigmaX'],ring_counters=div+1,cadence_s_for_w1=F(1,div),
                peak_upper=q['resource']['peak'],delay_upper_s=q['resource']['delay'],
                resource_pass=q['cadence_pass'],physical_extra_cost=None,physical_interface=False,
                g_unchanged=p['g'],qualified_monitor_aM=None,ERR_lower=None,joint_WCET=None))
    csv_write(out/'interface_requirements.csv',interface)
    counter_rows=[]
    for rid in ids:
        r=ev.records[rid]
        bits=(r['k']+1).bit_length()
        counter_rows.append(dict(calculation_id=rid,k=r['k'],subwindow_saturate_at=r['k']+1,
            bits_per_subwindow=bits,ring_counters=r['divisor']+1,
            ring_payload_bytes=((bits+7)//8)*(r['divisor']+1),mission_index_bits=r['J'].bit_length(),
            deadline_ticks=r['dticks'],max_message_spacing_s=r['Delta_m'],
            late_missing_overflow='S; never a zero count',physical_native_cadence=False,
            scope='bounded software sufficient-statistic storage, not LUTs or instrument capacity'))
    csv_write(out/'counter_requirements.csv',counter_rows)
    json_write(out/'sufficient_change_checks.json',dict(points=sum(r['points'] for r in changes),checks=changes))
