"""Static Russian PNG/SVG figures from T88 CSV; no network sources."""
import csv
from fractions import Fraction as F
import os
import tempfile

import engine as e


def plots(out):
    os.environ.setdefault('MPLCONFIGDIR',tempfile.mkdtemp(prefix='t88-mpl-'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'svg.hashsalt':'t88-dstar'})
    with (out/'curves.csv').open() as f:rows=list(csv.DictReader(f))
    with (out/'constant_U.csv').open() as f:fixed=list(csv.DictReader(f))
    labels={'combined':'ERR + монитор','monitor-only':'Только монитор','ERR-only':'Только ERR (модель)'}
    colors={'combined':'#176b9b','monitor-only':'#c35620','ERR-only':'#6c469c'}
    def number(r,k):return float(F(r[k]))
    for detail,name in [(False,'tax_vs_Dstar'),(True,'tax_1percent_detail')]:
        fig,axs=plt.subplots(1,2,figsize=(12,4.7),layout='constrained')
        for ax,s in zip(axs,('3','2.5'),strict=True):
            mx=5e-5
            detail_max=5e-5
            for mode in e.CFG['modes']:
                group=[r for r in rows if r['shield']==s and r['mode']==mode and r.get('objective')]
                group.sort(key=lambda r:number(r,'Dstar'))
                if group:
                    x=[number(r,'Dstar')*1e4 for r in group];y=[number(r,'objective')*100 for r in group]
                    if not detail or min(y)<=1.2:
                        ax.plot(x,y,'o-',ms=2.5,lw=1.3,color=colors[mode],label=labels[mode])
                        detail_max=max(detail_max,max((xx/1e4 for xx,yy in zip(x,y) if yy<=1.2),default=5e-5))
                    mx=max(mx,max(x)/1e4)
                elif not detail:
                    ax.plot([],[],color=colors[mode],label=labels[mode]+': область не установлена')
            if not detail:
                if s=='2.5':
                    fallback=[r for r in rows if r['shield']==s and r['mode']=='ERR-only' and r.get('always_S_upper')]
                    fallback.sort(key=lambda r:number(r,'Dstar'))
                    ax.plot([number(r,'Dstar')*1e4 for r in fallback],[number(r,'always_S_upper')*100 for r in fallback],
                            ':',color=colors['ERR-only'],lw=1.4,label='ERR always-S: отдельный резерв')
                fr=[r for r in fixed if r['shield']==s and r['mode_context']=='combined' and r['resource_pass']=='True']
                fr.sort(key=lambda r:number(r,'Dstar'))
                ax.plot([number(r,'Dstar')*1e4 for r in fr],[number(r,'cost_lower')*100 for r in fr],
                        '--',color='#333333',lw=1.4,label='Постоянный U: низ занятого времени')
                ax.set_yscale('log');ax.set_ylim(.1,100)
            else:
                ax.set_ylim(0,1.2)
                ax.set_xlim(.48,detail_max*1e4*1.025)
            ax.axhline(1,color='#8c2525',lw=1,ls=':',label='Цель 1%' if s=='3' else None)
            ax.set_title(f'Защита {s.replace(".",",")} г/см²'+(' — основная' if s=='3' else ''))
            ax.set_xlabel('D* за 10 лет, ×10⁻⁴')
            ax.set_ylabel('Полный спокойный налог, %')
            ax.grid(True,which='major',alpha=.22)
            ax.legend(fontsize=8,loc='best')
        fig.suptitle('R0-A / T73 / 32+6: условные границы, запас времени 10%')
        for ext in ('png','svg'):
            target=out/f'{name}.{ext}'
            fig.savefig(target,dpi=170,metadata={'Date':None} if ext=='svg' else {'Software':'T88'})
            if ext=='svg':
                target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
        plt.close(fig)


if __name__=='__main__':plots(e.HERE/'outputs')
