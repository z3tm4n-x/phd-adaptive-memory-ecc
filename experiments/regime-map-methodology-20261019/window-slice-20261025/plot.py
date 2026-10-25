"""One scientific map; plotted samples evaluate affine lines, not a search grid."""
import argparse
from fractions import Fraction as F
import json
from pathlib import Path
import sys
from table import down
ap=argparse.ArgumentParser();ap.add_argument('--deps-dir',type=Path);args=ap.parse_args()
if args.deps_dir:sys.path.insert(0,str(args.deps_dir.resolve()))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch,Rectangle

HERE=Path(__file__).resolve().parent
r=json.loads((HERE/'outputs/result.json').read_text('utf-8'))
f=lambda x:float(F(x))
a=f(r['affine_bus']['intercept']);slope=f(r['affine_bus']['slope_per_second'])
lo=f(r['constant_class']['whole_constant_class_lower_with_common_ECC'])
common=f(r['common_cost']['ECC_and_initial_bus_upper'])
xs=np.r_[np.linspace(0,30,100),np.geomspace(30.01,1200,400)]
lim={g:np.maximum(0,(lo/g-a-slope*xs-common)*1e6) for g in (1,2,4,5)}
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'svg.hashsalt':'t206-window-v1'})
fig,ax=plt.subplots(figsize=(12,7.2),layout='constrained')
ax.set_facecolor('#edf0f3')
colors={1:'#c5e0ee',2:'#f1df96',4:'#a2d5a6',5:'#3d9b78'}
bottom=np.zeros_like(xs)
for g in (5,4,2,1):
    ax.fill_between(xs,bottom,lim[g],color=colors[g])
    ax.plot(xs,lim[g],color='#34495e',linewidth=.8)
    bottom=lim[g]
ceiling=f(r['management']['composition_independent_u_upper'])*1e6
ax.axhspan(ceiling,10000,facecolor='none',edgecolor='#91989f',hatch='///',linewidth=0,alpha=.45)
ax.axhline(ceiling,color='#5b6066',ls='--',lw=1.2)
ax.text(450,ceiling*1.1,'Выше штриховой линии: проверить состав затрат',fontsize=9,ha='center',va='bottom')
for gain,xmax,ymax in [(5,30,20),(4,120,30)]:
    ax.add_patch(Rectangle((0,0),xmax,ymax,fill=False,edgecolor='#154e3b',lw=1.7,ls='--'))
    ax.annotate(f'{gain}× с запасом',xy=(xmax,ymax),xytext=(xmax*1.25,ymax*.75),fontsize=10,
                arrowprops={'arrowstyle':'-','color':'#154e3b'},color='#154e3b')
ax.axvline(30,color='#34495e',ls=':',lw=1)
ax.text(31,1200,'исходные ±30 с',rotation=90,va='center',fontsize=9)
for sample,mark in zip(r['management']['examples'],['o','s']):
    yy=f(sample['mean_bus_upper'])*1e6
    xx=sample['shown_eta_s']
    ax.plot(xx,yy,mark,color='#102f28',mfc='white',ms=6,zorder=6)
    ax.annotate(sample['id'],xy=(xx,yy),xytext=(xx*1.15,yy*1.03),fontsize=9)
ax.set_xscale('symlog',linthresh=30,linscale=.85)
ax.set_yscale('symlog',linthresh=20,linscale=.8)
ax.set_xlim(0,1200);ax.set_ylim(0,10000)
ax.set_xticks([0,15,30,60,120,300,600,1200],['0','15','30','60','120','300','600','1200'])
ax.set_yticks([0,10,20,50,100,300,1000,3000,10000],['0','10','20','50','100','300','1000','3000','10000'])
ax.set_xlabel('Неточность каждой границы η, с (линейно до 30 с, далее логарифмически)')
ax.set_ylabel('Общий бюджет управления u, мкс занятости шины в секунду\n(линейно до 20 мкс/с, далее логарифмически)')
ax.set_title('Предсказуемые окна: достаточный выигрыш при фиксированных периодах',loc='left',fontweight='bold',fontsize=14)
handles=[Patch(facecolor=colors[g],label=('>1×' if g==1 else f'≥{g}×')) for g in (1,2,4,5)]
handles.append(Patch(facecolor='#edf0f3',label='Выигрыш не доказан'))
ax.legend(handles=handles,ncol=5,loc='upper center',bbox_to_anchor=(.5,1),frameon=True,fontsize=10)
ax.grid(alpha=.17);ax.set_axisbelow(True)
fig.supxlabel('512 КиБ · (39,32) · kH=20 / kL=1780 · Q⁺≤0,000962971178, запас ≈3,70% ε\n'
    'Штриховка не означает невозможность. Обработка/ожидание ≤1 мс на пакет и дробление операций — условия расчёта.\n'
    'Границы цены аналитические; превосходство обратной связи над готовым расписанием не заявлено.',fontsize=10)
out=HERE/'outputs';fig.savefig(out/'window-management-map.png',dpi=190)
svg=out/'window-management-map.svg';fig.savefig(svg,metadata={'Date':None})
svg.write_text('\n'.join(x.rstrip() for x in svg.read_text('utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print('matplotlib',matplotlib.__version__)
