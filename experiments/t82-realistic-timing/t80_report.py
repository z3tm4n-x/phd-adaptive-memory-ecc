"""Tables/figures from T80 outputs, with addressed repairs (no new grid)."""
from __future__ import annotations

import csv
from fractions import Fraction as F
import gzip
import json
import lzma

from t80_engine import (FAMILY, CONFIG, PROFILE, source_check, context, ident,
                       monitor_window, threshold, lease, monitor_candidate, choose_monitor,
                       short_gate, t58, min_ticks)
from timing import resources, service_upper


def read_rows(path):
    opener = lzma.open if path.suffix=='.xz' else gzip.open if path.suffix=='.gz' else open
    with opener(path,'rt',encoding='utf-8',newline='') as stream:
        yield from csv.DictReader(stream)


def hard_tax(p, returns=False):
    # T80 (11) all-history mask, evaluated at the whole horizon. Not a new
    # probability formula. For returns use the separate per-interval edge.
    T = p['T']
    if returns:
        return p['cp']/p['gm']+p['CX']+(2*p['cp']+p['sigmaX'])*1000/(F('.9')*T)
    return (t58.mask_bound(2*p['cp'],2*p['gm'],T)+p['sigmaX']+p['CX']*T)/T


def timing_rows(ps):
    rows=[]
    for i,p in enumerate(ps):
        m=p['margin'];s=p['cfg']['service'];r=p['cfg']['resources']
        cu=service_upper('internal38_nominal_projection' if p['architecture']=='internal38' else 'external39_resource_projection')
        sources=[('U',p['cm'],cu,'nominal basis, joint upper unknown' if p['architecture']=='internal38' else 'existing conditional executor'),
                 ('gate',p['G']*p['tm'],F(r['application_max_request_s'])+F(s['gate_logic_wcet_s']),'T73 conditional joint guard'),
                 ('ERR',p['cfg']['t82_timing']['ERR_budget_ticks']*p['tm'],F(p['cfg']['t82_timing']['ERR_actual_upper_s']),'conditional 1us upper'),
                 ('app',F('.000003'),p['resource']['delay'],'FIFO bound (11)')]
        for d in map(F,FAMILY['delivery_compute_s']):
            sources.append((f'monitor_d={d}',min_ticks(d,m,p['tm'])*p['tm'],d,'declared diagnostic delivery+compute upper'))
        for label,A,C,source in sources:
            rows.append(dict(context_id=i,test=label,available_min_s=A,execution_upper_or_basis_s=C,
                             absolute_slack_s=A-C,relative_slack=A/C-1,required_margin=m,
                             margin_slack_s=A-(1+m)*C,admissible_upper_s=A/(1+m),source=source,
                             overhead_available_s=A/(1+m)-cu if label=='U' else None,
                             physical_qualification=False))
        prev=resources(p['cfg'],p['g']-1)
        rows.append(dict(context_id=i,test='previous_g',previous_g=p['g']-1,
                         previous_peak_upper=prev['peak'],previous_delay_upper_s=prev['delay'],
                         previous_pass=prev['ok'] and (1+m)*prev['delay']<=F('.000003')))
    return rows


