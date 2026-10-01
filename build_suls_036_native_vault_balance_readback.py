from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_036_native_vault_balance_readback.py"
TEST=ROOT/"test_suls_036_native_vault_balance_readback.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc

def _bal(account,timeout=20.0):
 r=_rpc("getTokenAccountBalance",[str(account),{"commitment":"finalized"}],timeout)
 v=(r or {}).get("value") or {}
 return {"account":str(account),"amount":v.get("amount"),"decimals":v.get("decimals"),
  "ui_amount":v.get("uiAmount"),"ui_amount_string":v.get("uiAmountString")}

def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));now=time.time();rows=[]
 for e in d.get("events",[]):
  rows.append({"event_id":e["event_id"],"signature":e["signature"],"block_time":e["block_time"],
   "observed_unix":now,"age_seconds":max(0.0,now-float(e["block_time"])),
   "token":_bal(e["token_vault"]),"quote":_bal(e["quote_vault"]),
   "execution_authority":False})
 return {"revision":"SULS_036","snapshot_count":len(rows),"snapshots":rows,
  "execution_authority":False,"read_only":True}

def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_vault_balance_readback.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_036_native_vault_balance_readback import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_readback(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[VAULT_SNAPSHOT]",json.dumps(x,sort_keys=True))
  if not d["snapshots"]:self.fail("NO_NATIVE_VAULT_SNAPSHOT")
  if not all(x["token"].get("amount") is not None and x["quote"].get("amount") is not None for x in d["snapshots"]):
   self.fail("NATIVE_VAULT_BALANCE_MISSING")
  print("[PASS] SULS-036 native vault balance readback")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")