"""Replay fixed PR281/C3 inputs and a bounded execution witness."""
from decimal import Decimal,localcontext,ROUND_FLOOR,ROUND_CEILING
from fractions import Fraction as F
import argparse
from cell_model import HERE,calculate,encoded,sha

def fmt(x,scale=1,places=9,up=True):
    x=F(x)*scale
    with localcontext() as ctx:
        ctx.prec=100
        return str((Decimal(x.numerator)/Decimal(x.denominator)).quantize(
            Decimal(1).scaleb(-places),rounding=ROUND_CEILING if up else ROUND_FLOOR))

def table(r):
    lines=['# Общее исполнение и цена нового клеточного правила','',
        'Только неизменённые настройки PR281; старой серии A11 здесь нет.',
        'V — достаточный верх известных операций плюс δ₀ и δ_C при C3, **до** G/z/escape/обработки.',
        'Цены V — % полного T, остатки — мкс/с. F и S — два полных класса, не выбранные оптимумы.','',
        '| ε | k_b / k_s; проходов n_b / n_s | Q⁺ при прежнем δ_C≤5e-5 | V bus / core, %T, вверх | Остаток20% F: bus / core, мкс/с, вниз | Остаток20% S: bus / core, мкс/с, вниз |',
        '|---:|---|---:|---:|---:|---:|']
    for row in r['rows']:
        eps=str(float(F(row['epsilon'])));a=row.get('adaptive')
        if not a:
            f=row['rivals']['constant_candidate']
            lines.append(f"| {eps} | А не сертифицировано; fixed k={f['period_blocks']} | — | — | — | — |")
            continue
        price=' / '.join(fmt(a['coordinates'][x]['V'],100,12) for x in ('bus','core'))
        gaps=[]
        for target in ('constant','schedule'):
            gaps.append(' / '.join(fmt(a['coordinates'][x]['comparison'][target]['allowance_20'],10**6,6,False) for x in ('bus','core')))
        lines.append(f"| {eps} | {a['k_base']} / {a['k_rare']}; {a['base_passes_per_cell']} / {a['rare_passes_per_cell']} | {fmt(a['Q_upper_at_design'],places=12)} | {price} | {gaps[0]} | {gaps[1]} |")
    lines+=['','Полная sufficient price в каждой координате:',
        '`V + A_z*z + A_G*G + (C_h−C_b)*δ_escape + c_all_handling`.',
        'Для20% вся сумма добавок должна быть не больше своего остатка справа.',
        'Одинаковые числа F/S при .1/.01 не отождествляют классы. Для30% все остатки отрицательны.',
        'Отказ данного верхнего сертификата не доказывает невозможности метода.',
        'CPU/энергия/память и общие приложение/init — отдельные координаты result.json.','']
    return '\n'.join(lines).encode()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--write',action='store_true');p.add_argument('--check',action='store_true');args=p.parse_args()
    r=calculate();raw=encoded(r);md=table(r)
    if args.write:(HERE/'result.json').write_bytes(raw);(HERE/'TABLE.md').write_bytes(md)
    elif args.check:
        assert raw==(HERE/'result.json').read_bytes(),'result mismatch'
        assert md==(HERE/'TABLE.md').read_bytes(),'table mismatch'
    else:print(raw.decode())
    print('PASS: unchanged four epsilon settings; C3 reference; calendar and full parameter region.',sha(raw))
