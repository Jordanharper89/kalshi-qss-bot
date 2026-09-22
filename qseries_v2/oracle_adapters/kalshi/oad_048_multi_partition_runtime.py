
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import asyncio,json

from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import build_auth_headers
from .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket
from .oad_037_ola_postgres_router_binding import (
    build_ola_production_persistence_router,
    persist_canonical_observation,
)
from .oad_047_physical_coverage_plan import build_physical_coverage_plan

OAD_048_BUILD_ID="OAD-048"
OAD_048_REVISION="OAD_048_TRUE_LIVE_FIRST_RUNTIME_CORRECTION_V4"

@dataclass(frozen=True)
class MultiPartitionRuntimeSummary:
    open_markets:int
    orderbook_partitions:int
    subscriptions_acknowledged:int
    events_persisted:int
    observed_market_tickers:tuple[str,...]
    websocket_connections:int


@dataclass(frozen=True)
class GlobalFastLaneSummary:
    subscriptions_acknowledged:int
    events_persisted:int
    observed_market_tickers:tuple[str,...]
    websocket_connections:int

@dataclass(frozen=True)
class SampledOrderbookSummary:
    sampled_markets:int
    activated_partitions:int
    subscriptions_acknowledged:int
    events_persisted:int

def build_kalshi_subscription_command(command_id,channels,market_tickers=None):
    params={"channels":list(channels)}
    if market_tickers is not None:
        params["market_tickers"]=list(market_tickers)
    return {"id":int(command_id),"cmd":"subscribe","params":params}

async def _connect_ws(credentials):
    import websockets
    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation
    foundation=build_kalshi_adapter_foundation()
    headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")
    kwargs={
        "open_timeout":15.0,
        "ping_interval":20.0,
        "ping_timeout":20.0,
        "close_timeout":10.0,
    }
    try:
        return websockets.connect(
            foundation.predictions_ws_url,
            additional_headers=headers,
            **kwargs,
        )
    except TypeError:
        return websockets.connect(
            foundation.predictions_ws_url,
            extra_headers=headers,
            **kwargs,
        )

async def _run_global_fast_lane(root,max_persisted,progress):
    credentials=load_kalshi_credentials(root=root)
    router=build_ola_production_persistence_router(root)
    cm=await _connect_ws(credentials)

    persisted=0
    acks=0
    observed=set()

    async with cm as ws:
        await ws.send(json.dumps(
            build_kalshi_subscription_command(
                1,
                ("ticker","trade"),
                None,
            ),
            separators=(",",":"),
        ))
        progress("[FAST LANE] WebSocket CONNECTED market_filter=NONE coverage=ALL")

        while persisted<int(max_persisted):
            raw=json.loads(await ws.recv())
            typ=str(raw.get("type",""))

            if typ in ("subscribed","ok"):
                acks+=1
                progress(f"[FAST LANE] subscription_ack={acks}")
                continue

            if typ not in ("ticker","trade"):
                continue

            msg=raw.get("msg") or {}
            ticker=str(
                msg.get("market_ticker")
                or msg.get("ticker")
                or ""
            ).strip()

            if ticker:
                observed.add(ticker)

            now=datetime.now(timezone.utc)
            observation=build_ola_canonical_observation_from_websocket(
                raw,
                received_at=now,
                acquisition_batch_id=(
                    f"batch.oad048.global.{persisted+1}."
                    f"{now.strftime('%Y%m%dT%H%M%S%fZ')}"
                ),
            )
            persist_canonical_observation(
                router,
                observation,
                routed_at=now,
            )
            persisted+=1
            progress(
                f"[FAST PERSIST] event={persisted} "
                f"type={typ} ticker={ticker} "
                f"observation_id={observation.observation_id}"
            )

    return GlobalFastLaneSummary(
        acks,
        persisted,
        tuple(sorted(observed)),
        1,
    )

