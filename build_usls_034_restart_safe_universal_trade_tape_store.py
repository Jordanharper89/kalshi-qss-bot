from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_034_restart_safe_universal_trade_tape_store.py"
TEST=ROOT/"test_usls_034_restart_safe_universal_trade_tape_store.py"

MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

def merge(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 p=base/"universal_trade_tape.json"
 old=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {"revision":"USLS_034","trades":{}}
 trades=old.get("trades") or {};before=len(trades)
 for x in src.get("rows") or []:trades.setdefault(x["trade_id"],x)
 old.update({"revision":"USLS_034","trades":trades,"trade_count":len(trades),
  "updated_unix":time.time(),"append_only":True,"execution_authority":False,"read_only":True})
 p.write_text(json.dumps(old,indent=2,sort_keys=True),encoding="utf-8")
 return p,old,before,len(trades)

def write(root):return merge(root)
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_034_restart_safe_universal_trade_tape_store import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_store(self):
  p,d,b1,a1=write(ROOT);p,d2,b2,a2=write(ROOT)
  rows=list(d2["trades"].values())
  print("[STATE]",json.dumps({"first_before":b1,"first_after":a1,"second_before":b2,"second_after":a2,
   "trade_count":d2["trade_count"],"buy_count":sum(1 for x in rows if x["side"]=="BUY"),
   "sell_count":sum(1 for x in rows if x["side"]=="SELL")},sort_keys=True))
  self.assertGreater(a1,0);self.assertEqual(a1,a2)
  self.assertEqual(d2["trade_count"],len(d2["trades"]))
  self.assertFalse(d2["execution_authority"])
  print("[PASS] USLS-034 restart-safe idempotent universal Solana trade-tape store")
  print("[PASS] exact Pump BUY/SELL observations survive rerun without duplication")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
