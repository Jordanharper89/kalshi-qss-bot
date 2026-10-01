from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_025_native_birth_verification_truth_gate.py"
TEST=ROOT/"test_suls_025_native_birth_verification_truth_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
def gate(root):
 p=root/"runtime_state/solana_opportunities/launch_surveillance/physical_exact_native_pool_birth_gate.json"
 d=json.loads(p.read_text(encoding="utf-8"));n=int(d.get("verified_birth_count",0))
 return {"revision":"SULS_025","exact_native_birth_verified":n>0,"verified_birth_count":n,
  "pool_token_account_roles_resolved":False,"canonical_tradeable_birth_event_ready":False,
  "next_required_boundary":"SULS_026_NATIVE_POOL_TOKEN_ACCOUNT_ROLE_RESOLUTION" if n>0 else "SULS_026_NATIVE_BIRTH_VERIFICATION_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_verification_truth_gate.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_025_native_birth_verification_truth_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT);print("[STATE]",json.dumps(d,sort_keys=True))
  if not d["exact_native_birth_verified"]:self.fail("EXACT_NATIVE_BIRTH_NOT_VERIFIED")
  print("[PASS] SULS-025 native birth verification truth gate")
if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")