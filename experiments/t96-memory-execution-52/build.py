#!/usr/bin/env python3
"""Build CXXRTL from the unmodified Git blob and copy only reached, settled state."""
import argparse
import hashlib
import os
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
RTL = HERE.parent / "native-example-20261111" / "native8.sv"
BLOB = "27f651fcea5b8ef677ccbad13fcfbb9f502c4296"


def build(build_dir, include):
    source = RTL.read_bytes().replace(b"\r\n", b"\n")
    if hashlib.sha1(b"blob " + str(len(source)).encode() + b"\0" + source).hexdigest() != BLOB:
        raise ValueError("native8 differs from the reviewed RTL")
    if not (include / "cxxrtl" / "cxxrtl.h").is_file():
        raise ValueError("set CXXRTL_INCLUDE to the directory containing cxxrtl/cxxrtl.h")
    build_dir.mkdir(parents=True, exist_ok=True)
    for variant in (0, 1):
        subprocess.run(["yosys", "-Q", "-q", "-p",
                        f'read_verilog -sv "{RTL}"; chparam -set CHECK_LOCAL {variant} native8; '
                        'prep -top native8; write_cxxrtl dut.cc'], cwd=build_dir, check=True)
        body = (build_dir / "dut.cc").read_text().split("struct p_native8 : public module {", 1)[1]
        body = body.split("p_native8(", 1)[0]
        # CXXRTL disallows ordinary copies of a wire. Include both halves of
        # every retained wire and all values (including prev_clk and inputs).
        # Reject unsupported state types instead of partially restoring them.
        members = re.findall(r"\b(value|wire)<\d+>\s+(\w+);", body)
        for line in body.splitlines():
            if re.search(r"\b(memory|std::vector|std::unique_ptr|bool)\b.*;\s*$", line) and "return" not in line:
                raise ValueError(f"unhandled generated state: {line}")
        if not members or len(dict((name, kind) for kind, name in members)) != len(members):
            raise ValueError("unrecognized CXXRTL model")
        copy, equal = [], []
        for kind, name in members:
            for suffix in ((".curr", ".next") if kind == "wire" else ("",)):
                field = name + suffix
                copy.append(f"dst.{field}=src.{field};")
                equal.append(f"std::equal(std::begin(dst.{field}.data), "
                             f"std::end(dst.{field}.data), std::begin(src.{field}.data))")
        (build_dir / "snapshot.h").write_text(
            "static void restore(Top &dst, const Top &src) {\n" + "\n".join(copy) + "\n}\n"
            + "static bool equal_state(const Top &dst, const Top &src) { return\n"
            + " &&\n".join(equal) + "; }\n")
        subprocess.run(["g++", "-O3", "-std=c++17", "-I", str(include), "-I", str(build_dir),
                        str(HERE / "pins.cc"), "-o", str(build_dir / f"pins{variant}")], check=True)
        print(f"CHECK_LOCAL={variant}: {len(members)} generated state fields", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    parser.add_argument("--include", type=Path, default=os.environ.get("CXXRTL_INCLUDE",
                        "/usr/share/yosys/include/backends/cxxrtl/runtime"))
    args = parser.parse_args()
    build(args.directory.resolve(), args.include.resolve())
