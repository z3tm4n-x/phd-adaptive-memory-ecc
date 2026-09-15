"""Only the fixed DREG slice, following frozen energy-level definitions."""
import argparse, ast, csv, dataclasses, json, sys, tempfile
from decimal import Decimal, localcontext
from pathlib import Path
import numpy as np
from input_contract import HERE,TIMES,archive_extract,reference,sources,transport,sha
sys.path.insert(0,str(HERE/'recovery/historical'))
import upstream_interface as u

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--archive',type=Path,required=True);ap.add_argument('--repo',type=Path,required=True);a=ap.parse_args()
    sources();npz=transport();d=HERE/'recovery/outputs';regression=json.loads((d/'upstream_regression.json').read_text())
    if not regression['pass'] or regression['transport_sha256']!=sha(npz):raise ValueError('upstream gate not passed')
    ref=reference(a.repo)
    with tempfile.TemporaryDirectory() as td:
        members=archive_extract(a.archive,a.repo,td);full=u.load_goes(td)
    ids=[i for i,t in enumerate(full.times) if t in set(TIMES)]
    if [full.times[i] for i in ids]!=TIMES:raise ValueError('selected coverage')
    gap=u.gap_integrals(full)[ids]
    g=dataclasses.replace(full,times=TIMES,flux=full.flux[ids],p11=full.p11[ids],valid=full.valid[ids])
    if not g.valid.all() or not np.isfinite(g.p11).all() or (g.p11<0).any():raise ValueError('incomplete selected flux')
    z=np.load(npz,allow_pickle=False);E=z['energy_mev'];i=list(z['shield_mm']).index(10.)
    inp=u.reconstruct(g,E)*u.FOUR_PI+u.low_ext(g,E)*u.FOUR_PI
    sig=u.sigma_model(E,'main_loglog');tw=u.trap_weights(E)
    density=np.stack([u.N_BITS*(inp[:,j]@z['primary'][i].T+inp[:,j]@z['secondary'][i].T)*sig[None,:]*tw[None,:] for j in range(2)],axis=1)
    highbit=u.N_BITS*u.FOUR_PI*float(u.sigma_model(np.array([600.]),'main_loglog')[0])*(gap+g.p11)
    upstream=np.sum(density,axis=2)+highbit
    ordinary=np.mean(upstream,axis=1);refv=np.array([float(r['d10_lambda_central_s-1']) for r in ref])
    if not np.all(np.abs(ordinary-refv)<=1e-6*refv):raise ValueError('primary-path upstream regression')
    other=list(csv.DictReader((d/'upstream_regression.csv').open()));other=np.array([float(r['computed_s_1']) for r in other])
    if not np.all(np.abs(ordinary-other)<=1e-12*np.maximum(ordinary,other)):raise ValueError('independent upstream disagreement')
    # Import only exact dreg_grid AST, never risk_bridge.main or its simulation dependencies.
    tree=ast.parse((HERE/'recovery/historical/risk_bridge.py').read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='dreg_grid')
    namespace={'np':np};exec(compile(ast.Module(body=[fn],type_ignores=[]),'frozen:dreg_grid','exec'),namespace)
    raw=list(csv.DictReader((HERE/'recovery/historical/registered_direct_by_energy.csv').open()))
    registered=[{k:float(r[k]) for k in ['energy_mev','p_registered_direct_W32seq','mean_accumulation_bits_per_registered_event']} for r in raw]
    preg,mreg=namespace['dreg_grid'](E,registered);_,kbar=u.multiplicity_grid(E,'K1_only')
    accum=np.sum(density*(mreg/np.maximum(kbar,1e-300))[None,None,:],axis=2)+highbit*mreg[-1]/max(kbar[-1],1e-300)
    direct=np.sum(density*(preg/np.maximum(kbar,1e-300))[None,None,:],axis=2)+highbit*preg[-1]/max(kbar[-1],1e-300)
    if not np.isfinite(accum).all() or (accum<0).any() or not np.array_equal(direct,np.zeros_like(direct)):raise ValueError('DREG validity')
    central=np.mean(accum,axis=1);rows=[]
    for j,t in enumerate(TIMES):
        nu=repr(float(central[j]))
        with localcontext() as ctx:
            ctx.prec=120;r=str(Decimal(nu)/Decimal(16777216))
        rows.append(dict(timestamp_utc=t.isoformat(),duration_s=300,shield_mm=10,sigma_model='main_loglog',direction_scenario='central_mean',scenario='DREG',mapping='W32_seq',nu_C_bit_DREG_s_1=nu,r_bit_s_1=r,r_D_DREG_s_1='0',upstream_total_s_1=repr(float(ordinary[j]))))
    with (HERE/'selected_rate.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    np.savez_compressed(d/'selected_energy_contributions.npz',energy_mev=E,density=density,highbit=highbit,mreg=mreg,kbar=kbar,preg=preg)
    result={'status':'REPRODUCED_FROM_PINNED_SOURCES','historical_full_csv_byte_identity':'NOT_CLAIMED','transport_sha256':sha(npz),'selected_rate_sha256':sha(HERE/'selected_rate.csv'),'rows':288,'start':TIMES[0].isoformat(),'last_block_start':TIMES[-1].isoformat(),'end_exclusive':'2026-01-20T04:00:00+00:00','duration_s':86400,'finite_nonnegative':True,'gaps':0,'duplicates':0,'normalization':'total accumulation data-bit stream / 2^24 exactly in decimal','shared_reference_max_relative_error':float(np.max(np.abs(ordinary-refv)/refv)),'independent_upstream_max_relative_difference':float(np.max(np.abs(ordinary-other)/ordinary)),'data_source_members':members,'environment_note':'full archive only for frozen metadata and fallback population; rates only selected window'}
    (d/'selected_recovery.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['status','selected_rate_sha256','rows','shared_reference_max_relative_error']}))

if __name__=='__main__':main()
