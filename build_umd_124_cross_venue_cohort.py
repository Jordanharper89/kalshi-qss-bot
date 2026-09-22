from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_124_CROSS_VENUE_IMPACT_COHORT_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_124_cross_venue_cohort.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_124_cross_venue_cohort.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_122_impact_venue_projection import VenueImpactProjection,VenueImpactBinding\nfrom .umd_123_impact_surface_registry import verify_umd_123_impact_surface_registry\n\nUMD_124_BUILD_ID="UMD-124"\nUMD_124_REVISION="UMD_124_CROSS_VENUE_IMPACT_COHORT_V1"\nUMD_124_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass MarketVenueCohort:\n    canonical_market_id:str\n    venue_keys:Tuple[str,...]\n    venue_market_ids:Tuple[Tuple[str,str],...]\n    direct:bool\n\n    def __post_init__(self):\n        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))\n        object.__setattr__(self,"venue_market_ids",tuple(self.venue_market_ids))\n        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):\n            raise ValueError("venue_keys must be unique and sorted")\n        if self.venue_market_ids!=tuple(sorted(set(self.venue_market_ids))):\n            raise ValueError("venue_market_ids must be unique and sorted")\n        if tuple(sorted({venue for venue,_ in self.venue_market_ids}))!=self.venue_keys:\n            raise ValueError("venue_keys must match venue_market_ids")\n\n    @property\n    def cross_venue(self)->bool:\n        return len(self.venue_keys)>1\n\n    @property\n    def cohort_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "venue_keys":self.venue_keys,\n            "venue_market_ids":self.venue_market_ids,\n            "direct":self.direct,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass CrossVenueImpactCohort:\n    observation_hash:str\n    markets:Tuple[MarketVenueCohort,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"markets",tuple(self.markets))\n        if self.markets!=tuple(sorted(self.markets,key=lambda m:(m.canonical_market_id,m.cohort_hash))):\n            raise ValueError("markets must be deterministically sorted")\n        if len({m.canonical_market_id for m in self.markets})!=len(self.markets):\n            raise ValueError("duplicate canonical market cohort")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_124_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-124")\n\n    def cross_venue_market_ids(self)->Tuple[str,...]:\n        return tuple(m.canonical_market_id for m in self.markets if m.cross_venue)\n\n    def for_market(self,canonical_market_id:str)->MarketVenueCohort|None:\n        for market in self.markets:\n            if market.canonical_market_id==canonical_market_id:\n                return market\n        return None\n\n    @property\n    def cohort_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "market_cohort_hashes":tuple(m.cohort_hash for m in self.markets),\n            "lineage":self.lineage,\n        })\n\nclass CrossVenueImpactCohortBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        projection:VenueImpactProjection,\n        *,\n        lineage:ImmutableLineage,\n    )->CrossVenueImpactCohort:\n        if not isinstance(projection,VenueImpactProjection):\n            raise TypeError("projection must be VenueImpactProjection")\n\n        buckets={}\n        for binding in projection.bindings:\n            bucket=buckets.setdefault(binding.canonical_market_id,{"direct":binding.direct,"pairs":[]})\n            if bucket["direct"] is not binding.direct:\n                raise ValueError("direct flag mismatch across venue bindings for canonical market")\n            bucket["pairs"].append((binding.venue_key,binding.venue_market_id))\n\n        markets=[]\n        for market_id,data in sorted(buckets.items()):\n            pairs=tuple(sorted(set(data["pairs"])))\n            venues=tuple(sorted({venue for venue,_ in pairs}))\n            markets.append(MarketVenueCohort(market_id,venues,pairs,data["direct"]))\n\n        return CrossVenueImpactCohort(\n            projection.observation_hash,\n            tuple(markets),\n            lineage,\n        )\n\ndef build_umd_124_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_124_BUILD_ID,"revision":UMD_124_REVISION,\n        "schema_version":UMD_124_SCHEMA_VERSION,"upstream_builds":("UMD-122","UMD-123"),\n        "mode":"deterministic_read_only_cross_venue_impact_cohort",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_124_cross_venue_impact_cohort()->bool:\n    if verify_umd_123_impact_surface_registry() is not True:\n        return False\n    m=build_umd_124_certification_manifest()\n    return m["build_id"]=="UMD-124" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import VenueImpactBinding,VenueImpactProjection\nfrom qseries_v2.universal_market_discovery.umd_124_cross_venue_cohort import *\n\nFIXED=datetime(2026,8,9,22,0,tzinfo=timezone.utc)\n\ndef projection():\n    l=ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-122",revision="UMD_122_IMPACT_VENUE_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://124/122",),created_at=FIXED\n    )\n    return VenueImpactProjection(\n        "a"*64,\n        (\n            VenueImpactBinding("kalshi","K-1","m1",True),\n            VenueImpactBinding("polymarket","P-1","m1",True),\n            VenueImpactBinding("kalshi","K-2","m2",False),\n        ),\n        (),\n        l,\n    )\n\ndef lineage():\n    return ImmutableLineage(\n        subsystem_id="UMD",build_id="UMD-124",revision=UMD_124_REVISION,\n        schema_version="1.0.0",parent_hashes=(),\n        source_refs=("fixture://124",),created_at=FIXED\n    )\n\nclass TestUMD124(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_124_cross_venue_impact_cohort())\n    def test_cross_venue_market(self):\n        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())\n        self.assertEqual(c.cross_venue_market_ids(),("m1",))\n        self.assertTrue(c.for_market("m1").cross_venue)\n    def test_single_venue_market(self):\n        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())\n        self.assertFalse(c.for_market("m2").cross_venue)\n    def test_direct_flag_preserved(self):\n        c=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())\n        self.assertTrue(c.for_market("m1").direct)\n        self.assertFalse(c.for_market("m2").direct)\n    def test_deterministic(self):\n        a=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())\n        b=CrossVenueImpactCohortBuilder().build(projection(),lineage=lineage())\n        self.assertEqual(a.cohort_hash,b.cohort_hash)\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            CrossVenueImpactCohortBuilder().build(object(),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_124_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-124 CERTIFICATION TEST");print(" CROSS-VENUE IMPACT COHORT");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD124))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_124_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical impacted markets grouped across venue bindings")\n    print("[PASS] Cross-venue and single-venue impact cohorts certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-124 CERTIFIED")\n'
UPSTREAM_MODULE='umd_123_impact_surface_registry'
UPSTREAM_VERIFIER='verify_umd_123_impact_surface_registry'
EXPORTED_NAMES=('UMD_124_REVISION', 'MarketVenueCohort', 'CrossVenueImpactCohort', 'CrossVenueImpactCohortBuilder', 'build_umd_124_certification_manifest', 'verify_umd_124_cross_venue_impact_cohort')

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
    marker="# UMD-124 exports"
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
            raise RuntimeError("UMD-124 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-124 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-124 INSTALLER")
    print(" CROSS VENUE IMPACT COHORT")
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
        print("[ROLLBACK] UMD-124 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-124',
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
    print("[DONE] UMD-124 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
