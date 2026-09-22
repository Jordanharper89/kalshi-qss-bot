\

import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_349_solana_economic_protocol_attribution_v2 as mod

class T(unittest.TestCase):
    def test_attr(self):
        old=mod.attribute_transaction_protocols
        try:
            mod.attribute_transaction_protocols=lambda envs:(
                SimpleNamespace(signature="s",
                    top_level_program_ids=("DF1ow4tspfHX9JwWJsAb9epbkA8hmpSEAtxXy1V27QBH",),
                    inner_program_ids=("9H6tua7jkLhdm3w8BvgpTn5LZNU7g4ZynDmCiNN3q6Rp","FLUX6xBayGxLX9UcimVRxXFMHH6q43mAbRvDzSpCsvfK")),
            )
            x=mod.attribute_economic_protocols_v2((object(),))[0]
        finally:
            mod.attribute_transaction_protocols=old
        print("[ATTR-V2]",x.economic_protocols,x.unknown_program_ids)
        self.assertIn("DFLOW_AGGREGATOR_V4",x.economic_protocols)
        self.assertIn("HUMIDIFI",x.economic_protocols)
        self.assertIn("FLUX6xBayGxLX9UcimVRxXFMHH6q43mAbRvDzSpCsvfK",x.unknown_program_ids)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-349 expanded economic top-level + CPI attribution certified")

