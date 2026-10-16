"""Рисунок 2.9 — окна наблюдения слов при последовательном контроле (схема, без числовых данных).

Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_09_windows.py
Выход: thesis/figures/ch2/fig2_09_windows.svg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

W, SLOT = 6, 0.1
y = {w: W - w for w in range(1, W + 1)}

fig, axs = plt.subplots(2, 1, figsize=(16 * CM, 10.5 * CM), sharex=True)
for ax, starts, title in ((axs[0], [0.0, 1.0, 2.0], "а) постоянный период $P$"),
                          (axs[1], [0.0, 1.0, 3.0], "б) период увеличен после прохода 1: $P_2 = 2P_1$")):
    for k, t0 in enumerate(starts):
        ax.axvspan(t0, t0 + W * SLOT, color="0.93", lw=0)
        ax.text(t0 + W * SLOT / 2, W - 0.4, f"проход {k}", ha="center", va="bottom")
    for w in range(1, W + 1):
        reads = [t0 + (w - 1) * SLOT for t0 in starts]
        for t in reads:
            ax.plot([t, t], [y[w] - 0.27, y[w] + 0.27], color="black", lw=0.9)
        ax.add_patch(plt.Rectangle((reads[0], y[w] - 0.13), reads[1] - reads[0], 0.26, fill=False, hatch="////",
                                   lw=0.5, ec="0.35"))
        ax.add_patch(plt.Rectangle((reads[1], y[w] - 0.13), reads[2] - reads[1], 0.26, fill=False, hatch="....",
                                   lw=0.5, ec="0.35"))
    ax.set_yticks([y[w] for w in range(1, W + 1)], [f"слово {w}" for w in range(1, W + 1)])
    ax.set_ylim(-0.7 if ax is axs[0] else -1.6, W + 0.2)
    ax.set_title(title, loc="left", fontsize=8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
t_star = 1.25
axs[0].axvline(t_star, ls="--", color="black", lw=0.7)
axs[0].text(2.68, y[3], "момент $t$ (штриховая\nлиния): слова 1–3\nуже прочитаны\nв проходе 1,\nслова 4–6 — нет", va="center")
axs[1].text(0.0, -1.5, "окна прохода 2 вдвое длиннее: при постоянной интенсивности\n"
              "вдвое больше и ожидаемое число касаний в них", va="bottom")
axs[1].set_xticks([])
axs[1].set_xlim(-0.05, 3.75)
axs[1].set_xlabel("время")
leg = [plt.Line2D([], [], color="black", marker="|", ls="", ms=8, label="чтение слова"),
       plt.Rectangle((0, 0), 1, 1, fill=False, hatch="////", ec="0.35", lw=0.5, label="окно, проверяемое в проходе 1"),
       plt.Rectangle((0, 0), 1, 1, fill=False, hatch="....", ec="0.35", lw=0.5, label="окно, проверяемое в проходе 2")]
axs[1].legend(handles=leg, loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_09_windows"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
