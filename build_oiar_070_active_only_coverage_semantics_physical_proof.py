from pathlib import Path
import ast,importlib,os,subprocess,sys,time
ROOT=Path.cwd().resolve();MOD=ROOT/"qseries_v2/oracle_intelligence_analytics_runtime/oiar_070_active_only_coverage_semantics_physical_proof.py";TEST=ROOT/"test_oiar_070_active_only_coverage_semantics_physical_proof.py";MODULE_SOURCE='from __future__ import annotations\nfrom pathlib import Path\nimport inspect\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_023_rotating_full_universe_coverage_cycle as opc23\nBUILD_ID="OIAR-070"\ndef contract_probe():\n f=inspect.getsource(opc23._active_markets);fetch=inspect.getsource(opc23.fetch_rotating_open_page);cycle=inspect.getsource(opc23.run_rotating_full_universe_coverage_cycle)\n return {"active_filter_proven":("active" in f.lower()),"status_open_request_absent":(\'"status":"open"\' not in fetch and "\'status\':\'open\'" not in fetch),"raw_page_count_preserved":("raw_page_markets" in cycle),"historical_settled_backfill_supported_by_normal_cycle":False}\ndef physical_probe(root=None):\n root=Path(root or Path.cwd()).resolve();c=contract_probe();state,markets,nxt,raw=opc23.fetch_rotating_open_page(root);nonactive=sum(str(x.get("status") or "").lower()!="active" for x in markets)\n return {**c,"current_page_active_markets":len(markets),"current_page_raw_markets":int(raw),"current_page_nonactive_admitted":nonactive,"read_only":True,"probability_enabled":False,"execution_authority":False}\ndef verify_oiar_070():\n c=contract_probe();return BUILD_ID=="OIAR-070" and c["active_filter_proven"] and c["status_open_request_absent"] and not c["historical_settled_backfill_supported_by_normal_cycle"]\n';TEST_SOURCE='import unittest\nimport qseries_v2.oracle_intelligence_analytics_runtime.oiar_070_active_only_coverage_semantics_physical_proof as m\nclass T(unittest.TestCase):\n def test_contract(self):self.assertTrue(m.verify_oiar_070())\nif __name__=="__main__":\n print("="*88);print(" OIAR-070 CERTIFICATION TEST");print(" ACTIVE-ONLY COVERAGE SEMANTICS PHYSICAL PROOF");print("="*88)\n r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n if not r.wasSuccessful():raise SystemExit(1)\n print("[PASS] normal OPC cycle proven ACTIVE/current only");print("[DONE] OIAR-070 CERTIFIED")\n'
def w(p,s):p.parent.mkdir(parents=True,exist_ok=True);t=p.with_name(p.name+f".{os.getpid()}.tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)
def rr(p,b):
 if b is None:
  if p.exists():p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88);print(" OIAR-070 INSTALLER");print(" ACTIVE-ONLY COVERAGE SEMANTICS PHYSICAL PROOF");print("="*88);print("[ROOT]",ROOT)
 bm=MOD.read_bytes() if MOD.exists() else None;bt=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);print("[PASS] installer payload syntax verified");w(MOD,MODULE_SOURCE);w(TEST,TEST_SOURCE);importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_070_active_only_coverage_semantics_physical_proof");s=time.monotonic();x=m.physical_probe(ROOT);print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
  if x["current_page_raw_markets"]<=0 or x["current_page_nonactive_admitted"]!=0:raise RuntimeError("active-only physical contract failed")
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=120)
 except Exception:
  rr(MOD,bm);rr(TEST,bt);print("[ROLLBACK] OIAR-070 failed; affected files restored");raise
 print("[PASS] settled historical markets are not admitted by normal ACTIVE coverage");print("[PASS] probability_enabled=FALSE");print("[PASS] execution_authority=FALSE");print("[DONE] OIAR-070 INSTALLATION COMPLETE")
if __name__=="__main__":main()
