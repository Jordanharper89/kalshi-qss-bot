from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_101b_pumpswap_exact_source_shape_diagnostic.py"
TEST=ROOT/"test_usls_101b_pumpswap_exact_source_shape_diagnostic.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from collections import Counter
from pathlib import Path

PROGRAM="pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA"

def rows_of(d):
 if not isinstance(d,dict):return []
 for k in ("rows","trades","events"):
  if isinstance(d.get(k),list):return d[k]
 return []

def pumpswap(x):
 return isinstance(x,dict) and (x.get("venue")=="PUMP_SWAP" or x.get("program_id")==PROGRAM)

def build(root):
 audit=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_source_audit.json"
 a=json.loads(audit.read_text(encoding="utf-8"));out=[]
 for c in a["candidates"]:
  p=Path(root)/c["path"]
  try:d=json.loads(p.read_text(encoding="utf-8"))
  except Exception:continue
  rs=[x for x in rows_of(d) if pumpswap(x)]
  if not rs:continue
  def cnt(k):return dict(Counter(str(x.get(k)) for x in rs).most_common(20))
  out.append({"path":c["path"],"revision":d.get("revision"),"row_count":len(rs),
   "decoder_state":cnt("decoder_state"),"status":cnt("status"),"side":cnt("side"),
   "identity_state":cnt("identity_state"),"economic_state":cnt("economic_state"),
   "exact_flags":{"exact":sum(x.get("exact") is True for x in rs),
    "exact_economics":sum(x.get("exact_economics") is True for x in rs),
    "identity_exact":sum(x.get("identity_exact") is True for x in rs)},
   "sample_keys":sorted(rs[0].keys())})
 return {"revision":"USLS_101B","candidate_count":len(out),"candidates":out,
  "certification_claimed":False,"execution_authority":False}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_exact_source_shape_diagnostic.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_101b_pumpswap_exact_source_shape_diagnostic import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_diag(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"candidate_count":d["candidate_count"]},sort_keys=True))
  for x in d["candidates"]:print("[SOURCE]",json.dumps(x,sort_keys=True))
  self.assertGreater(d["candidate_count"],0)
  self.assertFalse(d["certification_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-101B PumpSwap exact-source shape diagnostic")
  print("[PASS] no semantic certification claimed")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")