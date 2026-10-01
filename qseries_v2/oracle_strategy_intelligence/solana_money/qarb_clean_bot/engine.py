from __future__ import annotations
import argparse,json,math,os,time,urllib.error
from pathlib import Path
from statistics import median

from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c

REVISION="QARB_001_CLEAN_PROFIT_FIRST_ARB_BOT_V1"
MRIYA="MriyaNN8TMp6qRWjfr723PK7xgQK7yCt7Kg2v2PQu7X"
WSOL=c.WSOL
MIN_NET_BPS=float(os.getenv("QARB_MIN_NET_BPS","20"))
MAX_TOKENS=int(os.getenv("QARB_MAX_TOKENS","12"))
MAX_SLOT_SPREAD=int(os.getenv("QARB_MAX_SLOT_SPREAD","2"))
HOT_TTL=float(os.getenv("QARB_HOT_TTL","10"))
INTERVAL=float(os.getenv("QARB_INTERVAL","1.5"))
COARSE_SIZES=(0.005,0.010,0.025,0.050,0.100,0.180,0.280,0.500,0.900,1.100,1.400)
STRATEGIES=("PUMP_TO_METEORA","METEORA_TO_PUMP")
STATE_DIR=Path("runtime_state/qseries/qarb_clean_bot")
GAV_REGRESSION=(
    (0.005,0.000429809,859.62),
    (0.010,0.000859233,859.23),
    (0.025,0.002145190,858.08),
    (0.050,0.004280742,856.15),
)
_hot_cache={"at":0.0,"rows":[]}
_cross_cache={"at":0.0,"rows":[]}
CROSSLIST_TTL=float(os.getenv("QARB_CROSSLIST_TTL","20"))
DISCOVERY_BUDGET=int(os.getenv("QARB_DISCOVERY_BUDGET","48"))

def _rpc(method,params):
    return c.rpc(method,params)

def _slot():
    return int(_rpc("getSlot",[{"commitment":"confirmed"}]) or 0)

def _is_429(e):
    return isinstance(e,urllib.error.HTTPError) and getattr(e,"code",None)==429

def landing_cost_lamports():
    base=5000
    cu=int(os.getenv("QARB_CU_LIMIT","200000"))
    try:
        rows=_rpc("getRecentPrioritizationFees",[]) or []
        vals=sorted(int(x.get("prioritizationFee") or 0) for x in rows if isinstance(x,dict))
        if not vals:
            return base
        p75=vals[min(len(vals)-1,int((len(vals)-1)*0.75))]
        return base + (p75*cu+999999)//1_000_000
    except Exception:
        return base

def _tx_mints(tx):
    meta=(tx or {}).get("meta") or {}
    out=[];seen=set()
    for k in ("preTokenBalances","postTokenBalances"):
        for r in meta.get(k) or []:
            m=r.get("mint")
            if not m or m in (WSOL,getattr(c,"USDC",""),getattr(c,"USDT","")) or m in seen:
                continue
            seen.add(m);out.append(m)
    return out

def mriya_hot_tokens():
    now=time.time()
    if now-_hot_cache["at"]<HOT_TTL:
        return list(_hot_cache["rows"])
    rows=[]
    try:
        sigs=_rpc("getSignaturesForAddress",[MRIYA,{"limit":8,"commitment":"confirmed"}]) or []
        for rank,r in enumerate(sigs):
            if r.get("err") is not None or not r.get("signature"):
                continue
            try:
                tx=_rpc("getTransaction",[r["signature"],{
                    "encoding":"jsonParsed","commitment":"confirmed",
                    "maxSupportedTransactionVersion":0}])
            except Exception:
                continue
            bt=float((tx or {}).get("blockTime") or 0)
            age=max(0.0,now-bt) if bt else 999999.0
            for mint in _tx_mints(tx):
                rows.append({"token":mint,"age":age,"rank":rank})
    except Exception as e:
        print("[HOTSET_DEGRADED] %s: %s"%(type(e).__name__,e),flush=True)
        rows=[]
    best={}
    for r in rows:
        t=r["token"]
        if t not in best or (r["age"],r["rank"])<(best[t]["age"],best[t]["rank"]):
            best[t]=r
    ans=sorted(best.values(),key=lambda r:(r["age"],r["rank"]))
    _hot_cache["at"]=now;_hot_cache["rows"]=ans
    return list(ans)

def tape_candidates(root):
    try:
        return list(c.tape_candidates(root))
    except Exception as e:
        print("[TAPE_DEGRADED] %s: %s"%(type(e).__name__,e),flush=True)
        return []

def raw_candidate_universe(root):
    tape=tape_candidates(root)
    by_token={t:p for t,p in tape}
    out=[];seen=set()
    for h in mriya_hot_tokens():
        t=h["token"];p=by_token.get(t)
        if p is None:
            try:
                p=c.canonical_pump_pool(t)
            except Exception:
                p=None
        if p and t not in seen:
            out.append({"token":t,"pump_pool":p,"source":"MRIYA_HOT","age":h["age"]})
            seen.add(t)
    for t,p in tape:
        if t not in seen:
            out.append({"token":t,"pump_pool":p,"source":"LIVE_TAPE","age":None})
            seen.add(t)
    return out[:DISCOVERY_BUDGET]

