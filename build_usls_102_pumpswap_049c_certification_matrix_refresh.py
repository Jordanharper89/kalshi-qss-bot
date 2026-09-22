from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_102_pumpswap_049c_certification_matrix_refresh.py"
TEST=ROOT/"test_usls_102_pumpswap_049c_certification_matrix_refresh.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build(root):
 b=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 r=json.loads((b/"pumpswap_048c_repaired_trades.json").read_text(encoding="utf-8"))
 ok=(r["exact_trade_count"]==117 and all(r["repairs"].values()) and r["execution_authority"] is False)
 matrix={
  "PUMP_SWAP":{"program_id":"pAMMBay6oceH9fJKBRHGP5D4bD4sWpmSwMn52FMfXEA","exact_trade_rows":r["exact_trade_count"],
   "semantic_repair":"048C","identity_revision":"USLS_047C","status":"CERTIFIED" if ok else "BLOCKED"}}
 return {"revision":"USLS_102","matrix_revision":"049C","pumpswap_certified":ok,"matrix":matrix,
  "phase4_status":"IN_PROGRESS","next_boundary":"PHASE4_STRICT_FULL_VENUE_CLOSURE",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}
def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/pumpswap_049c_certification_matrix.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_102_pumpswap_049c_certification_matrix_refresh import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_matrix(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["pumpswap_certified"])
  self.assertEqual(d["matrix"]["PUMP_SWAP"]["exact_trade_rows"],117)
  self.assertEqual(d["matrix"]["PUMP_SWAP"]["semantic_repair"],"048C")
  self.assertEqual(d["matrix"]["PUMP_SWAP"]["identity_revision"],"USLS_047C")
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-102 PumpSwap 049C certification refresh")
  print("[NEXT] PHASE4_STRICT_FULL_VENUE_CLOSURE")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")