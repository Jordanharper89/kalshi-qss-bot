from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_intelligence_analytics_runtime"
MOD=PKG/"oiar_037_snapshot_event_time_source_discovery.py";TEST=ROOT/"test_oiar_037_snapshot_event_time_source_discovery.py"
MODULE_SOURCE='from pathlib import Path\nfrom .oiar_021_indexed_snapshot_identity_materializer import read_latest_indexed_snapshot_identity\nOIAR_037_BUILD_ID="OIAR-037";EXECUTION_AUTHORITY=False;TIME_FIELDS=("source_open_time","source_close_time","identity_observed_at")\ndef discover_event_time_sources(root=None):\n p=read_latest_indexed_snapshot_identity(Path(root or Path.cwd()).resolve())\n if not p:raise RuntimeError("OIAR-037 requires persisted OIAR-021 identity snapshot")\n rows=p.get("markets") or [];counts={k:sum(1 for r in rows if str(r.get(k) or "").strip()) for k in TIME_FIELDS}\n return {"market_count":len(rows),"field_counts":counts,"preferred_close_field":"source_close_time" if counts["source_close_time"] else None,"preferred_open_field":"source_open_time" if counts["source_open_time"] else None,"execution_authority":False}\ndef physical_probe(root=None):\n x=discover_event_time_sources(root)\n if x["market_count"]<=0:raise RuntimeError("OIAR-037 empty identity cohort")\n return x\n'
TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_037_snapshot_event_time_source_discovery as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_037_BUILD_ID,"OIAR-037")\n def test_fields(self):self.assertIn("source_close_time",m.TIME_FIELDS)\n def test_boundary(self):self.assertFalse(m.EXECUTION_AUTHORITY)\nif __name__=="__main__":\n print("="*88);print(" OIAR-037 CERTIFICATION TEST");print(" SNAPSHOT EVENT-TIME SOURCE DISCOVERY");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] snapshot-native event-time discovery contract certified")\n'
REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_021_indexed_snapshot_identity_materializer.py',)

def write_exact(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def main():
 print("="*88);print(" OIAR-037 INSTALLER");print(" SNAPSHOT EVENT-TIME SOURCE DISCOVERY");print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  p=ROOT/rel
  if not p.is_file():raise RuntimeError(f"Required proven upstream missing: {p}")
 targets=[MOD,TEST];old={p:(p.read_bytes() if p.exists() else None) for p in targets}
 try:
  ast.parse(MODULE_SOURCE,filename=str(MOD));ast.parse(TEST_SOURCE,filename=str(TEST))
  print("[PASS] installer payload syntax verified")
  write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=30)
  importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_037_snapshot_event_time_source_discovery")
  print("[PHYSICAL]",m.physical_probe(ROOT))
 except Exception:
  for p,b in old.items():restore(p,b)
  print("[ROLLBACK] OIAR-037 failed; affected repository files restored");raise
 print("[PASS] snapshot-only temporal intelligence boundary preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-037 INSTALLATION COMPLETE")
if __name__=="__main__":main()
