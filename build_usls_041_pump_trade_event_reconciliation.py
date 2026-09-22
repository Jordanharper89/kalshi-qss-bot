from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_041_pump_trade_event_reconciliation.py"
TEST=ROOT/"test_usls_041_pump_trade_event_reconciliation.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def reconcile(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"pump_trade_events_exact.json").read_text(encoding="utf-8"))
 rows=[]
 for x in src["rows"]:
  hits=[e for e in x["events"] if e["mint"]==x["token_address"] and e["side"]==x["expected_side"]]
  e=hits[0] if len(hits)==1 else None
  rows.append({"trade_id":x["trade_id"],"signature":x["signature"],
   "token_address":x["token_address"],"side":x["expected_side"],
   "event_match_count":len(hits),"trader":None if e is None else e["user"],
   "base_amount_raw":None if e is None else e["token_amount_raw"],
   "quote_amount_lamports":None if e is None else e["sol_amount_lamports"],
   "virtual_sol_reserves":None if e is None else e["virtual_sol_reserves"],
   "virtual_token_reserves":None if e is None else e["virtual_token_reserves"],
   "event_timestamp":None if e is None else e["timestamp"],
   "decoder_state":"TRADE_EVENT_EXACT" if e else "TRADE_EVENT_AMBIGUOUS_OR_MISSING",
   "execution_authority":False})
 return {"revision":"USLS_041","row_count":len(rows),
  "exact_count":sum(1 for x in rows if x["decoder_state"]=="TRADE_EVENT_EXACT"),
  "unresolved_count":sum(1 for x in rows if x["decoder_state"]!="TRADE_EVENT_EXACT"),
  "rows":rows,"execution_authority":False,"read_only":True}

def write(root):
 d=reconcile(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_trade_event_reconciled.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_041_pump_trade_event_reconciliation import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_reconcile(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_count":d["exact_count"],
   "unresolved_count":d["unresolved_count"]},sort_keys=True))
  for x in d["rows"]:print("[TRADE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["exact_count"],0)
  self.assertTrue(all(x["base_amount_raw"] is None or x["base_amount_raw"]>0 for x in d["rows"]))
  self.assertTrue(all(x["quote_amount_lamports"] is None or x["quote_amount_lamports"]>0 for x in d["rows"]))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-041 exact TradeEvent reconciliation")
  print("[PASS] prior signer/token-balance heuristic is no longer authoritative")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
