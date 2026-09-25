"""Bounded Scientific Reviewer checks. Stdlib; no upstream run or retuning.

Run from any directory: python THIS_FILE /path/to/exact/repository/checkout
The only production import is semantic_model, tested against separate state logic.
"""
import base64, csv, gzip, hashlib, importlib.util, itertools, json, math
import pathlib, platform, subprocess, sys
from fractions import Fraction as F

root = pathlib.Path(sys.argv[1]).resolve()
p = root/'experiments/RE-FIXED-ADAPTIVE-FEASIBILITY-01'
cfg = json.loads((p/'config.json').read_text())
out = {'reviewed_commit':'03e6c4ad8570fa3351378c9c77b1f9c2fe943f15',
       'python':platform.python_version(), 'platform':platform.platform()}

def blob(path):
    b=path.read_bytes()
    return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()

checked=0
m=json.loads((p/'FINAL_MANIFEST.json').read_text())
for field in ['immutable_preverification_files','final_machine_results']:
    for name,sha in m[field].items():
        assert blob(p/name)==sha;checked+=1
        if field=='immutable_preverification_files':
            actual=subprocess.check_output(['git','rev-parse',
                'e8713d187592c9b810ecf4194b6da7108d898e22:experiments/RE-FIXED-ADAPTIVE-FEASIBILITY-01/'+name],cwd=root,text=True).strip()
            assert actual==sha
for name,sha in m['full_preregistered_grid_archive']['chunks'].items():
    assert blob(p/name)==sha;checked+=1
repair=json.loads((p/'REPAIR_MANIFEST.json').read_text())
for name,sha in repair['files'].items():
    assert blob(p/name)==sha;checked+=1
data=base64.b64decode(''.join(f.read_text().strip() for f in sorted((p/'outputs').glob('*.b64.part*'))))
raw=gzip.decompress(data)
assert hashlib.sha256(raw).hexdigest()==m['full_preregistered_grid_archive']['raw_csv_sha256']
rows=list(csv.DictReader(raw.decode().splitlines()))
assert len(rows)==720
out['identity']={'manifest_blobs_checked':checked,'decoded_rows':len(rows),
                 'decoded_sha256':hashlib.sha256(raw).hexdigest()}

# Production-linked semantic oracle: integer bitmask, explicit latch and commits.
spec=importlib.util.spec_from_file_location('review_semantics',p/'semantic_model.py')
mod=importlib.util.module_from_spec(spec);sys.modules[spec.name]=mod;spec.loader.exec_module(mod)
stream_count=0
sites=list(itertools.product([0,2,4],range(3)))
for length in range(4):
    for stream in itertools.combinations_with_replacement(sites,length):
        actual=mod.WordState(nbits=3); mask=0; latched=None; first=None
        for t in range(6):
            for when,bit in stream:
                if when==t:
                    mask ^= 1<<bit
                    if mask.bit_count()>1 and first is None:first=t
                    actual.inject_toggle(bit,t)
            if t==1:
                weight=mask.bit_count()
                expected='clean' if weight==0 else 'correctable' if weight==1 else 'uncorrectable'
                assert actual.read_and_decode(t)==expected
                latched=0 if weight==1 else None
            if t==3:
                written=latched is not None
                assert actual.complete_conditional_write(t)==written
                if written:mask=latched
            assert actual.errors=={i for i in range(3) if mask>>i&1}
            assert actual.first_cap_time==first
        stream_count+=1
out['semantic_oracle_streams']=stream_count

# Actual served time, not counts of exported residuals or copied envelope helper.
W=4*1024**2//4; H=F(cfg['temporal_shape']['hours']); T=H*3600
n=39;d=F(38,39); tr=F(str(cfg['service_profiles']['4']['read_s']))
tw=F(str(cfg['service_profiles']['4']['write_s'])); g=tr+tw; J=max(tr,tw)
sh=cfg['temporal_shape']; mu=F(W*n)*F(str(cfg['error_rate_per_physical_bit_day']))/24
A=H*mu; vmax=mu*F(str(sh['max_old_per_hour']))/F(str(sh['mean_old_per_hour']))
v0=mu*F(str(sh['nu0_old_per_hour']))/F(str(sh['mean_old_per_hour']))
principal=json.loads((p/'outputs/final_results.json').read_text())['principal']
C=F(str(principal['causal_C'])); spacing=3600*C/(W*vmax); rho=g/spacing
delaycases=windows=0;max_excess=F(0)
for latebits in itertools.product([0,J],repeat=6):
    # The first operation is deliberately delayed and a following one may be on time.
    ops=[]
    for k,late in enumerate(latebits):
        due=F(k)*spacing
        app=None if late==0 else mod.Op('app',float(due),float(J))
        got=mod.WordBoundaryArbiter(float(J),float(g)).dispatch_scrub(float(due),app)
        assert abs(got.start-float(due+late))<1e-20
        ops.append((due+late,due+late+g))
    for i,j in itertools.combinations(range(12),2):
        times=sorted(x for op in ops for x in op); a,b=times[i],times[j]
        served=sum((max(F(0),min(b,end)-max(a,start)) for start,end in ops),F(0))
        assert served<=g+rho*(b-a)
        max_excess=max(max_excess,served-rho*(b-a));windows+=1
    delaycases+=1
