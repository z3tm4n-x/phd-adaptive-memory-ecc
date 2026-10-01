"""Integration checks using actual source files and independent numeric routes."""
from __future__ import annotations
import ctypes as C
from datetime import datetime,timezone
import json
import math
from pathlib import Path
import re
import numpy as np
from nc_reader import CFile, open_nc
import sgps
from response import Response, BITS, sigma, NS


def integration_checks(manifest,raw,out):
    names=[r["name"] for r in manifest["files"] if r["name"].startswith("se_") or "g19_d20260119_" in r["name"]]
    results=[]
    model=Response()
    for name in names:
        path=raw/name
        s=sgps.read(path)
        rates=model.calculate(s)
        # Independent typed C read vs adapter's numeric double route (optional
        # only when the C library is present; Python netCDF4 is also supported).
        typed=None
        try:
            with CFile(path) as f:
                a=np.empty(s.flux[:,:,:13].shape,dtype=np.float32)
                f.call("nc_get_var_float",f.ncid,f.varid("AvgDiffProtonFlux"),a.ctypes.data_as(C.POINTER(C.c_float)))
                double=f.array("AvgDiffProtonFlux")
                typed=bool(np.array_equal(a.astype(float),double))
                assert typed
        except RuntimeError:
            pass
        day=re.search(r"_d(\d{8})_",name)
        if day:
            expected=datetime.strptime(day[1],"%Y%m%d").replace(tzinfo=timezone.utc).timestamp()
            assert s.time[0]==expected and s.time[-1]+s.cadence==expected+86400
        max_error=0.
        for d in range(2):
            candidates=np.flatnonzero(np.all(np.isfinite(s.corrected[:,d]),axis=1))
            # Fixed spread over valid bins and the model peak; no cherry picking.
            selected=np.unique(np.r_[candidates[np.linspace(0,len(candidates)-1,min(9,len(candidates))).astype(int)],np.nanargmax(rates['main_loglog'][:,d])])
            for i in selected:
                sensor=1-d if s.yaw[i]==0 else d
                e=model.energy
                channel=s.corrected[i,d,:13]
                j=np.zeros(len(e))
                for k,E in enumerate(e):
                    if sigma.zero_crossing_low(model.points)<=E<s.lower[sensor,0]:
                        j[k]=channel[0]*(E/s.lower[sensor,0])**-2
                    elif s.lower[sensor,0]<=E<=s.upper[sensor,-1]:
                        z=np.searchsorted(s.energy[sensor],E)
                        if z==0: j[k]=channel[0]
                        elif z==13: j[k]=channel[-1]
                        else:
                            w=math.log(E/s.energy[sensor,z-1])/math.log(s.energy[sensor,z]/s.energy[sensor,z-1])
                            j[k]=(1-w)*channel[z-1]+w*channel[z]
                behind=(model.primary+model.secondary)@(4*math.pi*j)
                direct=BITS*np.trapezoid(behind*sigma.sigma_hat(e,model.points,'main_loglog'),e)
                compressed=rates['core_only'][i,d]
                rel=abs(direct-compressed)/max(abs(direct),1e-300)
                max_error=max(max_error,rel)
                assert rel<2e-13
        results.append({"file":name,"typed_float_vs_double_equal":typed,"timestamp_and_cadence_checked":True,
                        "independent_spectrum_and_full_transport_max_relative_error":max_error})
    record={"checks":results,"status":"all assertions passed","does_not_validate_physics":True}
    (out/'integration_checks.json').write_text(json.dumps(record,indent=2)+'\n')
    return record
