from __future__ import annotations
import asyncio,json,os,time,urllib.error,urllib.request
from pathlib import Path
import websockets
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

MRIYA="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
WSOL=c.WSOL
STATE=Path("runtime_state/qseries/qarb_clean_bot/mriya_dynamic_token_registry.json")
EXECUTION_AUTHORITY=False
READ_ONLY=True
RPC_GAP=float(os.getenv("QARB_DISCOVERY_RPC_GAP_SECONDS","0.80"))
BACKFILL_LIMIT=int(os.getenv("QARB_DISCOVERY_BACKFILL_LIMIT","20"))
MAX_RETRIES=int(os.getenv("QARB_DISCOVERY_RPC_RETRIES","5"))

def rpc(method,params,timeout=20):
    body=json.dumps({"jsonrpc":"2.0","id":1,"method":method,"params":params}).encode()
    req=urllib.request.Request(c.RPC,data=body,headers={"content-type":"application/json"})
    with urllib.request.urlopen(req,timeout=timeout) as r:j=json.loads(r.read().decode())
    if j.get("error"):raise RuntimeError("RPC "+json.dumps(j["error"],sort_keys=True))
    return j.get("result")

async def rpc_retry(method,params):
    delay=RPC_GAP
    for attempt in range(1,MAX_RETRIES+1):
        try:
            result=await asyncio.to_thread(rpc,method,params)
            await asyncio.sleep(RPC_GAP)
            return result
        except urllib.error.HTTPError as exc:
            if exc.code!=429 or attempt>=MAX_RETRIES:raise
            print("[RPC_429_BACKOFF] method=%s attempt=%d sleep=%.1fs"%(method,attempt,delay),flush=True)
            await asyncio.sleep(delay);delay=min(delay*2.0,8.0)
        except Exception:
            if attempt>=MAX_RETRIES:raise
            await asyncio.sleep(delay);delay=min(delay*2.0,8.0)

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

def ingest_tx(sig,tx,registry):
    if not tx:return 0
    now=time.time();seen=float(tx.get("blockTime") or now);slot=int(tx.get("slot") or 0);n=0
    for mint in tx_mints(tx):
        row=registry["tokens"].setdefault(mint,{"first_seen_epoch":seen,"last_seen_epoch":seen,"touches":0,"last_slot":0,"signatures":[]})
        row["first_seen_epoch"]=min(float(row["first_seen_epoch"]),seen)
        row["last_seen_epoch"]=max(float(row["last_seen_epoch"]),seen)
        row["touches"]=int(row.get("touches",0))+1;row["last_slot"]=max(int(row.get("last_slot",0)),slot)
        ss=row.setdefault("signatures",[])
        if sig not in ss:ss.insert(0,sig);del ss[8:]
        n+=1
    return n

async def fetch_and_ingest(sig,registry):
    tx=await rpc_retry("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":0}])
    return ingest_tx(sig,tx,registry)

async def paced_backfill():
    d=load();done=set(d.get("signatures") or [])
    rows=await rpc_retry("getSignaturesForAddress",[MRIYA,{"limit":BACKFILL_LIMIT,"commitment":"confirmed"}]) or []
    pending=[x.get("signature") for x in reversed(rows) if x.get("signature") and x.get("signature") not in done]
    print("[BACKFILL_PLAN] signatures=%d rpc_gap=%.2fs"%(len(pending),RPC_GAP),flush=True)
    good=0;touched=0
    for sig in pending:
        try:
            touched+=await fetch_and_ingest(sig,d);good+=1;done.add(sig)
        except Exception as exc:
            print("[BACKFILL_SKIP] sig=%s %s:%s"%(sig[:16],type(exc).__name__,str(exc)[:120]),flush=True)
    d["signatures"]=list(done)[-500:];d["updated_epoch"]=time.time();save(d)
    return {"new_signatures":good,"token_touches":touched,"tokens":len(d["tokens"])}

