"""Reconstruct the preregistered 2021-12-25 forecast from pre-observation inputs."""
import argparse
from collections import defaultdict
from datetime import datetime
import gzip
import math
from pathlib import Path

import erfa
import numpy as np
import pdfplumber

from data import HERE, PROTOCOL as cfg, json_text, output, sha, verified

DAY = datetime.fromisoformat(cfg["utc_day"])
DAY_LENGTH = cfg["day_seconds"]
MISSING = -1


def extract_map(path):
    """Read the actual filled cells beneath the overlaid coastlines in Fig. 1."""
    axis = cfg["axis_pdf_points"]
    west, east = axis["x_west"], axis["x_east"]
    south, north = axis["y_south"], axis["y_north"]
    with pdfplumber.open(path) as pdf:
        rects = [(r["x0"], r["y0"], r["x1"], r["y1"], r["non_stroking_color"])
                 for r in pdf.pages[1].rects]
    # The legend is painted twice at the same positions. Use filled primitives,
    # avoiding text, coastlines and the independent RBM-Z panel below it.
    legend = sorted({(y0, y1, tuple(rgb)) for x0,y0,x1,y1,rgb in rects
                     if abs(x0-east) < .01 and 4 < x1-x0 < 5
                     and south-.01 <= y0 < y1 <= north+.01 and 1 < y1-y0 < 2})
    steps = cfg["legend_steps"]
    if len(legend) != steps:
        raise ValueError(f"Expected {steps} legend steps, found {len(legend)}")
    groups = defaultdict(list)
    max_edge_error = 0.
    for j,(lo,hi,rgb) in enumerate(legend):
        max_edge_error = max(max_edge_error, abs(lo-(south+j*(north-south)/steps)),
                             abs(hi-(south+(j+1)*(north-south)/steps)))
        groups[rgb].append(j)
    assert max_edge_error < cfg["legend_edge_tolerance_pt"]
    bands, colour_id = {}, {}
    scale_error = 4*cfg["legend_edge_tolerance_pt"]/(north-south)
    for colour, members in groups.items():
        first, last = members[0], members[-1]
        assert members == list(range(first,last+1))
        lo, hi = -2+4*first/steps, -2+4*(last+1)/steps
        bands[first] = {
            "last_step": last, "proxy_Hz": round(10**((lo+hi)/2), 12),
            "reading_low_Hz": 0. if first == 0 else math.floor(10**(lo-scale_error)*1e12)/1e12,
            "reading_high_Hz": None if last == steps-1 else math.ceil(10**(hi+scale_error)*1e12)/1e12,
            "edge_colour": first == 0 or last == steps-1,
        }
        colour_id[colour] = first

    grid = np.full((180,360), MISSING, dtype=np.int16)
    x_error = y_error = 0.
    for x0,y0,x1,y1,colour in rects:
        if not (west-.01 <= x0 < x1 <= east+.01 and south <= y0 < y1 <= north
                and .35 < x1-x0 < .9 and .35 < y1-y0 < .9):
            continue
        ax, bx = (x0-west)*360/(east-west), (x1-west)*360/(east-west)
        ay, by = (y0-south)*180/(north-south), (y1-south)*180/(north-south)
        ix, iy = round(ax), round(ay)
        assert round(bx) == ix+1 and round(by) == iy+1
        assert grid[iy,ix] == MISSING
        grid[iy,ix] = colour_id[tuple(colour)]
        x_error = max(x_error, abs(ax-ix), abs(bx-ix-1))
        y_error = max(y_error, abs(ay-iy), abs(by-iy-1))
    assert x_error <= cfg["axis_tolerance_degrees"]["longitude"]
    assert y_error <= cfg["axis_tolerance_degrees"]["latitude"]
    assert np.count_nonzero(grid >= 0) == 37434 and len(bands) == 95
    missing = np.argwhere(grid[38:142] == MISSING)
    diagnostics = {
        "panel": "Fig. 1 upper, PDF page 2", "legend_steps": steps,
        "distinct_colours": len(bands), "degree_cell_count": int((grid >= 0).sum()),
        "latitude_edges_deg": [-52,52],
        "absent_cell_west_south_deg": [[int(x)-180,int(y)-52] for y,x in missing],
        "max_plot_edge_error_deg": [round(x_error,6),round(y_error,6)],
        "max_legend_edge_error_pt": round(max_edge_error,6),
        "single_step_high_over_low": round(10**(4/steps),9),
        "interior_high_over_proxy_with_scale_tolerance": round(10**(2/steps+scale_error),9),
    }
    return grid, bands, diagnostics


