"""R1 weak-E repair witnesses and an exact, narrowly scoped price replay.

The signed v4 information certificate is reused only with its input and
unaffected calculation code unchanged. No q-cell search or codec campaign.
"""
import ast
from copy import deepcopy
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess

from codec import Code, ROOT
from comparison import NS, cost_result, read_bounds, service

HERE = Path(__file__).resolve().parent
REL = HERE.relative_to(ROOT).as_posix()
SNAPSHOT = '0111d42490269b984e0f60bf0831cb897e9e10cd'
REVIEW = '64132c369832175d332624a267b149fe11eb68f3'


def fractions(value):
    if isinstance(value, dict):
        return {k: fractions(v) for k, v in value.items()}
    if isinstance(value, list):
        return [fractions(v) for v in value]
    if isinstance(value, str):
        try:
            return F(value)
        except ValueError:
            pass
    return value


def blob(path):
    return subprocess.check_output(['git', 'cat-file', 'blob', SNAPSHOT+':'+REL+'/'+path], cwd=ROOT).replace(b'\r\n', b'\n')


def frozen_snapshot():
    """Reject a price-only replay if its frozen computational basis changed."""
    paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', SNAPSHOT, '--', REL], cwd=ROOT, text=True).splitlines()
    protected = [p[len(REL)+1:] for p in paths if
                 (p.endswith('.py') and not p.endswith(('/comparison.py', '/reproduce.py')))
                 or p.endswith(('/common-input.json', '/sources.json'))]
    for name in protected:
        if (HERE/name).read_bytes().replace(b'\r\n', b'\n') != blob(name):
            raise ValueError('R1 frozen basis changed: '+name)
    # Exact AST scope: one factor in cost_result and an optional frozen
    # certificate argument. Every risk/read/hold/calendar function is equal.
    old = ast.parse(blob('comparison.py'))
    new = ast.parse((HERE/'comparison.py').read_text(encoding='utf-8'))
    for node in new.body:
        if isinstance(node, ast.FunctionDef) and node.name == 'cost_result':
            assignment = next(x for x in node.body if isinstance(x, ast.Assign)
                              and any(isinstance(t, ast.Name) and t.id == 'repairs' for t in x.targets))
            expected = ast.parse('repairs=min(N,2*Fparents+U*Hard)').body[0]
            if ast.dump(assignment) != ast.dump(expected):
                raise ValueError('R1 repair formula differs from the signed correction')
            assignment.value = ast.parse('min(N,Fparents+U*Hard)', mode='eval').body
        if isinstance(node, ast.FunctionDef) and node.name == 'calculate':
            if node.args.args[-1].arg != 'information' or not isinstance(node.body[1], ast.If):
                raise ValueError('R1 certificate injection differs')
            expected = ast.parse('if information is None:\n    information=information_candidates(cfg)').body[0]
            if ast.dump(node.body[1]) != ast.dump(expected):
                raise ValueError('R1 certificate reuse condition differs')
            node.args.args.pop()
            node.args.defaults.pop()
            node.body[1:2] = node.body[1].body
    if ast.dump(old) != ast.dump(new):
        raise ValueError('R1 changed a calculation outside the local repair correction')
    raws = {name: blob('outputs/'+name) for name in
            ('results.json', 'informational.json', 'sensitivity.json', 'validation.json')}
    return dict(result=fractions(json.loads(raws['results.json'])),
                information=fractions(json.loads(raws['informational.json'])),
                validation=json.loads(raws['validation.json']),
                output_sha256={n: hashlib.sha256(b).hexdigest() for n,b in raws.items()},
                snapshot=SNAPSHOT, protected_files=protected)


