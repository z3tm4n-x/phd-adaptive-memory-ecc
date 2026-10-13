"""Small deterministic T141 calculation; never writes to accepted packages."""
import argparse
import csv
import math
from pathlib import Path
import platform
import sys
import numpy as np

from chain import (HERE, ROOT, LEGACY, SEPEM, CFG, BITS, T, OLD, Spectrum,
                   cosrad, raw_table, fold, proton_sigma, envelope, digest,
                   write_json, write_csv, probability_release, load_module,
                   transport, unknown_residual_increment)


def component_rates(rho, model='main_loglog', geometry=1., check_ratio=1.,
                    residual_LET=False, cutoff=32.6, sigma_scale=1.):
    data = {}
    for phase, lfile, pfile in [('background','gl_x.txt','gp_x.txt'), ('solar','sl_x.txt','sp_x.txt')]:
        ls = cosrad(lfile, rho)
        def lsigma(x):
            val = OLD['sb'](x)
            if residual_LET:
                val *= OLD['fr'](x)
            if phase == 'solar':
                val = np.where(x <= cutoff, val, 0.)
            return val
        data[phase] = {'LET_exclusive': fold(ls, lsigma,
            knots=np.r_[.15, OLD['LETpts'], cutoff], check_ratio=check_ratio)}
        for band in ('low','high'):
            response = lambda x: sigma_scale*proton_sigma(x, band, model)
            data[phase]['H_'+band] = fold(cosrad(pfile, rho), response,
                knots=np.r_[transport.SIGMA_E, transport.sigma_module.zero_crossing_low(transport.POINTS),
                            OLD['Epdi'], 5., 10.], geometry=geometry, check_ratio=check_ratio)
    return data


def from_rates(rates, rho, label, exclusive=1., teff=115776., overlap=1., shape=1.):
    names = ['H_low','H_high','LET_exclusive']
    multipliers = np.array([1.,1.,exclusive])
    bg = np.array([rates['background'][n] for n in names])*multipliers
    p = np.array([rates['solar'][n] for n in names])*multipliers
    result = envelope(float(bg.sum()), p, teff*p, names, shape=[shape]*3, overlap=overlap)
    row = {'shield_g_cm2':rho, 'scenario':label,
           **{k:v for k,v in result.items() if k != 'cross_terms'},
           'status':'CONDITIONAL_COVERED_MODEL; physical_total_and_joint_q90_UNKNOWN'}
    return row, result['cross_terms']


def legacy_row(rho, model, full38=True):
    col = {2.5:5,3.:7,3.5:8,4.:9}[rho]
    scale = 38/32 if full38 else 1.
    rates = {}
    for phase, lfile, pfile in [('background','gl_x.txt','gp_x.txt'),('solar','sl_x.txt','sp_x.txt')]:
        x,f = OLD['make_phi'](col, raw_table(lfile))
        if phase == 'solar':
            f = np.where(x <= 32.6, f, 0.)
        ion = float(OLD['rate_naive'](x,f,OLD['sig_nak']))*scale
        sig = lambda e: proton_sigma(e, model=model)
        proton = float(OLD['rate_pl'](col,raw_table(pfile),sig,factor=.5)*2**24*scale)
        rates[phase] = {'LET_exclusive':ion,'H_low':proton,'H_high':0.}
    return from_rates(rates,rho,model)[0]


def discrepancies():
    rows=[]
    for rho in CFG['shield_g_cm2']:
        changes = [
            ('00_data32_HEP','baseline',legacy_row(rho,'historical_HEP',False)),
            ('01_full38_HEP','normalization_38_over_32',legacy_row(rho,'historical_HEP')),
            ('02_v18_PDI','cross_section_historical_PDI',legacy_row(rho,'historical_PDI')),
            ('03_T127_empirical','cross_section_PROTON_main_loglog',legacy_row(rho,'main_loglog')),
            ('04_knotted_integral','quadrature_and_exact_cutoff',from_rates(component_rates(rho,geometry=.5,residual_LET=True),rho,'knots')[0]),
            ('05_total_bit_LET','event_composition_remove_old_fr_subtraction',from_rates(component_rates(rho,geometry=.5),rho,'all_bits')[0]),
            ('06_common_geometry','geometry_proton_half_to_one',from_rates(component_rates(rho),rho,'common')[0])]
        prev = None
        for step,cause,r in changes:
            rows.append(dict(shield_g_cm2=rho,step=step,changed_only=cause,
                b_s_inv=r['background_s_inv'],peak_s_inv=r['peak_upper_s_inv'],
                N_solar=r['N_solar_upper'],S2_s_inv=r['S2_upper_s_inv'],
                delta_S2_s_inv=None if prev is None else r['S2_upper_s_inv']-prev,
                scope='same COSRAD exports; conditional Teff and aggregate LET; ordered attribution'))
            prev=r['S2_upper_s_inv']
    return rows


