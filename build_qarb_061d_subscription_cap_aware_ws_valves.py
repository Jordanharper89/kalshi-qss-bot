from pathlib import Path
import py_compile

R=Path.cwd()
S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"

REQ=[
    S/"qarb_061c_existing_runner_six_dex_valve_cutover.py",
    S/"qarb_061b_two_ws_valves_paper_lane.py",
]
for x in REQ:
    if not x.exists():
        raise SystemExit("[FAIL] missing dependency: "+str(x))

M=S/"qarb_061d_subscription_cap_aware_ws_valves.py"

M.write_text("""from __future__ import annotations
import asyncio
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061b_two_ws_valves_paper_lane as wv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061c_existing_runner_six_dex_valve_cutover as q61c

EXECUTION_AUTHORITY=False
PAPER_ONLY=True
MAX_SUBSCRIPTIONS_PER_CONNECTION=64
CONNECTION_STAGGER_SECONDS=0.75

_ORIG_WORKER=wv.q60b.p._worker

def capped_valves(addrs):
    a=list(dict.fromkeys(addrs))
    n=MAX_SUBSCRIPTIONS_PER_CONNECTION
    return [a[i:i+n] for i in range(0,len(a),n)]

async def staggered_worker(index,addresses,q,c,stop):
    if index:
        await asyncio.sleep(index*CONNECTION_STAGGER_SECONDS)
    return await _ORIG_WORKER(index,addresses,q,c,stop)

def install():
    wv.two_valves=capped_valves
    wv.q60b.m._shards=capped_valves
    wv.q60b.p.m._shards=capped_valves
    wv.q60b.p._worker=staggered_worker
    return q61c

def main(argv=None):
    runtime=install()
    print("[QARB-061D] SUBSCRIPTION-CAP-AWARE SHARED WS VALVES",flush=True)
    print("[WS_CAP] max_accounts_per_connection=%d"%MAX_SUBSCRIPTIONS_PER_CONNECTION,flush=True)
    print("[WS_START] connections staggered %.2fs apart"%CONNECTION_STAGGER_SECONDS,flush=True)
    print("[PRESERVE] QARB-061A serialized HTTP lane + six-DEX existing runner",flush=True)
    print("[MODE] PAPER_ONLY=True execution_authority=FALSE",flush=True)
    return runtime.main(argv)

if __name__=="__main__":
    main()
""",encoding="utf-8")

T=R/"test_qarb_061d_subscription_cap_aware_ws_valves.py"
U=R/"run_qarb_061d_subscription_cap_aware_ws_valves.py"

T.write_text("""import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061d_subscription_cap_aware_ws_valves as q
class T(unittest.TestCase):
    def test_mode(self):
        self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
    def test_cap(self):
        s=q.capped_valves(list(range(256)))
        self.assertEqual(len(s),4)
        self.assertTrue(all(len(x)<=64 for x in s))
    def test_preserves_all_accounts(self):
        s=q.capped_valves(list(range(257)))
        self.assertEqual(sum(map(len,s)),257)
if __name__=="__main__":
    unittest.main(verbosity=2)
""",encoding="utf-8")

U.write_text("""from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_061d_subscription_cap_aware_ws_valves import main
if __name__=="__main__":
    main()
""",encoding="utf-8")

for x in (M,T,U):
    py_compile.compile(str(x),doraise=True)

print("[PASS] QARB-061D subscription-cap-aware WS valves installed")
print("[WS] <=64 subscriptions per connection + staggered connection starts")
print("[PRESERVE] serialized HTTP valve + six-DEX existing runner")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")