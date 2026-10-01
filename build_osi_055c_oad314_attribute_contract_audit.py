from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_055_oad314_case_record_contract_audit.py"
TEST=ROOT/"test_osi_055c_oad314_attribute_contract_audit.py"

MOD_TEXT=r"""from __future__ import annotations
import ast,json
from pathlib import Path

TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
FUNCS=("attribute_forward_outcomes","_price_for_pair")

def _attrs(fn,text):
 out=[]
 for n in ast.walk(fn):
  if isinstance(n,ast.Attribute) and isinstance(n.value,ast.Name):
   out.append({"owner":n.value.id,"attribute":n.attr,"line":n.lineno})
 return out

def _dict_keys(fn,text):
 out=[]
 for n in ast.walk(fn):
  if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=="get" and n.args:
   k=n.args[0]
   if isinstance(k,ast.Constant) and isinstance(k.value,str):
    out.append({"owner":ast.get_source_segment(text,n.func.value) or "?","key":k.value,"line":n.lineno})
  elif isinstance(n,ast.Subscript):
   k=n.slice
   if isinstance(k,ast.Constant) and isinstance(k.value,str):
    out.append({"owner":ast.get_source_segment(text,n.value) or "?","key":k.value,"line":n.lineno})
 return out

def audit(root:Path)->dict:
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing OAD-314")
 text=p.read_text(encoding="utf-8",errors="replace");tree=ast.parse(text)
 found={}
 for n in ast.walk(tree):
  if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in FUNCS:
   found[n.name]={
    "args":[a.arg for a in n.args.args],
    "attributes":_attrs(n,text),
    "dict_keys":_dict_keys(n,text),
    "source":ast.get_source_segment(text,n)[:5000],
   }
 if "attribute_forward_outcomes" not in found or "_price_for_pair" not in found:
  raise RuntimeError("Required OAD-314 functions missing")
 return {"revision":"OSI_055C","module":TARGET,"functions":found,
  "execution_authority":False,"read_only":True}

def write(root:Path)->Path:
 d=audit(root)
 p=root/"runtime_state/solana_opportunities/oad314_case_record_contract.json"
 p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8")
 return p
"""

TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_055_oad314_case_record_contract_audit import audit,write

ROOT=Path(__file__).resolve().parent

class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write(ROOT)
  self.assertFalse(d["execution_authority"])
  a=d["functions"]["attribute_forward_outcomes"]
  price=d["functions"]["_price_for_pair"]
  case_attrs=sorted({x["attribute"] for x in a["attributes"] if x["owner"]=="c"})
  record_attrs=sorted({x["attribute"] for x in a["attributes"] if x["owner"]=="r"})
  price_record_attrs=sorted({x["attribute"] for x in price["attributes"] if x["owner"]=="record"})
  print("[CASE_ATTRIBUTES]",json.dumps(case_attrs))
  print("[RECORD_ATTRIBUTES]",json.dumps(record_attrs))
  print("[PRICE_RECORD_ATTRIBUTES]",json.dumps(price_record_attrs))
  print("[PRICE_DICT_KEYS]",json.dumps(price["dict_keys"],sort_keys=True))
  required={"snapshot_at","horizon_seconds","evidence_observation_ids","pair_address","experience_id","token_address"}
  self.assertTrue(required.issubset(set(case_attrs)),msg="MISSING_EXPECTED_CASE_ATTRIBUTES")
  self.assertIn("observed_at",record_attrs)
  self.assertIn("observation_id",record_attrs)
  print("[PASS] OSI-055C OAD-314 attribute-aware case/record contract audit")
  print("[TRADER] Exact object contract for future-outcome attribution is now explicit")
  print("[SCOPE] Read-only audit; no guessed dictionary contract")

if __name__=="__main__":
 unittest.main()
"""

def main():
 print("="*116)
 print(" OSI-055C OAD-314 ATTRIBUTE-AWARE CASE / RECORD CONTRACT AUDIT")
 print("="*116)
 SUB.mkdir(parents=True,exist_ok=True)
 MOD.write_text(MOD_TEXT,encoding="utf-8")
 TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] replaced:",MOD.relative_to(ROOT))
 print("[PASS] test:",TEST.name)
 print("[PASS] execution_authority=FALSE")
 print("[SCOPE] Replacement for OSI-055B dictionary-only contract audit")

if __name__=="__main__":
 main()
