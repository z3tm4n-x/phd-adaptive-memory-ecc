"""Independent archive/statistics/Fixed300 audit; no production imports.

Run from any directory with --data pointing to the three original trial NPZs.
Optional --raw points to the five original NOAA netCDF files (hash check only).
The calculation never writes to experiment directories.
"""
import argparse, csv, hashlib, io, json, math, platform, subprocess
from datetime import datetime
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import numpy as np
import scipy
from scipy.optimize import brentq
from scipy.stats import binom

ROOT = Path(__file__).resolve().parents[4]
PKG = ROOT/'experiments/RE-INTERNAL-COUNT-GOES16-VALIDATION-01'
TARGET = 'c0dd38ab3c01917e8e4bb165ecfae122b86dd9ae'
PRE = '870a3c5d725793dd45ff2cc2feaf6e8885df0df9'
BASE = '7b83f643efb37541547d7d93a65ba2f43acd43fd'
NAMES = ['Proposed','Count-disabled','Fixed','Precomputed','PA-DOM']
def sha(b): return hashlib.sha256(b).hexdigest()
def table(name): return list(csv.DictReader((PKG/name).open()))
def js(name): return json.loads((PKG/name).read_text())
def blob(ref,path): return subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT)
def close(x,y):
    assert math.isclose(float(x),float(y),rel_tol=3e-11,abs_tol=3e-12),(x,y)

def cp(k,n,alpha):
    # Invert binomial tails; production instead uses beta quantiles.
    lo=0. if k==0 else brentq(lambda p:binom.sf(k-1,n,p)-alpha/2,0,1,xtol=1e-16)
    hi=1. if k==n else brentq(lambda p:binom.cdf(k,n,p)-alpha/2,0,1,xtol=1e-16)
    return lo,hi
def eb(x,alpha,low=12,high=18000):
    values=[int(v) for v in x]; n=len(values)
    assert all(low<=v<=high for v in values)
    if n<2:return low,high
    # Exact integer sample sums, independently of numpy.var production path.
    total=sum(values); squares=sum(v*v for v in values)
    mean=total/n; variance=F(n*squares-total*total,n*(n-1))
    radius=math.sqrt(2*float(variance)*math.log(4/alpha)/n)+7*(high-low)*math.log(4/alpha)/(3*(n-1))
    return max(low,mean-radius),min(high,mean+radius)
def stream(rates,key,trial):
    gen=np.random.Generator(np.random.PCG64(np.random.SeedSequence([2026091601,key,trial])))
    epochs=[]
    for j,r in enumerate(rates):
        size=gen.poisson(300*r)
        epochs.extend((300*j+300*np.sort(gen.random(size))).tolist())
    t=np.asarray(epochs,dtype='<f8')
    w=gen.integers(0,524288,len(t),dtype=np.int32).astype('<i4')
    b=gen.integers(0,32,len(t),dtype=np.int8)
    return t,w,b

