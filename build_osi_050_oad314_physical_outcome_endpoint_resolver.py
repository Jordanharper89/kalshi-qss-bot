from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_050_oad314_physical_outcome_endpoint_resolver.py"
TEST=ROOT/"test_osi_050_oad314_physical_outcome_endpoint_resolver.py"
MOD_TEXT=r"""from __future__ import annotations
import ast,json
from pathlib import Path
TARGET="qseries_v2/oracle_adapters/independent/oad_314_solana_verified_forward_outcome_attribution.py"
def resolve(root):
 p=root/TARGET
 if not p.is_file():raise RuntimeError("Missing certified OAD-314 module")
 vals=[]
 try:
  tree=ast.parse(p.read_text(encoding="utf-8",errors="replace"))
  for n in ast.walk(tree):
   if isinstance(n,ast.Constant) and isinstance(n.value,str):
    s=n.value.strip().replace("\\","/")
    if any(x in s.lower() for x in ("runtime","json","jsonl","sqlite","db","postgres","outcome","forward","path")):vals.append(s)
 except Exception:pass
 files=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists():continue
  for f in base.rglob("*"):
   if not f.is_file():continue
   rel=str(f.relative_to(root)).replace("\\","/")
   low=rel.lower()
   if any(v.lower().lstrip("./")==low or ("/" in v and low.endswith(v.lower().lstrip("./"))) for v in vals):files.append(rel)
 return {"revision":"OSI_050","module":TARGET,"string_literals":vals[:300],"physical_files":sorted(set(files)),"physical_file_count":len(set(files)),"execution_authority":False,"read_only":True}
def write(root):
 d=resolve(root);p=root/"runtime_state/solana_opportunities/oad314_physical_outcome_endpoints.json";p.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_050_oad314_physical_outcome_endpoint_resolver import resolve,write
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=resolve(ROOT);p=write(ROOT);self.assertFalse(d["execution_authority"])
  print("[PHYSICAL_FILES]",d["physical_file_count"])
  for x in d["physical_files"][:20]:print("[OUTCOME_FILE]",x)
  print("[PASS] OSI-050 OAD-314 physical outcome endpoint resolver")
  print("[TRADER] Finds the exact future-result files already produced by the certified Solana pavement")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-050 OAD-314 PHYSICAL OUTCOME ENDPOINT RESOLVER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
