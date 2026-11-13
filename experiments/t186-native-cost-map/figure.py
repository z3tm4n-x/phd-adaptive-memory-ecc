"""Draw the cost intervals and the tested (u, m) coordinates from result.json."""
import json
from fractions import Fraction
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


HERE = Path(__file__).resolve().parent
DATA = json.loads((HERE/"result.json").read_bytes())
ROWS = DATA["rows"]
FIXED, ERR, MUTED = "#965019", "#006969", "#525b63"
VOLUMES = ("0,0625", "0,125", "0,25")
GROUP_COLORS = ("#534784", "#176a94", "#36703a")
DECISION = {"fixed":"П", "ERR":"Л", "open":"?", "excluded":"×"}
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                     "axes.spines.right":False,"axes.spines.top":False,
                     "axes.edgecolor":"#899098","xtick.color":"#344049","ytick.color":"#344049",
                     "figure.facecolor":"white","axes.facecolor":"white","axes.titleweight":"bold"})


def interval(ax, y, lo, hi, color, marker, passed):
    lo,hi = float(lo),float(hi)
    ax.plot([lo,hi],[y,y],color=color,ls="-" if passed else "--",lw=2)
    ax.plot([lo,hi],[y,y],ls="none",marker=marker,markersize=4.8,
            markerfacecolor=color if passed else "white",markeredgecolor=color)


def cost_panel(ax, rows, labels):
    for i,r in enumerate(rows):
        fixed, ladder = r["fixed"], r["ladder"]
        cand = fixed["candidate"]
        if cand:
            interval(ax,i-.16,fixed["s_lower"],cand["s_upper"],FIXED,"s",True)
        else:
            plain = fixed["continuous_tariff"]
            interval(ax,i-.16,plain["s_lower"],plain["s_upper"],FIXED,"s",False)
        interval(ax,i+.16,ladder["s_lower"],ladder["s_upper"],ERR,"o",r["ladder_pass"])
        ax.text(.985,i,DECISION[r["choice"]],transform=ax.get_yaxis_transform(),
                va="center",ha="right",fontweight="bold",color="#253944",fontsize=10)
    ax.set_yscale("linear")
    ax.set_xscale("log")
    ax.set(xlim=(9e3,2.8e8),ylim=(len(rows)-.38,-.62),yticks=range(len(labels)),yticklabels=labels)
    ax.set_xticks([1e4,1e5,1e6,1e7,1e8])
    ax.tick_params(axis="y",length=0,pad=6)
    ax.grid(axis="x",which="major",color="#d4d9dc",lw=.7)
    ax.set_axisbelow(True)
    ax.set_xlabel("Секунды защитного порта за десять лет")


def coordinates(ax):
    # All three primary series have exactly the same m; keep true data locations.
    ax.set_xscale("log")
    for idx,marker in enumerate(("o","s","^")):
        group = ROWS[4*idx:4*idx+4]
        color = GROUP_COLORS[idx]
        m = 1.2
        for r in group:
            ax.scatter(float(r["u_upper"]),m,s=42,marker=marker,edgecolor=color,
                       facecolor=color if r["ladder_pass"] else "white",linewidth=1.2,zorder=4)
        x = float(group[0]["u_test_boundary_lower"])
        ax.vlines(x,m-.34,m+.34,color=color,lw=1.8)
    symbol = {"geo":("o","#333b43"),"reconstructions":("D","#865779")}
    transverse = [r for r in ROWS if r["words"]==32768 and r["epsilon"]=="1/1000"]
    for r in transverse:
        m = float(Fraction(r["m"]))
        if m==1.2 and r["scope"]=="geo":
            continue
        marker,color = symbol[r["scope"]]
        ax.scatter(float(r["u_upper"]),m,s=43,marker=marker,edgecolor=color,
                   facecolor=color if r["ladder_pass"] else "white",linewidth=1.2,zorder=4)
        x = float(r["u_test_boundary_lower"])
        ax.vlines(x,m-.24,m+.24,color=color,lw=1.7)
    ax.set(xlim=(.00032,12),ylim=(.35,8.7),yticks=[1.2,2,4,5,8],
           yticklabels=["1,2","2","4","5","8"])
    ax.set_xticks([.001,.01,.1,1,10],["0,001","0,01","0,1","1","10"])
    ax.grid(color="#e1e5e7",lw=.7)
    ax.set_axisbelow(True)
    ax.set_xlabel("Доля допуска при непрерывном обходе, u")
    ax.set_ylabel("Слов на частицу, m")
    controls = [Line2D([],[],ls="none",marker=shape,color=c,markersize=5,label=v+" МиБ")
                for shape,c,v in zip(("o","s","^"),GROUP_COLORS,VOLUMES)]
    controls += [Line2D([],[],ls="none",marker=s,color=c,markersize=5,label=l)
                 for (s,c),l in zip(symbol.values(),("Срез ГСО","Реконструкции"))]
    ax.legend(handles=controls,loc="upper left",fontsize=8.2,frameon=True,framealpha=1,
              edgecolor="#e7ebed",ncol=1)


