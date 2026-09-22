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

def update_init(marker,module,exports):
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    if marker in current:
        return
    block=marker+"\nfrom ."+module+" import (\n"+"".join("    "+x+",\n" for x in exports)+")\n"
    write_exact(INIT,current.rstrip()+("\n\n" if current.strip() else "")+block)

def run_test(path):
    p=subprocess.run([sys.executable,str(path)],cwd=str(ROOT))
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-054'
TITLE='CONTINUOUS FULL-UNIVERSE RUNTIME BINDING'
REVISION='OAD_054_PRODUCTION_V2'
MODULE=PACKAGE/'oad_054_continuous_runtime_binding.py'
TEST=ROOT/'test_oad_054_continuous_full_universe_runtime_binding.py'
EXPORTS=('OAD_054_BUILD_ID', 'OAD_054_REVISION', 'ContinuousRuntimeBinding', 'build_continuous_runtime_binding', 'verify_oad_054_continuous_full_universe_runtime_binding')
MODULE_SOURCE='from __future__ import annotations\nfrom dataclasses import dataclass\n\nOAD_054_BUILD_ID="OAD-054"\nOAD_054_REVISION="OAD_054_CONTINUOUS_FULL_UNIVERSE_RUNTIME_BINDING_V1"\n\n@dataclass(frozen=True)\nclass ContinuousRuntimeBinding:\n    fast_lane_child:str\n    inventory_child:str\n    orderbook_rotation_capability:bool\n    terminal_dependency:bool=False\n    execution_authority:bool=False\n\ndef build_continuous_runtime_binding():\n    return ContinuousRuntimeBinding(\n        "run_oad_054_kalshi_global_fast_lane.py",\n        "run_oad_053_background_universe_inventory.py",\n        True,\n        False,\n        False,\n    )\n\ndef verify_oad_054_continuous_full_universe_runtime_binding():\n    b=build_continuous_runtime_binding()\n    return b.orderbook_rotation_capability and not b.terminal_dependency and not b.execution_authority\n'
TEST_SOURCE='import unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_054_continuous_runtime_binding import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_054_continuous_full_universe_runtime_binding())\nif __name__=="__main__":\n    print("="*72);print(" OAD-054 CERTIFICATION TEST");print(" CONTINUOUS FULL-UNIVERSE RUNTIME BINDING");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Continuous fast-lane + background-inventory runtime binding certified")\n    print("[DONE] OAD-054 CERTIFIED")\n'
EXTRA_1='from __future__ import annotations\nfrom datetime import datetime,timezone\nfrom pathlib import Path\nimport asyncio,json,time\n\nfrom qseries_v2.oracle_adapters.kalshi.oad_021_credentials import load_kalshi_credentials\nfrom qseries_v2.oracle_adapters.kalshi.oad_022_rest_transport import build_auth_headers\nfrom qseries_v2.oracle_adapters.kalshi.oad_036_websocket_canonical_bridge import build_ola_canonical_observation_from_websocket\nfrom qseries_v2.oracle_adapters.kalshi.oad_037_ola_postgres_router_binding import (\n    build_ola_production_persistence_router,\n    persist_canonical_observation,\n)\nfrom qseries_v2.oracle_adapters.kalshi.oad_048_multi_partition_runtime import build_kalshi_subscription_command\n\nasync def run_forever(root):\n    import websockets\n    from qseries_v2.oracle_adapters.kalshi.oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n\n    credentials=load_kalshi_credentials(root=root)\n    router=build_ola_production_persistence_router(root)\n    foundation=build_kalshi_adapter_foundation()\n\n    reconnects=0\n    persisted=0\n\n    while True:\n        headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")\n        kwargs={\n            "open_timeout":15.0,\n            "ping_interval":20.0,\n            "ping_timeout":20.0,\n            "close_timeout":10.0,\n        }\n\n        try:\n            try:\n                cm=websockets.connect(\n                    foundation.predictions_ws_url,\n                    additional_headers=headers,\n                    **kwargs,\n                )\n            except TypeError:\n                cm=websockets.connect(\n                    foundation.predictions_ws_url,\n                    extra_headers=headers,\n                    **kwargs,\n                )\n\n            async with cm as ws:\n                await ws.send(json.dumps(\n                    build_kalshi_subscription_command(\n                        1,\n                        ("ticker","trade"),\n                        None,\n                    ),\n                    separators=(",",":"),\n                ))\n\n                print(\n                    f"[FAST LANE] CONNECTED coverage=ALL reconnects={reconnects}",\n                    flush=True,\n                )\n\n                async for raw_text in ws:\n                    raw=json.loads(raw_text)\n                    typ=str(raw.get("type",""))\n\n                    if typ in ("subscribed","ok"):\n                        print("[FAST LANE] subscription_ack",flush=True)\n                        continue\n\n                    if typ not in ("ticker","trade"):\n                        continue\n\n                    msg=raw.get("msg") or {}\n                    ticker=str(\n                        msg.get("market_ticker")\n                        or msg.get("ticker")\n                        or ""\n                    ).strip()\n\n                    now=datetime.now(timezone.utc)\n                    observation=build_ola_canonical_observation_from_websocket(\n                        raw,\n                        received_at=now,\n                        acquisition_batch_id=(\n                            f"batch.oad054.{persisted+1}."\n                            f"{now.strftime(\'%Y%m%dT%H%M%S%fZ\')}"\n                        ),\n                    )\n\n                    persist_canonical_observation(\n                        router,\n                        observation,\n                        routed_at=now,\n                    )\n\n                    persisted+=1\n                    print(\n                        f"[FAST PERSIST] event={persisted} "\n                        f"type={typ} ticker={ticker} "\n                        f"observation_id={observation.observation_id}",\n                        flush=True,\n                    )\n\n        except asyncio.CancelledError:\n            raise\n\n        except Exception as exc:\n            reconnects+=1\n            delay=min(30.0,2.0**min(reconnects-1,5))\n            print(\n                f"[FAST LANE] connection_failure={type(exc).__name__} "\n                f"reconnects={reconnects} reconnecting_in={delay:.1f}s",\n                flush=True,\n            )\n            await asyncio.sleep(delay)\n\ndef main():\n    root=Path.cwd()\n    print("="*72,flush=True)\n    print(" OAD-054 KALSHI GLOBAL FAST LANE - 24/7 UNBOUNDED",flush=True)\n    print("="*72,flush=True)\n    try:\n        return asyncio.run(run_forever(root))\n    except KeyboardInterrupt:\n        print("\\n[STOP] Global fast lane stopped by operator.",flush=True)\n        return 0\n\nif __name__=="__main__":\n    raise SystemExit(main())\n'


