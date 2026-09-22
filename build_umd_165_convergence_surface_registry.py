from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_165_CONVERGENCE_SURFACE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_165_convergence_surface_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_165_convergence_surface_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_163_convergence_topology_projection import ConvergenceTopologyProjection\nfrom .umd_164_convergence_venue_projection import ConvergenceVenueProjection,verify_umd_164_convergence_venue_projection\n\nUMD_165_BUILD_ID="UMD-165"\nUMD_165_REVISION="UMD_165_CONVERGENCE_SURFACE_REGISTRY_V1"\nUMD_165_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ConvergenceSurfaceRegistry:\n    topology_projections:Tuple[ConvergenceTopologyProjection,...]\n    venue_projections:Tuple[ConvergenceVenueProjection,...]\n    market_index:Mapping[str,Tuple[str,...]]\n    ladder_index:Mapping[str,Tuple[str,...]]\n    partition_index:Mapping[str,Tuple[str,...]]\n    venue_index:Mapping[str,Tuple[str,...]]\n    change_type_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"topology_projections",tuple(self.topology_projections))\n        object.__setattr__(self,"venue_projections",tuple(self.venue_projections))\n        for name in ("market_index","ladder_index","partition_index","venue_index","change_type_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.topology_projections!=tuple(sorted(self.topology_projections,key=lambda p:p.projection_hash)):\n            raise ValueError("topology projections must be deterministically sorted")\n        if self.venue_projections!=tuple(sorted(self.venue_projections,key=lambda p:p.projection_hash)):\n            raise ValueError("venue projections must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_165_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-165")\n        required={p.projection_hash for p in self.topology_projections}|{p.projection_hash for p in self.venue_projections}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every convergence surface projection hash")\n\n    def change_types_for_market(self,market_id:str)->Tuple[str,...]:\n        return self.market_index.get(market_id,())\n\n    def markets_for_ladder(self,ladder_hash:str)->Tuple[str,...]:\n        return self.ladder_index.get(ladder_hash,())\n\n    def markets_for_partition(self,partition_hash:str)->Tuple[str,...]:\n        return self.partition_index.get(partition_hash,())\n\n    def markets_for_venue(self,venue_key:str)->Tuple[str,...]:\n        return self.venue_index.get(venue_key,())\n\n    def markets_for_change_type(self,change_type:str)->Tuple[str,...]:\n        return self.change_type_index.get(change_type,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "topology_projection_hashes":tuple(p.projection_hash for p in self.topology_projections),\n            "venue_projection_hashes":tuple(p.projection_hash for p in self.venue_projections),\n            "market_index":self.market_index,\n            "ladder_index":self.ladder_index,\n            "partition_index":self.partition_index,\n            "venue_index":self.venue_index,\n            "change_type_index":self.change_type_index,\n            "lineage":self.lineage,\n        })\n\nclass ConvergenceSurfaceRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        topology_projections:Iterable[ConvergenceTopologyProjection],\n        venue_projections:Iterable[ConvergenceVenueProjection],\n        *,\n        lineage_factory,\n    )->ConvergenceSurfaceRegistry:\n        tps=tuple(topology_projections)\n        vps=tuple(venue_projections)\n        if any(not isinstance(p,ConvergenceTopologyProjection) for p in tps):\n            raise TypeError("topology_projections must contain ConvergenceTopologyProjection")\n        if any(not isinstance(p,ConvergenceVenueProjection) for p in vps):\n            raise TypeError("venue_projections must contain ConvergenceVenueProjection")\n\n        tps=tuple(sorted(tps,key=lambda p:p.projection_hash))\n        vps=tuple(sorted(vps,key=lambda p:p.projection_hash))\n\n        market={}; ladder={}; partition={}; venue={}; change_type={}\n\n        for p in tps:\n            for market_id,types in p.market_to_change_types.items():\n                market.setdefault(market_id,[]).extend(types)\n                for t in types:\n                    change_type.setdefault(t,[]).append(market_id)\n            for market_id,hashes in p.market_to_ladders.items():\n                for h in hashes:\n                    ladder.setdefault(h,[]).append(market_id)\n            for market_id,hashes in p.market_to_partitions.items():\n                for h in hashes:\n                    partition.setdefault(h,[]).append(market_id)\n\n        for p in vps:\n            for binding in p.bindings:\n                venue.setdefault(binding.venue_key,[]).append(binding.canonical_market_id)\n                market.setdefault(binding.canonical_market_id,[]).extend(binding.change_types)\n                for t in binding.change_types:\n                    change_type.setdefault(t,[]).append(binding.canonical_market_id)\n\n        for index in (market,ladder,partition,venue,change_type):\n            for key,items in index.items():\n                index[key]=tuple(sorted(set(items)))\n\n        parents=tuple(p.projection_hash for p in tps)+tuple(p.projection_hash for p in vps)\n        lineage=lineage_factory(parents)\n        return ConvergenceSurfaceRegistry(tps,vps,market,ladder,partition,venue,change_type,lineage)\n\ndef build_umd_165_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_165_BUILD_ID,"revision":UMD_165_REVISION,\n        "schema_version":UMD_165_SCHEMA_VERSION,"upstream_builds":("UMD-163","UMD-164"),\n        "mode":"deterministic_read_only_convergence_surface_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_165_convergence_surface_registry()->bool:\n    if verify_umd_164_convergence_venue_projection() is not True:\n        return False\n    m=build_umd_165_certification_manifest()\n    return m["build_id"]=="UMD-165" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_163_convergence_topology_projection import ConvergenceTopologyProjection\nfrom qseries_v2.universal_market_discovery.umd_164_convergence_venue_projection import ConvergenceVenueBinding,ConvergenceVenueProjection\nfrom qseries_v2.universal_market_discovery.umd_165_convergence_surface_registry import *\n\nFIXED=datetime(2026,8,10,14,20,tzinfo=timezone.utc)\nL="a"*64; P="b"*64\n\ndef tp():\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-163",revision="UMD_163_CONVERGENCE_TOPOLOGY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://165/163",),created_at=FIXED)\n    return ConvergenceTopologyProjection(\n        ("m1","m2"),(L,),(P,),\n        {"m1":("convergence-added",),"m2":("convergence-composition-changed",)},\n        {"m1":(L,),"m2":(L,)},{"m2":(P,)},l\n    )\n\ndef vp():\n    b1=ConvergenceVenueBinding("m1","kalshi","K1",("convergence-added",))\n    b2=ConvergenceVenueBinding("m1","polymarket","P1",("convergence-added",))\n    b3=ConvergenceVenueBinding("m2","kalshi","K2",("convergence-composition-changed",))\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-164",revision="UMD_164_CONVERGENCE_VENUE_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(),source_refs=("fixture://165/164",),created_at=FIXED)\n    return ConvergenceVenueProjection(tuple(sorted((b1,b2,b3),key=lambda b:(b.canonical_market_id,b.venue_key,b.venue_market_id,b.binding_hash))),(),l)\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-165",revision=UMD_165_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://165",),created_at=FIXED)\n\nclass TestUMD165(unittest.TestCase):\n    def setUp(self):\n        self.r=ConvergenceSurfaceRegistryBuilder().build((tp(),),(vp(),),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_165_convergence_surface_registry())\n    def test_market_query(self):\n        self.assertEqual(self.r.change_types_for_market("m1"),("convergence-added",))\n    def test_ladder_query(self):\n        self.assertEqual(self.r.markets_for_ladder(L),("m1","m2"))\n    def test_partition_query(self):\n        self.assertEqual(self.r.markets_for_partition(P),("m2",))\n    def test_venue_query(self):\n        self.assertEqual(self.r.markets_for_venue("kalshi"),("m1","m2"))\n        self.assertEqual(self.r.markets_for_venue("polymarket"),("m1",))\n    def test_change_type_query(self):\n        self.assertEqual(self.r.markets_for_change_type("convergence-composition-changed"),("m2",))\n    def test_unknown(self):\n        self.assertEqual(self.r.markets_for_venue("missing"),())\n    def test_deterministic(self):\n        x=ConvergenceSurfaceRegistryBuilder().build((tp(),),(vp(),),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ConvergenceSurfaceRegistryBuilder().build((),(),lineage_factory=lf)\n        self.assertEqual(x.topology_projections,())\n        self.assertEqual(x.venue_projections,())\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ConvergenceSurfaceRegistryBuilder().build((object(),),(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_165_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-165 CERTIFICATION TEST");print(" CONVERGENCE SURFACE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD165))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_165_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Convergence surface queries by market, ladder, partition, venue, and change type certified")\n    print("[PASS] Temporal convergence is now structurally located across certified market and venue surfaces")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-165 CERTIFIED")\n'
UPSTREAM_MODULE='umd_164_convergence_venue_projection'
UPSTREAM_VERIFIER='verify_umd_164_convergence_venue_projection'
EXPORTED_NAMES=('UMD_165_REVISION', 'ConvergenceSurfaceRegistry', 'ConvergenceSurfaceRegistryBuilder', 'build_umd_165_certification_manifest', 'verify_umd_165_convergence_surface_registry')

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
    marker="# UMD-165 exports"
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
            raise RuntimeError("UMD-165 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-165 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-165 INSTALLER")
    print(" CONVERGENCE SURFACE REGISTRY")
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
        print("[ROLLBACK] UMD-165 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-165',
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
    print("[DONE] UMD-165 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
