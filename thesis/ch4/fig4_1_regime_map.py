"""Render thesis Figure 4.1 from the accepted decisions in the regime map."""

import json
from io import BytesIO
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


DIRECTORY = Path(__file__).resolve().parent
DATA = DIRECTORY.parents[1] / "experiments" / "t542-regime-map" / "map.json"
EPSILONS = (("1/10", "10⁻¹"), ("1/100", "10⁻²"),
            ("1/1000", "10⁻³"), ("1/10000", "10⁻⁴"))
VOLUMES = (64, 128, 256)
# Color only reinforces the cells where both admissibility and lower cost are proven.
STYLES = {
    "fixed": ("Постоянный", "#f6e9d8"),
    "ladder": ("Лестница", "#dceeea"),
    "overlap": ("Интервалы затрат\nпересекаются", "#f4f4f2"),
    "fixed_only": ("Подтверждён только\nпостоянный", "#ffffff"),
    "excluded": ("Оба режима\nисключены", "#e7e9ea"),
}


def draw():
    records = json.loads(DATA.read_text(encoding="utf-8"))["primary"]
    decisions = {(r["kib"], r["epsilon"]): r["decision"] for r in records}
    assert len(decisions) == len(records) == len(VOLUMES) * len(EPSILONS)

    style = {"font.family": "DejaVu Sans", "font.size": 9, "svg.fonttype": "none",
             "svg.hashsalt": "thesis-ch4-regime-decisions", "figure.facecolor": "white"}
    with plt.rc_context(style):
        figure, axes = plt.subplots(figsize=(160 / 25.4, 63 / 25.4))
        figure.subplots_adjust(left=.13, right=.995, top=.73, bottom=.025)
        axes.set(xlim=(0, 4), ylim=(3, 0))
        axes.set_axis_off()
        axes.text(2, -.88, "Допуск на накопление за десять лет", ha="center",
                  va="center", fontsize=10, fontweight="bold", clip_on=False)
        axes.text(-.26, -.29, "Объём,\nКиБ", ha="center", va="center", clip_on=False)
        for column, (_, short) in enumerate(EPSILONS):
            axes.text(column + .5, -.29, short, ha="center", va="center",
                      fontweight="bold", clip_on=False)
        for row, volume in enumerate(VOLUMES):
            axes.text(-.24, row + .5, str(volume), ha="center", va="center",
                      fontweight="bold", clip_on=False)
            for column, (epsilon, _) in enumerate(EPSILONS):
                decision = decisions[volume, epsilon]
                label, fill = STYLES[decision]
                axes.add_patch(Rectangle((column, row), 1, 1, facecolor=fill,
                                         edgecolor="#8d9699", linewidth=.75))
                axes.text(column + .5, row + .5, label, ha="center", va="center",
                          linespacing=1.16, fontsize=8.1, color="#172d35",
                          fontweight="bold" if decision in ("fixed", "ladder") else "normal")
        buffer = BytesIO()
        figure.savefig(buffer, format="svg", metadata={
            "Date": None,
            "Title": "Выбор режима с меньшей ожидаемой занятостью защитного порта",
            "Description": "Три проектные карты с половинами слова через полпрохода, "
                           "четыре допуска на накопление за десять лет на ГСО.",
        })
        plt.close(figure)
        lines = buffer.getvalue().splitlines()
        output = b"\n".join(line.rstrip() for line in lines) + b"\n"
        (DIRECTORY / "fig4_1_regime_map.svg").write_bytes(output)


if __name__ == "__main__":
    draw()
