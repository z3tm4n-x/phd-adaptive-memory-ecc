"""Reproduce the frozen window-uncertainty slice and finite engineering checks."""
import argparse
from fractions import Fraction as F
import hashlib
from model import Slice,encoded,HERE
from calendar_math import schedule_counts,boundary_checks


def result():
    s=Slice();rows=[]
    # Geometry and frozen identities, not a repeat of accepted numerical integration.
    assert s.upper(30)['pure_bus_upper']==s.a['pure_bus_upper']
    assert s.upper(30)['reads_upper']==s.a['reads_upper']
    assert s.upper(30)['repairs_upper']==s.a['repairs_upper']
    assert F(s.accepted['witness']['rise_s']['hi'])+430<600
    assert F(s.accepted['witness']['solar_mass']['hi'])<=s.accepted['witness']['solar_budget']
    for eta in (0,30,120,600,1200):
        row=s.upper(eta);row['healthy_schedule_upper']=s.upper(eta,loss=False)
        row['nominal_schedule_count']=schedule_counts(s,eta)
        assert row['nominal_schedule_count']['total_reads_exact']<=row['healthy_schedule_upper']['reads_upper']
        assert row['pure_bus_upper']==s.bus0+eta*s.slope
        assert row['reads_upper']<s.hard
        assert row['repairs_upper']==s.a['repairs_upper']
        rows.append(row)
    roots={str(g):(s.L/g-s.bus0-s.Ccommon)/s.slope for g in (1,2,4,5)}
    management=s.management();geom=s.geometry()
    assert geom['control_slack_s']>0 and geom['gap_after_app_s']>0 and geom['gap_before_next_control_s']>0
    assert geom['total_peak_upper']<=geom['mandatory_peak_cap']
    assert geom['app_response_upper_s']<=geom['app_deadline_s']
    # All-time recognized loss is safe with the high support but violates the economical loss quota.
    env=s.cfg['environment'];D=env['reference_words']*env['reference_bits']
    b,B,fs=[F(env[x]) for x in ('reference_background_per_s','reference_peak_per_s','reference_solar_mass')]
    K=F(s.W*39*38,2*D*D);delta0=F(s.cfg['lifetime_other_budget'])
    qH=delta0+K*s.Pplus(20)*(b*b*s.T+(B+b)*fs)+s.a['Q_terms']['E_cross']
    NH=s.W*(s.T/s.Pminus(20)+2)+s.delta*s.hard
    repairs=min(NH,2*s.a['parent_count_upper']+qH*s.hard)
    allH=dict(kH=20,Q_upper=qH,read_upper=NH,
        bus_upper=(s.rb*NH+s.cb*repairs)/s.T,
        outside_economical_loss_quota=True,
        is_original_all_potential_FAST=False)
    boxes=[]
    for g,eta,u in [(5,F(30),F(20,10**6)),(4,F(120),F(30,10**6))]:
        slack=s.upper(eta)['u_limits'][str(g)]-u
        assert slack>0 and u<management['composition_independent_u_upper']
        boxes.append(dict(gain_at_least=g,eta_range_s=[F(0),eta],management_range=[F(0),u],
            management_slack_at_worst_corner=slack,Q_slack=s.eps-s.U,
            requires_local_processing_at_most_s=management['local_processing_budget_for_map_s'],
            hardware_validation=False))
    return dict(status='NEW_ENGINEERING_SLICE_FOR_INDEPENDENT_REVIEW',
        base_main=s.manifest['base_main'],plan_commit=s.manifest['plan_commit'],
        eta_range_s=[0,1200],kH=20,kL=1780,rows=rows,
        affine_bus=dict(intercept=s.bus0,slope_per_second=s.slope),
        zero_management_eta_roots_s=roots,constant_class=s.fixed_witness(),
        common_cost=s.common,geometry=geom,management=management,
        boundary_checks=boundary_checks(s),all_time_recognized_loss=allH,boxes_with_margin=boxes,
        Q_target_half_epsilon_met=s.U<=s.eps/2,
        timing_target_20_percent_met=geom['app_response_upper_s']<=F(4,5)*geom['app_deadline_s'],
        resource_target_20_percent_met=geom['total_peak_upper']<=F(4,5)*geom['mandatory_peak_cap'],
        physical_Q=None,hardware_winner=None,feedback_beats_same_information_schedule=None,
        fixed_lower_scope='same nominal 256-pulse witness is inside every D(eta), eta >= 0',
        schedule_scope='healthy channel: identical policy; valid retained table can continue during external-link loss; invalid time/table requires the same safe fallback')


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check',action='store_true');args=ap.parse_args()
    payload=encoded(result());out=HERE/'outputs';out.mkdir(exist_ok=True)
    target=out/'result.json'
    if args.check:assert target.read_bytes()==payload,'Exact replay differs'
    else:target.write_bytes(payload)
    print(('Exact replay OK; ' if args.check else '')+'SHA256 '+hashlib.sha256(payload).hexdigest())
