import copy
import importlib.util
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import call, patch
from final_price_check import check_fixed, fixed_slots
from five_scenarios import record_table

# Other accepted packages also contain reproduce.py and amend sys.path.
# Bind this entry point by path, not a process-global generic module name.
_spec=importlib.util.spec_from_file_location('t106_reproduce',Path(__file__).resolve().parent/'reproduce.py')
_reproduce=importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_reproduce)


class DeliveryCheckTests(unittest.TestCase):
    def test_full_readonly_checks_start_both_and_wait_for_both(self):
        barrier=threading.Barrier(2)
        finished=[]
        def run(command,check):
            self.assertTrue(check)
            self.assertEqual(command[-2],'--mode')
            self.assertNotIn('--execute',command)
            self.assertNotIn('--record',command)
            barrier.wait(timeout=5)
            finished.append(command[-1])
        with patch.object(_reproduce.subprocess,'run',side_effect=run):
            _reproduce.verify_full_profiles()
        self.assertCountEqual(finished,['adaptive','fixed'])

    def test_one_failed_full_check_cannot_be_accepted(self):
        barrier=threading.Barrier(2)
        finished=[]
        def run(command,check):
            barrier.wait(timeout=5)
            finished.append(command[-1])
            if command[-1]=='adaptive':
                raise subprocess.CalledProcessError(1,command)
        with patch.object(_reproduce.subprocess,'run',side_effect=run):
            with self.assertRaises(subprocess.CalledProcessError):
                _reproduce.verify_full_profiles()
        self.assertCountEqual(finished,['adaptive','fixed'])

    def test_full_replay_routes_to_checkpointed_verifier(self):
        path=Path(__file__).resolve().parent/'replay_burst.py'
        with patch.object(sys,'argv',[str(path),'--case','burst']):
            with patch('verify_burst_v3.verify') as verify:
                runpy.run_path(str(path),run_name='__main__')
        self.assertEqual(verify.call_args_list,[call('adaptive'),call('fixed')])

    def test_cannot_publish_incomplete_or_replace_table(self):
        with tempfile.TemporaryDirectory() as folder:
            output=Path(folder)
            with self.assertRaises(AssertionError):
                record_table(dict(status='INCOMPLETE',missing=['scenario2']),output)
            self.assertFalse(list(output.iterdir()))
            data=dict(status='complete_digital_evidence_pending_review',missing=[],rows=[])
            record_table(data,output)
            before={p.name:p.read_bytes() for p in output.iterdir()}
            record_table(data,output)
            changed=copy.deepcopy(data);changed['new_unreviewed_result']=1
            with self.assertRaises(AssertionError):record_table(changed,output)
            self.assertEqual(before,{p.name:p.read_bytes() for p in output.iterdir()})

    def test_closed_form_against_enumerated_pulses(self):
        for horizon in range(1, 8000, 7):
            starts = [1568 * q + 164 * i for q in range(6) for i in range(8)]
            work = sum(max(0, min(92, horizon - s)) for s in starts)
            complete = sum(s + 92 <= horizon for s in starts)
            partial = sum(s < horizon < s + 92 for s in starts)
            self.assertEqual(fixed_slots(horizon), (work, complete, partial))

    def test_large_full_burst_without_float_conversion(self):
        work, complete, partial = fixed_slots(363_900_000_000_000)
        self.assertEqual(complete, 1_856_632_653_062)
        self.assertEqual(partial, 1)
        self.assertEqual(work, 1_856_632_653_062 * 92 + 40)

    def test_detects_resource_and_terminal_mutations(self):
        row = dict(scenario=2, horizon_ns=363_900_000_000_000,
            application_completed=0, completed_operations=1_856_632_653_062,
            unfinished_operations=1,
            bus_work_ns={'control_base_including_partial': 1_856_632_653_062 * 92 + 40},
            CPU={'ARM_instructions_runtime': 0})
        check_fixed(row)
        variants = []
        wrong = copy.deepcopy(row); wrong['bus_work_ns']['control_base_including_partial'] += 1
        variants.append(wrong)
        wrong = copy.deepcopy(row); wrong['completed_operations'] -= 1; variants.append(wrong)
        wrong = copy.deepcopy(row); wrong['unfinished_operations'] = 0; variants.append(wrong)
        wrong = copy.deepcopy(row); wrong['CPU']['ARM_instructions_runtime'] = 1; variants.append(wrong)
        for wrong in variants:
            with self.assertRaises(AssertionError):
                check_fixed(wrong)


if __name__ == '__main__':
    unittest.main()
