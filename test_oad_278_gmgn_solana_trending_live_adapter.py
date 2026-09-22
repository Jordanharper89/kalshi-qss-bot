import json
import unittest

from qseries_v2.oracle_adapters.independent.oad_277_gmgn_production_admission_boundary import (
    evaluate_gmgn_admission,
)
from qseries_v2.oracle_adapters.independent.oad_278_gmgn_solana_trending_live_adapter import (
    EXECUTION_AUTHORITY,
    PUBLICATION_ALLOWED,
    PROBABILITY_ENABLED,
    DIRECTION_ENABLED,
    _json_from_stdout,
    acquire_gmgn_solana_trending,
)


class T(unittest.TestCase):
    def test_utf8_parser_boundary(self):
        fixture = {
            "code": 0,
            "data": {
                "rank": [
                    {
                        "chain": "sol",
                        "address": "TEST_SOLANA_ADDRESS",
                        "symbol": "MIM",
                        "trans_name_zhcn": "神奇互联网货币",
                    }
                ]
            },
            "message": "success",
            "reason": "",
        }
        raw = json.dumps(fixture, ensure_ascii=False).encode("utf-8")
        parsed = _json_from_stdout(raw)
        self.assertEqual(parsed["code"], 0)
        self.assertEqual(
            parsed["data"]["rank"][0]["trans_name_zhcn"],
            "神奇互联网货币",
        )

    def test_physical_gmgn_solana_trending(self):
        a = evaluate_gmgn_admission()
        self.assertTrue(
            a.admitted,
            "OAD-277 GMGN production admission must be open",
        )

        r = acquire_gmgn_solana_trending(interval="1h", limit=5)
        raw = r.payload.get("raw")

        print("[PHYSICAL] source_id=", r.source_id)
        print("[PHYSICAL] provider=", r.provider)
        print("[PHYSICAL] payload_type=", type(raw).__name__)

        self.assertEqual(r.provider, "gmgn")
        self.assertEqual(r.payload["chain"], "sol")
        self.assertFalse(r.execution_authority)

        self.assertIsInstance(raw, dict)
        self.assertEqual(raw.get("code"), 0)
        self.assertEqual(raw.get("message"), "success")

        rank = ((raw.get("data") or {}).get("rank") or [])
        print("[PHYSICAL] rank_count=", len(rank))

        if rank:
            print("[PHYSICAL] first_address=", rank[0].get("address"))
            print("[PHYSICAL] first_symbol=", rank[0].get("symbol"))

        self.assertGreater(len(rank), 0)
        for row in rank:
            self.assertEqual(row.get("chain"), "sol")
            self.assertTrue(str(row.get("address") or "").strip())

    def test_read_only_safety_boundary(self):
        self.assertFalse(PROBABILITY_ENABLED)
        self.assertFalse(DIRECTION_ENABLED)
        self.assertFalse(PUBLICATION_ALLOWED)
        self.assertFalse(EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-278 PHYSICAL CERTIFICATION TEST")
    print(" GMGN SOLANA TRENDING — WINDOWS UTF-8 SAFE")
    print("=" * 120)

    r = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not r.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] UTF-8 GMGN JSON decode boundary certified")
    print("[PASS] live GMGN Solana trending acquisition certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-278 PHYSICALLY CERTIFIED")
