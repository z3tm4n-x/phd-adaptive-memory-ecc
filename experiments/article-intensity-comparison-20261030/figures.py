"""Three article figures. Curves are analytic displays, never extra lower tests."""
from io import BytesIO
from fractions import Fraction as F
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import calculation as c

W, D, COST = 1048576, F(86400), F(1,5_000_000)
STYLES = dict(avg=dict(color='0.42',linestyle='--',linewidth=2),
              event=dict(color='0.05',linestyle='-',linewidth=2.1),
              peak=dict(color='0.25',linestyle='-.',linewidth=1.8))
LABELS = dict(avg='Среднее: кандидат', event='Параметры события', peak='Пик на весь срок')


def sampled_ratios():
    values={F(str(x)) for x in np.geomspace(1,float(c.RMAX),c.CFG['figure_curve_samples'])}
    values={q for q in values if 1<=q<=c.RMAX}
    values.update([F(1),F(10),F(100),F(1000),c.RMAX])
    for kind in ('event','peak'):
        values.update(c.resource_ratio_boundary(W,D,COST,COST,'C',kind))
    return sorted(values)


def curve_row(d,r):
    stats=c.profile_statistics(W,d,r)
    roots={kind:c.root(stats[s],W,COST,'C') for kind,s in
           [('avg','S_mean'),('event','S_event'),('peak','S_peak')]}
    feasible=roots['event']>=W*COST
    p0=c.root(stats['S_event'],W,F(0),'C')
    return dict(r=float(r),r_exact=str(r),duration_s=float(d),duration_exact=str(d),
                roots_s={k:float(v) for k,v in roots.items()},
                P_min_s=float(W*COST), event_resource_feasible=feasible,
                operation_reduction_percent=float(100*(1-roots['event']/p0)) if feasible else None,
                E_over_Fs=float(stats['excess']/stats['global_cap']))


def datasets(results):
    ratios=[curve_row(D,r) for r in sampled_ratios()]
    main=[x for x in results['rows'] if x['accepted']['label']=='main' and x['accepted']['rule']=='C']
    markers=[]
    for row in main:
        q=row['comparison']; old=row['accepted']
        markers.append(dict(row_id=row['id'],r=float(F(old['peak_ratio'])),
            P_avg_s=float(F(q['choices']['avg']['selected_P_s']['exact'])),
            lower=q['lower_at_selected_P_avg']))
    common=dict(useful_MiB=4,W=W,T_s=str(c.T),epsilon=str(c.EPS),rule='C',
                c_s=str(COST),delta_s=str(COST),rho=str(c.RHO),
                curve_scope='analytic display only; not additional scientific rows or lower tests',
                source='T340 section 4 common test; known E subclass; PLAN.md and inputs.json',
                numerical_plot_fields='binary64 display; exact decisions in results.json')
    first=dict(**common,duration_s=str(D),curves=ratios,markers=markers,
        event_resource_r_interval=c.interval(*c.resource_ratio_boundary(W,D,COST,COST,'C','event')),
        peak_resource_r_interval=c.interval(*c.resource_ratio_boundary(W,D,COST,COST,'C','peak')))
    ds={F(str(x)) for x in np.geomspace(10800,864000,c.CFG['figure_curve_samples'])}
    ds={q for q in ds if 10800<=q<=864000}; ds.update([F(10800),D,F(864000)])
    second=dict(**common,peak_ratio='100',curves=[curve_row(d,F(100)) for d in sorted(ds)],
        registered_duration_s=[10800,86400,864000],registered_domain_s=[10800,864000],
        exposure_cap_duration_s=c.value(c.FSREF/(c.BREF*99)),
        same_confirmed_marker=next(x for x in markers if x['r']==100))
    operations=[]
    for row in results['rows']:
        if row['accepted']['label'].startswith('operation'):
            q=row['comparison']; old=row['accepted']
            operations.append(dict(row_id=row['id'],c_ns=float(F(old['c_s'])*10**9),
                delta_ns=float(F(old['delta_s'])*10**9),
                P_event_over_P_min=float(F(q['choices']['event']['exact_root_s']['exact'])/F(q['resource_floor_s']['exact'])),
                resource_feasible=q['choices']['event']['resource_feasible'],
                operation_reduction_percent=q['operation_reduction_percent']))
    third=dict(**common,duration_s=str(D),curves=ratios,
        operation_bound_percent=c.value(F(200,W+2)),
        event_resource_r_interval=first['event_resource_r_interval'],
        operation_registered_rows=operations)
    return {'figure1_data.json':first,'figure2_data.json':second,'figure3_data.json':third}


