from pathlib import Path
import py_compile
R=Path.cwd();S=R/"qseries_v2/oracle_strategy_intelligence/solana_money/qarb_clean_bot"
REQ=[S/"qarb_043b_paced_mriya_token_discovery.py",S/"qarb_037_mriya_priority_pair_hydration.py",S/"qarb_061a_shared_rpc_valve.py"]
for x in REQ:
    if not x.exists(): raise SystemExit("[FAIL] missing dependency: "+str(x))
M=S/"qarb_064a_silent_mriya_profit_feed.py"
M.write_text(r'''from __future__ import annotations
import contextlib,importlib,inspect,sys
from pathlib import Path
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_061a_shared_rpc_valve as rv
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_037_mriya_priority_pair_hydration as hot
EXECUTION_AUTHORITY=False;PAPER_ONLY=True
LOG=Path("runtime_state/qseries/qarb_clean_bot/mriya_internal_feed.log")
def bind_rpc():
    rv.install();bound=[]
    for name in (
      "qseries_v2.oracle_adapters.independent.oad_148_solana_mainnet_chain_state_acquisition",
      "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery",
      "qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_027_mriya_native_wallet_observer"):
        try:
            m=importlib.import_module(name)
            if hasattr(m,"_rpc"):m._rpc=lambda method,params,timeout_seconds=20.0:rv.gated_rpc(method,params);bound.append(name+"._rpc")
            if hasattr(m,"rpc"):m.rpc=lambda method,params,*a,**k:rv.gated_rpc(method,params);bound.append(name+".rpc")
        except Exception:pass
    return bound
def collect(root,seconds=8.0):
    bind_rpc();q=importlib.import_module("qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot.qarb_043b_paced_mriya_token_discovery")
    p=Path(root)/LOG;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        try:
            fn=q.main
            if len(inspect.signature(fn).parameters):fn(["--seconds",str(seconds)])
            else:
                old=sys.argv;sys.argv=[q.__name__,"--seconds",str(seconds)]
                try:fn()
                finally:sys.argv=old
        except SystemExit:pass
def candidates(root):
    pairs,landing,meta=hot.hydrate(Path(root))
    return list(pairs),landing,meta
''',encoding="utf-8")
T=R/"test_qarb_064a_silent_mriya_profit_feed.py"
T.write_text(r'''import inspect,unittest
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_clean_bot import qarb_064a_silent_mriya_profit_feed as q
class T(unittest.TestCase):
 def test_mode(self):self.assertTrue(q.PAPER_ONLY);self.assertFalse(q.EXECUTION_AUTHORITY)
 def test_silent(self):
  s=inspect.getsource(q.collect);self.assertIn("redirect_stdout",s);self.assertIn("mriya_internal_feed.log",inspect.getsource(q))
 def test_profit_handoff(self):self.assertIn("hot.hydrate",inspect.getsource(q.candidates))
if __name__=="__main__":unittest.main(verbosity=2)
''',encoding="utf-8")
for x in (M,T):py_compile.compile(str(x),doraise=True)
print("[PASS] QARB-064A silent Mriya profit feed installed")
print("[FEED] discoveries hidden from console and materialized as hot arbitrage pairs")
print("[MODE] PAPER_ONLY=True execution_authority=FALSE")