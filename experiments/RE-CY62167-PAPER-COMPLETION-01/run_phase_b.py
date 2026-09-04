from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from cosrad_parser import load_package,scenario_manifest,SHIELDS
from cosrad_operator import operator_closure
from cosrad_rate_reconstruction import *
from cosrad_event_mixture import event_weights
from phase_b_core import *
from phase_b_reporting import figure_outputs,write_status_and_manifests

HERE=Path(__file__).resolve().parent

def main(argv=None):
    ap=argparse.ArgumentParser();ap.add_argument('--cosrad-results',required=True,type=Path);args=ap.parse_args(argv)
    pkg=load_package(args.cosrad_results)
    (HERE/'pi_cosrad_input_manifest.json').write_text(json.dumps(scenario_manifest(pkg),indent=2,sort_keys=True)+'\n')
    write_csv(HERE/'cosrad_member_manifest.csv',pkg.members)
    closure=operator_closure(pkg);write_csv(HERE/'cosrad_operator_closure_full.csv',closure)
    cdf=pd.DataFrame(closure);cs=[]
    for (env,thr),g in cdf.groupby(['environment','threshold_MeV_cm2_mg']):
        cs.append({'environment':env,'threshold_MeV_cm2_mg':thr,'shield_count':len(g),'max_absolute_relative_difference':float(g.absolute_relative_difference.max()),'mean_absolute_relative_difference':float(g.absolute_relative_difference.mean()),'closure_status':'PASS' if (g.closure_status=='PASS').all() else 'SPECTRAL_OPERATOR_NOT_CLOSED'})
    write_csv(HERE/'cosrad_operator_closure.csv',cs)
    closure_status='PASS' if all(x['closure_status']=='PASS' for x in closure) else 'SPECTRAL_OPERATOR_NOT_CLOSED'
    groups=load_phase_a(HERE/'cosrad_input_cross_sections.csv')
    sg=spectral_rows(pkg,groups,'GCR');ss=spectral_rows(pkg,groups,'SEP')
    bg,bapprox,bstab=basis_rows(pkg,groups,'GCR');bs,_,_=basis_rows(pkg,groups,'SEP')
    rates=sg+bg;write_csv(HERE/'cosrad_rates_pi_reconstructed_full.csv',rates);write_csv(HERE/'cosrad_rates_pi_reconstructed.csv',sg)
    sep=[{'shield_g_cm2':r['shield_g_cm2'],'mapping_id':r['mapping_id'],'estimate_type':r['estimate_type'],'nu_direct_peak_s-1':r['nu_direct_total_s-1'],'nu_accumulation_peak_s-1':r['nu_accumulation_total_bit_s-1'],'rate_reconstruction_route':r['rate_reconstruction_route'],'status':'PEAK-RATE-DIAGNOSTIC; NO-MISSION-INTEGRATION-WITHOUT-DURATION'} for r in ss+bs]
    write_csv(HERE/'sep_peak_rates_full.csv',sep);write_csv(HERE/'sep_peak_rates.csv',[x for x in sep if x['rate_reconstruction_route']=='SPECTRAL_EXTERNAL_CONVOLUTION'])
    write_csv(HERE/'basis_target_approximation.csv',bapprox);write_csv(HERE/'basis_reconstruction_stability.csv',bstab)
    bounds=make_bounds(rates);write_csv(HERE/'geo_bound_results_full.csv',bounds);article=[x for x in bounds if x['rate_reconstruction_route']=='SPECTRAL_EXTERNAL_CONVOLUTION'];write_csv(HERE/'geo_bound_results.csv',article)
    refs=make_references(bounds);write_csv(HERE/'geo_reference_results_full.csv',refs);write_csv(HERE/'geo_reference_results.csv',[x for x in refs if x['rate_reconstruction_route']=='SPECTRAL_EXTERNAL_CONVOLUTION'])
    resources=resource_rows(bounds);write_csv(HERE/'resource_results_full.csv',resources)
    rd=pd.DataFrame([x for x in resources if x['mapping_id']=='W_00_01']);cols=['shield_g_cm2','mapping_id','estimate_type','period_source','tau_s','scan_mode','write_policy','reads_per_cycle','writes_per_cycle_or_expected','t_read_effective_s','t_write_effective_s','tau_min_arch_s','resource_margin','period_feasible','architecture_status','reads_per_s','writes_per_s','interface_fraction','interface_percent'];rd[cols].to_csv(HERE/'resource_results.csv',index=False,float_format='%.6g')
    write_csv(HERE/'shielding_boundary_summary.csv',boundary_rows(bounds));write_csv(HERE/'accumulation_interpolation_sensitivity.csv',accumulation_sensitivity(pkg,groups))
    ew=event_weights(pkg,groups,'GCR')+event_weights(pkg,groups,'SEP');write_csv(HERE/'cosrad_event_weights.csv',ew)
    ewd=pd.DataFrame(ew);ewd[(ewd.mapping_id=='W_00_01')&(ewd.environment_scenario=='GCR_ONLY')&(ewd.shield_g_cm2.isin([2.0,2.5,3.0]))].to_csv(HERE/'cosrad_event_weights_audit_subset.csv',index=False)
    write_csv(HERE/'legacy_article_regression.csv',legacy_rows(pkg,sg,bounds))
    figure_outputs(HERE,bounds,rates,resources);write_status_and_manifests(HERE,pkg,closure,closure_status)

if __name__=='__main__':main()
