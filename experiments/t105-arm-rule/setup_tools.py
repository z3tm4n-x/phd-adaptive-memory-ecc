"""Optional unprivileged Ubuntu tool extraction; no system package changes.

APT supplies authenticated repository indexes. Exact package filenames/hashes
are recorded; extracted third-party tools stay ignored and outside the commit.
"""
import hashlib, json, os, re, subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent
PACKAGES=['gcc-arm-none-eabi','qemu-system-arm']

def run(args,**kw):
    return subprocess.check_output(args,text=True,**kw)

def environment():
    root=HERE/'.tools/root/usr'
    env=dict(os.environ)
    env['PATH']=str(root/'bin')+os.pathsep+env.get('PATH','')
    env['LD_LIBRARY_PATH']=str(root/'lib/x86_64-linux-gnu')
    return env

def main():
    dest=HERE/'.tools'; debs=dest/'debs';debs.mkdir(parents=True,exist_ok=True)
    plan=run(['apt-get','-s','--no-install-recommends','install',*PACKAGES])
    packages=[]
    for name in re.findall(r'^Inst (\S+)',plan,re.M):
        # These policy/integration packages are not runtime dependencies of
        # the standalone emulator. No package scripts run during extraction.
        if name not in ('ubuntu-helper-virt-hwe','ubuntu-virt'):
            packages.append(name)
    if not packages:
        print('Requested tools already installed; extraction not needed.');return
    subprocess.run(['apt-get','download',*packages],cwd=debs,check=True)
    manifest=[]
    for path in sorted(debs.glob('*.deb')):
        subprocess.run(['dpkg-deb','-x',str(path),str(dest/'root')],check=True)
        manifest.append({'name':path.name,'bytes':path.stat().st_size,
                         'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    versions={}
    for tool in ('arm-none-eabi-gcc','arm-none-eabi-objdump','qemu-system-arm'):
        versions[tool]=run([tool,'--version'],env=environment()).splitlines()[0]
    out=HERE/'outputs';out.mkdir(exist_ok=True)
    (out/'tools.json').write_text(json.dumps({'status':'user-local extraction',
        'packages':manifest,'versions':versions,'system_modified':False},indent=2)+'\n')
    print(json.dumps(versions))

if __name__=='__main__':main()
