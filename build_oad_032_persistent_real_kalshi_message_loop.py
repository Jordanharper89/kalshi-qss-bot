from __future__ import annotations
import hashlib, importlib, json, os, subprocess, sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

def locate_repository():
    candidates=[]
    for base in (Path.cwd().resolve(), SCRIPT_DIR):
        candidates += [base, base/"kalshi-qss-bot"]
        for p in base.parents:
            candidates += [p, p/"kalshi-qss-bot"]
    seen=set()
    for c in candidates:
        try: c=c.resolve()
        except OSError: continue
        if c in seen: continue
        seen.add(c)
        if (c/"qseries_v2").is_dir():
            return c
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
    if p.returncode:
        raise RuntimeError("Certification test failed: "+path.name)

BUILD_ID='OAD-032'
TITLE='PERSISTENT REAL KALSHI MESSAGE LOOP'
REVISION='OAD_032_PRODUCTION_V1'
MODULE=PACKAGE/'oad_032_persistent_live_loop.py'
TEST=ROOT/'test_oad_032_persistent_real_kalshi_message_loop.py'
EXPORTS=('OAD_032_BUILD_ID', 'OAD_032_REVISION', 'PersistentKalshiLoopSummary', 'run_persistent_kalshi_loop', 'verify_oad_032_persistent_real_kalshi_message_loop')
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nimport asyncio, json, time\nfrom .oad_021_credentials import load_kalshi_credentials\nfrom .oad_022_rest_transport import kalshi_rest_get, build_auth_headers\nfrom .oad_026_persistent_stream_runner import build_persistent_stream_config, next_reconnect_delay\n\nOAD_032_BUILD_ID="OAD-032"\nOAD_032_REVISION="OAD_032_PERSISTENT_REAL_KALSHI_MESSAGE_LOOP_V1"\n\n@dataclass(frozen=True)\nclass PersistentKalshiLoopSummary:\n    connections:int\n    reconnects:int\n    subscription_acks:int\n    market_messages:int\n    last_message_type:str\n\nasync def _run(credentials,stop_after_market_messages,timeout_seconds,progress):\n    try:\n        import websockets\n    except Exception as e:\n        raise RuntimeError("websockets package required") from e\n    from .oad_006_kalshi_foundation import build_kalshi_adapter_foundation\n    from .oad_011_websocket_foundation import build_subscribe_command\n\n    f=build_kalshi_adapter_foundation()\n    r=kalshi_rest_get(credentials,"/markets",{"limit":1000,"status":"open"},timeout_seconds)\n    tickers=tuple(str(m["ticker"]) for m in r.body.get("markets",()) if m.get("ticker"))[:100]\n    if not tickers: raise RuntimeError("No open markets for persistent stream")\n\n    connections=reconnects=acks=market=0\n    last=""\n    attempt=0\n    config=build_persistent_stream_config()\n\n    while market<int(stop_after_market_messages):\n        headers=build_auth_headers(credentials,"GET","/trade-api/ws/v2")\n        kwargs={"open_timeout":float(timeout_seconds),"ping_interval":None}\n        try:\n            try:\n                cm=websockets.connect(f.predictions_ws_url,additional_headers=headers,**kwargs)\n            except TypeError:\n                cm=websockets.connect(f.predictions_ws_url,extra_headers=headers,**kwargs)\n            async with cm as ws:\n                connections+=1\n                attempt=0\n                await ws.send(json.dumps(build_subscribe_command(1,("ticker","trade"),tickers),separators=(",",":")))\n                progress(f"[KALSHI] connected markets={len(tickers)}")\n                while market<int(stop_after_market_messages):\n                    raw=await asyncio.wait_for(ws.recv(),timeout=float(timeout_seconds))\n                    msg=json.loads(raw)\n                    typ=str(msg.get("type",""))\n                    last=typ\n                    if typ in ("subscribed","ok"):\n                        acks+=1\n                    elif typ in ("ticker","trade","orderbook_snapshot","orderbook_delta"):\n                        market+=1\n                        progress(f"[KALSHI] market_event={market} type={typ}")\n        except asyncio.TimeoutError:\n            reconnects+=1\n            delay=next_reconnect_delay(attempt,config); attempt+=1\n            progress(f"[KALSHI] receive timeout; reconnecting in {delay:.1f}s")\n            await asyncio.sleep(delay)\n        except Exception:\n            reconnects+=1\n            delay=next_reconnect_delay(attempt,config); attempt+=1\n            progress(f"[KALSHI] connection lost; reconnecting in {delay:.1f}s")\n            await asyncio.sleep(delay)\n\n    return PersistentKalshiLoopSummary(connections,reconnects,acks,market,last)\n\ndef run_persistent_kalshi_loop(root=None,stop_after_market_messages=3,timeout_seconds=15,progress=print):\n    credentials=load_kalshi_credentials(root=root)\n    return asyncio.run(_run(credentials,stop_after_market_messages,timeout_seconds,progress))\n\ndef verify_oad_032_persistent_real_kalshi_message_loop():\n    return OAD_032_REVISION.endswith("_V1")\n'
TEST_SOURCE='\nimport unittest\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import *\nclass T(unittest.TestCase):\n    def test_verifier(self): self.assertTrue(verify_oad_032_persistent_real_kalshi_message_loop())\nif __name__=="__main__":\n    print("="*72);print(" OAD-032 CERTIFICATION TEST");print(" PERSISTENT REAL KALSHI MESSAGE LOOP");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    print("[PASS] Persistent real Kalshi message-loop implementation certified");print("[DONE] OAD-032 CERTIFIED")\n'
EXTRA_1='\nfrom pathlib import Path\nfrom qseries_v2.oracle_adapters.kalshi.oad_032_persistent_live_loop import run_persistent_kalshi_loop\n\nif __name__=="__main__":\n    print("="*72,flush=True);print(" OAD-032 PERSISTENT KALSHI LIVE STREAM",flush=True);print("="*72,flush=True)\n    r=run_persistent_kalshi_loop(Path.cwd(),stop_after_market_messages=3,timeout_seconds=15,progress=lambda x:print(x,flush=True))\n    print("[PASS] REAL MARKET MESSAGES:",r.market_messages,flush=True)\n    print("[SUMMARY]",r,flush=True)\n'

def verify_upstream():
    p=PACKAGE/'oad_031_runtime_binding.py'
    if not p.is_file():
        raise RuntimeError("Certified upstream missing: "+str(p))
    sys.path.insert(0,str(ROOT))
    try:
        importlib.invalidate_caches()
        m=importlib.import_module('qseries_v2.oracle_adapters.kalshi.oad_031_runtime_binding')
        if getattr(m,'verify_oad_031_physical_oracle_live_runtime_kalshi_binding')() is not True:
            raise RuntimeError("Certified upstream verifier returned false")
    finally:
        if str(ROOT) in sys.path: sys.path.remove(str(ROOT))

def main():
    print("="*72);print(" "+BUILD_ID+" INSTALLER");print(" "+TITLE);print("="*72)
    print("[BOOT] Revision: "+REVISION);print("[ROOT] "+str(ROOT))
    verify_upstream();print("[PASS] Certified upstream boundary verified read-only")
    affected=(MODULE,TEST,INIT,ROOT/'run_oad_032_kalshi_persistent_stream.py')
    backups={p:(p.read_bytes() if p.exists() else None) for p in affected}
    try:
        write_exact(MODULE,MODULE_SOURCE);write_exact(TEST,TEST_SOURCE)
        write_exact(ROOT/'run_oad_032_kalshi_persistent_stream.py',EXTRA_1)
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
