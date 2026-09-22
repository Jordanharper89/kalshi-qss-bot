from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_080_current_observation_source_independence_probe.py';TEST=ROOT/'test_oiar_080_current_observation_source_independence_probe.py'
SOURCE='from collections import Counter\nfrom pathlib import Path\nfrom qseries_v2.oracle_continuous_reasoning.ocr_002_live_observation_read_model import read_latest_canonical_observations\nOIAR_080_BUILD_ID="OIAR-080"\nMARKET_NATIVE={"market_snapshot","ticker","trade","orderbook","order_book","book"}\ndef classify_current_observation_sources(root=None,limit=5000):\n s=read_latest_canonical_observations(Path(root or Path.cwd()).resolve(),limit=int(limit));counts=Counter();independent=[]\n for r in s.rows:\n  typ=str(r.get("observation_type") or r.get("event_type") or "").lower();counts[typ or "(unknown)"]+=1\n  if typ not in MARKET_NATIVE:independent.append({"observation_id":r.get("observation_id"),"ticker":r.get("ticker"),"observation_type":typ,"source":r.get("source") or r.get("source_name")})\n return {"schema_version":"OIAR-080","rows_read":len(s.rows),"observation_type_counts":dict(counts),"market_native_rows":len(s.rows)-len(independent),"independent_candidate_rows":len(independent),"independent_candidates":independent[:100],"classification_only":True,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=classify_current_observation_sources(root);return {k:x[k] for k in ("rows_read","observation_type_counts","market_native_rows","independent_candidate_rows","probability_enabled","execution_authority")}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_080_current_observation_source_independence_probe as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["rows_read"],0);self.assertEqual(x["rows_read"],x["market_native_rows"]+x["independent_candidate_rows"]);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_continuous_reasoning/ocr_002_live_observation_read_model.py',)
def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-080 INSTALLER — CURRENT OBSERVATION SOURCE INDEPENDENCE PROBE');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 oldm=MOD.read_bytes() if MOD.exists() else None;oldt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");write_exact(MOD,SOURCE);write_exact(TEST,TEST_SOURCE);importlib.invalidate_caches()
  name="qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_080_current_observation_source_independence_probe';sys.modules.pop(name,None);m=importlib.import_module(name)
  s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  restore(MOD,oldm);restore(TEST,oldt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
