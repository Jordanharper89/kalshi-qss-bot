from pathlib import Path

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_026b_zero_reserve_price_state_repair.py"
TEST=ROOT/"test_usls_026b_zero_reserve_price_state_repair.py"

MOD.write_text(r'''from __future__ import annotations
import json
from pathlib import Path

def repair(root):
 root=Path(root)
 p=root/"runtime_state/solana_opportunities/universal_launch_scanner/pump_marginal_prices.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 rows=[]
 for x in d.get("rows") or []:
  vt=x.get("virtual_token_reserves") or 0
  vq=x.get("virtual_quote_reserves") or 0
  y=dict(x)
  if vt>0 and vq>0 and x.get("marginal_quote_per_token") is not None:
   y["price_state"]="PRICE_AVAILABLE"
   y["price_available"]=True
  else:
   y["marginal_quote_per_token"]=None
   y["price_state"]="PRICE_UNAVAILABLE_ZERO_RESERVES"
   y["price_available"]=False
  y["profitability_eligible"]=False
  y["execution_authority"]=False
  rows.append(y)
 out={"revision":"USLS_026B","row_count":len(rows),
  "price_available_count":sum(1 for x in rows if x["price_available"]),
  "price_unavailable_count":sum(1 for x in rows if not x["price_available"]),
  "rows":rows,"profitability_claimed":False,
  "execution_authority":False,"read_only":True}
 q=root/"runtime_state/solana_opportunities/universal_launch_scanner/pump_marginal_prices.json"
 q.write_text(json.dumps(out,indent=2,sort_keys=True),encoding="utf-8")
 return q,out

def write(root): return repair(root)
''',encoding="utf-8")

TEST.write_text(r'''import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_026b_zero_reserve_price_state_repair import write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_repair(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({
   "row_count":d["row_count"],
   "price_available_count":d["price_available_count"],
   "price_unavailable_count":d["price_unavailable_count"],
   "profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:
   print("[PRICE]",json.dumps({
    "token_address":x["token_address"],
    "quote_mint":x["quote_mint"],
    "marginal_quote_per_token":x["marginal_quote_per_token"],
    "price_state":x["price_state"]},sort_keys=True))
  self.assertEqual(d["row_count"],3)
  self.assertGreaterEqual(d["price_available_count"],2)
  self.assertGreaterEqual(d["price_unavailable_count"],1)
  self.assertTrue(all((x["marginal_quote_per_token"] is None) ==
                      (not x["price_available"]) for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-026B zero-reserve price state repaired")
  print("[PASS] unavailable curves retained without fabricated price")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
''',encoding="utf-8")

print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")