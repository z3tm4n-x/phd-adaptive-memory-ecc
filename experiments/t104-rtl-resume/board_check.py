"""Component evidence, candidate pin assignment and conditional timing margins.

No pin delay/load is silently assigned. The actual physical map of an ECC word
is deliberately absent. Sources/logic test/synthesis/board qualification differ.
"""
import argparse
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
XDC_URL = 'https://raw.githubusercontent.com/Digilent/digilent-xdc/master/Zedboard-Master.xdc'
XDC_HASH = '4c3ae9d40dce0cb0ca86fdd381a3ec05e0cc099c6f17f8299e270690b2b58b5c'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def pin_plan(raw):
    if sha(raw) != XDC_HASH:
        raise ValueError('board source identity mismatch')
    pairs = re.findall(r'PACKAGE_PIN (\w+)\s+\[get_ports \{(FMC_LA\d+[^}]+)\}\]', raw.decode())
    pins = {name: pin for pin, name in pairs}
    names = sorted(pins)[:42]
    targets = [f'sram_a[{i}]' for i in range(20)]+[f'sram_dq[{i}]' for i in range(16)]
    targets += ['sram_ce_n', 'sram_oe_n', 'sram_we_n', 'sram_lb_n', 'sram_ub_n', 'sram_err']
    if len(names) != 42 or len(set(pins[n] for n in names)) != 42:
        raise ValueError('FMC source coverage/uniqueness')
    return [dict(port=p, connector_signal=n, package_pin=pins[n],
                 bank=34 if int(re.search(r'LA(\d+)', n)[1]) <= 16 else 35)
            for p, n in zip(targets, names)]


