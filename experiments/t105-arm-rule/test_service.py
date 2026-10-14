import copy
import json
import unittest
from fractions import Fraction as F
from service_work import BASE,HERE,PATTERNS,analyze,parse,acyclic,branch
from service_budget import calculate_service,PARAMETERS


class StructuralServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ins,cls.fn=parse((HERE/'outputs/firmware-disassembly.txt').read_text(),
                            (HERE/'outputs/firmware-symbols.txt').read_text())
        cls.work=json.loads((HERE/'outputs/service-work.json').read_text())

    def test_fixed_binary_work(self):
        r=analyze(self.ins,self.fn)
        self.assertEqual(r['t105_driver_step']['upper'],
                         dict(instructions=1004,ocm_data_32bit_beats=416,mmio_reads=21,mmio_writes=15,dmb=10))

    def test_crc_bound_is_bytes_not_data_dependent(self):
        self.assertEqual(analyze(self.ins,self.fn)['t105_crc32']['upper']['instructions'],17+27*7)

    def test_zero_progress_loop_rejected(self):
        for off in (0x990,0xb34,0xb90,0xbdc):
            with self.subTest(offset=hex(off)):
                ins=copy.deepcopy(self.ins)
                word,op,args=ins[BASE+off]
                ins[BASE+off]=(word^1,op,args)
                with self.assertRaisesRegex(ValueError,'ranking template'):
                    analyze(ins,self.fn)

    def test_enlarged_crc_rejected(self):
        ins=copy.deepcopy(self.ins)
        _,op,args=ins[BASE+0x928]
        ins[BASE+0x928]=(0xe3a01020,op,args)
        with self.assertRaisesRegex(ValueError,'ranking template'):
            analyze(ins,self.fn)

    def test_new_infinite_cycle_rejected(self):
        ins=copy.deepcopy(self.ins)
        ins[BASE+0x100]=(0xeafffffe,'b','fffc0100')
        with self.assertRaisesRegex(ValueError,'unranked cycle'):
            analyze(ins,self.fn)

    def test_indirect_pc_write_rejected(self):
        ins=copy.deepcopy(self.ins)
        ins[BASE+0x100]=(0xe1a0f000,'mov','pc, r0')
        with self.assertRaisesRegex(ValueError,'control transfer'):
            analyze(ins,self.fn)

    def test_branch_decode_and_dag(self):
        self.assertEqual(branch(0xeafffffe,BASE),(BASE,False,True))
        acyclic({0:[1,2],1:[2],2:[]})
        with self.assertRaisesRegex(ValueError,'cycle'):
            acyclic({0:[1],1:[0]})

    def test_unknown_is_not_zero_or_success(self):
        r=calculate_service(self.work)
        self.assertEqual(len(r['missing_parameters']),5)
        self.assertIsNone(r['full_round_upper_ns'])
        self.assertIsNone(r['within_selected_1ms_if_parameters_valid'])
        self.assertFalse(r['established_on_PS7'])

    def test_conditional_budget_boundary_not_platform_claim(self):
        r=calculate_service(self.work)
        # Synthetic boundary test only. These zeros are NOT platform inputs.
        v={k:F(0) for k in PARAMETERS}
        v['core_fetch_ns']=r['visit_limit_for_1ms_ns']/1009
        at=calculate_service(self.work,v)
        self.assertEqual(at['full_round_upper_ns'],1000000)
        self.assertTrue(at['within_selected_1ms_if_parameters_valid'])
        self.assertFalse(at['established_on_PS7'])
        v['core_fetch_ns']+=F(1,10**9)
        self.assertFalse(calculate_service(self.work,v)['within_selected_1ms_if_parameters_valid'])

    def test_negative_latency_rejected(self):
        with self.assertRaises(ValueError):
            calculate_service(self.work,{'gp_read_ns':-1})


if __name__=='__main__':unittest.main()
