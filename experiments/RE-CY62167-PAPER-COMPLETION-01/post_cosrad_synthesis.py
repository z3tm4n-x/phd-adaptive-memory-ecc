from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from tau_bound import T_DEFAULT, Q_DEFAULT, direct_budget_fraction, direct_log_sensitivity, tau_max_upper
from resource_model import resource_at_period

HERE = Path(__file__).resolve().parent


def sha256_path(path: Path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def read_csv(path: Path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows, fields):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description='Phase B synthesis after PI COSRAD output; does not run COSRAD.')
    ap.add_argument('--pi-rates', required=True, type=Path)
    ap.add_argument('--event-weights', type=Path, default=None,
                    help='LET-resolved registered-event rates for model-conditional reference; omit to emit the allowed blocker.')
    ap.add_argument('--scenario', default='GEO article baseline')
    args = ap.parse_args(argv)

    rows = read_csv(args.pi_rates)
    required = {'shield_g_cm2','mapping_id','estimate_type','nu_direct_s-1','nu_accumulation_bit_s-1'}
    if not rows or not required.issubset(rows[0]):
        raise SystemExit('PI rate file missing required fields')
    if any(r['estimate_type'] not in {'POINT','ARTICLE_CONFIDENCE_STYLE'} for r in rows):
        raise SystemExit('estimate_type must be POINT or ARTICLE_CONFIDENCE_STYLE')

    bound = []
    resources = []
    for r in rows:
        nuD = float(r['nu_direct_s-1']); nuC = float(r['nu_accumulation_bit_s-1'])
        fD = direct_budget_fraction(nuD)
        SD, sd_status = direct_log_sensitivity(fD)
        tau, status = tau_max_upper(nuD, nuC)
        bound.append({
            **{k:r[k] for k in ('shield_g_cm2','mapping_id','estimate_type')},
            'nu_direct_s-1':nuD,'nu_accumulation_bit_s-1':nuC,'f_D':fD,
            'S_D': '' if SD is None else SD, 'tau_max_U_s': '' if tau is None else tau,
            'bound_status':status,
        })
        if tau is not None and tau != float('inf'):
            for scan in ('R1','R2'):
                for policy in ('U','E'):
                    d = resource_at_period(tau,scan,policy)
                    resources.append({
                        **{k:r[k] for k in ('shield_g_cm2','mapping_id','estimate_type')},
                        'period_source':'tau_max_U','tau_s':tau,'scan_mode':scan,'write_policy':policy,
                        **{k:d[k] for k in ('reads_per_cycle','writes_per_cycle_or_expected','t_read_effective_s','t_write_effective_s','tau_min_arch_s','resource_margin','period_feasible','architecture_status','reads_per_s','writes_per_s','interface_fraction','interface_percent')},
                    })
    write_csv(HERE/'geo_bound_results.csv', bound, ['shield_g_cm2','mapping_id','estimate_type','nu_direct_s-1','nu_accumulation_bit_s-1','f_D','S_D','tau_max_U_s','bound_status'])
    write_csv(HERE/'resource_results.csv', resources, ['shield_g_cm2','mapping_id','estimate_type','period_source','tau_s','scan_mode','write_policy','reads_per_cycle','writes_per_cycle_or_expected','t_read_effective_s','t_write_effective_s','tau_min_arch_s','resource_margin','period_feasible','architecture_status','reads_per_s','writes_per_s','interface_fraction','interface_percent'])

    # A scalar nu_D,nu_C cannot define the requested mark-resolved reference model. Even with a weights
    # file, the subsequent event-level solve uses the raw residual marks under each W and must be executed
    # under the controlled Phase-B run. No surrogate mark law is invented here.
    ref_fields=['shield_g_cm2','mapping_id','estimate_type','tau_max_U_s','tau_max_ref_low_s','tau_max_ref_high_s','eta_tau_low','eta_tau_high','scrub_rate_penalty_low','scrub_rate_penalty_high','reference_status']
    ref=[]
    if args.event_weights is None:
        for r,b in zip(rows,bound):
            ref.append({**{k:r[k] for k in ('shield_g_cm2','mapping_id','estimate_type')},'tau_max_U_s':b['tau_max_U_s'],
                        'tau_max_ref_low_s':'','tau_max_ref_high_s':'','eta_tau_low':'','eta_tau_high':'','scrub_rate_penalty_low':'','scrub_rate_penalty_high':'',
                        'reference_status':'TAU_MAX_REFERENCE_BLOCKED_BY_MISSING_EVENT_RATE_WEIGHTS'})
    else:
        # Presence/provenance is recorded; actual event-level reference execution is intentionally a controlled
        # Phase-B action so that the raw mark law and PI weights are bound to the same run manifest.
        weights = read_csv(args.event_weights)
        reqw={'shield_g_cm2','LET_MeV_cm2_mg','lambda_registered_event_s-1'}
        if not weights or not reqw.issubset(weights[0]):
            raise SystemExit('event weights missing required fields')
        for r,b in zip(rows,bound):
            ref.append({**{k:r[k] for k in ('shield_g_cm2','mapping_id','estimate_type')},'tau_max_U_s':b['tau_max_U_s'],
                        'tau_max_ref_low_s':'','tau_max_ref_high_s':'','eta_tau_low':'','eta_tau_high':'','scrub_rate_penalty_low':'','scrub_rate_penalty_high':'',
                        'reference_status':'EVENT_RATE_WEIGHTS_RECEIVED_REFERENCE_EVENT_RUN_REQUIRED'})
    write_csv(HERE/'geo_reference_results.csv',ref,ref_fields)

    manifest={
        'filename':args.pi_rates.name,'SHA-256':sha256_path(args.pi_rates),'date_received':'TO_BE_RECORDED_BY_PI_HANDOFF',
        'scenario':args.scenario,'units':{'nu_direct_s-1':'s^-1','nu_accumulation_bit_s-1':'s^-1'},
        'normalization_track':'declared per estimate_type / PI contract',
        'event_weights':None if args.event_weights is None else {'filename':args.event_weights.name,'SHA-256':sha256_path(args.event_weights)},
    }
    (HERE/'pi_cosrad_input_manifest.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')

if __name__=='__main__':
    main()
