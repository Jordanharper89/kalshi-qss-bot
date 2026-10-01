from __future__ import annotations
import json, math, time
from collections import deque
from pathlib import Path

ARTIFACTS=(
    ("PUMP_FUN","runtime_state/solana_opportunities/universal_trade_tape/pump_exact_economic_trade_tape.json"),
    ("PUMP_SWAP","runtime_state/solana_opportunities/universal_trade_tape/pumpswap_048c_repaired_trades.json"),
    ("PUMP_SWAP","runtime_state/solana_opportunities/universal_trade_tape/multidex_universal_economic_tape.json"),
)

def f(v,d=0.0):
    try:
        x=float(v)
        return x if math.isfinite(x) else float(d)
    except Exception:
        return float(d)

def walk(obj):
    if isinstance(obj,dict):
        yield obj
        for v in obj.values():
            if isinstance(v,(dict,list)):
                yield from walk(v)
    elif isinstance(obj,list):
        for v in obj:
            if isinstance(v,(dict,list)):
                yield from walk(v)

def normalize(d, expected_family=None):
    if not isinstance(d,dict): return None
    fam=str(d.get("venue") or d.get("family") or expected_family or "").upper().replace("-","_")
    if fam=="PUMPSWAP": fam="PUMP_SWAP"
    if fam not in ("PUMP_FUN","PUMP_SWAP"): return None
    token=d.get("token_address") or d.get("token_mint") or d.get("mint")
    market=d.get("market_address") or d.get("pair_address") or d.get("pool")
    side=str(d.get("side") or "").upper()
    price=f(d.get("effective_price") or d.get("price") or d.get("last_price"))
    ts=f(d.get("observed_unix") or d.get("event_timestamp") or d.get("block_time"))
    if not token or not market or side not in ("BUY","SELL") or price<=0 or ts<=0:
        return None
    quote=abs(f(d.get("quote_amount") or d.get("quote_quantity") or d.get("quote_amount_lamports")))
    trader=str(d.get("trader") or "")
    trade_id=str(d.get("trade_id") or "")
    if not trade_id:
        trade_id="|".join(map(str,(fam,d.get("signature") or "",d.get("instruction_index") or "",
                                  market,token,side,ts,price)))
    return {
        "trade_id":trade_id,"family":fam,"market":str(market),"token":str(token),
        "side":side,"price":price,"t":ts,"quote":quote,"trader":trader,
        "birth_age_seconds":f(d.get("birth_age_seconds"),-1),
    }

class ArtifactTapeReader:
    def __init__(self,root:Path,max_seen=200000):
        self.root=Path(root).resolve()
        self.mtimes={}
        self.seen=set()
        self.order=deque()
        self.max_seen=max_seen
        self.files_read=0
        self.rows_seen=0
        self.rows_emitted=0

    def _remember(self,k):
        if k in self.seen: return False
        self.seen.add(k);self.order.append(k)
        while len(self.order)>self.max_seen:
            old=self.order.popleft();self.seen.discard(old)
        return True

    def poll(self):
        out=[];present=0;changed=0
        for family,rel in ARTIFACTS:
            p=self.root/rel
            if not p.is_file(): continue
            present+=1
            try: mt=p.stat().st_mtime_ns
            except OSError: continue
            if self.mtimes.get(str(p))==mt: continue
            self.mtimes[str(p)]=mt;changed+=1
            try: obj=json.loads(p.read_text(encoding="utf-8",errors="ignore"))
            except Exception: continue
            self.files_read+=1
            for d in walk(obj):
                r=normalize(d,family)
                if not r: continue
                self.rows_seen+=1
                if self._remember(r["trade_id"]): out.append(r)
        out.sort(key=lambda x:(x["t"],x["trade_id"]))
        self.rows_emitted+=len(out)
        return out,{
            "artifact_files_present":present,"artifact_files_changed":changed,
            "new_events":len(out),"rows_emitted_total":self.rows_emitted,
            "files_read_total":self.files_read,
        }
