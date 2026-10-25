"""Exact PR260 slice. No period optimization and no probabilistic integral."""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
ACCEPTED=ROOT/'experiments/comparison-foundations-20261018/predictable-windows-20261025'
NS=10**9


def numeric(x):
    if isinstance(x,dict):return {k:numeric(v) for k,v in x.items()}
    if isinstance(x,list):return [numeric(v) for v in x]
    if isinstance(x,str):
        try:return F(x)
        except ValueError:pass
    return x


def encoded(x):return (json.dumps(x,sort_keys=True,indent=2,default=str)+'\n').encode('utf-8')
def ceil(x):return -(-x.numerator//x.denominator)


def load():
    manifest=json.loads((HERE/'frozen-inputs.json').read_text('utf-8'))
    for path,digest in manifest['sha256'].items():
        data=(ROOT/path).read_bytes().replace(b'\r\n',b'\n')
        assert hashlib.sha256(data).hexdigest()==digest,path
    cfg=json.loads((ROOT/'experiments/t186-method-comparison/code-strength/common-input.json').read_text('utf-8'))
    accepted=numeric(json.loads((ACCEPTED/'result.json').read_text('utf-8')))
    return cfg,accepted,manifest


class Slice:
    def __init__(self):
        self.cfg,self.accepted,self.manifest=load()
        self.m=self.accepted['model']; self.a=self.accepted['adaptive']
        self.W=self.m['words'];self.T=self.m['T_s'];self.eps=self.m['epsilon']
        self.xm=F(self.cfg['service']['clock_lower']);self.xp=F(self.cfg['service']['clock_upper'])
        self.J=F(self.cfg['service']['operation_endpoint_span_ns'])/NS
        self.kH,self.kL=20,1780
        assert (self.a['kH'],self.a['kL'])==(self.kH,self.kL)
        self.Pplus=lambda k:F(k*self.W*196)*self.xp/NS+self.J
        self.Pminus=lambda k:F(k*self.W*196)*self.xm/NS-self.J
        self.E=F(124)*self.xp/NS+self.J
        self.aperture=self.E+2*self.J
        self.C=self.m['price_padding_s']; self.H=self.m['complete_fast_cover_s']
        self.hplus=self.m['poll_step_upper_s'];self.hminus=self.m['poll_step_lower_s']
        self.delay=self.m['command_delay_s'];self.et=self.m['time_error_s']
        self.freeze=320*self.xp/NS+self.J
        quantum=self.cfg['adaptive']['timer_quantum_ticks']
        self.hold_count=ceil((self.H+self.J)/(quantum*self.xm/NS))+1
        self.hold_nominal=F(self.hold_count*quantum,NS)
        self.hold_lower=F((self.hold_count-1)*quantum,NS)*self.xm-self.J
        self.hold_upper=self.hold_nominal*self.xp+self.J
        assert self.hold_lower>=self.H and self.hold_count<2**34
        assert self.hplus+2*self.delay+self.hold_upper+self.freeze<=2*self.C
        assert 2*self.delay+self.hold_upper+self.freeze<=self.C
        self.rb=48*self.xp/NS+self.J; self.cb=56*self.xp/NS+self.J
        self.delta=F(self.cfg['lifetime_other_budget'])+F(1,10**6)
        self.U=self.a['Q_upper'];self.hard=self.a['original_hard_cap']
        self.common=self.accepted['common_cost']
        self.L=self.accepted['fixed']['pure_bus_class_lower']+self.common['ECC_and_initial_bus_lower']
        self.Ccommon=self.common['ECC_and_initial_bus_upper']
        self.slope=self.rb*2*self.m['windows']*self.W/self.Pminus(20)/self.T
        self.bus0=self.a['pure_bus_upper']-30*self.slope
        assert self.Pplus(20)+self.aperture<=self.H
        assert 600+2*1200+2*self.C<5400
        assert 1800-1200-self.C>0
        assert 2400+5400*(self.m['windows']-1)+1200+self.C<self.T

    def upper(self,eta,loss=True):
        eta=F(eta);assert 0<=eta<=1200
        nw=self.m['windows']; A=nw*(600+2*eta+2*self.C); n=F(nw)
        if loss:
            A+=self.m['loss_time_upper_s']+2*self.C*(self.m['loss_episodes_upper']+self.m['false_count_expected_upper'])
            n+=self.m['loss_episodes_upper']+self.m['false_count_expected_upper']
        SH=lambda length:self.W*(length/self.Pminus(20)+2)
        terms=dict(slow=self.W*(self.T/self.Pminus(1780)+2),
            fast_bands=self.W*(A/self.Pminus(20)+2*n),
            startup_tail=self.W+2*SH(self.C),bad_execution=self.delta*self.hard)
        N=min(self.hard,sum(terms.values(),F(0)))
        NC=min(N,2*self.a['parent_count_upper']+self.U*self.hard)
        bus=(self.rb*N+self.cb*NC)/self.T
        core=((68*self.xp/NS+self.J)*N+self.cb*NC)/self.T
        return dict(eta_s=eta,Q_upper=self.U,Q_slack=self.eps-self.U,
            relative_Q_slack=(self.eps-self.U)/self.eps,
            read_terms=terms,reads_upper=N,repairs_upper=NC,pure_bus_upper=bus,
            serial_core_upper=core,includes_common_ECC_upper=bus+self.Ccommon,
            gain_lower_at_zero_management=self.L/(bus+self.Ccommon),
            u_limits={str(g):self.L/g-bus-self.Ccommon for g in (1,2,4,5)},
            sufficient_Q=self.U<=self.eps,physical_Q=None)

    def fixed_witness(self):
        N=self.W*(self.T/self.Pminus(22)+2)
        U=self.accepted['fixed']['sufficient_Q_upper_conservative']
        NC=min(N,2*self.a['parent_count_upper']+U*N)
        bus=(self.rb*N+self.cb*NC)/self.T
        return dict(k=22,Q_upper=U,reads_upper=N,repairs_upper=NC,
            checks_repairs_bus_upper=bus,with_common_ECC_upper=bus+self.Ccommon,
            fixed_management_bus_upper=None,
            whole_constant_class_lower_with_common_ECC=self.L,
            exact_optimum=None)

    def geometry(self):
        # Original app window is retained even though useful writes are absent.
        Em=164*self.xm/NS-self.J
        app=144*self.xp/NS+self.J
        slot=64*self.xm/NS-self.J
        gap_left=160*self.xm/NS-self.J-app # 1472-1312
        gap_right=96*self.xm/NS-self.J-64*self.xp/NS-self.J # next frame - 1472
        L=F(self.cfg['constraints']['peak_window_ns'],NS)
        frames=2+ceil((L+app+self.J)/(1568*self.xm/NS))
        app_each=1+ceil((L+F(3000,NS))/F(self.cfg['application']['epoch_ns'],NS))
        oldpeak=(8*frames*self.E+app_each*((68*self.xp/NS+self.J)+app))/L
        management_peak=frames*(64*self.xp/NS+self.J)/L
        response=F(820,NS)+1568*self.xp/NS+self.J+app
        return dict(control_E_upper_s=self.E,control_slot_lower_s=Em,
            control_slack_s=Em-self.E,app_worst_service_upper_s=app,
            app_deadline_s=F(3000,NS),app_response_upper_s=response,
            management_slot_nominal_ticks=[1472,1536],management_chunk_budget_s=slot,
            recovery_timer_count=self.hold_count,recovery_hold_lower_s=self.hold_lower,
            recovery_hold_upper_s=self.hold_upper,recovery_hold_nominal_s=self.hold_nominal,
            management_atomic_limit_s=F(32,NS),
            guaranteed_management_progress_s=slot-F(32,NS),
            gap_after_app_s=gap_left,gap_before_next_control_s=gap_right,
            frame_upper_s=1568*self.xp/NS+self.J,
            peak_window_s=L,frames_intersecting_peak_window=frames,
            prior_core_peak=oldpeak,management_peak=management_peak,
            total_peak_upper=oldpeak+management_peak,
            mandatory_peak_cap=F(4,5),target_peak_cap=F(64,100),
            measured_WCET=False)

    def management(self):
        P=self.T/self.hminus+2
        # One active recovery timer; faulty decisions cannot spawn an unbounded queue.
        R=min(P+1,1+self.m['loss_episodes_upper']+self.m['false_count_expected_upper']+self.delta*P)
        counts=dict(check=P,command=P+R+1,timer=P+2*R+2,extra_bundle=P)
        rates={k:v/self.T for k,v in counts.items()}
        geom=self.geometry(); quantum=geom['guaranteed_management_progress_s']; frame=geom['frame_upper_s']
        # Coarse, composition-independent service envelope with a stated 1 ms local-processing budget.
        cpu_budget=F(1,1000)
        # Up to ten sequential bus phases in a special (startup/tail) collision.
        # Each can lose a frame waiting for readiness and one chunk to rounding.
        phase_overhead=20
        maxchunks=(self.delay-cpu_budget)//frame-phase_overhead
        burst_budget=maxchunks*quantum
        any_composition=rates['check']*burst_budget/5
        examples=[]
        for name,eta,coeff in [('A',30,dict(check=8,command=4,timer=2,extra_bundle=2)),
                           ('B',120,dict(check=10,command=20,timer=10,extra_bundle=20))]:
            b={k:F(x,10**6) for k,x in coeff.items()}
            u=sum(rates[k]*b[k] for k in b)
            burst=b['check']+3*b['command']+5*b['timer']+b['extra_bundle']
            latency=(ceil(burst/quantum)+phase_overhead)*frame
            examples.append(dict(id=name,shown_eta_s=eta,assumed_bus_WCET_s=b,mean_bus_upper=u,
                maximum_bundle_bus_s=burst,bus_response_upper_s=latency,
                available_local_processing_s=self.delay-latency,
                fivefold_eta_upper_s=(self.L/5-self.bus0-self.Ccommon-u)/self.slope,
                hardware_measurement=False))
        return dict(expected_count_upper=counts,rates_upper_per_s=rates,
            recovery_expiries_upper=R,
            count_scope='whole horizon; structural one-poll/one-timer contract; exceptional executions charged in recovery count',
            joint_mean='u >= sum(rate_a * b_a); same budget, not one budget per action',
            joint_burst='B = b_check + 3*b_command + 5*b_timer + b_extra_bundle',
            maximum_sequential_bus_phases=10,
            joint_deadline='(ceil(B/guaranteed_progress)+20)*frame_upper + local_processing_upper <= 0.01 s',
            local_processing_budget_for_map_s=cpu_budget,
            composition_independent_u_upper=any_composition,
            composition_independent_burst_upper_s=burst_budget,examples=examples,
            local_selector_evaluations_upper=self.hard,
            local_selector_uses_shared_bus=False,
            local_selector_contract='local counter/latches only at freeze; CPU/logic/energy are not zero or measured',
            hypothetical_bus_per_slot=dict(
                rate_lower=self.W*(self.T/self.Pplus(1)-2)/self.T,
                one_16bit_beat_bus_lower=self.W*(self.T/self.Pplus(1)-2)/self.T*(16*self.xm/NS-self.J),
                fivefold_per_slot_bus_budget_s=self.upper(30)['u_limits']['5']/(self.hard/self.T)),
            unknown_CPU=None,unknown_energy=None,unknown_channel_memory=None,
            extra_scope='one bounded splittable aggregate per poll; other arrivals require their own burst/rate contract')