def load_oem(path):
    text = path.read_text(encoding="ascii")
    for header in ("REF_FRAME            = EME2000", "TIME_SYSTEM          = UTC",
                   "CREATION_DATE  = "+cfg["sources"]["oem"]["creation_utc"]):
        assert header in text
    nodes = []
    for line in text.splitlines():
        if not line.startswith("2021-"):
            continue
        stamp, *state = line.split()
        offset = (datetime.fromisoformat(stamp)-DAY).total_seconds()
        if -480 <= offset <= DAY_LENGTH+480:
            nodes.append([offset, *map(float,state)])
    nodes = np.array(nodes)
    assert nodes.shape[1] == 7 and np.all(np.diff(nodes[:,0]) > 0)
    assert nodes[0,0] <= 0 and nodes[-1,0] >= DAY_LENGTH
    return nodes


def hermite(t, a, b):
    dt = b[:,0]-a[:,0]
    u = ((t-a[:,0])/dt)[:,None]
    return ((1+2*u)*(1-u)**2*a[:,1:4] + u*(1-u)**2*dt[:,None]*a[:,4:7]
            + u**2*(3-2*u)*b[:,1:4] + u**2*(u-1)*dt[:,None]*b[:,4:7])


def eop_forecast(path):
    text = path.read_text(encoding="ascii")
    assert "23 December 2021" in text and "XXXIV" in text
    rows = {}
    for line in text.split("PREDICTIONS:",1)[1].splitlines():
        f = line.split()
        if len(f) == 7 and f[0:2] == ["2021","12"] and f[2] in ("25","26"):
            rows[int(f[2])] = [float(v) for v in f[4:]]
    assert set(rows) == {25,26}
    return np.array([rows[25],rows[26]])


def track(nodes, eop, seconds):
    """OEM EME2000 km -> GCRS (frame bias) -> ITRS on supplied UTC labels."""
    right = np.searchsorted(nodes[:,0], seconds, side="right")
    if np.any(right == 0) or np.any(right == len(nodes)):
        raise ValueError("OEM extrapolation requested")
    a, b = nodes[right-1], nodes[right]
    supported = b[:,0]-a[:,0] <= cfg["max_oem_bracket_s"]+1e-7
    position = hermite(seconds,a,b)
    # ERFA bp00: rb transforms GCRS column vectors to mean J2000.
    # position is an array of row vectors; right multiplication applies rb.T.
    gcrs = position @ erfa.bp00(2451545.,0.)[0]
    eop_at_t = eop[0]+(seconds/DAY_LENGTH)[:,None]*(eop[1]-eop[0])
    utc = cfg["mjd_start"]+seconds/DAY_LENGTH
    tt = utc+(cfg["tai_minus_utc_s"]+32.184)/DAY_LENGTH
    ut1 = utc+eop_at_t[:,2]/DAY_LENGTH
    matrix = erfa.c2t06a(2400000.5,tt,2400000.5,ut1,
                         eop_at_t[:,0]*erfa.DAS2R,eop_at_t[:,1]*erfa.DAS2R)
    xyz = np.einsum("tij,tj->ti",matrix,gcrs)
    radius = np.linalg.norm(xyz,axis=1)
    lon, geodetic, height = erfa.gc2gd(erfa.WGS84,xyz*1000)
    lat = np.arctan2(xyz[:,2],np.hypot(xyz[:,0],xyz[:,1]))
    return np.degrees(lon), np.degrees(lat), np.degrees(geodetic), height/1000, radius, supported


def lookup(grid, longitude, latitude):
    x = np.floor((longitude+180)%360).astype(int)
    y = np.floor(latitude+90).astype(int)
    return grid[y,x]


def run_edges(values):
    changes = np.flatnonzero(np.any(values[1:] != values[:-1],axis=1))+1
    return np.r_[0,changes,len(values)]


def intervals(mask):
    edges = np.diff(np.r_[False,mask,False].astype(int))
    return np.c_[np.flatnonzero(edges == 1),np.flatnonzero(edges == -1)].tolist()