def fixed300(rates):
    # Explicit per-word integration, integer numerators. No closed-form moments.
    W=524288; P=F(.18874368); r=list(map(F,rates))
    den=max(x.denominator for x in r)
    R=[x.numerator*(den//x.denominator) for x in r]
    phase_den=P.denominator*W; total=0
    for j in range(W):
        d=P.numerator*j; rest=300*phase_den-d
        exposed=[R[0]*rest]+[R[k-1]*d+R[k]*rest for k in range(1,12)]+[R[-1]*d]
        total+=sum(x*x for x in exposed)
    return F(31*total,64*W*W*(den*phase_den)**2)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',type=Path,required=True)
    ap.add_argument('--raw',type=Path);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    result={'target':TARGET,'data_commit':'82282a8b36b04b388cb3441c474bede30a1287a2',
            'environment':{'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__},'cases':[]}
    for commit,parent in ((TARGET,PRE),(PRE,BASE)):
        assert subprocess.check_output(['git','show','-s','--format=%P',commit],cwd=ROOT,text=True).strip()==parent
    for name in ['prepare.py','experiment.py','check.py','config.json','PREREGISTRATION.md','selected_windows.json','derived_rates.csv','input_manifest.json']:
        rel=PKG.relative_to(ROOT).as_posix()+'/'+name
        assert blob(PRE,rel)==blob(TARGET,rel)==(PKG/name).read_bytes(),name
    paths=subprocess.check_output(['git','diff','--name-only',BASE,TARGET],cwd=ROOT,text=True).splitlines()
    assert all(x.startswith(PKG.relative_to(ROOT).as_posix()+'/') for x in paths)
    manifest=js('input_manifest.json')
    for path,h in manifest['pipeline_hashes'].items():assert sha(blob(TARGET,path))==h,path
    for name,h in js('outputs/output_hashes.json').items():assert sha((PKG/'outputs'/name).read_bytes())==h,name
    result['raw_hash_checks']=[]
    if args.raw:
        for rec in manifest['files']:
            assert sha((args.raw/rec['name']).read_bytes())==rec['sha256']
            result['raw_hash_checks'].append(rec['name'])
    rates=table('derived_rates.csv');quality=table('input_quality.csv')
    assert len(rates)==len(quality)==1440
    assert sha((PKG/'derived_rates.csv').read_bytes())=='e3a1ce8f2a33cd9a60b22039c86ae8f1f7214458850d5a0b609042eace1bc3ac'
    nu=[];times=[]
    for row,q in zip(rates,quality):
        E,W=float(row['lambda_bit_E_s_1']),float(row['lambda_bit_W_s_1'])
        n=float(row['nu_array_s_1']);close(n,524288*32*(E+W)/2)
        assert n>=0 and row['valid']=='True' and q['east_valid']==q['west_valid']=='True'
        assert q['ignored_dqf_E']==q['ignored_dqf_W']=='0'
        times.append(datetime.fromisoformat(row['timestamp_utc']));nu.append(n)
        assert (datetime.fromisoformat(row['end_utc'])-times[-1]).total_seconds()==300
    assert all((b-a).total_seconds()==300 for a,b in zip(times,times[1:]))
    candidates=[(j,300*sum(nu[j:j+12]),300*(sum(nu[j+6:j+12])-sum(nu[j:j+6]))) for j in range(1429)]
    picked=[max(candidates,key=lambda r:(r[2],-r[0]))[0],max(candidates,key=lambda r:(r[1],-r[0]))[0],sorted(candidates,key=lambda r:(r[1],r[0]))[714][0]]
    assert picked==[732,753,157]
    result['selection_indices']=picked
    result['fallback_counts']={d:sum(x['retrospective_bridge_'+d]=='True' for x in rates) for d in ['E','W']}
    archives=js('outputs/raw_results_manifest.json'); windows=js('selected_windows.json')['windows']
    for case,rec in zip(['growth','peak','typical'],archives):
        path=args.data/(case+'_trials.npz');assert sha(path.read_bytes())==rec['sha256']
        with np.load(path,allow_pickle=False) as z:arrays={k:z[k] for k in z.files}
        for k,v in arrays.items():assert sha(v.tobytes())==rec['arrays'][k]['sha256'],k
        S=arrays['samples'];assert S.shape==(20000,5,8) and np.isfinite(S).all()
        assert np.isin(S[:,:,0],[0,1]).all() and np.all(S[:,:,1]==np.floor(S[:,:,1]))
        pol={r['policy']:r for r in table('outputs/'+case+'_policies.csv')}
        paired={r['comparator']:r for r in table('outputs/'+case+'_paired.csv')}
        summary={'case':case,'failures':[],'pairs':[]}
        for j,name in enumerate(NAMES):
            row=pol[name];fail=S[:,j,0].astype(bool);x=S[~fail,j,1];k=int(fail.sum());summary['failures'].append(k)
            assert k==int(row['first_Ecap']) and len(x)==int(row['survivors']) and int(row['computational_failures'])==0
            for key,val in zip(['F95_low','F95_high'],cp(k,20000,.05)):close(row[key],val)
            for key,val in zip(['passes_survivor95_low','passes_survivor95_high'],eb(x,.05)):close(row[key],val)
            close(row['passes_survivor_mean'],sum(map(int,x))/len(x));close(row['passes_stop_mean'],S[:,j,1].mean())
            for key,col in [('busy_stop_mean_s',2),('reads_stop_mean',3),('writes_stop_mean',4)]:close(row[key],S[:,j,col].mean())
            close(row['partial_reads_stop_mean'],(S[:,j,3]-S[:,j,1]*2097152).mean())
            close(row['partial_writes_stop_mean'],(S[:,j,4]-S[:,j,1]*2097152).mean())
            if j<2:
                for key,val in zip(['primary_family_low','primary_family_upper'],cp(k,20000,.05/12)):close(row[key],val)
        for j in [1,4]:
            a,b=S[:,0,0].astype(bool),S[:,j,0].astype(bool)
            J=~a&~b;plus=int((a&~b).sum());minus=int((~a&b).sum());both=int((a&b).sum())
            cells=[int(J.sum()),plus,minus,both];row=paired[NAMES[j]]
            assert cells==[int(row[k]) for k in ['both_survive','proposed_only_Ecap','comparator_only_Ecap','both_Ecap']]
            x,y=S[J,0,1],S[J,j,1];gain=1-sum(map(int,x))/sum(map(int,y));diff=(plus-minus)/20000
            close(row['G_J'],gain);close(row['proposed_minus_comparator_risk'],diff)
            close(row['proposed_passes_on_J'],x.mean());close(row['comparator_passes_on_J'],y.mean())
            for alpha,prefix in [( .05,'nominal'),(.05/12,'family')]:
                lp,up=cp(plus,20000,alpha/2);lm,um=cp(minus,20000,alpha/2)
                xl,xu=eb(x,alpha/2);yl,yu=eb(y,alpha/2)
                dint=[lp-um,up-lm];gint=[1-xu/yl,1-xl/yu]
                if prefix=='nominal':keys=['risk_diff95_low','risk_diff95_high','G95_low','G95_high']
                else:keys=['primary_family_risk_diff_low','primary_family_risk_diff_high','primary_family_G_low','primary_family_G_high']
                if prefix=='nominal' or j==1:
                    for key,val in zip(keys,dint+gint):close(row[key],val)
                if (j==1 and prefix=='family') or (j==4 and prefix=='nominal'):
                    summary['pairs'].append(dict(comparator=NAMES[j],level=prefix,cells=cells,G=gain,G_interval=gint,risk_diff=diff,risk_interval=dint))
            for key,val in zip(['saved_passes95_low','saved_passes95_high'],eb(y-x,.05,-17988,17988)):close(row[key],val)
        w=next(w for w in windows if case in w['labels']);r=w['nu_array_s-1']
        key=int(datetime.fromisoformat(w['utc']).timestamp())//300
        assert key==int(arrays['utc_index'])
        nearest=.1
        for trial in range(20000):
            ev=stream(r,key,trial)
            assert sha(b''.join(x.tobytes() for x in ev))==arrays['event_hashes'][trial]
            assert len(ev[0])==arrays['event_counts'][trial]
            if len(ev[0]):nearest=min(nearest,float(np.abs(ev[0]-.1*np.rint(ev[0]/.1)).min()))
        summary['all_stream_hashes_verified']=20000;summary['nearest_event_to_0p1_grid_s']=nearest
        assert nearest>1e-12
        q=fixed300(r);published=js('outputs/'+case+'_run.json')['fixed300']
        assert q==F(int(published['exact_numerator']),int(published['exact_denominator']))
        assert F(published['upper_decimal_ceiling'])>=q and F(float(published['upper']))>=q
        assert q<F(1,10)
        summary['fixed300_exact']=str(q);summary['fixed300_upper']=published['upper_decimal_ceiling']
        result['cases'].append(summary);print(case,'PASS',flush=True)
    result['status']='PASS';args.out.write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
