from pathlib import Path
import py_compile
ROOT=Path.cwd()
SUB=ROOT/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
if not (SUB/"provider_binding_audit.py").is_file(): raise SystemExit("[FAIL] QARB-018 missing")
SRC=r"""
from __future__ import annotations
from dataclasses import dataclass
from .certified_roles import load as load_roles

@dataclass(frozen=True)
class Subscription:
    venue:str
    pool:str
    account:str

def build(root):
    rows=load_roles(root);out=[];seen=set()
    for r in rows:
        for a in r.accounts:
            k=(r.venue,r.pool,a)
            if k in seen: continue
            seen.add(k);out.append(Subscription(*k))
    return out

def requests(subs):
    return [
      {"jsonrpc":"2.0","id":i+1,"method":"accountSubscribe",
       "params":[s.account,{"encoding":"base64","commitment":"processed"}]}
      for i,s in enumerate(subs)
    ]
"""
TEST=r"""
import unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.six_dex_subscription_plan import *
class T(unittest.TestCase):
    def test_processed_account_subscribe(self):
        s=[Subscription("RAYDIUM_CPMM","P","A"),Subscription("ORCA","Q","B")]
        r=requests(s);self.assertEqual(len(r),2)
        self.assertTrue(all(x["method"]=="accountSubscribe" for x in r))
        self.assertTrue(all(x["params"][1]["commitment"]=="processed" for x in r))
        print("[PASS] six-DEX exact-role accounts compile to processed accountSubscribe requests")
if __name__=="__main__": unittest.main(verbosity=2)
"""
M=SUB/"six_dex_subscription_plan.py";M.write_text(SRC,encoding="utf-8");py_compile.compile(str(M),doraise=True)
T=ROOT/"test_qarb_019_six_dex_websocket_subscription_plan.py";T.write_text(TEST,encoding="utf-8");py_compile.compile(str(T),doraise=True)
print("[PASS] QARB-019 six-DEX websocket subscription plan installed")
print("[SOURCE] certified exact-role accounts only")
print("[COMMITMENT] processed")
print("[MODE] execution_authority=FALSE")
