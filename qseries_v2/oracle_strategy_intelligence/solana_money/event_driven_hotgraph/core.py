from __future__ import annotations
import json,time
from collections import defaultdict
from pathlib import Path

LIVE_PATHS=(
 "runtime_state/solana_opportunities/solana_scanner/phase8_strict_live_direct_economics.json",
 "runtime_state/solana_opportunities/solana_scanner/phase8_balanced_live_economics.json",
)
ANCHORS={
 "So11111111111111111111111111111111111111112":"WSOL",
 "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v":"USDC",
 "Es9vMFrzaCERmJfrF4H2FYD9zX6Y2pZPbBZ5w4M7ZC9":"USDT",
}
MAX_AGE_SECONDS=1.50
MAX_CROSSVENUE_SKEW=0.50
MIN_GROSS_BPS=8.0
SUPPORTED={
 "PUMP_FUN","PUMP_SWAP","RAYDIUM_LAUNCHLAB","RAYDIUM_V4","RAYDIUM_CLMM","RAYDIUM_CPMM",
 "METEORA_DBC","METEORA_DAMM_V1","METEORA_DAMM_V2","METEORA_DLMM","ORCA",
 "MOONIT","BOOP_FUN","HEAVEN",
}

def _rows(obj):
    out=[]
    def walk(x):
        if isinstance(x,dict):
            keys=set(x)
            if {"input_asset","input_amount","output_asset","output_amount"}.issubset(keys):
                out.append(x)
            for v in x.values():
                if isinstance(v,(dict,list)): walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(obj)
    return out

def normalize(x):
    try:
        fam=str(x.get("family") or x.get("venue") or "")
        ia=float(x["input_amount"]);oa=float(x["output_amount"])
        a=str(x["input_asset"]);b=str(x["output_asset"])
        t=float(x.get("observed_unix") or x.get("trade_observed_unix") or 0.0)
    except Exception:return None
    if fam not in SUPPORTED or ia<=0 or oa<=0 or not a or not b or a==b or t<=0:return None
    return {
      "family":fam,"market_address":x.get("market_address"),"input_asset":a,"output_asset":b,
      "input_amount":ia,"output_amount":oa,"rate":oa/ia,"observed_unix":t,
      "trade_signature":x.get("trade_signature") or x.get("signature"),
      "strict_live_provenance":bool(x.get("strict_live_provenance",True)),
    }

class HotGraph:
    def __init__(self):
        self.edges={}
        self.seen=set()

    def ingest(self,rows,now=None):
        now=time.time() if now is None else now
        changed=set();new=0
        for raw in rows:
            x=normalize(raw)
            if not x:continue
            sig=x.get("trade_signature")
            dedupe=(x["family"],sig,x["input_asset"],x["output_asset"],x["observed_unix"])
            if dedupe in self.seen:continue
            self.seen.add(dedupe)
            k=(x["family"],x.get("market_address"),x["input_asset"],x["output_asset"])
            cur=self.edges.get(k)
            if cur is None or x["observed_unix"]>=cur["observed_unix"]:
                self.edges[k]=x
                changed.add(x["input_asset"]);changed.add(x["output_asset"]);new+=1
        self.expire(now)
        return new,changed

    def expire(self,now=None):
        now=time.time() if now is None else now
        dead=[k for k,e in self.edges.items() if now-e["observed_unix"]>MAX_AGE_SECONDS]
        for k in dead:self.edges.pop(k,None)

    def _fresh(self,now=None):
        now=time.time() if now is None else now
        return [e for e in self.edges.values() if 0<=now-e["observed_unix"]<=MAX_AGE_SECONDS]

    def two_leg(self,changed=None,now=None):
        es=self._fresh(now);by_src=defaultdict(list)
        for e in es:by_src[e["input_asset"]].append(e)
        out=[]
        starts=set(ANCHORS)
        if changed: starts={a for a in starts if a in changed or any(e["output_asset"] in changed for e in by_src.get(a,[]))}
        for a in starts:
            for e1 in by_src.get(a,[]):
                mid=e1["output_asset"]
                for e2 in by_src.get(mid,[]):
                    if e2["output_asset"]!=a or e2["family"]==e1["family"]:continue
                    skew=abs(e2["observed_unix"]-e1["observed_unix"])
                    if skew>MAX_CROSSVENUE_SKEW:continue
                    mult=e1["rate"]*e2["rate"];bps=(mult-1.0)*10000.0
                    if bps>=MIN_GROSS_BPS:
                        out.append({"legs":2,"path":[a,mid,a],"families":[e1["family"],e2["family"]],
                                    "gross_bps":bps,"skew_seconds":skew,"edges":[e1,e2]})
        return sorted(out,key=lambda r:r["gross_bps"],reverse=True)

    def three_leg(self,changed=None,now=None):
        es=self._fresh(now);by_src=defaultdict(list)
        for e in es:by_src[e["input_asset"]].append(e)
        out=[]
        for a in ANCHORS:
            for e1 in by_src.get(a,[]):
                x=e1["output_asset"]
                for e2 in by_src.get(x,[]):
                    y=e2["output_asset"]
                    if y in (a,x):continue
                    for e3 in by_src.get(y,[]):
                        if e3["output_asset"]!=a:continue
                        if len({e1["family"],e2["family"],e3["family"]})<2:continue
                        ts=[e1["observed_unix"],e2["observed_unix"],e3["observed_unix"]]
                        skew=max(ts)-min(ts)
                        if skew>MAX_CROSSVENUE_SKEW:continue
                        mult=e1["rate"]*e2["rate"]*e3["rate"];bps=(mult-1.0)*10000.0
                        if bps>=MIN_GROSS_BPS:
                            out.append({"legs":3,"path":[a,x,y,a],
                                        "families":[e1["family"],e2["family"],e3["family"]],
                                        "gross_bps":bps,"skew_seconds":skew,"edges":[e1,e2,e3]})
        return sorted(out,key=lambda r:r["gross_bps"],reverse=True)

    def scan_changed(self,changed=None,now=None):
        t0=time.perf_counter_ns()
        routes=self.two_leg(changed,now)+self.three_leg(changed,now)
        routes.sort(key=lambda r:r["gross_bps"],reverse=True)
        micros=(time.perf_counter_ns()-t0)/1000.0
        return routes,micros

def read_changed(root,state):
    rows=[];changed_files=[]
    for rel in LIVE_PATHS:
        p=Path(root)/rel
        if not p.exists():continue
        try:m=p.stat().st_mtime_ns
        except OSError:continue
        if state.get(rel)==m:continue
        state[rel]=m
        try:d=json.loads(p.read_text(encoding="utf-8"))
        except Exception:continue
        rows.extend(_rows(d));changed_files.append(rel)
    return rows,changed_files
