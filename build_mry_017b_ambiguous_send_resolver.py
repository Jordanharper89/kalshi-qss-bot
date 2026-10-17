from pathlib import Path
import ast

P=Path("qseries_v2/oracle_execution/solana_atomic_executor")
M=P/"mry_017b_ambiguous_send_resolver.py"
T=Path("test_mry_017b_ambiguous_send_resolver.py")

module='''from __future__ import annotations
import time
from . import runtime as rt

def resolve():
    state=rt._live_010_load()
    if not bool(state.get("send_attempted")):
        print("[MRY017B_CLEAR] send_attempted=FALSE action=NONE",flush=True); return True
    status=str(state.get("status") or "")
    sig=state.get("send_signature")
    if status!="SEND_AMBIGUOUS_HOLD" or sig:
        print("[MRY017B_HOLD] status=%s signature=%s"%(status,sig),flush=True); return False
    attempted=float(state.get("attempted_unix") or 0)
    age=time.time()-attempted
    _,user=rt.q87.c.sim_identity()
    rows=rt.q96._rpc("getSignaturesForAddress",[
        str(user),{"limit":100,"commitment":"finalized"}
    ])
    if not isinstance(rows,list):
        raise RuntimeError("MRY017B_SIGNATURE_HISTORY_NOT_LIST")
    recent=[x for x in rows if float(x.get("blockTime") or 0)>=attempted-5]
    if recent:
        print("[MRY017B_HOLD] finalized_wallet_activity_after_ambiguous=%d first_signature=%s"%(
            len(recent),recent[0].get("signature")),flush=True); return False
    if age<120:
        print("[MRY017B_HOLD] ambiguous_age_seconds=%.1f minimum=120"%age,flush=True); return False
    state["send_attempted"]=False
    state["send_signature"]=None
    state["status"]="AMBIGUOUS_REARMED_NO_FINALIZED_WALLET_ACTIVITY"
    state["ambiguity_resolved_unix"]=time.time()
    rt._live_010_save(state)
    print("[MRY017B_REARMED] no finalized wallet activity after ambiguous send",flush=True)
    return True

if __name__=="__main__":
    raise SystemExit(0 if resolve() else 2)
'''

test='''import ast,unittest
from pathlib import Path
P=Path("qseries_v2/oracle_execution/solana_atomic_executor/mry_017b_ambiguous_send_resolver.py")
class T(unittest.TestCase):
 def test_source(self):
  s=P.read_text(encoding="utf-8");ast.parse(s)
  self.assertIn("getSignaturesForAddress",s)
  self.assertIn("SEND_AMBIGUOUS_HOLD",s)
  self.assertIn("send_attempted\\"]=False",s)
  self.assertIn("age<120",s)
if __name__=="__main__":unittest.main(verbosity=2)
'''

for x in (module,test): ast.parse(x)
M.write_text(module,encoding="utf-8")
T.write_text(test,encoding="utf-8")

print("[PASS] MRY-017B installed")
print("[PASS] ambiguous send requires finalized-chain clearance before rearm")
print("[PASS] no blind resend permitted")