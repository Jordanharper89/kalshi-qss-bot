from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();TARGET=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_074_current_repeated_history_temporal_evidence.py';TEST=ROOT/'test_oiar_074_current_repeated_history_temporal_evidence.py'
SOURCE='from pathlib import Path\nfrom decimal import Decimal,InvalidOperation\nfrom datetime import datetime,timezone\ndef _dec(v):\n try:return Decimal(str(v)) if v is not None else None\n except (InvalidOperation,ValueError,TypeError):return None\ndef _dt(v):\n if isinstance(v,datetime):return v if v.tzinfo else v.replace(tzinfo=timezone.utc)\n try:return datetime.fromisoformat(str(v).replace("Z","+00:00"))\n except:return None\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_053_proven_current_market_history import read_latest_current_market_history\nOIAR_074_BUILD_ID="OIAR-074"\ndef build_current_temporal_evidence(root=None):\n x=read_latest_current_market_history(root); \n if not x:raise RuntimeError("OIAR-053 current history unavailable")\n out=[]\n for m in x["markets"]:\n  h=list(m.get("history") or []); prices=[(_dt(r.get("observed_at")),_dec(r.get("last_price_dollars"))) for r in h];prices=[z for z in prices if z[1] is not None]\n  chronological=sorted(prices,key=lambda z:z[0] or datetime.min.replace(tzinfo=timezone.utc))\n  first=chronological[0][1] if chronological else None;last=chronological[-1][1] if chronological else None;chg=(last-first) if first is not None and last is not None else None\n  direction="UP" if chg is not None and chg>0 else "DOWN" if chg is not None and chg<0 else "FLAT_OR_UNKNOWN"\n  out.append({"market_id":m["market_ticker"],"history_rows":len(h),"priced_rows":len(prices),"first_price":None if first is None else str(first),"latest_price":None if last is None else str(last),"price_change":None if chg is None else str(chg),"temporal_direction":direction})\n return {"schema_version":"OIAR-074","market_count":len(out),"markets":out,"probability_enabled":False,"read_only":True,"execution_authority":False}\ndef physical_probe(root=None):\n x=build_current_temporal_evidence(root);return {"markets":x["market_count"],"repeated_history":sum(m["history_rows"]>=2 for m in x["markets"]),"priced":sum(m["priced_rows"]>=2 for m in x["markets"]),"probability_enabled":False,"execution_authority":False}\n';TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime import oiar_074_current_repeated_history_temporal_evidence as m\nclass T(unittest.TestCase):\n def test_physical(self):\n  x=m.physical_probe();self.assertGreater(x["markets"],0);self.assertGreater(x["repeated_history"],0);self.assertFalse(x["probability_enabled"]);self.assertFalse(x["execution_authority"])\nif __name__=="__main__":unittest.main(verbosity=2)\n';REQUIRED=('qseries_v2/oracle_intelligence_analytics_runtime/oiar_053_proven_current_market_history.py',)
def w(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(' OIAR-074 INSTALLER — CURRENT REPEATED-HISTORY TEMPORAL EVIDENCE');print("="*88);print("[ROOT]",ROOT)
 for rel in REQUIRED:
  if not (ROOT/rel).is_file():raise RuntimeError("Required certified upstream missing: "+rel)
 bm=TARGET.read_bytes() if TARGET.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE);ast.parse(TEST_SOURCE);print("[PASS] payload syntax verified");w(TARGET,SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches()
  m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime."+'oiar_074_current_repeated_history_temporal_evidence');s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=90)
 except Exception:
  restore(TARGET,bm);restore(TEST,bt);print("[ROLLBACK] failed; affected files restored");raise
 print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
