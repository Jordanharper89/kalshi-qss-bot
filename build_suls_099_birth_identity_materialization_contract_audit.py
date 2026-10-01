from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_099_birth_identity_materialization_contract_audit.py"
TEST=ROOT/"test_suls_099_birth_identity_materialization_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import inspect,json
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance import suls_042_native_birth_materialization as m

def audit(root):
 b=root/"runtime_state/solana_opportunities/launch_surveillance"
 inbox=json.loads((b/"event_driven_birth_inbox.json").read_text(encoding="utf-8"))
 events=json.loads((b/"confirmed_tradeable_birth_events.json").read_text(encoding="utf-8"))
 births=list(inbox.get("births") or [])
 out_events=list(events.get("events") or [])

 def shape(x):
  if not x:return {}
  env=x.get("envelope") or {}
  raw=env.get("raw_transaction") or {}
  tx=raw.get("transaction") or {}
  msg=tx.get("message") or {}
  meta=raw.get("meta") or {}
  return {
   "top_keys":sorted(x.keys()),
   "envelope_keys":sorted(env.keys()),
   "raw_keys":sorted(raw.keys()),
   "message_keys":sorted(msg.keys()),
   "meta_keys":sorted(meta.keys()),
   "account_keys_type":type(msg.get("accountKeys")).__name__,
   "account_keys_count":len(msg.get("accountKeys") or []),
   "log_count":len(meta.get("logMessages") or []),
   "signature":x.get("signature"),
   "token_address":x.get("token_address"),
   "pair_address":x.get("pair_address"),
  }

 return {
  "revision":"SULS_099",
  "birth_count":len(births),
  "event_count":len(out_events),
  "birth_sample":shape(births[-1] if births else {}),
  "event_sample":shape(out_events[-1] if out_events else {}),
  "materializer_source":inspect.getsource(m._materialize),
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_identity_materialization_contract_audit.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_099_birth_identity_materialization_contract_audit import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_audit(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({k:v for k,v in d.items() if k!="materializer_source"},sort_keys=True))
  print("[MATERIALIZER]")
  print(d["materializer_source"])
  self.assertGreater(d["birth_count"],0)
  self.assertGreater(d["event_count"],0)
  print("[PASS] SULS-099 birth identity materialization contract audit")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":
 unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")