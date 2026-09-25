"""Decimal integration, component fsum, CLI mutations and exact window probes.

Does not import cw_calculate, selected_recovery or historical risk calculators.
This is a RE check, not an independent appointed Scientific Review.
"""
import csv, copy, hashlib, json, math, subprocess, sys, tempfile
from decimal import Decimal as D, localcontext, Inexact
from fractions import Fraction as F
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent

def cli(*args):return subprocess.run([sys.executable,'-B',str(HERE/'cw_calculate.py'),*args],capture_output=True,text=True)

def eq_fraction_decimal(s,d):
    n,_,q=s.partition('/');return D(n)==d*D(q or '1')

def window_exposure(blocks,phase,delay):
    total=F(0);end=F(len(blocks)*3);c=phase
    while c<end:
        for j,r in enumerate(blocks):
            length=max(F(0),min(c+delay,end,F(3*(j+1)))-max(c,F(3*j)))
            total+=length*r
        c+=1
    return total

def main():
    rows=list(csv.DictReader((HERE/'selected_rate.csv').open()));result=json.loads((HERE/'recovery/outputs/cw_bounds.json').read_text());checks={}
    with localcontext() as ctx:
        ctx.prec=200;ctx.traps[Inexact]=True
        I1=D(0);I2=D(0)
        for row in reversed(rows):
            r=D(row['nu_C_bit_DREG_s_1'])/D(16777216)
            if r!=D(row['r_bit_s_1']):raise ValueError('independent normalization')
            I1+=D(300)*r;I2+=D(300)*r*r
        exact={'I1':I1,'I2_s_1':I2,'a':D(524288*496)*I2,'b_s_1':D(31*524288)*I1}
        for k,x in exact.items():
            checks[k+'_independent_exact']=eq_fraction_decimal(result[k]['exact'],x)
            lo=D(result[k]['lower']);hi=D(result[k]['upper']);checks[k+'_outward']=lo<=x<=hi and hi-lo<=D('1e-40')
    # Separate energy-component accumulation, same frozen numerical inputs.
    z=np.load(HERE/'recovery/outputs/selected_energy_contributions.npz',allow_pickle=False);weights=z['mreg']/z['kbar'];maxrel=0.
    for i,row in enumerate(rows):
        vals=[]
        for d in range(2):
            vals.append(math.fsum([float(x)*float(w) for x,w in zip(z['density'][i,d],weights)]+[float(z['highbit'][i,d])*float(weights[-1])]))
        x=math.fsum(vals)/2;y=float(row['nu_C_bit_DREG_s_1']);maxrel=max(maxrel,abs(x-y)/y if y else abs(x-y))
    checks['DREG_component_fsum']=maxrel<=1e-12
    threshold=result['domain'].get('delta_limit_s')
    if threshold is not None and 0<=F(threshold['exact'])<1:
        t=F(threshold['exact']);a=result['a_upper'];b=result['b_upper_s_1']
        p=cli('query','--a',a,'--b',b,'--delta',str(t))
        q=json.loads(p.stdout) if p.returncode==0 else {}
        checks['production_threshold_equality']=q.get('sufficient') is True and F(q['signed_slack']['exact'])==0
        t2=min((t+1)/2,t+F(1,10**30))
        p=cli('query','--a',a,'--b',b,'--delta',str(t2))
        q=json.loads(p.stdout) if p.returncode==0 else {}
        checks['production_above_threshold']=q.get('sufficient') is False and F(q['signed_slack']['exact'])<0
    probes=[('zero', '0','0','0','0.001',True),('equality','0.001','0','0','0',True),('negative_slack','0.002','0','0','0',False),('only_delta0','0.001','1','0','0',True),('above_delta0','0.001','1','1e-10','0',False),('threshold_equal','0','0.001','0.5','0.0005',True),('threshold_over','0','0.001','0.5','0.0005000001',False),('saturation','0','2','0.9','0',False),('strict_near_tau','0','0','0.999999','0',True)]
    for name,a,b,d,c,expected in probes:
        p=cli('query','--a',a,'--b',b,'--delta',d,'--coverage',c)
        q=json.loads(p.stdout) if p.returncode==0 else {};checks['boundary_'+name]=q.get('sufficient')==expected
        if name=='negative_slack':checks['negative_slack_retained']=F(q['signed_slack']['exact'])<0
        if name=='saturation':checks['saturation_signed_value']=F(q['signed_slack']['exact'])==F(-999,1000)
    for name,a,b,d,c in [('tau','0','0','1','0'),('negative_delta','0','0','-1','0'),('negative_coverage','0','0','0','-1'),('negative_coefficient','-1','0','0','0')]:
        checks['reject_'+name]=cli('query','--a',a,'--b',b,'--delta',d,'--coverage',c).returncode!=0
    # Production-linked bad-input tests call the real CLI, not a mirrored validator.
    with tempfile.TemporaryDirectory(dir=HERE/'recovery') as td:
        for name in ['missing','duplicate','no_division','double_division','negative','nan','wrong_duration','wrong_window']:
            bad=copy.deepcopy(rows)
            if name=='missing':bad.pop()
            elif name=='duplicate':bad[1]['timestamp_utc']=bad[0]['timestamp_utc']
            elif name=='no_division':bad[0]['r_bit_s_1']=bad[0]['nu_C_bit_DREG_s_1']
            elif name=='double_division':
                with localcontext() as c:
                    c.prec=120;bad[0]['r_bit_s_1']=str(D(bad[0]['r_bit_s_1'])/D(16777216))
            elif name=='negative':bad[0]['nu_C_bit_DREG_s_1']='-1'
            elif name=='nan':bad[0]['nu_C_bit_DREG_s_1']='NaN'
            elif name=='wrong_duration':bad[0]['duration_s']='299'
            else:bad[0]['timestamp_utc']='2026-01-19T03:55:00+00:00'
            p=Path(td)/(name+'.csv')
            with p.open('w',newline='') as f:
                w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(bad)
            checks['mutation_'+name]=cli('calculate','--input',str(p),'--output',str(Path(td)/'out.json')).returncode!=0
        # All-zero valid series tests the zero-coefficient domain at calculator level.
        zero=copy.deepcopy(rows)
        for row in zero:row['nu_C_bit_DREG_s_1']=row['r_bit_s_1']='0'
        p=Path(td)/'zero.csv'
        with p.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(zero)
        q=cli('calculate','--input',str(p),'--output',str(Path(td)/'zero.json'))
        zz=json.loads((Path(td)/'zero.json').read_text()) if q.returncode==0 else {}
        checks['zero_series_domain']=zz.get('domain',{}).get('zero_coverage')=='ALL_DELTA_IN_STRICT_DOMAIN'
    phases=[F(0),F(1,3),F(17,19)];delays=[F(0),F(1,7),F(999,1000)]
    window_cases=[]
    for phase in phases:
        for delay in delays:
            x=window_exposure([F(2),F(5)],phase,delay);upper=delay*21
            window_cases.append(dict(phase=str(phase),delay=str(delay),actual=str(x),duty_upper=str(upper)))
    checks['window_boundary_duty']=all(F(x['actual'])<=F(x['duty_upper']) for x in window_cases)
    # Arbitrary-rate negative regression: r=1 only on [0,1/4], potential window [0,1/4].
    checks['average_duty_not_general']=F(1,4)>F(1,4)*F(1,4)
    checks['production_duty_alignment']=len(rows)*300==86400 and all(r['duration_s']=='300' for r in rows)
    report={'checks':checks,'all_pass':all(checks.values()),'independent_integrals':{k:str(v) for k,v in exact.items()},'DREG_component_max_relative_difference':maxrel,'window_cases':window_cases,'independence':'Decimal reverse-order finite-decimal sums with Inexact trap; no main-calculator import. CLI mutation/boundary tests; Fraction window intersections. Shared model/constants/CSV and Python runtime remain.','scientific_review':'NOT_ASSIGNED; RE verification only'}
    (HERE/'recovery/outputs/independent_validation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'all_pass':report['all_pass'],'checks':len(checks),'DREG_component_max_relative_difference':maxrel}))
    if not report['all_pass']:raise ValueError('independent checks failed')

if __name__=='__main__':main()
