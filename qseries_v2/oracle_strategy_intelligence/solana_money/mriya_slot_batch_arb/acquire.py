from __future__ import annotations
import asyncio,time
from urllib.error import HTTPError
from .tx_decode import decode_edges,classify_target

async def capture_activity(seconds=.70,max_rows=1800):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    return await capture(seconds=seconds,max_rows=max_rows)

class SlotBatchAcquirer:
    def __init__(self,rpc=None,min_rpc_interval=.45):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.rpc=rpc or _rpc;self.min_rpc_interval=float(min_rpc_interval);self.last_rpc=0.0
        self.seen_slots=set();self.rate_limits=0;self.errors=0;self.blocks=0;self.transactions=0
    def _pace(self):
        d=self.min_rpc_interval-(time.monotonic()-self.last_rpc)
        if d>0:time.sleep(d)
    def fetch_block(self,slot):
        self._pace()
        try:
            b=self.rpc("getBlock",[int(slot),{"encoding":"jsonParsed","transactionDetails":"full",
                    "rewards":False,"commitment":"confirmed","maxSupportedTransactionVersion":1}],8.0)
            self.last_rpc=time.monotonic()
            return b,False
        except HTTPError as e:
            self.last_rpc=time.monotonic()
            if getattr(e,"code",None)==429:self.rate_limits+=1;return None,True
            self.errors+=1;return None,False
        except Exception:
            self.last_rpc=time.monotonic();self.errors+=1;return None,False
    def process_block(self,slot,block,received_unix):
        if not isinstance(block,dict):return [],[],{"tx":0}
        bt=block.get("blockTime") or 0;edges=[];targets=[];txs=block.get("transactions") or []
        self.transactions+=len(txs);self.blocks+=1
        for tx in txs:
            es,_=decode_edges(tx,slot,bt,received_unix);edges.extend(es)
            t=classify_target(tx)
            if t["contains_target"]:
                sigs=((tx.get("transaction") or {}).get("signatures") or [])
                t["signature"]=str(sigs[0]) if sigs else "";t["slot"]=int(slot);t["block_time"]=bt
                targets.append(t)
        return edges,targets,{"tx":len(txs)}
    def snapshot(self):
        return {"blocks":self.blocks,"transactions":self.transactions,"rpc429":self.rate_limits,"errors":self.errors}
