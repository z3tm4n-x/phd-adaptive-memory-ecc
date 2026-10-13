"""Bounded proof and packet evidence; raw vendor traces/DCP remain local."""
import hashlib,json,zipfile
from pathlib import Path
HERE=Path(__file__).resolve().parent
def main():
    files=[]
    for folder in ('interval-proof','arm-join'):
        files += [(folder+'/'+p.name,p) for p in (HERE/'.build'/folder).iterdir()
                  if p.suffix in ('.log','.sv','.json')]
    for label in ('valid','bad-crc','replay-sequence','wrong-generation'):
        files += [('mailbox/'+label+'/'+name,HERE/'.build/mailbox'/label/name)
                  for name in ('raw.txt','trace.txt','run.log')]
    hashes={}
    with zipfile.ZipFile(HERE/'outputs/check-evidence.zip','w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,path in sorted(files):
            data=path.read_bytes();hashes[name]=hashlib.sha256(data).hexdigest()
            entry=zipfile.ZipInfo(name,(2026,10,13,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(entry,data)
    (HERE/'outputs/check-evidence.json').write_text(json.dumps(hashes,indent=2)+'\n')
    print('Bounded checker evidence:',len(files),'files')
if __name__=='__main__':main()