assert J<g and spacing>J+g
# Release-count envelope is not an executed-start-count envelope.
two_start_window=spacing-J+F(1,10**15)
assert 2*g>g+rho*two_start_window
out['service']={'jitter_patterns':delaycases,'actual_time_windows':windows,
    'largest_observed_excess_ns':float(max_excess*10**9),
    'burst_allowance_ns':float(g*10**9),
    'delay_us':float((8*J+g)/(1-rho)*10**6),
    'busy_period_us':float((8*J+g)/(F(1,2)-rho)*10**6),
    'one_second_occupancy_upper':float(rho+g),
    'start_count_envelope_counterexample_window_ns':float(two_start_window*10**9)}

# Discrete conditional-write guard for Fixed. No periodic-reset domination assumed.
L=J+tr+tw
B=F(1,400)
# For any phase, at least W*(T/tau-2) reads; finite-horizon correction retained.
tau_resource=W*tr/(B+2*W*tr/T)
s2=H*mu*mu*(1+F(str(sh['cv2_old'])))
def short_core(tau):
    x=tau/3600
    exponent=float(d*s2/(2*W)*(x-2*x*x)*(1-L/tau)**2)*math.exp(-float(vmax/W*x))
    return -math.expm1(-exponent)
def long_core(tau):
    x=tau/3600; M=F(W)*(H/x+2)
    retained=A-M*vmax*L/(3600*W)
    exponent=float(d*retained**2/(2*M))*math.exp(-float(vmax*x/W))
    return -math.expm1(-exponent)
shortvals=[short_core(tau_resource),short_core(F(900))]
longvals=[long_core(F(900)),long_core(F(3600))]
assert min(shortvals+longvals)>.001
M900=F(W)*(H/F(1,4)+2)
retained900=A-M900*vmax*L/(3600*W)
# A uniform long-range bound: largest interval count and smallest exponential
# are deliberately taken at different endpoints. No monotonicity assumption.
long_uniform=-math.expm1(-float(d*retained900**2/(2*M900))*math.exp(-float(vmax/W)))
assert long_uniform>.001
out['fixed_with_finite_horizon_and_quiet_guard']={
    'resource_tau_lower_s':float(tau_resource),'guard_ns':float(L*10**9),
    'short_core_at_resource_and_900':shortvals,'long_core_at_900_and_3600':longvals,
    'uniform_lower_on_900_to_3600':long_uniform}

# Information-interface falsifier: change only the previously unspecified first scalar.
eta=F(str(sh['lag1_eta'])); coeff=d/(2*W)
R_ub=eta*A*A/(A+v0-vmax)
h=F(1,1000)  # addressed admissible positive initial scalar, not a new tuned scenario
# Old hat-sum <= A+v0, hence an independent LOWER bound on its ratio integral.
R_old_lower=eta*A*A/(A+v0)
R_new_lower=R_old_lower+v0*v0/h-v0
nominal_pair=F(str(principal['causal_risk_upper']))-A*vmax*tw/(3600*W)
assert coeff*C*R_new_lower>F(1,1000)
out['warm_start_certificate_counterexample']={
    'first_scalar_h':float(h),'first_true_rate_h':float(v0),
    'new_ratio_lower':float(R_new_lower),'published_ratio_upper':float(R_ub),
    'new_pair_certificate_lower':float(coeff*C*R_new_lower),
    'interpretation':'certificate invalidity for unrestricted warm start; not physical F lower bound'}

# Independent conservative physical timing transfer: deterministic enlarged read bins.
# Actual read completion is in [release, release+J+tr].
read_lag=J+tr; e=vmax*read_lag/(3600*W)
Nmax=math.ceil(T/spacing)+W+2
timing_guard=A*e+F(Nmax)*e*e/2
rmw=A*vmax*tw/(3600*W)
assert nominal_pair+timing_guard+rmw<F(1,1000)
avg=F(str(principal['causal_avg_fraction'])); cold149=avg+F(149)/H*rho+g/T
assert cold149<B
out['cold_and_timing_bound']={
    'read_lag_ns':float(read_lag*10**9),'pair_timing_guard':float(timing_guard),
    'risk_upper':float(nominal_pair+timing_guard+rmw),
    'cold_plus_148h_resource_fraction_upper_with_one_visit':float(cold149),
    'controller_fraction_room_at_0p25':float(B-cold149)}

# Independent exact two-bit SEC survival: different first two marks are sufficient
# after a clean reset; compare to the standard exactly-two event probability.
for k in [3,7,39]:
    distinct=sum(a!=b for a,b in itertools.product(range(k),repeat=2))
    assert F(distinct,k*k)==F(k-1,k)

out['all_checks_passed']=True
print(json.dumps(out,indent=2,sort_keys=True))
