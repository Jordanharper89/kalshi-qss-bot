from pathlib import Path
ROOT=Path(__file__).resolve().parent
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_intelligence"
MOD=SUB/"osi_028_safe_runtime_retention_cleanup_gate.py"
TEST=ROOT/"test_osi_028_safe_runtime_retention_cleanup_gate.py"
MOD_TEXT=r"""from __future__ import annotations
import json,time
from pathlib import Path
PROTECTED=("continuity","recovery","settlement","learning","outcome","state","queue","manifest","registry")
TRANSIENT=("debug","tmp","temp","trace","spool","raw_events")
def plan(root:Path)->dict:
 now=time.time();items=[]
 for base_name in ("runtime","runtime_state"):
  base=root/base_name
  if not base.exists():continue
  for p in base.rglob("*"):
   if not p.is_file():continue
   s=p.stat();rel=str(p.relative_to(root));low=rel.lower();age=max(0,now-s.st_mtime)
   if any(k in low for k in PROTECTED):
    action="KEEP_PROTECTED"
   elif s.st_size>=1_000_000_000 and any(k in low for k in TRANSIENT):
    action="ROTATE_OR_ARCHIVE_REVIEW"
   elif age>=2_592_000 and any(k in low for k in TRANSIENT):
    action="RETIRE_REVIEW"
   elif s.st_size>=250_000_000:
    action="REVIEW_LARGE"
   else:
    action="KEEP"
   items.append({"path":rel,"size":s.st_size,"age_seconds":age,"proposed_action":action})
 counts={}
 for x in items:counts[x["proposed_action"]]=counts.get(x["proposed_action"],0)+1
 return {"revision":"OSI_028","items":items,"counts":counts,
  "destructive_action_authorized":False,"execution_authority":False,"read_only":True,
  "rule":"No deletion until an explicit later retirement build consumes this reviewed plan."}
def write_plan(root:Path)->Path:
 p=root/"OSI_028_SAFE_RUNTIME_RETENTION_CLEANUP_PLAN.json";p.write_text(json.dumps(plan(root),indent=2,sort_keys=True),encoding="utf-8");return p
"""
TEST_TEXT=r"""import unittest,json
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_intelligence.osi_028_safe_runtime_retention_cleanup_gate import plan,write_plan
ROOT=Path(__file__).resolve().parent
class T(unittest.TestCase):
 def test_plan(self):
  d=plan(ROOT);p=write_plan(ROOT)
  self.assertTrue(p.is_file());self.assertFalse(d["destructive_action_authorized"]);self.assertFalse(d["execution_authority"])
  print("[PLAN]",p);print("[COUNTS]",json.dumps(d["counts"],sort_keys=True))
  review=[x for x in d["items"] if x["proposed_action"]!="KEEP" and x["proposed_action"]!="KEEP_PROTECTED"]
  if review:print("[TOP_REVIEW]",json.dumps(sorted(review,key=lambda x:x["size"],reverse=True)[0],sort_keys=True))
  print("[PASS] OSI-028 safe runtime retention/cleanup gate")
  print("[TRADER] Identifies expensive runtime junk without risking restart, continuity, outcomes, or learning state")
  print("[SCOPE] Planning only; destructive cleanup is NOT authorized")
if __name__=="__main__":unittest.main()
"""
def main():
 print("="*112);print(" OSI-028 SAFE RUNTIME RETENTION / CLEANUP GATE");print("="*112)
 SUB.mkdir(parents=True,exist_ok=True);MOD.write_text(MOD_TEXT,encoding="utf-8");TEST.write_text(TEST_TEXT,encoding="utf-8")
 print("[PASS] installed:",MOD.relative_to(ROOT));print("[PASS] test:",TEST.name);print("[PASS] destructive_action_authorized=FALSE");print("[PASS] execution_authority=FALSE")
if __name__=="__main__":main()
