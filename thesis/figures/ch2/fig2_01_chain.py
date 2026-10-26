"""Рисунок 2.1 — последовательность расчёта интенсивности сбоев памяти по ОСТ 134-1044-2007 (п. 5.2, рис. 5.1)
и РД 134-0139-2005 (схема, без числовых данных). Спектры протонов ЕРПЗ рассчитываются для орбиты отдельно;
функция прохождения в магнитосферу относится только к ГКЛ и СКЛ.

Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_01_chain.py
Выход: thesis/figures/ch2/fig2_01_chain.svg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

fig, ax = plt.subplots(figsize=(16 * CM, 6.4 * CM))
w, h = 3.0, 1.15


def box(x, y, title, note=None):
    ax.add_patch(plt.Rectangle((x, y), w, h, facecolor="0.92", edgecolor="black", lw=0.8))
    ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", fontsize=7.4)
    if note:
        ax.text(x + w / 2, y - 0.12, note, ha="center", va="top", fontsize=6.6)


def arrow(x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9))


yt, yb, ym = 2.75, 0.55, 1.65
box(0.0, yt, "ГКЛ и СКЛ\nза пределами\nмагнитосферы")
box(3.5, yt, "Прохождение\nв магнитосферу", "функция прохождения\nна орбиту КА")
box(0.0, yb, "Протоны ЕРПЗ\nна орбите КА", "по параметрам орбиты\nи времени полёта")
box(7.25, ym, "Прохождение\nчерез защиту", "спектры протонов\nи спектры ЛПЭ ТЗЧ")
box(10.75, ym, "Свёртка\nс сечениями", "формула (2.4)")
box(14.25, ym, "Интенсивность\nсбоев", "границы (2.1)–(2.3)")
arrow(3.0, yt + h / 2, 3.5, yt + h / 2)
arrow(6.5, yt + h / 2, 7.25, ym + h * 0.8)
arrow(3.0, yb + h / 2, 7.25, ym + h * 0.2)
arrow(10.25, ym + h / 2, 10.75, ym + h / 2)
arrow(13.75, ym + h / 2, 14.25, ym + h / 2)
ax.set_xlim(-0.1, 17.35)
ax.set_ylim(-0.05, 4.0)
ax.axis("off")
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_01_chain"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
