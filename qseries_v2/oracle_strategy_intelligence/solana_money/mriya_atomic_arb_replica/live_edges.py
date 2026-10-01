from __future__ import annotations
import asyncio,time
from collections import defaultdict
from urllib.error import HTTPError

def _ui_amount(b):
    try:return float((b.get("uiTokenAmount") or {}).get("uiAmountString") or 0)
    except Exception:return 0.0

def _owner_flows(tx):
    m=(tx or {}).get("meta") or {};pre=defaultdict(dict);post=defaultdict(dict)
    for key,target in (("preTokenBalances",pre),("postTokenBalances",post)):
        for b in m.get(key) or []:
            owner=str(b.get("owner") or "")
            mint=str(b.get("mint") or "")
            if owner and mint:target[owner][mint]=_ui_amount(b)
    flows={}
    for owner in set(pre)|set(post):
        d={mint:post[owner].get(mint,0)-pre[owner].get(mint,0) for mint in set(pre[owner])|set(post[owner])}
        d={k:v for k,v in d.items() if abs(v)>1e-12}
        if d:flows[owner]=d
    return flows

def implied_swap_edges(tx,venue,signature,observed_unix,chain_block_time=None):
    out=[]
    if not isinstance(tx,dict) or ((tx.get("meta") or {}).get("err") is not None):return out
    for owner,d in _owner_flows(tx).items():
        neg=[(m,-v) for m,v in d.items() if v<0];pos=[(m,v) for m,v in d.items() if v>0]
        # Only exact simple owner flow: one asset spent, one asset received.
        if len(neg)!=1 or len(pos)!=1:continue
        src,ain=neg[0];dst,aout=pos[0]
        if ain<=0 or aout<=0 or src==dst:continue
        out.append({"src":src,"dst":dst,"rate":aout/ain,"venue":str(venue),"market":str(venue)+":"+str(signature),
                    "t":float(observed_unix),"chain_block_time":float(chain_block_time) if isinstance(chain_block_time,(int,float)) else None,
                    "signature":str(signature),"owner":owner,
                    "basis":"EXECUTED_SWAP_IMPLIED_RATE","observed_direction":True})
    return out

async def _capture(seconds,max_rows):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    return await capture(seconds=seconds,max_rows=max_rows)

class LiveEdgeCapture:
    def __init__(self,rpc=None):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.rpc=rpc or _rpc;self.pending=[];self.seen=set();self.rate_limits=0;self.errors=0

    def capture(self,seconds=.65,max_rows=1800,max_hydrate=3):
        now=time.time()
        try:ret=asyncio.run(_capture(seconds,max_rows)) or {}
        except Exception as e:
            return [],{"raw_rows":0,"new_signatures":0,"hydrated":0,"edges":0,"rate_limits":self.rate_limits,"capture_error":type(e).__name__}
        rows=list(ret.get("rows") or []);venue_by_sig={}
        for r in rows:
            sig=r.get("signature")
            if not sig or sig in self.seen or sig in venue_by_sig:continue
            venue_by_sig[str(sig)]=str(r.get("venue") or "UNKNOWN")
        for sig,venue in venue_by_sig.items():
            self.pending.append((sig,venue,now))
        # A missed live signature is useful for historical learning, not for a
        # current arbitrage decision. Never build an unbounded stale live queue.
        self.pending=[x for x in self.pending if now-x[2]<=.75][-32:]
        edges=[];hydrated=0;attempts=0
        while self.pending and attempts<int(max_hydrate):
            sig,venue,obs=self.pending.pop(0);attempts+=1
            if sig in self.seen:continue
            try:
                tx=self.rpc("getTransaction",[sig,{"encoding":"jsonParsed","commitment":"confirmed","maxSupportedTransactionVersion":1}],8.0)
            except HTTPError as e:
                if getattr(e,"code",None)==429:
                    self.rate_limits+=1
                    # live arb evidence goes stale quickly; do not retry this signature as a live edge
                    self.seen.add(sig);continue
                self.errors+=1;self.seen.add(sig);continue
            except Exception:
                self.errors+=1;self.seen.add(sig);continue
            self.seen.add(sig);hydrated+=1
            # Freshness is measured from when this exact event reached us.
            # Chain blockTime is retained as an independent staleness guard.
            bt=tx.get("blockTime") if isinstance(tx,dict) else None
            edges.extend(implied_swap_edges(tx,venue,sig,obs,bt))
        return edges,{"raw_rows":len(rows),"new_signatures":len(venue_by_sig),"hydrated":hydrated,
                      "edges":len(edges),"pending":len(self.pending),"rate_limits":self.rate_limits,"errors":self.errors}
