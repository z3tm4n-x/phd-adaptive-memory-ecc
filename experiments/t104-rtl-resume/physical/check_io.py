"""Independent external SRAM phase composition from routed path reports.

No import of the RTL waveform generator. Declared times are checked against
the independently proved E contract. Diagnostic every-edge I/O slacks are
NOT acceptance results: only their propagation/clock/setup/hold arcs enter.
All arithmetic uses exact decimal rationals. Cross-corner global extrema
are deliberately pessimistic; no clock-pessimism credit is taken here.
"""
import argparse,hashlib,json,re
from fractions import Fraction as F
from pathlib import Path
from bounds import encode

def paths(text,direction):
    out=[]
    for block in re.split(r'(?m)^Slack',text)[1:]:
        def number(pattern):
            m=re.search(pattern,block);assert m,pattern
            return F(m[1])
        source=re.search(r'Source:\s+(\S+)',block)[1]
        dest=re.search(r'Destination:\s+(\S+)',block)[1]
        delay=number(r'Data Path Delay:\s+(-?[\d.]+)ns')
        clock=number((r'Destination Clock Delay \(DCD\):\s+' if direction=='input' else
                      r'Source Clock Delay\s+\(SCD\):\s+')+r'(-?[\d.]+)ns')
        arcs=re.findall(r'\((Setup|Hold)_\w+\)\s+(-?[\d.]+)',block)
        out.append({'source':source,'destination':dest,'delay':delay,'clock':clock,
          'setup':max([F(0)]+[-F(x) for k,x in arcs if k=='Setup']),
          'hold':max([F(0)]+[F(x) for k,x in arcs if k=='Hold']),
          'uncertainty':number(r'Clock Uncertainty:\s+([\d.]+)ns')})
    assert out
    return out

