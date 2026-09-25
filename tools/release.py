"""Offline, allowlisted, deterministic release builder. Performs NO remote writes."""
from __future__ import annotations
import argparse,hashlib,json,os,stat,zipfile
from pathlib import Path, PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
VERSION='0.1.0-research'
DIRS={'lab','tests','tools','schemas','evidence','docs','paper','LICENSES','.github'}
ROOT_FILES={'README.md','LICENSE','SECURITY.md','CHANGELOG.md','requirements.txt','run_all.py',
 'CITATION.cff','AUTHORSHIP.json','provenance.json','LICENSE-MAP.json','MANIFEST.sha256',
 'PUBLIC-FILES.json','.gitignore','DEPENDENCIES.json'}
PAPER_FILES={'main.tex','bibliography.tex','references.bib','metrics.tex','publication.tex','main.pdf'}
GENERATED={'MANIFEST.sha256','LICENSE-MAP.json','PUBLIC-FILES.json'}

def sha(b):return hashlib.sha256(b).hexdigest()
def paths():
    result=[]
    candidates=[ROOT/n for n in ROOT_FILES if (ROOT/n).exists()]
    for d in DIRS:
        candidates.extend((ROOT/d).rglob('*'))
    for p in sorted(candidates):
        rel=p.relative_to(ROOT)
        if p.is_symlink():raise RuntimeError('Symlink not admitted: '+str(rel))
        if not p.is_file() or '__pycache__' in rel.parts or p.suffix=='.pyc':continue
        if len(rel.parts)==1:
            if rel.name not in ROOT_FILES:continue
        elif rel.parts[0] not in DIRS:continue
        if rel.parts[0]=='paper' and (len(rel.parts)!=2 or rel.name not in PAPER_FILES):continue
        result.append(p)
    return result

def license_of(name):
    if name.startswith('LICENSES/'):return 'Third-party licence text (unmodified)'
    if name.startswith('paper/') or (name.startswith('docs/') and not name.endswith('.json')):return 'CC-BY-4.0'
    return 'Apache-2.0'

def prepare():
    files=set(p.relative_to(ROOT).as_posix() for p in paths())|GENERATED
    mapping={n:license_of(n) for n in sorted(files)}
    (ROOT/'LICENSE-MAP.json').write_text(json.dumps(mapping,indent=2)+'\n')
    (ROOT/'PUBLIC-FILES.json').write_text(json.dumps(sorted(files),indent=2)+'\n')
    data={p.relative_to(ROOT).as_posix():p.read_bytes() for p in paths() if p.name!='MANIFEST.sha256'}
    (ROOT/'MANIFEST.sha256').write_text(''.join(f'{sha(b)}  {n}\n' for n,b in sorted(data.items())))
    return verify()

def verify():
    listed={}
    for line in (ROOT/'MANIFEST.sha256').read_text().splitlines():
        h,n=line.split('  ',1)
        key=PurePosixPath(n)
        if key.is_absolute() or '..' in key.parts or '\\' in n or ':' in n:
            raise RuntimeError('Unsafe manifest path '+n)
        p=ROOT/n
        if not p.resolve().is_relative_to(ROOT) or not p.is_file():raise RuntimeError('Missing/unsafe '+n)
        if sha(p.read_bytes())!=h:raise RuntimeError('Hash mismatch '+n)
        if n in listed:raise RuntimeError('Duplicate manifest '+n)
        listed[n]=h
    actual={p.relative_to(ROOT).as_posix() for p in paths()}-{'MANIFEST.sha256'}
    if actual!=set(listed):raise RuntimeError('Unexpected or omitted allowlisted file')
    if set(json.loads((ROOT/'PUBLIC-FILES.json').read_text()))!=actual|{'MANIFEST.sha256'}:
        raise RuntimeError('Public file list mismatch')
    expected_map={n:license_of(n) for n in actual|{'MANIFEST.sha256'}}
    if json.loads((ROOT/'LICENSE-MAP.json').read_text())!=expected_map:
        raise RuntimeError('Licence map coverage or assignment mismatch')
    return {'verified_files':len(listed),'scope':'exact allowlisted files; not independent provenance'}

def write_zip(target,data):
    with zipfile.ZipFile(target,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for name,b in sorted(data.items()):
            info=zipfile.ZipInfo(name,(1980,1,1,0,0,0));info.create_system=3
            info.external_attr=(stat.S_IFREG|0o644)<<16;info.compress_type=zipfile.ZIP_DEFLATED
            z.writestr(info,b,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)

def partition_manifest(data):
    data=dict(data)
    data['MANIFEST.sha256']=''.join(f'{sha(b)}  {n}\n' for n,b in sorted(data.items())).encode()
    return data

def build(out):
    verify();out.mkdir(parents=True,exist_ok=True)
    data={p.relative_to(ROOT).as_posix():p.read_bytes() for p in paths()}
    full=out/f'mission-authority-conservation-{VERSION}-full.zip'
    write_zip(full,{f'mission-authority-conservation-{VERSION}/{k}':v for k,v in data.items()})
    # Separate licence domains for two Zenodo records.
    software={k:v for k,v in data.items() if license_of(k)=='Apache-2.0' and k not in GENERATED}
    software['LICENSE']=data['LICENSES/Apache-2.0.txt']
    software['README.md']=(b'# Software-only archive\n\nThis partition contains the executable material. Paper and narrative specification\n'
        b'are in the companion report archive and the full repository; their paths below\n'
        b'describe that full repository. run_all.py is self-contained in this partition.\n\n'+software['README.md'])
    software['LICENSES/Apache-2.0.txt']=data['LICENSES/Apache-2.0.txt']
    software_names=set(software)|{'LICENSE-MAP.json','MANIFEST.sha256'}
    software['LICENSE-MAP.json']=json.dumps({k:license_of(k) for k in sorted(software_names)},indent=2).encode()
    sw=out/f'mission-authority-conservation-{VERSION}-software.zip'
    write_zip(sw,partition_manifest(software))
    paper={k:v for k,v in data.items() if license_of(k)=='CC-BY-4.0' and not k.endswith('.pdf')}
    paper['LICENSE']=data['LICENSES/CC-BY-4.0.txt']
    paper['README.txt']=(b'Paper and narrative specification, CC BY 4.0. Build: cd paper; latexmk -pdf main.tex.\n'
        b'IEEEtran, Latin Modern and standard LaTeX packages are system dependencies, not bundled.\n'
        b'Experiment-derived metrics.tex is included. Software and raw evidence are in the companion software archive.\n')
    src=out/f'mission-authority-conservation-{VERSION}-paper-source.zip'
    write_zip(src,partition_manifest(paper))
    pdf=out/f'Mission_Authority_Conservation_{VERSION}.pdf';pdf.write_bytes(data['paper/main.pdf'])
    assets=[full,sw,src,pdf]
    manifest={p.name:{'bytes':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in assets}
    (out/'ASSETS.json').write_text(json.dumps({'version':VERSION,'files':manifest,
        'zip_metadata_note':'ZIP entry dates are normalized to 1980 for determinism, not claimed publication times.'},indent=2)+'\n')
    (out/'SHA256SUMS.txt').write_text(''.join(f"{v['sha256']}  {n}\n" for n,v in manifest.items()))
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('command',choices=['prepare','verify','build']);p.add_argument('--out',default='../release_assets');a=p.parse_args()
    print(json.dumps(prepare() if a.command=='prepare' else verify() if a.command=='verify' else build(Path(a.out).resolve()),indent=2))
