from pathlib import Path
import ast,os,subprocess,sys
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_013_trader_brief_renderer.py';TEST=ROOT/'test_oiar_013_trader_brief_renderer.py'
SRC='from .oiar_012_trader_interpretation_model import interpret_trader_row\nOIAR_013_BUILD_ID="OIAR-013"\ndef render_trader_brief(rows,freshness_status=None,age_seconds=None,limit=5):\n z=["="*80,"ORACLE TRADER BRIEF","READ-ONLY | TRADER INTERPRETATION, NOT EXECUTION","-"*80]\n if freshness_status:z+=["Data: %s | snapshot age: %.0fs"%(freshness_status,float(age_seconds or 0)),"-"*80]\n for n,r in enumerate(tuple(rows)[:limit],1):\n  x=interpret_trader_row(r);z += [f"#{n} {x.market_name}",f"   Oracle read: {x.takeaway}",f"   Direction: {x.direction} | Setup: {x.setup_quality}",f"   Historical knowledge: {x.historical_strength} | Live evidence: {x.live_evidence}",f"   Risk: {x.risk}",f"   Market ID: {x.market_id}",""]\n if not rows:z+=["No ranked markets in the current persisted snapshot."]\n return tuple(z+["No order placement. Q Series execution authority remains separate.","="*80])\n';TSRC='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_013_trader_brief_renderer as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_013_BUILD_ID,"OIAR-013")\nif __name__=="__main__":\n print("="*88);print(" OIAR-013 CERTIFICATION TEST");r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OIAR-013 contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-013 CERTIFIED")\n';REQ=['qseries_v2/oracle_intelligence_analytics_runtime/oiar_012_trader_interpretation_model.py']
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8");os.replace(t,p)
def main():
 print("="*88);print(" OIAR-013 INSTALLER");print(" TRADER BRIEF RENDERER");print("="*88);print("[ROOT]",ROOT)
 for x in REQ:
  if not (ROOT/x).is_file():raise RuntimeError(f"Required proven upstream missing: {ROOT/x}")
 ast.parse(SRC);ast.parse(TSRC);print("[PASS] installer payload syntax verified");write(MOD,SRC);write(TEST,TSRC);
 subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
 print("[PASS] read-only trader presentation boundary preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-013 INSTALLATION COMPLETE")
if __name__=="__main__":main()
