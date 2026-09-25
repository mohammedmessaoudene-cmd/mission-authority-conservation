from __future__ import annotations
import copy
import json
import sqlite3
import unittest
from concurrent.futures import ThreadPoolExecutor
from lab.core import (Denied, Key, canon,decode,digest,verify,invocation,ToyResource)
from lab.scenario import Scenario

class ContractTests(unittest.TestCase):
    def setUp(self):
        self.s=Scenario()
        self.g=self.s.gate
        self.r=self.s.resource
    def tearDown(self):
        self.s.close()
    def denied(self, code, fn, *a, **kw):
        with self.assertRaises(Denied) as ctx:
            fn(*a,**kw)
        self.assertEqual(ctx.exception.code,code)
    def prepared(self, p=None):
        p=p or self.s.make()
        pr=self.r.prepare(p)
        return p,pr,self.s.agents[0].sign('INVOKE',p)

    def test_01_honest_payment(self):
        self.s.execute(self.s.make())
        self.assertEqual(self.r.totals(),[10,0,1]);self.g.audit()
    def test_02_signature_tamper(self):
        p,pr,sig=self.prepared();sig['payload']['target']='evil'
        self.denied('BAD_SIGNATURE',self.g.reserve,sig,pr)
    def test_03_wrong_actor_key(self):
        p,pr,_=self.prepared()
        self.denied('ACTOR_BINDING',self.g.reserve,self.s.agents[1].sign('INVOKE',p),pr)
    def test_04_unknown_key(self):
        p,pr,_=self.prepared()
        self.denied('ACTOR',self.g.reserve,Key.generate().sign('INVOKE',p),pr)
    def test_05_wrong_signature_domain(self):
        p,pr,_=self.prepared()
        self.denied('SIGNER_OR_DOMAIN',self.g.reserve,self.s.agents[0].sign('APPROVE',p),pr)
    def test_06_wrong_resource_signer(self):
        p,pr,sig=self.prepared();pr=self.s.agents[0].sign('PREPARED',pr['payload'])
        self.denied('SIGNER_OR_DOMAIN',self.g.reserve,sig,pr)
    def test_07_action_rebound_after_preview(self):
        p,pr,_=self.prepared();p['params']['amount_minor']=11
        self.denied('ACTION_BINDING',self.g.reserve,self.s.agents[0].sign('INVOKE',p),pr)
    def test_08_cross_audience(self):
        p=self.s.make(aud='other-tool')
        self.denied('AUDIENCE',self.r.prepare,p)
    def test_09_destination_outside_scope(self):
        p,pr,sig=self.prepared(self.s.make(target='evil.example'))
        self.denied('SCOPE',self.g.reserve,sig,pr)
    def test_10_unknown_top_level(self):
        p=self.s.make();p['requires_human']=False
        self.denied('SCHEMA',self.r.prepare,p)
    def test_11_floats_forbidden(self):
        self.denied('UNSUPPORTED_TYPE',canon,{'a':1.5})
    def test_12_boolean_amount_forbidden(self):
        self.denied('NATURAL_NUMBER',self.r.prepare,self.s.make(amount=True))
    def test_13_negative_amount_forbidden(self):
        self.denied('NATURAL_NUMBER',self.r.prepare,self.s.make(amount=-1))
    def test_14_zero_payment_forbidden(self):
        self.denied('NATURAL_NUMBER',self.r.prepare,self.s.make(amount=0))
    def test_15_duplicate_json_key(self):
        self.denied('DUPLICATE_KEY',decode,b'{"amount":1,"amount":1000}')
    def test_16_nonascii_profile_reject(self):
        self.denied('ASCII_OR_LENGTH',canon,{'target':'caf\u00e9'})
    def test_17_integer_overflow_reject(self):
        self.denied('INTEGER_RANGE',canon,{'n':2**60})
    def test_18_expiry_boundary(self):
        self.denied('EXPIRED',self.r.prepare,self.s.make(deadline=1000))
    def test_19_policy_version(self):
        p,pr,sig=self.prepared(self.s.make(policy='policy-v2'))
        self.denied('POLICY_VERSION',self.g.reserve,sig,pr)
    def test_20_resource_version(self):
        self.r.version='resource-v2';p,pr,sig=self.prepared()
        self.denied('RESOURCE_VERSION',self.g.reserve,sig,pr)
    def test_21_missing_human(self):
        p,pr,sig=self.prepared(self.s.make(amount=50))
        self.denied('HUMAN_REQUIRED',self.g.reserve,sig,pr)
    def test_22_software_human_role_accepted(self):
        self.s.execute(self.s.make(amount=50),approved=True)
        self.assertEqual(self.r.totals(),[50,0,1])
    def test_23_agent_signature_not_human_role(self):
        p,pr,sig=self.prepared(self.s.make(amount=50))
        ap=self.s.approval(p,pr,self.s.agents[0])
        self.denied('SIGNER_OR_DOMAIN',self.g.reserve,sig,pr,ap)
    def test_24_principal_is_not_automatically_human_role(self):
        p,pr,sig=self.prepared(self.s.make(amount=50))
        ap=self.s.approval(p,pr,self.s.principal)
        self.denied('SIGNER_OR_DOMAIN',self.g.reserve,sig,pr,ap)
    def test_25_approval_cannot_follow_changed_amount(self):
        p,pr,_=self.prepared(self.s.make(amount=50));ap=self.s.approval(p,pr)
        p['params']['amount_minor']=51;pr=self.r.prepare(p)
        self.denied('APPROVAL_BINDING',self.g.reserve,self.s.agents[0].sign('INVOKE',p),pr,ap)
    def test_26_approval_expiry(self):
        p,pr,sig=self.prepared(self.s.make(amount=50));ap=self.s.approval(p,pr)
        ap['payload']['expires']=1000;ap=self.s.human.sign('APPROVE',ap['payload'])
        self.denied('APPROVAL_EXPIRED',self.g.reserve,sig,pr,ap)
    def test_27_duplicate_reserve_not_duplicate_debit(self):
        p,pr,sig=self.prepared();self.g.reserve(sig,pr);b=self.g.balance()
        self.g.reserve(sig,pr);self.assertEqual(b,self.g.balance());self.g.audit()
    def test_28_same_id_different_body(self):
        self.s.reserve(self.s.make());p,pr,sig=self.prepared(self.s.make(amount=11))
        self.denied('IDEMPOTENCY_CONFLICT',self.g.reserve,sig,pr)
    def test_29_double_dispatch(self):
        self.s.reserve(self.s.make());self.g.begin('a')
        self.denied('NO_REDISPATCH',self.g.begin,'a')
    def test_30_resource_duplicate_idempotence(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a')
        a=self.r.apply(p,pr,t);b=self.r.apply(p,pr,t)
        self.assertEqual(a,b);self.assertEqual(self.r.totals(),[10,0,1])
    def test_31_duplicate_receipt_no_reaccounting(self):
        rec=self.s.execute(self.s.make());before=self.g.balance();self.g.settle(rec)
        self.assertEqual(before,self.g.balance());self.g.audit()
    def test_32_forged_resource_receipt(self):
        rec=self.s.execute(self.s.make());bad=self.s.agents[0].sign('RECEIPT',rec['payload'])
        self.denied('SIGNER_OR_DOMAIN',self.g.settle,bad)
    def test_33_receipt_bound_cost(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a');rec=self.r.apply(p,pr,t)
        rec['payload']['cost'][0]=1;rec=self.s.rkey.sign('RECEIPT',rec['payload'])
        self.denied('RECEIPT_BINDING',self.g.settle,rec)
    def test_34_no_budget_overrun(self):
        self.s.execute(self.s.make(amount=1000),approved=True)
        self.denied('BUDGET',self.s.reserve,self.s.make('b',amount=1));self.g.audit()
    def test_35_export_cost_measured_by_resource(self):
        p=self.s.make(op='export',target='internal.example');pr=self.r.prepare(p)
        self.assertEqual(pr['payload']['cost'],[0,80,1])
    def test_36_agent_cannot_declare_zero_export_cost(self):
        p=self.s.make(op='export',params={'dataset':'dataset-a','cost':0})
        self.denied('SCHEMA',self.r.prepare,p)
    def test_37_export_byte_budget(self):
        self.s.issue('small',self.s.agents[0],[0,79,10])
        p=self.s.make(cap='small',mission='small',op='export',target='internal.example')
        self.denied('BUDGET',self.s.reserve,p,True)
    def test_38_irreversible_count_budget(self):
        self.s.issue('small',self.s.agents[0],[100,1000,1])
        self.s.execute(self.s.make(cap='small',mission='small'))
        self.denied('BUDGET',self.s.reserve,self.s.make('b',cap='small',mission='small'))
    def test_39_delegation_conserves_budget(self):
        self.g.delegate(self.s.delegation());self.assertEqual(self.g.balance()['free'],[900,10000,990]);self.g.audit()
    def test_40_delegation_budget_clone_denied(self):
        self.g.delegate(self.s.delegation(budget=[1000,0,10]))
        self.denied('BUDGET',self.g.delegate,self.s.delegation(id='child2',budget=[1,0,1]))
    def test_41_delegated_subject_cannot_be_forged(self):
        self.g.delegate(self.s.delegation());p=self.s.make(cap='child')
        self.denied('SUBJECT',self.s.reserve,p)
    def test_42_honest_delegate(self):
        self.g.delegate(self.s.delegation())
        p=invocation('a',self.s.agents[1],cap='child')
        self.s.execute(p,actor=self.s.agents[1]);self.g.audit()
    def test_43_delegation_permission_widening(self):
        self.g.delegate(self.s.delegation())
        d=self.s.delegation(id='grandchild',parent='child',actor=1,subject=2,ops=['pay','export'])
        self.denied('DELEGATION_WIDENING',self.g.delegate,d)
    def test_44_delegation_expiry_widening(self):
        self.denied('DELEGATION_WIDENING',self.g.delegate,self.s.delegation(expires=1300))
    def test_45_delegation_wrong_signer(self):
        d=self.s.delegation(actor=1)
        self.denied('SIGNER_OR_DOMAIN',self.g.delegate,d)
    def test_46_wrong_mission_binding(self):
        self.denied('MISSION_BINDING',self.s.reserve,self.s.make(mission='other'))
    def test_47_revoke_before_reserve(self):
        self.s.revoke();self.denied('REVOKED',self.s.reserve,self.s.make())
    def test_48_revoke_reserved_before_dispatch(self):
        self.s.reserve(self.s.make());self.s.revoke();self.denied('REVOKED',self.g.begin,'a')
    def test_49_parent_revocation_cascades(self):
        self.g.delegate(self.s.delegation());self.s.revoke()
        p=invocation('a',self.s.agents[1],cap='child')
        self.denied('REVOKED',self.s.reserve,p,actor=self.s.agents[1])
    def test_50_dispatched_before_revocation_is_inflight_not_retracted(self):
        p=self.s.make();pr,_=self.s.reserve(p);ticket=self.g.begin('a');self.s.revoke()
        rec=self.r.apply(p,pr,ticket);self.g.settle(rec)
        self.assertEqual(self.r.totals(),[10,0,1]);self.g.audit()
    def test_51_forged_revocation(self):
        bad=self.s.agents[0].sign('REVOKE',{'cap':'root','epoch':2})
        self.denied('SIGNER_OR_DOMAIN',self.g.revoke,bad)
    def test_52_revocation_rollback(self):
        bad=self.s.principal.sign('REVOKE',{'cap':'root','epoch':1})
        self.denied('REVOCATION_EPOCH',self.g.revoke,bad)
    def test_53_old_epoch_unrelated_mission(self):
        self.s.issue('other',self.s.agents[0],[10,10,10]);self.s.reserve(self.s.make())
        self.s.revoke('other');self.denied('STALE_EPOCH',self.g.begin,'a')
    def test_54_cancel_reserved_refunds(self):
        self.s.reserve(self.s.make());self.g.cancel('a')
        self.assertEqual(self.g.balance()['free'],[1000,10000,1000]);self.g.audit()
    def test_55_cancel_dispatched_forbidden(self):
        self.s.reserve(self.s.make());self.g.begin('a')
        self.denied('UNSAFE_REFUND',self.g.cancel,'a')
    def test_56_unknown_holds_budget(self):
        self.s.reserve(self.s.make());self.g.begin('a');self.g.mark_unknown('a')
        self.assertEqual(self.g.balance()['free'][0],990)
        self.denied('UNSAFE_REFUND',self.g.cancel,'a');self.g.audit()
    def test_57_timeout_never_means_not_applied(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a');self.r.apply(p,pr,t)
        self.g.mark_unknown('a');self.denied('NO_REDISPATCH',self.g.begin,'a')
        self.assertEqual(self.g.settle(self.r.receipt('a')),'COMMITTED');self.g.audit()
    def test_58_query_absence_not_evidence_for_refund(self):
        self.s.reserve(self.s.make());self.g.begin('a');self.g.mark_unknown('a')
        self.assertIsNone(self.r.receipt('a'));self.denied('UNSAFE_REFUND',self.g.cancel,'a')
    def test_59_restart_gate_preserves_uncertain(self):
        self.s.reserve(self.s.make());self.g.begin('a');self.g.mark_unknown('a')
        g2=self.s.open_gate();self.denied('NO_REDISPATCH',g2.begin,'a');g2.audit()
    def test_60_restart_resource_preserves_idempotence(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a');self.r.apply(p,pr,t)
        r2=ToyResource(self.s.base/'resource.db',self.s.clock,self.s.rkey,self.s.gkey)
        r2.apply(p,pr,t);self.assertEqual(r2.totals(),[10,0,1])
    def test_61_changed_resource_after_dispatch_aborts(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a');self.r.version='resource-v2'
        rec=self.r.apply(p,pr,t);self.assertEqual(self.g.settle(rec),'ABORTED')
        self.assertEqual(self.r.totals(),[0,0,0]);self.assertEqual(self.g.balance()['free'][0],1000)
    def test_62_not_applied_is_terminal_at_resource(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a');self.r.version='resource-v2'
        rec=self.r.apply(p,pr,t);self.r.version='resource-v1'
        self.assertEqual(self.r.apply(p,pr,t),rec);self.assertEqual(self.r.totals(),[0,0,0])
    def test_63_expiry_before_dispatch(self):
        self.s.reserve(self.s.make());self.s.clock.value=1100
        self.denied('EXPIRED',self.g.begin,'a')
    def test_64_clock_rollback_rejected(self):
        self.g.audit();self.s.clock.value=999;self.denied('CLOCK_ROLLBACK',self.g.audit)
    def test_65_event_tampering_detected(self):
        c=sqlite3.connect(self.g.path);c.execute("UPDATE events SET body='{}' WHERE seq=1");c.commit();c.close()
        self.denied('EVENT_CHAIN',self.g.audit)
    def test_66_balance_tampering_detected(self):
        c=sqlite3.connect(self.g.path);c.execute("UPDATE caps SET f0=f0+1 WHERE id='root'");c.commit();c.close()
        self.denied('CONSERVATION',self.g.audit)
    def test_67_concurrent_reservation_cannot_overspend(self):
        self.s.issue('small',self.s.agents[0],[100,0,100])
        def attempt(i):
            try:
                self.s.reserve(self.s.make(f'p-{i}',cap='small',mission='small',amount=1));return True
            except Denied as e:
                self.assertEqual(e.code,'BUDGET');return False
        with ThreadPoolExecutor(max_workers=16) as pool:
            results=list(pool.map(attempt,range(200)))
        self.assertEqual(sum(results),100);self.assertEqual(self.g.balance('small')['free'],[0,0,0]);self.g.audit()
    def test_68_concurrent_duplicate_commits_once(self):
        p=self.s.make();pr,_=self.s.reserve(p);t=self.g.begin('a')
        with ThreadPoolExecutor(max_workers=8) as pool:
            receipts=list(pool.map(lambda _:self.r.apply(p,pr,t),range(40)))
        self.assertTrue(all(r==receipts[0] for r in receipts));self.assertEqual(self.r.totals(),[10,0,1])
    def test_69_delegation_duplicate_id(self):
        d=self.s.delegation();self.g.delegate(d);self.denied('CAP_EXISTS',self.g.delegate,d)
    def test_70_policy_does_not_prove_message_truth(self):
        p=self.s.make(op='send',target='internal.example',params={'message':'2+2=5'})
        self.s.execute(p);self.assertEqual(self.r.totals(),[0,5,1])
    def test_71_direct_resource_without_gate_permit(self):
        p=self.s.make();pr=self.r.prepare(p)
        fake=self.s.agents[0].sign('DISPATCH',{'iid':'a'})
        self.denied('SIGNER_OR_DOMAIN',self.r.apply,p,pr,fake)
    def test_72_noninteger_json_rejected(self):
        for b in (b'{"n":1.0}',b'{"n":NaN}',b'{"n":Infinity}'):
            with self.subTest(b=b):self.denied('NONINTEGER_NUMBER',decode,b)
    def test_73_canonical_key_order_stable(self):
        self.assertEqual(digest({'b':1,'a':2}),digest({'a':2,'b':1}))
    def test_74_cancelled_id_cannot_be_reused(self):
        p,pr,sig=self.prepared();self.g.reserve(sig,pr);self.g.cancel('a')
        self.assertEqual(self.g.reserve(sig,pr),'ABORTED');self.denied('NO_REDISPATCH',self.g.begin,'a')
    def test_75_root_certificate_wrong_issuer(self):
        p={'id':'r2','subject':self.s.agents[0].kid,'aud':'tool-demo','ops':['pay'],
           'dest':['vendor-a'],'expires':1200,'budget':[10,0,10]}
        self.denied('SIGNER_OR_DOMAIN',self.g.issue,self.s.agents[0].sign('MISSION',p))
    def test_76_receipt_unknown_action(self):
        p={'iid':'missing','action_hash':'x','preview_hash':'y','cost':[1,0,1],
           'result':'APPLIED','epoch':1,'aud':'tool-demo'}
        self.denied('UNKNOWN_ACTION',self.g.settle,self.s.rkey.sign('RECEIPT',p))

    def test_77_approval_expiry_rechecked_before_dispatch(self):
        p,pr,sig=self.prepared(self.s.make(amount=50))
        ap=self.s.approval(p,pr);ap['payload']['expires']=1001
        self.g.reserve(sig,pr,self.s.human.sign('APPROVE',ap['payload']))
        self.s.clock.value=1002
        self.denied('EXPIRED',self.g.begin,p['iid'])
    def test_78_policy_change_before_dispatch(self):
        p=self.s.make();self.s.reserve(p)
        self.g.policy='policy-v2'
        self.denied('POLICY_VERSION',self.g.begin,p['iid'])
    def test_79_cap_expiry_limits_inflight_permit(self):
        p=self.s.make(deadline=1500);pr,_=self.s.reserve(p);t=self.g.begin(p['iid'])
        self.s.clock.value=1201
        rec=self.r.apply(p,pr,t)
        self.assertEqual(rec['payload']['result'],'NOT_APPLIED')
        self.g.settle(rec);self.g.audit()
    def test_80_approval_expiry_limits_inflight_permit(self):
        p,pr,sig=self.prepared(self.s.make(amount=50))
        ap=self.s.approval(p,pr);ap['payload']['expires']=1001
        self.g.reserve(sig,pr,self.s.human.sign('APPROVE',ap['payload']))
        t=self.g.begin(p['iid']);self.s.clock.value=1002
        rec=self.r.apply(p,pr,t)
        self.assertEqual(rec['payload']['result'],'NOT_APPLIED')
        self.g.settle(rec);self.g.audit()
    def test_81_malformed_key_identifier_fails_closed(self):
        p,pr,sig=self.prepared();sig['kid']=[]
        self.denied('ACTOR',self.g.reserve,sig,pr)

    def test_82_verification_requires_no_private_key(self):
        from lab.core import verify_public
        signed=self.s.principal.sign('EXAMPLE',{'n':7})
        self.assertEqual(verify_public(signed,'EXAMPLE',self.s.principal.public),{'n':7})
    def test_83_wrong_public_key_denied(self):
        from lab.core import verify_public
        signed=self.s.principal.sign('EXAMPLE',{'n':7})
        self.denied('SIGNER_OR_DOMAIN',verify_public,signed,'EXAMPLE',self.s.agents[0].public)

if __name__=='__main__':unittest.main(verbosity=2)
