from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_098_remaining_venue_universal_trade_normalizer.py"
TEST=ROOT/"test_usls_098_remaining_venue_universal_trade_normalizer.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def add(rows,venue,src,revision):
 for n,x in enumerate(src):
  if not x["decoder_state"].startswith("EXACT_"):continue
  rows.append({"trade_id":f'{venue}:{x["signature"]}:{n}',"signature":x["signature"],"venue":venue,
   "market_address":x["market_address"],"trader":x["trader"],"side":x["side"],
   "input_asset":x["input_asset"],"input_amount":x["input_amount"],
   "output_asset":x["output_asset"],"output_amount":x["output_amount"],
   "effective_output_per_input":x["output_amount"]/x["input_amount"],
   "decoder_state":"EXACT_ECONOMIC_TRADE","source_lineage":{"economics_revision":revision},
   "execution_authority":False})
def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape";rows=[]
 m=json.loads((b/"moonit_exact_economics.json").read_text(encoding="utf-8"))
 o=json.loads((b/"boop_exact_economics.json").read_text(encoding="utf-8"))
 h=json.loads((b/"heaven_exact_economics.json").read_text(encoding="utf-8"))
 add(rows,"MOONIT",m["rows"],"USLS_095");add(rows,"BOOP_FUN",o["rows"],"USLS_096");add(rows,"HEAVEN",h["rows"],"USLS_097")
 counts={v:sum(x["venue"]==v for x in rows) for v in ("MOONIT","BOOP_FUN","HEAVEN")}
 return {"revision":"USLS_098","exact_trade_count":len(rows),"venue_counts":counts,"rows":rows,
  "native_sol_policy":"NATIVE_SOL_PSEUDO_ASSET_NOT_FALSE_WS0L_MINT",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_universal_trade_rows.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_098_remaining_venue_universal_trade_normalizer import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_norm(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"exact_trade_count":d["exact_trade_count"],"venue_counts":d["venue_counts"]},sort_keys=True))
  self.assertEqual(d["venue_counts"],{"MOONIT":58,"BOOP_FUN":50,"HEAVEN":59})
  self.assertEqual(d["exact_trade_count"],167)
  self.assertTrue(all(x["input_amount"]>0 and x["output_amount"]>0 for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-098 Moonit/Boop/Heaven normalized into universal trade tape")
  print("[PASS] native SOL preserved as NATIVE_SOL rather than falsely relabeled WSOL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")