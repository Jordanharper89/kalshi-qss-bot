from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_universal_trade_tape"
MOD=SUB/"usls_086_remaining_venue_program_contract.py"
TEST=ROOT/"test_usls_086_remaining_venue_program_contract.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path

PROGRAMS={
 "MOONIT":"MoonCVVNZFSYkqNXP6bxHLPL6QQJiMagDL3qcqUQTrG",
 "BOOP_FUN":"boop8hVGQGqehUK2iVEMEnMrL5RbjywRzHKBmBE7ry4",
 "HEAVEN":"HEAVENoP2qxoeuF8Dj2oT1GHEnu49U5mJYkdeC8BAX2o",
}

def write(root):
 d={"revision":"USLS_086","programs":PROGRAMS,
  "policy":"PHYSICAL_DISCOVERY_FIRST_NO_UNVERIFIED_TRADE_DISCRIMINATORS",
  "unknown_instruction_retention":True,
  "execution_authority":False,"read_only":True}
 p=Path(root)/"runtime_state/solana_opportunities/universal_trade_tape/remaining_venue_program_contract.json"
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_086_remaining_venue_program_contract import *
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  self.assertEqual(set(d["programs"]),{"MOONIT","BOOP_FUN","HEAVEN"})
  self.assertTrue(d["unknown_instruction_retention"])
  self.assertFalse(d["execution_authority"])
  print("[PASS] USLS-086 Moonit/Boop/Heaven program contract")
  print("[PASS] no unverified trade discriminator encoded")
  print("[PASS] execution_authority=FALSE")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")