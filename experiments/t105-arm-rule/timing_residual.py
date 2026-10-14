"""Allocations and sampled ISA/RTL costs, explicitly NOT a CPU upper bound."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    allocation=json.loads((HERE/'outputs/batch-budget.json').read_text())['round_max_allowed_ns']
    isa=json.loads((HERE/'outputs/isa-rtl.json').read_text());rows=[]
    for case in isa['cases']:
        if case['mutation']!='none':continue
        name=f"{case['variant']}-{case['stall_max_slow_ticks']}-none"
        mmio=json.loads((HERE/'.build/isa'/name/'mmio.json').read_text())
        claims=[r for r in mmio if r[1]==0 and r[2]==4]
        instructions=[b[0]-a[0] for a,b in zip(claims,claims[1:])]
        cuts=case['cut_to_cut_peripheral_ticks'];assert cuts
        upper_observed=max(cuts)*20
        rows.append({'case':name,'nominal_peripheral_tick_ns':20,
          'cut_intervals':len(cuts),'observed_min_cut_ns':min(cuts)*20,
          'observed_max_cut_ns':upper_observed,
          'ARM_instructions_between_claims_min':min(instructions),
          'ARM_instructions_between_claims_max':max(instructions),
          'MMIO_reads':case['MMIO']['reads'],'MMIO_writes':case['MMIO']['writes'],
          'not_yet_paid_ns_at_observed_max':allocation-upper_observed,
          'CPU_instruction_time_charged':False,'GP0_SmartConnect_time_charged':False})
    out={'B_available_ns':allocation,'cases':rows,
      'classification':'full 10us result NOT ESTABLISHED; sampled direct-mailbox test only',
      'required_upper_inputs':[
        'minimum actual ARM clock; PLL/clock tolerance and qualified initial clock state',
        'instruction/data service upper in selected cache/OCM configuration, including cold paths',
        'ordered Device GP0/SmartConnect and DMB completion bound under declared owners/arbitration',
        'bounded polling/software progress, exceptions and fault disposition; no silent restart'],
      'fixed_software_conditions':['one owning bare-metal core; IRQ/FIQ disabled at entry',
        'no second core/DMA/OS competitors admitted; Device/shareable/non-cacheable mailbox',
        'qualified initial OCM/PS/PL state; startup-only state initialization'],
      'not_inferred':['sampled maximum is not WCET','ISA instruction count is not ARM cycles',
        'negative allocation residual does not prove the entire 10us requirement impossible',
        'positive residual does not prove CPU/PS fit; no arbitrary CPI fills the gap']}
    (HERE/'outputs/timing-residual.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
