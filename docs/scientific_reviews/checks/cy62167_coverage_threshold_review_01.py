"""SR-only finite checks. No RE scientific module is imported.

Usage: python3 -B this_file.py REPO --archive EXACT_ZIP --output RESULT_JSON
The ZIP check is byte provenance, not a NetCDF decoding/recovery check.
Only the explicitly requested output is written. Production query() is reached
through its CLI; expected arithmetic uses scaled integers and rational values.
"""
import argparse
import ast
import base64
import bisect
import csv
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from fractions import Fraction as F
import hashlib
import io
import json
import math
from pathlib import Path
import platform
import subprocess
import sys
import zipfile
import zlib

import numpy as np

TARGET = 'a9d9b74b9ac03a4eb20b209eb14552d5b914e21a'
BASE = '64a7a1f436b2abd6997d37d14e6ce571e3a480c8'
REL = 'experiments/RE-CY62167-COVERAGE-THRESHOLD-01'


def run(repo, archive):
    p = repo / REL
    checks = {}

    def check(name, condition):
        checks[name] = bool(condition)
        if not condition:
            raise AssertionError(name)

    def git(ref, path):
        return subprocess.check_output(['git', '-C', str(repo), 'show', ref + ':' + path])

    def rational_decimal(s):
        # Decimal is used only for exact parsing, never rounded arithmetic.
        t = Decimal(s).as_tuple()
        v = int(''.join(map(str, t.digits))) * (-1 if t.sign else 1)
        return F(v * 10**max(t.exponent, 0), 10**max(-t.exponent, 0))

    manifest = json.loads((p/'MANIFEST.json').read_text())
    for e in manifest['files']:
        raw = (p/e['path']).read_bytes()
        check('manifest:' + e['path'], len(raw) == e['bytes'] and
              hashlib.sha256(raw).hexdigest() == e['sha256'] and
              hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == e['git_blob'])
    for e in json.loads((p/'recovery/source_manifest.json').read_text()):
        raw = (p/e['package_path']).read_bytes()
        expected = (git(e['commit'], e['source_path']) if 'commit' in e else
                    zlib.decompress(base64.b85decode((p/e['derived_from']).read_bytes())))
        check('source:' + e['package_path'], raw == expected)

    members = json.loads((p/'recovery/outputs/selected_recovery.json').read_text())['data_source_members']
    if archive:
        check('archive SHA', hashlib.sha256(archive.read_bytes()).hexdigest() ==
              '7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581')
        with zipfile.ZipFile(archive) as z:
            found = {Path(n).name: hashlib.sha256(z.read(n)).hexdigest()
                     for n in z.namelist() if n.endswith('.nc')}
        check('all 59 archive members', found == members and len(found) == 59)

    rows = list(csv.DictReader((p/'selected_rate.csv').open()))
    start = datetime(2026, 1, 19, 4, tzinfo=timezone.utc)
    check('288 ordered complete blocks', len(rows) == 288 and all(
        datetime.fromisoformat(row['timestamp_utc']) == start+timedelta(seconds=300*i)
        and row['duration_s'] == '300' for i, row in enumerate(rows)))
    check('slice metadata', all(all(row[k] == v for k, v in {
        'shield_mm':'10', 'sigma_model':'main_loglog', 'direction_scenario':'central_mean',
        'scenario':'DREG', 'mapping':'W32_seq'}.items()) for row in rows))
    nus = [rational_decimal(row['nu_C_bit_DREG_s_1']) for row in rows]
    rates = [rational_decimal(row['r_bit_s_1']) for row in rows]
    check('one normalization and no direct substitution', all(
        v >= 0 and r >= 0 and v == 2**24*r and F(row['r_D_DREG_s_1']) == 0
        for row, v, r in zip(rows, nus, rates)))
    scale = math.lcm(*(v.denominator for v in nus))
    integers = [v.numerator*(scale//v.denominator) for v in nus]
    unit = scale * 2**24
    I1 = F(300*sum(integers), unit)
    I2 = F(300*sum(v*v for v in integers), unit*unit)
    exact = {'I1':I1, 'I2_s_1':I2, 'a':2**19*math.comb(32,2)*I2,
             'b_s_1':31*2**19*I1}
    result = json.loads((p/'recovery/outputs/cw_bounds.json').read_text())
    for name, v in exact.items():
        entry = result[name]
        lo, hi = F(entry['lower']), F(entry['upper'])
        check('exact and tight enclosure:' + name, F(entry['exact']) == v and
              lo <= v <= hi and hi-lo <= F(1,10**40) and
              (hi*10**40).denominator == (lo*10**40).denominator == 1)
    a, b = F(result['a']['upper']), F(result['b_s_1']['upper'])
    eps = F(1,1000)
    t = (eps-a)/b
    threshold = result['domain']['delta_limit_s']
    check('exact threshold and directed display', F(threshold['exact']) == t and
          F(threshold['lower']) <= t <= F(threshold['upper']) and
          threshold['lower'] != threshold['upper'])
    for q in result['probes']:
        d = F(q['delta_s'])
        u = min(F(1), a+b*d)
        check('exported probe:' + str(d), F(q['U_upper']['exact']) == u and
              F(q['signed_slack']['exact']) == eps-u and q['sufficient'] == (u <= eps))

    cases = [('zero',a,b,F(0),F(0)), ('threshold',a,b,t,F(0)),
             ('below',a,b,F(threshold['lower']),F(0)),
             ('above',a,b,F(threshold['upper']),F(0)),
             ('100ns coverage equality',a,b,F(1,10**7),eps-a-b/F(10**7)),
             ('100ns excessive coverage',a,b,F(1,10**7),eps-a-b/F(10**7)+F(1,10**40)),
             ('negative slack',a,b,F(1,10**6),F(0)),
             ('saturation',a,b,F(999,1000),F(0)),
             ('b0 all',F(0),F(0),F(999,1000),eps),
             ('b0 equality',eps,F(0),F(0),F(0)),
             ('b0 empty',2*eps,F(0),F(0),F(0)),
             ('only delta0',eps,F(1),F(0),F(0))]
    for name, aa, bb, dd, cc in cases:
        proc = subprocess.run([sys.executable,'-B',str(p/'cw_calculate.py'),'query',
            '--a',str(aa),'--b',str(bb),'--delta',str(dd),'--coverage',str(cc)],
            capture_output=True,text=True,check=True)
        q = json.loads(proc.stdout); u = min(F(1),aa+bb*dd)
        check('production CLI:' + name, F(q['U_upper']['exact']) == u and
              F(q['signed_slack']['exact']) == eps-u and q['sufficient'] == (u+cc <= eps))
    for d in ['1','-1/1000000']:
        proc = subprocess.run([sys.executable,'-B',str(p/'cw_calculate.py'),'query',
            '--a','0','--b','0','--delta',d],capture_output=True)
        check('reject outside executor domain:' + d, proc.returncode != 0)

    # Independent chronological interval intersection, not the duty formula.
    # Actual first/last rates and largest rising/falling adjacent pairs.
    indices = sorted({0,286,max(range(287),key=lambda i: rates[i+1]-rates[i]),
                       min(range(287),key=lambda i: rates[i+1]-rates[i])})
    window_cases = 0
    for ix in indices:
        rr = rates[ix:ix+2]
        def exposure(left,right):
            return sum((max(F(0),min(right,F(300*(j+1)))-max(left,F(300*j)))*v
                        for j,v in enumerate(rr)),F(0))
        for phase in [F(0),F(1,3),F(17,19)]:
            all_checks = [phase+k for k in range(-1,601)]
            actual_checks = [c for c in all_checks if 0 <= c < 600]
            edges = sorted({F(0),F(600),*actual_checks})
            pair_exposures = [exposure(x,y) for x,y in zip(edges,edges[1:])]
            check(f'pair partial intervals:{ix}:{phase}', all(
                y-x <= 1 for x,y in zip(edges,edges[1:])) and
                sum(v*v for v in pair_exposures) <= 300*sum(v*v for v in rr))
            for d in [F(0),F(1,10**7),F(1,7),F(999,1000)]:
                ext = sum((exposure(c,c+d) for c in all_checks),F(0))
                actual = sum((exposure(c,c+d) for c in actual_checks),F(0))
                check(f'window sweep:{ix}:{phase}:{d}',
                      0 <= actual <= ext and ext == d*300*sum(rr))
                window_cases += 1

    with np.load(p/'recovery/outputs/radar_transport.npz',allow_pickle=False) as z:
        E = z['energy_mev'].copy()
        check('matrix axes', E.shape == (192,) and E[0] == .11 and E[-1] == 390 and
              bool(np.all(np.diff(E)>0)) and list(z['shield_mm']) == [0,1,2,3,5,7,10])
        for name in ['primary','secondary']:
            check('matrix finite nonnegative:' + name, z[name].shape == (7,192,192)
                  and bool(np.isfinite(z[name]).all()) and bool((z[name]>=0).all()))
        zero_primary = float(np.max(np.abs(z['primary'][0]-np.eye(192))))
        zero_secondary = float(np.max(np.abs(z['secondary'][0])))
        # Use the declared numerical gate, not unjustified exact float identity.
        check('zero shield from actual matrix', zero_primary <= 1e-14 and zero_secondary <= 1e-14)

    tree = ast.parse((p/'recovery/historical/upstream_interface.py').read_text())
    mult = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
                and any(isinstance(t,ast.Name) and t.id == 'MULT_POINTS' for t in n.targets))
    reg = list(csv.DictReader((p/'recovery/historical/registered_direct_by_energy.csv').open()))
    energies = [float(row['energy_mev']) for row in reg]
    m = [F(int(row['accumulation_bits_W32seq']),int(row['N_registered_clusters'])) for row in reg]
    k = [F(nb,ne) for energy,ne,nb,n1 in mult]
    check('aligned multiplicity knots', energies == [v[0] for v in mult])
    differing = [e for e,mm,kk in zip(energies,m,k) if mm != kk]
    check('six unequal populations', differing == [29,40,80,124,164,186] and m[-1]/k[-1] == F(4323,4324))
    check('registered direct zero only', all(int(row['N_direct_W32seq']) == 0 and
          F(row['p_registered_direct_W32seq']) == 0 for row in reg))
    def interpolate(x, values):
        if x < energies[0]: return 1.0
        j = bisect.bisect_right(energies,x)
        if j == len(energies): return float(values[-1])
        left,right = energies[j-1],energies[j]
        alpha = (math.log(x)-math.log(left))/(math.log(right)-math.log(left))
        return (1-alpha)*float(values[j-1])+alpha*float(values[j])
    mg = [interpolate(float(x),m) for x in E]
    kg = [interpolate(float(x),k) for x in E]
    weights = [mm/kk for mm,kk in zip(mg,kg)]
    maxrel = maxup = maxreference = 0.0
    ref = list(csv.DictReader(io.StringIO(git(BASE,'experiments/RE-GOES19-PROTON-RATE-01/proton_rate_5min.csv').decode())))
    # Match by named timestamps; field name is checked, never chosen numerically.
    selected_times = {row['timestamp_utc'] for row in rows}
    reference = {row['timestamp_utc']:float(row['d10_lambda_central_s-1']) for row in ref
                 if row['timestamp_utc'] in selected_times}
    check('reference selected completeness', set(reference) == selected_times)
    with np.load(p/'recovery/outputs/selected_energy_contributions.npz',allow_pickle=False) as z:
        check('contribution axes', np.array_equal(E,z['energy_mev']) and
              z['density'].shape == (288,2,192) and z['highbit'].shape == (288,2))
        check('independent interpolated weights',
              max(abs(x-y) for x,y in zip(mg,z['mreg'])) < 1e-14 and
              max(abs(x-y) for x,y in zip(kg,z['kbar'])) < 1e-14 and
              bool(np.count_nonzero(z['preg']) == 0))
        check('nonnegative saved components', all(bool(np.isfinite(z[n]).all() and (z[n]>=0).all())
              for n in ['density','highbit']))
        for i,row in enumerate(rows):
            sides = [math.fsum([float(v)*w for v,w in zip(z['density'][i,d],weights)] +
                     [float(z['highbit'][i,d])*float(m[-1]/k[-1])]) for d in range(2)]
            value = math.fsum(sides)/2
            observed = float(row['nu_C_bit_DREG_s_1'])
            maxrel = max(maxrel,abs(value-observed)/observed if observed else abs(value))
            upstream = math.fsum(float(v) for v in z['density'][i].flat)/2 + math.fsum(z['highbit'][i])/2
            observed_up = float(row['upstream_total_s_1'])
            maxup = max(maxup,abs(upstream-observed_up)/observed_up)
            old = reference[row['timestamp_utc']]
            maxreference = max(maxreference,abs(upstream-old)/old)
    check('all 288 DREG component values', maxrel <= 1e-12)
    check('all 288 unweighted component values', maxup <= 1e-12)
    check('saved-components vs frozen upstream reference', maxreference <= 1e-6)
    return {'reviewed_target':TARGET,'python':sys.version,'platform':platform.platform(),
        'numpy':np.__version__, 'checks_passed':len(checks),'checks':checks,
        'window_cases':window_cases, 'integer_scale':str(scale),
        'exact_values':{k:str(v) for k,v in exact.items()},'threshold_exact_s':str(t),
        'slack_100ns_exact':str(eps-a-b/F(10**7)),
        'differing_knots_mev':differing,'zero_shield_primary_max_abs':zero_primary,
        'zero_shield_secondary_max_abs':zero_secondary,'DREG_component_max_relative':maxrel,
        'upstream_component_max_relative':maxup,'frozen_reference_max_relative':maxreference,
        'raw_netcdf_recovery':'NOT_PERFORMED_BY_THIS_CHECKER',
        'scope':'Independent finite arithmetic, source provenance, matrix structure and saved-component checks; shared model/data, no physical validation.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('repo',type=Path)
    ap.add_argument('--archive',type=Path)
    ap.add_argument('--output',type=Path,required=True)
    args = ap.parse_args()
    result = run(args.repo.resolve(),args.archive)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k != 'checks'},indent=2))
