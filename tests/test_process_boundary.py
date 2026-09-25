from __future__ import annotations
import unittest
from lab.scenario import Scenario
from lab.process_fixture import ResourceProcess

class ProcessBoundaryTests(unittest.TestCase):
    def setUp(self): self.s=Scenario()
    def tearDown(self): self.s.close()
    def worker(self):
        return ResourceProcess(self.s.base/'resource.db',self.s.rkey,self.s.gkey.public,self.s.clock.now())
    def prepared(self, **kw):
        p=self.s.make(**kw);pr,_=self.s.reserve(p);ticket=self.s.gate.begin(p['iid'])
        return {'op':'apply','action':p,'prepared':pr,'permit':ticket}
    def test_P1_separate_process_application(self):
        cmd=self.prepared()
        with self.worker() as r:
            rec=r.call(**cmd)
            self.s.gate.settle(rec)
            self.assertEqual(r.call(op='totals'),[10,0,1])
        self.s.gate.audit()
    def test_P2_exit_after_commit_reconcile_after_restart(self):
        cmd=self.prepared()
        with self.worker() as r:
            r.send(**cmd,exit_after_commit=True)
            with self.assertRaises(EOFError): r.receive()
            r.process.join(5); self.assertEqual(r.process.exitcode,73)
        self.s.gate.mark_unknown('a')
        self.s.gate=self.s.open_gate()
        self.assertEqual(self.s.gate.balance()['free'][0],990)
        with self.worker() as r:
            rec=r.call(op='receipt',iid='a')
            self.assertIsNotNone(rec)
            self.s.gate.settle(rec)
            self.assertEqual(r.call(op='totals'),[10,0,1])
        self.s.gate.audit()
    def test_P3_replay_survives_worker_restart(self):
        cmd=self.prepared()
        with self.worker() as r: first=r.call(**cmd)
        with self.worker() as r:
            second=r.call(**cmd)
            self.assertEqual(first,second)
            self.assertEqual(r.call(op='totals'),[10,0,1])
        self.s.gate.settle(second);self.s.gate.audit()
    def test_P4_expired_approval_produces_durable_refusal(self):
        p=self.s.make(amount=50)
        pr=self.s.resource.prepare(p);ap=self.s.approval(p,pr)
        ap['payload']['expires']=1001;ap=self.s.human.sign('APPROVE',ap['payload'])
        self.s.gate.reserve(self.s.agents[0].sign('INVOKE',p),pr,ap)
        permit=self.s.gate.begin('a')
        cmd={'op':'apply','action':p,'prepared':pr,'permit':permit}
        with self.worker() as r:
            rec=r.call(**cmd,now=1002)
            self.assertEqual(rec['payload']['result'],'NOT_APPLIED')
        self.s.clock.value=1002;self.s.gate.settle(rec)
        with self.worker() as r:
            self.assertEqual(r.call(**cmd,now=1003),rec)
            self.assertEqual(r.call(op='totals',now=1003),[0,0,0])
        self.assertEqual(self.s.gate.balance()['free'][0],1000);self.s.gate.audit()
    def test_P5_absent_receipt_does_not_refund_unknown(self):
        self.prepared();self.s.gate.mark_unknown('a')
        with self.worker() as r: self.assertIsNone(r.call(op='receipt',iid='a'))
        self.assertEqual(self.s.gate.balance()['free'][0],990)
        self.s.gate.audit()
    def test_P6_two_processes_same_permit_one_effect(self):
        cmd=self.prepared()
        with self.worker() as a,self.worker() as b:
            a.send(**cmd);b.send(**cmd)
            r1=a.receive();r2=b.receive()
            self.assertEqual(r1,r2)
            self.assertEqual(a.call(op='totals'),[10,0,1])
        self.s.gate.settle(r1);self.s.gate.audit()
if __name__=='__main__': unittest.main(verbosity=2)
