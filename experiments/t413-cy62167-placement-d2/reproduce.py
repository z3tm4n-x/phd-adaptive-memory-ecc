"""Reproduce the D2 handoff from the pinned repository and 14 Zenodo proton files."""
import argparse
import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from contextlib import ExitStack
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXP = ROOT / 'experiments'
CODE = EXP / 't186-method-comparison/code-strength'
PROTON = EXP / 'RE-CY62167-PROTON-01'
OBS = EXP / 'RE-CY62167-DISTANT-MCU-OBSERVABILITY-01'
MAPPING = EXP / 'RE-CY62167-ADDRESS-MAPPING-01'
MAP_INPUT = EXP / 'regime-map-methodology-20261019/predictability-volume-20261028/inputs.json'
M_CERT = ROOT / 'theory/t196-c01-direct-certificate-20261029/result.json'
L_CERT = EXP / 't331-window-reset-20261030/result.json'
CALENDAR = EXP / 'article-v-mcu-budget-20261105/results.json'
sys.path.insert(0, str(CODE))
sys.path.insert(0, str(PROTON))
sys.path.insert(0, str(MAPPING))
from codec import Code
from parse_zenodo_protons import parse_cluster_file, physical_records
from address_mapping_gf2 import predict_address


def load_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def packing(t):
    codec = Code(t)
    beats = []
    for beat in range(3):
        roles = {'data': [], 'check': [], 'unused': []}
        for lane in range(16):
            index = 16 * beat + lane
            encoded = [0, 0, 0]
            encoded[beat] = 1 << lane
            if index < codec.n:
                assert tuple(encoded) == codec.pack16(1 << index)
                assert codec.unpack16(encoded) == 1 << index
                role = 'check' if index in codec.parity_positions else 'data'
            else:
                assert codec.unpack16(encoded) == 0
                role = 'unused'
            roles[role].append(lane)
        beats.append({'beat': beat, 'lanes': roles})
    assert sum(len(b['lanes']['data']) for b in beats) == 32
    assert sum(len(b['lanes']['unused']) for b in beats) == 48 - codec.n
    return {'n': codec.n, 'check_indices': list(codec.parity_positions), 'beats': beats}


def mark(n, sites):
    """Project one atomic physical XOR support given as (global x16 address, lane)."""
    positions = set()
    for address, lane in sites:
        assert address >= 0 and 0 <= lane < 16
        word, beat = divmod(address, 3)
        index = 16 * beat + lane
        if index < n:
            positions.add((word, index))
    word_weights = Counter(w for w, _ in positions)
    maximum = max(word_weights.values(), default=0)
    return {'positions_w_i': [list(p) for p in sorted(positions)], 'm_bits': len(positions),
            'K_words': len(word_weights), 'B1_once': int(maximum >= 2),
            'B2_once': int(maximum >= 3)}