def candidate_universe(root):
    now=time.time()
    if now-_cross_cache["at"]<CROSSLIST_TTL and _cross_cache["rows"]:
        return list(_cross_cache["rows"])[:MAX_TOKENS]

    raw=raw_candidate_universe(root)
    rows=[]
    failures={}
    for x in raw:
        if len(rows)>=MAX_TOKENS:
            break
        t=x["token"];p=x["pump_pool"]

        ok,why=exact_pool_ok(t,p)
        if not ok:
            failures[why]=failures.get(why,0)+1
            continue

        try:
            meta=c.discover_dlmm(t)
        except Exception as exc:
            key="HTTP_429" if _is_429(exc) else ("NO_DLMM_PAIR" if str(exc)=="NO_DLMM_PAIR" else type(exc).__name__)
            failures[key]=failures.get(key,0)+1
            if key=="HTTP_429":
                break
            continue

        if not isinstance(meta,dict) or not meta.get("address"):
            failures["BAD_DLMM_META"]=failures.get("BAD_DLMM_META",0)+1
            continue

        tx=meta.get("token_x");ty=meta.get("token_y")
        if WSOL not in (tx,ty):
            failures["DLMM_NOT_WSOL_PAIR"]=failures.get("DLMM_NOT_WSOL_PAIR",0)+1
            continue

        y=dict(x)
        y["meteora_pool"]=meta["address"]
        y["crosslisted"]=True
        rows.append(y)

        try:
            cache=getattr(c,"_DLMM_CACHE",None)
            if isinstance(cache,dict):
                cache[t]=meta
        except Exception:
            pass

    _cross_cache["at"]=now
    _cross_cache["rows"]=rows
    print("[CROSSLIST_DISCOVERY] raw=%d exact_pairs=%d failures=%s"%(
        len(raw),len(rows),json.dumps(failures,sort_keys=True)),flush=True)
    return list(rows)[:MAX_TOKENS]

def exact_pool_ok(token,pump_pool):
    try:
        canonical=c.canonical_pump_pool(token)
    except Exception as e:
        return False,"CANONICAL_LOOKUP_"+type(e).__name__
    if not canonical:
        return False,"NO_CANONICAL_PUMP_POOL"
    if canonical!=pump_pool:
        return False,"PUMP_POOL_MISMATCH"
    return True,"OK"

def _fine_sizes(best):
    x=float(best)
    vals={x}
    for m in (0.75,0.90,1.10,1.25):
        y=round(x*m,6)
        if 0.003<=y<=2.0:vals.add(y)
    return tuple(sorted(vals))

def quote_snapshot(snap,sizes,landing):
    ranked=[]
    for size in sizes:
        try:
            ops=c.sized_snapshot_opportunities(snap,float(size))
        except RuntimeError as e:
            if str(e)=="DLMM_PARTIAL":
                continue
            raise
        for op in ops:
            if op["direction"] not in STRATEGIES:
                continue
            start=int(op["start"])
            net=int(op["local_net"])-int(landing)
            bps=net/start*10000.0
            row=dict(op)
            row["landing_cost_lamports"]=int(landing)
            row["net_after_cost_lamports"]=net
            row["net_after_cost_sol"]=net/1e9
            row["net_after_cost_bps"]=bps
            ranked.append(row)
    ranked.sort(key=lambda x:x["net_after_cost_lamports"],reverse=True)
    return ranked

def hydrate_and_rank(token,pump_pool,landing):
    snap=c.build_token_snapshot(token,pump_pool)
    coarse=quote_snapshot(snap,COARSE_SIZES,landing)
    if not coarse:return snap,[]
    fine=quote_snapshot(snap,_fine_sizes(coarse[0]["size_sol"]),landing)
    merged={}
    for r in coarse+fine:
        merged[(r["direction"],r["size_sol"])]=r
    rows=sorted(merged.values(),key=lambda x:x["net_after_cost_lamports"],reverse=True)
    return snap,rows

def revalidate(token,pump_pool,row,landing):
    s0=_slot()
    snap=c.build_token_snapshot(token,pump_pool)
    exact=quote_snapshot(snap,(float(row["size_sol"]),),landing)
    s1=_slot()
    match=next((x for x in exact if x["direction"]==row["direction"]),None)
    if match is None:
        return None,{"reason":"DIRECTION_MISSING","slot_spread":s1-s0}
    match["slot_start"]=s0;match["slot_end"]=s1;match["slot_spread"]=s1-s0
    fresh=(s1-s0)<=MAX_SLOT_SPREAD
    positive=match["net_after_cost_bps"]>=MIN_NET_BPS
    match["fresh"]=fresh
    match["qualified"]=bool(fresh and positive)
    return match,{"reason":"OK" if match["qualified"] else ("STALE" if not fresh else "NOT_POSITIVE"),
                  "slot_spread":s1-s0}

