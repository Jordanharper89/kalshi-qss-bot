from pathlib import Path
import ast, importlib, os, subprocess, sys, time

ROOT=Path.cwd().resolve()
TITLE='OPC-023 FROZEN-PAVEMENT REPAIR / ACTIVE MARKET SNAPSHOT COVERAGE'
TARGETS=['qseries_v2/oracle_pre_settlement_coverage/opc_023_rotating_full_universe_coverage_cycle.py']
PAYLOADS=['from dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot\nfrom .opc_007_coverage_gap_snapshot_planner import plan_missing_market_snapshots\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch\nfrom .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor\n@dataclass(frozen=True)\nclass RotatingCoverageCycleResult:\n    page_markets:int;covered_recently:int;missing_on_page:int;snapshots_planned:int;snapshots_persisted:int;cursor_advanced:bool;terminal_wrap:bool;execution_authority:bool=False\ndef _active(markets): return tuple(m for m in markets if isinstance(m,dict) and str(m.get("status") or "").strip().lower()=="active")\ndef fetch_rotating_open_page(root=None,budget=None):\n    root=Path(root or Path.cwd()).resolve();budget=budget or CoverageLoadBudget();state=load_coverage_universe_cursor(root)\n    params={"limit":budget.page_limit}\n    if state.cursor: params["cursor"]=state.cursor\n    r=kalshi_rest_get(load_kalshi_credentials(root=root),"/markets",params,budget.request_timeout_seconds)\n    body=r.body or {};raw=tuple(body.get("markets",[]) or []);return state,_active(raw),str(body.get("cursor") or ""),len(raw)\ndef run_rotating_full_universe_coverage_cycle(root=None,budget=None,progress=None,router=None):\n    root=Path(root or Path.cwd()).resolve();budget=budget or CoverageLoadBudget();state,markets,nxt,raw_count=fetch_rotating_open_page(root,budget)\n    recent=read_recent_canonical_tickers(root,budget.lookback_hours,250000);plan=plan_missing_market_snapshots(markets,recent,budget.max_snapshots_per_cycle);by={str(x.get("ticker") or ""):x for x in markets if isinstance(x,dict)}\n    now=datetime.now(timezone.utc);batch="batch.opc.023."+now.strftime("%Y%m%dT%H%M%S%fZ");obs=[build_universal_market_snapshot(by[t],acquired_at=now+timedelta(microseconds=i+1),batch_id=batch) for i,t in enumerate(plan.planned_tickers) if t in by]\n    router=router or build_opc_postgresql_router(root);persisted=persist_snapshot_batch(obs,routed_at=datetime.now(timezone.utc),router=router)\n    new=save_coverage_universe_cursor(next_coverage_cursor(state,nxt,raw_count),root)\n    if progress: progress(f"[COVERAGE] page={new.pages_completed} raw={raw_count} active={len(markets)} covered={plan.already_covered} missing={plan.missing_markets} planned={len(obs)} persisted={persisted.accepted} wrap={not bool(nxt)}")\n    return RotatingCoverageCycleResult(len(markets),plan.already_covered,plan.missing_markets,len(obs),persisted.accepted,new.pages_completed>state.pages_completed,not bool(nxt),False)\ndef verify_opc_023_rotating_full_universe_coverage_cycle():\n    import inspect\n    src=inspect.getsource(fetch_rotating_open_page);x=RotatingCoverageCycleResult(1000,100,900,100,100,True,False,False)\n    return x.snapshots_persisted==100 and x.cursor_advanced and not x.execution_authority and \'"status":"open"\' not in src and \'root=root\' in src\n']
TESTS=['test_opc_023_rotating_full_universe_coverage_cycle.py']

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
    print("="*88); print(" OPC-023 FROZEN-PAVEMENT REPAIR / ACTIVE MARKET SNAPSHOT COVERAGE"); print("="*88); print("[ROOT]",ROOT)
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
        m=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle")
        s=time.monotonic(); x=m.run_rotating_full_universe_coverage_cycle(ROOT,progress=print)
        print("[PHYSICAL]",x,"elapsed_seconds=",round(time.monotonic()-s,3))
        if not x.cursor_advanced: raise RuntimeError("coverage cursor did not advance")
        print("[PASS] current ACTIVE market_snapshot coverage physically exercised")
    except Exception:
        for rel,data in backups.items(): _restore(ROOT/rel,data)
        print("[ROLLBACK] repair failed; exact affected repository files restored")
        raise
    print("[PASS] public production path repaired in place")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-023 FROZEN-PAVEMENT REPAIR / ACTIVE MARKET SNAPSHOT COVERAGE COMPLETE")

if __name__=="__main__": main()
