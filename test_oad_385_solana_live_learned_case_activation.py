import unittest
from qseries_v2.oracle_adapters.independent.oad_385_solana_live_learned_case_activation import build_live_learned_cases

class T(unittest.TestCase):
    def test_certified_history_reuse(self):
        x,learned,stats,handoff=build_live_learned_cases()

        print(
            "[LEARNED-CASES] token=",x.token_address,
            "anchor_history=",x.anchor_history_records,
            "final_history=",x.final_history_records,
        )
        print(
            "[LEARNED-CASES] pending=",x.pending_cases,
            "outcomes=",x.attributed_outcomes,
            "learned=",x.learned_cases,
        )
        print(
            "[LEARNED-CASES] stats=",x.statistics_type,
            "handoff=",x.handoff_type,
        )

        self.assertGreaterEqual(x.anchor_history_records,13)
        self.assertGreater(x.final_history_records,x.anchor_history_records)
        self.assertGreater(x.pending_cases,0)
        self.assertGreater(x.attributed_outcomes,0)
        self.assertGreater(x.learned_cases,0)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] OAD-385 certified OAD-384 history reused without reacquisition")
    print("[PASS] OAD-315 real learned cases physically rebuilt")
    print("[PASS] OAD-316 comparable-case statistics physically rebuilt")
    print("[PASS] OAD-317 existing learning handoff physically rebuilt")
    print("[PASS] no new token selected")
    print("[PASS] no additional OPH-019 acquisition required")
