"""Derived adapter pin proposal and conditional datasheet margins.

Not a guessed ECC-word address map, nor a routed physical-top certificate.
The fixed pin facts were read from002-20054 Rev.*F, Figure5 p6.
"""
import argparse,hashlib,json,re
from fractions import Fraction as F
from pathlib import Path
HERE=Path(__file__).resolve().parent
DATASHEET_SHA='a7d9faf23208b6c0f3b2be402feb8653ff0c6f649306fc246605189018a9ed1f'

def calculate():
    board_path=HERE.parent/'outputs/board_components.json'
    board=json.loads(board_path.read_text())
    addresses=[25,24,23,22,21,20,19,18,8,7,6,5,4,3,2,1,48,17,16,9]
    data=[29,31,33,35,38,40,42,44,30,32,34,36,39,41,43,45]
    control={'sram_ce_n':26,'sram_oe_n':28,'sram_we_n':11,
             'sram_lb_n':15,'sram_ub_n':14,'sram_err':13}
    rows=[]
    for original in board['pin_plan']:
        row=dict(original);port=row['port']
        if port.startswith('sram_a['):pin=addresses[int(re.search(r'\[(\d+)\]',port)[1])]
        elif port.startswith('sram_dq['):pin=data[int(re.search(r'\[(\d+)\]',port)[1])]
        else:pin=control[port]
        row['TSOP_pin']=pin;rows.append(row)
    assert len(rows)==len({r['TSOP_pin'] for r in rows})==42
    ties={'VCC':[12,37,47],'VSS':[27,46],'NC':[10]}
    assert {r['TSOP_pin'] for r in rows}|set(sum(ties.values(),[]))==set(range(1,49))
    assert len({r['package_pin'] for r in rows})==42
    gap=lambda a,b:F(a)*F('.99999')-F(b)*F('1.00001')-F('.5')
    margins={'read_capture':gap(60,4)-4-45-2-1,
             'second_read_capture':gap(152,96)-4-45-2-1,
             'SRAM_off_before_FPGA_drive':gap(92,64)-4-18,
             'WE_pulse_over_35ns':gap(132,92)-4-35,
             'data_setup_over_25ns':gap(132,92)-4-25,
             'data_hold_over_0ns':gap(140,132)-4,
             'FPGA_off_before_next_read':gap(168,140)-4}
    assert min(margins.values())>0
    return {
      'status':'pin proposal checked; physical top and pad timing NOT established',
      'sources':{'SRAM':'CY62167GE30-45ZXI,002-20054 Rev.*F,pp6,8-10',
        'datasheet_sha256':DATASHEET_SHA,
        'board_master_xdc_sha256':board['source_sha256'],
        'reused_pin_plan_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest()},
      'pin_plan':rows,'tie_plan':ties,
      'tie_meaning':'CE2/BYTE high, x16 mode; pin45 is DQ15, not A20',
      'source_parameters':{'VCC_range_V':[2.2,3.6],
        'AA_ACE_max_ns':45,'DOE_max_ns':22,'HZOE_max_ns':18,'LZOE_min_ns':5,
        'OHA_min_ns':10,'PWE_min_ns':35,'SD_min_ns':25,'HD_min_ns':0,
        'AC_test_load_pF':30,'AC_input_slew_max_ns':3,
        'input_capacitance_pF_at_25C_1MHz_max':10,
        'power_recovery_stable_or_linear_ramp_min_us_exclusive':100},
      'clock_design':{'ref_MHz':100,'pin':'Y9','MMCM_VCO_MHz':1000,
        'output_divisors':[4,20],'BUFG_output_periods_ns':[4,20],
        'input_jitter_ns_assumed':0.05,'frequency_tolerance_ppm_assumed':10,
        'edge_span_ns_assumed':0.5},
      'assumptions':{'VADJ_V':3.3,'I/O':'LVCMOS33;DQ8mA/SLOW',
        'forward_ns':[0,4],'return_ns':[0,2],'setup_ns':1},
      'conditional_margins_ns':{k:float(v) for k,v in margins.items()},
      'unknown':{'ECC_two_alias_function':None,'actual_board_adapter_revision':None,
        'external_trace_and_connector_min_max_ns':None,'actual_load_pF':None,
        'pad_to_pad_delays_and_hold':None,'clock_envelope_source_validation':None,
        'qualified_clean_start_and_clock_failure_containment':None},
      'limitations':['pin numbers do not establish ECC grouping',
        '30pF datasheet test load is NOT the selected adapter load',
        'registered WE/OE removes RTL decode glitches, not physical pad skew',
        'no pin programming, hardware testing or flight qualification']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args()
    text=json.dumps(calculate(),indent=2)+'\n'
    if a.output:a.output.write_text(text)
    print(text)
