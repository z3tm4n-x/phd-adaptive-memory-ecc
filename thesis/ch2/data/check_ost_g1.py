#!/usr/bin/env python3
"""Сверка числового переноса таблицы Г.1 ОСТ 134-1044-2007 с копией стандарта.

Текст стандарта в репозиторий не копируется. Скрипт получает путь к копии
ОСТ в формате .docx, находит таблицу Г.1 («Среднегодовые значения чисел Вольфа
для среднего, максимального и минимального … циклов СА») и сравнивает столбец
среднего цикла за годы 1–10 с рядом, использованным в радиационной цепочке:
experiments/tNN-sepem-profiles/config.json, ключ wolf_v1_annual_mean_cycle,
в закреплённой версии PIN.

Повтор из корня репозитория (нужны python-docx и Git с объектом PIN):
    python3 thesis/ch2/data/check_ost_g1.py путь/к/ОСТ_134-1044-2007.docx
Код возврата 0 — совпадение; 1 — расхождение или таблица не найдена.
"""
import hashlib
import json
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

import docx  # python-docx

PIN = "140f8d36751f117cfc96969d7732f85456476a5d"
ROOT = Path(__file__).resolve().parents[3]
CFG = "experiments/tNN-sepem-profiles/config.json"


def main(path: str) -> int:
    raw = Path(path).read_bytes()
    print("копия ОСТ, SHA-256:", hashlib.sha256(raw).hexdigest())
    cfg = json.loads(subprocess.run(["git", "-C", str(ROOT), "show", f"{PIN}:{CFG}"],
                                    capture_output=True, check=True).stdout.decode("utf-8"))
    chain = [Decimal(str(x)) for x in cfg["wolf_v1_annual_mean_cycle"]]
    for table in docx.Document(path).tables:
        cells = [[c.text.strip() for c in row.cells] for row in table.rows]
        if not cells or "Год от начала солнечного цикла" not in cells[0][0]:
            continue
        rows = [r for r in cells if r and r[0][:2].strip().isdigit()]
        ost = {int(r[0].split()[0]): [Decimal(v.replace(",", ".")) for v in r[1:4]] for r in rows}
        mean = [ost[y][0] for y in range(1, len(chain) + 1)]
        print("годы 1–%d, средний цикл, ОСТ:  " % len(chain), [str(v) for v in mean])
        print("годы 1–%d, ряд цепочки:        " % len(chain), [str(v) for v in chain])
        print("сумма за годы 1–%d: ОСТ %s, цепочка %s" % (len(chain), sum(mean), sum(chain)))
        ok = mean == chain
        print("РЕЗУЛЬТАТ:", "совпадает" if ok else "РАСХОЖДЕНИЕ")
        return 0 if ok else 1
    print("таблица Г.1 не найдена")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
