"""Рисунок 2.1 — последовательность расчёта частоты сбоев памяти по ОСТ 134-1044-2007 (рис. 5.1) и РД 134-0139-2005 (схема).

Повтор из корня репозитория: python3 thesis/figures/ch2/fig2_01_chain.py
Выход: thesis/figures/ch2/fig2_01_chain.svg
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import CM, plt, save  # noqa: E402

boxes = [
    ("Спектры ЗЧ\nв МКП и ЕРПЗ", "модели ГКЛ, СКЛ\nи ЕРПЗ; параметры\nорбиты и время"),
    ("Прохождение\nв магнитосферу", "функция\nпрохождения ГКЛ\nи СКЛ на орбиту"),
    ("Прохождение\nчерез защиту", "спектры протонов\nи спектры ЛПЭ ТЗЧ\nза защитой"),
    ("Свёртка\nс сечениями", "ТЗЧ — по ЛПЭ,\nпротоны — по\nэнергии; (2.4)"),
    ("Частота\nсбоев памяти", "фон, пик и\nнадфоновое число;\n(2.1)–(2.3)"),
]
fig, ax = plt.subplots(figsize=(16 * CM, 4.8 * CM))
w, h, gap = 2.6, 1.3, 0.55
for i, (title, note) in enumerate(boxes):
    x = i * (w + gap)
    ax.add_patch(plt.Rectangle((x, 1.6), w, h, facecolor="0.92", edgecolor="black", lw=0.8))
    ax.text(x + w / 2, 1.6 + h / 2, title, ha="center", va="center", fontsize=8)
    ax.text(x + w / 2, 1.4, note, ha="center", va="top", fontsize=6.8)
    if i < len(boxes) - 1:
        ax.annotate("", xy=(x + w + gap - 0.05, 1.6 + h / 2), xytext=(x + w + 0.05, 1.6 + h / 2),
                    arrowprops=dict(arrowstyle="-|>", color="black", lw=0.9))
ax.set_xlim(-0.1, len(boxes) * (w + gap) - gap + 0.1)
ax.set_ylim(0.25, 3.05)
ax.axis("off")
fig.tight_layout()
out = Path(__file__).resolve().parent / "fig2_01_chain"
save(fig, str(out), preview=sys.argv[1] if len(sys.argv) > 1 else None)
