"""Read-only r3 reproduction and addressed regressions; no RTL/STA."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

HERE = Path(__file__).resolve().parent


def main():
    spec = importlib.util.spec_from_file_location('t135_verify_r3', HERE/'align64.py')
    a = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(a)
    before = a.unchanged_sources()
    suite = unittest.defaultTestLoader.discover(str(HERE), 'test_*.py')
    tests = unittest.TextTestRunner(verbosity=1).run(suite)
    assert tests.wasSuccessful()
    run = subprocess.run([sys.executable, '-B', str(HERE/'align64.py')], cwd=a.b.ROOT)
    assert run.returncode == 0
    assert before == a.unchanged_sources()
    print(f'T135 r3: {tests.testsRun} addressed tests passed (19 historical + 6 new).')
    print('Engineer contract_check.calculate() exact; registered source stages fit 320/320ns.')
    print('Report-r3 byte-identical; selected risk/resources/calendar equal r2; only saturation price removed.')
    print('14 accepted sources, historical r1/r2 calculation/report/test files preserved byte-for-byte.')
    print('No RTL/STA/physical campaign; composed LOW/WCET/pad acceptance remains open.')


if __name__ == '__main__':
    main()
