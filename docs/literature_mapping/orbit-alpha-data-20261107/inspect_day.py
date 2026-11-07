"""Inspect the fixed archive day. Arguments are the original MAXI, Metop and SWPC files."""
import argparse
import hashlib
from datetime import datetime
from pathlib import Path

import numpy as np
from netCDF4 import Dataset


def digest(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file, "sha256").hexdigest()


def compare_times(oem_path, rbm_path):
    with oem_path.open(encoding="ascii") as file:
        lines = [line.strip() for line in file]
    created = next(line.split("=", 1)[1].strip() for line in lines
                   if line.startswith("CREATION_DATE"))
    stamps = [line.split()[0] for line in lines if line.startswith("2021-12-24T")]
    # This check is fixed at 2021-12-24. UTC gained five leap seconds from the
    # MAXI epoch (end of 2005, 2008, June 2012, June 2015, end of 2016).
    epoch = datetime(2000, 1, 1)
    grid = np.array([(datetime.fromisoformat(t) - epoch).total_seconds() + 5
                     for t in stamps])
    observed = np.loadtxt(rbm_path, usecols=0)
    if np.any(np.diff(observed) <= 0) or np.any(np.diff(grid) <= 0):
        raise ValueError("Non-increasing time stamps")
    right = np.searchsorted(observed, grid)
    before = observed[np.clip(right - 1, 0, len(observed) - 1)]
    after = observed[np.clip(right, 0, len(observed) - 1)]
    separation = np.minimum(np.abs(grid - before), np.abs(grid - after))
    print("NASA file:", digest(oem_path), "created:", created)
    print("JAXA file:", digest(rbm_path), "records:", len(observed))
    print("Distinct trajectory epochs, nearest RBM record within 1 s:",
          len(grid), int(np.sum(separation <= 1)))
    print("Largest nearest-record time difference (s):", separation.max())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("maxi", "metop", "swpc"):
        parser.add_argument(name, type=Path)
    parser.add_argument('--alignment', nargs=2, type=Path, metavar=('NASA_OEM', 'RBM_20211224'))
    paths = parser.parse_args()
    for file in (paths.maxi, paths.metop, paths.swpc):
        print(file.name, digest(file))

    with paths.maxi.open(encoding="ascii") as file:
        fields = file.readline().strip().lstrip("#").split()
        if fields != ["TIME", "COUNT_H", "COUNT_Z", "LVL", "LON", "LAT", "RADIUS"]:
            raise ValueError(f"Unexpected MAXI columns: {fields}")
        records = np.loadtxt(file)
    times, level = records[:, 0], records[:, 3]
    print("MAXI rows, levels, first and last mission seconds:",
          len(times), np.unique(level), times[0], times[-1])
    print("MAXI largest adjacent time step (s):", np.diff(times).max())

    with Dataset(paths.metop) as data:
        # The 'time' variable has valid_range [0,0] despite nonzero Unix times.
        # Use the three calendar fields documented in this NetCDF file.
        years, days, msec = (data[key][:] for key in ("year", "day", "msec"))
        if any(np.ma.getmaskarray(column).any() for column in (years, days, msec)):
            raise ValueError("Missing values in Metop calendar")
        print("Metop rows, year/day of year, first and last milliseconds:",
              len(msec), np.unique(years), np.unique(days), msec[0], msec[-1])
        print("Metop median adjacent time step (ms):", np.median(np.diff(np.asarray(msec))))
        for key in ("mep_omni_flux_p1", "mep_omni_flux_flag_fit", "mep_omni_flux_flag_iter_lim"):
            print(key, data[key].long_name, data[key].units)

    for line in paths.swpc.read_text(encoding="ascii").splitlines():
        if line.startswith((":Issued:", "III.", "Proton ")):
            print(line)

    if paths.alignment:
        compare_times(*paths.alignment)


if __name__ == "__main__":
    main()
