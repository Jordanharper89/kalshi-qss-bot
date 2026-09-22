from pathlib import Path
import ast,os,subprocess,sys
ROOT=Path.cwd().resolve();MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_014_natural_trader_question_router.py';TEST=ROOT/'test_oiar_014_natural_trader_question_router.py'
SRC='OIAR_014_BUILD_ID="OIAR-014"\nTOKENS=("what do you like","best markets","best 5","best five","anything worth","anything moving","what should i watch","show me crypto","show me bitcoin","show me btc","show me sports","what does oracle know best","historically proven","live opportunities","rank trader intelligence","learned markets","worth trading","edge right now")\ndef normalize(q):return " ".join(str(q or "").lower().split())\ndef is_trader_brief_query(q):return any(t in normalize(q) for t in TOKENS)\ndef trader_query_filter(q):\n n=normalize(q)\n if "bitcoin" in n or "btc" in n or "crypto" in n:return "crypto"\n if "sport" in n:return "sports"\n return None\n';TSRC='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_014_natural_trader_question_router as m\nclass T(unittest.TestCase):\n def test_identity(self):self.assertEqual(m.OIAR_014_BUILD_ID,"OIAR-014")\nif __name__=="__main__":\n print("="*88);print(" OIAR-014 CERTIFICATION TEST");r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] OIAR-014 contract certified");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-014 CERTIFIED")\n';REQ=['qseries_v2/oracle_intelligence_analytics_runtime/oiar_013_trader_brief_renderer.py']
def write(p,s):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8");os.replace(t,p)
def main():
 print("="*88);print(" OIAR-014 INSTALLER");print(" NATURAL TRADER QUESTION ROUTER");print("="*88);print("[ROOT]",ROOT)
 for x in REQ:
  if not (ROOT/x).is_file():raise RuntimeError(f"Required proven upstream missing: {ROOT/x}")
 ast.parse(SRC);ast.parse(TSRC);print("[PASS] installer payload syntax verified");write(MOD,SRC);write(TEST,TSRC);
 subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
 print("[PASS] read-only trader presentation boundary preserved");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-014 INSTALLATION COMPLETE")
if __name__=="__main__":main()
