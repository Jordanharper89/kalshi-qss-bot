from __future__ import annotations
import unittest
from datetime import datetime,timezone

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_130_observation_classification import CanonicalObservationClassification
from qseries_v2.universal_market_discovery.umd_131_observation_entity_resolution import ObservationEntityResolution
from qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute,RoutedVenueBinding
from qseries_v2.universal_market_discovery.umd_133_observation_priority import ObservationPriorityProfile
from qseries_v2.universal_market_discovery.umd_134_observation_timeline import ObservationTimeline,ObservationTimelineEntry
from qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import *

FIXED=datetime(2026,8,10,2,0,tzinfo=timezone.utc)

def components(obs="obs-1"):
    l130=ImmutableLineage(subsystem_id="UMD",build_id="UMD-130",revision="UMD_130_OBSERVATION_CLASSIFICATION_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://135/130",),created_at=FIXED)
    c=CanonicalObservationClassification(obs,"economics",( ("metric","consumer-price-index"), ),l130)

    l131=ImmutableLineage(subsystem_id="UMD",build_id="UMD-131",revision="UMD_131_OBSERVATION_ENTITY_RESOLUTION_V1",schema_version="1.0.0",parent_hashes=(c.classification_hash,),source_refs=("fixture://135/131",),created_at=FIXED)
    e=ObservationEntityResolution(obs,c.classification_hash,(),(),l131)

    l132=ImmutableLineage(subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",schema_version="1.0.0",parent_hashes=(c.classification_hash,e.resolution_hash),source_refs=("fixture://135/132",),created_at=FIXED)
    r=ObservationRoute(obs,"economics",c.classification_hash,e.resolution_hash,(("metric","consumer-price-index"),),("m1",),("macro=cpi",),(RoutedVenueBinding("kalshi","K-CPI","m1"),),(("metric","consumer-price-index",("m1",)),),(),(),l132)

    l133=ImmutableLineage(subsystem_id="UMD",build_id="UMD-133",revision="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1",schema_version="1.0.0",parent_hashes=(r.route_hash,),source_refs=("fixture://135/133",),created_at=FIXED)
    p=ObservationPriorityProfile(obs,r.route_hash,1,1,1,1,0,0,4,l133)

    entry=ObservationTimelineEntry(obs,FIXED,r.route_hash,p.profile_hash,"economics")
    l134=ImmutableLineage(subsystem_id="UMD",build_id="UMD-134",revision="UMD_134_OBSERVATION_TIMELINE_REGISTRY_V1",schema_version="1.0.0",parent_hashes=(r.route_hash,p.profile_hash),source_refs=("fixture://135/134",),created_at=FIXED)
    t=ObservationTimeline("macro-timeline",(entry,),l134)
    return c,e,r,p,t

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-135",revision=UMD_135_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://135",),created_at=FIXED)

class TestUMD135(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_135_observation_routing_registry())
    def test_registry_build(self):
        x=components()
        reg=ObservationRoutingRegistryBuilder().build((x,),lineage_factory=lf)
        self.assertEqual(len(reg.records),1)
        self.assertEqual(reg.records[0].observation_id,"obs-1")
    def test_reverse_queries(self):
        x=components()
        reg=ObservationRoutingRegistryBuilder().build((x,),lineage_factory=lf)
        self.assertEqual(reg.observations_for_market("m1"),("obs-1",))
        self.assertEqual(reg.observations_for_family("macro=cpi"),("obs-1",))
        self.assertEqual(reg.observations_for_venue("kalshi"),("obs-1",))
        self.assertEqual(reg.observations_for_domain("economics"),("obs-1",))
        self.assertEqual(reg.observations_for_timeline("macro-timeline"),("obs-1",))
    def test_ownership_mismatch_rejected(self):
        c,e,r,p,t=components()
        bad_p=ObservationPriorityProfile("other",r.route_hash,1,1,1,1,0,0,4,p.lineage)
        with self.assertRaises(ValueError):
            ObservationRoutingRegistryBuilder().build(((c,e,r,bad_p,t),),lineage_factory=lf)
    def test_timeline_membership_rejected(self):
        c,e,r,p,t=components()
        other_entry=ObservationTimelineEntry("other",FIXED,r.route_hash,p.profile_hash,"economics")
        other_t=ObservationTimeline("macro-timeline",(other_entry,),t.lineage)
        with self.assertRaises(ValueError):
            ObservationRoutingRegistryBuilder().build(((c,e,r,p,other_t),),lineage_factory=lf)
    def test_deterministic(self):
        a=components("obs-a"); b=components("obs-b")
        x=ObservationRoutingRegistryBuilder().build((a,b),lineage_factory=lf)
        y=ObservationRoutingRegistryBuilder().build((b,a),lineage_factory=lf)
        self.assertEqual(x.registry_hash,y.registry_hash)
    def test_empty(self):
        reg=ObservationRoutingRegistryBuilder().build((),lineage_factory=lf)
        self.assertEqual(reg.records,())
    def test_side_effects(self):
        m=build_umd_135_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-135 CERTIFICATION TEST");print(" OBSERVATION ROUTING REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD135))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_135_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Classification, entity resolution, routing, priority, and timeline integration certified")
    print("[PASS] Reverse observation queries by market, family, venue, domain, and timeline certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-135 CERTIFIED")
