"""Read-only Git identities and independently accumulated reference budget."""
import argparse, hashlib, json, math, subprocess
from decimal import Decimal, localcontext
from pathlib import Path
import numpy as np
from scipy.stats import poisson

ROOT=Path(__file__).resolve().parents[3]
REL='experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01/continuation-02'
PKG=ROOT/REL
def js(name):return json.loads((PKG/name).read_text())
def blob(sha,path):return subprocess.check_output(['git','show',sha+':'+path],cwd=ROOT)
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    chain=['268e0d772aa718226ce7d3c2c18ded96306bdcf2','c09928f2ad0e483539426ec2c0d20e84adbb3d86','8ed0035d8b75b43733d9dcce4473835031d21f49','4979ee554fe67796ec5970ad61b41868b9864b59','c277567b86a294adb415cce65df3ea6f44dcb510']
    for parent,child in zip(chain,chain[1:]):assert subprocess.check_output(['git','show','-s','--format=%P',child],cwd=ROOT,text=True).strip()==parent
    changed=subprocess.check_output(['git','diff','--name-only',chain[0],chain[-1]],cwd=ROOT,text=True).splitlines();assert all(p.startswith(REL+'/') for p in changed)
    for f in ['engine.py','reference.py','run_experiment.py','config.json','inputs/templates.npz','outputs/controller_tables.npz','outputs/selected_policies.json']:
        assert blob(chain[2],REL+'/'+f)==blob(chain[-1],REL+'/'+f),(f,'changed after pretest')
    for f in ['config.json','PREREGISTRATION.md','inputs/templates.npz']:
        assert blob(chain[1],REL+'/'+f)==blob(chain[-1],REL+'/'+f)
    prov=js('outputs/provenance.json');checked=0
    for f,h in prov['code_sha256'].items():assert hashlib.sha256((PKG/f).read_bytes()).hexdigest()==h;checked+=1
    for f,rec in prov['artifacts'].items():assert hashlib.sha256((PKG/f).read_bytes()).hexdigest()==rec['sha256'];checked+=1
    for f,rec in prov['source_identities'].items():assert hashlib.sha256(blob(chain[-1],f)).hexdigest()==rec['sha256'];checked+=1
    cert=js('outputs/reference_certificate.json')
    for f,h in cert['accepted_source_sha256'].items():assert hashlib.sha256((ROOT/'experiments/RE-INTERNAL-COUNT-CONTROL-01'/f).read_bytes()).hexdigest()==h
    with np.load(PKG/'outputs/controller_tables.npz') as z:a={k:z[k] for k in z.files}
    kernels=a['kernels'];K=12
    with localcontext() as ctx:
        ctx.prec=70
        mass=max(abs(sum((Decimal(float(x)) for x in kernels[j,:,i,:].flat),Decimal(0))-1) for j in range(12) for i in range(26))
    posterior_min=1.
    for j in range(12):
        for y in range(33):
            block=kernels[j,y]
            for i in range(26):
                if y<32 and i%13>y:assert np.all(block[i]==0)
                else:
                    assert np.all(block[i]>0);posterior_min=min(posterior_min,float((block[i]/math.fsum(block[i])).min()))
    minimum=float(kernels[kernels>0].min());assert posterior_min*minimum>np.finfo(float).tiny
    # Decimal moments, forward propagation of the initial distribution and
    # accumulated reward, instead of production backward V/affine compression.
    with localcontext() as ctx:
        ctx.prec=65;D=Decimal;lo=D(float(a['low']));hi=D(float(a['high']));h=D('.5');k=D(2)/60
        m=(hi+lo)/2;d=(hi-lo)/2;A=(1-(-k*h).exp())/k;B=(h-A)/k
        first=[m*h-d*A,m*h+d*A];second=[m*m*h*h+2*d*d*B-2*m*d*h*A,m*m*h*h+2*d*d*B+2*m*d*h*A]
        reward=np.array([float((kk*first[zz]+second[zz]/2)/524288) for zz in range(2) for kk in range(13)])
    q=a['initial'].copy();potential=0.;idx=int(np.flatnonzero(a['periods']==.5)[0]);transition=a['transition'][idx]
    for _ in range(3600):potential+=math.fsum(q*reward);q=q@transition
    assert abs(potential-cert['backup_potential'])<1e-12
    cfg=js('config.json');P=cfg['memory']['pass_seconds'];hi=cfg['environment']['b_high'];lo=cfg['environment']['b_low'];nu=P/60;v=(hi-lo)*P;N=9000
    model=N*(poisson.sf(2,nu)+math.exp(-nu)*nu*(4*v+4*v*v)/(24*512**2)+math.exp(-nu)*nu**2/2*(40*v+40*v*v)/(24*128**2)+P*(hi+nu*(hi-lo))/(4*524288**2)+poisson.sf(12,hi*P/2))
    delta=model+.0003;slack=.1-delta-potential
    assert abs(delta-cert['delta'])<1e-15 and abs(slack-cert['initial_slack'])<1e-12
    with np.load(PKG/'outputs/illustration.npz') as illustration:
        trace=illustration['trace'];last=trace[-1]
        incomplete=np.flatnonzero(trace[:,2]+1e-10<trace[:,0]+trace[:,1])
        assert incomplete.tolist()==[len(trace)-1]
        illustration_note={'rows':len(trace),'completed_passes':int(illustration['result'][2]),'last_start':float(last[0]),'last_nominal_period':float(last[1]),'last_stop':float(last[2]),'plotted_terminal_count':float(last[3]),'terminal_count_is_observation':False}
    result=dict(status='PASS_WITH_MINOR_FIGURE_LABEL',ancestry=chain,hashed_objects=checked,frozen_pretest_objects=7,decimal_row_mass_error=str(mass),minimum_kernel=minimum,uniform_positive_posterior_lower=posterior_min,min_product=posterior_min*minimum,forward_backup_potential=potential,delta=delta,slack=slack,illustration=illustration_note,shared='published transition matrices; forward propagation and Decimal rewards independent of production V recurrence; no assertion of physical calibration')
    args.out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
