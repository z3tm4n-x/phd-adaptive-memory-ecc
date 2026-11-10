"""Print or check the six human-facing rows against their integer operation counts."""
import argparse
from decimal import Decimal
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
T = 315576000


def digits(value, places=0):
    return format(Decimal(value),f",.{places}f").replace(","," ").replace(".",",")


def amount(ns):
    seconds = Decimal(ns)/10**9
    return f"{digits(seconds,3)} ({digits(100*seconds/T,6)}%)"


def table():
    lines = ["| История | Шаг | Завершено проходов | Переключения (в частый) | Часто, с (% срока) | Защитные чтения слов | Исправляющие записи | Шина, с (% срока) |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    for name in ("SEPEM","East","West"):
        data = json.loads((HERE/(name.lower()+".json")).read_text(encoding="utf-8"))
        primary = data["pairs"][0]
        for rule in ("L/32L","4L"):
            row = primary[rule]
            assert row["complete_passes"] == row["started_passes"] == row["public_passes"]
            words = 65536
            l = 196*words
            if rule == "L/32L":
                cells, tail = divmod(row["fast_ns"],32*l)
                assert tail == 0 and row["to_rare"] == row["to_fast"]+1
                expected = (T*10**9-1)//(32*l)+1+31*cells
            else:
                expected = (T*10**9-1)//(4*l)+1
            assert row["complete_passes"] == expected and row["word_reads"] == words*expected
            assert row["protection_bus_ns"] == 48*row["word_reads"]+56*row["repair_writes"]
            switch = f'{digits(row["switches"])} ({digits(row["to_fast"])})' if row["switches"] else "0"
            fields = [name if name == "SEPEM" else "GOES "+name,rule,digits(row["complete_passes"]),
                      switch,amount(row["fast_ns"]) if row["fast_ns"] is not None else "—",
                      digits(row["word_reads"]),digits(row["repair_writes"]),amount(row["protection_bus_ns"])]
            lines.append("| "+" | ".join(fields)+" |")
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check",action="store_true")
    if parser.parse_args().check:
        if table() not in (HERE/"README.md").read_text(encoding="utf-8"):
            raise SystemExit("Table differs from published rows")
        print("Six table rows match the operation counts.")
    else:
        print(table())
