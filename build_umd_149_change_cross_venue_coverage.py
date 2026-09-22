from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_149_CHANGE_CROSS_VENUE_COVERAGE_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_149_change_cross_venue_coverage.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_149_change_cross_venue_coverage.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry\nfrom .umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry\nfrom .umd_148_change_topology_projection import verify_umd_148_change_topology_projection\n\nUMD_149_BUILD_ID="UMD-149"\nUMD_149_REVISION="UMD_149_CHANGE_CROSS_VENUE_COVERAGE_V1"\nUMD_149_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ChangeMarketVenueCoverage:\n    canonical_market_id:str\n    venue_keys:Tuple[str,...]\n    venue_market_ids:Tuple[Tuple[str,str],...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"venue_keys",tuple(self.venue_keys))\n        object.__setattr__(self,"venue_market_ids",tuple(self.venue_market_ids))\n        if self.venue_keys!=tuple(sorted(set(self.venue_keys))):\n            raise ValueError("venue_keys must be unique and sorted")\n        if self.venue_market_ids!=tuple(sorted(set(self.venue_market_ids))):\n            raise ValueError("venue_market_ids must be unique and sorted")\n        if tuple(sorted({v for v,_ in self.venue_market_ids}))!=self.venue_keys:\n            raise ValueError("venue_keys must match venue_market_ids")\n\n    @property\n    def cross_venue(self)->bool:\n        return len(self.venue_keys)>1\n\n    @property\n    def coverage_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "venue_keys":self.venue_keys,\n            "venue_market_ids":self.venue_market_ids,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ChangeCrossVenueCoverage:\n    change_hash:str\n    markets:Tuple[ChangeMarketVenueCoverage,...]\n    missing_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"markets",tuple(self.markets))\n        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))\n        if self.markets!=tuple(sorted(self.markets,key=lambda m:(m.canonical_market_id,m.coverage_hash))):\n            raise ValueError("markets must be deterministically sorted")\n        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):\n            raise ValueError("missing_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_149_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-149")\n\n    def cross_venue_market_ids(self)->Tuple[str,...]:\n        return tuple(m.canonical_market_id for m in self.markets if m.cross_venue)\n\n    @property\n    def coverage_hash(self)->str:\n        return deterministic_sha256({\n            "change_hash":self.change_hash,\n            "market_hashes":tuple(m.coverage_hash for m in self.markets),\n            "missing_market_ids":self.missing_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ChangeCrossVenueCoverageBuilder:\n    __slots__=("impact_registry","market_registry")\n\n    def __init__(self,impact_registry:ObservationChangeImpactRegistry,market_registry:CanonicalMarketRegistry):\n        if not isinstance(impact_registry,ObservationChangeImpactRegistry):\n            raise TypeError("impact_registry must be ObservationChangeImpactRegistry")\n        if not isinstance(market_registry,CanonicalMarketRegistry):\n            raise TypeError("market_registry must be CanonicalMarketRegistry")\n        self.impact_registry=impact_registry\n        self.market_registry=market_registry\n\n    def build(self,change_hash:str,*,lineage:ImmutableLineage)->ChangeCrossVenueCoverage:\n        market_ids=tuple(sorted({\n            market_id for market_id,changes in self.impact_registry.market_index.items()\n            if change_hash in changes\n        }))\n        result=[]; missing=[]\n\n        for market_id in market_ids:\n            record=self.market_registry.get(market_id)\n            if record is None:\n                missing.append(market_id)\n                continue\n            pairs=tuple(sorted({\n                (binding.venue_key,binding.venue_market_id)\n                for binding in record.venue_bindings\n            }))\n            venues=tuple(sorted({v for v,_ in pairs}))\n            result.append(ChangeMarketVenueCoverage(market_id,venues,pairs))\n\n        result.sort(key=lambda m:(m.canonical_market_id,m.coverage_hash))\n        return ChangeCrossVenueCoverage(change_hash,tuple(result),tuple(sorted(missing)),lineage)\n\ndef build_umd_149_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_149_BUILD_ID,"revision":UMD_149_REVISION,\n        "schema_version":UMD_149_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-147","UMD-148"),\n        "mode":"deterministic_read_only_change_cross_venue_coverage",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_149_change_cross_venue_coverage()->bool:\n    if verify_umd_148_change_topology_projection() is not True:\n        return False\n    m=build_umd_149_certification_manifest()\n    return m["build_id"]=="UMD-149" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_147_observation_change_impact_registry import ObservationChangeImpactRegistry\nfrom qseries_v2.universal_market_discovery.umd_149_change_cross_venue_coverage import *\n\nFIXED=datetime(2026,8,10,9,10,tzinfo=timezone.utc)\n\ndef record(cid,ih,bindings):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://149/102",),created_at=FIXED)\n    return CanonicalMarketRecord(cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l)\n\ndef market_registry():\n    a=record("m1","a"*64,(\n        VenueMarketBinding("kalshi","K1","a"*64),\n        VenueMarketBinding("polymarket","P1","b"*64),\n    ))\n    b=record("m2","c"*64,(VenueMarketBinding("kalshi","K2","c"*64),))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),\n        source_refs=("fixture://149/103",),created_at=FIXED)\n    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)\n\ndef impacts():\n    ch="1"*64\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-147",revision="UMD_147_OBSERVATION_CHANGE_IMPACT_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://149/147",),created_at=FIXED)\n    return ObservationChangeImpactRegistry((),{"m1":(ch,),"m2":(ch,),"missing":(ch,)},{},{},l),ch\n\ndef lineage(ch):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-149",revision=UMD_149_REVISION,\n        schema_version="1.0.0",parent_hashes=(ch,),source_refs=("fixture://149",),created_at=FIXED)\n\nclass TestUMD149(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_149_change_cross_venue_coverage())\n    def test_cross_venue(self):\n        ir,ch=impacts()\n        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))\n        self.assertEqual(c.cross_venue_market_ids(),("m1",))\n    def test_single_venue(self):\n        ir,ch=impacts()\n        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))\n        m=next(x for x in c.markets if x.canonical_market_id=="m2")\n        self.assertFalse(m.cross_venue)\n    def test_missing_market(self):\n        ir,ch=impacts()\n        c=ChangeCrossVenueCoverageBuilder(ir,market_registry()).build(ch,lineage=lineage(ch))\n        self.assertEqual(c.missing_market_ids,("missing",))\n    def test_deterministic(self):\n        ir,ch=impacts(); b=ChangeCrossVenueCoverageBuilder(ir,market_registry()); l=lineage(ch)\n        a=b.build(ch,lineage=l); c=b.build(ch,lineage=l)\n        self.assertEqual(a.coverage_hash,c.coverage_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): ChangeCrossVenueCoverageBuilder(object(),market_registry())\n    def test_side_effects(self):\n        m=build_umd_149_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-149 CERTIFICATION TEST");print(" CHANGE CROSS-VENUE COVERAGE");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD149))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_149_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] World-state changes projected across canonical market venue bindings")\n    print("[PASS] Cross-venue, single-venue, and missing-market coverage certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-149 CERTIFIED")\n'
UPSTREAM_MODULE='umd_148_change_topology_projection'
UPSTREAM_VERIFIER='verify_umd_148_change_topology_projection'
EXPORTED_NAMES=('UMD_149_REVISION', 'ChangeMarketVenueCoverage', 'ChangeCrossVenueCoverage', 'ChangeCrossVenueCoverageBuilder', 'build_umd_149_certification_manifest', 'verify_umd_149_change_cross_venue_coverage')

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
    marker="# UMD-149 exports"
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
            raise RuntimeError("UMD-149 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-149 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-149 INSTALLER")
    print(" CHANGE CROSS VENUE COVERAGE")
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
        print("[ROLLBACK] UMD-149 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-149',
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
    print("[DONE] UMD-149 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
