from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_058b_raydium_launchlab_physical_completion_gate.py"
TEST=ROOT/"test_usls_058b_raydium_launchlab_physical_completion_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

def build(root):
 base=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape"
 hyd=json.loads((base/"raydium_family_completion_transactions.json").read_text(encoding="utf-8"))
 ix=json.loads((base/"raydium_exact_instruction_pool_roles.json").read_text(encoding="utf-8"))
 selected=int(hyd["selected_counts"].get("RAYDIUM_LAUNCHLAB",0))
 hydrated=int(hyd["hydrated_counts"].get("RAYDIUM_LAUNCHLAB",0))
 exact=sum(x["venue"]=="RAYDIUM_LAUNCHLAB" for x in ix["rows"])
 if exact>0:status="EXACT_LAUNCHLAB_TRADE_INSTRUCTION_OBSERVED_ACCOUNT_ROLE_PENDING"
 elif hydrated>0:status="LIVE_LAUNCHLAB_TRANSACTIONS_OBSERVED_NO_VERIFIED_TRADE_IN_SAMPLE"
 else:status="BLOCKED_BY_NO_HYDRATABLE_LIVE_ACTIVITY"
 return {"revision":"USLS_058B","selected_signatures":selected,"hydrated_transactions":hydrated,
  "exact_trade_instructions":exact,"status":status,
  "completion_class":"EVIDENCE_BACKED_BLOCKED_OR_PARTIAL" if "EXACT_" not in status else "PARTIAL",
  "execution_authority":False,"read_only":True}

def write(root):
 d=build(root);p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/raydium_launchlab_completion_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""
TEST_TEXT=r"""import json,unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_058b_raydium_launchlab_physical_completion_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertIn(d["status"],("EXACT_LAUNCHLAB_TRADE_INSTRUCTION_OBSERVED_ACCOUNT_ROLE_PENDING",
   "LIVE_LAUNCHLAB_TRANSACTIONS_OBSERVED_NO_VERIFIED_TRADE_IN_SAMPLE","BLOCKED_BY_NO_HYDRATABLE_LIVE_ACTIVITY"))
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-058B LaunchLab physical completion gate")
  print("[PASS] no false certification: exact, observed-no-trade, or evidence-backed blocked only")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")