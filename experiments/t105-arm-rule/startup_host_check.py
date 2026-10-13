"""Use installed Tcl shared library: no Vivado route, JTAG or hardware access."""
import ctypes,ctypes.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    name=ctypes.util.find_library('tcl8.6')
    if not name: raise RuntimeError('Tcl8.6 library missing; install/extract tcl8.6, do not skip host test')
    t=ctypes.CDLL(name)
    t.Tcl_CreateInterp.restype=ctypes.c_void_p
    t.Tcl_Eval.argtypes=[ctypes.c_void_p,ctypes.c_char_p];t.Tcl_Eval.restype=ctypes.c_int
    t.Tcl_GetStringResult.argtypes=[ctypes.c_void_p];t.Tcl_GetStringResult.restype=ctypes.c_char_p
    t.Tcl_DeleteInterp.argtypes=[ctypes.c_void_p]
    interp=t.Tcl_CreateInterp()
    # Tcl core builtins suffice: no implicit package discovery or system writes.
    cmd=f'encoding system utf-8; set argc 1; set argv [list {{{HERE}/outputs/startup-host.json}}]; source {{{HERE}/startup_host_check.tcl}}'
    try:
        result=t.Tcl_Eval(interp,cmd.encode())
        if result:raise RuntimeError(t.Tcl_GetStringResult(interp).decode())
    finally:t.Tcl_DeleteInterp(interp)
    output=json.loads((HERE/'outputs/startup-host.json').read_text())
    from startup_check import execute
    regs={int(k,16):int(v,16) for k,v in output['registers'].items()}
    result=execute(host_regs=regs)
    assert result['policy_entered']
    # Audit PLL ordering independently of the Tcl implementation: bypass,
    # reset, FDIV change, lock-check then release. Lock check tested by timeout.
    pll=[v for a,v in output['writes'] if a==0xf8000100]
    assert pll==[0x10,0x11,0x24011,0x24010,0x24000],pll
    assert regs[0xf8000120]==0x1f000200 and regs[0xf80001c4]==1
    output['actual_startup_ELF_accepts_host_result']=True
    output['no_device_connection']=True
    output['PLL_programming_order_checked']=True
    (HERE/'outputs/startup-host.json').write_text(json.dumps(output,indent=2)+'\n')
    print('C0 host model -> actual startup ELF checked; timing NOT modeled')
if __name__=='__main__':main()
