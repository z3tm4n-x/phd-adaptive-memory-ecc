"""Read-only SEPEM inventory; raw bytes never written into this package.

SEPEM_RDS_V2 accepts an existing ZIP or extracted directory. The optional
--archive verifies the original ZIP against an extracted directory.
Only reference series are scanned numerically; individual spacecraft files
are inventoried/hashed, not certified by the reference-series audit.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import time
import zipfile

HERE = Path(__file__).resolve().parent
REFERENCES = {"SEPEM_H_reference.txt": 11, "SEPEM_He_reference.txt": 8}


def digest(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(block)
    return h.hexdigest()


def scan_reference(stream, channels):
    h = hashlib.sha256()
    header = next(stream)
    h.update(header)
    count = 0
    first = previous = last = None
    nonfinite = negative = off_grid = 0
    gap_count = duplicate_or_reverse = 0
    minimum = [math.inf] * channels
    maximum = [-math.inf] * channels
    zeros = [0] * channels
    allzero = 0
    gap_examples = []
    for line_number, line in enumerate(stream, 2):
        h.update(line)
        row = line.decode("ascii").rstrip("\r\n").split(",")
        if len(row) != channels + 1:
            raise ValueError(f"column count at line {line_number}")
        t = datetime.fromisoformat(row[0])
        if t.tzinfo is not None:
            raise ValueError("Unexpected time-zone suffix: inspect input convention")
        off_grid += int(t.second != 0 or t.minute % 5 != 0 or t.microsecond != 0)
        if previous is not None:
            step = (t - previous).total_seconds()
            if step <= 0:
                duplicate_or_reverse += 1
            elif step != 300:
                gap_count += 1
                if len(gap_examples) < 20:
                    gap_examples.append([previous.isoformat(), t.isoformat(), step])
        values = list(map(float, row[1:]))
        for j, x in enumerate(values):
            if not math.isfinite(x):
                nonfinite += 1
                continue
            negative += int(x < 0)
            minimum[j] = min(minimum[j], x)
            maximum[j] = max(maximum[j], x)
            zeros[j] += int(x == 0)
        allzero += int(all(x == 0 for x in values))
        first = t if first is None else first
        last = previous = t
        count += 1
    if not count:
        raise ValueError("Empty reference series")
    return {
        "sha256": h.hexdigest(), "records": count, "channels": channels,
        "first_bin_start": first.isoformat(), "last_bin_start": last.isoformat(),
        "end_exclusive": (last + timedelta(seconds=300)).isoformat(),
        "timestamp_timezone": "not encoded in rows; UTC convention must be sourced",
        "sample_seconds": 300, "off_grid_records": off_grid,
        "gap_count": gap_count, "gap_examples": gap_examples,
        "duplicate_or_reverse_count": duplicate_or_reverse,
        "nonfinite_values": nonfinite, "negative_values": negative,
        "zeros_by_channel": zeros, "allzero_records": allzero,
        "minimum_by_channel": [x if math.isfinite(x) else None for x in minimum],
        "maximum_by_channel": [x if math.isfinite(x) else None for x in maximum],
        "numerically_complete": not any([nonfinite, negative, off_grid, gap_count, duplicate_or_reverse]),
        "original_observation_completeness": "unknown; supplier filled gaps/removed spikes",
    }


@contextmanager
def input_files(path):
    if path.is_dir():
        paths = sorted((p for p in path.rglob("*") if p.is_file()),
                       key=lambda p: p.relative_to(path).as_posix())
        yield [(p.relative_to(path).as_posix(), p.stat().st_size,
                lambda p=p: p.open("rb")) for p in paths]
    elif zipfile.is_zipfile(path):
        with zipfile.ZipFile(path) as archive:
            infos = sorted((i for i in archive.infolist() if not i.is_dir()), key=lambda i: i.filename)
            names = [i.filename for i in infos]
            if len(names) != len(set(names)):
                raise ValueError("Duplicate archive member names")
            yield [(i.filename, i.file_size, lambda i=i: archive.open(i)) for i in infos]
    else:
        raise ValueError("SEPEM_RDS_V2 must be a directory or ZIP")


def inventory(path):
    files, refs = [], {}
    with input_files(path) as inputs:
        for name, size, opener in inputs:
            basename = Path(name).name
            with opener() as stream:
                if basename in REFERENCES:
                    if basename in refs:
                        raise ValueError("Duplicate reference filename")
                    result = scan_reference(stream, REFERENCES[basename])
                    refs[basename] = result
                    sha = result["sha256"]
                else:
                    sha = digest(stream)
            files.append({"name": name, "bytes": size, "sha256": sha})
            print(f"audited {name}", flush=True)
    if set(refs) != set(REFERENCES):
        raise ValueError("Missing H or He reference series")
    files.sort(key=lambda f: f["name"])
    # This digest identifies the named extracted bytes, not the original ZIP.
    text = "".join(f"{f['sha256']}  {f['name']}\n" for f in files)
    return {"files": files, "reference_series": refs,
            "named_file_manifest_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "total_uncompressed_bytes": sum(f["bytes"] for f in files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    parser.add_argument("--out", type=Path, default=HERE / "outputs")
    args = parser.parse_args()
    raw = os.environ.get("SEPEM_RDS_V2")
    if not raw:
        parser.error("Set SEPEM_RDS_V2; no implicit Desktop path is used")
    path = Path(raw).resolve(strict=True)
    start = time.perf_counter()
    result = inventory(path)
    archive = args.archive or (path if path.is_file() else None)
    result["archive"] = None
    if archive:
        with archive.open("rb") as stream:
            result["archive"] = {"name": archive.name, "bytes": archive.stat().st_size,
                                 "sha256": digest(stream)}
        if path.is_dir():
            with input_files(archive) as inputs:
                expected = {Path(f["name"]).name: f["sha256"] for f in result["files"]}
                found = {}
                for name, _, opener in inputs:
                    with opener() as stream:
                        found[Path(name).name] = digest(stream)
                if expected != found:
                    raise ValueError("Extracted files differ from ZIP")
            result["extracted_bytes_match_archive"] = True
    result["citation"] = "SEPEM Reference Data Set version 2.00, European Space Agency (2016)"
    result["download_date"] = None
    result["download_date_note"] = "Filesystem timestamps are not proof of download date"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "input_audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2,
        allow_nan=False) + "\n", encoding="utf-8", newline="\n")
    run = {"python": platform.python_version(), "platform": platform.platform(),
           "elapsed_seconds": time.perf_counter() - start, "input_location": str(path),
           "scientific_processing": "input audit only"}
    (args.out / "audit_run.json").write_text(json.dumps(run, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8", newline="\n")
    print(json.dumps(run, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
