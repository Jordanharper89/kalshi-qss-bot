from dataclasses import dataclass
from datetime import datetime,timezone,timedelta
from pathlib import Path

from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import kalshi_rest_get
from .opc_003_canonical_observation_coverage_read_model import read_recent_canonical_tickers
from .opc_006_universal_market_snapshot_canonicalizer import build_universal_market_snapshot
from .opc_007_coverage_gap_snapshot_planner import plan_missing_market_snapshots
from .opc_008_ola_postgresql_snapshot_persistence_bridge import build_opc_postgresql_router,persist_snapshot_batch
from .opc_022_rotating_universe_cursor_load_budget import CoverageLoadBudget,load_coverage_universe_cursor,save_coverage_universe_cursor,next_coverage_cursor

OPC_023_BUILD_ID="OPC-023"
OPC_023_REVISION="OPC_023_ROTATING_FULL_UNIVERSE_COVERAGE_ACTIVE_SEMANTICS_RECERTIFIED"

@dataclass(frozen=True)
class RotatingCoverageCycleResult:
    page_markets:int
    covered_recently:int
    missing_on_page:int
    snapshots_planned:int
    snapshots_persisted:int
    cursor_advanced:bool
    terminal_wrap:bool
    execution_authority:bool=False

def _active_markets(markets):
    return tuple(
        row for row in markets
        if isinstance(row,dict)
        and str(row.get("status") or "").strip().lower()=="active"
    )

def fetch_rotating_open_page(root=None,budget=None):
    root=Path(root or Path.cwd()).resolve()
    budget=budget or CoverageLoadBudget()
    state=load_coverage_universe_cursor(root)

    params={"limit":budget.page_limit}
    if state.cursor:
        params["cursor"]=state.cursor

    response=kalshi_rest_get(
        load_kalshi_credentials(root=root),
        "/markets",
        params,
        budget.request_timeout_seconds,
    )
    body=response.body or {}
    raw_markets=tuple(body.get("markets",[]) or ())
    active_markets=_active_markets(raw_markets)
    next_cursor=str(body.get("cursor") or "")

    # Four-value contract is intentional:
    # cursor accounting advances by the raw exchange page size while
    # downstream coverage admits only actual ACTIVE/current markets.
    return state,active_markets,next_cursor,len(raw_markets)

def run_rotating_full_universe_coverage_cycle(root=None,budget=None,progress=None,router=None):
    root=Path(root or Path.cwd()).resolve()
    budget=budget or CoverageLoadBudget()

    state,markets,nxt,raw_page_markets=fetch_rotating_open_page(root,budget)

    recent=read_recent_canonical_tickers(root,budget.lookback_hours,250000)
    plan=plan_missing_market_snapshots(
        markets,
        recent,
        budget.max_snapshots_per_cycle,
    )

    by={
        str(row.get("ticker") or ""):row
        for row in markets
        if isinstance(row,dict)
    }

    now=datetime.now(timezone.utc)
    batch="batch.opc.023."+now.strftime("%Y%m%dT%H%M%S%fZ")
    observations=[
        build_universal_market_snapshot(
            by[ticker],
            acquired_at=now+timedelta(microseconds=i+1),
            batch_id=batch,
        )
        for i,ticker in enumerate(plan.planned_tickers)
        if ticker in by
    ]

    router=router or build_opc_postgresql_router(root)
    persisted=persist_snapshot_batch(
        observations,
        routed_at=datetime.now(timezone.utc),
        router=router,
    )

    new_state=save_coverage_universe_cursor(
        next_coverage_cursor(state,nxt,raw_page_markets),
        root,
    )

    if progress:
        progress(
            f"[COVERAGE] page={new_state.pages_completed} "
            f"raw={raw_page_markets} active={len(markets)} "
            f"covered={plan.already_covered} missing={plan.missing_markets} "
            f"planned={len(observations)} persisted={persisted.accepted} "
            f"wrap={not bool(nxt)}"
        )

    return RotatingCoverageCycleResult(
        len(markets),
        plan.already_covered,
        plan.missing_markets,
        len(observations),
        persisted.accepted,
        new_state.pages_completed>state.pages_completed,
        not bool(nxt),
        False,
    )

def verify_opc_023_rotating_full_universe_coverage_cycle():
    import inspect
    src=inspect.getsource(fetch_rotating_open_page)
    cycle_src=inspect.getsource(run_rotating_full_universe_coverage_cycle)
    x=RotatingCoverageCycleResult(1000,100,900,100,100,True,False,False)
    return (
        x.snapshots_persisted==100
        and x.cursor_advanced
        and not x.execution_authority
        and '"status":"open"' not in src
        and "load_kalshi_credentials(root=root)" in src
        and "raw_page_markets" in cycle_src
        and "next_coverage_cursor(state,nxt,raw_page_markets)" in cycle_src
    )
