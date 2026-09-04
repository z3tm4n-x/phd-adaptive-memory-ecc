from __future__ import annotations
import hashlib, io, re, zipfile
from dataclasses import dataclass
from pathlib import Path
import numpy as np

COSRAD_SHA256='84b578195499782bb70570dc1dd6d492711a3f6e7f167528912295bf6a2e7beb'
SHIELDS=np.array([1.50,1.75,2.00,2.25,2.50,2.75,3.00,3.50,4.00],float)
THRESHOLDS=np.array([0.15,0.5,1,2,3,5,10,20,25,30,33,40],float)
TAGS={0.15:'015',0.5:'05',1:'1',2:'2',3:'3',5:'5',10:'10',20:'20',25:'25',30:'30',33:'33',40:'40'}
EXPECTED_ENV=['gd_x.txt','gfn.txt','gfx.txt','gfxm.txt','gl_x.txt','gn_x.txt','gp_x.txt','sd_x.txt','sfn.txt','sfx.txt','sfxm.txt','sl_x.txt','sn_x.txt','sp_x.txt']
EXPECTED_FILES=sorted(EXPECTED_ENV+[f'gw_x_{TAGS[t]}.txt' for t in THRESHOLDS]+[f'sw_x_{TAGS[t]}.txt' for t in THRESHOLDS])

@dataclass
class Spectrum:
    filename:str
    text:str
    x:np.ndarray
    values:np.ndarray
    shields:np.ndarray

@dataclass
class UnitResponse:
    filename:str
    environment:str
    declared_threshold:float
    printed_threshold:float
    bit:float
    sigma_m_cm2:float
    shields:np.ndarray
    proton_rate:np.ndarray
    ion_rate:np.ndarray
    sum_rate:np.ndarray
    text:str

@dataclass
class Package:
    path:Path
    sha256:str
    members:list[dict]
    spectra:dict[str,Spectrum]
    responses:dict[tuple[str,float],UnitResponse]
    texts:dict[str,str]


def sha256_bytes(b:bytes)->str:
    return hashlib.sha256(b).hexdigest()

def sha256_path(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''): h.update(chunk)
    return h.hexdigest()

def _basename(name:str)->str: return Path(name).name

def numeric_table(text:str,ncols:int)->np.ndarray:
    rows=[]
    for line in text.splitlines():
        p=line.split()
        if len(p)!=ncols: continue
        try: row=[float(v) for v in p]
        except ValueError: continue
        rows.append(row)
    if not rows: raise ValueError(f'no {ncols}-column numeric table found')
    return np.asarray(rows,float)

def parse_spectrum(filename:str,text:str)->Spectrum:
    tab=numeric_table(text,10)
    return Spectrum(filename,text,tab[:,0],tab[:,1:],SHIELDS.copy())

def _grab_float(text:str,pattern:str)->float:
    m=re.search(pattern,text,re.I)
    if not m: raise ValueError('header field not found: '+pattern)
    return float(m.group(1))

def parse_response(filename:str,text:str,declared_threshold:float,environment:str)->UnitResponse:
    tab=numeric_table(text,4)
    printed=_grab_float(text,r'LET\s+thresshold\s*=\s*([0-9.+\-Ee]+)')
    bit=_grab_float(text,r'Bit\s*=\s*([0-9.+\-Ee]+)')
    sig=_grab_float(text,r'cross\s+section\s*=\s*([0-9.+\-Ee]+)')
    return UnitResponse(filename,environment,float(declared_threshold),printed,bit,sig,tab[:,0],tab[:,1],tab[:,2],tab[:,3],text)

