"""Public NOAA archive inventory, explicit version selection and cached downloads."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.request
from urllib.parse import urljoin

ROOT = "https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/"
SPECIAL_ROOT = "https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/goesr/solar_proton_events/sgps_sep2017_event_data/"
SPECIAL = SPECIAL_ROOT + "se_sgps-l2-avg5m_g16_s20172440000000_e20172732355000_v2_0_0.nc"
CATALOGUE = "https://www.ngdc.noaa.gov/stp/space-weather/interplanetary-data/solar-proton-events/SEP%20page%20code.html"
DAY_RE = re.compile(r"^(dn|sci)_sgps-l2-avg([15])m_g(16|18|19)_d(\d{8})_v(\d+-\d+-\d+)\.nc$")


def sha256(path):
    return hashlib.file_digest(Path(path).open("rb"), "sha256").hexdigest()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(v for k, v in attrs if k == "href")


class Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th") and self.row is not None:
            self.cell = []

    def handle_data(self, s):
        if self.cell is not None:
            self.cell.append(s)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def fetch(url, cache):
    """Immutable URL-keyed local snapshot; refresh requires a new cache folder."""
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    name = url.rsplit("/", 1)[-1]
    key = hashlib.sha256(url.encode()).hexdigest()[:16]
    path = cache / (name if name.endswith(".nc") else key + ".html")
    if not path.exists():
        req = urllib.request.Request(url, headers={"User-Agent": "T67-reproducible-research/1.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        # Exclusive creation avoids silently replacing an already captured source.
        try:
            with path.open("xb") as f:
                f.write(data)
        except FileExistsError:
            pass
    return path


def listing(url, cache):
    path = fetch(url, cache)
    parser = Links()
    parser.feed(path.read_text())
    return parser.links, {"url": url, "sha256": sha256(path), "cache_file": path.name}


def inventory(cache, cutoff="20261001"):
    indexes, months = [], []
    for sat in (16, 18, 19):
        for cadence in (1, 5):
            root = ROOT + f"goes{sat}/l2/data/sgps-l2-avg{cadence}m/"
            years, meta = listing(root, cache)
            indexes.append(meta)
            for y in sorted(x for x in years if re.fullmatch(r"20\d\d/", x) and 2017 <= int(x[:4]) <= 2026):
                ms, meta = listing(root + y, cache)
                indexes.append(meta)
                months.extend(root + y + m for m in ms if re.fullmatch(r"\d\d/", m) and y[:4] + m[:2] < cutoff[:6])
    def one(url):
        links, meta = listing(url, cache)
        rows = []
        for f in sorted(links):
            m = DAY_RE.fullmatch(f)
            if m and "20170101" <= m[4] < cutoff:
                rows.append({"url": urljoin(url, f), "name": f, "satellite": int(m[3]),
                             "cadence_s": 60 * int(m[2]), "date": m[4], "version": m[5],
                             "product_prefix": m[1]})
        return rows, meta
    rows = []
    with ThreadPoolExecutor(max_workers=6) as pool:
        for part, meta in pool.map(one, sorted(set(months))):
            rows.extend(part)
            indexes.append(meta)
    groups = {}
    for row in rows:
        groups.setdefault((row["satellite"], row["cadence_s"], row["date"]), []).append(row)
    for candidates in groups.values():
        winner = max(candidates, key=lambda x: (tuple(map(int, x["version"].split("-"))), x["product_prefix"] == "sci"))
        for row in candidates:
            row["selected_version"] = row is winner
    return {"selection": "highest numeric product version per satellite/cadence/day; no mixing", "indexes": indexes, "files": rows}


def catalogue(cache):
    path = fetch(CATALOGUE, cache)
    table = Table()
    table.feed(path.read_text())
    result = []
    for row in table.rows:
        if len(row) < 3 or not re.match(r"20\d\d\s+\d\d/\d\d\s+\d{4}", row[0]):
            continue
        try:
            start = datetime.strptime(row[0], "%Y %m/%d %H%M").replace(tzinfo=timezone.utc)
            peak = datetime.strptime(row[1], "%Y %m/%d %H%M").replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if 2017 <= start.year and start.isoformat() < "2026-10-01":
            result.append({"onset_utc": start.isoformat(), "peak_utc": peak.isoformat(),
                           "peak_gt10mev_pfu": float(row[2].replace(",", "")), "source_row": row})
    return {"source_url": CATALOGUE, "sha256": sha256(path), "rows": result}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--cache", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    result = inventory(args.cache)
    result["catalogue"] = catalogue(args.cache)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"files": len(result["files"]), "indexes": len(result["indexes"]),
                      "catalogue_events": len(result["catalogue"]["rows"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
