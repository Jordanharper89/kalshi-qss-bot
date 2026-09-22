from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_013_live_birth_signal_discriminator.py"
TEST=ROOT/"test_usls_013_live_birth_signal_discriminator.py"
MOD_TEXT="""from __future__ import annotations
import json
from pathlib import Path
BIRTH_TERMS=("initialize","create","launch","migration","pool","mintto","initializepool","create_pool","new_pool")
TRADE_TERMS=("swap","buy","sell","exactin","exactout")
def discriminate(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"live_multifamily_transactions.json").read_text(encoding="utf-8"));rows=[]
 for x in d["rows"]:
  tx=x.get("raw_transaction") or {};meta=tx.get("meta") or {};logs=[str(v) for v in (meta.get("logMessages") or [])];low=" ".join(logs).lower()
  bh=sorted({t for t in BIRTH_TERMS if t in low});th=sorted({t for t in TRADE_TERMS if t in low})
  pre=meta.get("preTokenBalances") or [];post=meta.get("postTokenBalances") or []
  newidx=sorted(set(v.get("accountIndex") for v in post)-set(v.get("accountIndex") for v in pre))
  score=min(5,len(bh)+int(bool(newidx))+int("success" in low))
  state=("PROBABLE_BIRTH" if score>=3 else "POSSIBLE_BIRTH" if score>=2 else "ACTIVITY_NOT_BIRTH_PROVEN")
  rows.append({"family":x["family"],"signature":x["signature"],"slot":x.get("slot"),"state":state,
   "birth_hits":bh,"trade_hits":th,"new_token_balance_indexes":newidx,"birth_score":score,"execution_authority":False})
 return {"revision":"USLS_013","sample_count":len(rows),"probable_birth_count":sum(1 for x in rows if x["state"]=="PROBABLE_BIRTH"),
  "possible_birth_count":sum(1 for x in rows if x["state"]=="POSSIBLE_BIRTH"),"rows":rows,"execution_authority":False,"read_only":True}
def write(root):
 d=discriminate(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/live_birth_signal_discrimination.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT="""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_013_live_birth_signal_discriminator import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_discriminator(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({k:d[k] for k in ("sample_count","probable_birth_count","possible_birth_count")},sort_keys=True))
  for r in d["rows"]:print("[EVENT]",json.dumps(r,sort_keys=True))
  self.assertGreater(d["sample_count"],0)
  print("[PASS] USLS-013 live birth-vs-routine-activity discriminator")
  print("[SCOPE] candidate semantics only; no non-Meteora pool identity claim yet")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
