\

import unittest
from types import SimpleNamespace
from qseries_v2.oracle_adapters.independent.oad_356_solana_decoder_closeout_unknown_registry import *

class T(unittest.TestCase):
    def test_closeout(self):
        attrs=(SimpleNamespace(signature="s",unknown_program_ids=("X",)),)
        flows=(SimpleNamespace(signature="s",delta=-1,mint="A"),SimpleNamespace(signature="s",delta=1,mint="B"))
        x=rank_decoder_closeout_unknowns(attrs,flows)[0]
        print("[CLOSEOUT]",x.program_id,x.disposition,x.priority_score)
        self.assertEqual(x.disposition,"HIGH_VALUE_UNRESOLVED_DEFERRED_AFTER_CLOSEOUT")

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-356 remaining unresolved decoder backlog preserved without blocking Solana production completion")

