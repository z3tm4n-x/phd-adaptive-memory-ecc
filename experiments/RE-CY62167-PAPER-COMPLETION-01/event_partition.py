from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

TASK_ID = "RE-CY62167-PAPER-COMPLETION-01"
STARTING_SHA = "2f1292432b59d5637f024f216e3abd0694b744d7"
WORKING_BRANCH = "research/cy62167-paper-completion-01"
RAW_ARCHIVE_SHA256 = "16ab27789329adbbccdf9a7e5d0e15e855440d3f52b8dd93a384317a4635770a"
ADDRESS_BITS = 21
COORD_BITS = 12
MAX_ADDRESS = (1 << ADDRESS_BITS) - 1
MAX_COORD = (1 << COORD_BITS) - 1

# Frozen result of RE-CY62167-ADDRESS-MAPPING-01. These are not fitted here.
FROZEN_COEFFICIENT_MASKS = [
    131072, 16777216, 6145, 5121, 4609, 25165825, 529, 8192, 769, 521,
    2097152, 262144, 524288, 1048576, 65536, 4194304, 32768, 16384,
    515, 517, 4096,
]
FROZEN_COEFF_BLOB_SHA = "35f2410c8d6744bd80339bd38c08e31b90bc69b6"

HEADER_RE = re.compile(r"^cluster\s+(\d+)\s+with xmin\s+(-?\d+)\s+xmax\s+(-?\d+)\s+ymin\s+(-?\d+)\s+ymax\s+(-?\d+)\s*$")
XADD_RE = re.compile(r"^xadd\s+(-?\d+)\s+yadd\s+(-?\d+)(?:\s+(\d+):(\d+):(\d+))?\s*$")
COUNT_RE = re.compile(r"^NUMBER OF EVENTS\s*=\s*(\d+)\s*$")

# Controlled series metadata. P_HI is the nine-series manuscript subset.
SERIES_META = {
    "clust_Ar1050MeV.txt": ("heavy_ion", "Ar", 5.2, None, True),
    "clust_Ar548MeV.txt": ("heavy_ion", "Ar", None, None, False),
    "clust_C1080MeV.txt": ("heavy_ion", "C", None, None, False),
    "clust_C360MeV.txt": ("heavy_ion", "C", None, None, False),
    "clust_C720MeV.txt": ("heavy_ion", "C", None, None, False),
    "clust_Xe2700MeV.txt": ("heavy_ion", "Xe", None, None, False),
    "clust_XeLET27.txt": ("heavy_ion", "Xe", 27.0, None, True),
    "clust_XeLET42.txt": ("heavy_ion", "Xe", 42.0, None, True),
    "clust_XeLET57.txt": ("heavy_ion", "Xe", 57.0, None, True),
    "clust_U190.4GeV.txt": ("heavy_ion", "U", 15.0, None, True),
    "clust_U142.8GeV.txt": ("heavy_ion", "U", 17.0, None, True),
    "clust_U78.5GeV.txt": ("heavy_ion", "U", 22.0, None, True),
    "clust_U45.2GeV.txt": ("heavy_ion", "U", 29.0, None, True),
    "clust_U35.7GeV.txt": ("heavy_ion", "U", 33.0, None, True),
}
for e in (0.9, 1.0, 1.1, 1.5, 2.5, 3.0, 4.0, 5.0, 29.0, 40.0, 80.0, 124.0, 164.0, 186.0):
    tag = (str(int(e)) if float(e).is_integer() else str(e))
    # Actual names omit .0 and are p1MeV, p3MeV, etc.
    SERIES_META[f"clust_p{tag}MeV.txt"] = ("proton", "p", None, e, False)

# Correct potential integer name construction already matches all controlled names.

@dataclass(frozen=True)
class Cell:
    source_file: str
    segment_id: int
    cluster_id: int
    line_start: int
    cell_index: int
    timestamp: Optional[str]
    field_arity: int
    field0_raw: Optional[int]
    x: int
    y: int
    classification: str
    raw_fields: tuple[int, ...]

    @property
    def event_key(self):
        return (self.source_file, self.segment_id, self.cluster_id)

    @property
    def dedup_key(self):
        return (*self.event_key, self.x, self.y)

