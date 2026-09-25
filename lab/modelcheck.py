"""Finite-state exploration, not a theorem prover or code-refinement proof."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, replace, asdict
from typing import Iterator

@dataclass(frozen=True)
class State:
    free: int=4
    committed: int=0
    mode: tuple[str,...]=('N','N','N')
    ticket: tuple[bool,...]=(False,False,False)
    receipt: tuple[int,...]=(0,0,0)  # 0 absent,1 applied,2 durably refused
    effects: tuple[int,...]=(0,0,0)
    revoked: bool=False
    revoked_dispatch: bool=False

def at(t: tuple, i: int, value):
    return t[:i]+(value,)+t[i+1:]

def transitions(s: State, mutant: str='none') -> Iterator[tuple[str,State]]:
    if not s.revoked:
        yield 'revoke',replace(s,revoked=True)
    for i,m in enumerate(s.mode):
        if m=='N' and not s.revoked and (s.free>=2 or mutant=='no_budget_check'):
            yield f'reserve({i})',replace(s,free=s.free-2,mode=at(s.mode,i,'R'))
        if m=='R':
            yield f'cancel_before_dispatch({i})',replace(s,free=s.free+2,mode=at(s.mode,i,'A'))
            if not s.revoked or mutant=='ignore_revocation':
                yield f'dispatch({i})',replace(s,mode=at(s.mode,i,'D'),ticket=at(s.ticket,i,True),
                    revoked_dispatch=s.revoked_dispatch or s.revoked)
        if m=='D':
            yield f'lose_ack({i})',replace(s,mode=at(s.mode,i,'U'))
        if m=='U' and mutant=='refund_unknown':
            yield f'UNSAFE_refund_unknown({i})',replace(s,free=s.free+2,mode=at(s.mode,i,'A'))
        if s.ticket[i] and s.receipt[i]==0:
            yield f'resource_apply({i})',replace(s,receipt=at(s.receipt,i,1),effects=at(s.effects,i,s.effects[i]+1))
            yield f'resource_durable_refusal({i})',replace(s,receipt=at(s.receipt,i,2))
        if s.ticket[i] and s.receipt[i]==1 and mutant=='no_resource_idempotence':
            yield f'UNSAFE_replay_effect({i})',replace(s,effects=at(s.effects,i,s.effects[i]+1))
        if m in ('D','U') and s.receipt[i]:
            if s.receipt[i]==1:
                yield f'reconcile_applied({i})',replace(s,mode=at(s.mode,i,'C'),committed=s.committed+2)
            else:
                yield f'reconcile_not_applied({i})',replace(s,mode=at(s.mode,i,'A'),free=s.free+2)

def violations(s: State) -> list[str]:
    bad=[]
    if s.free<0: bad.append('negative_free_budget')
    if s.free+s.committed+2*sum(m in ('R','D','U') for m in s.mode)!=4:
        bad.append('accounting_conservation')
    if 2*sum(s.effects)>4:bad.append('effective_aggregate_budget_exceeded')
    if max(s.effects)>1:bad.append('duplicated_resource_effect')
    if s.revoked_dispatch:bad.append('new_dispatch_after_revocation')
    # A dispatched permission cannot remain usable after its allocation is refunded.
    if any(s.mode[i]=='A' and s.ticket[i] and s.receipt[i]!=2 for i in range(3)):
        bad.append('unbacked_live_or_applied_permission')
    return bad

def explore(mutant: str='none') -> dict:
    initial=State();queue=deque([initial]);parents={initial:None};edges=0
    while queue:
        s=queue.popleft()
        bad=violations(s)
        if bad:
            trace=[];cursor=s
            while parents[cursor] is not None:
                prev,label=parents[cursor];trace.append(label);cursor=prev
            return {'variant':mutant,'safe_in_finite_model':False,'states_discovered':len(parents),
                'edges_examined':edges,'violations':bad,'counterexample':list(reversed(trace)),
                'final_state':asdict(s)}
        for label,nxt in transitions(s,mutant):
            edges+=1
            if nxt not in parents:
                parents[nxt]=(s,label);queue.append(nxt)
    return {'variant':mutant,'safe_in_finite_model':True,'states_discovered':len(parents),
        'edges_examined':edges,'violations':[], 'scope':'3 actions, cost 2 each, budget 4, finite modes'}

def run() -> dict:
    variants=['none','no_budget_check','refund_unknown','ignore_revocation','no_resource_idempotence']
    result={v:explore(v) for v in variants}
    if not result['none']['safe_in_finite_model']: raise RuntimeError('Finite reference model failed')
    if not all(not result[v]['safe_in_finite_model'] for v in variants[1:]):
        raise RuntimeError('Model negative control escaped detection')
    return result
