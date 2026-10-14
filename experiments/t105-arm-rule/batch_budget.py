"""Conditional new transport ledger. Unknown CPU/PS bounds stay unknown."""
import json
from fractions import Fraction as F
from pathlib import Path
HERE=Path(__file__).resolve().parent
def calculate():
    u=lambda n:F(n)*F('1.00001')+F('.5')
    # Accepted source and FIFO are byte-identical, continuously drained.
    history=F('531869457677237/102498975000')
    external=u(80)
    # Conservatively include one previous XPM transaction, full recycling,
    # then the new certificate. 4 slow+8 fast edges covers preparation and
    # capture/check; 320ns is accepted post-consumption XPM watchdog premise.
    delivery=2*u(4*20+8*4)+u(320)
    candidate_allocation=u(600)
    assert delivery<candidate_allocation
    # Calendar maximum consecutive CONTROL separation is420ns; add its
    # fixed freeze lead320 and dispatch8. No free terminal cleanup.
    calendar=u(420+320+8)
    fixed=external+history+candidate_allocation+calendar
    round_limit=(10000-fixed)/2
    # A record just after cut may wait the current round AND next round.
    # Round includes claim/read/CPU/write/CRC/link backpressure/ACK/polling.
    crc=u(7*20)
    return {'status':'conditional allocation, NOT established ARM upper time',
      'external_loss_ns':float(external),'unchanged_history_ns':float(history),
      'derived_digital_certificate_ns':float(delivery),
      'certificate_allocation_ns':float(candidate_allocation),
      'certificate_with_10pct_ns':float(F('1.1')*candidate_allocation),
      'calendar_after_permit_ns':float(calendar),'fixed_sum_ns':float(fixed),
      'round_max_allowed_ns':float(round_limit),'round_max_allowed_rational':str(round_limit),
      'reaction_equation':'external + accepted_history + 2*B + certificate + calendar <= 10000 ns',
      'B_definition':'maximum full cut-to-cut service round; includes polling, all MMIO, program, CRC and ACK',
      'CRC_words':7,'CRC_processing_ns':float(crc),'history_bytes':96,'reply_bytes':32,
      'CPU_round_upper_ns':None,'PS_AXI_upper_ns':None,'B_established_upper_ns':None,
      'reaction_established_upper_ns':None,'CPU_load':None,'whole_system_price_claim':False,
      'assumptions':['accepted initialized digital XPM progress, continuous250/50 clocks',
        'new guard ready within3fast edges; at most one older XPM transaction',
        'every event prefix is retained; invalid packets are faults, not priced recovery',
        'not_before is a policy hold, not an unpriced service wait',
        'the first post-eligibility freeze/operation is charged; already frozen slots unchanged'],
      'open':['finite CPU/OCM/MMIO/barrier bound and BSP','full round including previous-round phase',
              'qualification of complete program-to-fast liveness, not only sampled traces']}
def main():
    data=calculate();(HERE/'outputs/batch-budget.json').write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data,indent=2))
if __name__=='__main__':main()
