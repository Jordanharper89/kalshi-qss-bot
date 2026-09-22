from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_133_OBSERVATION_PRIORITY_PROFILE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_133_observation_priority.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_133_observation_priority.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_132_observation_routing import ObservationRoute,verify_umd_132_observation_routing\n\nUMD_133_BUILD_ID="UMD-133"\nUMD_133_REVISION="UMD_133_OBSERVATION_PRIORITY_PROFILE_V1"\nUMD_133_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ObservationPriorityProfile:\n    observation_id:str\n    route_hash:str\n    direct_dependency_count:int\n    canonical_market_count:int\n    family_count:int\n    venue_count:int\n    cross_venue_market_count:int\n    unresolved_entity_count:int\n    structural_span:int\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        for name in (\n            "direct_dependency_count","canonical_market_count","family_count",\n            "venue_count","cross_venue_market_count","unresolved_entity_count","structural_span"\n        ):\n            value=getattr(self,name)\n            if not isinstance(value,int) or value<0:\n                raise ValueError(f"{name} must be a non-negative integer")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_133_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-133")\n        if self.route_hash not in self.lineage.parent_hashes:\n            raise ValueError("lineage must include route hash")\n\n    @property\n    def profile_hash(self)->str:\n        return deterministic_sha256({\n            "observation_id":self.observation_id,\n            "route_hash":self.route_hash,\n            "direct_dependency_count":self.direct_dependency_count,\n            "canonical_market_count":self.canonical_market_count,\n            "family_count":self.family_count,\n            "venue_count":self.venue_count,\n            "cross_venue_market_count":self.cross_venue_market_count,\n            "unresolved_entity_count":self.unresolved_entity_count,\n            "structural_span":self.structural_span,\n            "lineage":self.lineage,\n        })\n\nclass ObservationPriorityProfiler:\n    __slots__=()\n\n    def build(self,route:ObservationRoute,*,lineage:ImmutableLineage)->ObservationPriorityProfile:\n        if not isinstance(route,ObservationRoute):\n            raise TypeError("route must be ObservationRoute")\n\n        venue_sets={}\n        for binding in route.venue_bindings:\n            venue_sets.setdefault(binding.canonical_market_id,set()).add(binding.venue_key)\n\n        cross_venue=sum(1 for venues in venue_sets.values() if len(venues)>1)\n        dependency_count=len(route.matched_dependencies)\n        market_count=len(route.market_ids)\n        family_count=len(route.family_keys)\n        venue_count=len(route.venues())\n        unresolved_count=len(route.unresolved_entities)\n\n        # Structural span is deliberately not a trading score. It is only a\n        # deterministic measure of how broadly the observation touches the market universe.\n        structural_span=dependency_count+market_count+family_count+venue_count+cross_venue\n\n        return ObservationPriorityProfile(\n            route.observation_id,\n            route.route_hash,\n            dependency_count,\n            market_count,\n            family_count,\n            venue_count,\n            cross_venue,\n            unresolved_count,\n            structural_span,\n            lineage,\n        )\n\ndef build_umd_133_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_133_BUILD_ID,"revision":UMD_133_REVISION,\n        "schema_version":UMD_133_SCHEMA_VERSION,"upstream_builds":("UMD-132",),\n        "mode":"deterministic_read_only_observation_structural_priority",\n        "priority_semantics":"structural_reach_only_not_trade_value",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_133_observation_priority_profile()->bool:\n    if verify_umd_132_observation_routing() is not True:\n        return False\n    m=build_umd_133_certification_manifest()\n    return m["build_id"]=="UMD-133" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_132_observation_routing import ObservationRoute,RoutedVenueBinding\nfrom qseries_v2.universal_market_discovery.umd_133_observation_priority import *\n\nFIXED=datetime(2026,8,10,0,0,tzinfo=timezone.utc)\n\ndef route():\n    c="a"*64; e="b"*64\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-132",revision="UMD_132_OBSERVATION_ROUTING_V1",\n        schema_version="1.0.0",parent_hashes=(c,e),\n        source_refs=("fixture://133/132",),created_at=FIXED\n    )\n    return ObservationRoute(\n        "obs-1","economics",c,e,\n        (("asset","bitcoin"),("metric","consumer-price-index")),\n        ("m1","m2"),\n        ("asset=bitcoin","metric=consumer-price-index"),\n        (\n            RoutedVenueBinding("kalshi","K-1","m1"),\n            RoutedVenueBinding("kalshi","K-2","m2"),\n            RoutedVenueBinding("polymarket","P-1","m1"),\n        ),\n        (\n            ("asset","bitcoin",("m1",)),\n            ("metric","consumer-price-index",("m2",)),\n        ),\n        (("entity","unknown-entity"),),\n        (),\n        l,\n    )\n\ndef lineage(r):\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,\n        schema_version="1.0.0",parent_hashes=(r.route_hash,),\n        source_refs=("fixture://133",),created_at=FIXED\n    )\n\nclass TestUMD133(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_133_observation_priority_profile())\n    def test_profile_counts(self):\n        r=route()\n        p=ObservationPriorityProfiler().build(r,lineage=lineage(r))\n        self.assertEqual(p.direct_dependency_count,2)\n        self.assertEqual(p.canonical_market_count,2)\n        self.assertEqual(p.family_count,2)\n        self.assertEqual(p.venue_count,2)\n        self.assertEqual(p.cross_venue_market_count,1)\n        self.assertEqual(p.unresolved_entity_count,1)\n    def test_structural_span(self):\n        r=route()\n        p=ObservationPriorityProfiler().build(r,lineage=lineage(r))\n        self.assertEqual(p.structural_span,9)\n    def test_deterministic(self):\n        r=route(); l=lineage(r)\n        a=ObservationPriorityProfiler().build(r,lineage=l)\n        b=ObservationPriorityProfiler().build(r,lineage=l)\n        self.assertEqual(a.profile_hash,b.profile_hash)\n    def test_bad_route(self):\n        with self.assertRaises(TypeError):\n            ObservationPriorityProfiler().build(object(),lineage=ImmutableLineage(\n                subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,\n                schema_version="1.0.0",parent_hashes=(),\n                source_refs=("fixture://133/bad",),created_at=FIXED\n            ))\n    def test_lineage_required(self):\n        r=route()\n        bad=ImmutableLineage(\n            subsystem_id="UMD",build_id="UMD-133",revision=UMD_133_REVISION,\n            schema_version="1.0.0",parent_hashes=("0"*64,),\n            source_refs=("fixture://133/bad",),created_at=FIXED\n        )\n        with self.assertRaises(ValueError):\n            ObservationPriorityProfiler().build(r,lineage=bad)\n    def test_side_effects(self):\n        m=build_umd_133_certification_manifest()\n        self.assertEqual(m["priority_semantics"],"structural_reach_only_not_trade_value")\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-133 CERTIFICATION TEST");print(" OBSERVATION PRIORITY PROFILE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD133))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_133_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Structural observation reach profile certified")\n    print("[PASS] Priority semantics explicitly exclude trading value and prediction")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-133 CERTIFIED")\n'
UPSTREAM_MODULE='umd_132_observation_routing'
UPSTREAM_VERIFIER='verify_umd_132_observation_routing'
EXPORTED_NAMES=('UMD_133_REVISION', 'ObservationPriorityProfile', 'ObservationPriorityProfiler', 'build_umd_133_certification_manifest', 'verify_umd_133_observation_priority_profile')

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
    marker="# UMD-133 exports"
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
            raise RuntimeError("UMD-133 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-133 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-133 INSTALLER")
    print(" OBSERVATION PRIORITY PROFILE")
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
        print("[ROLLBACK] UMD-133 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-133',
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
    print("[DONE] UMD-133 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
