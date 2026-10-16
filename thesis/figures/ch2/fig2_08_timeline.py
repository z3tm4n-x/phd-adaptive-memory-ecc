"""Рисунок 2.8 — временная диаграмма последовательного контроля (схема, без числовых данных).

Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_08_timeline.py
Выход: thesis/figures/ch2/fig2_08_timeline.svg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

W, P, SLOT, T_PR = 6, 1.0, 0.1, 0.6          # схема: 6 слов, период P, проход короче периода
READ, WRITE = 0.035, 0.07                     # длительность операции без записи и с записью
y = {w: W - w for w in range(1, W + 1)}       # слово 1 сверху


def r(w, k):
    return k * P + (w - 1) * SLOT


hits = [(2, 0.32), (5, 0.25), (4, 0.45), (4, 0.85), (3, 1.45), (6, 1.52)]
writes = {(5, 0), (2, 1), (3, 2), (6, 2)}     # операции, в которых записывается исправление
signals = [(5, 0), (2, 1), (3, 2), (6, 2)]

fig, ax = plt.subplots(figsize=(16 * CM, 7.6 * CM))
for k in range(3):
    ax.axvspan(k * P, k * P + T_PR, color="0.93", lw=0)
    ax.text(k * P + T_PR / 2, W - 0.35, f"проход {k}", ha="center", va="bottom")
    for w in range(1, W + 1):
        t = r(w, k)
        dur = WRITE if (w, k) in writes else READ
        ax.add_patch(plt.Rectangle((t, y[w] - 0.16), dur, 0.32, color="0.25" if (w, k) in writes else "0.65", lw=0))
        ax.plot([t, t], [y[w] - 0.26, y[w] + 0.26], color="black", lw=0.9)
for w, s in hits:
    ax.plot(s, y[w], "o", color="black", ms=3.5)
for w, k in signals:
    ax.plot(r(w, k) + 0.035, y[w] + 0.38, "v", mfc="white", mec="black", ms=5)
ax.plot(0.85, y[4], "x", color="black", ms=8, mew=1.6)
for lab, (xx, yy) in {"а": (0.85, y[4]), "б": (1.45, y[3]), "в": (1.52, y[6])}.items():
    ax.text(xx + 0.035, yy + 0.2, lab, ha="left", va="bottom", fontsize=8, style="italic")
ax.annotate("", xy=(T_PR, -0.55), xytext=(0, -0.55), arrowprops=dict(arrowstyle="<->", lw=0.6))
ax.text(T_PR / 2, -0.5, "$T_{\\mathrm{пр}}$", ha="center", va="bottom")
ax.annotate("", xy=(r(1, 1), -1.05), xytext=(r(1, 0), -1.05), arrowprops=dict(arrowstyle="<->", lw=0.6))
ax.text(P / 2, -1.0, "$P$", ha="center", va="bottom")
ax.set_yticks([y[w] for w in range(1, W + 1)], [f"слово {w}" for w in range(1, W + 1)])
ax.set_xticks([])
ax.set_xlim(-0.05, 2.62)
ax.set_ylim(-1.2, W + 0.35)
ax.set_xlabel("время")
for s in ("top", "right"):
    ax.spines[s].set_visible(False)
leg = [plt.Line2D([], [], color="black", marker="|", ls="", ms=8, label="чтение слова"),
       plt.Rectangle((0, 0), 1, 1, color="0.65", label="операция без записи"),
       plt.Rectangle((0, 0), 1, 1, color="0.25", label="операция с записью исправления"),
       plt.Line2D([], [], color="black", marker="o", ls="", ms=3.5, label="новая ошибка"),
       plt.Line2D([], [], mfc="white", mec="black", marker="v", ls="", ms=5, label="сигнал исправления"),
       plt.Line2D([], [], color="black", marker="x", ls="", ms=6, mew=1.4, label="превышение")]
ax.legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=3, frameon=False)
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_08_timeline"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
