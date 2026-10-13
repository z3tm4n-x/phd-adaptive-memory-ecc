"""Bounded proof and packet evidence; raw vendor traces/DCP remain local."""
import hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    files=[]
    for folder in ('interval-proof','arm-join','compact-proof'):
        files += [(folder+'/'+p.name,p) for p in (HERE/'.build'/folder).iterdir()
                  if p.suffix in ('.log','.sv','.json')]
    for label in ('valid','bad-crc','replay-sequence','wrong-generation'):
        files += [('mailbox/'+label+'/'+name,HERE/'.build/mailbox'/label/name)
                  for name in ('raw.txt','trace.txt','run.log')]
    for label in ('reference-0-none','optimized-0-none','optimized-7-none','optimized-0-bad-crc','optimized-0-bad-sequence'):
        files += [('isa/'+label+'/'+name,HERE/'.build/isa'/label/name)
                  for name in ('raw.txt','packets.txt','cuts.txt','mmio.json','bridge.log')]
    # Compact sufficient service ledger; original pin logs remain hashed.
    previous={}
    if (HERE/'outputs/check-evidence.zip').exists():
        with zipfile.ZipFile(HERE/'outputs/check-evidence.zip') as z:
            previous={n:z.read(n) for n in z.namelist() if n.startswith('price/')}
    for n in ('stress-3.txt','stress-4.txt'):
        p=HERE/'.build/price'/n
        if p.exists():files.append(('price/'+n,p))
        elif 'price/'+n not in previous:raise RuntimeError('run price cases first')
    hashes={}
    with zipfile.ZipFile(HERE/'outputs/check-evidence.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in sorted(files):
            data=path.read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
            entry=zipfile.ZipInfo(name,(2026,10,13,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,data)
        for name,data in sorted(previous.items()):
            if name not in hashes:
                hashes[name]=hashlib.sha256(data).hexdigest()
                entry=zipfile.ZipInfo(name,(2026,10,13,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
                z.writestr(entry,data)
    (HERE/'outputs/check-evidence.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print('Bounded checker evidence:',len(files),'files')
if __name__=='__main__':main()
