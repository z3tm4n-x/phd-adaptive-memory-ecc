"""Supervise the two frozen full runs; no commits, push or acceptance."""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

HERE=Path(__file__).resolve().parent


def main():
    folder=HERE/'.build/full-profile';folder.mkdir(exist_ok=True)
    state=dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        supervisor_pid=os.getpid(),horizon_s=363900,events=5237,status='running',modes={})
    lock=threading.Lock()
    def save():
        temp=folder/'state.tmp';temp.write_text(json.dumps(state,indent=2)+'\n')
        temp.replace(folder/'state.json')
    save()
    def job(mode,delay):
        # Fixed never calls its loaded empty-rule C library after initial load.
        # Stagger compilation so both linkers do not create production.so together.
        time.sleep(delay)
        cmd=[sys.executable,str(HERE/'verify_burst.py'),'--execute','--record','--mode',mode]
        with (folder/f'{mode}.log').open('w') as log:
            child=subprocess.Popen(cmd,stdout=log,stderr=subprocess.STDOUT)
            with lock:state['modes'][mode]=dict(pid=child.pid,status='running');save()
            code=child.wait()
        with lock:
            state['modes'][mode].update(status='verified' if code==0 else 'failed',exit_code=code)
            save()
        return code
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fixed=pool.submit(job,'fixed',0)
        adaptive=pool.submit(job,'adaptive',30)
        codes=[fixed.result(),adaptive.result()]
    state['status']='verified_both' if codes==[0,0] else 'failed'
    state['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    print(json.dumps(state,indent=2),flush=True)
    if any(codes):raise SystemExit(1)


if __name__=='__main__':main()
