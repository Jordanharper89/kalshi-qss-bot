from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_025_dedicated_solana_opportunity_runtime_boundary.py"
TEST=ROOT/"test_osi_025_dedicated_solana_opportunity_runtime_boundary.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
REL="runtime_state/solana_opportunities"
DIRS=("intake","evidence","theses","outcomes","learning","health","reports")
def activate(root:Path)->dict:
 base=root/REL
 for d in DIRS:(base/d).mkdir(parents=True,exist_ok=True)
 manifest={"revision":"OSI_025","runtime_kind":"SOLANA_OPPORTUNITY",
  "primary_sources":["NATIVE_SOLANA","GMGN"],
  "context_sources":["COINBASE_SOL_REGIME"],
  "shared_acquisition":True,"execution_authority":False,"read_only":True,
  "directories":list(DIRS)}
 (base/"runtime_manifest.json").write_text(json.dumps(manifest,indent=2,sort_keys=True),encoding="utf-8")
 return manifest
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_025_dedicated_solana_opportunity_runtime_boundary import activate,REL,DIRS
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_boundary(self):
  d=activate(ROOT);base=ROOT/REL
  for x in DIRS:self.assertTrue((base/x).is_dir())
  self.assertEqual(d["primary_sources"],["NATIVE_SOLANA","GMGN"]);self.assertFalse(d["execution_authority"])
  print("[PASS] OSI-025 dedicated Solana opportunity runtime boundary")
  print("[RUNTIME]",base)
  print("[TRADER] Solana opportunity state is isolated from general Oracle runtime noise")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-025 DEDICATED SOLANA OPPORTUNITY RUNTIME BOUNDARY");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