def spectral_transfer():
    """One-factor comparisons at common support and response, no fitted factors."""
    # gost imports transport by its historical name. It is a pinned dependency.
    sys.modules['transport'] = transport
    gost = load_module('t141_pinned_gost', SEPEM/'gost.py')
    rows=[]
    native=cosrad('sfxm.txt')
    support=native.coordinate<=10000.
    incident=Spectrum(native.coordinate[support],native.density[support],native.variable,
        native.product,native.angular,native.boundary,native.species,native.source)
    # Common finite support is explicit: no invented COSRAD tails.
    for rho in CFG['shield_g_cm2']:
        response=lambda x: proton_sigma(x)
        a=fold(cosrad('sp_x.txt',rho),response,knots=np.r_[transport.SIGMA_E,
            transport.sigma_module.zero_crossing_low(transport.POINTS),5.],geometry=1.)
        b=fold(incident,response,rho=rho)
        # Same spectral nodes/interpolant for a controlled spectrum-only contrast.
        gost_at_nodes=Spectrum(incident.coordinate,
            4*math.pi*gost.spectrum(incident.coordinate,92.5548,'peak_flux'),
            'E_MeV','flux','omni','before_Al','H','GOST2025_at_COSRAD_nodes')
        c=fold(gost_at_nodes,response,rho=rho)
        # Fine direct GOST quadrature is a separate discretization check.
        e,w,_,_=transport.quadrature(transport.RangeTable(),rho,order=24)
        d=float(BITS*4*math.pi*np.dot(w,gost.spectrum(e,92.5548,'peak_flux')))
        n=float(BITS*np.dot(w,gost.spectrum(e,92.5548,'fluence')))
        rows.append(dict(shield_g_cm2=rho,
            COSRAD_postAl_fold_s_inv=a,CSDA_same_COSRAD_incident_s_inv=b,
            transport_delta_s_inv=b-a,CSDA_GOST_same_nodes_s_inv=c,
            spectrum_delta_s_inv=c-b,CSDA_GOST_direct_s_inv=d,
            GOST_marginal_fluence_N=n,diagnostic_marginal_product_s_inv=d*n,
            physical_joint_q90=None,
            scope='incident COSRAD truncated at 10GeV PSTAR limit; postAl support<=10GeV; transport delta includes unknown operator and edge; GOST/COSRAD scenario semantics differ'))
    return rows


def teff_audit():
    p,f=raw_table('sfxm.txt'),raw_table('sfn.txt')
    if not np.array_equal(p[:,0],f[:,0]):
        raise ValueError('Different incident grids')
    if np.any((p[:,1:]==0)&(f[:,1:]>0)):
        raise ValueError('Positive fluence with zero peak')
    rows=[]
    for z in range(1,29):
        valid=p[:,z]>0
        ratios=f[valid,z]/p[valid,z]
        rows.append(dict(Z=z,positive_peak_nodes=int(valid.sum()),
            positive_fluence_nodes=int((f[:,z]>0).sum()),
            max_F_over_p_s=float(ratios.max()) if len(ratios) else None,
            all_peak_supported_fluence_zero=bool(np.all(f[valid,z]==0)),
            same_positive_operator_verified=False))
    return rows