def build(directory):
    src = {name:verified(directory,spec) for name,spec in cfg["sources"].items()}
    grid, bands, info = extract_map(src["map"])
    nodes, eop = load_oem(src["oem"]), eop_forecast(src["iers"])
    seconds = np.arange(DAY_LENGTH,dtype=float)
    lon,lat,gd,height,radius,supported = track(nodes,eop,seconds)
    primary = lookup(grid,lon,lat)
    primary[~supported] = MISSING
    alternate = lookup(grid,lon,gd)
    alternate[~supported] = MISSING
    x_tol, y_tol = (cfg["axis_tolerance_degrees"][k] for k in ("longitude","latitude"))
    neighbours = np.stack([primary] + [lookup(grid,lon+dx,lat+dy)
                          for dx in (-x_tol,x_tol) for dy in (-y_tol,y_tol)])
    good_neighbourhood = (neighbours >= 0).all(axis=0)
    low = np.where(good_neighbourhood,neighbours.min(axis=0),MISSING)
    high = np.where(good_neighbourhood,neighbours.max(axis=0),MISSING)
    states = np.column_stack([primary,low,high])
    edges = run_edges(states)
    lines = ["# begin_s end_s_exclusive primary_colour lowest_colour highest_colour"]
    for start,end in zip(edges[:-1],edges[1:]):
        row = [start,end,*states[start]]
        lines.append(" ".join(str(x) for x in row))
    rle = "\n".join(lines)+"\n"

    proxy_values = np.full(cfg["legend_steps"]+1,np.nan)
    for key,band in bands.items():
        proxy_values[key] = band["proxy_Hz"]
    rates = proxy_values[primary]
    threshold = cfg["rate_threshold_Hz"]
    by_minute = rates.reshape(-1,60)
    coverage = np.isfinite(by_minute).sum(axis=1)
    mean = np.nansum(by_minute,axis=1)/np.maximum(coverage,1)
    minute_state = np.where(coverage >= cfg["minimum_seconds_per_UTC_minute"],
                            (mean >= threshold).astype(int),MISSING)
    comparable = (primary >= 0) & (alternate >= 0)
    nominal_high = rates >= threshold
    coord_hash = sha(np.rint(np.column_stack([lon,lat,radius])*1e6).astype("<i8").tobytes())
    interior = nodes[1:-1]
    omitted_error = np.linalg.norm(hermite(interior[:,0],nodes[:-2],nodes[2:])-interior[:,1:4],axis=1)
    created = datetime.fromisoformat(cfg["sources"]["oem"]["creation_utc"])
    lead = (DAY-created).total_seconds()/3600
    meta = {
        "day_UTC": cfg["utc_day"], "forecast_only": True,
        "protocol_sha256_lf": sha((HERE/"protocol.json").read_bytes().replace(b"\r\n",b"\n")),
        "forecast_source_sha256_lf": sha(Path(__file__).read_bytes().replace(b"\r\n",b"\n")),
        "source_sha256": {name:spec["sha256"] for name,spec in cfg["sources"].items()},
        "units": "counts per nominal second (Hz)",
        "lead_from_creation_hours_start_end": [round(lead,9),round(lead+24,9)],
        "orbit": {"bracketing_nodes":len(nodes),"largest_node_spacing_s":round(float(np.diff(nodes[:,0]).max()),6),
                  "supported_seconds":int(supported.sum()),"geodetic_height_km":[round(float(height.min()),3),round(float(height.max()),3)],
                  "leave_one_node_out_max_km":round(float(omitted_error.max()),6),
                  "coordinate_hash_lon_lat_radius_times_1e6_i64le":coord_hash,
                  "IERS_prediction_x_y_arcsec_UT1minusUTC_s":eop.tolist()},
        "map": info, "bands": {str(k):bands[k] for k in sorted(bands)},
        "seconds": {"missing_primary":int((primary < 0).sum()),
                    "edge_colour":int(np.isin(primary,[0,97]).sum()),
                    "missing_reading_neighbour":int((~good_neighbourhood).sum()),
                    "geodetic_lat_common":int(comparable.sum()),
                    "geodetic_changes_elevated":int(np.sum(comparable & (nominal_high != (proxy_values[alternate] >= threshold)))),
                    "coordinate_rounding_can_change_elevated":int(np.sum(good_neighbourhood & ((proxy_values[low] >= threshold) != (proxy_values[high] >= threshold))))},
        "frozen_elevated_second_intervals":intervals(nominal_high & (primary >= 0)),
        "frozen_elevated_minute_intervals":intervals(minute_state == 1),
        "frozen_unknown_minute_intervals":intervals(minute_state == MISSING),
        "runs":len(edges)-1, "rle_sha256_lf":sha(rle.encode("ascii")),
    }
    return rle,meta


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path)
    parser.add_argument("--check",action="store_true")
    args = parser.parse_args()
    rle,meta = build(args.directory)
    packed = HERE/"forecast.rle.gz"
    if args.check:
        if gzip.decompress(packed.read_bytes()).decode("ascii") != rle:
            raise ValueError("Reproduction differs: forecast.rle.gz (decompressed)")
    else:
        packed.write_bytes(gzip.compress(rle.encode("ascii"),mtime=0))
    output("forecast.json",json_text(meta),args.check)
    print(f"Forecast: {meta['runs']} runs, {meta['rle_sha256_lf']}, {meta['map']['degree_cell_count']} map cells.")


if __name__ == "__main__":
    main()
