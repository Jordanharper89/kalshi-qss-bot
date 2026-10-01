from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_089_top_level_osi_registration_gate.py"
TEST=ROOT/"test_suls_089_top_level_osi_registration_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 rows=[]
 for name in ("run_oracle_live.py","run_oracle_LIVE.py"):
  p=root/name
  if not p.exists():continue
  s=p.read_text(encoding="utf-8",errors="ignore")
  rows.append({"path":name,"registered":"run_osi_solana_intelligence_live.py" in s,
   "suls_direct_registration":"solana_launch_surveillance" in s})
 return {"revision":"SULS_089","launchers":rows,
  "osi_registered_all":bool(rows) and all(x["registered"] for x in rows),
  "no_direct_suls_registration":bool(rows) and all(not x["suls_direct_registration"] for x in rows),
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/top_level_osi_registration_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_089_top_level_osi_registration_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  self.assertTrue(d["osi_registered_all"]);self.assertTrue(d["no_direct_suls_registration"])
  print("[PASS] SULS-089 top-level OSI registration gate")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*116);print(" SULS-089 TOP-LEVEL OSI REGISTRATION GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()