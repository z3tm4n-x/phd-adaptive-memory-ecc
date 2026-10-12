"""Independent rational service/queue arithmetic; does NOT recompute Q(T).

These are conditional cycle-count bounds, not an STA pass or analog CDC WCET.
Vendor transport premises and their outstanding proof status are in REPORT.
No import from T135's calculator or the RTL/trace reference.
"""
from fractions import Fraction as F
import argparse,json,math
from pathlib import Path

def upper(ticks,j=F(1,2)):
    return F(ticks)*F('1.00001')+j

def calculate():
    lo,hi=F('.99999'),F('1.00001')
    frame_min=1568*lo;frame_max=1568*hi
    E=upper(148);R=upper(92);A=upper(216,F(1));read=upper(184,F(1))
    response=F('1.1')*(320+frame_max+F('.5')+A+320+100)
    window=F(10**6);expanded=window+3000
    # Any interval meets at most length/frame+2 frames. Count every CONTROL
    # as E, irrespective of LOW/ERR. Actual atomic intervals cannot overlap.
    control=8*E*(window/frame_min+2)
    other=F(209)+F('.0001')*expanded
    application=A*(1+F(10000)*expanded/F(10**9))
    bus=(control+other+application)/window
    assert response<=3000 and bus<=F('.8')

    # Common-clock digital arrival bounds. ERR is possible only at the first
    # coherent sample of CONTROL/observed-write: source separation >=164xi.
    # Loss input changes at most once per slow edge. T135 prices <=1001 rises,
    # hence <=2002 transitions in the WHOLE mission, not an invented ERR cap.
    loss_total=2002;loss_gap=20*lo;err_gap=164*lo;service=20*hi
    latency=upper(12+10*20)  # staging + generous XPM pointer/FWFT prefix
    # CDC may bunch adjacent source transitions: do not assume a20ns
    # minimum separation at its OUTPUT. Its <=36.5ns digital latency spread
    # is less than two slow periods, hence a conservative loss burst of3.
    # Source ERR edge-time jitter adds .5ns to its counting interval.
    loss_burst=3
    def arrivals(t):return min(loss_total,loss_burst+t/loss_gap)+1+(t+F('.5'))/err_gap
    kink=(loss_total-loss_burst)*loss_gap
    candidates=[F(0),latency,kink]
    backlog=max(arrivals(t)-max(F(0),(t-latency)/service) for t in candidates)
    # Bound a pessimistic full flag with sixteen extra not-yet-visible reads.
    occupancy=math.ceil(backlog)+16
    history=latency+service+max(service*arrivals(t)-t for t in candidates)
    # After the final new history item, next beacon f serves f+2. The first
    # freeze is 2816xi after that beacon. Queueing is already in history.
    # Ongoing ERR/loss already makes FAST applicable on its publication edge.
    loss_to_veto=upper(36)
    fresh=history+loss_to_veto+upper(3*1568-320)+upper(8)
    assert occupancy<512 and fresh<=10000
    candidate=upper(480)
    candidate_with_margin=F('1.1')*candidate
    # Beacon f for f+2 begins 3136xi before target, earlier than1440xi.
    assert candidate_with_margin<=1000
    assert upper(600)<frame_min # complete round trips before next beacon
    assert 16*frame_min>1000 # local tag wrap is NOT generation wrap

    input_path=upper(20+4*20+2*20+6*4+2*4)
    output_path=upper(4+2*4+6*20+4*20+20)
    assert input_path<320 and output_path<320
    max_increments=math.ceil((F(315576000)*10**9+F('.5'))/(4*lo))+1
    assert max_increments<2**57<2**64-1
    return {
        'status':'conditional digital bounds; no physical timing acceptance',
        'operations_ns':{'R':R,'E':E,'read32':read,'observed_write32':A},
        'application':{'joint_burst':1,'joint_rate_s':10000,'inbound_ns':input_path,
          'outbound_ns':output_path,'input_budget_ns':320,'output_budget_ns':320,
          'backpressure_budget_ns':100,'response_with_10pct_ns':response,
          'bus_any_1ms_upper':bus,'bus_control_ns':control,'bus_app_ns':application,'bus_other_ns':other},
        'history':{'loss_transitions_mission_max':loss_total,'ERR_min_spacing_ns':err_gap,
          'loss_output_arrival_burst':loss_burst,'ERR_edge_span_ns':F('.5'),
          'FIFO_depth':512,'backlog_upper':backlog,'full_flag_occupancy_upper':occupancy,
          'prefix_latency_ns':latency,'processed_history_ns':history,
          'last_history_to_fresh_applicable_including_loss_CDC_ns':fresh,
          'ongoing_history':'local FAST immediately; no LOW until processed generation equals source',
          'unresolved':'cycle bound assumes initialized XPM, continuous clocks, specified digital CDC resolution; not a formal proof of analog metastability'},
        'candidates':{'preparation_and_delivery_ns':candidate,'with_10pct_ns':candidate_with_margin,
          'roundtrip_budget_ns':upper(600),'begin_before_target_xi':3136,'freeze_lead_xi':320,
          'dispatch_ns':upper(8),'tag_bits':4,'tag_wrap_min_ns':16*frame_min,
          'lease':'target f+2; no backwards revocation of frozen decisions'},
        'generation':{'bits':64,'runtime_reset':False,'mission_fast_edges_upper':max_increments,
          'saturation_reachable_in_10y':False,'price_recalculated':False},
        'unchanged_theory_inputs':{'T135':'b3bbc5f2171c66ac4b975060111aab704ab3734b',
          'T135_64bit_confirmation':'5147d0d360e7483fb421c9b5d11ff96ac216ef78',
          'R0-A':True,'Q_recomputed':False,'lifetime_price_recomputed':False},
        'limits':['all-history cycle/network-calculus derivation, not a trace maximum',
          'accepted mean quotas for lifetime/quiet components still apply; no new lifetime price here',
          'startup FIFO readiness, source-valid stability and backpressure are interface premises',
          'no out-of-envelope application timing guarantee; conservation still checked']}

def encode(x):
    if isinstance(x,F):return {'rational':str(x),'decimal':float(x)}
    if isinstance(x,dict):return {k:encode(v) for k,v in x.items()}
    if isinstance(x,list):return [encode(v) for v in x]
    return x

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);args=ap.parse_args()
    text=json.dumps(encode(calculate()),indent=2,ensure_ascii=False)+'\n'
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(text)
    print(text)
