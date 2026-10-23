"""Directed numerical/contract tests; no accepted campaign or ERR grid."""
from copy import deepcopy
from fractions import Fraction as F
import json
from pathlib import Path
import unittest

import run as m


class ApplicationProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg,cls.p,cls.accepted,cls.manifest=m.load()
        cls.c=m.profile_counts(cls.cfg,cls.p)
        cls.screen=m.gate(cls.cfg,cls.p,cls.c,cls.accepted)

    def test_exact_counts_at_every_small_calendar_edge(self):
        # Independent explicit list; offers at T are excluded, at T-1 included.
        for epoch,cycle,n,phase in ((10,3,1,0),(10,7,3,9),(17,5,5,4)):
            offers=[(i*cycle+j)*epoch+phase for i in range(8) for j in range(n)]
            horizons={0,1,7*cycle*epoch}
            for t in offers:
                if t<7*cycle*epoch:
                    horizons.update((max(0,t-1),t,t+1))
            for H in horizons:
                with self.subTest(epoch=epoch,cycle=cycle,n=n,phase=phase,H=H):
                    self.assertEqual(m.cyclic_count(H,epoch,phase,cycle,n),
                                     sum(t<H for t in offers))

    def test_cadence_is_requirement_maximum_not_price_tuning(self):
        c=self.c;a=self.cfg['application'];D=self.cfg['constraints']['application_deadline_ns']
        self.assertLessEqual(c['cycle_with_service_s'],c['freshness_limit_s'])
        self.assertGreater(c['cycle_with_service_s']+F(a['epoch_ns'],m.NS),c['freshness_limit_s'])
        self.assertEqual(c['cycle_epochs'],999)
        # For each channel the gap is exactly cycle*epoch, not 16 times that.
        for channel in range(c['channels']):
            arrivals=[(i*c['cycle_epochs']+channel)*a['epoch_ns']+a['first_ns']
                      for i in range(3)]
            self.assertEqual(arrivals[1]-arrivals[0],arrivals[2]-arrivals[1])
            self.assertLessEqual(F(arrivals[1]-arrivals[0]+D,m.NS),c['freshness_limit_s'])

    def test_two_whole_images_fit_frozen_W(self):
        c=self.c
        self.assertEqual(c['images']*c['image_words'],self.cfg['words'])
        self.assertEqual(c['active_unique_data_bytes'],262144)
        self.assertEqual(c['total_data_bytes'],524288)
        self.assertEqual(c['raw_encoded_bytes'],786432)
        for bank in (0,1):
            for channel in range(16):
                for code in (0,1,2048,4095):
                    addr=bank*c['image_words']+channel*4096+code
                    self.assertTrue(bank*c['image_words']<=addr<(bank+1)*c['image_words'])
        bad=deepcopy(self.p);bad['requirements']['copies']=3
        with self.assertRaises(ValueError):
            m.profile_counts(self.cfg,bad)

    def test_updates_are_optional_even_at_mission_end(self):
        c=self.c;r=self.p['requirements'];T=self.cfg['mission_s']
        self.assertEqual(c['guaranteed_attempts'],0)
        self.assertEqual(c['maximum_retention_s'],T)
        self.assertIsNone(c['maximum_actual_refresh_gap_s'])
        # An attempted full load is paid even if rejected or still incomplete.
        self.assertEqual(c['mission_maintenance_reads_upper'],
                         c['optional_attempts_upper']*c['per_attempt_reads'])
        self.assertEqual((r['maintenance_admission_interval_s']*m.NS-1)//
                         (r['maintenance_admission_interval_s']*m.NS),0)
        self.assertEqual((T*m.NS-1)//(r['maintenance_admission_interval_s']*m.NS),121)
        for n in (39,44):
            row=self.screen['rows']['OFF'+str(n)]
            direct=m.cmp.risk(self.cfg,n,1 if n==39 else 2,T*m.NS,
                             self.cfg['constraints']['application_deadline_ns'])
            self.assertEqual(row['risk'],direct)
            self.assertEqual(row['admissibility'],'UPPER_FAILS_NOT_EXCLUDED')

    def test_loader_has_all_passes_and_never_writes_active(self):
        for B in (1,5,17):
            for g in (1,4):
                steps=list(m.workflow(B,g))
                self.assertEqual(sum(x[0]=='R' for x in steps),(3*g+1)*B)
                self.assertEqual(sum(x[0]=='W' for x in steps),2*g*B)
                self.assertTrue(all(bank=='inactive' for kind,bank,*rest in steps if kind=='W'))
                for word in range(B):
                    self.assertEqual(sum(x[0]=='W' and x[2]==word and x[3]=='copy' for x in steps),g)
                    self.assertEqual(sum(x[0]=='W' and x[2]==word and x[3]=='file' for x in steps),g)
                    self.assertEqual(sum(x[2]==word and x[3]=='range_validation' for x in steps),1)
                # Publication is allowed only after the final validation;
                # pinning the active image protects it during every prior step.
                self.assertEqual(steps[-1][3],'range_validation')
                self.assertTrue(all(0<=x[2]<B for x in steps))

    def test_serial_loader_stays_in_old_slots_without_runtime_collision(self):
        epoch=100;rp=10;wp=60;cycle=31;channels=4;D=3
        for start in (0,9,10,11,58,60,61,3059):
            for g in (1,4):
                t=start;previous=-1;nr=nw=0
                for kind,bank,word,stage,byte in m.workflow(53,g):
                    offer=m.next_offer(t,kind,epoch,rp,wp,cycle,channels)
                    self.assertGreaterEqual(offer,t)
                    self.assertGreater(offer,previous)
                    self.assertEqual(offer%epoch,rp if kind=='R' else wp)
                    if kind=='R':
                        self.assertGreaterEqual((offer//epoch)%cycle,channels);nr+=1
                    else:
                        nw+=1
                    previous=offer;t=offer+D
                ops=nr+nw
                bound=(ops+channels*(m.cmp.ceil(F(ops,cycle-channels))+1)+2)*epoch+D
                self.assertLessEqual(t-start,bound)
        self.assertGreater(self.c['maintenance_CPU_NVM_margin_s'],0)

    def test_full_price_retains_observation_and_repairs(self):
        original=self.accepted['holds']['theorist_approved_price_followup']['cost']
        saved=deepcopy(original);new=m.retarget_ERR_price(self.cfg,self.c,original)
        self.assertEqual(original,saved)
        for key in ('read_count_upper','repair_count_upper','expected_parent_count_upper',
                    'extra_veto_action_rates_per_unit_v','transport_plus_loss_state_bytes',
                    'veto_core_fraction_slope_per_notification_per_s'):
            self.assertEqual(new[key],original[key],key)
        for key in ('scrub_reads','scrub_corrections','captures','records','cuts','decisions','timer_events'):
            self.assertEqual(new['full_cost_rates'][key],original['full_cost_rates'][key],key)
        self.assertEqual(new['energy_coefficients_per_second']['transport_records'],
                         original['energy_coefficients_per_second']['transport_records'])
        self.assertIsNone(new['adaptive']['app_same_word_revisit_s'])
        self.assertGreater(new['extra_veto_action_rates_per_unit_v']['scrub_reads'],0)
        self.assertTrue(new['bad_history_paid'] and new['pending_paid'] and new['after_A_paid'])

    def test_only_application_terms_change_core_and_codec(self):
        original=self.accepted['holds']['theorist_approved_price_followup']['cost']
        new=m.retarget_ERR_price(self.cfg,self.c,original)
        counts=m.cmp.count_apps(self.cfg);s=m.cmp.service(self.cfg,39);H=self.cfg['mission_s']*m.NS
        oldapp=m.old.app_cost(self.cfg,39,counts['read'],counts['write'],'upper')
        newapp=m.app_interval(self.cfg,39,self.c)['upper']
        self.assertEqual(new['core_SRAM_fraction_upper']-original['core_SRAM_fraction_upper'],newapp-oldapp)
        self.assertEqual(new['all_history_SRAM_core_upper']-original['all_history_SRAM_core_upper'],newapp-oldapp)
        rates=new['full_cost_rates']
        self.assertEqual(new['codec_busy_fraction'],
                         (s['decode']*rates['decodes']+s['encode']*rates['encodes'])/m.NS)
        self.assertEqual(rates['decodes'],rates['scrub_reads']+rates['application_reads']+rates['application_writes'])
        self.assertEqual(rates['encodes'],rates['application_writes']+F(self.cfg['words'],self.cfg['mission_s']))

    def test_zero_optional_updates_is_lower_than_all_attempts(self):
        for n in (39,44):
            app=m.app_interval(self.cfg,n,self.c)
            self.assertLess(app['lower'],app['upper'])
            no_updates=m.old.app_cost(self.cfg,n,self.c['runtime_reads'],0,'upper')
            self.assertLess(no_updates,app['upper'])
            for g in (1,4):
                c=deepcopy(self.c)
                loads=c['optional_attempts_upper']+self.p['cfe']['startup_extra_full_loads_upper']
                c['upper_app_reads']=c['runtime_reads']+(3*g+1)*c['image_words']*loads
                c['upper_app_writes']=2*g*c['image_words']*loads
                self.assertLessEqual(m.app_interval(self.cfg,n,c)['upper'],app['upper'])

    def test_frozen_fixed_witness_and_service_envelope(self):
        for n,k in ((39,11),(44,44837)):
            row=self.screen['rows']['fixed'+str(n)]
            self.assertEqual(row['k'],k)
            direct=m.cmp.risk(self.cfg,n,1 if n==39 else 2,m.cmp.period(self.cfg,k)['upper_ns'],
                              m.cmp.service(self.cfg,n)['upper']['E'])
            self.assertEqual(row['risk'],direct)
            self.assertLessEqual(direct['upper'],F(self.cfg['epsilon'])/2)
            self.assertGreaterEqual(row['timing']['app_deadline_slack_ns'],0)
            price=row['price']
            self.assertGreaterEqual(price['core_upper'],price['core_lower'])
            self.assertEqual(price['core_upper'],price['app_core_interval']['upper']+price['added_control_core_upper'])
        self.assertEqual(self.cfg['words'],131072)
        self.assertEqual(self.cfg['mission_s'],315576000)
        self.assertEqual(F(self.cfg['epsilon']),F(1,1000))

    def test_result_if_available_is_one_point_not_new_campaign(self):
        path=m.HERE/'outputs/result.json'
        if not path.exists():
            self.skipTest('Full numerical result not written yet')
        result=m.old.numeric(json.loads(path.read_text('utf-8')))
        self.assertEqual(result['new_ERR_risk_calls'],1)
        self.assertEqual(result['new_hold_refinements'],0)
        self.assertEqual(result['new_archive_profiles'],0)
        self.assertEqual(result['informational']['k'],27)
        self.assertLessEqual(result['informational']['risk']['upper'],
            self.accepted['holds']['accepted_k27_ordinary_hold_probe']['risk_reused_without_reintegration'])
        self.assertTrue(result['comparison']['fixed44_upper_below_ERR_mandatory_lower'])
        self.assertIsNone(result['physical_Q'])


if __name__=='__main__':
    unittest.main()
