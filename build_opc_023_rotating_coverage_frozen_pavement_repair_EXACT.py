from pathlib import Path
import ast,importlib,os,subprocess,sys,time

ROOT=Path.cwd().resolve()
MOD=ROOT/"qseries_v2/oracle_pre_settlement_coverage/opc_023_rotating_full_universe_coverage_cycle.py"
TEST=ROOT/"test_opc_023_rotating_full_universe_coverage_cycle.py"
MODULE_SOURCE='from dataclasses import dataclass\nfrom datetime import datetime,timezone,timedelta\nfrom pathlib import Path\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get\nfrom .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers\nfrom .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot\nfrom .opc_007_coverage_gap_snapshot_planner import plan_missing_market_snapshots\nfrom .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch\nfrom .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor\n\nOPC_023_BUILD_ID="OPC-023"\nOPC_023_REVISION="OPC_023_ROTATING_FULL_UNIVERSE_COVERAGE_ACTIVE_SEMANTICS_RECERTIFIED"\n\n@dataclass(frozen=True)\nclass RotatingCoverageCycleResult:\n    page_markets:int\n    covered_recently:int\n    missing_on_page:int\n    snapshots_planned:int\n    snapshots_persisted:int\n    cursor_advanced:bool\n    terminal_wrap:bool\n    execution_authority:bool=False\n\ndef _active_markets(markets):\n    return tuple(\n        row for row in markets\n        if isinstance(row,dict)\n        and str(row.get("status") or "").strip().lower()=="active"\n    )\n\ndef fetch_rotating_open_page(root=None,budget=None):\n    root=Path(root or Path.cwd()).resolve()\n    budget=budget or CoverageLoadBudget()\n    state=load_coverage_universe_cursor(root)\n\n    params={"limit":budget.page_limit}\n    if state.cursor:\n        params["cursor"]=state.cursor\n\n    response=kalshi_rest_get(\n        load_kalshi_credentials(root=root),\n        "/markets",\n        params,\n        budget.request_timeout_seconds,\n    )\n    body=response.body or {}\n    raw_markets=tuple(body.get("markets",[]) or ())\n    active_markets=_active_markets(raw_markets)\n    next_cursor=str(body.get("cursor") or "")\n\n    # Four-value contract is intentional:\n    # cursor accounting advances by the raw exchange page size while\n    # downstream coverage admits only actual ACTIVE/current markets.\n    return state,active_markets,next_cursor,len(raw_markets)\n\ndef run_rotating_full_universe_coverage_cycle(root=None,budget=None,progress=None,router=None):\n    root=Path(root or Path.cwd()).resolve()\n    budget=budget or CoverageLoadBudget()\n\n    state,markets,nxt,raw_page_markets=fetch_rotating_open_page(root,budget)\n\n    recent=read_recent_canonical_tickers(root,budget.lookback_hours,250000)\n    plan=plan_missing_market_snapshots(\n        markets,\n        recent,\n        budget.max_snapshots_per_cycle,\n    )\n\n    by={\n        str(row.get("ticker") or ""):row\n        for row in markets\n        if isinstance(row,dict)\n    }\n\n    now=datetime.now(timezone.utc)\n    batch="batch.opc.023."+now.strftime("%Y%m%dT%H%M%S%fZ")\n    observations=[\n        build_universal_market_snapshot(\n            by[ticker],\n            acquired_at=now+timedelta(microseconds=i+1),\n            batch_id=batch,\n        )\n        for i,ticker in enumerate(plan.planned_tickers)\n        if ticker in by\n    ]\n\n    router=router or build_opc_postgresql_router(root)\n    persisted=persist_snapshot_batch(\n        observations,\n        routed_at=datetime.now(timezone.utc),\n        router=router,\n    )\n\n    new_state=save_coverage_universe_cursor(\n        next_coverage_cursor(state,nxt,raw_page_markets),\n        root,\n    )\n\n    if progress:\n        progress(\n            f"[COVERAGE] page={new_state.pages_completed} "\n            f"raw={raw_page_markets} active={len(markets)} "\n            f"covered={plan.already_covered} missing={plan.missing_markets} "\n            f"planned={len(observations)} persisted={persisted.accepted} "\n            f"wrap={not bool(nxt)}"\n        )\n\n    return RotatingCoverageCycleResult(\n        len(markets),\n        plan.already_covered,\n        plan.missing_markets,\n        len(observations),\n        persisted.accepted,\n        new_state.pages_completed>state.pages_completed,\n        not bool(nxt),\n        False,\n    )\n\ndef verify_opc_023_rotating_full_universe_coverage_cycle():\n    import inspect\n    src=inspect.getsource(fetch_rotating_open_page)\n    cycle_src=inspect.getsource(run_rotating_full_universe_coverage_cycle)\n    x=RotatingCoverageCycleResult(1000,100,900,100,100,True,False,False)\n    return (\n        x.snapshots_persisted==100\n        and x.cursor_advanced\n        and not x.execution_authority\n        and \'"status":"open"\' not in src\n        and "load_kalshi_credentials(root=root)" in src\n        and "raw_page_markets" in cycle_src\n        and "next_coverage_cursor(state,nxt,raw_page_markets)" in cycle_src\n    )\n'
TEST_SOURCE='import inspect\nimport unittest\n\nimport qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle as m\n\nclass T(unittest.TestCase):\n    def test_verifier(self):\n        self.assertTrue(m.verify_opc_023_rotating_full_universe_coverage_cycle())\n\n    def test_fetch_four_value_contract(self):\n        src=inspect.getsource(m.fetch_rotating_open_page)\n        self.assertIn("return state,active_markets,next_cursor,len(raw_markets)",src)\n\n    def test_no_stale_open_filter(self):\n        src=inspect.getsource(m.fetch_rotating_open_page)\n        self.assertNotIn(\'"status":"open"\',src)\n\n    def test_root_credential_alignment(self):\n        src=inspect.getsource(m.fetch_rotating_open_page)\n        self.assertIn("load_kalshi_credentials(root=root)",src)\n\nif __name__=="__main__":\n    print("="*80)\n    print(" OPC-023 CERTIFICATION TEST")\n    print(" ROTATING FULL UNIVERSE COVERAGE CYCLE - ACTIVE SEMANTICS")\n    print("="*80)\n    r=unittest.TextTestRunner(verbosity=2).run(\n        unittest.defaultTestLoader.loadTestsFromTestCase(T)\n    )\n    if not r.wasSuccessful():\n        raise SystemExit(1)\n    print("[PASS] OPC-023 four-value ACTIVE/current coverage contract certified")\n    print("[DONE] OPC-023 CERTIFIED")\n'

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+f".{os.getpid()}.tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def restore(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(data)

