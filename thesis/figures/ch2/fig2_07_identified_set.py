"""Рисунок 2.7 — учебная модель: интервалы точных значений Q(T) при четырёх периодах очистки.

Показываются только рассчитанные точки: для каждого периода — вертикальный интервал
между точными значениями при q = 1/2 и q = 1/6; промежуточные периоды не интерполируются.
Данные: thesis/ch2/data/res001_exact.csv (точные значения по принятой формуле).
Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_07_identified_set.py
Выход: thesis/figures/ch2/fig2_07_identified_set.svg
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

root = Path(__file__).resolve().parents[3]
rows = list(csv.DictReader(open(root / "thesis/ch2/data/res001_exact.csv", encoding="utf-8")))
val = {(r["модель"], float(r["период"])): float(r["Q_точн"]) for r in rows}
periods = sorted({p for _, p in val})
fig, ax = plt.subplots(figsize=(14 * CM, 8 * CM))
for i, p in enumerate(periods):
    lo, hi = val[("J-A", p)], val[("J-B", p)]
    ax.vlines(p, lo, hi, color="black", lw=1.6, label="интервал точных значений" if i == 0 else None)
    ax.plot(p, hi, "s", color="black", ms=4.5, label="q = 1/6" if i == 0 else None)
    ax.plot(p, lo, "o", color="black", ms=4.5, mfc="white", label="q = 1/2" if i == 0 else None)
for eps in (0.15, 0.25, 0.35, 0.55):
    ax.axhline(eps, color="0.45", lw=0.6, ls=":")
    ax.text(5.0, eps, "$Q_{\\mathrm{доп}}$ = " + str(eps).replace(".", ","), va="center", fontsize=7.5)
ax.set_xscale("log", base=2)
ax.set_xticks(periods, [str(p).replace(".0", "").replace(".", ",") for p in periods])
ax.set_xlim(0.38, 9.5)
ax.set_ylim(0, 0.62)
ax.set_xlabel("период очистки, ед. модельного времени")
ax.set_ylabel("Q(T)")
ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.1f}".replace(".", ",")))
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
ax.legend(loc="lower right", bbox_to_anchor=(0.80, 0.01), frameon=False, fontsize=7.5)
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_07_identified_set"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
