from __future__ import annotations
import hashlib, importlib, json, os, sys
from pathlib import Path

REVISION='UMD_150_CHANGE_STRUCTURE_REGISTRY_INSTALLER_V1'
ROOT=Path(__file__).resolve().parent
PKG=ROOT/"qseries_v2"/"universal_market_discovery"
MODULE=PKG/'umd_150_change_structure_registry.py'
INIT=PKG/"__init__.py"
TEST=ROOT/'test_umd_150_change_structure_registry.py'
MODULE_SOURCE='\nfrom __future__ import annotations\n\nfrom dataclasses import dataclass\nfrom types import MappingProxyType\nfrom typing import Iterable,Mapping,Tuple\n\nfrom .universal_market_discovery_foundation import UMD_SUBSYSTEM_ID,ImmutableLineage,deterministic_sha256\nfrom .umd_148_change_topology_projection import ChangeTopologyProjection\nfrom .umd_149_change_cross_venue_coverage import ChangeCrossVenueCoverage,verify_umd_149_change_cross_venue_coverage\n\nUMD_150_BUILD_ID="UMD-150"\nUMD_150_REVISION="UMD_150_CHANGE_STRUCTURE_REGISTRY_V1"\nUMD_150_SCHEMA_VERSION="1.0.0"\nPROHIBITED_CAPABILITIES=("network_invocation","persistence","mutation","publication","execution")\n\ndef _freeze(source):\n    return MappingProxyType({k:tuple(v) for k,v in sorted(source.items())})\n\n@dataclass(frozen=True,slots=True)\nclass ChangeStructureRegistry:\n    topology_projections:Tuple[ChangeTopologyProjection,...]\n    venue_coverages:Tuple[ChangeCrossVenueCoverage,...]\n    ladder_index:Mapping[str,Tuple[str,...]]\n    partition_index:Mapping[str,Tuple[str,...]]\n    cross_venue_market_index:Mapping[str,Tuple[str,...]]\n    market_index:Mapping[str,Tuple[str,...]]\n    lineage:ImmutableLineage\n\n    def __post_init__(self):\n        object.__setattr__(self,"topology_projections",tuple(self.topology_projections))\n        object.__setattr__(self,"venue_coverages",tuple(self.venue_coverages))\n        for name in ("ladder_index","partition_index","cross_venue_market_index","market_index"):\n            object.__setattr__(self,name,_freeze(getattr(self,name)))\n        if self.topology_projections!=tuple(sorted(self.topology_projections,key=lambda p:(p.change_hash,p.projection_hash))):\n            raise ValueError("topology projections must be deterministically sorted")\n        if self.venue_coverages!=tuple(sorted(self.venue_coverages,key=lambda c:(c.change_hash,c.coverage_hash))):\n            raise ValueError("venue coverages must be deterministically sorted")\n        if self.lineage.subsystem_id!=UMD_SUBSYSTEM_ID or self.lineage.build_id!=UMD_150_BUILD_ID:\n            raise ValueError("lineage must belong to UMD-150")\n        required={p.projection_hash for p in self.topology_projections}|{c.coverage_hash for c in self.venue_coverages}\n        if not required.issubset(set(self.lineage.parent_hashes)):\n            raise ValueError("lineage must include every structure artifact hash")\n\n    def changes_for_ladder(self,key:str)->Tuple[str,...]:\n        return self.ladder_index.get(key,())\n    def changes_for_partition(self,key:str)->Tuple[str,...]:\n        return self.partition_index.get(key,())\n    def changes_for_cross_venue_market(self,key:str)->Tuple[str,...]:\n        return self.cross_venue_market_index.get(key,())\n    def changes_for_market(self,key:str)->Tuple[str,...]:\n        return self.market_index.get(key,())\n\n    @property\n    def registry_hash(self)->str:\n        return deterministic_sha256({\n            "projection_hashes":tuple(p.projection_hash for p in self.topology_projections),\n            "coverage_hashes":tuple(c.coverage_hash for c in self.venue_coverages),\n            "ladder_index":self.ladder_index,\n            "partition_index":self.partition_index,\n            "cross_venue_market_index":self.cross_venue_market_index,\n            "market_index":self.market_index,\n            "lineage":self.lineage,\n        })\n\nclass ChangeStructureRegistryBuilder:\n    __slots__=()\n\n    def build(\n        self,\n        projections:Iterable[ChangeTopologyProjection],\n        coverages:Iterable[ChangeCrossVenueCoverage],\n        *,\n        lineage_factory,\n    )->ChangeStructureRegistry:\n        ps=tuple(projections)\n        cs=tuple(coverages)\n        if any(not isinstance(p,ChangeTopologyProjection) for p in ps):\n            raise TypeError("projections must contain ChangeTopologyProjection")\n        if any(not isinstance(c,ChangeCrossVenueCoverage) for c in cs):\n            raise TypeError("coverages must contain ChangeCrossVenueCoverage")\n\n        ps=tuple(sorted(ps,key=lambda p:(p.change_hash,p.projection_hash)))\n        cs=tuple(sorted(cs,key=lambda c:(c.change_hash,c.coverage_hash)))\n\n        ladder={}; partition={}; cross={}; market={}\n\n        for p in ps:\n            for key in p.ladder_hashes:\n                ladder.setdefault(key,[]).append(p.change_hash)\n            for key in p.partition_hashes:\n                partition.setdefault(key,[]).append(p.change_hash)\n            for key in p.market_ids:\n                market.setdefault(key,[]).append(p.change_hash)\n\n        for c in cs:\n            for key in c.cross_venue_market_ids():\n                cross.setdefault(key,[]).append(c.change_hash)\n            for m in c.markets:\n                market.setdefault(m.canonical_market_id,[]).append(c.change_hash)\n\n        for index in (ladder,partition,cross,market):\n            for key,values in index.items():\n                index[key]=tuple(sorted(set(values)))\n\n        parents=tuple(p.projection_hash for p in ps)+tuple(c.coverage_hash for c in cs)\n        lineage=lineage_factory(parents)\n        return ChangeStructureRegistry(ps,cs,ladder,partition,cross,market,lineage)\n\ndef build_umd_150_certification_manifest():\n    data={\n        "subsystem_id":"UMD","build_id":UMD_150_BUILD_ID,"revision":UMD_150_REVISION,\n        "schema_version":UMD_150_SCHEMA_VERSION,"upstream_builds":("UMD-148","UMD-149"),\n        "mode":"deterministic_read_only_change_structure_registry",\n        "prohibited_capabilities":PROHIBITED_CAPABILITIES,\n        "network_enabled":False,"persistence_enabled":False,"mutation_enabled":False,\n        "publication_enabled":False,"execution_enabled":False,\n    }\n    return MappingProxyType({**data,"manifest_hash":deterministic_sha256(data)})\n\ndef verify_umd_150_change_structure_registry()->bool:\n    if verify_umd_149_change_cross_venue_coverage() is not True:\n        return False\n    m=build_umd_150_certification_manifest()\n    return m["build_id"]=="UMD-150" and not any(\n        m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")\n    )\n'
TEST_SOURCE='\nfrom __future__ import annotations\nimport unittest\nfrom datetime import datetime,timezone\n\nfrom qseries_v2.universal_market_discovery.universal_market_discovery_foundation import ImmutableLineage\nfrom qseries_v2.universal_market_discovery.umd_148_change_topology_projection import ChangeTopologyProjection\nfrom qseries_v2.universal_market_discovery.umd_149_change_cross_venue_coverage import ChangeMarketVenueCoverage,ChangeCrossVenueCoverage\nfrom qseries_v2.universal_market_discovery.umd_150_change_structure_registry import *\n\nFIXED=datetime(2026,8,10,9,20,tzinfo=timezone.utc)\n\ndef projection(change,ladder,partition,market):\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-148",revision="UMD_148_CHANGE_TOPOLOGY_PROJECTION_V1",\n        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://150/148",),created_at=FIXED)\n    return ChangeTopologyProjection(change,(market,),(ladder,),(partition,),{market:(ladder,)},{market:(partition,)},l)\n\ndef coverage(change,market,cross=True):\n    pairs=(("kalshi","K1"),("polymarket","P1")) if cross else (("kalshi","K1"),)\n    venues=tuple(v for v,_ in pairs)\n    m=ChangeMarketVenueCoverage(market,venues,pairs)\n    l=ImmutableLineage(subsystem_id="UMD",build_id="UMD-149",revision="UMD_149_CHANGE_CROSS_VENUE_COVERAGE_V1",\n        schema_version="1.0.0",parent_hashes=(change,),source_refs=("fixture://150/149",),created_at=FIXED)\n    return ChangeCrossVenueCoverage(change,(m,),(),l)\n\ndef lf(parents):\n    return ImmutableLineage(subsystem_id="UMD",build_id="UMD-150",revision=UMD_150_REVISION,\n        schema_version="1.0.0",parent_hashes=parents,source_refs=("fixture://150",),created_at=FIXED)\n\nclass TestUMD150(unittest.TestCase):\n    def setUp(self):\n        self.ch1="1"*64; self.ch2="2"*64\n        self.p1=projection(self.ch1,"a"*64,"b"*64,"m1")\n        self.p2=projection(self.ch2,"a"*64,"c"*64,"m2")\n        self.c1=coverage(self.ch1,"m1",True)\n        self.c2=coverage(self.ch2,"m2",False)\n        self.r=ChangeStructureRegistryBuilder().build((self.p2,self.p1),(self.c2,self.c1),lineage_factory=lf)\n\n    def test_foundation(self): self.assertTrue(verify_umd_150_change_structure_registry())\n    def test_ladder_query(self):\n        self.assertEqual(self.r.changes_for_ladder("a"*64),(self.ch1,self.ch2))\n    def test_partition_query(self):\n        self.assertEqual(self.r.changes_for_partition("b"*64),(self.ch1,))\n    def test_cross_venue_query(self):\n        self.assertEqual(self.r.changes_for_cross_venue_market("m1"),(self.ch1,))\n        self.assertEqual(self.r.changes_for_cross_venue_market("m2"),())\n    def test_market_query(self):\n        self.assertEqual(self.r.changes_for_market("m2"),(self.ch2,))\n    def test_deterministic(self):\n        x=ChangeStructureRegistryBuilder().build((self.p1,self.p2),(self.c1,self.c2),lineage_factory=lf)\n        self.assertEqual(self.r.registry_hash,x.registry_hash)\n    def test_empty(self):\n        x=ChangeStructureRegistryBuilder().build((),(),lineage_factory=lf)\n        self.assertEqual(x.topology_projections,())\n        self.assertEqual(x.venue_coverages,())\n    def test_bad_projection(self):\n        with self.assertRaises(TypeError):\n            ChangeStructureRegistryBuilder().build((object(),),(),lineage_factory=lf)\n    def test_side_effects(self):\n        m=build_umd_150_certification_manifest()\n        self.assertFalse(any(m[k] for k in ("network_enabled","persistence_enabled","mutation_enabled","publication_enabled","execution_enabled")))\n\nif __name__=="__main__":\n    print("="*72);print(" UMD-150 CERTIFICATION TEST");print(" CHANGE STRUCTURE REGISTRY");print("="*72)\n    r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(TestUMD150))\n    if not r.wasSuccessful(): raise SystemExit(1)\n    m=build_umd_150_certification_manifest()\n    print();print(f"[PASS] Build: {m[\'build_id\']}");print(f"[PASS] Revision: {m[\'revision\']}");print(f"[PASS] Manifest hash: {m[\'manifest_hash\']}")\n    print("[PASS] Change-to-ladder, partition, market, and cross-venue structure queries certified")\n    print("[PASS] World-state changes can now be located inside deterministic market topology")\n    print("[PASS] Network, persistence, publication, and execution disabled")\n    print("[DONE] UMD-150 CERTIFIED")\n'
UPSTREAM_MODULE='umd_149_change_cross_venue_coverage'
UPSTREAM_VERIFIER='verify_umd_149_change_cross_venue_coverage'
EXPORTED_NAMES=('UMD_150_REVISION', 'ChangeStructureRegistry', 'ChangeStructureRegistryBuilder', 'build_umd_150_certification_manifest', 'verify_umd_150_change_structure_registry')

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
    marker="# UMD-150 exports"
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
            raise RuntimeError("UMD-150 missing symbols: "+", ".join(missing))
        verifier_name=[name for name in EXPORTED_NAMES if name.startswith("verify_")][0]
        if getattr(mod,verifier_name)() is not True:
            raise RuntimeError("UMD-150 verifier returned false")
    finally:
        if str(ROOT) in sys.path:
            sys.path.remove(str(ROOT))

def sha256_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    print("="*72)
    print(" UMD-150 INSTALLER")
    print(" CHANGE STRUCTURE REGISTRY")
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
        print("[ROLLBACK] UMD-150 installation failed; all affected files restored")
        raise

    manifest={
        "build_id":'UMD-150',
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
    print("[DONE] UMD-150 INSTALLATION COMPLETE")

if __name__=="__main__":
    main()
