#!/usr/bin/env python3
"""Parser for Zenodo 10.5281/zenodo.8314389 proton cluster files.

The parser is intentionally conservative. It preserves every numeric field that is
present in a cluster record, but does not assign undocumented semantics to the
leading integer in timestamped cell rows (`field0_raw`).

Run boundaries are recovered from explicit cluster-id resets. In timestamped
files a very specific 03:03:03 / all-zero record with an out-of-range leading
integer is classified as a service/end-of-run sentinel. The apparently similar
all-zero cluster 0 in some non-timestamped files is *not* removed because the
same invariant cannot be proved without the sentinel timestamp/field.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Iterable, Iterator, Optional

HEADER_RE = re.compile(
    r"^cluster\s+(\d+)\s+with xmin\s+(-?\d+)\s+xmax\s+(-?\d+)\s+"
    r"ymin\s+(-?\d+)\s+ymax\s+(-?\d+)\s*$"
)
XADD_RE = re.compile(
    r"^xadd\s+(-?\d+)\s+yadd\s+(-?\d+)(?:\s+(\d+):(\d+):(\d+))?\s*$"
)
COUNT_RE = re.compile(r"^NUMBER OF EVENTS\s*=\s*(\d+)\s*$")

# CY62167GE30 can be configured as 2M x 8, hence 2,097,151 is the largest
# externally addressable location in that configuration. This is used only as
# part of a *service-record signature*, not as a semantic assignment of field0.
MAX_EXTERNAL_2M_ADDRESS = 2_097_151


@dataclass(frozen=True)
class CellRecord:
    x: int
    y: int
    field0_raw: Optional[int] = None


@dataclass(frozen=True)
class ClusterRecord:
    source_file: str
    line_start: int
    cluster_id: int
    xmin: int
    xmax: int
    ymin: int
    ymax: int
    xadd: int
    yadd: int
    timestamp_raw: Optional[str]
    timestamp_sod: Optional[int]
    cells: tuple[CellRecord, ...]
    number_of_events_declared: int
    segment_id: int

    @property
    def k(self) -> int:
        return len(self.cells)

    @property
    def is_strict_service_record(self) -> bool:
        """Recognize only the fully evidenced timestamped end-of-run sentinel."""
        if self.timestamp_raw != "03:03:03":
            return False
        if (self.xmin, self.xmax, self.ymin, self.ymax, self.xadd, self.yadd) != (0, 0, 0, 0, 0, 0):
            return False
        if self.k != 1:
            return False
        c = self.cells[0]
        return (
            c.x == 0
            and c.y == 0
            and c.field0_raw is not None
            and c.field0_raw > MAX_EXTERNAL_2M_ADDRESS
        )

    @property
    def is_ambiguous_zero_record(self) -> bool:
        """Flag but retain zero cluster-0 records when no sentinel evidence exists."""
        if self.timestamp_raw is not None or self.cluster_id != 0:
            return False
        if (self.xmin, self.xmax, self.ymin, self.ymax, self.xadd, self.yadd) != (0, 0, 0, 0, 0, 0):
            return False
        if self.k != 1:
            return False
        c = self.cells[0]
        return c.field0_raw is None and c.x == 0 and c.y == 0


def _timestamp(h: Optional[str], m: Optional[str], s: Optional[str]) -> tuple[Optional[str], Optional[int]]:
    if h is None:
        return None, None
    hi, mi, si = int(h), int(m), int(s)
    if not (0 <= hi <= 23 and 0 <= mi <= 59 and 0 <= si <= 59):
        raise ValueError(f"invalid timestamp {hi:02d}:{mi:02d}:{si:02d}")
    return f"{hi:02d}:{mi:02d}:{si:02d}", hi * 3600 + mi * 60 + si


def parse_cluster_file(path: Path) -> list[ClusterRecord]:
    lines = path.read_text(encoding="utf-8", errors="strict").splitlines()
    records: list[ClusterRecord] = []
    i = 0
    segment_id = 1
    previous_cluster_id: Optional[int] = None

    while i < len(lines):
        if not lines[i].strip():
            i += 1
            continue
        line_start = i + 1
        hm = HEADER_RE.match(lines[i].strip())
        if not hm:
            raise ValueError(f"{path.name}:{i+1}: unexpected line: {lines[i]!r}")
        cluster_id, xmin, xmax, ymin, ymax = map(int, hm.groups())
        if previous_cluster_id is not None and cluster_id <= previous_cluster_id:
            segment_id += 1
        previous_cluster_id = cluster_id
        i += 1

        if i >= len(lines):
            raise ValueError(f"{path.name}:{line_start}: missing xadd line")
        xm = XADD_RE.match(lines[i].strip())
        if not xm:
            raise ValueError(f"{path.name}:{i+1}: invalid xadd line: {lines[i]!r}")
        xadd, yadd = map(int, xm.groups()[:2])
        ts_raw, ts_sod = _timestamp(*xm.groups()[2:])
        i += 1

        cells: list[CellRecord] = []
        while i < len(lines):
            cm = COUNT_RE.match(lines[i].strip())
            if cm:
                break
            raw = lines[i].strip()
            if raw:
                parts = raw.split()
                if len(parts) == 2:
                    x, y = map(int, parts)
                    cells.append(CellRecord(x=x, y=y, field0_raw=None))
                elif len(parts) == 3:
                    f0, x, y = map(int, parts)
                    cells.append(CellRecord(x=x, y=y, field0_raw=f0))
                else:
                    raise ValueError(f"{path.name}:{i+1}: unsupported cell row: {raw!r}")
            i += 1
        if i >= len(lines):
            raise ValueError(f"{path.name}:{line_start}: missing NUMBER OF EVENTS")
        declared = int(COUNT_RE.match(lines[i].strip()).group(1))
        i += 1

        if declared != len(cells):
            raise ValueError(
                f"{path.name}:{line_start}: NUMBER OF EVENTS={declared}, parsed cells={len(cells)}"
            )

        records.append(
            ClusterRecord(
                source_file=path.name,
                line_start=line_start,
                cluster_id=cluster_id,
                xmin=xmin,
                xmax=xmax,
                ymin=ymin,
                ymax=ymax,
                xadd=xadd,
                yadd=yadd,
                timestamp_raw=ts_raw,
                timestamp_sod=ts_sod,
                cells=tuple(cells),
                number_of_events_declared=declared,
                segment_id=segment_id,
            )
        )

    return records


def physical_records(records: Iterable[ClusterRecord]) -> Iterator[ClusterRecord]:
    """Yield records after excluding only strict service sentinels."""
    for record in records:
        if not record.is_strict_service_record:
            yield record
