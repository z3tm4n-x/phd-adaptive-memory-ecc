"""Compact evidence transfer and byte-preservation checks for this checkpoint."""
import argparse
import hashlib
import json
import re
import zipfile
from pathlib import Path

from audit_sta import source_bytes
from run import protected_bytes

HERE = Path(__file__).resolve().parent
BASE = '3a3656bdf09b7e99fd5f1de2baabb1b55e6a905d'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(name):
    return json.loads((HERE/'outputs'/name).read_text())


def checks():
    same = {}
    for name in ('integration.json', 'rtl.json'):
        old = source_bytes('outputs/'+name, BASE)
        new = (HERE/'outputs'/name).read_bytes()
        if old != new:
            raise ValueError('integration/RTL result changed: '+name)
        same[name] = digest(new)
    gate = read('gate_equivalence.json')
    if gate['production_sha256'] != digest((HERE/'rtl/permission_gate.sv').read_bytes()):
        raise ValueError('gate RTL drift')
    if gate['checker_sha256'] != digest((HERE/'gate_check.py').read_bytes()):
        raise ValueError('gate checker drift')
    if gate['induction']['status'] != 'proved' or gate['induction']['assumptions'] != 0:
        raise ValueError('gate proof missing')
    if not all(m['rejected'] for m in gate['mutants'].values()):
        raise ValueError('gate mutant survived')
    board = read('board_components.json')
    for name, expected in board['source_files_sha256'].items():
        if digest((HERE/name).read_bytes()) != expected:
            raise ValueError('board source drift: '+name)
    ownership = read('composition_ownership.json')
    if ownership['checker_sha256'] != digest((HERE/'composition_check.py').read_bytes()):
        raise ValueError('composition checker drift')
    return dict(baseline=BASE, byte_identical_outputs=same, accepted_inputs=protected_bytes(),
                composition_status={n: read(n)['status'] for n in ('composition.json', 'composition_ownership.json')})


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    verified = checks()
    archive = HERE/'outputs/alarm-evidence.zip'
    manifest = HERE/'outputs/alarm-evidence.json'
    if args.write:
        entries = {}
        for label, name in [('gate', 'gate_equivalence.json'), ('composition-base', 'composition.json'),
                            ('composition-ownership', 'composition_ownership.json')]:
            record = read(name)
            raw = Path(record['raw_directory'])
            files = (['proof.log', 'proof.sv', 'gold.sv', 'gate.sv'] if label == 'gate' else
                     ['build.ys', 'yosys.log', 'abc.log', *sorted(f.name for f in raw.glob('*.sv'))])
            for file in files:
                entries[label+'/'+file] = (raw/file).read_bytes()
        for file in ('alarm-final-regression.log', 'alarm-final-unit.log'):
            entries['regression/'+file] = (HERE/'.build'/file).read_bytes()
        text = entries['regression/alarm-final-regression.log'].decode()
        elapsed = re.findall(r'Elapsed: ([\d.]+)s', text)
        if len(elapsed) != 1 or 'FAILED' in text:
            raise ValueError('full regression incomplete')
        with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as z:
            for name, raw in sorted(entries.items()):
                z.writestr(name, raw)
        record = dict(**verified, archive_sha256=digest(archive.read_bytes()),
                      entries_sha256={n: digest(v) for n, v in entries.items()},
                      full_regression_elapsed_s=float(elapsed[0]),
                      note='earlier 22-property attempt used an earlier runner version; exact generated sources and logs retained',
                      source_files_sha256={n: digest((HERE/n).read_bytes()) for n in
                                           ('delivery_check.py', 'gate_check.py', 'composition_check.py', 'board_check.py',
                                            'compare_alarm.py', 'alarm_detail.tcl')})
        manifest.write_text(json.dumps(record, indent=2)+'\n', encoding='utf-8')
    else:
        record = json.loads(manifest.read_text())
        if any(record[k] != v for k, v in verified.items()) or digest(archive.read_bytes()) != record['archive_sha256']:
            raise ValueError('delivery manifest/archive mismatch')
        with zipfile.ZipFile(archive) as z:
            if set(z.namelist()) != set(record['entries_sha256']):
                raise ValueError('missing evidence member')
            for name, expected in record['entries_sha256'].items():
                if digest(z.read(name)) != expected:
                    raise ValueError('evidence member mismatch: '+name)
        for name, expected in record['source_files_sha256'].items():
            if digest((HERE/name).read_bytes()) != expected:
                raise ValueError('delivery checker source changed: '+name)
    print(json.dumps(verified, indent=2))


if __name__ == '__main__':
    main()
