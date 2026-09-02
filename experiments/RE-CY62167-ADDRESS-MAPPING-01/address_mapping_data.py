from __future__ import annotations
import hashlib, zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence

TASK_ID='RE-CY62167-ADDRESS-MAPPING-01'
STARTING_SHA='9fb2aca74b22c7fa533fc9f72715eae81d3e1596'
WORKING_BRANCH='research/cy62167-address-mapping-01'
ZENODO_DOI='10.5281/zenodo.8314389'
TRAINING_SOURCE='clust_C720MeV.txt'
ADDRESS_BITS=21; COORD_BITS=12; FEATURE_COUNT=25
MAX_EXTERNAL_ADDRESS=(1<<ADDRESS_BITS)-1; MAX_COORDINATE=(1<<COORD_BITS)-1
ZENODO_MD5={
'clust_Ar1050MeV.txt':'b15aa953e4a10656a674e6bd33a0ca98','clust_Ar548MeV.txt':'1359b0dee20a4fa1ced21bf6e3a7b700',
'clust_C1080MeV.txt':'299ad56c80bee8cd786bd7aaca850f5a','clust_C360MeV.txt':'9bfb8270cc37323299e16862d3c19e30',
'clust_C720MeV.txt':'b390b69b8b4ddbf9a4cd84cea219df71','clust_U142.8GeV.txt':'e5d15c02b35929ea637a8d46ed183c32',
'clust_U190.4GeV.txt':'8b58a54da164390ef3b863173a75803f','clust_U35.7GeV.txt':'cdc56859f2cde4208507902e3e1b8587',
'clust_U45.2GeV.txt':'b608b4e04f597a080c5f1a38ba06fd4c','clust_U78.5GeV.txt':'7c883708f041e6dbc41bbe81cbbe560c',
'clust_Xe2700MeV.txt':'6e48b3ff61ce611d56e12feb692340ff','clust_XeLET27.txt':'5c77e44c49c11780a4f3e4fa7ac1b17e',
'clust_XeLET42.txt':'0b880fec1ed829e5b5a57d7099f4ca93','clust_XeLET57.txt':'18539e6c23fc206ff71fba2ebca2ea3a',
'clust_p0.9MeV.txt':'10ab9973e182b8aa2d6647d3fb2d451a','clust_p1.1MeV.txt':'68b78596d0903c014747c62c606eb851',
'clust_p1.5MeV.txt':'fa049e8ef13a9c5e1e5d2c41353a6e4f','clust_p124MeV.txt':'dbf5911333c50a5b6eb366c026208e7c',
'clust_p164MeV.txt':'ec1a27f27a6b904557125d3219116a13','clust_p186MeV.txt':'28614930fc22db2365e07b6a55850a17',
'clust_p1MeV.txt':'a0dfb8e032b4102bd00815d800b9a770','clust_p2.5MeV.txt':'7cee7f8bc1497e3c79d11b2f304d2540',
'clust_p29MeV.txt':'be0a36e3ef587b3fa9fdcf0663aa404e','clust_p3MeV.txt':'88f4ce176d5a6826f71f37ff32641c0e',
'clust_p40MeV.txt':'ff7fe1c5365f6ade8c81680423d68aa3','clust_p4MeV.txt':'713f0f33a961e143598021c88c5f2de0',
'clust_p5MeV.txt':'2bcef85b1a963b2c4da61bf5c5544cce','clust_p80MeV.txt':'0ce14a24799e0523b8242d0d66d04c96'}

@dataclass(frozen=True)
class CellRecord:
    source_file:str; segment_id:int; cluster_id:int; line_start:int; cell_index:int
    timestamp_raw:Optional[str]; xmin:int; xmax:int; ymin:int; ymax:int; xadd:int; yadd:int
    number_of_events_declared:int; field_arity:int; field0_raw:Optional[int]; x:int; y:int
    raw_fields:tuple[int,...]; classification:str; classification_reason:str
    @property
    def event_key(self): return (self.source_file,self.segment_id,self.cluster_id)
    @property
    def dedup_key(self): return (*self.event_key,self.x,self.y)
    @property
    def triple(self): return None if self.field0_raw is None else (self.field0_raw,self.x,self.y)

@dataclass(frozen=True)
class ParseStats:
    source_file:str; cluster_count:int; cell_record_count:int; two_field_count:int; three_field_count:int
    strict_service_count:int; ambiguous_count:int; physical_eligible_count:int; physical_no_address_count:int
    bounds_mismatch_count:int; coordinate_out_of_range_count:int

def sha256_path(path:Path)->str:
    h=hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def inspect_archive_before_member_read(path:Path):
    with zipfile.ZipFile(path) as z: infos=[i for i in z.infolist() if not i.is_dir()]
    stub={'provided_archive_name':path.name,'archive_size_bytes':path.stat().st_size,'archive_sha256':sha256_path(path),
          'member_count':len(infos),'uncompressed_total_bytes':sum(i.file_size for i in infos),
          'archive_inspection_performed_before_member_payload_read':True,
          'member_listing':[{'archive_path':i.filename,'source_file':Path(i.filename).name,'size':i.file_size} for i in infos]}
    return stub,infos

def read_archive_members_and_hash(path:Path,infos:Sequence[zipfile.ZipInfo]):
    texts={}; members=[]; seen=set()
    with zipfile.ZipFile(path) as z:
        for i in infos:
            name=Path(i.filename).name
            if name in seen: raise ValueError('duplicate archive basename: '+name)
            seen.add(name); raw=z.read(i.filename); md5=hashlib.md5(raw).hexdigest(); sha=hashlib.sha256(raw).hexdigest(); exp=ZENODO_MD5.get(name)
            members.append({'archive_path':i.filename,'source_file':name,'size':len(raw),'md5':md5,'sha256':sha,
                            'zenodo_md5_expected':exp,'zenodo_md5_match':(md5==exp) if exp else None})
            texts[name]=raw.decode('utf-8','strict')
    return texts,members
