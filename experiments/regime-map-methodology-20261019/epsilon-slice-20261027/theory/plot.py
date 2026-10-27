"""Discrete epsilon-price evidence; arrows mean unpriced additions, not data."""
import json
from fractions import Fraction as F
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
HERE=Path(__file__).resolve().parent
r=json.loads((HERE/"result.json").read_text(encoding="utf-8"))["rows"]
ff=lambda a:float(F(a))
plt.rcParams.update({"font.family":"DejaVu Sans","svg.fonttype":"none","svg.hashsalt":"epsilon-theory-20261027","font.size":9})
fig,(ax,bx)=plt.subplots(1,2,figsize=(13,6.5))
fig.subplots_adjust(left=.07,right=.98,bottom=.22,top=.82,wspace=.25)
for row in r:
    ep=ff(row["epsilon"]);rv=row["rivals"];a=row["adaptive"]
    for factor,color,key in ((.87,"#315e9b","constant_read_bus_lower"),(1.,"#33845b","schedule_read_bus_lower")):
        low=ff(rv[key])*100
        up=100*ff(rv["constant_candidate"]["known_bus_upper"] if key.startswith("constant") else rv["schedule_known_upper"])
        xx=ep*factor
        ax.vlines(xx,low,up,color=color,lw=2,alpha=.85)
        ax.plot(xx,low,"_",color=color,ms=9,mew=2)
        ax.plot(xx,up,"o",mfc="white",mec=color,ms=5)
    if a["status"]=="CONDITIONAL_CERTIFICATE":
        yy=100*ff(a["bus_intercept_U0"])
        ax.plot(ep*1.15,yy,"D",color="#c67425",ms=5)
        ax.annotate("",xy=(ep*1.15,yy*1.65),xytext=(ep*1.15,yy*1.07),
                    arrowprops={"arrowstyle":"->","color":"#c67425","lw":1})
        for factor,color,k in ((.94,"#315e9b","constant_20pct_unpaid_allowance"),
                               (1.06,"#33845b","schedule_20pct_unpaid_allowance")):
            bx.scatter(ep*factor,1e6*ff(a[k]),color=color,s=35,zorder=3)
    else:
        ax.annotate("А: нет сертификата E5",xy=(ep*1.03,35),fontsize=8)
ax.set(xscale="log",yscale="log",xlabel="Допуск ε",ylabel="Защита: доля времени чистой шины, %",
       title="Низы классов и достаточные ценовые основания")
ax.set_xticks([.0001,.001,.01,.1],labels=["10⁻⁴","10⁻³","10⁻²","10⁻¹"])
ax.set_ylim(.002,80)
ax.grid(True,which="both",alpha=.15)
ax.legend(handles=[
    Line2D([0],[0],color="#315e9b",marker="o",mfc="white",label="Постоянный: низ → известная цена кандидата + u_F"),
    Line2D([0],[0],color="#33845b",marker="o",mfc="white",label="Расписание: низ → лучший из двух верхов + u_S"),
    Line2D([0],[0],color="#c67425",marker="D",ls="none",label="А: U₀; стрелка — все добавки Δ")],
    loc="lower left",fontsize=7)
bx.set(xscale="log",yscale="symlog",xlabel="Допуск ε",ylabel="Допустимая сумма всех добавок, мкс/с шины",
       title="Два отдельных условия экономии 20%")
bx.set_xticks([.001,.01,.1],labels=["10⁻³","10⁻²","10⁻¹"])
bx.set_ylim(-5000,200)
bx.axhline(0,color="black",lw=.7)
bx.grid(True,which="both",alpha=.15)
bx.annotate("Допуск добавок: +5.94 мкс/с\nδ_C, G, z и управление",
            xy=(.0106,5.943626),xytext=(.0013,60),fontsize=8,
            arrowprops={"arrowstyle":"->","color":"#33845b"})
bx.text(.002,-2500,"Отрицательно: этот сертификат не даёт 20%.\nЭто не запрет всего семейства.",fontsize=8)
bx.legend(handles=[Line2D([0],[0],color="#315e9b",marker="o",ls="none",label="Против постоянного класса"),
                   Line2D([0],[0],color="#33845b",marker="o",ls="none",label="Против сильного расписания")],
          fontsize=8,loc="upper right")
fig.suptitle("Одна среда p+r, полный (39,32), 512 КиБ, 10 лет — отдельные значения ε",fontsize=12)
fig.text(.5,.04,"Авторский условный расчёт. Полная цена: U₀ + C_h·δ_C + A_z·z + A_G·G + управление.\n"
                 "Неизвестные параметры не равны нулю; CPU/энергия и приложение — отдельно. Между точками граница не доказана.",
         ha="center",fontsize=8)
fig.savefig(HERE/"cost-axis.svg",metadata={"Date":None})
fig.savefig(HERE/"cost-axis-preview.png",dpi=140,metadata={"Software":"epsilon-theory-check"})
print("cost-axis.svg: discrete bounds and explicit unpriced additions")
