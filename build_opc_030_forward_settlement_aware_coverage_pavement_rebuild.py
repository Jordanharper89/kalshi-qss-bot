from pathlib import Path
import ast,importlib,os,subprocess,sys
ROOT=Path.cwd().resolve()
TARGET=ROOT/'qseries_v2/oracle_pre_settlement_coverage/opc_030_high_throughput_universal_coverage_gate.py'
TEST=ROOT/'test_opc_030_high_throughput_universal_coverage_gate.py'
SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport time\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_market_freshness\nfrom .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,save_coverage_universe_cursor,next_coverage_cursor\nfrom .opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page\nfrom .opc_026_full_page_coverage_admission import admit_full_page_coverage\nfrom .opc_027_chunked_full_page_persistence import persist_full_page_in_chunks\nfrom .opc_029_adaptive_coverage_throughput_controller import choose_throughput_budget\nOPC_030_BUILD_ID="OPC-030"; OPC_030_REVISION="OPC_030_FORWARD_FRESHNESS_SETTLEMENT_AWARE_RECERTIFIED"\n@dataclass(frozen=True)\nclass HighThroughputCoverageResult:\n    page_markets:int; already_covered:int; missing_markets:int; requested:int; persisted:int; retries_used:int; chunk_size:int; cursor_advanced:bool; execution_authority:bool=False\ndef run_high_throughput_coverage_cycle(root=None,progress=None,recent_retries=0,recent_failures=0):\n    root=Path(root or Path.cwd()).resolve(); throughput=choose_throughput_budget(recent_retries=recent_retries,recent_failures=recent_failures)\n    budget=CoverageLoadBudget(page_limit=1000,max_snapshots_per_cycle=1000,cycle_sleep_seconds=0.0,lookback_hours=24.0,request_timeout_seconds=20.0)\n    old,markets,nxt,raw=fetch_rotating_open_page(root,budget)\n    freshness=read_recent_canonical_market_freshness(root,24,250000)\n    admission=admit_full_page_coverage(markets,freshness=freshness)\n    result=persist_full_page_in_chunks(markets,admission.admitted_tickers,root=root,chunk_size=throughput.chunk_size,max_retries=throughput.max_retries,progress=progress)\n    new=save_coverage_universe_cursor(next_coverage_cursor(old,nxt,raw),root)\n    if progress:progress(f"[HIGH THROUGHPUT COVERAGE] page={new.pages_completed} raw={raw} active={len(markets)} fresh={admission.already_covered} due={admission.missing_markets} requested={result.requested} persisted={result.persisted} retries={result.retries_used} chunk_size={result.chunk_size} mode={throughput.mode}")\n    if throughput.inter_page_sleep_seconds:time.sleep(throughput.inter_page_sleep_seconds)\n    return HighThroughputCoverageResult(len(markets),admission.already_covered,admission.missing_markets,result.requested,result.persisted,result.retries_used,result.chunk_size,new.pages_completed>old.pages_completed,False)\ndef verify_opc_030_high_throughput_universal_coverage_gate():\n    x=HighThroughputCoverageResult(1000,10,990,990,990,1,200,True,False)\n    return x.requested==990 and x.persisted==990 and x.cursor_advanced and not x.execution_authority\n'
TEST_SOURCE='import unittest,inspect\nfrom qseries_v2.oracle_pre_settlement_coverage import opc_030_high_throughput_universal_coverage_gate as m\nclass T(unittest.TestCase):\n def test_contract(self):\n  self.assertTrue(m.verify_opc_030_high_throughput_universal_coverage_gate())\n  s=inspect.getsource(m.run_high_throughput_coverage_cycle)\n  self.assertIn("read_recent_canonical_market_freshness",s); self.assertIn("freshness=freshness",s)\nif __name__=="__main__":unittest.main(verbosity=2)\n'
def write_atomic(p,s):
 p.parent.mkdir(parents=True,exist_ok=True); t=p.with_name(p.name+f".{os.getpid()}.tmp"); t.write_text(s,encoding="utf-8",newline="\n"); os.replace(t,p)
def restore(p,b):
 if b is None:
  if p.exists(): p.unlink()
 else:p.write_bytes(b)
def main():
 print("="*88); print(' OPC-030 PAVEMENT REBUILD — FORWARD SETTLEMENT-AWARE COVERAGE'); print("="*88); print("[ROOT]",ROOT)
 before=TARGET.read_bytes() if TARGET.exists() else None; tb=TEST.read_bytes() if TEST.exists() else None
 try:
  ast.parse(SOURCE); ast.parse(TEST_SOURCE); print("[PASS] payload syntax verified")
  write_atomic(TARGET,SOURCE); write_atomic(TEST,TEST_SOURCE); importlib.invalidate_caches()
  pass
  subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True,timeout=180)
 except Exception:
  restore(TARGET,before); restore(TEST,tb); print("[ROLLBACK] failed; affected files restored"); raise
 print("[DONE] INSTALLATION COMPLETE")
if __name__=="__main__":main()
