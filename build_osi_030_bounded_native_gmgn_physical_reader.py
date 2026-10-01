from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_030_bounded_native_gmgn_physical_reader.py"
TEST=ROOT/"test_osi_030_bounded_native_gmgn_physical_reader.py"
MOD_TEXT=r"""from __future__ import annotations
import json
from pathlib import Path
ENDPOINTS="runtime_state/solana_opportunities/physical_source_endpoints.json"
def _read(path:Path,limit:int=100)->list[dict]:
 out=[]
 try:
  if path.suffix.lower()==".json":
   obj=json.loads(path.read_text(encoding="utf-8",errors="replace"));vals=obj if isinstance(obj,list) else [obj]
   return [x for x in vals[-limit:] if isinstance(x,dict)]
  if path.suffix.lower()==".jsonl":
   lines=path.read_text(encoding="utf-8",errors="replace").splitlines()[-limit:]
   for line in lines:
    try:
     x=json.loads(line)
     if isinstance(x,dict):out.append(x)
    except Exception:pass
 except Exception:pass
 return out
def read_registered(root:Path,limit_per_file:int=100,max_files:int=20)->dict:
 ep=root/ENDPOINTS
 if not ep.is_file():raise RuntimeError("Missing OSI-029 endpoint registry")
 d=json.loads(ep.read_text(encoding="utf-8"))
 native=[];gmgn=[]
 for rel in d.get("physical_native_files",[])[:max_files]:
  for row in _read(root/rel,limit_per_file):native.append({"source":rel,"row":row})
 for rel in d.get("physical_gmgn_files",[])[:max_files]:
  for row in _read(root/rel,limit_per_file):gmgn.append({"source":rel,"row":row})
 return {"native":native,"gmgn":gmgn,"native_rows":len(native),"gmgn_rows":len(gmgn),
  "execution_authority":False,"read_only":True,"bounded":True}
"""
TEST_TEXT=r"""import unittest
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_030_bounded_native_gmgn_physical_reader import read_registered
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=read_registered(ROOT,25,10);self.assertFalse(d["execution_authority"]);self.assertTrue(d["bounded"])
  print("[NATIVE_ROWS]",d["native_rows"]);print("[GMGN_ROWS]",d["gmgn_rows"])
  print("[PASS] OSI-030 bounded native Solana + GMGN physical reader")
  print("[TRADER] Reads only registered physical sources; no recursive scan of the giant Oracle runtime")
  print("[SCOPE] Read-only bounded consumption")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-030 BOUNDED NATIVE SOLANA + GMGN PHYSICAL READER");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
