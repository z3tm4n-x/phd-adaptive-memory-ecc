#!/usr/bin/env python3
"""Discrete price bounds for the unchanged accepted epsilon settings."""
from pathlib import Path
from fractions import Fraction
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
data=json.loads((HERE/"result.json").read_text(encoding="utf-8"))
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,
                     "svg.fonttype":"none","svg.hashsalt":"t196-count-price-20261027"})
fig,axs=plt.subplots(1,2,figsize=(11.6,5.6))
labels=["10⁻¹","10⁻²","10⁻³","10⁻⁴"]
for ax,metric,title in zip(axs,("bus","core"),("Чистая шина","Core с decode")):
    for i,row in enumerate(data["rows"]):
        for target,dx,mark,color,label in (
                ("constant",-.10,"^","#244764","Низ постоянного класса"),
                ("schedule",.10,"v","#558da8","Низ класса расписаний")):
            y=100*float(Fraction(row["rivals"][f"{target}_read_{metric}_lower"]))
            ax.scatter(i+dx,y,marker=mark,color=color,s=42,label=label if i==0 else None,zorder=4)
        f=row["rivals"]["constant_candidate"]
        if f:
            ax.scatter(i,100*float(Fraction(f[f"known_{metric}_upper"])),marker="s",
                       facecolors="none",edgecolors="#777777",s=46,
                       label="Постоянный кандидат: известный верх" if i==0 else None)
        if "adaptive" in row:
            y=100*float(Fraction(row["adaptive"]["coordinates"][metric]["V_at_design_delta_C"]))
            ax.scatter(i,y,marker="D",s=40,color="#c26b2a",
                       label="Адаптация: V + неизвестные добавки" if i==0 else None,zorder=5)
            ax.annotate("",xy=(i,y*1.65),xytext=(i,y*1.08),
                        arrowprops={"arrowstyle":"->","color":"#c26b2a","lw":1})
        else:
            ax.text(i,.02,"А: нет нового\nсертификата Q",ha="center",fontsize=9,color="#666666")
    ax.set_xticks(range(4),labels);ax.set_xlabel("Допуск ε")
    ax.set_yscale("log");ax.set_ylabel("Цена защиты, % срока")
    ax.set_title(title);ax.set_xlim(-.45,3.45);ax.grid(axis="y",which="major",alpha=.22)
handles,leg=axs[0].get_legend_handles_labels()
fig.legend(handles,leg,loc="lower center",ncol=2,bbox_to_anchor=(.5,.055),frameon=False,fontsize=9)
fig.suptitle("Ошибка счёта оплачена основным календарём; δ_C = 5·10⁻⁵",fontsize=13)
fig.text(.5,.02,"Стрелки: G, дополнительные invalid и обработка ещё добавляются. Точки не задают интерполяцию или полный аппаратный выигрыш.",
         ha="center",fontsize=9)
fig.subplots_adjust(left=.08,right=.98,top=.87,bottom=.26,wspace=.28)
fig.savefig(HERE/"cost-bounds.svg",metadata={"Date":None})
fig.savefig(HERE/"cost-bounds-preview.png",dpi=140)
print("SVG and local PNG preview written")

