from __future__ import annotations
import asyncio,json,os,time
from collections import Counter
from pathlib import Path
import websockets

SRC=Path("runtime_state/qseries/qarb_clean_bot/mriya_program_owned_pool_candidates.json")
OUT=Path("runtime_state/qseries/qarb_clean_bot/mriya_pool_live_update_probe.json")
RPC=os.getenv("SOLANA_RPC_URL","https://api.mainnet-beta.solana.com")
WS=os.getenv("SOLANA_WS_URL",RPC.replace("https://","wss://").replace("http://","ws://"))
SHARD=35

def chunks(xs,n=SHARD):return [xs[i:i+n] for i in range(0,len(xs),n)]

async def worker(rows,seconds,counter,seen):
    lookup={x["address"]:x for x in rows}
    async with websockets.connect(WS,ping_interval=20,ping_timeout=20,max_size=8_000_000) as ws:
        ids={}
        n=1
        for a in lookup:
            await ws.send(json.dumps({"jsonrpc":"2.0","id":n,"method":"accountSubscribe",
                "params":[a,{"encoding":"base64","commitment":"processed"}]}))
            ids[n]=a;n+=1
        submap={}
        armed=len(ids)
        deadline=time.monotonic()+seconds
        while time.monotonic()<deadline:
            try:m=json.loads(await asyncio.wait_for(ws.recv(),timeout=.5))
            except asyncio.TimeoutError:continue
            if "id" in m and "result" in m and m["id"] in ids:
                submap[m["result"]]=ids[m["id"]];continue
            if m.get("method")!="accountNotification":continue
            sid=(m.get("params") or {}).get("subscription");a=submap.get(sid)
            if not a:continue
            counter[a]+=1;seen[a]=time.time()
        return armed

async def probe(seconds=60,limit=80):
    if not SRC.is_file():raise SystemExit("[FAIL] run QARB-031 first")
    d=json.loads(SRC.read_text(encoding="utf-8"));rows=(d.get("rows") or [])[:int(limit)]
    counter=Counter();seen={};armed=await asyncio.gather(*(worker(s,float(seconds),counter,seen) for s in chunks(rows)))
    byvenue=Counter()
    for x in rows:
        if counter[x["address"]]>0:byvenue[x["program_name"]]+=1
    outrows=[]
    for x in rows:
        outrows.append({"address":x["address"],"program_name":x["program_name"],"mints":x.get("mints") or [],
                        "updates":counter[x["address"]],"live":counter[x["address"]]>0})
    payload={"accounts_tested":len(rows),"accounts_live":sum(x["live"] for x in outrows),
             "venue_live_accounts":dict(byvenue),"notifications":sum(counter.values()),
             "rows":outrows,"execution_authority":False}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8")
    return payload

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=60);ap.add_argument("--limit",type=int,default=80);a=ap.parse_args(argv)
    print("[QARB-032] MRIYA DEX STATE LIVE-UPDATE PROBE")
    print("[WS]",WS);print("[WINDOW]",a.seconds,"seconds")
    r=asyncio.run(probe(a.seconds,a.limit))
    print("[RESULT] tested=%d live=%d notifications=%d"%(r["accounts_tested"],r["accounts_live"],r["notifications"]))
    print("[LIVE_BY_VENUE]",json.dumps(r["venue_live_accounts"],sort_keys=True))
    for x in sorted(r["rows"],key=lambda z:-z["updates"])[:30]:
        print("[LIVE_STATE] venue=%s updates=%d live=%s account=%s mints=%s"%(
            x["program_name"],x["updates"],x["live"],x["address"][:16],[m[:10] for m in x["mints"]]))
    print("[REPORT]",OUT)
    print("[MODE] READ_ONLY=True execution_authority=FALSE")
