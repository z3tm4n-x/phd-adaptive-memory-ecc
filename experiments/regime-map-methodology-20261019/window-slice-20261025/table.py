"""One short table, conservative decimal display of sufficient budgets."""
from fractions import Fraction as F
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent


def down(x,places=2):
    y=F(x)*10**places;n=y.numerator//y.denominator
    sign='-' if n<0 else '';n=abs(n)
    return f'{sign}{n//10**places}.{n%10**places:0{places}d}'


def render():
    r=json.loads((HERE/'outputs/result.json').read_text('utf-8'))
    lines=['# Неточность окна и общий бюджет управления','',
      'В каждой строке k_H=20/k_L=1780. Числа — достаточные пределы u, мкс занятости шины в секунду, округлённые вниз. 10000 мкс/с = 1 процентный пункт шины. Общий ECC и инициализация включены; полезные обращения отдельно.','',
      '| Неточность каждой границы, с | >1×, u строго меньше | ≥2× | ≥4× | ≥5× |',
      '|---:|---:|---:|---:|---:|']
    for row in r['rows']:
        values=[F(row['u_limits'][str(g)]) for g in (1,2,4,5)]
        lines.append('| '+str(row['eta_s'])+' | '+' | '.join(down(v*10**6) if v>=0 else '—' for v in values)+' |')
    service=F(r['management']['composition_independent_u_upper'])*10**6
    lines+=['',
      '«—»: эта пара оценок не доказывает данный коэффициент даже при u=0; проигрыш метода не доказан.',
      '',
      f'Совместный сервис обязателен дополнительно. При u≤{down(service)} мкс/с любое сочетание объявленных цен проходит консервативный сервисный бюджет, если суммарная местная обработка/ожидание ≤1 мс и выполнен договор дробления операций. Выше этого уровня проверяется конкретный состав затрат по ENGINEERING.md.',
      '',
      'Во всём диапазоне Q_upper≤0,000962971178; запас ≥0,000037028822 (около 3,70% epsilon). Ориентир Q≤epsilon/2 не выполнен. Это условная модель PR260, не физический профиль орбиты.',
      '',
      'Готовое расписание с теми же сведениями и таймером совпадает с правилом на исправном канале. Новая карта не доказывает преимущество обратной связи над ним.']
    return '\n'.join(lines)+'\n'


if __name__=='__main__':(HERE/'TABLE.md').write_text(render(),encoding='utf-8',newline='\n')
