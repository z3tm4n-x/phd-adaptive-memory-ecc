"""One vector figure. Plot the coordinates actually tested, without interpolation."""
from fractions import Fraction
from io import BytesIO
from math import ceil

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import NullLocator


INK, FIXED, ERR = "#17303c", "#93501f", "#006b68"
VOLUME = {64:("o", "#505b94"), 128:("s", "#197799"), 256:("^", "#51702e")}
EPSILON = {"1/10":"10⁻¹","1/100":"10⁻²","1/1000":"10⁻³","1/10000":"10⁻⁴"}
SHORT = {"fixed":"П", "ladder":"Л", "overlap":"≈", "fixed_only":"П?", "excluded":"×"}
SIZES = [(64, "all", "64 · любые"), (128, "covered", "128 · ≥21 007 пар"),
         (256, "half", "256 · L/2")]


def mark(label, color, marker, filled=True):
    return Line2D([], [], ls="none", marker=marker, color=color, markersize=5.5,
                  markerfacecolor=color if filled else "white", label=label)


def costs(ax, data):
    for i, row in enumerate(data["primary"]):
        for y, lo, hi, ink, marker, certified in (
                (i-.17, row["fixed_lower_s"], row["fixed_upper_s"], FIXED, "s", True),
                (i+.17, row["ladder_lower_s"], row["ladder_upper_s"], ERR, "o",
                 row["decision"] not in ("fixed_only", "excluded"))):
            if hi is None:
                continue
            xs = [float(lo), float(hi)]
            ax.plot(xs, [y,y], lw=2, color=ink, marker=marker, markersize=4,
                    ls="-" if certified else "--", markerfacecolor=ink if certified else "white")
        ax.text(.98, i, SHORT[row["decision"]], ha="right", va="center", fontweight="bold",
                color=INK, transform=ax.get_yaxis_transform())
    for y in (3.5, 7.5):
        ax.axhline(y, color="#b0babc", lw=.8)
    ax.set_xscale("log")
    ax.set(xlim=(8e3, 2.9e8), ylim=(11.6,-.63),
           yticks=range(12), yticklabels=[f"{r['kib']}     {EPSILON[r['epsilon']]}" for r in data["primary"]])
    ax.set_xticks([1e4,1e5,1e6,1e7,1e8], ["10⁴","10⁵","10⁶","10⁷","10⁸"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.grid(axis="x", color="#d9dfe1")
    ax.set_title("Цена двух режимов на проектных картах", loc="left", pad=13)
    ax.set_ylabel("Объём, КиБ       Допуск за десять лет")
    ax.set_xlabel("Секунды защитного порта за десять лет")
    ax.legend(handles=[Line2D([],[],color=FIXED,marker="s",label="Постоянный"),
                       Line2D([],[],color=ERR,marker="o",label="Лестница")],
              loc="upper left", bbox_to_anchor=(.0,-.085), frameon=False, ncols=2)


def coordinates(ax, data):
    for row in data["primary"]:
        marker, col = VOLUME[row["kib"]]
        passed = row["decision"] not in ("excluded", "fixed_only")
        ax.scatter(float(row["u_upper"]), 1.2, marker=marker, s=47, edgecolor=col,
                   facecolor=col if passed else "white", zorder=4)
    for kib, (_, col) in VOLUME.items():
        r = next(r for r in data["primary"] if r["kib"]==kib)
        ax.vlines(float(r["u_test_lower"]), .87, 1.53, color=col, lw=1.5)
    for row in data["transverse"]:
        geo = row["scope"] == "geo"
        if geo and row["law"] == "compact_1p2":
            continue
        y = float(Fraction(row["m"]))
        m, col = ("s", VOLUME[128][1]) if geo else ("D", "#823c71")
        passed = row["decision"] == "ladder"
        ax.scatter(float(row["u_upper"]), y, marker=m, s=38, edgecolor=col,
                   facecolor=col if passed else "white", zorder=4)
        ax.vlines(float(row["u_test_lower"]), y-.22, y+.22, color=col, lw=1.2)
    ax.set_xscale("log")
    ax.set(xlim=(.00031,12), ylim=(.55,8.5), yticks=[1.2,2,4,5,8], yticklabels=["1,2","2","4","5","8"])
    ax.set_xticks([.001,.01,.1,1,10], ["0,001","0,01","0,1","1","10"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.grid(color="#e0e6e8", lw=.7)
    ax.set_xlabel("Доля допуска при непрерывном обходе, u⁺")
    ax.set_ylabel("Слов на частицу, m")
    ax.set_title("Проверенные сочетания нагрузки и кратности", loc="left", pad=12)
    handles = [mark(str(k)+" КиБ", color, m) for k,(m,color) in VOLUME.items()]
    handles.append(mark("Архив, 128 КиБ", "#823c71", "D"))
    ax.legend(handles=handles, loc="upper left", fontsize=8, ncols=1, frameon=False)


def classes(ax, data):
    rows = data["primary"] + data["map_and_archive"]
    for i, (kib, layout, _) in enumerate(SIZES):
        for dy, scope, marker, col in ((-.16, "geo", "o", "#245577"),(.16, "archive", "D", "#823c71")):
            r = next(x for x in rows if x["kib"]==kib and x["layout"]==layout and
                     x["scope"]==scope and x["epsilon"]=="1/1000")
            ratio = float(r["ratio_lower"])
            ax.plot(ratio, i+dy, marker=marker, color=col, ms=5)
            # All values are positive lower bounds. Truncate the published decimals.
            left, right = r["ratio_lower"].split(".")
            seconds = f"{ceil(Fraction(r['ladder_upper_s'])):,}".replace(",", " ")
            ax.annotate(f"≥{left},{right[:3]}\n≤{seconds} с", (ratio, i+dy), xytext=(6,0),
                        textcoords="offset points", va="center", fontsize=8, linespacing=1.08, color=col)
    ax.axvline(2, ls="--", color="#949b9c", lw=.8)
    ax.set(xlim=(0,18.7), ylim=(2.55,-.57), yticks=range(3), yticklabels=[x[2] for x in SIZES])
    ax.set_xticks([0,2,5,10,15])
    ax.grid(axis="x", color="#e0e6e8", lw=.7)
    ax.set_title("Один период для всего выбранного множества", loc="left", pad=11)
    ax.set_xlabel("Нижняя граница экономии, раз")
    ax.legend(handles=[mark("Весь ГСО","#245577","o"),mark("Все реконструкции","#823c71","D")],
              loc="lower left", bbox_to_anchor=(0,-.46), ncols=2, frameon=False, fontsize=8)


def draw(data):
    style = {"font.family":"DejaVu Sans","font.size":10,"svg.fonttype":"none",
             "svg.hashsalt":"t542-regime-map-v1","axes.spines.top":False,"axes.spines.right":False,
             "axes.edgecolor":"#a3adb2","text.color":INK,"axes.labelcolor":INK,"xtick.color":INK,
             "ytick.color":INK,"axes.titlecolor":INK,"axes.titleweight":"bold","axes.titlesize":11,
             "axes.axisbelow":True,"figure.facecolor":"white","axes.facecolor":"white"}
    with plt.rc_context(style):
        fig = plt.figure(figsize=(13.2, 9.0))
        grid = fig.add_gridspec(2,2, left=.09, right=.965, bottom=.205, top=.84,
                                width_ratios=(1.08,1), height_ratios=(1.36,.88),
                                hspace=.68, wspace=.42)
        costs(fig.add_subplot(grid[:,0]), data)
        coordinates(fig.add_subplot(grid[0,1]), data)
        classes(fig.add_subplot(grid[1,1]), data)
        fig.text(.032,.951,"Выбор режима защиты памяти на ГСО", fontsize=20, fontweight="bold")
        fig.text(.033,.912,"Десять лет  ·  CY62167GE30-45, встроенный код 32+6  ·  базовое управление I = X = 0",
                 fontsize=11, color="#42565f")
        fig.text(.033,.095,"Слева интервалы охватывают ожидаемую цену за срок. П, Л — доказан более дешёвый режим. "
                 "≈ — обе цены перекрываются. П? — подтверждён только постоянный. × — оба исключены.", fontsize=8.2)
        fig.text(.033,.066,"Справа вверху заполненный знак означает, что лестница выдерживает допуск. Черта — край "
                 "достаточного теста для данного закона и банка. Разные законы показаны отдельными точками.", fontsize=8.2)
        fig.text(.033,.037,"Справа внизу допуск 10⁻³, смесь 4/5 и 1/5. Рядом с отношением указан верх секунд лестницы. "
                 "На 64 и 128 КиБ отношение проверено покартово, на 256 КиБ задан разнос L/2.", fontsize=8.2)
        buffer = BytesIO()
        fig.savefig(buffer, format="svg", metadata={"Date":None, "Title":"Выбор режима защиты памяти на ГСО"})
        plt.close(fig)
        # Matplotlib adds padding at line breaks inside SVG path attributes.
        return b"\n".join(line.rstrip() for line in buffer.getvalue().splitlines()) + b"\n"
