"""Frozen full scenario2 v2; stop the peer if one execution/check fails."""
import concurrent.futures
import datetime
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

HERE = Path(__file__).resolve().parent


def main():
    folder = HERE/'.build/full-profile-v2'
    folder.mkdir(exist_ok=True)
    state = dict(started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        supervisor_pid=os.getpid(), horizon_s=363900, events=5237,
        protocol='BURST_REPAIR.md', status='running', modes={})
    lock = threading.Lock(); stop = threading.Event(); children = {}
    def save():
        temp = folder/'state.tmp'
        temp.write_text(json.dumps(state, indent=2)+'\n')
        temp.replace(folder/'state.json')
    save()
    def job(mode, delay):
        if stop.wait(delay):
            with lock:
                state['modes'][mode] = dict(status='not_started_after_peer_failure'); save()
            return 1
        cmd = [sys.executable, str(HERE/'verify_burst_v2.py'), '--execute', '--record', '--mode', mode]
        with (folder/(mode+'.log')).open('w') as log:
            child = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
            with lock:
                children[mode] = child
                state['modes'][mode] = dict(pid=child.pid, status='running'); save()
            code = child.wait()
        with lock:
            if code and not stop.is_set():
                state['first_failed_mode'] = mode; stop.set()
                for peer, process in children.items():
                    if peer != mode and process.poll() is None:
                        os.killpg(process.pid, signal.SIGINT)
            status = 'verified' if code == 0 else ('failed' if state.get('first_failed_mode') == mode
                                                   else 'cancelled_after_peer_failure')
            state['modes'][mode].update(status=status, exit_code=code); save()
        return code
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        fixed = pool.submit(job, 'fixed', 0)
        adaptive = pool.submit(job, 'adaptive', 30)
        codes = [fixed.result(), adaptive.result()]
    state['status'] = 'verified_both' if codes == [0, 0] else 'failed'
    state['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
    print(json.dumps(state, indent=2), flush=True)
    if any(codes): raise SystemExit(1)


if __name__ == '__main__': main()
