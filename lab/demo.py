"""An executed wire transcript with public keys only; all effects are toy rows."""
from pathlib import Path
import json
from .scenario import Scenario
from .core import verify_public

def run(out: Path) -> dict:
    s=Scenario(budget=[100,500,10])
    try:
        p=s.make(iid='demo-exact-action',amount=50)
        preview=s.resource.prepare(p);signed=s.agents[0].sign('INVOKE',p);approval=s.approval(p,preview)
        s.gate.reserve(signed,preview,approval);permit=s.gate.begin(p['iid'])
        receipt=s.resource.apply(p,preview,permit)
        # Simulated lost acknowledgement: durable effect exists, gate is uncertain.
        s.gate.mark_unknown(p['iid']);before=s.gate.balance()
        recovered=s.resource.receipt(p['iid']);s.gate.settle(recovered)
        objects={'invocation':signed,'preview':preview,'approval':approval,'permit':permit,'receipt':receipt}
        keys={'invocation':s.agents[0].public.hex(),'preview':s.rkey.public.hex(),
              'approval':s.human.public.hex(),'permit':s.gkey.public.hex(),'receipt':s.rkey.public.hex()}
        for label,obj in objects.items():verify_public(obj,obj['kind'],bytes.fromhex(keys[label]))
        result={'profile':'ATLAB/0.1 research-only','seed_private_keys_exported':False,
                'human_presence_demonstrated':False,'software_role_approval_only':True,
                'public_keys_hex':keys,'objects':objects,'state_before_reconciliation':'UNKNOWN',
                'balance_while_unknown':before,'state_after':s.gate.state(p['iid']),
                'balance_after':s.gate.balance(),'resource_effect_totals':s.resource.totals(),'audit':s.gate.audit()}
        out.mkdir(parents=True,exist_ok=True);(out/'demo_transcript.json').write_text(json.dumps(result,indent=2)+'\n')
        return result
    finally:s.close()

if __name__=='__main__':run(Path('evidence'))
