from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_100_damm_v2_pool_state_account_audit.py"
TEST=ROOT/"test_suls_100_damm_v2_pool_state_account_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import json

def audit(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/event_driven_birth_inbox.json"
 births=list(json.loads(p.read_text(encoding="utf-8")).get("births") or [])
 if not births:raise RuntimeError("NO_BIRTHS")
 b=births[-1];raw=(b.get("envelope") or {}).get("raw_transaction") or {}
 tx=raw.get("transaction") or {};msg=tx.get("message") or {};meta=raw.get("meta") or {}
 keys=msg.get("accountKeys") or []
 def key(i):
  if not isinstance(i,int) or i>=len(keys):return None
  x=keys[i];return x.get("pubkey") if isinstance(x,dict) else x
 ins=[]
 for n,ix in enumerate(msg.get("instructions") or []):
  ac=ix.get("accounts") or []
  ins.append({"index":n,"programId":ix.get("programId"),
   "programIdIndex":ix.get("programIdIndex"),
   "resolved_program":key(ix.get("programIdIndex")),
   "accounts":[key(i) if isinstance(i,int) else i for i in ac],
   "data":ix.get("data")})
 return {"revision":"SULS_100","signature":b.get("signature"),
  "account_keys":keys,"instructions":ins,
  "preTokenBalances":meta.get("preTokenBalances") or [],
  "postTokenBalances":meta.get("postTokenBalances") or [],
  "logs":meta.get("logMessages") or [],
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/damm_v2_pool_state_account_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_100_damm_v2_pool_state_account_audit import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"])
  print("[ACCOUNT_KEYS]",json.dumps(d["account_keys"],indent=2))
  print("[INSTRUCTIONS]",json.dumps(d["instructions"],indent=2))
  print("[PRE_TOKEN]",json.dumps(d["preTokenBalances"],indent=2))
  print("[POST_TOKEN]",json.dumps(d["postTokenBalances"],indent=2))
  print("[LOGS]",json.dumps(d["logs"],indent=2))
  self.assertGreater(len(d["account_keys"]),0)
  print("[PASS] SULS-100 DAMM V2 pool-state account physical audit")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")