def addressed_repairs(p):
    """One fixed T73/3/10% slice, no optimizing across environment classes."""
    rows=[];rho,DQ=F('.000001'),F(300)
    for kind in FAMILY['monitor_types']:
        for w in (F(60),F(300)):
            m=monitor_window(p,F(1000),w,F(1),F(2),kind)
            th=threshold(m,F(1));need=th['aM_for_k0']
            m2=monitor_window(p,need,w,F(1),F(2),kind)
            th2=threshold(m2,F(1));le=lease(p,m2,rho,F('0.015625'))
            after=monitor_candidate(p,m2,th2,le,DQ,'combined')
            rows.append(dict(condition='LOW k>=0',kind=kind,w=w,before_k=th['k'],value=m['mR'],
                sufficient_change='increase aM to the stated bound; same A_M/a_M and noise',
                parameter='aM',required=need,after_k=th2['k'],
                price_upper=min(after['quiet_upper'],hard_tax(p)),
                formula8_price_upper=after['quiet_upper'],remaining='quiet tax still fails; first condition only repaired'))
    m=monitor_window(p,F(10**6),F(300),F(60),F(2),'total_load')
    le=lease(p,m,F('.048'),F('.015625'))
    possible=[F(r) for r in FAMILY['rho_e_per_s_separate_classes']
              if lease(p,m,F(r),F('.015625'))['lease_slack_s']>=0]
    slower=max(possible)
    after=choose_monitor(p,F(10**6),F(300),F(60),F(2),slower,DQ,'total_load','combined')
    rows.append(dict(condition='LOW delay with margin',kind='total_load',w=300,
                     value=le['lease_min_s'],required_deadline_s=(1+p['margin'])*le['coverage_upper_s'],
                     sufficient_change='qualify the stated SLOW ENTRY class after DQ, retrospective rho_b unchanged',
                     parameter='rho_e',required=slower,price_upper=min(after['quiet_upper'],hard_tax(p)),
                     remaining='different declared environment class; original quiet tax still fails'))
    zero=monitor_window(p,F(10**6),F(60),F(1),F(1),'solar_plus_upper_unobserved_load')
    after=choose_monitor(p,F(10**6),F(60),F(1),F(2),rho,DQ,zero['kind'],'combined')
    rows.append(dict(condition='qR=bU gives zero retrospective exposure',kind=zero['kind'],w=60,value=zero['mR'],
                     sufficient_change='qualify qR=2*bbar reset class, not only increase aM',parameter='qR',required=2*p['b'],
                     price_upper=min(after['quiet_upper'],hard_tax(p)),remaining='different environment class; quiet tax still fails'))
    # An ADDITIONAL solar quiet spectrum is permitted by T80 B.2/V.2.
    # Solve the one stated requirement; do not silently substitute it into
    # the primary grid/original quiet class or claim it is a real instrument.
    for w in (F(60),F(300)):
        m=monitor_window(p,F(10**6),w,F(1),F(2),'solar_plus_upper_unobserved_load')
        th=threshold(m,F(1));le=lease(p,m,rho,F('0.015625'))
        original=monitor_candidate(p,m,th,le,DQ,'combined')
        def with_mean(mu):
            x=max(F(0),th['k']-mu)
            ex=x*x/(2*(mu+x/3)) if x else F(0)
            pt=t58.exp_neg(ex)[1] if x else F(1)
            return monitor_candidate(p,m,th|{'pM_upper':pt},le,DQ,'combined')
        lo=F(PROFILE['eta_per_s'])*m['wp'];hi=m['mu']
        lowest=with_mean(lo)
        if max(lowest['quiet_upper'],lowest['returns_upper'])>F('.01'):
            rows.append(dict(condition='quiet and return price',w=w,value=original['quiet_upper'],
                             sufficient_change='channel-only change insufficient at this calendar',price_upper=lowest['quiet_upper']))
            continue
        for _ in range(50):
            mid=(lo+hi)/2;result=with_mean(mid)
            if max(result['quiet_upper'],result['returns_upper'])<=F('.01'):lo=mid
            else:hi=mid
        repaired=with_mean(lo);next_bad=with_mean(hi)
        rows.append(dict(condition='quiet/return tax',kind=m['kind'],w=w,value=original['quiet_upper'],
                         sufficient_change='ADDITIONAL quiet solar contract, NOT original nu<=bnom class',
                         parameter='s_nom_upper_per_s',required=(lo/m['wp']-F(PROFILE['eta_per_s']))/m['aM'],
                         mu_before_upper=m['mu'],mu_required_upper=lo,
                         price_upper=repaired['quiet_upper'],returns_upper=repaired['returns_upper'],
                         next_mu_upper=hi,next_price_max=max(next_bad['quiet_upper'],next_bad['returns_upper']),
                         unchanged_risk_upper=repaired['risk_upper'],remaining='new quiet-spectrum input unqualified; no result for original quiet metric'))
    # One addressed execution requirement for the displayed ERR point,
    # NOT an added c/g search or a proposed hardware implementation.
    from t80_err import majorant,err_price
    from t80_engine import errors
    ka,h=13,F(120)
    changed=p|dict(c=13,cp=13*p['tp'],cm=13*p['tm'],f=13*p['tp'],gap=(2*p['g']-13)*p['tp'])
    Pl=ka*p['Ps'];tau=Pl+p['dE'];r0=tau+Pl+p['Gp']+changed['f'];r1=h+Pl+p['Gp']+changed['f']
    maj=majorant(p['B'],p['b'],p['T'],p['FS'],p['S2'],F(p['W']-1,p['W']),r0,r1)
    gate=short_gate(p,'ERR-only')
    risk=errors(p['q'],'ERR-only')+p['Dstar']+gate['initial_upper']+p['beta0']*min(Pl*p['S2'],p['Ps']*p['S2']+Pl*maj['Q'])
    price=err_price(changed,ka,h,risk)
    oldmaj=majorant(p['B'],p['b'],p['T'],p['FS'],p['S2'],F(p['W']-1,p['W']),tau+Pl+p['Gp']+p['f'],h+Pl+p['Gp']+p['f'])
    oldrisk=errors(p['q'],'ERR-only')+p['Dstar']+gate['initial_upper']+p['beta0']*min(Pl*p['S2'],p['Ps']*p['S2']+Pl*oldmaj['Q'])
    assert risk<=p['eps'] and max(price['quiet_upper'],price['returns_upper'])<=F('.01')
    rows.append(dict(condition='ERR-only quiet/return tax at ka=13,h=120',kind='singleton diagnostic',
                     value=err_price(p,ka,h,oldrisk)['quiet_upper'],parameter='joint_U_upper_s',
                     sufficient_change='addressed c=13 at fixed g=131 (outside nominal-service grid); verify a genuinely faster full U',
                     required=13*p['tm']/(1+p['margin']),price_upper=price['quiet_upper'],
                     returns_upper=price['returns_upper'],unchanged_risk_upper=risk,
                     remaining='requires U far below nominal 90 ns; NOT realizable by allocating extra margin or shrinking Dstar; no hardware change performed'))
    return rows


