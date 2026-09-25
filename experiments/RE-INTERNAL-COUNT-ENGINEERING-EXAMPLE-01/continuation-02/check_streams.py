"""Generator first-moment and uniform singleton mark diagnostics."""
import hashlib,json,copy
import numpy as np
from scipy.stats import chi2
from reference import ROOT,config,packed,accepted
import engine

def main():
    c=config();c['horizon_seconds']=10.;statistics=[]
    for case in range(3):
        total=expected=variance=0.;bits=bit_expected=0.;bit_values=[]
        cells=np.zeros(39,int)
        for trial in range(500):
            s=engine.stream(592317,case,trial,c)
            exposure=sum((r[1]-r[0])*r[3] for r in s[5]);total+=s[6];expected+=exposure;variance+=exposure
            observed=sum(int(m).bit_count() for m in s[3]);bits+=observed
            if case==1:
                bit_expected+=exposure
                for m in s[3]:cells[int(m).bit_length()-1]+=1
            else:
                meta=json.loads((ROOT/'inputs/manifest.json').read_text())
                groups=meta['merged_groups' if case==2 else 'groups']
                wanted=exposure*(meta['raw_bits']/groups)*13/64
                bit_expected+=wanted;bit_values.append(observed-wanted)
            if trial==0:
                before=hashlib.sha256(b''.join(x.tobytes() for x in s[:4])).hexdigest()
                p=packed();p.horizon=10.
                for policy in ([0,0,0,0,0,0,0],[1,0,0,0,0,0,0],[2,1,1,0,0,0,0]):engine.run(*s[:4],np.array(policy,float),accepted.args(p),8e-8)
                after=hashlib.sha256(b''.join(x.tobytes() for x in s[:4])).hexdigest()
                assert before==after
        standardized=(total-expected)/np.sqrt(variance)
        assert abs(standardized)<6
        item=dict(case=c['cases'][case],parent_count=total,conditional_expected_parents=expected,parent_standardized_residual=standardized,protected_bits=bits,expected_protected_bits=bit_expected)
        if case==1:
            statistic=float(((cells-cells.mean())**2/cells.mean()).sum());pvalue=float(chi2.sf(statistic,38));assert pvalue>1e-6
            item.update(uniform_lane_chi2=statistic,uniform_lane_p=pvalue)
        else:
            z=float(np.sum(bit_values)/(np.std(bit_values,ddof=1)*np.sqrt(len(bit_values))));assert abs(z)<6
            item['compound_mark_first_moment_standardized_residual']=z
        statistics.append(item)
    result=dict(trials_per_case=500,horizon_s=10,seed=592317,diagnostics=statistics,common_stream_immutable_after_each_policy=True,scope='addressed RNG diagnostics; physical law assumed, not validated by this test')
    (ROOT/'outputs/stream_checks.json').write_text(json.dumps(result,indent=2)+'\n',newline='\n');print(json.dumps(result,indent=2))

if __name__=='__main__':main()
