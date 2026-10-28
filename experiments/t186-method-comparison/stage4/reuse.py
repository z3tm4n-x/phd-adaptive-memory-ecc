"""Read-only accepted code, loaded under distinct module names."""
import importlib.util
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def load(name,path):
    if name in sys.modules:return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod
    spec.loader.exec_module(mod);return mod

calendar=load('s4_accepted_grid',HERE.parent/'stage2/engine.py')
policies=load('s4_accepted_policies',HERE.parent/'stage2/policies.py')
formats=load('s4_accepted_formats',HERE.parent/'stage2/scenarios.py')
legacy_app=load('s4_accepted_app',HERE.parent/'stage3/application.py')
generator=load('s4_accepted_generator',HERE.parent/'stage3/generator.py')
