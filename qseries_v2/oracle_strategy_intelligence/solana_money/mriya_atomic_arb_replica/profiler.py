from __future__ import annotations
import time,threading
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError
from .profile import TARGET_WALLET,TARGET_EXECUTOR_PROGRAM
from .persistence import read_json,write_json

def _empty(reason):
    return {"atomic_arb_candidate":False,"reason":reason,"executor_present":False,"sol_delta":0.0,
            "anchor_delta":{},"nonanchor_delta":{},"program_ids":(),"program_names":(),
            "compute_units":None,"fee_lamports":None}

def _keys(tx):
    msg=((tx or {}).get("transaction") or {}).get("message") or {};out=[]
    for x in msg.get("accountKeys") or []:
        p=x.get("pubkey") if isinstance(x,dict) else x
        if p:out.append(str(p))
    la=((tx or {}).get("meta") or {}).get("loadedAddresses") or {}
    for k in ("writable","readonly","readOnly"):
        for x in la.get(k) or []:
            if str(x) not in out:out.append(str(x))
    return out

def _program_ids(tx):
    keys=_keys(tx);out=[];msg=((tx or {}).get("transaction") or {}).get("message") or {}
    def add(ix):
        if not isinstance(ix,dict):return
        if ix.get("programId"):out.append(str(ix["programId"]));return
        i=ix.get("programIdIndex")
        if isinstance(i,int) and 0<=i<len(keys):out.append(keys[i])
    for ix in msg.get("instructions") or []:add(ix)
    for g in ((tx or {}).get("meta") or {}).get("innerInstructions") or []:
        for ix in g.get("instructions") or []:add(ix)
    return out

def _identify(pid):
    try:
        from qseries_v2.oracle_adapters.independent.oad_333_solana_authoritative_program_identity_registry import identify_solana_program
        x=identify_solana_program(pid);return str(getattr(x,"name",None) or pid)
    except Exception:return str(pid)

def _token_delta(tx,wallet):
    pre={};post={};m=(tx or {}).get("meta") or {}
    for side,target in (("preTokenBalances",pre),("postTokenBalances",post)):
        for b in m.get(side) or []:
            if str(b.get("owner") or "")!=wallet:continue
            try:target[str(b.get("mint"))]=float((b.get("uiTokenAmount") or {}).get("uiAmountString") or 0)
            except Exception:pass
    return {k:post.get(k,0)-pre.get(k,0) for k in set(pre)|set(post)}

def classify_target_transaction(tx,wallet=TARGET_WALLET):
    if not isinstance(tx,dict):return _empty("MALFORMED_TRANSACTION")
    b=_empty("UNCLASSIFIED");m=tx.get("meta") or {};pids=tuple(_program_ids(tx))
    b.update(executor_present=TARGET_EXECUTOR_PROGRAM in pids,program_ids=pids,
             program_names=tuple(_identify(x) for x in pids),compute_units=m.get("computeUnitsConsumed"),fee_lamports=m.get("fee"))
    if m.get("err") is not None:b["reason"]="TX_ERROR";return b
    keys=_keys(tx)
    if wallet not in keys:b["reason"]="WALLET_NOT_ACCOUNT";return b
    i=keys.index(wallet);pre=m.get("preBalances") or [];post=m.get("postBalances") or []
    if i>=len(pre) or i>=len(post):b["reason"]="BALANCE_INDEX_UNAVAILABLE";return b
    sol=(post[i]-pre[i])/1e9;td=_token_delta(tx,wallet)
    anchors={"So11111111111111111111111111111111111111112","EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
             "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB","USD1ttGY1N17NEEHLmELoaybftRBUSErhqYiQzvEmuB"}
    non={k:v for k,v in td.items() if k not in anchors and abs(v)>1e-8}
    ad={k:v for k,v in td.items() if k in anchors and abs(v)>1e-8}
    if abs(sol)>1e-9:ad["SOL_NATIVE"]=sol
    atomic=bool(b["executor_present"] and not non and any(v>0 for v in ad.values()))
    b.update(atomic_arb_candidate=atomic,sol_delta=sol,anchor_delta=ad,nonanchor_delta=non,
             reason="ATOMIC_CLOSED_CYCLE" if atomic else "NOT_CLOSED_ATOMIC_CYCLE")
    return b

class RateSafeTargetProfiler:
    def __init__(self,root:Path,limit=100,rpc=None,clock=time.time):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.root=Path(root).resolve();self.limit=int(limit);self.rpc=rpc or _rpc;self.clock=clock
        self.path=self.root/"runtime_state/qseries/qsb030_mriya_live_atomic_arb/target_profile_queue.json"
        self.data=read_json(self.path,{"discovered":[],"pending":[],"done":{},"reasons":{},"errors":{},"rate_limits":0})
        self.lock=threading.Lock();self.stop=threading.Event();self.thread=None;self.last_discovery=0.0

    def discover(self):
        try:sigs=self.rpc("getSignaturesForAddress",[TARGET_WALLET,{"limit":self.limit}],15.0) or []
        except Exception as e:
            self.data["errors"]["signature_fetch_"+type(e).__name__]=self.data["errors"].get("signature_fetch_"+type(e).__name__,0)+1
            self._save();return
        seen=set(self.data["discovered"])
        for row in sigs:
            sig=row.get("signature") if isinstance(row,dict) else None
            if sig and sig not in seen:
                seen.add(sig);self.data["discovered"].append(sig);self.data["pending"].append(sig)
        self.data["discovered"]=self.data["discovered"][-self.limit:]
        self._save()

    def cycle(self,budget=1):
        if not self.data["pending"] and len(self.data["discovered"])<self.limit:self.discover()
        n=0
        while self.data["pending"] and n<int(budget):
            sig=self.data["pending"][0]
            try:
                tx=self.rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":1}],12.0)
            except HTTPError as e:
                if getattr(e,"code",None)==429:
                    self.data["rate_limits"]+=1;self._save();return {"rate_limited":True,"hydrated":0}
                self.data["errors"]["HTTPError"]=self.data["errors"].get("HTTPError",0)+1
                self.data["pending"].pop(0);self._save();continue
            except Exception as e:
                k=type(e).__name__;self.data["errors"][k]=self.data["errors"].get(k,0)+1
                self.data["pending"].pop(0);self._save();continue
            c=classify_target_transaction(tx);c["signature"]=sig
            self.data["done"][sig]=c;self.data["pending"].pop(0);n+=1
            r=c["reason"];self.data["reasons"][r]=self.data["reasons"].get(r,0)+1
            self._save()
        return {"rate_limited":False,"hydrated":n}

    def _save(self):write_json(self.path,self.data)

    def snapshot(self):
        with self.lock:
            atomic=sum(bool(x.get("atomic_arb_candidate")) for x in self.data["done"].values())
            return {"discovered":len(self.data["discovered"]),"hydrated":len(self.data["done"]),
                    "pending":len(self.data["pending"]),"atomic_candidates":atomic,
                    "rate_limits":self.data["rate_limits"],"reasons":dict(self.data["reasons"]),
                    "errors":dict(self.data["errors"])}

    def _run(self):
        self.discover()
        while not self.stop.is_set():
            r=self.cycle(1)
            self.stop.wait(2.5 if r.get("rate_limited") else 1.0)

    def start(self):
        if self.thread:return
        self.thread=threading.Thread(target=self._run,name="QSB030-MRIYA-PROFILER",daemon=True);self.thread.start()

    def close(self):self.stop.set()
