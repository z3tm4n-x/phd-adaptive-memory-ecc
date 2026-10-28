"""One accepted PR294 point; exact fractions and directed exponential bounds.

Default replays first-point-result.json. --write writes only this new result.
No old result, environment, hardware contract or remaining grid is changed.
"""
import argparse
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import importlib.util
import json
from pathlib import Path
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
NS = 10**9
INTERVAL_PATH = ROOT / 'experiments/t114-two-stage-err/intervals.py'
spec = importlib.util.spec_from_file_location('accepted_directed', INTERVAL_PATH)
iv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(iv)
I = iv.I


def ceil(x):
    return -(-x.numerator // x.denominator)


def sha(path):
    return hashlib.sha256(path.read_bytes().replace(b'\r\n', b'\n')).hexdigest()


def numeric(x):
    if isinstance(x, dict):
        return {k: numeric(v) for k, v in x.items()}
    if isinstance(x, list):
        return [numeric(v) for v in x]
    if isinstance(x, str):
        try:
            return F(x)
        except ValueError:
            pass
    return x


def encoded(x):
    return (json.dumps(x, default=str, sort_keys=True, indent=2) + '\n').encode('utf-8')


def largest_integer(predicate, cap):
    if not predicate(1):
        return None
    lo, hi = 1, cap + 1
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if predicate(mid):
            lo = mid
        else:
            hi = mid
    return lo


def merge_intervals(intervals):
    out = []
    for a, b in sorted(intervals):
        if b <= a:
            continue
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


class Point:
    def __init__(self):
        self.c = json.loads((HERE / 'inputs.json').read_text('utf-8'))
        assert sha(HERE/'inputs.json') == '5f62171e4706854f6419345d7eaed1f2103c06bc4989976fde03942db091c6cd'
        self.sources = {}
        for path, blob in self.c['source_git_blobs'].items():
            raw = (ROOT/path).read_bytes().replace(b'\r\n', b'\n')
            assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == blob, path
            self.sources[path] = hashlib.sha256(raw).hexdigest()
        for path in (HERE/'THEORY.md', HERE/'inputs.json', HERE/'FIRST_POINT_PLAN.md', INTERVAL_PATH):
            self.sources[path.relative_to(ROOT).as_posix()] = sha(path)
        self.W = self.c['first_probe']['words']
        self.T = F(self.c['bank']['mission_s'])
        self.alpha = F(self.c['first_probe']['alpha'])
        self.eps = F(self.c['first_probe']['epsilon'])
        assert (self.W, self.alpha, self.eps) == (1048576, F(1,10), F(1,1000))
        e, s, ch = (self.c[k] for k in ('environment', 'service', 'information'))
        self.b, self.B, self.Fs = (F(e[k]) for k in ('b', 'B', 'Fs'))
        self.D = e['reference_positions']
        self.N = e['template']['count']
        self.width, self.cycle, self.left = (F(e['template'][k]) for k in ('width_s','cycle_s','left_s'))
        self.a0 = 2*self.Fs/(self.N*self.width)
        self.a = (1-self.alpha)*self.a0
        self.R, self.Fr = self.B-self.b-self.a, self.alpha*self.Fs
        self.g = F(e['rho'])*F(e['ell'])-self.a/F(e['template']['rise_s'])
        self.pmax = self.b+self.a
        self.LH = self.N*self.width
        self.LL = self.T-self.LH
        self.IH = self.LH*(self.b**2+self.b*self.a+self.a**2/3)
        self.IL = self.LL*self.b**2
        self.Ip = self.IH+self.IL
        self.box = self.LH*self.pmax**2
        self.K = F(self.W*39*38, 2*self.D**2)
        self.xm, self.xp, self.J = F(s['xi_minus']), F(s['xi_plus']), F(s['J_ns'])/NS
        self.dE = 124*self.xp/NS+3*self.J
        self.XE = 2*self.B*self.dE*(self.b*self.T+self.Fs)
        self.delta0, self.deltacal = F(ch['lifetime_delta_exec']), F(ch['lifetime_delta_calendar'])
        self.delta = self.delta0+self.deltacal
        self.hp, self.hm = self.xp+self.J, self.xm-self.J
        self.delay, self.et = F(ch['command_delay_upper_s']), F(ch['mission_time_error_upper_s'])
        self.freeze = 320*self.xp/NS+self.J
        self.Fparents = F(39*self.W,self.D)*(self.b*self.T+self.Fs)
        self.resource = next(numeric(row) for row in json.loads((HERE/'resource-result.json').read_text('utf-8'))['rows'] if row['words']==self.W)
        self.Nmax = self.resource['calendar']['necessary_class_maximum_reads_upper']
        self.quantum = s['timer_quantum_ticks']
        self.unit = {}
        for name, ticks in (('bus_read',48),('serial_read',68),('repair',56),('bus_init',56),('serial_init',76)):
            self.unit[name] = dict(lower=max(F(0),ticks*self.xm/NS-self.J), upper=ticks*self.xp/NS+self.J)

    def P(self, k, upper=True):
        return 196*k*self.W*(self.xp if upper else self.xm)/NS+(self.J if upper else -self.J)

    @lru_cache(None)
    def hold(self, k, guarded):
        if not guarded:
            return dict(ticks=0, lower_s=F(0), upper_s=F(0))
        ticks = self.quantum*ceil((self.P(k)+self.dE+self.J)/(self.quantum*self.xm/NS))
        lo, hi = ticks*self.xm/NS-self.J, ticks*self.xp/NS+self.J
        assert lo >= self.P(k)+self.dE
        assert (ticks-self.quantum)*self.xm/NS-self.J < self.P(k)+self.dE
        return dict(ticks=ticks, lower_s=lo, upper_s=hi)

    def risk(self, kH, kL, formula):
        PH, PL = self.P(kH), self.P(kL)
        constant = kH == kL
        delta = self.delta0 if constant else self.delta
        if formula in ('F','N0_actual'):
            known = (PL+self.dE)*self.Ip
            residual = (PL+self.dE)*(2*self.pmax+self.R)*self.Fr
            cross = self.XE
        else:
            AH, AL = (PH,PL) if formula=='N0_design' else (PH+self.dE,PL+self.dE)
            known = AH*(self.IH if formula=='M' else self.box)+AL*self.IL
            residual = self.Fr*max(AH*(2*self.pmax+self.R),AL*(2*self.b+self.R))
            cross = F(0) if formula=='N0_design' else self.XE
        terms = dict(exceptions=delta, known=self.K*known, residual=self.K*residual, E_cross=self.K*cross)
        raw = sum(terms.values(), F(0))
        return dict(upper=min(F(1),raw), raw=raw, terms=terms,
                    is_Q_certificate=formula!='N0_design', formula=formula)

    def price(self, kH, kL, U, guarded):
        constant = kH == kL
        delta = self.delta0 if constant else self.delta
        slow = self.W*(self.T/self.P(kL,False)+2)
        low = (1-delta)*self.W*max(F(0),self.T/self.P(kL)-2)
        if constant:
            h = dict(ticks=0,lower_s=F(0),upper_s=F(0))
            C, A, n = F(0),F(0),F(0)
            terms = dict(mandatory_support=slow, bad_execution=self.delta0*self.Nmax)
        else:
            h = self.hold(kH,guarded)
            C = h['upper_s']+self.hp+self.delay+self.freeze+2*self.et
            ch = self.c['information']
            nf = F(ch['false_expected_per_s'])*self.T
            n = self.N+ch['loss_episodes_upper']+nf
            A = min(self.T,self.N*(self.width+2*C)+F(ch['loss_time_upper_s'])+2*C*(ch['loss_episodes_upper']+nf))
            terms = dict(mandatory_support=slow, fast_bands=self.W*(A/self.P(kH,False)+2*n),
                         startup_tail=self.W+2*self.W*(C/self.P(kH,False)+2),bad_execution=self.delta*self.Nmax)
        NR = min(self.Nmax,sum(terms.values(),F(0)))
        ND = min(NR,2*self.Fparents+U*self.Nmax)
        coords = {}
        for coord in ('bus','serial'):
            read, repair = self.unit[coord+'_read'], self.unit['repair']
            check = read['upper']*NR
            rep = repair['upper']*ND
            initlo = self.W*self.unit[coord+'_init']['lower']
            inithi = self.W*self.unit[coord+'_init']['upper']
            appkey = 'pure_bus_mission_' if coord=='bus' else 'serial_mission_'
            app = {end:self.resource['application'][appkey+end]*self.T for end in ('lower','upper')}
            lower = read['lower']*low
            upper = check+rep
            coords[coord] = dict(checks_upper_s=check, repairs_upper_s=rep,
                protection_lower_s=lower, protection_upper_s=upper,
                protection_lower_fraction=lower/self.T,protection_upper_fraction=upper/self.T,
                app_s=app,init_s=dict(lower=initlo,upper=inithi),
                all_known_lower_s=lower+app['lower']+initlo,
                all_known_upper_s=upper+app['upper']+inithi)
        return dict(constant=constant, hold=h, C_s=C, fast_time_expected_upper_s=A,
            fast_bands_expected_upper=n, read_terms_upper=terms, reads_lower=low,reads_upper=NR,
            repairs_lower=0,repairs_upper=ND, repair_terms_upper=dict(parent=2*self.Fparents,after_failure=U*self.Nmax),
            coordinates=coords, control_included=False, control_CPU_energy='parameters',
            count_condition='same selector after memory failure; bounded all-slot fallback on execution exceptions',
            full_started_tail_paid=True, work_after_first_failure_paid=True)

    def candidates(self):
        cap = self.c['comparison']['period_menu']['max_kL']
        kF = largest_integer(lambda k:self.risk(k,k,'F')['upper']<=self.eps,cap)
        pairs, generation = set(), []
        if kF:
            pairs.add((kF,kF))
        for m in self.c['comparison']['period_menu']['ratios']:
            for formula in ('N0_design','Nplus_box','M'):
                k = largest_integer(lambda x:self.risk(x,m*x,formula)['upper']<=self.eps,cap//m)
                generation.append(dict(ratio=m,formula=formula,largest_kH=k))
                if k:
                    pairs.update(((k,m*k),(1,m)))
        rows = []
        for kH,kL in sorted(pairs):
            risks = {f:self.risk(kH,kL,f) for f in ('N0_design','N0_actual','Nplus_box','M','F')}
            constant = kH==kL
            prices = {}
            shared = self.price(kH,kL,risks['F']['upper'],False) if constant else None
            for label,f,guard in (('N0','N0_actual',False),('Nplus_box','Nplus_box',True),('M','M',True)):
                prices[label] = shared if constant else self.price(kH,kL,risks[f]['upper'],guard)
            eligible = {label:(risks['F' if constant else f]['upper']<=self.eps)
                        for label,f in (('N0','N0_design'),('Nplus_box','Nplus_box'),('M','M'))}
            rows.append(dict(pair=[kH,kL],period_high_s=dict(lower=self.P(kH,False),upper=self.P(kH)),
                period_low_s=dict(lower=self.P(kL,False),upper=self.P(kL)),risks=risks,prices=prices,eligible=eligible))
        selected, strict = {}, {}
        for label in ('N0','Nplus_box','M'):
            def key(row):
                c = row['prices'][label]['coordinates']
                return c['serial']['protection_upper_s'],c['bus']['protection_upper_s'],row['pair']
            allowed = [r for r in rows if r['eligible'][label]]
            selected[label] = min(allowed,key=key)['pair'] if allowed else None
            window = [r for r in allowed if r['pair'][0]!=r['pair'][1]]
            strict[label] = min(window,key=key)['pair'] if window else None
        selected['Nplus_refined'] = selected['M']
        return dict(fixed_k=kF,generation=generation,rows=rows,selected=selected,best_strict_window=strict)

    def witnesses(self):
        LR = self.Fr/self.R
        return [dict(name='initial_residual_plateau',length_s=max(F(0),LR-self.P(1)),multiplicity=1,
                     lambda_min=F(39,self.D)*(self.b+self.R),lambda_max=F(39,self.D)*self.B,
                     retained_p=True,initial_prefix_removed_s=self.P(1)),
                dict(name='zero_residual_central_bands',length_s=F(300),multiplicity=self.N,
                     lambda_min=F(39,self.D)*(self.b+self.a/2),lambda_max=F(39,self.D)*self.pmax,
                     retained_p=True,initial_pass_ends_before_band=self.P(1)<1950)]

    def witness_bound(self, witness, M):
        L, lamlo, lamhi = (witness[k] for k in ('length_s','lambda_min','lambda_max'))
        free = max(F(0),L-M*self.dE)
        S = free*free/(M+1)
        Z = I(witness['multiplicity']*self.W*F(38,78)*lamlo**2*S)*I(-lamhi*L).exp()
        q = I(1)-(I(0)-Z).exp()-I(self.delta0)
        return dict(name=witness['name'],apertures_per_word_upper=M,
            exponent_lower=F(Z.lo), exponent_upper=F(Z.hi),
            Q_lower=max(F(0),F(q.lo)),Q_lower_expression_enclosure_upper=max(F(0),F(q.hi)))

    def fixed_lower_at(self, P0):
        bounds = [self.witness_bound(w,w['length_s']/P0+2) for w in self.witnesses()]
        q = max(b['Q_lower'] for b in bounds)
        N = (1-self.delta0)*self.W*max(F(0),self.T/(P0+self.J)-2)
        return dict(P0_s=P0,witnesses=bounds,Q_lower=q,reads_lower=N,
            cost={c:dict(lower_s=N*self.unit[c+'_read']['lower'],
                         lower_fraction=N*self.unit[c+'_read']['lower']/self.T) for c in ('bus','serial')})

    def fixed_threshold(self):
        # Grid is only directed numerical rounding of the threshold, not a policy grid.
        unit = 10**9
        lo,hi = 0,unit
        while self.fixed_lower_at(F(hi,unit))['Q_lower']<=self.eps:
            hi *= 2
            if hi > int(self.T)*unit*2:
                return dict(excluded_from=None,reason='registered lower does not exclude OFF')
        while hi-lo>1:
            mid=(lo+hi)//2
            if self.fixed_lower_at(F(mid,unit))['Q_lower']>self.eps:
                hi=mid
            else:
                lo=mid
        yes = self.fixed_lower_at(F(hi,unit))
        yes['class_excluded_by_resource'] = (yes['cost']['serial']['lower_fraction']>
            self.resource['resource']['available_serial_upper_for_necessary_exclusion'] or yes['reads_lower']>self.Nmax)
        return dict(last_not_excluded=self.fixed_lower_at(F(lo,unit)),excluded_from=yes,
                    optimum_known=False,threshold_resolution_s=F(1,unit))

    def n0_lower(self, kH, kL):
        # Deterministic healthy channel, xi+, jitter=0. Every possible actual visit
        # is contained in the kH support (kL multiple of kH). Startup is removed.
        # This is an aperture superset, not a reset or a Monte Carlo path.
        P = 196*kH*self.W*self.xp/NS
        b = [self.witness_bound(w,(w['length_s']+self.dE)/P+2) for w in self.witnesses()]
        upper = self.risk(kH,kL,'F' if kH==kL else 'N0_actual')['upper']
        lo = max(x['Q_lower'] for x in b)
        return dict(Q_lower=lo,Q_upper=upper,witnesses=b,
            target='supremum over admissible environments/executions; lower witnessed, upper uniform',
            calendar='healthy deterministic xi_plus, zero jitter; actual N0 apertures contained in kH support',
            coarsening='equation14 using all-kH aperture superset; exact Q not claimed',
            status='certified' if upper<=self.eps else ('violates' if lo>self.eps else 'unresolved'))

    def slot_prefix(self, seconds):
        """Number of potential starts q(j)*xi+ < seconds; exact edge convention."""
        if seconds<=0:
            return 0
        ticks=seconds*NS/self.xp
        frames=ticks//1568
        rest=ticks-frames*1568
        return frames*8+min(8,ceil(rest/164))

    def support_prefix(self, seconds, k):
        j=self.slot_prefix(seconds)
        p,r=divmod(j,self.W)
        return self.W*((p+k-1)//k)+(r if p%k==0 else 0)

    def support_interval(self,a,b,k):
        return self.support_prefix(b,k)-self.support_prefix(a,k)

    def healthy_bands(self, kH, guarded, loss=None):
        """One declared admissible deterministic law, not a worst channel realization.

        Poll clock xi+, exact mission-time binding, command delay zero, no jitter.
        Commands change selection at freeze 320 ticks before a start. A supplied
        loss interval is detected at its first poll; fresh restoration at a poll.
        """
        h=self.hold(kH,guarded)
        H=h['upper_s']; actual_hold=h['ticks']*self.xp/NS
        C=H+self.hp+self.delay+self.freeze+2*self.et
        f=320*self.xp/NS
        bands=[]
        for j in range(self.N):
            a=self.left+self.cycle*j; b=a+self.width
            on=max(0,ceil((a-self.hp-self.delay-self.freeze-H-self.et)/self.xp))
            off=(b+H+self.et)//self.xp+1
            bands.append((max(F(0),on*self.xp+f),min(self.T,off*self.xp+f)))
        bands.extend(((F(0),min(self.T,actual_hold+f)),(max(F(0),self.T-C),self.T)))
        if loss is not None:
            a,b=loss
            assert a/self.xp==(a/self.xp)//1 and b/self.xp==(b/self.xp)//1
            bands.append((a+f,min(self.T,b+actual_hold+f)))
        return merge_intervals(bands)

    def exact_reads(self,kH,kL,guarded,loss=None):
        if kH==kL:
            return self.support_prefix(self.T,kL)
        extra=sum(self.support_interval(a,b,kH)-self.support_interval(a,b,kL)
                  for a,b in self.healthy_bands(kH,guarded,loss))
        return self.support_prefix(self.T,kL)+extra

    def guards(self, pair):
        kH,kL=pair
        hold=self.hold(kH,True)
        if kH==kL:
            return dict(pair=pair,constant=True,additional_reads=0,guard_required=False,
                        reason='identical supports: no calendar channel or recovery hold')
        n0=self.exact_reads(kH,kL,False)
        np=self.exact_reads(kH,kL,True)
        assert np>=n0
        # One loss, ten physical poll intervals, away from known windows.
        loss=(100*self.xp,110*self.xp)
        n0loss=self.exact_reads(kH,kL,False,loss)
        nploss=self.exact_reads(kH,kL,True,loss)
        assert nploss>=n0loss
        u0=self.risk(kH,kL,'N0_actual')['upper']
        up=self.risk(kH,kL,'M')['upper']
        c0=self.price(kH,kL,u0,False)
        cp=self.price(kH,kL,up,True)
        extra=np-n0
        ch=self.c['information']
        nf=F(ch['false_expected_per_s'])*self.T
        # Each endpoint expansion is at most H+ plus two poll intervals and
        # two freeze intervals. Count on kH support; no cost-bound subtraction.
        extension=hold['upper_s']+2*self.hp+2*self.freeze
        # Charge both ends of each loss/false component too; this avoids relying
        # on an optimistic one-sided recovery decomposition under overlaps.
        assert self.hp >= self.delay+2*self.et+self.freeze
        edge_count=2*(self.N+ch['loss_episodes_upper']+nf)+2
        additional_upper=min(self.Nmax,edge_count*self.W*(extension/self.P(kH,False)+2)+self.delta*self.Nmax)
        coords={}
        for c in ('bus','serial'):
            read=self.unit[c+'_read']; d=self.unit['repair']['upper']
            # Same deterministic channel and xi+: read difference exact. Repair
            # counts are bounded by lifetime U*Nmax, not monotonically coupled.
            exact_unit=(48 if c=='bus' else 68)*self.xp/NS
            dr=extra*exact_unit
            coords[c]=dict(healthy_extra_read_s=dr,
                healthy_full_difference_lower_s=dr-d*c0['repairs_upper'],
                healthy_full_difference_upper_s=dr+d*cp['repairs_upper'],
                universal_extra_read_upper_s=additional_upper*read['upper'],
                general_full_difference_lower_s=cp['coordinates'][c]['protection_lower_s']-c0['coordinates'][c]['protection_upper_s'],
                general_full_difference_upper_s=cp['coordinates'][c]['protection_upper_s']-c0['coordinates'][c]['protection_lower_s'])
        return dict(pair=pair,hold=hold,healthy_reads_N0=n0,healthy_reads_guarded=np,
            healthy_additional_reads=extra,healthy_additional_full_pass_equivalents=F(extra,self.W),
            one_loss_interval_s=loss,one_loss_N0_reads=n0loss,one_loss_guarded_reads=nploss,
            one_loss_additional_reads=nploss-n0loss,
            additional_recovery_reads_due_to_one_loss=(nploss-np)-(n0loss-n0),
            recovery_complete_high_cycle_cover_lower=hold['lower_s']/(self.P(kH)+self.dE),
            recovery_extra_time_upper_s=hold['upper_s'],price_band_extension_each_side_s=hold['upper_s'],
            terminal_extra_reads=self.support_interval(self.T-cp['C_s'],self.T-c0['C_s'],kH)-self.support_interval(self.T-cp['C_s'],self.T-c0['C_s'],kL),
            expected_additional_reads_upper=additional_upper,endpoint_envelope_s=extension,
            quota_endpoint_count_upper=edge_count,coordinates=coords,
            common_channel_coupling=True,unknown_control_difference='add T*(c_guarded-c_N0); neither coefficient is set to zero',
            exact_counts_are_not_the_channel_quota_realization=True)

    def management(self, price, lowerF, fixedprice):
        P=self.T/self.hm+2
        ch=self.c['information']
        R=min(P+1,1+ch['loss_episodes_upper']+F(ch['false_expected_per_s'])*self.T+self.delta*P)
        counts=dict(check=P,command=P+R+1,timer=P+2*R+2,extra_bundle=P)
        if price['constant']:
            counts={k:F(0) for k in counts} # unnecessary calendar channel actually disabled
        frame=(1568*self.xp/NS+self.J)
        progress=self.resource['resource']['guaranteed_management_progress_ns']/NS
        tau=F(1,1000) # conditional, inherited local-processing budget, NOT measured work
        B=max(0,(self.delay-tau)//frame-20)*progress
        c=price['coordinates']
        gains={}
        for coord in ('bus','serial'):
            # init is common but retained on both sides in the ratio denominator.
            total=c[coord]['all_known_upper_s']
            commonlo=c[coord]['app_s']['lower']+c[coord]['init_s']['lower']
            lf=lowerF['cost'][coord]['lower_s']+commonlo
            gains[coord]=dict(known_lowerF_to_rule_upper_ratio=lf/total,
                additional_rule_budget_for_strict_gain_per_s=(lf-total)/self.T,
                difference_of_sufficient_uppers_per_s=(fixedprice['coordinates'][coord]['all_known_upper_s']-total)/self.T,
                comparison_of_uppers_is_not_guaranteed_gain=True)
        average=self.resource['resource']['sufficient_serial_average_remainder_after_app_upper']-c['serial']['protection_upper_fraction']
        return dict(calendar_action_counts_upper=counts,rates_upper_per_s={k:v/self.T for k,v in counts.items()},
            local_slot_selector_checks_upper=self.Nmax,
            mean_budget='u_x=sum(action_rate*incremental_nonoverlapping_cost_x)+local_selector+enabled_unused_ERR',
            serial_average_resource_remainder=average,
            reserved_slot_guaranteed_progress_fraction=progress/frame,
            peak_including_reserved_management=self.resource['resource']['peak_including_full_reserved_management_slot'],
            burst='ceil((b_check+3*b_command+5*b_timer+b_extra_bundle)/progress)+20 frames, plus local CPU <= .01s; <=10 sequential phases',
            conditional_local_processing_budget_s=tau,conditional_burst_work_upper_s=B,
            window_action_mean_sufficient_for_any_composition=(P/self.T)*B/5,
            window_action_mean_budget_scope='only declared check/command/timer/extra-bundle work, not unbounded per-slot or ERR traffic',
            atomic_upper_s=F(32,NS),frame_upper_s=frame,guaranteed_progress_s=progress,
            gain_conditions=gains,CPU=None,energy=None,controller_state_bytes=None,
            unused_ERR='zero only if actually disabled; otherwise separate unknown rate/burst/cost',
            no_total_hardware_gain_claimed=True)


def calculate():
    p=Point()
    cand=p.candidates()
    lower=p.fixed_threshold()
    assert lower['excluded_from'] is not None
    selected=cand['selected']
    lookup={tuple(r['pair']):r for r in cand['rows']}
    fixedrow=lookup[(cand['fixed_k'],cand['fixed_k'])]
    fixedprice=fixedrow['prices']['M']
    management={}
    for label,pair in selected.items():
        if pair:
            key='M' if label=='Nplus_refined' else label
            management[label]=p.management(lookup[tuple(pair)]['prices'][key],lower['excluded_from'],fixedprice)
    strict_management={}
    for label,pair in cand['best_strict_window'].items():
        if pair:
            strict_management[label]=p.management(lookup[tuple(pair)]['prices'][label],lower['excluded_from'],fixedprice)
    guardpairs={tuple(x) for x in [selected['N0'],selected['M'],cand['best_strict_window']['N0'],cand['best_strict_window']['M']] if x}
    lowerpairs={tuple(x) for x in [selected['N0'],cand['best_strict_window']['N0']] if x}
    return dict(status='ONE_CONDITIONAL_POINT_NOT_SCIENTIFIC_ACCEPTANCE',base_main='8201d41c9c50e34d5a088f91d34c14b4fee88aee',
        plan_commit='8e9bd8827c159a284d0b60120bd523bd2a1d57c6',source_sha256_LF=p.sources,
        implementation_sha256=sha(Path(__file__)),words=p.W,useful_bytes=4*p.W,alpha=p.alpha,epsilon=p.eps,mission_s=p.T,
        environment=dict(b=p.b,B=p.B,a=p.a,R=p.R,Fr=p.Fr,g=p.g,Ip=p.Ip,IH=p.IH,IL=p.IL,box=p.box,K=p.K,XE=p.XE),
        candidates=cand,fixed_class=lower,fixed_next_Q=p.risk(cand['fixed_k']+1,cand['fixed_k']+1,'F'),
        diagnostic=dict(residual_only_sufficient_low_period_upper_s=(p.eps-p.delta-p.K*p.XE)/(p.K*p.Fr*(2*p.b+p.R))-p.dE,
            residual_fraction_of_fixed_physical_Q=fixedrow['risks']['F']['terms']['residual']/(fixedrow['risks']['F']['upper']-p.delta0),
            initial_residual_plateau_s=p.Fr/p.R,
            fixed_Q_slack=p.eps-fixedrow['risks']['F']['upper'],
            fixed_next_nominal_period_s=196*(cand['fixed_k']+1)*p.W/F(NS),
            source_of_dominance='concentrated residual allowed outside windows; this is a certificate/menu result, not impossibility of every schedule'),
        N0_Q_brackets=[dict(pair=list(pair),**p.n0_lower(*pair)) for pair in sorted(lowerpairs)],
        guard_diagnostics=[p.guards(list(pair)) for pair in sorted(guardpairs)],management=management,strict_window_management=strict_management,
        per_operation_seconds=p.unit,resource_reused=p.resource,
        Nplus_refined_equals_M=True,remaining_grid_executed=False,physical_Q=None,
        unknowns=['CPU','energy','controller state/code/buffers','local selector WCET','full 6MiB physical capacity','control coefficients','enabled unused ERR stream'])


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write',action='store_true')
    args=parser.parse_args()
    start=time.perf_counter()
    result=calculate()
    raw=encoded(result)
    dest=HERE/'first-point-result.json'
    if args.write:
        dest.write_bytes(raw)
    else:
        assert dest.read_bytes().replace(b'\r\n',b'\n')==raw,'First point replay differs'
    print(json.dumps(dict(selected=result['candidates']['selected'],candidate_pairs=len(result['candidates']['rows']),
        lowerF_serial=float(result['fixed_class']['excluded_from']['cost']['serial']['lower_fraction']),
        P0=float(result['fixed_class']['excluded_from']['P0_s']),
        elapsed_s=time.perf_counter()-start,result_sha256=hashlib.sha256(raw).hexdigest()),ensure_ascii=False))