@dataclass
class ParsedFile:
    source_file: str
    cells: list[Cell]
    raw_cluster_count: int
    bounds_mismatches: int


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _zero_geometry(xmin, xmax, ymin, ymax, xadd, yadd, raw_cells):
    if (xmin, xmax, ymin, ymax, xadd, yadd) != (0, 0, 0, 0, 0, 0) or len(raw_cells) != 1:
        return False
    c = raw_cells[0]
    return (len(c) == 2 and c == (0, 0)) or (len(c) == 3 and c[1:] == (0, 0))


def _classify(cluster_id, timestamp, xmin, xmax, ymin, ymax, xadd, yadd, raw_cells, cell):
    zero = _zero_geometry(xmin, xmax, ymin, ymax, xadd, yadd, raw_cells)
    if len(cell) == 3:
        a, x, y = cell
        if timestamp == "03:03:03" and zero and a > MAX_ADDRESS:
            return "STRICT_SERVICE"
        if timestamp == "03:03:03" and zero and 0 <= a <= MAX_ADDRESS:
            return "AMBIGUOUS"
        if not 0 <= a <= MAX_ADDRESS:
            return "AMBIGUOUS"
        if not (0 <= x <= MAX_COORD and 0 <= y <= MAX_COORD):
            return "AMBIGUOUS"
        return "PHYSICAL_ELIGIBLE"
    if len(cell) == 2:
        x, y = cell
        if timestamp is None and cluster_id == 0 and zero and x == 0 and y == 0:
            return "AMBIGUOUS"
        if not (0 <= x <= MAX_COORD and 0 <= y <= MAX_COORD):
            return "AMBIGUOUS"
        return "PHYSICAL_NO_ADDRESS"
    raise ValueError("unsupported cell arity")


def parse_cluster_text(source_file: str, text: str) -> ParsedFile:
    lines = text.splitlines()
    i = 0
    segment = 1
    prev_cluster = None
    cells: list[Cell] = []
    clusters = 0
    bounds_bad = 0
    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        line_start = i + 1
        hm = HEADER_RE.match(lines[i].strip())
        if not hm:
            raise ValueError(f"{source_file}:{i+1}: unexpected line {lines[i]!r}")
        cid, xmin, xmax, ymin, ymax = map(int, hm.groups())
        if prev_cluster is not None and cid <= prev_cluster:
            segment += 1
        prev_cluster = cid
        i += 1
        xm = XADD_RE.match(lines[i].strip()) if i < len(lines) else None
        if not xm:
            raise ValueError(f"{source_file}:{i+1}: invalid xadd line")
        xadd, yadd = map(int, xm.groups()[:2])
        if xm.group(3) is None:
            timestamp = None
        else:
            h, m, s = map(int, xm.groups()[2:])
            if not (0 <= h <= 23 and 0 <= m <= 59 and 0 <= s <= 59):
                raise ValueError("invalid timestamp")
            timestamp = f"{h:02d}:{m:02d}:{s:02d}"
        i += 1
        raw_cells: list[tuple[int, ...]] = []
        while i < len(lines) and not COUNT_RE.match(lines[i].strip()):
            raw = lines[i].strip()
            if raw:
                parts = tuple(map(int, raw.split()))
                if len(parts) not in (2, 3):
                    raise ValueError(f"{source_file}:{i+1}: unsupported cell row")
                raw_cells.append(parts)
            i += 1
        if i >= len(lines):
            raise ValueError(f"{source_file}:{line_start}: missing NUMBER OF EVENTS")
        declared = int(COUNT_RE.match(lines[i].strip()).group(1))
        i += 1
        if declared != len(raw_cells):
            raise ValueError(f"{source_file}:{line_start}: NUMBER OF EVENTS={declared}, parsed={len(raw_cells)}")
        if raw_cells:
            xs = [c[-2] for c in raw_cells]
            ys = [c[-1] for c in raw_cells]
            if (min(xs), max(xs), min(ys), max(ys)) != (xmin, xmax, ymin, ymax):
                bounds_bad += 1
        for cell_index, raw in enumerate(raw_cells):
            if len(raw) == 3:
                field0, x, y = raw
            else:
                field0, x, y = None, raw[0], raw[1]
            cls = _classify(cid, timestamp, xmin, xmax, ymin, ymax, xadd, yadd, raw_cells, raw)
            cells.append(Cell(source_file, segment, cid, line_start, cell_index, timestamp, len(raw), field0, x, y, cls, raw))
        clusters += 1
    return ParsedFile(source_file, cells, clusters, bounds_bad)


