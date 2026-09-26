"""Publish the reviewed AIGP snapshot; no tokens or private inputs are exported."""
import base64, datetime, hashlib, json, lzma, os, pathlib, re, shutil, subprocess, sys, zipfile
ROOT = pathlib.Path.cwd()
STAGE = ROOT / '.aigp-publication'
TARGET = ROOT / 'aigp'
REPO = 'mohammedmessaoudene-cmd/mission-authority-conservation'
BRANCH = 'aigp-publication-v0.2.0'
TAG = 'aigp-v0.2.0-research'
VERSION = '0.2.0-research'
def require(condition, message):
    if not condition: raise RuntimeError(message)
def run(args, **kwargs):
    return subprocess.run(args, check=True, text=True, capture_output=True, **kwargs).stdout.strip()
def h(data): return hashlib.sha256(data).hexdigest()
def safe_name(name):
    p = pathlib.PurePosixPath(name)
    require(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe path')
    require(p.parts and not any(x in {'.git','private_handoff','incoming_reports'} for x in p.parts), 'private path')
    require(p.suffix.lower() not in {'.pem','.key','.ttf','.otf','.woff','.woff2','.db','.sqlite'}, 'excluded file')
    return p

def unpack():
    require(not TARGET.exists(), 'target exists; never overwrite a publication')
    cfg = json.loads((STAGE/'READY.json').read_text())
    require(cfg['repository']==REPO and cfg['version']==VERSION, 'wrong target')
    parts=[]
    for item in cfg['parts']:
        require(re.fullmatch(r'part-[0-9]{2}\.b64',item['file']) is not None,'invalid part')
        raw=(STAGE/item['file']).read_bytes()
        require(h(raw)==item['sha256'],'part checksum: '+item['file'])
        parts.append(raw)
    packed=base64.b64decode(b''.join(parts),validate=True)
    require(h(packed)==cfg['payload_sha256'],'payload checksum')
    decoder=lzma.LZMADecompressor(memlimit=128*1024*1024)
    raw=decoder.decompress(packed,max_length=2*1024*1024)
    require(decoder.eof and not decoder.unused_data,'oversized/trailing payload')
    files=json.loads(raw)
    require(isinstance(files,dict) and len(files)==cfg['source_files'],'inventory')
    for name,text in files.items():
        safe_name(name); require(isinstance(text,str),'not text')
        require('-----BEGIN PRIVATE KEY-----' not in text and '-----BEGIN RSA PRIVATE KEY-----' not in text,'private key')
    for name,text in files.items():
        out=TARGET/safe_name(name); out.parent.mkdir(parents=True,exist_ok=True)
        out.write_bytes(text.encode('utf-8'))
    expected={}
    for line in (TARGET/'MANIFEST.sha256').read_text().splitlines():
        digest,name=line.split('  ',1)
        require(name not in expected,'duplicate manifest entry'); expected[name]=digest
    require(set(files)==(set(expected)-{'paper/main.pdf'})|{'MANIFEST.sha256'},'manifest inventory')
    for name,digest in expected.items():
        if name!='paper/main.pdf': require(h((TARGET/name).read_bytes())==digest,'source checksum: '+name)
    print(json.dumps({'unpacked_public_text_files':len(files),'original_non_pdf_manifest_verified':True}))

def publish():
    require(os.environ.get('GITHUB_REPOSITORY')==REPO,'wrong repository')
    require(os.environ.get('GITHUB_REF_NAME')==BRANCH,'wrong branch')
    require(bool(os.environ.get('GH_TOKEN')),'Actions token absent')
    old=subprocess.run(['gh','release','view',TAG,'--repo',REPO],text=True,capture_output=True)
    require(old.returncode!=0,'release exists; do not overwrite')
    summary=json.loads((TARGET/'local-results/summary.json').read_text())
    require(summary['research_checks_passed'] is True,'research checks failed')
    require({x['name'] for x in summary['steps']}=={'tests','compositions','mutations','experiments','node-verifier'},'missing check')
    require(all(x.get('passed') is True and x.get('returncode')==0 for x in summary['steps']),'failed step')
    log=(TARGET/'local-results/tests.log').read_text()
    require(re.search(r'Ran 105 tests in ',log) is not None and re.search(r'\nOK\s*$',log),'test count/result')
    require(not any(s in log for s in ('skipped=','expected failures=','unexpected successes=')),'skips/expected failures')
    pdf=TARGET/'paper/main.pdf'; require(pdf.read_bytes().startswith(b'%PDF-'),'missing paper')
    texlog=(TARGET/'paper/main.log').read_text()
    require('Overfull' not in texlog and 'undefined' not in texlog,'paper warnings')
    original=(TARGET/'MANIFEST.sha256').read_text()
    original_pdf=next(x.split('  ',1)[0] for x in original.splitlines() if x.endswith('  paper/main.pdf'))
    (TARGET/'evidence/original_input_manifest.sha256').write_text(original)
    shutil.copytree(TARGET/'local-results',TARGET/'evidence/github')
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    record={'version':VERSION,'checked_at_utc':now,'ordinary_tests':105,
        'source_workflow_commit':os.environ['GITHUB_SHA'],
        'workflow_run':'https://github.com/'+REPO+'/actions/runs/'+os.environ['GITHUB_RUN_ID'],
        'research_checks_passed':True,'production_ready':False,
        'pdf_sha256':h(pdf.read_bytes()),'original_pdf_sha256':original_pdf,
        'pdf_matches_original':h(pdf.read_bytes())==original_pdf,
        'python':sys.version,'node':run(['node','--version']),
        'tex':run(['pdflatex','--version']).splitlines()[0],
        'native_biscuit_cedar_tested':False,'real_hardware_attestation_tested':False,
        'qualified_identity_or_insurance_tested':False,'independent_human_review':False,
        'scope':'Complete research architecture; software-test composition and explicit external integration gates.'}
    (TARGET/'docs/PUBLICATION_CHECK.json').write_text(json.dumps(record,indent=2)+'\n')
    (TARGET/'docs/AVAILABILITY.md').write_text('# Public availability\n\nAIGP '+VERSION+' is a separate research supplement under `aigp/` in\n`'+REPO+'`. The original Mission Authority Conservation release is not\nreplaced, and its Zenodo DOIs do not identify this AIGP supplement.\n\nGitHub release: https://github.com/'+REPO+'/releases/tag/'+TAG+'\n\nThis release publishes the integrated software-test architecture, source, paper,\nhistorical and new execution evidence, limitations and native integration contracts.\nIt does not claim an operational worldwide trust infrastructure, a new Zenodo DOI,\npatent priority, hardware certification or legal compensation.\n\nThe author authorized public release. Private handoff instructions and original\nthird-party proposal texts are excluded. AI assistance is disclosed.\n')
    with (TARGET/'README.md').open('a') as f:
        f.write('\n## Published research supplement\n\nSource: https://github.com/'+REPO+'/tree/main/aigp\n\nRelease: https://github.com/'+REPO+'/releases/tag/'+TAG+'\n\nSee `docs/AVAILABILITY.md` and `docs/PUBLICATION_CHECK.json`.\n')
    cff=(TARGET/'CITATION.cff').read_text().replace('Please cite the research profile and the exact published version when available.','Please cite this research profile and its exact GitHub release.')
    cff=cff.replace('license: Apache-2.0','license:\n  - Apache-2.0\n  - CC-BY-4.0')
    cff+='url: "https://github.com/'+REPO+'/tree/main/aigp"\ndate-released: "'+now[:10]+'"\n'
    (TARGET/'CITATION.cff').write_text(cff)
    shutil.rmtree(TARGET/'local-results')
    for p in list(TARGET.rglob('__pycache__')): shutil.rmtree(p)
    for p in (TARGET/'paper').iterdir():
        if p.suffix in {'.aux','.log','.out','.toc'}: p.unlink()
    files=sorted(p for p in TARGET.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256')
    lm={}
    for p in files:
        rel=p.relative_to(TARGET).as_posix()
        lm[rel]=('Original license text; unmodified notice' if rel.startswith('licenses/') else 'CC-BY-4.0' if p.suffix in {'.md','.tex','.pdf'} else 'Apache-2.0')
    (TARGET/'LICENSE_MAP.json').write_text(json.dumps(lm,indent=2)+'\n')
    files=sorted(p for p in TARGET.rglob('*') if p.is_file() and p.name!='MANIFEST.sha256')
    (TARGET/'MANIFEST.sha256').write_text(''.join(h(p.read_bytes())+'  '+p.relative_to(TARGET).as_posix()+'\n' for p in files))
    run([sys.executable,str(TARGET/'tools/verify_manifest.py')])
    dist=ROOT/'.aigp-dist'; dist.mkdir(exist_ok=True)
    archive=dist/'AIGP_0.2.0-research.zip'
    def make_zip(path):
        with zipfile.ZipFile(path,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
            for p in sorted(TARGET.rglob('*')):
                if p.is_file():
                    info=zipfile.ZipInfo('aigp/'+p.relative_to(TARGET).as_posix(),date_time=(1980,1,1,0,0,0))
                    info.compress_type=zipfile.ZIP_DEFLATED; info.external_attr=0o100644<<16
                    z.writestr(info,p.read_bytes())
    make_zip(archive); second=dist/'second.zip'; make_zip(second)
    require(h(archive.read_bytes())==h(second.read_bytes()),'archive nondeterminism'); second.unlink()
    paper_copy=dist/'AIGP_Architecture_Federee_Rapport.pdf'; shutil.copy2(pdf,paper_copy)
    sums=dist/'SHA256SUMS.txt'; sums.write_text(''.join(h(p.read_bytes())+'  '+p.name+'\n' for p in (archive,paper_copy)))
    readme=ROOT/'README.md'; text=readme.read_text(); marker='## AIGP research supplement'
    require(marker not in text,'supplement already linked')
    readme.write_text(text+'\n'+marker+'\n\n[AIGP: Federated Acceptance and Evidence-Bound Enforcement](aigp/)\nis published as a separate full-scope software-test research profile.\nIts identity, appraisal, revocation and guarantee composition extends\nthe research scope; it does not replace the MAC 0.1.0 release or reuse\nits Zenodo DOI. See the [AIGP release](https://github.com/'+REPO+'/releases/tag/'+TAG+').\n')
    run(['git','config','user.name','github-actions[bot]'])
    run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'])
    run(['git','add','aigp','README.md'])
    run(['git','commit','-m','Publish AIGP 0.2.0-research: integrated profile, paper and reproduced evidence'])
    commit=run(['git','rev-parse','HEAD']); run(['git','push','origin','HEAD:refs/heads/'+BRANCH])
    notes=dist/'release-notes.md'
    notes.write_text('# AIGP 0.2.0-research\n\nFederated acceptance and evidence-bound enforcement for AI agents.\nResearch software, not an accepted standard or production trust service.\n\nSource: https://github.com/'+REPO+'/tree/'+commit+'/aigp\n\nIncludes the complete research architecture, Python implementation, limited\nMCP/A2A harnesses, real local TLS 1.3 binding, paper PDF and LaTeX source,\n105 passing ordinary tests, 256 fixture combinations, four source mutations,\n17-object JavaScript verification and crash/concurrency experiments.\n\nIdentity, hardware appraisal and guarantee providers are software fixtures.\nNative Biscuit/Cedar, live TEE, qualified identity, insurance, AP2 and\nofficial protocol conformance are not demonstrated. Privileged cloning\nstill produces 200 units from an original allocation of 100.\n\nCode/executable material: Apache-2.0. Paper/narrative: CC BY 4.0.\nMohammed Messaoudene: project initiative and direction. AI assistance disclosed.\nNo new Zenodo DOI, patent-priority claim or institutional endorsement.\n\nCommit: `'+commit+'`\n\nSHA-256 checksums are in the attached SHA256SUMS.txt.\n')
    print(run(['gh','release','create',TAG,str(archive),str(paper_copy),str(sums),'--repo',REPO,'--target',commit,'--title','AIGP 0.2.0-research - federated acceptance and enforcement','--prerelease','--notes-file',str(notes)]))
    print(json.dumps({'published_github_commit':commit,'release_tag':TAG,'archive_sha256':h(archive.read_bytes())}))
if __name__=='__main__':
    require(len(sys.argv)==2 and sys.argv[1] in {'unpack','publish'},'usage: publish.py unpack|publish')
    globals()[sys.argv[1]]()
