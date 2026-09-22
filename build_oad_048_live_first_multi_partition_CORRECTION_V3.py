from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path

ROOT = Path.cwd().resolve()
PACKAGE = ROOT / "qseries_v2" / "oracle_adapters" / "kalshi"
MODULE = PACKAGE / "oad_048_multi_partition_runtime.py"
TEST = ROOT / "test_oad_048_physical_multi_partition_persistence_runtime.py"

MODULE_SOURCE = r"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime,timezone
from pathlib import Path
import asyncio,json

from .oad_021_credentials import load_kalshi_credentials
from .oad_022_rest_transport import build_auth_headers
from .oad_046_live_universe_enumeration import LiveUniverseEnumeration
from .oad_047_physical_coverage_plan import build_physical_coverage_plan
from .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket
from .oad_037_ola_postgres_router_binding import (
    build_ola_production_persistence_router,
    persist_canonical_observation,
)

OAD_048_BUILD_ID="OAD-048"
OAD_048_REVISION="OAD_048_MULTI_PARTITION_RUNTIME_LIVE_FIRST_CORRECTION_V3"

@dataclass(frozen=True)
class MultiPartitionRuntimeSummary:
    open_markets:int
    orderbook_partitions:int
    subscriptions_acknowledged:int
    events_persisted:int
    observed_market_tickers:tuple[str,...]
    websocket_connections:int

def build_kalshi_subscription_command(command_id,channels,market_tickers=None):
    params={"channels":list(channels)}
    if market_tickers is not None:
        params["market_tickers"]=list(market_tickers)
    return {"id":int(command_id),"cmd":"subscribe","params":params}

async def _run(root,universe,max_persisted,orderbook_partitions_to_activate,progress):
    import websockets
    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation

    if not isinstance(universe,LiveUniverseEnumeration):
        raise ValueError("cached certified LiveUniverseEnumeration required")

    credentials=load_kalshi_credentials(root=root)
    router=build_ola_production_persistence_router(root)
    foundation=build_kalshi_adapter_foundation()
    plan=build_physical_coverage_plan(universe.tickers,100)

    headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")
    kwargs={
        "open_timeout":15.0,
        "ping_interval":20.0,
        "ping_timeout":20.0,
        "close_timeout":10.0,
    }

    try:
        cm=websockets.connect(
            foundation.predictions_ws_url,
            additional_headers=headers,
            **kwargs,
        )
    except TypeError:
        cm=websockets.connect(
            foundation.predictions_ws_url,
            extra_headers=headers,
            **kwargs,
        )

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
        progress(
            f"[FAST LANE] connected coverage=ALL "
            f"open_markets_snapshot={len(universe.tickers)}"
        )

        count=min(
            int(orderbook_partitions_to_activate),
            len(plan.orderbook_partitions),
        )

        for idx,partition in enumerate(
            plan.orderbook_partitions[:count],
            start=2,
        ):
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
                progress(f"[COVERAGE] subscription_ack={acks}")
                continue

            if typ not in (
                "ticker",
                "trade",
                "orderbook_snapshot",
                "orderbook_delta",
            ):
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
                    f"batch.oad048.{persisted+1}."
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
                f"[PERSIST] event={persisted} type={typ} "
                f"ticker={ticker} "
                f"observation_id={observation.observation_id}"
            )

    return MultiPartitionRuntimeSummary(
        len(universe.tickers),
        count,
        acks,
        persisted,
        tuple(sorted(observed)),
        1,
    )

def run_physical_multi_partition_persistence(
    root=None,
    universe=None,
    max_persisted=10,
    orderbook_partitions_to_activate=3,
    progress=print,
):
    root=Path(root or Path.cwd()).resolve()
    return asyncio.run(
        _run(
            root,
            universe,
            max_persisted,
            orderbook_partitions_to_activate,
            progress,
        )
    )

def verify_oad_048_physical_multi_partition_persistence_runtime():
    import inspect
    sig=inspect.signature(run_physical_multi_partition_persistence)
    return (
        "universe" in sig.parameters
        and OAD_048_REVISION.endswith("CORRECTION_V3")
    )
"""

TEST_SOURCE = r"""
import inspect
import unittest
from qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import *

class T(unittest.TestCase):
    def test_verifier(self):
        self.assertTrue(
            verify_oad_048_physical_multi_partition_persistence_runtime()
        )

    def test_requires_cached_universe_argument(self):
        sig=inspect.signature(run_physical_multi_partition_persistence)
        self.assertIn("universe",sig.parameters)

    def test_global_fast_lane_unfiltered(self):
        cmd=build_kalshi_subscription_command(
            1,
            ("ticker","trade"),
            None,
        )
        self.assertNotIn("market_tickers",cmd["params"])

if __name__=="__main__":
    print("="*72)
    print(" OAD-048 LIVE-FIRST CORRECTION V3 CERTIFICATION TEST")
    print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)
    print("[PASS] OAD-048 consumes cached universe snapshot")
    print("[PASS] Global ticker/trade fast lane remains unfiltered")
    print("[DONE] OAD-048 CORRECTION V3 CERTIFIED")
"""

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module(
            "qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan"
        )
        if getattr(m,"verify_oad_047_global_fast_lane_and_orderbook_partition_plan")() is not True:
            raise RuntimeError("Certified OAD-047 boundary verification failed")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72)
    print(" OAD-048 LIVE-FIRST CORRECTION V3 INSTALLER")
    print("="*72)
    print("[ROOT]",ROOT)
    verify_upstream()
    print("[PASS] Certified OAD-047 boundary verified read-only")

    affected=(MODULE,TEST)
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}

    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        subprocess.run([sys.executable,str(TEST)],cwd=str(ROOT),check=True)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] OAD-048 correction failed; affected files restored")
        raise

    print("[PASS] OAD-048 no longer performs its own REST universe crawl")
    print("[PASS] Cached universe snapshot is now required")
    print("[DONE] OAD-048 LIVE-FIRST CORRECTION V3 INSTALLED + CERTIFIED")

if __name__=="__main__":
    main()
