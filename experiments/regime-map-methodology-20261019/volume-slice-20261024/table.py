"""Render the only numerical comparison table with directed decimal rounding."""
from fractions import Fraction as F
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def directed(x,places,up):
    scaled=F(x)*10**places
    n=-(-scaled.numerator//scaled.denominator) if up else scaled.numerator//scaled.denominator
    sign='-' if n<0 else ''
    n=abs(n)
    return f'{sign}{n//10**places}.{n%10**places:0{places}d}'


def render():
    result=json.loads((HERE/'outputs/result.json').read_text('utf-8'))
    lines=['# Объём и цена управления: четыре отдельные точки','',
           'Фиксированный (39,32), T=315576000 с, ε=0,001, общий δ=0,000006.',
           'Цена ниже относится к проверкам/исправлениям; приложение, общий ECC и управление отделены.',
           '',
           '| КиБ | k адаптации | Q_upper | A_upper, % шины | F_class_lower, % | fixed k / F_witness_upper, % | Δu, п.п. |',
           '|---:|---:|---:|---:|---:|---:|---:|']
    for row in sorted(result['rows'],key=lambda r:r['kib']):
        s=next(a for a in row['adaptive_rows'] if a['k']==row['selected_k'])
        c=row['comparison']; method=' M' if 'mandatory-only' in s['certificate'] else ''
        lines.append(f"| {row['kib']} | {s['k']}{method} | {directed(s['Q_upper'],12,True)} | "
                     f"{directed(100*F(c['adaptive_bus_upper']),6,True)} | "
                     f"{directed(100*F(c['fixed_class_bus_lower']),6,False)} | "
                     f"{row['fixed']['k']} / {directed(100*F(c['fixed_witness_bus_upper']),6,True)} | "
                     f"{directed(100*F(c['control_bus_sufficient_strict_below']),6,False)} |")
    lines += ['',
      'Верхи округлены вверх, низы и Δu вниз. Δu=F_class_lower−A_upper; строгое достаточное преимущество при 0≤u_upper<Δu и соблюдении сервиса. Отрицательный Δu не доказывает проигрыш.',
      '',
      'M — Q из принятого mandatory-only основания; календарь и цена адаптации пересчитаны. Для 64/128 КиБ ценовой фильтр исключает положительный остаток данной пары оценок при любом k, поэтому информационный перебор пропущен. Оптимальность выбранных k не заявляется.',
      '',
      '512 КиБ — принятые результаты PR250. Остальные строки и ценовой фильтр требуют независимой проверки. Между четырьмя точками нет доказанной интерполяции. Для частичного банка Q всей памяти остаётся UNKNOWN.',
      '',
      'Дополнительные veto: v=0. При v>0 расход extra_veto_bus_slope·v добавляется к u; собственные издержки обработки veto также оплачиваются. CPU и энергия остаются отдельными параметрами.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':
    (HERE/'TABLE.md').write_text(render(),encoding='utf-8',newline='\n')
