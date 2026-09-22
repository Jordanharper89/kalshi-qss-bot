import unittest

import qseries_v2.oracle_adapters.independent.oad_279_gmgn_solana_token_intelligence_adapter as oad279


class T(unittest.TestCase):
    def test_direct_resource_shape(self):
        d = {"address": "TEST", "symbol": "T"}
        self.assertIs(oad279._token_resource(d), d)

    def test_envelope_shape(self):
        d = {"code": 0, "message": "success", "data": {"address": "TEST"}}
        self.assertEqual(oad279._token_resource(d)["address"], "TEST")

    def test_physical_current_token_intelligence(self):
        r = oad279.acquire_current_gmgn_solana_token_intelligence(
            timeout_seconds=30.0,
            candidate_limit=5,
        )

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] provider=", r.provider)

        for section in ("info", "security", "pool"):
            d = r.payload[section]
            resource = oad279._token_resource(d)
            print(
                "[PHYSICAL]",
                section,
                "raw_type=",
                type(d).__name__,
                "resource_type=",
                type(resource).__name__,
            )
            self.assertIsInstance(d, (dict, list))
            self.assertIsInstance(resource, (dict, list))

        self.assertEqual(r.provider, "gmgn")
        self.assertEqual(r.payload.get("chain"), "sol")
        self.assertTrue(r.token_address)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad279.PROBABILITY_ENABLED)
        self.assertFalse(oad279.DIRECTION_ENABLED)
        self.assertFalse(oad279.PUBLICATION_ALLOWED)
        self.assertFalse(oad279.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-279 PHYSICAL CERTIFICATION TEST")
    print(" GMGN SOLANA TOKEN INTELLIGENCE — EXPLICIT MODULE IMPORT")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] direct-resource raw JSON contract certified")
    print("[PASS] envelope raw JSON contract certified")
    print("[PASS] live GMGN token info/security/pool intelligence certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-279 PHYSICALLY CERTIFIED")
