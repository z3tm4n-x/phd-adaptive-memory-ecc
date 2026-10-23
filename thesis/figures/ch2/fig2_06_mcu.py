"""Рисунок 2.6 — двухклеточный сбой при разном размещении разрядов слов (схема, без числовых данных).

Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_06_mcu.py
Выход: thesis/figures/ch2/fig2_06_mcu.svg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

CELLS = 16
HIT = (5, 6)                                   # две соседние ячейки, затронутые одной частицей
layouts = {
    "а) разряды слова расположены подряд": [c // 4 for c in range(CELLS)],
    "б) разряды четырёх слов чередуются": [c % 4 for c in range(CELLS)],
}
shades = ["1.0", "0.85", "0.65", "0.45"]

fig, axs = plt.subplots(2, 1, figsize=(16 * CM, 6.2 * CM))
for ax, (title, words) in zip(axs, layouts.items()):
    for c, w in enumerate(words):
        ax.add_patch(plt.Rectangle((c, 0), 1, 1, facecolor=shades[w], edgecolor="black", lw=0.6))
        ax.text(c + 0.5, 0.5, f"{w}", ha="center", va="center", fontsize=8)
    ax.add_patch(plt.Rectangle((HIT[0] + 0.06, 0.06), len(HIT) - 0.12, 0.88, fill=False, lw=2.2, ec="black"))
    errs = {}
    for c in HIT:
        errs[words[c]] = errs.get(words[c], 0) + 1
    note = "; ".join(f"слово {w}: {n} ошибк{'а' if n == 1 else 'и'}" for w, n in sorted(errs.items()))
    ax.text(CELLS + 0.4, 0.5, note, va="center", fontsize=8)
    ax.set_title(title, loc="left", fontsize=8)
    ax.set_xlim(-0.1, CELLS + 7.2)
    ax.set_ylim(-0.15, 1.15)
    ax.axis("off")
axs[1].text(0, -0.55, "цифра в ячейке — номер слова; рамка — ячейки, инвертированные одной частицей", fontsize=7.5, va="top")
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_06_mcu"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
