"""Read-only r4 exact reproduction, source pins and addressed regressions."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent


def main():
    spec=importlib.util.spec_from_file_location('t135_verify_r4',HERE/'integrated_check.py')
    a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
    before=a.unchanged_sources()
    suite=unittest.defaultTestLoader.discover(str(HERE),'test_*.py')
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    assert result.wasSuccessful()
    run=subprocess.run([sys.executable,'-B',str(HERE/'integrated_check.py')],cwd=a.b.ROOT)
    assert run.returncode==0
    assert before==a.unchanged_sources()
    print(f'T135 r4: {result.testsRun} addressed tests passed (25 historical + 8 new).')
    print('Integrated bounds.calculate() repeated read-only at 99c0a41; report-r4 byte-identical.')
    print('Selected risk/calendar/resources equal r3 exactly; only bounded recovery tails added to price.')
    print('14 accepted sources, 10 historical T135 files and 3 address-contract sources unchanged.')
    print('Five predeclared rows only; no RTL/STA/PDR/physical campaign; complete hardware acceptance remains open.')


if __name__=='__main__':main()
