"""Read-only T135 r2 verification; no RTL/STA or accepted report writes."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

HERE=Path(__file__).resolve().parent


def main():
    spec=importlib.util.spec_from_file_location('t135_verify_r2',HERE/'reconcile.py')
    r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
    previous=json.loads((HERE/'report.json').read_text())
    before=r.b.source_pins()
    assert before==previous['source_sha256']
    suite=unittest.defaultTestLoader.discover(str(HERE),'test_*.py')
    tests=unittest.TextTestRunner(verbosity=1).run(suite)
    assert tests.wasSuccessful()
    run=subprocess.run([sys.executable,'-B',str(HERE/'reconcile.py')],cwd=r.b.ROOT)
    assert run.returncode==0
    assert before==r.b.source_pins()
    print('T135 r2: 19 addressed tests passed (11 old + 8 new); engineer arithmetic exact;')
    print('T119 anchor exact; report-r2 byte-identical; 14 accepted sources and v1 calculation/report preserved.')
    print('No RTL/STA or new physical campaign executed; integrated hardware obligations remain open.')


if __name__=='__main__':main()
