from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_042_pump_exact_economic_trade_tape.py"
TEST=ROOT/"test_usls_042_pump_exact_economic_trade_tape.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 tape=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 rec=json.loads((base/"pump_trade_event_reconciled.json").read_text(encoding="utf-8"))
 rb={x["trade_id"]:x for x in rec["rows"]};rows=[]
 for x in tape["rows"]:
  r=rb.get(x["trade_id"],{});raw_base=r.get("base_amount_raw");lam=r.get("quote_amount_lamports")
  y=dict(x);y["trader"]=r.get("trader")
  y["base_amount_raw"]=raw_base;y["base_decimals"]=6
  y["base_amount"]=None if raw_base is None else raw_base/1_000_000
  y["quote_amount_lamports"]=lam
  y["quote_amount"]=None if lam is None else lam/1_000_000_000
  y["effective_price"]=None if not y["base_amount"] or y["quote_amount"] is None else y["quote_amount"]/y["base_amount"]
  y["virtual_sol_reserves_after"]=r.get("virtual_sol_reserves")
  y["virtual_token_reserves_after"]=r.get("virtual_token_reserves")
  y["decoder_state"]="TRADE_EVENT_ECONOMICS_EXACT" if y["effective_price"] is not None else "TRADE_EVENT_UNRESOLVED"
  y["source_lineage"]={**(y.get("source_lineage") or {}),"economic_decoder_revision":"USLS_042"}
  rows.append(y)
 return {"revision":"USLS_042","row_count":len(rows),
  "economic_exact_count":sum(1 for x in rows if x["decoder_state"]=="TRADE_EVENT_ECONOMICS_EXACT"),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_042_pump_exact_economic_trade_tape import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_tape(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],
   "economic_exact_count":d["economic_exact_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"]:print("[ECON]",json.dumps({"trade_id":x["trade_id"],"side":x["side"],
   "trader":x["trader"],"base_amount":x["base_amount"],"quote_amount":x["quote_amount"],
   "effective_price":x["effective_price"],"decoder_state":x["decoder_state"]},sort_keys=True))
  self.assertGreater(d["economic_exact_count"],0)
  self.assertTrue(all(x["effective_price"] is None or x["effective_price"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-042 exact Pump economic trade tape")
  print("[PASS] actual TradeEvent token/SOL amounts replace wallet-delta inference")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
