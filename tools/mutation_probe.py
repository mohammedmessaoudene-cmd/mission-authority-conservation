"""A focused safety test and direct counterexample observer for one code mutant."""
import hashlib,io,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tests'))
from lab.core import Denied
from lab.scenario import Scenario

def observe(which):
    s=Scenario()
    try:
        if which=='M1':
            s.execute(s.make(amount=1000),approved=True)
            try:s.reserve(s.make('b',amount=1))
            except Denied as e:return {'unsafe':False,'denial':e.code}
            free=s.gate.balance()['free'][0]
            return {'unsafe':free<0,'remaining_money':free}
        if which=='M2':
            p=s.make();pr,_=s.reserve(p);permit=s.gate.begin('a');s.gate.mark_unknown('a')
            try:s.gate.cancel('a')
            except Denied as e:return {'unsafe':False,'denial':e.code}
            s.resource.apply(p,pr,permit)
            s.execute(s.make('b',amount=1000),approved=True)
            total=s.resource.totals()[0]
            return {'unsafe':total>1000,'initial_money':1000,'actual_effect_money':total}
        if which=='M3':
            p=s.make(amount=50);pr=s.resource.prepare(p);ap=s.approval(p,pr)
            ap['payload']['expires']=1001
            s.gate.reserve(s.agents[0].sign('INVOKE',p),pr,s.human.sign('APPROVE',ap['payload']))
            permit=s.gate.begin('a');s.clock.value=1002
            receipt=s.resource.apply(p,pr,permit)
            return {'unsafe':receipt['payload']['result']=='APPLIED',
                    'resource_result':receipt['payload']['result'],'now':1002,'approval_expiry':1001}
        if which=='M4':
            s.reserve(s.make());s.gate.policy='policy-v2'
            try:s.gate.begin('a')
            except Denied as e:return {'unsafe':False,'denial':e.code}
            return {'unsafe':True,'dispatch_after_policy_change':True}
        raise ValueError(which)
    finally:s.close()

def run(which, test, line):
    visited=set()
    def trace(frame,event,arg):
        if event=='line' and Path(frame.f_code.co_filename).name=='core.py':visited.add(frame.f_lineno)
        return trace
    sys.settrace(trace)
    try:
        stream=io.StringIO()
        suite=unittest.defaultTestLoader.loadTestsFromName('test_contract.ContractTests.'+test)
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
        observation=observe(which)
    finally:sys.settrace(None)
    return {'core_sha256':hashlib.sha256((Path(__file__).resolve().parents[1]/'lab/core.py').read_bytes()).hexdigest(),
            'optimization':sys.flags.optimize,'test':test,'tests_run':result.testsRun,'successful':result.wasSuccessful(),
            'failures':len(result.failures),'errors':len(result.errors),'direct':observation,
            'target_line_executed':line in visited,'log':stream.getvalue()}
if __name__=='__main__':
    print(json.dumps(run(sys.argv[1],sys.argv[2],int(sys.argv[3])),indent=2))
