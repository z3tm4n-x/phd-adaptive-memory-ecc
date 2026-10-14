"""Optional unprivileged Ubuntu tool extraction; no system package changes.

APT supplies authenticated repository indexes. Exact package filenames/hashes
are recorded; extracted third-party tools stay ignored and outside the commit.
"""
import hashlib, json, os, re, subprocess
from pathlib import Path
from urllib.parse import unquote

HERE=Path(__file__).resolve().parent
PACKAGES=['gcc-arm-none-eabi=15:14.2.rel1-1',
          'qemu-system-arm=1:10.2.1+ds-1ubuntu3',
          'qemu-system-common=1:10.2.1+ds-1ubuntu3',
          'qemu-system-data=1:10.2.1+ds-1ubuntu3']

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
    manifest_path=HERE/'outputs/tools.json'
    if manifest_path.exists():
        # Reproduction uses the published package bytes, not whatever a later
        # dependency resolver selects. A vanished version is a named input
        # failure; do not replace it or overwrite the accepted tool manifest.
        expected=json.loads(manifest_path.read_text())
        for item in expected['packages']:
            path=debs/item['name']
            if not path.exists():
                name,version,arch=unquote(item['name']).rsplit('_',2)
                subprocess.run(['apt-get','download',name+'='+version],cwd=debs,check=True)
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=item['sha256']:
                raise RuntimeError('Published tool package missing or hash mismatch: '+item['name'])
        for item in expected['packages']:
            subprocess.run(['dpkg-deb','-x',str(debs/item['name']),str(dest/'root')],check=True)
        for tool,version in expected['versions'].items():
            if run([tool,'--version'],env=environment()).splitlines()[0]!=version:
                raise RuntimeError('Published tool version mismatch: '+tool)
        print('Published tool packages and versions verified; manifest unchanged.')
        return
    plan=run(['apt-get','-s','--no-install-recommends','install',*PACKAGES])
    packages=[]
    for name,version in re.findall(r'^Inst (\S+)(?: \[[^]]+\])? \((\S+)',plan,re.M):
        # These policy/integration packages are not runtime dependencies of
        # the standalone emulator. No package scripts run during extraction.
        if name not in ('ubuntu-helper-virt-hwe','ubuntu-virt'):
            packages.append(name+'='+version)
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
