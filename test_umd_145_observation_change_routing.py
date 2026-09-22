from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import ObservationRoutingRecord,ObservationRoutingRegistry
from qseries_v2.universal_market_discovery.umd_144_observation_change_registry import ObservationChangeRecord,ObservationChangeRegistry
from qseries_v2.universal_market_discovery.umd_145_observation_change_routing import *

FIXED=datetime(2026,8,10,8,0,tzinfo=timezone.utc)

def routing_registry():
    r1=ObservationRoutingRecord("obs-a","economics","a"*64,"b"*64,"c"*64,"d"*64,"t1",("m1",),("f1",),("kalshi",),())
    r2=ObservationRoutingRecord("obs-b","economics","e"*64,"f"*64,"1"*64,"2"*64,"t1",("m2",),("f2",),("polymarket",),())
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-135",revision="UMD_135_OBSERVATION_ROUTING_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(r1.record_hash,r2.record_hash),source_refs=("fixture://145/135",),created_at=FIXED)
    return ObservationRoutingRegistry(
        (r1,r2),
        {"m1":("obs-a",),"m2":("obs-b",)},
        {"f1":("obs-a",),"f2":("obs-b",)},
        {"kalshi":("obs-a",),"polymarket":("obs-b",)},
        {"economics":("obs-a","obs-b")},
        {"t1":("obs-a","obs-b")},
        l
    )

def change_registry():
    c1=ObservationChangeRecord("canonical-added","obs-a","3"*64)
    c2=ObservationChangeRecord("contradiction-added","obs-a|obs-b","4"*64)
    c3=ObservationChangeRecord("cluster-added","cluster-1","5"*64)
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-144",revision="UMD_144_OBSERVATION_CHANGE_REGISTRY_V1",
        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://145/144",),created_at=FIXED)
    return ObservationChangeRegistry((),tuple(sorted((c1,c2,c3),key=lambda c:(c.change_type,c.subject_key,c.diff_hash))),
        {},{},l)

def lineage(cr):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-145",revision=UMD_145_REVISION,
        schema_version="1.0.0",parent_hashes=tuple(c.change_hash for c in cr.changes),
        source_refs=("fixture://145",),created_at=FIXED)

class TestUMD145(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_145_observation_change_routing())
    def test_canonical_change_route(self):
        cr=change_registry(); rr=routing_registry()
        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))
        route=next(r for r in x.routes if r.change_type=="canonical-added")
        self.assertEqual(route.observation_ids,("obs-a",))
        self.assertEqual(route.market_ids,("m1",))
        self.assertEqual(route.family_keys,("f1",))
        self.assertEqual(route.venue_keys,("kalshi",))
    def test_contradiction_route(self):
        cr=change_registry(); rr=routing_registry()
        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))
        route=next(r for r in x.routes if r.change_type=="contradiction-added")
        self.assertEqual(route.observation_ids,("obs-a","obs-b"))
        self.assertEqual(route.market_ids,("m1","m2"))
        self.assertEqual(route.venue_keys,("kalshi","polymarket"))
    def test_cluster_change_preserved_unrouted(self):
        cr=change_registry(); rr=routing_registry()
        x=ObservationChangeRouter(cr,rr).route(lineage=lineage(cr))
        route=next(r for r in x.routes if r.change_type=="cluster-added")
        self.assertEqual(route.observation_ids,())
        self.assertEqual(route.market_ids,())
    def test_deterministic(self):
        cr=change_registry(); rr=routing_registry(); l=lineage(cr)
        a=ObservationChangeRouter(cr,rr).route(lineage=l)
        b=ObservationChangeRouter(cr,rr).route(lineage=l)
        self.assertEqual(a.routing_hash,b.routing_hash)
    def test_bad_registry(self):
        with self.assertRaises(TypeError):
            ObservationChangeRouter(object(),routing_registry())
    def test_side_effects(self):
        m=build_umd_145_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-145 CERTIFICATION TEST");print(" OBSERVATION CHANGE ROUTING");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD145))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_145_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Observation-state changes routed back to certified observation market structure")
    print("[PASS] Canonical and contradiction changes preserve markets, families, and venues")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-145 CERTIFIED")
