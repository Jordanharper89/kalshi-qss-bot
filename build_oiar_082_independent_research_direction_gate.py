from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_082_independent_research_direction_gate.py';TEST=ROOT/'test_oiar_082_independent_research_direction_gate.py'
SOURCE='from qseries_v2.oracle_intelligence_analytics_runtime.oiar_079_research_direction_provenance_audit import audit_research_direction_provenance\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_081_current_independent_evidence_availability import build_current_independent_evidence_availability\nOIAR_082_BUILD_ID="OIAR-082"\ndef build_independent_research_direction_gate(root=None):\n p=audit_research_direction_provenance(root);e=build_current_independent_evidence_availability(root);emap={x["market_id"]:x for x in e["markets"]};rows=[]\n for r in p["markets"]:\n  a=emap.get(r["market_id"],{});available=bool(a.get("independent_evidence_available"))\n  rows.append({"market_id":r["market_id"],"market_derived_direction":r["research_direction"],"independent_evidence_available":available,"independent_research_direction":"neutral","direction_status":"EVIDENCE_PRESENT_DIRECTION_NOT_CERTIFIED" if available else "NO_INDEPENDENT_EVIDENCE","market_direction_may_not_substitute":True})\n return {"schema_version":"OIAR-082","market_count":len(rows),"independent_direction_certified":0,"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_independent_research_direction_gate(root);return {"markets":x["market_count"],"independent_evidence_present":sum(m["independent_evidence_available"] for m in x["markets"]),"independent_direction_certified":0,"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_082_independent_research_direction_gate as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertEqual(x["independent_direction_certified"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_079_research_direction_provenance_audit.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_081_current_independent_evidence_availability.py')
def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-082 INSTALLER — INDEPENDENT RESEARCH DIRECTION GATE');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 oldm=MOD.read_bytes() if MOD.exists() else None;oldt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");write_exact(MOD,SOURCE);write_exact(TEST,TEST_SOURCE);importlib.invalidate_caches()
  name="qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_082_independent_research_direction_gate';sys.modules.pop(name,None);m=importlib.import_module(name)
  s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  restore(MOD,oldm);restore(TEST,oldt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
