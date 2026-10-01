import unittest

from qseries_v2.oracle_strategy_intelligence.solana_money.qarb_execution_engineering import qarb_083_restart_continuity_rotation_durability as q


class T(unittest.TestCase):

    def base(self):
        return {
            "tokens":{
                "A":{
                    "samples":30,
                    "wins":27,
                    "pnl_sol":1.0
                }
            },
            "seen":["A"],
            "memory":["A"],
            "proven_tokens":["A"],
            "recyclable_proven_tokens":["A"],
            "restart_continuity":{
                "status":"PASS"
            },
            "q80_state":{
                "generation":2,
                "transport_failures":0,
                "usable_tokens":["A"]
            },
            "q82_state":{
                "status":"PASS",
                "runtime_return_code":0,
                "single_manual_launcher":True
            },
        }


    def test_clean_restart_passes(self):
        b=self.base()
        a=self.base()

        a["tokens"]["A"][
            "samples"
        ]=31

        a["tokens"]["A"][
            "wins"
        ]=28

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "PASS"
        )


    def test_sample_rollback_holds(self):
        b=self.base()
        a=self.base()

        a["tokens"]["A"][
            "samples"
        ]=29

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_win_rollback_holds(self):
        b=self.base()
        a=self.base()

        a["tokens"]["A"][
            "wins"
        ]=26

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_seen_rollback_holds(self):
        b=self.base()
        a=self.base()

        a["seen"]=[]

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_memory_rollback_holds(self):
        b=self.base()
        a=self.base()

        a["memory"]=[]

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_proven_history_must_survive(self):
        b=self.base()
        a=self.base()

        a["tokens"]={}

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_two_generations_required(self):
        b=self.base()
        a=self.base()

        a["q80_state"][
            "generation"
        ]=1

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_transport_must_stay_clean(self):
        b=self.base()
        a=self.base()

        a["q80_state"][
            "transport_failures"
        ]=1

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_child_failure_propagates(self):
        b=self.base()
        a=self.base()

        self.assertEqual(
            q.compare(
                b,
                a,
                2
            )["status"],
            "HOLD"
        )


    def test_one_launcher_contract(self):
        b=self.base()
        a=self.base()

        a["q82_state"][
            "single_manual_launcher"
        ]=False

        self.assertEqual(
            q.compare(
                b,
                a,
                0
            )["status"],
            "HOLD"
        )


    def test_safety(self):
        self.assertFalse(
            q.EXECUTION_AUTHORITY
        )

        self.assertTrue(
            q.PAPER_ONLY
        )

        self.assertFalse(
            q.REAL_MONEY_MOVED
        )


if __name__=="__main__":
    unittest.main(
        verbosity=2
    )
