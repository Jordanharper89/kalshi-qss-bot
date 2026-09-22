import unittest

import qseries_v2.oracle_adapters.independent.oad_281_gmgn_solana_single_writer_postgresql_persistence as oad281


class _FixtureGMGN:
    token_address = "TEST_TOKEN"
    observed_at = "2026-09-02T19:00:00+00:00"
    payload = {
        "chain": "sol",
        "info": {"address": "TEST_TOKEN", "symbol": "TEST"},
        "security": {"address": "TEST_TOKEN", "risk": "provider_claim"},
        "pool": {"address": "TEST_TOKEN", "liquidity": 123.0},
    }


class T(unittest.TestCase):
    def test_exact_oad261_shape_fixture(self):
        raw = oad281.build_gmgn_expansion_observations(_FixtureGMGN())
        self.assertEqual(len(raw), 3)

        for row in raw:
            self.assertTrue(row.source_id)
            self.assertEqual(len(row.provenance_hash), 64)
            self.assertTrue(row.observed_at)
            self.assertTrue(row.observation_type)
            self.assertEqual(row.source_class, "token_intelligence")
            self.assertEqual(row.provider, "gmgn")
            self.assertEqual(row.subject, "TEST_TOKEN")
            self.assertIsInstance(row.payload, dict)
            self.assertFalse(row.execution_authority)

            canonical = oad281.canonicalize_expansion_observation(
                row,
                oad281.BATCH_ID,
            )
            self.assertTrue(canonical.observation_id)

    def test_physical_postgresql_persistence(self):
        r = oad281.persist_gmgn_solana_token_intelligence()

        print("[PHYSICAL] token=", r.token_address)
        print("[PHYSICAL] raw=", r.raw_observations)
        print("[PHYSICAL] canonical=", r.canonical_observations)
        print("[PHYSICAL] already_present=", r.already_present)
        print("[PHYSICAL] committed_new=", r.committed_new)
        print("[PHYSICAL] exact_readback=", r.exact_readback)
        print("[PHYSICAL] providers=", r.providers)
        print("[PHYSICAL] source_ids=", r.source_ids)
        print("[PHYSICAL] observation_ids=", r.observation_ids)

        self.assertTrue(r.token_address)
        self.assertEqual(r.raw_observations, 3)
        self.assertEqual(r.canonical_observations, 3)
        self.assertEqual(
            r.already_present + r.committed_new,
            3,
        )
        self.assertEqual(r.exact_readback, 3)
        self.assertEqual(r.providers, ("gmgn", "gmgn", "gmgn"))
        self.assertEqual(len(r.source_ids), 3)
        self.assertEqual(len(r.observation_ids), 3)
        self.assertFalse(r.execution_authority)

    def test_safety(self):
        self.assertFalse(oad281.PROBABILITY_ENABLED)
        self.assertFalse(oad281.DIRECTION_ENABLED)
        self.assertFalse(oad281.PUBLICATION_ALLOWED)
        self.assertFalse(oad281.EXECUTION_AUTHORITY)


if __name__ == "__main__":
    print("=" * 120)
    print(" OAD-281 PHYSICAL CERTIFICATION TEST")
    print(" GMGN TOKEN INTELLIGENCE -> EXACT OAD-261 -> OPH-019 -> POSTGRESQL")
    print("=" * 120)

    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(T)
    )
    if not result.wasSuccessful():
        raise SystemExit(1)

    print("[PASS] GMGN observation shape satisfies exact OAD-261 contract")
    print("[PASS] GMGN info/security/pool persisted through universal single writer")
    print("[PASS] exact observation-ID PostgreSQL readback certified")
    print("[PASS] probability=FALSE direction=FALSE publication=FALSE execution=FALSE")
    print("[DONE] OAD-281 PHYSICALLY CERTIFIED")
