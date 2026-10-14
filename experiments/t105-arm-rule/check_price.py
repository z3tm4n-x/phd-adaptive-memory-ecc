"""Independent accounting of actual GRANT/RELEASE/PIN trace intervals.

No cycle model for ARM. Fixed FAST versus stationary eligible LOW, same
nonzero legal offered application, on the *same* executor. Not stage G.
"""
import argparse,bisect,hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
NS=1000 # simulator reports ps
def duration(intervals,a,b):return sum(max(0,min(y,b)-max(x,a)) for x,y in intervals)
def peak(intervals,a,b,width):
    intervals=sorted((max(x,a),min(y,b)) for x,y in intervals if x<b and y>a)
    ends=[y for x,y in intervals];starts=[x for x,y in intervals];sums=[0]
    for x,y in intervals:sums.append(sums[-1]+y-x)
    def primitive(t):
        i=bisect.bisect_right(ends,t);v=sums[i]
        if i<len(intervals):v+=max(0,t-starts[i])
        return v
    candidates={a,b-width}
    for x,y in intervals:
        candidates.update(t for t in (x,y,x-width,y-width) if a<=t<=b-width)
    # Extremum of a piecewise-linear moving integral occurs at an endpoint
    # or a service endpoint (with/without the width shift), not just bins.
    return max((primitive(t+width)-primitive(t))/width for t in candidates)
def check(stress,published=False):
    meta=json.loads((HERE/f'outputs/integration-0-{stress}.json').read_text())
    log=Path(meta['build'])/'vivado.log';grants={};operations=[];offers=[];slots=[];pins=[]
    name=f'price/stress-{stress}.txt'
    if log.exists() and not published:
        assert hashlib.sha256(log.read_bytes()).hexdigest()==meta['check']['log_sha256']
        lines=[]
        for line in log.read_text().splitlines():
            f=line.split()
            if not f:continue
            if f[0] in ('GRANT','RELEASE','OFFER','SLOT') or (f[0]=='PIN' and (int(f[12],16) or int(f[15],16))):
                lines.append(line)
        saved=HERE/'.build'/name;saved.parent.mkdir(parents=True,exist_ok=True)
        saved.write_text('\n'.join(lines)+'\n')
    else:
        with zipfile.ZipFile(HERE/'outputs/check-evidence.zip') as z:data=z.read(name)
        hashes=json.loads((HERE/'outputs/check-evidence.json').read_text())
        assert hashlib.sha256(data).hexdigest()==hashes[name]
        lines=data.decode().splitlines()
    for line in lines:
        f=line.split()
        if not f:continue
        if f[0]=='GRANT':grants[int(f[2])]=(int(f[1]),int(f[3]),int(f[4],16)&3)
        elif f[0]=='RELEASE':
            t,app,kind=grants.pop(int(f[2]));end=int(f[1]);operations.append((t,end,app,kind))
            assert end-t==({0:92,1:184,2:216}[kind])*NS
        elif f[0]=='OFFER':offers.append((int(f[1]),int(f[2]),f[3]))
        elif f[0]=='SLOT':slots.append((int(f[1]),int(f[3],16)))
        elif f[0]=='PIN':
            # sample low/high words and actual write commit, not entire
            # operation counted as a single physical memory access.
            pins.append((int(f[1]),int(f[12],16),int(f[15],16)))
    assert len(offers)==8
    assert all(y[0]-x[0]==500020*NS for x,y in zip(offers,offers[1:]))
    a=slots[0][0]+64*1568*NS;b=a+3000000*NS
    assert slots[-1][0]>b
    # Only complete measurement windows; start/end-clipped service paid.
    all_i=[(x,y) for x,y,_,_ in operations]
    counts={};charged={}
    for name,kind in [('control',0),('read32',1),('write32',2)]:
        iv=[(x,y) for x,y,_,k in operations if k==kind]
        counts[name]={'started':sum(a<=x<b for x,y in iv),
          'complete':sum(a<=x and y<=b for x,y in iv),
          'clipped':sum(x<b and y>a and not(a<=x and y<=b) for x,y in iv)}
        charged[name]=duration(iv,a,b)/NS
    for j,(t,execute) in enumerate(slots):
        expected=slots[0][0]+(j//8*1568+j%8*164)*NS
        assert t==expected
        if a<=t<b:assert execute==(1 if stress==3 else int(j%3==0))
    result={'mode':'constant_FAST' if stress==3 else 'stationary_eligible_LOW',
      'measurement_ns':[a/NS,b/NS],'duration_ns':(b-a)/NS,
      'operation_counts':counts,'busy_ns':charged,
      'mean_bus_fraction':duration(all_i,a,b)/(b-a),
      'max_any_1ms_bus_fraction_in_window':peak(all_i,a,b,1000000*NS),
      'physical_reads':sum(s for t,s,c in pins if a<=t<b),
      'physical_write_commits':sum(c for t,s,c in pins if a<=t<b),
      'offered_requests':len(offers),'application_offer_hash':hashlib.sha256(json.dumps(offers).encode()).hexdigest(),
      'max_observed_response_ns':meta['check']['observed_max_response_ns'],
      'responses':meta['check']['requests'],'source_trace_sha256':meta['check']['log_sha256']}
    assert result['max_any_1ms_bus_fraction_in_window']<.8
    assert result['max_observed_response_ns']<=3000
    return result
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--published',action='store_true');args=parser.parse_args()
    fast,low=check(3,args.published),check(4,args.published)
    assert fast['application_offer_hash']==low['application_offer_hash']
    freed=fast['mean_bus_fraction']-low['mean_bus_fraction']
    result={'kind':'calculated from finite HDL traces, not mission price or CPU WCET',
      'cases':[fast,low],'freed_bus_fraction_same_quiet_trace':freed,
      'analytical_stationary_control_fraction':{'FAST':8*92/1568,'LOW':8*92/(3*1568)},
      'CPU_allocation':{'constant_FAST':'no continuing rule task required',
        'current_firmware':'one exclusively reserved polling core (100% allocation, not measured useful CPU utilization)',
        'CPU_cycles_or_useful_percent':None},
      'production_code_bytes':json.loads((HERE/'outputs/firmware.json').read_text())['linked_code_and_rodata_bytes'],
      'limitations':['same routed production topology, functional WB=4 and staged timers40/80/130',
        'stationary after warmup only: full W524288 startup not timed by the accelerated trace',
        'post-warmup slot/must-execute arithmetic independent of WORD_BITS; full top resources use19',
        'no ERR/loss in this quiet service example; not full R0-A price17.484321%',
        'no ARM runtime in native-C/DPI service trace; CPU/OCM/AXI service remains open',
        'no claim of energy savings or optimal fixed policy; no new Q(T) calculation']}
    (HERE/'outputs/price.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
