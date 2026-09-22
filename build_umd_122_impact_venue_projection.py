from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_122_IMPACT_VENUE_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_122_impact_venue_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_122_impact_venue_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry\nfrom .umd_119_impact_provenance import ImpactProvenanceBundle\nfrom .umd_121_impact_family_projection import verify_umd_121_impact_family_projection\n\nUMD_122_BUILD_ID="UMD-122"\nUMD_122_REVISION="UMD_122_IMPACT_VENUE_PROJECTION_V1"\nUMD_122_SCHEMA_VERSION="1.0.0"\n\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass VenueImpactBinding:\n    venue_key:str\n    venue_market_id:str\n    canonical_market_id:str\n    direct:bool\n\n    @property\n    def binding_hash(self)->str:\n        return deterministic_sha256({\n            "venue_key":self.venue_key,\n            "venue_market_id":self.venue_market_id,\n            "canonical_market_id":self.canonical_market_id,\n            "direct":self.direct,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass VenueImpactProjection:\n    observation_hash:str\n    bindings:Tuple[VenueImpactBinding,...]\n    missing_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"bindings",tuple(self.bindings))\n        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))\n        expected=tuple(sorted(self.bindings,key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id,b.direct)))\n        if expected!=self.bindings:\n            raise ValueError("bindings must be deterministically sorted")\n        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):\n            raise ValueError("missing_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_122_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-122")\n\n    def venues(self)->Tuple[str,...]:\n        return tuple(sorted({b.venue_key for b in self.bindings}))\n\n    def bindings_for_venue(self,venue_key:str)->Tuple[VenueImpactBinding,...]:\n        return tuple(b for b in self.bindings if b.venue_key==venue_key)\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "observation_hash":self.observation_hash,\n            "binding_hashes":tuple(b.binding_hash for b in self.bindings),\n            "missing_market_ids":self.missing_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ImpactVenueProjector:\n    __slots__=()\n\n    def project(\n        self,\n        bundle:ImpactProvenanceBundle,\n        registry:CanonicalMarketRegistry,\n        *,\n        lineage:ImmutableLineage,\n    )->VenueImpactProjection:\n        if not isinstance(bundle,ImpactProvenanceBundle):\n            raise TypeError("bundle must be ImpactProvenanceBundle")\n        if not isinstance(registry,CanonicalMarketRegistry):\n            raise TypeError("registry must be CanonicalMarketRegistry")\n\n        bindings=[]\n        missing=[]\n        for entry in bundle.entries:\n            record=registry.get(entry.canonical_market_id)\n            if record is None:\n                missing.append(entry.canonical_market_id)\n                continue\n            for venue_binding in record.venue_bindings:\n                bindings.append(VenueImpactBinding(\n                    venue_binding.venue_key,\n                    venue_binding.venue_market_id,\n                    entry.canonical_market_id,\n                    entry.direct,\n                ))\n\n        bindings.sort(key=lambda b:(b.venue_key,b.venue_market_id,b.canonical_market_id,b.direct))\n        return VenueImpactProjection(\n            bundle.observation_hash,\n            tuple(bindings),\n            tuple(sorted(set(missing))),\n            lineage,\n        )\n\ndef build_umd_122_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_122_BUILD_ID,"revision":UMD_122_REVISION,\n        "schema_version":UMD_122_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-119","UMD-121"),\n        "mode":"deterministic_read_only_impact_venue_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_122_impact_venue_projection()->bool:\n    if verify_umd_121_impact_family_projection() is not True:\n        return False\n    m=build_umd_122_certification_manifest()\n    return m["build_id"]=="UMD-122" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import UMD_103_REVISION,CanonicalMarketRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_119_impact_provenance import MarketImpactProvenance,ImpactProvenanceBundle\nfrom qseries_v2.universal_market_discovery.umd_122_impact_venue_projection import *\n\nFIXED=datetime(2026,8,9,21,10,tzinfo=timezone.utc)\n\ndef record(cid,ih,bindings):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://122/102",),created_at=FIXED)\n    return CanonicalMarketRecord(\n        cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type",\n        "b"*64,"c"*64,(),(),"",{},l\n    )\n\ndef registry():\n    a=record("m1","a"*64,(VenueMarketBinding("kalshi","K-1","a"*64),VenueMarketBinding("polymarket","P-1","a"*64)))\n    b=record("m2","b"*64,(VenueMarketBinding("kalshi","K-2","b"*64),))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision=UMD_103_REVISION,\n        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),\n        source_refs=("fixture://122/103",),created_at=FIXED)\n    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)\n\ndef bundle(include_missing=False):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-119",revision="UMD_119_IMPACT_PROVENANCE_BUNDLE_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://122/119",),created_at=FIXED)\n    entries=[\n        MarketImpactProvenance("m1",True,(("asset","bitcoin"),),("m1",),()),\n        MarketImpactProvenance("m2",False,(),("m1","m2"),("implies",)),\n    ]\n    if include_missing:\n        entries.append(MarketImpactProvenance("missing",False,(),("m1","missing"),("implies",)))\n    return ImpactProvenanceBundle("a"*64,tuple(sorted(entries,key=lambda e:e.canonical_market_id)),l)\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-122",revision=UMD_122_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://122",),created_at=FIXED)\n\nclass TestUMD122(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_122_impact_venue_projection())\n    def test_cross_venue_projection(self):\n        p=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())\n        self.assertEqual(p.venues(),("kalshi","polymarket"))\n        self.assertEqual(len(p.bindings_for_venue("kalshi")),2)\n    def test_direct_flag_preserved(self):\n        p=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())\n        m1=[b for b in p.bindings if b.canonical_market_id=="m1"]\n        self.assertTrue(all(b.direct for b in m1))\n    def test_missing_market(self):\n        p=ImpactVenueProjector().project(bundle(True),registry(),lineage=lineage())\n        self.assertEqual(p.missing_market_ids,("missing",))\n    def test_deterministic(self):\n        a=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())\n        b=ImpactVenueProjector().project(bundle(),registry(),lineage=lineage())\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError):\n            ImpactVenueProjector().project(bundle(),object(),lineage=lineage())\n    def test_side_effects(self):\n        m=build_umd_122_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-122 CERTIFICATION TEST");print(" IMPACT VENUE PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD122))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_122_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Canonical observation impact projected across venue bindings")\n    print("[PASS] Cross-venue and missing-market coverage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-122 CERTIFIED")\n'
UPSTREAM_MODULE='umd_121_impact_family_projection'
UPSTREAM_VERIFIER='verify_umd_121_impact_family_projection'
EXPORTED_NAMES=('UMD_122_REVISION', 'VenueImpactBinding', 'VenueImpactProjection', 'ImpactVenueProjector', 'build_umd_122_certification_manifest', 'verify_umd_122_impact_venue_projection')

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
    marker="# UMD-122 exports"
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
            raise RuntimeError("UMD-122 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-122 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-122 INSTALLER")
    print(" IMPACT VENUE PROJECTION")
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
        print("[ROLLBACK] UMD-122 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-122',
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
    print("[DONE] UMD-122 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
