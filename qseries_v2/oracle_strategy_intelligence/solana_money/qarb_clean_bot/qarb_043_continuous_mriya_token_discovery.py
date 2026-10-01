from __future__ import annotations
import asyncio,json,os,time,urllib.request
from pathlib import Path
import websockets
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

MRIYA="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
WSOL=c.WSOL
STATE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_token_registry.json")
EXECUTION_AUTHORITY=False
READ_ONLY=True

def rpc(method,params,timeout=20):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(c.RPC,data=body,headers={"content-type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:j=json.loads(r.read().decode())
    if j.get("error"):raise RuntimeError("RPC "+json.dumps(j["error"],sort_keys=True))
    return j.get("result")

def load():
    if not STATE.is_file():return {"tokens":{},"signatures":[]}
    try:return json.loads(STATE.read_text(encoding="utf-8"))
    except Exception:return {"tokens":{},"signatures":[]}

def save(d):
    STATE.parent.mkdir(parents=True,exist_ok=True)
    tmp=STATE.with_name(STATE.name+".%d.tmp"%os.getpid())
    tmp.write_text(json.dumps(d,indent=2,sort_keys=True),encoding="utf-8");os.replace(tmp,STATE)

def tx_mints(tx):
    meta=(tx or {}).get("meta") or {};out=set()
    for k in ("preTokenBalances","postTokenBalances"):
        for b in meta.get(k) or []:
            m=b.get("mint")
            if m and m!=WSOL:out.add(m)
    return sorted(out)

def ingest_signature(sig,registry):
    tx=rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
    if not tx:return 0
    now=time.time();seen=float(tx.get("blockTime") or now);slot=int(tx.get("slot") or 0)
    n=0
    for mint in tx_mints(tx):
        row=registry["tokens"].setdefault(mint,{"first_seen_epoch":seen,"last_seen_epoch":seen,"touches":0,"last_slot":0,"signatures":[]})
        row["first_seen_epoch"]=min(float(row["first_seen_epoch"]),seen)
        row["last_seen_epoch"]=max(float(row["last_seen_epoch"]),seen)
        row["touches"]=int(row.get("touches",0))+1;row["last_slot"]=max(int(row.get("last_slot",0)),slot)
        ss=row.setdefault("signatures",[])
        if sig not in ss:ss.insert(0,sig);del ss[8:]
        n+=1
    return n

def refresh_once(limit=40):
    d=load();done=set(d.get("signatures") or [])
    rows=rpc("getSignaturesForAddress",[MRIYA,{"limit":int(limit),"commitment":"confirmed"}]) or []
    new=0;touched=0
    for x in reversed(rows):
        sig=x.get("signature")
        if not sig or sig in done:continue
        try:touched+=ingest_signature(sig,d);new+=1;done.add(sig)
        except Exception as exc:print("[DISCOVERY_TX_SKIP]",type(exc).__name__,str(exc)[:160],flush=True)
    d["signatures"]=list(done)[-500:];d["updated_epoch"]=time.time();save(d)
    return {"new_signatures":new,"token_touches":touched,"tokens":len(d["tokens"])}

async def serve(seconds=None):
    initial=refresh_once()
    print("[QARB-043] CONTINUOUS MRIYA TOKEN DISCOVERY",flush=True)
    print("[BACKFILL]",initial,flush=True)
    ws_url=os.getenv("SOLANA_WS_URL","").strip() or c.RPC.replace("https://","wss://",1).replace("http://","ws://",1)
    started=time.monotonic();events=0
    while seconds is None or time.monotonic()-started<float(seconds):
        try:
            async with websockets.connect(ws_url,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
                await ws.send(json.dumps({"jsonrpc":"2.0","id":43,"method":"logsSubscribe",
                    "params":[{"mentions":[MRIYA]},{"commitment":"confirmed"}]}))
                sub=json.loads(await ws.recv())
                print("[WS_SUBSCRIBED]",sub.get("result"),flush=True)
                while seconds is None or time.monotonic()-started<float(seconds):
                    timeout=1.0 if seconds is not None else None
                    try:raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                    except asyncio.TimeoutError:continue
                    msg=json.loads(raw)
                    if msg.get("method")!="logsNotification":continue
                    sig=(((msg.get("params") or {}).get("result") or {}).get("value") or {}).get("signature")
                    if not sig:continue
                    d=load()
                    if sig in set(d.get("signatures") or []):continue
                    try:
                        touched=ingest_signature(sig,d);events+=1
                        ss=d.setdefault("signatures",[]);ss.append(sig);d["signatures"]=ss[-500:]
                        d["updated_epoch"]=time.time();save(d)
                        print("[NEW_MRIYA_TX] sig=%s touched_tokens=%d registry=%d"%(sig[:16],touched,len(d["tokens"])),flush=True)
                    except Exception as exc:print("[DISCOVERY_TX_SKIP]",type(exc).__name__,str(exc)[:160],flush=True)
        except Exception as exc:
            print("[DISCOVERY_RECONNECT]",type(exc).__name__,str(exc)[:160],flush=True);await asyncio.sleep(1.0)
    print("[DISCOVERY_DONE] ws_events=%d tokens=%d"%(events,len(load().get("tokens",{}))),flush=True)
    return load()

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    print("[MODE] READ_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(serve(a.seconds))
if __name__=="__main__":main()
