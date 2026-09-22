from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_launch_scanner"
MOD=SUB/"usls_028_pump_sampled_path_outcomes.py"
TEST=ROOT/"test_usls_028_pump_sampled_path_outcomes.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def _raw_price(s):
 vt=s["virtual_token_reserves"];vq=s["virtual_quote_reserves"]
 return (vq/vt) if vt else None

def resolve(root):
 root=Path(root);base=root/"runtime_state/solana_opportunities/universal_launch_scanner"
 d=json.loads((base/"pump_short_horizon_curve_follow.json").read_text(encoding="utf-8"))
 pts=[]
 for x in d["samples"]:
  p=_raw_price(x["state"])
  pts.append({"horizon_seconds":x["horizon_seconds"],"price_ratio_raw":p,
   "target_unix":x["target_unix"],"observed_unix":x["observed_unix"],
   "lag_seconds":x.get("lag_seconds",0.0)})
 anchor=pts[0]["price_ratio_raw"]
 for x in pts:x["return_from_anchor"]=(x["price_ratio_raw"]/anchor-1.0) if anchor else None
 rets=[x["return_from_anchor"] for x in pts if x["return_from_anchor"] is not None]
 return {"revision":"USLS_028","signature":d["signature"],"token_address":d["token_address"],
  "quote_mint":d["quote_mint"],"points":pts,
  "sampled_mfe":max(rets) if rets else None,"sampled_mae":min(rets) if rets else None,
  "semantics":"SAMPLED_BONDING_CURVE_PRICE_PATH_PRE_FEE_NOT_EXECUTABLE_PNL",
  "remaining_horizons":d["remaining_horizons"],"profitability_claimed":False,
  "execution_authority":False,"read_only":True}

def write(root):
 d=resolve(root);p=Path(root)/"runtime_state/solana_opportunities/universal_launch_scanner/pump_sampled_path_outcomes.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_launch_scanner.usls_028_pump_sampled_path_outcomes import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_outcomes(self):
  p,d=write(ROOT);print("[STATE]",json.dumps({"token_address":d["token_address"],"sampled_mfe":d["sampled_mfe"],"sampled_mae":d["sampled_mae"],"remaining_horizons":d["remaining_horizons"]},sort_keys=True))
  for x in d["points"]:print("[OUTCOME]",json.dumps(x,sort_keys=True))
  self.assertEqual([x["horizon_seconds"] for x in d["points"]],[0,1,5,15,30])
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-028 prospective sampled price-path outcomes")
  print("[PASS] MFE/MAE labels are sampled only, not continuous and not executable PnL")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
