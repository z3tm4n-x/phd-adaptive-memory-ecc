"""Frozen catalogue selection and bounded, checksum-verified NOAA downloads."""
from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import time
from archive import SPECIAL, fetch, sha256


def dt(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def select(inv, config):
    events = []
    for row in inv["catalogue"]["rows"]:
        start, peak = dt(row["onset_utc"]), dt(row["peak_utc"])
        events.append({"id": "sep_" + start.strftime("%Y%m%d_%H%M"), "kind": "NOAA_catalogue",
                       **row, "catalogue_date_warning": (peak-start).total_seconds() > 7*86400})
    for s in config["author_dates"]:
        # A ±1 day overlap with an already selected catalogue episode identifies
        # the author's Jan 19 case with NOAA's Jan 18 onset, without duplicate data.
        target = dt(s + "T00:00:00+00:00")
        matches = [e for e in events if dt(e["onset_utc"])-timedelta(days=1) <= target <= dt(e["peak_utc"])+timedelta(days=1)]
        if matches:
            for e in matches:
                e.setdefault("author_dates", []).append(s)
        else:
            events.append({"id": "author_"+s.replace("-", ""), "kind": "author_date",
                           "onset_utc": target.isoformat(), "peak_utc": (target+timedelta(days=1)).isoformat(), "author_dates": [s]})
    cutoff = dt(config["cutoff_exclusive_utc"])
    for e in events:
        start, peak = dt(e["onset_utc"]), dt(e["peak_utc"])
        e["analysis_start"] = (start-timedelta(days=config["days_before_onset"])).isoformat()
        e["analysis_end_exclusive"] = min(peak+timedelta(days=config["days_after_peak"]), cutoff).isoformat()
        e["background_start"] = (dt(e["analysis_start"])-timedelta(hours=config["background_hours"])).isoformat()
        e["holdout"] = (start.year == 2017 or start.year >= 2025) and not e.get("author_dates")
    events.append({"id": "special_201709", "kind": "special_full_month",
                   "onset_utc": "2017-09-01T00:00:00+00:00", "peak_utc": "2017-09-30T23:55:00+00:00",
                   "analysis_start": "2017-09-01T00:00:00+00:00", "analysis_end_exclusive": "2017-10-01T00:00:00+00:00",
                   "background_start": "2017-08-31T00:00:00+00:00", "holdout": True})
    selected = []
    for row in inv["files"]:
        if not row["selected_version"]:
            continue
        day = datetime.strptime(row["date"], "%Y%m%d").replace(tzinfo=timezone.utc)
        ids = [e["id"] for e in events if dt(e["background_start"]) < day+timedelta(days=1) and day < dt(e["analysis_end_exclusive"])]
        if ids:
            selected.append({**row, "event_ids": ids})
    selected.append({"name": SPECIAL.rsplit("/", 1)[-1], "url": SPECIAL, "satellite": 16,
                     "cadence_s": 300, "date": "20170901", "version": "special_2_0_0", "product_prefix": "se",
                     "selected_version": True, "event_ids": [e["id"] for e in events if e["onset_utc"].startswith("2017-09")]})
    return {"catalogue": {k:v for k,v in inv["catalogue"].items() if k != "rows"},
            "events": events, "files": selected}


def download(manifest, cache, out):
    def one(row):
        for attempt in range(3):
            try:
                p = fetch(row["url"], cache)
                digest = sha256(p)
                if row.get("sha256") and digest != row["sha256"]:
                    raise ValueError("Source changed: " + row["name"])
                return {**row, "sha256": digest, "bytes": p.stat().st_size}
            except (TimeoutError, OSError):
                if attempt == 2:
                    raise
                time.sleep(1 + attempt)
    rows, failed = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(one, row): row for row in manifest["files"]}
        for i, future in enumerate(as_completed(futures), 1):
            try:
                rows.append(future.result())
            except Exception as exc:
                failed.append({"name": futures[future]["name"], "error": str(exc)})
            if i % 50 == 0:
                print(json.dumps({"downloaded_or_verified": i, "total": len(futures), "failed": len(failed)}), flush=True)
    result = {**manifest, "files": sorted(rows, key=lambda x:x["name"]), "download_failures": failed}
    Path(out).write_text(json.dumps(result, ensure_ascii=False, indent=2)+"\n")
    if failed:
        raise RuntimeError(f"{len(failed)} files unavailable; successful cache retained")
    return result


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--inventory", type=Path, required=True)
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--select-only", action="store_true")
    args=p.parse_args()
    config=json.loads(Path(__file__).with_name("config.json").read_text())
    manifest=select(json.loads(args.inventory.read_text()), config)
    if args.select_only:
        args.out.write_text(json.dumps(manifest, ensure_ascii=False, indent=2)+"\n")
    else:
        manifest=download(manifest, args.cache, args.out)
    print(json.dumps({"events": len(manifest["events"]), "selected_files": len(manifest["files"])}))


if __name__ == "__main__":
    main()