def main():
    fig = plt.figure(figsize=(13.6,10.4))
    gs = fig.add_gridspec(2,2,width_ratios=(1.22,1),height_ratios=(1,.93))
    left = fig.add_subplot(gs[:,0])
    right = fig.add_subplot(gs[0,1])
    axes = fig.add_subplot(gs[1,1])
    fig.subplots_adjust(left=.125,right=.98,top=.85,bottom=.11,wspace=.39,hspace=.47)
    fig.text(.025,.96,"Постоянный контроль и лестница по ERR",fontsize=20,
             va="top",fontweight="bold",color="#172c37")
    fig.text(.026,.914,"CY62167GE30-45  ·  встроенный SEC 32+6  ·  замкнутые карты адресов  ·  I = X = 0",
             fontsize=11,color=MUTED)
    left.set_title("Весь класс ГСО, смесь 4/5 и 1/5",loc="left",pad=14)
    powers = ("10⁻¹","10⁻²","10⁻³","10⁻⁴")
    labels = [f"{VOLUMES[i//4]}    {powers[i%4]}" for i in range(12)]
    cost_panel(left,ROWS[:12],labels)
    left.set_ylabel("Полезные МиБ     Допуск на накопление",labelpad=9)
    for boundary in (3.5,7.5):
        left.axhline(boundary,color="#a7b1b6",lw=.85)
    handles = [Line2D([],[],color=FIXED,marker="s",label="Постоянный период"),
               Line2D([],[],color=ERR,marker="o",label="Лестница по ERR")]
    fig.legend(handles=handles,loc="upper right",bbox_to_anchor=(.985,.928),borderaxespad=0,
               frameon=False,ncol=2,fontsize=9.5)
    right.set_title("Реконструкции, 0,125 МиБ и допуск 10⁻³",loc="left",pad=14)
    cost_panel(right,ROWS[-5:],["Смесь","Два равномерных","4 соседних","5 соседних","8 соседних"])
    axes.set_title("Граница достаточного условия для лестницы",loc="left",pad=10)
    coordinates(axes)
    fig.text(.025,.046,"П — дешевле постоянный, Л — лестница, ? — выбор открыт, × — оба режима исключены. "
             "Отрезок показывает границы затрат. Пунктир — цена исполнения без подтверждённого допуска.",
             fontsize=8.8,color="#364852")
    fig.text(.025,.021,"На карте (u, m) заполненная точка проходит тест лестницы. Вертикальная черта — предел u "
             "при заданных объёме и законе. Для исключённого постоянного класса показана работа при P = L.",
             fontsize=8.8,color="#364852")
    fig.savefig(HERE/"cost-map.png",dpi=150,metadata={"Title":"Карта затрат защиты памяти, задачи 3.1–3.2"})
    plt.close(fig)


if __name__ == "__main__":
    main()
