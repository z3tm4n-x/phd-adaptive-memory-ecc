"""Run the unmodified pinned entry point and independently qualify its output."""
import argparse, hashlib, importlib.metadata, json, os, platform, subprocess, sys, time
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
RADAR='b032505d4d1b15403b8ad06aef578339f6d1c6b4'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--radar-root',type=Path,required=True);ap.add_argument('--validate-only',action='store_true');a=ap.parse_args()
    root=a.radar_root.resolve();out=HERE/'recovery/outputs';out.mkdir(exist_ok=True)
    if subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()!=RADAR:raise ValueError('RADAR HEAD')
    if subprocess.check_output(['git','-C',str(root),'diff','HEAD','--']):raise ValueError('RADAR tracked edits')
    sources=json.loads((HERE/'recovery/source_manifest.json').read_text())
    for entry in sources:
        if hashlib.sha256((HERE/entry['package_path']).read_bytes()).hexdigest()!=entry['sha256']:raise ValueError('source identity')
    env=dict(os.environ);env['PYTHONDONTWRITEBYTECODE']='1';env['PYTHONPATH']=str(root/'src')+os.pathsep+env.get('PYTHONPATH','')
    if a.validate_only:
        info=json.loads((out/'transport_execution.json').read_text())
    else:
        info={'python':sys.version,'platform':platform.platform(),'packages':{n:importlib.metadata.version(n) for n in ['numpy','scipy','pandas','pydantic','pytest']},'preexecution_head':subprocess.check_output(['git','-C',str(HERE),'rev-parse','HEAD'],text=True).strip(),'start_unix':time.time()}
        (out/'transport_execution.json').write_text(json.dumps(info,indent=2)+'\n')
        tests=['test_proton_al_shielding.py','test_proton_al_survival.py','test_proton_al_secondary.py']
        with (out/'historical_tests.log').open('w') as log:
            subprocess.run([sys.executable,'-B','-m','pytest','-q','-p','no:cacheprovider',*[str(root/'tests'/t) for t in tests]],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
        with (out/'transport_build.log').open('w') as log:
            subprocess.run([sys.executable,'-B',str(HERE/'recovery/historical/radar_converged.py'),'--radar-root',str(root),'--sigma-csv',str(HERE/'recovery/historical/sigma_bit_experimental.csv'),'--out',str(out)],env=env,stdout=log,stderr=subprocess.STDOUT,check=True)
    z=np.load(out/'radar_transport.npz',allow_pickle=False);v=json.loads((out/'radar_validation.json').read_text())
    checks={'keys':set(z.files)=={'energy_mev','shield_mm','primary','secondary'},'energy':np.array_equal(z['energy_mev'],np.geomspace(.11,390.,192)),'shields':np.array_equal(z['shield_mm'],[0,1,2,3,5,7,10]),'grid_choice':v['grid_points']==192,'depth':v['production_depth_steps']==48,'survival':v['production_survival_steps']==128,'grid_convergence':v['energy_grid_convergence_pass'],'depth_convergence':v['secondary_depth_convergence_pass'],'zero_primary':v['d0_primary_identity_max_abs']<=1e-14,'zero_secondary':v['d0_secondary_max_abs']<=1e-14,'monoenergetic_one_bin':v['monoenergetic_max_relative_peak_error']<=np.expm1(np.log(390/.11)/191)}
    for n in ['primary','secondary']:
        x=z[n];checks[n+'_structure']=x.shape==(7,192,192) and x.dtype==np.float64 and bool(np.isfinite(x).all()) and bool((x>=0).all())
    checks={k:bool(v) for k,v in checks.items()}
    hashes={n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['radar_transport.npz','radar_validation.json']}
    result={'checks':checks,'hashes':hashes,'historical_npz_sha_matches':hashes['radar_transport.npz']=='af35f22ed333150e5ac46df951989811efdef31ee8e9c517f121e5f0853c9cb6','historical_json_sha_matches':hashes['radar_validation.json']=='c7b01f28d8fd395f62be32b54413d5e38c461d2e18aa779321ea03f6eea3f772','structural_numerical_gate_pass':all(checks.values()),'elapsed_s':time.time()-info['start_unix']}
    (out/'transport_qualification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
    if not all(checks.values()):raise ValueError('transport gate failed; do not run DREG')

if __name__=='__main__':main()
