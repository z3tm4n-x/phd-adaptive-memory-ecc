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
SHORT = {"fixed":"П", "ladder":"Л", "overlap":"∩", "fixed_only":"П?", "excluded":"×"}
SIZES = [(64, "all"), (128, "covered"), (256, "half")]


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
    ax.set_title("Затраты на проектных картах", loc="left", pad=9)
    ax.set_ylabel("Объём, КиБ   ·   Допуск", labelpad=-4)
    ax.set_xlabel("Занятость порта за десять лет, с")
    ax.legend(handles=[Line2D([],[],color=FIXED,marker="s",label="Постоянный"),
                       Line2D([],[],color=ERR,marker="o",label="Лестница")],
              loc="upper center", bbox_to_anchor=(.5,-.105), frameon=False, ncols=2,
              columnspacing=.8, handlelength=1.3)


def coordinates(ax, data):
    for row in data["primary"]:
        marker, col = VOLUME[row["kib"]]
        passed = row["decision"] not in ("excluded", "fixed_only")
        ax.scatter(float(row["u_upper"]), 1.2, marker=marker, s=20, edgecolor=col,
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
        ax.scatter(float(row["u_upper"]), y, marker=m, s=20, edgecolor=col,
                   facecolor=col if passed else "white", zorder=4)
        ax.vlines(float(row["u_test_lower"]), y-.27, y+.27, color=col, lw=1.2)
    ax.set_xscale("log")
    ax.set(xlim=(.00031,12), ylim=(.55,8.5), yticks=[1.2,2,4,5,8], yticklabels=["1,2","2","4","5","8"])
    ax.set_xticks([.001,.01,.1,1,10], ["0,001","0,01","0,1","1","10"])
    ax.xaxis.set_minor_locator(NullLocator())
    ax.grid(color="#e0e6e8", lw=.7)
    ax.set_xlabel("Доля допуска при непрерывном обходе, u⁺")
    ax.set_ylabel("Слов на частицу, m")
    ax.set_title("Кратность и видимость", loc="left", pad=9)
    handles = [mark(str(k)+" КиБ", color, m) for k,(m,color) in VOLUME.items()]
    handles.append(mark("Архив, 128 КиБ", "#823c71", "D"))
    ax.legend(handles=handles, loc="upper left", fontsize=8, frameon=False,
              handlelength=.8, handletextpad=.45, borderpad=.2, labelspacing=.25)


def classes(ax, data):
    rows = data["primary"] + data["map_and_archive"]
    for i, (kib, layout) in enumerate(SIZES):
        for dy, scope, marker, col in ((-.22, "geo", "o", "#245577"),(.22, "archive", "D", "#823c71")):
            r = next(x for x in rows if x["kib"]==kib and x["layout"]==layout and
                     x["scope"]==scope and x["epsilon"]=="1/1000")
            ratio = float(r["ratio_lower"])
            ax.plot(ratio, i+dy, marker=marker, color=col, ms=5)
            # All values are positive lower bounds. Truncate the published decimals.
            left, right = r["ratio_lower"].split(".")
            seconds = f"{ceil(Fraction(r['ladder_upper_s'])):,}".replace(",", " ")
            dx, align = (-4, "right") if ratio > 12 else (4, "left")
            ax.annotate(f"≥{left},{right[:3]}\n≤{seconds} с", (ratio, i+dy), xytext=(dx,0),
                        textcoords="offset points", ha=align, va="center", fontsize=8, linespacing=1.05, color=col)
    ax.axvline(2, ls="--", color="#949b9c", lw=.8)
    ax.set(xlim=(0,17), ylim=(2.68,-.68), yticks=range(3), yticklabels=[str(kib) for kib,_ in SIZES])
    ax.set_xticks([0,2,5,10,15])
    ax.grid(axis="x", color="#e0e6e8", lw=.7)
    ax.set_title("Экономия при допуске 10⁻³", loc="left", pad=8)
    ax.set_ylabel("Объём, КиБ")
    ax.set_xlabel("Нижняя граница экономии, раз")
    ax.legend(handles=[mark("Класс ГСО","#245577","o"),mark("Реконструкции","#823c71","D")],
              loc="upper center", bbox_to_anchor=(.5,-.27), ncols=2, frameon=False,
              fontsize=8, columnspacing=.8, handlelength=.9, handletextpad=.4)


def draw(data):
    style = {"font.family":["DejaVu Sans","Arial","sans-serif"],"font.size":8,"svg.fonttype":"none",
             "svg.hashsalt":"t542-regime-map-v1","axes.spines.top":False,"axes.spines.right":False,
             "axes.edgecolor":"#a3adb2","text.color":INK,"axes.labelcolor":INK,"xtick.color":INK,
             "ytick.color":INK,"axes.titlecolor":INK,"axes.titleweight":"bold","axes.titlesize":9,
             "axes.axisbelow":True,"figure.facecolor":"white","axes.facecolor":"white"}
    with plt.rc_context(style):
        # Size in the A4 manuscript. All tick labels and keys are at least 8 pt.
        fig = plt.figure(figsize=(160 / 25.4, 184 / 25.4))
        grid = fig.add_gridspec(2,2, left=.137, right=.975, bottom=.245, top=.87,
                                width_ratios=(1,1.13), height_ratios=(1.05,1),
                                hspace=.63, wspace=.39)
        costs(fig.add_subplot(grid[:,0]), data)
        coordinates(fig.add_subplot(grid[0,1]), data)
        classes(fig.add_subplot(grid[1,1]), data)
        fig.text(.015,.957,"Выбор режима защиты памяти на ГСО", fontsize=13, fontweight="bold")
        fig.text(.015,.925,"Десять лет  ·  CY62167GE30-45  ·  встроенный код 32+6  ·  I = X = 0", fontsize=8.5)
        fig.text(.015,.132,
                 "П — дешевле постоянный режим. Л — дешевле лестница. ∩ — интервалы затрат пересекаются.\n"
                 "П? — подтверждён только постоянный режим. × — оба режима исключены.\n"
                 "Пунктиром даны справочные затраты лестницы. Вверху справа черта — граница достаточного\n"
                 "теста. Закрашены точки, где тест пройден. Внизу справа для смеси 4/5 и 1/5 рядом с границей\n"
                 "экономии дан верх занятости лестницы. Для 64 КиБ учтены любые пары, для 128 КиБ —\n"
                 "не менее 21 007 полных пар, для 256 КиБ — разнос половин слова на полпрохода.",
                 fontsize=8, va="top", linespacing=1.26)
        buffer = BytesIO()
        fig.savefig(buffer, format="svg", metadata={"Date":None, "Title":"Выбор режима защиты памяти на ГСО"})
        plt.close(fig)
        # Matplotlib adds padding at line breaks inside SVG path attributes.
        return b"\n".join(line.rstrip() for line in buffer.getvalue().splitlines()) + b"\n"
