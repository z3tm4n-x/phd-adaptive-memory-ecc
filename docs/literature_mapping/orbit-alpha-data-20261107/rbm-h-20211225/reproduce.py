"""Fetch missing pinned files and verify the frozen forecast and its held-out score."""
import argparse
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory",type=Path,help="directory for original public data")
    args = parser.parse_args()
    data = str(args.directory.resolve())
    stages = (("data.py","predictors"),("forecast.py","--check"),
              ("data.py","observation"),("score.py","--check"),("archive_check.py","--check"))
    for name,flag in stages:
        subprocess.run([sys.executable,"-X","utf8","-B",str(HERE/name),data,flag],check=True)
    print("PASS: original sources, pre-observation forecast, both signs and threshold table.")


if __name__ == "__main__":
    main()
