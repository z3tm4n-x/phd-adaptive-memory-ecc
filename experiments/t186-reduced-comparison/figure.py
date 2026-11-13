"""One scientific figure from the published ledgers. No resimulation."""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FuncFormatter, NullLocator

HERE = Path(__file__).resolve().parent
results = json.loads((HERE / "result.json").read_bytes())["profiles"]
fig, axes = plt.subplots(1, 3, figsize=(11.5, 5.35), sharey=True)
fig.subplots_adjust(left=.077, right=.985, top=.79, bottom=.25, wspace=.09)
fig.suptitle("Первое превышение на стенде из 16 слов", x=.076, ha="left", y=.975,
             fontsize=19, fontweight="bold", color="#1c2a34")
fig.text(.078, .87, "131 072 общих траекторий на профиль   ·   допуск 0,001 за указанный срок",
         fontsize=11, color="#43545d")
for ax, (name, heading) in zip(axes, (("class_plateau", "Начальное плато  ·  10 лет"),
                                     ("sepem", "SEPEM 1996–2006  ·  10 лет"),
                                     ("stress", "Два импульса  ·  6 с"))):
    # A linear neighbourhood includes exact zeros; other decades are logarithmic.
    ax.set_yscale("symlog", linthresh=1e-9, linscale=.72)
    ax.set_ylim(-1.1e-9, .28)
    ax.set_xlim(-.48, 1.55)
    ax.set_title(heading, fontsize=12, pad=9)
    ax.axhline(1e-3, color="#875da1", linewidth=1.25, ls=(0,(3.2,2.7)))
    for x, method in enumerate(("fixed","ladder")):
        row = results[name]["rows"][method]
        q = row["frequency"]
        lo, hi = row["cp95"]
        ax.errorbar(x-.065, q, yerr=[[q-lo],[hi-q]], fmt="o", color="#18766f", lw=1.8,
                    ms=6, capsize=4, zorder=4)
        ax.plot(x+.13, row["q_upper"], "^", ms=8, color="#bc561f", zorder=4)
        if q == 0:
            ax.annotate("0 / 131 072", (x-.065, 0), xytext=(0,-12),
                        textcoords="offset points", ha="center", fontsize=8, color="#155e58")
        else:
            ax.annotate(f"{row['first']:,}".replace(","," "), (x-.065, q), xytext=(-6,8),
                        textcoords="offset points", ha="right", fontsize=8, color="#155e58")
    ax.set_xticks([0,1], ["Постоянный","Лестница"])
    ax.set_axisbelow(True)
    ax.grid(axis="y", linewidth=.65, color="#d9e0e2")
    ax.spines[["top","right"]].set_visible(False)
    ax.spines[["bottom","left"]].set_color("#afbabe")
    ax.tick_params(axis="both", length=0, pad=6)
axes[0].set_ylabel("Вероятность за срок", labelpad=9)
ticks = [0,1e-9,1e-7,1e-5,1e-3,1e-1]
labels = ["0","10⁻⁹","10⁻⁷","10⁻⁵","10⁻³","10⁻¹"]
axes[0].yaxis.set_major_locator(FixedLocator(ticks))
axes[0].yaxis.set_major_formatter(FuncFormatter(lambda y, _: dict(zip(ticks, labels)).get(y,"")))
axes[0].yaxis.set_minor_locator(NullLocator())
fig.legend(handles=[Line2D([], [], lw=1.8, marker="o", color="#18766f", label="Частота и двусторонний 95%-й ДИ"),
                    Line2D([], [], lw=0, marker="^", color="#bc561f", label="Аналитический верх"),
                    Line2D([], [], lw=1.25, ls="--", color="#875da1", label="Допуск")],
           loc="lower left", bbox_to_anchor=(.063,.092), ncol=3, frameon=False, fontsize=10)
fig.text(.078,.065,"Для нулевых строк односторонний верх 95% равен 2,286·10⁻⁵. "
         "Шкала линейна у нуля, логарифмическая выше 10⁻⁹.", fontsize=9, color="#43545d")
fig.savefig(HERE/"probability.png", dpi=160, facecolor="white", metadata={"Software":"Matplotlib"})
plt.close(fig)