def setup():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.titlesize':12,
        'axes.labelsize':11,'xtick.labelsize':10,'ytick.labelsize':10,
        'legend.fontsize':10,'axes.spines.top':False,'axes.spines.right':False,
        'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'none',
        'svg.hashsalt':'article-intensity-comparison-20261030',
        'savefig.facecolor':'white','figure.facecolor':'white','axes.axisbelow':True})


def title(fig, main, sub):
    fig.suptitle(main,x=.51,y=.97,fontsize=14,fontweight='bold')
    fig.text(.51,.915,sub,ha='center',fontsize=10)


def period_axes(ax):
    ax.set_yscale('log'); ax.set_xscale('log')
    ax.set_ylabel('Период полного обхода, с')
    ax.grid(which='major',color='0.85',linewidth=.6)


def figure1(data):
    fig,ax=plt.subplots(figsize=(9.4,6.2))
    fig.subplots_adjust(left=.105,right=.97,bottom=.20,top=.85)
    title(fig,'Как сведения об интенсивности меняют период',
          '4 МиБ; d = 1 сутки; правило С; c = Δ = 200 нс; ε = 10⁻³; T = 10 лет')
    rows=data['curves']; x=[v['r'] for v in rows]
    for kind in ('avg','event','peak'):
        ax.plot(x,[v['roots_s'][kind] for v in rows],label=LABELS[kind],**STYLES[kind])
    floor=float(W*COST)
    ax.set_ylim(6e-7,160); ax.set_xlim(.9,float(c.RMAX)*1.18)
    ax.axhspan(ax.get_ylim()[0],floor,color='0.94',zorder=0)
    ax.axhline(floor,color='0.15',linestyle=':',linewidth=1.4,label='Минимум по ресурсу')
    for m in data['markers']:
        fail=m['lower']['verdict']=='violation_proved'
        ax.plot(m['r'],m['P_avg_s'],marker='x' if fail else 'o',linestyle='none',
                color='black',markersize=7,markeredgewidth=1.5,markerfacecolor='white')
    ax.text(1.35,1.8e-5,'Ниже минимума:\nпредписание не помещается\nв выделенный ресурс',fontsize=10,
            bbox=dict(facecolor='0.94',edgecolor='none',pad=3))
    ax.annotate('P_min = 0,2097152 с',xy=(1.35,floor),xytext=(1.35,.42),fontsize=10)
    period_axes(ax); ax.set_xlabel('Отношение пика к фону r = B/b')
    handles,labels=ax.get_legend_handles_labels()
    handles.extend([Line2D([],[],marker='x',linestyle='none',color='black',markersize=7),
                    Line2D([],[],marker='o',markerfacecolor='white',linestyle='none',color='black')])
    labels.extend(['Q > ε: доказано в точке P_avg','Нарушение не установлено'])
    fig.legend(handles,labels,loc='lower center',ncol=3,bbox_to_anchor=(.51,.015),frameon=False)
    return fig


def figure2(data):
    fig,ax=plt.subplots(figsize=(9.4,6.2))
    fig.subplots_adjust(left=.105,right=.97,bottom=.20,top=.85)
    title(fig,'Длительность события и выбранный период',
          '4 МиБ; r = 100; правило С; c = Δ = 200 нс; ε = 10⁻³; T = 10 лет')
    rows=data['curves']; hours=[x['duration_s']/3600 for x in rows]
    for kind in ('avg','event','peak'):
        ax.plot(hours,[v['roots_s'][kind] for v in rows],label=LABELS[kind],**STYLES[kind])
    ax.set_xlim(2.5,288); ax.set_ylim(.003,160)
    ax.axhspan(.003,float(W*COST),color='0.94',zorder=0)
    ax.axhline(float(W*COST),color='0.15',linestyle=':',linewidth=1.4,label='Минимум по ресурсу')
    for a,b in ((2.5,3),(240,288)):
        ax.axvspan(a,b,facecolor='0.88',hatch='///',edgecolor='0.65',linewidth=0,zorder=0)
    for edge in (3,240):
        ax.axvline(edge,color='0.55',linewidth=.8)
    m=data['same_confirmed_marker']
    ax.plot(24,m['P_avg_s'],'x',color='black',markersize=7,markeredgewidth=1.5)
    ax.annotate('Доказано Q(T) > ε\nпри d = 24 ч',xy=(24,m['P_avg_s']),xytext=(44,85),fontsize=10,
                arrowprops=dict(arrowstyle='-',color='0.4',linewidth=.7))
    ax.text(4,.04,'Пиковое предписание вне ресурса\nна всём показанном диапазоне',fontsize=10)
    ax.text(4,1.0,'3 ч ≤ d ≤ 240 ч; квота E ≤ F_s выполнена',fontsize=10)
    period_axes(ax); ax.set_xlabel('Длительность события d, ч')
    ax.set_xticks([3,6,12,24,72,240],labels=['3','6','12','24','72','240'])
    handles,labels=ax.get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower center',ncol=2,bbox_to_anchor=(.51,.02),frameon=False)
    return fig


