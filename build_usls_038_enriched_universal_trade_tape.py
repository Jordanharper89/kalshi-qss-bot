from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_038_enriched_universal_trade_tape.py"
TEST=ROOT/"test_usls_038_enriched_universal_trade_tape.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def enrich(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_trade_tape"
 tape=json.loads((base/"pump_normalized_trade_tape.json").read_text(encoding="utf-8"))
 part=json.loads((base/"pump_trade_participants_amounts.json").read_text(encoding="utf-8"))
 quote=json.loads((base/"pump_quote_amount_evidence.json").read_text(encoding="utf-8"))
 pb={x["trade_id"]:x for x in part["rows"]};qb={x["trade_id"]:x for x in quote["rows"]}
 rows=[]
 for x in tape["rows"]:
  p=pb.get(x["trade_id"],{});q=qb.get(x["trade_id"],{})
  y=dict(x);y["trader"]=p.get("trader");y["base_amount"]=p.get("base_amount")
  y["quote_amount"]=q.get("quote_amount")
  y["effective_price"]=(y["quote_amount"]/y["base_amount"]) if y["quote_amount"] and y["base_amount"] else None
  y["decoder_state"]=("FULL_TRADE_AMOUNTS_EXACT" if y["effective_price"] is not None else
   "SIDE_TRADER_BASE_EXACT_QUOTE_PENDING" if y["trader"] and y["base_amount"] else
   "SIDE_EXACT_PARTICIPANT_OR_AMOUNT_PENDING")
  y["source_lineage"]={**(y.get("source_lineage") or {}),
   "participant_amount_revision":"USLS_036","quote_evidence_revision":"USLS_037"}
  rows.append(y)
 return {"revision":"USLS_038","row_count":len(rows),
  "trader_base_exact_count":sum(1 for x in rows if x["trader"] and x["base_amount"]),
  "full_amount_exact_count":sum(1 for x in rows if x["effective_price"] is not None),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=enrich(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pump_enriched_trade_tape.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_038_enriched_universal_trade_tape import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_enrich(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"row_count":d["row_count"],"trader_base_exact_count":d["trader_base_exact_count"],
   "full_amount_exact_count":d["full_amount_exact_count"],"profitability_claimed":d["profitability_claimed"]},sort_keys=True))
  for x in d["rows"][:40]:
   print("[ENRICHED]",json.dumps({"trade_id":x["trade_id"],"side":x["side"],"trader":x["trader"],
    "base_amount":x["base_amount"],"quote_amount":x["quote_amount"],
    "effective_price":x["effective_price"],"decoder_state":x["decoder_state"]},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertGreater(d["trader_base_exact_count"],0)
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-038 enriched universal trade tape")
  print("[PASS] exact trader/base evidence added without fabricating native-SOL quote amount")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
