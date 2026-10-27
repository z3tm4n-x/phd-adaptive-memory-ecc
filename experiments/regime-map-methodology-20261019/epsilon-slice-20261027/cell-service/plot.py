"""Discrete accepted settings; parameter additions are not assigned zero."""
from pathlib import Path
import json
from fractions import Fraction as F
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
plt.rcParams.update({'svg.hashsalt':'cell-service-20261027','svg.fonttype':'none','font.size':10})
r=json.loads((HERE/'result.json').read_bytes())
fig,axes=plt.subplots(1,2,figsize=(13,5.8),layout='constrained')
for ax,x,title in zip(axes,('bus','core'),('SRAM bus','Serial core: read / decode / repair')):
    for i,row in enumerate(r['rows']):
        eps=float(F(row['epsilon']));rv=row['rivals']
        for target,color,shift in (('constant','#2868a8',.91),('schedule','#218b44',1)):
            lo=float(F(rv[target+'_read_'+x+'_lower']))*100
            if target=='constant':hi=float(F(rv['constant_candidate']['known_'+x+'_upper']))*100
            elif x=='bus':hi=float(F(rv['schedule_known_upper']))*100
            else:hi=float(F(row['schedule_core_feasible_upper']))*100
            ax.plot([eps*shift]*2,[lo,hi],color=color,lw=2,label=target+' class: L / feasible U' if i==0 else None)
            ax.plot(eps*shift,lo,'_',color=color,ms=10);ax.plot(eps*shift,hi,'o',color=color,ms=4)
        if 'adaptive' in row:
            a=row['adaptive']['coordinates'][x]
            v=float(F(a['V']))*100
            ax.plot(eps*1.10,v,'^',ms=7,color='#c54820',label='Cell rule: V + all unpriced terms' if i==0 else None)
            ax.annotate('+ costs',(eps*1.10,v),xytext=((-45,7) if eps>.05 else (5,6)),textcoords='offset points',fontsize=8,color='#a84020')
        else:ax.text(eps*1.12,lo*.75,'A: uncertified',rotation=90,fontsize=8,color='#a84020',va='top')
    ax.set(xscale='log',yscale='log',xlabel=r'Requirement $\epsilon$',ylabel='Protection operations / T, %',title=title)
    ax.grid(which='both',alpha=.16)
    ax.set_xlim(7e-5,.16)
fig.suptitle('Same p+r input; unchanged PR281 settings, refined counter-error price\nConditional bounds. CPU / energy / handling remain parameters; no interpolated boundary.',fontsize=12)
handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='outside lower center',ncol=3,fontsize=9)
fig.savefig(HERE/'cost-epsilon.png',dpi=170,metadata={'Software':'cell-service fixed plot'})
fig.savefig(HERE/'cost-epsilon.svg',metadata={'Date':None})
p=HERE/'cost-epsilon.svg';p.write_text('\n'.join(x.rstrip() for x in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
print('Wrote deterministic PNG / SVG.')