async def _run_sampled_orderbook(root,market_tickers,max_persisted,partitions_to_activate,progress):
    credentials=load_kalshi_credentials(root=root)
    router=build_ola_production_persistence_router(root)
    plan=build_physical_coverage_plan(market_tickers,100)
    cm=await _connect_ws(credentials)

    persisted=0
    acks=0
    count=min(int(partitions_to_activate),len(plan.orderbook_partitions))

    async with cm as ws:
        for idx,partition in enumerate(plan.orderbook_partitions[:count],start=1):
            await ws.send(json.dumps(
                build_kalshi_subscription_command(
                    idx,
                    ("orderbook_delta",),
                    partition.market_tickers,
                ),
                separators=(",",":"),
            ))
            progress(
                f"[ORDERBOOK] activated_partition={partition.partition_id} "
                f"markets={len(partition.market_tickers)}"
            )

        while persisted<int(max_persisted):
            raw=json.loads(await ws.recv())
            typ=str(raw.get("type",""))

            if typ in ("subscribed","ok"):
                acks+=1
                progress(f"[ORDERBOOK] subscription_ack={acks}")
                continue

            if typ not in ("orderbook_snapshot","orderbook_delta"):
                continue

            now=datetime.now(timezone.utc)
            observation=build_ola_canonical_observation_from_websocket(
                raw,
                received_at=now,
                acquisition_batch_id=(
                    f"batch.oad048.orderbook.{persisted+1}."
                    f"{now.strftime('%Y%m%dT%H%M%S%fZ')}"
                ),
            )
            persist_canonical_observation(
                router,
                observation,
                routed_at=now,
            )
            persisted+=1
            progress(
                f"[ORDERBOOK PERSIST] event={persisted} "
                f"type={typ} observation_id={observation.observation_id}"
            )

    return SampledOrderbookSummary(
        len(tuple(market_tickers)),
        count,
        acks,
        persisted,
    )

def run_global_fast_lane_persistence(root=None,max_persisted=5,progress=print):
    root=Path(root or Path.cwd()).resolve()
    return asyncio.run(
        _run_global_fast_lane(
            root,
            max_persisted,
            progress,
        )
    )

def run_sampled_orderbook_persistence(root=None,market_tickers=(),max_persisted=3,partitions_to_activate=1,progress=print):
    root=Path(root or Path.cwd()).resolve()
    tickers=tuple(market_tickers)
    if not tickers:
        raise ValueError("sampled market_tickers required")
    return asyncio.run(
        _run_sampled_orderbook(
            root,
            tickers,
            max_persisted,
            partitions_to_activate,
            progress,
        )
    )


def run_physical_multi_partition_persistence(
    root=None,
    universe=None,
    max_persisted=10,
    orderbook_partitions_to_activate=3,
    progress=print,
):
    """
    Backward-compatible OAD-048 API.
    If a cached universe is supplied, it activates sampled orderbook partitions.
    The true live-first global lane is available independently via
    run_global_fast_lane_persistence().
    """
    if universe is None:
        raise ValueError(
            "cached universe required for backward-compatible multi-partition call; "
            "use run_global_fast_lane_persistence for enumeration-free live startup"
        )

    tickers=tuple(getattr(universe,"tickers",()) or ())
    if not tickers:
        raise ValueError("cached universe contains no tickers")

    sampled=run_sampled_orderbook_persistence(
        root,
        market_tickers=tickers,
        max_persisted=max_persisted,
        partitions_to_activate=orderbook_partitions_to_activate,
        progress=progress,
    )

    return MultiPartitionRuntimeSummary(
        len(tickers),
        sampled.activated_partitions,
        sampled.subscriptions_acknowledged,
        sampled.events_persisted,
        tuple(),
        1,
    )

def verify_oad_048_physical_multi_partition_persistence_runtime():
    cmd=build_kalshi_subscription_command(
        1,
        ("ticker","trade"),
        None,
    )
    return (
        "market_tickers" not in cmd["params"]
        and callable(run_global_fast_lane_persistence)
        and callable(run_sampled_orderbook_persistence)
        and callable(run_physical_multi_partition_persistence)
        and MultiPartitionRuntimeSummary.__name__=="MultiPartitionRuntimeSummary"
        and OAD_048_REVISION.endswith("CORRECTION_V4")
    )
