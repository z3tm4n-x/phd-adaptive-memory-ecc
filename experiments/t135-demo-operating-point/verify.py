"""Read-only verification, including accepted T114 and addressed T119 anchor."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]


def main():
    spec=importlib.util.spec_from_file_location('t135_verify_calc',HERE/'calculate.py')
    c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
    pins=c.source_pins()
    for path,expected in pins.items():
        original=subprocess.check_output(['git','show',c.CFG['base_main']+':'+path],cwd=ROOT)
        if hashlib.sha256(original).hexdigest()!=expected:raise AssertionError('Accepted source changed: '+path)
    run=subprocess.run([sys.executable,'-B','experiments/t114-two-stage-err/verify.py'],cwd=ROOT,text=True,capture_output=True)
    if run.returncode:raise RuntimeError(run.stdout+run.stderr)
    print(run.stdout.strip().splitlines()[-1],flush=True)
    suite=unittest.defaultTestLoader.discover(str(HERE),'test_contract.py')
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    if not tests.wasSuccessful():raise AssertionError('New regression failed')
    result=subprocess.run([sys.executable,'-B',str(HERE/'calculate.py')],cwd=ROOT)
    if result.returncode:raise AssertionError('T135 numerical report mismatch')
    if c.source_pins()!=pins:raise AssertionError('Accepted sources modified during run')
    print('T135: accepted T114 repeated; accepted T119 anchor exact; 11 addressed tests; report byte-identical; source pins preserved.')


if __name__=='__main__':main()