def evaluate(folder,read_max=F(45)):
    ins=[];outs=[];hashes={}
    for corner in ['Slow','Fast']:
        for kind in ['min','max']:
            for direction,dest in [('input',ins),('output',outs)]:
                f=folder/f'clocked_{direction}_{corner}_{kind}.rpt'
                data=f.read_bytes();hashes[f.name]=hashlib.sha256(data).hexdigest()
                dest.extend(paths(data.decode(),direction))
    assert {x['source'] for x in ins}=={'sram_err'}|{f'sram_dq[{i}]' for i in range(16)}
    expected={f'sram_a[{i}]' for i in range(20)}|{f'sram_dq[{i}]' for i in range(16)}|{
      'sram_ce_n','sram_oe_n','sram_we_n','sram_lb_n','sram_ub_n'}
    assert {x['destination'] for x in outs}==expected
    imin,imax=min(x['delay'] for x in ins),max(x['delay'] for x in ins)
    omin,omax=min(x['delay'] for x in outs),max(x['delay'] for x in outs)
    cmin,cmax=min(x['clock'] for x in ins+outs),max(x['clock'] for x in ins+outs)
    cs=cmax-cmin
    routed_setup=max(x['setup'] for x in ins);routed_hold=max(x['hold'] for x in ins)
    # DS187 v1.21 table56, -1C: ILOGIC D setup/hold .01/.33ns.
    # Keep the larger published requirement even where the configured
    # routed speed-file arc is tighter. Tables52/53/57 are cross-checks,
    # not extra serial delays to add on top of the complete routed path.
    setup=max(routed_setup,F('.01'));hold=max(routed_hold,F('.33'))
    # Includes .5ns setup uncertainty plus tool-derived jitter. The .5ns
    # physical waveform span is not added again on top of this larger value.
    jitter=max(x['uncertainty'] for x in ins+outs)
    assert jitter>=F('.5')
    # Report values are printed to .001ns. Outward allowances exceed half
    # an ulp, so exact rational arithmetic does not overstate print precision.
    rounding=F('.001')
    imin-=rounding;imax+=rounding;omin-=rounding;omax+=rounding
    cmin-=rounding;cmax+=rounding;cs=cmax-cmin
    setup+=rounding;hold+=rounding;jitter+=rounding
    lo,hi=F('.99999'),F('1.00001');flight_min,flight_max=F('.1'),F('.5')
    pin_spread=cs+(omax-omin)+(flight_max-flight_min)+jitter
    def pin_interval(n):return n*lo-pin_spread
    rows=[]
    def minimum(name,available,required):
        rows.append({'check':name,'available_lower_ns':available,'required_min_ns':required,
                     'margin_ns':available-required,'met':available>=required})
    # Both reads: CE4->sample60, CE96->sample152. ERR shares the45ns bound.
    read_available=56*lo-cs-omax-2*flight_max-imax-setup-jitter
    minimum('CE_to_data_and_ERR_capture_both_reads',read_available,read_max)
    minimum('address_to_capture_first_and_second',read_available+4*lo,read_max)
    minimum('OE_to_capture',read_available,F(22))
    minimum('byte_enable_to_capture',read_available,F(45))
    # No minimum high-Z delay is invented. Data may become invalid as soon
    # as the earliest OE/CE-off reaches SRAM; clock-to-off and both flights
    # plus FPGA input delay still preserve the capture hold interval.
    input_hold=4*lo-cs+omin+2*flight_min+imin-jitter
    minimum('capture_hold_before_OE_or_CE_off',input_hold,hold)
    minimum('WE_pulse_92_to132_and160_to200',pin_interval(40),F(35))
    minimum('write_CE_second_152_to200',pin_interval(48),F(35))
    minimum('write_address_second_148_to200',pin_interval(52),F(35))
    minimum('write_byte_enable_second_148_to200',pin_interval(52),F(35))
    minimum('write_address_to_start_second_148_to160',pin_interval(12),F(0))
    minimum('write_data_setup_first_92_to132',pin_interval(40),F(25))
    minimum('write_data_setup_second_152_to200',pin_interval(48),F(25))
    minimum('write_data_hold_commit_to_drive_off',pin_interval(8),F(0))
    minimum('write_address_and_mask_hold',pin_interval(16),F(0))
    minimum('write_cycle_92_to160',pin_interval(68),F(45))
    minimum('read_cycle_4_to96',pin_interval(92),F(45))
    minimum('read_to_FPGA_drive_64_to92',pin_interval(28),F(18))
    minimum('FPGA_release_to_next_read_140_to168',pin_interval(28),F(0))
    # Completion occurs at the LATEST possible terminating CE/WE edge,
    # never at the earliest one used for data setup. Still inside148/216.
    for end,bound,name in [(132,F('148.501480'),'repair_complete_before_E_release'),
                            (200,F('217.002160'),'write32_complete_before_app_release')]:
        latest=end*hi+F('.5')+cs+omax+flight_max
        minimum(name,bound-latest,F(0))
    return {'scope':'conditional full external phase budget, not manufactured adapter qualification',
      'source_reports':hashes,'datasheet_crosscheck_ns':{
      'source':'AMD DS187 v1.21 (2020-12-01), HR -1C LVCMOS33_F8, tables52/53/56/57',
      'TIOPI':F('1.41'),'TIOOP':F('3.12'),'TIOTP':F('3.13'),'TIOTPHZ':F('2.37'),
      'TOCKQ':F('.56'),'ILOGIC_D_setup':F('.01'),'ILOGIC_D_hold':F('.33'),
      'routed_input_setup_before_rounding':routed_setup,'routed_input_hold_before_rounding':routed_hold,
      'note':'datasheet output values use reference load; actual15pF paths are taken from routed speed model; no double addition; published minima not supplied'},
      'extrema_ns':{'input_min':imin,'input_max':imax,'output_min':omin,
      'output_max':omax,'clock_min':cmin,'clock_max':cmax,'clock_spread':cs,
      'input_setup':setup,'input_hold':hold,'jitter_and_uncertainty':jitter,'pin_interval_penalty':pin_spread,
      'outward_rounding_per_reported_quantity':rounding},
      'conditions':{'flight_ns':[flight_min,flight_max],'load_pf_each_direction':15,
        'SRAM_transition_ns_max':3,'nominal_ref_MHz':100,'xi_ns':[lo,hi],
        'PVT':'Vivado -1 all Slow/Fast min/max; SRAM45ns industrial table at VCC2.2..3.6V',
        'pulse_protocol':'OE HIGH during all writes; not the datasheet OE-LOW write example',
        'assumptions':'qualified clock span; adapter SI/fronts; lighter-load monotonic upper bound; clean qualified start'},
      'checks':rows,'all_met':all(x['met'] for x in rows)}

def main():
    p=argparse.ArgumentParser();p.add_argument('reports',type=Path);p.add_argument('--output',type=Path);a=p.parse_args()
    r=evaluate(a.reports)
    assert not evaluate(a.reports,F(80))['all_met'],'late-memory sentinel must fail'
    r['late_memory_sentinel_rejected']=True
    s=json.dumps(encode(r),indent=2)+'\n'
    if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(s)
    print(s)
    assert r['all_met'],'external timing obligation failed'
if __name__=='__main__':main()