def _persist(root,status,candidate=None):
    d=Path(root)/STATE_DIR;d.mkdir(parents=True,exist_ok=True)
    (d/"status.json").write_text(json.dumps(status,indent=2,sort_keys=True),encoding="utf-8")
    if candidate is not None:
        with (d/"candidates.jsonl").open("a",encoding="utf-8") as f:
            f.write(json.dumps(candidate,sort_keys=True)+"\n")

def scan_once(root):
    root=Path(root)
    landing=landing_cost_lamports()
    universe=candidate_universe(root)
    print("[QARB-001] CLEAN PROFIT-FIRST ARB BOT",flush=True)
    print("[STRATEGIES] PumpSwap<->Meteora DLMM | both directions | same-token | Jupiter=NONE",flush=True)
    print("[ARCH] hot tokens first -> exact Pump+DLMM crosslist cache -> one snapshot -> local sizes -> top-only fresh revalidation",flush=True)
    print("[CANDIDATES] quoteable_crosslisted=%d landing_cost=%.9f SOL"%(len(universe),landing/1e9),flush=True)

    raw=[]
    errors={}
    for i,x in enumerate(universe,1):
        t=x["token"];p=x["pump_pool"]
        ok,why=exact_pool_ok(t,p)
        if not ok:
            errors[why]=errors.get(why,0)+1
            print("[SKIP] %s token=%s"%(why,t[:10]),flush=True);continue
        try:
            _,rows=hydrate_and_rank(t,p,landing)
        except Exception as e:
            key="HTTP_429" if _is_429(e) else type(e).__name__+":"+str(e)
            errors[key]=errors.get(key,0)+1
            print("[SKIP] token=%s %s"%(t[:10],key),flush=True);continue
        if not rows:continue
        best=rows[0]
        raw.append((x,best))
        print("[RAW] token=%s src=%s dir=%s size=%.6f net=%+.9f SOL bps=%+.2f"%(
            t[:10],x["source"],best["direction"],best["size_sol"],
            best["net_after_cost_sol"],best["net_after_cost_bps"]),flush=True)

    raw.sort(key=lambda z:z[1]["net_after_cost_lamports"],reverse=True)
    qualified=None
    if raw and raw[0][1]["net_after_cost_bps"]>=MIN_NET_BPS:
        x,row=raw[0]
        try:
            rv,diag=revalidate(x["token"],x["pump_pool"],row,landing)
            if rv:
                print("[REVALIDATE] token=%s dir=%s size=%.6f net=%+.9f SOL bps=%+.2f slots=%d qualified=%s"%(
                    x["token"][:10],rv["direction"],rv["size_sol"],rv["net_after_cost_sol"],
                    rv["net_after_cost_bps"],rv["slot_spread"],rv["qualified"]),flush=True)
                if rv["qualified"]:
                    qualified={
                        "revision":REVISION,"observed_unix":time.time(),
                        "token":x["token"],"pump_pool":x["pump_pool"],
                        "meteora_pool":rv["meteora"]["address"],
                        "source":x["source"],"direction":rv["direction"],
                        "size_sol":rv["size_sol"],
                        "net_after_cost_sol":rv["net_after_cost_sol"],
                        "net_after_cost_bps":rv["net_after_cost_bps"],
                        "slot_spread":rv["slot_spread"],
                        "execution_authority":False,
                    }
        except Exception as e:
            errors["REVALIDATION_"+type(e).__name__]=errors.get("REVALIDATION_"+type(e).__name__,0)+1
            print("[REVALIDATE_FAIL] %s: %s"%(type(e).__name__,e),flush=True)

    status={
        "revision":REVISION,"observed_unix":time.time(),
        "universe":len(universe),"raw_pairs":len(raw),"errors":errors,
        "landing_cost_lamports":landing,
        "qualified":qualified,
        "execution_authority":False,
    }
    _persist(root,status,qualified)
    if qualified:
        print("[BEST] token=%s dir=%s size=%.6f net=%+.9f SOL bps=%+.2f"%(
            qualified["token"],qualified["direction"],qualified["size_sol"],
            qualified["net_after_cost_sol"],qualified["net_after_cost_bps"]),flush=True)
        print("[MONEY] FRESH_POSITIVE_PRE_SIM_CANDIDATE",flush=True)
    else:
        print("[MONEY] NO_FRESH_POSITIVE_CANDIDATE",flush=True)
    print("[MODE] scanner_only=True execution_authority=FALSE",flush=True)
    return status

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("--once",action="store_true")
    ap.add_argument("--interval",type=float,default=INTERVAL)
    ap.add_argument("--max-cycles",type=int,default=0)
    a=ap.parse_args(argv)
    root=Path.cwd();n=0
    try:
        while True:
            n+=1
            print("[CYCLE] %d"%n,flush=True)
            scan_once(root)
            if a.once or (a.max_cycles and n>=a.max_cycles):break
            time.sleep(max(0.25,a.interval))
    except KeyboardInterrupt:
        print("[STOP] user interrupted",flush=True)

if __name__=="__main__":
    main()
