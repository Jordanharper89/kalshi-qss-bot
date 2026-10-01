from pathlib import Path
import py_compile
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"six_dex_subscription_plan.py").is_file(): raise SystemExit("[FAIL] QARB-019 missing")
SRC=r"""
from __future__ import annotations
import asyncio,base64,json,os,time
from pathlib import Path
from time import perf_counter_ns
from .six_dex_subscription_plan import build,requests
from .native_provider_resolver import best

WS_URL=os.getenv("SOLANA_WS_URL","wss://api.mainnet-beta.solana.com")

async def run(root,seconds=15.0,max_accounts=256):
    import websockets
    subs=build(root)[:int(max_accounts)]
    req=requests(subs)
    by_id={i+1:s for i,s in enumerate(subs)}
    submap={}
    counts={};notifications=0;lat=[]
    if not req:
        return {"subscriptions":0,"notifications":0,"venues":{},"p99_dispatch_ms":None,
                "clmm_provider":bool(best(root,"RAYDIUM_CLMM")),
                "orca_provider":bool(best(root,"ORCA_WHIRLPOOL"))}
    started=time.monotonic()
    async with websockets.connect(WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000) as ws:
        for x in req: await ws.send(json.dumps(x,separators=(",",":")))
        while time.monotonic()-started<float(seconds):
            try: raw=await asyncio.wait_for(ws.recv(),timeout=min(1.0,max(.05,float(seconds)-(time.monotonic()-started))))
            except asyncio.TimeoutError: continue
            recv=perf_counter_ns();msg=json.loads(raw)
            if "id" in msg and isinstance(msg.get("result"),int):
                s=by_id.get(int(msg["id"]))
                if s: submap[int(msg["result"])]=s
                continue
            if msg.get("method")!="accountNotification": continue
            params=msg.get("params") or {};s=submap.get(params.get("subscription"))
            if not s: continue
            notifications+=1;counts[s.venue]=counts.get(s.venue,0)+1
            lat.append((perf_counter_ns()-recv)/1e6)
    lat.sort()
    p99=lat[min(len(lat)-1,int(len(lat)*.99))] if lat else None
    return {"subscriptions":len(req),"notifications":notifications,"venues":counts,"p99_dispatch_ms":p99,
            "clmm_provider":bool(best(root,"RAYDIUM_CLMM")),
            "orca_provider":bool(best(root,"ORCA_WHIRLPOOL"))}

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=15.0);ap.add_argument("--max-accounts",type=int,default=256)
    a=ap.parse_args(argv)
    print("[QARB-020] SIX-DEX LIVE STREAM PROBE",flush=True)
    print("[CONTRACT] processed accountSubscribe | hot dispatch target <=750ms",flush=True)
    r=asyncio.run(run(Path.cwd(),a.seconds,a.max_accounts))
    print("[RESULT] "+json.dumps(r,sort_keys=True),flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)
    return r
if __name__=="__main__": main()
"""
TEST=r"""
import asyncio,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_live_stream import *
class T(unittest.TestCase):
    def test_empty_plan_is_safe(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as td:
            Path(td,"runtime_state").mkdir()
            r=asyncio.run(run(td,0.01,8))
            self.assertEqual(r["subscriptions"],0);self.assertEqual(r["notifications"],0)
        print("[PASS] six-DEX live runtime safely handles zero certified accounts")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=SUB/"six_dex_live_stream.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_020_six_dex_live_stream_probe.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
RUN=ROOT/"run_qarb_020_six_dex_live_stream_probe.py"
RUN.write_text("from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_live_stream import main\nif __name__=='__main__': main()\n",encoding="utf-8");py_compile.compile(str(RUN),doraise=True)
print("[PASS] QARB-020 six-DEX live stream probe installed")
print("[LIVE] certified accounts -> processed accountSubscribe -> per-venue notification counts")
print("[TRUTH] reports whether CLMM/Orca native providers actually exist")
print("[MODE] execution_authority=FALSE")
