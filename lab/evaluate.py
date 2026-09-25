"""Reproducible software experiments. No network, real models, banks or TEEs."""
from __future__ import annotations
import copy,json,random,sqlite3,time,statistics,tempfile
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from .core import Denied,Key,Gate,digest,verify
from .scenario import Scenario
from .modelcheck import run as run_model
from .checks import checked, CheckFailed

SEED=20260925

def generated(n: int=10000) -> dict:
    rng=random.Random(SEED);s=Scenario();counts=Counter();unexpected=[];cases=[]
    started=time.perf_counter()
    try:
        for i in range(n):
            case=i%10;amount=rng.randint(1,49)
            p=s.make(iid=f'fuzz-{i}',amount=amount)
            pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p);ap=None
            expected=case in (0,9)
            if case==1:
                p['target']='evil.example';pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
            elif case==2:
                sig['payload']['params']['amount_minor']=amount+1
            elif case==3:
                p['params']['amount_minor']=amount+1;sig=s.agents[0].sign('INVOKE',p)
            elif case==4:
                p['mission']='another-root';pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
            elif case==5:
                p=s.make(iid=f'fuzz-{i}',amount=50);pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
            elif case==6:
                pr=s.agents[1].sign('PREPARED',pr['payload'])
            elif case==7:
                p['policy']='old-policy';pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
            elif case==8:
                p=s.make(iid=f'fuzz-{i}',amount=50);pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
                ap=s.approval(p,pr,s.agents[1])
            elif case==9:
                p=s.make(iid=f'fuzz-{i}',amount=50);pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
                ap=s.approval(p,pr)
            denial=None
            try:
                s.gate.reserve(sig,pr,ap)
            except Denied as exc:
                actual=False;denial=exc.code;counts[f'deny_{exc.code}']+=1
            else:
                actual=True;counts[f'case_{case}_accepted']+=1
            if actual!=expected:unexpected.append({'i':i,'case':case,'expected_allow':expected,'actual_allow':actual})
            cases.append({'i':i,'case':case,'amount_minor':p['params']['amount_minor'],
                          'expected_allow':expected,'actual_allow':actual,'denial':denial})
            if actual:
                try:
                    s.gate.cancel(p['iid'])
                except Denied as exc:
                    # Cleanup failure is not an authorization refusal and must not erase the decision.
                    raise CheckFailed('generated case cancellation failed',{
                        'seed':SEED,'requests':n,'processed':i+1,'complete':False,
                        'unexpected':unexpected,'counts':dict(counts),'cases':cases,
                        'cancellation_error':exc.code}) from exc
            if i%500==0:s.gate.audit()
        audit=s.gate.audit()
        result={'seed':SEED,'requests':n,'expected_accepted':sum(i%10 in (0,9) for i in range(n)),'unexpected':unexpected,
            'counts':dict(counts),'cases':cases,'final_free':s.gate.balance()['free'],'audit':audit,
            'elapsed_seconds':round(time.perf_counter()-started,3),
            'limitation':'10 authored scenario families with random amounts, not an independent attack corpus or uniform fuzzing'}
        return checked(not unexpected, 'generated case mismatch', result)
    finally:s.close()

def percentile(values: list[float],p: float) -> float:
    a=sorted(values);return a[min(len(a)-1,int((len(a)-1)*p))]

def benchmarks(n:int=300) -> dict:
    s=Scenario(budget=[10000,10000,10000]);reserve=[];endtoend=[];verifyonly=[]
    try:
        for i in range(n+20):
            p=s.make(iid=f'bench-{i}',amount=1);pr=s.resource.prepare(p);sig=s.agents[0].sign('INVOKE',p)
            t=time.perf_counter_ns();verify(sig,'INVOKE',s.agents[0]);tv=(time.perf_counter_ns()-t)/1e6
            t=time.perf_counter_ns();s.gate.reserve(sig,pr);tr=(time.perf_counter_ns()-t)/1e6
            permit=s.gate.begin(p['iid']);rec=s.resource.apply(p,pr,permit);s.gate.settle(rec)
            tt=(time.perf_counter_ns()-t)/1e6
            if i>=20:verifyonly.append(tv);reserve.append(tr);endtoend.append(tt)
        def summary(a):return {'median_ms':round(statistics.median(a),4),'p95_ms':round(percentile(a,.95),4),
             'p99_ms':round(percentile(a,.99),4),'max_ms':round(max(a),4)}
        return {'samples':n,'warmup':20,'single_thread':True,'signature_verification':summary(verifyonly),
             'reserve_including_checks_and_sqlite':summary(reserve),'reserve_dispatch_effect_settle_toy':summary(endtoend),
             'scope':'one local host, software keys, local SQLite; preparation excluded; no network or durability power-loss validation'}
    finally:s.close()

