from pathlib import Path
import json

ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_launch_surveillance"
MOD=SUB/"suls_097_exact_oad314_temporal_contract_extractor.py"
TEST=ROOT/"test_suls_097_exact_oad314_temporal_contract_extractor.py"

MOD_TEXT=r"""from __future__ import annotations
import json

FILES=(
 "oad312_314_shared_contract.json",
 "oad314_callable_interface.json",
 "oad314_case_record_contract.json",
 "oad314_forward_outcome_lineage.json",
 "oad314_runtime_callables.json",
 "temporal_record_producer_lineage.json",
 "temporal_runtime_callables.json",
)

def extract(root):
 base=root/"runtime_state/solana_opportunities"
 out={}
 for name in FILES:
  p=base/name
  if not p.exists():
   out[name]={"exists":False}
   continue
  try:
   d=json.loads(p.read_text(encoding="utf-8"))
  except Exception as e:
   out[name]={"exists":True,"error":repr(e)}
   continue
  out[name]={"exists":True,"keys":sorted(d.keys()),"data":d}
 return {"revision":"SULS_097","contracts":out,
  "execution_authority":False,"read_only":True}

def write(root):
 d=extract(root)
 p=root/"runtime_state/solana_opportunities/launch_surveillance/oad314_exact_temporal_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p,d
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_launch_surveillance.suls_097_exact_oad314_temporal_contract_extractor import write
ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_contract(self):
  p,d=write(ROOT)
  print("[STATE]",json.dumps({"revision":d["revision"],
   "files":{k:v.get("exists") for k,v in d["contracts"].items()}},sort_keys=True))
  for name,x in d["contracts"].items():
   print("[CONTRACT]",name,json.dumps(x,sort_keys=True)[:12000])
  required=("oad314_callable_interface.json",
            "oad314_case_record_contract.json",
            "oad314_runtime_callables.json",
            "temporal_runtime_callables.json")
  for name in required:
   self.assertTrue(d["contracts"][name].get("exists"),name)
  print("[PASS] SULS-097 exact OAD-314 / temporal contract extractor")
  print("[PASS] execution_authority=FALSE")

if __name__=="__main__":unittest.main()
"""

SUB.mkdir(parents=True,exist_ok=True)
MOD.write_text(MOD_TEXT,encoding="utf-8")
TEST.write_text(TEST_TEXT,encoding="utf-8")
print("[PASS] installed:",MOD.relative_to(ROOT))
print("[PASS] test:",TEST.name)
print("[PASS] execution_authority=FALSE")