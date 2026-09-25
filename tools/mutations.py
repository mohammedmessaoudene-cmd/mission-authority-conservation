"""Four selected source mutations, in disposable copies; not mutation coverage."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import difflib,hashlib,json,shutil,subprocess,sys,tempfile

CASES=[
 ('M1','test_34_no_budget_overrun',
  '            require(all(cost[i] <= cap[f"f{i}"] for i in range(3)), "BUDGET")',
  '            pass  # MUTANT: omit admission budget guard'),
 ('M2','test_56_unknown_holds_budget',
  '            require(r is not None and r["state"] == "RESERVED", "UNSAFE_REFUND")',
  '            require(r is not None and r["state"] in ("RESERVED", "DISPATCHED", "UNKNOWN"), "UNSAFE_REFUND")'),
 ('M3','test_80_approval_expiry_limits_inflight_permit',
  '                effective_expiry = min(effective_expiry, ap["expires"])',
  '                pass  # MUTANT: omit approval expiry bound'),
 ('M4','test_78_policy_change_before_dispatch',
  '            require(r["policy"] == self.policy, "POLICY_VERSION")',
  '            pass  # MUTANT: omit dispatch policy revalidation')]

def sha(b):return hashlib.sha256(b).hexdigest()

def run(out:Path)->dict:
    root=Path(__file__).resolve().parents[1];out.mkdir(parents=True,exist_ok=True)
    original=(root/'lab/core.py').read_bytes()
    def case(config):
        id,test,before,after=config
        text=original.decode()
        if text.count(before)!=1:raise RuntimeError(f'{id}: target is not unique')
        line=text[:text.index(before)].count('\n')+1
        with tempfile.TemporaryDirectory(prefix='authority-mutation-') as tmp:
            d=Path(tmp)
            for part in ('lab','tests','tools'):
                shutil.copytree(root/part,d/part,ignore=shutil.ignore_patterns('__pycache__'))
            def probe():
                p=subprocess.run([sys.executable,'-B',*(['-O'] if sys.flags.optimize else []),'-m','tools.mutation_probe',id,test,str(line)],
                    cwd=d,text=True,capture_output=True,timeout=30)
                if p.returncode:raise RuntimeError(id+': '+p.stderr)
                return json.loads(p.stdout)
            baseline=probe()
            mutated=text.replace(before,after)
            (d/'lab/core.py').write_bytes(mutated.encode('utf-8'))
            mutant=probe()
            (d/'lab/core.py').write_bytes(original)
            restored=probe()
        passed=(baseline['core_sha256']==sha(original) and restored['core_sha256']==sha(original)
          and mutant['core_sha256']==sha(mutated.encode('utf-8')) and baseline['successful'] and restored['successful'] and not mutant['successful']
          and mutant['failures']==1 and mutant['errors']==0
          and not baseline['direct']['unsafe'] and not restored['direct']['unsafe']
          and mutant['direct']['unsafe'] and mutant['target_line_executed'])
        result={'id':id,'test':test,'target_line':line,'original_sha256':sha(original),
            'mutant_sha256':sha(mutated.encode()),'single_line_replacement':True,
            'baseline':baseline,'mutant':mutant,'restored':restored,'passed':passed}
        (out/f'{id}.json').write_text(json.dumps(result,indent=2)+'\n')
        diff=''.join(difflib.unified_diff(text.splitlines(True),mutated.splitlines(True),
            fromfile='baseline/lab/core.py',tofile=f'{id}/lab/core.py'))
        (out/f'{id}.patch').write_text(diff)
        return result
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(case,CASES))
    unchanged=(root/'lab/core.py').read_bytes()==original
    summary={'controls':len(results),'passed':sum(x['passed'] for x in results),
       'original_unchanged':unchanged,'execution':'four concurrent experiment workers; not LLM agents or independent reviewers',
       'scope':'four selected single-line source mutations, focused test and direct unsafe observation; not exhaustive mutation coverage'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    if not unchanged or not all(x['passed'] for x in results):raise RuntimeError('Mutation gate failed')
    return summary
if __name__=='__main__': print(json.dumps(run(Path(sys.argv[1])),indent=2))
