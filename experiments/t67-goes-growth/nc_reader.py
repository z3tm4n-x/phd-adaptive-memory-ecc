"""Read-only NetCDF interface; netCDF4 Python, or existing libnetcdf via ctypes.

The fallback uses the documented Unidata C API, not a new HDF5 decoder. VTK's
bundled, symbol-prefixed copy is supported for the installed research runtime.
No dependencies are installed, and no input file is modified.
"""
from __future__ import annotations

import ctypes as C
import ctypes.util
import importlib.util
from functools import lru_cache
import os
from pathlib import Path
import numpy as np


@lru_cache(maxsize=1)
def library():
    candidates = []
    if os.environ.get("T67_NETCDF_LIBRARY"):
        candidates.append(os.environ["T67_NETCDF_LIBRARY"])
    normal = ctypes.util.find_library("netcdf")
    if normal:
        candidates.append(normal)
    vtk = importlib.util.find_spec("vtkmodules")
    if vtk and vtk.submodule_search_locations:
        for root in vtk.submodule_search_locations:
            candidates.extend(str(p) for p in Path(root).glob("libvtknetcdf*.so"))
            candidates.extend(str(p) for p in Path(root).glob("*netcdf*.dll"))
    for path in candidates:
        try:
            lib = C.CDLL(path)
        except OSError:
            continue
        prefix = "" if hasattr(lib, "nc_open") else "vtknetcdf_"
        if hasattr(lib, prefix + "nc_open"):
            return lib, prefix
    raise RuntimeError("NetCDF reader unavailable: install the declared netCDF4 dependency in the execution environment or provide T67_NETCDF_LIBRARY")


class CFile:
    def __init__(self, path):
        self.lib, self.prefix = library()
        self.id = C.c_int()
        self.call("nc_open", str(path).encode(), 0, C.byref(self.id))
        self.ncid = self.id.value
        self._names = None

    def call(self, name, *args):
        fn = getattr(self.lib, self.prefix + name)
        fn.restype = C.c_int
        code = fn(*args)
        if code:
            err = getattr(self.lib, self.prefix + "nc_strerror")
            err.restype = C.c_char_p
            raise ValueError(f"{name}: {err(code).decode()}")

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.call("nc_close", self.ncid)

    def varid(self, name):
        v = C.c_int()
        self.call("nc_inq_varid", self.ncid, name.encode(), C.byref(v))
        return v.value

    def names(self):
        n = C.c_int()
        self.call("nc_inq_nvars", self.ncid, C.byref(n))
        out = []
        for i in range(n.value):
            b = C.create_string_buffer(257)
            self.call("nc_inq_varname", self.ncid, i, b)
            out.append(b.value.decode())
        return out

    def attrs(self, name=None):
        vid = -1 if name is None else self.varid(name)
        n = C.c_int()
        if vid == -1:
            self.call("nc_inq_natts", self.ncid, C.byref(n))
        else:
            self.call("nc_inq_varnatts", self.ncid, vid, C.byref(n))
        out = {}
        for i in range(n.value):
            key = C.create_string_buffer(257)
            self.call("nc_inq_attname", self.ncid, vid, i, key)
            typ, length = C.c_int(), C.c_size_t()
            self.call("nc_inq_att", self.ncid, vid, key.value,
                      C.byref(typ), C.byref(length))
            if typ.value == 2:  # NC_CHAR
                buf = C.create_string_buffer(length.value + 1)
                self.call("nc_get_att_text", self.ncid, vid, key.value, buf)
                value = buf.raw[:length.value].decode("utf-8", errors="replace")
            elif typ.value == 12:  # NC_STRING
                buf = (C.c_char_p * length.value)()
                self.call("nc_get_att_string", self.ncid, vid, key.value, buf)
                value = [x.decode("utf-8", errors="replace") for x in buf]
                self.call("nc_free_string", length, buf)
                if len(value) == 1:
                    value = value[0]
            else:
                buf = (C.c_double * length.value)()
                self.call("nc_get_att_double", self.ncid, vid, key.value, buf)
                value = list(buf)
                if len(value) == 1:
                    value = value[0]
            out[key.value.decode()] = value
        return out

    def array(self, name):
        vid = self.varid(name)
        nd = C.c_int()
        self.call("nc_inq_varndims", self.ncid, vid, C.byref(nd))
        ids = (C.c_int * nd.value)()
        self.call("nc_inq_vardimid", self.ncid, vid, ids)
        shape = []
        for i in ids:
            n = C.c_size_t()
            self.call("nc_inq_dimlen", self.ncid, i, C.byref(n))
            shape.append(n.value)
        a = np.empty(shape, dtype=np.float64)
        self.call("nc_get_var_double", self.ncid, vid,
                  a.ctypes.data_as(C.POINTER(C.c_double)))
        return a


class PyFile:
    def __init__(self, path):
        import netCDF4
        self.ds = netCDF4.Dataset(path, "r")
        self.ds.set_auto_maskandscale(False)

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.ds.close()

    def names(self):
        return list(self.ds.variables)

    def attrs(self, name=None):
        obj = self.ds if name is None else self.ds.variables[name]
        return {k: obj.getncattr(k) for k in obj.ncattrs()}

    def array(self, name):
        return np.asarray(self.ds.variables[name][...], dtype=float)


def open_nc(path):
    return PyFile(path) if importlib.util.find_spec("netCDF4") else CFile(path)