def figures(out, curves, selected, err):
    import os
    import tempfile
    from pathlib import Path
    cache=Path(tempfile.gettempdir())/'t82-matplotlib-cache'
    cache.mkdir(exist_ok=True)
    os.environ.setdefault('MPLCONFIGDIR',str(cache))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    matplotlib.rcParams.update({'svg.hashsalt':'t82-t80-v1','font.size':9,
                                'axes.spines.top':False,'axes.spines.right':False})
    colors={'combined':'#0072B2','monitor-only':'#D55E00','ERR-only':'#009E73'}
    for axis, xlabel in [('aM','Conditional lower response a_M'),('d','Delivery + compute upper (s)')]:
        fig,axs=plt.subplots(2,2,figsize=(11,7),layout='constrained')
        for ax,ci in zip(axs.flat,(0,1,2,3)):
            rr=[r for r in curves if r['context_id']==ci and r['axis']==axis]
            for mode in ('combined','monitor-only'):
                data=sorted([r for r in rr if r['mode']==mode],key=lambda r:r['x'])
                xx=[float(r['x']) for r in data];yy=[float(r['best_tax_upper'])*100 if r['best_tax_upper'] is not None else np.nan for r in data]
                ax.plot(xx,yy,'o-' if mode=='combined' else 's--',color=colors[mode],label=mode)
                rejected=[float(r['x']) for r in data if r['best_tax_upper'] is None]
                ax.scatter(rejected,[98]*len(rejected),marker='x',color=colors[mode])
            er=next((r for r in err if int(r['context_id'])==ci),None)
            if er and er.get('quiet_upper'):
                tax=min(F(er['quiet_upper']),F(selected[ci]['hard_mask_upper']))
                ax.axhline(float(tax)*100,color=colors['ERR-only'],ls=':',label='new ERR-only (singleton)')
            ax.axhline(1,color='black',lw=1,label='1% target')
            if axis=='aM':ax.set_xscale('log')
            ax.set(xlabel=xlabel,ylabel='Certified conditional tax upper (%)',ylim=(0,102),
                   title=f"T73, shield {('2.5','3')[ci%2]}, margin {(10,10,5,5)[ci]}%")
            ax.grid(alpha=.2)
        axs[0,0].legend(fontsize=8,loc='center left')
        fig.suptitle('Fixed class: qR=2 bbar, rho_e=1e-6/s, DQ=300 s; total-load diagnostic\n'
                     'minimum of T80 price and hard mask; × = no LOW certificate; no physical qualification')
        for ext in ('png','svg'):
            fig.savefig(out/f'tax_vs_{axis}.{ext}',dpi=170,metadata={'Date':None} if ext=='svg' else {'Software':'T82'})
        plt.close(fig)
    p=context(source_check()[0],'.10','internal38',1)
    fig,axs=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for kind,label,color in [('total_load','total-load','#0072B2'),('solar_plus_upper_unobserved_load','solar lower, original quiet upper','#D55E00')]:
        xx=[];ex=[];ks=[];mu=[]
        for w in map(F,FAMILY['window_s']):
            m=monitor_window(p,F(10**6),w,F(1),F(2),kind);th=threshold(m,F(1))
            xx.append(float(w));ex.append(float(10**6*m['mR']));ks.append(th['k']);mu.append(float(m['mu']))
        axs[0].plot(xx,ex,'o-',label=label,color=color)
        axs[1].plot(xx,ks,'o-',label=f'k ({label})',color=color)
    axs[1].plot(xx,mu,'k--',label='quiet count upper (both profiles)')
    for ax in axs:ax.set_xscale('log');ax.set_xlabel('Nominal window w (s)');ax.grid(alpha=.2);ax.legend(fontsize=8)
    axs[0].set(ylabel='a_M × retrospective exposure',title='Fast rho_b=0.048/s: exposure saturates')
    axs[1].set(yscale='log',ylabel='Counts',title='Long windows retain large quiet false-alarm bound')
    for ext in ('png','svg'):fig.savefig(out/f'long_window.{ext}',dpi=170,metadata={'Date':None} if ext=='svg' else {'Software':'T82'})
    plt.close(fig)
    for path in out.glob('*.svg'):
        path.write_text('\n'.join(line.rstrip() for line in path.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8')


def build(out, ps, csv_write, json_write):
    path=out/'full_grid.csv.xz'
    if not path.exists():return
    # Display slice only. All other distinct environment classes remain in
    # full_grid; none is optimized away or presented as the same guarantee.
    selected={};curve_data={}
    for row in read_rows(path):
        if row['qratio']!='2' or row['rho_e']!='0.000001' or row['DQ']!='300' or row['kind']!='total_load':continue
        ci=int(row['context_id']);mode=row['mode'];p=ps[ci]
        good=row['status']=='certified_conditional'
        if good:
            formula=F(row['quiet_upper']);hard=hard_tax(p);tax=min(formula,hard)
            rr=dict(row,quiet_formula_upper=formula,hard_mask_upper=hard,best_tax_upper=tax,
                    return_best_upper=min(F(row['returns_upper']),hard_tax(p,True)))
            key=(ci,mode)
            if key not in selected or formula<selected[key]['quiet_formula_upper']:selected[key]=rr
        for axis,value in [('aM',row['aM']),('d',row['d'])]:
            if axis=='d' and row['aM']!='1000000':continue
            key=(ci,mode,axis,value)
            if key not in curve_data:curve_data[key]=dict(context_id=ci,mode=mode,axis=axis,x=F(value),best_tax_upper=None,formula_upper=None,feasible_windows=0)
            target=curve_data[key]
            if good:
                target['feasible_windows']+=1
                if target['best_tax_upper'] is None or (tax,formula)<(target['best_tax_upper'],target['formula_upper']):
                    target.update(best_tax_upper=tax,formula_upper=formula,w=row['w'],d=row['d'],aM=row['aM'])
    selected_rows=[]
    for ci,p in enumerate(ps):
        for mode in ('combined','monitor-only'):
            rr=selected.get((ci,mode),{'status':'no_certificate_in_display_class','context_id':ci,'mode':mode})
            selected_rows.append(dict(ident(p),**rr))
    csv_write(out/'selected_fixed_class.csv',selected_rows)
    csv_write(out/'curves_fixed_class.csv',list(curve_data.values()))
    csv_write(out/'timing_contracts.csv',timing_rows(ps))
    csv_write(out/'addressed_repairs.csv',addressed_repairs(ps[1]))
    real=json.loads((out.parents[1]/'monitor_profiles.json').read_text())
    csv_write(out/'real_profiles.csv',[dict(profile=x['id'],aM=None,quiet_upper=None,best_certified_tax=None,
        status='unqualified_channel',additional_T80_input='subwindow or cumulative counts at stride w/2; joint lower response and quiet upper; timing/resource/loss bounds') for x in real['profiles']])
    err=list(read_rows(out/'ERR_best.csv'))
    selected_for_plots={i:dict(hard_mask_upper=hard_tax(p)) for i,p in enumerate(ps)}
    figures(out,list(curve_data.values()),selected_for_plots,err)
    json_write(out/'display_scope.json',dict(qratio='2',rho_e='0.000001',DQ='300',kind='total_load',
        optimizer_scope='within class only; never minimize over qR, rho_e or DQ',
        hard_bound_source='T80 (11), same all-history mask at horizon; formula (8)/(10) retained separately',
        new_scientific_formulas=False,real_instrument_qualified=False))
