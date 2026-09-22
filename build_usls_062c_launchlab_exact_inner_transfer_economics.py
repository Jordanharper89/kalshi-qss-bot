from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_062c_launchlab_exact_inner_transfer_economics.py"
TEST=ROOT/"test_usls_062c_launchlab_exact_inner_transfer_economics.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_060_launchlab_official_trade_contract import roles

def group_index(level):
 try:return int(str(level).split(":",1)[1])
 except Exception:return None

def inner_group(tx,parent_index):
 for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
  if g.get("index")==parent_index:return g.get("instructions") or []
 return []

def amount_ui(info):
 ta=info.get("tokenAmount")
 if isinstance(ta,dict) and ta.get("amount") is not None:
  return int(ta["amount"])/(10**int(ta.get("decimals") or 0))
 if info.get("amount") is not None and info.get("decimals") is not None:
  return int(info["amount"])/(10**int(info["decimals"]))
 return None

def transfers(tx,parent_index):
 out=[]
 for ix in inner_group(tx,parent_index):
  p=ix.get("parsed")
  if not isinstance(p,dict):continue
  typ=p.get("type");info=p.get("info") or {}
  if typ not in ("transfer","transferChecked","transferCheckedWithFee"):continue
  out.append({"type":typ,"source":info.get("source"),"destination":info.get("destination"),
   "mint":info.get("mint"),"amount_ui":amount_ui(info),"raw_info":info})
 return out

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 src=json.loads((base/"launchlab_deep_trade_census.json").read_text(encoding="utf-8"));rows=[]
 for x in src["rows"]:
  r=roles(x["accounts"]);parent=group_index(x["level"]);ts=transfers(x["transaction"],parent)
  q=[t for t in ts if t["source"]==r["user_quote_token"] and t["destination"]==r["quote_vault"] and t["amount_ui"] is not None]
  b=[t for t in ts if t["source"]==r["base_vault"] and t["destination"]==r["user_base_token"] and t["amount_ui"] is not None]
  qa=sum(t["amount_ui"] for t in q);ba=sum(t["amount_ui"] for t in b);exact=qa>0 and ba>0
  rows.append({"signature":x["signature"],"instruction_name":x["instruction_name"],"parent_instruction_index":parent,
   "trader":r["payer"],"pool":r["pool_state"],"base_mint":r["base_token_mint"],"quote_mint":r["quote_token_mint"],
   "user_base_token_account":r["user_base_token"],"user_quote_token_account":r["user_quote_token"],
   "base_vault":r["base_vault"],"quote_vault":r["quote_vault"],"matched_quote_transfers":len(q),
   "matched_base_transfers":len(b),"base_amount":ba if exact else None,"quote_amount":qa if exact else None,
   "effective_price":qa/ba if exact else None,"side":"BUY" if exact else "UNKNOWN_TRADE_TYPE",
   "decoder_state":"EXACT_LAUNCHLAB_BUY_ECONOMICS" if exact else "INNER_TRANSFER_ECONOMICS_UNRESOLVED",
   "transfer_evidence":ts,"execution_authority":False})
 return {"revision":"USLS_062C","row_count":len(rows),
  "exact_economic_count":sum(x["decoder_state"]=="EXACT_LAUNCHLAB_BUY_ECONOMICS" for x in rows),
  "rows":rows,"profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/launchlab_exact_account_economics.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_062c_launchlab_exact_inner_transfer_economics import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_econ(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"row_count":d["row_count"],"exact_economic_count":d["exact_economic_count"]},sort_keys=True))
  for x in d["rows"]:
   print("[ECON]",json.dumps({k:x[k] for k in ("signature","parent_instruction_index","pool","base_mint","quote_mint",
    "matched_quote_transfers","matched_base_transfers","base_amount","quote_amount","effective_price","decoder_state")},sort_keys=True))
  self.assertGreater(d["row_count"],0)
  self.assertEqual(d["exact_economic_count"],d["row_count"],"LAUNCHLAB_INNER_TRANSFER_ECONOMICS_INCOMPLETE")
  self.assertTrue(all(x["effective_price"]>0 and x["side"]=="BUY" for x in d["rows"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-062C LaunchLab exact inner-transfer economics")
  print("[PASS] actual token-program CPI transfers replace failed owner/account-index balance heuristics")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
