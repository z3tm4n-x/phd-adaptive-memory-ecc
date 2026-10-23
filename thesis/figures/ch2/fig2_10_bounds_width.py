"""Рисунок 2.10 — относительная ширина между нижней и верхней оценками Q(T) в малых моделях.

Данные: thesis/ch2/data/ch2_numbers.csv, строки N2.4-{Б,С}{случай}-{L,Q,U}
(середины интервалов точных значений из принятых результатов проверок).
Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_10_bounds_width.py
Выход: thesis/figures/ch2/fig2_10_bounds_width.svg
"""
import csv
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

root = Path(__file__).resolve().parents[3]
val = {r["id"]: Decimal(r["значение_источника"])
       for r in csv.DictReader(open(root / "thesis/ch2/data/ch2_numbers.csv", encoding="utf-8"))
       if r["id"].startswith("N2.4-") and r["id"][-2:] in ("-L", "-Q", "-U")}
cases = [("4c0", "4/п/0"), ("4c5", "4/п/0,05"), ("4p0", "4/к/0"), ("4p5", "4/к/0,05"),
         ("8c0", "8/п/0"), ("8c5", "8/п/0,05"), ("8p0", "8/к/0"), ("8p5", "8/к/0,05")]


def width(svc, tag):
    q = val[f"N2.4-{svc}{tag}-Q"]
    return float(100 * (val[f"N2.4-{svc}{tag}-U"] - val[f"N2.4-{svc}{tag}-L"]) / q)


xs = range(len(cases))
fig, ax = plt.subplots(figsize=(15 * CM, 7.5 * CM))
ax.bar([x - 0.19 for x in xs], [width("Б", t) for t, _ in cases], width=0.36, color="0.75", edgecolor="black", lw=0.5,
       label="безусловная запись")
ax.bar([x + 0.19 for x in xs], [width("С", t) for t, _ in cases], width=0.36, color="0.35", edgecolor="black", lw=0.5,
       label="запись по сигналу")
ax.set_xticks(list(xs), [lab for _, lab in cases], fontsize=7.5)
ax.set_ylabel("$(U - Q^-)/Q(T)$, %")
ax.set_ylim(0, 75)
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0f}"))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(loc="upper left", frameon=False, fontsize=7.5)
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_10_bounds_width"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
