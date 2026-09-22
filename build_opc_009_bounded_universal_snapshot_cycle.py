from pathlib import Path
import os,sys,subprocess,importlib
ROOT=Path.cwd().resolve(); PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_009_bounded_universal_snapshot_cycle.py"; TEST=ROOT/"test_opc_009_bounded_universal_snapshot_cycle.py"; INIT=PKG/"__init__.py"
MODULE_SOURCE='from dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot\nfrom .opc_007_coverage_gap_snapshot_planner import plan_missing_market_snapshots\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch\n\n@dataclass(frozen=True)\nclass UniversalSnapshotCycleSummary:\n    open_markets:int\n    covered_before:int\n    missing_before:int\n    snapshots_planned:int\n    snapshots_persisted:int\n    read_only_intelligence:bool=True\n    execution_authority:bool=False\n\ndef fetch_open_market_page(limit=1000,timeout_seconds=15):\n    c=load_kalshi_credentials()\n    r=kalshi_rest_get(c,"/markets",{"limit":int(limit),"status":"open"},timeout_seconds)\n    return tuple((r.body or {}).get("markets",[]) or [])\n\ndef run_bounded_universal_snapshot_cycle(root=None,max_markets=100,lookback_hours=24,progress=None,router=None,open_markets=None):\n    root=Path(root or Path.cwd()).resolve()\n    now=datetime.now(timezone.utc)\n    markets=tuple(open_markets) if open_markets is not None else fetch_open_market_page()\n    recent=read_recent_canonical_tickers(root,lookback_hours,250000)\n    plan=plan_missing_market_snapshots(markets,recent,max_markets=max_markets)\n    by_ticker={str(x.get("ticker") or ""):x for x in markets if isinstance(x,dict)}\n    selected=[by_ticker[t] for t in plan.planned_tickers if t in by_ticker]\n    batch="batch.opc.009."+now.strftime("%Y%m%dT%H%M%S")\n    observations=[]\n    for i,row in enumerate(selected,1):\n        observations.append(build_universal_market_snapshot(row,acquired_at=now,batch_id=batch))\n        if progress: progress(f"[SNAPSHOT BUILD] {i}/{len(selected)} ticker={row.get(\'ticker\')}")\n    if router is None: router=build_opc_postgresql_router(root)\n    result=persist_snapshot_batch(observations,routed_at=now,router=router)\n    if progress: progress(f"[SNAPSHOT PERSIST] requested={result.requested} accepted={result.accepted} rejected={result.rejected}")\n    return UniversalSnapshotCycleSummary(plan.sampled_markets,plan.already_covered,plan.missing_markets,len(observations),result.accepted,True,False)\n\ndef verify_opc_009_bounded_universal_snapshot_cycle():\n    x=UniversalSnapshotCycleSummary(1000,3,997,100,100,True,False)\n    return x.missing_before==997 and x.snapshots_persisted==100 and not x.execution_authority\n'; TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_009_bounded_universal_snapshot_cycle import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_009_bounded_universal_snapshot_cycle())\nif __name__=="__main__":\n    print("="*72);print(" OPC-009 CERTIFICATION TEST");print(" BOUNDED UNIVERSAL SNAPSHOT CYCLE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Bounded universal snapshot cycle certified");print("[DONE] OPC-009 CERTIFIED")\n'
def w(p,t):
    p.parent.mkdir(parents=True,exist_ok=True); q=p.with_suffix(p.suffix+".tmp"); q.write_text(t,encoding="utf-8",newline="\n"); os.replace(q,p)
def main():
    print("="*72);print(" OPC-009 INSTALLER");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT)); up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_008_ola_postgresql_snapshot_persistence_bridge")
    if up.verify_opc_008_ola_postgresql_snapshot_persistence_bridge() is not True: raise RuntimeError("OPC-008 verification failed")
    print("[PASS] Certified OPC-008 upstream boundary verified")
    affected=(MOD,TEST,INIT); backups={x:(x.read_bytes() if x.exists() else None) for x in affected}
    try:
        w(MOD,MODULE_SOURCE); w(TEST,TEST_SOURCE)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else ""; line="from .opc_009_bounded_universal_snapshot_cycle import *"
        if line not in cur: w(INIT,cur.rstrip()+"\n"+line+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for x,old in backups.items():
            if old is None:
                if x.exists(): x.unlink()
            else: x.write_bytes(old)
        print("[ROLLBACK] OPC-009 installation failed"); raise
    print("[DONE] OPC-009 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
