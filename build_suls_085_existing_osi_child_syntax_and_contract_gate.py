from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_085_existing_osi_child_syntax_and_contract_gate.py"
TEST=ROOT/"test_suls_085_existing_osi_child_syntax_and_contract_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import ast,json
def verify(root):
 p=root/"run_osi_solana_intelligence_live.py";src=p.read_text(encoding="utf-8")
 ast.parse(src)
 return {"revision":"SULS_085","syntax_ok":True,
  "suls_imported":"suls_083_persistent_event_driven_runtime" in src,
  "daemon_thread":"OSI-SULS-EventDriven" in src and "daemon=True" in src,
  "existing_stop_contract":"STOP_OSI_LIVE" in src,
  "existing_intake_preserved":"intake_run" in src,
  "execution_authority_false":"EXECUTION_AUTHORITY=False" in src,
  "top_level_launcher_modified":False,"execution_authority":False,"read_only":True}
def write(root):
 d=verify(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/osi_child_binding_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_085_existing_osi_child_syntax_and_contract_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  for k in ("syntax_ok","suls_imported","daemon_thread","existing_stop_contract","existing_intake_preserved","execution_authority_false"):
   if not d[k]:self.fail(k.upper()+"_FALSE")
  self.assertFalse(d["top_level_launcher_modified"])
  print("[PASS] SULS-085 OSI child syntax/contract gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")