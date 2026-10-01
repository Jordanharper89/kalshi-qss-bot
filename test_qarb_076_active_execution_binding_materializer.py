import json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_076_active_execution_binding_materializer as q
class T(unittest.TestCase):
 def test_binding_and_learned_size(self):
  with tempfile.TemporaryDirectory() as d:
   r=Path(d);p=r/q.q73.JOURNAL;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_text(json.dumps({"outcome":{"token":"TOK","size_sol":.5,"paper_net_sol":.02}})+"\n")
   olda=q.q70._load;oldh=q.hot.priority_prepare_pairs
   try:
    q.q70._load=lambda _r:{"tokens":{"TOK":{"status":"ACTIVE","samples":3,"wins":3,"pnl_sol":.04}}}
    q.hot.priority_prepare_pairs=lambda _r:([SimpleNamespace(token="TOK",pump_pool="P",meteora_pool="M")],0)
    x=q.materialize(r);self.assertEqual(x["bound"],1);self.assertEqual(x["bindings"]["TOK"]["size_sol"],.5)
   finally:q.q70._load=olda;q.hot.priority_prepare_pairs=oldh
 def test_safety(self):self.assertFalse(q.EXECUTION_AUTHORITY);self.assertFalse(q.REAL_MONEY_MOVED)
if __name__=="__main__":unittest.main(verbosity=2)
