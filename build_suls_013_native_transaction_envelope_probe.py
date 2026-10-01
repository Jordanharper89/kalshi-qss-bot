from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_013_native_transaction_envelope_probe.py"
TEST=ROOT/"test_suls_013_native_transaction_envelope_probe.py"

MOD_TEXT=r"""from __future__ import annotations
import json,inspect
from pathlib import Path
from qseries_v2.oracle_adapters.independent import oad_319_solana_transaction_canonical_envelope as env

def audit():
 fn=env.canonical_transaction_envelopes
 sig=str(inspect.signature(fn))
 src=inspect.getsource(fn)
 return {"revision":"SULS_013","signature":sig,"source_excerpt":src[:5000],
  "execution_authority":False,"read_only":True}

def write(root):
 d=audit();p=root/"runtime_state/solana_opportunities/launch_surveillance/native_transaction_envelope_probe.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_013_native_transaction_envelope_probe import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_probe(self):
  p,d=write(ROOT)
  print("[SIGNATURE]",d["signature"]);print("[SOURCE_EXCERPT]");print(d["source_excerpt"])
  if "transaction" not in d["source_excerpt"].lower():self.fail("NO_TRANSACTION_ENVELOPE_LOGIC_VISIBLE")
  print("[PASS] SULS-013 native transaction envelope probe")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-013 NATIVE TRANSACTION ENVELOPE PROBE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
