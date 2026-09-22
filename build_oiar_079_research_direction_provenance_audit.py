from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_079_research_direction_provenance_audit.py';TEST=ROOT/'test_oiar_079_research_direction_provenance_audit.py'
SOURCE='from collections import Counter\nfrom pathlib import Path\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics\nOIAR_079_BUILD_ID="OIAR-079"\ndef audit_research_direction_provenance(root=None):\n x=read_latest_current_trader_analytics(root)\n if not x:raise RuntimeError("OIAR-054 snapshot unavailable")\n rows=[];dirs=Counter();reasons=Counter()\n for m in x.get("markets",[]):\n  c=m.get("candidate",{});u=m.get("usefulness",{});d=str(c.get("research_direction") or "neutral").lower();dirs[d]+=1\n  for r in c.get("reason_codes",[]) or []:reasons[str(r)]+=1\n  rows.append({"market_id":m["market_id"],"research_direction":d,"candidate_disposition":c.get("disposition"),"usefulness_classification":u.get("classification"),"provenance":"OIA-006_MARKET_DERIVED_FEATURE_CLASSIFICATION","independent_external_evidence":False})\n return {"schema_version":"OIAR-079","market_count":len(rows),"direction_counts":dict(dirs),"candidate_reason_counts":dict(reasons),"market_derived_direction_count":len(rows),"independent_direction_count":0,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=audit_research_direction_provenance(root);return {"markets":x["market_count"],"directions":x["direction_counts"],"candidate_reasons":x["candidate_reason_counts"],"market_derived_direction_count":x["market_derived_direction_count"],"independent_direction_count":0,"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_079_research_direction_provenance_audit as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertEqual(x["market_derived_direction_count"],x["markets"]);self.assertEqual(x["independent_direction_count"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_054_proven_current_trader_analytics.py',)
def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-079 INSTALLER — RESEARCH DIRECTION PROVENANCE AUDIT');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 oldm=MOD.read_bytes() if MOD.exists() else None;oldt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");write_exact(MOD,SOURCE);write_exact(TEST,TEST_SOURCE);importlib.invalidate_caches()
  name="qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_079_research_direction_provenance_audit';sys.modules.pop(name,None);m=importlib.import_module(name)
  s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  restore(MOD,oldm);restore(TEST,oldt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
