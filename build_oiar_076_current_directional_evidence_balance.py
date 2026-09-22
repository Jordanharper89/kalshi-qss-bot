from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();TARGET=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_076_current_directional_evidence_balance.py';TEST=ROOT/'test_oiar_076_current_directional_evidence_balance.py'
SOURCE='from pathlib import Path\nfrom decimal import Decimal,InvalidOperation\nfrom datetime import datetime,timezone\ndef _dec(v):\n try:return Decimal(str(v)) if v is not None else None\n except (InvalidOperation,ValueError,TypeError):return None\ndef _dt(v):\n if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n except:return None\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_075_current_repeated_history_evidence_quality import build_evidence_quality\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_054_proven_current_trader_analytics import read_latest_current_trader_analytics\nOIAR_076_BUILD_ID="OIAR-076"\ndef build_directional_evidence_balance(root=None):\n q=build_evidence_quality(root);a=read_latest_current_trader_analytics(root)\n amap={str(m.get("market_id")):m for m in ((a or {}).get("markets") or [])};out=[]\n for m in q["markets"]:\n  z=amap.get(m["market_id"],{});research=str((z.get("candidate") or {}).get("research_direction") or (z.get("admission") or {}).get("research_direction") or "neutral").lower()\n  td=m["temporal_direction"];temporal="bull" if td=="UP" else "bear" if td=="DOWN" else "neutral"\n  agreement=(research==temporal and research in ("bull","bear"));contradiction=(research in ("bull","bear") and temporal in ("bull","bear") and research!=temporal)\n  out.append({**m,"research_direction":research,"temporal_signal":temporal,"directional_agreement":agreement,"directional_contradiction":contradiction})\n return {"schema_version":"OIAR-076","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_directional_evidence_balance(root);return {"markets":x["market_count"],"agreements":sum(m["directional_agreement"] for m in x["markets"]),"contradictions":sum(m["directional_contradiction"] for m in x["markets"]),"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_076_current_directional_evidence_balance as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_075_current_repeated_history_evidence_quality.py', 'qseries_v2/oracle_intelligence_analytics_runtime/oiar_054_proven_current_trader_analytics.py')
def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-076 INSTALLER — CURRENT DIRECTIONAL EVIDENCE BALANCE');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 bm=TARGET.read_bytes() if TARGET.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
  m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_076_current_directional_evidence_balance');s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
 except Exception:
  restore(TARGET,bm);restore(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
