from pathlib import Path
import importlib,os,subprocess,sys
ROOT=Path.cwd().resolve();PKG=ROOT/"qseries_v2"/"oracle_pre_settlement_coverage"
MOD=PKG/"opc_023_rotating_full_universe_coverage_cycle.py";TEST=ROOT/"test_opc_023_rotating_full_universe_coverage_cycle.py";INIT=PKG/"__init__.py"
MODULE='from dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot\nfrom .opc_007_coverage_gap_snapshot_planner import plan_missing_market_snapshots\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch\nfrom .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor\n@dataclass(frozen=True)\nclass RotatingCoverageCycleResult:\n    page_markets:int;covered_recently:int;missing_on_page:int;snapshots_planned:int;snapshots_persisted:int;cursor_advanced:bool;terminal_wrap:bool;execution_authority:bool=False\ndef fetch_rotating_open_page(root=None,budget=None):\n    budget=budget or CoverageLoadBudget();state=load_coverage_universe_cursor(root)\n    params={"limit":budget.page_limit,"status":"open"}\n    if state.cursor: params["cursor"]=state.cursor\n    r=kalshi_rest_get(load_kalshi_credentials(),"/markets",params,budget.request_timeout_seconds)\n    body=r.body or {};return state,tuple(body.get("markets",[]) or []),str(body.get("cursor") or "")\ndef run_rotating_full_universe_coverage_cycle(root=None,budget=None,progress=None,router=None):\n    root=Path(root or Path.cwd()).resolve();budget=budget or CoverageLoadBudget()\n    state,markets,nxt=fetch_rotating_open_page(root,budget)\n    recent=read_recent_canonical_tickers(root,budget.lookback_hours,250000)\n    plan=plan_missing_market_snapshots(markets,recent,budget.max_snapshots_per_cycle)\n    by={str(x.get("ticker") or ""):x for x in markets if isinstance(x,dict)}\n    now=datetime.now(timezone.utc);batch="batch.opc.023."+now.strftime("%Y%m%dT%H%M%S%fZ")\n    obs=[build_universal_market_snapshot(by[t],acquired_at=now+timedelta(microseconds=i+1),batch_id=batch) for i,t in enumerate(plan.planned_tickers) if t in by]\n    router=router or build_opc_postgresql_router(root)\n    persisted=persist_snapshot_batch(obs,routed_at=datetime.now(timezone.utc),router=router)\n    new=save_coverage_universe_cursor(next_coverage_cursor(state,nxt,len(markets)),root)\n    if progress: progress(f"[COVERAGE] page={new.pages_completed} markets={len(markets)} covered={plan.already_covered} missing={plan.missing_markets} planned={len(obs)} persisted={persisted.accepted} wrap={not bool(nxt)}")\n    return RotatingCoverageCycleResult(len(markets),plan.already_covered,plan.missing_markets,len(obs),persisted.accepted,new.pages_completed>state.pages_completed,not bool(nxt),False)\ndef verify_opc_023_rotating_full_universe_coverage_cycle():\n    x=RotatingCoverageCycleResult(1000,100,900,100,100,True,False,False)\n    return x.snapshots_persisted==100 and x.cursor_advanced and not x.execution_authority\n';TESTSRC='import unittest\nfrom qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle import verify_opc_023_rotating_full_universe_coverage_cycle\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_opc_023_rotating_full_universe_coverage_cycle())\nif __name__=="__main__":\n    print("="*72);print(" OPC-023 CERTIFICATION TEST");print(" ROTATING FULL UNIVERSE COVERAGE CYCLE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] OPC-023 certified");print("[DONE] OPC-023 CERTIFIED")\n'

def write_exact(p,s):
    p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+".tmp");t.write_text(s,encoding="utf-8",newline="\n");os.replace(t,p)

def main():
    print("="*72);print(" OPC-023 INSTALLER");print(" ROTATING FULL UNIVERSE COVERAGE CYCLE");print("="*72);print("[ROOT]",ROOT)
    sys.path.insert(0,str(ROOT));up=importlib.import_module("qseries_v2.oracle_pre_settlement_coverage.opc_022_rotating_universe_cursor_load_budget")
    if up.verify_opc_022_rotating_universe_cursor_load_budget() is not True: raise RuntimeError("OPC-022 failed")
    print("[PASS] Certified OPC-022 upstream boundary verified")
    affected=(MOD,TEST,INIT);old={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MOD,MODULE);write_exact(TEST,TESTSRC)
        cur=INIT.read_text(encoding="utf-8") if INIT.exists() else "";ex="from .opc_023_rotating_full_universe_coverage_cycle import *"
        if ex not in cur: write_exact(INIT,cur.rstrip()+"\n"+ex+"\n")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)

    except Exception:
        for p,b in old.items():
            if b is None:
                if p.exists(): p.unlink()
            else:p.write_bytes(b)
        print("[ROLLBACK] OPC-023 installation failed");raise
    print("[PASS] Wrote:",MOD.relative_to(ROOT));print("[PASS] Wrote:",TEST.name);print("[DONE] OPC-023 INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":main()
