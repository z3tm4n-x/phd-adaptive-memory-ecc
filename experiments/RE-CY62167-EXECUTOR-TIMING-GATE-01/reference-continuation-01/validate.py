"""Bounded validation runner; records what actually ran and what did not."""
import compileall, contextlib, ctypes, hashlib, importlib.metadata, io, json
import os, platform, subprocess, sys, time, tracemalloc, unittest
from datetime import datetime, timezone
from pathlib import Path
import check_bounds
ROOT=Path(__file__).resolve().parent
def peak_working_set():
    if os.name!="nt": return None
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_=[("cb",wintypes.DWORD),("PageFaultCount",wintypes.DWORD)]+[
            (name,ctypes.c_size_t) for name in ("PeakWorkingSetSize","WorkingSetSize",
            "QuotaPeakPagedPoolUsage","QuotaPagedPoolUsage","QuotaPeakNonPagedPoolUsage",
            "QuotaNonPagedPoolUsage","PagefileUsage","PeakPagefileUsage")]
    counters=Counters(); counters.cb=ctypes.sizeof(counters)
    get_current=ctypes.windll.kernel32.GetCurrentProcess
    get_current.restype=wintypes.HANDLE
    get_info=ctypes.windll.psapi.GetProcessMemoryInfo
    get_info.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
    if not get_info(get_current(),ctypes.byref(counters),counters.cb): return None
    return counters.PeakWorkingSetSize
def main():
    start=datetime.now(timezone.utc).isoformat(); wall=time.perf_counter()
    tracemalloc.start()
    logs=io.StringIO()
    suite=unittest.defaultTestLoader.discover(str(ROOT),pattern="test_reference.py")
    result=unittest.TextTestRunner(stream=logs,verbosity=2).run(suite)
    with contextlib.redirect_stdout(logs):
        compiled=compileall.compile_dir(ROOT,quiet=1)
    numeric=check_bounds.verify()
    rtl=subprocess.run([sys.executable,str(ROOT/"check_rtl.py")],capture_output=True,text=True)
    try: rtl_result=json.loads(rtl.stdout)
    except json.JSONDecodeError: rtl_result={"status":"NOT_RUN_TOOL_LOAD_FAILURE","stderr":rtl.stderr,"exit_code":rtl.returncode}
    peak_trace=tracemalloc.get_traced_memory()[1]; tracemalloc.stop()
    output={
      "started_utc":start,"finished_utc":datetime.now(timezone.utc).isoformat(),
      "validation_wall_s":time.perf_counter()-wall,
      "python_peak_traced_bytes":peak_trace,"validation_process_peak_working_set_bytes":peak_working_set(),
      "memory_scope":"runner only; excludes independent compiler child",
      "environment":{"python":sys.version,"executable":sys.executable,"platform":platform.platform(),
        "git":subprocess.check_output(["git","--version"],text=True).strip(),
        "dependencies":{x:importlib.metadata.version(x) for x in ("pdfplumber","pypdf","pyslang")}},
      "unit_tests":{"run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"passed":result.wasSuccessful()},
      "compileall":compiled,"independent_numeric":numeric,"rtl_frontend":rtl_result,
      "rtl_simulation":json.loads((ROOT/"rtl_results.json").read_text()),
      "routed_sta":"NOT_RUN: Vivado unavailable; no FPGA or SRAM hardware tested",
      "test_image":{"data_bytes":2097152,"sha256":hashlib.sha256(bytes(2097152)).hexdigest(),"status":"functional zero data image only"},
      "boundedness":"no Monte Carlo, no new transport, no large raw outputs"}
    (ROOT/"test_results.txt").write_text(logs.getvalue(),encoding="utf-8",newline="\n")
    (ROOT/"validation.json").write_text(json.dumps(output,indent=2)+"\n",encoding="utf-8",newline="\n")
    print(json.dumps(output,indent=2))
    assert result.wasSuccessful() and compiled and rtl.returncode==0
if __name__=="__main__": main()
