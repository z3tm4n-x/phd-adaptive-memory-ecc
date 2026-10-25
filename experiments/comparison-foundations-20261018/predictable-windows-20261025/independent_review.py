"""Independent substitution of the declared bounds; no author-code imports."""
from decimal import Decimal, localcontext
from fractions import Fraction as F
from pathlib import Path
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
cfg = json.loads((ROOT / 'experiments/t186-method-comparison/code-strength/common-input.json').read_text('utf-8'))
result = json.loads((HERE / 'result.json').read_text('utf-8'))


def same(actual, section, key):
    assert actual == F(result[section][key]), (section, key)


def dec(value):
    return Decimal(value.numerator) / Decimal(value.denominator)


W, T, epsilon = cfg['words'], F(cfg['mission_s']), F(cfg['epsilon'])
environment, service, calendar = (cfg[key] for key in ('environment', 'service', 'calendar'))
D = environment['reference_words'] * environment['reference_bits']
b, B, Fs, rho, ell = [F(environment[key]) for key in (
    'reference_background_per_s', 'reference_peak_per_s', 'reference_solar_mass',
    'reference_growth_per_s', 'reference_growth_threshold_per_s')]
xmin, xmax = F(service['clock_lower']), F(service['clock_upper'])
J = F(service['operation_endpoint_span_ns']) / 10**9
delta0, deltap = F(cfg['lifetime_other_budget']), F(1, 10**6)
d = F(124, 10**9) * xmax + 3*J
K = F(W*39*38, 2*D*D)
base = F(W * calendar['g_ticks'], 10**9)
assert (result['adaptive']['kH'], result['adaptive']['kL']) == (20, 1780)
PH, PL = 20*base*xmax+J, 1780*base*xmax+J
ph, pl, pbase = 20*base*xmin-J, 1780*base*xmin-J, base*xmin-J
same(PH, 'adaptive', 'PH_upper_s')
same(PL, 'adaptive', 'PL_upper_s')
assert PH+d <= 1

M1, M2 = b*T+Fs, b*b*T+(B+b)*Fs
cross = 2*K*B*d*M1
upper = delta0+deltap+K*((PL+d)*b*b*T+(PH+d)*(B+b)*Fs)+cross
same(upper, 'adaptive', 'Q_upper')
same(epsilon-upper, 'adaptive', 'slack')
assert upper < epsilon
fixed_upper = delta0+K*(22*base*xmax+J)*M2+cross
same(fixed_upper, 'fixed', 'sufficient_Q_upper_conservative')
assert fixed_upper < epsilon
# Literal substitution into displayed (3) would add this positive term.
fixed_via_displayed_3 = fixed_upper + K*d*M2
assert fixed_via_displayed_3 < epsilon

with localcontext() as context:
    context.prec = 100
    log = (dec(B)/dec(ell)).ln()
    rise = (1-dec(b/ell)+log)/dec(rho)
    ramp = (dec((ell-b)**2/(2*ell)+B-ell)-dec(b)*log)/dec(rho)
    mass = 256*(ramp+dec((B-b)*430))
    for key, value in (('rise_s', rise), ('solar_mass', mass)):
        interval = result['witness'][key]
        assert Decimal(interval['lo']) <= value <= Decimal(interval['hi']), key
    assert rise+430 < 600 and mass < dec(Fs)
    lam = F(39)*B/D
    lower_values = []
    for p in (F('0.626997'), F('0.626998')):
        # Free lengths after removing every possible repair window, any phase.
        M = F(430)/p+2
        squares = (430-M*d)**2/(M+1)
        Z = dec(F(256*W)*F(38,39)*lam*lam*squares/2)*(-dec(lam*430)).exp()
        lower_values.append(1-(-Z).exp()-dec(delta0))
    assert lower_values[0] < dec(epsilon) < lower_values[1]
    for key, value in zip(('previous_Q_enclosure', 'Q_lower_enclosure'), lower_values):
        interval = result['witness'][key]
        assert Decimal(interval['lo']) <= value <= Decimal(interval['hi']), key

Nwin = T/5400
assert Nwin.denominator == 1
C = 1+(xmax+J)+F('.01')+F(calendar['freeze_ticks'], 10**9)*xmax+J+F('.002')
same(C, 'model', 'price_padding_s')
nloss = cfg['adaptive']['ordinary_loss_episodes_upper']
false = F(cfg['adaptive']['ordinary_false_expected_per_s'])*T
loss = F(cfg['adaptive']['ordinary_outage_fraction'])*T
A = Nwin*(660+2*C)+loss+2*C*(nloss+false)
hard = W*(T/pbase+2)
read_counts = {
    'slow_support': W*(T/pl+2),
    'windows_loss_false': W*(A/ph+2*(Nwin+nloss+false)),
    'startup_and_tail': W+2*W*(C/ph+2),
    'exceptional_execution': (delta0+deltap)*hard,
}
for key, value in read_counts.items():
    assert value == F(result['adaptive']['read_terms'][key]), key
reads = min(hard, sum(read_counts.values(), F(0)))
parents = F(39*W, D)*M1
repairs = min(reads, 2*parents+upper*hard)
R, Cwrite = F(48, 10**9)*xmax+J, F(56, 10**9)*xmax+J
bus = (R*reads+Cwrite*repairs)/T
serial = bus+F(20, 10**9)*xmax*reads/T
same(reads, 'adaptive', 'reads_upper')
same(repairs, 'adaptive', 'repairs_upper')
same(bus, 'adaptive', 'pure_bus_upper')
same(serial, 'adaptive', 'serial_core_upper')
lower_bus = W*(F(48, 10**9)*xmin-J)*(1/(F('0.626998')+J)-2/T)
same(lower_bus, 'fixed', 'pure_bus_class_lower')
app = cfg['application']
app_count = (T*10**9-1-app['first_ns']-app['read_offset_ns'])//app['epoch_ns']+1
same(app_count, 'common_cost', 'useful_reads')
common_low = (app_count*(F(16, 10**9)*xmin-J)+W*(F(56, 10**9)*xmin-J))/T
common_high = (app_count*(F(16, 10**9)*xmax+J)+W*Cwrite)/T
same(common_low, 'common_cost', 'ECC_and_initial_bus_lower')
same(common_high, 'common_cost', 'ECC_and_initial_bus_upper')
gain = (lower_bus+common_low)/(bus+common_high)
budget5 = (lower_bus+common_low)/5-bus-common_high
same(gain, 'comparison', 'protection_gain_at_u0_with_common_ECC')
same(budget5, 'comparison', 'fivefold_management_budget')
same(lower_bus+common_low-bus-common_high, 'comparison', 'strict_gain_management_budget')
assert F('0.0000288866') <= budget5
assert upper <= F('.000962971178')
assert bus*100 <= F('.194363904')
assert serial*100 <= F('.263066686')
assert lower_bus*100 >= F('.9929628253')
assert common_low*100 >= F('.0015499553')
assert common_high*100 <= F('.0016499854')
assert gain >= F('5.0736852')

print(json.dumps({
    'independent_arithmetic': 'matched; no production imports',
    'Q_upper': float(upper),
    'fixed_bound_literal_3_addition': float(K*d*M2),
    'gain_formal_u_zero': float(gain),
    'control_budget5_bus_microseconds_per_second': float(budget5*10**6),
    'Q_relative_slack': float((epsilon-upper)/epsilon),
    'read_bus_components_microseconds_per_second': {
        key: float(value*R/T*10**6) for key, value in read_counts.items()
    },
    'repair_bus_microseconds_per_second': float(Cwrite*repairs/T*10**6),
}, indent=2))
