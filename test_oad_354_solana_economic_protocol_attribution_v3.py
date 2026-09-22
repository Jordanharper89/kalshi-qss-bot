\

import unittest
from types import SimpleNamespace
import qseries_v2.oracle_adapters.independent.oad_354_solana_economic_protocol_attribution_v3 as mod

class T(unittest.TestCase):
    def test_attr(self):
        old=mod.attribute_transaction_protocols
        try:
            mod.attribute_transaction_protocols=lambda envs:(
                SimpleNamespace(signature="s",
                    top_level_program_ids=("dbcij3LWUppWqq96dh6gJWwBifmcGfLSB5D4DuSMaqN","CAMMCzo5YL8w4VFF8KVHrK22GGUsp5VTaW7grrKgrWqK"),
                    inner_program_ids=("whirLbMiicVdio4qvUfM5KAg6Ct8VwpYzGff3uctyCc","99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2")),
            )
            x=mod.attribute_economic_protocols_v3((object(),))[0]
        finally:
            mod.attribute_transaction_protocols=old
        print("[ATTR-V3]",x.economic_protocols,x.unknown_program_ids)
        self.assertIn("METEORA_DBC",x.economic_protocols)
        self.assertIn("RAYDIUM_CLMM",x.economic_protocols)
        self.assertIn("ORCA_WHIRLPOOLS",x.economic_protocols)
        self.assertIn("99vQwtBwYtrqqD9YSXbdum3KBdxPAVxYTaQ3cfnJSrN2",x.unknown_program_ids)

if __name__=="__main__":
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(T))
    if not r.wasSuccessful(): raise SystemExit(1)
    print("[PASS] OAD-354 final economic top-level + CPI attribution certified")

