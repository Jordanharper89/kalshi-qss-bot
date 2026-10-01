from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_024_runtime_usage_and_junk_audit.py"
TEST=ROOT/"test_osi_024_runtime_usage_and_junk_audit.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path

def audit(root:Path)->dict:
 now=time.time(); rows=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists(): continue
  for p in base.rglob("*"):
   if not p.is_file(): continue
   s=p.stat(); age=max(0,now-s.st_mtime)
   rows.append({"path":str(p.relative_to(root)),"size":s.st_size,"age_seconds":age,"suffix":p.suffix.lower()})
 rows.sort(key=lambda x:x["size"],reverse=True)
 total=sum(x["size"] for x in rows)
 return {"revision":"OSI_024","file_count":len(rows),"total_bytes":total,
         "largest_files":rows[:100],
         "over_1gb":[x for x in rows if x["size"]>=1_000_000_000],
         "over_100mb":[x for x in rows if x["size"]>=100_000_000],
         "older_than_7d":[x for x in rows if x["age_seconds"]>=604800][:250],
         "execution_authority":False,"read_only":True,
         "scope":"inventory_only_no_delete"}

def write_report(root:Path)->Path:
 p=root/"OSI_024_RUNTIME_USAGE_AND_JUNK_AUDIT.json"
 p.write_text(json.dumps(audit(root),indent=2,sort_keys=True),encoding="utf-8")
 return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_024_runtime_usage_and_junk_audit import audit,write_report
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_physical(self):
  d=audit(ROOT);p=write_report(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["execution_authority"])
  print("[REPORT]",p);print("[FILE_COUNT]",d["file_count"]);print("[TOTAL_BYTES]",d["total_bytes"])
  print("[OVER_1GB]",len(d["over_1gb"]));print("[OVER_100MB]",len(d["over_100mb"]))
  if d["largest_files"]:print("[LARGEST]",json.dumps(d["largest_files"][0],sort_keys=True))
  print("[PASS] OSI-024 runtime usage and junk audit")
  print("[TRADER] Measures what is actually consuming disk/runtime attention before cleanup")
  print("[SCOPE] Read-only inventory; nothing deleted")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-024 RUNTIME USAGE AND JUNK AUDIT");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] execution_authority=FALSE");print("[SCOPE] Inventory only; no deletion")
if __name__=="__main__":main()
