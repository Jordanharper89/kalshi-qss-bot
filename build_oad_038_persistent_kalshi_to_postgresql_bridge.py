from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR=Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(),SCRIPT_DIR):
        candidates += [base,base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p,p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir(): return c
    raise SystemExit("[ERROR] Could not locate current Q Series repository.")

ROOT=locate_repository()
PACKAGE=ROOT/"qseries_v2"/"oracle_adapters"/"kalshi"
INIT=PACKAGE/"__init__.py"

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
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

BUILD_ID='OAD-038'
TITLE='PERSISTENT KALSHI → OLA → POSTGRESQL BRIDGE'
REVISION='OAD_038_PRODUCTION_V1'
MODULE=PACKAGE/'oad_038_persistent_persistence_bridge.py'
TEST=ROOT/'test_oad_038_persistent_kalshi_to_postgresql_bridge.py'
EXPORTS=('OAD_038_BUILD_ID', 'OAD_038_REVISION', 'KalshiPersistenceBridgeSummary', 'run_kalshi_persistence_bridge', 'verify_oad_038_persistent_kalshi_to_postgresql_bridge')
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport asyncio,json\n\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get,build_auth_headers\nfrom .oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket\nfrom .oad_037_ola_postgres_router_binding import build_ola_production_persistence_router,persist_canonical_observation\n\nOAD_038_BUILD_ID="OAD-038"\nOAD_038_REVISION="OAD_038_PERSISTENT_KALSHI_TO_POSTGRESQL_BRIDGE_V1"\n\n@dataclass(frozen=True)\nclass KalshiPersistenceBridgeSummary:\n    websocket_connections:int\n    subscription_acks:int\n    market_events:int\n    persisted_observations:int\n    reconnects:int\n    last_observation_id:str\n\nasync def _run(root,max_persisted,progress):\n    try:\n        import websockets\n        from websockets.exceptions import ConnectionClosed\n    except Exception as e:\n        raise RuntimeError("websockets package required") from e\n\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n    from .oad_011_websocket_foundation import build_subscribe_command\n\n    creds=load_kalshi_credentials(root=root)\n    router=build_ola_production_persistence_router(root)\n    foundation=build_kalshi_adapter_foundation()\n    markets=kalshi_rest_get(creds,"/markets",{"limit":1000,"status":"open"},15)\n    tickers=tuple(str(m["ticker"]) for m in markets.body.get("markets",()) if m.get("ticker"))[:100]\n    if not tickers: raise RuntimeError("No open markets")\n\n    connections=acks=events=persisted=reconnects=0\n    last=""\n    while max_persisted is None or persisted<int(max_persisted):\n        headers=build_auth_headers(creds,"GET","/trade-api/ws/v2")\n        kwargs={"open_timeout":15.0,"ping_interval":20.0,"ping_timeout":20.0,"close_timeout":10.0}\n        try:\n            try: cm=websockets.connect(foundation.predictions_ws_url,additional_headers=headers,**kwargs)\n            except TypeError: cm=websockets.connect(foundation.predictions_ws_url,extra_headers=headers,**kwargs)\n            async with cm as ws:\n                connections+=1\n                await ws.send(json.dumps(build_subscribe_command(1,("ticker","trade"),tickers),separators=(",",":")))\n                progress(f"[BRIDGE] websocket_connected markets={len(tickers)}")\n                async for raw_text in ws:\n                    raw=json.loads(raw_text)\n                    typ=str(raw.get("type",""))\n                    if typ in ("subscribed","ok"):\n                        acks+=1\n                        progress(f"[BRIDGE] subscription_ack={acks}")\n                        continue\n                    if typ not in ("ticker","trade","orderbook_snapshot","orderbook_delta"):\n                        continue\n                    events+=1\n                    now=datetime.now(timezone.utc)\n                    batch_id=f"batch.oad038.{now.strftime(\'%Y%m%dT%H%M%S%fZ\')}.{events}"\n                    observation=build_ola_canonical_observation_from_websocket(\n                        raw,received_at=now,acquisition_batch_id=batch_id\n                    )\n                    evidence=persist_canonical_observation(router,observation,routed_at=now)\n                    persisted+=1\n                    last=observation.observation_id\n                    progress(f"[BRIDGE] event={events} type={typ} persisted={persisted} observation_id={last}")\n                    if max_persisted is not None and persisted>=int(max_persisted):\n                        break\n        except asyncio.CancelledError: raise\n        except KeyboardInterrupt: raise\n        except ConnectionClosed as exc:\n            reconnects+=1\n            progress(f"[BRIDGE] websocket_closed reconnects={reconnects}")\n            await asyncio.sleep(1)\n        except Exception as exc:\n            reconnects+=1\n            progress(f"[BRIDGE] connection_failure={type(exc).__name__} reconnects={reconnects}")\n            await asyncio.sleep(1)\n    return KalshiPersistenceBridgeSummary(connections,acks,events,persisted,reconnects,last)\n\ndef run_kalshi_persistence_bridge(root=None,max_persisted=None,progress=print):\n    root=Path(root or Path.cwd()).resolve()\n    return asyncio.run(_run(root,max_persisted,progress))\n\ndef verify_oad_038_persistent_kalshi_to_postgresql_bridge():\n    import inspect\n    return inspect.signature(run_kalshi_persistence_bridge).parameters["max_persisted"].default is None\n'
TEST_SOURCE='\nimport inspect,unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_038_persistent_kalshi_to_postgresql_bridge())\n    def test_unbounded(self): self.assertIsNone(inspect.signature(run_kalshi_persistence_bridge).parameters["max_persisted"].default)\nif __name__=="__main__":\n    print("="*72);print(" OAD-038 CERTIFICATION TEST");print(" PERSISTENT KALSHI → OLA → POSTGRESQL BRIDGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Persistent bridge is unbounded by default");print("[DONE] OAD-038 CERTIFIED")\n'
EXTRA_1='\nfrom pathlib import Path\nimport argparse\nfrom qseries_v2.oracle_adapters.kalshi.oad_038_persistent_persistence_bridge import run_kalshi_persistence_bridge\n\ndef main():\n    p=argparse.ArgumentParser()\n    p.add_argument("--max-persisted",type=int,default=None)\n    a=p.parse_args()\n    print("="*72,flush=True)\n    print(" OAD-038 KALSHI → OLA → POSTGRESQL LIVE BRIDGE",flush=True)\n    print("="*72,flush=True)\n    print("[MODE] "+("PRODUCTION 24/7 — UNBOUNDED" if a.max_persisted is None else f"DIAGNOSTIC — max_persisted={a.max_persisted}"),flush=True)\n    try:\n        r=run_kalshi_persistence_bridge(Path.cwd(),max_persisted=a.max_persisted,progress=lambda x:print(x,flush=True))\n        print("[SUMMARY]",r,flush=True)\n        return 0\n    except KeyboardInterrupt:\n        print("\\\\n[STOP] Kalshi persistence bridge stopped by operator.",flush=True)\n        return 0\nif __name__=="__main__": raise SystemExit(main())\n'

def verify_upstream():
    p=PACKAGE/'oad_037_ola_postgres_router_binding.py'
    if not p.is_file(): raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_037_ola_postgres_router_binding')
        if getattr(m,'verify_oad_037_ola_production_postgresql_router_binding')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_038_kalshi_persistence_bridge.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_038_kalshi_persistence_bridge.py',EXTRA_1)
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
    manifest={"build_id":BUILD_ID,"revision":REVISION,"module":str(MODULE.relative_to(ROOT)),
              "test":TEST.name,"files":{str(MODULE.relative_to(ROOT)):sha(MODULE),
              TEST.name:sha(TEST),str(INIT.relative_to(ROOT)):sha(INIT)}}
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[PASS] Deterministic install hash: "+digest)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__": main()
