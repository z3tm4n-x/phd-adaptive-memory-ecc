"""Scalar engineering checks for #73; applicability explicitly remains a contract.

No fit to GOES, no optimizer. The adaptive expression assumes exogenous monitor
calendar, nested passes, and the long-interval ceiling stated in contracts.md.
It is NOT a substitution of random intervals into a fixed-period theorem.
"""
from __future__ import annotations
import csv
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def ticks(value, tick, up):
    return int((Decimal(str(value))/Decimal(str(tick))).to_integral_value(
        rounding=ROUND_CEILING if up else ROUND_FLOOR))


def grow(x, l, rho, delay, cap):
    if min(x, rho, delay, cap) < 0 or l <= 0:
        raise ValueError('Invalid growth contract')
    y = x/l if x <= l else 1+math.log(x/l)
    z = y+rho*delay
    # Cap before exp prevents overflow and is part of the declared class.
    cap_h = cap/l if cap <= l else 1+math.log(cap/l)
    if z >= cap_h: return cap
    return l*z if z <= 1 else l*math.exp(z-1)


def input_rows(config):
    source = HERE.parent/'t68-v21-inputs/outputs/numerics.csv'
    with source.open(newline='') as f:
        values = list(csv.DictReader(f))
    c = config['conditional_r0a']
    for r in values:
        if float(r['rho']) not in c['shield_g_cm2']: continue
        b, s, f = [float(r[k]) for k in ['nuG','nuS','sep_exposure_upper']]
        yield {'shield_g_cm2':float(r['rho']), 'b_bar_full38_s_inv':b,
               'solar_peak_full38_s_inv':s, 'B_full38_s_inv':b+s,
               'solar_exposure_upper':f, 'I2_full38_upper_s_inv':b*b*c['mission_s']+(2*b+s)*f,
               'data32_direct_point':float(r['L1']), 'data32_direct_upper_A0':float(r['UA0']),
               'data32_direct_upper_R':float(r['UR']), 'T68_point_period_s':float(r['tU']),
               'full38_direct_upper_proposal':c['full38_direct_exposure_upper_proposal'],
               'status':'conditional extension of v21 equal-bit response; not physical full38 coverage',
               'source':'T68 outputs/numerics.csv; contracts.md sections 1-4'}