def conditional_margins():
    # Same declared T104 design envelopes, NOT measured pad/trace delays.
    # A conservative difference of bounded edge times; no optimistic min IO.
    gap = lambda end, start: end*0.99999-start*1.00001-0.5
    return {
        'read_capture_slack_ns': gap(60, 4)-4-45-2-1,
        'second_read_capture_slack_ns': gap(152, 96)-4-45-2-1,
        'memory_off_before_fpga_drive_ns': gap(92, 64)-4-18,
        'write_pulse_slack_over_35ns': gap(132, 92)-4-35,
        'write_data_setup_slack_over_25ns': gap(132, 92)-4-25,
        'write_data_hold_slack_over_0ns': gap(140, 132)-4,
        'fpga_off_before_next_read_ns': gap(164+4, 140)-4,
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--master-xdc', type=Path)
    p.add_argument('--vivado')
    p.add_argument('--write', action='store_true')
    args = p.parse_args()
    start = time.monotonic()
    raw = args.master_xdc.read_bytes() if args.master_xdc else urlopen(XDC_URL, timeout=30).read()
    pins = pin_plan(raw)
    out = HERE/'.build'/f'board-components-{time.time_ns()}'
    out.mkdir(parents=True)
    xdc = '# Candidate adapter wiring, NOT observed hardware. VADJ=3.3V required.\n'
    for pin in pins:
        xdc += f'set_property PACKAGE_PIN {pin["package_pin"]} [get_ports {{{pin["port"]}}}]\n'
        xdc += f'set_property IOSTANDARD LVCMOS33 [get_ports {{{pin["port"]}}}]\n'
    (out/'fmc_pins.xdc').write_text(xdc, encoding='utf-8')
    source = (HERE/'board/sram_pads.sv').read_text()
    results = {}
    for name, content in [('actual', source), ('wrong_drive_polarity', source.replace('.T(!drive)', '.T(drive)'))]:
        (out/'pads.sv').write_text(content, encoding='utf-8')
        subprocess.run(['iverilog', '-g2012', '-s', 'tb_pads', '-o', 'test.vvp',
                        str(HERE/'board/tb_pads.sv'), 'pads.sv'], cwd=out, check=True, capture_output=True)
        run = subprocess.run(['vvp', 'test.vvp'], cwd=out, capture_output=True, text=True, timeout=30)
        ok = 'PADS_PASS cases=4096' in run.stdout and run.returncode == 0
        if name == 'actual' and not ok or name != 'actual' and (ok or 'PAD_MISMATCH' not in run.stdout):
            raise AssertionError(run.stdout+run.stderr)
        results[name] = dict(exit_code=run.returncode, stdout=run.stdout.strip())
    synthesis = None
    if args.vivado:
        command = [args.vivado, '-mode', 'batch', '-source', str(HERE/'board/components.tcl'),
                   '-log', str(out/'vivado.log'), '-journal', str(out/'vivado.jou'), '-tclargs', str(out)]
        with (out/'console.log').open('w') as log:
            run = subprocess.run(command, cwd=out, stdout=log, stderr=subprocess.STDOUT, timeout=300)
        text = (out/'console.log').read_text()
        if run.returncode or 'T104_BOARD_COMPONENTS_COMPLETE' not in text:
            raise RuntimeError(f'component elaboration failed: {out}')
        clocks = re.findall(r'^CLOCK (\S+) ([\d.]+) (\S+)$', (out/'clock_properties.rpt').read_text(), re.M)
        generated = {n: float(period) for n, period, flag in clocks if flag == '1'}
        expected = {'feedback': 10.0, 'mem_unbuffered': 4.0, 'cpu_unbuffered': 10.0,
                    'x_unbuffered': 8.0, 'command_unbuffered': 10.0}
        if generated != expected:
            raise ValueError(f'wrong generated clocks: {clocks}')
        properties = (out/'pad_properties.rpt').read_text()
        if 'IOBUF_COUNT 16\n' not in properties:
            raise ValueError('not sixteen real IOBUF primitives')
        actual = re.findall(r'^PAD (\S+) (\S+) (\S+)$', properties, re.M)
        if {(p, pin, std) for p, pin, std in actual} != {(p['port'], p['package_pin'], 'LVCMOS33') for p in pins}:
            raise ValueError('pin assignment changed during synthesis')
        synthesis = dict(command=command, generated_clocks_ns=generated, iobufs=16,
                         part='xc7z020clg484-1', scope='component synthesis, NOT post-route IO timing',
                         report_sha256={f.name: sha(f.read_bytes()) for f in out.glob('*.rpt')})
        if args.write:
            target = HERE/'outputs/board-components'
            target.mkdir(exist_ok=True)
            for f in out.glob('*.rpt'):
                (target/f.name).write_bytes(f.read_bytes())
    result = dict(source_url=XDC_URL, source_sha256=XDC_HASH, source_access_date='2026-10-08',
                  pin_plan_status='engineering proposal for new adapter, not observed wiring',
                  pin_plan=pins, logic_tests=results, component_synthesis=synthesis,
                  conditional_margins=conditional_margins(),
                  assumptions={'xi_ns': [0.99999, 1.00001], 'edge_error_ns': 0.25,
                               'forward_ns': [0, 4], 'return_ns': [0, 2], 'setup_ns': 1,
                               'sram_read_max_ns': 45, 'sram_hz_max_ns': 18,
                               'vadj_V': 3.3, 'dq_drive_mA': 8, 'dq_slew': 'SLOW',
                               'input_jitter_ns': 0.05},
                  unknown={'alias_mapping': None, 'actual_load_pF': None, 'trace_delay_ns': None,
                           'clock_tolerance_ppm_verified': None, 'runtime_clock_failure_containment': None,
                           'hazard_free_control_pad_waveform': None},
                  source_files_sha256={f.relative_to(HERE).as_posix(): sha(f.read_bytes())
                                       for f in [Path(__file__), *sorted((HERE/'board').glob('*.sv')), HERE/'board/components.tcl']},
                  raw_directory=str(out), elapsed_s=round(time.monotonic()-start, 3),
                  physical_timing_qualified=False)
    if args.write:
        if not args.vivado:
            raise ValueError('published evidence requires real primitive synthesis')
        (HERE/'outputs/board_components.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
