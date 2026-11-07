"""Retrieve original public inputs and verify the recorded bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import ssl
from tempfile import NamedTemporaryFile
from urllib.error import HTTPError, URLError
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


def download(spec, path):
    url = spec["url"]
    # Equivalent public routes to the same NASA S3 key or JAXA archive.
    alternate = url.replace("s3.us-east-1.amazonaws.com","s3.amazonaws.com")
    alternate = alternate.replace("https://darts.isas.jaxa.jp/pub/", "https://data.darts.isas.jaxa.jp/pub/")
    for attempt,route in enumerate((url,alternate,url)):
        try:
            with urlopen(route,timeout=30) as response:
                if not response.geturl().startswith("https://"):
                    raise ValueError("Expected an HTTPS archive response")
                data = response.read()
            break
        except HTTPError as error:
            if attempt == 2 or (error.code != 429 and error.code < 500):
                raise
        except (URLError,TimeoutError) as error:
            if attempt == 2 or isinstance(getattr(error,"reason",None),ssl.SSLCertVerificationError):
                raise
    if sha(data) != spec["sha256"]:
        raise ValueError(f"Downloaded bytes differ from pinned source: {path.name}")
    with NamedTemporaryFile(dir=path.parent,delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(data)
    try:
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("stage", choices=["predictors", "observation"])
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=True)
    if args.stage == "predictors":
        specs = PROTOCOL["sources"].values()
    else:
        observation = json.loads((HERE / "observation.json").read_text(encoding="utf-8"))
        specs = [observation, observation["cdf_crosscheck"]]
    for spec in specs:
        path = args.directory / spec["file"]
        if not path.exists():
            download(spec,path)
        verified(args.directory, spec)
        print(f"{path.name} {spec['sha256']}",flush=True)


if __name__ == "__main__":
    main()
