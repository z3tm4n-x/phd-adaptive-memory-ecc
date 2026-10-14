import hashlib,json,unittest
from startup_check import HERE,PROFILE,EXPECT,GIC_FAULTS,execute,legacy_rejection,preservation
from gicv1_model import GicV1Controls

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
        for m in ('ignore-ttbr',*GIC_FAULTS):
            with self.subTest(m=m):self.assertTrue(execute(m)['trapped'])

    def test_gicv1_fields_and_reserved_raz_wi(self):
        g=GicV1Controls()
        # Independent expected sets from the primary tables, not a C mask.
        for address,fields in ((0xf8f00100,{0,1,2,3,4}),(0xf8f01000,{0,1})):
            self.assertEqual(g.read(address),0)
            for bit in range(32):
                with self.subTest(address=hex(address),bit=bit):
                    g.write(address,1<<bit)
                    self.assertEqual(g.read(address),(1<<bit) if bit in fields else 0)
            g.write(address,0xffffffff)
            self.assertEqual(g.read(address),31 if address==0xf8f00100 else 3)
            g.write(address,0)
            self.assertEqual(g.read(address),0)
        g.write(0xf8f00100,0x1e0)
        self.assertEqual(g.read(0xf8f00100),0)

    def test_unchanged_legacy_elf_is_rejected_by_target_model(self):
        r=legacy_rejection()
        self.assertFalse(r['policy_entered']);self.assertTrue(r['trapped'])
        self.assertEqual(r['report'][0],'0x3')

    def test_new_elf_clears_all_implemented_gic_control_fields(self):
        r=execute(gic_initial={0xf8f00100:31,0xf8f01000:3})
        self.assertTrue(r['policy_entered'])
        self.assertEqual(r['gicv1_controls'],{'0xf8f00100':'0x0','0xf8f01000':'0x0'})
        for m in GIC_FAULTS:
            with self.subTest(m=m):
                self.assertEqual(execute(m)['report'][0],'0x3')

    def test_disabled_gic_does_not_block_external_fiq(self):
        g=GicV1Controls()
        for irq in (False,True):
            for fiq in (False,True):
                self.assertEqual(g.disabled_pass_through(irq,fiq),(irq,fiq))
        # There is no fictitious software disable of NMFI or the bypass path.
        self.assertIn('external FIQ must remain inactive',PROFILE['interrupts'])
        self.assertIn('bypass remains enabled',PROFILE['interrupts'])

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

    def test_firmware_pl_and_scientific_contract_unchanged(self):
        self.assertTrue(preservation()['all_equal'])

if __name__=='__main__':unittest.main()
