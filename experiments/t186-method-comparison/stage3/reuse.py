"""Read-only imports from the accepted stage2 and digital reference."""
import importlib.util
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]


def load(name,path):
    if name in sys.modules:
        return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
    return module


calendar=load('t186_accepted_stage2_engine',HERE.parent/'stage2/engine.py')
policies=load('t186_accepted_stage2_policies',HERE.parent/'stage2/policies.py')
formats=load('t186_accepted_stage2_scenarios',HERE.parent/'stage2/scenarios.py')
