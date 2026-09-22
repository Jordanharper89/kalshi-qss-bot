from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_006b_verified_mainnet_program_registry_boop_repair.py"
TEST=ROOT/"test_usls_006b_verified_mainnet_program_registry_boop_repair.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time,urllib.request
from pathlib import Path

RPC="https://api.mainnet-beta.solana.com"
PROGRAMS={
 "PUMP_FUN":"6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P",
 "PUMP_SWAP":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA",
 "RAYDIUM_LAUNCHLAB":"LanMV9sAd7wArD4vJFi2qDdfnVhFxYSUg6eADduJ3uj",
 "RAYDIUM_V4":"675kPX9MHTjS2zt1qfr1NYHuzeLXfQM9H24wFSUt1Mp8",
 "RAYDIUM_CLMM":"CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK",
 "RAYDIUM_CPMM":"CPMMoo8L3F4NbTegBCKVNunggL7H1ZpdTHKxQB5qKP1C",
 "METEORA_DBC":"dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN",
 "METEORA_DAMM":"cpamdpZCGKUy5JxQXB4dcpGPiikHawvSWAd6mEn1sGG",
 "METEORA_DLMM":"LBUZKhRxPF3XUpBCjp4YzTKgLccjZhTSDM9YuVaPwxo",
 "METEORA_DYN":"Eo7WjKq67rjJQSZxS6z3YkapzY3eMj6Xy8X5EQVn5UaB",
 "ORCA":"whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc",
 "MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
}

def verify():
 ids=list(PROGRAMS.values())
 body=json.dumps({"jsonrpc":"2.0","id":1,"method":"getMultipleAccounts",
  "params":[ids,{"encoding":"base64","commitment":"confirmed"}]}).encode()
 req=urllib.request.Request(RPC,data=body,headers={"Content-Type":"application/json"})
 last=None
 for _ in range(3):
  try:
   with urllib.request.urlopen(req,timeout=20) as r:
    vals=(json.loads(r.read()).get("result") or {}).get("value") or []
   break
  except Exception as e:
   last=e;time.sleep(1)
 else: raise RuntimeError(f"MAINNET_RPC_FAILED:{last}")
 rows=[]
 for (fam,pid),v in zip(PROGRAMS.items(),vals):
  rows.append({"family":fam,"program_id":pid,"account_exists":v is not None,
   "executable":bool(v and v.get("executable")),"owner":v.get("owner") if v else None})
 return {"revision":"USLS_006B","program_count":len(rows),"programs":rows,
  "verified_executable_count":sum(1 for x in rows if x["executable"]),
  "all_verified":all(x["account_exists"] and x["executable"] for x in rows),
  "execution_authority":False,"read_only":True}

def write(root):
 d=verify()
 p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/verified_mainnet_program_registry.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_006b_verified_mainnet_program_registry_boop_repair import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_verify(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"program_count":d["program_count"],
   "verified_executable_count":d["verified_executable_count"],"all_verified":d["all_verified"]},sort_keys=True))
  for r in d["programs"]: print("[PROGRAM]",json.dumps(r,sort_keys=True))
  self.assertEqual(d["program_count"],14)
  self.assertEqual(d["verified_executable_count"],14)
  self.assertTrue(d["all_verified"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-006B all 14 target mainnet programs physically executable")
  print("[PASS] Boop.fun program ID repaired")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
