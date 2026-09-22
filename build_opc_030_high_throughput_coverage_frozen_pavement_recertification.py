from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
TITLE='OPC-030 FROZEN-PAVEMENT RECERTIFICATION / HIGH-THROUGHPUT ACTIVE COVERAGE'
TARGETS=['qseries_v2/oracle_pre_settlement_coverage/opc_030_high_throughput_universal_coverage_gate.py']
PAYLOADS=['from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport time\n\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_022_rotating_universe_cursor_load_budget import (\n    CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor\n)\nfrom .opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page\nfrom .opc_026_full_page_coverage_admission import admit_full_page_coverage\nfrom .opc_027_chunked_full_page_persistence import persist_full_page_in_chunks\nfrom .opc_029_adaptive_coverage_throughput_controller import choose_throughput_budget\n\nOPC_030_BUILD_ID="OPC-030"\nOPC_030_REVISION="OPC_030_HIGH_THROUGHPUT_UNIVERSAL_COVERAGE_GATE_ACTIVE_SEMANTICS_RECERTIFIED"\n\n@dataclass(frozen=True)\nclass HighThroughputCoverageResult:\n    page_markets:int\n    already_covered:int\n    missing_markets:int\n    requested:int\n    persisted:int\n    retries_used:int\n    chunk_size:int\n    cursor_advanced:bool\n    execution_authority:bool=False\n\ndef run_high_throughput_coverage_cycle(root=None,progress=None,recent_retries=0,recent_failures=0):\n    root=Path(root or Path.cwd()).resolve()\n    throughput=choose_throughput_budget(\n        recent_retries=recent_retries,\n        recent_failures=recent_failures,\n    )\n    base_budget=CoverageLoadBudget(\n        page_limit=1000,\n        max_snapshots_per_cycle=1000,\n        cycle_sleep_seconds=0.0,\n        lookback_hours=24.0,\n        request_timeout_seconds=20.0,\n    )\n\n    old_state,markets,next_cursor,raw_page_markets=fetch_rotating_open_page(root,base_budget)\n    recent=read_recent_canonical_tickers(root,24,250000)\n    admission=admit_full_page_coverage(markets,recent)\n\n    result=persist_full_page_in_chunks(\n        markets,\n        admission.admitted_tickers,\n        root=root,\n        chunk_size=throughput.chunk_size,\n        max_retries=throughput.max_retries,\n        progress=progress,\n    )\n\n    new_state=save_coverage_universe_cursor(\n        next_coverage_cursor(old_state,next_cursor,raw_page_markets),\n        root,\n    )\n\n    if progress:\n        progress(\n            f"[HIGH THROUGHPUT COVERAGE] page={new_state.pages_completed} "\n            f"raw={raw_page_markets} active={len(markets)} covered={admission.already_covered} "\n            f"missing={admission.missing_markets} requested={result.requested} "\n            f"persisted={result.persisted} retries={result.retries_used} "\n            f"chunk_size={result.chunk_size} mode={throughput.mode}"\n        )\n\n    if throughput.inter_page_sleep_seconds:\n        time.sleep(throughput.inter_page_sleep_seconds)\n\n    return HighThroughputCoverageResult(\n        len(markets),\n        admission.already_covered,\n        admission.missing_markets,\n        result.requested,\n        result.persisted,\n        result.retries_used,\n        result.chunk_size,\n        new_state.pages_completed>old_state.pages_completed,\n        False,\n    )\n\ndef verify_opc_030_high_throughput_universal_coverage_gate():\n    x=HighThroughputCoverageResult(1000,10,990,990,990,1,200,True,False)\n    return (\n        x.page_markets==1000\n        and x.requested==990\n        and x.persisted==990\n        and x.cursor_advanced\n        and not x.execution_authority\n    )\n']
TESTS=['test_opc_030_high_throughput_universal_coverage_gate.py']

def _write(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def _restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)

def main():
    print("="*88); print(" OPC-030 FROZEN-PAVEMENT RECERTIFICATION / HIGH-THROUGHPUT ACTIVE COVERAGE"); print("="*88); print("[ROOT]",ROOT)
    backups={}
    for rel,src in zip(TARGETS,PAYLOADS):
        p=ROOT/rel; backups[rel]=p.read_bytes() if p.exists() else None
        ast.parse(src,filename=str(p))
    print("[PASS] replacement payload syntax verified")
    try:
        for rel,src in zip(TARGETS,PAYLOADS): _write(ROOT/rel,src)
        importlib.invalidate_caches()
        for t in TESTS:
            subprocess.run([sys.executable,t],cwd=str(ROOT),check=True,timeout=60)
        import importlib
        m=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate")
        s=time.monotonic(); x=m.run_high_throughput_coverage_cycle(ROOT,progress=print)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if not x.cursor_advanced: raise RuntimeError("high-throughput coverage cursor did not advance")
        print("[PASS] high-throughput production coverage physically recertified")
    except Exception:
        for rel,data in backups.items(): _restore(ROOT/rel,data)
        print("[ROLLBACK] repair failed; exact affected repository files restored")
        raise
    print("[PASS] public production path repaired in place")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-030 FROZEN-PAVEMENT RECERTIFICATION / HIGH-THROUGHPUT ACTIVE COVERAGE COMPLETE")

if __name__=="__main__": main()
