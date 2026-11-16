"""Рисунок 3.1. Границы наблюдаемой истории и интервалы одной дополнительной пары.

Из корня репозитория: python thesis/figures/ch3/fig3_01_history_pairs.py
Дополнительно передайте --preview путь.png, чтобы просмотреть растровую копию.
Верхняя и нижняя части схематичны. Положения концов отвечают формулам §§3.3–3.4.
"""
import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def draw():
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9.4,
        "svg.fonttype": "none", "svg.hashsalt": "thesis-fig3-01",
        "hatch.linewidth": 0.6,
    })
    fig = plt.figure(figsize=(9.0, 6.35))
    ax = fig.add_axes((0.02, 0.02, 0.96, 0.96), xlim=(0, 100), ylim=(0, 100))
    ax.set_axis_off()
    ink, blue, gray = "#222c35", "#18566a", "#626971"

    def label(x, y, msg, ha="left", **fmt):
        ax.text(x, y, msg, ha=ha, va="center", color=ink, **fmt)

    def stroke(x0, x1, y0, y1, color=ink, **fmt):
        ax.plot([x0, x1], [y0, y1], color=color, lw=0.9, **fmt)

    def dot(x, y, closed, color=ink):
        ax.plot(x, y, marker="o", markersize=4.4, markeredgecolor=color,
                markeredgewidth=1.1, markerfacecolor=color if closed else "white",
                zorder=5)

    def bar(left, right, y, height, fill, edge, hatch=None):
        ax.add_patch(Rectangle((left, y), right-left, height,
                               facecolor=fill, edgecolor=edge,
                               linewidth=0.85, hatch=hatch))

    label(1, 95, "а   Накопление отчётов до решения", fontsize=12.0, weight="bold")
    gates = [5.5, 29.5, 53.5, 77.5]
    axis_y = 76
    ax.annotate("", xy=(97.5, axis_y), xytext=(3, axis_y),
                arrowprops={"arrowstyle": "->", "color": ink, "lw": 0.9})
    for index, gate in enumerate(gates):
        stroke(gate, gate, 74.4, 81.0)
        bar(gate, gate+3.1, 75.2, 1.6, "#344d5a", ink)
        label(gate-0.6, 85.2, f"j − {3-index}" if index < 3 else "j",
              ha="center", fontsize=9.6)
        if index < 3:
            label(gate+12, 79.6, r"$A_*$", ha="center", fontsize=10)
    label(95.8, 72.7, "время", ha="right", fontsize=8.5)

    label(2.0, 89.5, "Обязательные проходы выделены на оси. Показан первый порог, три общих интервала.",
          fontsize=9.3)
    left, right, decision = 10.4, 75.8, 83.1
    stroke(left, left, 72.3, 64.0, color=gray, linestyle=":")
    stroke(right, right, 74.5, 64.0, color=gray, linestyle=":")
    stroke(left, right, 64.9, 64.9, color=blue)
    dot(left, 64.9, True, blue)
    dot(right, 64.9, True, blue)
    label((left+right)/2, 68.3, r"Время отбора частиц $I_{jr}=[\ell_{jr},\,b_j]$", ha="center")
    label(left, 60.4, r"$\ell_{jr}$", ha="center")
    label(right, 60.4, r"$b_j$", ha="center")
    stroke(decision, decision, 75.1, 67.8, color=gray, linestyle=":")
    dot(decision, 67.8, True)
    label(84.2, 68.0, r"$t_j$  решение", fontsize=9.2)
    label(3, 54.2, "Отбор начинается после срока отчёта левого прохода и заканчивается к самому раннему",
          fontsize=9.2)
    label(3, 50.5, "возможному началу правого. Его полный отчёт учитывается при решении.", fontsize=9.2)

    stroke(1, 99, 46.8, 46.8, color="#c8ced0")
    label(1, 42.5, "б   Два попадания по разные стороны пропущенного посещения",
          fontsize=11.8, weight="bold")
    a, split, after, end = 10.4, 45.0, 51.0, 85.6
    for x in (a, split, after, end):
        stroke(x, x, 34.8, 18.1, color=gray, linestyle=":", zorder=0)
    bar(a, after, 32.9, 1.7, "#e6e8e9", ink)
    bar(split, end, 29.6, 1.7, "#e6e8e9", ink)
    label((a+split)/2, 37.2, "Первый короткий интервал", ha="center", fontsize=8.9)
    label((after+end)/2, 33.5, "Второй короткий интервал", ha="center", fontsize=8.9)
    bar(split, after, 20.4, 6.0, "#f2f2f2", gray, hatch="////")
    stroke(a, split, 23.5, 23.5, color=blue)
    stroke(after, end, 23.5, 23.5, color=blue)
    for x, closed in [(a, True), (split, False), (after, False), (end, True)]:
        dot(x, 23.5, closed, blue)
    label((a+split)/2, 26.6, r"$B_1$  первое попадание", ha="center", fontsize=9.2)
    label((after+end)/2, 26.6, r"$B_2$  второе попадание", ha="center", fontsize=9.2)
    label(a, 17.3, r"$a$", ha="center")
    label(split-0.7, 17.3, r"$a+p$", ha="right")
    label(after+0.7, 17.3, r"$a+p+d_E$", ha="left")
    label(end, 17.3, r"$a+2p+d_E$", ha="center")

    time_choice = 32.8
    ax.annotate("", xy=(time_choice, 23.2), xytext=(time_choice, 15.65),
                arrowprops={"arrowstyle": "-|>", "color": ink, "lw": 0.8})
    label(time_choice, 14.05, r"$t_j$  решение при ранней фазе слова", ha="center", fontsize=8.5)
    label(3, 10.1, r"Штриховка — перекрытие ширины $d_E$, учтённое короткими интервалами.",
          fontsize=9.2)
    label(3, 6.4, r"Для одного слова $a\geq b_j$, обе полосы длины $p$ лежат после истории $I_{jr}$.",
          fontsize=9.2)
    label(3, 2.3, "Закрашенная точка включает конец интервала, незакрашенная исключает. Масштаб условный.",
          fontsize=8.8)
    return fig


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    args = parser.parse_args()
    figure = draw()
    svg_path = Path(__file__).with_suffix(".svg")
    figure.savefig(svg_path, metadata={"Date": None})
    # Matplotlib leaves spaces before newlines in path data; SVG treats both as separators.
    svg_lines = svg_path.read_text(encoding="utf-8").splitlines()
    svg_path.write_text("\n".join(line.rstrip() for line in svg_lines) + "\n",
                        encoding="utf-8", newline="\n")
    if args.preview:
        figure.savefig(args.preview, dpi=150)
    plt.close(figure)
