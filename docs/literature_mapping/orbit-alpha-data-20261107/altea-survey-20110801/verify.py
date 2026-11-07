"""Replay the ALTEA-Survey passage from NASA RadLab (standard library only)."""

import argparse
import gzip
import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
DAY_START = datetime(2011, 8, 1, tzinfo=timezone.utc)
MINUTE = timedelta(minutes=1)
FIRST_INSIDE = DAY_START.replace(hour=2, minute=11)
LAST_INSIDE = DAY_START.replace(hour=2, minute=30)

BASE_QUERY = (
    "https://visualization.osdr.nasa.gov/radlab/api/"
    "?spacecraft=ISS&instrument_id=ALTEA-Survey"
)
FIELDS = "&absorbed_dose_rate&dose_equivalent_rate&flux&latitude&longitude&altitude&B&L&format=json"
DAY_URL = BASE_QUERY + "&timestamp%3E=2011-08-01T00%3A00&timestamp%3C2011-08-02T00%3A00" + FIELDS
PASS_URL = BASE_QUERY + "&timestamp%3E=1312164600&timestamp%3C1312165920&module&instrument_family" + FIELDS
DAY_SHA = "1d5724819cf97957262ca2a3891b10050d16445bf18197d9d10740c5c4658100"
PASS_SHA = "296e5a241e3cf410e8b1412cdb60d8ca303c8fa919ad59e876d4523c0b7f0ed1"


def read_rows(raw, expected_sha):
    digest = hashlib.sha256(raw).hexdigest()
    if digest != expected_sha:
        raise ValueError(f"Snapshot differs: SHA-256 {digest}, expected {expected_sha}")
    payload = json.loads(raw)
    rows = {}
    for values in payload["data"]:
        row = dict(zip(payload["columns"], values, strict=True))
        stamp = datetime.fromisoformat(row["timestamp"])
        stamp = stamp.astimezone(timezone.utc) if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)
        if not DAY_START <= stamp < DAY_START + timedelta(days=1):
            raise ValueError(f"Time outside selected day: {stamp}")
        if stamp in rows or stamp.second or stamp.microsecond:
            raise ValueError(f"Duplicate or off-grid timestamp: {stamp}")
        if row["spacecraft"] != "ISS" or row["instrument_id"] != "ALTEA-Survey":
            raise ValueError(f"Unexpected instrument at {stamp}")
        rows[stamp] = row
    return rows


def saa_flag(row):
    # An absent minute or either unknown coordinate breaks a run.
    if row is None or row["b"] is None or row["l"] is None:
        return None
    return row["b"] < 27_000 and row["l"] < 2.4


def first_bracketed_run(rows):
    # Both immediately adjacent outside labels must have been observed.
    start = None
    previous = None
    for minute in range(1440):
        stamp = DAY_START + minute * MINUTE
        current = saa_flag(rows.get(stamp))
        if current is True and previous is False:
            start = stamp
        if current is False and start is not None:
            return start, stamp - MINUTE
        if current is None:
            start = None
        previous = current
    raise ValueError("No pass with contiguous inside minutes and two observed flanks")


def check_pass(rows):
    before = FIRST_INSIDE - MINUTE
    after = LAST_INSIDE + MINUTE
    if len(rows) != 22 or min(rows) != before or max(rows) != after:
        raise ValueError("Unexpected time coverage for pass plus flanks")
    if first_bracketed_run(rows) != (FIRST_INSIDE, LAST_INSIDE):
        raise ValueError("Magnetic selection differs from the reported pass")
    for row in rows.values():
        if row["module"] != "US Lab" or row["instrument_family"] != "ALTEA" or None in row.values():
            raise ValueError(f"Incomplete record or unexpected detector at {row['timestamp']}")
    inside = [rows[stamp] for stamp in sorted(rows) if FIRST_INSIDE <= stamp <= LAST_INSIDE]
    peak = max(inside, key=lambda row: row["flux"])
    print(f"{len(inside)} inside minutes, {inside[0]['timestamp']} .. {inside[-1]['timestamp']} UTC")
    print("Peak flux %.8f cm^-2 sr^-1 s^-1 at %s UTC" % (peak["flux"], peak["timestamp"]))
    for row in (inside[0], peak, inside[-1]):
        print(row["timestamp"], row["latitude"], row["longitude"], row["altitude"],
              row["flux"], row["absorbed_dose_rate"], row["dose_equivalent_rate"])


def check_day(raw, pass_rows):
    rows = read_rows(raw, DAY_SHA)
    if len(rows) != 1348 or first_bracketed_run(rows) != (FIRST_INSIDE, LAST_INSIDE):
        raise ValueError("Daily coverage or first eligible pass has changed")
    for stamp, pass_row in pass_rows.items():
        if any(pass_row[key] != value for key, value in rows[stamp].items()):
            raise ValueError(f"Different records in the day and pass queries at {stamp}")
    print(f"Day replay: {len(rows)} minute records, {1440 - len(rows)} missing; same first pass")


def download(url):
    try:
        with urlopen(url, timeout=60) as response:
            return response.read()
    except (URLError, TimeoutError) as error:
        raise SystemExit(f"RadLab query failed: {error}\n{url}") from error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--archive", action="store_true", help="repeat both public RadLab queries")
    source.add_argument("--day-file", type=Path, help="replay the original day JSON from disk")
    args = parser.parse_args()
    pass_rows = read_rows((HERE / "radlab-pass.json").read_bytes(), PASS_SHA)
    check_pass(pass_rows)
    if args.archive:
        read_rows(download(PASS_URL), PASS_SHA)
        check_day(download(DAY_URL), pass_rows)
    elif args.day_file:
        check_day(args.day_file.read_bytes(), pass_rows)
    else:
        check_day(gzip.decompress((HERE / "radlab-day.json.gz").read_bytes()), pass_rows)
