from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();TARGET=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_075_current_repeated_history_evidence_quality.py';TEST=ROOT/'test_oiar_075_current_repeated_history_evidence_quality.py'
SOURCE='from pathlib import Path\nfrom decimal import Decimal,InvalidOperation\nfrom datetime import datetime,timezone\ndef _dec(v):\n try:return Decimal(str(v)) if v is not None else None\n except (InvalidOperation,ValueError,TypeError):return None\ndef _dt(v):\n if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n except:return None\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_074_current_repeated_history_temporal_evidence import build_current_temporal_evidence\nOIAR_075_BUILD_ID="OIAR-075"\ndef build_evidence_quality(root=None):\n x=build_current_temporal_evidence(root);out=[]\n for m in x["markets"]:\n  repeated=m["history_rows"]>=2;priced=m["priced_rows"]>=2\n  q="STRONG_TEMPORAL" if repeated and priced else "REPEATED_UNPRICED" if repeated else "THIN"\n  out.append({**m,"evidence_quality":q,"reason_codes":(["repeated_canonical_history"] if repeated else ["thin_history"])+(["price_trajectory_available"] if priced else ["price_trajectory_unavailable"])})\n return {"schema_version":"OIAR-075","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_evidence_quality(root);return {"markets":x["market_count"],"strong_temporal":sum(m["evidence_quality"]=="STRONG_TEMPORAL" for m in x["markets"]),"repeated_unpriced":sum(m["evidence_quality"]=="REPEATED_UNPRICED" for m in x["markets"]),"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_075_current_repeated_history_evidence_quality as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_074_current_repeated_history_temporal_evidence.py',)
def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-075 INSTALLER — CURRENT REPEATED-HISTORY EVIDENCE QUALITY');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 bm=TARGET.read_bytes() if TARGET.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
  m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_075_current_repeated_history_evidence_quality');s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
 except Exception:
  restore(TARGET,bm);restore(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
