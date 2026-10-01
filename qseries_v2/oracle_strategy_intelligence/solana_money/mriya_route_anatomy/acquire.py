from __future__ import annotations
import asyncio,time
from urllib.error import HTTPError
async def capture(seconds=.7,max_rows=1800):
    from qseries_v2.oracle_strategy_intelligence.solana_universal_trade_tape.usls_046b_shared_multidex_live_event_router import capture
    return await capture(seconds=seconds,max_rows=max_rows)
class Blocks:
    def __init__(self,rpc=None,spacing=.45):
        from qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition import _rpc
        self.rpc=rpc or _rpc;self.spacing=spacing;self.last=0;self.seen=set();self.rate_limits=0;self.errors=0
    def fetch(self,slot):
        d=self.spacing-(time.monotonic()-self.last)
        if d>0:time.sleep(d)
        try:
            b=self.rpc("getBlock",[int(slot),{"encoding":"jsonParsed","transactionDetails":"full","rewards":False,
                 "commitment":"confirmed","maxSupportedTransactionVersion":1}],8.0)
            self.last=time.monotonic();return b,False
        except HTTPError as e:
            self.last=time.monotonic()
            if getattr(e,"code",None)==429:self.rate_limits+=1;return None,True
            self.errors+=1;return None,False
        except Exception:
            self.last=time.monotonic();self.errors+=1;return None,False