def main(out):
    out.mkdir(parents=True,exist_ok=True)
    disc=discrepancies()
    write_csv(out/'discrepancies.csv',disc)
    numeric=[]; cross=[]; sensitivity=[]; components=[]
    for rho in CFG['shield_g_cm2']:
        rates=component_rates(rho)
        for phase,parts in rates.items():
            for name,value in parts.items():
                components.append(dict(shield_g_cm2=rho,phase=phase,component=name,
                    lambda_s_inv=value,energy_boundary='after_Al_before_BEOL',
                    angular_transfer='1; assumed invariant normal-incidence response',
                    composition='LET exclusive fraction is parameter; H bands disjoint'))
        row,cs=from_rates(rates,rho,'conservative_shape1_geometry1_exclusive1')
        numeric.append(row)
        for c in cs:
            cross.append(dict(shield_g_cm2=rho,**c))
        scenarios=[('nominal',rates,{}),
            ('proton_geometry_0.5',component_rates(rho,geometry=.5),{}),
            ('proton_geometry_2',component_rates(rho,geometry=2.),{}),
            ('check_ratio_0',component_rates(rho,check_ratio=0.),{}),
            ('check_ratio_2',component_rates(rho,check_ratio=2.),{}),
            ('exclusive_LET_fraction_0',rates,{'exclusive':0.}),
            ('exclusive_LET_fraction_0.5',rates,{'exclusive':.5}),
            ('sigma_gap_linear_5_40',component_rates(rho,model='gap_linear_5_40'),{}),
            ('sigma_low_hold',component_rates(rho,model='low_hold'),{}),
            ('sigma_proton_scale_0.5',component_rates(rho,sigma_scale=.5),{}),
            ('sigma_proton_scale_2',component_rates(rho,sigma_scale=2.),{}),
            ('LET_no_solar_cutoff',component_rates(rho,cutoff=200.),{}),
            ('temporal_overlap_0',rates,{'overlap':0.}),
            ('shape_0.5_all_species',rates,{'shape':.5}),
            ('Teff_x2',rates,{'teff':231552.})]
        for label,rr,kwargs in scenarios:
            v,_=from_rates(rr,rho,label,**kwargs)
            sensitivity.append(dict(shield_g_cm2=rho,parameter_case=label,
                S2_s_inv=v['S2_upper_s_inv'],ratio_to_nominal=v['S2_upper_s_inv']/row['S2_upper_s_inv'],
                kind='conditional model sensitivity, NOT confidence interval'))
        # Missing response/secondary processes have no default physical zero.
        for s_u in (1.,100.,1000.,10000.):
            total=row['S2_upper_s_inv']+unknown_residual_increment(row['S2_upper_s_inv'],s_u)
            sensitivity.append(dict(shield_g_cm2=rho,parameter_case=f'unknown_residual_S2_{s_u:g}',
                S2_s_inv=total,ratio_to_nominal=total/row['S2_upper_s_inv'],
                kind='Cauchy envelope for additional exclusive rate; residual S2 is ASSUMPTION'))
    write_csv(out/'components.csv',components)
    write_csv(out/'shield-summary.csv',numeric)
    write_csv(out/'cross-terms.csv',cross)
    write_csv(out/'sensitivity.csv',sensitivity)
    write_csv(out/'spectra-transfer.csv',spectral_transfer())
    write_csv(out/'Teff-by-species.csv',teff_audit())
    conditions=__import__('json').loads((HERE/'conditions.json').read_text(encoding='utf-8'))
    contract=dict(schema='t141.radiation-chain.v1',task=141,accepted_base=CFG['accepted_base'],
        status='DRAFT_CONDITIONAL_MODEL_WITH_EXPLICIT_PHYSICAL_GAPS',
        horizon_s=T,words=CFG['words'],data_bits=32,check_bits=6,
        lambda_definition='first moment of bit inversions per second over the full array; NOT parent or ERR rate',
        units={'lambda':'s^-1','N':'expected bit inversions','S2':'s^-1','sigma_bit':'cm^2/bit',
               'proton_energy':'MeV before BEOL','LET':'MeV cm^2/mg'},
        partitions=['H: E_pre_BEOL<5 MeV','H: E_pre_BEOL>=5 MeV',
                    'non-H exclusive remainder of aggregate LET, includes He; no separate He addition'],
        proton_mechanism_separation='energy partition only; within-band mechanism fractions UNKNOWN',
        design_probability={'Pi':.1,'definition':'Pr[S2_actual(T)>S2_design | specified physical model and mission class]',
            'horizon_s':T,'verified_joint_coverage':False,
            'marginal_products_are_quantiles':False,'physical_q90_s_inv':None,
            'release_requires':['joint scalar/spectral coverage','physical response/transfer','rare-tail control'],
            'union_budget_example':{'peak':.05,'fluence':.05,
                'scope':'only if these are genuine scalar bounds over the same mission and all other conditions fixed; not available here'},
            'hypothetical_two_SCALAR_marginal_Pi_0p1_joint_coverage_lower_bound':.8,
            'pointwise_spectral_quantiles_do_not_automatically_bound_a_convolution':True},
        scenarios=numeric,conditions=conditions,
        physical_unresolved={'additional_exclusive_species_or_secondaries_rate':None,
            'full38_Dstar':None,'ERR_lower_informativeness':None,'joint_S2_q90':
              probability_release(False,False,False,numeric[1]['S2_upper_s_inv']),
            'full38_grouped_parent_law':None},
        parameter_rules={'check_bit_response':'W*(32+6*r_check), once',
            'exclusive_LET':'q*LET_export, 0<=q<=1; response-weighted apportionment assumption, not species identification',
            'additional_rate':'S2_total <= (sqrt(S2_covered)+sqrt(S2_unknown))^2',
            'subbin_variance':'S2_true = S2_300s + sum integral(lambda-lambda_binmean)^2; no finite upper without an extra bound',
            'Dstar_and_ERR':'separate unknown inputs; never derived from sigma_bit'},
        profile_model={'summary':'profile-missions.csv','same_input_shape_transfer':'shape-transfer.csv',
            'chronology':'nonoverlapping packed RDS histories; remaining time uses outside-mask moments',
            'H_baseline':'p10 removed proportionally from bands; constant COSRAD GCR added',
            'ion_time_law':'HI_exclusive(t)=COSRAD_peak_ratio*H_excess(t), an unverified assumption',
            'unknown_ion_correlation':'main envelope uses Cauchy/peak-integral cap; sensitivity varies extra event overlap',
            'statistical_intervals':'order statistics MC only, fixed empirical population; no physical coverage',
            'saved_sha256':{n:digest(out/n) for n in ('profile-missions.csv','shape-transfer.csv','profile-provenance.json') if (out/n).is_file()}},
        differences_from_R0A={'accepted_S2_s_inv':6940.,'accepted_b_s_inv':.000154704,
            'accepted_solar_peak_s_inv':.244528,'accepted_B_s_inv':.244682704,
            'accepted_solar_N_upper':115776*.244528,'accepted_scope':'conditional declared Lambda/Theta, not unconditional physical coverage',
            'accepted_full38_Dstar_axis':.0002802445,'new_Dstar_inferred':False,'replacement_authorized':False,
            'response':'full experimental proton curve; total-bit LET without residual fr subtraction',
            'geometry':'proton factor1 in main sensitivity model vs historical0.5',
            'joint_probability':'not established by marginal Pi=.1 exports',
            'A2_per_bit_law_changed':False,'old_probability_or_cost_conclusions_transferred':False})
    write_json(out/'contract.json',contract)
    inputs=list((LEGACY/'inputs/cosrad_main').glob('*.txt'))+[
        LEGACY/'inputs/calc_v18.zip',LEGACY/'inputs/article-cy62167-v21.docx',LEGACY/'source_inputs.json',
        SEPEM/'transport.py',SEPEM/'gost.py',SEPEM/'inputs/nist_pstar_al.csv',
        SEPEM/'inputs/gost_selected_coefficients.csv',SEPEM/'config.json',
        ROOT/'experiments/RE-CY62167-PROTON-01/sigma_bit_experimental.csv',
        ROOT/'experiments/RE-GOES19-PROTON-RATE-01/sigma_model.py',
        ROOT/'experiments/t127-cy62167-pdi/outputs/shield-conditional.csv',
        ROOT/'experiments/t127-cy62167-pdi/outputs/inputs-126.json',
        ROOT/'experiments/t113-onset-growth/outputs/handoff.json',
        ROOT/'experiments/t126-regime-map/ANCHORS.md',ROOT/'theory/t73-burst-mode-count-inputs.json']
    write_json(out/'provenance.json',dict(accepted_base=CFG['accepted_base'],
        python=platform.python_version(),numpy=np.__version__,scipy=__import__('scipy').__version__,
        inputs_sha256={p.relative_to(ROOT).as_posix():digest(p) for p in inputs},
        code_sha256={p.name:digest(p) for p in [HERE/'chain.py',HERE/'calculate.py',HERE/'config.json',HERE/'conditions.json']},
        output_sha256={n:digest(out/n) for n in ('discrepancies.csv','components.csv','shield-summary.csv',
            'cross-terms.csv','sensitivity.csv','spectra-transfer.csv','Teff-by-species.csv','contract.json')}))
    print('T141 deterministic package:',len(numeric),'shields;',len(disc),'ordered discrepancy rows')


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--out',type=Path,default=HERE/'outputs')
    main(parser.parse_args().out)