def figure3(data):
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11.2,5.8),gridspec_kw={'width_ratios':[1.55,1]})
    fig.subplots_adjust(left=.075,right=.985,bottom=.24,top=.79,wspace=.30)
    title(fig,'Операционная поправка и её область применимости',
          '4 МиБ; d = 1 сутки; правило С; ε = 10⁻³; T = 10 лет; ρ = 1')
    rows=data['curves']; bound=float(F(data['operation_bound_percent']['exact']))
    x=[v['r'] for v in rows]
    y=[v['operation_reduction_percent']*1e4 if v['operation_reduction_percent'] is not None else np.nan for v in rows]
    edge=float(F(data['event_resource_r_interval']['lower']))
    ax.plot(x,y,color='black',linewidth=2,label='c = Δ = 200 нс')
    ax.plot([1,edge],[bound*1e4,bound*1e4],color='0.35',linestyle='--',linewidth=1.3,
            label='Доказанный верх 200/(W+2) %')
    ax.axvspan(edge,float(c.RMAX)*1.12,facecolor='0.94',hatch='///',edgecolor='0.75',linewidth=0)
    ax.axvline(edge,color='0.5',linestyle=':',linewidth=1)
    ax.text(.89,.40,'Нет достаточного\nпериода\nв ресурсе',fontsize=9,ha='center',transform=ax.transAxes)
    ax.set_xscale('log'); ax.set_xlim(.9,float(c.RMAX)*1.12); ax.set_ylim(0,bound*1e4*1.15)
    ax.set_title('(а) При существовании обоих периодов',fontsize=11)
    ax.set_xlabel('Отношение пика к фону r')
    ax.set_ylabel('Сокращение периода, 10⁻⁴ %')
    ax.grid(which='major',color='0.86',linewidth=.6)
    ax.legend(loc='lower left',fontsize=9,frameon=True,facecolor='white',framealpha=1)
    ops=data['operation_registered_rows']
    vals=[x['P_event_over_P_min'] for x in ops]
    bx.axhspan(0,1,color='0.94',zorder=0)
    bx.axhline(1,color='0.25',linestyle=':',linewidth=1.4)
    bx.plot(range(3),vals[:3],'o',color='black',markerfacecolor='white',markersize=8,linestyle='none')
    bx.plot(3,vals[3],'x',color='black',markersize=9,markeredgewidth=1.5)
    for i,v in enumerate(vals):
        bx.text(i,v+.035,f'{v:.4f}',ha='center',fontsize=9)
    bx.text(1.4,.60,'Корень ниже минимума:\nдостаточное предписание\nнеосуществимо',ha='center',fontsize=9)
    bx.set_xticks(range(4),labels=['200 / 0','200 / 100','200 / 200','1000 / 1000'],rotation=25,ha='right')
    bx.set_xlabel('c / Δ, нс'); bx.set_ylabel('P_event / P_min')
    bx.set_xlim(-.6,3.6); bx.set_ylim(0,1.42); bx.set_title('(б) При r = 1000',fontsize=11)
    bx.grid(axis='y',color='0.86',linewidth=.6)
    fig.text(.51,.025,'В пустой ресурсной области процент между допустимыми периодами не определён.\n'
             'Малая поправка не разрешает отбросить её при полностью исчерпанном ε.',ha='center',fontsize=10)
    return fig


def render(data):
    setup(); out={}
    for number,builder in enumerate((figure1,figure2,figure3),1):
        fig=builder(data[f'figure{number}_data.json'])
        for suffix in ('svg','pdf','png'):
            stream=BytesIO()
            metadata=({'Date':None} if suffix=='svg' else
                      {'CreationDate':None,'ModDate':None,'Creator':'Reproducible intensity comparison'} if suffix=='pdf' else
                      {'Software':'Reproducible intensity comparison'})
            fig.savefig(stream,format=suffix,dpi=200,metadata=metadata)
            content=stream.getvalue()
            if suffix=='svg':
                content=('\n'.join(line.rstrip() for line in content.decode('utf-8').splitlines())+'\n').encode('utf-8')
            out[f'figures/figure{number}.{suffix}']=content
        plt.close(fig)
    return out
