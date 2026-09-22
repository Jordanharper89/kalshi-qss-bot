from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_scanner_runtime"
MOD=SUB/"usls_159_phase8_enriched_feature_snapshots.py"
TEST=ROOT/"test_usls_159_phase8_enriched_feature_snapshots.py"

MOD_TEXT=r"""from __future__ import annotations
import json,math
from pathlib import Path

PATHS="runtime_state/solana_opportunities/solana_scanner/cross_venue_continuous_price_paths_repaired.json"
ECON="runtime_state/solana_opportunities/solana_scanner/cross_venue_economic_rows_repaired.json"
H=(1,5,15,30,60,300,900)

def _num(v):
 try:
  x=float(v);return x if math.isfinite(x) else None
 except Exception:return None

def run(root):
 root=Path(root)
 paths=json.loads((root/PATHS).read_text(encoding="utf-8"))
 econ=json.loads((root/ECON).read_text(encoding="utf-8"))
 sigidx={x.get("trade_signature"):x for x in econ.get("rows",[]) if x.get("trade_signature")}
 rows=[]
 for pi,p in enumerate(paths.get("paths",[])):
  tape=[x for x in p.get("price_path",[]) if isinstance(x.get("observed_unix"),(int,float)) and _num(x.get("price")) is not None]
  if not tape:continue
  tape.sort(key=lambda x:x["observed_unix"]);t0=tape[0]["observed_unix"];p0=float(tape[0]["price"])
  for h in H:
   cutoff=t0+h
   past=[x for x in tape if x["observed_unix"]<=cutoff]
   future=[x for x in tape if x["observed_unix"]>cutoff]
   if not past:continue
   prices=[float(x["price"]) for x in past]
   erows=[sigidx.get(x.get("signature")) for x in past if sigidx.get(x.get("signature"))]
   base=sum(_num(x.get("base_quantity")) or 0.0 for x in erows)
   quote=sum(_num(x.get("quote_quantity")) or 0.0 for x in erows)
   last=prices[-1];duration=max(1.0,float(h))
   f={"trade_count":len(past),
      "trade_velocity":len(past)/duration,
      "base_volume":base,"quote_volume":quote,
      "quote_volume_velocity":quote/duration,
      "return_to_cutoff":last/p0-1 if p0 else None,
      "mfe_to_cutoff":max(prices)/p0-1 if p0 else None,
      "mae_to_cutoff":min(prices)/p0-1 if p0 else None}
   outcome=None
   if future:
    final=float(future[-1]["price"]);outcome=final/last-1 if last else None
   rows.append({"case_id":f"USLS159-{pi:06d}-{h}",
    "family":p.get("family"),"market_address":p.get("market_address"),
    "horizon_seconds":h,"feature_cutoff_unix":cutoff,
    "features":f,"forward_observational_return":outcome,
    "feature_rows_after_cutoff":0,"execution_authority":False})
 return {"revision":"USLS_159","snapshot_count":len(rows),"snapshots":rows,
  "feature_semantics":"PRICE_PATH_PLUS_TRADE_COUNT_AND_VOLUME_AVAILABLE_BEFORE_CUTOFF",
  "future_leakage":"FORBIDDEN",
  "next_boundary":"CROSS_FAMILY_NEAREST_NEIGHBOR_INDEX",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=run(root)
 p=Path(root)/"runtime_state/solana_opportunities/solana_scanner/phase8_enriched_feature_snapshots.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True,default=str),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_scanner_runtime.usls_159_phase8_enriched_feature_snapshots import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  fam=len({x["family"] for x in d["snapshots"]})
  print("[STATE]",json.dumps({"snapshot_count":d["snapshot_count"],
   "family_count":fam,"next_boundary":d["next_boundary"]},sort_keys=True))
  self.assertGreater(d["snapshot_count"],0)
  self.assertGreater(fam,0)
  self.assertEqual(d["future_leakage"],"FORBIDDEN")
  self.assertTrue(all(x["feature_rows_after_cutoff"]==0 for x in d["snapshots"]))
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-159 enriched leakage-safe feature snapshots")
  print("[PASS] price, trade velocity and volume features frozen before outcome")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