def load_archive(archive_path: Path) -> dict[str, ParsedFile]:
    if sha256_path(archive_path) != RAW_ARCHIVE_SHA256:
        raise ValueError("raw archive SHA-256 does not match controlled fingerprint")
    parsed: dict[str, ParsedFile] = {}
    with zipfile.ZipFile(archive_path) as zf:
        for info in sorted((i for i in zf.infolist() if not i.is_dir()), key=lambda i: Path(i.filename).name):
            name = Path(info.filename).name
            if not name.lower().endswith(".txt"):
                continue
            text = zf.read(info.filename).decode("utf-8", "strict")
            parsed[name] = parse_cluster_text(name, text)
    return parsed


def is_ordinary(c: Cell) -> bool:
    return c.classification in ("PHYSICAL_ELIGIBLE", "PHYSICAL_NO_ADDRESS")


def event_local_dedup(cells: Iterable[Cell]) -> tuple[list[Cell], int]:
    groups: dict[tuple, list[Cell]] = defaultdict(list)
    for c in cells:
        if is_ordinary(c):
            groups[c.dedup_key].append(c)
    result = []
    removed = 0
    for key in sorted(groups):
        rs = sorted(groups[key], key=lambda c: (c.field0_raw if c.field0_raw is not None else -1, c.line_start, c.cell_index, c.raw_fields))
        result.append(rs[0])
        removed += len(rs) - 1
    return result, removed


def feature_mask(x: int, y: int) -> int:
    if not (0 <= x <= MAX_COORD and 0 <= y <= MAX_COORD):
        raise ValueError("coordinate outside 12-bit grid")
    v = 1
    for i in range(COORD_BITS):
        if (x >> i) & 1:
            v |= 1 << (1 + i)
        if (y >> i) & 1:
            v |= 1 << (1 + COORD_BITS + i)
    return v


def frozen_address(x: int, y: int) -> int:
    v = feature_mask(x, y)
    return sum((((v & int(c)).bit_count() & 1) << j) for j, c in enumerate(FROZEN_COEFFICIENT_MASKS))


def word_id(address: int, p: int, q: int) -> int:
    """Pack the 19 non-intra-word address bits into a stable integer."""
    if not (0 <= p < q < ADDRESS_BITS):
        raise ValueError("requires 0 <= p < q < 21")
    out = 0
    j = 0
    for bit in range(ADDRESS_BITS):
        if bit in (p, q):
            continue
        out |= ((address >> bit) & 1) << j
        j += 1
    return out


def direct_event(cells: list[Cell], p: int, q: int):
    """Return direct classification statistics for already-deduplicated distinct data cells."""
    words: dict[int, list[Cell]] = defaultdict(list)
    for c in cells:
        words[word_id(frozen_address(c.x, c.y), p, q)].append(c)
    counts = [len(v) for v in words.values()]
    direct = any(n >= 2 for n in counts)
    return {
        "direct": direct,
        "number_of_failing_words": sum(n >= 2 for n in counts),
        "max_same_word_data_cells": max(counts, default=0),
        "word_groups": words,
    }


def grouped_events(parsed: dict[str, ParsedFile]) -> dict[tuple, list[Cell]]:
    all_ordinary = []
    for name in sorted(parsed):
        all_ordinary.extend(c for c in parsed[name].cells if is_ordinary(c))
    dedup, _ = event_local_dedup(all_ordinary)
    events: dict[tuple, list[Cell]] = defaultdict(list)
    for c in dedup:
        events[c.event_key].append(c)
    return {k: sorted(v, key=lambda c: (c.x, c.y, c.field0_raw if c.field0_raw is not None else -1)) for k, v in sorted(events.items())}


