import hashlib,json,unittest
from startup_check import HERE,PROFILE,EXPECT,execute

class StartupTests(unittest.TestCase):
    def test_real_startup_enters_unchanged_policy_and_waits(self):
        r=execute()
        self.assertTrue(r['policy_entered']);self.assertFalse(r['trapped'])
        self.assertEqual(r['prestart_driver_visits'],4)

    def test_all_clock_mapping_and_isolation_readbacks(self):
        for address in EXPECT:
            with self.subTest(address=hex(address)):
                self.assertTrue(execute(address)['trapped'])

    def test_dirty_or_wrong_entry_rejected(self):
        for m in ('wrong-core','wrong-midr','nonsecure','mmu-on','dcache-on','icache-on','wrong-mode','early-start'):
            with self.subTest(m=m):self.assertTrue(execute(m)['trapped'])

    def test_configuration_write_readback_failures(self):
        for m in ('ignore-ttbr','gic-readback'):
            with self.subTest(m=m):self.assertTrue(execute(m)['trapped'])

    def test_independent_mapper_rejects_bad_attributes_and_alias(self):
        for m in ('cached-mmio','alias-ocm','domain-manager'):
            with self.subTest(m=m),self.assertRaises((AssertionError,ValueError)):execute(m)

    def test_firmware_identity_and_clock_equation(self):
        self.assertEqual(hashlib.sha256((HERE/'outputs/firmware.elf').read_bytes()).hexdigest(),PROFILE['firmware_sha256'])
        from fractions import Fraction
        self.assertEqual(Fraction(PROFILE['ps_clk_nominal_hz'])*PROFILE['arm_pll_fdiv']/PROFILE['cpu_divisor'],600000000)

    def test_profile_is_not_timing_evidence(self):
        result=json.loads((HERE/'outputs/service-budget.json').read_text())
        self.assertIsNone(PROFILE['platform_time_upper_ns'])
        self.assertIsNone(result['full_round_upper_ns'])
        self.assertFalse(PROFILE['physical_launch_performed'])
        self.assertEqual(result['visit_limit_for_1ms_ns']['rational'],'4996689967/25000')

if __name__=='__main__':unittest.main()
