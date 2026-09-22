from __future__ import annotations
import unittest
from datetime import datetime,timezone,timedelta

from qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage
from qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute
from qseries_v2.universal_market_discovery.umd_133_observation_priority import ObservationPriorityProfile
from qseries_v2.universal_market_discovery.umd_134_observation_timeline import *

BASE=datetime(2026,8,10,1,0,tzinfo=timezone.utc)

def route(obs,seed):
    c=seed*64; e=chr(ord(seed)+1)*64
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",
        schema_version="1.0.0",parent_hashes=(c,e),source_refs=("fixture://134/132",),created_at=BASE)
    return ObservationRoute(obs,"economics",c,e,(),(),(),(),(),(),(),l)

def priority(r):
    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-133",revision="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1",
        schema_version="1.0.0",parent_hashes=(r.route_hash,),source_refs=("fixture://134/133",),created_at=BASE)
    return ObservationPriorityProfile(r.observation_id,r.route_hash,0,0,0,0,0,0,0,l)

def lf(parents):
    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-134",revision=UMD_134_REVISION,
        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://134",),created_at=BASE)

class TestUMD134(unittest.TestCase):
    def test_foundation(self): self.assertTrue(verify_umd_134_observation_timeline_registry())
    def test_temporal_order(self):
        a=route("obs-a","a"); b=route("obs-b","c")
        t=ObservationTimelineBuilder().build("macro",(
            (b,priority(b),BASE+timedelta(minutes=2)),
            (a,priority(a),BASE),
        ),lineage_factory=lf)
        self.assertEqual(tuple(e.observation_id for e in t.entries),("obs-a","obs-b"))
    def test_range_query(self):
        a=route("obs-a","a"); b=route("obs-b","c")
        t=ObservationTimelineBuilder().build("macro",(
            (a,priority(a),BASE),(b,priority(b),BASE+timedelta(minutes=2))
        ),lineage_factory=lf)
        self.assertEqual(t.observations_between(BASE,BASE+timedelta(minutes=1)),("obs-a",))
    def test_naive_time_rejected(self):
        a=route("obs-a","a")
        with self.assertRaises(ValueError):
            ObservationTimelineBuilder().build("macro",(
                (a,priority(a),datetime(2026,8,10,1,0)),
            ),lineage_factory=lf)
    def test_priority_mismatch_rejected(self):
        a=route("obs-a","a"); b=route("obs-b","c")
        with self.assertRaises(ValueError):
            ObservationTimelineBuilder().build("macro",((a,priority(b),BASE),),lineage_factory=lf)
    def test_duplicate_observation_rejected(self):
        a=route("obs-a","a"); p=priority(a)
        with self.assertRaises(ValueError):
            ObservationTimelineBuilder().build("macro",(
                (a,p,BASE),(a,p,BASE+timedelta(minutes=1))
            ),lineage_factory=lf)
    def test_deterministic(self):
        a=route("obs-a","a"); b=route("obs-b","c")
        items=((a,priority(a),BASE),(b,priority(b),BASE+timedelta(minutes=1)))
        x=ObservationTimelineBuilder().build("macro",items,lineage_factory=lf)
        y=ObservationTimelineBuilder().build("macro",tuple(reversed(items)),lineage_factory=lf)
        self.assertEqual(x.timeline_hash,y.timeline_hash)
    def test_side_effects(self):
        m=build_umd_134_certification_manifest()
        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))

if __name__=="__main__":
    print("="*72);print(" UMD-134 CERTIFICATION TEST");print(" OBSERVATION TIMELINE REGISTRY");print("="*72)
    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD134))
    if not r.wasSuccessful(): raise SystemExit(1)
    m=build_umd_134_certification_manifest()
    print();print(f"[PASS] Build: {m['build_id']}");print(f"[PASS] Revision: {m['revision']}");print(f"[PASS] Manifest hash: {m['manifest_hash']}")
    print("[PASS] Deterministic timezone-aware observation timelines certified")
    print("[PASS] Route-to-priority ownership and duplicate observation rejection certified")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-134 CERTIFIED")
