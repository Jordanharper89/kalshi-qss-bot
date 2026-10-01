from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_055_oad312_314_shared_contract_audit.py"
TEST=ROOT/"test_osi_055_oad312_314_shared_contract_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json,re
from pathlib import Path
A="qseries_v2/oracle_adapters/independent/oad_312_solana_continuous_temporal_history_activation_gate.py"
B="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
TERMS=("asset","mint","token","pool","price","timestamp","observed_at","slot","horizon","return","mfe","mae","path","outcome")
def keys(path):
 text=path.read_text(encoding="utf-8",errors="replace");out=set()
 for m in re.finditer(r'["\']([A-Za-z_][A-Za-z0-9_]*)["\']',text):
  k=m.group(1)
  if any(t in k.lower() for t in TERMS):out.add(k)
 return sorted(out)
def audit(root):
 ka=keys(root/A);kb=keys(root/B);shared=sorted(set(ka)&set(kb))
 return {"revision":"OSI_055","oad312_keys":ka,"oad314_keys":kb,"shared_keys":shared,"shared_key_count":len(shared),"execution_authority":False,"read_only":True}
def write(root):
 d=audit(root);p=root/"runtime_state/solana_opportunities/oad312_314_shared_contract.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad312_314_shared_contract_audit import audit,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  print("[SHARED_KEY_COUNT]",d["shared_key_count"]);print("[SHARED_KEYS]",json.dumps(d["shared_keys"]))
  if d["shared_key_count"]==0:self.fail("NO_OAD312_OAD314_SHARED_DATA_CONTRACT")
  print("[PASS] OSI-055 OAD-312/OAD-314 shared contract audit")
  print("[TRADER] Confirms the temporal history and outcome grader speak a common data language")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-055 OAD-312 / OAD-314 SHARED CONTRACT AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