def load_package(path:Path|str,verify_sha:bool=True)->Package:
    path=Path(path)
    digest=sha256_path(path)
    if verify_sha and digest!=COSRAD_SHA256:
        raise ValueError(f'COSRAD ZIP SHA mismatch: {digest}')
    texts={}; members=[]
    with zipfile.ZipFile(path) as z:
        infos=sorted((i for i in z.infolist() if not i.is_dir()),key=lambda i:_basename(i.filename))
        for i in infos:
            raw=z.read(i.filename); name=_basename(i.filename)
            texts[name]=raw.decode('utf-8','strict')
            members.append({'archive_path':i.filename,'filename':name,'byte_size':len(raw),'sha256':sha256_bytes(raw)})
    names=sorted(texts)
    if names!=EXPECTED_FILES:
        missing=sorted(set(EXPECTED_FILES)-set(names)); extra=sorted(set(names)-set(EXPECTED_FILES))
        raise ValueError(f'unexpected COSRAD member set; missing={missing}; extra={extra}')
    spectra={n:parse_spectrum(n,texts[n]) for n in ['gl_x.txt','gp_x.txt','sl_x.txt','sp_x.txt']}
    responses={}
    for env,prefix in [('GCR','gw'),('SEP','sw')]:
        for t in THRESHOLDS:
            n=f'{prefix}_x_{TAGS[t]}.txt'
            responses[(env,float(t))]=parse_response(n,texts[n],float(t),env)
    return Package(path,digest,members,spectra,responses,texts)

def scenario_manifest(pkg:Package)->dict:
    gl=pkg.texts['gl_x.txt']; sl=pkg.texts['sl_x.txt']
    def contains(t,s):
        if s not in t: raise ValueError(f'scenario token not found: {s}')
    for s in ['36000','Inclination = 0.0','Argument of perigee = 0.0','Flight time=10 year(s)','Solar  cycle number - even','Solar cycle - mean']:
        contains(gl,s)
    for s in ['36000','Inclination = 0.0','Argument of perigee = 0.0','Flight time = 10 year(s)','Probability = 0.100','Solar cycle - mean']:
        contains(sl,s)
    for r in pkg.responses.values():
        if len(r.shields)!=9 or not np.allclose(r.shields,SHIELDS): raise ValueError('unit-response shield grid mismatch')
        if not np.isclose(r.bit,1.0) or not np.isclose(r.sigma_m_cm2,1.0): raise ValueError('unit-response Bit/sigma_m mismatch')
        if 'Thin sensitive volume' not in r.text: raise ValueError('thin-sensitive-volume marker missing')
    rounding=[]
    for env in ['GCR','SEP']:
        for t in THRESHOLDS:
            r=pkg.responses[(env,float(t))]
            if np.isclose(t,0.15):
                status='OUTPUT_FORMAT_ROUNDING' if np.isclose(r.printed_threshold,0.2) else 'UNEXPECTED'
            else:
                status='MATCH' if np.isclose(r.printed_threshold,t,rtol=0,atol=0.051) else 'MISMATCH'
            rounding.append({'environment':env,'PI_declared_L0':float(t),'COSRAD_printed_L0':float(r.printed_threshold),'status':status})
    if any(x['status'] in ('UNEXPECTED','MISMATCH') for x in rounding): raise ValueError('unit threshold header contradiction')
    return {
        'filename':pkg.path.name,'SHA-256':pkg.sha256,'date_received':'2026-09-04','member_count':len(pkg.members),'member_set_status':'PASS',
        'scenario':{'apogee_km':36000,'perigee_km':36000,'inclination_deg':0.0,'argument_of_perigee_deg':0.0,'start_year_from_solar_cycle':1,'flight_time_years':10,'solar_cycle':'mean','GCR_solar_cycle_number':'even','SEP_probability':0.100,'SEE_sensitive_volume':'Thin','Bit':1.0,'sigma_m_cm2':1.0},
        'shielding_grid_g_cm2':[float(x) for x in SHIELDS],
        'unit_response_thresholds_MeV_cm2_mg':[float(x) for x in THRESHOLDS],
        'threshold_printing_audit':rounding,
        'provenance_status':'PASS'
    }
