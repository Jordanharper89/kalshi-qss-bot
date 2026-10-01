from __future__ import annotations
import asyncio,json,os,time
from pathlib import Path
from time import perf_counter_ns

from .six_dex_subscription_plan import build as build_subscriptions, requests as build_requests

WS_URL=os.getenv("SOLANA_WS_URL","wss://api.mainnet-beta.solana.com")
DEFAULT_SHARD_SIZE=int(os.getenv("QARB_WS_SHARD_SIZE","48"))
DEFAULT_SUBSCRIBE_DELAY_MS=float(os.getenv("QARB_WS_SUBSCRIBE_DELAY_MS","40"))
DEFAULT_STAGGER_SECONDS=float(os.getenv("QARB_WS_SHARD_STAGGER_SECONDS","2.25"))

def shard_subscriptions(subs,shard_size=DEFAULT_SHARD_SIZE):
    n=max(1,int(shard_size))
    return [subs[i:i+n] for i in range(0,len(subs),n)]

def aggregate(results):
    out={"subscriptions":0,"acks":0,"notifications":0,"venues":{},"connections":len(results),
         "successful_connections":0,"rate_limited_connections":0,"errors":[],"p99_dispatch_ms":None}
    lat=[]
    for r in results:
        out["subscriptions"]+=int(r.get("subscriptions",0))
        out["acks"]+=int(r.get("acks",0))
        out["notifications"]+=int(r.get("notifications",0))
        if r.get("connected"): out["successful_connections"]+=1
        if r.get("rate_limited"): out["rate_limited_connections"]+=1
        if r.get("error"): out["errors"].append(r["error"])
        for k,v in (r.get("venues") or {}).items():
            out["venues"][k]=out["venues"].get(k,0)+int(v)
        lat.extend(r.get("dispatch_ms") or [])
    if lat:
        lat.sort()
        out["p99_dispatch_ms"]=lat[min(len(lat)-1,int(len(lat)*.99))]
    return out

async def _connection_worker(index,subs,seconds,subscribe_delay_ms,stagger_seconds):
    import websockets
    await asyncio.sleep(max(0.0,float(index)*float(stagger_seconds)))
    result={"index":index,"subscriptions":len(subs),"acks":0,"notifications":0,"venues":{},
            "connected":False,"rate_limited":False,"error":None,"dispatch_ms":[]}
    if not subs:
        return result

    reqs=build_requests(subs)
    by_id={i+1:s for i,s in enumerate(subs)}
    submap={}
    started=time.monotonic()
    hard_deadline=started+float(seconds)

    try:
        async with websockets.connect(
            WS_URL,ping_interval=20,ping_timeout=20,close_timeout=3,max_size=8_000_000
        ) as ws:
            result["connected"]=True
            for req in reqs:
                if time.monotonic()>=hard_deadline:
                    break
                await ws.send(json.dumps(req,separators=(",",":")))
                if subscribe_delay_ms>0:
                    await asyncio.sleep(float(subscribe_delay_ms)/1000.0)

            while time.monotonic()<hard_deadline:
                timeout=min(1.0,max(.05,hard_deadline-time.monotonic()))
                try:
                    raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                except asyncio.TimeoutError:
                    continue
                recv_ns=perf_counter_ns()
                msg=json.loads(raw)
                if "id" in msg and isinstance(msg.get("result"),int):
                    s=by_id.get(int(msg["id"]))
                    if s:
                        submap[int(msg["result"])]=s
                        result["acks"]+=1
                    continue
                if msg.get("method")!="accountNotification":
                    continue
                params=msg.get("params") or {}
                s=submap.get(params.get("subscription"))
                if not s:
                    continue
                result["notifications"]+=1
                result["venues"][s.venue]=result["venues"].get(s.venue,0)+1
                result["dispatch_ms"].append((perf_counter_ns()-recv_ns)/1e6)
    except Exception as exc:
        text=f"{type(exc).__name__}: {exc}"
        result["error"]=text
        low=text.lower()
        if "1013" in low or "rate limit" in low or "too many subscriptions" in low:
            result["rate_limited"]=True
    return result

async def run(root,seconds=30.0,max_accounts=256,shard_size=DEFAULT_SHARD_SIZE,
              subscribe_delay_ms=DEFAULT_SUBSCRIBE_DELAY_MS,
              stagger_seconds=DEFAULT_STAGGER_SECONDS):
    all_subs=build_subscriptions(root)[:int(max_accounts)]
    shards=shard_subscriptions(all_subs,shard_size)
    if not shards:
        return {"subscriptions":0,"acks":0,"notifications":0,"venues":{},"connections":0,
                "successful_connections":0,"rate_limited_connections":0,"errors":[],
                "p99_dispatch_ms":None}

    tasks=[
        asyncio.create_task(_connection_worker(i,shard,float(seconds),float(subscribe_delay_ms),float(stagger_seconds)))
        for i,shard in enumerate(shards)
    ]
    results=await asyncio.gather(*tasks)
    return aggregate(results)

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser()
    ap.add_argument("--seconds",type=float,default=30.0)
    ap.add_argument("--max-accounts",type=int,default=256)
    ap.add_argument("--shard-size",type=int,default=DEFAULT_SHARD_SIZE)
    ap.add_argument("--subscribe-delay-ms",type=float,default=DEFAULT_SUBSCRIBE_DELAY_MS)
    ap.add_argument("--stagger-seconds",type=float,default=DEFAULT_STAGGER_SECONDS)
    a=ap.parse_args(argv)

    print("[QARB-020B] RATE-LIMIT-SAFE SHARDED SIX-DEX LIVE RUNTIME",flush=True)
    print("[WS] %s"%WS_URL,flush=True)
    print("[RATE_LIMIT] shard_size=%d subscribe_delay_ms=%.1f stagger_seconds=%.2f"%(
        a.shard_size,a.subscribe_delay_ms,a.stagger_seconds),flush=True)
    print("[CONTRACT] processed accountSubscribe | multiple connections | <=750ms hot-dispatch target",flush=True)
    r=asyncio.run(run(Path.cwd(),a.seconds,a.max_accounts,a.shard_size,a.subscribe_delay_ms,a.stagger_seconds))
    print("[RESULT] "+json.dumps(r,sort_keys=True),flush=True)
    if r["rate_limited_connections"]:
        print("[HOLD] rate limit still observed; lower --shard-size or raise --subscribe-delay-ms",flush=True)
    else:
        print("[PASS] no websocket subscription-rate-limit disconnect observed",flush=True)
    print("[MODE] scanner/handoff only execution_authority=FALSE",flush=True)
    return r

if __name__=="__main__":
    main()
