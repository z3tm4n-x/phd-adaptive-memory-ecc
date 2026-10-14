"""Pair first-run inputs, make resources/acceptance explicit; no Q inference."""
import hashlib,json,platform,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ARM=HERE.parent/'t105-arm-rule'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    a=json.loads((HERE/'outputs/cold-adaptive.json').read_text())
    f=json.loads((HERE/'outputs/cold-fixed.json').read_text())
    assert a['input_sha256']==f['input_sha256'],'not comparable inputs'
    assert a['ARM_instructions_including_boot']-a['ARM_instructions_runtime']==f['ARM_instructions_including_boot']
    for p,expected in json.loads((ARM/'outputs/route-reuse.json').read_text())['matched_sha256'].items():
        assert sha(ARM/p)==expected,('STA reuse invalid',p)
    route=json.loads((ARM/'outputs/full-top.json').read_text())
    fields=('mean_bus_fraction','peak_any_1ms_fraction','observed_model_max_application_ns',
            'completed_operations','unfinished_operations_at_horizon','application_completed',
            'ERR_events','first_exceedance_relative_ns')
    # In this cold window the policy must not grant LOW. Equal behavior is
    # expected, but equality is not imposed in any later scenario.
    assert {k:a['check'][k] for k in fields}=={k:f['check'][k] for k in fields}
    out={'scope':'first actual run of scenario4 only; four other scenarios remain',
        'common_input_sha256':a['input_sha256'],
        'comparison':[{k:r['check'][k] for k in ('mode',*fields)} for r in (a,f)],
        'bus_fraction_difference_fixed_minus_adaptive':f['check']['mean_bus_fraction']-a['check']['mean_bus_fraction'],
        'resources_reused_not_resynthesized':route['resources'],'STA_reused_not_rerun':route['timing'],
        'startup_bytes':1268,'firmware_bytes':4244,'OCM_reserved_bytes':57344,
        'CPU_core_allocation_adaptive':1,'CPU_runtime_use_fixed':0,
        'physical_board_available':None,'actual_ARM_time_ns':None,'ARM_WCET_ns':None,
        'software_environment':{'Python':sys.version,'platform':platform.platform()},
        'Q_T_certified_by_emulation':False,'main_modified':False,
        'outputs_sha256':{p.name:sha(p) for p in sorted((HERE/'outputs').glob('*')) if p.name!='summary.json'},
        'remaining':['scenario1 full-timer quiet/false signal','scenario2 extracted accepted temporal profile and normalization',
                     'scenario3 loss/recovery with full holds','scenario5 long-lived data and writes',
                     'long-interval accelerator with production equivalence','all-five resource table and review']}
    (HERE/'outputs/summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
