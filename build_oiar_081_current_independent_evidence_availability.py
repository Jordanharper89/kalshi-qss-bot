from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_081_current_independent_evidence_availability.py';TEST=ROOT/'test_oiar_081_current_independent_evidence_availability.py'
SOURCE='from pathlib import Path\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_052_proven_current_canonical_trader_cohort import read_latest_current_trader_cohort\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_080_current_observation_source_independence_probe import classify_current_observation_sources\nOIAR_081_BUILD_ID="OIAR-081"\ndef build_current_independent_evidence_availability(root=None):\n c=read_latest_current_trader_cohort(root);p=classify_current_observation_sources(root)\n if not c:raise RuntimeError("OIAR-052 cohort unavailable")\n ids={m["market_ticker"] for m in c["markets"]};by={k:[] for k in ids}\n for r in p["independent_candidates"]:\n  t=str(r.get("ticker") or "")\n  if t in by:by[t].append(r)\n rows=[{"market_id":k,"independent_evidence_rows":len(v),"independent_evidence_available":bool(v),"evidence":v} for k,v in sorted(by.items())]\n return {"schema_version":"OIAR-081","market_count":len(rows),"markets_with_independent_evidence":sum(x["independent_evidence_available"] for x in rows),"markets":rows,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_current_independent_evidence_availability(root);return {"markets":x["market_count"],"markets_with_independent_evidence":x["markets_with_independent_evidence"],"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_081_current_independent_evidence_availability as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertLessEqual(x["markets_with_independent_evidence"],x["markets"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_052_proven_current_canonical_trader_cohort.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_080_current_observation_source_independence_probe.py')
def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-081 INSTALLER — CURRENT INDEPENDENT EVIDENCE AVAILABILITY');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 oldm=MOD.read_bytes() if MOD.exists() else None;oldt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");write_exact(MOD,SOURCE);write_exact(TEST,TEST_SOURCE);importlib.invalidate_caches()
  name="qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_081_current_independent_evidence_availability';sys.modules.pop(name,None);m=importlib.import_module(name)
  s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  restore(MOD,oldm);restore(TEST,oldt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
