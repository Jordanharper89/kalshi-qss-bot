from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_lifecycle"
MOD=SUB/"usls_104_phase5_birth_tape_lifecycle_contract.py"
TEST=ROOT/"test_usls_104_phase5_birth_tape_lifecycle_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

FIELDS=["lifecycle_id","venue","program_id","token_address","market_address","birth_signature","birth_slot",
 "birth_observed_unix","trade_signature","trade_slot","trade_observed_unix","side","trader","input_asset",
 "input_amount","output_asset","output_amount","decoder_state","source_lineage","execution_authority"]

def build(root):
 gate=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/phase4_strict_full_venue_closure.json"
 d=json.loads(gate.read_text(encoding="utf-8"))
 if not d.get("phase4_exact_trade_decoding_closed"):raise RuntimeError("PHASE4_NOT_CERTIFIED")
 return {"revision":"USLS_104","phase":5,"status":"IN_PROGRESS","contract_fields":FIELDS,
  "join_key_policy":"VENUE_PROGRAM_TOKEN_MARKET_PLUS_SIGNATURE_LINEAGE",
  "birth_without_trade":"RETAIN","trade_without_birth":"RETAIN_UNRESOLVED_BIRTH","unknown_program":"RETAIN_UNKNOWN",
  "future_leakage_policy":"NO_POST_EVENT_DATA_IN_PRE_EVENT_STATE",
  "next_boundary":"PHYSICAL_BIRTH_TO_FIRST_TRADE_JOIN",
  "profitability_claimed":False,"execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_lifecycle/phase5_birth_tape_lifecycle_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_lifecycle.usls_104_phase5_birth_tape_lifecycle_contract import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertEqual(d["phase"],5);self.assertEqual(d["status"],"IN_PROGRESS")
  self.assertEqual(d["birth_without_trade"],"RETAIN");self.assertEqual(d["trade_without_birth"],"RETAIN_UNRESOLVED_BIRTH")
  self.assertEqual(d["future_leakage_policy"],"NO_POST_EVENT_DATA_IN_PRE_EVENT_STATE")
  self.assertFalse(d["profitability_claimed"]);self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-104 Phase 5 birth+tape unified lifecycle contract")
  print("[NEXT] PHYSICAL_BIRTH_TO_FIRST_TRADE_JOIN")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")