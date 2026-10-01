from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_034_birth_age_zero_economic_snapshot.py"
TEST=ROOT/"test_suls_034_birth_age_zero_economic_snapshot.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from decimal import Decimal
def dec(x):
 try:return Decimal(str(x))
 except Exception:return None
def run(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/canonical_tradeable_native_birth_events.json"
 d=json.loads(p.read_text(encoding="utf-8"));out=[]
 for e in d.get("events",[]):
  ta=dec(e.get("initial_token_amount"));qa=dec(e.get("initial_quote_amount"))
  qpt=(qa/ta) if ta and qa and ta!=0 else None
  out.append({**e,"age_seconds":0,"initial_quote_per_token":None if qpt is None else str(qpt),
   "usd_price":None,"usd_liquidity":None,
   "pricing_scope":"NATIVE_QUOTE_RESERVES_ONLY_NO_EXTERNAL_USD_CONTEXT"})
 return {"revision":"SULS_034","snapshot_count":len(out),"snapshots":out,"execution_authority":False,"read_only":True}
def write(root):
 d=run(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/birth_age_zero_economic_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_034_birth_age_zero_economic_snapshot import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_snapshot(self):
  p,d=write(ROOT);print("[SNAPSHOT_COUNT]",d["snapshot_count"])
  for x in d["snapshots"]:print("[AGE_ZERO]",json.dumps(x,sort_keys=True))
  if d["snapshot_count"]==0:self.fail("NO_AGE_ZERO_SNAPSHOT")
  if not any(x.get("initial_quote_per_token") for x in d["snapshots"]):self.fail("NO_NATIVE_INITIAL_PRICE_RATIO")
  print("[PASS] SULS-034 birth age-zero economic snapshot")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")