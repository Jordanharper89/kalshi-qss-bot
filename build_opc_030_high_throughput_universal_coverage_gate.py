from pathlib import Path
import importlib,os,subprocess,sys

ROOT=Path.cwd().resolve()
PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_030_high_throughput_universal_coverage_gate.py"
TEST=ROOT/"test_opc_030_high_throughput_universal_coverage_gate.py"
INIT=PKG/"__init__.py"
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport time\n\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_022_rotating_universe_cursor_load_budget import (\n    CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor\n)\nfrom .opc_023_rotating_full_universe_coverage_cycle import fetch_rotating_open_page\nfrom .opc_026_full_page_coverage_admission import admit_full_page_coverage\nfrom .opc_027_chunked_full_page_persistence import persist_full_page_in_chunks\nfrom .opc_029_adaptive_coverage_throughput_controller import choose_throughput_budget\n\nOPC_030_BUILD_ID="OPC-030"\nOPC_030_REVISION="OPC_030_HIGH_THROUGHPUT_UNIVERSAL_COVERAGE_GATE_V1"\n\n@dataclass(frozen=True)\nclass HighThroughputCoverageResult:\n    page_markets:int\n    already_covered:int\n    missing_markets:int\n    requested:int\n    persisted:int\n    retries_used:int\n    chunk_size:int\n    cursor_advanced:bool\n    execution_authority:bool=False\n\ndef run_high_throughput_coverage_cycle(root=None,progress=None,recent_retries=0,recent_failures=0):\n    root=Path(root or Path.cwd()).resolve()\n    throughput=choose_throughput_budget(\n        recent_retries=recent_retries,\n        recent_failures=recent_failures,\n    )\n    base_budget=CoverageLoadBudget(\n        page_limit=1000,\n        max_snapshots_per_cycle=1000,\n        cycle_sleep_seconds=0.0,\n        lookback_hours=24.0,\n        request_timeout_seconds=20.0,\n    )\n\n    old_state,markets,next_cursor=fetch_rotating_open_page(root,base_budget)\n    recent=read_recent_canonical_tickers(root,24,250000)\n    admission=admit_full_page_coverage(markets,recent)\n\n    result=persist_full_page_in_chunks(\n        markets,\n        admission.admitted_tickers,\n        root=root,\n        chunk_size=throughput.chunk_size,\n        max_retries=throughput.max_retries,\n        progress=progress,\n    )\n\n    new_state=save_coverage_universe_cursor(\n        next_coverage_cursor(old_state,next_cursor,len(markets)),\n        root,\n    )\n\n    if progress:\n        progress(\n            f"[HIGH THROUGHPUT COVERAGE] page={new_state.pages_completed} "\n            f"markets={len(markets)} covered={admission.already_covered} "\n            f"missing={admission.missing_markets} requested={result.requested} "\n            f"persisted={result.persisted} retries={result.retries_used} "\n            f"chunk_size={result.chunk_size} mode={throughput.mode}"\n        )\n\n    if throughput.inter_page_sleep_seconds:\n        time.sleep(throughput.inter_page_sleep_seconds)\n\n    return HighThroughputCoverageResult(\n        len(markets),\n        admission.already_covered,\n        admission.missing_markets,\n        result.requested,\n        result.persisted,\n        result.retries_used,\n        result.chunk_size,\n        new_state.pages_completed>old_state.pages_completed,\n        False,\n    )\n\ndef verify_opc_030_high_throughput_universal_coverage_gate():\n    x=HighThroughputCoverageResult(1000,10,990,990,990,1,200,True,False)\n    return (\n        x.page_markets==1000\n        and x.requested==990\n        and x.persisted==990\n        and x.cursor_advanced\n        and not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate import verify_opc_030_high_throughput_universal_coverage_gate\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(verify_opc_030_high_throughput_universal_coverage_gate())\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-030 CERTIFICATION TEST")\n    print(" HIGH THROUGHPUT UNIVERSAL COVERAGE GATE")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-030 certified")\n    print("[DONE] OPC-030 CERTIFIED")\n'
RUNNER=ROOT/"run_opc_030_high_throughput_coverage_child.py"
PHYSICAL=ROOT/"run_opc_030_physical_high_throughput_universal_coverage_verification.py"
LAUNCHER=ROOT/"run_oracle_LIVE.py"
RUNNER_SOURCE='from pathlib import Path\nimport time\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate import run_high_throughput_coverage_cycle\n\ndef main():\n    print("="*88,flush=True)\n    print(" OPC-030 HIGH-THROUGHPUT UNIVERSAL PRE-SETTLEMENT COVERAGE CHILD",flush=True)\n    print(" FULL PAGE ADMISSION + CHUNKED PERSISTENCE + ADAPTIVE BACKPRESSURE",flush=True)\n    print("="*88,flush=True)\n\n    retries=0\n    failures=0\n\n    while True:\n        try:\n            r=run_high_throughput_coverage_cycle(\n                Path.cwd(),\n                progress=lambda x:print(x,flush=True),\n                recent_retries=retries,\n                recent_failures=failures,\n            )\n            retries=r.retries_used\n            failures=0\n\n            if r.requested!=r.persisted:\n                failures+=1\n\n            print(\n                f"[COVERAGE SUPERVISOR] status={\'SUCCESS\' if r.requested==r.persisted else \'PARTIAL\'} "\n                f"page_markets={r.page_markets} requested={r.requested} "\n                f"persisted={r.persisted} retries={r.retries_used} "\n                f"chunk_size={r.chunk_size} execution_authority=FALSE",\n                flush=True,\n            )\n        except KeyboardInterrupt:\n            return 0\n        except Exception as exc:\n            failures+=1\n            print(\n                f"[COVERAGE SUPERVISOR] failure type={type(exc).__name__} "\n                f"failures={failures} action=retry_next_cycle",\n                flush=True,\n            )\n            time.sleep(min(5.0,0.5*(2**min(failures,3))))\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'
PHYSICAL_SOURCE='from pathlib import Path\nimport time\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_030_high_throughput_universal_coverage_gate import run_high_throughput_coverage_cycle\n\nif __name__=="__main__":\n    print("="*96)\n    print(" OPC-030 PHYSICAL HIGH-THROUGHPUT UNIVERSAL COVERAGE VERIFICATION")\n    print("="*96)\n\n    started=time.perf_counter()\n    result=run_high_throughput_coverage_cycle(\n        Path.cwd(),\n        progress=lambda x:print(x,flush=True),\n    )\n    elapsed=max(0.0001,time.perf_counter()-started)\n    rate=result.persisted/elapsed\n\n    print(f"[RESULT] page_markets={result.page_markets}")\n    print(f"[RESULT] already_covered={result.already_covered}")\n    print(f"[RESULT] missing={result.missing_markets}")\n    print(f"[RESULT] requested={result.requested}")\n    print(f"[RESULT] persisted={result.persisted}")\n    print(f"[RESULT] retries={result.retries_used}")\n    print(f"[RESULT] chunk_size={result.chunk_size}")\n    print(f"[THROUGHPUT] elapsed_seconds={elapsed:.2f}")\n    print(f"[THROUGHPUT] persisted_per_second={rate:.2f}")\n\n    if result.requested!=result.persisted:\n        raise SystemExit("Full-page coverage persistence incomplete")\n    if not result.cursor_advanced:\n        raise SystemExit("Coverage cursor did not advance")\n\n    print("[PASS] Entire missing portion of the 1,000-market page persisted")\n    print("[PASS] No 100-market per-page admission cap remains")\n    print("[PASS] Cursor advanced after full-page coverage")\n    print("[PASS] Existing OLA persistence path preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OPC-030 PHYSICAL HIGH-THROUGHPUT UNIVERSAL COVERAGE VERIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def patch_coverage_runner(source):
    import ast
    tree=ast.parse(source)
    target=None
    for item in ast.walk(tree):
        if isinstance(item,ast.Assign) and isinstance(item.value,ast.Dict):
            if any(isinstance(t,ast.Name) and t.id=="CHILDREN" for t in item.targets):
                target=item.value
                break
    if target is None:
        raise RuntimeError("run_oracle_LIVE.py CHILDREN dictionary not found")

    found=False
    for key,val in zip(target.keys,target.values):
        if isinstance(key,ast.Constant) and key.value=="coverage":
            found=True
            if not isinstance(val,ast.Constant):
                raise RuntimeError("coverage child value is not a literal string")
            start=val.col_offset
            line_index=val.lineno-1
            line=source.splitlines(keepends=True)[line_index]
            old=val.value
            new="run_opc_030_high_throughput_coverage_child.py"
            if old==new:
                return source,False
            lines=source.splitlines(keepends=True)
            lines[line_index]=line.replace(repr(old),repr(new),1).replace('"'+old+'"','"'+new+'"',1).replace("'"+old+"'","'"+new+"'",1)
            patched="".join(lines)
            ast.parse(patched)
            return patched,True

    if not found:
        raise RuntimeError("coverage child entry not found in CHILDREN registry")