def existing_transaction_baseline() -> dict:
    # Strong non-agent-specific baseline: ordinary SQL transaction plus uniqueness.
    with tempfile.TemporaryDirectory() as d:
        path=str(Path(d)/'baseline.db');c=sqlite3.connect(path)
        c.executescript('CREATE TABLE budget(n INTEGER);INSERT INTO budget VALUES(100);CREATE TABLE effects(iid INTEGER PRIMARY KEY);')
        c.commit();c.close()
        def attempt(i):
            c=sqlite3.connect(path,timeout=30)
            try:
                c.execute('BEGIN IMMEDIATE')
                if c.execute('SELECT 1 FROM effects WHERE iid=?',(i,)).fetchone():c.commit();return 'replayed'
                if c.execute('SELECT n FROM budget').fetchone()[0]<1:c.rollback();return 'denied'
                c.execute('UPDATE budget SET n=n-1');c.execute('INSERT INTO effects VALUES(?)',(i,));c.commit();return 'applied'
            finally:c.close()
        with ThreadPoolExecutor(max_workers=16) as pool:counts=Counter(pool.map(attempt,list(range(200))*2))
        c=sqlite3.connect(path);effects=c.execute('SELECT count(*) FROM effects').fetchone()[0];free=c.execute('SELECT n FROM budget').fetchone()[0];c.close()
        result = {'attempts':400,'unique_ids':200,'workers':16,'budget':100,'effects':effects,'free':free,'outcomes':dict(counts),
            'conclusion':'An ordinary correctly engineered transactional resource can provide aggregate budget and durable deduplication too. No uniqueness of the proposed branding is demonstrated.'}
        return checked(effects==100 and free==0, 'conventional baseline mismatch', result)

def clone_limitation() -> dict:
    # Actual database backup, then two independent authorities with the same budget.
    s=Scenario(budget=[100,0,100]);path=s.base/'cloned-gate.db'
    try:
        src=sqlite3.connect(s.gate.path);dst=sqlite3.connect(path);src.backup(dst);dst.close();src.close()
        g2=Gate(path,s.clock,s.gkey,s.principal,s.human,s.rkey,s.actors)
        for g,identifier in ((s.gate,'copy-a'),(g2,'copy-b')):
            p=s.make(iid=identifier,amount=100);pr=s.resource.prepare(p);ap=s.approval(p,pr)
            g.reserve(s.agents[0].sign('INVOKE',p),pr,ap)
            t=g.begin(identifier);g.settle(s.resource.apply(p,pr,t));g.audit()
        spent=s.resource.totals()[0]
        result = {'issued_root_budget':100,'copied_independent_gate_databases':2,'actual_toy_spent':spent,
            'expected_limitation_reproduced':spent>100,
            'conclusion':'Privileged authority-state cloning violates the single-serialization-domain assumption. Both copies audit internally. No anti-rollback guarantee is claimed.'}
        return checked(spent==200, 'expected cloning limitation not reproduced', result)
    finally:s.close()

def propagation_model() -> dict:
    # Fixed-time discrete synthetic events; no measured Internet delays.
    rows=[];B=100;cost=1;ttl=2000;rate_step=20
    for n in (2,10,50):
        for lag in (0,100,1000,None):
            horizon=ttl if lag is None else min(ttl,lag)
            attempts=len(range(0,horizon,rate_step))
            naive=sum(min(B,attempts)*cost for _ in range(n))
            q,r=divmod(B,n);escrow=sum(min(q+(i<r),attempts)*cost for i in range(n))
            rows.append({'nodes':n,'revocation_delay_ms':lag,'token_ttl_ms':ttl,'attempt_step_ms':rate_step,
                'attempts_per_node_before_stop':attempts,'copied_budget_effect_units':naive,
                'disjoint_escrow_effect_units':escrow,'root_budget':B})
    result = {'rows':rows,'scope':'deterministic synthetic schedule; no consensus implementation, no real network, no statistical SLO claim',
        'assumption':'escrow partitions cannot be copied or rolled back and executors enforce local durable single-use; clock trustworthy'}
    return checked(all(row['disjoint_escrow_effect_units'] <= B for row in rows),
                   'synthetic escrow exceeded budget', result)

def run(out: Path) -> dict:
    out.mkdir(parents=True,exist_ok=True)
    tasks={'model_check':run_model,'generated_cases':generated,'local_benchmark':benchmarks,
           'strong_existing_baseline':existing_transaction_baseline,'cloning_limitation':clone_limitation,
           'synthetic_revocation':propagation_model}
    all_results={}
    for name,fn in tasks.items():
        print(f'RUN {name}',flush=True)
        try:
            result=fn()
        except CheckFailed as exc:
            (out/f'{name}.json').write_text(json.dumps(exc.result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
            raise
        all_results[name]=result
        (out/f'{name}.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
        print(f'OK {name}',flush=True)
    return all_results

if __name__=='__main__':run(Path('evidence'))
