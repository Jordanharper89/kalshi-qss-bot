
import inspect
import tempfile
import unittest
from pathlib import Path

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_080_single_runtime_dynamic_mriya_supervisor as q

class T(unittest.TestCase):
    def test_current_repo_contracts(self):
        self.assertTrue(callable(q.q47.prepare_from))
        self.assertTrue(callable(q.q47.write_generation))
        self.assertTrue(callable(q.rv.gated_rpc))
        self.assertEqual(q.q61d.MAX_SUBSCRIPTIONS_PER_CONNECTION,64)

    def test_cross_process_hydration_lock(self):
        s=inspect.getsource(q.acquire_hydration_lock)
        self.assertIn("O_EXCL",s)
        self.assertIn("LOCK_STALE_SECONDS",s)

    def test_exact_rpc_valve_applied(self):
        self.assertIn(
            "q47.p.m.pd.c.rpc=rv.gated_rpc",
            inspect.getsource(q.generation_worker)
        )

    def test_single_worker_hydration(self):
        s=inspect.getsource(q.generation_worker)
        self.assertIn("pairs,landing=q47.prepare_from",s)
        self.assertIn("def cached_prepare",s)
        self.assertIn("q47.p.m.pd.prepare_pairs=cached_prepare",s)

    def test_horizon_safe_windows(self):
        r,d=q.normalize_windows(30,125)
        self.assertGreaterEqual(r,60)
        self.assertGreaterEqual(d,r+95)
        self.assertGreaterEqual(d-r,90)

    def test_learning_preserved(self):
        self.assertTrue(issubclass(q.LearningAgeLane,q.q47.AgeDrainLane))
        self.assertIn("q73.observe",inspect.getsource(q.LearningAgeLane.capture))

    def test_presence_state(self):
        self.assertEqual(q.PRESENCE.name,"qarb_080_presence.json")

    def test_new_token_only_once(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:(set(),set())
                new,ret=q.announce(root,[{"token":"NEW1"}])
                self.assertEqual(new,["NEW1"])
                self.assertEqual(ret,[])
                new,ret=q.announce(root,[{"token":"NEW1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,[])
            finally:
                q.lifecycle_sets=old

    def test_true_retired_return(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:(set(),{"TOK1"})
                q._save(root/q.SEEN,{"tokens":["TOK1"]})
                q._save(root/q.PRESENCE,{"tokens":[]})
                new,ret=q.announce(root,[{"token":"TOK1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,["TOK1"])
            finally:
                q.lifecycle_sets=old

    def test_continuous_active_not_return(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            old=q.lifecycle_sets
            try:
                q.lifecycle_sets=lambda _:({"WIN1"},set())
                q._save(root/q.SEEN,{"tokens":["WIN1"]})
                q._save(root/q.PRESENCE,{"tokens":["WIN1"]})
                new,ret=q.announce(root,[{"token":"WIN1"}])
                self.assertEqual(new,[])
                self.assertEqual(ret,[])
            finally:
                q.lifecycle_sets=old

    def test_ws_stagger_repair(self):
        self.assertGreaterEqual(q.WS_CONNECTION_STAGGER_SECONDS,2.0)
        self.assertIn(
            "CONNECTION_STAGGER_SECONDS",
            inspect.getsource(q.generation_worker)
        )

    def test_transport_zero_reconnect_requirement(self):
        s=inspect.getsource(q.generation_worker)
        self.assertIn("reconnects==0",s)
        self.assertIn("rate_limits==0",s)
        self.assertIn("WS_TRANSPORT_",s)

    def test_parent_propagates_worker_failure(self):
        s=inspect.getsource(q.run)
        self.assertIn("transport_failures",s)
        self.assertIn("WS_TRANSPORT_FINAL",s)

    def test_safety(self):
        self.assertFalse(q.EXECUTION_AUTHORITY)
        self.assertTrue(q.PAPER_ONLY)
        self.assertFalse(q.REAL_MONEY_MOVED)

if __name__=="__main__":
    unittest.main(verbosity=2)