def archived_geometry(path):
    manifest = load_json(OBS / 'input_manifest.json')['raw_inputs']
    with (OBS / 'cluster_span_by_energy.csv').open(encoding='utf-8') as source:
        published = {row['source_file']: row for row in csv.DictReader(source)}
    rows, witness = [], []
    with ExitStack() as stack:
        if path.is_dir():
            files = {entry['file']: path / entry['file'] for entry in manifest}
        else:
            archive = stack.enter_context(zipfile.ZipFile(path))
            names = archive.namelist()
            files = {}
            for entry in manifest:
                name = entry['file']
                members = [key for key in names if Path(key).name == name]
                if len(members) != 1:
                    raise ValueError(f'Expected one archive member {name}, found {members}')
                files[name] = zipfile.Path(archive, members[0])
        for entry in manifest:
            name = entry['file']
            source = files[name]
            if hashlib.sha256(source.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError(f'Zenodo member differs from accepted SHA-256: {name}')
            totals = Counter()
            for record in physical_records(parse_cluster_file(source)):
                cells = {(cell.x, cell.y) for cell in record.cells}
                xs, ys = zip(*cells)
                bounds = (min(xs), max(xs), min(ys), max(ys))
                assert bounds == (record.xmin, record.xmax, record.ymin, record.ymax)
                span = max(bounds[1] - bounds[0], bounds[3] - bounds[2])
                totals['registered_clusters'] += 1
                totals['recorded_cell_rows'] += record.k
                totals['K2_clusters'] += record.k == 2
                totals['K2_dinf_gt3'] += record.k == 2 and span > 3
                totals['Kge3_clusters'] += record.k >= 3
                totals['w16_exact_candidate_event_count'] += any(
                    (x+16, y) in cells or (x, y+16) in cells for x, y in cells)
                if name == 'clust_p4MeV.txt' and record.segment_id == 1 and record.cluster_id in (985, 986):
                    witness.append({'cluster_id': record.cluster_id, 'segment': record.segment_id,
                                    'line': record.line_start, 'clock': record.timestamp_raw,
                                    'cells_A_x_y': [[c.field0_raw, c.x, c.y] for c in record.cells]})
            for key, count in totals.items():
                if key != 'recorded_cell_rows' and count != int(published[name][key]):
                    raise ValueError(f'Geometry disagrees for {name}: {key}')
            rows.append({'file': name, 'sha256': entry['sha256'], **totals})
    assert len(rows) == 14 and [r['cluster_id'] for r in witness] == [985, 986]
    assert witness[0]['clock'] == witness[1]['clock'] == '21:00:01'
    return rows, witness


def wiring_witness(records):
    """Two explicit conditional bank layouts for the *same* recorded cells on die 0."""
    masks = load_json(MAPPING / 'address_mapping_coefficients.json')['coefficient_masks_lsb_feature_order']
    scenarios = {}
    for layout in ('contiguous_die_addresses', 'interleaved_dies_per_beat'):
        groups = []
        for record in records:
            sites = []
            for byte_address, x, y in record['cells_A_x_y']:
                assert predict_address(x, y, masks) == byte_address
                # An explicit bijection to x16 lanes for this example, not the vendor wiring.
                half, local = divmod(byte_address, 2**20)
                lane = 8 * half + (x >> 4) % 8
                global_address = local if layout == 'contiguous_die_addresses' else 3 * local
                sites.append((global_address, lane))
            groups.append(sites)
        separate = [mark(39, sites) for sites in groups]
        merged = mark(39, groups[0] + groups[1])
        scenarios[layout] = {'two_parents': separate, 'one_parent': merged}
    contiguous = scenarios['contiguous_die_addresses']
    assert [v['K_words'] for v in contiguous['two_parents']] == [2, 1]
    assert sum(v['B1_once'] for v in contiguous['two_parents']) == 0
    assert contiguous['one_parent']['K_words'] == 2 and contiguous['one_parent']['B1_once'] == 1
    striped = scenarios['interleaved_dies_per_beat']['one_parent']
    assert striped['K_words'] == 3 and striped['B1_once'] == 0
    return scenarios


def budgets():
    source = load_json(MAP_INPUT)
    env = source['environment']
    m_cert = load_json(M_CERT)
    eps = Fraction(m_cert['epsilon'])
    words = m_cert['words']
    horizon = source['bank']['mission_s']
    s1 = Fraction(env['b']) * horizon + Fraction(env['Fs'])
    assert words == 2**20 and m_cert['alpha'] == '0'
    assert s1 == Fraction('77131.343232') and horizon == int(m_cert['mission_s'])
    inversions = s1 * 39 * words / env['reference_positions']
    l_margin = Fraction(load_json(L_CERT)['values']['physical_margin']['exact'])
    own_calendar = next(r for r in load_json(CALENDAR)['rows'] if r['P_exact_s'] == '86/5')
    anchors = []
    for value, origin in [(Fraction(0), 'singleton embedding or structural exclusion of same-word pairs'),
                          (Fraction('1e-5'), 'issue 413 sensitivity near the existing c01 M and L_cut margins'),
                          (Fraction('1e-4'), 'issue 413 sensitivity at ten percent of epsilon')]:
        anchors.append({'D1_upper_parents_per_bank_T': str(value),
                        'share_of_epsilon_first_moment': str(value / eps),
                        'sufficient_f1_at_unknown_mbar_exact': str(value / inversions),
                        'origin': origin, 'status': 'CONDITIONAL', 'is_test_derived': False})
    return {'W': words, 'T_s': horizon, 'epsilon': str(eps), 'S1_reference': str(s1),
            'anchor_semantics': 'upper limits on E[N_B1(T)] over the admitted class, not exact measured intensities',
            'normalization': 'per active position per second: (p+r)/(38*524288) for both code projections',
            'to_determine_for_t2': ['bank-level D2 for n=44', 'residual size-1 and size-2 group rates and position unions'],
            'reference_bit_count': env['reference_positions'], 'F_b39_inversions': str(inversions),
            'trivial_upper_E_N_B1_from_F_b_only': str(inversions/2),
            'particle_fraction_denominator': 'expected nonempty parents in bank over T',
            'anchors': anchors,
            'old_headroom_for_scale_only': {'c01_M': str(eps - Fraction(m_cert['Q_upper'])),
                 'c01_L_cut': str(l_margin), 'separate_PR388_17_2s': own_calendar['p_D_allow_exact']}}


def handoff(raw):
    bus = load_json(CODE / 'common-input.json')['bus']
    assert bus['address'] == '3*word + beat' and bus['width_bits'] == 16
    geometry, records = archived_geometry(raw)
    layouts = wiring_witness(records)
    # A parent dangerous in two words is charged once. Added 44-only positions matter for t=2.
    assert mark(39, [(0,0),(0,1),(3,0),(3,1)])['B1_once'] == 1
    extra_sites = [(2,7),(2,8),(2,9)]
    extra39, extra44 = mark(39, extra_sites), mark(44, extra_sites)
    assert extra39['K_words'] == 0 and extra44['B2_once'] == 1
    with (OBS/'cross_cluster_diagnostics.csv').open(encoding='utf-8') as source:
        diagnostic = next(r for r in csv.DictReader(source) if r['energy_mev']=='4.0' and r['dt_class']=='same_bin')
    first, other = records
    # Distant cells in two different blocks with a single readout label.
    assert first['cells_A_x_y'][0][1:] == [6, 1738] and other['cells_A_x_y'][0][1:] == [6, 1754]
    sources = [CODE/'codec.py', CODE/'common-input.json', EXP/'t187-code-strength/model.py', MAP_INPUT,
               OBS/'input_manifest.json', OBS/'cluster_span_by_energy.csv', OBS/'cross_cluster_diagnostics.csv',
               OBS/'observation_contract.json', MAPPING/'address_mapping_coefficients.json',
               MAPPING/'address_mapping_gf2.py', MAPPING/'address_mapping_data.py',
               PROTON/'parse_zenodo_protons.py', M_CERT, L_CERT, CALENDAR]
    return {'task': '413 D2', 'base': '3a4f0e1044218d0501c17ce24e14342cfc871a3b',
            'D1_source': '46ac00ea5d39c4ba2157f6bc9be3f9cf13c4e763',
            'archive_DOI': '10.5281/zenodo.8314389', 'packing': [packing(1), packing(2)],
            'observed_proton_records_by_file': geometry,
            'totals': {key: sum(row[key] for row in geometry) for key in (
                'registered_clusters','recorded_cell_rows','K2_clusters','K2_dinf_gt3',
                'Kge3_clusters','w16_exact_candidate_event_count')},
            'raw_distant_records': records,
            'published_same_bin_exact16_4MeV': {k: diagnostic[k] for k in (
                'observed_w16_exact_cell_pairs','expected_independent_w16_exact_cell_pairs','exact16_obs_over_expected')},
            'conditional_projections_of_same_records': layouts,
            'synthetic_slots_39_40_41': {'n39': extra39, 'n44': extra44},
            'D3_input': budgets(), 'test_derived_lifetime_upper': None,
            'physical_parent_K_distribution': None, 'identified_K_given_m': 'ceil(m/n)..min(m,W) including empty at m=0',
            'source_sha256_LF': {p.relative_to(ROOT).as_posix(): hashlib.sha256(
                p.read_bytes().replace(b'\r\n',b'\n')).hexdigest() for p in sources}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', required=True, type=Path, help='Zenodo 8314389 zip or directory of original files')
    parser.add_argument('--check', action='store_true', help='Compare with the published handoff without writing')
    args = parser.parse_args()
    result = handoff(args.archive)
    target = HERE/'handoff.json'
    if args.check:
        if result != load_json(target):
            raise SystemExit('D2 handoff differs from published data')
    else:
        target.write_bytes((json.dumps(result, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))
    print('PASS: 14 source hashes and per-file geometry, both packings, distant-record ambiguity and D2 anchors')
    print(json.dumps(result['totals']))


if __name__ == '__main__':
    main()
