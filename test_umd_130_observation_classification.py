from __future__ import annotations
import unittest
from dataclasses import FrozenInstanceError
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_130_observation_classification import *

FIXED=datetime(2026,8,9,23,30,tzinfo=timezone.utc)

def lineage():
    return ImmutableLineage(
        subsystem_id="UMD",
        build_id="UMD-130",
        revision=UMD_130_REVISION,
        schema_version="1.0.0",
        parent_hashes=(),
        source_refs=("fixture://130",),
        created_at=FIXED,
    )

class TestUMD130(unittest.TestCase):
    def test_foundation(self):
        self.assertTrue(verify_umd_130_observation_classification())

    def test_classification(self):
        c=ObservationClassifier().classify(
            "obs-1",
            "Economic",
            (("metric","Consumer Price Index"),("event","CPI Release")),
            lineage=lineage(),
        )
        self.assertEqual(c.domain,"economics")
        self.assertEqual(
            c.routing_facts,
            (("event","cpi-release"),("metric","consumer-price-index")),
        )

    def test_domain_alias(self):
        c=ObservationClassifier().classify("obs-2","FED",(),lineage=lineage())
        self.assertEqual(c.domain,"central-banking")

    def test_deduplication(self):
        c=ObservationClassifier().classify(
            "obs-3","crypto",
            (("asset","Bitcoin"),("asset","BITCOIN")),
            lineage=lineage(),
        )
        self.assertEqual(c.routing_facts,(("asset","bitcoin"),))

    def test_entity_reserved_for_131(self):
        with self.assertRaises(ValueError):
            ObservationClassifier().classify(
                "obs-4","politics",
                (("entity","Federal Reserve"),),
                lineage=lineage(),
            )

    def test_unknown_domain_rejected(self):
        with self.assertRaises(ValueError):
            ObservationClassifier().classify("obs-5","unknown-domain",(),lineage=lineage())

    def test_deterministic(self):
        a=ObservationClassifier().classify(
            "obs-6","weather",
            (("event","Hurricane Warning"),("geography","Gulf Coast")),
            lineage=lineage(),
        )
        b=ObservationClassifier().classify(
            "obs-6","weather",
            (("geography","Gulf Coast"),("event","Hurricane Warning")),
            lineage=lineage(),
        )
        self.assertEqual(a.classification_hash,b.classification_hash)

    def test_immutable(self):
        c=ObservationClassifier().classify("obs-7","sports",(),lineage=lineage())
        with self.assertRaises((FrozenInstanceError,AttributeError)):
            c.domain="weather"

    def test_side_effects(self):
        m=build_umd_130_certification_manifest()
        self.assertFalse(any(
            m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")
        ))

if __name__=="__main__":
    print("="*72);print(" UMD-130 CERTIFICATION TEST");print(" OBSERVATION CLASSIFICATION");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD130))
    if not r.wasSuccessful():
        raise SystemExit(1)
    m=build_umd_130_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Canonical observation domains and routing-fact normalization certified")
    print("[PASS] Entity resolution remains isolated to UMD-131")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-130 CERTIFIED")