async def consumer(q,stop_at):
    processed=0
    while stop_at is None or time.monotonic()<stop_at or not q.empty():
        try:sig=await asyncio.wait_for(q.get(),timeout=.5)
        except asyncio.TimeoutError:continue
        d=load();done=set(d.get("signatures") or [])
        if sig in done:q.task_done();continue
        try:
            touched=await fetch_and_ingest(sig,d)
            ss=d.setdefault("signatures",[]);ss.append(sig);d["signatures"]=ss[-500:]
            d["updated_epoch"]=time.time();save(d);processed+=1
            print("[NEW_MRIYA_TX] sig=%s touched_tokens=%d registry=%d queue=%d"%(sig[:16],touched,len(d["tokens"]),q.qsize()),flush=True)
        except Exception as exc:
            print("[LIVE_TX_RETRY_LATER] sig=%s %s:%s"%(sig[:16],type(exc).__name__,str(exc)[:120]),flush=True)
        finally:q.task_done()
    return processed

async def serve(seconds=None):
    print("[QARB-043B] PACED CONTINUOUS MRIYA TOKEN DISCOVERY",flush=True)
    print("[PACER] rpc_gap=%.2fs backfill_limit=%d retries=%d"%(RPC_GAP,BACKFILL_LIMIT,MAX_RETRIES),flush=True)
    initial=await paced_backfill();print("[BACKFILL]",initial,flush=True)
    ws_url=os.getenv("SOLANA_WS_URL","").strip() or c.RPC.replace("https://","wss://",1).replace("http://","ws://",1)
    started=time.monotonic();stop_at=None if seconds is None else started+float(seconds);q=asyncio.Queue(maxsize=2000)
    worker=asyncio.create_task(consumer(q,stop_at));reconnect_delay=2.0;events=0
    try:
        while stop_at is None or time.monotonic()<stop_at:
            try:
                async with websockets.connect(ws_url,ping_interval=20,ping_timeout=20,max_size=4_000_000) as ws:
                    await ws.send(json.dumps({"jsonrpc":"2.0","id":43,"method":"logsSubscribe",
                        "params":[{"mentions":[MRIYA]},{"commitment":"confirmed"}]}))
                    sub=json.loads(await ws.recv());print("[WS_SUBSCRIBED]",sub.get("result"),flush=True);reconnect_delay=2.0
                    while stop_at is None or time.monotonic()<stop_at:
                        timeout=1.0 if stop_at is not None else None
                        try:raw=await asyncio.wait_for(ws.recv(),timeout=timeout)
                        except asyncio.TimeoutError:continue
                        msg=json.loads(raw)
                        if msg.get("method")!="logsNotification":continue
                        sig=(((msg.get("params") or {}).get("result") or {}).get("value") or {}).get("signature")
                        if not sig:continue
                        try:q.put_nowait(sig);events+=1
                        except asyncio.QueueFull:print("[DISCOVERY_QUEUE_FULL] dropping=%s"%sig[:16],flush=True)
            except Exception as exc:
                print("[DISCOVERY_RECONNECT] %s %s sleep=%.1fs"%(type(exc).__name__,str(exc)[:120],reconnect_delay),flush=True)
                await asyncio.sleep(reconnect_delay);reconnect_delay=min(reconnect_delay*2.0,15.0)
    finally:
        await q.join()
        if not worker.done():worker.cancel()
        try:await worker
        except BaseException:pass
    print("[DISCOVERY_DONE] ws_events=%d tokens=%d"%(events,len(load().get("tokens",{}))),flush=True)
    return load()

def main(argv=None):
    import argparse
    ap=argparse.ArgumentParser();ap.add_argument("--seconds",type=float,default=None);a=ap.parse_args(argv)
    print("[MODE] READ_ONLY=True execution_authority=FALSE",flush=True)
    return asyncio.run(serve(a.seconds))
if __name__=="__main__":main()
