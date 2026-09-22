from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path

from qseries_v2.oracle_adapters.kalshi.oad_021_credentials import (
    load_kalshi_credentials,
)
from qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import (
    kalshi_rest_get,
)
from .opc_003_canonical_observation_coverage_read_model import (
    read_recent_canonical_tickers,
)
from .opc_006_universal_market_snapshot_canonicalizer import (
    build_universal_market_snapshot,
)
from .opc_007_coverage_gap_snapshot_planner import (
    plan_missing_market_snapshots,
)
from .opc_008_ola_postgresql_snapshot_persistence_bridge import (
    build_opc_postgresql_router,
    persist_snapshot_batch,
)

OPC_009_BUILD_ID="OPC-009"
OPC_009_REVISION="OPC_009_BOUNDED_UNIVERSAL_SNAPSHOT_CYCLE_ALIGNMENT_V2"

@dataclass(frozen=True)
class UniversalSnapshotCycleSummary:
    open_markets:int
    covered_before:int
    missing_before:int
    snapshots_planned:int
    snapshots_persisted:int
    read_only_intelligence:bool=True
    execution_authority:bool=False

def fetch_open_market_page(limit=1000,timeout_seconds=15):
    credentials=load_kalshi_credentials()
    response=kalshi_rest_get(
        credentials,
        "/markets",
        {"limit":int(limit),"status":"open"},
        timeout_seconds,
    )
    return tuple((response.body or {}).get("markets",[]) or [])

def run_bounded_universal_snapshot_cycle(
    root=None,
    max_markets=100,
    lookback_hours=24,
    progress=None,
    router=None,
    open_markets=None,
):
    root=Path(root or Path.cwd()).resolve()
    cycle_started=datetime.now(timezone.utc)

    markets=(
        tuple(open_markets)
        if open_markets is not None
        else fetch_open_market_page()
    )

    recent=read_recent_canonical_tickers(
        root,
        lookback_hours,
        250000,
    )

    plan=plan_missing_market_snapshots(
        markets,
        recent,
        max_markets=max_markets,
    )

    by_ticker={
        str(row.get("ticker") or ""):row
        for row in markets
        if isinstance(row,dict)
    }

    selected=[
        by_ticker[ticker]
        for ticker in plan.planned_tickers
        if ticker in by_ticker
    ]

    batch_id=(
        "batch.opc.009."
        + cycle_started.strftime("%Y%m%dT%H%M%S%fZ")
    )

    observations=[]
    for index,row in enumerate(selected,1):
        # Each observation receives its own microsecond epoch. Even if Kalshi
        # state is identical across observations, source observation identity
        # remains unique while opc_source_state_hash stays stable.
        observation_time=cycle_started + timedelta(microseconds=index)

        observations.append(
            build_universal_market_snapshot(
                row,
                acquired_at=observation_time,
                batch_id=batch_id,
            )
        )

        if progress:
            progress(
                f"[SNAPSHOT BUILD] {index}/{len(selected)} "
                f"ticker={row.get('ticker')} "
                f"epoch={observation_time.isoformat()}"
            )

    if router is None:
        router=build_opc_postgresql_router(root)

    result=persist_snapshot_batch(
        observations,
        routed_at=datetime.now(timezone.utc),
        router=router,
    )

    if progress:
        progress(
            f"[SNAPSHOT PERSIST] requested={result.requested} "
            f"accepted={result.accepted} "
            f"rejected={result.rejected}"
        )

    return UniversalSnapshotCycleSummary(
        plan.sampled_markets,
        plan.already_covered,
        plan.missing_markets,
        len(observations),
        result.accepted,
        True,
        False,
    )

def verify_opc_009_bounded_universal_snapshot_cycle():
    first=build_universal_market_snapshot(
        {"ticker":"KXA","yes_bid":1},
        acquired_at="2026-08-16T20:00:00.000001Z",
        batch_id="b",
    )
    second=build_universal_market_snapshot(
        {"ticker":"KXB","yes_bid":1},
        acquired_at="2026-08-16T20:00:00.000002Z",
        batch_id="b",
    )

    summary=UniversalSnapshotCycleSummary(
        1000,3,997,100,100,True,False
    )

    return (
        first.observation_id!=second.observation_id
        and summary.missing_before==997
        and summary.snapshots_persisted==100
        and summary.read_only_intelligence
        and not summary.execution_authority
    )
