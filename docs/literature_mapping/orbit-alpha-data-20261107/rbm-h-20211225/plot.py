"""Draw the two signed series in the verified minute ledger."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FixedLocator, FuncFormatter
import numpy as np

HERE = Path(__file__).resolve().parent


def main():
    with (HERE/"minutes.jsonl").open(encoding="utf-8") as stream:
        columns = json.loads(next(stream))
        rows = [dict(zip(columns,json.loads(line))) for line in stream]
    x = np.array([(r["minute_UTC_from_midnight"]+.5)/60 for r in rows])
    observed = np.array([r["observed_counts"]/r["exposure_s"] if r["eligible"] else np.nan for r in rows])
    predicted = np.array([r["predicted_counts"]/r["exposure_s"] if r["eligible"] else np.nan for r in rows])
    delta = observed-predicted
    fig,(top,bottom) = plt.subplots(2,1,figsize=(12.8,6.5),sharex=True,
                                   gridspec_kw={"height_ratios":[1.3,1]},layout="constrained")
    fig.suptitle("MAXI/RBM-H на МКС, 25 декабря 2021 года",fontsize=17)
    measured,forecast = "#17658a","#ae4817"
    top.plot(x,observed,color=measured,lw=1.0,label="Измерено")
    top.plot(x,predicted,color=forecast,lw=1.35,label="Прогноз по карте первого года")
    top.axhline(1,color="#555",lw=.85,ls="--",label="Порог 1 Гц")
    top.legend(loc="upper right",ncol=3,fontsize=9)
    top.set_yscale("symlog",linthresh=.1)
    top.set_ylim(-.007,30000)
    top.set_ylabel("Минутная частота, Гц")
    top.yaxis.set_major_locator(FixedLocator([0,.1,1,10,100,1000,10000]))
    bottom.plot(x,delta,color=measured,lw=1.0)
    negative = np.where(delta < 0,delta,np.nan)
    bottom.scatter(x,negative,color=forecast,s=7,zorder=3)
    bottom.axhline(0,color="#454545",lw=.8)
    bottom.set_yscale("symlog",linthresh=1)
    bottom.set_ylim(-45,24000)
    bottom.set_ylabel("Измерено минус прогноз, Гц")
    bottom.yaxis.set_major_locator(FixedLocator([-10,-1,0,1,10,100,1000,10000]))
    bottom.set_xlabel("Время UTC, часы")
    for ax in (top,bottom):
        ax.set_xlim(0,24)
        ax.set_xticks(np.arange(0,25,2))
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v,pos:f"{v:g}".replace(".",",")))
        ax.grid(axis="both",alpha=.22)
        ax.spines[["top","right"]].set_visible(False)
    for i,offset in ((np.nanargmax(delta),(18,-6)),(np.nanargmin(delta),(18,12))):
        minute = rows[i]["minute_UTC_from_midnight"]
        label = f"{minute//60:02d}:{minute%60:02d}  {delta[i]:+.1f} Гц".replace(".",",")
        bottom.annotate(label,(x[i],delta[i]),xytext=offset,textcoords="offset points",
                        fontsize=9,arrowprops={"arrowstyle":"-","color":"#555","lw":.7},
                        bbox={"boxstyle":"round,pad=.2","fc":"white","ec":"none","alpha":.85})
    fig.savefig(HERE/"profile.png",dpi=150,facecolor="white")
    plt.close(fig)


if __name__ == "__main__":
    main()
