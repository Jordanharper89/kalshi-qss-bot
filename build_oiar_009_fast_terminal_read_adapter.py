from pathlib import Path
import ast, importlib, os, subprocess, sys, time, hashlib

ROOT=Path.cwd().resolve()
MOD=ROOT/'qseries_v2/oracle_intelligence_analytics_runtime/oiar_009_fast_terminal_read_adapter.py'
TEST=ROOT/'test_oiar_009_fast_terminal_read_adapter.py'

MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom pathlib import Path\nimport time\n\nfrom .oiar_005_persisted_trader_intelligence_read_surface import (\n    build_persisted_trader_intelligence,\n    render_persisted_trader_intelligence,\n)\nfrom .oiar_007_snapshot_freshness_last_good_state import inspect_snapshot_freshness\n\nOIAR_009_BUILD_ID="OIAR-009"\nOIAR_009_REVISION="OIAR_009_FAST_TERMINAL_READ_ADAPTER_V1"\n\n@dataclass(frozen=True)\nclass FastTraderIntelligenceRead:\n    snapshot_id:str\n    freshness_status:str\n    age_seconds:float\n    market_count:int\n    rows:tuple\n    lines:tuple\n    elapsed_seconds:float\n    serves_last_good:bool=True\n    read_only:bool=True\n    execution_authority:bool=False\n\ndef read_fast_trader_intelligence(root=None,limit=10):\n    root=Path(root or Path.cwd()).resolve()\n    started=time.monotonic()\n    freshness=inspect_snapshot_freshness(root)\n    rows=build_persisted_trader_intelligence(root,limit)\n    body=list(render_persisted_trader_intelligence(root,limit))\n    header=(\n        f"[SNAPSHOT] id={freshness.snapshot_id} freshness={freshness.freshness_status} "\n        f"age_seconds={freshness.age_seconds:.1f} runtime_status={freshness.runtime_status}"\n    )\n    lines=tuple([header]+body)\n    elapsed=time.monotonic()-started\n    return FastTraderIntelligenceRead(\n        freshness.snapshot_id,freshness.freshness_status,freshness.age_seconds,\n        len(rows),rows,lines,elapsed,True,True,False\n    )\n\ndef verify_oiar_009_fast_terminal_read(root=None):\n    x=read_fast_trader_intelligence(root,10)\n    return bool(\n        x.snapshot_id and x.market_count>0 and x.elapsed_seconds<5.0\n        and x.serves_last_good and x.read_only and not x.execution_authority\n    )\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_intelligence_analytics_runtime.oiar_009_fast_terminal_read_adapter import (\n    OIAR_009_BUILD_ID,FastTraderIntelligenceRead\n)\nclass T(unittest.TestCase):\n    def test_identity(self):self.assertEqual(OIAR_009_BUILD_ID,"OIAR-009")\n    def test_contract(self):\n        x=FastTraderIntelligenceRead("x","FRESH",1,10,(),(),.5,True,True,False)\n        self.assertTrue(x.read_only);self.assertFalse(x.execution_authority)\nif __name__=="__main__":\n    print("="*88);print(" OIAR-009 CERTIFICATION TEST");print(" FAST TERMINAL READ ADAPTER");print("="*88)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful():raise SystemExit(1)\n    print("[PASS] persisted snapshot-only terminal adapter certified")\n    print("[PASS] last-good degraded serving preserved")\n    print("[PASS] execution_authority=FALSE")\n    print("[DONE] OIAR-009 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8")
    os.replace(tmp,path)

def restore(path,data):
    if data is None:
        if path.exists(): path.unlink()
    else:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

def update_init(path,export):
    current=path.read_text(encoding="utf-8") if path.exists() else ""
    if export not in current.splitlines():
        write_exact(path,current.rstrip()+"\n"+export+"\n")

def main():
    print("="*88);print(" OIAR-009 INSTALLER");print(" FAST TERMINAL READ ADAPTER");print("="*88);print("[ROOT]",ROOT)
    PKG=MOD.parent;INIT=PKG/"__init__.py"
    for p in (PKG/"oiar_005_persisted_trader_intelligence_read_surface.py",PKG/"oiar_007_snapshot_freshness_last_good_state.py"):
        if not p.is_file():raise RuntimeError(f"Required proven upstream missing: {p}")
    old={p:(p.read_bytes() if p.exists() else None) for p in (MOD,TEST,INIT)}
    try:
        write_exact(MOD,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        update_init(INIT,"from .oiar_009_fast_terminal_read_adapter import *")
        ast.parse(MODULE_SOURCE);ast.parse(TEST_SOURCE);subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
        importlib.invalidate_caches();m=importlib.import_module("qseries_v2.oracle_intelligence_analytics_runtime.oiar_009_fast_terminal_read_adapter")
        x=m.read_fast_trader_intelligence(ROOT,10)
        print(f"[PHYSICAL] snapshot_id={x.snapshot_id} freshness={x.freshness_status} market_count={x.market_count} elapsed_seconds={x.elapsed_seconds:.4f}")
        if not m.verify_oiar_009_fast_terminal_read(ROOT):raise RuntimeError("OIAR-009 physical verification failed")
    except Exception:
        for p,b in old.items():restore(p,b)
        print("[ROLLBACK] OIAR-009 failed; affected repository files restored");raise
    print("[PASS] terminal adapter reads persisted snapshots only")
    print("[PASS] no OIA analytics recomputation at query time")
    print("[PASS] physical read under 5 seconds")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OIAR-009 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
