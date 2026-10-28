"""Orchestrator acceptance arithmetic; no new Q/policy cells are evaluated."""
from pathlib import Path
from fractions import Fraction as F
from math import gcd
import json, hashlib

root=Path(__file__).resolve().parents[3]
d=root/'experiments/regime-map-methodology-20261019/predictability-volume-20261028'
cfg=json.loads((root/'experiments/t186-method-comparison/code-strength/common-input.json').read_text(encoding='utf-8'))
saved=json.loads((d/'resource-result.json').read_text(encoding='utf-8'))
xm=F('0.99999'); xp=F('1.00001'); J=F('0.5'); T=F(cfg['mission_s'])
E=(3*16+20+3*16+8)*xp+J
ar=68*xp+J; aw=144*xp+J
ceil=lambda x:-((-x.numerator)//x.denominator)
frames=2+ceil((F(10**6)+max(E,aw)+J)/(1568*xm))
apps=1+ceil((F(10**6)+3000)/1000020)
peak=(8*frames*E+apps*(ar+aw)+frames*(64*xp+J))/10**6
response=320+80+320+100+1568*xp+J+aw
H=int(T*10**9)
offers=(H-1-100000)//1000020+1
lower_app=F(offers-1)*(68*xm-J)/H
for row in saved['rows']:
    W=row['useful_bytes']//4
    assert row['words']==W and row['raw_storage_required_bytes']==6*W
    assert gcd(3,W)==1 and W%8==0
    assert F(row['calendar']['nominal_minimum_full_pass_cycle_ns'])==196*W
    assert F(row['calendar']['cycle_lower_ns'])==196*W*xm-J
    assert F(row['calendar']['cycle_upper_ns'])==196*W*xp+J
    assert F(row['resource']['peak_including_full_reserved_management_slot'])==peak
    assert F(row['application']['inherited_response_envelope_ns'])==response
    assert F(row['resource']['available_serial_upper_for_necessary_exclusion'])==F(4,5)-lower_app
    assert row['fixed_class_excluded'] is None and row['M'] is None
print('Independent resource arithmetic: four rows agree.')
print('peak percent:',float(100*peak),'response ns:',float(response))
print('resource result SHA256:',hashlib.sha256((d/'resource-result.json').read_bytes().replace(b'\r\n',b'\n')).hexdigest())

# Candidate family published only in #186 comment6464956513. Inspect its
# concentration algebra, without accepting it or generating map rows.
e=cfg['environment']; b=F(e['reference_background_per_s'])
B=F(e['reference_peak_per_s']); Fs=F(e['reference_solar_mass'])
N=58440; width=600; a0=2*Fs/(N*width)
triangle_M2=b*b*T+2*b*Fs+F(2,3)*a0*Fs
old_window_M2_cap=b*b*T+(B+b)*Fs
print('candidate alpha=0 amplitude a0:',float(a0))
print('candidate alpha=0 exact reference integral p^2:',float(triangle_M2))
print('old window reference moment upper:',float(old_window_M2_cap))
print('upper/exact diagnostic ratio:',float(old_window_M2_cap/triangle_M2))
print('Not a Q ratio, cost ratio, physical estimate, or published theory acceptance.')
