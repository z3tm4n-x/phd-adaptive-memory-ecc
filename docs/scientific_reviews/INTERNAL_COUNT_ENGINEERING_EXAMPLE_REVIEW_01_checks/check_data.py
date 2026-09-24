"""Review-owned statistics, raw graph reconstruction and direct-floor audit.

No imports from RE code. Reads source ZIP/NPZ/JSON; writes only --out.
"""
import argparse, collections, csv, hashlib, io, json, math, re, zipfile
from decimal import Decimal, localcontext
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.stats import binom, t, chi2
import openpyxl

REPO=Path(__file__).resolve().parents[3]
PKG=REPO/'experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01/continuation-02'
def js(p):return json.loads((PKG/p).read_text())
def close(a,b):assert math.isclose(float(a),float(b),rel_tol=2e-10,abs_tol=3e-10),(a,b)
def cp(k,n,alpha):
    lo=0. if not k else brentq(lambda p:binom.sf(k-1,n,p)-alpha/2,0,1,xtol=1e-16)
    hi=1. if k==n else brentq(lambda p:binom.cdf(k,n,p)-alpha/2,0,1,xtol=1e-16)
    return lo,hi
def mean(x):return math.fsum(map(float,x))/len(x)
def variance(x):
    m=mean(x);return math.fsum((float(v)-m)**2 for v in x)/(len(x)-1)
def ci_mean(x,a):
    m=mean(x);r=float(t.ppf(1-a/2,len(x)-1))*math.sqrt(variance(x)/len(x));return m,m-r,m+r
def floor_decimal(rate):
    # Explicit analytic 2x2 exponential, 60-decimal arithmetic; no scipy expm.
    with localcontext() as ctx:
        ctx.prec=60; r=Decimal(str(rate));switch=Decimal(1)/60;lo=r/10
        center=-switch-(lo+r)/2;d=((r-lo)/2)**2+switch**2;d=d.sqrt();H=Decimal(1800)
        cosh=((d*H).exp()+(-d*H).exp())/2
        sinh=((d*H).exp()-(-d*H).exp())/2
        return Decimal(1)-(center*H).exp()*(cosh+switch/d*sinh)
