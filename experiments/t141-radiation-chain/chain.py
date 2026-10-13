"""T141: explicit interfaces and nonnegative first/second moments.

This is a conditional response calculation, not a physical device qualification.
The two proton partitions are disjoint ENERGY bands of a total measured curve;
they are not a measured separation of nuclear and direct-ionization mechanisms.
"""
from dataclasses import dataclass
from pathlib import Path
import ast
import csv
import hashlib
import importlib.util
import json
import math
import sys
import zipfile

import numpy as np
from numpy.polynomial.legendre import leggauss

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
LEGACY = ROOT / 'experiments/t68-v21-inputs'
SEPEM = ROOT / 'experiments/tNN-sepem-profiles'
CFG = json.loads((HERE/'config.json').read_text(encoding='utf-8'))
BITS = CFG['words'] * (CFG['data_bits'] + CFG['check_bits'])
T = CFG['mission_s']


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


transport = load_module('t141_pinned_transport', SEPEM/'transport.py')


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n',
                    encoding='utf-8', newline='\n')


def write_csv(path, rows):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


def nonnegative(x, name):
    a = np.asarray(x, dtype=float)
    if not np.isfinite(a).all() or np.any(a < 0):
        raise ValueError(name + ' must be finite and nonnegative')
    return a


@dataclass(frozen=True)
class Spectrum:
    coordinate: np.ndarray
    density: np.ndarray
    variable: str  # E_MeV or LET_MeV_cm2_mg
    product: str  # flux or fluence
    angular: str  # per_sr or omni
    boundary: str  # before_Al or after_Al_before_BEOL
    species: str
    source: str

    def __post_init__(self):
        x = nonnegative(self.coordinate, 'coordinate')
        y = nonnegative(self.density, 'density')
        if x.ndim != 1 or len(x) < 2 or x.shape != y.shape or np.any(np.diff(x) <= 0) or x[0] <= 0:
            raise ValueError('Invalid spectral grid')
        if self.product not in ('flux', 'fluence') or self.angular not in ('per_sr', 'omni'):
            raise ValueError('Explicit product and angular units required')
        if self.boundary not in ('before_Al', 'after_Al_before_BEOL'):
            raise ValueError('Unsupported energy boundary; BEOL is already in measured response')
        if self.variable not in ('E_MeV', 'LET_MeV_cm2_mg'):
            raise ValueError('Explicit supported coordinate units required')

    def solid_angle(self):
        return 4*math.pi if self.angular == 'per_sr' else 1.0


def power_interpolation(x, nodes, values, zero_rule='linear'):
    """No extrapolation. Log-log positive endpoints; specified zero rule."""
    x = np.asarray(x, float)
    if np.any(x < nodes[0]*(1-1e-14)) or np.any(x > nodes[-1]*(1+1e-14)):
        raise ValueError('Spectrum extrapolation requires an explicit model')
    k = np.clip(np.searchsorted(nodes, x, side='right')-1, 0, len(nodes)-2)
    f = np.log(x/nodes[k])/np.log(nodes[k+1]/nodes[k])
    a, b = values[k], values[k+1]
    positive = (a > 0) & (b > 0)
    if zero_rule == 'legacy_floor':
        y = np.exp(np.log(np.maximum(a, 1e-300))*(1-f)+np.log(np.maximum(b, 1e-300))*f)
        return np.where(y < 1e-290, 0., y)
    y = a*(1-f)+b*f
    y[positive] = np.exp(np.log(a[positive])*(1-f[positive])+np.log(b[positive])*f[positive])
    return np.maximum(y, 0.)


def quadrature(cuts, order=24):
    cuts = np.unique(cuts)
    z, w = leggauss(order)
    lo, hi = cuts[:-1], cuts[1:]
    return (((lo[:, None]+hi[:, None])/2+(hi-lo)[:, None]*z/2).ravel(),
            ((hi-lo)[:, None]*w/2).ravel())


