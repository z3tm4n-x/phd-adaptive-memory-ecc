"""Discrete scientific figure; no interpolated certified boundary."""
import json
from fractions import Fraction as F
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
def make():
    r=json.loads((HERE/'result.json').read_bytes()); plt.rcParams['svg.hashsalt']='epsilon-slice-20261027'
    plt.rcParams.update({'font.size':10,'axes.titlesize':12})
    fig,axes=plt.subplots(1,2,figsize=(12,5.8),sharex=True,layout='constrained')
    for ax,coordinate in zip(axes,('bus','core')):
        for row in r['rows']:
            eps=float(F(row['epsilon'])); low=row['lower_bounds']; fixed=row['fixed']; a=row['adaptive']
            for factor,name,color in ((.86,'constant','#2864a6'),(1.,'schedule','#238b45')):
                if fixed.get('k'):
                    l=float(F(low[name+'_'+coordinate+'_lower']))*100; u=float(F(fixed[coordinate+'_upper']))*100
                    ax.plot([eps*factor]*2,[l,u],color=color,lw=3)
                    ax.plot(eps*factor,l,'_',color=color,ms=11); ax.plot(eps*factor,u,'o',color=color,ms=5)
            if a.get('Q_upper'):
                l=float(F(a['mandatory_expected_'+coordinate+'_lower']))*100
                u=float(F(a['hard_'+coordinate+'_upper']))*100
                comp=float(F(a['no_guard_no_credit_'+coordinate+'_upper_component']))*100
                ax.plot([eps*1.16]*2,[l,u],color='#bd4b23',lw=1,ls=':')
                ax.plot(eps*1.16,l,'_',color='#bd4b23',ms=11)
                ax.plot(eps*1.16,u,'^',color='#bd4b23',ms=6)
                ax.plot(eps*1.16,comp,'o',mfc='none',mec='#bd4b23',ms=6)
            else:
                ax.text(eps*1.16,20,'A: no certificate',rotation=90,ha='center',va='center',fontsize=8,color='#bd4b23')
        ax.set(xscale='log',yscale='log',xlabel=r'Requirement $\epsilon$',ylabel='Protection resource time / T, %',
               title='SRAM bus operations' if coordinate=='bus' else 'Serial read/codec/repair operations')
        ax.set_xticks([.0001,.001,.01,.1],['$10^{-4}$\noptional','$10^{-3}$','$10^{-2}$','$10^{-1}$'])
        ax.grid(which='both',alpha=.15);ax.set_xlim(.000065,.17)
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],color='#2864a6',marker='o',label='Constant class: necessary L / feasible U'),
        Line2D([],[],color='#238b45',marker='o',label='Schedule class: necessary L / same feasible member U'),
        Line2D([],[],color='#bd4b23',marker='_',label='Adaptive family: mandatory L'),
        Line2D([],[],color='#bd4b23',marker='o',mfc='none',ls='',label='A upper component with G=0, no success credit'),
        Line2D([],[],color='#bd4b23',marker='^',ls=':',label='A all-history always-E cap')]
    fig.legend(handles=handles,loc='outside lower center',ncol=2,fontsize=8)
    fig.suptitle('Fixed p+r input; discrete epsilon slice — conditional operation-cost bounds\n'
        'Unknown controller / CPU / energy costs remain additive; no optimum or continuous-boundary claim',fontsize=11)
    fig.savefig(HERE/'cost-epsilon.svg',metadata={'Date':None})
    fig.savefig(HERE/'cost-epsilon.png',dpi=170,metadata={'Software':'epsilon-slice-20261027'})
    plt.close(fig)

if __name__=='__main__': make()
