"""Missing-member ledger; model hypotheses are never inferred from allocation."""
import json
from fractions import Fraction as F
from pathlib import Path
from advance_budget import calculate, encode

HERE=Path(__file__).resolve().parent
PARAMETERS=('core_fetch_ns','ocm_beat_ns','gp_read_ns','gp_write_ns','dmb_ns')


def calculate_service(work, parameters=None):
    old=calculate()
    w=work['service_visit_upper']
    weights=dict(zip(PARAMETERS,[w['instructions'],w['ocm_data_32bit_beats'],
                               w['mmio_reads'],w['mmio_writes'],w['dmb']]))
    # Deliberately loose: old in-flight channel + acceptance/ACK/cut edges.
    # Continuous healthy polling, one owner and qualified startup are required.
    fixed=old['certificate_allocation_ns']+3*old['cut_refresh_edge_ns']
    d_limit=(old['selected_service_allocation_ns']-fixed)/5
    values=parameters or {k:None for k in PARAMETERS}
    missing=[k for k in PARAMETERS if values.get(k) is None]
    if any(F(v)<0 for v in values.values() if v is not None):
        raise ValueError('negative latency')
    visit=None if missing else sum(weights[k]*F(values[k]) for k in PARAMETERS)
    total=None if visit is None else 5*visit+fixed
    return {
        'kind':'conditional response-time composition, not measured or established PS timing',
        'visit_weights':weights,'platform_upper_parameters_ns':values,
        'missing_parameters':missing,'visit_upper_ns':visit,
        'PL_tail_upper_ns':fixed,'round_formula':'5*d + certificate_allocation + 3*slow_edge',
        'd_definition':'one whole driver_step plus main loop, all permitted inputs and admitted PS microstates',
        'visit_limit_for_1ms_ns':d_limit,'full_round_upper_ns':total,
        'within_selected_1ms_if_parameters_valid':None if total is None else total<=1000000,
        'established_on_PS7':False,
        'initial_cut_condition':'qualified startup with CPU already initialized/polling, bounded by 2*d+3*slow_edge',
        'assumptions':['continuous isolated polling, no WFI/interrupts on healthy path',
                       'ordered Device accesses with end-to-end completion bound, no stale status cache',
                       'accepted finite XPM progress, clocks continue, no silent corruption',
                       'finite per-instruction/memory/ordering envelope independent of observed traces'],
    }


if __name__=='__main__':
    work=json.loads((HERE/'outputs/service-work.json').read_text())
    result=encode(calculate_service(work))
    (HERE/'outputs/service-budget.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
