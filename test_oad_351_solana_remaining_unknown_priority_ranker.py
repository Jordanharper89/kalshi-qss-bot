\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_351_solana_remaining_unknown_priority_ranker import *

class T(unittest.TestCase):
    def test_rank(self):
        attrs=(
            SimpleNamespace(signature="a",unknown_program_ids=("X",)),
            SimpleNamespace(signature="b",unknown_program_ids=("Y","Y")),
        )
        flows=(
            SimpleNamespace(signature="a",delta=-1,mint="A"),
            SimpleNamespace(signature="a",delta=1,mint="B"),
        )
        rows=rank_remaining_unknown_programs(attrs,flows)
        print("[RANK]",tuple((x.program_id,x.priority_score,x.priority_class) for x in rows))
        self.assertEqual(rows[0].program_id,"X")
        self.assertEqual(rows[0].priority_class,"HIGH_PRIORITY_BIDIRECTIONAL_FLOW")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-351 remaining unknown economic-priority ranker certified")