def run(cfg, result, frozen):
    passed = []
    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        passed.append(name)

    # Same real code, one parent, no bad history: a permissible weak-E
    # survivor is repaired twice. No application write intervenes.
    witnesses = []
    W = cfg['words']
    code = Code(1)
    clean = code.encode(0x13579bdf)
    for mode,k in [('fixed',11), ('adaptive',27)]:
        word = 3 if mode == 'fixed' else pow(k,-1,W)
        starts = (164,164+W*196*(k if mode == 'fixed' else 1))
        appq = word*pow(5,-1,W) % W
        appstart = 600000+appq*1000020
        birth = 165
        live = {0: birth}
        trace = []
        for start in starts:
            decoded = code.decode(clean ^ sum(1 << b for b in live))
            live = {b: born for b,born in live.items() if born >= start}
            trace.append(dict(start_ns=start,snapshot_ns=start+48,
                              release_ns=start+service(cfg,39)['nominal']['E'],
                              ERR=decoded['ERR'],survivors=len(live)))
        check(mode+' weak-E two-repair witness before application',
              appstart > trace[-1]['release_ns'] and birth < trace[0]['snapshot_ns']
              and all(x['ERR'] for x in trace) and trace[0]['survivors']==1 and not live)
        witnesses.append(dict(mode=mode,word=word,parent_ns=birth,parents=1,
                              repairs=2,publications=2,max_error_weight=1,bad_history=False,
                              first_app_write_ns=appstart,trace=trace))

    changes = {}
    for name,row in result['rows'].items():
        oldrow = frozen['result']['rows'][name]
        check(name+' complete Q/period/timing/selection unchanged',
              {k:v for k,v in row.items() if k!='cost'} == {k:v for k,v in oldrow.items() if k!='cost'})
        old,c = oldrow['cost'],row['cost']
        hard = read_bounds(cfg,1 if name=='t1_adaptive' else row['k_passes'])['upper']
        new = min(c['read_count_upper'],2*c['expected_parent_count_upper']+row['risk']['upper']*hard)
        delta = new-old['repair_count_upper']
        delta_rate = delta/cfg['mission_s']
        bus_delta = delta_rate*(service(cfg,row['n'])['upper']['E']-service(cfg,row['n'])['upper']['R'])/NS
        check(name+' two-repair expected bound incl bad histories',c['repair_count_upper']==new and delta>0)
        check(name+' exact bus delta and invariant hard/lower',
              c['core_SRAM_fraction_upper']==old['core_SRAM_fraction_upper']+bus_delta
              and c['core_SRAM_fraction_lower']==old['core_SRAM_fraction_lower']
              and c['all_history_SRAM_core_upper']==old['all_history_SRAM_core_upper'])
        for field in ('full_cost_rates','energy_coefficients_per_second'):
            expected = deepcopy(old[field])
            for key,factor in [('scrub_corrections',1),('write_beats',3),('turnarounds',1)]:
                expected[key] += factor*delta_rate
            check(name+' exact '+field+' propagation; other actions unchanged',c[field]==expected)
        check(name+' read/hold/veto/controller/init/pending unchanged',
              all(c[key]==old[key] for key in c if key not in {
                  'repair_count_upper','core_SRAM_fraction_upper','full_cost_rates',
                  'energy_coefficients_per_second','veto_hard_cap_reached_per_s'}))
        # Endpoint U=0 detects the former one-parent formula; U=1 forces
        # the min(S_upper, ...) cap and must never manufacture extra reads.
        for U in (F(0),F(1)):
            test = cost_result(cfg,row['n'],row['t'],row['k_passes'],U,
                               name=='t1_adaptive',result['informational_certificate']['selected']['calendar'] if name=='t1_adaptive' else None)
            check(name+f' repair bound endpoint U={U}', test['repair_count_upper']==
                  (2*test['expected_parent_count_upper'] if U==0 else test['read_count_upper']))
        changes[name] = dict(old_repair_upper=old['repair_count_upper'],repair_upper=new,
                            repair_rate_addition=delta_rate,SRAM_fraction_addition=bus_delta,
                            SRAM_fraction_upper=c['core_SRAM_fraction_upper'])

    a=result['rows']['t1_adaptive']['cost']; two=result['rows']['t2_constant']['cost']
    fixed=result['rows']['t1_constant']['cost']; cmp=result['conditional_bus_comparison']
    check('exact revised veto threshold and sufficient 1057.380/s',
          cmp['extra_veto_rate_before_losing_selected_fixed_lower_comparison']==
          (fixed['core_SRAM_fraction_lower']-a['core_SRAM_fraction_upper'])/a['veto_core_fraction_slope_per_notification_per_s']
          > F('1057.380'))
    check('exact revised veto hard-cap boundary', a['veto_hard_cap_reached_per_s']==
          (a['all_history_SRAM_core_upper']-a['core_SRAM_fraction_upper'])/a['veto_core_fraction_slope_per_notification_per_s'])
    check('t2 hard upper below selected adaptive lower, independent of repair and v',
          two['all_history_SRAM_core_upper']<a['core_SRAM_fraction_lower'])
    check('service-limit Q unchanged; repair cost increases',
          cmp['t2_at_service_decode_limit']['Q_upper']==frozen['result']['conditional_bus_comparison']['t2_at_service_decode_limit']['Q_upper']
          and cmp['t2_at_service_decode_limit']['SRAM_core_upper']>frozen['result']['conditional_bus_comparison']['t2_at_service_decode_limit']['SRAM_core_upper'])
    return dict(count=len(passed),checks=passed,witnesses=witnesses,price_changes=changes,
                reviewed_snapshot=SNAPSHOT,theory_review=REVIEW,
                frozen_output_sha256=frozen['output_sha256'],
                scope='R1 exact price correction; historical 203 checks and q-cell search are separate evidence',
                scientific_acceptance=False)
