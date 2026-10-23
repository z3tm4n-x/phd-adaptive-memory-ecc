"""One preregistered cFE design profile; accepted maps/holds are read-only.

Exact counters and rational resource accounts. --probe does not run ERR.
--write evaluates one unchanged informational point after the price gate.
"""
import argparse
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
ACCEPTED = ROOT / 'experiments/t186-method-comparison/code-strength'
sys.path.insert(0, str(ACCEPTED))
import comparison as cmp
import informational

spec = importlib.util.spec_from_file_location('accepted_write_retention',
    HERE.parent / 'write-retention/run.py')
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
NS = cmp.NS


def encoded(x):
    return (json.dumps(x, indent=2, sort_keys=True, default=str) + '\n').encode()


def load():
    manifest = json.loads((HERE / 'frozen-inputs.json').read_text('utf-8'))
    for path, digest in manifest['sha256'].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != digest:
            raise ValueError('Frozen input changed: ' + path)
    p = json.loads((HERE / 'profile.json').read_text('utf-8'))
    cfg = json.loads((ROOT / p['common_input']).read_text('utf-8'))
    accepted = old.numeric(json.loads(
        (HERE.parent / 'write-retention/outputs/result.json').read_text('utf-8')))
    return cfg, p, accepted, manifest


def cyclic_count(H, epoch, phase, cycle, channels):
    """Exactly count [0,H) offers at (m*cycle+j)*epoch+phase, j<channels."""
    if H < 0 or not 0 <= phase < epoch or not 0 < channels <= cycle:
        raise ValueError('Invalid cyclic calendar')
    full, tail = divmod(H, cycle * epoch)
    return full * channels + min(channels, max(0, (tail - 1 - phase) // epoch + 1))


def next_read_epoch(j, cycle, channels):
    """Maintenance reads never occupy one of the runtime slots."""
    pos = j % cycle
    return j + channels - pos if pos < channels else j


def next_offer(t, kind, epoch, read_phase, write_phase, cycle, channels):
    phase = read_phase if kind == 'R' else write_phase
    j = max(0, cmp.ceil(F(t - phase, epoch)))
    if kind == 'R':
        j = next_read_epoch(j, cycle, channels)
    return j * epoch + phase


def workflow(image_words, g):
    """Complete logical copy, file overwrite, two CRCs, validation.

    g scalar transfers per word. Each W is a complete ECC E transaction:
    predecode, merge (if narrow), encode and full payload store.
    """
    for i in range(image_words):
        for byte in range(g):
            yield ('R', 'active', i, 'copy', byte)
            yield ('W', 'inactive', i, 'copy', byte)
    for i in range(image_words):
        for byte in range(g):
            yield ('W', 'inactive', i, 'file', byte)
    for pass_id in ('load_crc', 'validate_crc'):
        for i in range(image_words):
            for byte in range(g):
                yield ('R', 'inactive', i, pass_id, byte)
    for i in range(image_words):
        yield ('R', 'inactive', i, 'range_validation', 0)


def profile_counts(cfg, p):
    r = p['requirements']; a = cfg['application']; H = cfg['mission_s'] * NS
    channels = r['modules'] * r['channels_per_module']
    B = channels * 2 ** r['adc_bits']
    if B * r['copies'] != cfg['words'] or r['output_bits'] != cfg['data_bits']:
        raise ValueError('Profile does not fit the frozen W/data layout')
    if r['acquisition_deadline_ns'] != cfg['constraints']['application_deadline_ns']:
        raise ValueError('Application deadline changed')
    freshness = F(r['staleness_budget_C']) / F(r['temperature_slew_C_per_s'])
    cycle = (freshness * NS - r['acquisition_deadline_ns']) // a['epoch_ns']
    cycle = int(cycle)
    first = a['first_ns'] + a['read_offset_ns']
    nr = cyclic_count(H, a['epoch_ns'], first, cycle, channels)
    # Bucket start exactly at T is not an admitted offer; the first is at R.
    interval = r['maintenance_admission_interval_s'] * NS
    attempts = max(0, (H - 1) // interval)
    g = p['cfe']['transfer_granularity_operations_per_word']['upper']
    mr, mw = (3 * g + 1) * B, 2 * g * B
    startup = p['cfe']['startup_extra_full_loads_upper']
    # Serial worker: every transaction completes before the next is offered.
    # One whole epoch per operation, plus at most channels skipped epochs
    # per block of cycle-channels maintenance opportunities. This bounds any
    # mix of R/W and the initial alignment. CPU/NVM time is an extra addend.
    ops = mr + mw
    max_epochs = ops + channels * (cmp.ceil(F(ops, cycle - channels)) + 1) + 2
    finish = max_epochs * a['epoch_ns'] + cfg['constraints']['application_deadline_ns']
    return dict(channels=channels,values_per_channel=2**r['adc_bits'],
        image_words=B,image_bytes=4*B,images=r['copies'],
        total_data_bytes=4*cfg['words'],raw_encoded_bytes=6*cfg['words'],
        active_unique_data_bytes=4*B,duplicate_or_version_bytes=4*B,
        freshness_limit_s=freshness,cycle_epochs=cycle,
        cycle_s=F(cycle*a['epoch_ns'],NS),
        cycle_with_service_s=F(cycle*a['epoch_ns']+r['acquisition_deadline_ns'],NS),
        runtime_reads=nr,runtime_reads_per_s=F(nr,cfg['mission_s']),
        optional_attempts_upper=attempts,guaranteed_attempts=0,
        maximum_retention_s=cfg['mission_s'],
        g_upper=g,per_attempt_reads=mr,per_attempt_full_E_writes=mw,
        logical_new_file_word_writes_per_attempt=B,
        logical_copy_word_writes_per_attempt=B,
        mission_maintenance_reads_upper=attempts*mr,
        mission_maintenance_writes_upper=attempts*mw,
        startup_reads_upper=startup*mr,startup_writes_upper=startup*mw,
        upper_app_reads=nr+(attempts+startup)*mr,
        upper_app_writes=(attempts+startup)*mw,
        maintenance_bus_schedule_finish_upper_s=F(finish,NS),
        maintenance_CPU_NVM_margin_s=F(r['allowed_update_finish_s'])-F(finish,NS),
        maximum_actual_refresh_gap_s=None,
        startup_before_t0=True,after_A_and_partial_last_attempt_paid=True)


def app_interval(cfg, n, c):
    return dict(
        lower=old.app_cost(cfg,n,c['runtime_reads'],0,'lower'),
        upper=old.app_cost(cfg,n,c['upper_app_reads'],c['upper_app_writes'],'upper'))


def row_fixed(cfg, c, n, fixed):
    price = old.price(cfg,n,1 if n==39 else 2,c['upper_app_reads'],
                      c['upper_app_writes'],fixed)
    app = app_interval(cfg,n,c)
    support_lower = (cmp.service(cfg,n)['lower']['R'] *
                     (cmp.read_bounds(cfg,fixed['k'])['lower'] if fixed else 0) /
                     (cfg['mission_s']*NS))
    price['core_lower'] = app['lower'] + support_lower
    price['app_core_interval'] = app
    price['added_control_core_upper'] = price['core_upper'] - app['upper']
    price['added_control_core_lower'] = support_lower
    price['rates_scope'] = 'upper optional attempts incl paid startup, never stop after A'
    price['payload_buffer_minimum_bytes'] = 100
    risk = fixed['risk'] if fixed else cmp.risk(
        cfg,n,1 if n==39 else 2,cfg['mission_s']*NS,
        cfg['constraints']['application_deadline_ns'])
    return dict(n=n,t=1 if n==39 else 2,k=fixed['k'] if fixed else None,
        risk=risk,sufficient=risk['upper']<=F(cfg['epsilon'])/2,
        admissibility='CONDITIONAL_SUFFICIENT' if risk['upper']<=F(cfg['epsilon'])/2
                      else 'UPPER_FAILS_NOT_EXCLUDED',
        price=price,timing=fixed['timing'] if fixed else None,
        risk_scope='old mandatory support; optional correct E ignored; addresses not conditioned Poisson')


def gate(cfg,p,c,accepted):
    fixed = accepted['fixed_candidates']
    if (fixed['39']['k'],fixed['44']['k']) != (
            p['numerical']['fixed_k39'],p['numerical']['fixed_k44']):
        raise ValueError('Fixed witnesses drifted')
    rows = {name:row_fixed(cfg,c,n,fixed.get(str(n)) if name.startswith('fixed') else None)
            for name,n in (('OFF39',39),('OFF44',44),('fixed39',39),('fixed44',44))}
    floor=app_interval(cfg,39,c)['lower']
    ceiling=rows['fixed44']['price']['core_upper']/floor
    return dict(rows=rows,mandatory_app39_core_lower=floor,
        full_fixed44_over_mandatory_app39_ceiling=ceiling,
        opens_5x_core_search=ceiling>=5,opens_10x_core_search=ceiling>=10,
        whole_hardware_price_ceiling=None,
        scope='uniform upper/lower over admitted workloads; open gate is not achievement')


def retarget_ERR_price(cfg,c,accepted_cost):
    """Keep every accepted ERR support/hold/repair/observation count.

    Replace only the application vector. No hold calculation is rerun.
    Remove old app lower too: no optional attempt is mandatory.
    """
    out=deepcopy(accepted_cost); T=F(cfg['mission_s']); H=T*NS
    s=cmp.service(cfg,39); before=cmp.count_apps(cfg)
    dr=F(c['upper_app_reads'])-before['read']
    dw=F(c['upper_app_writes'])-before['write']
    delta_core=(s['upper']['app_read']*dr+s['upper']['app_write']*dw)/H
    out['core_SRAM_fraction_upper']+=delta_core
    out['all_history_SRAM_core_upper']+=delta_core
    app=app_interval(cfg,39,c)
    out['core_SRAM_fraction_lower']=app['lower']+s['lower']['R']*cmp.read_bounds(cfg,27)['lower']/H
    changes=dict(application_reads=dr/T,application_writes=dw/T,
        decodes=(dr+dw)/T,encodes=dw/T,read_beats=3*(dr+dw)/T,
        write_beats=3*dw/T,turnarounds=dw/T,app_dispatch=(dr+dw)/T)
    for group in ('full_cost_rates','energy_coefficients_per_second'):
        for key,delta in changes.items():
            out[group][key]+=delta
    for key in ('transport_requests','transport_replies'):
        out['energy_coefficients_per_second'][key]+=(dr+dw)/T
    out['CPU_fraction_coefficients']['app_dispatch_ns']+=(dr+dw)/H
    out['codec_busy_fraction']+=(s['decode']*(dr+dw)+s['encode']*dw)/H
    out['payload_data_bytes']=4*(c['upper_app_reads']+c['upper_app_writes'])
    out['payload_rate_Bps']=out['payload_data_bytes']/T
    out['veto_hard_cap_reached_per_s']=(out['all_history_SRAM_core_upper']-
        out['core_SRAM_fraction_upper'])/out['veto_core_fraction_slope_per_notification_per_s']
    # Old address-revisit field is descriptive only; never use it as a
    # promised refresh in the new profile.
    out['adaptive']['app_same_word_revisit_s']=None
    out['adaptive']['application_refresh_guarantee_s']=None
    out['app_core_interval']=app
    out['added_control_core_upper']=out['core_SRAM_fraction_upper']-app['upper']
    out['added_control_core_lower']=out['core_SRAM_fraction_lower']-app['lower']
    out['payload_buffer_minimum_bytes']=100
    out['new_hold_price_integrations']=0
    out['old_hold_price_source']='write-retention/outputs/result.json'
    return out


def extras(cfg,p,c):
    T=F(cfg['mission_s']); a=cfg['application']; r=p['requirements']
    cycles=cmp.ceil(F(c['runtime_reads'],c['channels']))
    loads=c['optional_attempts_upper']+p['cfe']['startup_extra_full_loads_upper']
    B=c['image_words']; g=c['g_upper']
    # Additional software action coefficients are distinct from hardware
    # dispatch/codec counts. Calibrate non-overlapping times/energies.
    actions=dict(thermal_cycles=F(cycles)/T,ADC_samples=F(c['runtime_reads'])/T,
        control_lookups=F(c['runtime_reads'])/T,full_load_attempts=F(loads)/T,
        file_bytes=F(4*B*loads)/T,copy_bytes=F(4*B*loads)/T,
        CRC_bytes=F(8*B*loads)/T,validation_words=F(B*loads)/T)
    return dict(application_software_actions_per_s=actions,
        additional_CPU_fraction_formula='sum(action_rate*disjoint_CPU_ns)/1e9 + OS_background_fraction',
        additional_energy_formula='T*sum(action_rate*incremental_J) + T*background_W',
        bus_formula='target SRAM: known_core + B_controller_on_target + B_aux_on_target; each nonnegative unknown',
        other_bus_occupancy='separate unknown coordinate, not added across different bus capacities',
        memory_formula='6W encoded +100 scratch + M_cFE_registry + M_stacks + M_OS_IO + M_codec + M_policy; adaptive adds 131136 transport/loss bytes',
        raw_encoded_bytes=6*cfg['words'],scratch_minimum_bytes=r['scratch_algorithm_bytes'],
        external_file_payload_bytes_per_attempt=4*B,
        hidden_full_copy_allowed=False,
        initialization_reference_encodes=cfg['words'],
        optional_extra_full_loads_before_t0=p['cfe']['startup_extra_full_loads_upper'],
        file_source_integrity_probability=None,
        hardware_CPU_energy_RAM_LUT_BRAM_feasibility=None,
        no_scalar_weights_or_global_winner=True)


def evaluate(run_ERR):
    cfg,p,accepted,manifest=load(); unchanged=deepcopy(cfg)
    theory=json.loads((HERE/'theory-basis.json').read_text('utf-8'))
    c=profile_counts(cfg,p); screen=gate(cfg,p,c,accepted)
    result=dict(status='CONDITIONAL_CFE_DESIGN_PROFILE_READY_FOR_REVIEW',
        profile_counts=c,screen=screen,full_cost_additional_parameters=extras(cfg,p,c),
        fixed_resources=accepted['codec_resource_models'],
        common_input_unchanged=True,physical_Q=None,profile_accepted=False,
        new_archive_profiles=0,new_hold_refinements=0,new_ERR_risk_calls=0,
        theory_handoff='https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/issues/196#issuecomment-6361394200',
        theory_applicability_status=theory['status'],
        theory_applicability_reply=theory['reply_url'],
        theory_reviewed_input_commit=theory['reviewed_input_commit'],
        numerical_code_independently_reviewed=False)
    if run_ERR and screen['opens_5x_core_search']:
        # Exactly one accepted point, all numerical settings unchanged.
        info=informational.compute(cfg,p['numerical']['adaptive_k'])
        accepted_risk=accepted['holds']['accepted_k27_ordinary_hold_probe']['risk_reused_without_reintegration']
        # PR235 priced the coarser, accepted pilot certificate (2 phase / 16 q
        # cells). The frozen common input uses 8 / 192. A tighter risk upper
        # leaves the accepted, more conservative bad-history price valid;
        # do not silently recompute that price with the new upper.
        if info['risk']['upper']>accepted_risk:
            raise ValueError('New risk upper exceeds the one retained in accepted price')
        cost=retarget_ERR_price(cfg,c,accepted['holds']['theorist_approved_price_followup']['cost'])
        f=screen['rows']['fixed44']['price']; f1=screen['rows']['fixed39']['price']
        comparison=dict(
            fixed44_upper_below_ERR_mandatory_lower=f['core_upper']<cost['core_SRAM_fraction_lower'],
            selected_ERR_gain_vs_fixed44_upper=f['core_upper']/cost['core_SRAM_fraction_lower'],
            selected_fixed39_lower_over_ERR_upper=f1['core_lower']/cost['core_SRAM_fraction_upper'],
            selected_ERR_vs_fixed44_5x_gap_core=cost['core_SRAM_fraction_lower']-f['core_upper']/5,
            fixed44_unpriced_extra_bus_allowance=cost['core_SRAM_fraction_lower']-f['core_upper'],
            scope='selected k27 only; not impossibility of all old-ERR parameters or all adaptive rules; no whole-hardware winner')
        result.update(informational=info,ERR_price=cost,comparison=comparison,new_ERR_risk_calls=1,
            accepted_risk_upper_retained_in_price=accepted_risk,
            price_uses_conservative_accepted_coarse_certificate=True)
    if cfg!=unchanged:
        raise AssertionError('Common input mutated')
    return result


def overview(r):
    c=r['profile_counts']; g=r['screen']
    out=dict(cycle_s=float(c['cycle_s']),runtime_reads_per_s=float(c['runtime_reads_per_s']),
        updates_upper=c['optional_attempts_upper'],
        app39_core_lower=float(g['mandatory_app39_core_lower']),
        fixed44_core_upper=float(g['rows']['fixed44']['price']['core_upper']),
        gain_ceiling=float(g['full_fixed44_over_mandatory_app39_ceiling']),
        maintenance_finish_s=float(c['maintenance_bus_schedule_finish_upper_s']),
        new_ERR_risk_calls=r['new_ERR_risk_calls'])
    if 'ERR_price' in r:
        out.update(ERR_Q_upper=float(r['informational']['risk']['upper']),
            ERR_core_upper=float(r['ERR_price']['core_SRAM_fraction_upper']),
            ERR_core_lower=float(r['ERR_price']['core_SRAM_fraction_lower']),
            ERR_selected_gain_upper=float(r['comparison']['selected_ERR_gain_vs_fixed44_upper']))
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe',action='store_true')
    parser.add_argument('--write',action='store_true')
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args()
    if sum((args.probe,args.write,args.check))!=1:
        parser.error('Choose exactly one of --probe / --write / --check')
    start=time.perf_counter()
    result=evaluate(not args.probe)
    data=encoded(result); path=HERE/'outputs/result.json'
    if args.write:
        path.parent.mkdir(exist_ok=True); path.write_bytes(data)
    if args.check and path.read_bytes()!=data:
        raise AssertionError('Replay differs from committed result')
    print(json.dumps(dict(**overview(result),elapsed_s=time.perf_counter()-start,
                         output_written=args.write,exact_replay=args.check)),flush=True)


if __name__=='__main__':
    main()
