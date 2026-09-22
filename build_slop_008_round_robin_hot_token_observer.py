from pathlib import Path
import ast
R=Path.cwd();D=R/"qseries_v2/oracle_strategy_intelligence/solana_live_opportunity"
if not (D/"slop_007_temporal_readiness_gate.py").exists():raise SystemExit("[FAIL] SLOP-007 missing")
M=D/"slop_008_round_robin_hot_token_observer.py"
M.write_text(r"""from qseries_v2.oracle_adapters.independent.oad_275_solana_continuous_observation_resilient_worker import run_solana_continuous_cycle
READ_ONLY=True;EXECUTION_AUTHORITY=False
def observe_hot_round(tokens,root=None,cycle_base=0,progress=print):
 out=[]
 for i,t in enumerate(tuple(tokens),1):
  c=run_solana_continuous_cycle(root=root,cycle=int(cycle_base)+i,token_address=t)
  out.append(c);progress(f"[HOT] token={t} history={c.history_records}")
 return tuple(out)
""",encoding="utf-8")
T=R/"test_slop_008_round_robin_hot_token_observer.py"
T.write_text(r"""import unittest
from unittest.mock import patch
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_008_round_robin_hot_token_observer import observe_hot_round
class T(unittest.TestCase):
 @patch("qseries_v2.oracle_strategy_intelligence.solana_live_opportunity.slop_008_round_robin_hot_token_observer.run_solana_continuous_cycle")
 def test_explicit(self,m):
  m.side_effect=lambda **k:SimpleNamespace(token_address=k["token_address"],history_records=1)
  x=observe_hot_round(("A","B"),progress=lambda x:None);print("[SLOP-008]",[z.token_address for z in x])
  self.assertEqual([z.token_address for z in x],["A","B"])
if __name__=="__main__":unittest.main(verbosity=2)
""",encoding="utf-8")
ast.parse(M.read_text());ast.parse(T.read_text())
print("[PASS] SLOP-008 installed")
print("[PASS] explicit-token round-robin observer; no rediscovery inside acquisition")