"""Literal production RTL vs absolute enumeration and accelerated integrals."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import time
from empty_time import integrate, peak, slot

HERE=Path(__file__).resolve().parent
RTL=HERE.parent/'t104-rtl-resume/physical/frame_engine.sv'


def check_log(text, wb):
    words=1<<wb;inv=pow(3,-1,words);hf=hl=0;nf=nl=0
    for j in range(words+1024):
        t=1568*(j//8)+164*(j%8);w=inv*j%words
        lo=int(j<words or j%3==0)
        hf=(((hf<<5)|(hf>>27))^w^t^1)&0xffffffff
        hl=(((hl<<5)|(hl>>27))^w^t^lo)&0xffffffff
        nf+=1;nl+=lo
    pattern=r'EMPTY_CALENDAR WB=(\d+) slots=(\d+) freezes=(\d+) fast=(\d+) low=(\d+) hash_fast=([0-9a-f]+) hash_low=([0-9a-f]+) end_ns=(\d+)'
    match=re.search(pattern,text)
    assert match and 'FATAL' not in text and 'ERROR' not in text
    vals=[int(v,16 if i in (5,6) else 10) for i,v in enumerate(match.groups())]
    assert vals[:2]==[wb,words+1024]
    assert vals[3:]==[nf,nl,hf,hl,t],vals
    for row in re.findall(r'^SLOT (.*)$',text,re.M):
        j,t,w,fast,low=map(int,row.split())
        assert (t,w,fast,low)==(1568*(j//8)+164*(j%8),inv*j%words,1,int(j<words or j%3==0))
    # Include the final nominal clean operation; the RTL trace ends on GO.
    end=slot(words+1023)+92
    for low,expected in ((False,nf),(True,nl)):
        got=integrate(0,end,low,words)
        assert got['started']==got['completed']==expected and got['occupied_ns']==92*expected
        assert got['partial_end']==0
    return {'word_bits':wb,'slots_compared':nf,'freeze_transitions':vals[2],
            'executed_FAST':nf,'executed_LOW':nl,'end_ns':end,
            'hash_fast':f'{hf:08x}','hash_low':f'{hl:08x}',
            'RTL_log_sha256':hashlib.sha256(text.encode()).hexdigest()}


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--execute',action='store_true');args=ap.parse_args()
    out=HERE/'outputs';build=HERE/'.build/empty-calendar';build.mkdir(parents=True,exist_ok=True)
    rows=[]
    for wb in (3,4,19):
        path=out/f'empty-calendar-{wb}.txt'
        if args.execute:
            exe=build/f'calendar-{wb}'
            subprocess.run(['iverilog','-g2012','-s','tb_empty_calendar',f'-Ptb_empty_calendar.WB={wb}',
                            '-o',str(exe),str(RTL),str(HERE/'tb_empty_calendar.sv')],check=True)
            before=time.monotonic()
            with path.open('w') as f:
                subprocess.run(['vvp',str(exe)],stdout=f,stderr=subprocess.STDOUT,check=True,timeout=600)
            print(f'WB={wb} host elapsed {time.monotonic()-before:.3f}s',flush=True)
        rows.append(check_log(path.read_text(),wb))
    # No new scenario result: these are empty steady-calendar prices only.
    result={'scope':'component; full-W RTL clocked literally; not integrated mission',
        'rows':rows,'steady_clean_peak_1ms':{
            mode:peak(1000000000,2000000000,low=low) for mode,low in [('FAST',False),('LOW',True)]},
        'source_sha256':{str(p.relative_to(HERE.parents[1])):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (RTL,HERE/'tb_empty_calendar.sv',HERE/'empty_time.py',HERE/'verify_empty_calendar.py')},
        'physical_ARM_time_ns':None,'new_STA':False}
    (out/'empty-calendar.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result['rows'],indent=2))


if __name__=='__main__':main()
