\

import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_344_solana_expanded_protocol_attribution as mod

class T(unittest.TestCase):
    def test_attribution(self):
        original=mod.attribute_transaction_protocols
        try:
            mod.attribute_transaction_protocols=lambda envs:(
                SimpleNamespace(
                    signature="s",
                    top_level_program_ids=("EtrnLzgbS7nMMy5fbD42kXiUzGg8XQzJ972Xtk1cjWih","pythWSnswVUd12oZpeFP8e9CVaEqJg25g1Vtc2biRsT"),
                    inner_program_ids=("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR",)
                ),
            )
            x=mod.attribute_expanded_protocols((object(),))[0]
        finally:
            mod.attribute_transaction_protocols=original
        print("[ATTR]",x.economic_protocols,x.infrastructure_protocols,x.unknown_program_ids)
        self.assertEqual(x.economic_protocols,("PHOENIX_ETERNAL",))
        self.assertEqual(x.infrastructure_protocols,("PYTH_PRICE_FEED",))
        self.assertEqual(x.unknown_program_ids,("W1LDCARDa67SPBG7TFpQivHnEZXRtxCFP13ysEd1bWR",))

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-344 expanded top-level + CPI protocol attribution certified")