def meta_for(source_file: str):
    if source_file not in SERIES_META:
        raise KeyError(f"missing controlled series metadata for {source_file}")
    radiation_type, particle, let, energy, in_hi = SERIES_META[source_file]
    return {"radiation_type": radiation_type, "particle": particle, "LET_MeV_cm2_mg": let, "energy_MeV": energy, "in_P_HI": in_hi}


def population_audit(parsed: dict[str, ParsedFile]):
    rows = []
    for name in sorted(parsed):
        pf = parsed[name]
        meta = meta_for(name)
        ordinary = [c for c in pf.cells if is_ordinary(c)]
        dedup, removed = event_local_dedup(ordinary)
        ordinary_event_keys = {c.event_key for c in ordinary}
        dedup_event_keys = {c.event_key for c in dedup}
        rows.append({
            "source_file": name,
            "radiation_type": meta["radiation_type"],
            "particle": meta["particle"],
            "LET_MeV_cm2_mg": "" if meta["LET_MeV_cm2_mg"] is None else meta["LET_MeV_cm2_mg"],
            "energy_MeV": "" if meta["energy_MeV"] is None else meta["energy_MeV"],
            "raw_cluster_count": pf.raw_cluster_count,
            "raw_cell_record_count": len(pf.cells),
            "S_raw": len(pf.cells),
            "ordinary_eligible_cells": len(ordinary),
            "S_ordinary": len(ordinary),
            "service_records": sum(c.classification == "STRICT_SERVICE" for c in pf.cells),
            "ambiguous_records": sum(c.classification == "AMBIGUOUS" for c in pf.cells),
            "event_local_duplicate_cells": removed,
            "deduplicated_cells": len(dedup),
            "S_dedup": len(dedup),
            "clusters_used_mapping_sweep": len(dedup_event_keys),
            "cells_used_mapping_sweep": len(dedup),
            "clusters_used_heavy_ion_xs": len(dedup_event_keys) if meta["in_P_HI"] else 0,
            "cells_used_heavy_ion_xs": len(dedup) if meta["in_P_HI"] else 0,
        })
    return rows


def aggregate_population(rows):
    return {
        "RAW": {"clusters": sum(int(r["raw_cluster_count"]) for r in rows), "cells": sum(int(r["raw_cell_record_count"]) for r in rows)},
        "ORDINARY": {"clusters": sum(int(r["clusters_used_mapping_sweep"]) for r in rows), "cells": sum(int(r["ordinary_eligible_cells"]) for r in rows)},
        "DEDUP": {"clusters": sum(int(r["clusters_used_mapping_sweep"]) for r in rows), "cells": sum(int(r["deduplicated_cells"]) for r in rows)},
        "service_records": sum(int(r["service_records"]) for r in rows),
        "ambiguous_records": sum(int(r["ambiguous_records"]) for r in rows),
        "event_local_duplicate_cells": sum(int(r["event_local_duplicate_cells"]) for r in rows),
        "P_HI": {"series": sum(bool(int(r["clusters_used_heavy_ion_xs"])) for r in rows), "clusters": sum(int(r["clusters_used_heavy_ion_xs"]) for r in rows), "cells": sum(int(r["cells_used_heavy_ion_xs"]) for r in rows)},
    }


def verify_frozen_addresses(parsed: dict[str, ParsedFile]):
    checked = 0
    mismatch = []
    for name in sorted(parsed):
        for c in parsed[name].cells:
            if c.classification == "PHYSICAL_ELIGIBLE" and c.field0_raw is not None:
                checked += 1
                pred = frozen_address(c.x, c.y)
                if pred != c.field0_raw:
                    mismatch.append((name, c.segment_id, c.cluster_id, c.x, c.y, c.field0_raw, pred))
    return checked, mismatch


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
