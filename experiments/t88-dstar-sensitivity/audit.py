"""Read-only accepted-source audit, original-point controls, test protocol."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from decimal import Decimal,localcontext

import engine as e

ROOT=e.HERE.parent.parent


def assert_configuration():
    f=e.old.FAMILY;c=e.CFG;s=c['search'];m=c['monitor'];env=c['environment']
    assert s['z']==f['z'] and s['ERR_hold_s']==f['ERR_only']['h_s']
    assert s['monitor_hold_E_s']==[f['hold_ERR_s']]
    assert s['monitor_hold_M_s']==[f['hold_monitor_s']]
    assert m==dict(a_M='1000000',A_M='1000000',eta_per_s='0.001',w_s='1',d_s='1',
                   stride_divisor=2,kind='total_load',LOW_type='direct-fast')
    assert env==dict(q_R_over_bbar='2',rho_e_per_s='0.000001',D_Q_s='300',
        rho_b_per_s='0.048',l_per_s='0.001',T_Q_fraction_min='0.9',K_Q_max=1000)
    assert f['rho_b_per_s']==env['rho_b_per_s'] and f['l_per_s']==env['l_per_s']
    assert e.F(e.old.PROFILE['upper_to_lower_ratio'])==1
    assert e.old.PROFILE['eta_per_s']==m['eta_per_s']


def effective_inputs(out):
    rows=[]
    for shield in e.CFG['shields_g_cm2']:
        p=e.calendar(e.context(shield,'combined'),131)
        rows.append(dict(shield=shield,scope='all D* and all three channel variants',
            units=dict(T='s',b='s^-1',B='s^-1',FS='1',S2='s^-1',Dstar='expected parents / mission',
                       risk='conditional probability upper',cost='expected occupied-time fraction'),
            physical_qualification=False,
            environment={k:p[k] for k in ('T','eps','W','n','b','B','FS','S2','K','beta','beta0')},
            quotas=p['q'],mark_contract=p['cfg']['mark_contract']|{
                'D_star_full38_direct_exposure_upper':'variable prescribed axis D*, never optimized downward',
                'Dstar_meaning':'E[number of parents touching >=2 positions of at least one full word / mission]'},
            service=dict(c_ticks=p['c'],tick_lower_s=p['tm'],tick_upper_s=p['tp'],
                joint_U_WCET_required_upper_s=p['cm']/(1+p['margin']),
                physical_joint_U_WCET_s=None,dE_upper_s=p['dE'],decision_lead_ticks=p['G'],
                gate_upper_s=p['Gp'],fence_upper_s=p['f'],application_contract=p['cfg']['resources'],
                calendar='g chosen per witness; paired layout; inverse ka modulo W; ka odd'),
            channel=e.CFG['monitor'],quiet_control_profile=e.old.PROFILE,
            model_ERR_only=e.old.FAMILY['ERR_only'],
            monitor_window_at_g131=e.window(p),
            note='window/lease and resources are recomputed at selected g; source older monitor fields are not substituted'))
    e.json_write(out/'effective_inputs.json',rows)
    handoff=json.loads((out/'handoff.json').read_text())
    handoff['effective_inputs_file']='effective_inputs.json'
    handoff['effective_inputs_sha256']=hashlib.sha256((out/'effective_inputs.json').read_bytes()).hexdigest()
    handoff['engineering_source_sha256']=delivery_sources()
    e.json_write(out/'handoff.json',handoff)


def accepted_snapshot():
    paths=['experiments/t58-fixed-baseline-r0b','experiments/t72-r0a-onset-inputs',
           'experiments/t82-realistic-timing','theory/t80-realistic-channel.md',
           'theory/t80-realistic-channel-appendix.md','theory/t80-realistic-channel-inputs.json']
    raw=subprocess.check_output(['git','ls-tree','-r',e.CFG['base_sha'],'--',*paths],cwd=ROOT,text=True)
    ans={}
    for line in raw.splitlines():
        meta,path=line.split('\t');mode,kind,oid=meta.split()
        assert kind=='blob'
        data=(ROOT/path).read_bytes()
        actual=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        assert actual==oid, ('accepted dependency differs from base',path,oid,actual)
        ans[path]=dict(git_blob=oid,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data))
    return ans


def delivery_sources():
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(e.HERE.iterdir()) if p.suffix in ('.py','.json')}


def regressions(out):
    results=[]
    for label,path,pattern in [('accepted_T80_T82',e.T82,'test_t*.py'),
                               ('T88',e.HERE,'test_t88.py')]:
        cmd=[sys.executable,'-X','utf8','-B','-m','unittest','discover','-s',str(path),'-p',pattern,'-v']
        proc=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True)
        text=proc.stdout+proc.stderr
        (out/(label+'_tests.txt')).write_text(text,encoding='utf-8')
        assert proc.returncode==0,text
        count=int(re.search(r'Ran (\d+) tests?',text).group(1))
        results.append(dict(suite=label,count=count,returncode=proc.returncode))
    return results


def baseline(out):
    pilot=json.loads((e.HERE/'outputs/pilot.json').read_text())
    accepted=json.loads((e.T82/'outputs/t80_joint/selected.json').read_text())
    rows=[]
    for x in pilot['rows']:
        p=e.calendar(e.context(x['shield'],x['mode']),131)
        r=e.evaluate(p,x['result'])
        for k in ('risk_upper','quiet_upper','returns_upper'):
            original=e.F(x['result'][k])
            if x['mode']=='ERR-only' and k!='risk_upper':
                # The previously uncapped formula (10) is preserved as history;
                # the additional accepted hard-mask upper is labelled explicitly.
                assert r[k]<=original
            else:assert r[k]==original
        ids=[]
        if x['mode']!='ERR-only':
            matches=[a for a in accepted if a['set_representative']=='T73_published'
                and a['architecture']=='internal38' and a['shield']==x['shield']
                and a['mode']==x['mode'] and e.F(a['margin'])==e.F('.1')
                and a['low_type']=='direct-fast' and e.F(a['aM'])==10**6
                and e.F(a['w'])==e.F(a['d'])==1 and a['divisor']==2
                and e.F(a['qratio'])==2 and a['kind']=='total_load']
            assert matches
            for a in matches:
                for k in ('risk_upper','quiet_upper','returns_upper','objective'):
                    assert r[k]==e.F(a[k]),(x['mode'],x['shield'],k)
                ids.append(a['id'])
        rows.append(dict(shield=x['shield'],mode=x['mode'],Dstar=e.DMIN,
            accepted_calculation_ids=ids,original_tax=max(e.F(x['result'][k]) for k in ('quiet_upper','returns_upper')),
            hard_mask_capped_tax=r['objective'],risk_upper=r['risk_upper'],g=131,ka=r['ka'],
            source='accepted T82 selected rows' if ids else 'accepted err_scan, original pilot retained',
            historical_ERR_2_5_always_S=x['mode']=='ERR-only' and x['shield']=='2.5'))
    e.csv_write(out/'baseline_controls.csv',rows)
    return dict(rows=len(rows),exact_monitor_comparisons=sum(len(r['accepted_calculation_ids']) for r in rows),
                ERR_formula_9_controls=2,success=True)


def constant_checks(out):
    rows=json.loads((out/'constant_U.json').read_text());count=0;ends=[]
    def dec(x):
        x=e.F(x);return Decimal(x.numerator)/Decimal(x.denominator)
    with localcontext() as dc:
        dc.prec=90
        for r in rows:
            p=e.context(r['shield'],'combined');M=r['M']
            if not M:
                assert r['status']=='no_risk_candidate'
                continue
            # Recompute moments from the declared environment, independently
            # of the T58 rarity helper and without floating-point acceptance.
            b,B,T,FS=(dec(p[k]) for k in ('b','B','T','FS'))
            s2=b*b*T+(B+b)*FS
            assert abs(s2-dec(r['square_upper']))<Decimal('1e-75')
            slope=dec(p['beta'])*s2+p['K']*B/p['W']
            q=Decimal('.000003')+dec(r['Dstar'])
            here=q+M*dec(p['tp'])*slope
            nxt=q+(M+1)*dec(p['tp'])*slope
            assert here<=Decimal('.001') and nxt>Decimal('.001')
            assert abs(here-dec(r['risk_upper']))<Decimal('1e-75')
            occupied=Decimal(p['W']*p['c'])/M
            assert dec(r['cost_lower'])<=occupied<=dec(r['cost_upper'])
            assert r['monitor_cost']=='0' and r['physical_occupied_lower_s'] is None
            if r['resource_pass']:
                assert dec(r['peak_upper'])<=Decimal('.8')
                assert Decimal('1.1')*dec(r['delay_upper_s'])<=Decimal('.000003')
            count+=1
        for s in e.CFG['shields_g_cm2']:
            p=e.context(s,'combined');r=e.fixed(p,e.DMIN);m=r['M_resource_min']
            assert m is not None
            slope=p['beta']*r['square_upper']+p['K']*p['B']/p['W']
            direct=p['eps']-r['quota_upper']-m*p['tp']*slope
            end=e.fixed(p,direct);bad=e.fixed(p,direct+e.TOL)
            assert end['M']==m and end['resource_pass'] and not bad['resource_pass']
            br=e.bracket(direct)
            ends.append(dict(shield=s,**br,M_resource_min=m,
                exact_endpoint_risk=end['risk_upper'],next_Dstar=direct+e.TOL,
                next_status=bad['status'],cost_lower=end['cost_lower'],cost_upper=end['cost_upper']))
    e.json_write(out/'constant_endpoints.json',ends)
    e.csv_write(out/'constant_endpoints.csv',ends)
    return dict(precision=90,rows=count,M_and_next_checked=True,resource_endpoints=len(ends),success=True)
