"""Run the frozen whole profile, or a separately labelled technical prefix."""
import gzip
import hashlib
import json
from pathlib import Path
from sparse_inputs import build as sparse_build

HERE=Path(__file__).resolve().parent


def build(case='burst',pilot_events=0):
    if case!='burst':
        if pilot_events:raise ValueError('pilot prefix only applies to burst')
        return sparse_build(case)
    passport=json.loads((HERE/'outputs/burst-input.json').read_text())
    path=HERE/'outputs/burst-stimulus.json.gz'
    assert hashlib.sha256(path.read_bytes()).hexdigest()==passport['burst-stimulus_sha256']
    with gzip.open(path,'rt') as f:stim=json.load(f)
    if pilot_events:
        assert 0<pilot_events<len(stim['injections'])
        stop=stim['injections'][pilot_events-1]['at_ns']+1_000_000_000
        # Preserve all original arrivals before stop (also a near neighbour).
        stim['injections']=[e for e in stim['injections'] if e['at_ns']<stop]
        stim['horizon_ns']=(stop+3)//4*4
        stim['scenario']='burst-pilot'
        stim['pilot_only']=True
    return stim