def check(c, g, r, long, short, threshold, delay, hold):
    w, n, tick = c['words'], c['full_word_bits'], c['tick_s']
    long_ticks, short_ticks = ticks(long,tick,False), ticks(short,tick,False)
    cost_ticks = ticks(c['read_s']+c['write_s'],tick,True)
    c_op = cost_ticks*tick
    busy = w*c_op
    nested = long_ticks % short_ticks == 0
    # Fixed per-word phase floor(w*M/W): no conflicts if min spacing >= c.
    batch = g['control_words_per_batch']
    gap_ticks = ticks(g['reserved_application_gap_s'],tick,True)
    pass_ticks = w*cost_ticks+((w-1)//batch)*gap_ticks
    resources = pass_ticks <= short_ticks and nested
    beta = (n-1)/(2*n*w)
    b,s,f = r['b_bar_full38_s_inv'], r['solar_peak_full38_s_inv'],r['solar_exposure_upper']
    total_i2 = r['I2_full38_upper_s_inv']
    # Alarm -> next fixed fast pass -> its final word. Not instant full reset.
    response_delay = delay+2*short
    ceiling = grow(threshold,g['growth_threshold_s_inv'],g['growth_rho_s_inv'],response_delay,s)
    low_i2 = min(total_i2, b*b*c['mission_s']+(2*b+ceiling)*f)
    direct = -math.expm1(-c['full38_direct_exposure_upper_proposal'])
    delta = sum(c[k] for k in ['delta_initial_proposal','delta_service_proposal','delta_ERR_proposal','delta_monitor_joint_proposal'])
    pair = beta*(short*total_i2+(long-short)*low_i2)
    risk = direct+delta+pair
    quiet_horizon = c['quiet_cost_horizon_s']
    hold_effective = hold+2*short+g['ERR_delivery_upper_s_proposal']
    # Includes carry-in after a preceding real burst; no bound on number of weak bursts.
    occupied_fraction = min(1.,(b+g['monitor_false_alarm_expected_rate_s_inv'])*hold_effective+
                            (hold+long+2*short+g['ERR_delivery_upper_s_proposal'])/quiet_horizon)
    # On any hidden failure path charge the maximal bus tax for the rest of the
    # mission, not zero and not just direct/observable faults. This is essential.
    quiet = busy/long + occupied_fraction*busy/short + g['monitor_extra_quiet_bus_fraction']+min(1.,risk)
    # Constant U does not use ERR or a monitor; do not charge their failure budgets.
    fixed_delta = c['delta_initial_proposal']+c['delta_service_proposal']
    fixed_max = (c['epsilon']-direct-fixed_delta)/(beta*total_i2)
    fixed_safe_ticks = ticks(max(0.,fixed_max),tick,False)
    fixed_safe = fixed_safe_ticks*tick
    fixed_cost = busy/fixed_safe if fixed_safe else None
    coefficient = w*(1/long+occupied_fraction/short)
    max_c_quiet = (c['quiet_cost_target']-g['monitor_extra_quiet_bus_fraction']-min(1.,risk))/coefficient
    # Largest permitted long-interval solar ceiling for this scalar test.
    allowance = (c['epsilon']-direct-delta-beta*short*total_i2)/(beta*(long-short))
    max_ceiling = (allowance-b*b*c['mission_s'])/f-2*b
    return {'shield_g_cm2':r['shield_g_cm2'],'long_period_s':long,'short_period_s':short,
            'monitor_solar_threshold_s_inv':threshold,'monitor_delay_s':delay,'hold_s':hold,
            'full_fast_fence_delay_s':response_delay,'solar_ceiling_on_long_intervals_s_inv':ceiling,
            'solar_ceiling_required_max_s_inv':max_ceiling,'pair_risk_upper_conditional':pair,
            'direct_risk_upper_conditional':direct,'other_failure_union_upper':delta,
            'total_risk_upper_conditional':risk,'quiet_expected_tax_upper_conditional':quiet,
            'short_bus_fraction':busy/short,'calendar_pass_s':pass_ticks*tick,
            'short_peak_window_1ms_upper':min(1.,.001/(batch*c_op+gap_ticks*tick)*batch*c_op/.001+batch*c_op/.001),
            'application_reserved_service_fraction':gap_ticks/(batch*cost_ticks+gap_ticks),
            'application_delay_upper_conditional_s':(batch*cost_ticks+gap_ticks)*tick+
                g['application_envelope_proposal']['burst_bus_work_s']/(gap_ticks/(batch*cost_ticks+gap_ticks)),
            'application_envelope_supported':g['application_envelope_proposal']['sustained_bus_fraction']<gap_ticks/(batch*cost_ticks+gap_ticks),
            'read_write_busy_s':busy,'word_slot_s':c_op,'word_slot_required_max_by_quiet_s':max_c_quiet,
            'fixed_period_max_certificate_s':fixed_max,'fixed_safe_grid_period_s':fixed_safe,
            'fixed_other_failure_union_upper':fixed_delta,
            'fixed_same_contract_tax':fixed_cost,'resources_and_nested_grid':resources,
            'conditional_risk_pass':risk<=c['epsilon'], 'conditional_quiet_pass':quiet<=c['quiet_cost_target'],
            'conditional_algebra_pass':resources and risk<=c['epsilon'] and quiet<=c['quiet_cost_target'],
            'proof_status':'engineering envelope; requires #73 causal/monitor/calendar proof',
            'physical_status':'unqualified full38/ERR/U/monitor/coverage',
            'peak_requirement_status':'no application arrival/peak budget supplied'}


def fixed_necessity(c, r):
    """T45 §2 cell witness, restricted to a constant-period full38 U competitor.

    Starts at the allowed peak, no SMU, independent uniform singletons. Finite
    quiet-window edge allowance 2C avoids treating C/tau as exact for 24h.
    The lower bound is for this witness, not for the full mixture with XOR SMU.
    """
    w,n=c['words'],c['full_word_bits']
    cost=ticks(c['read_s']+c['write_s'],c['tick_s'],True)*c['tick_s']
    busy=w*cost
    minimum=busy/(c['quiet_cost_target']+2*busy/c['quiet_cost_horizon_s'])
    length=r['solar_exposure_upper']/r['solar_peak_full38_s_inv']
    cell=minimum/4
    service_windows=math.floor(length/minimum)+2
    cells=max(0,math.ceil(w*length/cell-service_windows*(w*cost/cell+2*w)))
    bit_rate=r['B_full38_s_inv']/(n*w)
    prob=math.comb(n,2)*(bit_rate*cell)**2*math.exp(-n*bit_rate*cell)
    exponent=cells*prob
    return {'shield_g_cm2':r['shield_g_cm2'],'minimum_period_if_quiet_tax_le_1pct_s':minimum,
            'witness_peak_duration_s':length,'cell_length_s':cell,'cells_lower':cells,
            'per_cell_lower_probability':prob,'lower_exponent':exponent,
            'first_exceedance_probability_lower':-math.expm1(-exponent),
            'excludes_constant_1pct_on_conditional_class':-math.expm1(-exponent)>c['epsilon'],
            'source':'T45 section2 eq1/3, n=38 singleton specialization; pure witness, no monotonic SMU thinning',
            'scope':'fixed single-period U, one bounded word service window per period; not an unrestricted controller lower bound'}


def table(config):
    c,g=config['conditional_r0a'],config['method_parameter_grid']
    rows=[]
    for r in input_rows(config):
        for a,z,h,d,hold in itertools.product(g['long_period_s'],g['short_period_s'],g['monitor_solar_threshold_s_inv'],g['monitor_total_delay_s'],g['hold_s']):
            rows.append(check(c,g,r,a,z,h,d,hold))
    return rows


if __name__ == '__main__':
    config=json.loads((HERE/'config.json').read_text())
    rows=table(config)
    print(json.dumps({'tested':len(rows),'algebra_pass':sum(r['conditional_algebra_pass'] for r in rows),
        'reference':[r for r in rows if r['long_period_s']==6 and r['short_period_s']==.05 and
                     r['monitor_solar_threshold_s_inv']==.0001 and r['monitor_delay_s']==2 and r['hold_s'] in [5,10]]},indent=2))
