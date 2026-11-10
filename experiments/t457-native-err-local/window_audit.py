"""Second port accounting: intersect actual GRANT..RELEASE pairs with named windows.
Unlike the whole-horizon meter, this reads no internal read/repair duration field.
"""
from decimal import Decimal as D

def load(path):
    ops=[]; apps=[]; starts={}; cuts={}; installs={}; opened=None; end=None
    with path.open() as h:
        for line in h:
            if "$finish called" in line: continue
            f=line.split(); typ=f[0]; tick=int(f[1])
            if typ=="B": starts[int(f[2])]=tick
            elif typ=="G":
                assert opened is None
                opened=(tick,int(f[4]))
            elif typ=="R":
                assert opened is not None and opened[1]==int(f[2]) and tick>opened[0]
                ops.append((opened[0],tick));opened=None
            elif typ=="A": apps.append((tick,tick+10))
            elif typ=="C": cuts[int(f[2])]=tick
            elif typ=="K": installs[int(f[2])]=tick
            elif typ=="END": end=tick
    assert end is not None
    if opened:ops.append((opened[0],end))
    return ops,apps,starts,cuts,installs,end

def interval(data,start,end):
    ops,apps,*_=data
    assert 0<=start<end<=data[-1]
    def work(items): return 10*sum(max(0,min(b,end)-max(a,start)) for a,b in items)
    return dict(start_ns=10*start,end_ns=10*end,wall_ns=10*(end-start),
                scheduled_native_port_ns=work(ops),application_port_ns=work(apps),
                occupied_visits=sum(a<end and start<b for a,b in ops))

def check(work,rows,budget):
    loss=load(work/"loss_and_requalification.trace")
    top=load(work/"all_rungs_long_pause.trace")
    cold=load(work/"last_check_bit.trace")
    _,_,starts,cuts,install,_=loss
    windows={
        "last_ERR_cut_to_install":interval(cold,cold[3][0],cold[4][0]),
        "enter_rare":interval(loss,cuts[1280],install[1280]),
        "fall_back_to_fast":interval(loss,cuts[1282],install[1282]),
        "first_fast_base_interval_after_fallback":interval(loss,starts[1283],starts[1284]),
        "last_invalid_install_through_fresh_promotion":interval(loss,install[1283],install[2816]),
        "rare_256L_slots_outside_active_base_interval":interval(top,top[2][152576]+280,top[2][152832]),
        "rare_256L_last_release_to_next_grant":interval(top,
            max(b for a,b in top[0] if a<top[2][152832]),top[2][152832]),
        "maximum_step_fallback":interval(top,top[3][152832],top[4][152832]),
    }
    for name in ("last_ERR_cut_to_install","enter_rare","fall_back_to_fast","maximum_step_fallback"):
        w=windows[name]
        assert w["wall_ns"]==200 and w["scheduled_native_port_ns"]==0
    f=windows["last_invalid_install_through_fresh_promotion"]
    assert (f["wall_ns"],f["occupied_visits"],f["scheduled_native_port_ns"])==(4292400,12264,1226400)
    assert windows["first_fast_base_interval_after_fallback"]["scheduled_native_port_ns"]==800
    assert windows["last_ERR_cut_to_install"]["application_port_ns"]==20
    pause=windows["rare_256L_last_release_to_next_grant"]
    assert (pause["wall_ns"],pause["scheduled_native_port_ns"],pause["application_port_ns"])==(714540,0,100)
    assert windows["rare_256L_slots_outside_active_base_interval"]["wall_ns"]==714000
    for data,name in ((loss,"loss_and_requalification"),(top,"all_rungs_long_pause"),(cold,"last_check_bit")):
        assert interval(data,0,data[-1])["scheduled_native_port_ns"]==rows[name]["protected_port_ns"]
    left=D("34.016758"); B=D("2850848.789"); n=budget["hard_integer_limit"]
    assert D("7825256.934")/2-D("1061779.678")==B and left*n<=B<left*(n+1)
    assert D(budget["bad_cells_per_day_down"])*D("3652.5")*left<=B
    assert D(budget["uniform_per_cell_probability_sufficient_down"])*budget["max_cell_opportunities"]*left<=B
    assert D(budget["uniform_per_report_probability_sufficient_down"])*budget["max_pass_opportunities"]*left<=B
    return windows
