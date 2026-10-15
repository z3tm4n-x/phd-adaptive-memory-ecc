"""Portable independent replay of the empty-transition evidence (stdlib).

Recomputes calendar sums and raw rule deadlines. Does not execute C/ARM/RTL
or claim that archived executions occurred again. Those use --execute-empty.
"""
import hashlib
import json
from pathlib import Path
import struct
import sys
import zlib

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
sys.path.insert(0,str(HERE.parent/'t105-arm-rule'))
from batch_model import collect
from verify_empty_calendar import check_log
from verify_empty_rule import cases,STEP
from empty_time import peak


def check():
    out=HERE/'outputs'
    rule=json.loads((out/'empty-rule.json').read_text())
    assert rule['literal_prefixes_checked_against_raw_oracle']==rule['literal_packets']
    assert rule['compressed_endpoint_comparisons']==len(rule['cases'])
    calendar=json.loads((out/'empty-calendar.json').read_text())
    for report in (rule,calendar):
        for p,digest in report['source_sha256'].items():
            assert hashlib.sha256((REPO/p).read_bytes()).hexdigest()==digest,('source drift',p)
    for row in calendar['rows']:
        assert check_log((out/f"empty-calendar-{row['word_bits']}.txt").read_text(),row['word_bits'])==row
    for mode,low in [('FAST',False),('LOW',True)]:
        assert peak(1000000000,2000000000,low=low)==calendar['steady_clean_peak_1ms'][mode]
    vectors=json.loads((out/'empty-rule-vectors.json').read_text())
    assert hashlib.sha256(json.dumps(vectors,sort_keys=True).encode()).hexdigest()==rule['vector_sha256']
    model={name:(groups,n) for name,groups,n in cases()}
    for row in rule['cases']:
        groups,n=model[row['case']];end=groups[-1][0]+n*STEP
        expected=collect(0,groups+[(end,[])])[-1][1]
        assert tuple(row['last_rule'])==expected
        macro=row['macro'];assert (macro['packets'],macro['step_slow_ticks'])==(n,STEP)
        assert macro['represented_elapsed_ns']==n*STEP*20
        raw=bytes.fromhex(macro['after'])
        assert struct.unpack('<6Q2I2Q',raw)==(*expected,n+1,0)
    for v in vectors:
        name,k=v['label'].split('/');groups,n=model[name]
        if k=='seed':
            expected=collect(0,groups)[-1][1];sequence=1
        else:
            expected=collect(0,groups+[(groups[-1][0]+int(k)*STEP,[])])[-1][1];sequence=1+int(k)
        assert struct.unpack('<6Q2I2Q',bytes.fromhex(v['after']))==(*expected,sequence,0),v['label']
        packet=struct.unpack('<10Q4I',bytes.fromhex(v['packet']))
        assert packet[0]==sequence and packet[3]==expected[0]
        now,g,last,short,long,rec,flags,_=expected
        allow=(flags&3)==3 and not flags&8
        decision=(sequence,g,now+max(short,long,rec,int(bool(flags&16))) if allow else 0,int(allow))
        assert struct.unpack('<QQQII',bytes.fromhex(v['decision']))==(
            *decision,zlib.crc32(struct.pack('<QQQI',*decision))),v['label']
    assert len(vectors)==rule['ELF']['vectors']
    print('Empty-time replay:',sum(r['slots_compared'] for r in calendar['rows']),
          'archived RTL slots,',rule['literal_packets'],'represented C packets,',len(vectors),'ELF vectors; no fresh hardware/ISA execution')


if __name__=='__main__':check()