def fold(spectrum, response, knots=(), geometry=1., check_ratio=1., rho=None, order=24):
    """Return bit inversions/s (flux) or expected bit inversions (fluence).

    A scalar geometry factor is a declared transfer sensitivity, not a measured
    angular response. Check-bit count and solid angle enter exactly here once.
    Incident integration preserves dEin, avoiding a missing transport Jacobian.
    """
    nonnegative([geometry, check_ratio], 'response scales')
    x, y = spectrum.coordinate, spectrum.density
    if rho is not None:
        if spectrum.boundary != 'before_Al' or spectrum.variable != 'E_MeV' or spectrum.species != 'H':
            raise ValueError('CSDA accepts only incident H, never retransports an export')
        if not math.isfinite(rho) or rho < 0:
            raise ValueError('Invalid shielding')
        table = transport.RangeTable()
        extra = table.inverse(rho+table.range(np.r_[.001, transport.SIGMA_E,
                               transport.sigma_module.zero_crossing_low(transport.POINTS), table.energy]))
        cuts = np.r_[x, table.energy, extra, table.inverse(rho)]
    else:
        if spectrum.boundary != 'after_Al_before_BEOL':
            raise ValueError('Incident spectra require an explicit transfer')
        cuts = np.r_[x, knots]
    if spectrum.variable == 'E_MeV':
        # Legacy zero->positive intervals use a 1e-300 log floor. Their very
        # large slopes need internal cuts; resolving only endpoint knots is
        # insufficient even at Gauss order24. Keep the declared interpolant.
        for k in range(len(x)-1):
            if (y[k] == 0) != (y[k+1] == 0):
                jumps = abs(math.log(max(y[k+1],1e-300)/max(y[k],1e-300)))
                pieces = max(1, math.ceil(jumps/8))
                cuts = np.r_[cuts, np.geomspace(x[k],x[k+1],pieces+1)]
    cuts = cuts[(cuts >= x[0]) & (cuts <= x[-1])]
    e, w = quadrature(cuts, order)
    f = power_interpolation(e, x, y, 'legacy_floor' if spectrum.variable == 'E_MeV' else 'linear')
    residual = table.residual(e, rho) if rho is not None else e
    sigma = nonnegative(response(residual), 'cross section')
    count = CFG['words'] * (CFG['data_bits'] + CFG['check_bits']*check_ratio)
    return float(count*spectrum.solid_angle()*geometry*np.dot(w, f*sigma))


def raw_table(name):
    rows = []
    for line in (LEGACY/'inputs/cosrad_main'/name).read_text().splitlines():
        try:
            row = [float(v) for v in line.split()]
        except ValueError:
            continue
        if len(row) in (10, 29):
            rows.append(row)
    return np.asarray(rows)


def cosrad(name, rho=None):
    tab = raw_table(name)
    col = 1 if rho is None else {2.5: 5, 3.: 7, 3.5: 8, 4.: 9}[rho]
    let = name in ('gl_x.txt', 'sl_x.txt')
    return Spectrum(tab[:, 0]/1000 if let else tab[:, 0],
                    tab[:, col]*1000 if let else tab[:, col],
                    'LET_MeV_cm2_mg' if let else 'E_MeV',
                    'fluence' if name == 'sfn.txt' else 'flux', 'omni',
                    'before_Al' if rho is None else 'after_Al_before_BEOL',
                    'aggregate_LET_UNRESOLVED' if let else 'H', name)


def legacy_functions():
    # Only inspected function definitions and the two PDI arrays are evaluated.
    ns = dict(np=np, math=math, Nbits=2**24, ssat=2.6e-7, L0w=.15, W=70., h=1.2,
              LETpts=np.array([5.2,15,17,22,27,29,33,42,57]),
              frac=np.array([1,1,1,1,1,1,1,16969/17012,21058/21185]))
    files = {'spectra_lib.py': {'make_phi','trapz','rate_naive'},
             'orbital.py': {'sb','fr','sig_nak','sig_p_710'},
             'sep.py': {'sig_p_pdi','rate_pl'}}
    with zipfile.ZipFile(LEGACY/'inputs/calc_v18.zip') as z:
        for f, names in files.items():
            tree = ast.parse(z.read(f).decode())
            nodes = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names]
            if {n.name for n in nodes} != names:
                raise ValueError('Legacy API changed')
            if f == 'sep.py':
                arrays = [n for n in tree.body if isinstance(n, ast.Assign)
                          and all(isinstance(t, ast.Name) and t.id in ('Epdi','Spdi') for t in n.targets)]
                if len(arrays) != 2:
                    raise ValueError('Legacy PDI anchors changed')
                nodes = arrays+nodes
            exec(compile(ast.Module(body=nodes, type_ignores=[]), f, 'exec'), ns)
    return ns


OLD = legacy_functions()