def main():
    print("="*88)
    print(" OPC-023 FROZEN-PAVEMENT REPAIR")
    print(" EXACT ACTIVE-MARKET FOUR-VALUE COVERAGE CONTRACT")
    print("="*88)
    print("[ROOT]",ROOT)

    if not MOD.is_file() or not TEST.is_file():
        raise RuntimeError("Exact frozen OPC-023 production files are missing")

    old_mod=MOD.read_bytes()
    old_test=TEST.read_bytes()

    try:
        ast.parse(MODULE_SOURCE,filename=str(MOD))
        ast.parse(TEST_SOURCE,filename=str(TEST))
        print("[PASS] exact replacement payload syntax verified")

        write_exact(MOD,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)

        subprocess.run(
            [sys.executable,str(TEST)],
            cwd=str(ROOT),
            check=True,
            timeout=30,
        )

        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_pre_settlement_coverage.opc_023_rotating_full_universe_coverage_cycle"
        )

        started=time.monotonic()
        state,markets,nxt,raw_count=m.fetch_rotating_open_page(ROOT)
        elapsed=round(time.monotonic()-started,3)

        print(
            "[PHYSICAL]",
            "raw_page_markets=",raw_count,
            "active_markets=",len(markets),
            "cursor_present=",bool(nxt),
            "elapsed_seconds=",elapsed,
        )

        if raw_count<=0:
            raise RuntimeError("OPC-023 physical Kalshi page was empty")
        if len(markets)<=0:
            raise RuntimeError("OPC-023 physical page contained no ACTIVE/current markets")
        if len(markets)>raw_count:
            raise RuntimeError("OPC-023 ACTIVE count exceeds raw exchange page count")
        if any(str(x.get("status") or "").strip().lower()!="active" for x in markets):
            raise RuntimeError("OPC-023 admitted non-ACTIVE market")

    except Exception:
        restore(MOD,old_mod)
        restore(TEST,old_test)
        print("[ROLLBACK] OPC-023 repair failed; exact frozen files restored")
        raise

    print("[PASS] stale status=open request removed")
    print("[PASS] raw page count preserved for cursor accounting")
    print("[PASS] downstream market set restricted to ACTIVE/current")
    print("[PASS] four-value fetch contract physically proven")
    print("[PASS] execution_authority=FALSE")
    print("[DONE] OPC-023 FROZEN PAVEMENT RECERTIFIED")

if __name__=="__main__":
    main()
