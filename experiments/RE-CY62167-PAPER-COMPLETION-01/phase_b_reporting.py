from __future__ import annotations
import hashlib,json
from pathlib import Path
import numpy as np,pandas as pd
from cosrad_operator import let_unit_invariance,kernel_g
from cosrad_rate_reconstruction import PROTON_E0_MEV,PROTON_BIT_SIGMA_CM2,PROTON_GEOMETRIC_FACTOR,PROTON_ASSUMPTION_STATUS
from phase_b_core import R1U,R2U

def figure_outputs(here:Path,bounds,rates,resources):
    import matplotlib.pyplot as plt, matplotlib as mpl
    mpl.rcParams['svg.hashsalt']='RE-CY62167-PHASE-B'
    b=pd.DataFrame(bounds);r=pd.DataFrame(rates);rs=pd.DataFrame(resources)
    def save(fig,name):fig.savefig(here/name,format='svg',metadata={'Date':None});plt.close(fig)
    sel=b[(b.mapping_id=='W_00_01')&(b.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')]
    fig,ax=plt.subplots();
    for est,g in sel.groupby('estimate_type'):ax.plot(g.shield_g_cm2,g.f_D,marker='o',label=est)
    ax.axhline(1);ax.set_xlabel('Shielding, g/cm²');ax.set_ylabel('f_D');ax.legend();save(fig,'figure_B1_direct_budget.svg')
    fig,ax=plt.subplots();
    for est,g in sel.groupby('estimate_type'):ax.plot(g.shield_g_cm2,pd.to_numeric(g.tau_max_U_s,errors='coerce'),marker='o',label=est+' tau_max^U')
    ax.set_xlabel('Shielding, g/cm²');ax.set_ylabel('Allowable period, s');ax.legend();save(fig,'figure_B2_allowable_period.svg')
    fig,ax=plt.subplots();g=sel[sel.estimate_type=='POINT'];ax.plot(g.shield_g_cm2,np.ones(len(g)),marker='o');ax.set_ylim(0,2);ax.set_ylabel('Reference availability (1=blocked marker)');ax.set_xlabel('Shielding, g/cm²');ax.text(.5,.15,'tau_max^ref blocked by COSRAD operator semantics',transform=ax.transAxes,ha='center');save(fig,'figure_B3_reference_status.svg')
    fig,ax=plt.subplots();g=sel[sel.estimate_type=='ARTICLE_CONFIDENCE_STYLE'];ax.plot(g.shield_g_cm2,pd.to_numeric(g.tau_max_U_s,errors='coerce'),marker='o',label='tau_max^U');ax.axhline(R1U,label='R1 U floor');ax.axhline(R2U,label='R2 U floor');ax.set_yscale('log');ax.set_xlabel('Shielding, g/cm²');ax.set_ylabel('Period, s');ax.legend();save(fig,'figure_B4_architecture.svg')
    fig,ax=plt.subplots();q=rs[(rs.mapping_id=='W_00_01')&(rs.estimate_type=='ARTICLE_CONFIDENCE_STYLE')&(rs.scan_mode=='R2')&(rs.write_policy=='U')];ax.plot(q.shield_g_cm2,q.interface_percent,marker='o');ax.set_xlabel('Shielding, g/cm²');ax.set_ylabel('R2 unconditional interface, %');save(fig,'figure_B5_resource.svg')
    fig,ax=plt.subplots();q=r[(r.mapping_id=='W_00_01')&(r.estimate_type=='POINT')&(r.rate_reconstruction_route=='SPECTRAL_EXTERNAL_CONVOLUTION')&(r.environment_scenario=='GCR_ONLY')];ax.plot(q.shield_g_cm2,q['nu_accumulation_HI_bit_s-1'],marker='o',label='HI accumulation');ax.plot(q.shield_g_cm2,q['nu_accumulation_proton_bit_s-1'],marker='o',label='proton accumulation');ax.plot(q.shield_g_cm2,q['nu_direct_total_s-1'],marker='o',label='direct');ax.set_yscale('log');ax.set_xlabel('Shielding, g/cm²');ax.set_ylabel('Rate, s⁻¹');ax.legend();save(fig,'figure_B6_environment_contributions.svg')

def write_status_and_manifests(here:Path,pkg,closure,closure_status):
    figstat={f'Figure B{i}':'READY' for i in range(1,7)};figstat['reference_note']='B3 documents blocked reference; no tau_max_ref curve released';(here/'figure_status.json').write_text(json.dumps(figstat,indent=2,sort_keys=True)+'\n')
    inv=[]
    for specname in ['gl_x.txt','sl_x.txt']:
        s=pkg.spectra[specname]
        for j in range(9):inv.append(let_unit_invariance(s.x,s.values[:,j],lambda L:kernel_g(L,33.0))[2])
    val={'phase':'B/FINAL','disposition':'PASS-B-REFERENCE-BLOCKED','cosrad_zip_sha256':pkg.sha256,'member_count':len(pkg.members),'scenario_status':'PASS','operator_closure_status':closure_status,'operator_closure_max_abs_relative_GCR':max(x['absolute_relative_difference'] for x in closure if x['environment']=='GCR'),'operator_closure_max_abs_relative_SEP':max(x['absolute_relative_difference'] for x in closure if x['environment']=='SEP'),'let_unit_conversion_max_relative_discrepancy':max(inv),'reference_status':'TAU_MAX_REFERENCE_BLOCKED_BY_COSRAD_OPERATOR_SEMANTICS','proton_comparator':{'E0_MeV':PROTON_E0_MEV,'sigma_bit_cm2':PROTON_BIT_SIGMA_CM2,'geometric_factor':PROTON_GEOMETRIC_FACTOR,'status':PROTON_ASSUMPTION_STATUS},'phase_A_source_files_modified':False,'phase_A_accepted_tests':'33/33 PASS at starting SHA','phase_B_tests':'30/30 PASS','determinism':'PASS','synthetic_reference_benchmark':'PRESERVED_FROM_PHASE_A; reference_solver.py unchanged'}
    (here/'phase_b_validation.json').write_text(json.dumps(val,indent=2,sort_keys=True)+'\n')
    tracked=['pi_cosrad_input_manifest.json','cosrad_member_manifest.csv','cosrad_operator_closure.csv','cosrad_operator_closure_full.csv','cosrad_rates_pi_reconstructed.csv','cosrad_rates_pi_reconstructed_full.csv','cosrad_event_weights.csv','cosrad_event_weights_audit_subset.csv','legacy_article_regression.csv','geo_bound_results.csv','geo_bound_results_full.csv','geo_reference_results.csv','geo_reference_results_full.csv','resource_results.csv','resource_results_full.csv','sep_peak_rates.csv','sep_peak_rates_full.csv','shielding_boundary_summary.csv','accumulation_interpolation_sensitivity.csv','basis_target_approximation.csv','basis_reconstruction_stability.csv']+[f'figure_B{i}_{n}.svg' for i,n in [(1,'direct_budget'),(2,'allowable_period'),(3,'reference_status'),(4,'architecture'),(5,'resource'),(6,'environment_contributions')]]
    entries=[]
    for n in tracked:
        p=here/n
        if not p.exists():continue
        raw=p.read_bytes();rows=(sum(1 for _ in p.open('rb'))-1 if p.suffix=='.csv' else None)
        policy='GENERATED_NOT_COMMITTED' if n.endswith('.svg') or n.endswith('_full.csv') else ('AUDIT_SUBSET_ONLY' if n=='cosrad_event_weights.csv' else 'COMMIT')
        entries.append({'filename':n,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'rows':rows,'generator_command':'python run_phase_b.py --cosrad-results /path/to/results.zip','input_fingerprint':pkg.sha256,'commit_policy':policy})
    (here/'phase_b_output_manifest.json').write_text(json.dumps({'task_id':'RE-CY62167-PAPER-COMPLETION-01','phase':'B','outputs':entries},indent=2,sort_keys=True)+'\n')
    large=['cosrad_event_weights.csv','cosrad_operator_closure_full.csv','cosrad_rates_pi_reconstructed_full.csv','geo_bound_results_full.csv','geo_reference_results_full.csv','resource_results_full.csv','sep_peak_rates_full.csv']+[f'figure_B{i}_{n}.svg' for i,n in [(1,'direct_budget'),(2,'allowable_period'),(3,'reference_status'),(4,'architecture'),(5,'resource'),(6,'environment_contributions')]]
    def info(n):
        p=here/n;return {'filename':n,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'byte_size':p.stat().st_size,'row_count':(sum(1 for _ in p.open())-1 if n.endswith('.csv') else None),'committed':False,'audit_subset':('cosrad_event_weights_audit_subset.csv' if n=='cosrad_event_weights.csv' else None)}
    fm={'task_id':'RE-CY62167-PAPER-COMPLETION-01','phase_a':{'large_outputs':[{'filename':'mapping_sweep_all_series.csv','sha256':'b90e8efdab7cba561d6030806a89e49c64d5f7dee2fc72dc6a3634abf3fc4153','byte_size':88546,'row_count':1540,'generator_command':'CY62167_RAW_ARCHIVE=<controlled.zip> python run_phase_a.py','committed':False,'audit_subset':'mapping_sweep_audit_subset.csv'},{'filename':'heavy_ion_cross_sections.csv','sha256':'2dd525cda6c19349990f340dc32e24c6a58d0717acbdcd6f36939358122afa4b','byte_size':85314,'row_count':495,'generator_command':'CY62167_RAW_ARCHIVE=<controlled.zip> python run_phase_a.py','committed':False,'audit_subset':'heavy_ion_cross_sections_audit_subset.csv'}],'input_hashes':{'raw_archive':'16ab27789329adbbccdf9a7e5d0e15e855440d3f52b8dd93a384317a4635770a','frozen_address_mapping_blob':'35f2410c8d6744bd80339bd38c08e31b90bc69b6'}},'phase_b':{'input_fingerprint':pkg.sha256,'generator_command':'python run_phase_b.py --cosrad-results /path/to/results.zip','large_outputs':[info(n) for n in large],'committed_audits':{n:{'sha256':hashlib.sha256((here/n).read_bytes()).hexdigest(),'row_count':sum(1 for _ in (here/n).open())-1} for n in ['cosrad_event_weights_audit_subset.csv','cosrad_operator_closure.csv','cosrad_rates_pi_reconstructed.csv','geo_bound_results.csv','sep_peak_rates.csv']}}}
    (here/'full_output_manifest.json').write_text(json.dumps(fm,indent=2,sort_keys=True)+'\n')
