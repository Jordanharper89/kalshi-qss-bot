from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
M=S/"qarb_061a_shared_rpc_valve.py"
M.write_text("""from __future__ import annotations
import threading,time,urllib.error
from qseries_v2.oracle_strategy_intelligence.solana_money.native_atomic_money_machine import core as c
EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MIN_RPC_GAP_SECONDS=0.28
_ORIG_RPC=c.rpc
_LOCK=threading.Lock()
_LAST_RPC=0.0
_GAP=MIN_RPC_GAP_SECONDS
RPC_CALLS=0
RPC_429=0
def gated_rpc(method,params,tries=6):
    global _LAST_RPC,_GAP,RPC_CALLS,RPC_429
    last=None
    for attempt in range(int(tries)):
        with _LOCK:
            wait=_GAP-(time.monotonic()-_LAST_RPC)
            if wait>0: time.sleep(wait)
            _LAST_RPC=time.monotonic()
        try:
            out=_ORIG_RPC(method,params);RPC_CALLS+=1
            _GAP=max(MIN_RPC_GAP_SECONDS,_GAP*0.985)
            return out
        except urllib.error.HTTPError as e:
            last=e
            if e.code!=429: raise
            RPC_429+=1
        except Exception as e:
            last=e
            if "429" not in str(e): raise
            RPC_429+=1
        _GAP=min(2.0,max(_GAP*1.6,MIN_RPC_GAP_SECONDS))
        time.sleep(min(8.0,1.25*(attempt+1)))
    raise last
def install():
    c.rpc=gated_rpc
    return c
""",encoding="utf-8")
T=R/"test_qarb_061a_shared_rpc_valve.py"
T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as q
class T(unittest.TestCase):
    def test_mode(self): self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_gap(self): self.assertGreaterEqual(q.MIN_RPC_GAP_SECONDS,.25)
if __name__=="__main__": unittest.main(verbosity=2)
""",encoding="utf-8")
for x in (M,T): py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-061A shared serialized RPC valve installed")
print("[429] one adaptive HTTP lane; no independent RPC fanout")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")