def bfs(points,offsets,merge):
    unseen=set(points);groups=[]
    while unseen:
        first=min(unseen);unseen.remove(first);queue=[first];group=[]
        while queue:
            p=queue.pop();group.append(p)
            neighbours=[p^a for a in offsets]
            if merge:neighbours.extend(16*(p//16)+b for b in range(16))
            for q in neighbours:
                if q in unseen:unseen.remove(q);queue.append(q)
        groups.append(tuple(sorted(group)))
    return sorted(groups)
def raw_check(path):
    manifest=js('inputs/manifest.json');content=path.read_bytes()
    assert hashlib.sha256(content).hexdigest()==manifest['archive_sha256']
    z=zipfile.ZipFile(io.BytesIO(content))
    for name,h in manifest['member_sha256'].items():assert hashlib.sha256(z.read(name)).hexdigest()==h
    prefix='OpenData/2025-02-14MeV-NEUTRONS/'
    raw=prefix+'01-Original_DATA/01-STATIC-3.3V/';treated=prefix+'02-TREATED_DATA/01-STATIC-3.3V/'
    source=z.read(treated+'Global_Analysis.jl').decode('utf-8-sig')
    offsets=sorted(set(int(x,16) for x in re.findall(r'0x[\da-fA-F]+',re.search(r'Anomalies\s*=\s*\[([^]]+)\]',source,re.S)[1])))
    assert offsets==manifest['anomalies'] and len(offsets)==35
    wb=openpyxl.load_workbook(io.BytesIO(z.read(raw+'Study_3V3_0x5555.xlsx')),read_only=True,data_only=True)
    metadata={re.search(r'out__\d+',r[0])[0]:r for r in wb['events'].iter_rows(values_only=True) if isinstance(r[0],str) and r[0].startswith('out__')}
    allgroups=[];allmerged=[];double=[];times=[];hist=collections.Counter();rows=0;bits=0
    for name in sorted(n for n in z.namelist() if n.startswith(raw) and n.endswith('.dat')):
        points=[];words={};stem=Path(name).stem
        for line in z.read(name).decode('utf-8-sig').splitlines():
            if not line.startswith('0x'):continue
            w,v,expected=[int(x,16) for x in line.split(',')[:3]];mask=v^expected
            assert 0<w<2**21 and mask>0 and w not in words;words[w]=mask
            points.extend(16*w+b for b in range(16) if mask&(1<<b))
        groups=bfs(points,offsets,False);merged=bfs(points,offsets,True)
        log=next(n for n in z.namelist() if n.startswith(treated) and n.endswith(stem+'_global.log'))
        logs=sorted(tuple(sorted(int(v,16) for v in re.findall(r'0x[\da-fA-F]+',line))) for line in z.read(log).decode('utf-8-sig').splitlines() if line.lstrip().startswith('0x'))
        assert groups==logs
        m=next(x for x in manifest['tests'] if x['id']==stem);r=metadata[stem]
        close(m['duration_s'],r[3]);close(m['fluence_cm2'],r[4]/r[5]);close(r[6],r[4]/r[5]);times.append(float(r[3]))
        assert m['bits']==len(points) and m['raw_words']==len(words) and m['groups']==len(groups)
        if stem=='out__1740591142':assert len(points)==941
        for g in merged:
            byword=collections.defaultdict(list)
            for p in g:byword[p//16].append(p%16)
            pairs=[(w,b) for w,b in byword.items() if len(b)>1]
            if pairs:
                assert len(pairs)==1 and len(pairs[0][1])==2
                double.append((stem,pairs[0][0],pairs[0][1]))
        allgroups.extend(groups);allmerged.extend(merged);hist.update(map(len,groups));rows+=len(words);bits+=len(points)
    with np.load(PKG/'inputs/templates.npz') as templates:
        for groups,pk,ok in [(allgroups,'points','offsets'),(allmerged,'merged_points','merged_offsets')]:
            recovered=[tuple(map(int,templates[pk][a:b])) for a,b in zip(templates[ok][:-1],templates[ok][1:])]
            assert groups==recovered
    assert (rows,bits,len(allgroups),len(allmerged),sum(times),len(double))==(55344,55353,44364,44355,3119.5,9)
    # Exhaust all 16 common lane translations and each possible safe pre-state.
    worst=1.;count=0
    for _,_,pair in double:
        for chip in [0,1]:
            for existing in range(-1,39):
                fail=0
                for shift in range(16):
                    incoming={16*chip+(b^shift) for b in pair}
                    after=incoming.symmetric_difference(set() if existing<0 else {existing})
                    fail+=len(after)>=2;count+=1
                worst=min(worst,fail/16)
    assert worst==7/8
    return dict(raw_words=rows,bits=bits,xor_groups=len(allgroups),merged_groups=len(allmerged),duration=sum(times),group_log_matches=60,histogram=dict(sorted(hist.items())),double_words=double,lane_prestate_cases=count,minimum_conditional_failure=worst)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--raw',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    result={'raw':raw_check(args.raw),'cases':{}};cfg=js('config.json');a=.05/54;analysis=js('outputs/analysis.json')
    expected=['b16ccf6b64f21c7b8391818fb19b579133ed5e7db10760429a05f8013be8b1c7','6b39b46b54f6eb3435a1c63d48e6b7106f250097c84d286016ea24b6e0984f25','25944e0f0e8275154899d0fba060a30883cf017714a326c6a343397b2017e36d']
    selected=js('outputs/selected_policies.json')
    for case,h in zip(cfg['cases'],expected):
        path=PKG/'outputs'/('test_'+case+'.npz');assert hashlib.sha256(path.read_bytes()).hexdigest()==h
        with np.load(path) as z:
            R=z['rows'];assert R.shape==(20000,5,12) and np.isfinite(R).all() and np.all(R[:,:,11]==0)
            assert len(set(z['event_sha256']))==20000;np.testing.assert_array_equal(z['policies'],selected[case]['policies'])
        n=len(R);stats=analysis['results'][case];pols=[];pairs=[]
        assert np.isin(R[:,:,0],[0,1]).all() and np.all((R[:,:,1]>=0)&(R[:,:,1]<=1800))
        assert np.all((R[:,:,10]>0)&(R[:,:,10]<=1+1e-12))
        for j,row in enumerate(stats['policies']):
            x=R[:,j];alive=x[:,0]==0;k=int(sum(x[:,0]));lo,hi=cp(k,n,a)
            assert k==row['failures'];close(lo,row['family_low']);close(hi,row['family_high'])
            for u,v in zip(cp(k,n,.05),[row['F95_low'],row['F95_high']]):close(u,v)
            close(cp(k,n,.1)[1],row['F95_upper'])
            status='supports_requirement' if hi<=.1 else 'supports_violation' if lo>.1 else 'unresolved';assert status==row['status']
            for col,key in [(7,'reservation'),(2,'passes')]:
                m,l,u=ci_mean(x[alive,col],.05);stem='survivor_'+key
                close(m,row[stem+'_s'] if col==7 else row[stem]);close(l,row[stem+'95_low']);close(u,row[stem+'95_high'])
            for col,key in [(7,'reservation_s'),(2,'complete_passes'),(3,'partial_pass_equivalent'),(4,'read_transactions'),(5,'completed_writes'),(6,'actual_bus_s')]:close(mean(x[:,col]),row['stop_'+key])
            for col,key in [(4,'read_transactions'),(5,'completed_writes'),(6,'actual_bus_s'),(8,'updates')]:close(mean(x[alive,col]),row['survivor_'+key])
            # Independent consistency of reserved time and executed pass fractions.
            np.testing.assert_allclose(x[:,7],(x[:,2]+x[:,3])*.0524288,atol=3e-8,rtol=3e-10)
            assert np.all(x[:,6]<=x[:,7]+1e-7) and np.all(x[:,4]>=x[:,2]*524288)
            pols.append(dict(policy=row['policy'],failures=k,interval=[lo,hi],status=status,own_reservation=mean(x[alive,7]),stop_reservation=mean(x[:,7])))
        for j,row in enumerate(stats['pairs'],1):
            f=R[:,0,0].astype(int);g=R[:,j,0].astype(int);cells=np.bincount(2*f+g,minlength=4).tolist();J=(f+g)==0
            for key,v in zip(['both_survive','only_comparator_fails','only_proposed_fails','both_fail'],cells):assert row[key]==v
            lp,up=cp(cells[2],n,a/2);lm,um=cp(cells[1],n,a/2)
            close(lp-um,row['risk_difference_low']);close(up-lm,row['risk_difference_high']);close((cells[2]-cells[1])/n,row['risk_difference'])
            x=R[J,0,7];y=R[J,j,7];m,l,u=ci_mean(x-y,a)
            for k,v in zip(['reservation_difference','reservation_difference_low','reservation_difference_high'],[m,l,u]):close(row[k],v)
            # Delta variance expressed through covariance matrix, not production influence vector.
            mx,my=mean(x),mean(y);cov=math.fsum((float(xx)-mx)*(float(yy)-my) for xx,yy in zip(x,y))/(len(x)-1)
            vv=variance(x)/my**2+mx**2*variance(y)/my**4-2*mx*cov/my**3
            gain=1-mx/my;width=float(t.ppf(1-a/2,len(x)-1))*math.sqrt(max(0,vv)/len(x))
            for key,v in zip(['G','G_low','G_high'],[gain,gain-width,gain+width]):close(row[key],v)
            close(-m/mean(R[J,0,8]),row['saving_s_per_proposed_update']);close(-u/mean(R[J,0,8]),row['saving_lower_s_per_proposed_update'])
            effect='established' if gain-width>=.1 else 'below_10_percent' if gain+width<.1 else 'unresolved';assert effect==row['meaningful_effect']
            pairs.append(dict(comparator=row['comparator'],cells=cells,G=[gain,gain-width,gain+width],risk=[(cells[2]-cells[1])/n,lp-um,up-lm],saved_seconds=-m,absolute_capacity_pp=-m/18))
        result['cases'][case]={'policies':pols,'pairs':pairs};print(case,'statistics PASS',flush=True)
    scores=list(csv.DictReader((PKG/'outputs/tuning_candidates.csv').open()));assert len(scores)==576
    for case in cfg['cases']:
        for record in selected[case]['selection']:
            candidates=[r for r in scores if r['case']==case and int(r['kind'])==record['kind']]
            for r in candidates:close(cp(int(r['failures']),2000,.1)[1],r['upper95'])
            chosen=min(candidates,key=lambda r:(float(r['upper95'])>.1,float(r['survivor_reservation_s']) if float(r['upper95'])<=.1 else float(r['upper95']),int(r['candidate'])))
            assert int(chosen['failures'])==record['failures'];close(chosen['upper95'],record['risk_upper'])
            p=record['policy'];U=cfg['periods_seconds'];close(chosen['first_period'],U[int(p[1])]);close(chosen['second_period'],U[int(p[2])])
            for k,v in zip(['Ms','cap','growth','zero_mode'],p[3:]):close(chosen[k],v)
    result['tuning_score_rows_verified']=len(scores)
    meta=js('inputs/manifest.json');T=meta['total_duration_s'];rate=9/T*2*.25*7/8;floor=floor_decimal(rate)
    recorded=js('outputs/input_sensitivity.json');close(rate,recorded['direct_lower_killing_rate_high']);close(floor,recorded['direct_model_risk_lower'])
    values=np.array([[r['duration_s'],r['bits'],r['groups'],r['double_words']] for r in meta['tests']]);rng=np.random.default_rng(2026091607)
    res=values[rng.integers(60,size=(2000,60))].sum(axis=1)
    for x,key in [(res[:,1]/res[:,0]*39/64,'bit_rate_percentile95'),(3*res[:,2]/res[:,0],'all_chip_group_rate_percentile95'),([float(floor_decimal(v)) for v in res[:,3]/res[:,0]*2*.25*7/8],'bootstrap_direct_lower_percentile95')]:
        for v,pub in zip(np.quantile(x,[.025,.975]),recorded[key]):close(v,pub)
    lower=.5*chi2.ppf(.025,18)/T*2*.25*7/8;close(floor_decimal(lower),recorded['poisson_count_lower95_model_risk'])
    result['direct_floor']={'rate':rate,'decimal_closed_form':str(floor),'bootstrap':recorded['bootstrap_direct_lower_percentile95']}
    with np.load(PKG/'outputs/controller_tables.npz') as tables:
        sizes={k:tables[k].nbytes for k in tables.files if tables[k].ndim>0}
    assert sizes==js('outputs/resource_accounting.json')['packed_table_bytes']
    result['packed_array_bytes']=sum(sizes.values());result['status']='PASS'
    args.out.write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
