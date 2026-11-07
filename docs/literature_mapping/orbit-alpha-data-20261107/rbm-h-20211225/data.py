"""Retrieve original public inputs and verify the recorded bytes."""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen

HERE = Path(__file__).resolve().parent
PROTOCOL = json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verified(directory, spec):
    path = directory / spec["file"]
    if sha(path.read_bytes()) != spec["sha256"]:
        raise ValueError(f"Unexpected source digest: {path}")
    return path


def output(name, text, check):
    path = HERE / name
    if check:
        if path.read_text(encoding="utf-8") != text:
            raise ValueError(f"Reproduction differs: {name}")
    else:
        path.write_text(text, encoding="utf-8", newline="\n")


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("stage", choices=["predictors", "observation"])
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.stage == "predictors":
        specs = PROTOCOL["sources"].values()
    else:
        specs = [json.loads((HERE / "observation.json").read_text(encoding="utf-8"))]
    for spec in specs:
        path = args.directory / spec["file"]
        if not path.exists():
            with urlopen(spec["url"], timeout=60) as response:
                data = response.read()
            if sha(data) != spec["sha256"]:
                raise ValueError(f"Downloaded bytes differ from pinned source: {path.name}")
            path.write_bytes(data)
        verified(args.directory, spec)
        print(f"{path.name} {spec['sha256']}")


if __name__ == "__main__":
    main()