def proton_sigma(e, band='full', model='main_loglog'):
    e = np.asarray(e, float)
    out = np.zeros_like(e)
    keep = e > 0
    if model == 'historical_HEP':
        out = OLD['sig_p_710'](e)
    elif model == 'historical_PDI':
        out = OLD['sig_p_pdi'](e)
    else:
        out[keep] = transport.sigma_module.sigma_hat(e[keep], transport.POINTS, model)
    if band == 'low':
        out[e >= CFG['proton_split_pre_BEOL_MeV']] = 0.
    elif band == 'high':
        out[e < CFG['proton_split_pre_BEOL_MeV']] = 0.
    elif band != 'full':
        raise ValueError('Unknown proton response partition')
    return out


def validate_components(names):
    allowed = {'H_full', 'H_low', 'H_high', 'LET_exclusive', 'He', 'Z_ge3'}
    if len(set(names)) != len(names) or not set(names) <= allowed:
        raise ValueError('Duplicate/unknown components')
    if 'H_full' in names and {'H_low', 'H_high'} & set(names):
        raise ValueError('Full proton response already includes both energy partitions')
    if 'LET_exclusive' in names and {'He', 'Z_ge3'} & set(names):
        raise ValueError('LET aggregate must not be combined with separately included ions')


def envelope(background, peak, exposure, names, duration=T, shape=None, overlap=1.):
    """Conditional deterministic bound from scalar component peak and integral.

    No independence assumption. Cij <= min(sqrt(Si Sj), pi Nj, pj Ni).
    Shape<1 or overlap<1 requires its own physical/temporal assumption.
    """
    validate_components(names)
    p, n = nonnegative(peak, 'peak'), nonnegative(exposure, 'exposure')
    if p.shape != n.shape or p.ndim != 1 or len(p) != len(names):
        raise ValueError('Mismatched moments')
    nonnegative([background, duration], 'time/background')
    if duration <= 0 or np.any(n > p*duration*(1+1e-12)):
        raise ValueError('Exposure incompatible with a peak over the horizon')
    r = np.ones(len(p)) if shape is None else nonnegative(shape, 'shape')
    if r.shape != p.shape or np.any(r > 1) or not 0 <= overlap <= 1:
        raise ValueError('Invalid shape/overlap')
    s = r*p*n
    if np.any(s+1e-9 < n*n/duration):
        raise ValueError('Shape violates Cauchy lower bound')
    cross = []
    for i in range(len(p)):
        for j in range(i+1, len(p)):
            c = overlap*min(math.sqrt(s[i]*s[j]), p[i]*n[j], p[j]*n[i])
            cross.append({'left': names[i], 'right': names[j], 'twice_integral_s_inv': 2*c})
    quiet = background**2*duration
    mixed = 2*background*float(n.sum())
    total = quiet+mixed+float(s.sum())+sum(c['twice_integral_s_inv'] for c in cross)
    return dict(background_s_inv=float(background), peak_upper_s_inv=float(background+p.sum()),
                N_solar_upper=float(n.sum()), N_total_upper=float(background*duration+n.sum()),
                S2_background_s_inv=float(quiet), S2_background_solar_s_inv=float(mixed),
                S2_solar_diagonal_s_inv=float(s.sum()),
                S2_solar_cross_s_inv=float(sum(c['twice_integral_s_inv'] for c in cross)),
                S2_upper_s_inv=float(total), cross_terms=cross)


def timeseries_moments(rates, dt, background=0.):
    """All rates share the SAME bins. Gram matrix retains every cross term."""
    x = nonnegative(rates, 'rates')
    if x.ndim != 2 or x.shape[0] == 0 or not math.isfinite(dt) or dt <= 0:
        raise ValueError('Nonempty common time axis required')
    nonnegative(background, 'background')
    n = x.sum(axis=0)*dt
    gram = x.T@x*dt
    total = x.sum(axis=1)+background
    return dict(duration_s=len(x)*dt, N_components=n.tolist(), gram_s_inv=gram.tolist(),
                peak_s_inv=float(total.max()), N=float(total.sum()*dt),
                S2_s_inv=float(total@total*dt))


def unknown_residual_increment(known_S2, residual_S2):
    nonnegative([known_S2, residual_S2], 'second moments')
    return residual_S2+2*math.sqrt(known_S2*residual_S2)


def probability_release(joint_coverage, physical_transfer, rare_tail, value):
    """Fail closed: deterministic/scenario arithmetic is not a mission quantile."""
    if joint_coverage is not True or physical_transfer is not True or rare_tail is not True:
        return None
    return float(value)
