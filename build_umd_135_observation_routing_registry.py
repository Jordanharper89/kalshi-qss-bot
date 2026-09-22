from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_135_OBSERVATION_ROUTING_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_135_observation_routing_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_135_observation_routing_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_130_observation_classification import CanonicalObservationClassification\nfrom .umd_131_observation_entity_resolution import ObservationEntityResolution\nfrom .umd_132_observation_routing import ObservationRoute\nfrom .umd_133_observation_priority import ObservationPriorityProfile\nfrom .umd_134_observation_timeline import ObservationTimeline,verify_umd_134_observation_timeline_registry\n\nUMD_135_BUILD_ID="UMD-135"\nUMD_135_REVISION="UMD_135_OBSERVATION_ROUTING_REGISTRY_V1"\nUMD_135_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ObservationRoutingRecord:\n    observation_id:str\n    domain:str\n    classification_hash:str\n    entity_resolution_hash:str\n    route_hash:str\n    priority_profile_hash:str\n    timeline_id:str\n    market_ids:Tuple[str,...]\n    family_keys:Tuple[str,...]\n    venue_keys:Tuple[str,...]\n    unresolved_entities:Tuple[Tuple[str,str],...]\n\n    @property\n    def record_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "domain":self.domain,\n            "classification_hash":self.classification_hash,\n            "entity_resolution_hash":self.entity_resolution_hash,\n            "route_hash":self.route_hash,\n            "priority_profile_hash":self.priority_profile_hash,\n            "timeline_id":self.timeline_id,\n            "market_ids":self.market_ids,\n            "family_keys":self.family_keys,\n            "venue_keys":self.venue_keys,\n            "unresolved_entities":self.unresolved_entities,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ObservationRoutingRegistry:\n    records:Tuple[ObservationRoutingRecord,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    family_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    domain_index:Mapping[str,Tuple[str,...]]\n    timeline_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"records",tuple(self.records))\n        for name in ("market_index","family_index","venue_index","domain_index","timeline_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.records!=tuple(sorted(self.records,key=lambda r:(r.observation_id,r.record_hash))):\n            raise ValueError("records must be deterministically sorted")\n        if len({r.observation_id for r in self.records})!=len(self.records):\n            raise ValueError("observation ids must be unique")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_135_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-135")\n        required={r.record_hash for r in self.records}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every routing record hash")\n\n    def observations_for_market(self,key:str)->Tuple[str,...]: return self.market_index.get(key,())\n    def observations_for_family(self,key:str)->Tuple[str,...]: return self.family_index.get(key,())\n    def observations_for_venue(self,key:str)->Tuple[str,...]: return self.venue_index.get(key,())\n    def observations_for_domain(self,key:str)->Tuple[str,...]: return self.domain_index.get(key,())\n    def observations_for_timeline(self,key:str)->Tuple[str,...]: return self.timeline_index.get(key,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "record_hashes":tuple(r.record_hash for r in self.records),\n            "market_index":self.market_index,\n            "family_index":self.family_index,\n            "venue_index":self.venue_index,\n            "domain_index":self.domain_index,\n            "timeline_index":self.timeline_index,\n            "lineage":self.lineage,\n        })\n\nclass ObservationRoutingRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        items:Iterable[tuple[\n            CanonicalObservationClassification,\n            ObservationEntityResolution,\n            ObservationRoute,\n            ObservationPriorityProfile,\n            ObservationTimeline,\n        ]],\n        *,\n        lineage_factory,\n    )->ObservationRoutingRegistry:\n        records=[]\n        market={}; family={}; venue={}; domain={}; timeline={}\n\n        for classification,entities,route,priority,timeline_obj in items:\n            if not isinstance(classification,CanonicalObservationClassification): raise TypeError("classification must be CanonicalObservationClassification")\n            if not isinstance(entities,ObservationEntityResolution): raise TypeError("entities must be ObservationEntityResolution")\n            if not isinstance(route,ObservationRoute): raise TypeError("route must be ObservationRoute")\n            if not isinstance(priority,ObservationPriorityProfile): raise TypeError("priority must be ObservationPriorityProfile")\n            if not isinstance(timeline_obj,ObservationTimeline): raise TypeError("timeline must be ObservationTimeline")\n\n            obs=classification.observation_id\n            if not (entities.observation_id==route.observation_id==priority.observation_id==obs):\n                raise ValueError("observation components do not belong to same observation")\n            if entities.classification_hash!=classification.classification_hash:\n                raise ValueError("entity resolution classification mismatch")\n            if route.classification_hash!=classification.classification_hash or route.entity_resolution_hash!=entities.resolution_hash:\n                raise ValueError("route ownership mismatch")\n            if priority.route_hash!=route.route_hash:\n                raise ValueError("priority ownership mismatch")\n            if obs not in {e.observation_id for e in timeline_obj.entries}:\n                raise ValueError("timeline does not contain observation")\n\n            rec=ObservationRoutingRecord(\n                obs,classification.domain,classification.classification_hash,entities.resolution_hash,\n                route.route_hash,priority.profile_hash,timeline_obj.timeline_id,route.market_ids,\n                route.family_keys,route.venues(),route.unresolved_entities\n            )\n            records.append(rec)\n\n            for x in rec.market_ids: market.setdefault(x,[]).append(obs)\n            for x in rec.family_keys: family.setdefault(x,[]).append(obs)\n            for x in rec.venue_keys: venue.setdefault(x,[]).append(obs)\n            domain.setdefault(rec.domain,[]).append(obs)\n            timeline.setdefault(rec.timeline_id,[]).append(obs)\n\n        records.sort(key=lambda r:(r.observation_id,r.record_hash))\n        for index in (market,family,venue,domain,timeline):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        lineage=lineage_factory(tuple(r.record_hash for r in records))\n        return ObservationRoutingRegistry(tuple(records),market,family,venue,domain,timeline,lineage)\n\ndef build_umd_135_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_135_BUILD_ID,"revision":UMD_135_REVISION,\n        "schema_version":UMD_135_SCHEMA_VERSION,"upstream_builds":("UMD-130","UMD-131","UMD-132","UMD-133","UMD-134"),\n        "mode":"deterministic_read_only_observation_routing_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_135_observation_routing_registry()->bool:\n    if verify_umd_134_observation_timeline_registry() is not True:\n        return False\n    m=build_umd_135_certification_manifest()\n    return m["build_id"]=="UMD-135" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_130_observation_classification import CanonicalObservationClassification\nfrom qseries_v2.universal_market_discovery.umd_131_observation_entity_resolution import ObservationEntityResolution\nfrom qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute,RoutedVenueBinding\nfrom qseries_v2.universal_market_discovery.umd_133_observation_priority import ObservationPriorityProfile\nfrom qseries_v2.universal_market_discovery.umd_134_observation_timeline import ObservationTimeline,ObservationTimelineEntry\nfrom qseries_v2.universal_market_discovery.umd_135_observation_routing_registry import *\n\nFIXED=datetime(2026,8,10,2,0,tzinfo=timezone.utc)\n\ndef components(obs="obs-1"):\n    l130=ImmutableLineage(subsystem_id="UMD",build_id="UMD-130",revision="UMD_130_OBSERVATION_CLASSIFICATION_V1",schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://135/130",),created_at=FIXED)\n    c=CanonicalObservationClassification(obs,"economics",( ("metric","consumer-price-index"), ),l130)\n\n    l131=ImmutableLineage(subsystem_id="UMD",build_id="UMD-131",revision="UMD_131_OBSERVATION_ENTITY_RESOLUTION_V1",schema_version="1.0.0",parent_hashes=(c.classification_hash,),source_refs=("fixture://135/131",),created_at=FIXED)\n    e=ObservationEntityResolution(obs,c.classification_hash,(),(),l131)\n\n    l132=ImmutableLineage(subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",schema_version="1.0.0",parent_hashes=(c.classification_hash,e.resolution_hash),source_refs=("fixture://135/132",),created_at=FIXED)\n    r=ObservationRoute(obs,"economics",c.classification_hash,e.resolution_hash,(("metric","consumer-price-index"),),("m1",),("macro=cpi",),(RoutedVenueBinding("kalshi","K-CPI","m1"),),(("metric","consumer-price-index",("m1",)),),(),(),l132)\n\n    l133=ImmutableLineage(subsystem_id="UMD",build_id="UMD-133",revision="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1",schema_version="1.0.0",parent_hashes=(r.route_hash,),source_refs=("fixture://135/133",),created_at=FIXED)\n    p=ObservationPriorityProfile(obs,r.route_hash,1,1,1,1,0,0,4,l133)\n\n    entry=ObservationTimelineEntry(obs,FIXED,r.route_hash,p.profile_hash,"economics")\n    l134=ImmutableLineage(subsystem_id="UMD",build_id="UMD-134",revision="UMD_134_OBSERVATION_TIMELINE_REGISTRY_V1",schema_version="1.0.0",parent_hashes=(r.route_hash,p.profile_hash),source_refs=("fixture://135/134",),created_at=FIXED)\n    t=ObservationTimeline("macro-timeline",(entry,),l134)\n    return c,e,r,p,t\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-135",revision=UMD_135_REVISION,schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://135",),created_at=FIXED)\n\nclass TestUMD135(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_135_observation_routing_registry())\n    def test_registry_build(self):\n        x=components()\n        reg=ObservationRoutingRegistryBuilder().build((x,),lineage_factory=lf)\n        self.assertEqual(len(reg.records),1)\n        self.assertEqual(reg.records[0].observation_id,"obs-1")\n    def test_reverse_queries(self):\n        x=components()\n        reg=ObservationRoutingRegistryBuilder().build((x,),lineage_factory=lf)\n        self.assertEqual(reg.observations_for_market("m1"),("obs-1",))\n        self.assertEqual(reg.observations_for_family("macro=cpi"),("obs-1",))\n        self.assertEqual(reg.observations_for_venue("kalshi"),("obs-1",))\n        self.assertEqual(reg.observations_for_domain("economics"),("obs-1",))\n        self.assertEqual(reg.observations_for_timeline("macro-timeline"),("obs-1",))\n    def test_ownership_mismatch_rejected(self):\n        c,e,r,p,t=components()\n        bad_p=ObservationPriorityProfile("other",r.route_hash,1,1,1,1,0,0,4,p.lineage)\n        with self.assertRaises(ValueError):\n            ObservationRoutingRegistryBuilder().build(((c,e,r,bad_p,t),),lineage_factory=lf)\n    def test_timeline_membership_rejected(self):\n        c,e,r,p,t=components()\n        other_entry=ObservationTimelineEntry("other",FIXED,r.route_hash,p.profile_hash,"economics")\n        other_t=ObservationTimeline("macro-timeline",(other_entry,),t.lineage)\n        with self.assertRaises(ValueError):\n            ObservationRoutingRegistryBuilder().build(((c,e,r,p,other_t),),lineage_factory=lf)\n    def test_deterministic(self):\n        a=components("obs-a"); b=components("obs-b")\n        x=ObservationRoutingRegistryBuilder().build((a,b),lineage_factory=lf)\n        y=ObservationRoutingRegistryBuilder().build((b,a),lineage_factory=lf)\n        self.assertEqual(x.registry_hash,y.registry_hash)\n    def test_empty(self):\n        reg=ObservationRoutingRegistryBuilder().build((),lineage_factory=lf)\n        self.assertEqual(reg.records,())\n    def test_side_effects(self):\n        m=build_umd_135_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-135 CERTIFICATION TEST");print(" OBSERVATION ROUTING REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD135))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_135_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Classification, entity resolution, routing, priority, and timeline integration certified")\n    print("[PASS] Reverse observation queries by market, family, venue, domain, and timeline certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-135 CERTIFIED")\n'
UPSTREAM_MODULE='umd_134_observation_timeline'
UPSTREAM_VERIFIER='verify_umd_134_observation_timeline_registry'
EXPORTED_NAMES=('UMD_135_REVISION', 'ObservationRoutingRecord', 'ObservationRoutingRegistry', 'ObservationRoutingRegistryBuilder', 'build_umd_135_certification_manifest', 'verify_umd_135_observation_routing_registry')

def verify_upstream():
    sys.path.insert(0,str(ROOT))
    try:
        mod=importlib.import_module("qseries_v2.universal_market_discovery."+UPSTREAM_MODULE)
        verifier=getattr(mod,UPSTREAM_VERIFIER,None)
        if verifier is None:
            raise RuntimeError(f"Certified upstream verifier missing: {UPSTREAM_MODULE}.{UPSTREAM_VERIFIER}")
        if verifier() is not True:
            raise RuntimeError(f"Certified upstream verification failed: {UPSTREAM_MODULE}")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def write_exact(path,text):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(text.lstrip("\n"),encoding="utf-8",newline="\n")
    os.replace(tmp,path)

def update_init():
    current=INIT.read_text(encoding="utf-8") if INIT.exists() else ""
    marker="# UMD-135 exports"
    block=marker+"\nfrom ."+MODULE.stem+" import (\n"+"".join(f"    {name},\n" for name in EXPORTED_NAMES)+")\n"
    if marker not in current:
        write_exact(INIT,current.rstrip()+"\n\n"+block)

def verify_current():
    sys.path.insert(0,str(ROOT))
    try:
        name="qseries_v2.universal_market_discovery."+MODULE.stem
        sys.modules.pop(name,None)
        importlib.invalidate_caches()
        mod=importlib.import_module(name)
        missing=[name for name in EXPORTED_NAMES if not hasattr(mod,name)]
        if missing:
            raise RuntimeError("UMD-135 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-135 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-135 INSTALLER")
    print(" OBSERVATION ROUTING REGISTRY")
    print("="*72)
    print(f"[BOOT] Revision: {REVISION}")
    print(f"[ROOT] {ROOT}")
    verify_upstream()
    print("[PASS] Certified upstream verified read-only")
    backups={p:(p.read_bytes() if p.exists() else None) for p in (MODULE,INIT,TEST)}
    try:
        write_exact(MODULE,MODULE_SOURCE)
        write_exact(TEST,TEST_SOURCE)
        update_init()
        compile(MODULE.read_text(encoding="utf-8"),str(MODULE),"exec")
        compile(TEST.read_text(encoding="utf-8"),str(TEST),"exec")
        compile(INIT.read_text(encoding="utf-8"),str(INIT),"exec")
        verify_current()
    except Exception:
        for p,old in backups.items():
            if old is None:
                if p.exists():
                    p.unlink()
            else:
                p.write_bytes(old)
        importlib.invalidate_caches()
        print("[ROLLBACK] UMD-135 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-135',
        "revision":REVISION,
        "module":MODULE.name,
        "test":TEST.name,
        "files":{
            str(MODULE.relative_to(ROOT)):sha256_file(MODULE),
            str(INIT.relative_to(ROOT)):sha256_file(INIT),
            str(TEST.relative_to(ROOT)):sha256_file(TEST),
        },
        "network_enabled":False,
        "persistence_enabled":False,
        "publication_enabled":False,
        "execution_enabled":False,
    }
    digest=hashlib.sha256(json.dumps(manifest,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    print(f"[PASS] Wrote: {MODULE.relative_to(ROOT)}")
    print(f"[PASS] Updated: {INIT.relative_to(ROOT)}")
    print(f"[PASS] Wrote: {TEST.relative_to(ROOT)}")
    print("[PASS] In-memory compilation verified")
    print("[PASS] Required symbols and verifier certified")
    print(f"[PASS] Deterministic install hash: {digest}")
    print("[PASS] Network, persistence, publication, and execution disabled")
    print("[DONE] UMD-135 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
