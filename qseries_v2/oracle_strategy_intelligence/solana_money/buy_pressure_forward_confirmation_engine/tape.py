from __future__ import annotations
import json,math,time
from collections import Counter,deque
from pathlib import Path
from .failure_memory import FORBIDDEN_ASSETS

ARTIFACTS=(
("PUMP_FUN","runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"),
("PUMP_SWAP","runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"),
("PUMP_SWAP","runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"),
)

def f(v,d=0.0):
    try:
        x=float(v);return x if math.isfinite(x) else float(d)
    except Exception:return float(d)

def walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():
            if isinstance(v,(dict,list)):yield from walk(v)
    elif isinstance(x,list):
        for v in x:
            if isinstance(v,(dict,list)):yield from walk(v)

def normalize(d,family):
    if not isinstance(d,dict):return None,"NOT_DICT"
    fam=str(d.get("venue") or d.get("family") or family or "").upper().replace("-","_")
    if fam=="PUMPSWAP":fam="PUMP_SWAP"
    if fam not in ("PUMP_FUN","PUMP_SWAP"):return None,"NON_PUMP_FAMILY"
    token=d.get("token_address") or d.get("token_mint") or d.get("mint")
    if not token:return None,"NO_TOKEN_IDENTITY"
    token=str(token)
    if token in FORBIDDEN_ASSETS:return None,"QUOTE_ASSET_AS_TOKEN"
    quote=str(d.get("quote_mint") or "")
    if quote and quote==token:return None,"TOKEN_EQUALS_QUOTE"
    market=d.get("market_address") or d.get("pair_address") or d.get("pool")
    side=str(d.get("side") or "").upper()
    price=f(d.get("effective_price") or d.get("price") or d.get("last_price"))
    ts=f(d.get("observed_unix") or d.get("event_timestamp") or d.get("trade_observed_unix") or d.get("block_time"))
    if not market:return None,"NO_MARKET"
    if side not in ("BUY","SELL"):return None,"NO_SIDE"
    if price<=0:return None,"NO_PRICE"
    if ts<=0:return None,"NO_TIME"
    q=abs(f(d.get("quote_amount") or d.get("quote_quantity") or d.get("quote_amount_lamports")))
    tid=str(d.get("trade_id") or "")
    if not tid:tid="|".join(map(str,(fam,d.get("signature") or "",d.get("instruction_index") or "",market,token,side,ts,price)))
    return {"trade_id":tid,"family":fam,"market":str(market),"token":token,"side":side,"price":price,"t":ts,
            "quote":q,"trader":str(d.get("trader") or ""),"birth_age_seconds":f(d.get("birth_age_seconds"),-1)},"OK"

class ArtifactTapeReader:
    def __init__(self,root:Path,max_seen=400000):
        self.root=Path(root).resolve();self.mtimes={};self.seen=set();self.order=deque();self.max_seen=max_seen
        self.rejects=Counter();self.emitted=0;self.generation=0
    def _remember(self,k):
        if k in self.seen:return False
        self.seen.add(k);self.order.append(k)
        while len(self.order)>self.max_seen:self.seen.discard(self.order.popleft())
        return True
    def poll(self):
        out=[];present=0;changed=0
        for fam,rel in ARTIFACTS:
            p=self.root/rel
            if not p.is_file():continue
            present+=1
            try:mt=p.stat().st_mtime_ns
            except OSError:continue
            if self.mtimes.get(str(p))==mt:continue
            self.mtimes[str(p)]=mt;changed+=1
            try:obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception:self.rejects["READ_ERROR"]+=1;continue
            for d in walk(obj):
                r,why=normalize(d,fam)
                if not r:self.rejects[why]+=1;continue
                if self._remember(r["trade_id"]):out.append(r)
        out.sort(key=lambda x:(x["t"],x["trade_id"]))
        if changed:self.generation+=1
        self.emitted+=len(out)
        newest=max((x["t"] for x in out),default=0)
        age=time.time()-newest if newest else None
        return out,{"generation":self.generation,"files":present,"changed":changed,"new_events":len(out),
                    "emitted":self.emitted,"newest_event_age":age,"rejects":dict(self.rejects)}
