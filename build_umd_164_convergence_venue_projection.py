from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_164_CONVERGENCE_VENUE_PROJECTION_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_164_convergence_venue_projection.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_164_convergence_venue_projection.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_103_canonical_market_registry import CanonicalMarketRegistry\nfrom .umd_163_convergence_topology_projection import ConvergenceTopologyProjection,verify_umd_163_convergence_topology_projection\n\nUMD_164_BUILD_ID="UMD-164"\nUMD_164_REVISION="UMD_164_CONVERGENCE_VENUE_PROJECTION_V1"\nUMD_164_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceVenueBinding:\n    canonical_market_id:str\n    venue_key:str\n    venue_market_id:str\n    change_types:Tuple[str,...]\n\n    def __post_init__(self):\n        object.__setattr__(self,"change_types",tuple(self.change_types))\n        if self.change_types!=tuple(sorted(set(self.change_types))):\n            raise ValueError("change_types must be unique and sorted")\n        if not self.canonical_market_id or not self.venue_key or not self.venue_market_id:\n            raise ValueError("venue binding fields must be non-empty")\n\n    @property\n    def binding_hash(self)->str:\n        return deterministic_sha256({\n            "canonical_market_id":self.canonical_market_id,\n            "venue_key":self.venue_key,\n            "venue_market_id":self.venue_market_id,\n            "change_types":self.change_types,\n        })\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceVenueProjection:\n    bindings:Tuple[ConvergenceVenueBinding,...]\n    missing_market_ids:Tuple[str,...]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"bindings",tuple(self.bindings))\n        object.__setattr__(self,"missing_market_ids",tuple(self.missing_market_ids))\n        if self.bindings!=tuple(sorted(\n            self.bindings,key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash)\n        )):\n            raise ValueError("bindings must be deterministically sorted")\n        if self.missing_market_ids!=tuple(sorted(set(self.missing_market_ids))):\n            raise ValueError("missing_market_ids must be unique and sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_164_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-164")\n\n    def venues_for_market(self,market_id:str)->Tuple[str,...]:\n        return tuple(sorted({b.venue_key for b in self.bindings if b.canonical_market_id==market_id}))\n\n    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:\n        return tuple(sorted({b.canonical_market_id for b in self.bindings if b.venue_key==venue_key}))\n\n    @property\n    def projection_hash(self)->str:\n        return deterministic_sha256({\n            "binding_hashes":tuple(b.binding_hash for b in self.bindings),\n            "missing_market_ids":self.missing_market_ids,\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceVenueProjector:\n    __slots__=("market_registry",)\n\n    def __init__(self,market_registry:CanonicalMarketRegistry):\n        if not isinstance(market_registry,CanonicalMarketRegistry):\n            raise TypeError("market_registry must be CanonicalMarketRegistry")\n        self.market_registry=market_registry\n\n    def project(\n        self,\n        topology_projection:ConvergenceTopologyProjection,\n        *,\n        lineage:ImmutableLineage,\n    )->ConvergenceVenueProjection:\n        if not isinstance(topology_projection,ConvergenceTopologyProjection):\n            raise TypeError("topology_projection must be ConvergenceTopologyProjection")\n\n        bindings=[]; missing=[]\n        for market_id in topology_projection.market_ids:\n            record=self.market_registry.get(market_id)\n            if record is None:\n                missing.append(market_id)\n                continue\n            types=topology_projection.market_to_change_types.get(market_id,())\n            for venue in record.venue_bindings:\n                bindings.append(ConvergenceVenueBinding(\n                    market_id,venue.venue_key,venue.venue_market_id,types\n                ))\n\n        bindings.sort(key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash))\n        return ConvergenceVenueProjection(tuple(bindings),tuple(sorted(missing)),lineage)\n\ndef build_umd_164_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_164_BUILD_ID,"revision":UMD_164_REVISION,\n        "schema_version":UMD_164_SCHEMA_VERSION,"upstream_builds":("UMD-103","UMD-163"),\n        "mode":"deterministic_read_only_convergence_venue_projection",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_164_convergence_venue_projection()->bool:\n    if verify_umd_163_convergence_topology_projection() is not True:\n        return False\n    m=build_umd_164_certification_manifest()\n    return m["build_id"]=="UMD-164" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_102_canonical_market_record import CanonicalMarketRecord,VenueMarketBinding\nfrom qseries_v2.universal_market_discovery.umd_103_canonical_market_registry import CanonicalMarketRegistryBuilder\nfrom qseries_v2.universal_market_discovery.umd_163_convergence_topology_projection import ConvergenceTopologyProjection\nfrom qseries_v2.universal_market_discovery.umd_164_convergence_venue_projection import *\n\nFIXED=datetime(2026,8,10,14,10,tzinfo=timezone.utc)\n\ndef record(cid,ih,bindings):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-102",revision="UMD_102_CANONICAL_MARKET_RECORD_ASSEMBLY_V1",\n        schema_version="1.0.0",parent_hashes=(ih,),source_refs=("fixture://164/102",),created_at=FIXED)\n    return CanonicalMarketRecord(cid,ih,tuple(bindings),"fixture/domain/category/subcategory/type","b"*64,"c"*64,(),(),"",{},l)\n\ndef registry():\n    a=record("m1","a"*64,(\n        VenueMarketBinding("kalshi","K1","a"*64),\n        VenueMarketBinding("polymarket","P1","b"*64),\n    ))\n    b=record("m2","c"*64,(VenueMarketBinding("kalshi","K2","c"*64),))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-103",revision="UMD_103_CANONICAL_MARKET_REGISTRY_V1",\n        schema_version="1.0.0",parent_hashes=(a.record_hash,b.record_hash),\n        source_refs=("fixture://164/103",),created_at=FIXED)\n    return CanonicalMarketRegistryBuilder().build((a,b),lineage=l)\n\ndef topology_projection():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-163",revision="UMD_163_CONVERGENCE_TOPOLOGY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://164/163",),created_at=FIXED)\n    return ConvergenceTopologyProjection(\n        ("m1","m2","missing"),(),(),\n        {"m1":("convergence-added",),"m2":("convergence-composition-changed",),"missing":("convergence-removed",)},\n        {},{},l\n    )\n\ndef lineage():\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-164",revision=UMD_164_REVISION,\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://164",),created_at=FIXED)\n\nclass TestUMD164(unittest.TestCase):\n    def test_foundation(self): self.assertTrue(verify_umd_164_convergence_venue_projection())\n    def test_cross_venue(self):\n        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())\n        self.assertEqual(p.venues_for_market("m1"),("kalshi","polymarket"))\n    def test_single_venue(self):\n        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())\n        self.assertEqual(p.venues_for_market("m2"),("kalshi",))\n    def test_reverse_venue(self):\n        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())\n        self.assertEqual(p.markets_for_venue("kalshi"),("m1","m2"))\n    def test_change_type_preserved(self):\n        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())\n        b=next(x for x in p.bindings if x.canonical_market_id=="m2")\n        self.assertEqual(b.change_types,("convergence-composition-changed",))\n    def test_missing_market(self):\n        p=ConvergenceVenueProjector(registry()).project(topology_projection(),lineage=lineage())\n        self.assertEqual(p.missing_market_ids,("missing",))\n    def test_deterministic(self):\n        projector=ConvergenceVenueProjector(registry()); tp=topology_projection(); l=lineage()\n        a=projector.project(tp,lineage=l); b=projector.project(tp,lineage=l)\n        self.assertEqual(a.projection_hash,b.projection_hash)\n    def test_bad_registry(self):\n        with self.assertRaises(TypeError): ConvergenceVenueProjector(object())\n    def test_side_effects(self):\n        m=build_umd_164_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-164 CERTIFICATION TEST");print(" CONVERGENCE VENUE PROJECTION");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD164))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_164_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Convergence changes projected across exact certified venue bindings")\n    print("[PASS] Cross-venue, single-venue, missing-market, and change-type preservation certified")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-164 CERTIFIED")\n'
UPSTREAM_MODULE='umd_163_convergence_topology_projection'
UPSTREAM_VERIFIER='verify_umd_163_convergence_topology_projection'
EXPORTED_NAMES=('UMD_164_REVISION', 'ConvergenceVenueBinding', 'ConvergenceVenueProjection', 'ConvergenceVenueProjector', 'build_umd_164_certification_manifest', 'verify_umd_164_convergence_venue_projection')

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
    marker="# UMD-164 exports"
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
            raise RuntimeError("UMD-164 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-164 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-164 INSTALLER")
    print(" CONVERGENCE VENUE PROJECTION")
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
        print("[ROLLBACK] UMD-164 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-164',
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
    print("[DONE] UMD-164 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
