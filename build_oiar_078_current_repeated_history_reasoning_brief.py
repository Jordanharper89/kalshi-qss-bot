from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();TARGET=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_078_current_repeated_history_reasoning_brief.py';TEST=ROOT/'test_oiar_078_current_repeated_history_reasoning_brief.py'
SOURCE='from pathlib import Path\nfrom decimal import Decimal,InvalidOperation\nfrom datetime import datetime,timezone\ndef _dec(v):\n try:return Decimal(str(v)) if v is not None else None\n except (InvalidOperation,ValueError,TypeError):return None\ndef _dt(v):\n if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n except:return None\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_077_current_abstention_aware_reasoning_state import build_reasoning_states\nOIAR_078_BUILD_ID="OIAR-078"\ndef render_current_reasoning_brief(root=None,limit=10):\n x=build_reasoning_states(root);rank={"READY":0,"OBSERVE":1,"ABSTAIN":2};ms=sorted(x["markets"],key=lambda m:(rank[m["reasoning_state"]],m["market_id"]))[:max(1,int(limit))]\n lines=["="*88,"ORACLE CURRENT REPEATED-HISTORY REASONING BRIEF","EVIDENCE-GROUNDED | ABSTENTION-AWARE | PROBABILITY DISABLED","-"*88]\n for i,m in enumerate(ms,1):\n  lines += [f"#{i} {m[\'market_id\']}",f"   State: {m[\'reasoning_state\']} | Direction: {m[\'direction\']}",f"   History: {m[\'history_rows\']} | Priced: {m[\'priced_rows\']} | Temporal: {m[\'temporal_direction\']}",f"   Research: {m[\'research_direction\']} | Evidence: {m[\'evidence_quality\']}",f"   Reason: {m[\'state_reason\']}",""]\n lines += ["Probability: DISABLED pending certified post-repair outcome learning.","No order placement. Q Series execution authority remains separate.","="*88]\n return tuple(lines)\ndef physical_probe(root=None):\n lines=render_current_reasoning_brief(root);return {"lines":len(lines),"header":lines[1],"probability_enabled":False,"read_only":True,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_078_current_repeated_history_reasoning_brief as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["lines"],5);self.assertEqual(x["header"],"ORACLE CURRENT REPEATED-HISTORY REASONING BRIEF");self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_077_current_abstention_aware_reasoning_state.py',)
def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-078 INSTALLER — CURRENT REPEATED-HISTORY REASONING BRIEF');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 bm=TARGET.read_bytes() if TARGET.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
  m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_078_current_repeated_history_reasoning_brief');s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
 except Exception:
  restore(TARGET,bm);restore(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
