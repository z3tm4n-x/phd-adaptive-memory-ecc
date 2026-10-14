"""Attack actual published trace, including interfaces absent from unit tests."""
import gzip,json,tempfile
from pathlib import Path
from check import check
HERE=Path(__file__).resolve().parent

def main():
    c=json.loads((HERE/'config.json').read_text())
    original=gzip.open(HERE/'outputs/cold-adaptive.trace.gz','rt').read().splitlines(True)
    changes={}
    for name in ('drop_ERR','duplicate_reply','erase_post_start_error','corrupt_partial_write','premature_LOW'):
        lines=original.copy();changed=False
        for n,line in enumerate(lines):
            f=line.split()
            if name=='drop_ERR' and f[0]=='EVENT':del lines[n];changed=True;break
            if name=='duplicate_reply' and f[0]=='REPLY':lines.insert(n,line);changed=True;break
            if name=='erase_post_start_error' and f[0]=='WRITE' and int(f[-1],16):
                f[-1]='0';lines[n]=' '.join(f)+'\n';changed=True;break
            if name=='corrupt_partial_write' and f[0]=='WRITE' and int(f[5],16)!=3:
                f[6]=f'{int(f[6],16)^1:x}';lines[n]=' '.join(f)+'\n';changed=True;break
            if name=='premature_LOW' and f[0]=='FREEZE':
                f[3]='1';lines[n]=' '.join(f)+'\n';changed=True;break
        assert changed,('mutation not exercised',name)
        build=HERE/'.build';build.mkdir(exist_ok=True)
        with tempfile.NamedTemporaryFile(mode='w',suffix='.trace',dir=build,delete=False) as tmp:
            tmp.writelines(lines);path=Path(tmp.name)
        try:
            try:check(path,c,'adaptive')
            except AssertionError as e:
                message=str(e).replace(path.name,'mutant.trace')
                assert 't=' in message,'missing first-divergence locator'
                changes[name]={'rejected':True,'first_difference':message}
            else:raise AssertionError('sentinel survived: '+name)
        finally:path.unlink()
    (HERE/'outputs/mutations.json').write_text(json.dumps(changes,indent=2)+'\n')
    print(json.dumps(changes,indent=2))
if __name__=='__main__':main()
