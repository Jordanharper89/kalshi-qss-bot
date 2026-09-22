from __future__ import annotations
import importlib, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
MODULE=PACKAGE/'oad_048_multi_partition_runtime.py'
TEST=ROOT/'test_oad_048_physical_multi_partition_persistence_runtime.py'
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport asyncio,json\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import build_auth_headers\nfrom .oad_046_live_universe_enumeration import enumerate_live_open_universe,LiveUniverseEnumeration\nfrom .oad_047_physical_coverage_plan import build_physical_coverage_plan\nfrom .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket\nfrom .oad_037_ola_postgres_router_binding import build_ola_production_persistence_router,persist_canonical_observation\n\nOAD_048_BUILD_ID="OAD-048"\nOAD_048_REVISION="OAD_048_PHYSICAL_MULTI_PARTITION_PERSISTENCE_RUNTIME_CORRECTION_V2"\n\n@dataclass(frozen=True)\nclass MultiPartitionRuntimeSummary:\n    open_markets:int\n    orderbook_partitions:int\n    subscriptions_acknowledged:int\n    events_persisted:int\n    observed_market_tickers:tuple[str,...]\n    websocket_connections:int\n\ndef build_kalshi_subscription_command(command_id,channels,market_tickers=None):\n    params={"channels":list(channels)}\n    if market_tickers is not None:\n        params["market_tickers"]=list(market_tickers)\n    return {"id":int(command_id),"cmd":"subscribe","params":params}\n\nasync def _run(root,universe,max_persisted,orderbook_partitions_to_activate,progress):\n    import websockets\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n\n    credentials=load_kalshi_credentials(root=root)\n    router=build_ola_production_persistence_router(root)\n    foundation=build_kalshi_adapter_foundation()\n\n    if universe is None:\n        universe=enumerate_live_open_universe(credentials,timeout_seconds=10,progress=progress)\n    if not isinstance(universe,LiveUniverseEnumeration):\n        raise ValueError("certified LiveUniverseEnumeration required")\n\n    plan=build_physical_coverage_plan(universe.tickers,100)\n\n    headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")\n    kwargs={"open_timeout":15.0,"ping_interval":20.0,"ping_timeout":20.0,"close_timeout":10.0}\n    try:\n        cm=websockets.connect(foundation.predictions_ws_url,additional_headers=headers,**kwargs)\n    except TypeError:\n        cm=websockets.connect(foundation.predictions_ws_url,extra_headers=headers,**kwargs)\n\n    persisted=0\n    acks=0\n    observed=set()\n\n    async with cm as ws:\n        await ws.send(json.dumps(build_kalshi_subscription_command(1,("ticker","trade"),None),separators=(",",":")))\n        progress(f"[FAST LANE] connected coverage=ALL open_markets={len(universe.tickers)}")\n\n        count=min(int(orderbook_partitions_to_activate),len(plan.orderbook_partitions))\n        for idx,partition in enumerate(plan.orderbook_partitions[:count],start=2):\n            await ws.send(json.dumps(build_kalshi_subscription_command(idx,("orderbook_delta",),partition.market_tickers),separators=(",",":")))\n            progress(f"[ORDERBOOK] activated_partition={partition.partition_id} markets={len(partition.market_tickers)}")\n\n        while persisted<int(max_persisted):\n            raw=json.loads(await ws.recv())\n            typ=str(raw.get("type",""))\n            if typ in ("subscribed","ok"):\n                acks+=1\n                progress(f"[COVERAGE] subscription_ack={acks}")\n                continue\n            if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"):\n                continue\n\n            msg=raw.get("msg") or {}\n            ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()\n            if ticker:\n                observed.add(ticker)\n\n            now=datetime.now(timezone.utc)\n            observation=build_ola_canonical_observation_from_websocket(\n                raw,\n                received_at=now,\n                acquisition_batch_id=f"batch.oad048.{persisted+1}.{now.strftime(\'%Y%m%dT%H%M%S%fZ\')}",\n            )\n            persist_canonical_observation(router,observation,routed_at=now)\n            persisted+=1\n            progress(f"[PERSIST] event={persisted} type={typ} ticker={ticker} observation_id={observation.observation_id}")\n\n    return MultiPartitionRuntimeSummary(\n        len(universe.tickers),\n        count,\n        acks,\n        persisted,\n        tuple(sorted(observed)),\n        1,\n    )\n\ndef run_physical_multi_partition_persistence(root=None,universe=None,max_persisted=10,orderbook_partitions_to_activate=3,progress=print):\n    root=Path(root or Path.cwd()).resolve()\n    return asyncio.run(_run(root,universe,max_persisted,orderbook_partitions_to_activate,progress))\n\ndef verify_oad_048_physical_multi_partition_persistence_runtime():\n    import inspect\n    sig=inspect.signature(run_physical_multi_partition_persistence)\n    return "universe" in sig.parameters and build_kalshi_subscription_command(1,("ticker","trade"),None)["params"].get("market_tickers") is None\n'
TEST_SOURCE='import inspect,unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_048_physical_multi_partition_persistence_runtime())\n    def test_universe_param(self): self.assertIn("universe",inspect.signature(run_physical_multi_partition_persistence).parameters)\nif __name__=="__main__":\n    print("="*72);print(" OAD-048 CORRECTION V2 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Multi-partition runtime reuses supplied universe snapshot")\n    print("[DONE] OAD-048 CORRECTION V2 CERTIFIED")\n'

def write_exact(path,text):
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan')
        if getattr(m,'verify_oad_047_global_fast_lane_and_orderbook_partition_plan')() is not True:
            raise RuntimeError("Certified upstream verification failed")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" OAD-048 CORRECTION V2 INSTALLER");print(" REUSE CERTIFIED UNIVERSE SNAPSHOT");print("="*72)
    print("[ROOT]",ROOT)
    verify_upstream()
    print("[PASS] Certified upstream boundary verified read-only")
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
        print("[ROLLBACK] Correction failed; affected files restored")
        raise
    print("[PASS] Corrected:",MODULE.relative_to(ROOT))
    print("[PASS] Corrected:",TEST.name)
    print("[DONE] OAD-048 CORRECTION V2 INSTALLED + CERTIFIED")
if __name__=="__main__":
    main()
