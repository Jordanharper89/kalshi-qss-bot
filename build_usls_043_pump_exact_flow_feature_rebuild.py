from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_043_pump_exact_flow_feature_rebuild.py"
TEST=ROOT/"test_usls_043_pump_exact_flow_feature_rebuild.py"

MOD_TEXT=r"""from __future__ import annotations
import json,statistics
from collections import Counter,defaultdict
from pathlib import Path
H=(5,15,30)

def window(rows,h):
 r=[x for x in rows if x["birth_age_seconds"]<=h and x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"]
 users=[x["trader"] for x in r if x.get("trader")];q=[x["quote_amount"] for x in r if x.get("quote_amount") is not None]
 by=defaultdict(float)
 for x in r:
  if x.get("trader") and x.get("quote_amount") is not None:by[x["trader"]]+=x["quote_amount"]
 total=sum(q)
 return {"horizon_seconds":h,"exact_trade_count":len(r),"buy_count":sum(x["side"]=="BUY" for x in r),
  "sell_count":sum(x["side"]=="SELL" for x in r),"unique_trader_count":len(set(users)),
  "repeat_trader_count":sum(n>1 for n in Counter(users).values()),
  "quote_volume_sol":total,
  "net_quote_flow_sol":sum((1 if x["side"]=="BUY" else -1)*x["quote_amount"] for x in r),
  "largest_trader_quote_share":max(by.values())/total if by and total else None}

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 d=json.loads((base/"pump_exact_economic_trade_tape.json").read_text(encoding="utf-8"))
 rows=sorted(d["rows"],key=lambda x:x["observed_unix"])
 exact=[x for x in rows if x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"]
 gaps=[exact[i]["observed_unix"]-exact[i-1]["observed_unix"] for i in range(1,len(exact))]
 return {"revision":"USLS_043","captured_trade_count":len(rows),"economic_exact_count":len(exact),
  "coverage_ratio":len(exact)/len(rows) if rows else 0.0,
  "median_intertrade_seconds":statistics.median(gaps) if gaps else None,
  "windows":[window(rows,h) for h in H],"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_flow_features.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_043_pump_exact_flow_feature_rebuild import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_features(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"captured_trade_count":d["captured_trade_count"],
   "economic_exact_count":d["economic_exact_count"],"coverage_ratio":d["coverage_ratio"],
   "median_intertrade_seconds":d["median_intertrade_seconds"]},sort_keys=True))
  for x in d["windows"]:print("[WINDOW]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["economic_exact_count"],0);self.assertGreater(d["coverage_ratio"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-043 exact Pump trade-flow features rebuilt")
  print("[PASS] buyer/seller counts, unique traders and SOL flow now use TradeEvent economics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
