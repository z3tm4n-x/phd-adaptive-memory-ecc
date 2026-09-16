"""Whole-test input bootstrap and conservative direct-hit model diagnostic."""
import json
import numpy as np
from scipy.linalg import expm
from scipy.stats import chi2
from reference import ROOT,config

def first_passage_lower(rate,H,D):
    Q=np.array([[-1/D-.1*rate,1/D],[1/D,-1/D-rate]])
    return float(1-np.array([.5,.5])@expm(Q*H)@np.ones(2))

def main():
    m=json.loads((ROOT/'inputs/manifest.json').read_text());c=config();tests=m['tests'];n=len(tests)
    values=np.array([[t['duration_s'],t['fluence_cm2'],t['bits'],t['groups'],t['double_words']] for t in tests])
    rng=np.random.default_rng(c['simulation']['input_bootstrap_seed'])
    sampled=values[rng.integers(n,size=(c['simulation']['input_bootstraps'],n))].sum(axis=1)
    b=sampled[:,2]/sampled[:,0]*39/64;group=3*sampled[:,3]/sampled[:,0]
    # A native double-word template on data chip 0 or 1, translated into active
    # quarter. Even conditioned on survival and any dirty-word state, at most
    # 2 of 16 common lane shifts cancel the existing bit; >=7/8 cause E_cap.
    # Ignore chip2 and any additional words: conservative for this model only.
    rate=values[:,4].sum()/values[:,0].sum()*2*.25*7/8
    bootstrap_rate=sampled[:,4]/sampled[:,0]*2*.25*7/8
    k=int(values[:,4].sum());T=values[:,0].sum()
    poisson_low=.5*chi2.ppf(.025,2*k)/T*2*.25*7/8
    result=dict(bootstrap_unit='whole static test, 60 iid/exchangeable tests assumed; systematic facility calibration not included',bootstrap_replicates=len(b),protected_high_bit_rate=float(c['environment']['b_high']),bit_rate_percentile95=np.quantile(b,[.025,.975]).tolist(),all_chip_group_rate_percentile95=np.quantile(group,[.025,.975]).tolist(),native_double_words=k,direct_lower_killing_rate_high=rate,direct_model_risk_lower=first_passage_lower(rate,c['horizon_seconds'],60),bootstrap_direct_lower_percentile95=np.quantile([first_passage_lower(r,c['horizon_seconds'],60) for r in bootstrap_rate],[.025,.975]).tolist(),poisson_count_sensitivity='additional Poisson/exposure assumption for rare observed double-word templates, not certified incident particles',poisson_count_lower95_rate=poisson_low,poisson_count_lower95_model_risk=first_passage_lower(poisson_low,c['horizon_seconds'],60),interpretation='diagnostic applies only to declared native-word-merged model; no physical lower bound for the chip; not a new RES theorem')
    (ROOT/'outputs/input_sensitivity.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
