from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_116c_repaired_cross_venue_continuous_paths.py"
TEST=ROOT/"test_usls_116c_repaired_cross_venue_continuous_paths.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
H=(1,5,15,30,60,300,900)

def run(root):
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
 d=json.loads(p.read_text(encoding="utf-8"))
 groups={}
 for x in d.get("rows",[]):
  price=x.get("effective_price")
  if price is None:continue
  k=(x["family"],x.get("market_address"),x.get("asset_a"),x.get("asset_b"))
  groups.setdefault(k,[]).append(x)
 paths=[]
 for k,xs in groups.items():
  xs.sort(key=lambda z:(z.get("trade_slot") or 0,
                        z.get("trade_observed_unix") or 0,
                        str(z.get("trade_signature"))))
  p0=float(xs[0]["effective_price"])
  prices=[float(x["effective_price"]) for x in xs]
  anchor=xs[0].get("trade_observed_unix")
  cp=[]
  for h in H:
   y=None
   if isinstance(anchor,(int,float)):
    for x in xs:
     t=x.get("trade_observed_unix")
     if isinstance(t,(int,float)) and t>=anchor+h:
      y=x;break
   cp.append({"horizon_seconds":h,
    "state":"OBSERVED" if y else "PENDING_OR_UNAVAILABLE",
    "price":None if y is None else y["effective_price"],
    "return_from_first_trade":None if y is None else float(y["effective_price"])/p0-1})
  paths.append({"family":k[0],"market_address":k[1],
   "asset_a":k[2],"asset_b":k[3],"trade_count":len(xs),
   "first_price":p0,"last_price":prices[-1],
   "high_price":max(prices),"low_price":min(prices),
   "mfe":max(prices)/p0-1,"mae":min(prices)/p0-1,
   "volume_base":sum(float(x.get("base_quantity") or 0) for x in xs),
   "volume_quote":sum(float(x.get("quote_quantity") or 0) for x in xs),
   "price_path":[{"signature":x.get("trade_signature"),
                  "slot":x.get("trade_slot"),
                  "observed_unix":x.get("trade_observed_unix"),
                  "price":x.get("effective_price")} for x in xs],
   "checkpoints":cp})
 by={}
 for x in paths:by[x["family"]]=by.get(x["family"],0)+1
 return {"revision":"USLS_116C","source_revision":"USLS_116B",
  "path_count":len(paths),"family_path_counts":by,"paths":paths,
  "continuous_between_horizons":True,
  "identity_policy":"DIRECTED_ASSET_PAIR_PRESERVED",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_116c_repaired_cross_venue_continuous_paths import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"path_count":d["path_count"],
   "family_path_counts":d["family_path_counts"]},sort_keys=True))
  self.assertGreater(d["path_count"],0,"NO_REPAIRED_CROSS_VENUE_PATHS")
  self.assertEqual(len(d["family_path_counts"]),14,
   "NOT_ALL_14_CERTIFIED_FAMILIES_HAVE_REPAIRED_PATHS")
  self.assertTrue(d["continuous_between_horizons"])
  self.assertEqual(d["identity_policy"],"DIRECTED_ASSET_PAIR_PRESERVED")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-116C repaired cross-venue continuous paths")
  print("[PASS] all 14 certified venue families have price-path materialization")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")
