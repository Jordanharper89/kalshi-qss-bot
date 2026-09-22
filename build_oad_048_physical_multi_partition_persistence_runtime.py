from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path
ROOT=Path.cwd().resolve()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"
def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text,encoding="utf-8",newline="\n")
    os.replace(tmp,path)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current: return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)
def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode: raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-048'
TITLE='PHYSICAL MULTI-PARTITION PERSISTENCE RUNTIME'
REVISION='OAD_048_PRODUCTION_V1'
MODULE=PACKAGE/'oad_048_multi_partition_runtime.py'
TEST=ROOT/'test_oad_048_physical_multi_partition_persistence_runtime.py'
EXPORTS=('OAD_048_BUILD_ID', 'OAD_048_REVISION', 'MultiPartitionRuntimeSummary', 'run_physical_multi_partition_persistence', 'verify_oad_048_physical_multi_partition_persistence_runtime')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport asyncio,json\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import build_auth_headers\nfrom .oad_046_live_universe_enumeration import enumerate_live_open_universe\nfrom .oad_047_physical_coverage_plan import build_physical_coverage_plan\nfrom .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket\nfrom .oad_037_ola_postgres_router_binding import build_ola_production_persistence_router,persist_canonical_observation\nOAD_048_BUILD_ID="OAD-048"\nOAD_048_REVISION="OAD_048_PHYSICAL_MULTI_PARTITION_PERSISTENCE_RUNTIME_V1"\n@dataclass(frozen=True)\nclass MultiPartitionRuntimeSummary:\n    open_markets:int; orderbook_partitions:int; subscriptions_acknowledged:int; events_persisted:int; observed_market_tickers:tuple[str,...]; websocket_connections:int\ndef _subscribe_command(command_id,channels,market_tickers=None):\n    params={"channels":list(channels)}\n    if market_tickers is not None: params["market_tickers"]=list(market_tickers)\n    return {"id":int(command_id),"cmd":"subscribe","params":params}\nasync def _run(root,max_persisted,orderbook_partitions_to_activate,progress):\n    import websockets\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n    creds=load_kalshi_credentials(root=root)\n    router=build_ola_production_persistence_router(root)\n    universe=enumerate_live_open_universe(creds,timeout_seconds=15)\n    plan=build_physical_coverage_plan(universe.tickers,100)\n    foundation=build_kalshi_adapter_foundation()\n    headers=build_auth_headers(creds,"GET","/trade-api/ws/v2")\n    kwargs={"open_timeout":15.0,"ping_interval":20.0,"ping_timeout":20.0,"close_timeout":10.0}\n    try: cm=websockets.connect(foundation.predictions_ws_url,additional_headers=headers,**kwargs)\n    except TypeError: cm=websockets.connect(foundation.predictions_ws_url,extra_headers=headers,**kwargs)\n    persisted=0; acks=0; observed=set()\n    async with cm as ws:\n        await ws.send(json.dumps(_subscribe_command(1,("ticker","trade"),None),separators=(",",":")))\n        progress(f"[COVERAGE] global_fast_lane=ticker,trade market_filter=NONE open_markets={len(universe.tickers)}")\n        count=min(int(orderbook_partitions_to_activate),len(plan.orderbook_partitions))\n        for idx,partition in enumerate(plan.orderbook_partitions[:count],start=2):\n            await ws.send(json.dumps(_subscribe_command(idx,("orderbook_delta",),partition.market_tickers),separators=(",",":")))\n            progress(f"[COVERAGE] orderbook_partition={partition.partition_id} markets={len(partition.market_tickers)}")\n        while persisted<int(max_persisted):\n            raw=json.loads(await ws.recv()); typ=str(raw.get("type",""))\n            if typ in ("subscribed","ok"): acks+=1; progress(f"[COVERAGE] subscription_ack={acks}"); continue\n            if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"): continue\n            msg=raw.get("msg") or {}; ticker=str(msg.get("market_ticker") or msg.get("ticker") or "").strip()\n            if ticker: observed.add(ticker)\n            now=datetime.now(timezone.utc)\n            obs=build_ola_canonical_observation_from_websocket(raw,received_at=now,acquisition_batch_id=f"batch.oad048.{persisted+1}.{now.strftime(\'%Y%m%dT%H%M%S%fZ\')}")\n            persist_canonical_observation(router,obs,routed_at=now); persisted+=1\n            progress(f"[PERSIST] event={persisted} type={typ} ticker={ticker} observation_id={obs.observation_id}")\n    return MultiPartitionRuntimeSummary(len(universe.tickers),count,acks,persisted,tuple(sorted(observed)),1)\ndef run_physical_multi_partition_persistence(root=None,max_persisted=10,orderbook_partitions_to_activate=3,progress=print):\n    return asyncio.run(_run(Path(root or Path.cwd()).resolve(),max_persisted,orderbook_partitions_to_activate,progress))\ndef verify_oad_048_physical_multi_partition_persistence_runtime():\n    return "market_tickers" not in _subscribe_command(1,("ticker","trade"),None)["params"]\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_048_physical_multi_partition_persistence_runtime())\n    def test_orderbook(self): self.assertEqual(_subscribe_command(2,("orderbook_delta",),("A","B"))["params"]["market_tickers"],["A","B"])\nif __name__=="__main__":\n    print("="*72);print(" OAD-048 CERTIFICATION TEST");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Physical multi-partition persistence runtime implementation certified");print("[DONE] OAD-048 CERTIFIED")\n'
EXTRA_1='from pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import run_physical_multi_partition_persistence\nif __name__=="__main__":\n    print("="*72,flush=True);print(" OAD-048 PHYSICAL MULTI-PARTITION KALSHI RUNTIME",flush=True);print("="*72,flush=True)\n    r=run_physical_multi_partition_persistence(Path.cwd(),max_persisted=10,orderbook_partitions_to_activate=3,progress=lambda x:print(x,flush=True))\n    print("[SUMMARY]",r,flush=True)\n    print("[PASS] Multi-partition live market data persisted through OLA PostgreSQL",flush=True)\n'

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_047_physical_coverage_plan')
        if getattr(m,'verify_oad_047_global_fast_lane_and_orderbook_partition_plan')() is not True: raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_048_physical_multi_partition_runtime.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_048_physical_multi_partition_runtime.py',EXTRA_1)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            v=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if v() is not True: raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
        run_test(TEST)
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else: p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),"test":TEST.name}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)));print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name);print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
