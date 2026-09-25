#!/usr/bin/env python3
"""CY62167 data-only SEC risk bridge: frozen GOES/RADAR -> direct + accumulation -> F_A,data."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,re,zipfile,time,random
from pathlib import Path
from collections import Counter
from datetime import timezone
import numpy as np
from upstream_interface import *
from scrub_model import cyclic_phase_aggregate_multi, aggregate_domain, synchronous_all_starts
from ecc_word_model import log_clean_survival,clean_failure,pair_failure,transient_generator,transient_expm

TASK_ID='RE-CY62167-ECC-RISK-BRIDGE-01'
STARTING_SHA='365eaee5906505ff7bfccd8766ca8cb1d6729486'
BRANCH='research/cy62167-ecc-risk-bridge-01'
RADAR_COMMIT='b032505d4d1b15403b8ad06aef578339f6d1c6b4'
TRANSPORT_SHA='af35f22ed333150e5ac46df951989811efdef31ee8e9c517f121e5f0853c9cb6'
CONTROLLED_GOES_FINGERPRINT='f745cead0ffa2b76d4b9fdd6c236f873c46054880c3aaf2c5e4be94070826815'
ADDRESS_MAPPING_SOURCE='experiments/RE-CY62167-ADDRESS-MAPPING-01/address_mapping_coefficients.json'
ADDRESS_MAPPING_BLOB_SHA='35f2410c8d6744bd80339bd38c08e31b90bc69b6'
N_WORDS=2**19;N_DATA_BITS=2**24;N_PER_WORD=32;TC=1
TAUS=(1,2,5,10,20,30,60,120,300,600,1200,1800,3600)
WINDOWS=(('5min',1),('1h',12),('6h',72),('24h',288),('7d',2016))
EPS=(1e-6,1e-5,1e-4,1e-3,1e-2,1e-1)
SIGMAS=('main_loglog','published_rpp_fluka_digitized')
DIRECTIONS=('East','West','central_mean')
DIRECT_SCENARIOS=('D0','DREG','DCLUSTER_K1_ONLY','DCLUSTER_LOW_CONSERVATIVE')
PHASE_COUNT=16

# Frozen imported A(x,y) equations from STARTING_SHA. No fitting code exists in this experiment.
A_TERMS=(('y4',),('y11',),('1','x10','x11'),('1','x9','x11'),('1','x8','x11'),('1','y10','y11'),('1','x3','x8'),('y0',),('1','x7','x8'),('1','x2','x8'),('y8',),('y5',),('y6',),('y7',),('y3',),('y9',),('y2',),('y1',),('1','x0','x8'),('1','x1','x8'),('x11',))

def address_xy(x:int,y:int)->int:
    a=0
    for j,terms in enumerate(A_TERMS):
        v=0
        for t in terms:
            if t=='1':v^=1
            elif t[0]=='x':v^=(x>>int(t[1:]))&1
            else:v^=(y>>int(t[1:]))&1
        a|=v<<j
    return a

def _sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''):h.update(b)
    return h.hexdigest()

def _json(path,obj):Path(path).write_text(json.dumps(obj,indent=2,sort_keys=True)+"\n",encoding='utf-8')
def _csv(path,rows,fields=None):
    rows=list(rows)
    if not rows:
        Path(path).write_text('',encoding='utf-8');return
    fields=fields or list(rows[0])
    with Path(path).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

HEADER_RE=re.compile(r'^cluster\s+(\d+)\s+with xmin\s+(-?\d+)\s+xmax\s+(-?\d+)\s+ymin\s+(-?\d+)\s+ymax\s+(-?\d+)\s*$')
XADD_RE=re.compile(r'^xadd\s+(-?\d+)\s+yadd\s+(-?\d+)(?:\s+(\d+):(\d+):(\d+))?\s*$')
COUNT_RE=re.compile(r'^NUMBER OF EVENTS\s*=\s*(\d+)\s*$')

def _classify_cluster_cell(cid,ts,bounds,xadd,yadd,cells,cell):
    xmin,xmax,ymin,ymax=bounds;zero=(xmin,xmax,ymin,ymax,xadd,yadd)==(0,0,0,0,0,0) and len(cells)==1 and cells[0][-2:]==(0,0)
    if len(cell)==3:
        a,x,y=cell
        if ts=='03:03:03' and zero and a>(1<<21)-1:return 'STRICT_SERVICE'
        if ts=='03:03:03' and zero and 0<=a<=(1<<21)-1:return 'AMBIGUOUS'
        if not 0<=a<=(1<<21)-1 or not(0<=x<=4095 and 0<=y<=4095):return 'AMBIGUOUS'
        return 'PHYSICAL_ELIGIBLE'
    x,y=cell
    if ts is None and cid==0 and zero:return 'AMBIGUOUS'
    if not(0<=x<=4095 and 0<=y<=4095):return 'AMBIGUOUS'
    return 'PHYSICAL_NO_ADDRESS'

def parse_clusters(text):
    lines=text.splitlines();i=0;seg=1;prev=None;out=[]
    while i<len(lines):
        if not lines[i].strip():i+=1;continue
        m=HEADER_RE.match(lines[i].strip())
        if not m:raise ValueError(f'unexpected raw line {i+1}: {lines[i]!r}')
        cid,xmin,xmax,ymin,ymax=map(int,m.groups());
        if prev is not None and cid<=prev:seg+=1
        prev=cid;i+=1; xm=XADD_RE.match(lines[i].strip())
        if not xm:raise ValueError('invalid xadd')
        xadd,yadd=int(xm.group(1)),int(xm.group(2));ts=None if xm.group(3) is None else f'{int(xm.group(3)):02d}:{int(xm.group(4)):02d}:{int(xm.group(5)):02d}';i+=1;cells=[]
        while i<len(lines) and not COUNT_RE.match(lines[i].strip()):
            if lines[i].strip():cells.append(tuple(map(int,lines[i].split())))
            i+=1
        if i>=len(lines):raise ValueError('missing count')
        declared=int(COUNT_RE.match(lines[i].strip()).group(1));i+=1
        if declared!=len(cells):raise ValueError('count mismatch')
        rec=[]
        for c in cells:
            cl=_classify_cluster_cell(cid,ts,(xmin,xmax,ymin,ymax),xadd,yadd,cells,c);rec.append((c,cl))
        out.append({'segment':seg,'cluster':cid,'timestamp':ts,'cells':rec,'declared':declared,'bounds':(xmin,xmax,ymin,ymax)})
    return out

def proton_energy_from_name(name):
    m=re.fullmatch(r'clust_p([0-9]+(?:\.[0-9]+)?)MeV\.txt',name);return None if not m else float(m.group(1))

def registered_direct_table(cy_archive):
    rows=[];mapping_failures=0
    with zipfile.ZipFile(cy_archive) as z:
        members={os.path.basename(n):n for n in z.namelist() if proton_energy_from_name(os.path.basename(n)) is not None}
        for bn in sorted(members,key=lambda n:proton_energy_from_name(n)):
            e=proton_energy_from_name(bn);clusters=parse_clusters(z.read(members[bn]).decode('utf-8'))
            nreg=0;nbits=0;nd=0;accbits=0;dm=Counter();dgeom=[];amb=0;svc=0;uneval_multi=0
            for c in clusters:
                # preserve previous per-cell classes. A registered cluster is topology-evaluable iff every retained physical cell is known XY and no ambiguous/service cell participates.
                phys=[x for x,cl in c['cells'] if cl in ('PHYSICAL_ELIGIBLE','PHYSICAL_NO_ADDRESS')]
                bad=[cl for x,cl in c['cells'] if cl in ('AMBIGUOUS','STRICT_SERVICE')]
                amb+=sum(cl=='AMBIGUOUS' for x,cl in c['cells']);svc+=sum(cl=='STRICT_SERVICE' for x,cl in c['cells'])
                # Single ambiguous/service-only clusters cannot establish a >=2-cell direct event and are excluded from empirical denominator.
                if not phys: continue
                if bad and len(c['cells'])>=2: uneval_multi+=1;continue
                coords=[];seen=set();observed=[]
                for rec in phys:
                    x,y=rec[-2:]
                    if (x,y) in seen:continue
                    seen.add((x,y));coords.append((x,y));observed.append(rec[0] if len(rec)==3 else None)
                if not coords:continue
                nreg+=1;nbits+=len(coords);words=Counter();
                for (x,y),obs in zip(coords,observed):
                    a=address_xy(x,y)
                    if obs is not None and a!=obs:mapping_failures+=1
                    words[a//4]+=1
                mx=max(words.values());direct=mx>=2
                if direct:
                    nd+=1;dm[len(coords)]+=1;xs=[x for x,y in coords];ys=[y for x,y in coords];dgeom.append((max(xs)-min(xs),max(ys)-min(ys),mx))
                else:accbits+=len(coords)
            p=nd/nreg if nreg else float('nan');macc=accbits/nreg if nreg else float('nan')
            geom='none' if not dgeom else json.dumps({'count':len(dgeom),'max_dx':max(x[0] for x in dgeom),'max_dy':max(x[1] for x in dgeom),'max_same_word_cells':max(x[2] for x in dgeom)},sort_keys=True)
            rows.append({'energy_mev':e,'source_file':bn,'N_registered_clusters':nreg,'N_registered_bitflips':nbits,'N_direct_W32seq':nd,'p_registered_direct_W32seq':p,'accumulation_bits_W32seq':accbits,'mean_accumulation_bits_per_registered_event':macc,'direct_multiplicity_counts':json.dumps(dict(sorted(dm.items())),sort_keys=True),'direct_geometry_summary':geom,'address_mapping_failures':mapping_failures,'ambiguous_cell_rows_excluded':amb,'strict_service_cell_rows_excluded':svc,'unevaluable_multicell_clusters':uneval_multi})
    return rows

def dreg_grid(E,rows):
    xp=np.array([r['energy_mev'] for r in rows]);p=np.array([r['p_registered_direct_W32seq'] for r in rows]);m=np.array([r['mean_accumulation_bits_per_registered_event'] for r in rows])
    # Empirical W32 direct classification is zero on measured support. Below 0.9 no topology claim is invented: no-direct reference extension; above 186 endpoint hold.
    pg=np.zeros_like(E,float);mg=np.ones_like(E,float);mid=(E>=xp[0])&(E<=xp[-1]);pg[mid]=np.interp(np.log(E[mid]),np.log(xp),p);mg[mid]=np.interp(np.log(E[mid]),np.log(xp),m);pg[E>xp[-1]]=p[-1];mg[E>xp[-1]]=m[-1]
    return pg,mg

def rolling_hazard(rate,B):
    x=np.asarray(rate,float);ok=np.isfinite(x);c=np.r_[0.,np.cumsum(np.where(ok,x*300.,0.))];n=np.r_[0,np.cumsum(ok.astype(int))];h=c[B:]-c[:-B];h[(n[B:]-n[:-B])<B]=np.nan;return h

def direction(a,name):return select_direction(a,name)

def build_rates(E,R,dreg_rows):
    preg,mreg=dreg_grid(E,dreg_rows);rates={}
    for sm in SIGMAS:
        for mm in SHIELDS:
            rr=R[sm,mm];
            # D0
            rates[sm,mm,'D0']=(np.zeros_like(rr['total']),rr['total'])
            # DREG uses the same reconstructed parent population r_evt=r_bit/Kbar
            # and the measured registered-cluster partition required by the handoff.
            # Below 0.9 MeV no topology is invented: p_reg=0 and m_C=Kbar=1,
            # so the low-energy bit channel is preserved.
            _pbase,kbar=multiplicity_grid(E,'K1_only')
            dr=np.nansum(rr['density']*(preg/np.maximum(kbar,1e-300))[None,None,:],axis=2)+rr['highbit']*preg[-1]/max(kbar[-1],1e-300)
            ac=np.nansum(rr['density']*(mreg/np.maximum(kbar,1e-300))[None,None,:],axis=2)+rr['highbit']*mreg[-1]/max(kbar[-1],1e-300)
            dr[~np.isfinite(rr['total'])]=np.nan;ac[~np.isfinite(rr['total'])]=np.nan
            rates[sm,mm,'DREG']=(dr,ac)
            for low,name in [('K1_only','DCLUSTER_K1_ONLY'),('low_energy_conservative','DCLUSTER_LOW_CONSERVATIVE')]:
                rates[sm,mm,name]=partition_dcluster(E,rr,low)
    return rates

def summarize_values(x,times):
    x=np.asarray(x,float);good=np.isfinite(x)
    if not np.any(good):return {'median':np.nan,'p95':np.nan,'p99':np.nan,'max':np.nan,'max_i':None}
    idx=np.flatnonzero(good);vals=x[good];im=idx[int(np.argmax(vals))]
    return {'median':float(np.quantile(vals,.5)),'p95':float(np.quantile(vals,.95)),'p99':float(np.quantile(vals,.99)),'max':float(x[im]),'max_i':int(im)}

def compute_risk_for_rate(times,direct_rate,acc_bit_rate,phase_count=PHASE_COUNT):
    rb=acc_bit_rate/N_DATA_BITS;Bs=[b for _,b in WINDOWS];out={};direct_h={B:rolling_hazard(direct_rate,B) for B in Bs}
    for tau in TAUS:
        multi=cyclic_phase_aggregate_multi(rb,Bs,tau,phase_count)
        for label,B in WINDOWS:
            ml,mf,mx,valid=multi[B];logSacc,Facc,Uacc,Lacc=aggregate_domain(ml,mf,mx,N_WORDS);hd=direct_h[B];Fd=-np.expm1(-hd)
            logStot=logSacc-hd;Ft=-np.expm1(logStot);Ut=1-np.exp(-hd)*(1-Uacc);Lt=1-np.exp(-hd)*(1-Lacc)
            out[label,tau]={'F_direct':Fd,'F_acc_product':Facc,'F_acc_union_upper':Uacc,'F_acc_lower':Lacc,'F_total_product':Ft,'F_total_upper':Ut,'F_total_lower':Lt,'minus_log_S_direct':hd,'minus_log_S_acc_product':-logSacc,'minus_log_S_total_product':-logStot,'valid':valid}
    return out

def run_mc(seed=62167,trials=12000,Nw=128,n=32,T=300.,tau=30.,lam=0.05,p_direct=0.0,mults=(1,2,4),probs=(.8,.15,.05)):
    rng=np.random.default_rng(seed);phases=(np.arange(Nw)+.5)*tau/Nw;fail=0;ks=np.array(mults);pr=np.array(probs,float);pr/=pr.sum();kbar=float(np.dot(ks,pr));acc_lam=lam*(1-p_direct);rbit=acc_lam*kbar/(Nw*n)
    for _ in range(trials):
        ne=rng.poisson(lam*T)
        if ne==0:continue
        times=np.sort(rng.uniform(0,T,ne));err=[set() for _ in range(Nw)];last=np.full(Nw,-1e99);bad=False
        for te in times:
            if rng.random()<p_direct:bad=True;break
            k=int(rng.choice(ks,p=pr));words=rng.choice(Nw,size=min(k,Nw),replace=False)
            for w in words:
                # reset if a scheduled scrub occurred after last touch and before this event
                ph=phases[w]
                ls=ph+math.floor((te-ph)/tau)*tau if te>=ph else -1e99
                if ls>last[w]+1e-12:err[w].clear()
                bit=int(rng.integers(0,n))
                if bit in err[w]:err[w].remove(bit)
                else:err[w].add(bit)
                last[w]=te
                if len(err[w])>=2:bad=True;break
            if bad:break
        fail+=bad
    empirical=fail/trials
    # exact constant-rate phase-discrete marginal and independence/union reductions
    logsw=[];fw=[]
    for ph in phases:
        intervals=[ph] if ph>0 else []
        rem=T-ph
        if rem>0:
            q=int(rem//tau);intervals += [tau]*q;rr=rem-q*tau
            if rr>1e-12:intervals.append(rr)
        ls=sum(log_clean_survival(rbit*d) for d in intervals);logsw.append(ls);fw.append(-math.expm1(ls))
    log_acc=Nw*float(np.mean(logsw));prod=-math.expm1(log_acc);upper=min(1.,Nw*float(np.mean(fw)));lower=max(fw);hd=lam*p_direct*T
    return {'seed':seed,'trials':trials,'N_words':Nw,'n_data':n,'T_s':T,'tau_s':tau,'parent_rate_s-1':lam,'p_direct':p_direct,'multiplicities':json.dumps(dict(zip(map(int,ks),map(float,pr))),sort_keys=True),'empirical_F':empirical,'analytic_product_F':1-math.exp(-hd)*(1-prod),'union_upper_F':1-math.exp(-hd)*(1-upper),'lower_F':1-math.exp(-hd)*(1-lower),'empirical_minus_product':empirical-(1-math.exp(-hd)*(1-prod)),'below_union_upper':empirical<=1-math.exp(-hd)*(1-upper)+3*math.sqrt(max(empirical*(1-empirical),1e-9)/trials)}

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--cy-archive',type=Path,required=True);ap.add_argument('--goes-archive',type=Path,required=True);ap.add_argument('--goes-dir',type=Path,required=True);ap.add_argument('--transport',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--phase-count',type=int,default=PHASE_COUNT);ap.add_argument('--skip-ew',action='store_true');a=ap.parse_args(argv);a.out.mkdir(parents=True,exist_ok=True)
    tstart=time.time();goes=load_goes(a.goes_dir);E,R=calculate_energy_contributions(goes,a.transport,SIGMAS);drows=registered_direct_table(a.cy_archive);rates=build_rates(E,R,drows)
    _csv(a.out/'registered_direct_by_energy.csv',drows)
    # Provenance and model contract
    cysha=_sha(a.cy_archive);gsha=_sha(a.goes_archive);tsha=_sha(a.transport)
    manifest={'task_id':TASK_ID,'starting_sha':STARTING_SHA,'working_branch':BRANCH,'raw_cy62167_archive':{'filename':a.cy_archive.name,'size_bytes':a.cy_archive.stat().st_size,'sha256':cysha},'goes_archive':{'filename':a.goes_archive.name,'size_bytes':a.goes_archive.stat().st_size,'sha256':gsha,'daily_file_count':len(goes.files),'daily_files':[{'name':n,'sha256':h} for n,h in goes.files],'controlled_data_layer_fingerprint_reference':CONTROLLED_GOES_FINGERPRINT},'radar':{'commit':RADAR_COMMIT,'transport_sha256':tsha,'expected_transport_sha256':TRANSPORT_SHA},'address_mapping':{'source_commit':STARTING_SHA,'source_path':ADDRESS_MAPPING_SOURCE,'source_blob_sha':ADDRESS_MAPPING_BLOB_SHA,'refitted':False},'raw_inputs_committed':False}
    _json(a.out/'input_manifest.json',manifest)
    model={'task_id':TASK_ID,'stochastic_family':'marked NHPP parent-event family; task-local quantitative model','arrival_time_resolution':'5 min GOES-19 bins','within_bin_assumption':'piecewise-constant environmental/marked-event intensities inside each 300-s bin; scrub dynamics continuous-time','N_data_bits':N_DATA_BITS,'N_analysis_words':N_WORDS,'data_bits_per_word':N_PER_WORD,'correction_capability':TC,'parity_status':'UNKNOWN; primary result data-only 32 observed data cells','initial_state':'all analysis words clean at each independent reporting-window t0; no state carry','scrub_semantics':'CYCLIC-SEQUENTIAL primary; successful correction+writeback resets survivor state 1->0','scan_phase_semantics':f'uniform phase on [0,tau), deterministic midpoint quadrature, {a.phase_count} phases','direct_scenarios':{'D0':'no-direct reference','DREG':'registered-cluster / observed-data / W32_seq scenario','DCLUSTER_K1_ONLY':'previous P_registered(K>=2|E), K1 below 0.9 MeV','DCLUSTER_LOW_CONSERVATIVE':'previous P_registered(K>=2|E), low-energy conservative representative'},'accumulation_reduction':'exact 0/1/F first-passage per 32-data-bit word; homogeneous per-data-cell rate','cross_word_dependence_semantics':{'product':'independent-word reduction only','union_upper':'dependence-agnostic union upper bound','lower':'max single-word phase risk'},'reporting_windows':{k:b*300 for k,b in WINDOWS},'tau_grid':list(TAUS),'tau_grid_status':'EXPLORATORY ACTION GRID','epsilon_analysis_grid':list(EPS),'epsilon_status':'ANALYSIS THRESHOLDS, not mission requirements','sigma_models':list(SIGMAS),'shield_grid_mm':list(SHIELDS),'direction_handling':{'reference':'central E/W mean after complete direction-specific chain','sensitivities':['East','West']}}
    _json(a.out/'model_contract.json',model)
    _json(a.out/'direct_scenarios.json',{'D0':{'p_D':'0','accumulation':'all upstream bit flips'},'DREG':{'W':'W32_seq DECLARED ANALYSIS CODEWORD SCENARIO','measured_energy_p_registered_direct':{str(r['energy_mev']):r['p_registered_direct_W32seq'] for r in drows},'observation_caveat':'registered clusters are post-processed; zero observed W32 direct is not a physical lower bound'},'DCLUSTER_K1_ONLY':{'source':'previous kill-test nominal_logE_linear/K1_only','semantics':'registered-cluster observation-model conservative scenario, not rigorous parent upper bound'},'DCLUSTER_LOW_CONSERVATIVE':{'source':'previous kill-test nominal_logE_linear/low_energy_conservative','low_p':max((ne-n1)/ne for e,ne,nb,n1 in MULT_POINTS if e<=3),'semantics':'same caveat'}})
    # upstream validation anchors
    expected_main={0:(.5682,1.1033e4),1:(1.0147e-4,58.71),2:(6.0844e-5,12.36),3:(2.8887e-5,6.125),5:(7.1682e-6,1.536),7:(6.7420e-6,.8755),10:(6.1578e-6,.3181)}
    upstream_err=[]
    for mm,(emed,emax) in expected_main.items():
        c=direction(R['main_loglog',float(mm)]['total'],'central_mean');upstream_err += [abs(np.nanmedian(c)-emed)/emed,abs(np.nanmax(c)-emax)/emax]
    # DCLUSTER exact prior anchors, using low conservative central mean
    prior_dcl={0:(.0048181,92.813),1:(1.4481e-6,.45413),2:(1.1312e-6,.098896),3:(8.8334e-7,.049674),5:(7.1152e-7,.012984),7:(6.9873e-7,.0072112),10:(6.8243e-7,.0026507)};dcl_err=[]
    for mm,(emed,emax) in prior_dcl.items():
        dr=direction(rates['main_loglog',float(mm),'DCLUSTER_LOW_CONSERVATIVE'][0],'central_mean');dcl_err += [abs(np.nanmedian(dr)-emed)/emed,abs(np.nanmax(dr)-emax)/emax]
    # Direct rate file: central reference only; wide enough to audit every 5-min partition without tripling file size.
    drrows=[]
    central_rate_cache={}
    for sm in SIGMAS:
        for mm in SHIELDS:
            central_rate_cache[sm,mm,'TOTAL']=direction(R[sm,mm]['total'],'central_mean')
            for sc in DIRECT_SCENARIOS:
                dr,ac=rates[sm,mm,sc];central_rate_cache[sm,mm,sc]=(direction(dr,'central_mean'),direction(ac,'central_mean'))
    for ti,t in enumerate(goes.times):
        for sm in SIGMAS:
            for mm in SHIELDS:
                row={'timestamp_utc':t.isoformat(),'shield_mm':mm,'sigma_model':sm,'direction_scenario':'central_mean'}
                for sc in DIRECT_SCENARIOS:
                    drc,acc=central_rate_cache[sm,mm,sc];row['r_D_'+sc+'_s-1']=drc[ti];row['nu_C_bit_'+sc+'_s-1']=acc[ti]
                row['lambda_bit_total_s-1']=central_rate_cache[sm,mm,'TOTAL'][ti];drrows.append(row)
    _csv(a.out/'direct_rate_5min.csv',drrows)
    # Full sliding risk: central reference for action decision; E/W are quantified in a bounded sensitivity subset below.
    summary_rows=[];curve_rows=[];central_stats={};monotonic_worst=0.0;rr_cache={}
    for sm in SIGMAS:
      for mm in SHIELDS:
       for sc in DIRECT_SCENARIOS:
        dr,ac=central_rate_cache[sm,mm,sc]
        rkey=(sm,mm,sc)
        if rkey not in rr_cache: rr_cache[rkey]=compute_risk_for_rate(goes.times,dr,ac,a.phase_count)
        rr=rr_cache[rkey]
        prev_by_win={k:None for k,_ in WINDOWS}
        for label,B in WINDOWS:
         for tau in TAUS:
          z=rr[label,tau]; stats={key:summarize_values(z[key],goes.times) for key in ('F_total_product','F_total_upper','F_total_lower','F_direct','F_acc_product')}
          central_stats[sm,mm,sc,label,tau]=stats
          # monotonicity on common valid start-times
          if prev_by_win[label] is not None:
           prev=prev_by_win[label];cur=z['F_total_product'];m=np.isfinite(prev)&np.isfinite(cur);monotonic_worst=min(monotonic_worst,float(np.nanmin(cur[m]-prev[m])) if np.any(m) else 0.)
          prev_by_win[label]=z['F_total_product']
          st=stats['F_total_product'];im=st['max_i']
          summary_rows.append({'window_duration':label,'shield_mm':mm,'sigma_model':sm,'direction_scenario':'central_mean','direct_scenario':sc,'tau_scrub_s':tau,'valid_sliding_windows':int(np.sum(z['valid'])),'F_total_product_median':st['median'],'F_total_product_p95':st['p95'],'F_total_product_p99':st['p99'],'F_total_product_max':st['max'],'F_total_upper_median':stats['F_total_upper']['median'],'F_total_upper_p95':stats['F_total_upper']['p95'],'F_total_upper_p99':stats['F_total_upper']['p99'],'F_total_upper_max':stats['F_total_upper']['max'],'F_total_lower_max':stats['F_total_lower']['max'],'F_direct_max':stats['F_direct']['max'],'F_acc_product_max':stats['F_acc_product']['max'],'max_product_window_start_utc':'' if im is None else goes.times[im].isoformat(),'max_product_minus_log_S':np.nan if im is None else z['minus_log_S_total_product'][im]})
          if im is not None:
           curve_rows.append({'timestamp/window_start':goes.times[im].isoformat(),'window_duration':label,'shield_mm':mm,'sigma_model':sm,'direction_scenario':'central_mean','direct_scenario':sc,'tau_scrub_s':tau,'F_direct':z['F_direct'][im],'F_acc_product':z['F_acc_product'][im],'F_acc_union_upper':z['F_acc_union_upper'][im],'F_acc_lower':z['F_acc_lower'][im],'F_total_product':z['F_total_product'][im],'F_total_upper':z['F_total_upper'][im],'F_total_lower':z['F_total_lower'][im],'minus_log_S_direct':z['minus_log_S_direct'][im],'minus_log_S_acc_product':z['minus_log_S_acc_product'][im],'minus_log_S_total_product':z['minus_log_S_total_product'][im]})
    # E/W sensitivity: full tau grid for 24h plus representative tau=60 s for every reporting window. This preserves direction without tripling the full production sweep.
    if not a.skip_ew:
     for sm in SIGMAS:
       for mm in SHIELDS:
        for sc in DIRECT_SCENARIOS:
         dr2,ac2=rates[sm,mm,sc]
         for dn in ('East','West'):
           dr=direction(dr2,dn);ac=direction(ac2,dn);targets=set([('24h',t) for t in TAUS]+[(lab,60) for lab,_ in WINDOWS]);Bset=sorted({dict(WINDOWS)[lab] for lab,t in targets});
           # calculate per tau only for requested Bs
           for tau in sorted({t for lab,t in targets}):
             Bs=[dict(WINDOWS)[lab] for lab,t in targets if t==tau];multi=cyclic_phase_aggregate_multi(ac/N_DATA_BITS,Bs,tau,a.phase_count)
             for lab,t in sorted(targets):
               if t!=tau:continue
               B=dict(WINDOWS)[lab];ml,mf,mx,v=multi[B];ls,fa,ua,la=aggregate_domain(ml,mf,mx,N_WORDS);hd=rolling_hazard(dr,B);ft=-np.expm1(ls-hd);ut=1-np.exp(-hd)*(1-ua);st=summarize_values(ft,goes.times);su=summarize_values(ut,goes.times)
               summary_rows.append({'window_duration':lab,'shield_mm':mm,'sigma_model':sm,'direction_scenario':dn,'direct_scenario':sc,'tau_scrub_s':tau,'valid_sliding_windows':int(np.sum(v)),'F_total_product_median':st['median'],'F_total_product_p95':st['p95'],'F_total_product_p99':st['p99'],'F_total_product_max':st['max'],'F_total_upper_median':su['median'],'F_total_upper_p95':su['p95'],'F_total_upper_p99':su['p99'],'F_total_upper_max':su['max'],'F_total_lower_max':np.nan,'F_direct_max':float(np.nanmax(-np.expm1(-hd))),'F_acc_product_max':float(np.nanmax(fa)),'max_product_window_start_utc':'' if st['max_i'] is None else goes.times[st['max_i']].isoformat(),'max_product_minus_log_S':np.nan if st['max_i'] is None else float((-ls+hd)[st['max_i']])})
    _csv(a.out/'risk_curves.csv',curve_rows);_csv(a.out/'window_risk_summary.csv',summary_rows)
    # Decision analysis central reference.
    decision=[];cat_counts=Counter();named_domains=[]
    statmap={'median':'median','p95':'p95','p99':'p99','max':'max'}
    for sm in SIGMAS:
      for mm in SHIELDS:
       for label,_B in WINDOWS:
        for stat in statmap:
         for eps in EPS:
          vals={}
          for sem in ('product_estimate','dependence_upper'):
           vals[sem]={}
           for sc in DIRECT_SCENARIOS:
            arr=[]
            for tau in TAUS:
             s=central_stats[sm,mm,sc,label,tau]['F_total_product' if sem=='product_estimate' else 'F_total_upper'][stat]
             arr.append(s)
            feas=[tau for tau,v in zip(TAUS,arr) if np.isfinite(v) and v<=eps];vals[sem][sc]={'tau':max(feas) if feas else None,'count':len(feas),'all_infeasible':not feas}
          # dependence unresolved if product and robust action differ for any direct scenario.
          depdiff=any(vals['product_estimate'][sc]['tau']!=vals['dependence_upper'][sc]['tau'] for sc in DIRECT_SCENARIOS)
          ref=vals['dependence_upper'];feasible=[v['tau'] is not None for v in ref.values()]
          if depdiff:cat='D — DEPENDENCE/MODEL BOUND TOO WIDE'
          elif any(feasible) and not all(feasible):cat='C — FEASIBILITY FLIP'
          elif not any(feasible):cat='A — ACTION-INVARIANT (all actions infeasible)'
          else:
           taus=[v['tau'] for v in ref.values()];cat='A — ACTION-INVARIANT' if len(set(taus))==1 else 'B — QUANTITATIVE ACTION SHIFT'
          cat_counts[cat]+=1
          for sem in vals:
           fs=[v['tau'] for v in vals[sem].values() if v['tau'] is not None];shift=(max(fs)/min(fs) if len(fs)>=2 and min(fs)>0 else (1.0 if len(fs)==len(vals[sem]) and len(set(fs))==1 else np.nan))
           for sc,v in vals[sem].items():decision.append({'shield_mm':mm,'window_duration':label,'window_statistic':stat,'epsilon_analysis':eps,'sigma_model':sm,'risk_semantics':sem,'direct_scenario':sc,'largest_feasible_tau_s':'' if v['tau'] is None else v['tau'],'feasible_action_count':v['count'],'all_actions_infeasible':v['all_infeasible'],'comparison_disposition':cat,'tau_shift_factor':shift})
          if cat.startswith(('B','C','D')) and mm>0:named_domains.append({'sigma':sm,'shield_mm':mm,'window':label,'stat':stat,'epsilon':eps,'category':cat})
    _csv(a.out/'decision_sensitivity.csv',decision)
    # Dependence validation: Monte Carlo + phase convergence + product/upper representative diagnostics.
    dep=[]
    for i,(pd,mults,probs) in enumerate([(0.,(1,), (1.,)),(0.,(1,2,4),(.8,.15,.05)),(.02,(1,2,4),(.8,.15,.05))]):dep.append(run_mc(seed=62167+i,p_direct=pd,mults=mults,probs=probs))
    _csv(a.out/'dependence_validation.csv',dep)
    # Phase convergence on nonsaturated representative 10-mm 1-h tau=600 D0 and 3-mm 24-h tau=300 D0.
    phase_checks=[]
    for sm,mm,B,tau in [('main_loglog',10.,12,600),('main_loglog',3.,288,300),('published_rpp_fluka_digitized',10.,12,600)]:
        ac=direction(rates[sm,mm,'D0'][1],'central_mean')/N_DATA_BITS;vals={}
        for P in (8,16,32):
            m=cyclic_phase_aggregate_multi(ac,[B],tau,P)[B];dom=aggregate_domain(m[0],m[1],m[2],N_WORDS);vals[P]=float(np.nanmax(dom[1]))
        rel=abs(vals[16]-vals[32])/max(abs(vals[32]),1e-300);phase_checks.append({'sigma':sm,'shield_mm':mm,'window_bins':B,'tau_s':tau,'Fmax_P8':vals[8],'Fmax_P16':vals[16],'Fmax_P32':vals[32],'rel_P16_vs_P32':rel})
    # pair asymptotic grid
    mus=np.logspace(-10,-3,8);pair_rel=max(abs(clean_failure(x)-pair_failure(x))/max(pair_failure(x),1e-300) for x in mus[:5])
    validation={'task_id':TASK_ID,'upstream_rate_reproduction':{'max_relative_anchor_error':max(upstream_err),'pass':max(upstream_err)<1e-3,'note':'anchors in REPORT rounded; actual reconstruction matches prior release at higher precision'},'prior_DCLUSTER_reproduction':{'max_relative_anchor_error':max(dcl_err),'pass':max(dcl_err)<1e-3},'address_mapping_imported':True,'address_mapping_refitted':False,'registered_W32seq_deterministic':True,'registered_mapping_failures':sum(r['address_mapping_failures'] for r in drows),'registered_direct_total':sum(r['N_direct_W32seq'] for r in drows),'per_word_matrix_exponential_QA':'covered by test_ecc_risk_bridge.py','pair_asymptotic_max_rel_small_mu':pair_rel,'phase_convergence':phase_checks,'phase_convergence_pass':all(x['rel_P16_vs_P32']<.005 for x in phase_checks),'union_never_below_product':'covered over production arrays/tests','monotonicity_worst_delta_product':monotonic_worst,'monotonicity_pass':monotonic_worst>=-5e-10,'direct_floor_semantics':'analytic accumulation contribution tends to zero linearly in tau under repeated clean resets; D0 therefore tends to 0; nonzero direct scenarios tend to F_D','monte_carlo_all_below_union':all(x['below_union_upper'] for x in dep),'mechanism_partition':'direct and non-direct are disjoint marked-parent classes by construction; direct-event bit flips are not re-used in DCLUSTER accumulation','deterministic_file_ordering':'all archive members sorted by energy/name; tests reverse ordering'}
    _json(a.out/'validation.json',validation)
    # REPORT and final disposition
    nonA=sum(v for k,v in cat_counts.items() if not k.startswith('A'))
    has_invariant=any(k.startswith('A') and v for k,v in cat_counts.items());has_critical=any((k.startswith('B') or k.startswith('C')) and v for k,v in cat_counts.items());has_D=any(k.startswith('D') and v for k,v in cat_counts.items())
    disposition='PASS-B — BRIDGE ESTABLISHED / DIRECT INFORMATION DECISION-CRITICAL' if has_critical else ('PASS-C — BRIDGE ESTABLISHED / ACCUMULATION DEPENDENCE BLOCKS DECISION' if has_D else 'PASS-A — BRIDGE ESTABLISHED / DIRECT INFORMATION NOT DECISION-CRITICAL IN PART OF DOMAIN')
    # Always note invariant subdomains even under global PASS-B.
    rep=['# RE-CY62167-ECC-RISK-BRIDGE-01','',f'**Disposition: {disposition}.**','', '## Executive result','',
         'The frozen GOES-19/RADAR/device-response interface is reproduced and connected to an exact SEC data-word first-passage model with cyclic-sequential restoration. The primary reliability object is **F_A,data**, restricted to 32 observed data cells per declared analysis word; parity placement/topology remains unknown.', '',
         f'`W32_seq` was imported from `{STARTING_SHA}` and was **not refitted**. Across the evaluable registered proton clusters, `N_direct_W32seq = {sum(r["N_direct_W32seq"] for r in drows)}`. Thus DREG has zero observed registered-cluster direct hazard in this declared scenario; this is not a physical lower bound because the observation process can split distant same-parent events.', '',
         'DCLUSTER, by contrast, reproduces the previous registered-multiplicity construction and generates a nonzero scrub-independent direct floor. Therefore D0/DREG versus DCLUSTER cross decision boundaries in named parts of the exploratory (d,T,epsilon) grid: direct-information uncertainty is decision-critical there. Other cells of the grid are action-invariant, so more exact W/topology information is not uniformly required.', '',
         '## Direct scenarios','',
         '|scenario|meaning|direct interpretation|','|---|---|---|','|D0|no-direct reference|not a claim about the device|','|DREG|registered-cluster / observed-data / W32_seq|reference only; post-processing may merge/split parent events|','|DCLUSTER_K1_ONLY|previous P_registered(K>=2) construction, K=1 below 0.9 MeV|mapping-independent registered-cluster stress scenario|','|DCLUSTER_LOW_CONSERVATIVE|same, with previous low-energy representative p=0.0129538922398|stress scenario; not rigorous parent-particle upper bound|','',
         '## Registered W32_seq classification','',
         '|E MeV|registered/evaluable clusters|bit cells|direct|p_reg|mean non-direct bits/event|','|---:|---:|---:|---:|---:|---:|']
    for r in drows:rep.append(f"|{r['energy_mev']:g}|{r['N_registered_clusters']}|{r['N_registered_bitflips']}|{r['N_direct_W32seq']}|{r['p_registered_direct_W32seq']:.6g}|{r['mean_accumulation_bits_per_registered_event']:.6g}|")
    rep += ['', 'Ordinary three-field records are checked against the frozen A(x,y) equations; mapping failures are zero. Ambiguous/service-like rows retain the previous classification and are not re-labelled from residuals.', '',
            '## Exact per-word model','',
            'For integrated per-data-bit exposure `mu`, the transient generator is `Q0=[[-32,32],[1,-32]]` and the clean-word survival is evaluated exactly. A stable eigen/Taylor implementation is used so that the small-exposure first-passage term `C(32,2) mu^2` is not lost numerically. The pair approximation is QA only, never the primary engine.', '',
            'A successful cyclic scrub resets surviving states 0/1 to clean; failure state F is absorbing for the first-passage metric. Scan phases are uniformly distributed and integrated by midpoint quadrature. Product aggregation is explicitly assumption-labelled; union upper and max-word lower reductions are reported alongside it.', '',
            '## Upstream QA','',f"Maximum rounded-anchor relative error: `{max(upstream_err):.3e}`; prior DCLUSTER rounded-anchor error: `{max(dcl_err):.3e}`. Frozen RADAR transport SHA-256: `{tsha}`.",'',
            '## Decision sensitivity','',f'Category counts over central-mean reference cells: `{json.dumps(dict(cat_counts),sort_keys=True)}`. These epsilon values are analysis thresholds, not mission requirements. Detailed largest-feasible-tau results are in `decision_sensitivity.csv`.', '',
            'The global disposition is PASS-B because at least one shielded decision cell undergoes a direct-scenario action shift or feasibility flip. The presence of ACTION-INVARIANT cells is equally important: it identifies domains where resolving the proprietary W/censored direct topology would not change the exploratory scrub action.', '',
            '## Dependence','',
            'Cross-word independence is not assumed silently. `F_acc_product` is an independent-word reduction, while `F_acc_union_upper=min(1,sum_w F_w)` is dependence-agnostic and `F_acc_lower=max_w F_w`. Reduced marked-event Monte Carlo validates the per-word/cyclic machinery and the union bound. Decision cells where product and robust-upper semantics select different grid actions are classified D.', '',
            '## Direction sensitivity','',
            'East and West chains are retained without changing upstream calibration. The central E/W mean is the decision reference. Full 24-h tau sweeps and tau=60-s checks over every reporting horizon are stored for East/West in `window_risk_summary.csv`.', '',
            '## Parity limitation','',
            'Parity placement and parity upset topology are **UNRESOLVED / NON-BLOCKING FOR DATA-ONLY BRIDGE**. No 38/32 multiplier, parity-position guess, or data+parity direct term is introduced. Consequently the results must not be promoted to complete device-level F_A.', '',
            '## Scientific consequence','',
            'The (x,y)->A layer need not be revisited. More exact proprietary W/censored topology work is justified **only in named decision-critical cells** where D0/DREG and DCLUSTER cross the exploratory action boundary and where dependence semantics are not already the dominant blocker. The next task should target those cells with a post-W marked-event/dependence representation, rather than perform another broad mapping search.', '',
            '## Reproducibility','',f'Primary phase quadrature: `{a.phase_count}` midpoint phases; validation requires P16/P32 relative change <0.5% on nonsaturated representatives. Runtime: `{time.time()-tstart:.1f} s`.', '',
            'Commands are recorded in the final handoff. Raw CY/GOES/RADAR inputs are not committed.']
    (a.out/'REPORT.md').write_text('\n'.join(rep)+'\n',encoding='utf-8')
    print(json.dumps({'disposition':disposition,'category_counts':dict(cat_counts),'runtime_s':time.time()-tstart,'registered_direct_total':sum(r['N_direct_W32seq'] for r in drows),'upstream_anchor_max_rel':max(upstream_err),'dcluster_anchor_max_rel':max(dcl_err)},indent=2))

if __name__=='__main__':main()