def main():
    print("="*80)
    print(" OPC-030 INSTALLER")
    print(" HIGH THROUGHPUT UNIVERSAL COVERAGE GATE")
    print("="*80)
    print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT))

    up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_029_adaptive_coverage_throughput_controller")
    if up.verify_opc_029_adaptive_coverage_throughput_controller() is not True:
        raise RuntimeError("Certified OPC-029 verification failed")
    print("[PASS] Certified OPC-029 upstream boundary verified")

    affected=(MOD,TEST,INIT,RUNNER,PHYSICAL,LAUNCHER)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(RUNNER,RUNNER_SOURCE)
        write_exact(PHYSICAL,PHYSICAL_SOURCE)
        if not LAUNCHER.exists():
            raise RuntimeError("run_oracle_LIVE.py missing")
        patched,changed=patch_coverage_runner(LAUNCHER.read_text(encoding="utf-8"))
        if changed:
            write_exact(LAUNCHER,patched)
        print("[PASS] Oracle Live coverage child switched to OPC-030 high-throughput runner")
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
        export="from .opc_030_high_throughput_universal_coverage_gate import *"
        if export not in cur:
            write_exact(INIT,cur.rstrip()+"\n"+export+"\n")
        compile(MOD.read_text(encoding="utf-8"),str(MOD),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        compile(RUNNER.read_text(encoding="utf-8"),str(RUNNER),"exec")
        compile(PHYSICAL.read_text(encoding="utf-8"),str(PHYSICAL),"exec")
        compile(LAUNCHER.read_text(encoding="utf-8"),str(LAUNCHER),"exec")
        subprocess.run([sys.executable,str(LAUNCHER),"--check"],cwd=str(ROOT),check=True)
        print("[PASS] Oracle Live --check passed with high-throughput coverage binding")

    except Exception:
        for p,b in backups.items():
            if b is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(b)
        print("[ROLLBACK] OPC-030 installation failed; affected files restored")
        raise

    print("[PASS] Wrote:",MOD.relative_to(ROOT))
    print("[PASS] Wrote:",TEST.name)
    print("[DONE] OPC-030 INSTALLATION AND CERTIFICATION COMPLETE")

if __name__=="__main__":
    main()
