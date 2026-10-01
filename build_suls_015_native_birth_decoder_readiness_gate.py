from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_015_native_birth_decoder_readiness_gate.py"
TEST=ROOT/"test_suls_015_native_birth_decoder_readiness_gate.py"

MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
def gate(root):
 base=root/"runtime_state/solana_opportunities/launch_surveillance"
 a=json.loads((base/"native_pool_birth_activation.json").read_text(encoding="utf-8"))
 b=json.loads((base/"native_block_shape_probe.json").read_text(encoding="utf-8"))
 c=json.loads((base/"native_transaction_envelope_probe.json").read_text(encoding="utf-8"))
 d=json.loads((base/"program_registry_exact_readback.json").read_text(encoding="utf-8"))
 ready=bool(a.get("callable_count",0)>0 and b.get("ok") and d.get("address_count",0)>0)
 return {"revision":"SULS_015","native_acquisition_callable":a.get("callable_count",0)>0,
  "native_block_probe_ok":b.get("ok"),"transaction_envelope_contract_present":bool(c.get("signature")),
  "program_identity_evidence_present":d.get("address_count",0)>0,
  "physical_native_birth_decoder_ready":ready,
  "next_required_boundary":"SULS_016_NATIVE_POOL_BIRTH_EVENT_DECODER" if ready else "SULS_016_NATIVE_FOUNDATION_REPAIR",
  "execution_authority":False,"read_only":True}
def write(root):
 d=gate(root);p=root/"runtime_state/solana_opportunities/launch_surveillance/native_birth_decoder_readiness.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_015_native_birth_decoder_readiness_gate import write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_gate(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps(d,sort_keys=True))
  print("[PASS] SULS-015 native birth decoder readiness gate")
if __name__=="__main__":unittest.main()
"""

def main():
 print("="*116);print(" SULS-015 NATIVE BIRTH DECODER READINESS GATE");print("="*116)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
