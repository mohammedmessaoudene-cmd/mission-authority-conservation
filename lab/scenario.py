"""Local test fixture; software keys represent roles, not real human presence."""
from __future__ import annotations
import tempfile
from pathlib import Path
from typing import Any
from .core import Clock, Gate, ToyResource, Key, invocation, digest

class Scenario:
    def __init__(self, budget: list[int] | None = None):
        self.tmp = tempfile.TemporaryDirectory(prefix="agent-trust-")
        self.base = Path(self.tmp.name)
        self.clock = Clock()
        self.principal, self.human, self.gkey, self.rkey = (Key.generate() for _ in range(4))
        self.agents = [Key.generate() for _ in range(12)]
        self.actors = {a.kid:a for a in self.agents}
        self.gate = self.open_gate()
        self.resource = ToyResource(self.base/'resource.db', self.clock, self.rkey, self.gkey)
        self.issue('root', self.agents[0], budget or [1000,10000,1000])

    def close(self) -> None:
        self.tmp.cleanup()

    def open_gate(self) -> Gate:
        return Gate(self.base/'gate.db', self.clock, self.gkey, self.principal,
                    self.human,self.rkey,self.actors)

    def issue(self, id: str, actor: Key, budget: list[int]) -> None:
        self.gate.issue(self.principal.sign('MISSION', {
            'id':id,'subject':actor.kid,'aud':'tool-demo','ops':['pay','send','export'],
            'dest':['vendor-a','internal.example'],'expires':1200,'budget':budget}))

    def make(self, iid: str = 'a', **kw: Any) -> dict[str,Any]:
        return invocation(iid, self.agents[0], **kw)

    def approval(self,p: dict[str,Any],pr: dict[str,Any], key: Key | None = None) -> dict[str,Any]:
        return (key or self.human).sign('APPROVE',{
            'action_hash':digest(p),'preview_hash':digest(pr['payload']),'cap':p['cap'],
            'epoch':self.gate.epoch(),'expires':p['deadline'],'decision':'approve'})

    def reserve(self,p: dict[str,Any], approved: bool = False,
                actor: Key | None = None) -> tuple[dict[str,Any],str]:
        a=actor or self.agents[0]
        pr=self.resource.prepare(p)
        status=self.gate.reserve(a.sign('INVOKE',p),pr,self.approval(p,pr) if approved else None)
        return pr,status

    def execute(self,p: dict[str,Any],approved: bool = False,
                actor: Key | None = None) -> dict[str,Any]:
        pr,_=self.reserve(p,approved,actor)
        ticket=self.gate.begin(p['iid'])
        rec=self.resource.apply(p,pr,ticket)
        self.gate.settle(rec)
        return rec

    def delegation(self, id: str = 'child', parent: str = 'root', actor: int = 0,
                   subject: int = 1, budget: list[int] | None = None, **kw: Any) -> dict[str,Any]:
        p={'parent':parent,'id':id,'subject':self.agents[subject].kid,'aud':'tool-demo',
            'ops':['pay'],'dest':['vendor-a'],'expires':1150,'budget':budget or [100,0,10]}
        p.update(kw)
        return self.agents[actor].sign('DELEGATE',p)

    def revoke(self, cap: str = 'root') -> None:
        self.gate.revoke(self.principal.sign('REVOKE',{'cap':cap,'epoch':self.gate.epoch()+1}))