def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_053_background_universe_inventory')
        if getattr(m,'verify_oad_053_incremental_background_universe_inventory')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_054_kalshi_global_fast_lane.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_054_kalshi_global_fast_lane.py',EXTRA_1)

        update_init("# "+BUILD_ID+" exports",MODULE.stem,EXPORTS)
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        sys.path.insert(0,str(ROOT))
        try:
            importlib.invalidate_caches()
            name="qseries_v2.oracle_adapters.kalshi."+MODULE.stem
            sys.modules.pop(name,None)
            m=importlib.import_module(name)
            verifier=getattr(m,[x for x in EXPORTS if x.startswith("verify_")][-1])
            if verifier() is not True:
                raise RuntimeError("Production verifier returned false")
        finally:
            if str(ROOT) in sys.path:
                sys.path.remove(str(ROOT))
        run_test(TEST)

    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists(): p.unlink()
            else:
                p.write_bytes(old)
        print("[ROLLBACK] "+BUILD_ID+" installation failed; affected files restored")
        raise
    print("[PASS] Wrote: "+str(MODULE.relative_to(ROOT)))
    print("[PASS] Updated: "+str(INIT.relative_to(ROOT)))
    print("[PASS] Wrote: "+TEST.name)
    print("[DONE] "+BUILD_ID+" INSTALLATION AND CERTIFICATION COMPLETE")
if __name__=="__main__":
    main()
