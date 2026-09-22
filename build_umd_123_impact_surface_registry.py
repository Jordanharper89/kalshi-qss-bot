from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_123_IMPACT_SURFACE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_123_impact_surface_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_123_impact_surface_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable, Mapping, Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_121_impact_family_projection import FamilyImpactProjection\nfrom .umd_122_impact_venue_projection import VenueImpactProjection, verify_umd_122_impact_venue_projection\n\nUMD_123_BUILD_ID="UMD-123"\nUMD_123_REVISION="UMD_123_IMPACT_SURFACE_REGISTRY_V1"\nUMD_123_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze_index(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ImpactSurface:\n    observation_hash:str\n    family_keys:Tuple[str,...]\n    canonical_market_ids:Tuple[str,...]\n    venue_keys:Tuple[str,...]\n    family_projection_hash:str\n    venue_projection_hash:str\n\n    def __post_init__(self):\n        for name in ("family_keys","canonical_market_ids","venue_keys"):\n            value=tuple(getattr(self,name))\n            if value!=tuple(sorted(set(value))):\n                raise ValueError(f"{name} must be unique and sorted")\n            object.__setattr__(self,name,value)\n\n    @property\n    def surface_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "family_keys":self.family_keys,\n            "canonical_market_ids":self.canonical_market_ids,\n            "venue_keys":self.venue_keys,\n            "family_projection_hash":self.family_projection_hash,\n            "venue_projection_hash":self.venue_projection_hash,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ImpactSurfaceRegistry:\n    surfaces:Tuple[ImpactSurface,...]\n    observation_index:Mapping[str,Tuple[str,...]]\n    family_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    market_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"surfaces",tuple(self.surfaces))\n        for name in ("observation_index","family_index","venue_index","market_index"):\n            object.__setattr__(self,name,_freeze_index(getattr(self,name)))\n        if tuple(sorted(self.surfaces,key=lambda s:(s.observation_hash,s.surface_hash)))!=self.surfaces:\n            raise ValueError("surfaces must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_123_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-123")\n        required={s.surface_hash for s in self.surfaces}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every surface hash")\n\n    def observations_for_venue(self,venue_key:str)->Tuple[str,...]:\n        return self.venue_index.get(venue_key,())\n\n    def observations_for_family(self,family_key:str)->Tuple[str,...]:\n        return self.family_index.get(family_key,())\n\n    def observations_for_market(self,canonical_market_id:str)->Tuple[str,...]:\n        return self.market_index.get(canonical_market_id,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "surface_hashes":tuple(s.surface_hash for s in self.surfaces),\n            "observation_index":self.observation_index,\n            "family_index":self.family_index,\n            "venue_index":self.venue_index,\n            "market_index":self.market_index,\n            "lineage":self.lineage,\n        })\n\nclass ImpactSurfaceRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        pairs:Iterable[tuple[FamilyImpactProjection,VenueImpactProjection]],\n        *,\n        lineage_factory,\n    )->ImpactSurfaceRegistry:\n        surfaces=[]\n        observation={}\n        family={}\n        venue={}\n        market={}\n\n        for family_projection,venue_projection in pairs:\n            if not isinstance(family_projection,FamilyImpactProjection):\n                raise TypeError("family projection must be FamilyImpactProjection")\n            if not isinstance(venue_projection,VenueImpactProjection):\n                raise TypeError("venue projection must be VenueImpactProjection")\n            if family_projection.observation_hash!=venue_projection.observation_hash:\n                raise ValueError("projection observation hashes do not match")\n\n            family_keys=tuple(sorted(x.family_key for x in family_projection.family_impacts))\n            markets=set(family_projection.unmatched_market_ids)\n            for impact in family_projection.family_impacts:\n                markets.update(impact.impacted_market_ids)\n            venue_keys=venue_projection.venues()\n\n            surface=ImpactSurface(\n                family_projection.observation_hash,\n                family_keys,\n                tuple(sorted(markets)),\n                venue_keys,\n                family_projection.projection_hash,\n                venue_projection.projection_hash,\n            )\n            surfaces.append(surface)\n\n            observation.setdefault(surface.observation_hash,[]).append(surface.surface_hash)\n            for key in surface.family_keys:\n                family.setdefault(key,[]).append(surface.observation_hash)\n            for key in surface.venue_keys:\n                venue.setdefault(key,[]).append(surface.observation_hash)\n            for key in surface.canonical_market_ids:\n                market.setdefault(key,[]).append(surface.observation_hash)\n\n        surfaces.sort(key=lambda s:(s.observation_hash,s.surface_hash))\n        for index in (observation,family,venue,market):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        lineage=lineage_factory(tuple(s.surface_hash for s in surfaces))\n        return ImpactSurfaceRegistry(tuple(surfaces),observation,family,venue,market,lineage)\n\ndef build_umd_123_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_123_BUILD_ID,"revision":UMD_123_REVISION,\n        "schema_version":UMD_123_SCHEMA_VERSION,"upstream_builds":("UMD-121","UMD-122"),\n        "mode":"deterministic_read_only_impact_surface_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_123_impact_surface_registry()->bool:\n    if verify_umd_122_impact_venue_projection() is not True:\n        return False\n    m=build_umd_123_certification_manifest()\n    return m["build_id"]=="UMD-123" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_121_impact_family_projection import FamilyImpact,FamilyImpactProjection\nfrom qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import VenueImpactBinding,VenueImpactProjection\nfrom qseries_v2.universal_market_discovery.umd_123_impact_surface_registry import *\n\nFIXED=datetime(2026,8,9,21,20,tzinfo=timezone.utc)\n\ndef pair(obs_hash="a"*64):\n    l121=ImmutableLineage(subsystem_id="UMD",build_id="UMD-121",revision="UMD_121_IMPACT_FAMILY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://123/121",),created_at=FIXED)\n    fp=FamilyImpactProjection(\n        obs_hash,\n        (FamilyImpact("asset=bitcoin","b"*64,("m1","m2"),("m1",),("m2",)),),\n        ("m3",),\n        l121\n    )\n    l122=ImmutableLineage(subsystem_id="UMD",build_id="UMD-122",revision="UMD_122_IMPACT_VENUE_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://123/122",),created_at=FIXED)\n    vp=VenueImpactProjection(\n        obs_hash,\n        (\n            VenueImpactBinding("kalshi","K-1","m1",True),\n            VenueImpactBinding("kalshi","K-2","m2",False),\n            VenueImpactBinding("polymarket","P-1","m1",True),\n        ),\n        ("m3",),\n        l122\n    )\n    return fp,vp\n\ndef lineage_factory(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-123",revision=UMD_123_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://123",),created_at=FIXED)\n\nclass TestUMD123(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_123_impact_surface_registry())\n    def test_surface_build(self):\n        fp,vp=pair()\n        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)\n        s=r.surfaces[0]\n        self.assertEqual(s.family_keys,("asset=bitcoin",))\n        self.assertEqual(s.canonical_market_ids,("m1","m2","m3"))\n        self.assertEqual(s.venue_keys,("kalshi","polymarket"))\n    def test_venue_reverse_query(self):\n        fp,vp=pair()\n        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)\n        self.assertEqual(r.observations_for_venue("kalshi"),("a"*64,))\n    def test_family_reverse_query(self):\n        fp,vp=pair()\n        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)\n        self.assertEqual(r.observations_for_family("asset=bitcoin"),("a"*64,))\n    def test_market_reverse_query(self):\n        fp,vp=pair()\n        r=ImpactSurfaceRegistryBuilder().build(((fp,vp),),lineage_factory=lineage_factory)\n        self.assertEqual(r.observations_for_market("m3"),("a"*64,))\n    def test_mismatch_rejected(self):\n        fp,vp=pair()\n        wrong=VenueImpactProjection("b"*64,vp.bindings,vp.missing_market_ids,vp.lineage)\n        with self.assertRaises(ValueError):\n            ImpactSurfaceRegistryBuilder().build(((fp,wrong),),lineage_factory=lineage_factory)\n    def test_deterministic(self):\n        a1,b1=pair("a"*64)\n        a2,b2=pair("b"*64)\n        x=ImpactSurfaceRegistryBuilder().build(((a1,b1),(a2,b2)),lineage_factory=lineage_factory)\n        y=ImpactSurfaceRegistryBuilder().build(((a2,b2),(a1,b1)),lineage_factory=lineage_factory)\n        self.assertEqual(x.registry_hash,y.registry_hash)\n    def test_empty(self):\n        r=ImpactSurfaceRegistryBuilder().build((),lineage_factory=lineage_factory)\n        self.assertEqual(r.surfaces,())\n    def test_side_effects(self):\n        m=build_umd_123_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-123 CERTIFICATION TEST");print(" IMPACT SURFACE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD123))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_123_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Observation impact surface across families, canonical markets, and venues certified")\n    print("[PASS] Reverse queries by venue, family, and market certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-123 CERTIFIED")\n'
UPSTREAM_MODULE='umd_122_impact_venue_projection'
UPSTREAM_VERIFIER='verify_umd_122_impact_venue_projection'
EXPORTED_NAMES=('UMD_123_REVISION', 'ImpactSurface', 'ImpactSurfaceRegistry', 'ImpactSurfaceRegistryBuilder', 'build_umd_123_certification_manifest', 'verify_umd_123_impact_surface_registry')

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
    marker="# UMD-123 exports"
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
            raise RuntimeError("UMD-123 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-123 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-123 INSTALLER")
    print(" IMPACT SURFACE REGISTRY")
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
        print("[ROLLBACK] UMD-123 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-123',
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
    print("[DONE] UMD-123 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
